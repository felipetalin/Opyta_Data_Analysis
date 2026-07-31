from __future__ import annotations

import math
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import gerar_resultados_superficial_meio_fisico as superficial  # noqa: E402


CLIENT_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
PROJECT_DIR = next(path for path in CLIENT_ROOT.iterdir() if path.name.startswith("A&G"))
OUTPUT_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "resultados" / "superficial"
HYDROLOGY_KMZ = PROJECT_DIR / "Geo" / "1AEMG002" / "Hidrografia.kmz"

CAMPAIGNS = ["Campanha-01-Chuva", "Campanha-02-Seca"]
POINT_COLORS = {
    "base": "#F2F5F2",
    "edge": "#263238",
    "text": "#202A2E",
    "hydro": "#4F8DB3",
    "grid": "#DDE5DF",
}
VIOLATION_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "violacoes_verde", ["#E8F5E9", "#9CCC65", "#43A047", "#1B7F22"]
)
IQA_COLORS = {
    "Péssima": "#8B0000",
    "Ruim": "#E74C3C",
    "Regular": "#F39C12",
    "Boa": "#3498DB",
    "Ótima": "#2ECC71",
}
IET_COLORS = {
    "Ultraoligotrófico": "#1F77B4",
    "Oligotrófico": "#5DADE2",
    "Mesotrófico": "#F1C40F",
    "Eutrófico": "#E67E22",
    "Supereutrófico": "#E74C3C",
    "Hipereutrófico": "#8B0000",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def fold(value: Any) -> str:
    text = clean_text(value)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def point_key(point: str) -> int:
    match = re.search(r"(\d+)$", clean_text(point))
    return int(match.group(1)) if match else 999


def campaign_key(campaign: str) -> int:
    return CAMPAIGNS.index(campaign) if campaign in CAMPAIGNS else 999


def load_hydrology_segments(kmz_path: Path) -> list[np.ndarray]:
    if not kmz_path.exists():
        return []
    with zipfile.ZipFile(kmz_path) as archive:
        kml_names = [name for name in archive.namelist() if name.lower().endswith(".kml")]
        if not kml_names:
            return []
        xml_bytes = archive.read(kml_names[0])
    root = ET.fromstring(xml_bytes)
    segments: list[np.ndarray] = []
    for node in root.iter():
        if not node.tag.lower().endswith("coordinates") or not node.text:
            continue
        coords = []
        for token in node.text.replace("\n", " ").replace("\t", " ").split():
            parts = token.split(",")
            if len(parts) < 2:
                continue
            try:
                lon = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                continue
            coords.append((lon, lat))
        if len(coords) >= 2:
            segments.append(np.asarray(coords, dtype=float))
    return segments


def load_points(surface: pd.DataFrame) -> pd.DataFrame:
    coords = (
        surface[["nome_ponto", "latitude", "longitude"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"nome_ponto": "Ponto", "latitude": "Latitude", "longitude": "Longitude"})
    )
    coords["Ponto"] = coords["Ponto"].map(clean_text)
    coords["PlotLongitude"] = coords["Longitude"]
    coords["PlotLatitude"] = coords["Latitude"]
    display_offsets = {
        "PT_04": (-0.00035, -0.00022),
        "PT_07": (0.00035, 0.00022),
        "PT_08": (-0.00032, 0.00018),
        "PT_11": (0.00032, -0.00018),
    }
    for point, (dx, dy) in display_offsets.items():
        mask = coords["Ponto"].eq(point)
        coords.loc[mask, "PlotLongitude"] = coords.loc[mask, "Longitude"] + dx
        coords.loc[mask, "PlotLatitude"] = coords.loc[mask, "Latitude"] + dy
    return coords.sort_values("Ponto", key=lambda s: s.map(point_key)).reset_index(drop=True)


def build_violation_by_point(surface: pd.DataFrame) -> pd.DataFrame:
    df = surface.copy()
    df["campanha_display"] = df["nome_campanha"].map(lambda x: superficial.CAMPAIGN_LABELS.get(clean_text(x), clean_text(x)))
    df["status_classe2"] = "Sem VMP Classe 2"
    for _, group in df.groupby("nome_parametro", sort=False):
        limits = superficial.get_limits(group)
        df.loc[group.index, "status_classe2"] = group.apply(lambda row: superficial.classify_row(row, limits), axis=1)

    numeric = df[df["valor_medido"].notna()].copy()
    summary = (
        numeric.groupby(["campanha_display", "nome_ponto"], as_index=False)
        .agg(
            parametros_avaliados=("nome_parametro", "nunique"),
            violacoes=("status_classe2", lambda s: int((s == "Viola").sum())),
        )
        .rename(columns={"campanha_display": "Campanha", "nome_ponto": "Ponto"})
    )
    summary["percentual_violacao"] = np.where(
        summary["parametros_avaliados"] > 0,
        100 * summary["violacoes"] / summary["parametros_avaliados"],
        0,
    )
    return summary.sort_values(["Campanha", "Ponto"], key=lambda s: s.map(point_key) if s.name == "Ponto" else s.map(campaign_key))


def map_limits(points: pd.DataFrame, segments: list[np.ndarray]) -> tuple[float, float, float, float]:
    xmin = float(points[["Longitude", "PlotLongitude"]].min().min())
    xmax = float(points[["Longitude", "PlotLongitude"]].max().max())
    ymin = float(points[["Latitude", "PlotLatitude"]].min().min())
    ymax = float(points[["Latitude", "PlotLatitude"]].max().max())
    xpad = max((xmax - xmin) * 0.28, 0.003)
    ypad = max((ymax - ymin) * 0.28, 0.003)
    return xmin - xpad, xmax + xpad, ymin - ypad, ymax + ypad


def add_scale_bar(ax: Any, xmin: float, xmax: float, ymin: float, ymax: float) -> None:
    lat_mid = (ymin + ymax) / 2
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat_mid))
    width_km = max((xmax - xmin) * km_per_deg_lon, 0.1)
    raw = width_km / 5
    candidates = np.array([0.1, 0.2, 0.5, 1, 2, 5, 10])
    scale_km = float(candidates[np.argmin(np.abs(candidates - raw))])
    scale_deg = scale_km / km_per_deg_lon
    x0 = xmin + (xmax - xmin) * 0.05
    y0 = ymin + (ymax - ymin) * 0.055
    ax.plot([x0, x0 + scale_deg], [y0, y0], color="#202A2E", lw=2.0, zorder=5)
    ax.plot([x0, x0], [y0 - (ymax - ymin) * 0.006, y0 + (ymax - ymin) * 0.006], color="#202A2E", lw=1.2, zorder=5)
    ax.plot(
        [x0 + scale_deg, x0 + scale_deg],
        [y0 - (ymax - ymin) * 0.006, y0 + (ymax - ymin) * 0.006],
        color="#202A2E",
        lw=1.2,
        zorder=5,
    )
    label = f"{scale_km:g} km".replace(".", ",")
    ax.text(x0 + scale_deg / 2, y0 + (ymax - ymin) * 0.014, label, ha="center", va="bottom", fontsize=8.5, color="#202A2E")


def add_north_arrow(ax: Any) -> None:
    ax.annotate(
        "N",
        xy=(0.94, 0.90),
        xytext=(0.94, 0.80),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#202A2E",
        arrowprops={"arrowstyle": "-|>", "lw": 1.4, "color": "#202A2E"},
        zorder=8,
    )


def add_point_labels(ax: Any, points: pd.DataFrame) -> None:
    offsets = {
        "PT_08": (0.0012, 0.0011),
        "PT_11": (0.0012, -0.0012),
        "PT_10": (-0.0020, -0.0010),
        "PT_09": (-0.0020, 0.0007),
    }
    for row in points.itertuples(index=False):
        dx, dy = offsets.get(row.Ponto, (0.00035, 0.00025))
        ax.text(
            row.PlotLongitude + dx,
            row.PlotLatitude + dy,
            row.Ponto.replace("_", "-"),
            fontsize=8.0,
            color="#344047",
            zorder=4,
        )


def base_map(ax: Any, points: pd.DataFrame, segments: list[np.ndarray], bounds: tuple[float, float, float, float]) -> None:
    xmin, xmax, ymin, ymax = bounds
    for seg in segments:
        if seg.size == 0:
            continue
        sxmin, symin = seg.min(axis=0)
        sxmax, symax = seg.max(axis=0)
        if sxmax < xmin or sxmin > xmax or symax < ymin or symin > ymax:
            continue
        ax.plot(seg[:, 0], seg[:, 1], color=POINT_COLORS["hydro"], lw=0.85, alpha=0.75, zorder=0.8)
    ax.scatter(
        points["PlotLongitude"],
        points["PlotLatitude"],
        s=18,
        color="#D7DDE0",
        edgecolor="#8B969A",
        linewidth=0.45,
        zorder=1.0,
    )
    add_point_labels(ax, points)
    add_scale_bar(ax, xmin, xmax, ymin, ymax)
    add_north_arrow(ax)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(color=POINT_COLORS["grid"], linewidth=0.65, alpha=0.8)
    ax.tick_params(axis="both", labelsize=8.4)
    ax.set_aspect("equal", adjustable="box")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)


def panel_figure() -> tuple[Any, list[Any]]:
    fig, axes = plt.subplots(1, 2, figsize=(16.54, 8.27), dpi=450, sharex=True, sharey=True)
    return fig, list(axes)


def plot_violations(points: pd.DataFrame, data: pd.DataFrame, segments: list[np.ndarray], bounds: tuple[float, float, float, float]) -> Path:
    out_png = OUTPUT_DIR / "07_minimapa_violacoes_por_ponto_chuva_seca.png"
    max_value = max(1, int(data["violacoes"].max()))
    norm = mcolors.Normalize(vmin=0, vmax=max_value)
    fig, axes = panel_figure()
    mappable = None
    for ax, campaign in zip(axes, CAMPAIGNS, strict=True):
        base_map(ax, points, segments, bounds)
        subset = points.merge(data[data["Campanha"].eq(campaign)], on="Ponto", how="left")
        subset[["violacoes", "parametros_avaliados", "percentual_violacao"]] = subset[
            ["violacoes", "parametros_avaliados", "percentual_violacao"]
        ].fillna(0)
        mappable = ax.scatter(
            subset["PlotLongitude"],
            subset["PlotLatitude"],
            s=175,
            c=subset["violacoes"],
            cmap=VIOLATION_CMAP,
            norm=norm,
            edgecolor=POINT_COLORS["edge"],
            linewidth=0.75,
            zorder=3,
        )
        for row in subset.itertuples(index=False):
            ax.text(row.PlotLongitude, row.PlotLatitude, f"{int(row.violacoes)}", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#102015", zorder=4)
        ax.set_title(campaign, fontsize=16, fontweight="bold", pad=10)
    axes[0].set_ylabel("Latitude", fontsize=10.5)
    axes[0].set_xlabel("Longitude", fontsize=10.5)
    axes[1].set_xlabel("Longitude", fontsize=10.5)
    cax = fig.add_axes([0.91, 0.24, 0.018, 0.52])
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label("Parâmetros com violação (n)", fontsize=10.5)
    cb.ax.tick_params(labelsize=8.8)
    fig.legend(
        handles=[Line2D([0], [0], color=POINT_COLORS["hydro"], lw=1.5, label="Hidrografia")],
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


def class_panel(
    points: pd.DataFrame,
    data: pd.DataFrame,
    value_col: str,
    class_col: str,
    colors: dict[str, str],
    legend_order: list[str],
    output_name: str,
    colorbar_label: str,
    segments: list[np.ndarray],
    bounds: tuple[float, float, float, float],
) -> Path:
    out_png = OUTPUT_DIR / output_name
    fig, axes = panel_figure()
    for ax, campaign in zip(axes, CAMPAIGNS, strict=True):
        base_map(ax, points, segments, bounds)
        subset = points.merge(data[data["Campanha"].eq(campaign)], on="Ponto", how="left")
        marker_colors = [colors.get(clean_text(cls), "#D7DDE0") for cls in subset[class_col]]
        ax.scatter(
            subset["PlotLongitude"],
            subset["PlotLatitude"],
            s=175,
            color=marker_colors,
            edgecolor=POINT_COLORS["edge"],
            linewidth=0.75,
            zorder=3,
        )
        for row in subset.itertuples(index=False):
            value = getattr(row, value_col)
            label = "" if pd.isna(value) else f"{float(value):.0f}"
            ax.text(row.PlotLongitude, row.PlotLatitude, label, ha="center", va="center", fontsize=8.0, fontweight="bold", color=POINT_COLORS["text"], zorder=4)
        ax.set_title(campaign, fontsize=16, fontweight="bold", pad=10)
    axes[0].set_ylabel("Latitude", fontsize=10.5)
    axes[0].set_xlabel("Longitude", fontsize=10.5)
    axes[1].set_xlabel("Longitude", fontsize=10.5)
    handles = [Patch(facecolor=colors[label], edgecolor=POINT_COLORS["edge"], label=label) for label in legend_order if label in colors]
    handles.append(Line2D([0], [0], color=POINT_COLORS["hydro"], lw=1.5, label="Hidrografia"))
    fig.legend(
        handles=handles,
        loc="lower center",
        frameon=False,
        ncol=min(5, len(handles)),
        fontsize=9.5,
        bbox_to_anchor=(0.5, 0.026),
        title=colorbar_label,
        title_fontsize=10.5,
    )
    fig.tight_layout(rect=(0.035, 0.09, 0.99, 0.96))
    fig.savefig(out_png, facecolor="white", dpi=300)
    plt.close(fig)
    return out_png


def load_index_table(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    df = pd.read_excel(path)
    df["Ponto"] = df["Ponto"].map(clean_text)
    df["Campanha"] = df["Campanha"].map(clean_text)
    return df


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    surface = superficial.load_surface()
    points = load_points(surface)
    segments = load_hydrology_segments(HYDROLOGY_KMZ)
    bounds = map_limits(points, segments)

    violations = build_violation_by_point(surface)
    iqa = load_index_table("05_IQA_Tabela.xlsx")
    iet = load_index_table("06_IET_Tabela.xlsx")

    outputs = {
        "violacoes": plot_violations(points, violations, segments, bounds),
        "iqa": class_panel(
            points,
            iqa,
            "IQA",
            "Classe",
            IQA_COLORS,
            ["Ótima", "Boa", "Regular", "Ruim", "Péssima"],
            "08_minimapa_iqa_chuva_seca.png",
            "Classe IQA",
            segments,
            bounds,
        ),
        "iet": class_panel(
            points,
            iet,
            "IET",
            "Classe",
            IET_COLORS,
            ["Ultraoligotrófico", "Oligotrófico", "Mesotrófico", "Eutrófico", "Supereutrófico", "Hipereutrófico"],
            "09_minimapa_iet_chuva_seca.png",
            "Classe IET",
            segments,
            bounds,
        ),
    }

    out_xlsx = OUTPUT_DIR / "07_Dados_Minimapas_Agua_Superficial.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        points.to_excel(writer, sheet_name="pontos", index=False)
        violations.to_excel(writer, sheet_name="violacoes_por_ponto", index=False)
        iqa.to_excel(writer, sheet_name="iqa", index=False)
        iet.to_excel(writer, sheet_name="iet", index=False)

    print({"xlsx": str(out_xlsx), "pngs": {key: str(value) for key, value in outputs.items()}, "hidrografia_segmentos": len(segments)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
