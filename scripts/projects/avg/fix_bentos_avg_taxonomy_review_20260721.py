from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
for path in (ROOT / "src", OPYTA_DATA_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.engine import get_engine  # noqa: E402


PROJECT_CODE = "BRAAVG002"
GROUP = "Zoobentos"
AUDIT_DIR = ROOT / "outputs" / "_migration" / "avg_bentos_2026"


CORRECTIONS = [
    {
        "label": "Oligochaeta_sem_Hemiptera",
        "where": "trim(coalesce(nome_cientifico, '')) = 'Oligochaeta'",
        "set": {"ordem": None},
        "reason": "Hemiptera nao pertence a Oligochaeta; manter sem ordem no padrao operacional de biomonitoramento.",
    },
    {
        "label": "Artropoda_para_Arthropoda",
        "where": "trim(coalesce(filo, '')) = 'Artropoda'",
        "set": {"filo": "Arthropoda"},
        "reason": "Padronizacao grafica/taxonomica do filo Arthropoda.",
    },
    {
        "label": "Scirtodae_para_Scirtidae",
        "where": "trim(coalesce(nome_cientifico, '')) = 'Scirtodae' OR trim(coalesce(familia, '')) = 'Scirtodae'",
        "set": {"nome_cientifico": "Scirtidae", "familia": "Scirtidae"},
        "reason": "Correcao de grafia da familia Scirtidae; BMWP permanece 0 por nao constar na adaptacao Rio das Velhas.",
    },
    {
        "label": "Dolychopodidae_para_Dolichopodidae",
        "where": "trim(coalesce(nome_cientifico, '')) = 'Dolychopodidae' OR trim(coalesce(familia, '')) = 'Dolychopodidae'",
        "set": {"nome_cientifico": "Dolichopodidae", "familia": "Dolichopodidae"},
        "reason": "Correcao de grafia da familia Dolichopodidae.",
    },
    {
        "label": "Turbelaria_para_Turbellaria",
        "where": "trim(coalesce(classe, '')) = 'Turbelaria'",
        "set": {"classe": "Turbellaria"},
        "reason": "Correcao de grafia da classe Turbellaria.",
    },
    {
        "label": "Melanoides_sp_classificacao_molusco",
        "where": "trim(coalesce(nome_cientifico, '')) = 'Melanoides sp.'",
        "set": {"filo": "Mollusca", "classe": "Gastropoda", "ordem": "Mesogastropoda", "familia": "Thiaridae"},
        "reason": "Melanoides e molusco gastrópode, nao Insecta/Arthropoda.",
    },
    {
        "label": "Acarina_para_Acari",
        "where": "trim(coalesce(nome_cientifico, '')) = 'Acarina' OR trim(coalesce(ordem, '')) = 'Acarina'",
        "set": {"nome_cientifico": "Acari", "ordem": "Acari"},
        "reason": "Uso do nome atualmente aceito para acaros, evitando mistura entre nome cientifico Acarina e ordem Acari.",
    },
    {
        "label": "Sphaeriida_para_Veneroida",
        "where": "trim(coalesce(ordem, '')) = 'Sphaeriida'",
        "set": {"ordem": "Veneroida"},
        "reason": "Padrao operacional adotado para biomonitoramento; Cardiida fica como alternativa moderna nao aplicada nesta rodada.",
    },
]

MERGES = [
    {
        "label": "merge_Dolychopodidae_em_Dolichopodidae",
        "source_name": "Dolychopodidae",
        "target_name": "Dolichopodidae",
        "reason": "Nome cientifico possui restricao unica; referencias do erro grafico devem apontar para o taxon correto ja existente.",
    },
    {
        "label": "merge_Hemiptera_Annelida_em_Oligochaeta",
        "source_name": "Hemiptera",
        "target_name": "Oligochaeta",
        "source_filter": "filo = 'Annelida' AND classe = 'Oligochaeta'",
        "reason": "Registro Hemiptera classificado como Annelida/Oligochaeta e taxonomicamente incorreto; deve ser Oligochaeta com ordem em branco.",
    }
]


WATCH_SQL = text(
    """
    SELECT
        id_especie,
        nome_cientifico,
        reino,
        filo,
        classe,
        ordem,
        familia,
        genero,
        bmwp_score
    FROM public.especies
    WHERE trim(coalesce(nome_cientifico, '')) IN (
        'Oligochaeta', 'Scirtodae', 'Scirtidae', 'Dolychopodidae',
        'Dolichopodidae', 'Melanoides sp.', 'Acarina', 'Acari', 'Sphaerium sp.'
    )
       OR trim(coalesce(filo, '')) = 'Artropoda'
       OR trim(coalesce(classe, '')) = 'Turbelaria'
       OR trim(coalesce(ordem, '')) IN ('Acarina', 'Sphaeriida')
       OR trim(coalesce(familia, '')) IN ('Scirtodae', 'Dolychopodidae')
    ORDER BY nome_cientifico, id_especie
    """
)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _fetch_watch(conn) -> pd.DataFrame:
    return pd.read_sql(WATCH_SQL, conn)


def _affected_sql(where_clause: str) -> text:
    return text(f"SELECT COUNT(*)::int AS n FROM public.especies WHERE {where_clause}")


def _update_sql(correction: dict[str, Any]) -> tuple[text, dict[str, Any]]:
    sets = []
    params: dict[str, Any] = {}
    for idx, (field, value) in enumerate(correction["set"].items()):
        key = f"value_{idx}"
        sets.append(f"{field} = :{key}")
        params[key] = value
    sql = text(f"UPDATE public.especies SET {', '.join(sets)} WHERE {correction['where']} RETURNING id_especie, nome_cientifico")
    return sql, params


def _species_id(conn, name: str, extra_filter: str | None = None) -> int | None:
    where = "trim(nome_cientifico) = :name"
    if extra_filter:
        where = f"{where} AND {extra_filter}"
    row = conn.execute(
        text(f"SELECT id_especie::int FROM public.especies WHERE {where} ORDER BY id_especie LIMIT 1"),
        {"name": name},
    ).first()
    return int(row[0]) if row else None


def _reference_count(conn, species_id: int) -> int:
    return int(
        conn.execute(
            text("SELECT COUNT(*)::int FROM public.resultados_zoobentos WHERE id_especie = :species_id"),
            {"species_id": species_id},
        ).scalar_one()
    )


def _apply_merges(conn, apply: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for merge in MERGES:
        source_id = _species_id(conn, merge["source_name"], merge.get("source_filter"))
        target_id = _species_id(conn, merge["target_name"])
        source_refs = _reference_count(conn, source_id) if source_id else 0
        item = {
            "label": merge["label"],
            "source_name": merge["source_name"],
            "target_name": merge["target_name"],
            "source_id": source_id,
            "target_id": target_id,
            "source_refs_resultados_zoobentos": source_refs,
            "reason": merge["reason"],
        }
        if apply and source_id and target_id and source_id != target_id:
            updated = conn.execute(
                text(
                    """
                    UPDATE public.resultados_zoobentos
                    SET id_especie = :target_id
                    WHERE id_especie = :source_id
                    """
                ),
                {"source_id": source_id, "target_id": target_id},
            ).rowcount
            deleted = conn.execute(
                text("DELETE FROM public.especies WHERE id_especie = :source_id"),
                {"source_id": source_id},
            ).rowcount
            item["updated_resultados_zoobentos"] = int(updated or 0)
            item["deleted_source_species"] = int(deleted or 0)
        results.append(item)
    return results


def run(apply: bool) -> dict[str, Any]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    with engine.begin() as conn:
        before = _fetch_watch(conn)
        merges = _apply_merges(conn, apply)
        plan = []
        applied = []
        for correction in CORRECTIONS:
            affected = int(conn.execute(_affected_sql(correction["where"])).scalar_one())
            item = {
                "label": correction["label"],
                "affected_before": affected,
                "set": correction["set"],
                "reason": correction["reason"],
            }
            plan.append(item)
            if apply and affected:
                sql, params = _update_sql(correction)
                rows = [dict(row) for row in conn.execute(sql, params).mappings().all()]
                item["updated_rows"] = len(rows)
                item["updated_ids"] = [row["id_especie"] for row in rows]
                applied.append(item)
        after = _fetch_watch(conn)

    xlsx = AUDIT_DIR / "taxonomia_bentos_avg_revisao_20260721.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        before.to_excel(writer, sheet_name="antes", index=False)
        pd.DataFrame(merges).to_excel(writer, sheet_name="mesclagens", index=False)
        pd.DataFrame(plan).to_excel(writer, sheet_name="plano", index=False)
        after.to_excel(writer, sheet_name="depois", index=False)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "apply": apply,
        "audit_workbook": xlsx,
        "merges": merges,
        "plan": plan,
        "applied": applied,
        "before_rows": int(len(before)),
        "after_rows": int(len(after)),
    }
    suffix = "aplicada" if apply else "dry_run"
    json_path = AUDIT_DIR / f"taxonomia_bentos_avg_revisao_20260721_{suffix}.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["audit_json"] = json_path
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita/aplica revisao taxonomica AVG Zoobentos 20260721.")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.apply), ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
