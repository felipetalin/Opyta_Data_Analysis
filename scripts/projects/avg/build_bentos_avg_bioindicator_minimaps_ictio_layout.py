from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

GEOARC_DIR = SCRIPT_DIR.parent / "geoarc001"
if str(GEOARC_DIR) not in sys.path:
    sys.path.insert(0, str(GEOARC_DIR))

import build_ictio_avg_threatened_species_synthesis as ictio_maps  # noqa: E402
from generate_functional_spatial_mini_maps import (  # noqa: E402
    _ada_polygons,
    _add_ada,
    _add_hydrology,
    _hydrology_segments,
    _point_limits,
    load_ada,
    load_hydrology,
)
from opyta_analysis.geo_reference import read_kml_polygon_coordinates  # noqa: E402


ROOT = ictio_maps.ROOT
BASE_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
ANALYTIC_XLSX = (
    BASE_DIR
    / "zoobentos_consolidated_analytic_base_20260721"
    / "base_analitica_consolidada_zoobentos_20260721.xlsx"
)
SUPPORT_DIR = BASE_DIR / "zoobentos_bioindicator_minimaps_ictio_layout_20260721"
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos\Planilha Consolidada\Resultados e planilhas\Resultados bentos\Consolidado_2026"
)

HYDROLOGY_LAYER = ictio_maps.HYDROLOGY_LAYER
ADA_LAYER = ictio_maps.ADA_LAYER
CONTROL_AREA_LAYERS = ictio_maps.CONTROL_AREA_LAYERS
CONTROL_AREA_COLORS = ictio_maps.CONTROL_AREA_COLORS

BMWP_CLASS_COLORS = {
    "Muito boa": "#00B0F0",
    "Boa": "#92D050",
    "Regular": "#FFFF00",
    "Ruim": "#FFC000",
    "Pessima": "#FF0000",
    "Não monitorado": "#D7DDE0",
}


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _classify_bmwp(score: float) -> str:
    if score > 85:
        return "Muito boa"
    if score >= 64:
        return "Boa"
    if score >= 37:
        return "Regular"
    if score >= 17:
        return "Ruim"
    return "Pessima"


def load_control_areas() -> pd.DataFrame:
    frames = []
    for label, layer in CONTROL_AREA_LAYERS.items():
        if not layer.exists():
            continue
        data = read_kml_polygon_coordinates(layer)
        if data.empty:
            continue
        data["area_controle"] = label
        data["camada"] = layer.stem
        frames.append(data)
    if not frames:
        return pd.DataFrame(
            columns=[
                "fonte",
                "camada",
                "polygon_id",
                "ring_id",
                "ring_type",
                "vertex_order",
                "Longitude",
                "Latitude",
                "area_controle",
            ]
        )
    return pd.concat(frames, ignore_index=True)


def _control_polygons(control_areas: pd.DataFrame, xmin: float, xmax: float, ymin: float, ymax: float) -> dict[str, list[np.ndarray]]:
    polygons: dict[str, list[np.ndarray]] = {label: [] for label in CONTROL_AREA_LAYERS}
    if control_areas.empty:
        return polygons
    outer = control_areas[control_areas["ring_type"] == "outer"].copy()
    for (label, _source, polygon_id, ring_id), ring in outer.groupby(
        ["area_controle", "fonte", "polygon_id", "ring_id"], sort=False
    ):
        ring = ring.sort_values("vertex_order")
        if ring.empty:
            continue
        if (
            float(ring["Longitude"].max()) < xmin
            or float(ring["Longitude"].min()) > xmax
            or float(ring["Latitude"].max()) < ymin
            or float(ring["Latitude"].min()) > ymax
        ):
            continue
        coords = ring[["Longitude", "Latitude"]].to_numpy(dtype=float)
        if len(coords) >= 3:
            polygons.setdefault(label, []).append(coords)
    return polygons


def _add_control_areas(ax: Any, polygons: dict[str, list[np.ndarray]]) -> None:
    for label, rings in polygons.items():
        if not rings:
            continue
        color = CONTROL_AREA_COLORS.get(label, "#777777")
        ax.add_collection(
            PolyCollection(
                rings,
                facecolors=[mcolors.to_rgba(color, 0.055)],
                edgecolors=[mcolors.to_rgba(color, 0.82)],
                linewidths=1.0,
                linestyles="--",
                zorder=0.18,
            )
        )


def build_annual_metrics(point_campaign: pd.DataFrame) -> pd.DataFrame:
    df = point_campaign.copy()
    monitored = df[df["Status_Monitoramento"].eq("Monitorado")].copy()
    annual = (
        monitored.groupby(
            ["Ano_Temporal", "Ciclo_Temporal", "Ponto", "Area_Controle", "Latitude", "Longitude"],
            as_index=False,
        )
        .agg(
            campanhas_monitoradas=("Campanha", "nunique"),
            abundancia_total=("abundancia", "sum"),
            bmwp_medio=("bmwp_score", "mean"),
            bmwp_familias_media=("bmwp_familias", "mean"),
            ept_abundancia=("ept_abundancia", "sum"),
            chol_abundancia=("chol_abundancia", "sum"),
        )
    )
    annual["ept_percentual"] = np.where(
        annual["abundancia_total"] > 0,
        100 * annual["ept_abundancia"] / annual["abundancia_total"],
        0,
    )
    annual["chol_percentual"] = np.where(
        annual["abundancia_total"] > 0,
        100 * annual["chol_abundancia"] / annual["abundancia_total"],
        0,
    )
    annual["bmwp_classe"] = annual["bmwp_medio"].map(_classify_bmwp)

    grid_cols = ["Ano_Temporal", "Ciclo_Temporal", "Ponto", "Area_Controle", "Latitude", "Longitude"]
    grid = df[grid_cols].drop_duplicates()
    out = grid.merge(annual, on=grid_cols, how="left")
    out["Status_Monitoramento"] = np.where(out["campanhas_monitoradas"].fillna(0) > 0, "Monitorado", "Não monitorado")
    out["bmwp_classe"] = np.where(out["Status_Monitoramento"].eq("Monitorado"), out["bmwp_classe"], "Não monitorado")
    for col in ["campanhas_monitoradas", "abundancia_total", "bmwp_medio", "bmwp_familias_media", "ept_percentual", "chol_percentual"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out.sort_values(["Ano_Temporal", "Ponto"]).reset_index(drop=True)


def build_bmwp_annual_comparison(base: pd.DataFrame, point_campaign: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    monitored = base[
        base["Status_Monitoramento"].eq("Monitorado")
        & (base["Numero_de_Individuos"].fillna(0) > 0)
        & base["BMWP_Score"].notna()
    ].copy()
    monitored["BMWP_Key"] = monitored["Familia"].fillna("").replace("", np.nan).fillna(monitored["Nome_Cientifico"])
    annual_pool = (
        monitored.groupby(["Ano_Temporal", "Ponto", "BMWP_Key"], dropna=False, as_index=False)
        .agg(BMWP_Score=("BMWP_Score", "max"))
        .groupby(["Ano_Temporal", "Ponto"], as_index=False)
        .agg(
            bmwp_acumulado_anual_familias=("BMWP_Score", "sum"),
            familias_bmwp_acumuladas=("BMWP_Key", "nunique"),
        )
    )
    monitored_pc = point_campaign[point_campaign["Status_Monitoramento"].eq("Monitorado")].copy()
    campaign_scores = monitored_pc[
        ["Ano_Temporal", "Ponto", "Campanha", "bmwp_score", "bmwp_familias", "riqueza", "abundancia"]
    ].copy()
    comparison = annual[
        [
            "Ano_Temporal",
            "Ponto",
            "Area_Controle",
            "campanhas_monitoradas",
            "bmwp_medio",
            "bmwp_familias_media",
            "bmwp_classe",
        ]
    ].merge(annual_pool, on=["Ano_Temporal", "Ponto"], how="left")
    comparison[["bmwp_acumulado_anual_familias", "familias_bmwp_acumuladas"]] = comparison[
        ["bmwp_acumulado_anual_familias", "familias_bmwp_acumuladas"]
    ].fillna(0)
    comparison["diferenca_acumulado_menos_medio"] = (
        comparison["bmwp_acumulado_anual_familias"] - comparison["bmwp_medio"]
    )
    comparison["observacao_metodologica"] = (
        "Mapa usa BMWP medio anual das campanhas monitoradas; acumulado anual soma familias unicas registradas no ano."
    )
    return comparison.sort_values(["Ano_Temporal", "Ponto"]).reset_index(drop=True), campaign_scores


def _bubble_size(value: float, max_value: float) -> float:
    if max_value <= 0 or value <= 0:
        return 0.0
    return 34 + np.sqrt(value / max_value) * 360


def _label_points(ax: Any, coords_plot: pd.DataFrame) -> None:
    for point, x, y in coords_plot[["Ponto", "Longitude", "Latitude"]].itertuples(index=False):
        if point in {"PIC-02", "PIC-04"}:
            continue
        ax.text(x + 0.00016, y + 0.00012, point, fontsize=8.2, color="#344047", zorder=4)
    callout_offsets = {"PIC-02": (-0.0022, 0.00105), "PIC-04": (0.0018, 0.00055)}
    for point, (dx_label, dy_label) in callout_offsets.items():
        row = coords_plot.loc[coords_plot["Ponto"] == point]
        if row.empty:
            continue
        x = float(row["Longitude"].iloc[0])
        y = float(row["Latitude"].iloc[0])
        ax.annotate(
            point,
            xy=(x, y),
            xytext=(x + dx_label, y + dy_label),
            fontsize=8.2,
            color="#344047",
            ha="center",
            va="center",
            arrowprops={"arrowstyle": "-", "color": "#59666C", "lw": 0.7, "shrinkA": 0, "shrinkB": 2},
            zorder=5,
        )


def _spatial_context(coords_plot: pd.DataFrame):
    hydrology = load_hydrology([HYDROLOGY_LAYER])
    ada = load_ada(ADA_LAYER)
    control_areas = load_control_areas()
    xmin, xmax, ymin, ymax = _point_limits(coords_plot)
    segments = _hydrology_segments(hydrology, xmin, xmax, ymin, ymax)
    polygons = _ada_polygons(ada, xmin, xmax, ymin, ymax)
    control_polygons = _control_polygons(control_areas, xmin, xmax, ymin, ymax)
    return xmin, xmax, ymin, ymax, segments, polygons, control_polygons


def _base_map(ax: Any, coords_plot: pd.DataFrame, context) -> None:
    xmin, xmax, ymin, ymax, segments, polygons, control_polygons = context
    _add_ada(ax, polygons)
    _add_control_areas(ax, control_polygons)
    _add_hydrology(ax, segments)
    ax.scatter(
        coords_plot["Longitude"],
        coords_plot["Latitude"],
        s=12,
        color="#D7DDE0",
        edgecolor="#8B969A",
        linewidth=0.45,
        zorder=1.0,
    )
    _label_points(ax, coords_plot)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(color="#E8ECEE", linewidth=0.65)
    ax.tick_params(axis="both", labelsize=8.5)
    ax.set_aspect("equal", adjustable="box")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)


def plot_bmwp(annual: pd.DataFrame, output_png: Path) -> None:
    years = [2023, 2024, 2025, 2026]
    coords_plot = annual[["Ponto", "Longitude", "Latitude"]].drop_duplicates()
    context = _spatial_context(coords_plot)
    fig, axes_grid = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=450, sharex=True, sharey=True)
    axes = axes_grid.ravel()
    for ax, year in zip(axes, years, strict=True):
        _base_map(ax, coords_plot, context)
        data = annual[annual["Ano_Temporal"].eq(year)].copy()
        for label, color in BMWP_CLASS_COLORS.items():
            subset = data[data["bmwp_classe"].eq(label)]
            if subset.empty:
                continue
            ax.scatter(
                subset["Longitude"],
                subset["Latitude"],
                s=150,
                color=color,
                edgecolor="#1F1F1F",
                linewidth=0.6,
                alpha=0.9,
                zorder=3,
            )
        ax.set_title(str(year), fontsize=17, fontweight="bold", pad=10)
    axes[0].set_ylabel("Latitude", fontsize=11)
    axes[2].set_ylabel("Latitude", fontsize=11)
    axes[2].set_xlabel("Longitude", fontsize=11)
    axes[3].set_xlabel("Longitude", fontsize=11)
    index_handles = [
        Patch(facecolor=BMWP_CLASS_COLORS[label], edgecolor="#1F1F1F", label=label)
        for label in ["Muito boa", "Boa", "Regular", "Ruim", "Pessima"]
    ]
    area_handles = [
        Line2D([0], [0], color=CONTROL_AREA_COLORS["Area de controle 01"], lw=1.2, ls="--", label="Área de controle 01"),
        Line2D([0], [0], color=CONTROL_AREA_COLORS["Area de controle 02"], lw=1.2, ls="--", label="Área de controle 02"),
    ]
    fig.legend(handles=index_handles, loc="lower center", ncol=5, frameon=False, fontsize=10.5, bbox_to_anchor=(0.5, 0.052))
    fig.legend(handles=area_handles, loc="lower center", ncol=2, frameon=False, fontsize=10.5, bbox_to_anchor=(0.5, 0.023))
    fig.tight_layout(rect=(0.03, 0.11, 0.99, 0.96))
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300)
    plt.close(fig)


def plot_gradient_indicator(annual: pd.DataFrame, output_png: Path, column: str, label: str, cmap_name: str = "YlGn") -> None:
    years = [2023, 2024, 2025, 2026]
    coords_plot = annual[["Ponto", "Longitude", "Latitude"]].drop_duplicates()
    context = _spatial_context(coords_plot)
    max_value = max(1.0, float(annual[column].max()))
    cmap = plt.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=0, vmax=max_value)
    fig, axes_grid = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=450, sharex=True, sharey=True)
    axes = axes_grid.ravel()
    mappable = None
    for ax, year in zip(axes, years, strict=True):
        _base_map(ax, coords_plot, context)
        data = annual[annual["Ano_Temporal"].eq(year)].copy()
        not_monitored = data[data["Status_Monitoramento"].eq("Não monitorado")]
        monitored = data[data["Status_Monitoramento"].eq("Monitorado")]
        ax.scatter(
            not_monitored["Longitude"],
            not_monitored["Latitude"],
            s=115,
            color="#D7DDE0",
            edgecolor="#8B969A",
            linewidth=0.55,
            zorder=2,
        )
        sizes = monitored[column].map(lambda value: _bubble_size(float(value), max_value))
        mappable = ax.scatter(
            monitored["Longitude"],
            monitored["Latitude"],
            s=sizes,
            c=monitored[column],
            cmap=cmap,
            norm=norm,
            edgecolor="#1F1F1F",
            linewidth=0.55,
            alpha=0.9,
            zorder=3,
        )
        ax.set_title(str(year), fontsize=17, fontweight="bold", pad=10)
    axes[0].set_ylabel("Latitude", fontsize=11)
    axes[2].set_ylabel("Latitude", fontsize=11)
    axes[2].set_xlabel("Longitude", fontsize=11)
    axes[3].set_xlabel("Longitude", fontsize=11)
    cax = fig.add_axes([0.91, 0.24, 0.018, 0.52])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label, fontsize=11)
    cb.ax.tick_params(labelsize=9)
    handles = [
        Line2D([0], [0], color=CONTROL_AREA_COLORS["Area de controle 01"], lw=1.2, ls="--", label="Área de controle 01"),
        Line2D([0], [0], color=CONTROL_AREA_COLORS["Area de controle 02"], lw=1.2, ls="--", label="Área de controle 02"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=10.5, bbox_to_anchor=(0.5, 0.03))
    fig.tight_layout(rect=(0.03, 0.09, 0.89, 0.96))
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300)
    plt.close(fig)


def build(output_dir: Path, support_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(ANALYTIC_XLSX, sheet_name="base_analitica")
    point_campaign = pd.read_excel(ANALYTIC_XLSX, sheet_name="ponto_campanha")
    annual = build_annual_metrics(point_campaign)
    bmwp_comparison, bmwp_campaign_scores = build_bmwp_annual_comparison(base, point_campaign, annual)

    outputs = {
        "bmwp": output_dir / "APROVACAO_06B_mini_mapas_anuais_bmwp_zoobentos.png",
        "ept": output_dir / "APROVACAO_06C_mini_mapas_anuais_ept_zoobentos.png",
        "chol": output_dir / "APROVACAO_06D_mini_mapas_anuais_chol_zoobentos.png",
        "table": output_dir / "APROVACAO_06BCD_df_mini_mapas_anuais_bmwp_ept_chol_zoobentos.xlsx",
    }
    plot_bmwp(annual, outputs["bmwp"])
    plot_gradient_indicator(annual, outputs["ept"], "ept_percentual", "%EPT", cmap_name="YlGn")
    plot_gradient_indicator(annual, outputs["chol"], "chol_percentual", "%CHOL", cmap_name="RdYlGn_r")

    with pd.ExcelWriter(outputs["table"], engine="openpyxl") as writer:
        annual.to_excel(writer, sheet_name="indicadores_anuais_ponto", index=False)
        bmwp_comparison.to_excel(writer, sheet_name="comparativo_BMWP_anual", index=False)
        bmwp_campaign_scores.to_excel(writer, sheet_name="BMWP_campanha_ponto", index=False)
        point_campaign.to_excel(writer, sheet_name="ponto_campanha", index=False)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": "BRAAVG002",
        "group": "Zoobentos",
        "layout_reference": "Ictiofauna AVG minimapas anuais aprovados, painel 2x2 por indicador",
        "method": {
            "BMWP": "media anual por ponto das campanhas monitoradas; BMWP por campanha calculado por familias unicas; Excel inclui comparativo com BMWP acumulado anual por familias",
            "EPT": "percentual anual ponderado pela abundancia total do ponto; gradiente verde",
            "CHOL": "percentual anual ponderado pela abundancia total do ponto; gradiente verde-vermelho, com maiores valores em vermelho por indicarem menor qualidade",
        },
        "outputs": outputs,
    }
    manifest_path = support_dir / "manifesto_aprovacao_06BCD_minimapas_bioindicadores_zoobentos_20260721.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera minimapas AVG Zoobentos no layout aprovado da Ictiofauna.")
    parser.add_argument("--output-dir", type=Path, default=FINAL_DIR)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    args = parser.parse_args()
    manifest = build(args.output_dir, args.support_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
