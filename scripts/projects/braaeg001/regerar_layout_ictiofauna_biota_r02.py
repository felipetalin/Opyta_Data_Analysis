from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


CLIENT_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
PROJECT_DIR = next(path for path in CLIENT_ROOT.iterdir() if path.name.startswith("A&G"))
OUTPUT_DIR = PROJECT_DIR / "resultados" / "migracao_biota" / "ictiofauna"

FIGSIZE = (11.69, 8.27)
DPI = 600
CAMPAIGNS = ["C001-2026-02-CH", "C002-2026-06-SC"]
CAMPAIGN_LABELS = {
    "C001-2026-02-CH": "C01-Chuva",
    "C002-2026-06-SC": "C02-Seca",
}
CAMPAIGN_COLORS = {
    "C001-2026-02-CH": "#0B4F12",
    "C002-2026-06-SC": "#10F20A",
}
EDGE = "#111111"
GRID = "#B7D9B3"
PIELOU_COLOR = "#6F9367"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 15,
        "axes.labelsize": 18,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "axes.unicode_minus": False,
    }
)


def point_sort_key(point: str) -> tuple[int, str]:
    digits = "".join(ch for ch in str(point) if ch.isdigit())
    return (int(digits) if digits else 9999, str(point))


def fmt_point(point: str) -> str:
    return str(point).replace("_", "_")


def fmt_value(value: float, decimals: int) -> str:
    if pd.isna(value):
        return ""
    if decimals == 0:
        return str(int(round(float(value))))
    text = f"{float(value):.{decimals}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def save(fig: plt.Figure, out_png: Path) -> None:
    fig.savefig(out_png, facecolor="white")
    plt.close(fig)


def style_axis(ax: plt.Axes) -> None:
    ax.yaxis.grid(True, color=GRID, linestyle="--", linewidth=0.8, alpha=0.55)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)


def plot_point_panels(source: str, value_col: str, ylabel: str, out_name: str, decimals: int) -> None:
    df = pd.read_excel(OUTPUT_DIR / source)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
    points = sorted(df["nome_ponto"].dropna().unique().tolist(), key=point_sort_key)
    ymax = max(float(df[value_col].max()) * 1.18, 1.0)
    if decimals == 0:
        ymax = max(ymax, float(df[value_col].max()) + 1)

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI, sharey=True)
    x = np.arange(len(points))
    for ax, campaign in zip(axes, CAMPAIGNS):
        data = df[df["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points)
        values = data[value_col].fillna(0).to_numpy(dtype=float)
        bars = ax.bar(
            x,
            values,
            color=CAMPAIGN_COLORS[campaign],
            edgecolor=EDGE,
            linewidth=0.9,
            width=0.62,
        )
        ax.set_title(CAMPAIGN_LABELS[campaign], fontsize=18, fontweight="bold", pad=13)
        ax.set_xticks(x)
        ax.set_xticklabels([fmt_point(p) for p in points], rotation=50, ha="right")
        ax.set_xlabel("Ponto amostral")
        ax.set_ylim(0, ymax)
        style_axis(ax)
        for rect, value in zip(bars, values):
            y = value + ymax * 0.025 if value > 0 else ymax * 0.018
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                y,
                fmt_value(value, decimals),
                ha="center",
                va="bottom",
                fontsize=12,
                color="#111111",
            )
    axes[0].set_ylabel(ylabel)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.20, wspace=0.08)
    save(fig, OUTPUT_DIR / out_name)


def plot_species_campaign(source: str, ylabel: str, out_name: str, decimals: int) -> None:
    df = pd.read_excel(OUTPUT_DIR / source)
    for campaign in CAMPAIGNS:
        df[campaign] = pd.to_numeric(df[campaign], errors="coerce").fillna(0)
    df["_max"] = df[CAMPAIGNS].max(axis=1)
    df = df.sort_values("_max", ascending=True).reset_index(drop=True)
    taxa = df["nome_cientifico"].astype(str).tolist()
    ymax = max(float(df[CAMPAIGNS].to_numpy().max()) * 1.18, 1.0)

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI, sharey=True)
    y = np.arange(len(taxa))
    for ax, campaign in zip(axes, CAMPAIGNS):
        values = df[campaign].to_numpy(dtype=float)
        bars = ax.barh(
            y,
            values,
            color=CAMPAIGN_COLORS[campaign],
            edgecolor=EDGE,
            linewidth=0.9,
            height=0.62,
        )
        ax.set_title(CAMPAIGN_LABELS[campaign], fontsize=18, fontweight="bold", pad=13)
        ax.set_xlabel(ylabel)
        ax.set_xlim(0, ymax)
        ax.set_yticks(y)
        ax.set_yticklabels(taxa, fontstyle="italic", fontsize=15)
        ax.xaxis.grid(True, color="#D9D9D9", linestyle="--", linewidth=0.8, alpha=0.55)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_linewidth(1.2)
        for rect, value in zip(bars, values):
            if value <= 0:
                continue
            ax.text(
                value + ymax * 0.012,
                rect.get_y() + rect.get_height() / 2,
                fmt_value(value, decimals),
                ha="left",
                va="center",
                fontsize=12,
            )
    axes[0].set_ylabel("Espécie")
    fig.subplots_adjust(left=0.34, right=0.985, top=0.82, bottom=0.16, wspace=0.08)
    save(fig, OUTPUT_DIR / out_name)


def plot_diversity() -> None:
    df = pd.read_excel(OUTPUT_DIR / "10_df_diversidade_alfa_ictiofauna.xlsx")
    df = df[~df["nome_ponto"].astype(str).str.contains("Geral", case=False, na=False)].copy()
    df["Shannon_H"] = pd.to_numeric(df["Shannon_H"], errors="coerce").fillna(0)
    df["Pielou_J"] = pd.to_numeric(df["Pielou_J"], errors="coerce").fillna(0)
    points = sorted(df["nome_ponto"].dropna().unique().tolist(), key=point_sort_key)
    sh_max = max(float(df["Shannon_H"].max()) * 1.25, 1.0)

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI, sharey=True)
    x = np.arange(len(points))
    secondary_axes: list[plt.Axes] = []
    for ax, campaign in zip(axes, CAMPAIGNS):
        data = df[df["nome_campanha"] == campaign].set_index("nome_ponto").reindex(points)
        shannon = data["Shannon_H"].fillna(0).to_numpy(dtype=float)
        pielou = data["Pielou_J"].fillna(0).to_numpy(dtype=float)
        bars = ax.bar(
            x,
            shannon,
            color=CAMPAIGN_COLORS[campaign],
            edgecolor=EDGE,
            linewidth=0.9,
            width=0.62,
        )
        ax2 = ax.twinx()
        ax2.scatter(x, pielou, s=34, color=PIELOU_COLOR, zorder=4)
        secondary_axes.append(ax2)
        ax.set_title(CAMPAIGN_LABELS[campaign], fontsize=18, fontweight="bold", pad=13)
        ax.set_xticks(x)
        ax.set_xticklabels([fmt_point(p) for p in points], rotation=50, ha="right")
        ax.set_xlabel("Ponto amostral")
        ax.set_ylim(0, sh_max)
        ax2.set_ylim(0, 1.08)
        style_axis(ax)
        ax2.tick_params(axis="y", labelsize=13)
        for rect, value in zip(bars, shannon):
            if value <= 0:
                continue
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                value + sh_max * 0.025,
                fmt_value(value, 2),
                ha="center",
                va="bottom",
                fontsize=11,
            )
    axes[0].set_ylabel("Shannon (H')")
    secondary_axes[-1].set_ylabel("Pielou (J')")
    for ax2 in secondary_axes[:-1]:
        ax2.set_yticklabels([])
        ax2.set_ylabel("")

    legend_items = [
        Patch(facecolor=CAMPAIGN_COLORS["C001-2026-02-CH"], edgecolor=EDGE, label="Diversidade (H')"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PIELOU_COLOR, markeredgecolor=PIELOU_COLOR, markersize=7, label="Equitabilidade (J')"),
    ]
    fig.legend(legend_items, [h.get_label() for h in legend_items], loc="upper center", ncol=2, frameon=False, fontsize=18)
    fig.subplots_adjust(left=0.075, right=0.93, top=0.78, bottom=0.20, wspace=0.08)
    save(fig, OUTPUT_DIR / "10_grafico_diversidade_alfa_ictiofauna.png")


def main() -> None:
    plot_point_panels(
        "02_df_riqueza_por_ponto_ictiofauna.xlsx",
        "riqueza",
        "Riqueza taxonômica",
        "02_grafico_riqueza_por_ponto_ictiofauna.png",
        0,
    )
    plot_point_panels(
        "03_df_abundancia_por_ponto_ictiofauna.xlsx",
        "abundancia_total",
        "Abundância total (nº de indivíduos)",
        "03_grafico_abundancia_por_ponto_ictiofauna.png",
        0,
    )
    plot_point_panels(
        "06_df_cpue_por_ponto_ictiofauna.xlsx",
        "cpuen",
        "CPUEn (ind/100 m²)",
        "06_grafico_cpuen_por_ponto_ictiofauna.png",
        2,
    )
    plot_point_panels(
        "06_df_cpue_por_ponto_ictiofauna.xlsx",
        "cpueb",
        "CPUEb (g/100 m²)",
        "07_grafico_cpueb_por_ponto_ictiofauna.png",
        2,
    )
    plot_species_campaign(
        "08_df_cpuen_por_especie_ictiofauna.xlsx",
        "CPUEn (ind/100 m²)",
        "08_grafico_cpuen_por_especie_ictiofauna.png",
        2,
    )
    plot_species_campaign(
        "09_df_cpueb_por_especie_ictiofauna.xlsx",
        "CPUEb (g/100 m²)",
        "09_grafico_cpueb_por_especie_ictiofauna.png",
        2,
    )
    plot_diversity()


if __name__ == "__main__":
    main()
