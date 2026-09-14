from __future__ import annotations

import hashlib
import json
import math
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from PIL import Image


DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
PROJECT_CODE = "BRAAEG001"
PRODUCT_STEM = "mini_mapa_cambevas_cpuen_ictiofauna"
PRODUCT_CODE = "mini_mapa_cambevas_cpuen"
HYDRO = "#8ED1F2"
GRID = "#E5E7EB"
GRAY = "#AEB7BC"
GREEN_DARK = "#0B4F12"
GREEN_LIGHT = "#10F20A"
SPECIES = ["Trichomycterus brasiliensis", "Trichomycterus immaculatus"]
SPECIES_LABELS = {
    "Trichomycterus brasiliensis": r"$\it{Trichomycterus\ brasiliensis}$",
    "Trichomycterus immaculatus": r"$\it{Trichomycterus\ immaculatus}$",
}
CAMPAIGNS = ["C001-2026-02-CH", "C002-2026-06-SC"]
LABEL_OFFSETS = {
    "PT_01": (-0.00055, 0.00065),
    "PT_02": (-0.00065, 0.00035),
    "PT_03": (0.00035, 0.00055),
    "PT_04": (-0.00120, 0.00092),
    "PT_05": (-0.00175, -0.00058),
    "PT_06": (0.00035, 0.00045),
    "PT_07": (0.00105, -0.00092),
    "PT_08": (-0.00155, 0.00052),
    "PT_09": (0.00078, -0.00092),
    "PT_10": (0.00045, 0.00055),
    "PT_11": (0.00055, -0.00055),
    "PT_12": (-0.00135, -0.00060),
}


def client_root() -> Path:
    base = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
    return next(path for path in base.iterdir() if path.is_dir() and path.name.startswith("A&G"))


CLIENT_ROOT = client_root()
OUTPUT_DIR = CLIENT_ROOT / "resultados" / "migracao_biota" / "ictiofauna"
LASTROS_DIR = CLIENT_ROOT / "resultados" / "migracao_biota" / "lastros_migracao"
AUDIT_DIR = Path("outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna")
KMZ_PATH = CLIENT_ROOT / "Geo" / "1AEMG002" / "Hidrografia.kmz"


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def point_key(point: str) -> tuple[int, str]:
    digits = "".join(ch for ch in str(point) if ch.isdigit())
    return (int(digits) if digits else 9999, str(point))


def point_label(point: str) -> str:
    return str(point).replace("_", "-")


def campaign_label(campaign: str) -> str:
    text = str(campaign).upper()
    if "02-CH" in text:
        return "C01-Chuva"
    if "06-SC" in text:
        return "C02-Seca"
    return str(campaign)


def load_hydro_lines() -> list[dict]:
    with zipfile.ZipFile(KMZ_PATH) as archive:
        kml = archive.read("doc.kml")
    root = ET.fromstring(kml)
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    lines: list[dict] = []
    for placemark in root.findall(".//k:Placemark", ns):
        name_el = placemark.find("k:name", ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else ""
        for geom in placemark.findall(".//k:LineString", ns):
            coords_el = geom.find(".//k:coordinates", ns)
            if coords_el is None or not coords_el.text:
                continue
            coords: list[tuple[float, float]] = []
            for token in coords_el.text.split():
                parts = token.split(",")
                if len(parts) < 2:
                    continue
                try:
                    coords.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
            if coords:
                lines.append({"name": name, "coords": coords})
    return lines


def source_workbook() -> Path:
    return next(LASTROS_DIR.glob("Resultados_Migra*_Ictio.xlsx"))


def load_cpuen() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source = source_workbook()
    points_raw = pd.read_excel(source, sheet_name="Pontos_e_Campanhas")
    efforts = pd.read_excel(source, sheet_name="Metadados_Esforco")
    results = pd.read_excel(source, sheet_name="Resultados_Ictiofauna")

    points = points_raw.rename(
        columns={"Ponto": "nome_ponto", "Campanha": "nome_campanha", "Latitude": "latitude", "Longitude": "longitude"}
    )
    points = points[points["nome_campanha"].isin(CAMPAIGNS)].copy()
    points["nome_ponto"] = points["nome_ponto"].astype(str).str.strip()
    points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
    points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
    point_coords = (
        points[["nome_ponto", "latitude", "longitude"]]
        .dropna()
        .drop_duplicates("nome_ponto")
        .sort_values("nome_ponto", key=lambda s: s.map(point_key))
        .reset_index(drop=True)
    )

    efforts = efforts.rename(
        columns={
            "Ponto": "nome_ponto",
            "Campanha": "nome_campanha",
            "Metodo_de_Captura": "metodo_de_captura",
            "Esforco": "esforco",
            "Unidade_Esforco": "unidade_esforco",
        }
    )
    results = results.rename(
        columns={
            "Ponto": "nome_ponto",
            "Campanha": "nome_campanha",
            "Metodo_de_Captura": "metodo_de_captura",
            "Nome_Cientifico": "nome_cientifico",
            "Numero_de_Individuos": "contagem",
        }
    )
    for frame in [efforts, results]:
        for col in ["nome_ponto", "nome_campanha", "metodo_de_captura"]:
            frame[col] = frame[col].astype(str).str.strip()
    results["nome_cientifico"] = results["nome_cientifico"].astype(str).str.strip()
    results["contagem"] = pd.to_numeric(results["contagem"], errors="coerce").fillna(0)
    efforts["esforco"] = pd.to_numeric(efforts["esforco"], errors="coerce")

    point_effort = (
        efforts[efforts["nome_campanha"].isin(CAMPAIGNS)]
        .dropna(subset=["esforco"])
        .drop_duplicates(["nome_campanha", "nome_ponto", "metodo_de_captura", "unidade_esforco", "esforco"])
        .groupby(["nome_campanha", "nome_ponto"], as_index=False)["esforco"]
        .sum()
        .rename(columns={"esforco": "esforco_total_ponto"})
    )
    target = results[results["nome_cientifico"].isin(SPECIES)].copy()
    target = (
        target.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], as_index=False)
        .agg(individuos=("contagem", "sum"))
        .merge(point_effort, on=["nome_campanha", "nome_ponto"], how="left")
    )
    target = target[target["esforco_total_ponto"].notna() & (target["esforco_total_ponto"] > 0)].copy()
    target["CPUEn"] = target["individuos"] / target["esforco_total_ponto"] * 100

    full_index = pd.MultiIndex.from_product(
        [CAMPAIGNS, point_coords["nome_ponto"].tolist(), SPECIES],
        names=["nome_campanha", "nome_ponto", "nome_cientifico"],
    ).to_frame(index=False)
    summary = (
        full_index.merge(target, on=["nome_campanha", "nome_ponto", "nome_cientifico"], how="left")
        .merge(point_coords, on="nome_ponto", how="left")
        .fillna({"individuos": 0, "CPUEn": 0})
    )
    summary["campanha_label"] = summary["nome_campanha"].map(campaign_label)
    summary["ponto_label"] = summary["nome_ponto"].map(point_label)
    return point_coords, summary, point_effort


def set_equal_aspect(ax: plt.Axes) -> None:
    ax.set_aspect(1 / math.cos(math.radians(-19.94)))


def symbol_size(value: float, max_value: float) -> float:
    if value <= 0 or max_value <= 0:
        return 42
    return 68 + 260 * math.sqrt(value / max_value)


def draw_panel(
    ax: plt.Axes,
    points: pd.DataFrame,
    local: pd.DataFrame,
    hydro_lines: list[dict],
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    norm: Normalize,
    cmap: LinearSegmentedColormap,
    max_cpuen: float,
) -> None:
    for line in hydro_lines:
        coords = np.asarray(line["coords"], dtype=float)
        if len(coords) == 0:
            continue
        if coords[:, 0].max() < xlim[0] or coords[:, 0].min() > xlim[1] or coords[:, 1].max() < ylim[0] or coords[:, 1].min() > ylim[1]:
            continue
        ax.plot(coords[:, 0], coords[:, 1], color=HYDRO, linewidth=0.38, alpha=0.70, zorder=1)

    symbol_offsets = {
        "PT_04": (-0.00022, 0.00010),
        "PT_07": (0.00025, -0.00010),
        "PT_08": (-0.00018, 0.00008),
        "PT_11": (0.00020, -0.00008),
    }

    local = points.merge(local[["nome_ponto", "CPUEn"]], on="nome_ponto", how="left").fillna({"CPUEn": 0})
    for _, row in local.iterrows():
        sx, sy = symbol_offsets.get(row["nome_ponto"], (0.0, 0.0))
        x_symbol = row["longitude"] + sx
        y_symbol = row["latitude"] + sy
        value = float(row["CPUEn"])
        if sx or sy:
            ax.plot([row["longitude"], x_symbol], [row["latitude"], y_symbol], color="#9CA3AF", linewidth=0.38, zorder=3)
        color = "white" if value <= 0 else cmap(norm(value))
        edge = GRAY if value <= 0 else "black"
        ax.scatter(
            x_symbol,
            y_symbol,
            s=symbol_size(value, max_cpuen),
            facecolor=color,
            edgecolor=edge,
            linewidth=0.65,
            alpha=0.94,
            zorder=4,
        )
    for _, row in points.iterrows():
        dx, dy = LABEL_OFFSETS.get(row["nome_ponto"], (0.0004, 0.0004))
        ax.annotate(
            point_label(row["nome_ponto"]),
            xy=(row["longitude"], row["latitude"]),
            xytext=(row["longitude"] + dx, row["latitude"] + dy),
            fontsize=5.7,
            color="#374151",
            arrowprops={"arrowstyle": "-", "color": "#9CA3AF", "lw": 0.35, "shrinkA": 0, "shrinkB": 2},
            bbox={"boxstyle": "round,pad=0.08", "fc": "white", "ec": "none", "alpha": 0.72},
            zorder=7,
        )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.grid(True, color=GRID, linewidth=0.42)
    set_equal_aspect(ax)
    for spine in ax.spines.values():
        spine.set_linewidth(0.7)
        spine.set_color("#30343B")
    ax.tick_params(axis="both", labelsize=5.2)


def plot_minimap(points: pd.DataFrame, summary: pd.DataFrame, hydro_lines: list[dict], out_png: Path) -> None:
    fig, axes = plt.subplots(
        len(CAMPAIGNS),
        len(SPECIES),
        figsize=A4_LANDSCAPE,
        dpi=DPI,
        sharex=True,
        sharey=True,
        squeeze=False,
    )
    all_lon = points["longitude"].to_numpy(dtype=float)
    all_lat = points["latitude"].to_numpy(dtype=float)
    pad_x = max((all_lon.max() - all_lon.min()) * 0.14, 0.002)
    pad_y = max((all_lat.max() - all_lat.min()) * 0.17, 0.002)
    xlim = (all_lon.min() - pad_x, all_lon.max() + pad_x)
    ylim = (all_lat.min() - pad_y, all_lat.max() + pad_y)
    max_cpuen = max(float(summary["CPUEn"].max()), 1.0)
    cmap = LinearSegmentedColormap.from_list("cpuen_cambevas", ["#CFE7C8", "#6A8F63", GREEN_DARK])
    norm = Normalize(vmin=0, vmax=max_cpuen)

    for row_idx, campaign in enumerate(CAMPAIGNS):
        for col_idx, species in enumerate(SPECIES):
            ax = axes[row_idx, col_idx]
            local = summary[(summary["nome_campanha"] == campaign) & (summary["nome_cientifico"] == species)]
            draw_panel(ax, points, local, hydro_lines, xlim, ylim, norm, cmap, max_cpuen)
            if row_idx == 0:
                ax.set_title(SPECIES_LABELS[species], fontweight="bold", fontsize=10.5, pad=7)
            if col_idx == 0:
                ax.text(
                    -0.18,
                    0.5,
                    campaign_label(campaign),
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    rotation=90,
                    fontsize=9,
                    fontweight="bold",
                )
            if row_idx == len(CAMPAIGNS) - 1:
                ax.set_xlabel("Longitude", fontsize=7)

    handles = [
        plt.Line2D([0], [0], color=HYDRO, lw=2, label="Hidrografia"),
        plt.Line2D([0], [0], marker="o", color=GRAY, markerfacecolor="white", markersize=5.2, lw=0, label="Sem registro"),
    ]
    size_values = [v for v in [0.5, 1.5, max_cpuen] if v <= max_cpuen + 1e-9]
    for value in size_values:
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="black",
                markerfacecolor=GREEN_DARK,
                markersize=max(4.8, math.sqrt(symbol_size(value, max_cpuen)) / 1.8),
                lw=0,
                label=f"CPUEn {value:.2f}",
            )
        )
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.07), ncol=len(handles), frameon=False, fontsize=7.1)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cax = fig.add_axes([0.39, 0.035, 0.22, 0.012])
    colorbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
    colorbar.set_label("CPUEn (ind/100 m²)", fontsize=7.0, labelpad=1)
    colorbar.ax.tick_params(labelsize=6, length=2)
    fig.subplots_adjust(left=0.085, right=0.99, bottom=0.17, top=0.91, wspace=0.08, hspace=0.12)
    fig.savefig(out_png, dpi=DPI, facecolor="white")
    plt.close(fig)


def image_info(path: Path) -> dict:
    with Image.open(path) as image:
        arr = np.asarray(image.convert("RGB"))
        return {
            "arquivo": path.name,
            "path": str(path),
            "tamanho_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "largura_px": int(image.size[0]),
            "altura_px": int(image.size[1]),
            "nonblank": bool(arr.std() > 0.5),
            "pixel_std": float(arr.std()),
        }


def main() -> int:
    tag = now_tag()
    hydro_lines = load_hydro_lines()
    points, summary, effort = load_cpuen()
    out_png = OUTPUT_DIR / f"15_{PRODUCT_STEM}.png"
    out_xlsx = OUTPUT_DIR / f"15_df_{PRODUCT_STEM}.xlsx"
    plot_minimap(points, summary, hydro_lines, out_png)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="cpuen_indicadores", index=False)
        effort.to_excel(writer, sheet_name="esforco_por_ponto", index=False)
        points.assign(ponto_label=points["nome_ponto"].map(point_label)).to_excel(writer, sheet_name="pontos", index=False)
        pd.DataFrame({"nome_cientifico": SPECIES}).to_excel(writer, sheet_name="taxons_indicadores", index=False)

    audit = {
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "group": "Ictiofauna",
        "product": PRODUCT_CODE,
        "source_workbook": str(source_workbook()),
        "hydro_kmz": str(KMZ_PATH),
        "hydro_lines": len(hydro_lines),
        "species": SPECIES,
        "max_cpuen": float(summary["CPUEn"].max()),
        "outputs": {
            "figure": image_info(out_png),
            "table": {
                "arquivo": out_xlsx.name,
                "path": str(out_xlsx),
                "sha256": sha256(out_xlsx),
                "tamanho_bytes": out_xlsx.stat().st_size,
            },
        },
        "notes": [
            "Produto em A4 paisagem, sem titulo geral, seguindo premissas dos minimapas de biota aquatica.",
            "CPUEn calculada como individuos da especie no ponto / esforco total quantitativo do ponto x 100.",
            "O esforco total inclui metodos quantitativos com ou sem captura, preservando a padronizacao da amostragem.",
            "Os taxons selecionados sao apresentados como organismos de interesse para leitura de integridade ambiental, sem diagnostico isolado de qualidade da agua.",
        ],
    }
    audit_path = AUDIT_DIR / f"{tag}_{PRODUCT_STEM}.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"audit_json": str(audit_path), **audit["outputs"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
