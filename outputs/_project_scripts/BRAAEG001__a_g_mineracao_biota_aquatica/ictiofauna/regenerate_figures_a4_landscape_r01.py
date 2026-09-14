from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter, MaxNLocator
from PIL import Image, ImageDraw
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform


ROOT = Path(__file__).resolve().parents[4]
OUTPUT_DIR = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/"
    "A&G Minera\u00e7\u00e3o/resultados/migracao_biota/ictiofauna"
)
AUDIT_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAEG001__a_g_mineracao_biota_aquatica" / "ictiofauna"

DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
PRIMARY = "#237C1A"
SECONDARY = "#19FF00"
PRIMARY_DARK = "#11420C"
SECONDARY_DARK = "#6A8F63"
GRID = "#D8E9D4"

FINAL_FIGURES = [
    "02_grafico_riqueza_por_ponto_ictiofauna.png",
    "03_grafico_abundancia_por_ponto_ictiofauna.png",
    "04_grafico_riqueza_familia_barras_ictiofauna.png",
    "04_grafico_riqueza_ordem_barras_ictiofauna.png",
    "05_grafico_riqueza_familia_rosca_ictiofauna.png",
    "05_grafico_riqueza_ordem_rosca_ictiofauna.png",
    "06_grafico_cpuen_por_ponto_ictiofauna.png",
    "07_grafico_cpueb_por_ponto_ictiofauna.png",
    "08_grafico_cpuen_por_especie_ictiofauna.png",
    "08B_grafico_cpuen_por_especie_ponto_ictiofauna.png",
    "09_grafico_cpueb_por_especie_ictiofauna.png",
    "09B_grafico_cpueb_por_especie_ponto_ictiofauna.png",
    "10_grafico_diversidade_alfa_ictiofauna.png",
    "11_dendrograma_similaridade_ictiofauna_seca_chuva_somadas.png",
    "12_curva_suficiencia_amostral_ictiofauna.png",
    "14_grafico_sintese_ecologica_ictiofauna.png",
]

BAD_VISIBLE_PTBR_LABELS = [
    "Abund" + "ancia total",
    "Abund" + "ancia total (n de individuos)",
    "Comportamento migr" + "atorio",
    "Esp" + "ecie",
    "Fam" + "ilia",
    "Num" + "ero de especies",
    "Num" + "ero de unidades amostrais",
    "Riqueza taxon" + "omica",
    "Sint" + "ese ecol" + "ogica da ictiofauna - BRAAEG001",
]


def validate_ptbr_labels() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    found = []
    for label in BAD_VISIBLE_PTBR_LABELS:
        if f'"{label}"' in source or f"'{label}'" in source:
            found.append(label)
    if found:
        joined = ", ".join(found)
        raise ValueError(f"Rótulos visíveis sem acentuação pt-BR: {joined}")


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


def read_xlsx(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_excel(OUTPUT_DIR / name, **kwargs)


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


def style_box_axes(ax, *, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", which="major", linestyle="--", linewidth=0.8, color=GRID, alpha=0.95)
    ax.grid(axis="x", visible=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.2)
    ax.tick_params(axis="both", direction="out", length=4, width=1.0, colors="black")
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=10)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=8)


def save_fig(fig, out_name: str) -> None:
    fig.savefig(OUTPUT_DIR / out_name, dpi=DPI, facecolor="white")
    plt.close(fig)


def palette(n: int) -> list[str]:
    if n <= 1:
        return [PRIMARY]
    start = np.array(mcolors.to_rgb(PRIMARY))
    end = np.array(mcolors.to_rgb(SECONDARY))
    return [mcolors.to_hex(start + (end - start) * (i / (n - 1))) for i in range(n)]


def label_color_for_value(value: float, vmax: float) -> str:
    if not np.isfinite(vmax) or vmax <= 0:
        return "black"
    return "black" if value >= 0.65 * vmax else "white"


def plot_grouped_campaign_bars(
    table: pd.DataFrame,
    *,
    value_col: str,
    ylabel: str,
    out_name: str,
    decimals: int,
    integer_axis: bool = False,
) -> None:
    table = table.copy()
    table["nome_campanha"] = table["nome_campanha"].astype(str).str.strip()
    table["nome_ponto"] = table["nome_ponto"].astype(str).str.strip()
    table[value_col] = pd.to_numeric(table[value_col], errors="coerce").fillna(0)
    campaigns = sorted(table["nome_campanha"].dropna().unique().tolist(), key=campaign_key)
    points = sorted(table["nome_ponto"].dropna().unique().tolist(), key=point_key)
    full = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"])
    table = table.set_index(["nome_campanha", "nome_ponto"]).reindex(full, fill_value=0).reset_index()
    pivot = table.pivot_table(
        index="nome_ponto",
        columns="nome_campanha",
        values=value_col,
        aggfunc="sum",
        fill_value=0,
    ).reindex(index=points, columns=campaigns, fill_value=0)

    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    x = np.arange(len(points))
    width = 0.8 / max(len(campaigns), 1)
    colors = palette(max(len(campaigns), 1))
    max_value = float(pivot.to_numpy(dtype=float).max()) if not pivot.empty else 0.0
    label_offset = max(0.035, max_value * 0.012)
    handles = []
    labels = []

    for i, campaign in enumerate(campaigns):
        values = pivot[campaign].to_numpy(dtype=float)
        bars = ax.bar(
            x + (i - (len(campaigns) - 1) / 2) * width,
            values,
            width=width,
            color=colors[i],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        handles.append(bars[0])
        labels.append(campaign_label(campaign))
        for bar, value in zip(bars, values):
            text = f"{int(round(float(value)))}" if decimals == 0 else f"{float(value):.{decimals}f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                float(value) + label_offset,
                text,
                ha="center",
                va="bottom",
                fontsize=12,
                color="black",
                zorder=4,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(points, rotation=45, ha="right")
    if integer_axis:
        y_tick_max = max(1, int(math.ceil(max_value)))
        ax.yaxis.set_major_locator(FixedLocator(list(range(0, y_tick_max + 1))))
        ax.yaxis.set_major_formatter(FixedFormatter([str(i) for i in range(0, y_tick_max + 1)]))
        ax.set_ylim(0, y_tick_max + 0.28)
    elif decimals == 0:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        ax.set_ylim(0, max(max_value * 1.13, 1.0))
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.set_ylim(0, max(max_value * 1.13, 1.0))
    style_box_axes(ax, xlabel="Ponto amostral", ylabel=ylabel)
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.975),
        ncol=min(2, len(labels)),
        frameon=False,
        handlelength=2.2,
        columnspacing=1.8,
    )
    fig.subplots_adjust(left=0.08, right=0.995, bottom=0.155, top=0.835)
    save_fig(fig, out_name)


def plot_taxon_bar(df: pd.DataFrame, *, category_col: str, xlabel: str, out_name: str) -> None:
    df = df.copy()
    df["numero_de_especies"] = pd.to_numeric(df["numero_de_especies"], errors="coerce").fillna(0)
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    x = np.arange(len(df))
    bars = ax.bar(
        x,
        df["numero_de_especies"].to_numpy(dtype=float),
        color=PRIMARY_DARK,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(df[category_col].astype(str).tolist(), rotation=45, ha="right")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    ymax = max(float(df["numero_de_especies"].max()) if not df.empty else 0.0, 1.0)
    ax.set_ylim(0, ymax * 1.18)
    style_box_axes(ax, xlabel=xlabel, ylabel="Número de espécies")
    for bar, value in zip(bars, df["numero_de_especies"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            float(value) + ymax * 0.02,
            f"{int(round(float(value)))}",
            ha="center",
            va="bottom",
            fontsize=12,
        )
    fig.subplots_adjust(left=0.08, right=0.995, bottom=0.22, top=0.93)
    save_fig(fig, out_name)


def plot_taxon_donut(df: pd.DataFrame, *, category_col: str, out_name: str) -> None:
    df = df.copy()
    df["numero_de_especies"] = pd.to_numeric(df["numero_de_especies"], errors="coerce").fillna(0)
    values = df["numero_de_especies"].to_numpy(dtype=float)
    total = int(round(values.sum()))
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)

    def autopct_visible(pct: float) -> str:
        return f"{pct:.1f}%" if pct >= 4.0 else ""

    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        colors=palette(len(values)),
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
        df[category_col].astype(str).tolist(),
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=15,
    )
    ax.text(0, 0, f"Total\n{total}", ha="center", va="center", fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    fig.subplots_adjust(left=0.02, right=0.78, bottom=0.06, top=0.96)
    save_fig(fig, out_name)


def plot_species_horizontal(df: pd.DataFrame, *, metric_label: str, out_name: str) -> None:
    df = df.copy()
    campaigns = [c for c in df.columns if c != "nome_cientifico"]
    labels = df["nome_cientifico"].astype(str).tolist()
    y = np.arange(len(labels))
    height = min(0.18, 0.82 / max(len(campaigns), 1))
    colors = palette(max(len(campaigns), 1))
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    all_bars = []

    for i, campaign in enumerate(campaigns):
        values = pd.to_numeric(df[campaign], errors="coerce").fillna(0).to_numpy(dtype=float)
        bars = ax.barh(
            y + (i - (len(campaigns) - 1) / 2) * height,
            values,
            height=height,
            label=campaign_label(campaign),
            color=colors[i],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        all_bars.append(bars)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontstyle="italic")
    style_box_axes(ax, xlabel=metric_label, ylabel="Espécie")
    ax.grid(axis="y", linestyle="-", linewidth=0.7, color="#D9D9D9", alpha=0.35)
    ax.grid(axis="x", visible=False)
    max_value = max((float(pd.to_numeric(df[c], errors="coerce").fillna(0).max()) for c in campaigns), default=0.0)
    offset = max(max_value * 0.015, 0.08)
    ax.set_xlim(0, max(max_value * 1.15, 1.0))
    for bars in all_bars:
        for bar in bars:
            w = float(bar.get_width())
            if abs(w) < 1e-12:
                continue
            ax.text(
                w + offset,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}",
                va="center",
                ha="left",
                fontsize=11,
            )
    handles, legend_labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.975),
        ncol=min(2, len(legend_labels)),
        frameon=False,
    )
    fig.subplots_adjust(left=0.36, right=0.97, bottom=0.15, top=0.83)
    save_fig(fig, out_name)


def plot_heatmap(df: pd.DataFrame, *, metric_label: str, out_name: str) -> None:
    df = df.copy()
    columns = [c for c in df.columns if c != "nome_cientifico"]
    labels = df["nome_cientifico"].astype(str).tolist()
    values = df[columns].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(dtype=float)
    vmax = float(np.nanmax(values)) if values.size else 0.0
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    cmap = mcolors.LinearSegmentedColormap.from_list("braaeg001_green", [PRIMARY, SECONDARY])
    im = ax.imshow(values, aspect="auto", cmap=cmap, vmin=0, vmax=vmax if vmax > 0 else 1)
    ax.set_xticks(np.arange(len(columns)))
    ax.set_xticklabels(columns, rotation=90, ha="center")
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels, fontstyle="italic")
    style_box_axes(ax, xlabel="Ponto amostral", ylabel="Espécie")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", labelsize=12)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            v = float(values[i, j])
            if abs(v) < 1e-12:
                continue
            ax.text(
                j,
                i,
                f"{v:.2f}",
                ha="center",
                va="center",
                fontsize=9,
                color=label_color_for_value(v, vmax),
            )
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label(metric_label)
    cbar.ax.tick_params(labelsize=11)
    fig.subplots_adjust(left=0.24, right=0.88, bottom=0.18, top=0.94)
    save_fig(fig, out_name)


def plot_diversity() -> None:
    df = read_xlsx("10_df_diversidade_alfa_ictiofauna.xlsx")
    df["Shannon_H"] = pd.to_numeric(df["Shannon_H"], errors="coerce").fillna(0)
    df["Pielou_J"] = pd.to_numeric(df["Pielou_J"], errors="coerce").fillna(0)
    labels = []
    for _, row in df.iterrows():
        point = str(row["nome_ponto"])
        if point.endswith("(Geral)"):
            labels.append(f"{campaign_label(str(row['nome_campanha']))} (Geral)")
        else:
            labels.append(point)
    x = np.arange(len(df))
    fig, ax1 = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    bars = ax1.bar(
        x,
        df["Shannon_H"].to_numpy(dtype=float),
        color=PRIMARY_DARK,
        edgecolor="black",
        linewidth=0.8,
        label="Diversidade (H')",
        zorder=3,
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    style_box_axes(ax1, xlabel="Ponto amostral", ylabel="Shannon (H')")
    ax1.set_ylim(0, max(float(df["Shannon_H"].max()) * 1.16, 1.0))
    ax1.tick_params(axis="x", labelsize=11)

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        df["Pielou_J"].to_numpy(dtype=float),
        marker="o",
        linestyle="None",
        color=SECONDARY_DARK,
        markersize=6,
        label="Equitabilidade (J')",
        zorder=4,
    )
    ax2.set_ylabel("Pielou (J')")
    ax2.set_ylim(0, 1.1)
    ax2.tick_params(axis="y", labelsize=13)
    for spine in ax2.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.2)

    campaigns = df["nome_campanha"].astype(str).drop_duplicates().tolist()
    for campaign in campaigns[:-1]:
        split_n = df[df["nome_campanha"].isin(campaigns[: campaigns.index(campaign) + 1])].shape[0]
        if 0 < split_n < len(x):
            ax1.axvline(x=split_n - 0.5, color="#888888", linestyle="--", linewidth=1.2)

    for bar, value in zip(bars, df["Shannon_H"].tolist()):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            float(value) + 0.015,
            f"{float(value):.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(
        handles1 + handles2,
        labels1 + labels2,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.975),
        ncol=2,
        frameon=False,
    )
    fig.subplots_adjust(left=0.08, right=0.92, bottom=0.29, top=0.84)
    save_fig(fig, "10_grafico_diversidade_alfa_ictiofauna.png")


def plot_dendrogram() -> None:
    dist = read_xlsx("11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx")
    labels = dist.iloc[:, 0].astype(str).tolist()
    matrix = dist.iloc[:, 1:].to_numpy(dtype=float)
    condensed = squareform(matrix, checks=False)
    z = linkage(condensed, method="average")
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    dendrogram(z, labels=labels, orientation="right", ax=ax, color_threshold=None)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.02, -0.02)
    ticks_sim = np.arange(0, 101, 10)
    ticks_dist = 1 - ticks_sim / 100.0
    ax.set_xticks(ticks_dist)
    ax.set_xticklabels([str(t) for t in ticks_sim])
    style_box_axes(ax, xlabel="Similaridade de Bray-Curtis (%) - matriz CPUEn", ylabel="")
    ax.grid(axis="x", linestyle="--", linewidth=0.7, color="#D9D9D9", alpha=0.35)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="both", labelsize=13)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.08, top=0.84)
    save_fig(fig, "11_dendrograma_similaridade_ictiofauna_seca_chuva_somadas.png")


def plot_sufficiency() -> None:
    df = read_xlsx("12_df_curva_suficiencia_ictiofauna.xlsx")
    x = pd.to_numeric(df["n_amostras"], errors="coerce").fillna(0).to_numpy(dtype=float)
    obs = pd.to_numeric(df["riqueza_obs_media"], errors="coerce").fillna(0).to_numpy(dtype=float)
    est = pd.to_numeric(df["riqueza_est_jackknife1_media"], errors="coerce").fillna(0).to_numpy(dtype=float)
    std = pd.to_numeric(df["jackknife1_desvio_padrao"], errors="coerce").fillna(0).to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=A4_LANDSCAPE, dpi=DPI)
    ax.plot(x, obs, linewidth=2.2, label="Riqueza observada", color=PRIMARY_DARK)
    ax.plot(x, est, linewidth=2.2, label="Riqueza estimada (Jackknife 1)", color=SECONDARY_DARK)
    ax.fill_between(x, est - std, est + std, alpha=0.18, color=SECONDARY_DARK)
    style_box_axes(ax, xlabel="Número de unidades amostrais", ylabel="Riqueza")
    ax.set_xlim(float(np.nanmin(x)), float(np.nanmax(x)) + 1.0)
    ax.set_ylim(0, max(float(np.nanmax(est + std)) * 1.08, 1.0))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
    ax.text(x[-1] + 0.15, obs[-1], f"{obs[-1]:.0f}", color="black", va="center", fontsize=12)
    ax.text(x[-1] + 0.15, est[-1], f"{est[-1]:.1f}", color="black", va="center", fontsize=12)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.975), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.08, right=0.96, bottom=0.13, top=0.84)
    save_fig(fig, "12_curva_suficiencia_amostral_ictiofauna.png")


def plot_ecological_synthesis() -> None:
    sheets = pd.read_excel(OUTPUT_DIR / "14_tabela_sintese_ecologica_ictiofauna.xlsx", sheet_name=None)
    panels = [
        ("sintese_origem", "Origem"),
        ("sintese_migratorio", "Comportamento migratório"),
    ]
    fig, axes = plt.subplots(1, len(panels), figsize=A4_LANDSCAPE, dpi=DPI)
    if len(panels) == 1:
        axes = [axes]
    for ax, (sheet, title) in zip(axes, panels):
        df = sheets.get(sheet, pd.DataFrame()).copy()
        if df.empty:
            ax.axis("off")
            continue
        df["abundancia_total"] = pd.to_numeric(df["abundancia_total"], errors="coerce").fillna(0)
        df = df.sort_values("abundancia_total", ascending=True)
        ax.barh(df["categoria"].astype(str), df["abundancia_total"], color=PRIMARY_DARK, edgecolor="black")
        ax.set_title(title, fontweight="bold", fontsize=17, pad=12)
        ax.set_xlabel("Abundância total", fontsize=13, labelpad=10)
        ax.tick_params(axis="both", labelsize=13)
        ax.grid(axis="x", alpha=0.2, linestyle="--")
        ax.grid(axis="y", visible=False)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color("black")
            ax.spines[spine].set_linewidth(1.2)
    fig.suptitle("Síntese ecológica da ictiofauna - BRAAEG001", fontweight="bold", fontsize=17)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.13, top=0.82, wspace=0.32)
    save_fig(fig, "14_grafico_sintese_ecologica_ictiofauna.png")


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
        im = Image.open(OUTPUT_DIR / name).convert("RGB")
        im.thumbnail((560, 360))
        canvas = Image.new("RGB", (590, 420), "white")
        canvas.paste(im, ((590 - im.width) // 2, 10))
        d = ImageDraw.Draw(canvas)
        d.text((12, 388), name[:82], fill="black")
        thumbs.append(canvas)
    cols = 2
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 590, rows * 420), "white")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % cols) * 590, (i // cols) * 420))
    out = AUDIT_DIR / f"{tag}_contact_sheet_figuras_ictio_a4_paisagem_R01.png"
    sheet.save(out)
    return out


def backup_figures(tag: str) -> Path:
    backup_dir = AUDIT_DIR / f"{tag}_backup_figuras_ictio_pre_R01"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in FINAL_FIGURES:
        src = OUTPUT_DIR / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
    return backup_dir


def update_manifest_and_validation(tag: str) -> tuple[Path, Path, Path, Path]:
    manifest_json = OUTPUT_DIR / "manifesto_entrega_ictiofauna_braaeg001.json"
    manifest_xlsx = OUTPUT_DIR / "manifesto_entrega_ictiofauna_braaeg001.xlsx"
    manifest_md = OUTPUT_DIR / "manifesto_entrega_ictiofauna_braaeg001.md"
    validation_json = OUTPUT_DIR / "validacao_entrega_ictiofauna_braaeg001.json"
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    file_names = [row["arquivo"] for row in manifest.get("files", []) if "_A4_" not in row["arquivo"]]

    missing = [name for name in file_names if not (OUTPUT_DIR / name).exists()]
    zero_size = [name for name in file_names if (OUTPUT_DIR / name).exists() and (OUTPUT_DIR / name).stat().st_size <= 0]
    validation = {
        "validated_at": now_iso(),
        "status": "OK" if not missing and not zero_size else "ERROR",
        "files_checked": len(file_names),
        "missing_files": missing,
        "zero_size_files": zero_size,
        "errors_count": len(missing) + len(zero_size),
        "warnings": [
            "Diversidade, similaridade e suficiência são apoio diagnóstico para base curta.",
            "Figuras e relatório HTML de ictiofauna revisados em A4 paisagem na revisão R01.",
        ],
    }
    validation_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for name in file_names:
        path = OUTPUT_DIR / name
        rows.append(
            {
                "arquivo": name,
                "extensao": path.suffix.lower().lstrip("."),
                "tamanho_bytes": path.stat().st_size,
                "modificado_em": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z"),
                "sha256": sha256(path),
            }
        )
    manifest["generated_at"] = now_iso()
    manifest["files_count"] = len(rows)
    manifest["files"] = rows
    manifest["revision"] = {
        "id": "R01",
        "applied_at": now_iso(),
        "description": "Figuras PNG de ictiofauna e relatório HTML revisados com padrão visual aprovado e acentuação pt-BR.",
        "audit_tag": tag,
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(rows).to_excel(manifest_xlsx, index=False, engine="openpyxl")

    lines = [
        "# BRAAEG001 - Manifesto de entrega - Ictiofauna",
        "",
        f"- gerado em: `{manifest['generated_at']}`",
        f"- revisão: `R01 - figuras A4 paisagem`",
        f"- arquivos listados: `{len(rows)}`",
        f"- taxons: `{manifest['summary']['taxa_total']}`",
        f"- indivíduos: `{manifest['summary']['individuos_total']}`",
        f"- biomassa total: `{manifest['summary']['biomassa_total_g']:.1f} g`",
        "",
        "## Arquivos",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['arquivo']}` ({row['extensao']}, {row['tamanho_bytes']} bytes)")
    manifest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_json, manifest_xlsx, manifest_md, validation_json


def regenerate_all() -> list[str]:
    validate_ptbr_labels()
    plot_grouped_campaign_bars(
        read_xlsx("02_df_riqueza_por_ponto_ictiofauna.xlsx"),
        value_col="riqueza",
        ylabel="Riqueza taxonômica",
        out_name="02_grafico_riqueza_por_ponto_ictiofauna.png",
        decimals=0,
        integer_axis=True,
    )
    plot_grouped_campaign_bars(
        read_xlsx("03_df_abundancia_por_ponto_ictiofauna.xlsx"),
        value_col="abundancia_total",
        ylabel="Abundância total (nº de indivíduos)",
        out_name="03_grafico_abundancia_por_ponto_ictiofauna.png",
        decimals=0,
    )
    plot_taxon_bar(
        read_xlsx("04_df_riqueza_por_familia_ictiofauna.xlsx"),
        category_col="familia",
        xlabel="Família",
        out_name="04_grafico_riqueza_familia_barras_ictiofauna.png",
    )
    plot_taxon_bar(
        read_xlsx("04_df_riqueza_por_ordem_ictiofauna.xlsx"),
        category_col="ordem",
        xlabel="Ordem",
        out_name="04_grafico_riqueza_ordem_barras_ictiofauna.png",
    )
    plot_taxon_donut(
        read_xlsx("04_df_riqueza_por_familia_ictiofauna.xlsx"),
        category_col="familia",
        out_name="05_grafico_riqueza_familia_rosca_ictiofauna.png",
    )
    plot_taxon_donut(
        read_xlsx("04_df_riqueza_por_ordem_ictiofauna.xlsx"),
        category_col="ordem",
        out_name="05_grafico_riqueza_ordem_rosca_ictiofauna.png",
    )
    cpue = read_xlsx("06_df_cpue_por_ponto_ictiofauna.xlsx")
    plot_grouped_campaign_bars(
        cpue,
        value_col="cpuen",
        ylabel="CPUEn (ind/100 m²)",
        out_name="06_grafico_cpuen_por_ponto_ictiofauna.png",
        decimals=2,
    )
    plot_grouped_campaign_bars(
        cpue,
        value_col="cpueb",
        ylabel="CPUEb (g/100 m²)",
        out_name="07_grafico_cpueb_por_ponto_ictiofauna.png",
        decimals=2,
    )
    plot_species_horizontal(
        read_xlsx("08_df_cpuen_por_especie_ictiofauna.xlsx"),
        metric_label="CPUEn (ind/100 m²)",
        out_name="08_grafico_cpuen_por_especie_ictiofauna.png",
    )
    plot_species_horizontal(
        read_xlsx("09_df_cpueb_por_especie_ictiofauna.xlsx"),
        metric_label="CPUEb (g/100 m²)",
        out_name="09_grafico_cpueb_por_especie_ictiofauna.png",
    )
    plot_heatmap(
        read_xlsx("08B_df_cpuen_por_especie_ponto_ictiofauna.xlsx"),
        metric_label="CPUEn (ind/100 m²)",
        out_name="08B_grafico_cpuen_por_especie_ponto_ictiofauna.png",
    )
    plot_heatmap(
        read_xlsx("09B_df_cpueb_por_especie_ponto_ictiofauna.xlsx"),
        metric_label="CPUEb (g/100 m²)",
        out_name="09B_grafico_cpueb_por_especie_ponto_ictiofauna.png",
    )
    plot_diversity()
    plot_dendrogram()
    plot_sufficiency()
    plot_ecological_synthesis()
    return FINAL_FIGURES


def main() -> int:
    setup_rc()
    tag = now_tag()
    backup_dir = backup_figures(tag)
    before = {name: sha256(OUTPUT_DIR / name) for name in FINAL_FIGURES if (OUTPUT_DIR / name).exists()}
    regenerated = regenerate_all()
    after_infos = [image_info(OUTPUT_DIR / name) for name in regenerated]
    manifest_files = update_manifest_and_validation(tag)
    contact_sheet = make_contact_sheet(tag)

    audit_rows = []
    for info in after_infos:
        name = info["arquivo"]
        row = {
            **info,
            "sha256_pre_r01": before.get(name),
            "sha256_changed": before.get(name) != info["sha256"],
            "backup_dir": str(backup_dir),
            "status": "OK" if info["nonblank"] and info["largura_px"] == 7014 and info["altura_px"] == 4962 else "CHECK",
        }
        audit_rows.append(row)

    audit = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "project_code": "BRAAEG001",
        "group": "Ictiofauna",
        "revision": "R01",
        "action": "regenerate_final_figures_a4_landscape",
        "output_dir": str(OUTPUT_DIR),
        "backup_dir": str(backup_dir),
        "figures_count": len(audit_rows),
        "figures_ok": sum(1 for row in audit_rows if row["status"] == "OK"),
        "contact_sheet": str(contact_sheet),
        "manifest_files": [str(path) for path in manifest_files],
        "figures": audit_rows,
    }
    audit_json = AUDIT_DIR / f"{tag}_regeneracao_figuras_ictio_a4_paisagem_R01.json"
    audit_xlsx = AUDIT_DIR / f"{tag}_regeneracao_figuras_ictio_a4_paisagem_R01.xlsx"
    audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(audit_rows).to_excel(audit_xlsx, index=False, engine="openpyxl")

    print(json.dumps({"audit_json": str(audit_json), "audit_xlsx": str(audit_xlsx), "contact_sheet": str(contact_sheet)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
