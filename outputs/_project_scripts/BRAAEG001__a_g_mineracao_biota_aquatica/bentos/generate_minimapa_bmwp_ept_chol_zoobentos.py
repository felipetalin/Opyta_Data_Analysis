from __future__ import annotations

import hashlib
import json
import math
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
from matplotlib.colors import LinearSegmentedColormap, Normalize

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from opyta_analysis.pipelines.diagnostico.zoobentos import _load_zoobentos_df  # noqa: E402


PROJECT_ID = 195
PROJECT_CODE = "BRAAEG001"
GROUP = "Zoobentos"
DPI = 600
A4_LANDSCAPE = (11.69, 8.27)
HYDRO = "#8ED1F2"
GRID = "#E5E7EB"
GRAY = "#AEB7BC"
EPT_BLUE = "#2A6F97"
CHOL_RED = "#C1121F"
BMWP_CLASSES = [
    ("Muito boa", 86, np.inf, "#00b0f0"),
    ("Boa", 64, 85, "#92d050"),
    ("Regular", 37, 63, "#ffff00"),
    ("Ruim", 17, 36, "#ffc000"),
    ("Péssima", -np.inf, 16, "#ff0000"),
]
EPT_ORDERS = {"Ephemeroptera", "Plecoptera", "Trichoptera"}


def client_root() -> Path:
    base = Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt")
    return next(p for p in base.iterdir() if p.is_dir() and p.name.startswith("A&G"))


CLIENT_ROOT = client_root()
OUTPUT_DIR = CLIENT_ROOT / "resultados" / "migracao_biota" / "bentos"
AUDIT_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAEG001__a_g_mineracao_biota_aquatica" / "bentos"
KMZ_PATH = CLIENT_ROOT / "Geo" / "1AEMG002" / "Hidrografia.kmz"


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def point_key(point: str) -> tuple[int, str]:
    import re

    match = re.search(r"(\d+)", str(point))
    return (int(match.group(1)) if match else 999999, str(point))


def campaign_key(campaign: str) -> tuple[int, str]:
    import re

    match = re.match(r"^C0*(\d+)", str(campaign), flags=re.IGNORECASE)
    return (int(match.group(1)) if match else 999999, str(campaign))


def campaign_label(name: str) -> str:
    text = str(name).upper()
    import re

    match = re.match(r"^C0*(\d+)", str(name).strip(), flags=re.IGNORECASE)
    base = f"C{int(match.group(1)):02d}" if match else str(name)
    if "02-CH" in text or "CHUVA" in text:
        return f"{base}-Chuva"
    if "06-SC" in text or "SECA" in text:
        return f"{base}-Seca"
    return base


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


def clean_text(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "n.a.", "na"} else text


def is_ept(row: pd.Series) -> bool:
    return clean_text(row.get("ordem", "")) in EPT_ORDERS


def is_chol(row: pd.Series) -> bool:
    text = " ".join(str(row.get(col, "")) for col in ["nome_cientifico", "familia", "classe", "ordem"]).casefold()
    return "chironomidae" in text or "oligochaeta" in text or "oligoqueta" in text


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = _load_zoobentos_df(project_id=PROJECT_ID, group=GROUP, env_file=".env")
    if df.empty:
        raise RuntimeError("A fatia consolidada de Zoobentos retornou vazia.")
    df = df.copy()
    for col in ["nome_campanha", "nome_ponto", "nome_cientifico", "filo", "classe", "ordem", "familia", "genero"]:
        df[col] = df[col].astype(str).str.strip().replace({"None": "", "nan": "", "NaN": ""})
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0.0)
    df["bmwp_score"] = pd.to_numeric(df["bmwp_score"], errors="coerce").fillna(0.0)
    df["familia_bmwp"] = np.where(df["familia"].astype(str).str.strip() != "", df["familia"], df["nome_cientifico"])
    df["campanha_label"] = df["nome_campanha"].map(campaign_label)

    points = (
        df[["nome_ponto", "latitude", "longitude"]]
        .drop_duplicates()
        .assign(latitude=lambda x: pd.to_numeric(x["latitude"], errors="coerce"), longitude=lambda x: pd.to_numeric(x["longitude"], errors="coerce"))
        .sort_values("nome_ponto", key=lambda s: s.map(point_key))
        .reset_index(drop=True)
    )

    campaigns = sorted(df["nome_campanha"].unique().tolist(), key=campaign_key)
    point_names = points["nome_ponto"].tolist()
    rows = []
    details = []
    for campaign in campaigns:
        for point in point_names:
            local = df[(df["nome_campanha"] == campaign) & (df["nome_ponto"] == point)].copy()
            total = float(local["contagem"].sum()) if not local.empty else 0.0
            positive = local[local["contagem"] > 0].copy()
            family_scores = positive.groupby("familia_bmwp", dropna=False)["bmwp_score"].max() if not positive.empty else pd.Series(dtype=float)
            ept = positive[positive.apply(is_ept, axis=1)] if not positive.empty else positive
            chol = positive[positive.apply(is_chol, axis=1)] if not positive.empty else positive
            rows.append(
                {
                    "nome_campanha": campaign,
                    "campanha_label": campaign_label(campaign),
                    "nome_ponto": point,
                    "BMWP": float(family_scores.sum()) if not family_scores.empty else 0.0,
                    "EPT (%)": float(ept["contagem"].sum() / total * 100) if total > 0 and not ept.empty else 0.0,
                    "CHOL (%)": float(chol["contagem"].sum() / total * 100) if total > 0 and not chol.empty else 0.0,
                    "abundancia_total": total,
                    "familias_bmwp": int(len(family_scores)),
                    "riqueza_EPT": int(ept["nome_cientifico"].nunique()) if not ept.empty else 0,
                    "abundancia_EPT": float(ept["contagem"].sum()) if not ept.empty else 0.0,
                    "abundancia_CHOL": float(chol["contagem"].sum()) if not chol.empty else 0.0,
                }
            )
            for indicator, subset in [("EPT", ept), ("CHOL", chol)]:
                if subset.empty:
                    continue
                for _, item in subset.iterrows():
                    details.append({"indicador": indicator, **item.to_dict()})
    return points, pd.DataFrame(rows), pd.DataFrame(details)


def classify_bmwp(score: float) -> tuple[str, str]:
    value = float(score)
    for label, lower, upper, color in BMWP_CLASSES:
        if lower <= value <= upper:
            return label, color
    return "Péssima", "#ff0000"


def pct_color(value: float, base: str) -> str:
    value = float(value)
    if value <= 0:
        return "white"
    if value <= 25:
        return "#CFE7F3" if base == "ept" else "#F6C7C7"
    if value <= 50:
        return "#72A9C9" if base == "ept" else "#E56B6F"
    return EPT_BLUE if base == "ept" else CHOL_RED


def pct_label(value: float) -> str:
    value = float(value)
    return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"


def set_equal_aspect(ax) -> None:
    ax.set_aspect(1 / math.cos(math.radians(-19.94)))


def draw_panel(
    ax,
    points: pd.DataFrame,
    local: pd.DataFrame,
    hydro_lines: list[dict],
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    indicator: str,
    label_offsets: dict[str, tuple[float, float]],
    symbol_offsets: dict[str, tuple[float, float]],
) -> None:
    for line in hydro_lines:
        coords = np.asarray(line["coords"], dtype=float)
        if len(coords) == 0:
            continue
        if coords[:, 0].max() < xlim[0] or coords[:, 0].min() > xlim[1] or coords[:, 1].max() < ylim[0] or coords[:, 1].min() > ylim[1]:
            continue
        ax.plot(coords[:, 0], coords[:, 1], color=HYDRO, linewidth=0.38, alpha=0.70, zorder=1)

    local = points.merge(local, on="nome_ponto", how="left")
    for _, row in local.iterrows():
        sx, sy = symbol_offsets.get(row["nome_ponto"], (0.0, 0.0))
        x_symbol = row["longitude"] + sx
        y_symbol = row["latitude"] + sy
        if sx or sy:
            ax.plot([row["longitude"], x_symbol], [row["latitude"], y_symbol], color="#9CA3AF", linewidth=0.38, zorder=3)

        if indicator == "BMWP":
            value = float(row.get("BMWP", 0) or 0)
            _, color = classify_bmwp(value)
        elif indicator == "EPT":
            value = float(row.get("EPT (%)", 0) or 0)
            color = pct_color(value, "ept")
        else:
            value = float(row.get("CHOL (%)", 0) or 0)
            color = pct_color(value, "chol")
        edge = GRAY if color == "white" else "black"
        ax.scatter(x_symbol, y_symbol, s=72, facecolor=color, edgecolor=edge, linewidth=0.65, alpha=0.94, zorder=4)

    for _, row in points.iterrows():
        dx, dy = label_offsets.get(row["nome_ponto"], (0.0004, 0.0004))
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


def plot_minimap(points: pd.DataFrame, bio: pd.DataFrame, hydro_lines: list[dict], out_png: Path) -> Path:
    campaigns = sorted(bio["nome_campanha"].unique().tolist(), key=campaign_key)
    indicators = ["BMWP", "EPT", "CHOL"]
    fig, axes = plt.subplots(len(campaigns), len(indicators), figsize=A4_LANDSCAPE, dpi=DPI, sharex=True, sharey=True)
    axes = np.asarray(axes)

    all_lon = points["longitude"].to_numpy(dtype=float)
    all_lat = points["latitude"].to_numpy(dtype=float)
    pad_x = max((all_lon.max() - all_lon.min()) * 0.14, 0.002)
    pad_y = max((all_lat.max() - all_lat.min()) * 0.17, 0.002)
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
    symbol_offsets = {
        "PT_04": (-0.00022, 0.00010),
        "PT_07": (0.00025, -0.00010),
        "PT_08": (-0.00018, 0.00008),
        "PT_11": (0.00020, -0.00008),
    }

    for row_idx, campaign in enumerate(campaigns):
        for col_idx, indicator in enumerate(indicators):
            ax = axes[row_idx, col_idx]
            col = "BMWP" if indicator == "BMWP" else f"{indicator} (%)"
            local = bio[bio["nome_campanha"] == campaign][["nome_ponto", col]].copy()
            draw_panel(ax, points, local, hydro_lines, xlim, ylim, indicator, label_offsets, symbol_offsets)
            if row_idx == 0:
                title = "BMWP" if indicator == "BMWP" else f"{indicator} (%)"
                ax.set_title(title, fontweight="bold", fontsize=10.2, pad=7)
            if col_idx == 0:
                ax.text(-0.18, 0.5, campaign_label(campaign), transform=ax.transAxes, ha="center", va="center", rotation=90, fontsize=9, fontweight="bold")
            if row_idx == len(campaigns) - 1:
                ax.set_xlabel("Longitude", fontsize=7)

    handles = [
        plt.Line2D([0], [0], color=HYDRO, lw=2, label="Hidrografia"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#00b0f0", markersize=5.4, lw=0, label="BMWP muito boa"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#92d050", markersize=5.4, lw=0, label="BMWP boa"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#ffff00", markersize=5.4, lw=0, label="BMWP regular"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#ffc000", markersize=5.4, lw=0, label="BMWP ruim"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor="#ff0000", markersize=5.4, lw=0, label="BMWP péssima"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.078), ncol=6, frameon=False, fontsize=6.8)

    ept_cmap = LinearSegmentedColormap.from_list("ept_pct", ["#FFFFFF", "#CFE7F3", "#72A9C9", EPT_BLUE])
    chol_cmap = LinearSegmentedColormap.from_list("chol_pct", ["#FFFFFF", "#F6C7C7", "#E56B6F", CHOL_RED])
    norm = Normalize(vmin=0, vmax=100)
    sm_ept = plt.cm.ScalarMappable(cmap=ept_cmap, norm=norm)
    sm_chol = plt.cm.ScalarMappable(cmap=chol_cmap, norm=norm)
    sm_ept.set_array([])
    sm_chol.set_array([])
    cax_ept = fig.add_axes([0.36, 0.035, 0.11, 0.012])
    cax_chol = fig.add_axes([0.55, 0.035, 0.11, 0.012])
    cb1 = fig.colorbar(sm_ept, cax=cax_ept, orientation="horizontal", ticks=[0, 50, 100])
    cb2 = fig.colorbar(sm_chol, cax=cax_chol, orientation="horizontal", ticks=[0, 50, 100])
    cb1.ax.tick_params(labelsize=5.8, length=2)
    cb2.ax.tick_params(labelsize=5.8, length=2)
    cb1.set_label("EPT (%)", fontsize=6.5, labelpad=1)
    cb2.set_label("CHOL (%)", fontsize=6.5, labelpad=1)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.17, top=0.92, wspace=0.09, hspace=0.12)
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
    points, bio, details = load_data()
    out_png = OUTPUT_DIR / "16_mini_mapa_bmwp_ept_chol_zoobentos.png"
    out_xlsx = OUTPUT_DIR / "16_df_mini_mapa_bmwp_ept_chol_zoobentos.xlsx"
    plot_minimap(points, bio, hydro_lines, out_png)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        bio.to_excel(writer, sheet_name="indicadores_por_ponto", index=False)
        details.to_excel(writer, sheet_name="taxons_ept_chol", index=False)
        points.assign(ponto_label=points["nome_ponto"].map(point_label)).to_excel(writer, sheet_name="pontos", index=False)
        pd.DataFrame(BMWP_CLASSES, columns=["classe", "limite_inferior", "limite_superior", "cor"]).to_excel(writer, sheet_name="classes_bmwp", index=False)
    audit = {
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "project_id": PROJECT_ID,
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "product": "mini_mapa_bmwp_ept_chol",
        "hydro_kmz": str(KMZ_PATH),
        "hydro_lines": len(hydro_lines),
        "records": int(len(bio)),
        "campaigns": sorted(bio["campanha_label"].unique().tolist()),
        "points": int(points["nome_ponto"].nunique()),
        "outputs": {
            "figure": image_info(out_png),
            "table": {"arquivo": out_xlsx.name, "path": str(out_xlsx), "sha256": sha256(out_xlsx), "tamanho_bytes": out_xlsx.stat().st_size},
        },
        "notes": [
            "Produto complementar em A4 paisagem, com BMWP, EPT e CHOL no mesmo painel.",
            "Linhas separam C01-Chuva e C02-Seca; colunas separam os indicadores.",
            "BMWP usa as cores originais de classe do indicador; EPT e CHOL usam classes visuais de percentual.",
            "Círculos sem valores internos para reduzir poluição visual; BMWP indicado por classe e EPT/CHOL por escala percentual.",
        ],
    }
    audit_path = AUDIT_DIR / f"{tag}_mini_mapa_bmwp_ept_chol_zoobentos.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"audit_json": str(audit_path), **audit["outputs"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
