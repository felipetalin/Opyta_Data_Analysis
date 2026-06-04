from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge

try:
    import contextily as cx
except Exception:  # pragma: no cover - optional map background
    cx = None


DATE_TAG = "20260603"
RESULTADOS_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados"
)
BASE_FILE = RESULTADOS_DIR / "base_analitica_ictiofauna_porto_estrela_20260602.xlsx"
MIGRATION_FILE = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Porto Estrela/Planilha/Migra"
    "\u00e7\u00e3o/Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA_260602.xlsx"
)
OUTPUT_DIR = (
    RESULTADOS_DIR
    / "resultados_ictiofauna_porto_estrela_20260602"
    / f"testes_analises_exploratorias_espaciais_bolhas_colar_{DATE_TAG}"
)

POINT_ORDER = ["P4", "P5", "P2", "P1", "P3", "P6", "P7", "P8", "P9"]
POINT_TO_TRECHO = {
    "P4": "Montante",
    "P5": "Montante",
    "P2": "Montante",
    "P1": "Montante",
    "P3": "Jusante",
    "P6": "Jusante",
    "P7": "Jusante",
    "P8": "Jusante",
    "P9": "Jusante",
}
COORDINATE_OVERRIDES = {
    # Coordenada corrigida no Supabase em 2026-06-03.
    "P1": (-19.108602, -42.662967),
}

PRIMARY = "#002060"
SECONDARY = "#5B9BD5"
ORANGE = "#D4672A"
GREEN = "#6BA547"
PURPLE = "#7B4EA3"
RED = "#B75D69"
GREY = "#6C757D"
GRID = "#D9D9D9"
RECENT = "#F2C94C"

TRECHO_COLORS = {"Montante": PRIMARY, "Jusante": ORANGE}
GROUP_COLORS = {
    "Migradora nativa": PRIMARY,
    "Migradora não nativa": SECONDARY,
    "Não migradora nativa": GREEN,
    "Não migradora não nativa": ORANGE,
    "Ameaçada": RED,
}

FONT_BASE = 16
FONT_AXIS = 16
FONT_TICK = 11
FONT_LEGEND = 13
WEB_MERCATOR_RADIUS = 6378137.0


def _configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": FONT_BASE,
            "axes.labelsize": FONT_AXIS,
            "xtick.labelsize": FONT_TICK,
            "ytick.labelsize": FONT_TICK,
            "legend.fontsize": FONT_LEGEND,
            "axes.edgecolor": "black",
            "axes.linewidth": 1.1,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _style_axis(ax: plt.Axes, both: bool = False) -> None:
    ax.grid(axis="both" if both else "y", color=GRID, alpha=0.35, linewidth=1.0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.0)


def _fix_label(value: object) -> str:
    text = str(value)
    return text.replace("N?o", "Nao").replace("Não", "Nao").replace("nao", "nao")


def _display_label(value: object) -> str:
    text = str(value)
    return text.replace("N?o", "Não").replace("NÃ£o", "Não").replace("Nao", "Não")


def _ah_order(base: pd.DataFrame) -> pd.DataFrame:
    return (
        base[["ano_hidrologico", "ano_hidrologico_rotulo", "campanha_ordem"]]
        .dropna(subset=["ano_hidrologico"])
        .groupby(["ano_hidrologico", "ano_hidrologico_rotulo"], as_index=False)["campanha_ordem"]
        .min()
        .sort_values("campanha_ordem")
        .assign(Ordem_AH=lambda d: np.arange(1, len(d) + 1))
    )


def _load_coordinates() -> pd.DataFrame:
    coords = pd.read_excel(MIGRATION_FILE, sheet_name="Pontos_e_Campanhas")
    coords = coords[["Ponto", "Latitude", "Longitude"]].dropna().drop_duplicates("Ponto")
    coords["Ponto"] = coords["Ponto"].astype(str).str.strip()
    coords["Latitude"] = pd.to_numeric(coords["Latitude"], errors="coerce")
    coords["Longitude"] = pd.to_numeric(coords["Longitude"], errors="coerce")
    for point, (lat, lon) in COORDINATE_OVERRIDES.items():
        mask = coords["Ponto"].eq(point)
        coords.loc[mask, "Latitude"] = lat
        coords.loc[mask, "Longitude"] = lon
    coords["Trecho"] = coords["Ponto"].map(POINT_TO_TRECHO)
    coords["Ordem_Espacial"] = coords["Ponto"].map({p: i + 1 for i, p in enumerate(POINT_ORDER)})
    return coords.sort_values("Ordem_Espacial")


def _group_label(migration: object, origin: object) -> str:
    mig = _fix_label(migration).strip().lower()
    ori = _fix_label(origin).strip().lower()
    mig_label = "Migradora" if mig == "migradora" else "Não migradora"
    ori_label = "nativa" if ori == "nativa" else "não nativa"
    return f"{mig_label} {ori_label}"


def _normalize_sizes(values: pd.Series, min_size: float = 90, max_size: float = 1450) -> np.ndarray:
    arr = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(dtype=float)
    vmax = float(np.nanmax(arr)) if len(arr) else 0.0
    if vmax <= 0:
        return np.repeat(min_size, len(arr))
    return min_size + (arr / vmax) * (max_size - min_size)


def _xy_columns(df: pd.DataFrame) -> tuple[str, str]:
    if {"Plot_X", "Plot_Y"}.issubset(df.columns):
        return "Plot_X", "Plot_Y"
    return "Longitude", "Latitude"


def _lonlat_to_webmercator(lon: pd.Series, lat: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    lon_arr = pd.to_numeric(lon, errors="coerce").to_numpy(dtype=float)
    lat_arr = pd.to_numeric(lat, errors="coerce").clip(-85.05112878, 85.05112878).to_numpy(dtype=float)
    x = WEB_MERCATOR_RADIUS * np.deg2rad(lon_arr)
    y = WEB_MERCATOR_RADIUS * np.log(np.tan(np.pi / 4 + np.deg2rad(lat_arr) / 2))
    return x, y


def _with_plot_coordinates(df: pd.DataFrame, satellite: bool = False) -> pd.DataFrame:
    out = df.copy()
    if satellite:
        out["Plot_X"], out["Plot_Y"] = _lonlat_to_webmercator(out["Longitude"], out["Latitude"])
    else:
        out["Plot_X"] = out["Longitude"]
        out["Plot_Y"] = out["Latitude"]
    return out


def _prepare_tables(base: pd.DataFrame, coords: pd.DataFrame) -> dict[str, pd.DataFrame]:
    ah = _ah_order(base)
    point_meta = coords[["Ponto", "Trecho", "Ordem_Espacial", "Latitude", "Longitude"]].copy()

    real = base.loc[(base["Numero_de_Individuos"].fillna(0) > 0) & base["Nome_Cientifico"].notna()].copy()
    quanti = base.loc[
        base["Tipo_Amostragem_Base"].astype(str).str.contains("Quanti", case=False, na=False)
        & base["Nome_Cientifico"].notna()
    ].copy()
    quanti["Grupo_Migracao_Origem"] = [
        _group_label(m, o) for m, o in zip(quanti["Migradora_Nao_Migradora"], quanti["Nativa_Nao_Nativa"])
    ]
    quanti["Grupo_Ameaca"] = np.where(
        quanti["Ameacada_Extincao"].astype(str).str.lower().str.startswith("sim"),
        "Ameaçada",
        "Não ameaçada",
    )

    point_total = (
        quanti.groupby("Ponto", as_index=False)
        .agg(
            CPUEn=("CPUEn_linha", "sum"),
            CPUEb=("CPUEb_linha", "sum"),
            Abundancia=("Numero_de_Individuos", "sum"),
            Biomassa_g=("Biomassa_g_linha", "sum"),
        )
        .merge(real.groupby("Ponto")["Nome_Cientifico"].nunique().rename("Riqueza_Total"), on="Ponto", how="left")
        .merge(point_meta, on="Ponto", how="right")
        .fillna({"CPUEn": 0, "CPUEb": 0, "Abundancia": 0, "Biomassa_g": 0, "Riqueza_Total": 0})
        .sort_values("Ordem_Espacial")
    )

    point_ah = (
        quanti.groupby(["Ponto", "ano_hidrologico"], as_index=False)
        .agg(
            CPUEn=("CPUEn_linha", "sum"),
            CPUEb=("CPUEb_linha", "sum"),
            Abundancia=("Numero_de_Individuos", "sum"),
            Biomassa_g=("Biomassa_g_linha", "sum"),
            Riqueza_Quanti=("Nome_Cientifico", "nunique"),
        )
        .merge(ah, on="ano_hidrologico", how="left")
        .merge(point_meta, on="Ponto", how="right")
        .sort_values(["Ordem_AH", "Ordem_Espacial"])
    )
    point_ah[["CPUEn", "CPUEb", "Abundancia", "Biomassa_g", "Riqueza_Quanti"]] = point_ah[
        ["CPUEn", "CPUEb", "Abundancia", "Biomassa_g", "Riqueza_Quanti"]
    ].fillna(0)

    real_ah_richness = (
        real.groupby(["Ponto", "ano_hidrologico"])["Nome_Cientifico"]
        .nunique()
        .rename("Riqueza_Total")
        .reset_index()
    )
    point_ah = point_ah.merge(real_ah_richness, on=["Ponto", "ano_hidrologico"], how="left")
    point_ah["Riqueza_Total"] = point_ah["Riqueza_Total"].fillna(0)

    group_point = (
        quanti.groupby(["Ponto", "Grupo_Migracao_Origem"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"), Abundancia=("Numero_de_Individuos", "sum"))
        .merge(point_meta, on="Ponto", how="left")
        .sort_values(["Grupo_Migracao_Origem", "Ordem_Espacial"])
    )

    threat_point = (
        quanti.groupby(["Ponto", "Grupo_Ameaca"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"), Abundancia=("Numero_de_Individuos", "sum"))
        .merge(point_meta, on="Ponto", how="left")
        .sort_values(["Grupo_Ameaca", "Ordem_Espacial"])
    )

    species_point = (
        quanti.groupby(["Ponto", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"), Abundancia=("Numero_de_Individuos", "sum"))
        .merge(point_meta, on="Ponto", how="left")
    )
    top_species = (
        species_point.groupby("Nome_Cientifico")["CPUEn"]
        .sum()
        .sort_values(ascending=False)
        .head(22)
        .index.tolist()
    )
    species_point_top = species_point.loc[species_point["Nome_Cientifico"].isin(top_species)].copy()
    species_point_top["Ordem_Especie"] = species_point_top["Nome_Cientifico"].map({s: i for i, s in enumerate(top_species)})

    recent_ah = ["AH2324", "AH2425", "AH2526"]
    recent_point_ah = point_ah.loc[point_ah["ano_hidrologico"].isin(recent_ah)].copy()

    return {
        "Coordenadas_Pontos": point_meta,
        "Espacial_Ponto_Total": point_total,
        "Espacial_Ponto_AH": point_ah,
        "Grupos_Ponto": group_point,
        "Ameaca_Ponto": threat_point,
        "Top_Especies_Ponto": species_point_top,
        "Recente_Ponto_AH": recent_point_ah,
    }


def _point_limits(df: pd.DataFrame) -> tuple[float, float, float, float]:
    x_col, y_col = _xy_columns(df)
    xmin, xmax = df[x_col].min(), df[x_col].max()
    ymin, ymax = df[y_col].min(), df[y_col].max()
    dx = xmax - xmin
    dy = ymax - ymin
    return xmin - dx * 0.12, xmax + dx * 0.12, ymin - dy * 0.18, ymax + dy * 0.18


def _draw_point_path(ax: plt.Axes, coords: pd.DataFrame, highlight_transition: bool = False) -> None:
    ordered = coords.sort_values("Ordem_Espacial")
    x_col, y_col = _xy_columns(ordered)
    offsets = {
        "P1": (28, 18),
        "P2": (-24, 19),
        "P3": (-38, -15),
        "P4": (-27, -11),
        "P5": (24, 18),
        "P6": (34, -20),
        "P7": (25, 14),
        "P8": (25, -18),
        "P9": (24, 20),
    }
    arrowprops = (
        dict(arrowstyle="-", color="#555555", lw=0.75, alpha=0.72, shrinkA=0, shrinkB=3)
        if highlight_transition
        else None
    )
    if highlight_transition:
        montante = ordered.loc[ordered["Trecho"].eq("Montante")]
        jusante = ordered.loc[ordered["Trecho"].eq("Jusante")]
        ax.plot(
            montante[x_col],
            montante[y_col],
            color=PRIMARY,
            linewidth=2.4,
            linestyle="-",
            alpha=0.62,
            zorder=1,
        )
        ax.plot(
            jusante[x_col],
            jusante[y_col],
            color=ORANGE,
            linewidth=2.4,
            linestyle="-",
            alpha=0.62,
            zorder=1,
        )
    else:
        ax.plot(
            ordered[x_col],
            ordered[y_col],
            color="#9AA7B4",
            linewidth=2.2,
            linestyle="-",
            alpha=0.65,
            zorder=1,
        )
    for _, row in ordered.iterrows():
        dx, dy = offsets.get(row["Ponto"], (6, 5))
        ax.annotate(
            row["Ponto"],
            (row[x_col], row[y_col]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=10.5,
            weight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.16", facecolor="white", alpha=0.78, edgecolor="none"),
            arrowprops=arrowprops,
            zorder=7,
        )


def _draw_montante_jusante_separator(ax: plt.Axes, coords: pd.DataFrame) -> None:
    ordered = coords.sort_values("Ordem_Espacial")
    p1 = ordered.loc[ordered["Ponto"].eq("P1")].iloc[0]
    p3 = ordered.loc[ordered["Ponto"].eq("P3")].iloc[0]
    mid_lon = float((p1["Longitude"] + p3["Longitude"]) / 2)
    mid_lat = float((p1["Latitude"] + p3["Latitude"]) / 2)
    dx = float(p3["Longitude"] - p1["Longitude"])
    dy = float(p3["Latitude"] - p1["Latitude"])
    norm = math.hypot(dx, dy) or 1.0
    perp_x = -dy / norm
    perp_y = dx / norm
    length = max(
        float(coords["Longitude"].max() - coords["Longitude"].min()),
        float(coords["Latitude"].max() - coords["Latitude"].min()),
    ) * 0.10
    ax.plot(
        [mid_lon - perp_x * length / 2, mid_lon + perp_x * length / 2],
        [mid_lat - perp_y * length / 2, mid_lat + perp_y * length / 2],
        color="#404040",
        linewidth=2.8,
        linestyle=(0, (4, 3)),
        alpha=0.98,
        zorder=6,
    )


def _add_satellite_background(ax: plt.Axes, coords: pd.DataFrame) -> bool:
    if cx is None:
        return False
    xmin, xmax, ymin, ymax = _point_limits(coords)
    try:
        img, extent = cx.bounds2img(
            xmin,
            ymin,
            xmax,
            ymax,
            zoom=10,
            source=cx.providers.Esri.WorldImagery,
            ll=False,
        )
    except Exception:
        return False
    ax.imshow(img, extent=extent, interpolation="bilinear", zorder=0)
    return True


def _plot_bubble_map(point_total: pd.DataFrame, metric: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 8.8))
    data = point_total.sort_values("Ordem_Espacial")
    sizes = _normalize_sizes(data[metric], 120, 1900)
    vmax = max(float(data[metric].max()), 1.0)
    edgecolors = [TRECHO_COLORS.get(t, "black") for t in data["Trecho"]]
    scatter = ax.scatter(
        data["Longitude"],
        data["Latitude"],
        s=sizes,
        c=data[metric],
        cmap="viridis",
        norm=Normalize(vmin=0, vmax=vmax),
        alpha=0.86,
        edgecolor=edgecolors,
        linewidth=2.2,
        zorder=3,
    )
    _draw_point_path(ax, data)
    xmin, xmax, ymin, ymax = _point_limits(data)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Distribuição espacial acumulada - {metric}", pad=16)
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.84, pad=0.02)
    cbar.set_label(metric)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=color, markeredgewidth=2.2, markersize=11, label=f"Borda {trecho}")
        for trecho, color in TRECHO_COLORS.items()
    ]
    ax.legend(handles=handles, loc="lower left", frameon=True, facecolor="white", framealpha=0.88)
    _style_axis(ax, both=True)
    _save_fig(fig, path)


def _plot_pie_map(
    group_point: pd.DataFrame,
    point_total: pd.DataFrame,
    path: Path,
    report_test: bool = False,
    satellite: bool = False,
) -> None:
    fig_height = 5.9 if satellite else 5.7 if report_test else 8.8
    fig, ax = plt.subplots(figsize=(12.5, fig_height))
    coords = _with_plot_coordinates(point_total.sort_values("Ordem_Espacial"), satellite=satellite)
    x_col, y_col = _xy_columns(coords)
    has_satellite = _add_satellite_background(ax, coords) if satellite else False
    _draw_point_path(ax, coords, highlight_transition=report_test)
    group_order = ["Migradora nativa", "Migradora não nativa", "Não migradora nativa", "Não migradora não nativa"]
    vmax = max(float(point_total["CPUEn"].max()), 1.0)
    x_span = coords[x_col].max() - coords[x_col].min()
    y_span = coords[y_col].max() - coords[y_col].min()
    base_radius = min(x_span, y_span) * (0.035 if report_test else 0.045)

    for _, point in coords.iterrows():
        subset = group_point.loc[group_point["Ponto"] == point["Ponto"]].set_index("Grupo_Migracao_Origem")
        values = np.array([subset["CPUEn"].get(g, 0.0) for g in group_order], dtype=float)
        total = values.sum()
        if total > 0:
            radius = base_radius * (0.50 + (1.50 if report_test else 1.85) * math.sqrt(total / vmax))
        else:
            radius = base_radius * 0.45
        start = 90.0
        if total <= 0:
            wedge = Wedge((point[x_col], point[y_col]), radius, 0, 360, facecolor="#E5E9F0", edgecolor="black", linewidth=0.9)
            ax.add_patch(wedge)
            continue
        for group, value in zip(group_order, values):
            if value <= 0:
                continue
            angle = 360.0 * value / total
            wedge = Wedge(
                (point[x_col], point[y_col]),
                radius,
                start,
                start + angle,
                facecolor=GROUP_COLORS[group],
                edgecolor="black",
                linewidth=0.6,
                alpha=0.88,
                zorder=3,
            )
            ax.add_patch(wedge)
            start += angle

    xmin, xmax, ymin, ymax = _point_limits(coords)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    if satellite:
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    if not report_test:
        ax.set_title("Composição espacial de CPUEn por grupo migração x origem", pad=16)
    ax.set_aspect("equal", adjustable="box")
    if report_test:
        ax.set_anchor("N")
    handles = [Line2D([0], [0], marker="o", color="none", markerfacecolor=GROUP_COLORS[g], markeredgecolor="black", markersize=12, label=g) for g in group_order]
    trecho_handles = [
        Line2D([0], [0], color=PRIMARY, linewidth=3, label="Montante"),
        Line2D([0], [0], color=ORANGE, linewidth=3, label="Jusante"),
    ]
    if report_test:
        fig.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.985),
            ncol=len(handles),
            frameon=False,
            columnspacing=1.2,
            handletextpad=0.45,
        )
        fig.legend(
            handles=trecho_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.855),
            ncol=2,
            frameon=False,
            columnspacing=1.4,
            handlelength=2.6,
        )
        fig.subplots_adjust(top=0.76, bottom=0.12)
        if satellite and has_satellite:
            ax.text(
                0.995,
                0.012,
                "Imagem base: Esri World Imagery",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=7,
                color="#555555",
                bbox=dict(facecolor="white", alpha=0.55, edgecolor="none", pad=1.5),
            )
    else:
        ax.legend(handles=handles, loc="lower left", frameon=True, facecolor="white", framealpha=0.9)
    if satellite:
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("black")
            spine.set_linewidth(1.0)
    else:
        _style_axis(ax, both=True)
    _save_fig(fig, path)


def _plot_mini_maps(point_ah: pd.DataFrame, path: Path, only_recent: bool = False) -> None:
    data = point_ah.copy()
    if only_recent:
        data = data.loc[data["ano_hidrologico"].isin(["AH2324", "AH2425", "AH2526"])].copy()
    years = (
        data[["ano_hidrologico", "ano_hidrologico_rotulo", "Ordem_AH"]]
        .drop_duplicates()
        .sort_values("Ordem_AH")
    )
    n = len(years)
    ncols = 3 if only_recent else 5
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 4.0 * nrows), squeeze=False)
    axes_flat = axes.ravel()
    coords = data[["Ponto", "Latitude", "Longitude", "Ordem_Espacial"]].drop_duplicates("Ponto").sort_values("Ordem_Espacial")
    xmin, xmax, ymin, ymax = _point_limits(coords)
    vmax = max(float(data["CPUEn"].max()), 1.0)
    norm = Normalize(vmin=0, vmax=vmax)

    for i, (_, year) in enumerate(years.iterrows()):
        ax = axes_flat[i]
        subset = data.loc[data["ano_hidrologico"] == year["ano_hidrologico"]].sort_values("Ordem_Espacial")
        ax.plot(coords["Longitude"], coords["Latitude"], color="#C5CCD6", linewidth=1.5, zorder=1)
        sizes = _normalize_sizes(subset["CPUEn"], 55, 850)
        ax.scatter(
            subset["Longitude"],
            subset["Latitude"],
            s=sizes,
            c=subset["CPUEn"],
            cmap="viridis",
            norm=norm,
            alpha=0.86,
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        for _, row in subset.iterrows():
            ax.text(row["Longitude"], row["Latitude"], row["Ponto"], fontsize=8, weight="bold", ha="left", va="bottom")
        ax.set_title(str(year["ano_hidrologico"]), fontsize=13, weight="bold")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_xticks([])
        ax.set_yticks([])
        _style_axis(ax, both=True)

    for j in range(n, len(axes_flat)):
        axes_flat[j].axis("off")

    sm = plt.cm.ScalarMappable(norm=norm, cmap="viridis")
    cbar = fig.colorbar(sm, ax=axes_flat[:n], shrink=0.72, pad=0.01)
    cbar.set_label("CPUEn")
    subtitle = "anos hidrológicos recentes" if only_recent else "todos os anos hidrológicos"
    fig.suptitle(f"Mini mapas de bolhas - CPUEn por ponto ({subtitle})", fontsize=20, weight="bold", y=0.995)
    _save_fig(fig, path)


def _plot_heatmap(point_ah: pd.DataFrame, metric: str, path: Path) -> None:
    data = point_ah.copy()
    matrix = (
        data.pivot_table(index="Ponto", columns="ano_hidrologico", values=metric, aggfunc="sum", fill_value=0)
        .reindex(POINT_ORDER)
    )
    ordered_cols = (
        data[["ano_hidrologico", "Ordem_AH"]]
        .drop_duplicates()
        .sort_values("Ordem_AH")["ano_hidrologico"]
        .tolist()
    )
    matrix = matrix.reindex(columns=ordered_cols, fill_value=0)
    fig, ax = plt.subplots(figsize=(18, 7.2))
    sns.heatmap(
        matrix,
        ax=ax,
        cmap="YlGnBu",
        linewidths=0.35,
        linecolor="white",
        cbar_kws={"label": metric},
    )
    ax.set_xlabel("Ano hidrológico")
    ax.set_ylabel("Ponto em ordem espacial")
    ax.set_title(f"Mapa de calor espacial-temporal - {metric}", pad=16)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    _save_fig(fig, path)


def _plot_collar_groups(group_point: pd.DataFrame, path: Path) -> None:
    group_order = ["Migradora nativa", "Migradora não nativa", "Não migradora nativa", "Não migradora não nativa"]
    grid = (
        group_point.pivot_table(index="Grupo_Migracao_Origem", columns="Ponto", values="CPUEn", aggfunc="sum", fill_value=0)
        .reindex(index=group_order, columns=POINT_ORDER, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(17.5, 7.0))
    vmax = max(float(grid.to_numpy().max()), 1.0)
    for y, group in enumerate(group_order):
        for x, point in enumerate(POINT_ORDER):
            value = grid.loc[group, point]
            size = 80 + (value / vmax) * 1800
            ax.scatter(x, y, s=size, c=[value], cmap="viridis", vmin=0, vmax=vmax, edgecolor="black", linewidth=0.8, alpha=0.86)
            if value > 0:
                ax.text(x, y, f"{value:.1f}", ha="center", va="center", fontsize=8, color="white" if value > vmax * 0.45 else "black", weight="bold")
    ax.axvspan(-0.5, 3.5, color=PRIMARY, alpha=0.06, linewidth=0)
    ax.axvspan(3.5, 8.5, color=ORANGE, alpha=0.06, linewidth=0)
    ax.set_xticks(range(len(POINT_ORDER)))
    ax.set_xticklabels(POINT_ORDER)
    ax.set_yticks(range(len(group_order)))
    ax.set_yticklabels(group_order)
    ax.set_xlim(-0.7, len(POINT_ORDER) - 0.3)
    ax.set_ylim(len(group_order) - 0.5, -0.5)
    ax.set_xlabel("Pontos em ordem espacial: Montante -> Jusante")
    ax.set_title("Colar espacial de bolhas - CPUEn por grupo ecológico e ponto", pad=16)
    sm = plt.cm.ScalarMappable(norm=Normalize(vmin=0, vmax=vmax), cmap="viridis")
    cbar = fig.colorbar(sm, ax=ax, shrink=0.82, pad=0.02)
    cbar.set_label("CPUEn")
    _style_axis(ax, both=True)
    _save_fig(fig, path)


def _plot_collar_species(species_point: pd.DataFrame, path: Path) -> None:
    species_order = (
        species_point.groupby("Nome_Cientifico")["CPUEn"].sum().sort_values(ascending=False).index.tolist()
    )
    matrix = (
        species_point.pivot_table(index="Nome_Cientifico", columns="Ponto", values="CPUEn", aggfunc="sum", fill_value=0)
        .reindex(index=species_order, columns=POINT_ORDER, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(17.5, 11.5))
    vmax = max(float(matrix.to_numpy().max()), 1.0)
    for y, species in enumerate(matrix.index):
        for x, point in enumerate(POINT_ORDER):
            value = matrix.loc[species, point]
            if value <= 0:
                ax.scatter(x, y, s=18, color="#EEF1F5", edgecolor="none")
                continue
            size = 35 + (value / vmax) * 1250
            ax.scatter(x, y, s=size, c=[value], cmap="viridis", vmin=0, vmax=vmax, edgecolor="black", linewidth=0.55, alpha=0.88)
    ax.axvspan(-0.5, 3.5, color=PRIMARY, alpha=0.06, linewidth=0)
    ax.axvspan(3.5, 8.5, color=ORANGE, alpha=0.06, linewidth=0)
    ax.set_xticks(range(len(POINT_ORDER)))
    ax.set_xticklabels(POINT_ORDER)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_xlim(-0.7, len(POINT_ORDER) - 0.3)
    ax.set_ylim(len(matrix.index) - 0.5, -0.5)
    ax.set_xlabel("Pontos em ordem espacial: Montante -> Jusante")
    ax.set_title("Colar espacial de bolhas - principais espécies por CPUEn", pad=16)
    sm = plt.cm.ScalarMappable(norm=Normalize(vmin=0, vmax=vmax), cmap="viridis")
    cbar = fig.colorbar(sm, ax=ax, shrink=0.82, pad=0.02)
    cbar.set_label("CPUEn")
    _style_axis(ax, both=True)
    _save_fig(fig, path)


def _plot_longitudinal_profile(point_total: pd.DataFrame, path: Path) -> None:
    data = point_total.sort_values("Ordem_Espacial")
    fig, axes = plt.subplots(3, 1, figsize=(17.5, 10.5), sharex=True)
    metrics = [("CPUEn", "CPUEn acumulada"), ("CPUEb", "CPUEb acumulada"), ("Riqueza_Total", "Riqueza total")]
    for ax, (metric, ylabel) in zip(axes, metrics):
        ax.plot(data["Ordem_Espacial"], data[metric], color=PRIMARY, marker="o", linewidth=3.0)
        ax.fill_between(data["Ordem_Espacial"], data[metric], color=SECONDARY, alpha=0.13)
        for _, row in data.iterrows():
            ax.text(row["Ordem_Espacial"], row[metric], row["Ponto"], ha="center", va="bottom", fontsize=10, weight="bold")
        ax.axvspan(0.5, 4.5, color=PRIMARY, alpha=0.06, linewidth=0)
        ax.axvspan(4.5, 9.5, color=ORANGE, alpha=0.06, linewidth=0)
        ax.set_ylabel(ylabel)
        _style_axis(ax)
    axes[-1].set_xticks(data["Ordem_Espacial"])
    axes[-1].set_xticklabels(data["Ponto"])
    axes[-1].set_xlabel("Ordem espacial aprovada: Montante -> Jusante")
    axes[0].set_title("Perfil longitudinal espacial das métricas acumuladas", pad=16)
    _save_fig(fig, path)


def _write_excel(path: Path, tables: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in tables.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)


def _write_readme(path: Path, tables: dict[str, pd.DataFrame]) -> None:
    total = tables["Espacial_Ponto_Total"]
    lines = [
        "# Porto Estrela - exploratório espacial",
        "",
        "Bancada fora do escopo oficial, inspirada nos mapas de bolhas e mini-mapas de Aimorés.",
        "",
        "## Produtos",
        "",
    ]
    for png in sorted(path.parent.glob("*.png")):
        lines.append(f"- `{png.name}`")
    lines.extend(
        [
            "",
            "## Base usada",
            "",
            "- Coordenadas reais: aba `Pontos_e_Campanhas` da planilha migrada validada.",
            "- Métricas quantitativas: `CPUEn_linha` e `CPUEb_linha` agregadas por ponto, ano hidrológico e grupo.",
            "- Riqueza: capturas reais qualitativas e quantitativas.",
            "- Ordem espacial aprovada: `P4`, `P5`, `P2`, `P1`, `P3`, `P6`, `P7`, `P8`, `P9`.",
            "",
            "## Leituras preliminares",
            "",
            f"- Ponto com maior CPUEn acumulada: `{total.sort_values('CPUEn', ascending=False).iloc[0]['Ponto']}`.",
            f"- Ponto com maior CPUEb acumulada: `{total.sort_values('CPUEb', ascending=False).iloc[0]['Ponto']}`.",
            f"- Ponto com maior riqueza total: `{total.sort_values('Riqueza_Total', ascending=False).iloc[0]['Ponto']}`.",
            "",
            "## Cautelas",
            "",
            "- Mapas de coordenadas mostram distribuição espacial visual, não substituem modelagem espacial.",
            "- Colares de bolhas são diagnósticos visuais para comparar pontos e grupos rapidamente.",
            "- Estes produtos permanecem exploratórios até revisão e aprovação.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera exploratorias espaciais de ictiofauna para Porto Estrela.")
    parser.add_argument(
        "--only-pie-report-test",
        action="store_true",
        help="Gera somente a versao de teste para relatorio do mapa de pizzas espaciais.",
    )
    parser.add_argument(
        "--satellite",
        action="store_true",
        help="No teste do mapa de pizzas, usa imagem satelite como fundo quando disponivel.",
    )
    args = parser.parse_args()

    _configure_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(BASE_FILE, sheet_name="Base_Linhas")
    coords = _load_coordinates()
    tables = _prepare_tables(base, coords)

    point_total = tables["Espacial_Ponto_Total"]
    point_ah = tables["Espacial_Ponto_AH"]
    group_point = tables["Grupos_Ponto"]
    species_point = tables["Top_Especies_Ponto"]

    if args.only_pie_report_test:
        suffix = "_satelite" if args.satellite else ""
        out = OUTPUT_DIR / f"espacial_03_mapa_pizzas_grupos_cpuen_pontos_teste_relatorio{suffix}.png"
        _plot_pie_map(group_point, point_total, out, report_test=True, satellite=args.satellite)
        print(f"Saida: {out}")
        return

    _plot_bubble_map(point_total, "CPUEn", OUTPUT_DIR / "espacial_01_mapa_bolhas_cpuen_acumulado.png")
    _plot_bubble_map(point_total, "CPUEb", OUTPUT_DIR / "espacial_02_mapa_bolhas_cpueb_acumulado.png")
    _plot_pie_map(group_point, point_total, OUTPUT_DIR / "espacial_03_mapa_pizzas_grupos_cpuen_pontos.png")
    _plot_mini_maps(point_ah, OUTPUT_DIR / "espacial_04_mini_mapas_cpuen_anos_hidrologicos.png", only_recent=False)
    _plot_mini_maps(point_ah, OUTPUT_DIR / "espacial_05_mini_mapas_cpuen_recente.png", only_recent=True)
    _plot_collar_groups(group_point, OUTPUT_DIR / "espacial_06_colar_grupos_cpuen_pontos.png")
    _plot_collar_species(species_point, OUTPUT_DIR / "espacial_07_colar_top_especies_cpuen_pontos.png")
    _plot_heatmap(point_ah, "CPUEn", OUTPUT_DIR / "espacial_08_mapa_calor_cpuen_ponto_ano.png")
    _plot_heatmap(point_ah, "Riqueza_Total", OUTPUT_DIR / "espacial_09_mapa_calor_riqueza_ponto_ano.png")
    _plot_longitudinal_profile(point_total, OUTPUT_DIR / "espacial_10_perfil_longitudinal_metricas_pontos.png")

    _write_excel(OUTPUT_DIR / "dados_exploratorios_espaciais_porto_estrela.xlsx", tables)
    _write_readme(OUTPUT_DIR / "README_analises_exploratorias_espaciais_porto_estrela.md", tables)
    print(f"Saida: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
