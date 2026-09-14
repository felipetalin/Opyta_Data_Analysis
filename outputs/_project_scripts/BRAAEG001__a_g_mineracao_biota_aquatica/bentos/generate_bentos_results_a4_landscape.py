from __future__ import annotations

import hashlib
import html
import json
import math
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
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
from PIL import Image, ImageDraw
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform


ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from opyta_analysis.pipelines.diagnostico.darwincore_ief import export_darwincore_ief  # noqa: E402
from opyta_analysis.pipelines.diagnostico.zoobentos import _load_zoobentos_df  # noqa: E402


PROJECT_CODE = "BRAAEG001"
PROJECT_ID = 195
GROUP = "Zoobentos"
GROUP_DISPLAY = "Zoobentos"
OUTPUT_DIR = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/"
    "A&G Mineração/resultados/migracao_biota/bentos"
)
AUDIT_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAEG001__a_g_mineracao_biota_aquatica" / "bentos"

DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
PRIMARY = "#11420C"
SECONDARY = "#19FF00"
SECONDARY_DARK = "#6A8F63"
GRID = "#D8E9D4"
CATEGORY_COLORS = ["#11420C", "#19FF00", "#6A8F63", "#2A6F97", "#C77D32", "#6D597A", "#4D908E", "#9C6644", "#577590", "#BC6C25"]
EPT_ORDERS = {"Ephemeroptera", "Plecoptera", "Trichoptera"}
BMWP_CLASSES = [
    ("Muito boa", 86, np.inf, "#00b0f0"),
    ("Boa", 64, 85, "#92d050"),
    ("Regular", 37, 63, "#ffff00"),
    ("Ruim", 17, 36, "#ffc000"),
    ("Péssima", -np.inf, 16, "#ff0000"),
]

FINAL_FIGURES = [
    "02_grafico_riqueza_por_ponto_zoobentos.png",
    "03_grafico_abundancia_total_por_ponto_zoobentos.png",
    "04_grafico_riqueza_ordem_barras_zoobentos.png",
    "05_grafico_riqueza_ordem_rosca_zoobentos.png",
    "06_grafico_abundancia_ordem_por_ponto_zoobentos.png",
    "07_grafico_abundancia_relativa_ordem_por_ponto_zoobentos.png",
    "08_grafico_abundancia_por_taxon_zoobentos.png",
    "09_grafico_abundancia_taxon_ponto_zoobentos.png",
    "10_grafico_diversidade_alfa_zoobentos.png",
    "11_dendrograma_similaridade_zoobentos.png",
    "11B_dendrograma_similaridade_pontos_zoobentos.png",
    "12_curva_suficiencia_amostral_zoobentos.png",
    "13_grafico_bmwp_por_ponto_zoobentos.png",
    "14_grafico_ept_chol_por_ponto_zoobentos.png",
    "15_grafico_sintese_zoobentos.png",
    "16_mini_mapa_bmwp_ept_chol_zoobentos.png",
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
            "legend.fontsize": 15,
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


def clean_text(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "n.a.", "na"} else text


def taxonomic_level_label(row: pd.Series) -> str:
    order = clean_text(row.get("ordem", ""))
    if order:
        return order
    for col, level in [("classe", "Classe"), ("familia", "Família"), ("genero", "Gênero"), ("filo", "Filo"), ("nome_cientifico", "Táxon")]:
        value = clean_text(row.get(col, ""))
        if value:
            return f"{value} ({level})"
    return "Classificação não informada"


def is_genus_sp_label(label: object) -> bool:
    return bool(re.match(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚáéíóúÂÊÔâêôÃÕãõÇç-]+ sp\.$", str(label).strip()))


def apply_taxon_tick_styles(labels: list[object], ticklabels: list[object]) -> None:
    for label, tick in zip(labels, ticklabels):
        tick.set_fontstyle("italic" if is_genus_sp_label(label) else "normal")


def classify_bmwp(score: float) -> str:
    value = float(score)
    for label, lower, upper, _ in BMWP_CLASSES:
        if lower <= value <= upper:
            return label
    return "Péssima"


def bmwp_color(label: str) -> str:
    return next(color for class_label, _, _, color in BMWP_CLASSES if class_label == label)


def first_valid(series: pd.Series, default: str = "") -> str:
    values = series.dropna().astype(str).str.strip()
    values = values[(values != "") & (values.str.lower() != "nan") & (values.str.lower() != "none")]
    return str(values.iloc[0]) if not values.empty else default


def fmt_number(value: float, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return ""
    value = float(value)
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


def load_data(env_file: str | None = ".env") -> pd.DataFrame:
    df = _load_zoobentos_df(project_id=PROJECT_ID, group=GROUP, env_file=env_file)
    if df.empty:
        raise RuntimeError("A fatia consolidada de Zoobentos retornou vazia.")
    df = df.copy()
    for col in ["nome_campanha", "nome_ponto", "nome_cientifico", "filo", "classe", "ordem", "familia", "genero", "tipo_amostragem"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"None": "", "nan": "", "NaN": ""})
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0.0)
    df["bmwp_score"] = pd.to_numeric(df["bmwp_score"], errors="coerce").fillna(0.0)
    df["campanha_label"] = df["nome_campanha"].map(campaign_label)
    df["amostra_label"] = [sample_label(c, p) for c, p in zip(df["nome_campanha"], df["nome_ponto"])]
    df["familia_bmwp"] = np.where(df["familia"].astype(str).str.strip() != "", df["familia"], df["nome_cientifico"])
    return df.sort_values(["nome_campanha", "nome_ponto", "nome_cientifico"]).reset_index(drop=True)


def campaigns_points(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    campaigns = sorted(df["nome_campanha"].dropna().astype(str).unique().tolist(), key=campaign_key)
    points = sorted(df["nome_ponto"].dropna().astype(str).unique().tolist(), key=point_key)
    return campaigns, points


def unit_label(df: pd.DataFrame) -> str:
    values = df["unidade_esforco"].dropna().astype(str).str.strip()
    values = values[(values != "") & (values.str.lower() != "nan")]
    return values.mode().iloc[0] if not values.empty else "org/amostra"


def write_excel(df: pd.DataFrame, filename: str, sheet_name: str = "dados") -> Path:
    out = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        ws = writer.sheets[sheet_name[:31]]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for column_cells in ws.columns:
            header = str(column_cells[0].value or "")
            max_len = max([len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells[:200]] + [len(header)])
            ws.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 48)
    return out


def complete_campaign_point(df_value: pd.DataFrame, campaigns: list[str], points: list[str], value_col: str) -> pd.DataFrame:
    base = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"]).to_frame(index=False)
    out = base.merge(df_value, on=["nome_campanha", "nome_ponto"], how="left")
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce").fillna(0.0)
    out["campanha_label"] = out["nome_campanha"].map(campaign_label)
    return out


def build_composition(df: pd.DataFrame) -> pd.DataFrame:
    attrs = (
        df.groupby("nome_cientifico", as_index=False)
        .agg(
            Filo=("filo", first_valid),
            Classe=("classe", first_valid),
            Ordem=("ordem", first_valid),
            Família=("familia", first_valid),
            Gênero=("genero", first_valid),
            Ocorrências=("amostra_label", "nunique"),
            Campanhas=("nome_campanha", lambda s: "; ".join(campaign_label(v) for v in sorted(s.unique(), key=campaign_key))),
            Abundância_total=("contagem", "sum"),
            BMWP=("bmwp_score", "max"),
        )
        .rename(columns={"nome_cientifico": "Táxon", "Abundância_total": "Abundância total"})
    )
    total = max(float(attrs["Abundância total"].sum()), 1.0)
    attrs["Abundância relativa (%)"] = attrs["Abundância total"] / total * 100
    return attrs.sort_values(["Ordem", "Família", "Táxon"], na_position="last").reset_index(drop=True)


def build_occurrence(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    rows = []
    for (taxon, campaign, point), g in df.groupby(["nome_cientifico", "nome_campanha", "nome_ponto"], dropna=False):
        rows.append({"Táxon": taxon, "campanha": campaign, "ponto": point, "valor": g["contagem"].sum()})
    occ = pd.DataFrame(rows)
    occ["coluna"] = occ["campanha"].map(campaign_label) + " - " + occ["ponto"].astype(str)
    table = occ.pivot_table(index="Táxon", columns="coluna", values="valor", aggfunc="sum", fill_value=0).reset_index()
    for campaign in campaigns:
        cols = [f"{campaign_label(campaign)} - {p}" for p in points]
        for col in cols:
            if col not in table.columns:
                table[col] = 0
        table[f"{campaign_label(campaign)} - OC"] = table[cols].apply(lambda row: sum(float(v) > 0 for v in row), axis=1)
        table[f"{campaign_label(campaign)} - %OC"] = table[f"{campaign_label(campaign)} - OC"].apply(lambda value: f"{(100 * value / max(len(points), 1)):.0f}%")
    ordered_cols = ["Táxon"]
    for campaign in campaigns:
        ordered_cols.extend([f"{campaign_label(campaign)} - {p}" for p in points])
        ordered_cols.extend([f"{campaign_label(campaign)} - OC", f"{campaign_label(campaign)} - %OC"])
    return table[ordered_cols].sort_values("Táxon").reset_index(drop=True)


def build_richness_by_point(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    richness = df.groupby(["nome_campanha", "nome_ponto"])["nome_cientifico"].nunique().reset_index(name="riqueza")
    return complete_campaign_point(richness, campaigns, points, "riqueza")


def build_abundance_by_point(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    abundance = df.groupby(["nome_campanha", "nome_ponto"])["contagem"].sum().reset_index(name="abundancia_total")
    return complete_campaign_point(abundance, campaigns, points, "abundancia_total")


def build_richness_by_order(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.assign(ordem_plot=df.apply(taxonomic_level_label, axis=1))
        .groupby("ordem_plot")["nome_cientifico"]
        .nunique()
        .reset_index(name="Número de táxons")
        .rename(columns={"ordem_plot": "Ordem"})
        .sort_values("Número de táxons", ascending=False)
        .reset_index(drop=True)
    )
    return out


def build_abundance_order(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = df.copy()
    work["ordem_plot"] = work.apply(taxonomic_level_label, axis=1)
    orders = work.groupby("ordem_plot")["contagem"].sum().sort_values(ascending=False).index.tolist()
    abundance = work.groupby(["nome_campanha", "nome_ponto", "ordem_plot"])["contagem"].sum().reset_index(name="abundancia")
    base = pd.MultiIndex.from_product([campaigns, points, orders], names=["nome_campanha", "nome_ponto", "ordem_plot"]).to_frame(index=False)
    abundance = base.merge(abundance, on=["nome_campanha", "nome_ponto", "ordem_plot"], how="left").fillna({"abundancia": 0})
    totals = abundance.groupby(["nome_campanha", "nome_ponto"])["abundancia"].transform("sum").replace(0, np.nan)
    abundance["abundancia_relativa_pct"] = (abundance["abundancia"] / totals * 100).fillna(0)
    pivot_abs = abundance.pivot_table(index=["nome_campanha", "nome_ponto"], columns="ordem_plot", values="abundancia", aggfunc="sum", fill_value=0).reset_index()
    pivot_rel = abundance.pivot_table(index=["nome_campanha", "nome_ponto"], columns="ordem_plot", values="abundancia_relativa_pct", aggfunc="sum", fill_value=0).reset_index()
    return pivot_abs, pivot_rel


def build_abundance_taxon(df: pd.DataFrame, campaigns: list[str]) -> pd.DataFrame:
    abundance = df.groupby(["nome_campanha", "nome_cientifico"])["contagem"].sum().reset_index(name="abundancia")
    taxa = abundance.groupby("nome_cientifico")["abundancia"].sum().sort_values(ascending=False).index.tolist()
    base = pd.MultiIndex.from_product([campaigns, taxa], names=["nome_campanha", "nome_cientifico"]).to_frame(index=False)
    out = base.merge(abundance, on=["nome_campanha", "nome_cientifico"], how="left").fillna({"abundancia": 0})
    out["campanha_label"] = out["nome_campanha"].map(campaign_label)
    return out


def is_ept(row: pd.Series) -> bool:
    return str(row.get("ordem", "")).strip() in EPT_ORDERS


def is_chol(row: pd.Series) -> bool:
    text = " ".join(str(row.get(col, "")) for col in ["nome_cientifico", "familia", "classe", "ordem"]).casefold()
    return "chironomidae" in text or "oligochaeta" in text or "oligoqueta" in text


def build_bioindicators(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    rows = []
    for campaign in campaigns:
        for point in points:
            local = df[(df["nome_campanha"] == campaign) & (df["nome_ponto"] == point)].copy()
            total = float(local["contagem"].sum()) if not local.empty else 0.0
            positive = local[local["contagem"] > 0].copy()
            family_scores = (
                positive.groupby("familia_bmwp", dropna=False)["bmwp_score"].max()
                if not positive.empty
                else pd.Series(dtype=float)
            )
            ept = positive[positive.apply(is_ept, axis=1)] if not positive.empty else positive
            chol = positive[positive.apply(is_chol, axis=1)] if not positive.empty else positive
            rows.append(
                {
                    "nome_campanha": campaign,
                    "campanha_label": campaign_label(campaign),
                    "nome_ponto": point,
                    "abundancia_total": total,
                    "riqueza_total": int(positive["nome_cientifico"].nunique()) if not positive.empty else 0,
                    "BMWP": float(family_scores.sum()) if not family_scores.empty else 0.0,
                    "familias_bmwp": int(len(family_scores)),
                    "abundancia_EPT": float(ept["contagem"].sum()) if not ept.empty else 0.0,
                    "riqueza_EPT": int(ept["nome_cientifico"].nunique()) if not ept.empty else 0,
                    "EPT (%)": float(ept["contagem"].sum() / total * 100) if total > 0 and not ept.empty else 0.0,
                    "abundancia_CHOL": float(chol["contagem"].sum()) if not chol.empty else 0.0,
                    "CHOL (%)": float(chol["contagem"].sum() / total * 100) if total > 0 and not chol.empty else 0.0,
                }
            )
    return pd.DataFrame(rows)


def plot_panel_bars(
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
        bars = ax.bar(x, values, width=0.62, color=colors[i % len(colors)], edgecolor="black", linewidth=0.8, zorder=3)
        for bar, value in zip(bars, values):
            if value <= 0 and not integer_axis:
                continue
            ax.text(bar.get_x() + bar.get_width() / 2, float(value) + ymax * 0.018, fmt_number(value, decimals), ha="center", va="bottom", fontsize=12)
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

    colors = [CATEGORY_COLORS[i % len(CATEGORY_COLORS)] for i in range(len(values))]
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
    ax.legend(wedges, plot_df[category_col].astype(str).tolist(), loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=14)
    ax.text(0, 0, f"Total\n{total}", ha="center", va="center", fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    fig.subplots_adjust(left=0.02, right=0.78, bottom=0.06, top=0.96)
    return save_fig(fig, out_name)


def plot_stacked_category(pivot_df: pd.DataFrame, *, campaigns: list[str], points: list[str], value_label: str, out_name: str, relative: bool = False) -> Path:
    categories = [c for c in pivot_df.columns if c not in {"nome_campanha", "nome_ponto"}]
    colors = {cat: CATEGORY_COLORS[i % len(CATEGORY_COLORS)] for i, cat in enumerate(categories)}
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=not relative)
    axes = np.atleast_1d(axes).tolist()
    for ax, campaign in zip(axes, campaigns):
        local = pivot_df[pivot_df["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points, fill_value=0)
        x = np.arange(len(points))
        bottom = np.zeros(len(points))
        for cat in categories:
            values = pd.to_numeric(local[cat], errors="coerce").fillna(0).to_numpy(dtype=float)
            ax.bar(x, values, bottom=bottom, label=cat, color=colors[cat], edgecolor="white", linewidth=0.6, zorder=3)
            bottom += values
        ax.set_xticks(x)
        ax.set_xticklabels(points, rotation=45, ha="right")
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        if relative:
            ax.set_ylim(0, 100)
        style_box_axes(ax, xlabel="Ponto amostral", ylabel=value_label if ax is axes[0] else "")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.975), ncol=min(len(labels), 5), frameon=False, fontsize=11)
    fig.subplots_adjust(left=0.075, right=0.995, bottom=0.16, top=0.74, wspace=0.12)
    return save_fig(fig, out_name)


def plot_taxon_horizontal(df_taxon: pd.DataFrame, *, out_name: str, unit: str, top_n: int = 20) -> Path:
    totals = df_taxon.groupby("nome_cientifico")["abundancia"].sum().sort_values(ascending=False)
    selected = totals.head(top_n).index.tolist()
    taxa_order = list(reversed(selected))
    campaigns = sorted(df_taxon["nome_campanha"].unique().tolist(), key=campaign_key)
    pivot = (
        df_taxon[df_taxon["nome_cientifico"].isin(selected)]
        .pivot_table(index="nome_cientifico", columns="nome_campanha", values="abundancia", aggfunc="sum", fill_value=0)
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
        bars = ax.barh(y, values, height=0.64, color=colors[i % len(colors)], edgecolor="black", linewidth=0.8, zorder=3)
        for bar, value in zip(bars, values):
            if value <= 0:
                continue
            ax.text(float(value) + xmax * 0.014, bar.get_y() + bar.get_height() / 2, fmt_number(value, 0), va="center", ha="left", fontsize=10)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=10)
        apply_taxon_tick_styles(labels, ax.get_yticklabels())
        ax.set_xlim(0, xmax * 1.15)
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        style_box_axes(ax, xlabel=f"Abundância ({unit})", ylabel="Táxon" if ax is axes[0] else "")
        ax.grid(axis="x", linestyle="--", linewidth=0.7, color="#E8E8E8", alpha=0.75)
        ax.grid(axis="y", color="#EFEFEF", linestyle="-", linewidth=0.6, alpha=0.8)
        if ax is not axes[0]:
            ax.tick_params(labelleft=False)
    fig.subplots_adjust(left=0.18, right=0.985, bottom=0.14, top=0.84, wspace=0.10)
    return save_fig(fig, out_name)


def build_matrix(df: pd.DataFrame, *, campaigns: list[str], points: list[str], positive_only: bool = True) -> pd.DataFrame:
    ordered_samples = [sample_label(c, p) for c in campaigns for p in points]
    mat = (
        df.assign(amostra_label=[sample_label(c, p) for c, p in zip(df["nome_campanha"], df["nome_ponto"])])
        .pivot_table(index="amostra_label", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0)
        .reindex(index=ordered_samples, fill_value=0)
        .fillna(0)
    )
    if positive_only:
        mat = mat.loc[mat.sum(axis=1) > 0]
    return mat


def build_point_matrix(df: pd.DataFrame, *, points: list[str], positive_only: bool = True) -> pd.DataFrame:
    mat = (
        df.pivot_table(index="nome_ponto", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0)
        .reindex(index=points, fill_value=0)
        .fillna(0)
    )
    if positive_only:
        mat = mat.loc[mat.sum(axis=1) > 0]
    return mat


def plot_taxon_heatmap(df: pd.DataFrame, *, campaigns: list[str], points: list[str], out_name: str, unit: str, top_n: int = 20) -> tuple[Path, pd.DataFrame]:
    ordered_samples = [(c, p) for c in campaigns for p in points]
    sample_cols = [sample_label(c, p) for c, p in ordered_samples]
    totals = df.groupby("nome_cientifico")["contagem"].sum().sort_values(ascending=False)
    taxa_all = totals.index.tolist()
    mat_all = (
        df.assign(amostra_label=[sample_label(c, p) for c, p in zip(df["nome_campanha"], df["nome_ponto"])])
        .pivot_table(index="nome_cientifico", columns="amostra_label", values="contagem", aggfunc="sum", fill_value=0)
        .reindex(index=taxa_all, columns=sample_cols, fill_value=0)
        .fillna(0)
    )
    out_df = mat_all.reset_index().rename(columns={"nome_cientifico": "Táxon"})
    mat = mat_all.loc[totals.head(top_n).index.tolist()]
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
        ax.set_xticklabels(points, rotation=90, ha="center", fontsize=11)
        ax.set_yticks(np.arange(len(mat.index)))
        labels = mat.index.tolist()
        ax.set_yticklabels(labels, fontsize=9)
        apply_taxon_tick_styles(labels, ax.get_yticklabels())
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
                ax.text(j, i, fmt_number(value, 0), ha="center", va="center", fontsize=7, color=color)
        for spine in ["top", "right", "left", "bottom"]:
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_color("black")
            ax.spines[spine].set_linewidth(1.2)
    cbar = fig.colorbar(im, ax=axes, fraction=0.030, pad=0.02)
    cbar.set_label(f"Abundância ({unit})", rotation=90, labelpad=12)
    fig.subplots_adjust(left=0.18, right=0.90, bottom=0.18, top=0.84, wspace=0.08)
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


def simpson(counts: np.ndarray) -> float:
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size == 0:
        return 0.0
    p = counts / counts.sum()
    return float(1 - np.sum(p**2))


def build_diversity(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    mat = build_matrix(df, campaigns=campaigns, points=points, positive_only=False)
    rows = []
    for campaign in campaigns:
        for point in points:
            sample = sample_label(campaign, point)
            vec = mat.loc[sample].to_numpy(dtype=float)
            rows.append(
                {
                    "nome_campanha": campaign,
                    "campanha_label": campaign_label(campaign),
                    "nome_ponto": point,
                    "amostra": sample,
                    "riqueza": int((vec > 0).sum()),
                    "abundancia_total": float(vec.sum()),
                    "Shannon_H": shannon(vec),
                    "Pielou_J": pielou(vec),
                    "Simpson_1_D": simpson(vec),
                }
            )
    return pd.DataFrame(rows)


def plot_diversity(diversity: pd.DataFrame, *, campaigns: list[str], points: list[str], out_name: str) -> Path:
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes).tolist()
    x = np.arange(len(points))
    ymax = max(float(diversity["Shannon_H"].max()) if not diversity.empty else 0.0, 0.25)
    legend_handles = []
    legend_labels = []
    for i, (ax1, campaign) in enumerate(zip(axes, campaigns)):
        local = diversity[diversity["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points).fillna({"Shannon_H": 0, "Pielou_J": 0})
        shannon_values = pd.to_numeric(local["Shannon_H"], errors="coerce").fillna(0).to_numpy(dtype=float)
        pielou_values = pd.to_numeric(local["Pielou_J"], errors="coerce").fillna(0).to_numpy(dtype=float)
        bars = ax1.bar(x, shannon_values, color=PRIMARY, edgecolor="black", linewidth=0.8, label="Diversidade (H')", zorder=3)
        ax1.set_xticks(x)
        ax1.set_xticklabels(points, rotation=45, ha="right")
        ax1.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        ax1.set_ylim(0, ymax * 1.25)
        style_box_axes(ax1, xlabel="Ponto amostral", ylabel="Shannon (H')" if ax1 is axes[0] else "")
        if ax1 is not axes[0]:
            ax1.tick_params(labelleft=False)
        for bar, value in zip(bars, shannon_values):
            if value <= 0:
                continue
            ax1.text(bar.get_x() + bar.get_width() / 2, float(value) + ymax * 0.02, f"{value:.2f}", ha="center", va="bottom", fontsize=10)
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
    ax.tick_params(axis="both", labelsize=11)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.08, top=0.84)
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
    return pd.DataFrame(
        {
            "Número de unidades amostrais quantitativas": x_axis,
            "Riqueza observada média": sobs_curves.mean(axis=0),
            "Riqueza estimada média (Jackknife 1)": sest_curves.mean(axis=0),
            "Riqueza estimada desvio padrão": sest_curves.std(axis=0),
        }
    )


def plot_sufficiency(curve: pd.DataFrame, out_name: str) -> Path | None:
    if curve.empty:
        return None
    x = curve["Número de unidades amostrais quantitativas"].to_numpy(dtype=float)
    obs = curve["Riqueza observada média"].to_numpy(dtype=float)
    est = curve["Riqueza estimada média (Jackknife 1)"].to_numpy(dtype=float)
    std = curve["Riqueza estimada desvio padrão"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    ax.plot(x, obs, color=PRIMARY, linewidth=1.4, label="Riqueza observada")
    ax.plot(x, est, color=SECONDARY_DARK, linewidth=1.4, label="Riqueza estimada (Jackknife 1)")
    ax.fill_between(x, np.maximum(est - std, 0), est + std, color=SECONDARY_DARK, alpha=0.18, linewidth=0)
    ax.text(x[-1], obs[-1], fmt_number(obs[-1], 1), ha="left", va="center", fontsize=11, color=PRIMARY)
    ax.text(x[-1], est[-1], fmt_number(est[-1], 1), ha="left", va="center", fontsize=11, color=SECONDARY_DARK)
    style_box_axes(ax, xlabel="Número de unidades amostrais quantitativas", ylabel="Riqueza")
    ax.set_xlim(1, float(max(x)) + 1.0)
    ax.set_ylim(0, max(float(np.nanmax(est + std)) * 1.08, 1.0))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.12, top=0.83)
    return save_fig(fig, out_name)


def plot_bmwp_classes(bio: pd.DataFrame, *, campaigns: list[str], points: list[str], out_name: str) -> Path:
    work = bio.copy()
    work["classe_bmwp"] = work["BMWP"].apply(classify_bmwp)
    ymax = max(float(work["BMWP"].max()) if not work.empty else 0.0, 1.0)
    fig, axes = plt.subplots(1, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_1d(axes).tolist()
    x = np.arange(len(points))
    for ax, campaign in zip(axes, campaigns):
        local = work[work["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points).fillna({"BMWP": 0, "classe_bmwp": "Péssima"})
        values = pd.to_numeric(local["BMWP"], errors="coerce").fillna(0).to_numpy(dtype=float)
        classes = local["classe_bmwp"].astype(str).tolist()
        colors = [bmwp_color(label) for label in classes]
        bars = ax.bar(x, values, width=0.62, color=colors, edgecolor="black", linewidth=0.8, zorder=3)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, float(value) + ymax * 0.018, fmt_number(value, 0), ha="center", va="bottom", fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(points, rotation=45, ha="right")
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=12)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        ax.set_ylim(0, max(90, ymax * 1.20))
        style_box_axes(ax, xlabel="Ponto amostral", ylabel="BMWP" if ax is axes[0] else "")
        if ax is not axes[0]:
            ax.tick_params(labelleft=False)
    legend_labels = [label for label, _, _, _ in BMWP_CLASSES]
    handles = [Patch(facecolor=bmwp_color(label), edgecolor="black", label=label) for label in legend_labels]
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=len(legend_labels), frameon=False, title="Classe BMWP")
    fig.subplots_adjust(left=0.075, right=0.995, bottom=0.16, top=0.77, wspace=0.12)
    return save_fig(fig, out_name)


def plot_ept_chol(bio: pd.DataFrame, *, campaigns: list[str], points: list[str], out_name: str) -> Path:
    fig, axes = plt.subplots(2, len(campaigns), figsize=A4_LANDSCAPE, dpi=DPI, sharey=True)
    axes = np.atleast_2d(axes)
    x = np.arange(len(points))
    ymax = max(float(bio[["EPT (%)", "CHOL (%)"]].to_numpy(dtype=float).max()), 1.0)
    indicators = [("EPT (%)", "EPT", "#2A6F97"), ("CHOL (%)", "CHOL", "#C1121F")]
    for row_idx, (value_col, indicator, color) in enumerate(indicators):
        for col_idx, campaign in enumerate(campaigns):
            ax = axes[row_idx, col_idx]
            local = bio[bio["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points).fillna(0)
            values = local[value_col].to_numpy(dtype=float)
            bars = ax.bar(x, values, width=0.62, color=color, edgecolor="black", linewidth=0.8, zorder=3)
            for bar, value in zip(bars, values):
                if value > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, value + ymax * 0.018, fmt_number(value, 1), ha="center", va="bottom", fontsize=8)
            ax.set_xticks(x)
            ax.set_xticklabels(points, rotation=45, ha="right", fontsize=11)
            ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=15, pad=10)
            ax.set_ylim(0, max(100, ymax * 1.20))
            ax.text(0.02, 0.92, indicator, transform=ax.transAxes, ha="left", va="top", fontsize=13, fontweight="bold", color=color)
            ylabel = "Abundância relativa (%)" if col_idx == 0 else ""
            style_box_axes(ax, xlabel="Ponto amostral" if row_idx == 1 else "", ylabel=ylabel)
            ax.yaxis.label.set_size(13)
            if row_idx == 0:
                ax.tick_params(labelbottom=False)
            if col_idx > 0:
                ax.tick_params(labelleft=False)
    handles = [
        Patch(facecolor="#2A6F97", edgecolor="black", label="EPT (%)"),
        Patch(facecolor="#C1121F", edgecolor="black", label="CHOL (%)"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.105, right=0.995, bottom=0.14, top=0.82, wspace=0.10, hspace=0.34)
    return save_fig(fig, out_name)


def build_synthesis(df: pd.DataFrame, richness_order: pd.DataFrame, abundance_order: pd.DataFrame, bio: pd.DataFrame) -> dict[str, pd.DataFrame]:
    order_totals = abundance_order.drop(columns=["nome_campanha", "nome_ponto"]).sum().sort_values(ascending=False).reset_index()
    order_totals.columns = ["Ordem", "Abundância total"]
    return {
        "riqueza_por_ordem": richness_order,
        "abundancia_por_ordem": order_totals,
        "bioindicadores_por_ponto": bio,
        "resumo_por_campanha": df.groupby("nome_campanha").agg(linhas=("nome_cientifico", "size"), pontos=("nome_ponto", "nunique"), táxons=("nome_cientifico", "nunique"), abundância=("contagem", "sum")).reset_index(),
    }


def write_synthesis_workbook(sheets: dict[str, pd.DataFrame]) -> Path:
    out = OUTPUT_DIR / "15_tabela_sintese_zoobentos.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet_name, data in sheets.items():
            data.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return out


def plot_synthesis(sheets: dict[str, pd.DataFrame], unit: str, out_name: str) -> Path:
    richness = sheets["riqueza_por_ordem"].sort_values("Número de táxons", ascending=True)
    abundance = sheets["abundancia_por_ordem"].sort_values("Abundância total", ascending=True)
    bio = sheets["bioindicadores_por_ponto"]
    bmwp_campaign = bio.groupby("campanha_label")["BMWP"].mean().reset_index()
    ept_campaign = bio.groupby("campanha_label")["EPT (%)"].mean().reset_index()
    fig, axes = plt.subplots(2, 2, figsize=A4_LANDSCAPE, dpi=DPI)
    panels = [
        (axes[0, 0], richness, "Ordem", "Número de táxons", "Riqueza por ordem", "Número de táxons"),
        (axes[0, 1], abundance, "Ordem", "Abundância total", "Abundância por ordem", f"Abundância ({unit})"),
        (axes[1, 0], bmwp_campaign, "campanha_label", "BMWP", "BMWP médio", "BMWP"),
        (axes[1, 1], ept_campaign, "campanha_label", "EPT (%)", "EPT médio", "EPT (%)"),
    ]
    for ax, local, cat_col, value_col, title, xlabel in panels:
        values = pd.to_numeric(local[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        y = np.arange(len(local))
        ax.barh(y, values, color=PRIMARY, edgecolor="black", linewidth=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(local[cat_col].astype(str).tolist(), fontsize=9)
        ax.set_title(title, fontweight="bold", fontsize=11, pad=8)
        style_box_axes(ax, xlabel=xlabel, ylabel="")
        ax.tick_params(axis="both", labelsize=9)
        xmax = max(float(values.max()) if len(values) else 0.0, 1.0)
        ax.set_xlim(0, xmax * 1.22)
        for yi, value in zip(y, values):
            ax.text(float(value) + xmax * 0.02, yi, fmt_number(value, 1), va="center", ha="left", fontsize=8)
    fig.suptitle("Síntese dos zoobentos - BRAAEG001", fontweight="bold", fontsize=14)
    fig.subplots_adjust(left=0.16, right=0.97, bottom=0.10, top=0.84, wspace=0.45, hspace=0.48)
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
    out = AUDIT_DIR / f"{tag}_contact_sheet_figuras_zoobentos_a4_paisagem.png"
    sheet.save(out)
    return out


def write_html_report(metrics: dict, unit: str) -> Path:
    out = OUTPUT_DIR / "relatorio_tecnico_zoobentos_braaeg001.html"
    figures = [
        ("02_grafico_riqueza_por_ponto_zoobentos.png", "Riqueza por ponto"),
        ("03_grafico_abundancia_total_por_ponto_zoobentos.png", "Abundância total por ponto"),
        ("06_grafico_abundancia_ordem_por_ponto_zoobentos.png", "Abundância por ordem"),
        ("08_grafico_abundancia_por_taxon_zoobentos.png", "Abundância por táxon"),
        ("09_grafico_abundancia_taxon_ponto_zoobentos.png", "Abundância por táxon e ponto"),
        ("10_grafico_diversidade_alfa_zoobentos.png", "Diversidade alfa"),
        ("11_dendrograma_similaridade_zoobentos.png", "Similaridade"),
        ("11B_dendrograma_similaridade_pontos_zoobentos.png", "Similaridade por ponto"),
        ("12_curva_suficiencia_amostral_zoobentos.png", "Suficiência amostral"),
        ("13_grafico_bmwp_por_ponto_zoobentos.png", "BMWP por ponto"),
        ("14_grafico_ept_chol_por_ponto_zoobentos.png", "EPT e CHOL"),
        ("15_grafico_sintese_zoobentos.png", "Síntese"),
    ]
    figure_blocks = []
    for name, caption in figures:
        if (OUTPUT_DIR / name).exists():
            figure_blocks.append(
                f'<figure><img src="{html.escape(name)}" alt="{html.escape(caption)}">'
                f"<figcaption>{html.escape(caption)}</figcaption></figure>"
            )
    body = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Resultados de Zoobentos - BRAAEG001</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f1f1f; }}
    h1, h2 {{ color: #11420C; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }}
    figure {{ margin: 0; }}
    img {{ width: 100%; border: 1px solid #ddd; }}
    figcaption {{ font-weight: 700; margin-top: 8px; }}
    table {{ border-collapse: collapse; margin: 16px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
  </style>
</head>
<body>
  <h1>Resultados de Zoobentos - BRAAEG001</h1>
  <p>Pacote gerado em A4 paisagem, com painéis por estação/campanha nos gráficos de comparação por ponto.</p>
  <h2>Premissas técnicas</h2>
  <ul>
    <li>Registros de zoobentos tratados como quantitativos.</li>
    <li>Abundância consolidada em <strong>{html.escape(unit)}</strong>.</li>
    <li>BMWP calculado por famílias únicas presentes em cada ponto e campanha.</li>
    <li>BMWP exibido com cores e legenda das classes do indicador.</li>
    <li>EPT calculado por abundância relativa de Ephemeroptera, Plecoptera e Trichoptera.</li>
    <li>CHOL calculado por abundância relativa de Chironomidae e Oligochaeta.</li>
    <li>Similaridade de Bray-Curtis apresentada por amostra e por ponto sem distinguir campanha.</li>
    <li>Classificações sem ordem informada são rotuladas pelo nível taxonômico válido disponível.</li>
  </ul>
  <h2>Resumo</h2>
  <table>
    <tr><th>Indicador</th><th>Valor</th></tr>
    <tr><td>Linhas consolidadas</td><td>{metrics["rows_consolidated"]}</td></tr>
    <tr><td>Táxons</td><td>{metrics["taxa_total"]}</td></tr>
    <tr><td>Abundância total</td><td>{fmt_number(metrics["abundance_total"], 0)} {html.escape(unit)}</td></tr>
    <tr><td>Táxon dominante</td><td>{html.escape(metrics["dominant_taxon"])}</td></tr>
    <tr><td>Ordem dominante</td><td>{html.escape(metrics["dominant_order"])}</td></tr>
    <tr><td>BMWP máximo</td><td>{fmt_number(metrics["max_bmwp"], 0)}</td></tr>
  </table>
  <h2>Figuras</h2>
  <div class="grid">
    {"".join(figure_blocks)}
  </div>
</body>
</html>
"""
    validate_html_ptbr(body)
    out.write_text(body, encoding="utf-8")
    return out


BAD_HTML_TERMS = [
    "diagn" + "ostico",
    "taxons",
    "familias",
    "abundancia",
    "suficiencia",
    "relatorio",
    "graficos",
]


def validate_html_ptbr(text: str) -> None:
    visible = re.sub(r"<code>.*?</code>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    visible = re.sub(r"<[^>]+>", " ", visible)
    found = [term for term in BAD_HTML_TERMS if term in visible]
    if found:
        raise ValueError("Texto visível sem acentuação pt-BR no HTML: " + ", ".join(found))


def build_metrics(
    df: pd.DataFrame,
    richness_point: pd.DataFrame,
    abundance_point: pd.DataFrame,
    richness_order: pd.DataFrame,
    abundance_taxon: pd.DataFrame,
    abundance_order: pd.DataFrame,
    bio: pd.DataFrame,
    suff_curve: pd.DataFrame,
    unit: str,
) -> dict:
    max_rich = richness_point.sort_values("riqueza", ascending=False).iloc[0]
    max_abund = abundance_point.sort_values("abundancia_total", ascending=False).iloc[0]
    taxon_totals = abundance_taxon.groupby("nome_cientifico")["abundancia"].sum().sort_values(ascending=False)
    order_totals = abundance_order.drop(columns=["nome_campanha", "nome_ponto"]).sum().sort_values(ascending=False)
    max_bmwp = bio.sort_values("BMWP", ascending=False).iloc[0]
    suff_obs = float(suff_curve["Riqueza observada média"].iloc[-1]) if not suff_curve.empty else 0.0
    suff_est = float(suff_curve["Riqueza estimada média (Jackknife 1)"].iloc[-1]) if not suff_curve.empty else 0.0
    return {
        "rows_consolidated": int(len(df)),
        "campaigns": sorted(df["nome_campanha"].unique().tolist(), key=campaign_key),
        "campaigns_text": ", ".join(campaign_label(c) for c in sorted(df["nome_campanha"].unique().tolist(), key=campaign_key)),
        "points_count": int(df["nome_ponto"].nunique()),
        "taxa_total": int(df["nome_cientifico"].nunique()),
        "families_total": int(df["familia_bmwp"].nunique()),
        "orders_total": int(df["ordem"].replace("", np.nan).nunique()),
        "abundance_total": float(df["contagem"].sum()),
        "unit": unit,
        "max_richness": float(max_rich["riqueza"]),
        "max_richness_point": str(max_rich["nome_ponto"]),
        "max_richness_campaign": campaign_label(str(max_rich["nome_campanha"])),
        "max_abundance": float(max_abund["abundancia_total"]),
        "max_abundance_point": str(max_abund["nome_ponto"]),
        "max_abundance_campaign": campaign_label(str(max_abund["nome_campanha"])),
        "dominant_taxon": str(taxon_totals.index[0]) if not taxon_totals.empty else "",
        "dominant_taxon_abundance": float(taxon_totals.iloc[0]) if not taxon_totals.empty else 0.0,
        "dominant_order": str(order_totals.index[0]) if not order_totals.empty else "",
        "dominant_order_abundance": float(order_totals.iloc[0]) if not order_totals.empty else 0.0,
        "max_bmwp": float(max_bmwp["BMWP"]),
        "max_bmwp_point": str(max_bmwp["nome_ponto"]),
        "max_bmwp_campaign": campaign_label(str(max_bmwp["nome_campanha"])),
        "mean_ept_pct": float(bio["EPT (%)"].mean()),
        "mean_chol_pct": float(bio["CHOL (%)"].mean()),
        "suff_obs": suff_obs,
        "suff_est": suff_est,
    }


def build_manifest_and_validation(generated_files: list[Path], metrics: dict, tag: str) -> tuple[Path, Path, Path, Path]:
    manifest_json = OUTPUT_DIR / "manifesto_entrega_zoobentos_braaeg001.json"
    manifest_xlsx = OUTPUT_DIR / "manifesto_entrega_zoobentos_braaeg001.xlsx"
    manifest_md = OUTPUT_DIR / "manifesto_entrega_zoobentos_braaeg001.md"
    validation_json = OUTPUT_DIR / "validacao_entrega_zoobentos_braaeg001.json"
    files = []
    for path in sorted([p for p in OUTPUT_DIR.iterdir() if p.is_file() and p.name != "desktop.ini"], key=lambda p: p.name):
        if path.name.startswith("manifesto_entrega_zoobentos_braaeg001"):
            continue
        row = {"arquivo": path.name, "path": str(path), "tamanho_bytes": path.stat().st_size, "sha256": sha256(path)}
        if path.suffix.lower() == ".png":
            row.update(image_info(path))
        files.append(row)
    missing = [str(p) for p in generated_files if not p.exists()]
    zero_size = [row["arquivo"] for row in files if row["tamanho_bytes"] <= 0]
    figure_checks = [image_info(OUTPUT_DIR / name) for name in FINAL_FIGURES if (OUTPUT_DIR / name).exists()]
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
            "BMWP calculado por famílias únicas presentes em cada ponto/campanha.",
            "BMWP exibido com cores de classe do índice.",
            "Figura 11B adicionada com similaridade de Bray-Curtis por ponto, sem distinguir campanha.",
            "Figura 16 adicionada como minimapa conjunto de BMWP, EPT e CHOL, separado por C01-Chuva e C02-Seca.",
            "Classificações sem ordem informada usam o nível taxonômico válido disponível, por exemplo Oligochaeta (Classe).",
            "Figuras 08 e 09 mostram os 20 táxons mais abundantes para preservar legibilidade em A4 paisagem; as planilhas mantêm todos os táxons.",
        ],
    }
    validation_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"schema_version": "1.0", "generated_at": now_iso(), "project_code": PROJECT_CODE, "group": GROUP_DISPLAY, "output_dir": str(OUTPUT_DIR), "metrics": metrics, "validation": validation, "files": files}
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(files).to_excel(manifest_xlsx, index=False, engine="openpyxl")
    lines = [
        f"# Manifesto de entrega - Zoobentos - {PROJECT_CODE}",
        "",
        f"- gerado em: {manifest['generated_at']}",
        f"- pasta: `{OUTPUT_DIR}`",
        f"- validação: `{validation['status']}`",
        f"- arquivos listados: {len(files)}",
        f"- figuras finais: {len(figure_checks)}",
        "",
        "## Arquivos",
        "",
    ]
    for row in files:
        lines.append(f"- `{row['arquivo']}` ({row['tamanho_bytes']} bytes)")
    manifest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_json, manifest_xlsx, manifest_md, validation_json


def generate(env_file: str | None = ".env") -> dict:
    setup_rc()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    tag = now_tag()
    generated: list[Path] = []
    df = load_data(env_file)
    campaigns, points = campaigns_points(df)
    unit = unit_label(df)

    generated.append(write_excel(df.drop(columns=["campanha_label", "amostra_label"], errors="ignore"), "00_base_consolidada_zoobentos.xlsx", sheet_name="base_consolidada"))
    composition = build_composition(df)
    generated.append(write_excel(composition, "01_tabela_composicao_zoobentos.xlsx", sheet_name="composicao"))
    occurrence = build_occurrence(df, campaigns, points)
    generated.append(write_excel(occurrence, "01_tabela_ocorrencia_zoobentos.xlsx", sheet_name="ocorrencia"))

    richness_point = build_richness_by_point(df, campaigns, points)
    generated.append(write_excel(richness_point, "02_df_riqueza_por_ponto_zoobentos.xlsx"))
    generated.append(plot_panel_bars(richness_point, value_col="riqueza", ylabel="Riqueza taxonômica", out_name="02_grafico_riqueza_por_ponto_zoobentos.png", decimals=0, integer_axis=True))

    abundance_point = build_abundance_by_point(df, campaigns, points)
    generated.append(write_excel(abundance_point, "03_df_abundancia_total_por_ponto_zoobentos.xlsx"))
    generated.append(plot_panel_bars(abundance_point, value_col="abundancia_total", ylabel=f"Abundância total ({unit})", out_name="03_grafico_abundancia_total_por_ponto_zoobentos.png", decimals=0, integer_axis=True))

    richness_order = build_richness_by_order(df)
    generated.append(write_excel(richness_order, "04_df_riqueza_por_ordem_zoobentos.xlsx"))
    generated.append(plot_taxon_bar(richness_order, category_col="Ordem", value_col="Número de táxons", xlabel="Ordem", ylabel="Número de táxons", out_name="04_grafico_riqueza_ordem_barras_zoobentos.png"))
    generated.append(plot_donut(richness_order, category_col="Ordem", value_col="Número de táxons", out_name="05_grafico_riqueza_ordem_rosca_zoobentos.png"))

    abundance_order, abundance_order_rel = build_abundance_order(df, campaigns, points)
    generated.append(write_excel(abundance_order, "06_df_abundancia_ordem_por_ponto_zoobentos.xlsx"))
    generated.append(plot_stacked_category(abundance_order, campaigns=campaigns, points=points, value_label=f"Abundância ({unit})", out_name="06_grafico_abundancia_ordem_por_ponto_zoobentos.png"))
    generated.append(write_excel(abundance_order_rel, "07_df_abundancia_relativa_ordem_por_ponto_zoobentos.xlsx"))
    generated.append(plot_stacked_category(abundance_order_rel, campaigns=campaigns, points=points, value_label="Abundância relativa (%)", out_name="07_grafico_abundancia_relativa_ordem_por_ponto_zoobentos.png", relative=True))

    abundance_taxon = build_abundance_taxon(df, campaigns)
    generated.append(write_excel(abundance_taxon, "08_df_abundancia_por_taxon_zoobentos.xlsx"))
    generated.append(plot_taxon_horizontal(abundance_taxon, out_name="08_grafico_abundancia_por_taxon_zoobentos.png", unit=unit))

    heatmap_png, heatmap_df = plot_taxon_heatmap(df, campaigns=campaigns, points=points, out_name="09_grafico_abundancia_taxon_ponto_zoobentos.png", unit=unit)
    generated.append(write_excel(heatmap_df, "09_df_abundancia_taxon_ponto_zoobentos.xlsx"))
    generated.append(heatmap_png)

    diversity = build_diversity(df, campaigns, points)
    generated.append(write_excel(diversity, "10_df_diversidade_alfa_zoobentos.xlsx"))
    generated.append(plot_diversity(diversity, campaigns=campaigns, points=points, out_name="10_grafico_diversidade_alfa_zoobentos.png"))

    mat = build_matrix(df, campaigns=campaigns, points=points, positive_only=True)
    mat.index.name = "Amostra"
    generated.append(write_excel(mat.reset_index(), "11_df_matriz_comunidade_zoobentos.xlsx"))
    dendro_png, dist_sq = plot_dendrogram(mat, "11_dendrograma_similaridade_zoobentos.png")
    if dist_sq is not None:
        dist_sq.index.name = "Amostra"
        generated.append(write_excel(dist_sq.reset_index(), "11_df_distancias_braycurtis_zoobentos.xlsx"))
    if dendro_png is not None:
        generated.append(dendro_png)

    mat_points = build_point_matrix(df, points=points, positive_only=True)
    mat_points.index.name = "Ponto"
    generated.append(write_excel(mat_points.reset_index(), "11B_df_matriz_comunidade_pontos_zoobentos.xlsx"))
    dendro_points_png, dist_points_sq = plot_dendrogram(mat_points, "11B_dendrograma_similaridade_pontos_zoobentos.png")
    if dist_points_sq is not None:
        dist_points_sq.index.name = "Ponto"
        generated.append(write_excel(dist_points_sq.reset_index(), "11B_df_distancias_braycurtis_pontos_zoobentos.xlsx"))
    if dendro_points_png is not None:
        generated.append(dendro_points_png)

    suff_curve = build_sufficiency(mat)
    generated.append(write_excel(suff_curve, "12_df_curva_suficiencia_zoobentos.xlsx"))
    suff_png = plot_sufficiency(suff_curve, "12_curva_suficiencia_amostral_zoobentos.png")
    if suff_png is not None:
        generated.append(suff_png)

    bio = build_bioindicators(df, campaigns, points)
    generated.append(write_excel(bio, "13_df_bioindicadores_bmwp_ept_chol_zoobentos.xlsx"))
    generated.append(plot_bmwp_classes(bio, campaigns=campaigns, points=points, out_name="13_grafico_bmwp_por_ponto_zoobentos.png"))
    generated.append(plot_ept_chol(bio, campaigns=campaigns, points=points, out_name="14_grafico_ept_chol_por_ponto_zoobentos.png"))

    dwc_files: list[str] = []
    export_darwincore_ief(
        df=df.drop(columns=["campanha_label", "amostra_label"], errors="ignore"),
        group=GROUP_DISPLAY,
        output_dir=OUTPUT_DIR,
        generated_files=dwc_files,
        output_filename="DarwinCore_IEF_Zoobentos_BRAAEG001.xlsx",
        municipality_default="Barão de Cocais",
        county_default="Barão de Cocais",
    )
    generated.extend(Path(p) for p in dwc_files)

    synthesis_sheets = build_synthesis(df, richness_order, abundance_order, bio)
    generated.append(write_synthesis_workbook(synthesis_sheets))
    generated.append(plot_synthesis(synthesis_sheets, unit, "15_grafico_sintese_zoobentos.png"))

    metrics = build_metrics(df, richness_point, abundance_point, richness_order, abundance_taxon, abundance_order, bio, suff_curve, unit)
    report = write_html_report(metrics, unit)
    generated.append(report)
    manifest_files = build_manifest_and_validation(generated, metrics, tag)
    generated.extend(manifest_files)
    contact_sheet = make_contact_sheet(tag)

    figure_infos = [image_info(OUTPUT_DIR / name) for name in FINAL_FIGURES if (OUTPUT_DIR / name).exists()]
    file_rows = []
    for path in generated:
        if path.exists():
            row = {"arquivo": path.name, "path": str(path), "tamanho_bytes": path.stat().st_size, "sha256": sha256(path)}
            if path.suffix.lower() == ".png":
                row.update(image_info(path))
            file_rows.append(row)
    audit = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": GROUP_DISPLAY,
        "action": "generate_bentos_results_a4_landscape",
        "output_dir": str(OUTPUT_DIR),
        "figures_count": len(figure_infos),
        "figures_ok": sum(1 for row in figure_infos if row["nonblank"] and row["largura_px"] == 7014 and row["altura_px"] == 4962),
        "files_count": len(file_rows),
        "contact_sheet": str(contact_sheet),
        "metrics": metrics,
        "files": file_rows,
    }
    audit_json = AUDIT_DIR / f"{tag}_geracao_resultados_zoobentos_a4_paisagem.json"
    audit_xlsx = AUDIT_DIR / f"{tag}_geracao_resultados_zoobentos_a4_paisagem.xlsx"
    audit["audit_json"] = str(audit_json)
    audit["audit_xlsx"] = str(audit_xlsx)
    audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(file_rows).to_excel(audit_xlsx, index=False, engine="openpyxl")
    metadata = {
        "generated_at": audit["generated_at"],
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": GROUP_DISPLAY,
        "output_dir": str(OUTPUT_DIR),
        "source": "public.resultados_zoobentos / public.biota_analise_consolidada",
        "script": str(Path(__file__).resolve()),
        "audit_json": str(audit_json),
        "audit_xlsx": str(audit_xlsx),
        "contact_sheet": str(contact_sheet),
        "premises": [
            "Figuras em A4 paisagem, 600 dpi.",
            "Painéis por estação/campanha nas comparações por ponto.",
            "BMWP calculado por famílias únicas por ponto/campanha.",
            "EPT e CHOL calculados por abundância relativa.",
        ],
    }
    (AUDIT_DIR / "execution_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (AUDIT_DIR / f"{tag}_execution_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return audit


if __name__ == "__main__":
    result = generate()
    print(
        json.dumps(
            {
                "audit_json": result["audit_json"],
                "audit_xlsx": result["audit_xlsx"],
                "contact_sheet": result["contact_sheet"],
                "figures_count": result["figures_count"],
                "figures_ok": result["figures_ok"],
                "files_count": result["files_count"],
                "output_dir": result["output_dir"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )

