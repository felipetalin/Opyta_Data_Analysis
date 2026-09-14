from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

GEOARC_DIR = SCRIPT_DIR.parent / "geoarc001"
if str(GEOARC_DIR) not in sys.path:
    sys.path.insert(0, str(GEOARC_DIR))

import build_ictio_avg_threatened_species_synthesis as sentinel_base  # noqa: E402
import run_ictio_avg_tradicional_consolidado_2026 as traditional  # noqa: E402
from generate_functional_spatial_mini_maps import (  # noqa: E402
    _ada_polygons,
    _add_ada,
    _add_hydrology,
    _hydrology_segments,
    _point_limits,
    load_ada,
    load_hydrology,
    summarize_ada,
    summarize_hydrology,
)
from opyta_analysis.config import load_theme  # noqa: E402
from opyta_analysis.geo_reference import read_kml_polygon_coordinates  # noqa: E402


ROOT = traditional.ROOT
FINAL_DIR = sentinel_base.FINAL_DIR
SUPPORT_DIR = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "functional_group_sentinel_maps_20260716"
)
SOURCE = sentinel_base.SOURCE
HYDROLOGY_LAYER = sentinel_base.HYDROLOGY_LAYER
ADA_LAYER = sentinel_base.ADA_LAYER
CONTROL_AREA_LAYERS = sentinel_base.CONTROL_AREA_LAYERS
CONTROL_AREA_COLORS = sentinel_base.CONTROL_AREA_COLORS

FUNCTIONAL_GROUPS = {
    "especialistas_loticos_sensiveis": {
        "rotulo": "Especialistas lóticos sensíveis",
        "cor": "#0B6E3A",
        "offset": (-0.00016, 0.00014),
        "especies": [
            "Neoplecostomus franciscoensis",
            "Pareiorhaphis mutuca",
            "Trichomycterus brasiliensis",
            "Trichomycterus novalimensis",
        ],
    },
    "generalistas_tolerantes": {
        "rotulo": "Generalistas tolerantes",
        "cor": "#C7782B",
        "offset": (0.00016, -0.00014),
        "especies": [
            "Geophagus brasiliensis",
            "Phalloceros uai",
            "Poecilia cf. mexicana",
            "Poecilia reticulata",
            "Rhamdia quelen",
        ],
    },
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


def _bubble_size(value: float, max_value: float) -> float:
    if max_value <= 0 or value <= 0:
        return 0.0
    return 24 + np.sqrt(value / max_value) * 380


def load_latest_coordinates(source: Path) -> pd.DataFrame:
    return sentinel_base.load_latest_coordinates(source)


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
            columns=["fonte", "camada", "polygon_id", "ring_id", "ring_type", "vertex_order", "Longitude", "Latitude", "area_controle"]
        )
    return pd.concat(frames, ignore_index=True)


def _control_polygons(control_areas: pd.DataFrame, xmin: float, xmax: float, ymin: float, ymax: float) -> dict[str, list[np.ndarray]]:
    polygons: dict[str, list[np.ndarray]] = {label: [] for label in CONTROL_AREA_LAYERS}
    if control_areas.empty:
        return polygons
    outer = control_areas[control_areas["ring_type"] == "outer"].copy()
    for (label, _source, polygon_id, ring_id), ring in outer.groupby(["area_controle", "fonte", "polygon_id", "ring_id"], sort=False):
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
                facecolors=[matplotlib.colors.to_rgba(color, 0.055)],
                edgecolors=[matplotlib.colors.to_rgba(color, 0.82)],
                linewidths=1.0,
                linestyles="--",
                zorder=0.18,
            )
        )


def build_group_annual_base(source: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    effort = pd.read_excel(source, sheet_name="Metadados_Esforco")
    results = pd.read_excel(source, sheet_name="Resultados_Ictiofauna")
    effort = effort[effort["Tipo_de_Amostragem"].astype(str).str.lower().str.contains("quant", na=False)].copy()
    effort["Esforco"] = pd.to_numeric(effort["Esforco"], errors="coerce")
    effort = effort[effort["Esforco"].notna() & (effort["Esforco"] > 0)].copy()
    effort_sample = (
        effort.groupby(["Campanha", "Ponto", "Ano_Temporal", "Periodo_Hidrologico", "Area_Controle"], as_index=False)
        .agg(esforco_total=("Esforco", "sum"))
    )
    rows = []
    for code, definition in FUNCTIONAL_GROUPS.items():
        species = definition["especies"]
        counts = (
            results[results["Nome_Cientifico"].isin(species)]
            .groupby(["Campanha", "Ponto"], as_index=False)
            .agg(contagem=("Numero_de_Individuos", "sum"), riqueza_especies=("Nome_Cientifico", "nunique"))
        )
        base = effort_sample.copy()
        base["grupo_funcional"] = code
        base["grupo_rotulo"] = definition["rotulo"]
        base = base.merge(counts, on=["Campanha", "Ponto"], how="left")
        base["contagem"] = pd.to_numeric(base["contagem"], errors="coerce").fillna(0)
        base["riqueza_especies"] = pd.to_numeric(base["riqueza_especies"], errors="coerce").fillna(0).astype(int)
        base["cpuen"] = (base["contagem"] / base["esforco_total"]) * 100
        rows.append(base)
    campaign_level = pd.concat(rows, ignore_index=True)
    campaign_level["campanha_curta"] = campaign_level["Campanha"].map(lambda value: f"C{traditional.standard_campaign_sequence(value):02d}")
    annual = (
        campaign_level.groupby(["Ano_Temporal", "Ponto", "Area_Controle", "grupo_funcional", "grupo_rotulo"], as_index=False)
        .agg(
            cpuen_medio_anual=("cpuen", "mean"),
            cpuen_total_anual=("cpuen", "sum"),
            contagem_total=("contagem", "sum"),
            riqueza_media_especies=("riqueza_especies", "mean"),
            n_campanhas_amostradas=("Campanha", "nunique"),
            campanhas_com_registro=("contagem", lambda values: int((pd.to_numeric(values, errors="coerce") > 0).sum())),
        )
        .rename(columns={"Ano_Temporal": "ano", "Ponto": "nome_ponto"})
    )
    return campaign_level, annual


def plot_group_maps(annual: pd.DataFrame, coords: pd.DataFrame, output_png: Path, theme: dict) -> None:
    years = [2023, 2024, 2025, 2026]
    coords_plot = coords[["Ponto", "Longitude", "Latitude"]].copy()
    hydrology = load_hydrology([HYDROLOGY_LAYER])
    ada = load_ada(ADA_LAYER)
    control_areas = load_control_areas()
    xmin, xmax, ymin, ymax = _point_limits(coords_plot)
    segments = _hydrology_segments(hydrology, xmin, xmax, ymin, ymax)
    polygons = _ada_polygons(ada, xmin, xmax, ymin, ymax)
    control_polygons = _control_polygons(control_areas, xmin, xmax, ymin, ymax)
    max_value = float(annual["cpuen_medio_anual"].max()) if not annual.empty else 0.0

    fig, axes_grid = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=int(theme.get("dpi", 450)), sharex=True, sharey=True)
    axes = axes_grid.ravel()
    for ax, year in zip(axes, years, strict=True):
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

        year_data = annual[annual["ano"] == year].copy()
        for code, definition in FUNCTIONAL_GROUPS.items():
            subset = year_data[year_data["grupo_funcional"] == code].merge(
                coords_plot, left_on="nome_ponto", right_on="Ponto", how="left"
            )
            dx, dy = definition["offset"]
            values = pd.to_numeric(subset["cpuen_medio_anual"], errors="coerce").fillna(0).to_numpy(dtype=float)
            sizes = np.array([_bubble_size(value, max_value) for value in values])
            keep = sizes > 0
            ax.scatter(
                subset.loc[keep, "Longitude"] + dx,
                subset.loc[keep, "Latitude"] + dy,
                s=sizes[keep],
                color=definition["cor"],
                edgecolor="#1F1F1F",
                linewidth=0.55,
                alpha=0.84,
                zorder=3,
            )

        ax.set_title(str(year), fontsize=17, fontweight="bold", pad=10)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.grid(color="#E8ECEE", linewidth=0.65)
        ax.tick_params(axis="both", labelsize=8.5)
        ax.set_aspect("equal", adjustable="box")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
    axes[0].set_ylabel("Latitude", fontsize=11)
    axes[2].set_ylabel("Latitude", fontsize=11)
    axes[2].set_xlabel("Longitude", fontsize=11)
    axes[3].set_xlabel("Longitude", fontsize=11)

    group_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=definition["cor"], markeredgecolor="#1F1F1F", markersize=10, label=definition["rotulo"])
        for definition in FUNCTIONAL_GROUPS.values()
    ]
    control_handles = [
        Line2D([0], [0], color=CONTROL_AREA_COLORS[label], linestyle="--", linewidth=1.4, label=label)
        for label in CONTROL_AREA_LAYERS
    ]
    size_values = [max_value * relative for relative in (0.25, 0.55, 1.00)]
    size_handles = [
        plt.scatter([], [], s=_bubble_size(value, max_value), color="#8EA66B", edgecolor="#1F1F1F", linewidth=0.55, label=label)
        for value, label in zip(
            size_values,
            [f"Baixa ({size_values[0]:.2f})", f"Media ({size_values[1]:.2f})", f"Alta ({size_values[2]:.2f})"],
            strict=True,
        )
    ]
    fig.legend(handles=group_handles, loc="lower center", bbox_to_anchor=(0.50, 0.092), ncol=2, frameon=False, fontsize=11.2)
    fig.legend(handles=control_handles, loc="lower center", bbox_to_anchor=(0.50, 0.058), ncol=2, frameon=False, fontsize=10.2)
    fig.legend(handles=size_handles, title="CPUEn media anual do grupo", loc="lower center", bbox_to_anchor=(0.50, 0.016), ncol=3, frameon=False, fontsize=9.8, title_fontsize=10.4)
    fig.subplots_adjust(left=0.065, right=0.992, top=0.94, bottom=0.20, wspace=0.075, hspace=0.22)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, pad_inches=0.04)
    plt.close(fig)


def write_outputs(
    campaign_level: pd.DataFrame,
    annual: pd.DataFrame,
    coords: pd.DataFrame,
    output_xlsx: Path,
) -> None:
    hydrology_summary = summarize_hydrology(load_hydrology([HYDROLOGY_LAYER]))
    ada_summary = summarize_ada(load_ada(ADA_LAYER))
    control_areas = load_control_areas()
    if control_areas.empty:
        control_summary = pd.DataFrame(columns=["area_controle", "poligonos", "vertices", "lon_min", "lon_max", "lat_min", "lat_max"])
    else:
        control_summary = (
            control_areas.groupby("area_controle", as_index=False)
            .agg(
                poligonos=("polygon_id", "nunique"),
                vertices=("vertex_order", "size"),
                lon_min=("Longitude", "min"),
                lon_max=("Longitude", "max"),
                lat_min=("Latitude", "min"),
                lat_max=("Latitude", "max"),
            )
            .sort_values("area_controle")
        )
    definitions = pd.DataFrame(
        [
            {
                "grupo_funcional": code,
                "grupo_rotulo": definition["rotulo"],
                "especies": "; ".join(definition["especies"]),
            }
            for code, definition in FUNCTIONAL_GROUPS.items()
        ]
    )
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        annual.to_excel(writer, sheet_name="cpuen_anual_ponto_grupo", index=False)
        campaign_level.to_excel(writer, sheet_name="cpuen_campanha_ponto_grupo", index=False)
        definitions.to_excel(writer, sheet_name="definicoes_grupos", index=False)
        coords.to_excel(writer, sheet_name="coordenadas_pontos", index=False)
        hydrology_summary.to_excel(writer, sheet_name="malha_hidrica_resumo", index=False)
        ada_summary.to_excel(writer, sheet_name="ada_resumo", index=False)
        control_summary.to_excel(writer, sheet_name="areas_controle_resumo", index=False)


def build(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", "braavg002")
    campaign_level, annual = build_group_annual_base(SOURCE)
    coords = load_latest_coordinates(SOURCE)
    figure = output_dir / "10E_grafico_mini_mapas_grupos_funcionais_sentinelas_ano_ictiofauna.png"
    table = output_dir / "10E_df_mini_mapas_grupos_funcionais_sentinelas_ano_ictiofauna.xlsx"
    support_figure = support_dir / figure.name
    support_table = support_dir / table.name
    plot_group_maps(annual, coords, figure, theme)
    write_outputs(campaign_level, annual, coords, table)
    shutil.copy2(figure, support_figure)
    shutil.copy2(table, support_table)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": traditional.PROJECT_CODE,
        "status": "generated",
        "metric": "CPUEn",
        "groups": {
            code: {"rotulo": definition["rotulo"], "especies": definition["especies"]}
            for code, definition in FUNCTIONAL_GROUPS.items()
        },
        "figure": str(figure),
        "table": str(table),
        "support_figure": str(support_figure),
        "support_table": str(support_table),
        "years": sorted(int(x) for x in annual["ano"].dropna().unique().tolist()),
        "points": int(coords["Ponto"].nunique()),
        "coordinate_strategy": "last_coordenada_valida_planilha",
        "coordinate_source": str(SOURCE),
        "control_area_layers": {label: str(path) for label, path in CONTROL_AREA_LAYERS.items()},
        "map_rule": "CPUEn media anual por ponto e grupo funcional, incluindo zeros nas campanhas quantitativas amostradas sem registro do grupo.",
    }
    manifest = support_dir / "manifesto_10E_grupos_funcionais_sentinelas_ictiofauna.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
