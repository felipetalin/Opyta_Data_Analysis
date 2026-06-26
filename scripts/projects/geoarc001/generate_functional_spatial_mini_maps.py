from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import load_theme
from opyta_analysis.geo_reference import read_kml_point_coordinates, standardize_point_name


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
    number = _point_number(point)
    return f"IC-{number:02d}" if number < 999999 else str(point)


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


def load_group_panel(group_table: Path, coords: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not group_table.exists():
        raise FileNotFoundError(f"Tabela do produto 23 não encontrada: {group_table}")
    panel = pd.read_excel(group_table, sheet_name="heatmap_funcoes")
    definitions = pd.read_excel(group_table, sheet_name="definicoes_funcoes")
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


def plot_spatial_mini_maps(annual: pd.DataFrame, coords: pd.DataFrame, out_png: Path, theme: dict) -> None:
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
        figsize=(15.5, 11.8),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
    )
    if nrows == 1:
        axes = np.array([axes])
    xmin, xmax, ymin, ymax = _point_limits(coords)
    vmax_color = 100.0
    vmax_size = max(float(annual["CPUEn_grupo_medio"].max()), 1.0)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "geoarc_spatial_functional", ["#F7F7F7", "#D9E6F2", "#8DBFD2", primary]
    )
    norm = mcolors.Normalize(vmin=0, vmax=vmax_color)

    for row_idx, group in enumerate(groups):
        for col_idx, year in enumerate(years):
            ax = axes[row_idx, col_idx]
            data = annual[(annual["grupo_funcional"] == group["grupo_funcional"]) & (annual["ano"] == year)].copy()
            data = data.sort_values("nome_ponto", key=lambda s: s.map(_point_sort_key))
            ax.scatter(
                coords["Longitude"],
                coords["Latitude"],
                s=10,
                color="#E4E8EE",
                edgecolor="#AAB2BD",
                linewidth=0.35,
                zorder=1,
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
        "Cor = participação média do grupo no CPUEn total do ponto/ano; bolhas maiores indicam maior CPUEn médio anual absoluto do grupo. Rótulos abreviados IC-XX; produto exploratório.",
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
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"xlsx": str(xlsx), "manifest": str(manifest)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera mini mapas espaciais funcionais exploratórios do GEOARC001.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Planilha de migração com coordenadas.")
    parser.add_argument("--group-table", default=str(DEFAULT_GROUP_TABLE), help="Planilha do produto 23.")
    parser.add_argument("--coordinate-reference", default=str(DEFAULT_COORD_REFERENCE), help="KMZ/KML com coordenadas oficiais dos pontos.")
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
    annual, definitions = load_group_panel(group_table, coords)
    out_png = output_dir / f"{product_prefix}_grafico_mini_mapas_funcoes_ecologicas_ano_ictiofauna.png"
    plot_spatial_mini_maps(annual, coords, out_png, theme)

    summary = {
        "source": str(source),
        "group_table": str(group_table),
        "output_dir": str(output_dir),
        "product_prefix": product_prefix,
        "figure": str(out_png),
        "points": int(coords["Ponto"].nunique()),
        "years": sorted(int(y) for y in annual["ano"].dropna().unique().tolist()),
        "groups": definitions[["codigo", "rotulo", "criterio"]].to_dict("records"),
        "rows": int(len(annual)),
        "max_CPUEn_grupo_medio": float(annual["CPUEn_grupo_medio"].max()),
        "max_perc_CPUEn_medio": float(annual["perc_CPUEn_medio"].max()),
        "coordinate_reference": str(coordinate_reference) if coordinate_reference else None,
        "coordinate_strategy": "referencia_kmz" if coordinate_reference else "primeira_coordenada_valida_planilha",
        "close_pairs_under_1km": close_pairs[close_pairs["distancia_km"] < 1.0].to_dict("records"),
        "coordinate_note": "Mapa gerado com coordenadas oficiais do KMZ; a variacao das coordenadas da planilha foi mantida em diagnostico_variacao_coords.",
        "note": "Produto exploratório; não substitui os heatmaps temporais nem representa modelagem espacial.",
    }
    outputs = write_outputs(output_dir, product_prefix, annual, coords, definitions, close_pairs, coord_variation, summary)
    summary["outputs"] = outputs
    (output_dir / f"{product_prefix}_manifesto_mini_mapas_funcoes_ecologicas_ictiofauna.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
