from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.braaeg001 import migrar_biota_aquatica as base


PROJECT_CODE = "BRACED001"
PROJECT_ID = 133
BACKUP_PREFIX = "backup_biota_braced001"
LEGACY_CAMPAIGNS = ("1o Campanha (Chuva)",)


def configure_base() -> None:
    base.PROJECT_CODE = PROJECT_CODE
    base.PROJECT_ID = PROJECT_ID
    base.OUTPUT_LOG_DIR = Path(
        "outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/ictiofauna/migration"
    )
    base.create_backups = create_backups


def create_backups(connection, stamp: str) -> dict[str, str]:
    groups = [info["canonical"] for info in base.GROUPS.values()]
    targets = {
        "pontos": (
            "SELECT * FROM public.pontos_coleta WHERE id_projeto = :id",
            {"id": PROJECT_ID},
        ),
        "esforcos": (
            """
            SELECT e.* FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id AND e.grupo_biologico = ANY(:groups)
            """,
            {"id": PROJECT_ID, "groups": groups},
        ),
        "ictiofauna": (
            """
            SELECT r.* FROM public.resultados_ictiofauna r
            JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id AND e.grupo_biologico = ANY(:groups)
            """,
            {"id": PROJECT_ID, "groups": groups},
        ),
        "consolidado": (
            """
            SELECT * FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code AND grupo_biologico = ANY(:groups)
            """,
            {"code": PROJECT_CODE, "groups": groups},
        ),
    }
    backups = {}
    for name, (select_sql, params) in targets.items():
        table_name = f"{BACKUP_PREFIX}_{stamp}_{name}"
        connection.execute(text(f"CREATE TABLE public.{table_name} AS {select_sql}"), params)
        backups[name] = f"public.{table_name}"
    return backups


def cleanup_legacy_orphan_points(connection) -> dict[str, int]:
    deleted = {}
    for campaign in LEGACY_CAMPAIGNS:
        result = connection.execute(
            text(
                """
                DELETE FROM public.pontos_coleta p
                USING public.campanhas c
                WHERE p.id_campanha = c.id_campanha
                  AND p.id_projeto = :project_id
                  AND c.nome_campanha = :campaign
                  AND NOT EXISTS (
                      SELECT 1 FROM public.esforcos_amostragem e
                      WHERE e.id_ponto_coleta = p.id_ponto_coleta
                  )
                """
            ),
            {"project_id": PROJECT_ID, "campaign": campaign},
        )
        deleted[campaign] = result.rowcount or 0
    return deleted


def records(values: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(values) if values else pd.DataFrame()


def write_outputs(payload: dict[str, Any], output_dir: Path, applied: bool, stamp: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    mode = "apply" if applied else "dry_run"
    stem = f"{stamp}_{mode}_migracao_ictiofauna_braced001"
    json_path = output_dir / f"{stem}.json"
    xlsx_path = output_dir / f"{stem}.xlsx"
    summary = base.serializable_payload(payload, applied=applied, stamp=stamp)
    summary["project_code"] = PROJECT_CODE
    summary["project_id"] = PROJECT_ID
    summary["legacy_cleanup"] = payload.get("legacy_cleanup")
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=base.json_default),
        encoding="utf-8",
    )
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame([summary.get("source_summary", {})]).to_excel(writer, sheet_name="00_source_summary", index=False)
        pd.DataFrame([summary.get("db_before", {})]).to_excel(writer, sheet_name="01_db_before", index=False)
        if summary.get("db_after"):
            pd.DataFrame([summary["db_after"]]).to_excel(writer, sheet_name="02_db_after", index=False)
        records(payload.get("campaigns", [])).to_excel(writer, sheet_name="03_campaigns", index=False)
        records(payload.get("result_summary", [])).to_excel(writer, sheet_name="04_result_summary", index=False)
        records(payload.get("points", [])).to_excel(writer, sheet_name="05_points", index=False)
        records(payload.get("efforts", [])).to_excel(writer, sheet_name="06_efforts", index=False)
        records(payload.get("result_detail", [])).to_excel(writer, sheet_name="07_result_detail", index=False)
        if payload.get("consolidated_by_campaign"):
            records(payload["consolidated_by_campaign"]).to_excel(writer, sheet_name="08_consolidated_campaign", index=False)
        if payload.get("backups"):
            pd.DataFrame([payload["backups"]]).to_excel(writer, sheet_name="09_backups", index=False)
    return json_path, xlsx_path, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run/apply da migracao de ictiofauna do BRACED001.")
    parser.add_argument("--input-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--opyta-data-root", type=Path, default=REPO_ROOT.parent / "Opyta_Data")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approved-gates-ab", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.approved_gates_ab:
        raise SystemExit("Use --approved-gates-ab somente apos os Gates A e B aprovados.")

    configure_base()
    base.configure_groups(["Ictiofauna"])
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    engine = base.connect_engine(args.opyta_data_root)
    try:
        if args.apply:
            with engine.begin() as connection:
                payload = base.apply_migration(args.input_file.parent, connection, stamp, [args.input_file])
                payload["legacy_cleanup"] = cleanup_legacy_orphan_points(connection)
                payload["db_after"] = base.count_db(connection)
        else:
            with engine.connect() as connection:
                payload = base.build_plan(args.input_file.parent, connection, apply=False, input_files=[args.input_file])
        json_path, xlsx_path, summary = write_outputs(payload, args.output_dir, args.apply, stamp)
        print(json.dumps({**summary, "json": str(json_path), "xlsx": str(xlsx_path)}, ensure_ascii=False, indent=2, default=base.json_default))
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
