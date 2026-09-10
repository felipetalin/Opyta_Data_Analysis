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

import build_ictio_avg_species_cpuen_synthesis as species08c  # noqa: E402
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
FINAL_DIR = species08c.FINAL_DIR
SUPPORT_DIR = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "threatened_species_synthesis_20260716"
)
SOURCE = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "geoarc001_long_study_source_20260713"
    / "braavg002_geoarc001_source_ictiofauna.xlsx"
)
HYDROLOGY_LAYER = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\Hidrografia.kmz")
ADA_LAYER = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\1AVGM015_ADA_Sem_Adutora_region.kmz")
CONTROL_AREA_LAYERS = {
    "Area de controle 01": Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\771_area_controle_01_pl.kml"),
    "Area de controle 02": Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\771_area_controle_02_pl.kml"),
}
CONTROL_AREA_COLORS = {
    "Area de controle 01": "#1D8B4A",
    "Area de controle 02": "#6B8F35",
}

THREATENED_SPECIES = ["Neoplecostomus franciscoensis", "Pareiorhaphis mutuca"]
EXOTIC_SPECIES = ["Poecilia cf. mexicana", "Poecilia reticulata"]
SPECIES_COLORS = {
    "Neoplecostomus franciscoensis": "#0B6E3A",
    "Pareiorhaphis mutuca": "#C0711F",
    "Poecilia cf. mexicana": "#7E3F98",
    "Poecilia reticulata": "#1F78B4",
}
SPECIES_OFFSETS = {
    "Neoplecostomus franciscoensis": (-0.00018, 0.00012),
    "Pareiorhaphis mutuca": (0.00018, -0.00012),
    "Poecilia cf. mexicana": (-0.00018, 0.00012),
    "Poecilia reticulata": (0.00018, -0.00012),
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


def _campaign_short(campaign: object) -> str:
    return f"C{traditional.standard_campaign_sequence(campaign):02d}"


def _year_from_campaign(campaign: object) -> int | None:
    seq = traditional.standard_campaign_sequence(campaign)
    for year, start, end in traditional.TEMPORAL_YEAR_BANDS:
        if start <= seq <= end:
            return int(year)
    return None


def _decorate_year_bands(ax: Any, campaigns: list[str], n_species: int) -> None:
    seq_by_idx = {idx: traditional.standard_campaign_sequence(campaign) for idx, campaign in enumerate(campaigns)}
    for year, start, end in traditional.TEMPORAL_YEAR_BANDS:
        indices = [idx for idx, seq in seq_by_idx.items() if start <= seq <= end]
        if not indices:
            continue
        left = min(indices) - 0.5
        right = max(indices) + 0.5
        ax.text((left + right) / 2, -0.72, f"Ano {year}", ha="center", va="bottom", fontsize=8.7, color="#50614A")
        ax.axvline(right, color="#B8B8B8", linestyle=":", linewidth=0.75, zorder=3)
    ax.set_ylim(n_species - 0.5, -0.78)


def plot_threatened_panel_a4(
    totals: pd.DataFrame,
    presence: pd.DataFrame,
    spatial: pd.DataFrame,
    output_png: Path,
) -> str:
    species = totals["nome_cientifico"].tolist()
    campaigns = [col for col in presence.columns if col != "nome_cientifico"]
    points = [col for col in spatial.columns if col != "nome_cientifico"]
    n_species = len(species)
    y = np.arange(n_species)

    fig = plt.figure(figsize=(11.69, 8.27), dpi=450)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.02, 1.86, 1.18], wspace=0.09)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_time = fig.add_subplot(gs[0, 1], sharey=ax_bar)
    ax_space = fig.add_subplot(gs[0, 2], sharey=ax_bar)

    max_percent = float(totals["cpuen_percentual"].max()) if n_species else 0.0
    bars = ax_bar.barh(y, totals["cpuen_percentual"], color=species08c.GREEN_HIGH, edgecolor=species08c.BAR_EDGE, height=0.50)
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(species, fontsize=10.6)
    for label in ax_bar.get_yticklabels():
        label.set_fontstyle("italic")
    ax_bar.invert_yaxis()
    ax_bar.set_xlim(0, max(100.0, max_percent * 1.10))
    ax_bar.set_xlabel("Contribuicao relativa da CPUEn (%)", fontsize=10.4)
    ax_bar.grid(axis="x", color="#D9D9D9", linewidth=0.55, alpha=0.7)
    ax_bar.tick_params(axis="x", labelsize=9.3)
    ax_bar.tick_params(axis="y", length=0)
    for spine in ["top", "right", "left"]:
        ax_bar.spines[spine].set_visible(False)
    for bar, value in zip(bars, totals["cpuen_percentual"], strict=True):
        ax_bar.text(bar.get_width() + 1.2, bar.get_y() + bar.get_height() / 2, f"{value:.1f}", va="center", ha="left", fontsize=9.4)

    presence_values = presence[campaigns].to_numpy(dtype=float)
    max_temporal = float(np.nanmax(presence_values)) if presence_values.size else 0.0
    temporal_relative = np.divide(
        presence_values,
        max_temporal,
        out=np.zeros_like(presence_values, dtype=float),
        where=max_temporal > 0,
    )
    intensity = np.zeros_like(presence_values, dtype=float)
    intensity[(presence_values > 0) & (temporal_relative <= 1 / 3)] = 1
    intensity[(temporal_relative > 1 / 3) & (temporal_relative <= 2 / 3)] = 2
    intensity[temporal_relative > 2 / 3] = 3
    cmap = matplotlib.colors.ListedColormap([species08c.ABSENT_COLOR, species08c.GREEN_LOW, species08c.GREEN_MID, species08c.GREEN_HIGH])
    ax_time.imshow(intensity, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=3, zorder=1)
    _decorate_year_bands(ax_time, campaigns, n_species)
    ax_time.set_xticks(np.arange(len(campaigns)))
    ax_time.set_xticklabels([_campaign_short(campaign) for campaign in campaigns], rotation=90, fontsize=5.4)
    ax_time.set_xlabel("Ocorrencia por campanha (CPUEn)", fontsize=10.4)
    ax_time.tick_params(axis="y", left=False, labelleft=False)
    ax_time.set_xticks(np.arange(-0.5, len(campaigns), 1), minor=True)
    ax_time.set_yticks(np.arange(-0.5, n_species, 1), minor=True)
    ax_time.grid(which="minor", color="white", linewidth=0.22)
    ax_time.tick_params(which="minor", bottom=False, left=False)
    for spine in ["top", "right", "left"]:
        ax_time.spines[spine].set_visible(False)

    spatial_values = spatial[points].to_numpy(dtype=float) if points else np.empty((n_species, 0))
    row_max = np.nanmax(spatial_values, axis=1) if points else np.zeros(n_species)
    relative_spatial = np.divide(
        spatial_values,
        row_max[:, None],
        out=np.zeros_like(spatial_values, dtype=float),
        where=row_max[:, None] > 0,
    )
    for x, point in enumerate(points):
        values = spatial[point].to_numpy(dtype=float)
        relative_values = relative_spatial[:, x]
        sizes = np.where(values > 0, 36 + relative_values * 260, 0)
        color = species08c.AREA_COLORS.get(traditional.avg_runner.AREA_BY_POINT.get(point), "#777777")
        ax_space.scatter(np.full(n_species, x), y, s=sizes, color=color, edgecolor="#1F1F1F", linewidth=0.42, alpha=0.82)
    if "PIC-10" in points:
        ax_space.axvline(points.index("PIC-10") - 0.5, color="#4F4F4F", linestyle=":", linewidth=0.95)
    ax_space.set_xlim(-0.6, len(points) - 0.4)
    ax_space.set_xticks(np.arange(len(points)))
    ax_space.set_xticklabels(points, rotation=90, fontsize=8.0)
    ax_space.text(
        0.5,
        -0.23,
        "Distribuicao espacial relativa",
        transform=ax_space.transAxes,
        ha="center",
        va="top",
        fontsize=9.6,
    )
    ax_space.tick_params(axis="y", left=False, labelleft=False)
    ax_space.grid(axis="y", color="#EEEEEE", linewidth=0.5)
    for spine in ["top", "right", "left"]:
        ax_space.spines[spine].set_visible(False)

    heat_handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=species08c.GREEN_HIGH, markeredgecolor="#777777", markersize=7.0, label="Alta (>67%)"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=species08c.GREEN_MID, markeredgecolor="#777777", markersize=7.0, label="Media (34-67%)"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=species08c.GREEN_LOW, markeredgecolor="#777777", markersize=7.0, label="Baixa (<=33%)"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=species08c.ABSENT_COLOR, markeredgecolor="#777777", markersize=7.0, label="Ausencia"),
    ]
    area_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=species08c.AREA_COLORS[species08c.AREA_01], markeredgecolor="#1F1F1F", markersize=7.2, label="Area de controle 01"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=species08c.AREA_COLORS[species08c.AREA_02], markeredgecolor="#1F1F1F", markersize=7.2, label="Area de controle 02"),
    ]
    size_handles = [
        plt.scatter([], [], s=36 + relative * 260, color="#9EB77E", edgecolor="#1F1F1F", linewidth=0.42, label=label)
        for relative, label in [(0.25, "Baixa (<=33%)"), (0.55, "Media (34-67%)"), (0.90, "Alta (>67%)")]
    ]
    fig.legend(handles=heat_handles, loc="lower center", bbox_to_anchor=(0.50, 0.135), ncol=4, frameon=False, fontsize=8.2)
    fig.legend(handles=area_handles, loc="lower center", bbox_to_anchor=(0.50, 0.085), ncol=2, frameon=False, fontsize=8.0)
    fig.legend(handles=size_handles, title="CPUEn relativa no ponto", loc="lower center", bbox_to_anchor=(0.50, 0.025), ncol=3, frameon=False, fontsize=8.0, title_fontsize=8.4)
    fig.subplots_adjust(left=0.21, right=0.975, top=0.90, bottom=0.31)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, pad_inches=0.04)
    plt.close(fig)
    return str(output_png)


def build_subset_panel(
    output_dir: Path,
    support_dir: Path,
    species_list: list[str] | None = None,
    product_prefix: str = "10A",
    product_slug: str = "especies_ameacadas",
) -> dict[str, str]:
    species_list = species_list or THREATENED_SPECIES
    totals, presence, spatial = species08c.build_cpuen_tables()
    totals = totals[totals["nome_cientifico"].isin(species_list)].copy()
    totals = totals.sort_values(["cpuen_total", "nome_cientifico"], ascending=[False, True]).reset_index(drop=True)
    threatened_total = float(totals["cpuen_total"].sum())
    totals["cpuen_percentual_total_assembleia"] = totals["cpuen_percentual"]
    totals["cpuen_percentual"] = np.where(threatened_total > 0, (totals["cpuen_total"] / threatened_total) * 100, 0.0)
    totals["ordem"] = np.arange(1, len(totals) + 1)
    presence = presence[presence["nome_cientifico"].isin(species_list)].copy()
    presence = totals[["nome_cientifico"]].merge(presence, on="nome_cientifico", how="left")
    spatial = spatial[spatial["nome_cientifico"].isin(species_list)].copy()
    spatial = totals[["nome_cientifico"]].merge(spatial, on="nome_cientifico", how="left")

    figure = output_dir / f"{product_prefix}_grafico_sintese_cpuen_{product_slug}_ictiofauna.png"
    table = output_dir / f"{product_prefix}_df_sintese_cpuen_{product_slug}_ictiofauna.xlsx"
    support_figure = support_dir / figure.name
    support_table = support_dir / table.name
    plot_threatened_panel_a4(totals, presence, spatial, figure)
    temp_table = Path(species08c.write_tables(totals, presence, spatial, output_dir))
    if temp_table != table:
        table.parent.mkdir(parents=True, exist_ok=True)
        temp_table.replace(table)
    plot_threatened_panel_a4(totals, presence, spatial, support_figure)
    temp_support_table = Path(species08c.write_tables(totals, presence, spatial, support_dir))
    if temp_support_table != support_table:
        support_table.parent.mkdir(parents=True, exist_ok=True)
        temp_support_table.replace(support_table)
    return {
        "figure": str(figure),
        "table": str(table),
        "support_figure": str(support_figure),
        "support_table": str(support_table),
    }


def load_latest_coordinates(source: Path) -> pd.DataFrame:
    points = pd.read_excel(source, sheet_name="Pontos_e_Campanhas")
    point_order = sum(traditional.REPORT_POINT_GROUPS.values(), [])
    points = points[points["Ponto"].isin(point_order)].copy()
    points["campanha_seq"] = points["Campanha"].map(traditional.standard_campaign_sequence)
    coords = (
        points.dropna(subset=["Latitude", "Longitude"])
        .sort_values(["Ponto", "campanha_seq"])
        .groupby("Ponto", as_index=False)
        .tail(1)
        .rename(columns={"Ponto": "nome_ponto"})
    )
    coords["Ponto"] = coords["nome_ponto"]
    return coords[["nome_ponto", "Ponto", "Latitude", "Longitude", "Campanha", "Fonte_Coordenada", "Fonte_Coordenada_Ajuste"]]


def build_annual_species_base(source: Path, species_list: list[str] | None = None) -> pd.DataFrame:
    species_list = species_list or THREATENED_SPECIES
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
    counts = (
        results[results["Nome_Cientifico"].isin(species_list)]
        .groupby(["Campanha", "Ponto", "Nome_Cientifico"], as_index=False)
        .agg(contagem=("Numero_de_Individuos", "sum"))
    )
    for species in species_list:
        base = effort_sample.copy()
        base["nome_cientifico"] = species
        base = base.merge(
            counts[counts["Nome_Cientifico"] == species][["Campanha", "Ponto", "contagem"]],
            on=["Campanha", "Ponto"],
            how="left",
        )
        base["contagem"] = pd.to_numeric(base["contagem"], errors="coerce").fillna(0)
        base["cpuen"] = (base["contagem"] / base["esforco_total"]) * 100
        rows.append(base)
    campaign_level = pd.concat(rows, ignore_index=True)
    campaign_level["campanha_curta"] = campaign_level["Campanha"].map(_campaign_short)
    annual = (
        campaign_level.groupby(["Ano_Temporal", "Ponto", "Area_Controle", "nome_cientifico"], as_index=False)
        .agg(
            cpuen_medio_anual=("cpuen", "mean"),
            cpuen_total_anual=("cpuen", "sum"),
            contagem_total=("contagem", "sum"),
            n_campanhas_amostradas=("Campanha", "nunique"),
            campanhas_com_registro=("contagem", lambda values: int((pd.to_numeric(values, errors="coerce") > 0).sum())),
        )
        .rename(columns={"Ano_Temporal": "ano", "Ponto": "nome_ponto"})
    )
    return campaign_level, annual


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


def _size_values(values: pd.Series, max_value: float) -> np.ndarray:
    arr = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(dtype=float)
    if max_value <= 0:
        return np.zeros_like(arr)
    return np.where(arr > 0, 26 + np.sqrt(arr / max_value) * 390, 0)


def _bubble_size(value: float, max_value: float) -> float:
    if max_value <= 0 or value <= 0:
        return 0.0
    return 26 + np.sqrt(value / max_value) * 390


def plot_annual_maps(
    annual: pd.DataFrame,
    coords: pd.DataFrame,
    output_png: Path,
    theme: dict,
    species_list: list[str] | None = None,
) -> None:
    species_list = species_list or THREATENED_SPECIES
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
        for species in species_list:
            subset = year_data[year_data["nome_cientifico"] == species].merge(
                coords_plot, left_on="nome_ponto", right_on="Ponto", how="left"
            )
            dx, dy = SPECIES_OFFSETS[species]
            sizes = _size_values(subset["cpuen_medio_anual"], max_value)
            keep = sizes > 0
            ax.scatter(
                subset.loc[keep, "Longitude"] + dx,
                subset.loc[keep, "Latitude"] + dy,
                s=sizes[keep],
                color=SPECIES_COLORS[species],
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

    species_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=SPECIES_COLORS[species], markeredgecolor="#1F1F1F", markersize=10, label=species)
        for species in species_list
    ]
    size_handles = [
        plt.scatter([], [], s=size, color="#8EA66B", edgecolor="#1F1F1F", linewidth=0.55, label=label)
        for size, label in [(26 + 0.30 * 390, "Baixa"), (26 + 0.60 * 390, "Média"), (26 + 1.00 * 390, "Alta")]
    ]
    control_handles = [
        Line2D([0], [0], color=CONTROL_AREA_COLORS[label], linestyle="--", linewidth=1.4, label=label)
        for label in CONTROL_AREA_LAYERS
    ]
    species_legend = fig.legend(handles=species_handles, loc="lower center", bbox_to_anchor=(0.30, 0.055), ncol=2, frameon=False, fontsize=11.5)
    for text in species_legend.get_texts():
        text.set_fontstyle("italic")
    fig.legend(handles=control_handles, loc="lower center", bbox_to_anchor=(0.58, 0.055), ncol=2, frameon=False, fontsize=10.8)
    fig.legend(handles=size_handles, title="CPUEn média anual", loc="lower center", bbox_to_anchor=(0.77, 0.042), ncol=3, frameon=False, fontsize=11, title_fontsize=11.5)
    for legend in list(fig.legends):
        legend.remove()
    size_values = [max_value * relative for relative in (0.25, 0.55, 1.00)]
    size_handles = [
        plt.scatter([], [], s=_bubble_size(value, max_value), color="#8EA66B", edgecolor="#1F1F1F", linewidth=0.55, label=label)
        for value, label in zip(
            size_values,
            [f"Baixa ({size_values[0]:.2f})", f"Media ({size_values[1]:.2f})", f"Alta ({size_values[2]:.2f})"],
            strict=True,
        )
    ]
    species_legend = fig.legend(handles=species_handles, loc="lower center", bbox_to_anchor=(0.50, 0.092), ncol=2, frameon=False, fontsize=11.2)
    for text in species_legend.get_texts():
        text.set_fontstyle("italic")
    fig.legend(handles=control_handles, loc="lower center", bbox_to_anchor=(0.50, 0.058), ncol=2, frameon=False, fontsize=10.2)
    fig.legend(handles=size_handles, title="CPUEn media anual", loc="lower center", bbox_to_anchor=(0.50, 0.016), ncol=3, frameon=False, fontsize=9.8, title_fontsize=10.4)
    fig.text(
        0.012,
        0.018,
        "Bolhas proporcionais à CPUEn média anual por ponto; zeros representam campanhas amostradas sem registro da espécie.",
        fontsize=9.6,
        color="#505050",
    )
    for text in list(fig.texts):
        text.remove()
    fig.subplots_adjust(left=0.065, right=0.992, top=0.94, bottom=0.20, wspace=0.075, hspace=0.22)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, pad_inches=0.04)
    plt.close(fig)


def write_maps_table(
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
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        annual.to_excel(writer, sheet_name="cpuen_anual_ponto_especie", index=False)
        campaign_level.to_excel(writer, sheet_name="cpuen_campanha_ponto_especie", index=False)
        coords.to_excel(writer, sheet_name="coordenadas_pontos", index=False)
        hydrology_summary.to_excel(writer, sheet_name="malha_hidrica_resumo", index=False)
        ada_summary.to_excel(writer, sheet_name="ada_resumo", index=False)
        control_summary.to_excel(writer, sheet_name="areas_controle_resumo", index=False)


def build_custom(
    species_list: list[str],
    panel_prefix: str,
    map_prefix: str,
    product_slug: str,
    manifest_slug: str,
    output_dir: Path = FINAL_DIR,
    support_dir: Path = SUPPORT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", "braavg002")

    panel_outputs = build_subset_panel(output_dir, support_dir, species_list, panel_prefix, product_slug)
    campaign_level, annual = build_annual_species_base(SOURCE, species_list)
    coords = load_latest_coordinates(SOURCE)
    map_png = output_dir / f"{map_prefix}_grafico_mini_mapas_{product_slug}_ano_ictiofauna.png"
    map_xlsx = output_dir / f"{map_prefix}_df_mini_mapas_{product_slug}_ano_ictiofauna.xlsx"
    support_map_png = support_dir / map_png.name
    support_map_xlsx = support_dir / map_xlsx.name
    plot_annual_maps(annual, coords, map_png, theme, species_list)
    write_maps_table(campaign_level, annual, coords, map_xlsx)
    shutil.copy2(map_png, support_map_png)
    shutil.copy2(map_xlsx, support_map_xlsx)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": traditional.PROJECT_CODE,
        "species": species_list,
        "status": "generated",
        "metric": "CPUEn",
        "panel": panel_outputs,
        "annual_maps": {
            "figure": str(map_png),
            "table": str(map_xlsx),
            "support_figure": str(support_map_png),
            "support_table": str(support_map_xlsx),
        },
        "years": sorted(int(x) for x in annual["ano"].dropna().unique().tolist()),
        "points": int(coords["Ponto"].nunique()),
        "coordinate_strategy": "last_coordenada_valida_planilha",
        "coordinate_source": str(SOURCE),
        "hydrology_layer": str(HYDROLOGY_LAYER),
        "ada_layer": str(ADA_LAYER),
        "control_area_layers": {label: str(path) for label, path in CONTROL_AREA_LAYERS.items()},
        "map_rule": "CPUEn media anual por ponto e especie, incluindo zeros nas campanhas quantitativas amostradas sem registro.",
    }
    manifest = support_dir / f"manifesto_{manifest_slug}_ictiofauna.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def build(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, Any]:
    return build_custom(
        species_list=THREATENED_SPECIES,
        panel_prefix="10A",
        map_prefix="10B",
        product_slug="especies_ameacadas",
        manifest_slug="10AB_especies_ameacadas",
        output_dir=output_dir,
        support_dir=support_dir,
    )


def build_exotic(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, Any]:
    return build_custom(
        species_list=EXOTIC_SPECIES,
        panel_prefix="10C",
        map_prefix="10D",
        product_slug="especies_exoticas",
        manifest_slug="10CD_especies_exoticas",
        output_dir=output_dir,
        support_dir=support_dir,
    )


def main() -> int:
    summary = {"threatened": build(), "exotic": build_exotic()}
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
