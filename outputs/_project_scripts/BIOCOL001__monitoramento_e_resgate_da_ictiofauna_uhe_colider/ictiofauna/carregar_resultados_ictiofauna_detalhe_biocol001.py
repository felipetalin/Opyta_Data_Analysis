from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_ID = 206
PROJECT_CODE = "BIOCOL001"
GROUP = "Ictiofauna"

ANALYSIS_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data_Analysis")
BIOS_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios")
PROJECT_ROOT = (
    ANALYSIS_ROOT
    / "outputs"
    / "_project_scripts"
    / "BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider"
)
INVENTORY_DIR = PROJECT_ROOT / "inventory"
SQL_DIR = PROJECT_ROOT / "sql"


def _load_env() -> None:
    for env_path in [
        ANALYSIS_ROOT / ".env",
        Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env"),
    ]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _engine():
    _load_env()
    url = os.getenv("FISICO_DB_URL") or os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("FISICO_DB_URL/DATABASE_URL/SUPABASE_DB_URL nao encontrado.")
    return create_engine(url + ("&" if "?" in url else "?") + "connect_timeout=20", pool_pre_ping=True)


def _find_one(pattern: str) -> Path:
    matches = list(BIOS_ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return sorted(matches, key=lambda path: path.stat().st_mtime, reverse=True)[0]


DATA_WORKBOOK = _find_one(
    "*/Planilha/Migracao/Opyta-Bios-Ictio-2026_MIGRACAO_DE DADOS -version 4.xlsx"
)
CAMPAIGN_MAP = INVENTORY_DIR / "de_para_campanhas_biocol001_regra_aprovada.csv"


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _norm_key(value) -> str:
    return _strip_accents(_norm_text(value)).lower()


def _is_missing_token(value) -> bool:
    key = _norm_key(value).replace(".", "").replace("-", "")
    return key in {"", "na", "nan", "none", "null", "ni", "n/i", "nao informado"}


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False).str.strip(),
        errors="coerce",
    )


def _sexo_padronizado(value) -> str | None:
    if _is_missing_token(value):
        return None
    txt = _norm_key(value)
    if txt in {"f", "femea", "fem", "female"}:
        return "F"
    if txt in {"m", "macho", "male"}:
        return "M"
    if txt in {"nd", "indeterminado", "nao determinado"}:
        return "ND"
    if txt in {"j", "juvenil"}:
        return "J"
    return _norm_text(value)


def _emg_codigo(value, sexo_value=None) -> str | None:
    if _is_missing_token(value):
        return None
    txt = _strip_accents(_norm_text(value)).upper().replace(" ", "")
    if not txt:
        return None
    match = re.search(r"([FM])\s*([1-4])", txt)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    match = re.search(r"(^|[^0-9])([1-4])([^0-9]|$)", txt)
    if match:
        sexo_txt = _sexo_padronizado(sexo_value)
        prefix = sexo_txt if sexo_txt in {"F", "M"} else ""
        return f"{prefix}{match.group(2)}" if prefix else match.group(2)
    return txt


def _emg_estadio(code: str | None) -> str | None:
    if not code:
        return None
    stage = str(code)[-1]
    return {
        "1": "Repouso",
        "2": "Maturacao inicial",
        "3": "Maturacao avancada/maduro",
        "4": "Desovado/esgotado",
    }.get(stage, "Nao classificado")


def _emg_ordem(code: str | None) -> float:
    if not code:
        return np.nan
    stage = str(code)[-1]
    return float(stage) if stage in {"1", "2", "3", "4"} else np.nan


def _campanha_operacional(value) -> str:
    match = re.search(r"(C\d{3})", _norm_text(value))
    return match.group(1) if match else ""


def _prepare_source() -> pd.DataFrame:
    campaign_map = pd.read_csv(CAMPAIGN_MAP)
    df = pd.read_excel(DATA_WORKBOOK, sheet_name="Resultados_Ictiofauna").dropna(how="all")
    df = df.copy()
    df.insert(0, "linha_fonte", np.arange(2, len(df) + 2))

    for col in ["Ponto", "Campanha", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]:
        df[col] = df[col].map(_norm_text)

    df = df[df["Nome_Cientifico"].ne("")].copy()
    df["campanha_operacional"] = df["Campanha"].map(_campanha_operacional)
    df = df.merge(
        campaign_map[["campanha_operacional", "rotulo_canonico"]],
        on="campanha_operacional",
        how="left",
    )
    df["campanha_canonica"] = df["rotulo_canonico"].fillna(df["Campanha"])

    df["numero_de_individuos"] = _to_number(df["Numero_de_individuos"]).fillna(0)
    df["ct_cm"] = _to_number(df["CT_cm"])
    df["cp_cm"] = _to_number(df["CP_cm"])
    df["pc_g"] = _to_number(df["PC_g"])
    df["sexo_raw"] = df["Sexo"].map(_norm_text)
    df["emg_raw"] = df["EMG"].map(_norm_text)
    df["sexo_padronizado"] = df["sexo_raw"].map(_sexo_padronizado)
    df["emg_codigo"] = [
        _emg_codigo(emg, sexo)
        for emg, sexo in zip(df["emg_raw"], df["sexo_raw"], strict=False)
    ]
    df["emg_estadio"] = df["emg_codigo"].map(_emg_estadio)
    df["emg_ordem"] = df["emg_codigo"].map(_emg_ordem)
    df["evidencia_reprodutiva_forte"] = df["emg_codigo"].isin({"F3", "M3", "F4", "M4"})
    df["species_key"] = df["Nome_Cientifico"].map(_norm_key)
    df["effort_key"] = (
        df["campanha_canonica"].map(_norm_text)
        + "|"
        + df["Ponto"].map(_norm_text)
        + "|"
        + df["Metodo_de_Captura"].map(_norm_text)
    )
    return df


def _ensure_schema(conn) -> None:
    ddl = (SQL_DIR / "proposta_resultados_ictiofauna_detalhe.sql").read_text(encoding="utf-8")
    conn.execute(text(ddl))


def main() -> None:
    run_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_table = f"bkp_biocol001_detail_{run_tag}"
    stage_file = INVENTORY_DIR / f"staging_resultados_ictiofauna_detalhe_biocol001_{run_tag}.csv"
    audit_file = INVENTORY_DIR / f"auditoria_resultados_ictiofauna_detalhe_biocol001_{run_tag}.csv"

    source = _prepare_source()
    engine = _engine()

    with engine.begin() as conn:
        _ensure_schema(conn)

        effort = pd.read_sql(
            text(
                """
                SELECT ea.id_esforco, c.nome_campanha, pc.nome_ponto, ea.metodo_de_captura
                FROM esforcos_amostragem ea
                JOIN pontos_coleta pc ON pc.id_ponto_coleta = ea.id_ponto_coleta
                JOIN campanhas c ON c.id_campanha = pc.id_campanha
                WHERE pc.id_projeto = :pid AND ea.grupo_biologico = :grupo
                """
            ),
            conn,
            params={"pid": PROJECT_ID, "grupo": GROUP},
        )
        species = pd.read_sql(
            text("SELECT id_especie, nome_cientifico FROM especies WHERE grupo_biologico = :grupo"),
            conn,
            params={"grupo": GROUP},
        )
        results = pd.read_sql(
            text(
                """
                SELECT r.id_resultado_ictio, r.id_esforco, r.id_especie
                FROM resultados_ictiofauna r
                JOIN esforcos_amostragem ea ON ea.id_esforco = r.id_esforco
                JOIN pontos_coleta pc ON pc.id_ponto_coleta = ea.id_ponto_coleta
                WHERE pc.id_projeto = :pid AND ea.grupo_biologico = :grupo
                """
            ),
            conn,
            params={"pid": PROJECT_ID, "grupo": GROUP},
        )

        effort["effort_key"] = (
            effort["nome_campanha"].map(_norm_text)
            + "|"
            + effort["nome_ponto"].map(_norm_text)
            + "|"
            + effort["metodo_de_captura"].map(_norm_text)
        )
        species["species_key"] = species["nome_cientifico"].map(_norm_key)

        stage = source.merge(effort[["id_esforco", "effort_key"]], on="effort_key", how="left")
        stage = stage.merge(species[["id_especie", "species_key"]], on="species_key", how="left")
        if stage["id_esforco"].isna().any() or stage["id_especie"].isna().any():
            stage.to_csv(stage_file, index=False, encoding="utf-8-sig")
            raise RuntimeError(f"Mapeamento incompleto. Staging salvo em {stage_file}")

        stage["id_esforco"] = stage["id_esforco"].astype(int)
        stage["id_especie"] = stage["id_especie"].astype(int)
        stage = stage.merge(results, on=["id_esforco", "id_especie"], how="left")
        if stage["id_resultado_ictio"].isna().any():
            stage.to_csv(stage_file, index=False, encoding="utf-8-sig")
            raise RuntimeError(f"Resultado agregado ausente. Staging salvo em {stage_file}")
        stage["id_resultado_ictio"] = stage["id_resultado_ictio"].astype(int)

        existing_count = conn.execute(
            text(
                """
                SELECT count(*)
                FROM public.resultados_ictiofauna_detalhe
                WHERE codigo_opyta = :code
                """
            ),
            {"code": PROJECT_CODE},
        ).scalar_one()
        if existing_count:
            conn.execute(
                text(
                    f"""
                    CREATE TABLE public.{backup_table} AS
                    SELECT *
                    FROM public.resultados_ictiofauna_detalhe
                    WHERE codigo_opyta = :code
                    """
                ),
                {"code": PROJECT_CODE},
            )

        conn.execute(
            text("DELETE FROM public.resultados_ictiofauna_detalhe WHERE codigo_opyta = :code"),
            {"code": PROJECT_CODE},
        )

        load = pd.DataFrame(
            {
                "id_resultado_ictio": stage["id_resultado_ictio"],
                "id_esforco": stage["id_esforco"],
                "id_especie": stage["id_especie"],
                "codigo_opyta": PROJECT_CODE,
                "linha_fonte": stage["linha_fonte"].astype(int),
                "ponto": stage["Ponto"],
                "campanha": stage["campanha_canonica"],
                "metodo_de_captura": stage["Metodo_de_Captura"],
                "tipo_de_amostragem": stage["Tipo_de_Amostragem"],
                "malha_ou_anzol": stage["Malha_ou_Anzol"].map(_norm_text),
                "numero_de_individuos": stage["numero_de_individuos"],
                "ct_cm": stage["ct_cm"],
                "cp_cm": stage["cp_cm"],
                "pc_g": stage["pc_g"],
                "sexo_raw": stage["sexo_raw"],
                "sexo_padronizado": stage["sexo_padronizado"],
                "emg_raw": stage["emg_raw"],
                "emg_codigo": stage["emg_codigo"],
                "emg_estadio": stage["emg_estadio"],
                "emg_ordem": stage["emg_ordem"],
                "evidencia_reprodutiva_forte": stage["evidencia_reprodutiva_forte"],
                "observacao_individuo_lote": stage["Observacoes_Coleta"].map(_norm_text),
                "source_workbook": str(DATA_WORKBOOK),
                "source_sheet": "Resultados_Ictiofauna",
            }
        )
        load.to_csv(stage_file, index=False, encoding="utf-8-sig")
        load.to_sql(
            "resultados_ictiofauna_detalhe",
            conn,
            schema="public",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )

        audit = pd.read_sql(
            text(
                """
                SELECT
                    count(*) AS linhas,
                    coalesce(sum(numero_de_individuos), 0) AS individuos,
                    count(distinct id_especie) AS especies,
                    count(distinct campanha) AS campanhas,
                    count(distinct ponto) AS pontos,
                    count(*) FILTER (WHERE cp_cm IS NOT NULL) AS linhas_cp,
                    count(*) FILTER (WHERE pc_g IS NOT NULL) AS linhas_pc,
                    count(*) FILTER (WHERE sexo_padronizado IN ('F', 'M')) AS linhas_sexo_fm,
                    count(*) FILTER (WHERE emg_codigo IS NOT NULL) AS linhas_emg,
                    count(*) FILTER (WHERE evidencia_reprodutiva_forte) AS linhas_evidencia_forte,
                    coalesce(sum(numero_de_individuos) FILTER (WHERE evidencia_reprodutiva_forte), 0) AS individuos_evidencia_forte
                FROM public.resultados_ictiofauna_detalhe
                WHERE codigo_opyta = :code
                """
            ),
            conn,
            params={"code": PROJECT_CODE},
        )
        audit.to_csv(audit_file, index=False, encoding="utf-8-sig")

    print(f"source_workbook={DATA_WORKBOOK}")
    print(f"linhas_carregadas={len(load)}")
    print(f"backup_table={backup_table if existing_count else 'nao_aplicavel_sem_dados_previos'}")
    print(f"stage_file={stage_file}")
    print(f"audit_file={audit_file}")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
