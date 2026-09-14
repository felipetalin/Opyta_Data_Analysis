from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
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
CLIENT_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
PROJECT_DIR = next(path for path in CLIENT_ROOT.iterdir() if path.name.startswith("A&G"))
OUTPUT_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "migracao" / "revisoes_vmp_subterranea"
LOG_DIR = ROOT / "logs" / "validacao_meio_fisico"

VMP_COLS = [
    "vmp_396_consumo_humano",
    "vmp_396_dessedentacao_animal",
    "vmp_396_irrigacao",
    "vmp_396_recreacao",
]

# Campos numericos: ausente em 100 mL = 0; faixa 100 a 700 = 100, pela regra
# operacional do projeto de usar o menor valor para destacar violacao.
CORRECTIONS = {
    "escherichia coli": (0.0, 200.0, None, 800.0),
    "coliformes termotolerantes": (0.0, 200.0, None, 1000.0),
    "aluminio dissolvido": (0.20, 5.0, 5.0, 0.20),
    "arsenio total": (0.01, 0.20, None, 0.05),
    "bario total": (0.70, None, None, 1.0),
    "boro total": (0.50, 5.0, 0.50, 1.0),
    "cloreto dissolvido": (250.0, None, 100.0, 400.0),
    "cobalto total": (None, 1.0, 0.05, None),
    "cobre dissolvido": (2.0, 0.50, 0.20, 1.0),
    "ferro total": (0.30, None, 5.0, 0.30),
    "nitrato n": (10.0, 90.0, None, 10.0),
    "vanadio total": (0.05, 0.10, 0.10, None),
}


def configure_database_access() -> None:
    repo_env = ROOT / ".env"
    if repo_env.exists():
        load_dotenv(repo_env, override=False)
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)
    has_database_url = bool(os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL"))
    has_db_parts = all(os.getenv(name) for name in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"))
    has_supabase_parts = all(os.getenv(name) for name in ("SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_HOST"))
    if not (has_database_url or has_db_parts or has_supabase_parts):
        fisico_url = os.getenv("FISICO_DB_URL")
        if fisico_url:
            os.environ.setdefault("DATABASE_URL", fisico_url)


def fold(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text_value = str(value).replace("\xa0", " ").strip()
    text_value = text_value.replace("ę", "e").replace("Ę", "E")
    text_value = unicodedata.normalize("NFKD", text_value)
    text_value = "".join(ch for ch in text_value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text_value.lower()).strip()


def tuple_to_payload(values: tuple[float | None, float | None, float | None, float | None]) -> dict[str, float | None]:
    return dict(zip(VMP_COLS, values, strict=True))


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    configure_database_access()
    engine = get_engine()

    audit_rows: list[dict[str, Any]] = []
    with engine.begin() as conn:
        backup_fisico = f"backup_fisico_braaeg001_vmp_subterranea_{ts.lower()}"
        backup_param = f"backup_parametros_analise_braaeg001_vmp_subterranea_{ts.lower()}"
        conn.execute(
            text(
                f"""
                CREATE TABLE public.{backup_fisico} AS
                SELECT *
                FROM public.fisico_analise_consolidada
                WHERE codigo_interno_opyta = :project_code
                  AND matriz ILIKE '%Subterr%'
                """
            ),
            {"project_code": PROJECT_CODE},
        )

        fisico_rows = conn.execute(
            text(
                """
                SELECT id_consolidated, nome_parametro, nome_campanha, nome_ponto,
                       vmp_396_consumo_humano, vmp_396_dessedentacao_animal,
                       vmp_396_irrigacao, vmp_396_recreacao
                FROM public.fisico_analise_consolidada
                WHERE codigo_interno_opyta = :project_code
                  AND matriz ILIKE '%Subterr%'
                """
            ),
            {"project_code": PROJECT_CODE},
        ).mappings().all()

        matched_ids: list[int] = []
        for row in fisico_rows:
            key = fold(row["nome_parametro"])
            if key not in CORRECTIONS:
                continue
            matched_ids.append(int(row["id_consolidated"]))
            payload = tuple_to_payload(CORRECTIONS[key])
            before = {col: row[col] for col in VMP_COLS}
            conn.execute(
                text(
                    """
                    UPDATE public.fisico_analise_consolidada
                    SET vmp_396_consumo_humano = :vmp_396_consumo_humano,
                        vmp_396_dessedentacao_animal = :vmp_396_dessedentacao_animal,
                        vmp_396_irrigacao = :vmp_396_irrigacao,
                        vmp_396_recreacao = :vmp_396_recreacao
                    WHERE id_consolidated = :id_consolidated
                    """
                ),
                {**payload, "id_consolidated": row["id_consolidated"]},
            )
            audit_rows.append(
                {
                    "tabela": "fisico_analise_consolidada",
                    "id": row["id_consolidated"],
                    "parametro": row["nome_parametro"],
                    "campanha": row["nome_campanha"],
                    "ponto": row["nome_ponto"],
                    **{f"antes_{col}": before[col] for col in VMP_COLS},
                    **{f"depois_{col}": payload[col] for col in VMP_COLS},
                }
            )

        conn.execute(
            text(
                f"""
                CREATE TABLE public.{backup_param} AS
                SELECT *
                FROM public.parametros_analise
                WHERE matriz ILIKE '%Subterr%'
                """
            )
        )

        param_rows = conn.execute(
            text(
                """
                SELECT id_parametro, nome_parametro, matriz,
                       vmp_396_consumo_humano, vmp_396_dessedentacao_animal,
                       vmp_396_irrigacao, vmp_396_recreacao
                FROM public.parametros_analise
                WHERE matriz ILIKE '%Subterr%'
                """
            )
        ).mappings().all()

        param_updates = 0
        for row in param_rows:
            key = fold(row["nome_parametro"])
            if key not in CORRECTIONS:
                continue
            payload = tuple_to_payload(CORRECTIONS[key])
            before = {col: row[col] for col in VMP_COLS}
            conn.execute(
                text(
                    """
                    UPDATE public.parametros_analise
                    SET vmp_396_consumo_humano = :vmp_396_consumo_humano,
                        vmp_396_dessedentacao_animal = :vmp_396_dessedentacao_animal,
                        vmp_396_irrigacao = :vmp_396_irrigacao,
                        vmp_396_recreacao = :vmp_396_recreacao
                    WHERE id_parametro = :id_parametro
                    """
                ),
                {**payload, "id_parametro": row["id_parametro"]},
            )
            param_updates += 1
            audit_rows.append(
                {
                    "tabela": "parametros_analise",
                    "id": row["id_parametro"],
                    "parametro": row["nome_parametro"],
                    "campanha": None,
                    "ponto": None,
                    **{f"antes_{col}": before[col] for col in VMP_COLS},
                    **{f"depois_{col}": payload[col] for col in VMP_COLS},
                }
            )

    audit_df = pd.DataFrame(audit_rows)
    audit_path = OUTPUT_DIR / f"{ts}_auditoria_correcao_vmp_subterranea_braaeg001.xlsx"
    audit_df.to_excel(audit_path, index=False)
    manifest = {
        "timestamp": ts,
        "status": "APPLIED",
        "project_code": PROJECT_CODE,
        "backup_fisico": backup_fisico,
        "backup_parametros": backup_param,
        "fisico_rows_updated": len(matched_ids),
        "parametros_rows_updated": param_updates,
        "audit_xlsx": str(audit_path),
        "rule": "Ausente em 100 mL armazenado como 0; Cloreto irrigacao 100 a 700 armazenado como 100 pela regra do menor valor.",
    }
    log_path = LOG_DIR / f"{ts}_correcao_vmp_subterranea_braaeg001.json"
    log_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
