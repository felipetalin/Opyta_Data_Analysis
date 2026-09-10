from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
for path in (ROOT / "src", OPYTA_DATA_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.engine import get_engine  # noqa: E402


PROJECT_CODE = "BRAAEG001"
ENV_FILE = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")

PARAM_TABLE_COLS = [
    "nome_parametro",
    "unidade_medida",
    "matriz",
    "vmp_357_cl1",
    "vmp_357_cl2",
    "vmp_357_cl3",
    "vmp_396_vmp",
    "vmp_396_vr",
    "vmp_454_n1",
    "vmp_454_n2",
    "vmp_430_padrao",
    "vmp_396_consumo_humano",
    "vmp_396_animal",
    "vmp_396_irrigacao",
    "vmp_396_recreacao",
    "vmp_357_cl2_min",
    "vmp_357_cl2_max",
    "vmp_357_cl1_min",
    "vmp_357_cl1_max",
    "vmp_396_dessedentacao_animal",
]

FISICO_INSERT_COLS = [
    "codigo_interno_opyta",
    "nome_projeto",
    "nome_empresa",
    "nome_campanha",
    "nome_ponto",
    "data_hora_coleta",
    "latitude",
    "longitude",
    "bacia_hidrografica",
    "matriz",
    "nome_parametro",
    "sinal_limite",
    "valor_medido",
    "unidade_medida",
    "unidade_original_laudo",
    "laboratorio_responsavel",
    "observacoes_resultado",
    "vmp_357_cl1_min",
    "vmp_357_cl1_max",
    "vmp_357_cl2_min",
    "vmp_357_cl2_max",
    "vmp_amonia_dinamico",
    "vmp_454_n1",
    "vmp_454_n2",
    "vmp_396_consumo_humano",
    "vmp_396_dessedentacao_animal",
    "vmp_396_irrigacao",
    "vmp_396_recreacao",
    "vmp_430_padrao",
]

NUMERIC_COLS = {
    "id_cliente",
    "id_parametro",
    "latitude",
    "longitude",
    "valor_medido",
    "vmp_357_cl1",
    "vmp_357_cl2",
    "vmp_357_cl3",
    "vmp_396_vmp",
    "vmp_396_vr",
    "vmp_454_n1",
    "vmp_454_n2",
    "vmp_430_padrao",
    "vmp_396_consumo_humano",
    "vmp_396_animal",
    "vmp_396_irrigacao",
    "vmp_396_recreacao",
    "vmp_357_cl2_min",
    "vmp_357_cl2_max",
    "vmp_357_cl1_min",
    "vmp_357_cl1_max",
    "vmp_396_dessedentacao_animal",
    "vmp_amonia_dinamico",
}

DATE_COLS = {"data_inicio", "data_fim_prevista", "data_hora_coleta"}


def configure_database_access(env_file: Path) -> None:
    repo_env = ROOT / ".env"
    if repo_env.exists():
        load_dotenv(repo_env, override=False)
    if env_file.exists():
        load_dotenv(env_file, override=False)

    has_database_url = bool(os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL"))
    has_db_parts = all(os.getenv(name) for name in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"))
    has_supabase_db_parts = all(
        os.getenv(name) for name in ("SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_HOST")
    )
    if not (has_database_url or has_db_parts or has_supabase_db_parts):
        fisico_url = os.getenv("FISICO_DB_URL")
        if fisico_url:
            os.environ.setdefault("DATABASE_URL", fisico_url)


def cell_value(value: Any, col: str) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() in {"nan", "none"}:
            return None
        if col in DATE_COLS:
            parsed = pd.to_datetime(text, errors="coerce")
            if pd.isna(parsed):
                return None
            return parsed.date() if col in {"data_inicio", "data_fim_prevista"} else parsed.to_pydatetime()
        if col in NUMERIC_COLS:
            try:
                number = float(text.replace(",", "."))
            except ValueError:
                return None
            return int(number) if number.is_integer() and col.startswith("id_") else number
        return text
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.date() if col in {"data_inicio", "data_fim_prevista"} else value.to_pydatetime()
    if col in NUMERIC_COLS:
        number = float(value)
        return int(number) if number.is_integer() and col.startswith("id_") else number
    return value


def row_payload(row: pd.Series, cols: list[str]) -> dict[str, Any]:
    return {col: cell_value(row.get(col), col) for col in cols if col in row.index}


class RestClient:
    def __init__(self, env_file: Path) -> None:
        load_dotenv(env_file, override=True)
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_SERVICE_KEY")
            or os.getenv("SUPABASE_ANON_KEY", "")
        )
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL/SUPABASE_ANON_KEY ausentes.")

    def _request(self, method: str, table: str, query: str = "", payload: Any | None = None) -> Any:
        endpoint = f"{self.url}/rest/v1/{urllib.parse.quote(table)}"
        if query:
            endpoint += "?" + query
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            method=method,
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else []

    def get(self, table: str, query: str, page_size: int = 1000) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            range_query = query
            req = urllib.request.Request(
                f"{self.url}/rest/v1/{urllib.parse.quote(table)}?{range_query}",
                headers={
                    "apikey": self.key,
                    "Authorization": f"Bearer {self.key}",
                    "Accept": "application/json",
                    "Range": f"{offset}-{offset + page_size - 1}",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                batch = json.loads(response.read().decode("utf-8"))
            rows.extend(batch)
            if len(batch) < page_size:
                return rows
            offset += page_size

    def post(self, table: str, payload: Any) -> Any:
        return self._request("POST", table, payload=payload)

    def patch(self, table: str, query: str, payload: dict[str, Any]) -> Any:
        return self._request("PATCH", table, query=query, payload=payload)

    def delete(self, table: str, query: str) -> Any:
        return self._request("DELETE", table, query=query)


def quote_filter(value: Any) -> str:
    return urllib.parse.quote(str(value), safe="")


def read_report_for_dry_run(dry_run_xlsx: Path, log_dir: Path) -> dict[str, Any] | None:
    stem = dry_run_xlsx.name.replace("_dry_run_migracao_controlada_braaeg001.xlsx", "")
    json_path = log_dir / f"{stem}_dry_run_migracao_controlada_braaeg001.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    return None


def insert_rows(conn, table: str, rows: list[dict[str, Any]], cols: list[str], batch_size: int = 500) -> int:
    if not rows:
        return 0
    col_sql = ", ".join(cols)
    value_sql = ", ".join(f":{col}" for col in cols)
    stmt = text(f"INSERT INTO public.{table} ({col_sql}) VALUES ({value_sql})")
    inserted = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        result = conn.execute(stmt, batch)
        inserted += result.rowcount if result.rowcount and result.rowcount > -1 else len(batch)
    return inserted


def update_parameter_rows(conn, updates_df: pd.DataFrame) -> tuple[int, list[int]]:
    updated = 0
    updated_ids: list[int] = []
    for _, row in updates_df.iterrows():
        id_param = int(float(row["id_parametro"]))
        payload: dict[str, Any] = {}
        for col in PARAM_TABLE_COLS:
            if col not in row.index or col in {"nome_parametro", "matriz"}:
                continue
            value = cell_value(row[col], col)
            if value is not None:
                payload[col] = value
        if not payload:
            continue
        payload["id_parametro"] = id_param
        set_sql = ", ".join(f"{col} = :{col}" for col in payload if col != "id_parametro")
        result = conn.execute(
            text(f"UPDATE public.parametros_analise SET {set_sql} WHERE id_parametro = :id_parametro"),
            payload,
        )
        updated += result.rowcount if result.rowcount and result.rowcount > -1 else 1
        updated_ids.append(id_param)
    return updated, updated_ids


def rollback(client: RestClient, inserted_params: list[dict[str, Any]], backup_rows: list[dict[str, Any]], inserted_project: bool, inserted_fisico: bool) -> list[str]:
    events: list[str] = []
    if inserted_fisico:
        client.delete("fisico_analise_consolidada", f"codigo_interno_opyta=eq.{PROJECT_CODE}")
        events.append("rollback_delete_fisico")
    for row in reversed(inserted_params):
        name = quote_filter(row["nome_parametro"])
        matrix = quote_filter(row["matriz"])
        client.delete("parametros_analise", f"nome_parametro=eq.{name}&matriz=eq.{matrix}")
        events.append(f"rollback_delete_parametro:{row['nome_parametro']}|{row['matriz']}")
    for row in backup_rows:
        id_param = int(row["id_parametro"])
        payload = {col: cell_value(row.get(col), col) for col in PARAM_TABLE_COLS}
        client.patch("parametros_analise", f"id_parametro=eq.{id_param}", payload)
        events.append(f"rollback_update_parametro:{id_param}")
    if inserted_project:
        client.delete("projetos", f"codigo_interno_opyta=eq.{PROJECT_CODE}")
        events.append("rollback_delete_project")
    return events


def apply_migration(dry_run_xlsx: Path, log_dir: Path, env_file: Path, output_dir: Path) -> tuple[Path, dict[str, Any]]:
    report = read_report_for_dry_run(dry_run_xlsx, log_dir)
    if report and report.get("status") != "DRY_RUN_READY":
        raise RuntimeError(f"Dry-run nao esta pronto: {report.get('status')}")

    project_df = pd.read_excel(dry_run_xlsx, sheet_name="projeto_payload", dtype=object).where(pd.notna, None)
    inserts_df = pd.read_excel(dry_run_xlsx, sheet_name="parametros_insert", dtype=object).where(pd.notna, None)
    updates_df = pd.read_excel(dry_run_xlsx, sheet_name="parametros_update", dtype=object).where(pd.notna, None)
    backup_df = pd.read_excel(dry_run_xlsx, sheet_name="parametros_backup", dtype=object).where(pd.notna, None)
    preview_df = pd.read_excel(dry_run_xlsx, sheet_name="preview_migracao", dtype=object).where(pd.notna, None)

    backup_rows = [row_payload(row, ["id_parametro"] + PARAM_TABLE_COLS) for _, row in backup_df.iterrows()]
    project_payload = row_payload(
        project_df.iloc[0],
        ["id_cliente", "nome_projeto", "codigo_interno_opyta", "data_inicio", "data_fim_prevista", "descricao_projeto", "status_projeto"],
    )
    param_insert_rows = [row_payload(row, PARAM_TABLE_COLS) for _, row in inserts_df.iterrows()]
    fisico_rows = [row_payload(row, FISICO_INSERT_COLS) for _, row in preview_df.iterrows()]
    update_ids_pre = [int(float(value)) for value in updates_df.get("id_parametro", pd.Series(dtype=object)).dropna().tolist()]

    configure_database_access(env_file)
    engine = get_engine()
    try:
        with engine.begin() as conn:
            existing_project = conn.execute(
                text("SELECT COUNT(*)::int FROM public.projetos WHERE codigo_interno_opyta = :code"),
                {"code": PROJECT_CODE},
            ).scalar_one()
            existing_fisico = conn.execute(
                text("SELECT COUNT(*)::int FROM public.fisico_analise_consolidada WHERE codigo_interno_opyta = :code"),
                {"code": PROJECT_CODE},
            ).scalar_one()
            params_before = conn.execute(text("SELECT COUNT(*)::int FROM public.parametros_analise")).scalar_one()
            if existing_project:
                raise RuntimeError("Projeto BRAAEG001 ja existe; carga abortada para evitar duplicidade.")
            if existing_fisico:
                raise RuntimeError("Ja existem registros BRAAEG001 em fisico_analise_consolidada; carga abortada.")

            backup_table = None
            backup_count = 0
            if update_ids_pre:
                backup_table = "backup_parametros_analise_braaeg001_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
                ids_sql = ", ".join(str(value) for value in sorted(set(update_ids_pre)))
                conn.execute(
                    text(
                        f"""
                        CREATE TABLE public.{backup_table} AS
                        SELECT *
                        FROM public.parametros_analise
                        WHERE id_parametro IN ({ids_sql})
                        """
                    )
                )
                backup_count = conn.execute(text(f"SELECT COUNT(*)::int FROM public.{backup_table}")).scalar_one()

            insert_rows(conn, "projetos", [project_payload], list(project_payload))
            inserted_params = insert_rows(conn, "parametros_analise", param_insert_rows, PARAM_TABLE_COLS)
            updated_params, updated_param_ids = update_parameter_rows(conn, updates_df)
            inserted_fisico = insert_rows(conn, "fisico_analise_consolidada", fisico_rows, FISICO_INSERT_COLS, batch_size=250)

            project_rows_after = conn.execute(
                text("SELECT COUNT(*)::int FROM public.projetos WHERE codigo_interno_opyta = :code"),
                {"code": PROJECT_CODE},
            ).scalar_one()
            fisico_rows_after = conn.execute(
                text("SELECT COUNT(*)::int FROM public.fisico_analise_consolidada WHERE codigo_interno_opyta = :code"),
                {"code": PROJECT_CODE},
            ).scalar_one()
            params_after = conn.execute(text("SELECT COUNT(*)::int FROM public.parametros_analise")).scalar_one()

            if project_rows_after != 1:
                raise RuntimeError(f"Conferencia de projeto falhou: project_rows_after={project_rows_after}")
            if fisico_rows_after != len(fisico_rows):
                raise RuntimeError(
                    "Conferencia de linhas fisicas falhou: "
                    f"fonte={len(fisico_rows)}, banco={fisico_rows_after}, insert_rowcount={inserted_fisico}"
                )

            result = {
                "status": "APPLIED",
                "access_mode": "sqlalchemy_core_engine",
                "transactional": True,
                "events": [
                    "insert_project:1",
                    f"insert_parametros:{inserted_params}",
                    f"update_parametros:{updated_params}",
                    f"insert_fisico:{inserted_fisico}",
                ],
                "inserted_params": [
                    {"nome_parametro": row.get("nome_parametro"), "matriz": row.get("matriz")}
                    for row in param_insert_rows
                ],
                "updated_param_ids": updated_param_ids,
                "param_backup_table": backup_table,
                "param_backup_db_rows": backup_count,
                "param_backup_rows": len(backup_rows),
                "params_before": params_before,
                "params_after": params_after,
                "fisico_rows_after": fisico_rows_after,
                "project_rows_after": project_rows_after,
            }
    finally:
        engine.dispose()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest_path = output_dir / f"{ts}_aplicacao_migracao_controlada_braaeg001.json"
    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dry_run_xlsx": str(dry_run_xlsx),
        **result,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply BRAAEG001 controlled migration via SQL transaction.")
    parser.add_argument("--dry-run-xlsx", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--log-dir", default=Path("logs/validacao_meio_fisico"), type=Path)
    parser.add_argument("--env-file", default=ENV_FILE, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        print("DRY_MODE=1")
        print("Use --apply para gravar no Supabase.")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    try:
        manifest_path, manifest = apply_migration(args.dry_run_xlsx, args.log_dir, args.env_file, args.output_dir)
    except Exception as exc:
        print(f"STATUS=FAILED")
        print(str(exc))
        return 1
    print(f"STATUS={manifest['status']}")
    print(f"MANIFEST={manifest_path}")
    print("SUMMARY=" + json.dumps({k: manifest[k] for k in ["fisico_rows_after", "project_rows_after"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
