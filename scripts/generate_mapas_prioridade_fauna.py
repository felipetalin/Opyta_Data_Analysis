"""Gera mapas de prioridade para conservacao da fauna – PCH Senhora do Porto.

Fonte das prioridades: IDE-Sisema, geosservico WFS do ZEE-MG.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon
from matplotlib.backends.backend_pdf import PdfPages


GEO_DIR = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Plano de resgate\PT Fauna e Ictiofauna\Geo")
RESERVOIR_KML = GEO_DIR / "Reservatorio_PCH_Senhora_do_Porto.kml"
AMBIENTAL_KML = GEO_DIR / "Camadas_ambientais_PCH_Senhora_do_Porto.kml"
DATA_DIR = GEO_DIR / "camadas_IDE_Sisema"
WFS = "https://homologa.geoserver.meioambiente.mg.gov.br/wfs"
BBOX = (-43.08, -19.16, -42.78, -18.86)  # contexto cartografico de aproximadamente 30 km

LAYERS = {
    "Herpetofauna": "ide_2401_mg_prioridade_conservacao_herpetofauna_pol",
    "Mastofauna": "ide_2401_mg_prioridade_conservacao_mamiferos_pol",
    "Avifauna": "ide_2401_mg_prioridade_conservacao_avifauna_pol",
    "Ictiofauna": "ide_2401_mg_prioridade_conservacao_ictiofauna_pol",
}

COLORS = {
    "Muito baixa": "#58b9e6",
    "Baixa": "#b6e880",
    "Média": "#ffd23f",
    "Alta": "#f26522",
    "Muito alta": "#d7191c",
}
OFFICIAL_CLASSES = ("Baixa", "Média", "Alta", "Muito alta")
KML_NS = {"k": "http://www.opengis.net/kml/2.2"}


def coords(text: str):
    """Converte uma sequencia KML de lon,lat[,z] em tuplas lon/lat."""
    return [tuple(map(float, item.split(",")[:2])) for item in text.split()]


def reservoir_geometry():
    root = ET.parse(RESERVOIR_KML).getroot()
    node = root.find(".//k:Polygon/k:outerBoundaryIs/k:LinearRing/k:coordinates", KML_NS)
    return coords(node.text)


def hydrography():
    root = ET.parse(AMBIENTAL_KML).getroot()
    lines = []
    for folder in root.findall(".//k:Document/k:Folder", KML_NS):
        name = folder.findtext("k:name", default="", namespaces=KML_NS)
        if "Hidrog" not in name:
            continue
        for node in folder.findall(".//k:LineString/k:coordinates", KML_NS):
            lines.append(coords(node.text))
    return lines


def fetch_layer(label: str, typename: str):
    DATA_DIR.mkdir(exist_ok=True)
    output = DATA_DIR / f"{typename}.geojson"
    if output.exists() and output.stat().st_size > 100:
        return json.loads(output.read_text(encoding="utf-8"))
    bbox = ",".join(map(str, BBOX)) + ",EPSG:4674"
    url = (f"{WFS}?service=WFS&version=2.0.0&request=GetFeature"
           f"&typeNames=IDE:{typename}&outputFormat=application/json"
           f"&srsName=EPSG:4674&bbox={bbox}")
    result = subprocess.run(
        ["curl.exe", "-L", "--connect-timeout", "25", "--max-time", "180", "-sS", "-o", str(output), url],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode or not output.exists():
        raise RuntimeError(f"Falha ao obter {label}: {result.stderr.strip()}")
    return json.loads(output.read_text(encoding="utf-8"))


def norm_class(value):
    value = str(value).strip()
    # Mantem a escrita institucional, normalizando somente capitalizacao.
    return value[:1].upper() + value[1:].lower()


def rings(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    return []


def draw_priorities(ax, features):
    present = []
    for feat in features:
        category = norm_class(feat["properties"].get("indicador", "Sem classificação"))
        color = COLORS.get(category, "#d9d9d9")
        present.append(category)
        for ring in rings(feat["geometry"]):
            # As classes sao multipoligonos estaduais. Descartar aneis que nao
            # alcancam a moldura reduz muito o tempo de renderizacao.
            xs, ys = zip(*ring)
            if max(xs) < BBOX[0] or min(xs) > BBOX[2] or max(ys) < BBOX[1] or min(ys) > BBOX[3]:
                continue
            ax.add_patch(Polygon(ring, closed=True, facecolor=color, edgecolor="#ffffff", lw=0.22, alpha=0.82, zorder=2))
    return present


def draw_context(ax, reservoir, hydro):
    for line in hydro:
        xs, ys = zip(*line)
        ax.plot(xs, ys, color="#1e88c8", lw=0.55, alpha=0.78, zorder=4)
    ax.add_patch(Polygon(reservoir, closed=True, facecolor="#1379b8", edgecolor="#ffffff", lw=1.0, zorder=6))
    ax.set_xlim(BBOX[0], BBOX[2])
    ax.set_ylim(BBOX[1], BBOX[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_facecolor("#eef3ed")
    ax.grid(color="#ffffff", alpha=0.55, lw=0.45)
    ax.tick_params(labelsize=6, length=2)
    ax.set_xlabel("Longitude (°)", fontsize=6)
    ax.set_ylabel("Latitude (°)", fontsize=6)


def north_arrow(ax):
    x, y = 0.94, 0.91
    ax.annotate("N", xy=(x, y + 0.055), xycoords="axes fraction", ha="center", fontsize=8, fontweight="bold")
    ax.annotate("", xy=(x, y + 0.04), xytext=(x, y - 0.04), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", lw=1.1, color="#202020"))


def scale_bar(ax):
    km = 5
    lat = sum(ax.get_ylim()) / 2
    width = km / (111.32 * math.cos(math.radians(abs(lat))))
    x0 = BBOX[0] + 0.018
    y0 = BBOX[1] + 0.015
    ax.plot([x0, x0 + width], [y0, y0], color="#202020", lw=2.2, zorder=9)
    ax.plot([x0, x0], [y0 - 0.002, y0 + 0.002], color="#202020", lw=1.0, zorder=9)
    ax.plot([x0 + width, x0 + width], [y0 - 0.002, y0 + 0.002], color="#202020", lw=1.0, zorder=9)
    ax.text(x0 + width / 2, y0 + 0.005, "5 km", ha="center", fontsize=6, zorder=9)


def legend_handles(classes=None):
    # A legenda explicita o conjunto completo de classes oficial, ainda que
    # alguma classe nao ocorra na moldura escolhida para o empreendimento.
    return [Patch(facecolor=COLORS[x], edgecolor="#666", label=x) for x in OFFICIAL_CLASSES] + [
        Patch(facecolor="#1379b8", edgecolor="#fff", label="Reservatório PCH Senhora do Porto"),
        Patch(facecolor="#1e88c8", edgecolor="#1e88c8", label="Hidrografia"),
    ]


def footer(fig):
    fig.text(0.01, 0.012,
             f"Fonte: IDE-Sisema – ZEE-MG, camadas de prioridade para conservação (acesso em {date.today().strftime('%d/%m/%Y')}). "
             "Reservatório e hidrografia: arquivos do projeto. SRC: SIRGAS 2000 (EPSG:4674).",
             fontsize=6.5, color="#333333")


def save_panel(data, reservoir, hydro):
    order = ["Herpetofauna", "Mastofauna", "Avifauna"]
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 6.25), dpi=220, constrained_layout=False)
    all_classes = set()
    for ax, title in zip(axes, order):
        classes = draw_priorities(ax, data[title]["features"])
        all_classes.update(classes)
        draw_context(ax, reservoir, hydro)
        north_arrow(ax)
        scale_bar(ax)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    fig.suptitle("PRIORIDADE PARA CONSERVAÇÃO DA FAUNA TERRESTRE", fontsize=14, fontweight="bold", y=0.965)
    fig.legend(handles=legend_handles(all_classes), loc="lower center", ncol=7, fontsize=7,
               frameon=True, bbox_to_anchor=(0.5, 0.045))
    footer(fig)
    fig.subplots_adjust(left=0.04, right=0.99, top=0.89, bottom=0.18, wspace=0.18)
    base = GEO_DIR / "Mapa_prioridade_conservacao_fauna_terrestre_painel"
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def save_ictio(data, reservoir, hydro):
    fig, ax = plt.subplots(figsize=(10.5, 8.0), dpi=220)
    classes = draw_priorities(ax, data["Ictiofauna"]["features"])
    draw_context(ax, reservoir, hydro)
    north_arrow(ax)
    scale_bar(ax)
    ax.set_title("PRIORIDADE PARA CONSERVAÇÃO DA ICTIOFAUNA", fontsize=14, fontweight="bold", pad=12)
    ax.legend(handles=legend_handles(set(classes)), title="Legenda", title_fontsize=8, fontsize=7,
              loc="lower right", frameon=True)
    footer(fig)
    fig.tight_layout(rect=(0, 0.045, 1, 0.97))
    base = GEO_DIR / "Mapa_prioridade_conservacao_ictiofauna"
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def main():
    data = {name: fetch_layer(name, layer) for name, layer in LAYERS.items()}
    reservoir = reservoir_geometry()
    hydro = hydrography()
    save_panel(data, reservoir, hydro)
    save_ictio(data, reservoir, hydro)
    for name, layer in LAYERS.items():
        classes = sorted({norm_class(f["properties"].get("indicador", "Sem classificação")) for f in data[name]["features"]})
        print(f"{name}: {', '.join(classes)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise
