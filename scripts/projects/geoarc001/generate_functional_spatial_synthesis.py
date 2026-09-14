from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_functional_spatial_mini_maps import (  # noqa: E402
    DEFAULT_ADA_LAYER,
    DEFAULT_COORD_REFERENCE,
    DEFAULT_GROUP_TABLE,
    DEFAULT_HYDROLOGY_LAYERS,
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE,
    POINT_LABEL_OFFSETS,
    _add_ada,
    _add_hydrology,
    _ada_polygons,
    _hydrology_segments,
    _normalize_sizes,
    _point_limits,
    _point_sort_key,
    _short_point,
    load_ada,
    load_coordinates,
    load_group_panel,
    load_hydrology,
    summarize_ada,
    summarize_hydrology,
)
from opyta_analysis.config import load_theme  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
SENTINEL_GROUPS = [
    "especialistas_loticos_sensiveis",
    "raspadores_bentonicos_reofilicos",
    "generalistas_tolerantes",
]
SENSITIVE_GROUPS = ["especialistas_loticos_sensiveis", "raspadores_bentonicos_reofilicos"]
GENERALIST_GROUP = "generalistas_tolerantes"

CATEGORY_COLORS = {
    "Refúgio funcional": "#2F7D4A",
    "Área de transição": "#D9A441",
    "Perfil funcional generalista": "#C46A3A",
    "Sem sinal funcional consistente": "#D5D9DE",
}
CATEGORY_ORDER = [
    "Refúgio funcional",
    "Área de transição",
    "Perfil funcional generalista",
    "Sem sinal funcional consistente",
]
TRAJECTORY_COLORS = {
    "Ganho funcional": "#2F7D4A",
    "Estabilidade funcional": "#5F7C8A",
    "Oscilação funcional": "#D9A441",
    "Enfraquecimento funcional": "#B65B5A",
    "Perfil funcional generalista": "#C46A3A",
    "Sem sinal funcional consistente": "#D5D9DE",
}
TRAJECTORY_ORDER = [
    "Ganho funcional",
    "Estabilidade funcional",
    "Oscilação funcional",
    "Enfraquecimento funcional",
    "Perfil funcional generalista",
    "Sem sinal funcional consistente",
]
BALANCE_LABEL_OFFSETS = {
    "IC-ARC-01": (8, -12),
    "IC-ARC-02": (-32, -12),
    "IC-ARC-04": (8, -15),
    "IC-ARC-07": (-42, 12),
    "IC-ARC-09": (12, -16),
    "IC-ARC-10": (-48, 0),
    "IC-ARC-12": (8, -12),
    "IC-ARC-14": (6, 10),
}


def _load_background(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if args.no_hydrology:
        hydrology_layers: list[Path] = []
    elif args.hydrology_layer:
        hydrology_layers = [Path(layer) for layer in args.hydrology_layer]
    else:
        hydrology_layers = DEFAULT_HYDROLOGY_LAYERS
    hydrology = load_hydrology(hydrology_layers)
    ada_layer = None if args.no_ada or not args.ada_layer else Path(args.ada_layer)
    ada = load_ada(ada_layer)
    return hydrology, ada, summarize_hydrology(hydrology), summarize_ada(ada)


def build_persistence(annual: pd.DataFrame) -> pd.DataFrame:
    data = annual[annual["grupo_funcional"].isin(SENTINEL_GROUPS)].copy()
    data["ocorreu_ano"] = data["campanhas_com_registro"] > 0
    persistence = (
        data.groupby(
            [
                "grupo_funcional",
                "grupo_rotulo",
                "ordem_grupo",
                "nome_ponto",
                "Longitude",
                "Latitude",
            ],
            as_index=False,
        )
        .agg(
            anos_monitorados=("ano", "nunique"),
            anos_com_registro=("ocorreu_ano", "sum"),
            campanhas_com_registro=("campanhas_com_registro", "sum"),
            CPUEn_soma_periodo=("CPUEn_grupo_soma", "sum"),
            CPUEn_medio_periodo=("CPUEn_grupo_medio", "mean"),
            perc_CPUEn_medio_periodo=("perc_CPUEn_medio", "mean"),
        )
        .sort_values(["ordem_grupo", "nome_ponto"], key=lambda s: s.map(_point_sort_key) if s.name == "nome_ponto" else s)
    )
    persistence["anos_com_registro"] = persistence["anos_com_registro"].astype(int)
    persistence["anos_monitorados"] = persistence["anos_monitorados"].astype(int)
    persistence["perc_anos_com_registro"] = np.where(
        persistence["anos_monitorados"] > 0,
        persistence["anos_com_registro"] / persistence["anos_monitorados"] * 100.0,
        0.0,
    )
    return persistence.reset_index(drop=True)


def build_balance(annual: pd.DataFrame, persistence: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = annual[annual["grupo_funcional"].isin(SENTINEL_GROUPS)].copy()
    base["ocorreu_ano"] = base["campanhas_com_registro"] > 0
    sensitive_years = (
        base[base["grupo_funcional"].isin(SENSITIVE_GROUPS)]
        .groupby(["nome_ponto", "ano"], as_index=False)["ocorreu_ano"]
        .max()
        .groupby("nome_ponto", as_index=False)["ocorreu_ano"]
        .sum()
        .rename(columns={"ocorreu_ano": "anos_funcoes_sensiveis"})
    )
    generalist_years = (
        base[base["grupo_funcional"] == GENERALIST_GROUP]
        .groupby("nome_ponto", as_index=False)["ocorreu_ano"]
        .sum()
        .rename(columns={"ocorreu_ano": "anos_generalistas"})
    )
    cpuen = (
        persistence.pivot_table(index="nome_ponto", columns="grupo_funcional", values="CPUEn_soma_periodo", aggfunc="sum", fill_value=0)
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for code in SENTINEL_GROUPS:
        if code not in cpuen.columns:
            cpuen[code] = 0.0
    coords = base.drop_duplicates("nome_ponto")[["nome_ponto", "Longitude", "Latitude"]].copy()
    balance = coords.merge(sensitive_years, on="nome_ponto", how="left").merge(generalist_years, on="nome_ponto", how="left").merge(cpuen, on="nome_ponto", how="left")
    for col in ["anos_funcoes_sensiveis", "anos_generalistas", *SENTINEL_GROUPS]:
        balance[col] = pd.to_numeric(balance[col], errors="coerce").fillna(0)
    balance["CPUEn_funcoes_sensiveis"] = balance[SENSITIVE_GROUPS].sum(axis=1)
    balance["CPUEn_generalistas"] = balance[GENERALIST_GROUP]
    balance["CPUEn_total_sentinelas"] = balance["CPUEn_funcoes_sensiveis"] + balance["CPUEn_generalistas"]
    balance["perc_CPUEn_generalistas"] = np.where(
        balance["CPUEn_total_sentinelas"] > 0,
        balance["CPUEn_generalistas"] / balance["CPUEn_total_sentinelas"] * 100.0,
        0.0,
    )
    balance["perc_CPUEn_funcoes_sensiveis"] = np.where(
        balance["CPUEn_total_sentinelas"] > 0,
        balance["CPUEn_funcoes_sensiveis"] / balance["CPUEn_total_sentinelas"] * 100.0,
        0.0,
    )
    balance["categoria_balanco"] = balance.apply(_classify_balance, axis=1)
    balance["cor_categoria"] = balance["categoria_balanco"].map(CATEGORY_COLORS)
    balance = balance.sort_values("nome_ponto", key=lambda s: s.map(_point_sort_key)).reset_index(drop=True)

    criteria = pd.DataFrame(
        [
            {
                "categoria": "Refúgio funcional",
                "criterio": "Funções sensíveis ocorreram em pelo menos 3 anos e representaram pelo menos 25% do CPUEn sentinela acumulado.",
            },
            {
                "categoria": "Perfil funcional generalista",
                "criterio": "Generalistas ocorreram em pelo menos 3 anos e funções sensíveis foram ausentes/raras ou generalistas ultrapassaram 75% do CPUEn sentinela acumulado.",
            },
            {
                "categoria": "Área de transição",
                "criterio": "Houve sinal funcional, mas sem predomínio claro de funções sensíveis ou generalistas pelos limiares exploratórios.",
            },
            {
                "categoria": "Sem sinal funcional consistente",
                "criterio": "Não houve CPUEn acumulado nos grupos sentinelas considerados.",
            },
        ]
    )
    return balance, criteria


def _classify_balance(row: pd.Series) -> str:
    if float(row["CPUEn_total_sentinelas"]) <= 0:
        return "Sem sinal funcional consistente"
    if int(row["anos_funcoes_sensiveis"]) >= 3 and float(row["perc_CPUEn_funcoes_sensiveis"]) >= 25.0:
        return "Refúgio funcional"
    if int(row["anos_generalistas"]) >= 3 and (
        int(row["anos_funcoes_sensiveis"]) <= 1 or float(row["perc_CPUEn_generalistas"]) >= 75.0
    ):
        return "Perfil funcional generalista"
    return "Área de transição"


def build_trajectory(annual: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = annual[annual["grupo_funcional"].isin(SENTINEL_GROUPS)].copy()
    yearly = (
        base.pivot_table(
            index=["nome_ponto", "Longitude", "Latitude", "ano"],
            columns="grupo_funcional",
            values="CPUEn_grupo_medio",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for code in SENTINEL_GROUPS:
        if code not in yearly.columns:
            yearly[code] = 0.0
    yearly["CPUEn_funcoes_sensiveis"] = yearly[SENSITIVE_GROUPS].sum(axis=1)
    yearly["CPUEn_generalistas"] = yearly[GENERALIST_GROUP]
    yearly["CPUEn_total_sentinelas"] = yearly["CPUEn_funcoes_sensiveis"] + yearly["CPUEn_generalistas"]
    yearly["perc_CPUEn_funcoes_sensiveis"] = np.where(
        yearly["CPUEn_total_sentinelas"] > 0,
        yearly["CPUEn_funcoes_sensiveis"] / yearly["CPUEn_total_sentinelas"] * 100.0,
        0.0,
    )
    yearly = yearly.sort_values(["nome_ponto", "ano"], key=lambda s: s.map(_point_sort_key) if s.name == "nome_ponto" else s)

    rows = []
    for point, data in yearly.groupby("nome_ponto", sort=False):
        data = data.sort_values("ano")
        years = data["ano"].to_numpy(dtype=float)
        sensitive = data["CPUEn_funcoes_sensiveis"].to_numpy(dtype=float)
        generalist = data["CPUEn_generalistas"].to_numpy(dtype=float)
        rows.append(_summarize_point_trajectory(point, data, years, sensitive, generalist))
    trajectory = pd.DataFrame(rows)
    trajectory["cor_trajetoria"] = trajectory["trajetoria_funcional"].map(TRAJECTORY_COLORS)
    trajectory = trajectory.sort_values("nome_ponto", key=lambda s: s.map(_point_sort_key)).reset_index(drop=True)

    criteria = pd.DataFrame(
        [
            {
                "trajetoria": "Ganho funcional",
                "criterio": "Funções sensíveis ausentes/baixas no início e presentes de forma persistente nos anos seguintes/recentes.",
            },
            {
                "trajetoria": "Estabilidade funcional",
                "criterio": "Funções sensíveis presentes em pelo menos 3 anos, com média recente ainda próxima do pico/histórico.",
            },
            {
                "trajetoria": "Oscilação funcional",
                "criterio": "Funções sensíveis aparecem e desaparecem sem direção clara, ou ocorrem em poucos anos alternados.",
            },
            {
                "trajetoria": "Enfraquecimento funcional",
                "criterio": "Funções sensíveis já ocorreram, mas a média recente caiu fortemente ou zerou em relação ao pico/histórico.",
            },
            {
                "trajetoria": "Perfil funcional generalista",
                "criterio": "Funções sensíveis ausentes e generalistas persistentes nos anos monitorados.",
            },
            {
                "trajetoria": "Sem sinal funcional consistente",
                "criterio": "CPUEn sentinela acumulado nulo ou residual, sem base suficiente para classificar trajetória.",
            },
        ]
    )
    return trajectory, yearly, criteria


def _summarize_point_trajectory(
    point: str,
    data: pd.DataFrame,
    years: np.ndarray,
    sensitive: np.ndarray,
    generalist: np.ndarray,
) -> dict[str, object]:
    positive = sensitive > 0
    generalist_positive = generalist > 0
    positive_years = int(positive.sum())
    generalist_years = int(generalist_positive.sum())
    total_sentinel = float(sensitive.sum() + generalist.sum())
    peak = float(sensitive.max()) if sensitive.size else 0.0
    first = float(sensitive[0]) if sensitive.size else 0.0
    last = float(sensitive[-1]) if sensitive.size else 0.0
    early_mean = float(sensitive[:2].mean()) if sensitive.size >= 2 else first
    recent_mean = float(sensitive[-2:].mean()) if sensitive.size >= 2 else last
    historical_mean = float(sensitive.mean()) if sensitive.size else 0.0
    transitions = int(np.abs(np.diff(positive.astype(int))).sum()) if positive.size > 1 else 0
    slope = float(np.polyfit(years - years.min(), sensitive, 1)[0]) if len(years) >= 2 else 0.0
    peak_year = int(data.loc[data["CPUEn_funcoes_sensiveis"].idxmax(), "ano"]) if peak > 0 else None
    trajectory, rationale = _classify_trajectory(
        positive_years=positive_years,
        generalist_years=generalist_years,
        total_sentinel=total_sentinel,
        first=first,
        last=last,
        early_mean=early_mean,
        recent_mean=recent_mean,
        historical_mean=historical_mean,
        peak=peak,
        transitions=transitions,
    )
    return {
        "nome_ponto": point,
        "Longitude": float(data["Longitude"].iloc[0]),
        "Latitude": float(data["Latitude"].iloc[0]),
        "trajetoria_funcional": trajectory,
        "justificativa": rationale,
        "anos_funcoes_sensiveis": positive_years,
        "anos_generalistas": generalist_years,
        "CPUEn_sensivel_inicio": first,
        "CPUEn_sensivel_final": last,
        "CPUEn_sensivel_media_inicial": early_mean,
        "CPUEn_sensivel_media_recente": recent_mean,
        "CPUEn_sensivel_media_historica": historical_mean,
        "CPUEn_sensivel_pico": peak,
        "ano_pico_sensivel": peak_year,
        "transicoes_presenca_sensivel": transitions,
        "slope_CPUEn_sensivel": slope,
        "CPUEn_generalistas_total": float(generalist.sum()),
        "CPUEn_sentinel_total": total_sentinel,
    }


def _classify_trajectory(
    *,
    positive_years: int,
    generalist_years: int,
    total_sentinel: float,
    first: float,
    last: float,
    early_mean: float,
    recent_mean: float,
    historical_mean: float,
    peak: float,
    transitions: int,
) -> tuple[str, str]:
    if total_sentinel < 1.0:
        return "Sem sinal funcional consistente", "CPUEn sentinela acumulado residual (<1)."
    if peak <= 0:
        if generalist_years >= 3:
            return "Perfil funcional generalista", "Funções sensíveis ausentes e generalistas recorrentes."
        return "Sem sinal funcional consistente", "Sem funções sensíveis e sem recorrência suficiente de generalistas."
    if early_mean > 0 and recent_mean <= max(0.25 * max(early_mean, peak), 0.01):
        return "Enfraquecimento funcional", "Funções sensíveis registradas no início/histórico e ausentes ou muito reduzidas no período recente."
    if positive_years >= 3 and first <= 0 and recent_mean >= 0.35 * peak and last > 0:
        return "Ganho funcional", "Funções sensíveis ausentes no início e persistentes no período posterior/recente."
    if positive_years >= 3 and recent_mean <= 0.40 * peak:
        return "Enfraquecimento funcional", "Média recente das funções sensíveis inferior a 40% do pico histórico."
    if transitions >= 3 or positive_years <= 2:
        return "Oscilação funcional", "Presença intermitente de funções sensíveis, sem direção temporal robusta."
    if positive_years >= 3 and recent_mean >= 0.50 * peak:
        return "Estabilidade funcional", "Funções sensíveis recorrentes e ainda próximas do pico/histórico recente."
    if recent_mean > historical_mean * 1.2:
        return "Ganho funcional", "Média recente superior ao histórico das funções sensíveis."
    return "Oscilação funcional", "Sinal funcional presente, mas sem direção inequívoca."


def _setup_spatial_layers(coords: pd.DataFrame, hydrology: pd.DataFrame, ada: pd.DataFrame) -> tuple[tuple[float, float, float, float], dict[str, list[np.ndarray]], list[np.ndarray]]:
    xmin, xmax, ymin, ymax = _point_limits(coords.rename(columns={"nome_ponto": "Ponto"}))
    hydrology_segments = _hydrology_segments(hydrology, xmin, xmax, ymin, ymax)
    ada_polygons = _ada_polygons(ada, xmin, xmax, ymin, ymax)
    return (xmin, xmax, ymin, ymax), hydrology_segments, ada_polygons


def _draw_base(ax, coords: pd.DataFrame, limits: tuple[float, float, float, float], hydrology_segments: dict[str, list[np.ndarray]], ada_polygons: list[np.ndarray]) -> None:
    xmin, xmax, ymin, ymax = limits
    _add_ada(ax, ada_polygons)
    _add_hydrology(ax, hydrology_segments)
    ax.scatter(
        coords["Longitude"],
        coords["Latitude"],
        s=10,
        color="#E4E8EE",
        edgecolor="#AAB2BD",
        linewidth=0.35,
        zorder=1.4,
    )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, color="#E6E6E6", linewidth=0.45)
    ax.tick_params(axis="both", labelsize=7)


def _annotate_points(
    ax,
    coords: pd.DataFrame,
    *,
    fontsize: float = 6.4,
    offsets: dict[str, tuple[int, int]] | None = None,
    leader: bool = False,
) -> None:
    label_offsets = offsets or POINT_LABEL_OFFSETS
    for _, point in coords.iterrows():
        dx, dy = label_offsets.get(point["nome_ponto"], POINT_LABEL_OFFSETS.get(point["nome_ponto"], (4, 4)))
        ax.annotate(
            _short_point(point["nome_ponto"]),
            (point["Longitude"], point["Latitude"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=fontsize,
            color="#202020",
            ha="left" if dx >= 0 else "right",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=0.45),
            arrowprops=dict(arrowstyle="-", color="#7A7A7A", linewidth=0.35, shrinkA=0, shrinkB=2) if leader else None,
            zorder=5,
        )


def plot_persistence(
    persistence: pd.DataFrame,
    coords: pd.DataFrame,
    hydrology: pd.DataFrame,
    ada: pd.DataFrame,
    out_png: Path,
    theme: dict,
) -> None:
    groups = (
        persistence[["ordem_grupo", "grupo_funcional", "grupo_rotulo"]]
        .drop_duplicates()
        .sort_values("ordem_grupo")
        .to_dict("records")
    )
    max_years = int(max(persistence["anos_monitorados"].max(), 1))
    limits, hydrology_segments, ada_polygons = _setup_spatial_layers(coords, hydrology, ada)
    cmap = mcolors.LinearSegmentedColormap.from_list("permanencia_funcional", ["#F3F5F1", "#BFDDB8", "#6DAE6B", "#2F7D4A"])
    norm = mcolors.Normalize(vmin=0, vmax=max_years)
    fig, axes = plt.subplots(1, len(groups), figsize=(15.4, 4.7), dpi=int(theme.get("dpi", 600)), sharex=True, sharey=True)
    if len(groups) == 1:
        axes = np.array([axes])

    for ax, group in zip(axes, groups):
        data = persistence[persistence["grupo_funcional"] == group["grupo_funcional"]].copy()
        _draw_base(ax, coords, limits, hydrology_segments, ada_polygons)
        sizes = _normalize_sizes(data["anos_com_registro"], 55, 430)
        ax.scatter(
            data["Longitude"],
            data["Latitude"],
            s=sizes,
            c=data["anos_com_registro"],
            cmap=cmap,
            norm=norm,
            edgecolor="#1C1C1C",
            linewidth=0.45,
            alpha=0.94,
            zorder=3,
        )
        for _, row in data.iterrows():
            value = int(row["anos_com_registro"])
            if value > 0:
                ax.text(
                    row["Longitude"],
                    row["Latitude"],
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    fontweight="bold",
                    color="#202020",
                    zorder=4,
                )
        _annotate_points(ax, coords)
        ax.set_title(group["grupo_rotulo"], fontsize=10.2, fontweight="bold")
        ax.set_xlabel("Longitude", fontsize=8)
    axes[0].set_ylabel("Latitude", fontsize=8)

    cax = fig.add_axes([0.92, 0.20, 0.018, 0.62])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, cax=cax, ticks=range(max_years + 1))
    cbar.set_label("Anos com ocorrência", fontsize=9.2)
    fig.suptitle("Mapa de permanência dos grupos funcionais sentinelas", x=0.02, y=0.995, ha="left", fontsize=14.5, fontweight="bold")
    fig.text(
        0.02,
        0.035,
        "Número na bolha = anos com registro do grupo funcional no ponto; tamanho e cor aumentam com a permanência. Produto exploratório.",
        ha="left",
        fontsize=8.5,
        color="#404040",
    )
    fig.subplots_adjust(left=0.07, right=0.89, top=0.84, bottom=0.16, wspace=0.12)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def plot_balance(
    balance: pd.DataFrame,
    coords: pd.DataFrame,
    hydrology: pd.DataFrame,
    ada: pd.DataFrame,
    out_png: Path,
    theme: dict,
) -> None:
    limits, hydrology_segments, ada_polygons = _setup_spatial_layers(coords, hydrology, ada)
    fig, ax = plt.subplots(figsize=(8.2, 6.2), dpi=int(theme.get("dpi", 600)))
    _draw_base(ax, coords, limits, hydrology_segments, ada_polygons)
    sizes = _normalize_sizes(balance["CPUEn_total_sentinelas"], 150, 560)
    for category in CATEGORY_ORDER:
        data = balance[balance["categoria_balanco"] == category]
        if data.empty:
            continue
        ax.scatter(
            data["Longitude"],
            data["Latitude"],
            s=sizes[data.index],
            color=CATEGORY_COLORS[category],
            edgecolor="#1C1C1C",
            linewidth=0.65,
            alpha=0.92,
            zorder=3,
            label=category,
        )
    _annotate_points(ax, coords, fontsize=7, offsets=BALANCE_LABEL_OFFSETS, leader=True)
    ax.set_title("Mapa de balanço funcional", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=CATEGORY_COLORS[category],
            markeredgecolor="#1C1C1C",
            markersize=8,
            label=category,
        )
        for category in CATEGORY_ORDER
        if category in set(balance["categoria_balanco"])
    ]
    ax.legend(
        handles=legend_handles,
        title="Classificação exploratória",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        fontsize=8.2,
        title_fontsize=8.6,
        frameon=True,
    )
    fig.text(
        0.02,
        0.025,
        "Classificação baseada em permanência anual e participação acumulada de CPUEn dos grupos sentinelas; tamanho da bolha = CPUEn sentinela acumulado.",
        ha="left",
        fontsize=8.3,
        color="#404040",
    )
    fig.subplots_adjust(left=0.10, right=0.74, top=0.90, bottom=0.12)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def plot_trajectory(
    trajectory: pd.DataFrame,
    coords: pd.DataFrame,
    hydrology: pd.DataFrame,
    ada: pd.DataFrame,
    out_png: Path,
    theme: dict,
) -> None:
    limits, hydrology_segments, ada_polygons = _setup_spatial_layers(coords, hydrology, ada)
    fig, ax = plt.subplots(figsize=(8.2, 6.2), dpi=int(theme.get("dpi", 600)))
    _draw_base(ax, coords, limits, hydrology_segments, ada_polygons)
    sizes = _normalize_sizes(trajectory["CPUEn_sentinel_total"], 150, 560)
    for category in TRAJECTORY_ORDER:
        data = trajectory[trajectory["trajetoria_funcional"] == category]
        if data.empty:
            continue
        ax.scatter(
            data["Longitude"],
            data["Latitude"],
            s=sizes[data.index],
            color=TRAJECTORY_COLORS[category],
            edgecolor="#1C1C1C",
            linewidth=0.65,
            alpha=0.92,
            zorder=3,
            label=category,
        )
    _annotate_points(ax, coords, fontsize=7, offsets=BALANCE_LABEL_OFFSETS, leader=True)
    ax.set_title("Mapa de trajetória funcional", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=TRAJECTORY_COLORS[category],
            markeredgecolor="#1C1C1C",
            markersize=8,
            label=category,
        )
        for category in TRAJECTORY_ORDER
        if category in set(trajectory["trajetoria_funcional"])
    ]
    ax.legend(
        handles=legend_handles,
        title="Tendência exploratória",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        fontsize=8.0,
        title_fontsize=8.4,
        frameon=True,
    )
    fig.text(
        0.02,
        0.025,
        "Classificação baseada na série anual de CPUEn das funções sensíveis; tamanho da bolha = CPUEn sentinela acumulado. 2026 é parcial.",
        ha="left",
        fontsize=8.3,
        color="#404040",
    )
    fig.subplots_adjust(left=0.10, right=0.74, top=0.90, bottom=0.12)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    output_dir: Path,
    data_prefix: str,
    persistence: pd.DataFrame,
    balance: pd.DataFrame,
    criteria: pd.DataFrame,
    trajectory: pd.DataFrame,
    trajectory_yearly: pd.DataFrame,
    trajectory_criteria: pd.DataFrame,
    annual: pd.DataFrame,
    coords: pd.DataFrame,
    hydrology_summary: pd.DataFrame,
    ada_summary: pd.DataFrame,
    summary: dict,
) -> dict[str, str]:
    xlsx = output_dir / f"{data_prefix}_df_sintese_espacial_funcional_ictiofauna.xlsx"
    manifest = output_dir / f"{data_prefix}_manifesto_sintese_espacial_funcional_ictiofauna.json"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        persistence.to_excel(writer, sheet_name="permanencia_funcional", index=False)
        balance.to_excel(writer, sheet_name="balanco_funcional", index=False)
        criteria.to_excel(writer, sheet_name="criterios_balanco", index=False)
        trajectory.to_excel(writer, sheet_name="trajetoria_funcional", index=False)
        trajectory_yearly.to_excel(writer, sheet_name="serie_trajetoria_anual", index=False)
        trajectory_criteria.to_excel(writer, sheet_name="criterios_trajetoria", index=False)
        annual.to_excel(writer, sheet_name="base_anual", index=False)
        coords.to_excel(writer, sheet_name="coordenadas_pontos", index=False)
        hydrology_summary.to_excel(writer, sheet_name="malha_hidrica_resumo", index=False)
        ada_summary.to_excel(writer, sheet_name="ada_resumo", index=False)
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"xlsx": str(xlsx), "manifest": str(manifest)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera mapas de sintese espacial funcional do GEOARC001.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Planilha de migracao com coordenadas.")
    parser.add_argument("--group-table", default=str(DEFAULT_GROUP_TABLE), help="Planilha do produto 23.")
    parser.add_argument("--coordinate-reference", default=str(DEFAULT_COORD_REFERENCE), help="KMZ/KML com coordenadas oficiais dos pontos.")
    parser.add_argument(
        "--workbook-coordinate-strategy",
        choices=["first", "last"],
        default="first",
        help="Quando --coordinate-reference estiver vazio, escolhe primeira ou ultima coordenada valida por ponto na planilha.",
    )
    parser.add_argument("--hydrology-layer", action="append", default=None, help="Camada KML/KMZ de drenagem/talvegue. Pode ser usada mais de uma vez.")
    parser.add_argument("--no-hydrology", action="store_true", help="Nao desenha malha hidrica nos mapas.")
    parser.add_argument("--ada-layer", default=str(DEFAULT_ADA_LAYER), help="Camada KML/KMZ da ADA.")
    parser.add_argument("--no-ada", action="store_true", help="Nao desenha a ADA nos mapas.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Pasta de saida exploratoria.")
    parser.add_argument("--permanence-prefix", default="34", help="Prefixo da figura de permanencia.")
    parser.add_argument("--balance-prefix", default="35", help="Prefixo da figura de balanco.")
    parser.add_argument("--trajectory-prefix", default="36", help="Prefixo da figura de trajetoria.")
    parser.add_argument("--data-prefix", default="34_36", help="Prefixo da planilha/manifesto de apoio.")
    parser.add_argument("--data-only", action="store_true", help="Atualiza apenas planilha e manifesto, sem reescrever as figuras.")
    parser.add_argument("--client", default="default", help="Tema visual.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    group_table = Path(args.group_table)
    coordinate_reference = Path(args.coordinate_reference) if args.coordinate_reference else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", args.client)

    coords_raw, close_pairs, coord_variation = load_coordinates(source, coordinate_reference, args.workbook_coordinate_strategy)
    annual, definitions = load_group_panel(group_table, coords_raw, {"predadores"})
    coords = coords_raw.rename(columns={"Ponto": "nome_ponto"})[["nome_ponto", "Longitude", "Latitude"]].copy()
    hydrology, ada, hydrology_summary, ada_summary = _load_background(args)
    persistence = build_persistence(annual)
    balance, criteria = build_balance(annual, persistence)
    trajectory, trajectory_yearly, trajectory_criteria = build_trajectory(annual)

    permanence_png = output_dir / f"{args.permanence_prefix}_grafico_mapa_permanencia_funcional_ictiofauna.png"
    balance_png = output_dir / f"{args.balance_prefix}_grafico_mapa_balanco_funcional_ictiofauna.png"
    trajectory_png = output_dir / f"{args.trajectory_prefix}_grafico_mapa_trajetoria_funcional_ictiofauna.png"
    if not args.data_only:
        plot_persistence(persistence, coords, hydrology, ada, permanence_png, theme)
        plot_balance(balance, coords, hydrology, ada, balance_png, theme)
        plot_trajectory(trajectory, coords, hydrology, ada, trajectory_png, theme)

    summary = {
        "source": str(source),
        "group_table": str(group_table),
        "output_dir": str(output_dir),
        "permanence_figure": str(permanence_png),
        "balance_figure": str(balance_png),
        "trajectory_figure": str(trajectory_png),
        "data_prefix": str(args.data_prefix),
        "coordinate_reference": str(coordinate_reference) if coordinate_reference else None,
        "coordinate_strategy": "referencia_kmz" if coordinate_reference else f"{args.workbook_coordinate_strategy}_coordenada_valida_planilha",
        "data_only": bool(args.data_only),
        "groups_considered": definitions[definitions["codigo"].isin(SENTINEL_GROUPS)][["codigo", "rotulo", "criterio"]].to_dict("records"),
        "groups_excluded": ["predadores"],
        "points": int(coords["nome_ponto"].nunique()),
        "years": sorted(int(year) for year in annual["ano"].dropna().unique().tolist()),
        "hydrology_features": int(hydrology[["fonte", "feature_id"]].drop_duplicates().shape[0]) if not hydrology.empty else 0,
        "hydrology_vertices": int(len(hydrology)),
        "ada_polygons": int(ada["polygon_id"].nunique()) if not ada.empty else 0,
        "ada_vertices": int(len(ada)),
        "balance_categories": balance["categoria_balanco"].value_counts().to_dict(),
        "trajectory_categories": trajectory["trajetoria_funcional"].value_counts().to_dict(),
        "close_pairs_under_1km": close_pairs[close_pairs["distancia_km"] < 1.0].to_dict("records"),
        "coordinate_variation_rows": int(len(coord_variation)),
        "note": "Produto exploratorio; classificacao funcional e heuristica e deve ser interpretada junto das series temporais e composicao taxonomica.",
    }
    outputs = write_outputs(
        output_dir,
        str(args.data_prefix),
        persistence,
        balance,
        criteria,
        trajectory,
        trajectory_yearly,
        trajectory_criteria,
        annual,
        coords_raw,
        hydrology_summary,
        ada_summary,
        summary,
    )
    summary["outputs"] = outputs
    (output_dir / f"{args.data_prefix}_manifesto_sintese_espacial_funcional_ictiofauna.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
