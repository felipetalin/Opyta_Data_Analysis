"""Apply the approved, non-conflicting WSPKIN001 taxonomy R01 changes.

The validated workbooks remain the source of truth. Ambiguous merges are
explicitly excluded. Default mode is dry-run; ``--apply`` writes only after
creating database backups in the same transaction.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text


PROJECT_CODE = "WSPKIN001"
PROJECT_ID = 211
DEFAULT_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
DEFAULT_RESULTS = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados")
WORKBOOKS = {
    "fitoplancton": "Controle_Taxonomico_R01/Planilhas_Validadas/01_tabela_composicao_fitoplancton_ALGAEBASE_GBIF_validada.xlsx",
    "zooplancton": "Controle_Taxonomico_R01/Planilhas_Validadas/01_tabela_composicao_zooplancton_COL_WoRMS_validada.xlsx",
}
FIELD_MAP = {
    "Reino": "reino",
    "Filo": "filo",
    "Classe": "classe",
    "Ordem": "ordem",
    "Familia": "familia",
    "Genero": "genero",
    "Nome Cientifico": "nome_cientifico",
    "Autor e Ano": "autor_e_ano",
}
CONSOLIDATED_FIELDS = {"reino", "filo", "classe", "ordem", "familia", "genero", "nome_cientifico"}
EXCLUDED_TAXA = {
    "zooplancton": {
        "Cyphoderia ampula": "conflita com cadastro existente de Cyphoderia ampulla",
        "Trichocerca pussilla": "exige fusao com cadastro existente de Trichocerca pusilla",
    },
    "fitoplancton": {},
}


def connect_engine(data_root: Path):
    sys.path.insert(0, str(data_root))
    from core.engine import get_engine  # noqa: PLC0415

    return get_engine()


def clean(value: object) -> str:
    return " ".join(str(value).strip().split())


def load_plan(results_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for group, filename in WORKBOOKS.items():
        path = results_dir / filename
        changes = pd.read_excel(path, sheet_name="Alteracoes")
        for _, row in changes.iterrows():
            original = clean(row["Táxon original"])
            field_label = clean(row["Campo alterado"])
            if field_label not in FIELD_MAP:
                raise RuntimeError(f"Campo não permitido em {filename}: {field_label}")
            item = {
                "group": group,
                "workbook": filename,
                "original_name": original,
                "field_label": field_label,
                "field": FIELD_MAP[field_label],
                "before_workbook": row.get("Valor original"),
                "after": row.get("Valor aplicado"),
                "criterion": row.get("Critério"),
            }
            if original in EXCLUDED_TAXA[group]:
                item["exclusion_reason"] = EXCLUDED_TAXA[group][original]
                excluded.append(item)
            else:
                selected.append(item)
    return selected, excluded


def fetch_species(conn, names: list[str]) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT id_especie, nome_cientifico, grupo_biologico, reino, filo, classe,
               ordem, familia, genero, autor_e_ano, observacoes
        FROM public.especies
        WHERE nome_cientifico IN :names
        ORDER BY nome_cientifico, id_especie
        """
    ).bindparams(bindparam("names", expanding=True))
    return [dict(row) for row in conn.execute(query, {"names": names}).mappings()]


def group_updates(plan: list[dict[str, Any]], species: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for row in species:
        by_name.setdefault(row["nome_cientifico"], []).append(row)
    updates: list[dict[str, Any]] = []
    for original in sorted({item["original_name"] for item in plan}):
        matches = by_name.get(original, [])
        if len(matches) != 1:
            raise RuntimeError(f"Esperado um cadastro para {original!r}; encontrados={len(matches)}")
        changes = {item["field"]: item["after"] for item in plan if item["original_name"] == original}
        updates.append({"id_especie": matches[0]["id_especie"], "original_name": original, "changes": changes})
    return updates


def validate_targets(conn, updates: list[dict[str, Any]]) -> None:
    for update in updates:
        target = update["changes"].get("nome_cientifico")
        if not target or clean(target) == update["original_name"]:
            continue
        existing = conn.execute(
            text("SELECT id_especie FROM public.especies WHERE nome_cientifico = :target AND id_especie <> :id"),
            {"target": target, "id": update["id_especie"]},
        ).fetchall()
        if existing:
            raise RuntimeError(f"Destino já cadastrado e não seguro para renomear: {update['original_name']} -> {target}")


def backup(conn, stamp: str, updates: list[dict[str, Any]]) -> list[str]:
    ids = [update["id_especie"] for update in updates]
    names = [update["original_name"] for update in updates]
    species_table = f"backup_especies_wspkin001_taxonomia_r01_{stamp}"
    consolidated_table = f"backup_biota_wspkin001_taxonomia_r01_{stamp}"
    species_sql = text(f"CREATE TABLE public.{species_table} AS SELECT * FROM public.especies WHERE id_especie IN :ids").bindparams(bindparam("ids", expanding=True))
    consolidated_sql = text(f"CREATE TABLE public.{consolidated_table} AS SELECT * FROM public.biota_analise_consolidada WHERE nome_cientifico IN :names").bindparams(bindparam("names", expanding=True))
    conn.execute(species_sql, {"ids": ids})
    conn.execute(consolidated_sql, {"names": names})
    return [f"public.{species_table}", f"public.{consolidated_table}"]


def apply_updates(conn, updates: list[dict[str, Any]]) -> tuple[int, int]:
    species_rows = 0
    consolidated_rows = 0
    for update in updates:
        changes = update["changes"]
        set_sql = ", ".join(f"{field} = :{field}" for field in changes)
        params = {**changes, "id_especie": update["id_especie"]}
        result = conn.execute(text(f"UPDATE public.especies SET {set_sql} WHERE id_especie = :id_especie"), params)
        species_rows += int(result.rowcount or 0)

        consolidated_fields = {field: value for field, value in changes.items() if field in CONSOLIDATED_FIELDS}
        if not consolidated_fields:
            continue
        consolidated_set = ", ".join(f"{field} = :{field}" for field in consolidated_fields)
        consolidated_params = {**consolidated_fields, "original_name": update["original_name"]}
        result = conn.execute(
            text(f"UPDATE public.biota_analise_consolidada SET {consolidated_set} WHERE nome_cientifico = :original_name"),
            consolidated_params,
        )
        consolidated_rows += int(result.rowcount or 0)
    return species_rows, consolidated_rows


def verify(conn, updates: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for update in updates:
        row = conn.execute(
            text("SELECT * FROM public.especies WHERE id_especie = :id"),
            {"id": update["id_especie"]},
        ).mappings().one()
        for field, expected in update["changes"].items():
            if clean(row.get(field)) != clean(expected):
                failures.append(f"id={update['id_especie']} field={field}: {row.get(field)!r} != {expected!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--opyta-data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args()

    plan, excluded = load_plan(args.results_dir)
    names = sorted({item["original_name"] for item in plan})
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S").lower()
    engine = connect_engine(args.opyta_data_root)
    report: dict[str, Any] = {
        "project": PROJECT_CODE,
        "mode": "apply" if args.apply else "dry_run",
        "planned_field_changes": len(plan),
        "excluded_field_changes": len(excluded),
        "excluded": excluded,
        "backups": [],
    }
    try:
        with engine.begin() as conn:
            before = fetch_species(conn, names)
            updates = group_updates(plan, before)
            validate_targets(conn, updates)
            report["target_species"] = len(updates)
            report["before"] = before
            if args.apply:
                report["backups"] = backup(conn, stamp, updates)
                species_rows, consolidated_rows = apply_updates(conn, updates)
                failures = verify(conn, updates)
                if failures:
                    raise RuntimeError("Falha de verificação; transação revertida: " + "; ".join(failures))
                report["species_rows_updated"] = species_rows
                report["consolidated_rows_updated"] = consolidated_rows
                report["after"] = fetch_species(conn, sorted({u["changes"].get("nome_cientifico", u["original_name"]) for u in updates}))
    finally:
        engine.dispose()

    log_dir = args.results_dir / "Controle_Taxonomico_R01" / "Auditoria"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{stamp}_{report['mode']}_lote_seguro_wspkin001.json"
    log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in {"before", "after", "excluded"}}, ensure_ascii=False, indent=2))
    print(f"log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
