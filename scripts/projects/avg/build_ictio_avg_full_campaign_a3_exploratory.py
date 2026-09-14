from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados ictio"
    r"\Consolidado_2026\icitiofauna"
)
OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "traditional_full_campaign_a3_exploratory_20260714"
)

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
TEMPORAL_YEAR_BANDS = [
    (2023, 1, 12),
    (2024, 13, 24),
    (2025, 25, 36),
    (2026, 37, 47),
]
SEASON_COLORS = {"CH": "#0B7A3B", "SC": "#8AAE3C", "ND": "#5B5B5B"}


def campaign_sequence(value: object) -> int:
    match = re.match(r"^C0*(\d+)", str(value or "").strip(), flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Campanha padrao nao reconhecida: {value}")
    return int(match.group(1))


def campaign_short(value: object) -> str:
    return f"C{campaign_sequence(value):02d}"


def campaign_season(value: object) -> str:
    text = str(value or "").upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text):
        return "CH"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text):
        return "SC"
    return "ND"


def setup_frame() -> tuple[plt.Figure, np.ndarray]:
    fig, axes = plt.subplots(
        4,
        4,
        figsize=(16.54, 11.69),
        dpi=450,
        sharex=True,
        sharey=True,
    )
    for ax in axes.ravel()[len(POINT_ORDER) :]:
        ax.axis("off")
    return fig, axes


def decorate_temporal_axis(ax, *, ymax: float) -> None:
    for index, (year, start, end) in enumerate(TEMPORAL_YEAR_BANDS):
        if index % 2 == 0:
            ax.axvspan(start - 0.5, end + 0.5, color="#F3F7F0", zorder=0)
        x_mid = (start + end) / 2
        ax.text(
            x_mid,
            ymax * 0.98,
            f"AT {year}",
            ha="center",
            va="top",
            fontsize=7.5,
            color="#52614C",
            zorder=3,
        )
    for boundary in [12.5, 24.5, 36.5]:
        ax.axvline(boundary, color="#666666", linewidth=0.8, linestyle=":", zorder=2)


def plot_full_campaign(
    df: pd.DataFrame,
    *,
    value_col: str,
    ylabel: str,
    filename: str,
    y_floor: float = 1.0,
) -> str:
    data = df.copy()
    data["campanha_seq"] = data["nome_campanha"].map(campaign_sequence)
    data["campanha_curta"] = data["nome_campanha"].map(campaign_short)
    data["periodo"] = data["nome_campanha"].map(campaign_season)
    campaigns = (
        data[["nome_campanha", "campanha_seq", "campanha_curta", "periodo"]]
        .drop_duplicates()
        .sort_values("campanha_seq")
        .reset_index(drop=True)
    )
    x_all = campaigns["campanha_seq"].to_numpy(dtype=float)
    labels = campaigns["campanha_curta"].tolist()
    season_by_seq = campaigns.set_index("campanha_seq")["periodo"].to_dict()

    values = pd.to_numeric(data[value_col], errors="coerce").fillna(0)
    ymax = max(float(values.max()) if not values.empty else 0.0, y_floor) * 1.16

    fig, axes = setup_frame()
    for ax, point in zip(axes.ravel(), POINT_ORDER):
        point_data = (
            data[data["nome_ponto"] == point]
            .set_index("campanha_seq")
            .reindex(range(1, 48))
            .reset_index()
        )
        y = pd.to_numeric(point_data[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        x = point_data["campanha_seq"].to_numpy(dtype=float)
        decorate_temporal_axis(ax, ymax=ymax)
        ax.plot(x, y, color="#595959", linewidth=1.0, zorder=1)
        for season, color in SEASON_COLORS.items():
            mask = np.array([season_by_seq.get(int(seq), "ND") == season for seq in x])
            ax.scatter(
                x[mask],
                y[mask],
                s=11,
                color=color,
                edgecolor="black",
                linewidth=0.25,
                zorder=4,
                label=season,
            )

        ax.text(0.03, 0.92, point, transform=ax.transAxes, ha="left", va="top", fontsize=12, fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xlim(0.5, 47.5)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.55, alpha=0.75)
        ax.grid(axis="x", color="#EEEEEE", linewidth=0.35, alpha=0.55)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

    for ax in axes.ravel():
        if not ax.has_data():
            continue
        ax.set_xticks(x_all)
        ax.set_xticklabels(labels, rotation=90, fontsize=5.8)
        ax.tick_params(axis="x", labelbottom=True, pad=1)
        ax.tick_params(axis="y", labelsize=7.5)

    for ax in axes[-1, :]:
        if ax.has_data():
            ax.set_xlabel("Campanha")
    for ax in axes[:, 0]:
        if ax.has_data():
            ax.set_ylabel(ylabel)

    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=SEASON_COLORS["CH"], markeredgecolor="black", label="CH"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=SEASON_COLORS["SC"], markeredgecolor="black", label="SC"),
        plt.Line2D([0], [0], color="#666666", linestyle=":", label="Separador de ano temporal"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=10)
    fig.tight_layout(rect=[0.02, 0.025, 1.0, 0.94])
    out_png = OUTPUT_DIR / filename
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    return str(out_png)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    richness = pd.read_excel(FINAL_DIR / "02_df_riqueza_por_ponto_ictiofauna.xlsx")
    abundance = pd.read_excel(FINAL_DIR / "03_df_abundancia_por_ponto_ictiofauna.xlsx")
    cpue = pd.read_excel(FINAL_DIR / "06_df_cpue_por_ponto_ictiofauna.xlsx")
    diversity = pd.read_excel(FINAL_DIR / "10_df_diversidade_alfa_ictiofauna.xlsx")
    diversity = diversity[diversity["nome_ponto"].isin(POINT_ORDER)].copy()

    outputs = {
        "02_riqueza": plot_full_campaign(
            richness,
            value_col="riqueza",
            ylabel="Riqueza taxonomica",
            filename="EXP_A3_02_riqueza_por_ponto_c001_c047.png",
        ),
        "03_abundancia": plot_full_campaign(
            abundance,
            value_col="abundancia_total",
            ylabel="Abundancia total",
            filename="EXP_A3_03_abundancia_por_ponto_c001_c047.png",
        ),
        "06_cpuen": plot_full_campaign(
            cpue,
            value_col="cpuen",
            ylabel="CPUEn (ind/100m2)",
            filename="EXP_A3_06_cpuen_por_ponto_c001_c047.png",
        ),
        "07_cpueb": plot_full_campaign(
            cpue,
            value_col="cpueb",
            ylabel="CPUEb (g/100m2)",
            filename="EXP_A3_07_cpueb_por_ponto_c001_c047.png",
        ),
        "10_shannon": plot_full_campaign(
            diversity,
            value_col="Shannon_H",
            ylabel="Shannon (H')",
            filename="EXP_A3_10A_shannon_por_ponto_c001_c047.png",
        ),
        "10_pielou": plot_full_campaign(
            diversity,
            value_col="Pielou_J",
            ylabel="Pielou (J')",
            filename="EXP_A3_10B_pielou_por_ponto_c001_c047.png",
        ),
    }
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "exploratory_not_final",
        "source_dir": str(FINAL_DIR),
        "output_dir": str(OUTPUT_DIR),
        "idea": "Uma figura A3 paisagem por metrica, com C001-C047 no eixo X e separadores pontilhados de ano temporal.",
        "outputs": outputs,
        "notes": [
            "Faixas sutis alternadas indicam anos temporais.",
            "Linhas pontilhadas separam C012/C013, C024/C025 e C036/C037.",
            "Marcadores indicam periodo hidrologico CH/SC.",
        ],
    }
    (OUTPUT_DIR / "manifesto_a3_c001_c047_ictiofauna.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "README_a3_c001_c047_ictiofauna.md").write_text(
        "\n".join(
            [
                "# Exploratorio - A3 C001-C047",
                "",
                "Este teste usa uma figura A3 paisagem por metrica, com todas as campanhas no eixo X.",
                "Os anos temporais sao indicados por faixas sutis e linhas pontilhadas.",
                "Os marcadores distinguem periodo hidrologico CH/SC.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
