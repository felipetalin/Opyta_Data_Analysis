from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[4]
OPYTA_DATA_ROOT = ROOT.parent / "Opyta_Data"
sys.path.insert(0, str(OPYTA_DATA_ROOT))

from core.engine import get_engine  # noqa: E402


PROJECT_ID = 133
OUTPUT_DIR = Path(__file__).resolve().parent / "gate_b"
TAXONOMY_COLUMNS = ["reino", "filo", "classe", "ordem", "familia", "genero"]


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_species_sql() -> str:
    return """
        SELECT DISTINCT sp.id_especie
        FROM public.resultados_zooplancton rz
        JOIN public.esforcos_amostragem e ON e.id_esforco = rz.id_esforco
        JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
        JOIN public.especies sp ON sp.id_especie = rz.id_especie
        WHERE p.id_projeto = :project_id
    """


def load_slice(connection) -> pd.DataFrame:
    return pd.read_sql(
        text(
            f"""
            SELECT sp.id_especie, sp.nome_cientifico, sp.reino, sp.filo, sp.classe,
                   sp.ordem, sp.familia, sp.genero, count(rz.*) AS ocorrencias
            FROM public.resultados_zooplancton rz
            JOIN public.esforcos_amostragem e ON e.id_esforco = rz.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            JOIN public.especies sp ON sp.id_especie = rz.id_especie
            WHERE p.id_projeto = :project_id
            GROUP BY sp.id_especie, sp.nome_cientifico, sp.reino, sp.filo,
                     sp.classe, sp.ordem, sp.familia, sp.genero
            ORDER BY sp.nome_cientifico
            """
        ),
        connection,
        params={"project_id": PROJECT_ID},
    )


def load_consolidated_slice(connection) -> pd.DataFrame:
    return pd.read_sql(
        text(
            """
            SELECT nome_cientifico, reino, filo, classe, ordem, familia, genero,
                   count(*) AS ocorrencias
            FROM public.biota_analise_consolidada
            WHERE id_projeto = :project_id AND grupo_biologico LIKE 'Zoopl%'
            GROUP BY nome_cientifico, reino, filo, classe, ordem, familia, genero
            ORDER BY nome_cientifico
            """
        ),
        connection,
        params={"project_id": PROJECT_ID},
    )


def issue_rows(frame: pd.DataFrame) -> pd.DataFrame:
    invalid_families = {"Ciclopideos", "Ciclopídeos", "Difflugidae", "Cyphoderidae"}
    invalid_names = {"Collurella minima"}
    mask = frame["familia"].isin(invalid_families) | frame["nome_cientifico"].isin(invalid_names)
    for column in TAXONOMY_COLUMNS:
        values = frame[column].astype("string").str.strip().str.lower()
        mask |= frame[column].isna() | values.isin(["", "none"])
    mask |= frame["genero"].astype("string").str.strip().str.casefold().eq("ciliado ni")
    return frame.loc[mask].copy()


def apply_corrections(connection, backup_table: str, consolidated_backup_table: str) -> None:
    connection.execute(
        text(
            f"""
            CREATE TABLE public.{backup_table} AS
            SELECT sp.*
            FROM public.especies sp
            WHERE sp.familia IN ('Ciclopideos', 'Ciclopídeos', 'Difflugidae', 'Cyphoderidae')
               OR sp.nome_cientifico = 'Collurella minima'
               OR sp.id_especie IN ({project_species_sql()})
            """
        ),
        {"project_id": PROJECT_ID},
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE public.{consolidated_backup_table} AS
            SELECT *
            FROM public.biota_analise_consolidada
            WHERE id_projeto = :project_id AND grupo_biologico LIKE 'Zoopl%'
            """
        ),
        {"project_id": PROJECT_ID},
    )
    connection.execute(
        text(
            """
            UPDATE public.biota_analise_consolidada
            SET familia = CASE familia
                WHEN 'Ciclopideos' THEN 'Cyclopidae'
                WHEN 'Ciclopídeos' THEN 'Cyclopidae'
                WHEN 'Difflugidae' THEN 'Difflugiidae'
                WHEN 'Cyphoderidae' THEN 'Cyphoderiidae'
                ELSE familia
            END
            WHERE id_projeto = :project_id AND grupo_biologico LIKE 'Zoopl%'
            """
        ),
        {"project_id": PROJECT_ID},
    )
    connection.execute(
        text(
            """
            UPDATE public.biota_analise_consolidada
            SET nome_cientifico = 'Colurella minima', genero = 'Colurella'
            WHERE id_projeto = :project_id AND grupo_biologico LIKE 'Zoopl%'
              AND nome_cientifico = 'Collurella minima'
            """
        ),
        {"project_id": PROJECT_ID},
    )
    for column in TAXONOMY_COLUMNS:
        connection.execute(
            text(
                f"""
                UPDATE public.biota_analise_consolidada
                SET {column} = 'N.A.'
                WHERE id_projeto = :project_id AND grupo_biologico LIKE 'Zoopl%'
                  AND ({column} IS NULL OR btrim({column}) = '' OR lower(btrim({column})) = 'none')
                """
            ),
            {"project_id": PROJECT_ID},
        )
    connection.execute(
        text(
            """
            UPDATE public.biota_analise_consolidada
            SET genero = 'N.A.'
            WHERE id_projeto = :project_id AND grupo_biologico LIKE 'Zoopl%'
              AND lower(btrim(genero)) = 'ciliado ni'
            """
        ),
        {"project_id": PROJECT_ID},
    )
    connection.execute(
        text(
            """
            UPDATE public.especies
            SET familia = CASE familia
                WHEN 'Ciclopideos' THEN 'Cyclopidae'
                WHEN 'Ciclopídeos' THEN 'Cyclopidae'
                WHEN 'Difflugidae' THEN 'Difflugiidae'
                WHEN 'Cyphoderidae' THEN 'Cyphoderiidae'
                ELSE familia
            END
            WHERE familia IN ('Ciclopideos', 'Ciclopídeos', 'Difflugidae', 'Cyphoderidae')
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE public.especies
            SET nome_cientifico = 'Colurella minima', genero = 'Colurella'
            WHERE nome_cientifico = 'Collurella minima'
            """
        )
    )
    for column in TAXONOMY_COLUMNS:
        connection.execute(
            text(
                f"""
                UPDATE public.especies
                SET {column} = 'N.A.'
                WHERE id_especie IN ({project_species_sql()})
                  AND ({column} IS NULL OR btrim({column}) = '' OR lower(btrim({column})) = 'none')
                """
            ),
            {"project_id": PROJECT_ID},
        )
    connection.execute(
        text(
            f"""
            UPDATE public.especies
            SET genero = 'N.A.'
            WHERE id_especie IN ({project_species_sql()})
              AND lower(btrim(genero)) = 'ciliado ni'
            """
        ),
        {"project_id": PROJECT_ID},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = now_tag()
    backup_table = f"bk_esp_braced001_zoo_r01_{tag.lower()}"
    consolidated_backup_table = f"bk_cons_braced001_zoo_r01_{tag.lower()}"
    engine = get_engine()

    with engine.begin() as connection:
        before = load_slice(connection)
        before_issues = issue_rows(before)
        consolidated_before = load_consolidated_slice(connection)
        consolidated_issues_before = issue_rows(consolidated_before)
        if args.apply:
            apply_corrections(connection, backup_table, consolidated_backup_table)
        after = load_slice(connection)
        after_issues = issue_rows(after)
        consolidated_after = load_consolidated_slice(connection)
        consolidated_issues_after = issue_rows(consolidated_after)
        counts = connection.execute(
            text(
                """
                SELECT
                  (SELECT count(*) FROM public.resultados_zooplancton rz
                   JOIN public.esforcos_amostragem e ON e.id_esforco = rz.id_esforco
                   JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
                   WHERE p.id_projeto = :project_id) AS resultados,
                  (SELECT count(*) FROM public.biota_analise_consolidada
                   WHERE id_projeto = :project_id AND grupo_biologico = 'Zooplâncton') AS consolidado
                """
            ),
            {"project_id": PROJECT_ID},
        ).mappings().one()

    changed = before.merge(after, on="id_especie", suffixes=("_antes", "_depois"))
    compare_columns = ["nome_cientifico", *TAXONOMY_COLUMNS]
    changed_mask = pd.Series(False, index=changed.index)
    for column in compare_columns:
        changed_mask |= changed[f"{column}_antes"].fillna("<NULL>") != changed[f"{column}_depois"].fillna("<NULL>")
    changed = changed.loc[changed_mask].copy()

    status = (
        "PASS"
        if args.apply
        and after_issues.empty
        and consolidated_issues_after.empty
        and counts["resultados"] == counts["consolidado"] == 624
        else "DRY_RUN"
    )
    json_path = OUTPUT_DIR / f"{tag}_taxonomia_r01_zooplancton_braced001.json"
    xlsx_path = OUTPUT_DIR / f"{tag}_taxonomia_r01_zooplancton_braced001.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        before.to_excel(writer, sheet_name="antes", index=False)
        after.to_excel(writer, sheet_name="depois", index=False)
        changed.to_excel(writer, sheet_name="alteracoes", index=False)
        before_issues.to_excel(writer, sheet_name="pendencias_antes", index=False)
        after_issues.to_excel(writer, sheet_name="pendencias_depois", index=False)
        consolidated_before.to_excel(writer, sheet_name="consolidado_antes", index=False)
        consolidated_after.to_excel(writer, sheet_name="consolidado_depois", index=False)
        consolidated_issues_before.to_excel(writer, sheet_name="pend_cons_antes", index=False)
        consolidated_issues_after.to_excel(writer, sheet_name="pend_cons_depois", index=False)
    audit = {
        "executed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "project_id": PROJECT_ID,
        "group": "Zooplancton",
        "mode": "apply" if args.apply else "dry_run",
        "status": status,
        "backup_table": backup_table if args.apply else None,
        "consolidated_backup_table": consolidated_backup_table if args.apply else None,
        "species_before": int(len(before)),
        "species_after": int(len(after)),
        "issues_before": int(len(before_issues)),
        "issues_after": int(len(after_issues)),
        "consolidated_issues_before": int(len(consolidated_issues_before)),
        "consolidated_issues_after": int(len(consolidated_issues_after)),
        "changed_species": int(len(changed)),
        "results_rows": int(counts["resultados"]),
        "consolidated_rows": int(counts["consolidado"]),
        "xlsx": str(xlsx_path),
    }
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    audit["xlsx_sha256"] = sha256(xlsx_path)
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0 if status in {"PASS", "DRY_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
