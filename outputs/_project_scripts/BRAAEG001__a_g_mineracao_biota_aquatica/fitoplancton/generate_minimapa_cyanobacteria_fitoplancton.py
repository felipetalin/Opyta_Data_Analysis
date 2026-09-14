from __future__ import annotations

import json
import math
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine  # noqa: E402


PROJECT_ID = 195
DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
PRIMARY = "#11420C"
SECONDARY = "#81A65D"
ACCENT = "#2D8C8C"
HYDRO = "#8ED1F2"
GRAY = "#AEB7BC"


def client_root() -> Path:
    base = Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt")
    return next(p for p in base.iterdir() if p.is_dir() and p.name.startswith("A&G"))


CLIENT_ROOT = client_root()
OUTPUT_DIR = CLIENT_ROOT / "resultados" / "migracao_biota" / "fitoplancton"
AUDIT_DIR = Path("outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton")
KMZ_PATH = CLIENT_ROOT / "Geo" / "1AEMG002" / "Hidrografia.kmz"


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def campaign_label(name: str) -> str:
    if "02-CH" in name:
        return "C01-Chuva"
    if "06-SC" in name:
        return "C02-Seca"
    return str(name)


def point_label(name: str) -> str:
    return str(name).replace("_", "-")


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


def load_points_and_cyanobacteria() -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = get_engine()
    points = pd.read_sql(
        text(
            """
            select nome_ponto, latitude::float as latitude, longitude::float as longitude
            from public.pontos_coleta
            where id_projeto = :project_id and nome_ponto like 'PT_%'
            group by nome_ponto, latitude, longitude
            order by nome_ponto
            """
        ),
        engine,
        params={"project_id": PROJECT_ID},
    )
    cyano = pd.read_sql(
        text(
            """
            select nome_campanha, nome_ponto, latitude::float as latitude, longitude::float as longitude,
                   nome_cientifico, genero, tipo_amostragem, contagem
            from public.biota_analise_consolidada
            where id_projeto = :project_id
              and grupo_biologico ilike 'Fito%'
              and lower(filo) = 'cyanobacteria'
            order by nome_campanha, nome_ponto, nome_cientifico
            """
        ),
        engine,
        params={"project_id": PROJECT_ID},
    )
    return points, cyano


def build_summary(cyano: pd.DataFrame) -> pd.DataFrame:
    summary = (
        cyano.groupby(["nome_campanha", "nome_ponto", "latitude", "longitude"], dropna=False)
        .agg(
            campanha=("nome_campanha", "first"),
            ponto=("nome_ponto", "first"),
            riqueza=("nome_cientifico", "nunique"),
            densidade=("contagem", "sum"),
            taxons=("nome_cientifico", lambda s: "; ".join(sorted(set(map(str, s))))),
            generos=("genero", lambda s: "; ".join(sorted({str(v) for v in s if pd.notna(v) and str(v).strip()}))),
            registros=("nome_cientifico", "size"),
        )
        .reset_index()
    )
    summary["campanha_label"] = summary["campanha"].map(campaign_label)
    summary["ponto_label"] = summary["ponto"].map(point_label)
    return summary.sort_values(["campanha", "ponto"]).reset_index(drop=True)


def set_equal_aspect(ax) -> None:
    ax.set_aspect(1 / math.cos(math.radians(-19.94)))


def plot_minimap(points: pd.DataFrame, summary: pd.DataFrame, hydro_lines: list[dict], out_png: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=A4_LANDSCAPE, dpi=DPI, sharex=True, sharey=True)
    campaigns = sorted(summary["campanha"].unique().tolist())
    all_lon = points["longitude"].to_numpy(dtype=float)
    all_lat = points["latitude"].to_numpy(dtype=float)
    pad_x = max((all_lon.max() - all_lon.min()) * 0.12, 0.002)
    pad_y = max((all_lat.max() - all_lat.min()) * 0.15, 0.002)
    xlim = (all_lon.min() - pad_x, all_lon.max() + pad_x)
    ylim = (all_lat.min() - pad_y, all_lat.max() + pad_y)

    label_offsets = {
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

    for ax, campaign in zip(axes, campaigns):
        local = summary[summary["campanha"] == campaign].copy()
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
            ax.plot(coords[:, 0], coords[:, 1], color=HYDRO, linewidth=0.55, alpha=0.75, zorder=1)

        ax.scatter(
            points["longitude"],
            points["latitude"],
            s=22,
            facecolor="white",
            edgecolor=GRAY,
            linewidth=0.9,
            zorder=3,
        )
        colors = np.where(local["riqueza"].to_numpy(dtype=int) >= 2, PRIMARY, ACCENT)
        ax.scatter(
            local["longitude"],
            local["latitude"],
            s=210,
            facecolor=colors,
            edgecolor="black",
            linewidth=0.85,
            alpha=0.88,
            zorder=4,
        )
        for _, row in points.iterrows():
            dx, dy = label_offsets.get(row["nome_ponto"], (0.0004, 0.0004))
            ax.annotate(
                point_label(row["nome_ponto"]),
                xy=(row["longitude"], row["latitude"]),
                xytext=(row["longitude"] + dx, row["latitude"] + dy),
                fontsize=8.5,
                color="#374151",
                arrowprops={"arrowstyle": "-", "color": "#9CA3AF", "lw": 0.55, "shrinkA": 0, "shrinkB": 2},
                bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.72},
                zorder=5,
            )
        for _, row in local.iterrows():
            ax.text(
                row["longitude"],
                row["latitude"],
                str(int(row["riqueza"])),
                ha="center",
                va="center",
                fontsize=8.5,
                color="white",
                fontweight="bold",
                zorder=6,
            )
        ax.set_title(campaign_label(campaign), fontweight="bold", fontsize=16, pad=12)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.grid(True, color="#E5E7EB", linewidth=0.65)
        ax.set_xlabel("Longitude", fontsize=11)
        set_equal_aspect(ax)
        for spine in ax.spines.values():
            spine.set_linewidth(0.9)
            spine.set_color("#30343B")
        ax.tick_params(axis="both", labelsize=9)

    axes[0].set_ylabel("Latitude", fontsize=11)
    handles = [
        plt.Line2D([0], [0], color=HYDRO, lw=2, label="Hidrografia"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=ACCENT, markersize=9, lw=0, label="Riqueza = 1 táxon"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=PRIMARY, markersize=9, lw=0, label="Riqueza = 2 táxons"),
        plt.Line2D([0], [0], marker="o", color=GRAY, markerfacecolor="white", markersize=6, lw=0, label="Ponto sem registro"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.055), ncol=4, frameon=False, fontsize=10)
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.14, top=0.92, wspace=0.10)
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
    hydro_lines = load_hydro_lines()
    points, cyano = load_points_and_cyanobacteria()
    summary = build_summary(cyano)

    out_png = OUTPUT_DIR / "13_mini_mapa_cyanobacteria_fitoplancton.png"
    out_xlsx = OUTPUT_DIR / "13_df_mini_mapa_cyanobacteria_fitoplancton.xlsx"
    plot_minimap(points, summary, hydro_lines, out_png)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="cyanobacteria", index=False)
        points.assign(ponto_label=points["nome_ponto"].map(point_label)).to_excel(writer, sheet_name="pontos", index=False)

    audit = {
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "project_id": PROJECT_ID,
        "group": "Fitoplâncton",
        "product": "mini_mapa_cyanobacteria",
        "hydro_kmz": str(KMZ_PATH),
        "hydro_lines": len(hydro_lines),
        "records": int(len(cyano)),
        "point_campaign_occurrences": int(len(summary)),
        "unique_points": int(summary["ponto"].nunique()),
        "unique_taxa": int(cyano["nome_cientifico"].nunique()),
        "campaigns": sorted(summary["campanha_label"].unique().tolist()),
        "outputs": {
            "figure": image_info(out_png),
            "table": {"arquivo": out_xlsx.name, "path": str(out_xlsx), "sha256": sha256(out_xlsx), "tamanho_bytes": out_xlsx.stat().st_size},
        },
        "notes": [
            "Produto gerado para ilustrar ocorrência e riqueza de Cyanobacteria em Fitoplâncton.",
            "Mapa definitivo sem título; círculos em tamanho fixo porque apenas Anagnostidinema sp. possui valor quantitativo.",
            "A base possui 10 ocorrências ponto-campanha e 8 pontos únicos com registro de Cyanobacteria.",
            "O texto técnico deve evitar 'dez pontos amostrais' se a intenção for pontos únicos; usar 'dez ocorrências ponto-campanha' ou 'oito pontos amostrais'.",
        ],
    }
    audit_path = AUDIT_DIR / f"{tag}_mini_mapa_cyanobacteria_fitoplancton.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"audit_json": str(audit_path), **audit["outputs"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
