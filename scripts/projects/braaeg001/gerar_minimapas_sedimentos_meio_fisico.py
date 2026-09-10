from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import gerar_minimapas_superficial_meio_fisico as maps  # noqa: E402
import gerar_resultados_subterranea_sedimentos_meio_fisico as results  # noqa: E402


OUTPUT_DIR = results.RESULTS_DIR / "sedimentos"
HYDROLOGY_KMZ = results.PROJECT_DIR / "Geo" / "1AEMG002" / "Hidrografia.kmz"
CAMPAIGNS = ["Campanha-01-Chuva", "Campanha-02-Seca"]
VIOLATION_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "violacoes_sedimentos_verde", ["#E8F5E9", "#9CCC65", "#43A047", "#1B7F22"]
)


def point_key(point: Any) -> int:
    return maps.point_key(str(point))


def load_points(sediments: pd.DataFrame) -> pd.DataFrame:
    points = (
        sediments[["nome_ponto", "latitude", "longitude"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"nome_ponto": "Ponto", "latitude": "Latitude", "longitude": "Longitude"})
    )
    points["Ponto"] = points["Ponto"].map(maps.clean_text)
    points["PlotLongitude"] = points["Longitude"]
    points["PlotLatitude"] = points["Latitude"]
    display_offsets = {
        "PT_04": (-0.00035, -0.00022),
        "PT_07": (0.00035, 0.00022),
        "PT_08": (-0.00032, 0.00018),
        "PT_11": (0.00032, -0.00018),
    }
    for point, (dx, dy) in display_offsets.items():
        mask = points["Ponto"].eq(point)
        points.loc[mask, "PlotLongitude"] = points.loc[mask, "Longitude"] + dx
        points.loc[mask, "PlotLatitude"] = points.loc[mask, "Latitude"] + dy
    return points.sort_values("Ponto", key=lambda s: s.map(point_key)).reset_index(drop=True)


def build_violation_by_point(sediments: pd.DataFrame) -> pd.DataFrame:
    df = sediments.copy()
    df["Campanha"] = df["nome_campanha"].map(lambda x: results.CAMPAIGN_LABELS.get(maps.clean_text(x), maps.clean_text(x)))
    df["violacao_conservadora"] = df["status_conformidade"].isin(["Viola", "Entre N1 e N2"])
    df["acima_nivel_2"] = df["status_conformidade"].eq("Viola")
    df["entre_nivel_1_e_2"] = df["status_conformidade"].eq("Entre N1 e N2")
    numeric = df[df["valor_medido"].notna()].copy()
    summary = (
        numeric.groupby(["Campanha", "nome_ponto"], as_index=False)
        .agg(
            parametros_avaliados=("parametro_exibicao", "nunique"),
            violacoes=("violacao_conservadora", "sum"),
            entre_nivel_1_e_2=("entre_nivel_1_e_2", "sum"),
            acima_nivel_2=("acima_nivel_2", "sum"),
        )
        .rename(columns={"nome_ponto": "Ponto"})
    )
    summary["percentual_violacao"] = np.where(
        summary["parametros_avaliados"] > 0,
        100 * summary["violacoes"] / summary["parametros_avaliados"],
        0,
    )
    return summary.sort_values(
        ["Campanha", "Ponto"],
        key=lambda s: s.map(point_key) if s.name == "Ponto" else s.map(maps.campaign_key),
    )


def plot_violations(points: pd.DataFrame, data: pd.DataFrame, segments: list[np.ndarray], bounds: tuple[float, float, float, float]) -> Path:
    out_png = OUTPUT_DIR / "05_minimapa_violacoes_por_ponto_chuva_seca.png"
    max_value = max(1, int(data["violacoes"].max()))
    norm = mcolors.Normalize(vmin=0, vmax=max_value)
    fig, axes = maps.panel_figure()
    mappable = None
    for ax, campaign in zip(axes, CAMPAIGNS, strict=True):
        maps.base_map(ax, points, segments, bounds)
        subset = points.merge(data[data["Campanha"].eq(campaign)], on="Ponto", how="left")
        fill_cols = ["violacoes", "parametros_avaliados", "percentual_violacao", "entre_nivel_1_e_2", "acima_nivel_2"]
        subset[fill_cols] = subset[fill_cols].fillna(0)
        mappable = ax.scatter(
            subset["PlotLongitude"],
            subset["PlotLatitude"],
            s=175,
            c=subset["violacoes"],
            cmap=VIOLATION_CMAP,
            norm=norm,
            edgecolor=maps.POINT_COLORS["edge"],
            linewidth=0.75,
            zorder=3,
        )
        for row in subset.itertuples(index=False):
            label = f"{int(row.violacoes)}"
            ax.text(
                row.PlotLongitude,
                row.PlotLatitude,
                label,
                ha="center",
                va="center",
                fontsize=8.2,
                fontweight="bold",
                color="#102015",
                zorder=4,
            )
        ax.set_title(campaign, fontsize=16, fontweight="bold", pad=10)
    axes[0].set_ylabel("Latitude", fontsize=10.5)
    axes[0].set_xlabel("Longitude", fontsize=10.5)
    axes[1].set_xlabel("Longitude", fontsize=10.5)
    cax = fig.add_axes([0.91, 0.24, 0.018, 0.52])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label("Parâmetros com violação > Nível 1 (n)", fontsize=10.5)
    cb.ax.tick_params(labelsize=8.8)
    fig.legend(
        handles=[maps.Line2D([0], [0], color=maps.POINT_COLORS["hydro"], lw=1.5, label="Hidrografia")],
        loc="lower center",
        frameon=False,
        ncol=1,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.025),
    )
    fig.tight_layout(rect=(0.035, 0.06, 0.89, 0.96))
    fig.savefig(out_png, facecolor="white", dpi=300)
    plt.close(fig)
    return out_png


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = results.read_data()
    cfg = results.MATRIX_CONFIG["sedimentos"]
    sediments = results.prepare_matrix(df, "sedimentos", cfg)
    points = load_points(sediments)
    segments = maps.load_hydrology_segments(HYDROLOGY_KMZ)
    bounds = maps.map_limits(points, segments)
    violations = build_violation_by_point(sediments)
    out_png = plot_violations(points, violations, segments, bounds)
    out_xlsx = OUTPUT_DIR / "05_Dados_Minimapas_Sedimentos.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        points.to_excel(writer, sheet_name="pontos", index=False)
        violations.to_excel(writer, sheet_name="violacoes_por_ponto", index=False)
    results.style_workbook(out_xlsx)
    print({"xlsx": str(out_xlsx), "png": str(out_png), "hidrografia_segmentos": len(segments)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
