from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from PIL import Image, ImageDraw
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform


ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from opyta_analysis.pipelines.diagnostico.darwincore_ief import export_darwincore_ief  # noqa: E402
from opyta_analysis.pipelines.diagnostico.fitoplancton import _load_fitoplancton_df  # noqa: E402


PROJECT_CODE = "WSPKIN001"
PROJECT_ID = 211
GROUP = "Fitoplancton"
GROUP_DISPLAY = "Fitoplâncton"
DEFAULT_OUTPUT_DIR = Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/WSP/BAndeirinhas_Kinross/Resultados/Fitoplancton")
OUTPUT_DIR = Path(os.environ.get("WSPKIN001_FITO_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
AUDIT_DIR = ROOT / "outputs" / "_project_scripts" / "WSPKIN001__kinross_bandeirinhas" / "fitoplancton"

DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
PRIMARY = "#11420C"
SECONDARY = "#19FF00"
SECONDARY_DARK = "#6A8F63"
GRID = "#D8E9D4"
PHYLA_COLORS = ["#11420C", "#19FF00", "#6A8F63", "#2A6F97", "#C77D32", "#6D597A", "#4D908E", "#9C6644", "#7A8B99"]

FINAL_FIGURES = [
    "02_grafico_riqueza_por_ponto_fitoplancton.png",
    "03_grafico_densidade_total_por_ponto_fitoplancton.png",
    "04_grafico_riqueza_filo_barras_fitoplancton.png",
    "05_grafico_riqueza_filo_rosca_fitoplancton.png",
    "06_grafico_densidade_filo_por_ponto_fitoplancton.png",
    "07_grafico_densidade_relativa_filo_por_ponto_fitoplancton.png",
    "08_grafico_densidade_por_taxon_fitoplancton.png",
    "09_grafico_densidade_taxon_ponto_fitoplancton.png",
    "10_grafico_diversidade_alfa_fitoplancton.png",
    "11_dendrograma_similaridade_fitoplancton.png",
    "11B_dendrograma_similaridade_pontos_fitoplancton.png",
    "12_curva_suficiencia_amostral_fitoplancton.png",
    "13_mini_mapa_cyanobacteria_fitoplancton.png",
    "14_grafico_sintese_fitoplancton.png",
]

def now_tag() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def setup_rc() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 17,
            "axes.labelsize": 17,
            "xtick.labelsize": 17,
            "ytick.labelsize": 17,
            "legend.fontsize": 17,
            "axes.linewidth": 1.2,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def point_key(point: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", str(point))
    return (int(match.group(1)) if match else 999999, str(point))


def campaign_key(campaign: str) -> tuple[int, str]:
    match = re.match(r"^C0*(\d+)", str(campaign), flags=re.IGNORECASE)
    return (int(match.group(1)) if match else 999999, str(campaign))


def campaign_short(campaign: str) -> str:
    match = re.match(r"^C0*(\d+)", str(campaign).strip(), flags=re.IGNORECASE)
    return f"C{int(match.group(1)):02d}" if match else str(campaign).strip()


def campaign_season(campaign: str) -> str:
    text = str(campaign).upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text) or "CHUVA" in text:
        return "Chuva"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text) or "SECA" in text:
        return "Seca"
    return "Campanha"


def campaign_label(campaign: str) -> str:
    season = campaign_season(campaign)
    base = campaign_short(campaign)
    return f"{base}-{season}" if season != "Campanha" else base


def sample_label(campaign: str, point: str) -> str:
    return f"{campaign_short(campaign)}-{point}"


def is_quantitative(series: pd.Series) -> pd.Series:
    return series.astype(str).str.contains("Quantitativa", case=False, na=False)


def first_valid(series: pd.Series, default: str = "") -> str:
    values = series.dropna().astype(str).str.strip()
    values = values[(values != "") & (values.str.lower() != "nan")]
    return str(values.iloc[0]) if not values.empty else default


def fmt_number(value: float, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return ""
    value = float(value)
    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}"
    return f"{value:.{decimals}f}"


def style_box_axes(ax, *, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.8, color=GRID, alpha=0.95)
    ax.grid(axis="x", visible=False)
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color("black")
        ax.spines[spine].set_linewidth(1.2)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=10)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=10)
    ax.tick_params(axis="both", direction="out")


def save_fig(fig, name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / name
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def ensure_nonempty(df: pd.DataFrame) -> None:
    if df.empty:
        raise RuntimeError("A fatia consolidada de Fitoplâncton retornou vazia.")


def load_data(env_file: str | None = ".env") -> pd.DataFrame:
    df = _load_fitoplancton_df(project_id=PROJECT_ID, group=GROUP, env_file=env_file)
    ensure_nonempty(df)
    df = df.copy()
    for col in ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem", "filo", "classe", "ordem", "familia", "genero"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0.0)
    df["tipo_norm"] = np.where(is_quantitative(df["tipo_amostragem"]), "Quantitativa", "Qualitativa")
    df["campanha_label"] = df["nome_campanha"].map(campaign_label)
    df["amostra_label"] = [sample_label(c, p) for c, p in zip(df["nome_campanha"], df["nome_ponto"])]
    return df.sort_values(["nome_campanha", "nome_ponto", "nome_cientifico"]).reset_index(drop=True)


def campaigns_points(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    campaigns = sorted(df["nome_campanha"].dropna().astype(str).unique().tolist(), key=campaign_key)
    points = sorted(df["nome_ponto"].dropna().astype(str).unique().tolist(), key=point_key)
    return campaigns, points


def quantitative_df(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["tipo_norm"] == "Quantitativa"].copy()


def density_unit(df: pd.DataFrame) -> str:
    return "org/amostra"


def write_excel(df: pd.DataFrame, name: str, *, sheet_name: str = "dados") -> Path:
    out = OUTPUT_DIR / name
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return out


def complete_campaign_point(df_value: pd.DataFrame, campaigns: list[str], points: list[str], value_col: str) -> pd.DataFrame:
    base = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"]).to_frame(index=False)
    out = base.merge(df_value, on=["nome_campanha", "nome_ponto"], how="left")
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce").fillna(0.0)
    out["campanha_label"] = out["nome_campanha"].map(campaign_label)
    return out


def plot_grouped_campaign_bars(
    df: pd.DataFrame,
    *,
    value_col: str,
    ylabel: str,
    out_name: str,
    decimals: int = 0,
    integer_axis: bool = False,
) -> Path:
    campaigns, points = campaigns_points(df)
    pivot = (
        df.pivot_table(index="nome_ponto", columns="nome_campanha", values=value_col, aggfunc="sum", fill_value=0)
        .reindex(index=points, columns=campaigns, fill_value=0)
        .fillna(0)
    )

    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes).tolist()
    x = np.arange(len(points))
    colors = [PRIMARY, SECONDARY, SECONDARY_DARK]
    ymax = max(float(np.nanmax(pivot.to_numpy(dtype=float))) if pivot.size else 0.0, 1.0)

    for i, (ax, campaign) in enumerate(zip(axes, campaigns)):
        values = pivot[campaign].to_numpy(dtype=float)
        bars = ax.bar(
            x,
            values,
            width=0.62,
            color=colors[i % len(colors)],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        for bar, value in zip(bars, values):
            if value <= 0 and not integer_axis:
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                float(value) + ymax * 0.018,
                fmt_number(value, decimals),
                ha="center",
                va="bottom",
                fontsize=12,
                zorder=4,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(points, rotation=45, ha="right")
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        if integer_axis:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        ax.set_ylim(0, ymax * 1.20)
        style_box_axes(ax, xlabel="Ponto amostral", ylabel=ylabel if ax is axes[0] else "")
        if ax is not axes[0]:
            ax.tick_params(labelleft=False)
    fig.subplots_adjust(left=0.075, right=0.995, bottom=0.16, top=0.84, wspace=0.12)
    return save_fig(fig, out_name)


def plot_taxon_bar(df: pd.DataFrame, *, category_col: str, value_col: str, xlabel: str, ylabel: str, out_name: str) -> Path:
    plot_df = df.sort_values(value_col, ascending=False).copy()
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    x = np.arange(len(plot_df))
    values = pd.to_numeric(plot_df[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
    bars = ax.bar(x, values, color=PRIMARY, edgecolor="black", linewidth=0.8, zorder=3)
    ymax = max(float(values.max()) if len(values) else 0.0, 1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df[category_col].astype(str).tolist(), rotation=45, ha="right")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    ax.set_ylim(0, ymax * 1.18)
    style_box_axes(ax, xlabel=xlabel, ylabel=ylabel)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, float(value) + ymax * 0.02, fmt_number(value, 0), ha="center", va="bottom", fontsize=12)
    fig.subplots_adjust(left=0.09, right=0.995, bottom=0.23, top=0.93)
    return save_fig(fig, out_name)


def plot_donut(df: pd.DataFrame, *, category_col: str, value_col: str, out_name: str) -> Path:
    plot_df = df.sort_values(value_col, ascending=False).copy()
    values = pd.to_numeric(plot_df[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
    total = int(round(values.sum()))
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)

    def autopct_visible(pct: float) -> str:
        return f"{pct:.1f}%" if pct >= 4.0 else ""

    colors = [PHYLA_COLORS[i % len(PHYLA_COLORS)] for i in range(len(values))]
    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.45, "edgecolor": "white", "linewidth": 1.2},
        autopct=autopct_visible,
        pctdistance=0.78,
        radius=1.08,
        textprops={"fontsize": 13},
    )
    for wedge, text in zip(wedges, autotexts):
        if not text.get_text().strip():
            continue
        r, g, b = mcolors.to_rgb(wedge.get_facecolor())
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        text.set_color("white" if luminance < 0.50 else "black")
        text.set_fontweight("bold")
    ax.legend(
        wedges,
        plot_df[category_col].astype(str).tolist(),
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=15,
    )
    ax.text(0, 0, f"Total\n{total}", ha="center", va="center", fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    fig.subplots_adjust(left=0.02, right=0.78, bottom=0.06, top=0.96)
    return save_fig(fig, out_name)


def build_composition(df: pd.DataFrame) -> pd.DataFrame:
    q = quantitative_df(df)
    density_by_taxon = q.groupby("nome_cientifico")["contagem"].sum().rename("densidade_quantitativa_total")
    occurrence = (
        df.assign(amostra=df["nome_campanha"] + " | " + df["nome_ponto"])
        .groupby("nome_cientifico")
        .agg(
            ocorrencias=("amostra", "nunique"),
            campanhas=("nome_campanha", lambda s: "; ".join(campaign_label(v) for v in sorted(s.unique(), key=campaign_key))),
            tipos_amostragem=("tipo_norm", lambda s: "; ".join(sorted(s.unique()))),
        )
    )
    attrs = (
        df.groupby("nome_cientifico", as_index=True)
        .agg(
            filo=("filo", first_valid),
            classe=("classe", first_valid),
            ordem=("ordem", first_valid),
            familia=("familia", first_valid),
            genero=("genero", first_valid),
            origem=("origem", first_valid),
        )
        .join(occurrence, how="left")
        .join(density_by_taxon, how="left")
        .fillna({"densidade_quantitativa_total": 0})
        .reset_index()
    )
    attrs = attrs.rename(
        columns={
            "nome_cientifico": "Táxon",
            "filo": "Filo",
            "classe": "Classe",
            "ordem": "Ordem",
            "familia": "Família",
            "genero": "Gênero",
            "origem": "Origem",
            "ocorrencias": "Ocorrências",
            "campanhas": "Campanhas",
            "tipos_amostragem": "Tipos de amostragem",
            "densidade_quantitativa_total": "Densidade quantitativa total",
        }
    )
    return attrs.sort_values(["Filo", "Classe", "Ordem", "Família", "Gênero", "Táxon"], na_position="last").reset_index(drop=True)


def build_occurrence(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    rows = []
    for (taxon, campaign, point), g in df.groupby(["nome_cientifico", "nome_campanha", "nome_ponto"], dropna=False):
        q = g[g["tipo_norm"] == "Quantitativa"]
        if not q.empty:
            value = q["contagem"].sum()
            cell = fmt_number(value, 2)
        else:
            cell = "X"
        rows.append({"Táxon": taxon, "campanha": campaign, "ponto": point, "valor": cell})
    occ = pd.DataFrame(rows)
    if occ.empty:
        return pd.DataFrame(columns=["Táxon"])
    occ["coluna"] = occ["campanha"].map(campaign_label) + " - " + occ["ponto"].astype(str)
    table = occ.pivot_table(index="Táxon", columns="coluna", values="valor", aggfunc="first", fill_value="").reset_index()
    for campaign in campaigns:
        cols = [f"{campaign_label(campaign)} - {p}" for p in points]
        for col in cols:
            if col not in table.columns:
                table[col] = ""
        table[f"{campaign_label(campaign)} - OC"] = table[cols].apply(lambda row: sum(str(v).strip() not in {"", "0", "0.0"} for v in row), axis=1)
        table[f"{campaign_label(campaign)} - %OC"] = table[f"{campaign_label(campaign)} - OC"].apply(lambda value: f"{(100 * value / max(len(points), 1)):.0f}%")
    ordered_cols = ["Táxon"]
    for campaign in campaigns:
        ordered_cols.extend([f"{campaign_label(campaign)} - {p}" for p in points])
        ordered_cols.extend([f"{campaign_label(campaign)} - OC", f"{campaign_label(campaign)} - %OC"])
    return table[ordered_cols].sort_values("Táxon").reset_index(drop=True)


def build_richness_by_point(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    richness = df.groupby(["nome_campanha", "nome_ponto"])["nome_cientifico"].nunique().reset_index(name="riqueza")
    return complete_campaign_point(richness, campaigns, points, "riqueza")


def build_density_by_point(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    q = quantitative_df(df)
    density = q.groupby(["nome_campanha", "nome_ponto"])["contagem"].sum().reset_index(name="densidade_total")
    return complete_campaign_point(density, campaigns, points, "densidade_total")


def build_richness_by_phylum(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("filo")["nome_cientifico"]
        .nunique()
        .reset_index(name="numero_de_taxons")
        .rename(columns={"filo": "Filo", "numero_de_taxons": "Número de táxons"})
        .sort_values("Número de táxons", ascending=False)
        .reset_index(drop=True)
    )
    out["Representatividade (%)"] = (out["Número de táxons"] / out["Número de táxons"].sum() * 100).round(1)
    return out


def build_density_phylum(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    q = quantitative_df(df)
    density = q.groupby(["nome_campanha", "nome_ponto", "filo"])["contagem"].sum().reset_index(name="densidade")
    base = pd.MultiIndex.from_product([campaigns, points, sorted(q["filo"].dropna().unique().tolist())], names=["nome_campanha", "nome_ponto", "filo"]).to_frame(index=False)
    density = base.merge(density, on=["nome_campanha", "nome_ponto", "filo"], how="left").fillna({"densidade": 0})
    density["campanha_label"] = density["nome_campanha"].map(campaign_label)
    totals = density.groupby(["nome_campanha", "nome_ponto"])["densidade"].transform("sum").replace(0, np.nan)
    density["densidade_relativa_pct"] = (density["densidade"] / totals * 100).fillna(0)
    pivot_abs = density.pivot_table(index=["nome_campanha", "nome_ponto"], columns="filo", values="densidade", aggfunc="sum", fill_value=0).reset_index()
    pivot_rel = density.pivot_table(index=["nome_campanha", "nome_ponto"], columns="filo", values="densidade_relativa_pct", aggfunc="sum", fill_value=0).reset_index()
    return pivot_abs, pivot_rel


def plot_stacked_phylum(
    pivot_df: pd.DataFrame,
    *,
    campaigns: list[str],
    points: list[str],
    value_label: str,
    out_name: str,
    relative: bool = False,
) -> Path:
    phyla = [c for c in pivot_df.columns if c not in {"nome_campanha", "nome_ponto"}]
    colors = {phylum: PHYLA_COLORS[i % len(PHYLA_COLORS)] for i, phylum in enumerate(phyla)}
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=not relative)
    if len(campaigns) == 1:
        axes = [axes]

    for ax, campaign in zip(axes, campaigns):
        local = pivot_df[pivot_df["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points, fill_value=0)
        x = np.arange(len(points))
        bottom = np.zeros(len(points))
        for phylum in phyla:
            values = pd.to_numeric(local[phylum], errors="coerce").fillna(0).to_numpy(dtype=float)
            ax.bar(x, values, bottom=bottom, label=phylum, color=colors[phylum], edgecolor="white", linewidth=0.6, zorder=3)
            bottom += values
        ax.set_xticks(x)
        ax.set_xticklabels(points, rotation=45, ha="right")
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        if relative:
            ax.set_ylim(0, 100)
        style_box_axes(ax, xlabel="Ponto amostral", ylabel=value_label if ax is axes[0] else "")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=min(len(labels), 4), frameon=False)
    fig.subplots_adjust(left=0.075, right=0.995, bottom=0.16, top=0.78, wspace=0.12)
    return save_fig(fig, out_name)


def build_density_taxon(df: pd.DataFrame, campaigns: list[str]) -> pd.DataFrame:
    q = quantitative_df(df)
    density = q.groupby(["nome_campanha", "nome_cientifico"])["contagem"].sum().reset_index(name="densidade")
    taxa = density.groupby("nome_cientifico")["densidade"].sum().sort_values(ascending=False).index.tolist()
    base = pd.MultiIndex.from_product([campaigns, taxa], names=["nome_campanha", "nome_cientifico"]).to_frame(index=False)
    density = base.merge(density, on=["nome_campanha", "nome_cientifico"], how="left").fillna({"densidade": 0})
    density["campanha_label"] = density["nome_campanha"].map(campaign_label)
    return density


def plot_taxon_horizontal(df_taxon: pd.DataFrame, *, out_name: str, unit: str, top_n: int = 20) -> Path:
    totals = df_taxon.groupby("nome_cientifico")["densidade"].sum().sort_values(ascending=False)
    selected = totals.head(top_n).index.tolist()
    taxa_order = list(reversed(selected))
    campaigns = sorted(df_taxon["nome_campanha"].unique().tolist(), key=campaign_key)
    pivot = (
        df_taxon[df_taxon["nome_cientifico"].isin(selected)]
        .pivot_table(index="nome_cientifico", columns="nome_campanha", values="densidade", aggfunc="sum", fill_value=0)
        .reindex(index=taxa_order, columns=campaigns, fill_value=0)
    )
    labels = pivot.index.tolist()
    y = np.arange(len(labels))
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes).tolist()
    colors = [PRIMARY, SECONDARY, SECONDARY_DARK]
    xmax = max(float(np.nanmax(pivot.to_numpy(dtype=float))) if pivot.size else 0.0, 1.0)
    for i, (ax, campaign) in enumerate(zip(axes, campaigns)):
        values = pivot[campaign].to_numpy(dtype=float)
        bars = ax.barh(
            y,
            values,
            height=0.64,
            color=colors[i % len(colors)],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        for bar, value in zip(bars, values):
            if value <= 0:
                continue
            ax.text(float(value) + xmax * 0.014, bar.get_y() + bar.get_height() / 2, fmt_number(value, 2), va="center", ha="left", fontsize=10)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontstyle="italic", fontsize=10)
        ax.set_xlim(0, xmax * 1.15)
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        style_box_axes(ax, xlabel=f"Densidade ({unit})", ylabel="Táxon" if ax is axes[0] else "")
        ax.grid(axis="x", linestyle="--", linewidth=0.7, color="#E8E8E8", alpha=0.75)
        ax.grid(axis="y", color="#EFEFEF", linestyle="-", linewidth=0.6, alpha=0.8)
        if ax is not axes[0]:
            ax.tick_params(labelleft=False)
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.14, top=0.84, wspace=0.10)
    return save_fig(fig, out_name)


def plot_taxon_heatmap(df: pd.DataFrame, *, campaigns: list[str], points: list[str], out_name: str, unit: str, top_n: int = 20) -> tuple[Path, pd.DataFrame]:
    q = quantitative_df(df)
    ordered_samples = [(c, p) for c in campaigns for p in points]
    sample_cols = [sample_label(c, p) for c, p in ordered_samples]
    taxa = q.groupby("nome_cientifico")["contagem"].sum().sort_values(ascending=False).index.tolist()
    mat = (
        q.assign(amostra_label=[sample_label(c, p) for c, p in zip(q["nome_campanha"], q["nome_ponto"])])
        .pivot_table(index="nome_cientifico", columns="amostra_label", values="contagem", aggfunc="sum", fill_value=0)
        .reindex(index=taxa, columns=sample_cols, fill_value=0)
        .fillna(0)
    )
    out_df = mat.reset_index().rename(columns={"nome_cientifico": "Táxon"})

    mat = mat.loc[taxa[:top_n]]
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes).tolist()
    cmap = mcolors.LinearSegmentedColormap.from_list("opyta_green", ["#f6fbf4", "#b9deb2", "#2a8b22", "#11420C"])
    global_values = mat.to_numpy(dtype=float)
    vmax = max(float(global_values.max()) if global_values.size else 1.0, 1.0)
    im = None
    for ax, campaign in zip(axes, campaigns):
        local_cols = [sample_label(campaign, point) for point in points]
        values = mat.reindex(columns=local_cols, fill_value=0).to_numpy(dtype=float)
        im = ax.imshow(values, aspect="auto", cmap=cmap, vmin=0, vmax=vmax)
        ax.set_xticks(np.arange(len(points)))
        ax.set_xticklabels(points, rotation=90, ha="center", fontsize=12)
        ax.set_yticks(np.arange(len(mat.index)))
        ax.set_yticklabels(mat.index.tolist(), fontstyle="italic", fontsize=9)
        ax.set_xlabel("Ponto amostral")
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        if ax is axes[0]:
            ax.set_ylabel("Táxon")
        else:
            ax.tick_params(labelleft=False)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                value = values[i, j]
                if value <= 0:
                    continue
                color = "white" if value > vmax * 0.45 else "black"
                ax.text(j, i, fmt_number(value, 1), ha="center", va="center", fontsize=7, color=color)
        for spine in ["top", "right", "left", "bottom"]:
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_color("black")
            ax.spines[spine].set_linewidth(1.2)
    cbar = fig.colorbar(im, ax=axes, fraction=0.030, pad=0.02)
    cbar.set_label(f"Densidade ({unit})", rotation=90, labelpad=12)
    fig.subplots_adjust(left=0.22, right=0.90, bottom=0.18, top=0.84, wspace=0.08)
    return save_fig(fig, out_name), out_df


def shannon(counts: np.ndarray) -> float:
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-np.sum(p * np.log(p)))


def pielou(counts: np.ndarray) -> float:
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size <= 1:
        return 0.0
    return float(shannon(counts) / np.log(counts.size))


def build_quant_matrix(df: pd.DataFrame, *, campaigns: list[str], points: list[str], positive_only: bool = True) -> pd.DataFrame:
    q = quantitative_df(df)
    ordered_samples = [sample_label(c, p) for c in campaigns for p in points]
    mat = (
        q.assign(amostra_label=[sample_label(c, p) for c, p in zip(q["nome_campanha"], q["nome_ponto"])])
        .pivot_table(index="amostra_label", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0)
        .reindex(index=ordered_samples, fill_value=0)
        .fillna(0)
    )
    if positive_only:
        mat = mat.loc[mat.sum(axis=1) > 0]
    return mat


def build_point_matrix(df: pd.DataFrame, *, points: list[str], positive_only: bool = True) -> pd.DataFrame:
    q = quantitative_df(df)
    mat = (
        q.pivot_table(index="nome_ponto", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0)
        .reindex(index=points, fill_value=0)
        .fillna(0)
    )
    if positive_only:
        mat = mat.loc[mat.sum(axis=1) > 0]
    return mat


def build_occurrence_matrix(df: pd.DataFrame, *, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    ordered_samples = [sample_label(c, p) for c in campaigns for p in points]
    mat = (
        df.assign(presenca=1)
        .pivot_table(index="amostra_label", columns="nome_cientifico", values="presenca", aggfunc="max", fill_value=0)
        .reindex(index=ordered_samples, fill_value=0)
        .fillna(0)
    )
    mat = mat.loc[mat.sum(axis=1) > 0, mat.sum(axis=0) > 0]
    return mat.astype(int)


def build_diversity(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    mat = build_quant_matrix(df, campaigns=campaigns, points=points, positive_only=False)
    rows = []
    for campaign in campaigns:
        local_samples = [sample_label(campaign, p) for p in points]
        local = mat.reindex(local_samples, fill_value=0)
        for point, sample in zip(points, local_samples):
            vec = local.loc[sample].to_numpy(dtype=float)
            rows.append(
                {
                    "nome_campanha": campaign,
                    "campanha_label": campaign_label(campaign),
                    "nome_ponto": point,
                    "amostra": sample,
                    "riqueza_quantitativa": int((vec > 0).sum()),
                    "densidade_total": float(vec.sum()),
                    "Shannon_H": shannon(vec),
                    "Pielou_J": pielou(vec),
                }
            )
        total_vec = local.sum(axis=0).to_numpy(dtype=float)
        rows.append(
            {
                "nome_campanha": campaign,
                "campanha_label": campaign_label(campaign),
                "nome_ponto": "Geral",
                "amostra": f"{campaign_label(campaign)}-Geral",
                "riqueza_quantitativa": int((total_vec > 0).sum()),
                "densidade_total": float(total_vec.sum()),
                "Shannon_H": shannon(total_vec),
                "Pielou_J": pielou(total_vec),
            }
        )
    div = pd.DataFrame(rows)
    geral = div[div["nome_ponto"] == "Geral"].copy()
    return div, geral


def plot_diversity(diversity: pd.DataFrame, *, campaigns: list[str], points: list[str], out_name: str) -> Path:
    plot_df = diversity[diversity["nome_ponto"] != "Geral"].copy()
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes).tolist()
    x = np.arange(len(points))
    ymax = max(float(plot_df["Shannon_H"].max()) if not plot_df.empty else 0.0, 0.25)
    legend_handles = []
    legend_labels = []

    for i, (ax1, campaign) in enumerate(zip(axes, campaigns)):
        local = (
            plot_df[plot_df["nome_campanha"] == campaign]
            .set_index("nome_ponto")
            .reindex(points)
            .fillna({"Shannon_H": 0, "Pielou_J": 0})
        )
        shannon_values = pd.to_numeric(local["Shannon_H"], errors="coerce").fillna(0).to_numpy(dtype=float)
        pielou_values = pd.to_numeric(local["Pielou_J"], errors="coerce").fillna(0).to_numpy(dtype=float)
        bars = ax1.bar(x, shannon_values, color=PRIMARY, edgecolor="black", linewidth=0.8, label="Diversidade (H')", zorder=3)
        ax1.set_xticks(x)
        ax1.set_xticklabels(points, rotation=45, ha="right")
        ax1.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        ax1.set_ylim(0, ymax * 1.30)
        style_box_axes(ax1, xlabel="Ponto amostral", ylabel="Shannon (H')" if ax1 is axes[0] else "")
        if ax1 is not axes[0]:
            ax1.tick_params(labelleft=False)
        for bar, value in zip(bars, shannon_values):
            if value <= 0:
                continue
            ax1.text(bar.get_x() + bar.get_width() / 2, float(value) + ymax * 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=12)

        ax2 = ax1.twinx()
        marker_line = ax2.plot(x, pielou_values, marker="o", linestyle="None", markersize=6, color=SECONDARY_DARK, label="Equitabilidade (J')", zorder=4)
        ax2.set_ylim(0, 1.1)
        ax2.tick_params(axis="both", direction="out")
        ax2.set_ylabel("Pielou (J')" if i == len(axes) - 1 else "", labelpad=10)
        if i != len(axes) - 1:
            ax2.tick_params(labelright=False)
        for spine in ["top", "right", "left", "bottom"]:
            ax2.spines[spine].set_visible(True)
            ax2.spines[spine].set_color("black")
            ax2.spines[spine].set_linewidth(1.2)
        if i == 0:
            h1, l1 = ax1.get_legend_handles_labels()
            legend_handles.extend(h1)
            legend_labels.extend(l1)
            legend_handles.extend(marker_line)
            legend_labels.append("Equitabilidade (J')")

    fig.legend(legend_handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.075, right=0.92, bottom=0.16, top=0.78, wspace=0.12)
    return save_fig(fig, out_name)


def plot_dendrogram(mat: pd.DataFrame, out_name: str) -> tuple[Path | None, pd.DataFrame | None]:
    if mat.shape[0] < 2:
        return None, None
    dist_cond = pdist(mat.values, metric="braycurtis")
    z = linkage(dist_cond, method="average")
    dist_sq = pd.DataFrame(squareform(dist_cond), index=mat.index, columns=mat.index)
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    dendrogram(z, labels=mat.index.tolist(), orientation="right", ax=ax, color_threshold=None)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.02, -0.02)
    ticks_sim = np.arange(0, 101, 10)
    ticks_dist = 1 - ticks_sim / 100.0
    ax.set_xticks(ticks_dist)
    ax.set_xticklabels([str(t) for t in ticks_sim])
    style_box_axes(ax, xlabel="Similaridade de Bray-Curtis (%)", ylabel="")
    ax.grid(axis="x", linestyle="--", linewidth=0.7, color="#D9D9D9", alpha=0.35)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="both", labelsize=13)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.08, top=0.84)
    return save_fig(fig, out_name), dist_sq


def jackknife_1(pa_matrix: np.ndarray) -> float:
    k = int(pa_matrix.shape[0])
    if k == 0:
        return 0.0
    spp_occ = pa_matrix.sum(axis=0)
    s_obs = int((spp_occ > 0).sum())
    q1 = int((spp_occ == 1).sum())
    return float(s_obs + q1 * ((k - 1) / k))


def build_sufficiency(mat: pd.DataFrame) -> pd.DataFrame:
    mat_pa = (mat > 0).astype(int)
    n_samples = int(mat_pa.shape[0])
    if n_samples < 2:
        return pd.DataFrame()
    n_random = 200
    rng = np.random.default_rng(42)
    values = mat_pa.to_numpy(dtype=int)
    sobs_curves = np.zeros((n_random, n_samples), dtype=float)
    sest_curves = np.zeros((n_random, n_samples), dtype=float)
    for r in range(n_random):
        idx = rng.permutation(n_samples)
        shuffled = values[idx, :]
        for i in range(1, n_samples + 1):
            subset = shuffled[:i, :]
            spp_occ = subset.sum(axis=0)
            sobs_curves[r, i - 1] = float((spp_occ > 0).sum())
            sest_curves[r, i - 1] = jackknife_1(subset)
    x_axis = np.arange(1, n_samples + 1)
    mean_sobs = sobs_curves.mean(axis=0)
    mean_sest = sest_curves.mean(axis=0)
    std_sest = sest_curves.std(axis=0)
    return pd.DataFrame(
        {
            "n_amostras": x_axis,
            "riqueza_obs_media": mean_sobs,
            "riqueza_est_jackknife1_media": mean_sest,
            "jackknife1_desvio_padrao": std_sest,
            "jackknife1_inf": mean_sest - std_sest,
            "jackknife1_sup": mean_sest + std_sest,
        }
    )


def plot_sufficiency(df_curve: pd.DataFrame, out_name: str) -> Path | None:
    if df_curve.empty:
        return None
    x = df_curve["n_amostras"].to_numpy(dtype=float)
    obs = df_curve["riqueza_obs_media"].to_numpy(dtype=float)
    est = df_curve["riqueza_est_jackknife1_media"].to_numpy(dtype=float)
    std = df_curve["jackknife1_desvio_padrao"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    ax.plot(x, obs, linewidth=2.2, label="Riqueza observada", color=PRIMARY)
    ax.plot(x, est, linewidth=2.2, label="Riqueza estimada (Jackknife 1)", color=SECONDARY_DARK)
    ax.fill_between(x, est - std, est + std, alpha=0.18, color=SECONDARY_DARK)
    style_box_axes(ax, xlabel="Número de unidades amostrais", ylabel="Riqueza")
    ax.set_xlim(float(np.nanmin(x)), float(np.nanmax(x)) + 1.0)
    ax.set_ylim(0, max(float(np.nanmax(est + std)) * 1.08, 1.0))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
    ax.text(x[-1] + 0.15, obs[-1], f"{obs[-1]:.0f}", color="black", va="center", fontsize=12)
    ax.text(x[-1] + 0.15, est[-1], f"{est[-1]:.1f}", color="black", va="center", fontsize=12)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.09, right=0.96, bottom=0.14, top=0.82)
    return save_fig(fig, out_name)


def build_synthesis(df: pd.DataFrame, richness_phylum: pd.DataFrame, density_phylum: pd.DataFrame) -> dict[str, pd.DataFrame]:
    density_totals = density_phylum.drop(columns=["nome_campanha", "nome_ponto"]).sum().sort_values(ascending=False).reset_index()
    density_totals.columns = ["Filo", "Densidade quantitativa total"]
    return {
        "riqueza_por_filo": richness_phylum,
        "densidade_quantitativa_por_filo": density_totals,
        "resumo_por_campanha": df.groupby(["nome_campanha", "tipo_norm"]).agg(linhas=("nome_cientifico", "size"), taxons=("nome_cientifico", "nunique"), contagem=("contagem", "sum")).reset_index(),
    }


def plot_synthesis(sheets: dict[str, pd.DataFrame], unit: str, out_name: str) -> Path:
    richness = sheets["riqueza_por_filo"].sort_values("Número de táxons", ascending=True)
    density = sheets["densidade_quantitativa_por_filo"].sort_values("Densidade quantitativa total", ascending=True)
    fig, axes = plt.subplots(1, 2, figsize=A4_LANDSCAPE, dpi=DPI)
    panels = [
        (axes[0], richness, "Filo", "Número de táxons", "Riqueza por filo", "Número de táxons"),
        (axes[1], density, "Filo", "Densidade quantitativa total", "Densidade quantitativa por filo", f"Densidade ({unit})"),
    ]
    for ax, local, cat_col, value_col, title, xlabel in panels:
        values = pd.to_numeric(local[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        y = np.arange(len(local))
        ax.barh(y, values, color=PRIMARY, edgecolor="black", linewidth=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(local[cat_col].astype(str).tolist())
        ax.set_title(title, fontweight="bold", fontsize=13, pad=12)
        style_box_axes(ax, xlabel=xlabel, ylabel="")
        ax.tick_params(axis="both", labelsize=12)
        ax.xaxis.label.set_size(13)
        xmax = max(float(values.max()) if len(values) else 0.0, 1.0)
        ax.set_xlim(0, xmax * 1.18)
        for yi, value in zip(y, values):
            ax.text(float(value) + xmax * 0.02, yi, fmt_number(value, 1), va="center", ha="left", fontsize=10)
    fig.subplots_adjust(left=0.20, right=0.97, bottom=0.15, top=0.82, wspace=0.70)
    fig.suptitle("Síntese do fitoplâncton - WSPKIN001", fontweight="bold", fontsize=15)
    return save_fig(fig, out_name)


def image_info(path: Path) -> dict:
    with Image.open(path) as im:
        dpi = im.info.get("dpi") or (DPI, DPI)
        arr = np.asarray(im.convert("RGB"))
        return {
            "arquivo": path.name,
            "tamanho_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "largura_px": int(im.size[0]),
            "altura_px": int(im.size[1]),
            "dpi_x": float(dpi[0]),
            "dpi_y": float(dpi[1]),
            "largura_cm": round((im.size[0] / float(dpi[0])) * 2.54, 2),
            "altura_cm": round((im.size[1] / float(dpi[1])) * 2.54, 2),
            "pixel_std": float(arr.std()),
            "nonblank": bool(arr.std() > 0.5),
        }


def make_contact_sheet(tag: str) -> Path:
    thumbs = []
    for name in FINAL_FIGURES:
        path = OUTPUT_DIR / name
        if not path.exists():
            continue
        im = Image.open(path).convert("RGB")
        im.thumbnail((560, 360))
        canvas = Image.new("RGB", (590, 420), "white")
        canvas.paste(im, ((590 - im.width) // 2, 10))
        d = ImageDraw.Draw(canvas)
        d.text((12, 388), name[:82], fill="black")
        thumbs.append(canvas)
    cols = 2
    rows = max(1, math.ceil(len(thumbs) / cols))
    sheet = Image.new("RGB", (cols * 590, rows * 420), "white")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % cols) * 590, (i // cols) * 420))
    out = AUDIT_DIR / f"{tag}_contact_sheet_figuras_fitoplancton_a4_paisagem.png"
    sheet.save(out)
    return out


def write_html_report(metrics: dict, unit: str) -> Path:
    out = OUTPUT_DIR / "relatorio_tecnico_fitoplancton_wspkin001.html"
    figures = [
        ("02_grafico_riqueza_por_ponto_fitoplancton.png", "Riqueza por ponto"),
        ("03_grafico_densidade_total_por_ponto_fitoplancton.png", "Densidade total por ponto"),
        ("04_grafico_riqueza_filo_barras_fitoplancton.png", "Riqueza por filo"),
        ("06_grafico_densidade_filo_por_ponto_fitoplancton.png", "Densidade por filo"),
        ("08_grafico_densidade_por_taxon_fitoplancton.png", "Densidade por táxon"),
        ("09_grafico_densidade_taxon_ponto_fitoplancton.png", "Densidade por táxon e amostra"),
        ("10_grafico_diversidade_alfa_fitoplancton.png", "Diversidade alfa"),
        ("11_dendrograma_similaridade_fitoplancton.png", "Similaridade"),
        ("11B_dendrograma_similaridade_pontos_fitoplancton.png", "Similaridade geral por ponto"),
        ("12_curva_suficiencia_amostral_fitoplancton.png", "Suficiência amostral"),
        ("14_grafico_sintese_fitoplancton.png", "Síntese"),
    ]
    figure_blocks = []
    for name, caption in figures:
        if (OUTPUT_DIR / name).exists():
            figure_blocks.append(
                f'<figure><img src="{html.escape(name)}" alt="{html.escape(caption)}">'
                f"<figcaption>{html.escape(caption)}</figcaption></figure>"
            )

    body = f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>WSPKIN001 - Relatório técnico de fitoplâncton</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ color: #11420C; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #d6d6d6; border-radius: 6px; padding: 12px; }}
    .value {{ font-size: 24px; font-weight: 700; color: #11420C; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d6d6d6; padding: 7px 9px; text-align: left; }}
    th {{ background: #eef4ec; }}
    figure {{ margin: 24px 0; page-break-inside: avoid; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #e5e7eb; }}
    figcaption {{ font-size: 13px; color: #4b5563; margin-top: 6px; }}
    .note {{ background: #f7faf5; border-left: 4px solid #11420C; padding: 10px 12px; }}
  </style>
</head>
<body>
  <h1>WSPKIN001 - Diagnóstico do fitoplâncton</h1>
  <p>Pacote diagnóstico gerado para as campanhas {html.escape(metrics["campaigns_text"])}, com {metrics["points_count"]} pontos amostrais.</p>
  <div class="cards">
    <div class="card"><div class="value">{metrics["taxa_total"]}</div><div>táxons totais</div></div>
    <div class="card"><div class="value">{metrics["taxa_quant"]}</div><div>táxons quantitativos</div></div>
    <div class="card"><div class="value">{fmt_number(metrics["density_total"], 1)}</div><div>densidade quantitativa total ({html.escape(unit)})</div></div>
    <div class="card"><div class="value">{metrics["phyla_total"]}</div><div>filos</div></div>
  </div>

  <h2>Destaques diagnósticos</h2>
  <ul>
    <li>Maior riqueza: {html.escape(metrics["max_richness_point"])} em {html.escape(metrics["max_richness_campaign"])}, com {fmt_number(metrics["max_richness"], 0)} táxons.</li>
    <li>Maior densidade quantitativa: {html.escape(metrics["max_density_point"])} em {html.escape(metrics["max_density_campaign"])}, com {fmt_number(metrics["max_density"], 1)} {html.escape(unit)}.</li>
    <li>Filo dominante na fração quantitativa: {html.escape(metrics["dominant_phylum"])} ({fmt_number(metrics["dominant_phylum_density"], 1)} {html.escape(unit)}).</li>
    <li>Táxon com maior densidade: <em>{html.escape(metrics["dominant_taxon"])}</em> ({fmt_number(metrics["dominant_taxon_density"], 1)} {html.escape(unit)}).</li>
    <li>Curva de suficiência amostral: riqueza observada final {fmt_number(metrics["suff_obs"], 0)}; Jackknife 1 {fmt_number(metrics["suff_est"], 1)}.</li>
  </ul>

  <p class="note">Riqueza, ocorrência e suficiência amostral usam registros qualitativos e quantitativos. Densidade, diversidade e similaridade usam somente registros quantitativos, pois a contagem consolidada de Fitoplâncton já representa a densidade migrada.</p>

  <h2>Figuras principais</h2>
  {''.join(figure_blocks)}

  <h2>Rastreabilidade</h2>
  <p>Manifesto: <code>manifesto_entrega_fitoplancton_wspkin001.json</code> e <code>manifesto_entrega_fitoplancton_wspkin001.xlsx</code>.</p>
</body>
</html>
"""
    validate_html_ptbr(body)
    out.write_text(body, encoding="utf-8")
    return out


BAD_HTML_TERMS = [
    "diagn" + "ostico",
    "fitoplancton",
    "taxons",
    "sufici" + "encia",
    "abund" + "ancia",
    "indiv" + "iduos",
    "famil" + "ias",
]


def validate_html_ptbr(text: str) -> None:
    visible = re.sub(r"<code>.*?</code>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    visible = re.sub(r"<[^>]+>", " ", visible)
    found = [term for term in BAD_HTML_TERMS if term in visible]
    if found:
        raise ValueError("Texto visível sem acentuação pt-BR no HTML: " + ", ".join(found))


def build_manifest_and_validation(generated_files: list[Path], metrics: dict, tag: str) -> tuple[Path, Path, Path, Path]:
    manifest_json = OUTPUT_DIR / "manifesto_entrega_fitoplancton_wspkin001.json"
    manifest_xlsx = OUTPUT_DIR / "manifesto_entrega_fitoplancton_wspkin001.xlsx"
    manifest_md = OUTPUT_DIR / "manifesto_entrega_fitoplancton_wspkin001.md"
    validation_json = OUTPUT_DIR / "validacao_entrega_fitoplancton_wspkin001.json"

    files = [p for p in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.name.lower()) if p.is_file() and p.name != "desktop.ini" and not p.name.startswith("manifesto_entrega_fitoplancton_wspkin001")]
    rows = []
    for path in files:
        rows.append(
            {
                "arquivo": path.name,
                "extensao": path.suffix.lower().lstrip("."),
                "tamanho_bytes": path.stat().st_size,
                "modificado_em": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z"),
                "sha256": sha256(path),
            }
        )

    expected_names = {p.name for p in generated_files}
    missing = sorted(name for name in expected_names if not (OUTPUT_DIR / name).exists())
    zero_size = sorted(path.name for path in files if path.stat().st_size <= 0)
    figure_checks = []
    for name in FINAL_FIGURES:
        path = OUTPUT_DIR / name
        if not path.exists():
            continue
        info = image_info(path)
        figure_checks.append(info)
    bad_dimensions = [row["arquivo"] for row in figure_checks if row["largura_px"] != 7014 or row["altura_px"] != 4962]
    blank = [row["arquivo"] for row in figure_checks if not row["nonblank"]]

    validation = {
        "validated_at": now_iso(),
        "status": "OK" if not missing and not zero_size and not bad_dimensions and not blank else "ERROR",
        "files_checked": len(files),
        "figures_checked": len(figure_checks),
        "missing_files": missing,
        "zero_size_files": zero_size,
        "bad_dimensions": bad_dimensions,
        "blank_figures": blank,
        "errors_count": len(missing) + len(zero_size) + len(bad_dimensions) + len(blank),
        "warnings": [
            "Densidade, diversidade e similaridade foram calculadas somente com registros quantitativos.",
            "Registros qualitativos foram usados para composição, ocorrência, riqueza taxonômica e suficiência amostral.",
            "A figura 11B agrega as campanhas e apresenta a similaridade de Bray-Curtis por ponto.",
        ],
    }
    validation_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": GROUP_DISPLAY,
        "output_dir": str(OUTPUT_DIR),
        "summary": metrics,
        "files_count": len(rows),
        "files": rows,
        "revision": {
            "id": "FITO_GERACAO_01",
            "applied_at": now_iso(),
            "description": "Resultados de Fitoplâncton gerados em A4 paisagem com padrão visual de ictiofauna e premissas técnicas do grupo.",
            "audit_tag": tag,
        },
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(rows).to_excel(manifest_xlsx, index=False, engine="openpyxl")

    lines = [
        "# WSPKIN001 - Manifesto de entrega - Fitoplâncton",
        "",
        f"- gerado em: `{manifest['generated_at']}`",
        f"- grupo: `{GROUP_DISPLAY}`",
        f"- arquivos listados: `{len(rows)}`",
        f"- táxons totais: `{metrics['taxa_total']}`",
        f"- táxons quantitativos: `{metrics['taxa_quant']}`",
        f"- densidade quantitativa total: `{fmt_number(metrics['density_total'], 1)} {metrics['density_unit']}`",
        "",
        "## Arquivos",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['arquivo']}` ({row['extensao']}, {row['tamanho_bytes']} bytes)")
    manifest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_json, manifest_xlsx, manifest_md, validation_json


def build_metrics(
    df: pd.DataFrame,
    richness_point: pd.DataFrame,
    density_point: pd.DataFrame,
    richness_phylum: pd.DataFrame,
    density_taxon: pd.DataFrame,
    density_phylum: pd.DataFrame,
    suff_curve: pd.DataFrame,
    unit: str,
) -> dict:
    q = quantitative_df(df)
    max_rich = richness_point.sort_values("riqueza", ascending=False).iloc[0]
    max_den = density_point.sort_values("densidade_total", ascending=False).iloc[0]
    phylum_totals = density_phylum.drop(columns=["nome_campanha", "nome_ponto"]).sum().sort_values(ascending=False)
    taxon_totals = density_taxon.groupby("nome_cientifico")["densidade"].sum().sort_values(ascending=False)
    campaigns = sorted(df["nome_campanha"].unique().tolist(), key=campaign_key)
    points = sorted(df["nome_ponto"].unique().tolist(), key=point_key)
    suff_obs = float(suff_curve["riqueza_obs_media"].iloc[-1]) if not suff_curve.empty else 0.0
    suff_est = float(suff_curve["riqueza_est_jackknife1_media"].iloc[-1]) if not suff_curve.empty else 0.0
    metrics = {
        "rows_consolidated": int(len(df)),
        "rows_quantitative": int(len(q)),
        "rows_qualitative": int((df["tipo_norm"] == "Qualitativa").sum()),
        "campaigns": campaigns,
        "campaigns_text": ", ".join(campaign_label(c) for c in campaigns),
        "points_count": int(len(points)),
        "taxa_total": int(df["nome_cientifico"].nunique()),
        "taxa_quant": int(q["nome_cientifico"].nunique()),
        "phyla_total": int(df["filo"].nunique()),
        "density_total": float(q["contagem"].sum()),
        "density_unit": unit,
        "max_richness": float(max_rich["riqueza"]),
        "max_richness_point": str(max_rich["nome_ponto"]),
        "max_richness_campaign": campaign_label(str(max_rich["nome_campanha"])),
        "max_density": float(max_den["densidade_total"]),
        "max_density_point": str(max_den["nome_ponto"]),
        "max_density_campaign": campaign_label(str(max_den["nome_campanha"])),
        "dominant_phylum": str(phylum_totals.index[0]) if not phylum_totals.empty else "",
        "dominant_phylum_density": float(phylum_totals.iloc[0]) if not phylum_totals.empty else 0.0,
        "dominant_taxon": str(taxon_totals.index[0]) if not taxon_totals.empty else "",
        "dominant_taxon_density": float(taxon_totals.iloc[0]) if not taxon_totals.empty else 0.0,
        "suff_obs": suff_obs,
        "suff_est": suff_est,
    }
    return metrics


def write_synthesis_workbook(sheets: dict[str, pd.DataFrame]) -> Path:
    out = OUTPUT_DIR / "14_tabela_sintese_fitoplancton.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet_name, data in sheets.items():
            data.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return out


def generate(env_file: str | None = ".env") -> dict:
    setup_rc()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    tag = now_tag()
    generated: list[Path] = []

    df = load_data(env_file)
    campaigns, points = campaigns_points(df)
    unit = density_unit(df)

    generated.append(write_excel(df.drop(columns=["tipo_norm", "campanha_label", "amostra_label"], errors="ignore"), "00_base_consolidada_fitoplancton.xlsx", sheet_name="base_consolidada"))

    composition = build_composition(df)
    generated.append(write_excel(composition, "01_tabela_composicao_fitoplancton.xlsx", sheet_name="composicao"))

    occurrence = build_occurrence(df, campaigns, points)
    generated.append(write_excel(occurrence, "01_tabela_ocorrencia_fitoplancton.xlsx", sheet_name="ocorrencia"))

    richness_point = build_richness_by_point(df, campaigns, points)
    generated.append(write_excel(richness_point, "02_df_riqueza_por_ponto_fitoplancton.xlsx"))
    generated.append(plot_grouped_campaign_bars(richness_point, value_col="riqueza", ylabel="Riqueza taxonômica", out_name="02_grafico_riqueza_por_ponto_fitoplancton.png", decimals=0, integer_axis=True))

    density_point = build_density_by_point(df, campaigns, points)
    generated.append(write_excel(density_point, "03_df_densidade_total_por_ponto_fitoplancton.xlsx"))
    generated.append(plot_grouped_campaign_bars(density_point, value_col="densidade_total", ylabel=f"Densidade total ({unit})", out_name="03_grafico_densidade_total_por_ponto_fitoplancton.png", decimals=1))

    richness_phylum = build_richness_by_phylum(df)
    generated.append(write_excel(richness_phylum, "04_df_riqueza_por_filo_fitoplancton.xlsx"))
    generated.append(plot_taxon_bar(richness_phylum, category_col="Filo", value_col="Número de táxons", xlabel="Filo", ylabel="Número de táxons", out_name="04_grafico_riqueza_filo_barras_fitoplancton.png"))
    generated.append(plot_donut(richness_phylum, category_col="Filo", value_col="Número de táxons", out_name="05_grafico_riqueza_filo_rosca_fitoplancton.png"))

    density_phylum, density_phylum_rel = build_density_phylum(df, campaigns, points)
    generated.append(write_excel(density_phylum, "06_df_densidade_filo_por_ponto_fitoplancton.xlsx"))
    generated.append(plot_stacked_phylum(density_phylum, campaigns=campaigns, points=points, value_label=f"Densidade ({unit})", out_name="06_grafico_densidade_filo_por_ponto_fitoplancton.png"))
    generated.append(write_excel(density_phylum_rel, "07_df_densidade_relativa_filo_por_ponto_fitoplancton.xlsx"))
    generated.append(plot_stacked_phylum(density_phylum_rel, campaigns=campaigns, points=points, value_label="Densidade relativa (%)", out_name="07_grafico_densidade_relativa_filo_por_ponto_fitoplancton.png", relative=True))

    density_taxon = build_density_taxon(df, campaigns)
    generated.append(write_excel(density_taxon, "08_df_densidade_por_taxon_fitoplancton.xlsx"))
    generated.append(plot_taxon_horizontal(density_taxon, out_name="08_grafico_densidade_por_taxon_fitoplancton.png", unit=unit))

    heatmap_png, heatmap_df = plot_taxon_heatmap(df, campaigns=campaigns, points=points, out_name="09_grafico_densidade_taxon_ponto_fitoplancton.png", unit=unit)
    generated.append(write_excel(heatmap_df, "09_df_densidade_taxon_ponto_fitoplancton.xlsx"))
    generated.append(heatmap_png)

    diversity_all, diversity_general = build_diversity(df, campaigns, points)
    generated.append(write_excel(diversity_all, "10_df_diversidade_alfa_fitoplancton.xlsx"))
    generated.append(plot_diversity(diversity_all, campaigns=campaigns, points=points, out_name="10_grafico_diversidade_alfa_fitoplancton.png"))

    mat_quant = build_quant_matrix(df, campaigns=campaigns, points=points, positive_only=True)
    mat_quant.index.name = "Amostra"
    generated.append(write_excel(mat_quant.reset_index(), "11_df_matriz_comunidade_fitoplancton.xlsx"))
    dendro_png, dist_sq = plot_dendrogram(mat_quant, "11_dendrograma_similaridade_fitoplancton.png")
    if dist_sq is not None:
        dist_sq.index.name = "Amostra"
        generated.append(write_excel(dist_sq.reset_index(), "11_df_distancias_braycurtis_fitoplancton.xlsx"))
    if dendro_png is not None:
        generated.append(dendro_png)

    mat_points = build_point_matrix(df, points=points, positive_only=True)
    mat_points.index.name = "Ponto"
    generated.append(write_excel(mat_points.reset_index(), "11B_df_matriz_comunidade_pontos_fitoplancton.xlsx"))
    dendro_points_png, dist_points_sq = plot_dendrogram(mat_points, "11B_dendrograma_similaridade_pontos_fitoplancton.png")
    if dist_points_sq is not None:
        dist_points_sq.index.name = "Ponto"
        generated.append(write_excel(dist_points_sq.reset_index(), "11B_df_distancias_braycurtis_pontos_fitoplancton.xlsx"))
    if dendro_points_png is not None:
        generated.append(dendro_points_png)

    mat_occ = build_occurrence_matrix(df, campaigns=campaigns, points=points)
    suff_curve = build_sufficiency(mat_occ)
    generated.append(write_excel(suff_curve, "12_df_curva_suficiencia_fitoplancton.xlsx"))
    suff_png = plot_sufficiency(suff_curve, "12_curva_suficiencia_amostral_fitoplancton.png")
    if suff_png is not None:
        generated.append(suff_png)

    dwc_files: list[str] = []
    export_darwincore_ief(
        df=df.drop(columns=["tipo_norm", "campanha_label", "amostra_label"], errors="ignore"),
        group=GROUP_DISPLAY,
        output_dir=OUTPUT_DIR,
        generated_files=dwc_files,
        output_filename="DarwinCore_IEF_Fitoplancton_WSPKIN001.xlsx",
        municipality_default="Paracatu",
        county_default="Paracatu",
    )
    generated.extend(Path(p) for p in dwc_files)

    synthesis_sheets = build_synthesis(df, richness_phylum, density_phylum)
    generated.append(write_synthesis_workbook(synthesis_sheets))
    generated.append(plot_synthesis(synthesis_sheets, unit, "14_grafico_sintese_fitoplancton.png"))

    metrics = build_metrics(df, richness_point, density_point, richness_phylum, density_taxon, density_phylum, suff_curve, unit)
    report = write_html_report(metrics, unit)
    generated.append(report)
    manifest_files = build_manifest_and_validation(generated, metrics, tag)
    generated.extend(manifest_files)
    contact_sheet = make_contact_sheet(tag)

    figure_infos = [image_info(OUTPUT_DIR / name) for name in FINAL_FIGURES if (OUTPUT_DIR / name).exists()]
    file_rows = []
    for path in generated:
        if path.exists():
            row = {
                "arquivo": path.name,
                "path": str(path),
                "tamanho_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            if path.suffix.lower() == ".png":
                row.update(image_info(path))
            file_rows.append(row)

    audit = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": GROUP_DISPLAY,
        "action": "generate_fitoplancton_results_a4_landscape",
        "output_dir": str(OUTPUT_DIR),
        "figures_count": len(figure_infos),
        "figures_ok": sum(1 for row in figure_infos if row["nonblank"] and row["largura_px"] == 7014 and row["altura_px"] == 4962),
        "files_count": len(file_rows),
        "contact_sheet": str(contact_sheet),
        "metrics": metrics,
        "files": file_rows,
    }
    audit_json = AUDIT_DIR / f"{tag}_geracao_resultados_fitoplancton_a4_paisagem.json"
    audit_xlsx = AUDIT_DIR / f"{tag}_geracao_resultados_fitoplancton_a4_paisagem.xlsx"
    audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(file_rows).to_excel(audit_xlsx, index=False, engine="openpyxl")

    metadata = {
        "executed_at": now_iso(),
        "project_id": PROJECT_ID,
        "group": GROUP_DISPLAY,
        "pipeline": "project_specific_fitoplancton_a4_landscape",
        "source": "public.biota_analise_consolidada",
        "rows_loaded": int(len(df)),
        "output_dir": str(OUTPUT_DIR),
        "generated_files_count": len(file_rows),
        "generated_files": [row["path"] for row in file_rows],
        "audit_json": str(audit_json),
        "audit_xlsx": str(audit_xlsx),
        "contact_sheet": str(contact_sheet),
        "warnings": [
            "Densidade, diversidade e similaridade calculadas com dados quantitativos.",
            "Ocorrência, riqueza taxonômica e suficiência amostral calculadas com dados qualitativos e quantitativos.",
            "Figura 11B gerada por ponto, com as campanhas agregadas.",
        ],
    }
    (AUDIT_DIR / "execution_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (AUDIT_DIR / f"{tag}_execution_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "audit_json": str(audit_json),
        "audit_xlsx": str(audit_xlsx),
        "contact_sheet": str(contact_sheet),
        "figures_count": audit["figures_count"],
        "figures_ok": audit["figures_ok"],
        "files_count": audit["files_count"],
        "output_dir": str(OUTPUT_DIR),
    }


def main() -> int:
    result = generate(env_file=".env")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
