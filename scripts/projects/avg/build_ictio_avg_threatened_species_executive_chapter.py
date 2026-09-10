from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

GEOARC_DIR = SCRIPT_DIR.parent / "geoarc001"
if str(GEOARC_DIR) not in sys.path:
    sys.path.insert(0, str(GEOARC_DIR))

import build_ictio_avg_threatened_species_synthesis as threatened  # noqa: E402
import run_ictio_avg_tradicional_consolidado_2026 as traditional  # noqa: E402
from generate_functional_spatial_mini_maps import (  # noqa: E402
    _ada_polygons,
    _add_ada,
    _add_hydrology,
    _hydrology_segments,
    _point_limits,
    load_ada,
    load_hydrology,
)
from opyta_analysis.config import load_theme  # noqa: E402


ROOT = traditional.ROOT
FINAL_DIR = threatened.FINAL_DIR
SUPPORT_DIR = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "threatened_species_executive_20260717"
)
SPECIES = threatened.THREATENED_SPECIES
SPECIES_COLORS = threatened.SPECIES_COLORS
SOURCE_XLSX = FINAL_DIR / "10A_df_sintese_cpuen_especies_ameacadas_ictiofauna.xlsx"
MAP_XLSX = FINAL_DIR / "10B_df_mini_mapas_especies_ameacadas_ano_ictiofauna.xlsx"
HYDROLOGY_LAYER = threatened.HYDROLOGY_LAYER
ADA_LAYER = threatened.ADA_LAYER
CONTROL_AREA_COLORS = threatened.CONTROL_AREA_COLORS


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


def _campaign_short(campaign: object) -> str:
    return f"C{traditional.standard_campaign_sequence(campaign):02d}"


def _format_species(value: str) -> str:
    return f"*{value}*"


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "ranking": pd.read_excel(SOURCE_XLSX, sheet_name="ranking_cpuen"),
        "temporal": pd.read_excel(SOURCE_XLSX, sheet_name="cpuen_temporal"),
        "spatial": pd.read_excel(SOURCE_XLSX, sheet_name="cpuen_por_ponto"),
        "annual": pd.read_excel(MAP_XLSX, sheet_name="cpuen_anual_ponto_especie"),
        "campaign": pd.read_excel(MAP_XLSX, sheet_name="cpuen_campanha_ponto_especie"),
        "coords": pd.read_excel(MAP_XLSX, sheet_name="coordenadas_pontos"),
    }


def build_summary_tables(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranking = data["ranking"].copy()
    temporal = data["temporal"].copy()
    spatial = data["spatial"].copy()
    campaigns = [col for col in temporal.columns if col != "nome_cientifico"]
    points = [col for col in spatial.columns if col != "nome_cientifico"]
    rows = []
    for _, row in ranking.iterrows():
        species = row["nome_cientifico"]
        temporal_values = pd.to_numeric(
            temporal.loc[temporal["nome_cientifico"] == species, campaigns].iloc[0],
            errors="coerce",
        ).fillna(0)
        spatial_values = pd.to_numeric(
            spatial.loc[spatial["nome_cientifico"] == species, points].iloc[0],
            errors="coerce",
        ).fillna(0)
        rows.append(
            {
                "nome_cientifico": species,
                "CPUEn_total": float(row["cpuen_total"]),
                "contribuicao_ameacadas_pct": float(row["cpuen_percentual"]),
                "contribuicao_assembleia_pct": float(row["cpuen_percentual_total_assembleia"]),
                "campanhas_com_registro": int((temporal_values > 0).sum()),
                "pontos_com_registro": int((spatial_values > 0).sum()),
                "pontos": "; ".join([point for point, value in spatial_values.items() if float(value) > 0]),
            }
        )
    summary = pd.DataFrame(rows)
    total = pd.DataFrame(
        [
            {
                "indicador": "especies_ameacadas",
                "valor": len(summary),
            },
            {
                "indicador": "cpuen_total_ameacadas",
                "valor": float(summary["CPUEn_total"].sum()),
            },
            {
                "indicador": "campanhas_com_registro_qualquer_especie",
                "valor": int(
                    (
                        temporal[campaigns]
                        .apply(pd.to_numeric, errors="coerce")
                        .fillna(0)
                        .sum(axis=0)
                        > 0
                    ).sum()
                ),
            },
            {
                "indicador": "pontos_com_registro_qualquer_especie",
                "valor": int(
                    (
                        spatial[points]
                        .apply(pd.to_numeric, errors="coerce")
                        .fillna(0)
                        .sum(axis=0)
                        > 0
                    ).sum()
                ),
            },
        ]
    )
    return summary, total


def _control_polygons(coords: pd.DataFrame, xmin: float, xmax: float, ymin: float, ymax: float) -> dict[str, list[np.ndarray]]:
    control_areas = threatened.load_control_areas()
    return threatened._control_polygons(control_areas, xmin, xmax, ymin, ymax)


def _add_control_areas(ax: Any, polygons: dict[str, list[np.ndarray]]) -> None:
    threatened._add_control_areas(ax, polygons)


def _bubble_size(value: float, max_value: float) -> float:
    if max_value <= 0 or value <= 0:
        return 0.0
    return 32 + np.sqrt(value / max_value) * 430


def plot_executive_figure(data: dict[str, pd.DataFrame], summary: pd.DataFrame, out_png: Path) -> None:
    theme = load_theme(ROOT / "configs", "braavg002")
    coords = data["coords"][["Ponto", "Longitude", "Latitude"]].copy()
    spatial = data["spatial"].copy()
    temporal = data["temporal"].copy()
    campaigns = [col for col in temporal.columns if col != "nome_cientifico"]
    points = [col for col in spatial.columns if col != "nome_cientifico"]
    hydrology = load_hydrology([HYDROLOGY_LAYER])
    ada = load_ada(ADA_LAYER)
    xmin, xmax, ymin, ymax = _point_limits(coords)
    segments = _hydrology_segments(hydrology, xmin, xmax, ymin, ymax)
    ada_polygons = _ada_polygons(ada, xmin, xmax, ymin, ymax)
    control_polygons = _control_polygons(coords, xmin, xmax, ymin, ymax)

    map_rows = []
    for _, row in spatial.iterrows():
        species = row["nome_cientifico"]
        for point in points:
            value = float(row[point]) if pd.notna(row[point]) else 0.0
            if value <= 0:
                continue
            coord = coords.loc[coords["Ponto"] == point]
            if coord.empty:
                continue
            map_rows.append(
                {
                    "nome_cientifico": species,
                    "Ponto": point,
                    "CPUEn_total": value,
                    "Longitude": float(coord["Longitude"].iloc[0]),
                    "Latitude": float(coord["Latitude"].iloc[0]),
                }
            )
    map_df = pd.DataFrame(map_rows)
    max_map = float(map_df["CPUEn_total"].max()) if not map_df.empty else 0.0

    fig = plt.figure(figsize=(16.54, 11.69), dpi=int(theme.get("dpi", 450)))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.35, 1.05], width_ratios=[1.05, 1.55, 0.95], hspace=0.22, wspace=0.18)
    ax_map = fig.add_subplot(gs[0, 0:2])
    ax_cards = fig.add_subplot(gs[0, 2])
    ax_time = fig.add_subplot(gs[1, :])

    _add_ada(ax_map, ada_polygons)
    _add_control_areas(ax_map, control_polygons)
    _add_hydrology(ax_map, segments)
    ax_map.scatter(coords["Longitude"], coords["Latitude"], s=15, color="#D7DDE0", edgecolor="#8B969A", linewidth=0.45, zorder=1.0)
    callout_offsets = {"PIC-02": (-0.0022, 0.00105), "PIC-04": (0.0018, 0.00055)}
    for point, x, y in coords[["Ponto", "Longitude", "Latitude"]].itertuples(index=False):
        if point in callout_offsets:
            dx, dy = callout_offsets[point]
            ax_map.annotate(
                point,
                xy=(x, y),
                xytext=(x + dx, y + dy),
                fontsize=8.8,
                color="#344047",
                ha="center",
                va="center",
                arrowprops={"arrowstyle": "-", "color": "#59666C", "lw": 0.7, "shrinkA": 0, "shrinkB": 2},
                zorder=5,
            )
        else:
            ax_map.text(x + 0.00016, y + 0.00012, point, fontsize=8.8, color="#344047", zorder=4)
    offsets = {
        "Neoplecostomus franciscoensis": (-0.00017, 0.00013),
        "Pareiorhaphis mutuca": (0.00017, -0.00013),
    }
    for species in SPECIES:
        subset = map_df[map_df["nome_cientifico"] == species].copy()
        if subset.empty:
            continue
        dx, dy = offsets[species]
        sizes = [_bubble_size(value, max_map) for value in subset["CPUEn_total"]]
        ax_map.scatter(
            subset["Longitude"] + dx,
            subset["Latitude"] + dy,
            s=sizes,
            color=SPECIES_COLORS[species],
            edgecolor="#1F1F1F",
            linewidth=0.55,
            alpha=0.86,
            zorder=3,
        )
    ax_map.set_title("Distribuição espacial acumulada", fontsize=14, fontweight="bold", pad=10)
    ax_map.set_xlim(xmin, xmax)
    ax_map.set_ylim(ymin, ymax)
    ax_map.set_aspect("equal", adjustable="box")
    ax_map.grid(color="#E8ECEE", linewidth=0.65)
    ax_map.tick_params(labelsize=8.5)
    ax_map.set_xlabel("Longitude", fontsize=10)
    ax_map.set_ylabel("Latitude", fontsize=10)
    for spine in ["top", "right"]:
        ax_map.spines[spine].set_visible(False)

    ax_cards.axis("off")
    card_y = [0.63, 0.24]
    for y0, (_, row) in zip(card_y, summary.iterrows(), strict=True):
        species = row["nome_cientifico"]
        ax_cards.add_patch(
            plt.Rectangle((0.02, y0 - 0.14), 0.96, 0.28, transform=ax_cards.transAxes, facecolor="#F7F9F7", edgecolor="#C9D6C9", linewidth=0.9)
        )
        ax_cards.scatter([0.08], [y0 + 0.075], s=95, color=SPECIES_COLORS[species], edgecolor="#1F1F1F", transform=ax_cards.transAxes, zorder=3)
        ax_cards.text(0.14, y0 + 0.08, species, fontsize=11.5, fontstyle="italic", fontweight="bold", transform=ax_cards.transAxes, ha="left", va="center")
        ax_cards.text(
            0.14,
            y0 - 0.005,
            f"{row['contribuicao_ameacadas_pct']:.1f}% da CPUEn das ameaçadas",
            fontsize=10.2,
            color="#263238",
            transform=ax_cards.transAxes,
            ha="left",
        )
        ax_cards.text(
            0.14,
            y0 - 0.085,
            f"{int(row['campanhas_com_registro'])} campanhas | {int(row['pontos_com_registro'])} pontos",
            fontsize=9.8,
            color="#54636B",
            transform=ax_cards.transAxes,
            ha="left",
        )
    temporal_matrix = temporal.set_index("nome_cientifico")[campaigns].apply(pd.to_numeric, errors="coerce").fillna(0)
    max_temporal = float(temporal_matrix.to_numpy().max()) if not temporal_matrix.empty else 0.0
    relative = np.divide(
        temporal_matrix.to_numpy(dtype=float),
        max_temporal,
        out=np.zeros_like(temporal_matrix.to_numpy(dtype=float)),
        where=max_temporal > 0,
    )
    intensity = np.zeros_like(relative)
    intensity[(temporal_matrix.to_numpy(dtype=float) > 0) & (relative <= 1 / 3)] = 1
    intensity[(relative > 1 / 3) & (relative <= 2 / 3)] = 2
    intensity[relative > 2 / 3] = 3
    cmap = matplotlib.colors.ListedColormap(["#FFFFFF", "#C9E7C1", "#68B74A", "#0C7438"])
    ax_time.imshow(intensity, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=3)
    temporal_labels = {
        "Neoplecostomus franciscoensis": "N. franciscoensis",
        "Pareiorhaphis mutuca": "P. mutuca",
    }
    ax_time.set_yticks(np.arange(len(temporal_matrix.index)))
    ax_time.set_yticklabels([temporal_labels.get(label, label) for label in temporal_matrix.index], fontsize=11)
    for label in ax_time.get_yticklabels():
        label.set_fontstyle("italic")
    ax_time.set_xticks(np.arange(len(campaigns)))
    ax_time.set_xticklabels([_campaign_short(campaign) for campaign in campaigns], rotation=90, fontsize=6.3)
    ax_time.set_title("Ocorrência temporal por campanha", fontsize=14, fontweight="bold", pad=8)
    for year, start, end in traditional.TEMPORAL_YEAR_BANDS:
        indices = [idx for idx, campaign in enumerate(campaigns) if start <= traditional.standard_campaign_sequence(campaign) <= end]
        if not indices:
            continue
        left = min(indices) - 0.5
        right = max(indices) + 0.5
        ax_time.text((left + right) / 2, -0.78, f"Ano {year}", ha="center", va="bottom", fontsize=9.3, color="#50614A")
        ax_time.axvline(right, color="#B8B8B8", linestyle=":", linewidth=0.75, zorder=3)
    ax_time.set_ylim(len(temporal_matrix.index) - 0.5, -0.86)
    ax_time.set_xticks(np.arange(-0.5, len(campaigns), 1), minor=True)
    ax_time.set_yticks(np.arange(-0.5, len(temporal_matrix.index), 1), minor=True)
    ax_time.grid(which="minor", color="white", linewidth=0.22)
    ax_time.tick_params(axis="y", length=0)
    ax_time.tick_params(which="minor", bottom=False, left=False)
    for spine in ["top", "right", "left"]:
        ax_time.spines[spine].set_visible(False)

    species_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=SPECIES_COLORS[species], markeredgecolor="#1F1F1F", markersize=9.5, label=species)
        for species in SPECIES
    ]
    control_handles = [
        Line2D([0], [0], color=CONTROL_AREA_COLORS[label], linestyle="--", linewidth=1.4, label=label)
        for label in threatened.CONTROL_AREA_LAYERS
    ]
    size_values = [max_map * relative_value for relative_value in (0.25, 0.55, 1.0)]
    size_handles = [
        plt.scatter([], [], s=_bubble_size(value, max_map), color="#9EB77E", edgecolor="#1F1F1F", linewidth=0.55, label=label)
        for value, label in zip(
            size_values,
            [f"Baixa ({size_values[0]:.1f})", f"Média ({size_values[1]:.1f})", f"Alta ({size_values[2]:.1f})"],
            strict=True,
        )
    ]
    species_legend = fig.legend(handles=species_handles, loc="lower center", bbox_to_anchor=(0.50, 0.075), ncol=2, frameon=False, fontsize=10.4)
    for text in species_legend.get_texts():
        text.set_fontstyle("italic")
    fig.legend(handles=control_handles, loc="lower center", bbox_to_anchor=(0.50, 0.045), ncol=2, frameon=False, fontsize=9.7)
    fig.legend(handles=size_handles, title="CPUEn acumulada no ponto", loc="lower center", bbox_to_anchor=(0.50, 0.004), ncol=3, frameon=False, fontsize=9.2, title_fontsize=9.8)
    fig.subplots_adjust(left=0.135, right=0.985, top=0.955, bottom=0.145)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, pad_inches=0.04)
    plt.close(fig)


def write_chapter_text(summary: pd.DataFrame, total: pd.DataFrame, out_md: Path) -> str:
    n_species = int(total.loc[total["indicador"] == "especies_ameacadas", "valor"].iloc[0])
    n_campaigns = int(total.loc[total["indicador"] == "campanhas_com_registro_qualquer_especie", "valor"].iloc[0])
    n_points = int(total.loc[total["indicador"] == "pontos_com_registro_qualquer_especie", "valor"].iloc[0])
    neo = summary.loc[summary["nome_cientifico"] == "Neoplecostomus franciscoensis"].iloc[0]
    par = summary.loc[summary["nome_cientifico"] == "Pareiorhaphis mutuca"].iloc[0]
    text = f"""# Espécies ameaçadas de extinção registradas na ictiofauna

Foram registradas {n_species} espécies ameaçadas de extinção no conjunto de dados de ictiofauna: {_format_species('Neoplecostomus franciscoensis')} e {_format_species('Pareiorhaphis mutuca')}. Ambas apresentam associação funcional com ambientes lóticos, bentônicos e de maior dependência de condições físicas específicas do habitat, o que torna sua ocorrência relevante para a leitura conservacionista dos trechos monitorados.

A maior representatividade foi observada para {_format_species('Neoplecostomus franciscoensis')}, responsável por {neo['contribuicao_ameacadas_pct']:.1f}% da CPUEn total calculada para as espécies ameaçadas. A espécie foi registrada em {int(neo['campanhas_com_registro'])} campanhas e {int(neo['pontos_com_registro'])} pontos amostrais ({neo['pontos']}), indicando distribuição mais recorrente no período avaliado. Esse padrão sugere que parte dos ambientes monitorados ainda apresentou condições compatíveis com a manutenção de espécies reofílicas/bentônicas de interesse conservacionista.

Por outro lado, {_format_species('Pareiorhaphis mutuca')} apresentou ocorrência mais restrita, com {par['contribuicao_ameacadas_pct']:.1f}% da CPUEn das espécies ameaçadas, registros em {int(par['campanhas_com_registro'])} campanhas e {int(par['pontos_com_registro'])} pontos amostrais ({par['pontos']}). Esse resultado caracteriza a espécie como um componente pontual da assembleia registrada, cuja permanência deve ser acompanhada nas próximas campanhas em função de sua relevância conservacionista.

De forma integrada, as espécies ameaçadas foram registradas em {n_campaigns} campanhas e {n_points} pontos amostrais. A distribuição espacial e temporal desses registros não deve ser interpretada isoladamente como indicativo de ausência de impacto ou de melhoria ambiental, mas como evidência de que determinados trechos ainda mantêm condições adequadas para espécies de maior especificidade ecológica. A interpretação deve considerar simultaneamente o esforço amostral, a continuidade dos pontos, as alterações de acesso, a estrutura dos habitats e as variações hidrológicas entre campanhas.

Para fins de acompanhamento, recomenda-se manter atenção especial aos pontos com registros recorrentes de {_format_species('Neoplecostomus franciscoensis')} e aos pontos com registros pontuais de {_format_species('Pareiorhaphis mutuca')}. Reduções abruptas, deslocamentos espaciais ou ausência persistente dessas espécies em pontos historicamente ocupados devem ser avaliados em conjunto com informações de campo, condições de substrato, conectividade e vazão.
"""
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(text, encoding="utf-8")
    return text


def write_tables(summary: pd.DataFrame, total: pd.DataFrame, out_xlsx: Path) -> None:
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="sintese_especies", index=False)
        total.to_excel(writer, sheet_name="indicadores_gerais", index=False)


def build(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, Any]:
    data = load_inputs()
    summary, total = build_summary_tables(data)
    figure = output_dir / "10F_grafico_sintese_executiva_especies_ameacadas_ictiofauna.png"
    table = output_dir / "10F_df_sintese_executiva_especies_ameacadas_ictiofauna.xlsx"
    chapter = output_dir / "10F_texto_capitulo_especies_ameacadas_ictiofauna.md"
    plot_executive_figure(data, summary, figure)
    write_tables(summary, total, table)
    text = write_chapter_text(summary, total, chapter)
    support_dir.mkdir(parents=True, exist_ok=True)
    support_figure = support_dir / figure.name
    support_table = support_dir / table.name
    support_chapter = support_dir / chapter.name
    support_figure.write_bytes(figure.read_bytes())
    support_table.write_bytes(table.read_bytes())
    support_chapter.write_text(text, encoding="utf-8")
    manifest = support_dir / "manifesto_10F_sintese_executiva_especies_ameacadas_ictiofauna.json"
    summary_manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": traditional.PROJECT_CODE,
        "status": "generated",
        "figure": str(figure),
        "table": str(table),
        "chapter_text": str(chapter),
        "support_figure": str(support_figure),
        "support_table": str(support_table),
        "support_chapter_text": str(support_chapter),
        "species": SPECIES,
        "source_tables": [str(SOURCE_XLSX), str(MAP_XLSX)],
    }
    manifest.write_text(json.dumps(summary_manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary_manifest["manifest"] = str(manifest)
    return summary_manifest


def main() -> int:
    summary = build()
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
