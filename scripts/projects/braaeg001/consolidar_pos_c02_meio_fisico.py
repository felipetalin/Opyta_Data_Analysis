from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

SOURCE_MIGRATOR = ROOT / "scripts" / "projects" / "braaeg001" / "preparar_migracao_controlada_meio_fisico.py"
spec = importlib.util.spec_from_file_location("braaeg001_preparar_migracao_controlada_meio_fisico", SOURCE_MIGRATOR)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Nao foi possivel carregar {SOURCE_MIGRATOR}")
mf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mf)

PROJECT_CODE = "BRAAEG001"
ENV_FILE = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")
CLIENT_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
PROJECT_DIR = next(path for path in CLIENT_ROOT.iterdir() if path.name.startswith("A&G"))
OUTPUT_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "migracao" / "consolidacao_pos_c02"
LOG_DIR = ROOT / "logs" / "validacao_meio_fisico"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def fetch_rows() -> pd.DataFrame:
    client = mf.RestClient(ENV_FILE)
    rows = client.get(
        "fisico_analise_consolidada",
        "select=*&codigo_interno_opyta=eq.BRAAEG001&order=matriz.asc,nome_campanha.asc,nome_ponto.asc,nome_parametro.asc",
        page_size=1000,
    )
    return pd.DataFrame(rows)


def add_order_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    matrix_order = {"Água Superficial": 1, "Agua Superficial": 1, "Água Subterrânea": 2, "Agua Subterranea": 2, "Sedimento": 3}
    out["_ordem_matriz"] = out["matriz"].map(lambda value: matrix_order.get(clean_text(value), 99))
    out["_ordem_ponto"] = out["nome_ponto"].map(lambda value: int(clean_text(value).split("_")[-1]) if clean_text(value).split("_")[-1].isdigit() else 999)
    return out.sort_values(["_ordem_matriz", "nome_campanha", "_ordem_ponto", "nome_parametro"]).drop(columns=["_ordem_matriz", "_ordem_ponto"])


def count_vmp(row: pd.Series) -> int:
    vmp_cols = [col for col in row.index if col.startswith("vmp_")]
    return sum(1 for col in vmp_cols if clean_text(row[col]) != "")


def build_summary(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    grain = ["codigo_interno_opyta", "nome_campanha", "nome_ponto", "matriz", "nome_parametro", "laboratorio_responsavel"]
    duplicates = df[df.duplicated(subset=grain, keep=False)].sort_values(grain)

    summary = pd.DataFrame(
        [
            {"Metrica": "registros_consolidados", "Valor": len(df)},
            {"Metrica": "campanhas", "Valor": df["nome_campanha"].nunique()},
            {"Metrica": "matrizes", "Valor": df["matriz"].nunique()},
            {"Metrica": "pontos", "Valor": df["nome_ponto"].nunique()},
            {"Metrica": "parametros", "Valor": df["nome_parametro"].nunique()},
            {"Metrica": "duplicidades_grao_tecnico", "Valor": len(duplicates)},
            {"Metrica": "valores_numericos_nulos", "Valor": int(df["valor_medido"].isna().sum())},
            {"Metrica": "registros_com_sinal_limite", "Valor": int(df["sinal_limite"].notna().sum())},
            {"Metrica": "registros_com_algum_vmp", "Valor": int(df.apply(count_vmp, axis=1).gt(0).sum())},
            {"Metrica": "observacao", "Valor": "Tabela fisico_analise_consolidada nao possui campo Curso_d_Agua; pendencia permanece para produtos integrados."},
        ]
    )

    by_matrix_campaign = (
        df.groupby(["matriz", "nome_campanha"], dropna=False)
        .agg(
            registros=("nome_parametro", "size"),
            pontos=("nome_ponto", "nunique"),
            parametros=("nome_parametro", "nunique"),
            sinais_limite=("sinal_limite", lambda values: int(values.notna().sum())),
            valores_numericos_nulos=("valor_medido", lambda values: int(values.isna().sum())),
        )
        .reset_index()
        .sort_values(["matriz", "nome_campanha"])
    )

    by_point = (
        df.groupby(["matriz", "nome_campanha", "nome_ponto"], dropna=False)
        .agg(
            registros=("nome_parametro", "size"),
            parametros=("nome_parametro", "nunique"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            bacia_hidrografica=("bacia_hidrografica", "first"),
        )
        .reset_index()
        .sort_values(["matriz", "nome_campanha", "nome_ponto"])
    )

    surface = df[df["matriz"].isin(["Água Superficial", "Agua Superficial"])].copy()
    surface_coverage = (
        surface.groupby(["nome_ponto", "nome_parametro"], dropna=False)["nome_campanha"]
        .agg(lambda values: " | ".join(sorted(set(clean_text(value) for value in values if clean_text(value)))))
        .reset_index(name="campanhas_presentes")
    )
    expected_campaigns = {"C001-2026-02-CH", "C002-2026-06-SC"}
    surface_coverage["cobertura_c01_c02"] = surface_coverage["campanhas_presentes"].map(
        lambda value: "completa" if set(value.split(" | ")) == expected_campaigns else "incompleta"
    )

    signs = (
        df.assign(sinal_limite=df["sinal_limite"].fillna("sem_sinal"))
        .groupby(["matriz", "nome_campanha", "sinal_limite"], dropna=False)
        .size()
        .reset_index(name="registros")
        .sort_values(["matriz", "nome_campanha", "sinal_limite"])
    )

    return {
        "Resumo": summary,
        "Por_Matriz_Campanha": by_matrix_campaign,
        "Por_Ponto": by_point,
        "Cobertura_AS_C01_C02": surface_coverage,
        "Duplicidades": duplicates,
        "Sinais_Limite": signs,
    }


def write_workbook(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    mf.style_workbook(path)


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    df = fetch_rows()
    if df.empty:
        raise RuntimeError("Nenhum registro BRAAEG001 encontrado em fisico_analise_consolidada.")
    df = add_order_columns(df)
    summaries = build_summary(df)
    consolidated_path = OUTPUT_DIR / f"{ts}_consolidado_meio_fisico_braaeg001_pos_c02.xlsx"
    audit_path = OUTPUT_DIR / f"{ts}_auditoria_consolidacao_meio_fisico_braaeg001_pos_c02.xlsx"
    write_workbook(consolidated_path, {"fisico_analise_consolidada": df})
    write_workbook(audit_path, summaries)

    summary_counter = Counter({row["Metrica"]: row["Valor"] for _, row in summaries["Resumo"].iterrows()})
    manifest = {
        "timestamp": ts,
        "status": "CONSOLIDATED",
        "project_code": PROJECT_CODE,
        "consolidated_xlsx": str(consolidated_path),
        "audit_xlsx": str(audit_path),
        "records": int(summary_counter["registros_consolidados"]),
        "campaigns": int(summary_counter["campanhas"]),
        "matrices": int(summary_counter["matrizes"]),
        "points": int(summary_counter["pontos"]),
        "parameters": int(summary_counter["parametros"]),
        "duplicates": int(summary_counter["duplicidades_grao_tecnico"]),
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{ts}_consolidacao_meio_fisico_braaeg001_pos_c02.json"
    log_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"STATUS={manifest['status']}")
    print(f"CONSOLIDADO={consolidated_path}")
    print(f"AUDITORIA={audit_path}")
    print(f"LOG={log_path}")
    print(json.dumps({k: manifest[k] for k in ["records", "campaigns", "matrices", "points", "parameters", "duplicates"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
