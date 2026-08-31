from __future__ import annotations

import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
import numpy as np
import pandas as pd


BIOS_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios")
COLIDER_ROOT = next(path for path in BIOS_ROOT.iterdir() if path.is_dir() and path.name.startswith("Col"))
JUNE_ROOT = COLIDER_ROOT / "Resultados" / "2026" / "Junho-2026"
OFFICIAL_ROOT = JUNE_ROOT / "BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02"
EXPLORATORY_ROOT = JUNE_ROOT / "BIOCOL001_ANALISES_EXPLORATORIAS_R01"
SOURCE_WORKBOOK = (
    COLIDER_ROOT
    / "Planilha"
    / "Migracao"
    / "Opyta-Bios-Ictio-2026_MIGRACAO_DE DADOS -version 4.xlsx"
)
SPATIAL_WORKBOOK = OFFICIAL_ROOT / "05_05_distribuicao_espacial_riqueza_abundancia.xlsx"
PROJECT_ROOT = (
    Path(r"G:\Meu Drive\Opyta\Opyta_Data_Analysis")
    / "outputs"
    / "_project_scripts"
    / "BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider"
)
SECTION_LAYER = PROJECT_ROOT / "inventory" / "camada_trechos_longitudinais_biocol001.csv"
KMZ_PATH = COLIDER_ROOT / "Geo" / "UHE_Colider_reservatorio_malha_hidrica.kmz"
OUTPUTS = {
    "riqueza": OFFICIAL_ROOT / "05_05_1_mapa_riqueza_espacial.png",
    "abundancia": OFFICIAL_ROOT / "05_05_2_mapa_abundancia_espacial.png",
    "biomassa": OFFICIAL_ROOT / "05_05_3_mapa_biomassa_espacial.png",
    "ameacadas_riqueza": OFFICIAL_ROOT / "05_03_1_mapa_riqueza_ameacadas_espacial.png",
    "ameacadas_abundancia": OFFICIAL_ROOT / "05_03_2_mapa_abundancia_ameacadas_espacial.png",
    "cpuen": OFFICIAL_ROOT / "05_07_7_mapa_cpuen_espacial.png",
    "cpueb": OFFICIAL_ROOT / "05_07_8_mapa_cpueb_espacial.png",
    "shannon": OFFICIAL_ROOT / "05_08_3_mapa_diversidade_shannon_espacial.png",
    "pielou": OFFICIAL_ROOT / "05_08_4_mapa_equitabilidade_pielou_espacial.png",
    "reproducao_femeas": OFFICIAL_ROOT / "05_12_3_mapa_femeas_reprodutivas_espacial.png",
    "reproducao_machos": OFFICIAL_ROOT / "05_12_4_mapa_machos_reprodutivos_espacial.png",
    "recrutamento_mld": OFFICIAL_ROOT / "05_15_3_mapa_recrutamento_mld_espacial.png",
}

PRIMARY = "#002060"
SECONDARY = "#5B9BD5"
ORANGE = "#D4672A"
GRID = "#D9D9D9"
EDGE = "#333333"
SECTION_COLORS = {"Montante": PRIMARY, "Jusante": ORANGE}
BUBBLE_COLOR = "#8CC4E8"
RESERVOIR_COLOR = "#B7DDE8"
MAIN_RIVER_COLOR = "#43A6C6"
TRIBUTARY_COLOR = "#8FD3D1"
DAM_COLOR = "#F2C80F"

LABEL_OFFSETS = {
    "ICTIO01": (-18, -16),
    "ICTIO02": (0, 17),
    "ICTIO03": (-4, 17),
    "ICTIO04": (0, 17),
    "ICTIO05": (0, 17),
    "ICTIO06": (-20, -18),
    "ICTIO07": (-18, 18),
    "ICTIO08": (22, -15),
    "ICTIO09": (0, 18),
    "ICTIO10": (0, -21),
    "ICTIO11": (0, -23),
    "ICTIO12": (-5, 28),
    "ICTIO13A": (-48, -18),
    "ICTIO13B": (-34, 24),
    "ICTIO14": (-34, 18),
    "ICTIO15": (34, -17),
}


def load_data() -> pd.DataFrame:
    summary = pd.read_excel(SPATIAL_WORKBOOK, sheet_name="Resumo_pontos")
    coordinates = pd.read_excel(SOURCE_WORKBOOK, sheet_name="Pontos_e_Campanhas")
    coordinates = coordinates[["Ponto", "Latitude", "Longetude"]].drop_duplicates("Ponto")
    coordinates = coordinates.rename(
        columns={"Ponto": "ponto", "Latitude": "latitude", "Longetude": "longitude"}
    )
    for column in ["latitude", "longitude"]:
        coordinates[column] = (
            coordinates[column].astype(str).str.replace(",", ".", regex=False).astype(float)
        )
    sections = pd.read_csv(SECTION_LAYER)
    data = summary.merge(coordinates, on="ponto", how="left", validate="one_to_one")
    data = data.merge(sections, on="ponto", how="left", validate="one_to_one")
    if data[["latitude", "longitude", "trecho_longitudinal", "ordem_lista"]].isna().any().any():
        raise ValueError("Pontos do produto 5.5 sem coordenada, trecho ou ordem espacial.")
    if set(data["ponto"]) != set(sections["ponto"]):
        raise ValueError("A camada longitudinal e o universo espacial 5.5 nao reconciliam.")
    return data.sort_values("ordem_lista").reset_index(drop=True)


def metric_frame(
    base: pd.DataFrame,
    source: pd.DataFrame,
    point_column: str,
    value_column: str,
    transform: float = 1.0,
) -> pd.DataFrame:
    values = source[[point_column, value_column]].rename(
        columns={point_column: "ponto", value_column: "valor"}
    )
    values["valor"] = pd.to_numeric(values["valor"], errors="coerce") * transform
    output = base.drop(columns=["riqueza", "abundancia", "biomassa_g", "campanhas_amostradas"]).merge(
        values, on="ponto", how="left", validate="one_to_one"
    )
    if output["valor"].isna().any():
        missing = output.loc[output["valor"].isna(), "ponto"].tolist()
        raise ValueError(f"Metrica espacial sem valor para: {missing}")
    return output


def load_metric_specs(base: pd.DataFrame) -> dict[str, dict[str, object]]:
    threatened = pd.read_excel(
        OFFICIAL_ROOT / "05_03_tabela_especies_ameacadas.xlsx", sheet_name="Variacao_espacial"
    )
    cpue = pd.read_excel(
        OFFICIAL_ROOT / "05_07_captura_unidade_esforco.xlsx", sheet_name="CPUEn_CPUEb_trecho"
    )
    diversity = pd.read_excel(
        OFFICIAL_ROOT / "05_08_dados_diversidade_equitabilidade.xlsx", sheet_name="Geral_por_ponto"
    )
    reproduction = pd.read_excel(
        OFFICIAL_ROOT / "05_12_processo_reprodutivo.xlsx", sheet_name="Migradoras_reprod_espacial"
    )
    recruitment = pd.read_excel(
        OFFICIAL_ROOT / "05_15_recrutamento_mld_auditoria.xlsx",
        sheet_name="Juvenis_MLD_espacial",
    )

    common = {
        "riqueza": {
            "data": metric_frame(base, base, "ponto", "riqueza"),
            "legend": "Riqueza acumulada (nº de espécies)",
            "decimals": 0,
        },
        "abundancia": {
            "data": metric_frame(base, base, "ponto", "abundancia"),
            "legend": "Abundância acumulada (nº de indivíduos)",
            "decimals": 0,
        },
        "biomassa": {
            "data": metric_frame(base, base, "ponto", "biomassa_g", transform=0.001),
            "legend": "Biomassa acumulada (kg)",
            "decimals": 1,
        },
        "ameacadas_riqueza": {
            "data": metric_frame(base, threatened, "Ponto", "Riqueza_ameacadas"),
            "legend": "Riqueza acumulada de espécies ameaçadas (nº de espécies)",
            "decimals": 0,
        },
        "ameacadas_abundancia": {
            "data": metric_frame(base, threatened, "Ponto", "Abundancia_total"),
            "legend": "Abundância acumulada de espécies ameaçadas (nº de indivíduos)",
            "decimals": 0,
        },
        "cpuen": {
            "data": metric_frame(base, cpue, "ponto", "CPUEn_media"),
            "legend": "CPUEn média (ind./100 m² de rede)",
            "decimals": 1,
        },
        "cpueb": {
            "data": metric_frame(base, cpue, "ponto", "CPUEb_kg_media"),
            "legend": "CPUEb média (kg/100 m² de rede)",
            "decimals": 1,
        },
        "shannon": {
            "data": metric_frame(base, diversity, "ponto", "Shannon_H"),
            "legend": "Diversidade de Shannon (H')",
            "decimals": 2,
        },
        "pielou": {
            "data": metric_frame(base, diversity, "ponto", "Pielou_J"),
            "legend": "Equitabilidade de Pielou (J')",
            "decimals": 2,
        },
        "reproducao_femeas": {
            "data": metric_frame(base, reproduction, "ponto", "Femeas_reprodutivas"),
            "legend": "Fêmeas migradoras reprodutivas MLD (nº de indivíduos; EMG F3-F4)",
            "decimals": 0,
        },
        "reproducao_machos": {
            "data": metric_frame(base, reproduction, "ponto", "Machos_reprodutivos"),
            "legend": "Machos migradores reprodutivos MLD (nº de indivíduos; EMG M3-M4)",
            "decimals": 0,
        },
        "recrutamento_mld": {
            "data": metric_frame(base, recruitment, "ponto", "Total_juvenis_MLD"),
            "legend": "Recrutamento MLD acumulado (nº de juvenis)",
            "decimals": 0,
        },
    }
    return common


def parse_coordinates(text: str | None) -> list[tuple[float, float]]:
    coordinates = []
    for token in (text or "").split():
        parts = token.split(",")
        if len(parts) >= 2:
            coordinates.append((float(parts[0]), float(parts[1])))
    return coordinates


def load_cartography() -> dict[str, object]:
    namespace = {"k": "http://www.opengis.net/kml/2.2"}
    with zipfile.ZipFile(KMZ_PATH) as archive:
        root = ET.fromstring(archive.read("doc.kml"))

    reservoir_outer: list[tuple[float, float]] = []
    reservoir_holes: list[list[tuple[float, float]]] = []
    main_river: list[list[tuple[float, float]]] = []
    tributaries: list[list[tuple[float, float]]] = []
    dam: tuple[float, float] | None = None

    for placemark in root.findall(".//k:Placemark", namespace):
        style = (placemark.findtext("k:styleUrl", default="", namespaces=namespace) or "").strip()
        if style == "#reservatorio":
            outer = placemark.find(".//k:outerBoundaryIs//k:coordinates", namespace)
            reservoir_outer = parse_coordinates(outer.text if outer is not None else None)
            reservoir_holes = [
                parse_coordinates(element.text)
                for element in placemark.findall(".//k:innerBoundaryIs//k:coordinates", namespace)
            ]
        elif style in {"#rioPrincipal", "#tributario"}:
            target = main_river if style == "#rioPrincipal" else tributaries
            for element in placemark.findall(".//k:LineString/k:coordinates", namespace):
                line = parse_coordinates(element.text)
                if len(line) >= 2:
                    target.append(line)
        elif style == "#barragem":
            element = placemark.find(".//k:Point/k:coordinates", namespace)
            coordinates = parse_coordinates(element.text if element is not None else None)
            dam = coordinates[0] if coordinates else None

    if not reservoir_outer or not main_river or not tributaries or dam is None:
        raise ValueError("O KMZ nao possui reservatorio, rio principal, tributarios e barragem completos.")
    return {
        "reservoir_outer": reservoir_outer,
        "reservoir_holes": reservoir_holes,
        "main_river": main_river,
        "tributaries": tributaries,
        "dam": dam,
    }


def point_limits(data: pd.DataFrame) -> tuple[float, float, float, float]:
    xmin, xmax = float(data["longitude"].min()), float(data["longitude"].max())
    ymin, ymax = float(data["latitude"].min()), float(data["latitude"].max())
    dx, dy = xmax - xmin, ymax - ymin
    return xmin - dx * 0.12, xmax + dx * 0.12, ymin - dy * 0.18, ymax + dy * 0.18


def style_axes(ax: plt.Axes) -> None:
    ax.grid(axis="both", color=GRID, alpha=0.35, linewidth=1.0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.1)


def draw_labels(ax: plt.Axes, data: pd.DataFrame) -> None:
    for row in data.itertuples(index=False):
        dx, dy = LABEL_OFFSETS.get(row.ponto, (7, 6))
        ax.annotate(
            row.ponto,
            (row.longitude, row.latitude),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=9.5,
            fontweight="bold",
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.14", "facecolor": "white", "alpha": 0.78, "edgecolor": "none"},
            arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.75, "alpha": 0.72, "shrinkA": 0, "shrinkB": 3},
            zorder=7,
        )


def draw_cartography(ax: plt.Axes, cartography: dict[str, object]) -> None:
    ax.add_patch(
        Polygon(
            cartography["reservoir_outer"],
            closed=True,
            facecolor=RESERVOIR_COLOR,
            edgecolor=MAIN_RIVER_COLOR,
            linewidth=0.9,
            alpha=0.72,
            zorder=0.8,
        )
    )
    for hole in cartography["reservoir_holes"]:
        ax.add_patch(
            Polygon(hole, closed=True, facecolor="white", edgecolor=MAIN_RIVER_COLOR, linewidth=0.35, zorder=0.9)
        )
    for line in cartography["tributaries"]:
        x, y = zip(*line)
        ax.plot(x, y, color=TRIBUTARY_COLOR, linewidth=0.65, alpha=0.70, zorder=0.4)
    for line in cartography["main_river"]:
        x, y = zip(*line)
        ax.plot(x, y, color=MAIN_RIVER_COLOR, linewidth=1.35, alpha=0.90, zorder=1.0)
    dam_x, dam_y = cartography["dam"]
    ax.scatter(
        [dam_x],
        [dam_y],
        marker="D",
        s=75,
        facecolor=DAM_COLOR,
        edgecolor="#3F3F3F",
        linewidth=1.0,
        zorder=6,
    )


def draw_metric_panel(
    ax: plt.Axes,
    data: pd.DataFrame,
    cartography: dict[str, object],
    legend_title: str,
    decimals: int,
) -> None:
    draw_cartography(ax, cartography)
    draw_labels(ax, data)
    values = data["valor"].astype(float)
    minimum = float(values.min())
    maximum = float(data["valor"].max())
    positive = values[values > 0]
    positive_minimum = float(positive.min()) if not positive.empty else 0.0
    positive_span = max(maximum - positive_minimum, 1.0)

    def size_for(value: float) -> float:
        if value <= 0:
            return 0.0
        relative = (value - positive_minimum) / positive_span
        return 85 + 560 * math.sqrt(max(relative, 0.0))

    sizes = values.map(size_for).to_numpy()
    ax.scatter(
        data["longitude"],
        data["latitude"],
        s=sizes,
        facecolors=BUBBLE_COLOR,
        edgecolors=data["trecho_longitudinal"].map(SECTION_COLORS),
        linewidths=2.2,
        alpha=0.88,
        zorder=3,
    )
    xmin, xmax, ymin, ymax = point_limits(data)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("N")
    style_axes(ax)

    if positive.empty:
        legend_values = [0.0]
    else:
        candidates = [positive_minimum, float(positive.median()), maximum]
        legend_values = list(dict.fromkeys(candidates))
    legend_sizes = [math.sqrt(size_for(value)) for value in legend_values]
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=BUBBLE_COLOR,
            markeredgecolor=EDGE,
            markeredgewidth=0.8,
            markersize=size,
            alpha=0.88,
            label=(f"≈ {value:,.{decimals}f}" if decimals else f"≈ {value:,.0f}")
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
        )
        for value, size in zip(legend_values, legend_sizes)
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=3,
        frameon=False,
        title=legend_title,
        columnspacing=1.7,
        handletextpad=0.8,
    )


def plot(metric_specs: dict[str, dict[str, object]], cartography: dict[str, object]) -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 16,
            "axes.labelsize": 16,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 13,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    section_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor="white",
            markeredgecolor=SECTION_COLORS[section],
            markeredgewidth=2.5,
            markersize=11,
            label=section,
        )
        for section in ["Montante", "Jusante"]
    ]
    section_handles[0].set_label("Reservatório/montante")
    cartographic_handles = [
        Patch(facecolor=RESERVOIR_COLOR, edgecolor=MAIN_RIVER_COLOR, label="Reservatório"),
        Line2D([0], [0], color=TRIBUTARY_COLOR, linewidth=1.5, label="Hidrografia"),
        Line2D(
            [0],
            [0],
            marker="D",
            linestyle="none",
            markerfacecolor=DAM_COLOR,
            markeredgecolor="#3F3F3F",
            markersize=7,
            label="Barragem",
        ),
    ]
    OFFICIAL_ROOT.mkdir(parents=True, exist_ok=True)
    for metric, spec in metric_specs.items():
        fig, ax = plt.subplots(1, 1, figsize=(18, 10.2), dpi=300)
        draw_metric_panel(
            ax,
            spec["data"],
            cartography,
            str(spec["legend"]),
            int(spec["decimals"]),
        )
        fig.legend(
            handles=section_handles + cartographic_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.975),
            ncol=5,
            frameon=False,
            columnspacing=1.4,
            handlelength=2.6,
        )
        fig.subplots_adjust(top=0.90, bottom=0.20, left=0.065, right=0.985)
        fig.savefig(OUTPUTS[metric], dpi=300, facecolor="white")
        plt.close(fig)


def main() -> None:
    data = load_data()
    cartography = load_cartography()
    metric_specs = load_metric_specs(data)
    if set(metric_specs) != set(OUTPUTS):
        raise ValueError("A lista de metricas e a lista de arquivos de saida nao reconciliam.")
    plot(metric_specs, cartography)
    print(
        {
            "outputs": {metric: str(path) for metric, path in OUTPUTS.items()},
            "points": len(data),
            "montante": int(data["trecho_longitudinal"].eq("Montante").sum()),
            "jusante": int(data["trecho_longitudinal"].eq("Jusante").sum()),
            "abundance": int(data["abundancia"].sum()),
            "metrics": len(metric_specs),
            "hydrography_segments": len(cartography["main_river"]) + len(cartography["tributaries"]),
        }
    )


if __name__ == "__main__":
    main()
