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
    / "traditional_full_campaign_a4_3linhas_exploratory_20260714"
)

POINT_GROUPS = {
    "G01_AC01_PIC01_PIC03": ["PIC-01", "PIC-02", "PIC-03"],
    "G02_AC01_PIC04_PIC06": ["PIC-04", "PIC-05", "PIC-06"],
    "G03_AC01_PIC07_PIC09": ["PIC-07", "PIC-08", "PIC-09"],
    "G04_AC01_PIC11": ["PIC-11"],
    "G05_AC02_PIC10_PIC13": ["PIC-10", "PIC-12", "PIC-13"],
}
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


def decorate_temporal_axis(ax, *, ymax: float) -> None:
    for index, (year, start, end) in enumerate(TEMPORAL_YEAR_BANDS):
        if index % 2 == 0:
            ax.axvspan(start - 0.5, end + 0.5, color="#F3F7F0", zorder=0)
        ax.text(
            (start + end) / 2,
            ymax * 0.98,
            f"Ano {year}",
            ha="center",
            va="top",
            fontsize=10.0,
            color="#52614C",
            zorder=3,
        )
    for boundary in [12.5, 24.5, 36.5]:
        ax.axvline(boundary, color="#666666", linewidth=0.9, linestyle=":", zorder=2)


def plot_group(
    data: pd.DataFrame,
    *,
    points: list[str],
    group_name: str,
    value_col: str,
    ylabel: str,
    filename_prefix: str,
    y_floor: float = 1.0,
) -> str:
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

    rows, cols = len(points), 1
    fig, axes = plt.subplots(
        rows,
        cols,
        figsize=(11.69, 8.27),
        dpi=500,
        sharex=True,
        sharey=True,
    )
    axes_grid = np.asarray(axes, dtype=object).reshape(rows, cols)
    axes_flat = axes_grid.ravel()
    for ax in axes_flat[len(points) :]:
        ax.axis("off")

    for ax, point in zip(axes_flat, points):
        point_data = (
            data[data["nome_ponto"] == point]
            .set_index("campanha_seq")
            .reindex(range(1, 48))
            .reset_index()
        )
        y = pd.to_numeric(point_data[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        x = point_data["campanha_seq"].to_numpy(dtype=float)
        decorate_temporal_axis(ax, ymax=ymax)
        ax.plot(x, y, color="#595959", linewidth=1.1, zorder=1)
        for season, color in SEASON_COLORS.items():
            mask = np.array([season_by_seq.get(int(seq), "ND") == season for seq in x])
            ax.scatter(
                x[mask],
                y[mask],
                s=16,
                color=color,
                edgecolor="black",
                linewidth=0.28,
                zorder=4,
            )

        ax.text(0.03, 0.88, point, transform=ax.transAxes, ha="left", va="top", fontsize=17, fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xlim(0.5, 47.5)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.65, alpha=0.78)
        ax.grid(axis="x", color="#EEEEEE", linewidth=0.42, alpha=0.58)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.set_xticks(x_all)
        ax.set_xticklabels(labels, rotation=90, fontsize=8.4)
        ax.tick_params(axis="x", labelbottom=True, pad=1)
        ax.tick_params(axis="y", labelsize=11)

    for ax in axes_grid[-1, :]:
        if ax.has_data():
            ax.set_xlabel("Campanha", fontsize=12)
    if cols == 1:
        axes_grid[rows // 2, 0].set_ylabel(ylabel, fontsize=12)
    else:
        for ax in axes_grid[:, 0]:
            if ax.has_data():
                ax.set_ylabel(ylabel, fontsize=12)

    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=SEASON_COLORS["CH"], markeredgecolor="black", label="CH"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=SEASON_COLORS["SC"], markeredgecolor="black", label="SC"),
        plt.Line2D([0], [0], color="#666666", linestyle=":", label="Ano temporal"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=12)
    fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.93])
    out_png = OUTPUT_DIR / f"{filename_prefix}_{group_name}.png"
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    return str(out_png)


def prepare_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["campanha_seq"] = out["nome_campanha"].map(campaign_sequence)
    out["campanha_curta"] = out["nome_campanha"].map(campaign_short)
    out["periodo"] = out["nome_campanha"].map(campaign_season)
    return out


def plot_metric_groups(
    df: pd.DataFrame,
    *,
    value_col: str,
    ylabel: str,
    filename_prefix: str,
) -> list[str]:
    data = prepare_table(df)
    outputs: list[str] = []
    for group_name, points in POINT_GROUPS.items():
        outputs.append(
            plot_group(
                data,
                points=points,
                group_name=group_name,
                value_col=value_col,
                ylabel=ylabel,
                filename_prefix=filename_prefix,
            )
        )
    return outputs


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    richness = pd.read_excel(FINAL_DIR / "02_df_riqueza_por_ponto_ictiofauna.xlsx")
    abundance = pd.read_excel(FINAL_DIR / "03_df_abundancia_por_ponto_ictiofauna.xlsx")
    cpue = pd.read_excel(FINAL_DIR / "06_df_cpue_por_ponto_ictiofauna.xlsx")
    diversity = pd.read_excel(FINAL_DIR / "10_df_diversidade_alfa_ictiofauna.xlsx")
    diversity = diversity[diversity["nome_ponto"].isin(sum(POINT_GROUPS.values(), []))].copy()

    outputs = {
        "02_riqueza": plot_metric_groups(
            richness,
            value_col="riqueza",
            ylabel="Riqueza taxonomica",
            filename_prefix="EXP_A4_02_riqueza_por_ponto_c001_c047",
        ),
        "03_abundancia": plot_metric_groups(
            abundance,
            value_col="abundancia_total",
            ylabel="Abundancia total",
            filename_prefix="EXP_A4_03_abundancia_por_ponto_c001_c047",
        ),
        "06_cpuen": plot_metric_groups(
            cpue,
            value_col="cpuen",
            ylabel="CPUEn (ind/100m2)",
            filename_prefix="EXP_A4_06_cpuen_por_ponto_c001_c047",
        ),
        "07_cpueb": plot_metric_groups(
            cpue,
            value_col="cpueb",
            ylabel="CPUEb (g/100m2)",
            filename_prefix="EXP_A4_07_cpueb_por_ponto_c001_c047",
        ),
        "10_shannon": plot_metric_groups(
            diversity,
            value_col="Shannon_H",
            ylabel="Shannon (H')",
            filename_prefix="EXP_A4_10A_shannon_por_ponto_c001_c047",
        ),
        "10_pielou": plot_metric_groups(
            diversity,
            value_col="Pielou_J",
            ylabel="Pielou (J')",
            filename_prefix="EXP_A4_10B_pielou_por_ponto_c001_c047",
        ),
    }
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "exploratory_not_final",
        "source_dir": str(FINAL_DIR),
        "output_dir": str(OUTPUT_DIR),
        "idea": "Figuras A4 paisagem com um ponto por linha, priorizando grupos de 3 pontos, C001-C047 no eixo X e separadores pontilhados de ano temporal.",
        "point_groups": POINT_GROUPS,
        "outputs": outputs,
        "figures_per_metric": len(POINT_GROUPS),
    }
    (OUTPUT_DIR / "manifesto_a4_grupos_c001_c047_ictiofauna.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "README_a4_grupos_c001_c047_ictiofauna.md").write_text(
        "\n".join(
            [
                "# Exploratorio - A4 com um ponto por linha",
                "",
                "Este teste usa A4 paisagem com um ponto por linha e prioriza 3 pontos por figura.",
                "A Area de controle 01 gera uma prancha residual para PIC-11, evitando mistura com a Area de controle 02.",
                "O eixo X preserva C001-C047 e os anos temporais sao separados por linhas pontilhadas com rotulo Ano.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
