from __future__ import annotations

import math
import re
import shutil
import sys
import unicodedata
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from opyta_analysis.config import load_theme
import opyta_analysis.pipelines.diagnostico.ictio as ictio_mod
from core.engine import get_engine


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
    return df


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
        df_projeto=df_observed, group=group, output_dir=output_dir, generated_files=generated_files
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
        df_projeto=df_observed, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files
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


def _fmt(value: float, decimals: int) -> str:
    if decimals == 0:
        return str(int(round(value)))
    return f"{float(value):.{decimals}f}"


def _plot_point_metric(data: pd.DataFrame, value_col: str, ylabel: str, out_png: Path, decimals: int) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 18,
            "axes.labelsize": 23,
            "xtick.labelsize": 20,
            "ytick.labelsize": 20,
            "figure.dpi": 120,
        }
    )
    x = np.arange(len(data))
    values = data[value_col].astype(float).to_numpy()
    colors = [AREA_COLORS.get(area, AREA_COLORS[AREA_01]) for area in data["area_controle"]]

    fig, ax = plt.subplots(figsize=(15.8, 7.8))
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
            fontsize=18,
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
        fontsize=22,
        color=AREA_COLORS[AREA_01],
    )
    ax.text(
        len(AC01_POINTS) + (len(AC02_POINTS) - 1) / 2,
        -0.13,
        AREA_02,
        transform=trans,
        ha="center",
        va="top",
        fontsize=22,
        color=AREA_COLORS[AREA_02],
    )

    fig.subplots_adjust(left=0.09, right=0.99, top=0.965, bottom=0.24)
    fig.savefig(out_png, dpi=600, bbox_inches="tight")
    plt.close(fig)


def _write_final_point_outputs(out_dir: Path, campaign: str, folder: str) -> pd.DataFrame:
    metrics = _build_final_point_metrics(out_dir, campaign, folder)

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
        _plot_point_metric(metrics, col, ylabel, out_dir / filename, decimals)
    return metrics


def main() -> int:
    theme = load_theme(ROOT / "configs", CLIENT)
    BASE_OUT.mkdir(parents=True, exist_ok=True)

    df_all = _load_df_from_sql()
    if df_all.empty:
        print("[ERRO] Sem dados carregados para Ictiofauna projeto 9.")
        return 1

    df_esf = _load_esforcos_quantitativos()

    for folder, campaign in CAMPAIGNS.items():
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
        metrics = _write_final_point_outputs(out_dir, campaign, folder)
        print(
            f"[ok] {campaign} -> {out_dir} | arquivos pipeline: {len(details.get('generated_files', []))} | "
            f"pontos finais: {len(metrics)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
