from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.geo_reference import read_kml_polygon_coordinates  # noqa: E402


BASE_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
ANALYTIC_XLSX = (
    BASE_DIR
    / "zoobentos_consolidated_analytic_base_20260721"
    / "base_analitica_consolidada_zoobentos_20260721.xlsx"
)
SUPPORT_DIR = BASE_DIR / "zoobentos_bioindicator_approval_20260721"
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos\Planilha Consolidada\Resultados e planilhas\Resultados bentos\Consolidado_2026"
)
AREA_CONTROL_LAYERS = [
    (
        "Area de controle 01",
        Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\771_area_controle_01_pl.kml"),
        "#18844a",
    ),
    (
        "Area de controle 02",
        Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\771_area_controle_02_pl.kml"),
        "#7a9a35",
    ),
]


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


def load_area_polygons() -> list[tuple[str, pd.DataFrame, str]]:
    layers = []
    for label, path, color in AREA_CONTROL_LAYERS:
        if not path.exists():
            continue
        poly = read_kml_polygon_coordinates(path)
        poly = poly[poly["ring_type"].eq("outer")].copy()
        layers.append((label, poly, color))
    return layers


def build_annual_metrics(point_campaign: pd.DataFrame) -> pd.DataFrame:
    df = point_campaign.copy()
    df["monitorado"] = df["Status_Monitoramento"].eq("Monitorado")
    monitored = df[df["monitorado"]].copy()
    metrics = (
        monitored.groupby(
            ["Ano_Temporal", "Ciclo_Temporal", "Ponto", "Area_Controle", "Latitude", "Longitude"],
            as_index=False,
        )
        .agg(
            campanhas_monitoradas=("Campanha", "nunique"),
            riqueza_media=("riqueza", "mean"),
            abundancia_total=("abundancia", "sum"),
            bmwp_medio=("bmwp_score", "mean"),
            bmwp_maximo=("bmwp_score", "max"),
            ept_abundancia=("ept_abundancia", "sum"),
            chol_abundancia=("chol_abundancia", "sum"),
        )
    )
    metrics["ept_percentual"] = np.where(
        metrics["abundancia_total"] > 0,
        100 * metrics["ept_abundancia"] / metrics["abundancia_total"],
        0,
    )
    metrics["chol_percentual"] = np.where(
        metrics["abundancia_total"] > 0,
        100 * metrics["chol_abundancia"] / metrics["abundancia_total"],
        0,
    )

    grid_cols = ["Ano_Temporal", "Ciclo_Temporal", "Ponto", "Area_Controle", "Latitude", "Longitude"]
    grid = df[grid_cols].drop_duplicates()
    out = grid.merge(metrics, on=grid_cols, how="left")
    out["Status_Monitoramento"] = np.where(out["campanhas_monitoradas"].fillna(0) > 0, "Monitorado", "Não monitorado")
    numeric_cols = [
        "campanhas_monitoradas",
        "riqueza_media",
        "abundancia_total",
        "bmwp_medio",
        "bmwp_maximo",
        "ept_abundancia",
        "chol_abundancia",
        "ept_percentual",
        "chol_percentual",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out.sort_values(["Ano_Temporal", "Ponto"]).reset_index(drop=True)


def plot_polygons(ax: plt.Axes, polygons: list[tuple[str, pd.DataFrame, str]]) -> None:
    for _, poly, color in polygons:
        for (_, _), ring in poly.groupby(["polygon_id", "ring_id"], sort=False):
            ax.plot(ring["Longitude"], ring["Latitude"], color=color, lw=1.2, alpha=0.75, zorder=1)


def annotate_points(ax: plt.Axes, data: pd.DataFrame) -> None:
    offsets = {
        "PIC-02": (-0.00115, 0.0007),
        "PIC-04": (-0.00115, -0.00045),
        "PIC-10": (-0.00055, 0.00025),
        "PIC-11": (0.00035, 0.00035),
    }
    for _, row in data.iterrows():
        point = str(row["Ponto"])
        dx, dy = offsets.get(point, (0.00015, 0.00015))
        ax.annotate(
            point.replace("PIC-", "P"),
            xy=(row["Longitude"], row["Latitude"]),
            xytext=(row["Longitude"] + dx, row["Latitude"] + dy),
            fontsize=7.4,
            color="#1f2933",
            arrowprops=dict(arrowstyle="-", lw=0.45, color="#6b7280") if point in offsets else None,
            ha="left",
            va="center",
            zorder=5,
        )


def plot_panel(annual: pd.DataFrame, output_png: Path) -> None:
    polygons = load_area_polygons()
    years = annual[["Ano_Temporal", "Ciclo_Temporal"]].drop_duplicates().sort_values("Ano_Temporal")
    indicators = [
        ("BMWP médio", "bmwp_medio", "YlGn", Normalize(0, max(1, float(annual["bmwp_medio"].max())))),
        ("%EPT", "ept_percentual", "Blues", Normalize(0, max(1, float(annual["ept_percentual"].max())))),
        ("%CHOL", "chol_percentual", "YlOrRd", Normalize(0, max(1, float(annual["chol_percentual"].max())))),
    ]

    lon_min = min(annual["Longitude"].min(), *(poly["Longitude"].min() for _, poly, _ in polygons)) - 0.001
    lon_max = max(annual["Longitude"].max(), *(poly["Longitude"].max() for _, poly, _ in polygons)) + 0.001
    lat_min = min(annual["Latitude"].min(), *(poly["Latitude"].min() for _, poly, _ in polygons)) - 0.001
    lat_max = max(annual["Latitude"].max(), *(poly["Latitude"].max() for _, poly, _ in polygons)) + 0.001

    fig, axes = plt.subplots(
        nrows=len(indicators),
        ncols=len(years),
        figsize=(16.5, 11.2),
        dpi=220,
        constrained_layout=False,
    )
    fig.subplots_adjust(left=0.065, right=0.9, top=0.92, bottom=0.09, wspace=0.12, hspace=0.18)

    for r, (label, col, cmap_name, norm) in enumerate(indicators):
        cmap = plt.get_cmap(cmap_name)
        for c, (_, year_row) in enumerate(years.iterrows()):
            ax = axes[r, c]
            year_data = annual[annual["Ano_Temporal"].eq(year_row["Ano_Temporal"])].copy()
            plot_polygons(ax, polygons)
            not_monitored = year_data[year_data["Status_Monitoramento"].eq("Não monitorado")]
            monitored = year_data[year_data["Status_Monitoramento"].eq("Monitorado")]
            ax.scatter(
                not_monitored["Longitude"],
                not_monitored["Latitude"],
                s=72,
                facecolor="#d1d5db",
                edgecolor="#6b7280",
                linewidth=0.7,
                zorder=2,
            )
            sc = ax.scatter(
                monitored["Longitude"],
                monitored["Latitude"],
                c=monitored[col],
                cmap=cmap,
                norm=norm,
                s=92,
                edgecolor="#25342b",
                linewidth=0.75,
                zorder=3,
            )
            annotate_points(ax, year_data)
            ax.set_xlim(lon_min, lon_max)
            ax.set_ylim(lat_min, lat_max)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color("#d5ddd6")
                spine.set_linewidth(0.8)
            if r == 0:
                ax.set_title(str(year_row["Ciclo_Temporal"]), fontsize=13, fontweight="bold", color="#1f2933", pad=8)
            if c == 0:
                ax.text(
                    -0.08,
                    0.5,
                    label,
                    transform=ax.transAxes,
                    rotation=90,
                    ha="center",
                    va="center",
                    fontsize=12.5,
                    fontweight="bold",
                    color="#1f2933",
                )
        cax = fig.add_axes([0.915, 0.69 - r * 0.292, 0.012, 0.18])
        cb = fig.colorbar(sc, cax=cax)
        cb.ax.tick_params(labelsize=8)
        cb.outline.set_linewidth(0.5)

    legend_handles = [
        Patch(facecolor="none", edgecolor="#18844a", label="Área de controle 01"),
        Patch(facecolor="none", edgecolor="#7a9a35", label="Área de controle 02"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#d1d5db", markeredgecolor="#6b7280", label="Não monitorado"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=10,
        bbox_to_anchor=(0.49, 0.035),
    )
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300)
    plt.close(fig)


def build(output_dir: Path, support_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    point_campaign = pd.read_excel(ANALYTIC_XLSX, sheet_name="ponto_campanha")
    annual = build_annual_metrics(point_campaign)

    out_png = output_dir / "APROVACAO_06_mini_mapas_anuais_bmwp_chol_ept_zoobentos.png"
    out_xlsx = output_dir / "APROVACAO_06_df_mini_mapas_anuais_bmwp_chol_ept_zoobentos.xlsx"
    plot_panel(annual, out_png)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        annual.to_excel(writer, sheet_name="indicadores_anuais_ponto", index=False)
        point_campaign.to_excel(writer, sheet_name="ponto_campanha", index=False)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": "BRAAVG002",
        "group": "Zoobentos",
        "product": "figura_modelo_bioindicadores",
        "method": {
            "BMWP": "media anual por ponto das campanhas monitoradas",
            "EPT": "percentual anual ponderado pela abundancia total do ponto",
            "CHOL": "percentual anual ponderado pela abundancia total do ponto",
            "not_monitored": "cinza quando nao ha campanha monitorada no ano temporal pela regra de vigencia",
        },
        "outputs": {"figure": out_png, "table": out_xlsx},
        "support_dir": support_dir,
    }
    manifest_path = support_dir / "manifesto_aprovacao_bioindicadores_zoobentos_20260721.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera figura-modelo de bioindicadores AVG Zoobentos.")
    parser.add_argument("--output-dir", type=Path, default=FINAL_DIR)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    args = parser.parse_args()
    manifest = build(args.output_dir, args.support_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
