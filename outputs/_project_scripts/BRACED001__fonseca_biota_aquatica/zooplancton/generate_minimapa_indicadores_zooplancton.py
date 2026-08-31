from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine  # noqa: E402


PROJECT_ID = 133
DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
PRIMARY = "#11420C"
SECONDARY = "#6A8F63"
ACCENT = "#2D8C8C"
HYDRO = "#8ED1F2"
GRAY = "#AEB7BC"
GRID = "#E5E7EB"


CLIENT_ROOT = Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineração")
OUTPUT_DIR = CLIENT_ROOT / "Produtos" / "Resultados" / "Zooplancton"
OUTPUT_DIR = Path(os.environ.get("BRACED001_ZOO_OUTPUT_DIR", str(OUTPUT_DIR)))
AUDIT_DIR = Path("outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton")
KMZ_PATH = CLIENT_ROOT / "geo" / "Geo_Fonseca" / "Anteriores" / "Hidrografia - Fonseca.kmz"


ASSOCIATIONS = {
    "Ampla tolerância ecológica": {
        "color": PRIMARY,
        "taxa_label": r"$\it{Arcella}$ spp.; $\it{Difflugia}$ spp.; Bdelloida",
    },
    "Matéria orgânica": {
        "color": SECONDARY,
        "taxa_label": r"$\it{Centropyxis}$ spp.; $\it{Lesquereusia}$ spp.",
    },
    "Gradientes tróficos": {
        "color": ACCENT,
        "taxa_label": r"$\it{Bosmina\ freyi}$; $\it{Diaphanosoma\ birgei}$; Calanoida; Cyclopoida",
    },
}


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def point_label(name: str) -> str:
    return str(name).replace("_", "-")


def build_label_offsets(points: pd.DataFrame) -> dict[str, tuple[float, float]]:
    lon_span = max(float(points["longitude"].max() - points["longitude"].min()), 0.01)
    lat_span = max(float(points["latitude"].max() - points["latitude"].min()), 0.01)
    dx = max(lon_span * 0.052, 0.0035)
    dy = max(lat_span * 0.055, 0.0025)
    patterns = [(-dx, 0.0), (0.0, dy), (dx, -dy)]
    offsets: dict[str, tuple[float, float]] = {}
    work = points.copy()
    work["grupo"] = work["nome_ponto"].astype(str).str.rsplit("-", n=1).str[0]
    for _, group in work.sort_values("nome_ponto").groupby("grupo", sort=True):
        for index, point in enumerate(group["nome_ponto"].astype(str)):
            offsets[point] = patterns[index % len(patterns)]
    return offsets


def campaign_label(name: str) -> str:
    text = str(name).upper()
    if "03-CH" in text:
        return "C01-Chuva"
    if "06-SC" in text:
        return "C02-Seca"
    return str(name)


def load_hydro_lines() -> list[dict]:
    with zipfile.ZipFile(KMZ_PATH) as z:
        kml = z.read("doc.kml")
    root = ET.fromstring(kml)
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    lines: list[dict] = []
    for pm in root.findall(".//k:Placemark", ns):
        name_el = pm.find("k:name", ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else ""
        for geom in pm.findall(".//k:LineString", ns):
            coords_el = geom.find(".//k:coordinates", ns)
            if coords_el is None or not coords_el.text:
                continue
            coords: list[tuple[float, float]] = []
            for token in coords_el.text.split():
                parts = token.split(",")
                if len(parts) < 2:
                    continue
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                except ValueError:
                    continue
                coords.append((lon, lat))
            if coords:
                lines.append({"name": name, "coords": coords})
    return lines


def load_points_and_records() -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = get_engine()
    points = pd.read_sql(
        text(
            """
            select nome_ponto, latitude::float as latitude, longitude::float as longitude
            from public.pontos_coleta
            where id_projeto = :project_id
            group by nome_ponto, latitude, longitude
            order by nome_ponto
            """
        ),
        engine,
        params={"project_id": PROJECT_ID},
    )
    records = pd.read_sql(
        text(
            """
            select nome_campanha, nome_ponto, latitude::float as latitude, longitude::float as longitude,
                   nome_cientifico, filo, classe, ordem, familia, genero, tipo_amostragem, contagem
            from public.biota_analise_consolidada
            where id_projeto = :project_id
              and grupo_biologico like 'Zoopl%'
              and (
                genero in ('Arcella','Difflugia','Centropyxis','Lesquereusia','Lecane','Lepadella','Cephalodella')
                or nome_cientifico = 'Bdelloida'
                or nome_cientifico in ('Bosmina freyi','Diaphanosoma birgei')
                or ordem in ('Calanoida','Cyclopoida')
                or nome_cientifico ilike 'CALANOIDA%'
                or nome_cientifico ilike 'CYCLOPOIDA%'
              )
            order by nome_campanha, nome_ponto, nome_cientifico
            """
        ),
        engine,
        params={"project_id": PROJECT_ID},
    )
    return points, classify_records(records)


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        taxon = str(row["nome_cientifico"])
        genus = str(row.get("genero") or "").strip()
        order = str(row.get("ordem") or "").strip()
        groups: list[str] = []
        if genus in {"Arcella", "Difflugia"} or taxon == "Bdelloida":
            groups.append("Ampla tolerância ecológica")
        if genus in {"Centropyxis", "Lesquereusia"}:
            groups.append("Matéria orgânica")
        if taxon in {"Bosmina freyi", "Diaphanosoma birgei"} or order in {"Calanoida", "Cyclopoida"} or taxon.startswith(("CALANOIDA", "CYCLOPOIDA")):
            groups.append("Gradientes tróficos")
        for group in groups:
            out = row.to_dict()
            out["associacao_ecologica"] = group
            out["campanha_label"] = campaign_label(row["nome_campanha"])
            rows.append(out)
    return pd.DataFrame(rows)


def build_summary(records: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail = records.sort_values(["associacao_ecologica", "nome_campanha", "nome_ponto", "nome_cientifico"]).reset_index(drop=True)
    summary = (
        detail.groupby(["associacao_ecologica", "nome_campanha", "campanha_label", "nome_ponto", "latitude", "longitude"], dropna=False)
        .agg(
            riqueza=("nome_cientifico", "nunique"),
            taxons=("nome_cientifico", lambda s: "; ".join(sorted(set(map(str, s))))),
            registros=("nome_cientifico", "size"),
        )
        .reset_index()
    )
    summary["ponto_label"] = summary["nome_ponto"].map(point_label)
    return summary.sort_values(["associacao_ecologica", "nome_campanha", "nome_ponto"]).reset_index(drop=True), detail


def set_equal_aspect(ax) -> None:
    ax.set_aspect(1 / math.cos(math.radians(-19.94)))


def richness_class(value: float) -> tuple[str, str]:
    if value <= 0:
        return "Sem registro", "white"
    if value == 1:
        return "Riqueza = 1", "#CFE7C8"
    if value <= 3:
        return "Riqueza = 2-3", "#6A8F63"
    return "Riqueza ≥ 4", PRIMARY


def plot_minimap(points: pd.DataFrame, summary: pd.DataFrame, hydro_lines: list[dict], out_png: Path) -> Path:
    campaigns = sorted(summary["nome_campanha"].dropna().unique().tolist(), key=lambda x: campaign_label(x))
    associations = list(ASSOCIATIONS)
    fig, axes = plt.subplots(len(campaigns), len(associations), figsize=A4_LANDSCAPE, dpi=DPI, sharex=True, sharey=True)
    axes = np.asarray(axes)
    all_lon = points["longitude"].to_numpy(dtype=float)
    all_lat = points["latitude"].to_numpy(dtype=float)
    pad_x = max((all_lon.max() - all_lon.min()) * 0.14, 0.002)
    pad_y = max((all_lat.max() - all_lat.min()) * 0.17, 0.002)
    xlim = (all_lon.min() - pad_x, all_lon.max() + pad_x)
    ylim = (all_lat.min() - pad_y, all_lat.max() + pad_y)

    label_offsets = build_label_offsets(points)
    symbol_offsets = {
        "PT_04": (-0.00022, 0.00010),
        "PT_07": (0.00025, -0.00010),
        "PT_08": (-0.00018, 0.00008),
        "PT_11": (0.00020, -0.00008),
    }

    for row_idx, campaign in enumerate(campaigns):
        for col_idx, association in enumerate(associations):
            ax = axes[row_idx, col_idx]
            local = points.merge(
                summary[
                    (summary["associacao_ecologica"] == association)
                    & (summary["nome_campanha"] == campaign)
                ][["nome_ponto", "riqueza"]],
                on="nome_ponto",
                how="left",
            ).fillna({"riqueza": 0})
            for line in hydro_lines:
                coords = np.asarray(line["coords"], dtype=float)
                if len(coords) == 0:
                    continue
                if (
                    coords[:, 0].max() < xlim[0]
                    or coords[:, 0].min() > xlim[1]
                    or coords[:, 1].max() < ylim[0]
                    or coords[:, 1].min() > ylim[1]
                ):
                    continue
                ax.plot(coords[:, 0], coords[:, 1], color=HYDRO, linewidth=0.38, alpha=0.70, zorder=1)

            for _, row in local.iterrows():
                label, color = richness_class(float(row["riqueza"]))
                edge = GRAY if label == "Sem registro" else "black"
                sx, sy = symbol_offsets.get(row["nome_ponto"], (0.0, 0.0))
                x_symbol = row["longitude"] + sx
                y_symbol = row["latitude"] + sy
                if sx or sy:
                    ax.plot(
                        [row["longitude"], x_symbol],
                        [row["latitude"], y_symbol],
                        color="#9CA3AF",
                        linewidth=0.38,
                        zorder=3,
                    )
                ax.scatter(
                    x_symbol,
                    y_symbol,
                    s=70,
                    facecolor=color,
                    edgecolor=edge,
                    linewidth=0.65,
                    alpha=0.92,
                    zorder=4,
                )
                if row["riqueza"] > 0:
                    txt_color = "white" if float(row["riqueza"]) > 3 else "black"
                    ax.text(
                        x_symbol,
                        y_symbol,
                        str(int(row["riqueza"])),
                        ha="center",
                        va="center",
                        fontsize=4.9,
                        color=txt_color,
                        fontweight="bold",
                        zorder=6,
                    )
            for _, row in points.iterrows():
                dx, dy = label_offsets.get(row["nome_ponto"], (0.0004, 0.0004))
                horizontal_alignment = "right" if dx < 0 else "left" if dx > 0 else "center"
                ax.annotate(
                    point_label(row["nome_ponto"]),
                    xy=(row["longitude"], row["latitude"]),
                    xytext=(row["longitude"] + dx, row["latitude"] + dy),
                    ha=horizontal_alignment,
                    fontsize=5.2,
                    color="#374151",
                    arrowprops={"arrowstyle": "-", "color": "#9CA3AF", "lw": 0.35, "shrinkA": 0, "shrinkB": 2},
                    bbox={"boxstyle": "round,pad=0.08", "fc": "white", "ec": "none", "alpha": 0.72},
                    zorder=7,
                )
            if row_idx == 0:
                ax.set_title(association, fontweight="bold", fontsize=9.2, pad=7)
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
            if row_idx == len(campaigns) - 1:
                ax.set_xlabel("Longitude", fontsize=7)
                ax.text(
                    0.5,
                    -0.26,
                    ASSOCIATIONS[association]["taxa_label"],
                    transform=ax.transAxes,
                    ha="center",
                    va="top",
                    fontsize=5.4,
                    color="#374151",
                    wrap=True,
                )
            if col_idx == 0:
                ax.set_ylabel("")
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            ax.grid(True, color=GRID, linewidth=0.42)
            set_equal_aspect(ax)
            for spine in ax.spines.values():
                spine.set_linewidth(0.7)
                spine.set_color("#30343B")
            ax.tick_params(axis="both", labelsize=5.2)
    handles = [
        plt.Line2D([0], [0], color=HYDRO, lw=2, label="Hidrografia"),
        plt.Line2D([0], [0], marker="o", color=GRAY, markerfacecolor="white", markersize=5.6, lw=0, label="Sem registro"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#CFE7C8", markersize=5.6, lw=0, label="Riqueza = 1"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#6A8F63", markersize=5.6, lw=0, label="Riqueza = 2-3"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=PRIMARY, markersize=5.6, lw=0, label="Riqueza ≥ 4"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=5, frameon=False, fontsize=7.5)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.22, top=0.92, wspace=0.09, hspace=0.12)
    fig.savefig(out_png, dpi=DPI)
    plt.close(fig)
    return out_png


def image_info(path: Path) -> dict:
    with Image.open(path) as im:
        dpi = im.info.get("dpi") or (DPI, DPI)
        arr = np.asarray(im.convert("RGB"))
        return {
            "arquivo": path.name,
            "path": str(path),
            "tamanho_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "largura_px": int(im.size[0]),
            "altura_px": int(im.size[1]),
            "dpi_x": float(dpi[0]),
            "dpi_y": float(dpi[1]),
            "nonblank": bool(arr.std() > 0.5),
            "pixel_std": float(arr.std()),
        }


def main() -> int:
    tag = now_tag()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    hydro_lines = load_hydro_lines()
    points, records = load_points_and_records()
    summary, detail = build_summary(records)

    out_png = OUTPUT_DIR / "13_mini_mapa_taxons_bioindicadores_zooplancton.png"
    out_xlsx = OUTPUT_DIR / "13_df_mini_mapa_taxons_bioindicadores_zooplancton.xlsx"
    plot_minimap(points, summary, hydro_lines, out_png)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="resumo_por_ponto", index=False)
        detail.to_excel(writer, sheet_name="registros", index=False)
        points.assign(ponto_label=points["nome_ponto"].map(point_label)).to_excel(writer, sheet_name="pontos", index=False)
        pd.DataFrame(
            [
                {"associacao_ecologica": k, "taxons_representados": v["taxa_label"]}
                for k, v in ASSOCIATIONS.items()
            ]
        ).to_excel(writer, sheet_name="grupos", index=False)

    audit = {
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "project_id": PROJECT_ID,
        "group": "Zooplâncton",
        "product": "mini_mapa_taxons_bioindicadores",
        "hydro_kmz": str(KMZ_PATH),
        "hydro_lines": len(hydro_lines),
        "records": int(len(records)),
        "unique_taxa": int(records["nome_cientifico"].nunique()),
        "unique_points": int(records["nome_ponto"].nunique()),
        "associations": sorted(summary["associacao_ecologica"].unique().tolist()),
        "outputs": {
            "figure": image_info(out_png),
            "table": {"arquivo": out_xlsx.name, "path": str(out_xlsx), "sha256": sha256(out_xlsx), "tamanho_bytes": out_xlsx.stat().st_size},
        },
        "notes": [
            "Produto gerado para ilustrar ocorrência e riqueza de táxons associados à bioindicação/ecologia de ecossistemas aquáticos continentais.",
            "Mapa sem título geral, em A4 paisagem, seguindo as premissas do minimapa de Fitoplâncton.",
            "Círculos em tamanho fixo; a cor representa classe de riqueza, não densidade nem qualidade ambiental.",
            "A interpretação deve ser integrada à comunidade zooplanctônica, demais grupos da biota e variáveis físico-químicas.",
        ],
    }
    audit_path = AUDIT_DIR / f"{tag}_mini_mapa_taxons_bioindicadores_zooplancton.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"audit_json": str(audit_path), **audit["outputs"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
