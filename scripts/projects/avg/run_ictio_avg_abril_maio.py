from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
import tempfile
import unicodedata
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text


ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from opyta_analysis.config import load_theme
import opyta_analysis.pipelines.diagnostico.ictio as ictio_mod
from core.engine import get_engine


CONFIG_PATH = ROOT / "configs" / "projects" / "braavg002_ictiofauna_2026.json"
PROJECT_ID = 9
GROUP = "Ictiofauna"
CLIENT = "braavg002"
BASE_OUT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados ictio\2026"
)

CAMPAIGNS = {
    "abril": "45\u00aa-Abr-26",
    "maio": "46\u00aa-Mai-26",
    "junho": "47\u00aa-Jun-26",
}

AREA_01 = "\u00c1rea de controle 01"
AREA_02 = "\u00c1rea de controle 02"
AC01_POINTS = [
    "PIC-01",
    "PIC-02",
    "PIC-03",
    "PIC-04",
    "PIC-05",
    "PIC-06",
    "PIC-07",
    "PIC-08",
    "PIC-09",
    "PIC-11",
]
AC02_POINTS = ["PIC-10", "PIC-12", "PIC-13"]
POINT_ORDER = AC01_POINTS + AC02_POINTS
AREA_BY_POINT = {p: AREA_01 for p in AC01_POINTS} | {p: AREA_02 for p in AC02_POINTS}

AREA_COLORS = {
    AREA_01: "#16803A",
    AREA_02: "#7FA33A",
}
NOT_SAMPLED_CAMPAIGN_RANGES = {
    "PIC-01": [(40, None)],
    "PIC-02": [(40, 42)],
    "PIC-03": [(40, 42), (44, None)],
    "PIC-11": [(40, None)],
}
GRID_COLOR = "#DDEBD8"
EDGE_COLOR = "#173B23"

MONTHS = {
    "jan": "Jan",
    "janeiro": "Jan",
    "fev": "Fev",
    "fevereiro": "Fev",
    "mar": "Mar",
    "marco": "Mar",
    "mar\u00e7o": "Mar",
    "abr": "Abr",
    "abri": "Abr",
    "abril": "Abr",
    "mai": "Mai",
    "maio": "Mai",
    "jun": "Jun",
    "junho": "Jun",
    "jul": "Jul",
    "julho": "Jul",
    "ago": "Ago",
    "agosto": "Ago",
    "set": "Set",
    "setembro": "Set",
    "out": "Out",
    "outubro": "Out",
    "nov": "Nov",
    "novembro": "Nov",
    "dez": "Dez",
    "dezembro": "Dez",
}


def _json_default(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return str(value)


def _load_recipe(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_recipe(recipe: dict) -> None:
    if not recipe:
        return

    global PROJECT_ID, GROUP, CLIENT, BASE_OUT, CAMPAIGNS
    global AREA_01, AREA_02, AC01_POINTS, AC02_POINTS, POINT_ORDER, AREA_BY_POINT, AREA_COLORS

    PROJECT_ID = int(recipe.get("project_id", PROJECT_ID))
    CLIENT = str(recipe.get("client_config", CLIENT))
    if recipe.get("output_root"):
        BASE_OUT = Path(recipe["output_root"])

    groups = recipe.get("groups") or []
    if groups:
        GROUP = str(groups[0].get("group", GROUP))

    targets = recipe.get("generation", {}).get("targets") or []
    parsed_targets = {}
    for target in targets:
        folder = target.get("folder") or target.get("key")
        campaign = target.get("campaign")
        if folder and campaign:
            parsed_targets[str(folder)] = str(campaign)
    if parsed_targets:
        CAMPAIGNS = parsed_targets

    layout = recipe.get("point_layout") or {}
    control_groups = layout.get("control_groups") or []
    if len(control_groups) >= 2:
        AREA_01 = str(control_groups[0].get("label", AREA_01))
        AREA_02 = str(control_groups[1].get("label", AREA_02))
        AC01_POINTS = [str(point) for point in control_groups[0].get("points", AC01_POINTS)]
        AC02_POINTS = [str(point) for point in control_groups[1].get("points", AC02_POINTS)]
        POINT_ORDER = AC01_POINTS + AC02_POINTS
        AREA_BY_POINT = {p: AREA_01 for p in AC01_POINTS} | {p: AREA_02 for p in AC02_POINTS}

    colors = layout.get("control_area_colors") or {}
    AREA_COLORS = {
        AREA_01: str(colors.get("area_01", colors.get(AREA_01, AREA_COLORS.get(AREA_01, "#16803A")))),
        AREA_02: str(colors.get("area_02", colors.get(AREA_02, AREA_COLORS.get(AREA_02, "#7FA33A")))),
    }


def _selected_campaigns(campaign_key: str | None) -> dict[str, str]:
    if not campaign_key:
        return CAMPAIGNS
    if campaign_key not in CAMPAIGNS:
        choices = ", ".join(sorted(CAMPAIGNS))
        raise RuntimeError(f"Campanha nao cadastrada: {campaign_key}. Opcoes: {choices}")
    return {campaign_key: CAMPAIGNS[campaign_key]}


def _list_campaigns_payload(recipe_path: Path) -> dict:
    return {
        "recipe": recipe_path,
        "project_id": PROJECT_ID,
        "client": CLIENT,
        "group": GROUP,
        "output_root": BASE_OUT,
        "campaigns": [
            {
                "key": folder,
                "campaign": campaign,
                "output_dir": BASE_OUT / folder,
            }
            for folder, campaign in CAMPAIGNS.items()
        ],
    }


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value).replace("\xa0", " ").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def canonical_campaign(value: object) -> str:
    raw = "" if value is None or pd.isna(value) else str(value).strip()
    text = _norm(raw).replace("Âª", "a").replace("Âº", "o").replace("Â°", "o")
    match = re.match(r"^\s*(\d+)\s*(?:a|o)?[\s._-]*(.*)$", text)
    if not match:
        return raw

    seq = int(match.group(1))
    tokens = [tok for tok in re.split(r"[\s._-]+", match.group(2)) if tok]
    month = None
    year2 = None
    for token in tokens:
        if token in MONTHS:
            month = MONTHS[token]
        elif re.fullmatch(r"\d{2,4}", token):
            year2 = int(token) % 100
    if month is None or year2 is None:
        return raw
    return f"{seq}\u00aa-{month}-{year2:02d}"


def _campaign_seq(value: object) -> int | None:
    match = re.match(r"^\s*(\d+)", canonical_campaign(value))
    return int(match.group(1)) if match else None


def apply_sampling_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    """Remove ponto-campanha definido como nao amostrado da camada analitica."""
    if df.empty or "nome_campanha" not in df.columns or "nome_ponto" not in df.columns:
        return df
    out = df.copy()
    seq = out["nome_campanha"].map(_campaign_seq)
    point = out["nome_ponto"].astype(str).str.strip()
    remove = pd.Series(False, index=out.index)
    for point_name, ranges in NOT_SAMPLED_CAMPAIGN_RANGES.items():
        for first_seq, last_seq in ranges:
            in_range = seq >= first_seq
            if last_seq is not None:
                in_range &= seq <= last_seq
            remove |= (point == point_name) & in_range
    return out.loc[~remove].copy()


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def _load_df_from_sql() -> pd.DataFrame:
    engine = get_engine()
    try:
        query = text(
            """
            SELECT *
            FROM biota_analise_consolidada
            WHERE codigo_interno_opyta = :codigo
              AND grupo_biologico ILIKE :grupo
            """
        )
        df = pd.read_sql(query, engine, params={"codigo": "BRAAVG002", "grupo": "%Ictio%"})
    finally:
        engine.dispose()

    if df.empty:
        return df

    if "contagem" in df.columns:
        df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    if "biomassa" in df.columns:
        df["biomassa"] = pd.to_numeric(df["biomassa"], errors="coerce").fillna(0)
    if "esforco" in df.columns:
        df["esforco"] = pd.to_numeric(df["esforco"], errors="coerce")

    for col in [
        "nome_campanha",
        "nome_ponto",
        "nome_cientifico",
        "tipo_amostragem",
        "ordem",
        "familia",
    ]:
        if col in df.columns:
            df[col] = df[col].map(_clean_text)

    df["nome_campanha"] = df["nome_campanha"].map(canonical_campaign)
    return df


def _load_esforcos_quantitativos() -> pd.DataFrame:
    """Carrega esforcos quantitativos de Ictiofauna do projeto 9."""
    engine = get_engine()
    try:
        query = text(
            """
            SELECT
                c.nome_campanha,
                p.nome_ponto,
                e.tipo_amostragem,
                e.esforco
            FROM esforcos_amostragem e
            JOIN pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            JOIN campanhas c ON c.id_campanha = p.id_campanha
            WHERE p.id_projeto = :pid
              AND e.grupo_biologico = :grupo
            """
        )
        df = pd.read_sql(query, engine, params={"pid": PROJECT_ID, "grupo": GROUP})
    finally:
        engine.dispose()

    if df.empty:
        return df

    df["nome_campanha"] = df["nome_campanha"].map(canonical_campaign)
    df["nome_ponto"] = df["nome_ponto"].map(_clean_text)
    df["tipo_amostragem"] = df["tipo_amostragem"].map(_clean_text)
    df["esforco"] = pd.to_numeric(df["esforco"], errors="coerce")
    tipo_norm = df["tipo_amostragem"].map(_norm)
    df = df[tipo_norm.str.startswith("quanti")].copy()
    df = df[df["esforco"].notna() & (df["esforco"] > 0)].copy()
    df = df.groupby(["nome_campanha", "nome_ponto"], as_index=False)["esforco"].sum()
    df["tipo_amostragem"] = "Quantitativo"
    return apply_sampling_adjustments(df)


def _pad_zero_catch(df_camp: pd.DataFrame, df_esf_camp: pd.DataFrame) -> pd.DataFrame:
    """Adiciona linhas placeholder para pontos com esforco e captura zero."""
    if df_esf_camp.empty:
        return df_camp
    obs_pts = set(df_camp["nome_ponto"].dropna().astype(str).str.strip().unique())
    missing = df_esf_camp[~df_esf_camp["nome_ponto"].isin(obs_pts)].copy()
    if missing.empty:
        return df_camp

    pad_rows = []
    template = df_camp.iloc[0].to_dict() if not df_camp.empty else {}
    for _, r in missing.iterrows():
        row = {k: None for k in df_camp.columns}
        for k, v in template.items():
            if k in {"codigo_interno_opyta", "grupo_biologico", "id_projeto", "nome_projeto"}:
                row[k] = v
        row["nome_campanha"] = r["nome_campanha"]
        row["nome_ponto"] = r["nome_ponto"]
        row["tipo_amostragem"] = "Quantitativo"
        row["esforco"] = float(r["esforco"])
        row["contagem"] = 0
        row["biomassa"] = 0
        row["nome_cientifico"] = None
        pad_rows.append(row)
    df_pad = pd.DataFrame(pad_rows, columns=df_camp.columns)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=FutureWarning,
            message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated.*",
        )
        return pd.concat([df_camp, df_pad], ignore_index=True)


def _summarize_campaign_preflight(
    df_all: pd.DataFrame,
    df_esf: pd.DataFrame,
    folder: str,
    campaign: str,
) -> dict:
    out_dir = BASE_OUT / folder
    df_c = df_all[df_all["nome_campanha"] == campaign].copy()
    if df_c.empty:
        return {
            "key": folder,
            "campaign": campaign,
            "status": "missing_in_consolidated",
            "output_dir": out_dir,
            "available_campaigns": sorted(df_all["nome_campanha"].dropna().astype(str).unique().tolist()),
        }

    if not df_esf.empty:
        df_esf_c = df_esf[df_esf["nome_campanha"] == campaign].copy()
    else:
        df_esf_c = df_esf
    df_point_metrics = _pad_zero_catch(df_c, df_esf_c)

    counts = pd.to_numeric(df_c.get("contagem", 0), errors="coerce").fillna(0)
    biomass_col = "biomassa_total_analitica" if "biomassa_total_analitica" in df_c.columns else "biomassa"
    biomass = pd.to_numeric(df_c.get(biomass_col, 0), errors="coerce").fillna(0)
    observed_points = sorted(df_c["nome_ponto"].dropna().astype(str).unique().tolist())
    effort_points = sorted(df_esf_c["nome_ponto"].dropna().astype(str).unique().tolist()) if not df_esf_c.empty else []
    zero_capture_points = [point for point in POINT_ORDER if point in effort_points and point not in observed_points]
    existing_files = [p for p in out_dir.iterdir() if p.name.lower() != "desktop.ini"] if out_dir.exists() else []

    return {
        "key": folder,
        "campaign": campaign,
        "status": "ready",
        "output_dir": out_dir,
        "output_dir_exists": out_dir.exists(),
        "existing_files": len(existing_files),
        "records_observed": int(len(df_c)),
        "records_with_zero_points": int(len(df_point_metrics)),
        "points_expected": POINT_ORDER,
        "points_observed": observed_points,
        "points_with_effort": effort_points,
        "zero_capture_points_with_effort": zero_capture_points,
        "taxa": int(df_c["nome_cientifico"].dropna().astype(str).str.strip().replace("", np.nan).nunique()),
        "abundance_total": float(counts.sum()),
        "biomass_total": float(biomass.sum()),
    }


def _run_preflight(selected_campaigns: dict[str, str], recipe_path: Path) -> dict:
    df_all = _load_df_from_sql()
    if df_all.empty:
        raise RuntimeError("Sem dados carregados para Ictiofauna projeto 9.")
    df_esf = _load_esforcos_quantitativos()
    campaign_results = [
        _summarize_campaign_preflight(df_all, df_esf, folder, campaign)
        for folder, campaign in selected_campaigns.items()
    ]
    return {
        "mode": "preflight",
        "recipe": recipe_path,
        "project_id": PROJECT_ID,
        "client": CLIENT,
        "group": GROUP,
        "output_root": BASE_OUT,
        "campaign_results": campaign_results,
        "ready": all(result["status"] == "ready" for result in campaign_results),
    }


def _clean_output_dir(out_dir: Path) -> None:
    resolved_base = BASE_OUT.resolve()
    resolved_dir = out_dir.resolve()
    if resolved_dir.parent != resolved_base or resolved_dir.name not in CAMPAIGNS:
        raise RuntimeError(f"Recusando limpar pasta fora do alvo AVG: {resolved_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    for item in out_dir.iterdir():
        if item.name.lower() == "desktop.ini":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def _run_blocks_for_df(df_observed: pd.DataFrame, df_point_metrics: pd.DataFrame, group: str, theme: dict, output_dir: Path) -> dict:
    generated_files: list[str] = []
    details: dict = {
        "rows_loaded": int(len(df_observed)),
        "rows_loaded_with_zero_points": int(len(df_point_metrics)),
        "group": group,
        "campaigns": sorted(df_observed["nome_campanha"].dropna().astype(str).unique().tolist())
        if "nome_campanha" in df_observed.columns
        else [],
        "points": sorted(df_point_metrics["nome_ponto"].dropna().astype(str).unique().tolist())
        if "nome_ponto" in df_point_metrics.columns
        else [],
    }

    details["block_3"] = ictio_mod._run_block_3(
        df_projeto=df_observed, group=group, output_dir=output_dir, generated_files=generated_files
    )
    details["block_4"] = ictio_mod._run_block_4(
        df_projeto=df_observed, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_5"] = ictio_mod._run_block_5(
        df_projeto=df_point_metrics, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_6"] = ictio_mod._run_block_6(
        df_projeto=df_point_metrics, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_7"] = ictio_mod._run_block_7(
        df_projeto=df_observed, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_8"] = ictio_mod._run_block_8(
        df_projeto=df_point_metrics, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_9"] = ictio_mod._run_block_9(
        df_projeto=df_observed, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_10"] = ictio_mod._run_block_10(
        df_projeto=df_observed, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_11"] = ictio_mod._run_block_11(
        df_projeto=df_observed, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_12"] = ictio_mod._run_block_12(
        df_projeto=df_point_metrics, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
    )
    details["block_13"] = ictio_mod._run_block_13(
        df_projeto=df_observed, group=group, output_dir=output_dir, generated_files=generated_files
    )

    details["executed_blocks"] = ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]
    details["generated_files"] = generated_files
    return details


def _point_frame(campaign: str) -> pd.DataFrame:
    out = pd.DataFrame({"nome_ponto": POINT_ORDER})
    out["nome_campanha"] = campaign
    out["area_controle"] = out["nome_ponto"].map(AREA_BY_POINT)
    out["ordem_ponto"] = range(1, len(out) + 1)
    return out


def _read_table(path: Path, campaign: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    if "nome_campanha" in df.columns:
        df["nome_campanha"] = df["nome_campanha"].map(canonical_campaign)
        df = df[df["nome_campanha"] == campaign].copy()
    if "nome_ponto" in df.columns:
        df["nome_ponto"] = df["nome_ponto"].map(_clean_text)
    return df


def _validate_same_abundance(abundance: pd.DataFrame, cpue: pd.DataFrame, folder: str) -> None:
    check = abundance[["nome_ponto", "abundancia_total"]].merge(
        cpue[["nome_ponto", "abundancia_total"]],
        on="nome_ponto",
        how="outer",
        suffixes=("_abundancia", "_cpue"),
    )
    left = pd.to_numeric(check["abundancia_total_abundancia"], errors="coerce").fillna(0)
    right = pd.to_numeric(check["abundancia_total_cpue"], errors="coerce").fillna(0)
    mismatches = check.loc[~np.isclose(left, right), "nome_ponto"].tolist()
    if mismatches:
        raise RuntimeError(f"{folder}: abundancia diverge entre 03_df e 06_df em {mismatches}")


def _build_final_point_metrics(out_dir: Path, campaign: str, folder: str) -> pd.DataFrame:
    richness = _read_table(out_dir / "02_df_riqueza_por_ponto_ictiofauna.xlsx", campaign)[
        ["nome_ponto", "riqueza"]
    ].copy()
    abundance = _read_table(out_dir / "03_df_abundancia_por_ponto_ictiofauna.xlsx", campaign)[
        ["nome_ponto", "abundancia_total"]
    ].copy()
    cpue = _read_table(out_dir / "06_df_cpue_por_ponto_ictiofauna.xlsx", campaign)[
        [
            "nome_ponto",
            "abundancia_total",
            "biomassa_total",
            "esforco_total_ponto",
            "unidades_esforco",
            "cpuen",
            "cpueb",
        ]
    ].copy()

    _validate_same_abundance(abundance, cpue, folder)
    cpue = cpue.drop(columns=["abundancia_total"])
    data = (
        _point_frame(campaign)
        .merge(richness, on="nome_ponto", how="left")
        .merge(abundance, on="nome_ponto", how="left")
        .merge(cpue, on="nome_ponto", how="left")
    )

    numeric_cols = [
        "riqueza",
        "abundancia_total",
        "biomassa_total",
        "esforco_total_ponto",
        "unidades_esforco",
        "cpuen",
        "cpueb",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)
    return data.sort_values("ordem_ponto").reset_index(drop=True)


def _build_final_point_metrics_from_frame(df_point_metrics: pd.DataFrame, campaign: str) -> pd.DataFrame:
    df = df_point_metrics.copy()
    df["nome_campanha"] = df["nome_campanha"].map(canonical_campaign)
    df["nome_ponto"] = df["nome_ponto"].map(_clean_text)
    df["contagem"] = pd.to_numeric(df.get("contagem", 0), errors="coerce").fillna(0)
    df["biomassa"] = pd.to_numeric(df.get("biomassa", 0), errors="coerce").fillna(0)
    df["esforco"] = pd.to_numeric(df.get("esforco", np.nan), errors="coerce")
    df = df[df["nome_campanha"] == campaign].copy()

    valid_taxa = df[(df["contagem"] > 0) & df["nome_cientifico"].notna()].copy()
    valid_taxa = valid_taxa[valid_taxa["nome_cientifico"].astype(str).str.strip() != ""]
    richness = (
        valid_taxa.groupby("nome_ponto", dropna=False)["nome_cientifico"]
        .nunique()
        .reset_index(name="riqueza")
    )
    abundance = (
        df.groupby("nome_ponto", dropna=False)["contagem"]
        .sum()
        .reset_index(name="abundancia_total")
    )

    tipo_norm = df["tipo_amostragem"].astype(str).map(ictio_mod._normalizar_tipo_amostragem)
    df_quant = df[tipo_norm == "quantitativo"].copy()
    df_quant = df_quant[df_quant["esforco"].notna() & (df_quant["esforco"] > 0)].copy()
    if "biomassa_total_analitica" in df_quant.columns:
        df_quant["biomassa_total_analitica"] = pd.to_numeric(
            df_quant["biomassa_total_analitica"], errors="coerce"
        ).fillna(0)
        biomass_col = "biomassa_total_analitica"
    else:
        biomass_col = "biomassa"

    if df_quant.empty:
        cpue = pd.DataFrame(
            columns=[
                "nome_ponto",
                "abundancia_total",
                "biomassa_total",
                "esforco_total_ponto",
                "unidades_esforco",
                "cpuen",
                "cpueb",
            ]
        )
    else:
        totals = (
            df_quant.groupby(["nome_campanha", "nome_ponto"], dropna=False)
            .agg(
                abundancia_total=("contagem", "sum"),
                biomassa_total=(biomass_col, "sum"),
            )
            .reset_index()
        )
        method_cols = [c for c in ["metodo_de_captura", "unidade_esforco"] if c in df_quant.columns]
        dedup_cols = ["nome_campanha", "nome_ponto", *method_cols, "esforco"]
        effort = (
            df_quant[dedup_cols]
            .dropna(subset=["esforco"])
            .drop_duplicates()
            .groupby(["nome_campanha", "nome_ponto"], dropna=False)
            .agg(esforco_total_ponto=("esforco", "sum"), unidades_esforco=("esforco", "size"))
            .reset_index()
        )
        cpue = totals.merge(effort, on=["nome_campanha", "nome_ponto"], how="left")
        cpue = cpue[cpue["esforco_total_ponto"].notna() & (cpue["esforco_total_ponto"] > 0)].copy()
        cpue["cpuen"] = (cpue["abundancia_total"] / cpue["esforco_total_ponto"]) * 100
        cpue["cpueb"] = (cpue["biomassa_total"] / cpue["esforco_total_ponto"]) * 100
        cpue = cpue.drop(columns=["nome_campanha"])

    cpue_for_merge = cpue.drop(columns=["abundancia_total"], errors="ignore")
    data = (
        _point_frame(campaign)
        .merge(richness, on="nome_ponto", how="left")
        .merge(abundance, on="nome_ponto", how="left")
        .merge(cpue_for_merge, on="nome_ponto", how="left")
    )
    numeric_cols = [
        "riqueza",
        "abundancia_total",
        "biomassa_total",
        "esforco_total_ponto",
        "unidades_esforco",
        "cpuen",
        "cpueb",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)
    return data.sort_values("ordem_ponto").reset_index(drop=True)


def _fmt(value: float, decimals: int) -> str:
    if decimals == 0:
        return str(int(round(value)))
    return f"{float(value):.{decimals}f}"


def _theme_int(theme: dict, key: str, default: int) -> int:
    try:
        return int(theme.get(key, default))
    except (TypeError, ValueError):
        return default


def _theme_figsize(theme: dict) -> tuple[float, float]:
    raw = theme.get("figsize_standard", [16, 10])
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        try:
            return float(raw[0]), float(raw[1])
        except (TypeError, ValueError):
            pass
    return 16.0, 10.0


def _plot_point_metric(
    data: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    decimals: int,
    theme: dict,
) -> None:
    base_size = _theme_int(theme, "font_size_base", 21)
    tick_size = _theme_int(theme, "point_label_size", base_size)
    axis_label_size = _theme_int(theme, "label_size", max(base_size, 20))
    annotation_size = _theme_int(theme, "annotation_size", base_size)
    area_label_size = _theme_int(theme, "control_area_label_size", max(tick_size, 22))
    dpi = _theme_int(theme, "dpi", 600)
    plt.rcParams.update(
        {
            "font.family": str(theme.get("font_family", "DejaVu Sans")),
            "font.size": base_size,
            "axes.labelsize": axis_label_size,
            "xtick.labelsize": tick_size,
            "ytick.labelsize": tick_size,
            "figure.dpi": dpi,
        }
    )
    x = np.arange(len(data))
    values = data[value_col].astype(float).to_numpy()
    colors = [AREA_COLORS.get(area, AREA_COLORS[AREA_01]) for area in data["area_controle"]]

    fig, ax = plt.subplots(figsize=_theme_figsize(theme))
    bars = ax.bar(x, values, color=colors, edgecolor=EDGE_COLOR, linewidth=0.9, width=0.68)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(data["nome_ponto"].tolist(), rotation=0, ha="center")
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.9, alpha=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    vmax = float(np.nanmax(values)) if len(values) else 0.0
    upper = max(vmax * 1.25, 1.0 if decimals == 0 else 0.25)
    ax.set_ylim(0, upper)

    for rect, value in zip(bars, values):
        label = _fmt(value, decimals)
        y = value + upper * 0.025 if value > 0 else upper * 0.025
        color = "black" if value > 0 else "#666666"
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            y,
            label,
            ha="center",
            va="bottom",
            fontsize=annotation_size,
            color=color,
        )

    split_after = len(AC01_POINTS) - 0.5
    ax.axvline(split_after, color="#5A6B48", linewidth=1.2, linestyle="--", ymin=0.0, ymax=0.96)
    trans = ax.get_xaxis_transform()
    ax.text(
        (len(AC01_POINTS) - 1) / 2,
        -0.13,
        AREA_01,
        transform=trans,
        ha="center",
        va="top",
        fontsize=area_label_size,
        color=AREA_COLORS[AREA_01],
    )
    ax.text(
        len(AC01_POINTS) + (len(AC02_POINTS) - 1) / 2,
        -0.13,
        AREA_02,
        transform=trans,
        ha="center",
        va="top",
        fontsize=area_label_size,
        color=AREA_COLORS[AREA_02],
    )

    fig.subplots_adjust(left=0.09, right=0.99, top=0.965, bottom=0.24)
    with tempfile.TemporaryDirectory(prefix="avg_ictio_plot_") as tmp_dir:
        tmp_png = Path(tmp_dir) / out_png.name
        fig.savefig(tmp_png, dpi=dpi, bbox_inches="tight")
        shutil.copy2(tmp_png, out_png)
    plt.close(fig)


def _write_final_point_outputs(
    out_dir: Path,
    campaign: str,
    folder: str,
    theme: dict,
    source_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if source_df is None:
        metrics = _build_final_point_metrics(out_dir, campaign, folder)
    else:
        metrics = _build_final_point_metrics_from_frame(source_df, campaign)

    metrics[["nome_campanha", "nome_ponto", "riqueza"]].to_excel(
        out_dir / "02_df_riqueza_por_ponto_ictiofauna.xlsx",
        index=False,
        engine="openpyxl",
    )
    metrics[["nome_campanha", "nome_ponto", "abundancia_total"]].to_excel(
        out_dir / "03_df_abundancia_por_ponto_ictiofauna.xlsx",
        index=False,
        engine="openpyxl",
    )
    metrics[
        [
            "nome_campanha",
            "nome_ponto",
            "abundancia_total",
            "biomassa_total",
            "esforco_total_ponto",
            "unidades_esforco",
            "cpuen",
            "cpueb",
        ]
    ].to_excel(
        out_dir / "06_df_cpue_por_ponto_ictiofauna.xlsx",
        index=False,
        engine="openpyxl",
    )

    specs = [
        ("02_grafico_riqueza_por_ponto_ictiofauna.png", "riqueza", "Riqueza taxon\u00f4mica", 0),
        ("03_grafico_abundancia_por_ponto_ictiofauna.png", "abundancia_total", "Abund\u00e2ncia total (n\u00ba de indiv\u00edduos)", 0),
        ("06_grafico_cpuen_por_ponto_ictiofauna.png", "cpuen", "CPUEn (ind/100m\u00b2)", 2),
        ("07_grafico_cpueb_por_ponto_ictiofauna.png", "cpueb", "CPUEb (g/100m\u00b2)", 2),
    ]
    for filename, col, ylabel, decimals in specs:
        _plot_point_metric(metrics, col, ylabel, out_dir / filename, decimals, theme)
    return metrics


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera resultados parciais de Ictiofauna AVG por campanha.")
    parser.add_argument(
        "--recipe",
        type=Path,
        default=CONFIG_PATH,
        help="Recipe com campanhas, saida e regras de geracao.",
    )
    parser.add_argument(
        "--campaign",
        help="Pasta/campanha cadastrada no recipe. Sem este argumento, usa todas as campanhas cadastradas.",
    )
    parser.add_argument("--list-campaigns", action="store_true", help="Lista alvos cadastrados e nao gera arquivos.")
    parser.add_argument("--preflight", action="store_true", help="Confere dados/saida sem limpar pasta nem gerar produtos.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    recipe = _load_recipe(args.recipe)
    _apply_recipe(recipe)

    if args.list_campaigns:
        print(json.dumps(_list_campaigns_payload(args.recipe), ensure_ascii=False, indent=2, default=_json_default))
        return 0

    try:
        selected_campaigns = _selected_campaigns(args.campaign)
    except RuntimeError as exc:
        print(f"[ERRO] {exc}")
        return 1

    if args.preflight:
        try:
            payload = _run_preflight(selected_campaigns, args.recipe)
        except RuntimeError as exc:
            print(f"[ERRO] {exc}")
            return 1
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
        return 0 if payload["ready"] else 1

    theme = load_theme(ROOT / "configs", CLIENT)
    BASE_OUT.mkdir(parents=True, exist_ok=True)

    df_all = _load_df_from_sql()
    if df_all.empty:
        print("[ERRO] Sem dados carregados para Ictiofauna projeto 9.")
        return 1

    df_esf = _load_esforcos_quantitativos()

    for folder, campaign in selected_campaigns.items():
        out_dir = BASE_OUT / folder
        _clean_output_dir(out_dir)

        df_c = df_all[df_all["nome_campanha"] == campaign].copy()
        if df_c.empty:
            print(f"[ERRO] Campanha nao encontrada: {campaign}")
            return 1
        df_c["nome_campanha"] = campaign

        if not df_esf.empty:
            df_esf_c = df_esf[df_esf["nome_campanha"] == campaign].copy()
        else:
            df_esf_c = df_esf
        df_point_metrics = _pad_zero_catch(df_c, df_esf_c)

        details = _run_blocks_for_df(
            df_observed=df_c,
            df_point_metrics=df_point_metrics,
            group=GROUP,
            theme=theme,
            output_dir=out_dir,
        )
        metrics = _write_final_point_outputs(out_dir, campaign, folder, theme, source_df=df_point_metrics)
        print(
            f"[ok] {campaign} -> {out_dir} | arquivos pipeline: {len(details.get('generated_files', []))} | "
            f"pontos finais: {len(metrics)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
