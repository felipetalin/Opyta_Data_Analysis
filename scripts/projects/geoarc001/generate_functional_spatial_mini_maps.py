from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import load_theme
from opyta_analysis.geo_reference import (
    read_kml_line_coordinates,
    read_kml_point_coordinates,
    read_kml_polygon_coordinates,
    standardize_point_name,
)


DEFAULT_SOURCE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Planilhas de migracao"
    r"\Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx"
)
DEFAULT_OUTPUT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\Exploratorio_assembleia_ictiofauna"
)
DEFAULT_GROUP_TABLE = DEFAULT_OUTPUT / "23_df_heatmap_funcoes_ecologicas_ictiofauna.xlsx"
DEFAULT_COORD_REFERENCE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Geo\Arcelor_2026.kmz"
)
DEFAULT_HYDROLOGY_LAYERS = [
    Path(
        r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
        r"\Arcellor Monitoramento\Geo\Drenagem_AID.kml"
    ),
    Path(
        r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
        r"\Arcellor Monitoramento\Geo\Drenagem_ADA.kml"
    ),
    Path(
        r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
        r"\Arcellor Monitoramento\Geo\Talvegue_ADA.kml"
    ),
]
DEFAULT_ADA_LAYER = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Geo\ADA .kml"
)

POINT_LABEL_OFFSETS = {
    "IC-ARC-01": (5, 5),
    "IC-ARC-02": (-30, -8),
    "IC-ARC-04": (5, 8),
    "IC-ARC-05": (-8, 4),
    "IC-ARC-06": (6, -8),
    "IC-ARC-07": (5, 7),
    "IC-ARC-08": (5, 5),
    "IC-ARC-09": (6, -8),
    "IC-ARC-10": (-30, 0),
    "IC-ARC-12": (5, -8),
    "IC-ARC-14": (5, 6),
}


def _point_number(point: str) -> int:
    match = re.search(r"(\d+)", str(point))
    return int(match.group(1)) if match else 999999


def _point_sort_key(point: str) -> tuple[int, str]:
    return (_point_number(point), str(point))


def _campaign_sort_key(campaign: object) -> tuple[int, str]:
    text = str(campaign)
    match = re.search(r"(\d+)", text)
    return (int(match.group(1)) if match else 999999, text)


def _short_point(point: str) -> str:
    text = str(point)
    number = _point_number(text)
    if number >= 999999:
        return text
    if re.search(r"\bPIC\b|^PIC[-_\s]*\d+", text, flags=re.IGNORECASE):
        return f"PIC-{number:02d}"
    if re.search(r"\bIC[\s_-]*ARC\b|^IC[-_\s]*\d+", text, flags=re.IGNORECASE):
        return f"IC-{number:02d}"
    prefix_match = re.match(r"^\s*([A-Za-z]{1,4})", text)
    prefix = prefix_match.group(1).upper() if prefix_match else "P"
    return f"{prefix}-{number:02d}"


def _theme_colors(theme: dict) -> tuple[str, str, str]:
    return (
        str(theme.get("primary_hex", "#2E6F95")),
        str(theme.get("secondary_hex", "#E07A5F")),
        str(theme.get("highlight_hex", "#3D5A80")),
    )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _normalize_sizes(values: pd.Series, min_size: float = 10, max_size: float = 360) -> np.ndarray:
    arr = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(dtype=float)
    if arr.size == 0:
        return np.array([], dtype=float)
    vmax = float(np.nanmax(arr))
    if vmax <= 0:
        return np.full(arr.shape, min_size, dtype=float)
    return min_size + (np.sqrt(arr / vmax) * (max_size - min_size))


def _coordinate_variation_from_workbook(source: Path) -> pd.DataFrame:
    pc = pd.read_excel(source, sheet_name="Pontos_e_Campanhas")
    required = ["Ponto", "Campanha", "Latitude", "Longitude"]
    missing = [col for col in required if col not in pc.columns]
    if missing:
        raise ValueError(f"Colunas de coordenadas ausentes: {', '.join(missing)}")

    raw = pc[required].copy()
    raw["Ponto"] = raw["Ponto"].map(standardize_point_name)
    raw["Campanha"] = raw["Campanha"].astype(str).str.strip()
    raw["Latitude"] = pd.to_numeric(raw["Latitude"], errors="coerce")
    raw["Longitude"] = pd.to_numeric(raw["Longitude"], errors="coerce")
    raw = raw.dropna(subset=["Ponto", "Latitude", "Longitude"]).copy()
    coord_variation = raw.groupby("Ponto", as_index=False).agg(
        n_registros=("Latitude", "size"),
        n_latitudes=("Latitude", "nunique"),
        n_longitudes=("Longitude", "nunique"),
        lat_min=("Latitude", "min"),
        lat_max=("Latitude", "max"),
        lon_min=("Longitude", "min"),
        lon_max=("Longitude", "max"),
    )
    coord_variation["amplitude_lat"] = coord_variation["lat_max"] - coord_variation["lat_min"]
    coord_variation["amplitude_lon"] = coord_variation["lon_max"] - coord_variation["lon_min"]
    return coord_variation.sort_values("Ponto", key=lambda s: s.map(_point_sort_key)).reset_index(drop=True)


def load_coordinates(source: Path, coordinate_reference: Path | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coord_variation = _coordinate_variation_from_workbook(source)
    if coordinate_reference is not None:
        ref = read_kml_point_coordinates(coordinate_reference)
        if ref.empty:
            raise ValueError(f"Nenhuma coordenada de ponto encontrada na referencia: {coordinate_reference}")
        coords = ref.rename(columns={"Latitude_ref": "Latitude", "Longitude_ref": "Longitude"}).copy()
        coords["estrategia_coordenada"] = "referencia_kmz"
    else:
        pc = pd.read_excel(source, sheet_name="Pontos_e_Campanhas")
        raw = pc[["Ponto", "Campanha", "Latitude", "Longitude"]].copy()
        raw["Ponto"] = raw["Ponto"].map(standardize_point_name)
        raw["Campanha"] = raw["Campanha"].astype(str).str.strip()
        raw["Latitude"] = pd.to_numeric(raw["Latitude"], errors="coerce")
        raw["Longitude"] = pd.to_numeric(raw["Longitude"], errors="coerce")
        raw = raw.dropna(subset=["Ponto", "Latitude", "Longitude"]).copy()
        raw = raw.sort_values(
            ["Ponto", "Campanha"],
            key=lambda s: s.map(_point_sort_key) if s.name == "Ponto" else s.map(_campaign_sort_key),
        )
        coords = raw.drop_duplicates("Ponto", keep="first")[["Ponto", "Campanha", "Latitude", "Longitude"]].copy()
        coords = coords.rename(columns={"Campanha": "Campanha_Coordenada"})
        coords["estrategia_coordenada"] = "primeira_coordenada_valida_planilha"
    coords = coords.merge(coord_variation, on="Ponto", how="left")
    coords = coords.sort_values("Ponto", key=lambda s: s.map(_point_sort_key)).reset_index(drop=True)

    pairs = []
    for i, a in coords.iterrows():
        for j, b in coords.iterrows():
            if i >= j:
                continue
            distance = _haversine_km(a["Latitude"], a["Longitude"], b["Latitude"], b["Longitude"])
            pairs.append(
                {
                    "ponto_a": a["Ponto"],
                    "ponto_b": b["Ponto"],
                    "distancia_km": distance,
                    "risco_sobreposicao": "alto" if distance < 0.5 else "moderado" if distance < 1.0 else "baixo",
                }
            )
    close_pairs = pd.DataFrame(pairs).sort_values("distancia_km")
    return coords, close_pairs, coord_variation


def load_group_panel(
    group_table: Path,
    coords: pd.DataFrame,
    exclude_groups: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not group_table.exists():
        raise FileNotFoundError(f"Tabela do produto 23 não encontrada: {group_table}")
    panel = pd.read_excel(group_table, sheet_name="heatmap_funcoes")
    definitions = pd.read_excel(group_table, sheet_name="definicoes_funcoes")
    if exclude_groups:
        panel = panel[~panel["grupo_funcional"].isin(exclude_groups)].copy()
        definitions = definitions[~definitions["codigo"].isin(exclude_groups)].copy()
    required = [
        "grupo_funcional",
        "grupo_rotulo",
        "ordem_grupo",
        "ano",
        "nome_ponto",
        "nome_campanha",
        "CPUEn_grupo",
        "CPUEn_total",
        "perc_CPUEn",
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise ValueError(f"Colunas ausentes na tabela do produto 23: {', '.join(missing)}")

    points = coords["Ponto"].tolist()
    years = sorted(int(y) for y in panel["ano"].dropna().unique().tolist())
    groups = definitions.sort_values("ordem_grupo")[
        ["ordem_grupo", "codigo", "rotulo", "criterio"]
    ].rename(columns={"codigo": "grupo_funcional", "rotulo": "grupo_rotulo"})

    grouped = (
        panel.groupby(["grupo_funcional", "grupo_rotulo", "ordem_grupo", "ano", "nome_ponto"], as_index=False)
        .agg(
            CPUEn_grupo_medio=("CPUEn_grupo", "mean"),
            CPUEn_grupo_soma=("CPUEn_grupo", "sum"),
            perc_CPUEn_medio=("perc_CPUEn", "mean"),
            CPUEn_total_medio=("CPUEn_total", "mean"),
            n_campanhas=("nome_campanha", "nunique"),
            campanhas_com_registro=("CPUEn_grupo", lambda values: int((pd.to_numeric(values, errors="coerce") > 0).sum())),
        )
    )

    skeleton = pd.MultiIndex.from_product(
        [groups["grupo_funcional"].tolist(), years, points],
        names=["grupo_funcional", "ano", "nome_ponto"],
    ).to_frame(index=False)
    annual = skeleton.merge(groups, on="grupo_funcional", how="left")
    annual = annual.merge(grouped, on=["grupo_funcional", "grupo_rotulo", "ordem_grupo", "ano", "nome_ponto"], how="left")
    for col in [
        "CPUEn_grupo_medio",
        "CPUEn_grupo_soma",
        "perc_CPUEn_medio",
        "CPUEn_total_medio",
        "n_campanhas",
        "campanhas_com_registro",
    ]:
        annual[col] = pd.to_numeric(annual[col], errors="coerce").fillna(0)
    annual["n_campanhas"] = annual["n_campanhas"].astype(int)
    annual["campanhas_com_registro"] = annual["campanhas_com_registro"].astype(int)
    annual = annual.merge(coords, left_on="nome_ponto", right_on="Ponto", how="left")
    annual = annual.sort_values(["ordem_grupo", "ano", "nome_ponto"], key=lambda s: s.map(_point_sort_key) if s.name == "nome_ponto" else s)
    return annual, definitions


def _point_limits(coords: pd.DataFrame) -> tuple[float, float, float, float]:
    xmin, xmax = float(coords["Longitude"].min()), float(coords["Longitude"].max())
    ymin, ymax = float(coords["Latitude"].min()), float(coords["Latitude"].max())
    xpad = max((xmax - xmin) * 0.12, 0.002)
    ypad = max((ymax - ymin) * 0.12, 0.002)
    return xmin - xpad, xmax + xpad, ymin - ypad, ymax + ypad


def load_hydrology(layers: list[Path]) -> pd.DataFrame:
    frames = []
    for layer in layers:
        if not layer.exists():
            continue
        data = read_kml_line_coordinates(layer)
        if data.empty:
            continue
        data["camada"] = layer.stem
        data["tipo_malha"] = np.where(data["camada"].str.contains("Talvegue", case=False, na=False), "talvegue", "drenagem")
        frames.append(data)
    if not frames:
        return pd.DataFrame(columns=["fonte", "camada", "tipo_malha", "feature_id", "vertex_order", "Longitude", "Latitude"])
    return pd.concat(frames, ignore_index=True)


def summarize_hydrology(hydrology: pd.DataFrame) -> pd.DataFrame:
    if hydrology.empty:
        return pd.DataFrame(columns=["camada", "tipo_malha", "feicoes", "vertices", "lon_min", "lon_max", "lat_min", "lat_max"])
    return (
        hydrology.groupby(["camada", "tipo_malha"], as_index=False)
        .agg(
            feicoes=("feature_id", "nunique"),
            vertices=("vertex_order", "size"),
            lon_min=("Longitude", "min"),
            lon_max=("Longitude", "max"),
            lat_min=("Latitude", "min"),
            lat_max=("Latitude", "max"),
        )
        .sort_values(["tipo_malha", "camada"])
    )


def load_ada(layer: Path | None) -> pd.DataFrame:
    columns = [
        "fonte",
        "camada",
        "polygon_id",
        "ring_id",
        "ring_type",
        "nome_feicao",
        "vertex_order",
        "Longitude",
        "Latitude",
    ]
    if layer is None or not layer.exists():
        return pd.DataFrame(columns=columns)
    data = read_kml_polygon_coordinates(layer)
    if data.empty:
        return pd.DataFrame(columns=columns)
    data["camada"] = layer.stem.strip()
    return data[columns]


def summarize_ada(ada: pd.DataFrame) -> pd.DataFrame:
    if ada.empty:
        return pd.DataFrame(columns=["camada", "poligonos", "vertices", "lon_min", "lon_max", "lat_min", "lat_max"])
    return (
        ada.groupby("camada", as_index=False)
        .agg(
            poligonos=("polygon_id", "nunique"),
            vertices=("vertex_order", "size"),
            lon_min=("Longitude", "min"),
            lon_max=("Longitude", "max"),
            lat_min=("Latitude", "min"),
            lat_max=("Latitude", "max"),
        )
        .sort_values("camada")
    )


def _hydrology_segments(
    hydrology: pd.DataFrame,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> dict[str, list[np.ndarray]]:
    segments = {"drenagem": [], "talvegue": []}
    if hydrology.empty:
        return segments
    for (_source, feature_id), line in hydrology.groupby(["fonte", "feature_id"], sort=False):
        line = line.sort_values("vertex_order")
        if line.empty:
            continue
        if (
            float(line["Longitude"].max()) < xmin
            or float(line["Longitude"].min()) > xmax
            or float(line["Latitude"].max()) < ymin
            or float(line["Latitude"].min()) > ymax
        ):
            continue
        coords = line[["Longitude", "Latitude"]].to_numpy(dtype=float)
        if len(coords) < 2:
            continue
        kind = "talvegue" if str(line["tipo_malha"].iloc[0]) == "talvegue" else "drenagem"
        segments[kind].append(coords)
    return segments


def _ada_polygons(
    ada: pd.DataFrame,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> list[np.ndarray]:
    polygons: list[np.ndarray] = []
    if ada.empty:
        return polygons
    outer = ada[ada["ring_type"] == "outer"].copy()
    for (_source, polygon_id, ring_id), ring in outer.groupby(["fonte", "polygon_id", "ring_id"], sort=False):
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
        if len(coords) < 3:
            continue
        polygons.append(coords)
    return polygons


def _add_ada(ax, polygons: list[np.ndarray]) -> None:
    if not polygons:
        return
    ax.add_collection(
        PolyCollection(
            polygons,
            facecolors=[mcolors.to_rgba("#C43D4D", 0.12)],
            edgecolors="none",
            zorder=0.05,
        )
    )
    ax.add_collection(
        PolyCollection(
            polygons,
            facecolors="none",
            edgecolors=[mcolors.to_rgba("#C43D4D", 0.85)],
            linewidths=0.9,
            zorder=0.15,
        )
    )


def _add_hydrology(ax, segments: dict[str, list[np.ndarray]]) -> None:
    hydrology_segments = []
    hydrology_segments.extend(segments.get("drenagem", []))
    hydrology_segments.extend(segments.get("talvegue", []))
    if hydrology_segments:
        ax.add_collection(
            LineCollection(
                hydrology_segments,
                colors="#8AC9E8",
                linewidths=0.38,
                alpha=1.0,
                zorder=0.25,
            )
        )


def plot_spatial_mini_maps(
    annual: pd.DataFrame,
    coords: pd.DataFrame,
    hydrology: pd.DataFrame,
    ada: pd.DataFrame,
    out_png: Path,
    theme: dict,
) -> None:
    primary, _secondary, _highlight = _theme_colors(theme)
    groups = (
        annual[["ordem_grupo", "grupo_funcional", "grupo_rotulo"]]
        .drop_duplicates()
        .sort_values("ordem_grupo")
        .to_dict("records")
    )
    years = sorted(int(y) for y in annual["ano"].dropna().unique().tolist())
    nrows, ncols = len(groups), len(years)
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(15.5, max(7.4, 2.95 * nrows)),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
    )
    if nrows == 1:
        axes = np.array([axes])
    xmin, xmax, ymin, ymax = _point_limits(coords)
    ada_polygons = _ada_polygons(ada, xmin, xmax, ymin, ymax)
    hydrology_segments = _hydrology_segments(hydrology, xmin, xmax, ymin, ymax)
    vmax_color = 100.0
    vmax_size = max(float(annual["CPUEn_grupo_medio"].max()), 1.0)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "geoarc_spatial_functional", ["#F7F7F7", "#DDEEDB", "#8BC28A", "#2F7D4A"]
    )
    norm = mcolors.Normalize(vmin=0, vmax=vmax_color)

    for row_idx, group in enumerate(groups):
        for col_idx, year in enumerate(years):
            ax = axes[row_idx, col_idx]
            data = annual[(annual["grupo_funcional"] == group["grupo_funcional"]) & (annual["ano"] == year)].copy()
            data = data.sort_values("nome_ponto", key=lambda s: s.map(_point_sort_key))
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
            nonzero = data[data["CPUEn_grupo_medio"] > 0].copy()
            if not nonzero.empty:
                sizes = _normalize_sizes(nonzero["CPUEn_grupo_medio"], 26, 330)
                ax.scatter(
                    nonzero["Longitude"],
                    nonzero["Latitude"],
                    s=sizes,
                    c=nonzero["perc_CPUEn_medio"],
                    cmap=cmap,
                    norm=norm,
                    edgecolor="#1C1C1C",
                    linewidth=0.45,
                    alpha=0.92,
                    zorder=3,
                )
            for _, point in coords.iterrows():
                dx, dy = POINT_LABEL_OFFSETS.get(point["Ponto"], (4, 4))
                ax.annotate(
                    _short_point(point["Ponto"]),
                    (point["Longitude"], point["Latitude"]),
                    xytext=(dx, dy),
                    textcoords="offset points",
                    fontsize=5.9,
                    color="#202020",
                    ha="left" if dx >= 0 else "right",
                    va="center",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=0.45),
                    zorder=4,
                )
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.grid(True, color="#E6E6E6", linewidth=0.45)
            ax.tick_params(axis="both", labelsize=6)
            if row_idx == 0:
                ax.set_title(str(year), fontsize=10.5, fontweight="bold")
            if col_idx == 0:
                ax.set_ylabel(group["grupo_rotulo"], fontsize=9.5, fontweight="bold")
            else:
                ax.set_ylabel("")
            if row_idx == nrows - 1:
                ax.set_xlabel("Longitude", fontsize=8)
            if col_idx == 0:
                ax.tick_params(labelleft=True)
            else:
                ax.tick_params(labelleft=False)

    cax = fig.add_axes([0.915, 0.18, 0.018, 0.66])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label("CPUEn do grupo funcional (%)", fontsize=9.5)

    fig.suptitle(
        "Mini mapas anuais dos grupos funcionais sentinelas",
        x=0.02,
        y=0.988,
        ha="left",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.02,
        0.018,
        "Cor = participação média do grupo no CPUEn total do ponto/ano; bolhas maiores indicam maior CPUEn médio anual absoluto do grupo. Rótulos abreviados por ponto; produto exploratório.",
        ha="left",
        fontsize=8.6,
        color="#404040",
    )
    fig.subplots_adjust(left=0.085, right=0.89, top=0.94, bottom=0.075, hspace=0.28, wspace=0.10)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    output_dir: Path,
    product_prefix: str,
    annual: pd.DataFrame,
    coords: pd.DataFrame,
    definitions: pd.DataFrame,
    close_pairs: pd.DataFrame,
    coord_variation: pd.DataFrame,
    hydrology_summary: pd.DataFrame,
    ada_summary: pd.DataFrame,
    summary: dict,
) -> dict[str, str]:
    xlsx = output_dir / f"{product_prefix}_df_mini_mapas_funcoes_ecologicas_ictiofauna.xlsx"
    manifest = output_dir / f"{product_prefix}_manifesto_mini_mapas_funcoes_ecologicas_ictiofauna.json"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        annual.to_excel(writer, sheet_name="mini_mapas_ano", index=False)
        coords.to_excel(writer, sheet_name="coordenadas_pontos", index=False)
        definitions.to_excel(writer, sheet_name="definicoes_funcoes", index=False)
        close_pairs.to_excel(writer, sheet_name="diagnostico_sobreposicao", index=False)
        coord_variation.to_excel(writer, sheet_name="diagnostico_variacao_coords", index=False)
        hydrology_summary.to_excel(writer, sheet_name="malha_hidrica_resumo", index=False)
        ada_summary.to_excel(writer, sheet_name="ada_resumo", index=False)
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"xlsx": str(xlsx), "manifest": str(manifest)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera mini mapas espaciais funcionais exploratórios do GEOARC001.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Planilha de migração com coordenadas.")
    parser.add_argument("--group-table", default=str(DEFAULT_GROUP_TABLE), help="Planilha do produto 23.")
    parser.add_argument("--coordinate-reference", default=str(DEFAULT_COORD_REFERENCE), help="KMZ/KML com coordenadas oficiais dos pontos.")
    parser.add_argument("--hydrology-layer", action="append", default=None, help="Camada KML/KMZ de drenagem/talvegue. Pode ser usada mais de uma vez.")
    parser.add_argument("--no-hydrology", action="store_true", help="Nao desenha malha hidrica nos mini mapas.")
    parser.add_argument("--ada-layer", default=str(DEFAULT_ADA_LAYER), help="Camada KML/KMZ da ADA.")
    parser.add_argument("--no-ada", action="store_true", help="Nao desenha a ADA nos mini mapas.")
    parser.add_argument("--exclude-group", action="append", default=[], help="Codigo de grupo funcional a remover da figura. Pode ser usado mais de uma vez.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Pasta de saída exploratória.")
    parser.add_argument("--product-prefix", default="24", help="Prefixo numerico/textual dos arquivos de saida.")
    parser.add_argument("--client", default="default", help="Tema visual.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    group_table = Path(args.group_table)
    coordinate_reference = Path(args.coordinate_reference) if args.coordinate_reference else None
    output_dir = Path(args.output_dir)
    product_prefix = str(args.product_prefix).strip().rstrip("_")
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", args.client)

    coords, close_pairs, coord_variation = load_coordinates(source, coordinate_reference)
    exclude_groups = {str(group).strip() for group in args.exclude_group if str(group).strip()}
    annual, definitions = load_group_panel(group_table, coords, exclude_groups)
    if args.no_hydrology:
        hydrology_layers: list[Path] = []
    elif args.hydrology_layer:
        hydrology_layers = [Path(layer) for layer in args.hydrology_layer]
    else:
        hydrology_layers = DEFAULT_HYDROLOGY_LAYERS
    hydrology = load_hydrology(hydrology_layers)
    hydrology_summary = summarize_hydrology(hydrology)
    ada_layer = None if args.no_ada or not args.ada_layer else Path(args.ada_layer)
    ada = load_ada(ada_layer)
    ada_summary = summarize_ada(ada)
    out_png = output_dir / f"{product_prefix}_grafico_mini_mapas_funcoes_ecologicas_ano_ictiofauna.png"
    plot_spatial_mini_maps(annual, coords, hydrology, ada, out_png, theme)

    summary = {
        "source": str(source),
        "group_table": str(group_table),
        "output_dir": str(output_dir),
        "product_prefix": product_prefix,
        "figure": str(out_png),
        "points": int(coords["Ponto"].nunique()),
        "years": sorted(int(y) for y in annual["ano"].dropna().unique().tolist()),
        "groups": definitions[["codigo", "rotulo", "criterio"]].to_dict("records"),
        "excluded_groups": sorted(exclude_groups),
        "rows": int(len(annual)),
        "max_CPUEn_grupo_medio": float(annual["CPUEn_grupo_medio"].max()),
        "max_perc_CPUEn_medio": float(annual["perc_CPUEn_medio"].max()),
        "coordinate_reference": str(coordinate_reference) if coordinate_reference else None,
        "coordinate_strategy": "referencia_kmz" if coordinate_reference else "primeira_coordenada_valida_planilha",
        "hydrology_layers": [str(layer) for layer in hydrology_layers],
        "hydrology_features": int(hydrology[["fonte", "feature_id"]].drop_duplicates().shape[0]) if not hydrology.empty else 0,
        "hydrology_vertices": int(len(hydrology)),
        "ada_layer": str(ada_layer) if ada_layer else None,
        "ada_polygons": int(ada["polygon_id"].nunique()) if not ada.empty else 0,
        "ada_vertices": int(len(ada)),
        "close_pairs_under_1km": close_pairs[close_pairs["distancia_km"] < 1.0].to_dict("records"),
        "coordinate_note": "Mapa gerado com coordenadas oficiais do KMZ; a variacao das coordenadas da planilha foi mantida em diagnostico_variacao_coords.",
        "note": "Produto exploratório; não substitui os heatmaps temporais nem representa modelagem espacial.",
    }
    outputs = write_outputs(
        output_dir,
        product_prefix,
        annual,
        coords,
        definitions,
        close_pairs,
        coord_variation,
        hydrology_summary,
        ada_summary,
        summary,
    )
    summary["outputs"] = outputs
    (output_dir / f"{product_prefix}_manifesto_mini_mapas_funcoes_ecologicas_ictiofauna.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
