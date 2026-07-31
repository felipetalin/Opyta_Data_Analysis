from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial import ConvexHull
from scipy.spatial.distance import squareform


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_ictio_avg_tradicional_consolidado_2026 as ictio_traditional  # noqa: E402


ROOT = ictio_traditional.ROOT
BASE_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
ANALYTIC_XLSX = (
    BASE_DIR
    / "zoobentos_consolidated_analytic_base_20260721"
    / "base_analitica_consolidada_zoobentos_20260721.xlsx"
)
SUPPORT_DIR = BASE_DIR / "zoobentos_selected_results_20260721"
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados bentos"
    r"\Consolidado_2026"
)

GROUP_SLUG = "zoobentos"
ORDER_PALETTE = ["#3E7369", "#007032", "#00A859", "#82C21F"]
GROUP_COLORS = ["#007032", "#82C21F", "#3E7369", "#00A859", "#6A8F2F"]
BRAY_CUT_HEIGHT = 0.80
AREA_COLORS = {"Área de controle 01": "#16803A", "Área de controle 02": "#6A8F2F"}
GREEN_LOW = "#C9E7C1"
GREEN_MID = "#68B74A"
GREEN_HIGH = "#0C7438"
ABSENT_COLOR = "#FFFFFF"
TOP_TAXA_SYNTHESIS = 30


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


def _campaign_seq(campaign: object) -> int:
    text = str(campaign)
    if text.startswith("C") and "-" in text:
        return int(text[1:4])
    return int(str(campaign).replace("C", ""))


def _campaign_short(campaign: object) -> str:
    return f"C{_campaign_seq(campaign):02d}"


def _prepare_panel_table(point_campaign: pd.DataFrame, value_col: str) -> pd.DataFrame:
    table = point_campaign.copy()
    table["nome_campanha"] = table["Campanha"]
    table["campanha_seq"] = table["Campanha"].map(_campaign_seq)
    table["campanha_curta"] = table["Campanha"].map(_campaign_short)
    table["periodo"] = table["Periodo_Hidrologico"].fillna("ND")
    table["nome_ponto"] = table["Ponto"]
    table[value_col] = pd.to_numeric(table[value_col], errors="coerce").fillna(0)
    if "Status_Monitoramento" in table.columns:
        monitored = table["Status_Monitoramento"].astype(str).str.strip().eq("Monitorado")
        table.loc[~monitored, value_col] = np.nan
    return table


def _diversity_from_records(base: pd.DataFrame, point_campaign: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in base.groupby(["Campanha", "Ponto"], dropna=False):
        campaign, point = keys
        abund = (
            group.groupby("Nome_Cientifico", dropna=False)["Numero_de_Individuos"]
            .sum()
            .to_numpy(dtype=float)
        )
        abund = abund[abund > 0]
        total = float(abund.sum())
        richness = int(len(abund))
        if total > 0 and richness > 0:
            p = abund / total
            shannon = float(-(p * np.log(p)).sum())
            pielou = float(shannon / np.log(richness)) if richness > 1 else 0.0
        else:
            shannon = 0.0
            pielou = 0.0
        rows.append({"Campanha": campaign, "Ponto": point, "Shannon_H": shannon, "Pielou_J": pielou})
    diversity = point_campaign[["Campanha", "Ponto"]].drop_duplicates().merge(
        pd.DataFrame(rows), on=["Campanha", "Ponto"], how="left"
    )
    diversity[["Shannon_H", "Pielou_J"]] = diversity[["Shannon_H", "Pielou_J"]].fillna(0)
    return diversity


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, table in sheets.items():
            table.to_excel(writer, sheet_name=sheet[:31], index=False)


def build_composition(base: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    taxon_cols = ["Filo", "Classe", "Ordem", "Familia", "Nome_Cientifico"]
    composition = (
        base[taxon_cols]
        .drop_duplicates()
        .sort_values(taxon_cols, na_position="last")
        .reset_index(drop=True)
    )
    by_order = (
        composition.groupby("Ordem", dropna=False)
        .agg(riqueza_taxonomica=("Nome_Cientifico", "nunique"))
        .reset_index()
    )
    by_order["Ordem"] = by_order["Ordem"].fillna("Não classificada")
    by_order = by_order.sort_values("riqueza_taxonomica", ascending=False).reset_index(drop=True)

    total_order_richness = float(by_order["riqueza_taxonomica"].sum())
    by_order["percentual_riqueza"] = np.where(
        total_order_richness > 0,
        by_order["riqueza_taxonomica"] / total_order_richness * 100,
        0,
    )
    by_order["ordem_ranking"] = np.arange(1, len(by_order) + 1)

    top_orders = by_order.loc[by_order["ordem_ranking"] <= 8, ["Ordem", "riqueza_taxonomica", "percentual_riqueza"]]
    top_orders = top_orders.rename(columns={"Ordem": "grupo_rosca"})
    if len(by_order) > 8:
        other_orders = by_order.loc[by_order["ordem_ranking"] > 8]
        plot_data = pd.concat(
            [
                top_orders,
                pd.DataFrame(
                    {
                        "grupo_rosca": ["Outras ordens"],
                        "riqueza_taxonomica": [other_orders["riqueza_taxonomica"].sum()],
                        "percentual_riqueza": [other_orders["percentual_riqueza"].sum()],
                    }
                ),
            ],
            ignore_index=True,
        )
    else:
        plot_data = top_orders.reset_index(drop=True)

    colors = (ORDER_PALETTE * int(np.ceil(len(plot_data) / len(ORDER_PALETTE))))[: len(plot_data)]
    if "Outras ordens" in set(plot_data["grupo_rosca"]):
        colors[plot_data.index[plot_data["grupo_rosca"].eq("Outras ordens")][0]] = "#D8DDD9"

    fig, ax = plt.subplots(figsize=(10.5, 7.2), dpi=420)
    values = plot_data["riqueza_taxonomica"].to_numpy(dtype=float)
    total = int(values.sum())

    def _autopct(percent: float) -> str:
        return f"{percent:.1f}%" if percent >= 5.0 else ""

    wedges, _texts, autotexts = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=True,
        wedgeprops={"width": 0.45, "edgecolor": "white", "linewidth": 1.15},
        autopct=_autopct,
        pctdistance=0.78,
        textprops={"fontsize": 13.5, "fontweight": "bold"},
    )
    for autotext, wedge in zip(autotexts, wedges, strict=False):
        r, g, b, _a = wedge.get_facecolor()
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        autotext.set_color("black" if luminance > 0.58 else "white")
    ax.text(0, 0, f"Total\n{total}", ha="center", va="center", fontsize=15.5, fontweight="bold")
    ax.legend(
        wedges,
        plot_data["grupo_rosca"],
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=13,
    )
    ax.set_aspect("equal")
    figure = output_dir / "01_grafico_composicao_taxonomica_por_ordem_zoobentos.png"
    fig.savefig(figure, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)

    table = output_dir / "01_tabela_composicao_taxonomica_zoobentos.xlsx"
    _write_excel(table, {"composicao_taxonomica": composition, "riqueza_por_ordem": by_order, "dados_rosca_ordem": plot_data})
    return {"figure": str(figure), "table": str(table)}


def build_metric_panels(point_campaign: pd.DataFrame, base: pd.DataFrame, output_dir: Path) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    richness = _prepare_panel_table(point_campaign, "riqueza")
    abundance = _prepare_panel_table(point_campaign, "abundancia")
    density = _prepare_panel_table(point_campaign, "densidade_total")
    diversity_raw = _diversity_from_records(base, point_campaign)
    diversity = point_campaign.merge(diversity_raw, on=["Campanha", "Ponto"], how="left")
    diversity = _prepare_panel_table(diversity, "Shannon_H")
    diversity["Pielou_J"] = pd.to_numeric(diversity["Pielou_J"], errors="coerce").fillna(0)

    _write_excel(output_dir / "02_df_riqueza_taxonomica_zoobentos.xlsx", {"riqueza": richness})
    _write_excel(
        output_dir / "03_df_abundancia_densidade_zoobentos.xlsx",
        {"abundancia_densidade": abundance, "densidade": density},
    )
    _write_excel(output_dir / "04_df_indices_diversidade_alfa_zoobentos.xlsx", {"diversidade": diversity})

    outputs["02_riqueza"] = ictio_traditional._plot_report_point_groups(
        table=richness,
        value_col="riqueza",
        ylabel="Riqueza taxonômica",
        output_dir=output_dir,
        filename_prefix="02_grafico_riqueza_taxonomica_por_ponto_c001_c047",
        group_slug=GROUP_SLUG,
    )
    outputs["03A_abundancia"] = ictio_traditional._plot_report_point_groups(
        table=abundance,
        value_col="abundancia",
        ylabel="Abundância total",
        output_dir=output_dir,
        filename_prefix="03A_grafico_abundancia_por_ponto_c001_c047",
        group_slug=GROUP_SLUG,
    )
    outputs["03B_densidade"] = ictio_traditional._plot_report_point_groups(
        table=density,
        value_col="densidade_total",
        ylabel="Densidade total",
        output_dir=output_dir,
        filename_prefix="03B_grafico_densidade_por_ponto_c001_c047",
        group_slug=GROUP_SLUG,
    )
    outputs["04A_shannon"] = ictio_traditional._plot_report_point_groups(
        table=diversity,
        value_col="Shannon_H",
        ylabel="Shannon (H')",
        output_dir=output_dir,
        filename_prefix="04A_grafico_shannon_por_ponto_c001_c047",
        group_slug=GROUP_SLUG,
    )
    outputs["04B_pielou"] = ictio_traditional._plot_report_point_groups(
        table=diversity,
        value_col="Pielou_J",
        ylabel="Pielou (J')",
        output_dir=output_dir,
        filename_prefix="04B_grafico_pielou_por_ponto_c001_c047",
        group_slug=GROUP_SLUG,
    )
    outputs["tables"] = [
        str(output_dir / "02_df_riqueza_taxonomica_zoobentos.xlsx"),
        str(output_dir / "03_df_abundancia_densidade_zoobentos.xlsx"),
        str(output_dir / "04_df_indices_diversidade_alfa_zoobentos.xlsx"),
    ]
    return outputs


def build_taxon_synthesis(base: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    totals = (
        base.groupby("Nome_Cientifico", dropna=False)
        .agg(
            abundancia_total=("Numero_de_Individuos", "sum"),
            campanhas_ocorrencia=("Campanha", "nunique"),
            pontos_ocorrencia=("Ponto", "nunique"),
            ordem=("Ordem", "first"),
            familia=("Familia", "first"),
        )
        .reset_index()
        .sort_values("abundancia_total", ascending=False)
    )
    grand = float(totals["abundancia_total"].sum())
    totals["abundancia_relativa_percentual"] = np.where(grand > 0, totals["abundancia_total"] / grand * 100, 0)
    totals["ordem_ranking"] = np.arange(1, len(totals) + 1)
    selected_taxa = totals.head(TOP_TAXA_SYNTHESIS)["Nome_Cientifico"].tolist()
    campaigns = sorted(base["Campanha"].dropna().unique(), key=_campaign_seq)
    points = sum(ictio_traditional.REPORT_POINT_GROUPS.values(), [])

    temporal = (
        base.pivot_table(index="Nome_Cientifico", columns="Campanha", values="Numero_de_Individuos", aggfunc="sum", fill_value=0)
        .reindex(index=totals["Nome_Cientifico"], columns=campaigns, fill_value=0)
        .reset_index()
    )
    spatial = (
        base.pivot_table(index="Nome_Cientifico", columns="Ponto", values="Numero_de_Individuos", aggfunc="sum", fill_value=0)
        .reindex(index=totals["Nome_Cientifico"], columns=points, fill_value=0)
        .reset_index()
    )
    _write_excel(
        output_dir / "08C_df_sintese_abundancia_taxons_temporal_espacial_zoobentos.xlsx",
        {"ranking_abundancia": totals, "abundancia_temporal": temporal, "abundancia_por_ponto": spatial},
    )

    plot_totals = totals[totals["Nome_Cientifico"].isin(selected_taxa)].copy()
    plot_temporal = temporal[temporal["Nome_Cientifico"].isin(selected_taxa)].set_index("Nome_Cientifico").loc[selected_taxa].reset_index()
    plot_spatial = spatial[spatial["Nome_Cientifico"].isin(selected_taxa)].set_index("Nome_Cientifico").loc[selected_taxa].reset_index()
    n_taxa = len(selected_taxa)
    y = np.arange(n_taxa)
    fig = plt.figure(figsize=(16.54, 11.69), dpi=420)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.45, 1.45, 1.03], wspace=0.08)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_time = fig.add_subplot(gs[0, 1], sharey=ax_bar)
    ax_space = fig.add_subplot(gs[0, 2], sharey=ax_bar)

    ax_bar.barh(y, plot_totals["abundancia_relativa_percentual"], color=GREEN_HIGH, edgecolor="#38620E", height=0.62)
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(selected_taxa, fontsize=9.8)
    for label in ax_bar.get_yticklabels():
        label.set_fontstyle("italic")
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel("Contribuição relativa da abundância (%)", fontsize=11.5)
    ax_bar.grid(axis="x", color="#D9D9D9", linewidth=0.6, alpha=0.7)
    for spine in ["top", "right", "left"]:
        ax_bar.spines[spine].set_visible(False)
    for yi, value in enumerate(plot_totals["abundancia_relativa_percentual"]):
        ax_bar.text(value + 0.1, yi, f"{value:.1f}", va="center", fontsize=8.8)

    values = plot_temporal[campaigns].to_numpy(dtype=float)
    max_value = float(values.max()) if values.size else 0.0
    rel = np.divide(values, max_value, out=np.zeros_like(values), where=max_value > 0)
    intensity = np.zeros_like(values)
    intensity[(values > 0) & (rel <= 1 / 3)] = 1
    intensity[(rel > 1 / 3) & (rel <= 2 / 3)] = 2
    intensity[rel > 2 / 3] = 3
    cmap = mcolors.ListedColormap([ABSENT_COLOR, GREEN_LOW, GREEN_MID, GREEN_HIGH])
    ax_time.imshow(intensity, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=3)
    ax_time.set_xticks(np.arange(len(campaigns)))
    ax_time.set_xticklabels([_campaign_short(c) for c in campaigns], rotation=90, fontsize=6.7)
    ax_time.tick_params(axis="y", left=False, labelleft=False)
    ax_time.set_xlabel("Ocorrência por campanha (abundância)", fontsize=11.5)
    for year, start, end in ictio_traditional.TEMPORAL_YEAR_BANDS:
        ax_time.text((start + end) / 2 - 1, -0.85, f"Ano {year}", ha="center", fontsize=9.2, color="#50614A")
        ax_time.axvline(end - 0.5, color="#B8B8B8", linestyle=":", linewidth=0.8)
    ax_time.set_ylim(n_taxa - 0.5, -1.05)
    for spine in ["top", "right", "left"]:
        ax_time.spines[spine].set_visible(False)

    spatial_values = plot_spatial[points].to_numpy(dtype=float)
    row_max = np.nanmax(spatial_values, axis=1)
    spatial_rel = np.divide(spatial_values, row_max[:, None], out=np.zeros_like(spatial_values), where=row_max[:, None] > 0)
    for x, point in enumerate(points):
        color = AREA_COLORS.get(ictio_traditional.avg_runner.AREA_BY_POINT.get(point), "#777777")
        sizes = np.where(spatial_values[:, x] > 0, 18 + spatial_rel[:, x] * 145, 0)
        ax_space.scatter(np.full(n_taxa, x), y, s=sizes, color=color, edgecolor="#1F1F1F", linewidth=0.35, alpha=0.82)
    ax_space.set_xticks(np.arange(len(points)))
    ax_space.set_xticklabels(points, rotation=90, fontsize=8.5)
    ax_space.tick_params(axis="y", left=False, labelleft=False)
    ax_space.set_title("Distribuição espacial relativa por ponto", fontsize=11.5, pad=12)
    ax_space.grid(axis="y", color="#EEEEEE", linewidth=0.5)
    for spine in ["top", "right", "left"]:
        ax_space.spines[spine].set_visible(False)

    area_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor="#1F1F1F",
            markersize=6.8,
            label=area,
        )
        for area, color in AREA_COLORS.items()
    ]
    area_legend = ax_space.legend(
        handles=area_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.145),
        ncol=2,
        frameon=False,
        fontsize=8.6,
        columnspacing=1.2,
        handletextpad=0.45,
    )
    ax_space.add_artist(area_legend)
    size_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=AREA_COLORS["Área de controle 02"],
            markeredgecolor="#596B34",
            alpha=0.72,
            markersize=size,
            label=label,
        )
        for size, label in [(5.2, "Baixa (≤33%)"), (7.5, "Média (34-67%)"), (10.0, "Alta (>67%)")]
    ]
    ax_space.legend(
        handles=size_handles,
        title="Abundância relativa no ponto",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.225),
        ncol=3,
        frameon=False,
        fontsize=8.6,
        title_fontsize=8.8,
        columnspacing=1.0,
        handletextpad=0.45,
    )

    heat_handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=GREEN_HIGH, markeredgecolor="#777", markersize=7, label="Alta (>67%)"),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=GREEN_MID, markeredgecolor="#777", markersize=7, label="Média (34-67%)"),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=GREEN_LOW, markeredgecolor="#777", markersize=7, label="Baixa (≤33%)"),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=ABSENT_COLOR, markeredgecolor="#777", markersize=7, label="Ausência"),
    ]
    ax_time.legend(handles=heat_handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4, frameon=False, fontsize=8.6)
    fig.subplots_adjust(left=0.19, right=0.985, top=0.91, bottom=0.24)
    figure = output_dir / "08C_grafico_sintese_abundancia_taxons_temporal_espacial_zoobentos.png"
    fig.savefig(figure, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return {
        "figure": str(figure),
        "table": str(output_dir / "08C_df_sintese_abundancia_taxons_temporal_espacial_zoobentos.xlsx"),
    }


def _bray_curtis(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            denom = matrix[i].sum() + matrix[j].sum()
            value = 0.0 if denom == 0 else np.abs(matrix[i] - matrix[j]).sum() / denom
            dist[i, j] = value
            dist[j, i] = value
    return dist


def _pcoa(distance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = distance.shape[0]
    if n < 2:
        return np.zeros((n, 2)), np.zeros(2)
    d2 = distance**2
    h = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * h @ d2 @ h
    eigvals, eigvecs = np.linalg.eigh(b)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    positive = np.maximum(eigvals[:2], 0)
    coords = eigvecs[:, :2] * np.sqrt(positive)
    total = eigvals[eigvals > 0].sum()
    explained = positive / total * 100 if total > 0 else np.zeros(2)
    return coords, explained


def _taxon_vectors(matrix: pd.DataFrame, coords: np.ndarray, *, max_taxa: int = 4) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    if coords.shape[0] < 3:
        return pd.DataFrame(columns=["Nome_Cientifico", "correlacao_PCoA1", "correlacao_PCoA2", "forca_associacao"])
    for taxon in matrix.columns:
        values = matrix[taxon].to_numpy(dtype=float)
        if np.nanstd(values) == 0:
            corr1 = 0.0
            corr2 = 0.0
        else:
            corr1 = float(np.corrcoef(values, coords[:, 0])[0, 1]) if np.nanstd(coords[:, 0]) > 0 else 0.0
            corr2 = float(np.corrcoef(values, coords[:, 1])[0, 1]) if np.nanstd(coords[:, 1]) > 0 else 0.0
        corr1 = 0.0 if np.isnan(corr1) else corr1
        corr2 = 0.0 if np.isnan(corr2) else corr2
        records.append(
            {
                "Nome_Cientifico": taxon,
                "correlacao_PCoA1": corr1,
                "correlacao_PCoA2": corr2,
                "forca_associacao": float(np.sqrt(corr1**2 + corr2**2)),
            }
        )
    vectors = pd.DataFrame(records).sort_values("forca_associacao", ascending=False)
    selected = vectors[vectors["forca_associacao"] >= 0.55].head(max_taxa)
    if selected.empty:
        selected = vectors.head(min(3, len(vectors)))
    return selected.reset_index(drop=True)


def build_pcoa(base: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    taxa = sorted(base["Nome_Cientifico"].dropna().unique())
    years = sorted(base["Ano_Temporal"].dropna().unique())
    score_tables = []
    distance_tables = []
    group_tables = []
    vector_tables = []

    fig, axes = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=380)
    axes_flat = axes.ravel()
    for ax, year in zip(axes_flat, years, strict=False):
        sub = base[base["Ano_Temporal"].eq(year)]
        matrix = (
            sub.pivot_table(index="Ponto", columns="Nome_Cientifico", values="Numero_de_Individuos", aggfunc="sum", fill_value=0)
            .reindex(columns=taxa, fill_value=0)
        )
        matrix = matrix.loc[matrix.sum(axis=1) > 0]
        points = matrix.index.tolist()
        dist = _bray_curtis(matrix.to_numpy(dtype=float))
        coords, explained = _pcoa(dist)
        if len(points) > 1:
            z = linkage(squareform(dist, checks=False), method="average")
            groups = fcluster(z, t=BRAY_CUT_HEIGHT, criterion="distance")
        else:
            groups = np.ones(len(points), dtype=int)
        scores = pd.DataFrame(coords, columns=["PCoA1", "PCoA2"])
        scores["Ponto"] = points
        scores["Ano_Temporal"] = year
        scores["Grupo_Bray_080"] = groups
        score_tables.append(scores)
        group_tables.append(scores[["Ano_Temporal", "Ponto", "Grupo_Bray_080"]].copy())
        dist_df = pd.DataFrame(dist, index=points, columns=points).reset_index(names="Ponto")
        dist_df.insert(0, "Ano_Temporal", year)
        distance_tables.append(dist_df)

        for group_id in sorted(scores["Grupo_Bray_080"].unique()):
            part = scores[scores["Grupo_Bray_080"].eq(group_id)]
            color = GROUP_COLORS[(int(group_id) - 1) % len(GROUP_COLORS)]
            ax.scatter(
                part["PCoA1"],
                part["PCoA2"],
                s=82,
                color=color,
                edgecolor="#1F1F1F",
                linewidth=0.55,
                label=f"Grupo {int(group_id)}",
                zorder=3,
            )
            if len(part) >= 3 and scores["Grupo_Bray_080"].nunique() > 1:
                try:
                    hull = ConvexHull(part[["PCoA1", "PCoA2"]].to_numpy(dtype=float))
                    hull_points = part[["PCoA1", "PCoA2"]].to_numpy(dtype=float)[hull.vertices]
                    ax.fill(hull_points[:, 0], hull_points[:, 1], color=color, alpha=0.12, zorder=1)
                    ax.plot(
                        np.r_[hull_points[:, 0], hull_points[0, 0]],
                        np.r_[hull_points[:, 1], hull_points[0, 1]],
                        color=color,
                        linewidth=1.0,
                        alpha=0.6,
                        zorder=2,
                    )
                except Exception:
                    pass
        for _, row in scores.iterrows():
            ax.text(row["PCoA1"], row["PCoA2"], row["Ponto"], fontsize=8.2, ha="left", va="bottom", zorder=4)

        vectors = _taxon_vectors(matrix, coords, max_taxa=4 if int(year) == 2026 else 3)
        vectors.insert(0, "Ano_Temporal", year)
        vector_tables.append(vectors)
        x_span = max(float(np.ptp(coords[:, 0])), 0.1)
        y_span = max(float(np.ptp(coords[:, 1])), 0.1)
        scale = 0.34 * min(x_span, y_span)
        head_width = 0.025 * min(x_span, y_span)
        label_offsets = np.linspace(0.12, -0.12, len(vectors)) * y_span if int(year) == 2026 else np.zeros(len(vectors))
        for vector_idx, row in enumerate(vectors.itertuples(index=False)):
            dx = row.correlacao_PCoA1 * scale
            dy = row.correlacao_PCoA2 * scale
            ax.arrow(
                0,
                0,
                dx,
                dy,
                color="#303030",
                linewidth=1.0,
                head_width=head_width,
                length_includes_head=True,
                alpha=0.86,
                zorder=5,
            )
            ax.text(
                dx * 1.08,
                dy * 1.08 + label_offsets[vector_idx],
                row.Nome_Cientifico,
                fontsize=7.5,
                fontstyle="italic",
                color="#222222",
                ha="left" if dx >= 0 else "right",
                va="bottom" if dy >= 0 else "top",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 0.5},
                zorder=6,
            )
        ax.axhline(0, color="#D0D0D0", linewidth=0.8)
        ax.axvline(0, color="#D0D0D0", linewidth=0.8)
        ax.set_title(str(int(year)), fontsize=16, fontweight="bold")
        ax.set_xlabel(f"PCoA1 ({explained[0]:.1f}%)")
        ax.set_ylabel(f"PCoA2 ({explained[1]:.1f}%)")
        ax.grid(color="#ECECEC", linewidth=0.6)
        ax.legend(loc="best", fontsize=8.0, frameon=False, ncol=2)
    for ax in axes_flat[len(years) :]:
        ax.axis("off")
    fig.tight_layout(rect=(0.02, 0.02, 0.99, 0.98))
    figure = output_dir / "07_grafico_pcoa_bray_curtis_por_ano_temporal_zoobentos.png"
    fig.savefig(figure, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)

    table = output_dir / "07_df_pcoa_bray_curtis_zoobentos.xlsx"
    _write_excel(
        table,
        {
            "scores_pcoa": pd.concat(score_tables, ignore_index=True),
            "grupos_bray_080": pd.concat(group_tables, ignore_index=True),
            "taxons_vetores_pcoa": pd.concat(vector_tables, ignore_index=True),
            "distancias_bray_curtis": pd.concat(distance_tables, ignore_index=True),
        },
    )
    return {"figure": str(figure), "table": str(table)}


def build_bioindicator_tables(base: pd.DataFrame, point_campaign: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    ept = base[base["EPT"].eq(True)][["Nome_Cientifico", "Ordem", "Familia"]].drop_duplicates().sort_values(["Ordem", "Familia", "Nome_Cientifico"])
    chol = base[base["CHOL"].eq(True)][["Nome_Cientifico", "Ordem", "Familia"]].drop_duplicates().sort_values(["Ordem", "Familia", "Nome_Cientifico"])
    bmwp = (
        base[["Nome_Cientifico", "Ordem", "Familia", "BMWP_Score"]]
        .drop_duplicates()
        .sort_values(["BMWP_Score", "Familia", "Nome_Cientifico"], ascending=[False, True, True])
    )
    indicators = point_campaign[
        ["Campanha", "Ponto", "Ano_Temporal", "Area_Controle", "bmwp_score", "bmwp_familias", "ept_percentual", "chol_percentual"]
    ].copy()
    monitored = base[
        base["Status_Monitoramento"].eq("Monitorado")
        & (base["Numero_de_Individuos"].fillna(0) > 0)
        & base["BMWP_Score"].notna()
    ].copy()
    monitored["BMWP_Key"] = monitored["Familia"].fillna("").replace("", np.nan).fillna(monitored["Nome_Cientifico"])
    bmwp_accumulated = (
        monitored.groupby(["Ano_Temporal", "Ponto", "BMWP_Key"], dropna=False, as_index=False)
        .agg(BMWP_Score=("BMWP_Score", "max"))
        .groupby(["Ano_Temporal", "Ponto"], as_index=False)
        .agg(
            bmwp_acumulado_anual_familias=("BMWP_Score", "sum"),
            familias_bmwp_acumuladas=("BMWP_Key", "nunique"),
        )
    )
    bmwp_annual = (
        point_campaign[point_campaign["Status_Monitoramento"].eq("Monitorado")]
        .groupby(["Ano_Temporal", "Ponto", "Area_Controle"], as_index=False)
        .agg(
            campanhas_monitoradas=("Campanha", "nunique"),
            bmwp_medio_anual=("bmwp_score", "mean"),
            familias_bmwp_media=("bmwp_familias", "mean"),
        )
        .merge(bmwp_accumulated, on=["Ano_Temporal", "Ponto"], how="left")
    )
    bmwp_annual[["bmwp_acumulado_anual_familias", "familias_bmwp_acumuladas"]] = bmwp_annual[
        ["bmwp_acumulado_anual_familias", "familias_bmwp_acumuladas"]
    ].fillna(0)
    bmwp_annual["diferenca_acumulado_menos_medio"] = (
        bmwp_annual["bmwp_acumulado_anual_familias"] - bmwp_annual["bmwp_medio_anual"]
    )
    bmwp_annual["observacao_metodologica"] = (
        "Produto principal usa BMWP medio anual; acumulado anual soma familias unicas registradas no ano."
    )
    table = output_dir / "05_df_grupos_bioindicadores_bmwp_ept_chol_zoobentos.xlsx"
    _write_excel(
        table,
        {
            "indicadores_ponto_campanha": indicators,
            "comparativo_BMWP_anual": bmwp_annual,
            "taxons_EPT": ept,
            "taxons_CHOL": chol,
            "taxons_BMWP": bmwp,
        },
    )
    return {"table": str(table)}


def build_darwin_core(base: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    events = (
        base[
            [
                "Campanha",
                "Ponto",
                "Data",
                "Latitude",
                "Longitude",
                "Metodo_de_Captura",
                "Esforco",
                "Unidade_Esforco",
                "Tipo_de_Amostragem",
            ]
        ]
        .drop_duplicates()
        .copy()
    )
    events["eventID"] = events["Campanha"] + "_" + events["Ponto"]
    events["samplingProtocol"] = events["Metodo_de_Captura"]
    events["samplingEffort"] = events["Esforco"].astype(str) + " " + events["Unidade_Esforco"].astype(str)
    events["eventDate"] = pd.to_datetime(events["Data"], errors="coerce").dt.date.astype(str)
    events["decimalLatitude"] = events["Latitude"]
    events["decimalLongitude"] = events["Longitude"]
    events["locality"] = events["Ponto"]

    occurrences = base.copy()
    occurrences["eventID"] = occurrences["Campanha"] + "_" + occurrences["Ponto"]
    occurrences["occurrenceID"] = occurrences["eventID"] + "_" + occurrences["Nome_Cientifico"].astype(str)
    occurrences["basisOfRecord"] = "HumanObservation"
    occurrences["scientificName"] = occurrences["Nome_Cientifico"]
    occurrences["individualCount"] = occurrences["Numero_de_Individuos"]
    occurrences["kingdom"] = occurrences["Reino"]
    occurrences["phylum"] = occurrences["Filo"]
    occurrences["class"] = occurrences["Classe"]
    occurrences["order"] = occurrences["Ordem"]
    occurrences["family"] = occurrences["Familia"]
    occurrences["genus"] = occurrences["Genero"]
    occurrences["eventDate"] = pd.to_datetime(occurrences["Data"], errors="coerce").dt.date.astype(str)
    occurrences["decimalLatitude"] = occurrences["Latitude"]
    occurrences["decimalLongitude"] = occurrences["Longitude"]
    event_cols = [
        "eventID",
        "eventDate",
        "locality",
        "decimalLatitude",
        "decimalLongitude",
        "samplingProtocol",
        "samplingEffort",
        "Tipo_de_Amostragem",
        "Campanha",
        "Ponto",
    ]
    occurrence_cols = [
        "occurrenceID",
        "eventID",
        "basisOfRecord",
        "scientificName",
        "individualCount",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "eventDate",
        "decimalLatitude",
        "decimalLongitude",
    ]
    table = output_dir / "DarwinCore_IEF_Zoobentos_Monitoramento_De_Ictio_E_Bentos_Brumado_Avg.xlsx"
    _write_excel(table, {"event": events[event_cols], "occurrence": occurrences[occurrence_cols]})
    return {"table": str(table)}


def build(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(ANALYTIC_XLSX, sheet_name="base_analitica")
    point_campaign = pd.read_excel(ANALYTIC_XLSX, sheet_name="ponto_campanha")
    base = base[base["Status_Monitoramento"].eq("Monitorado")].copy()
    outputs = {
        "composition": build_composition(base, output_dir),
        "metric_panels": build_metric_panels(point_campaign, base, output_dir),
        "taxon_synthesis": build_taxon_synthesis(base, output_dir),
        "bioindicator_tables": build_bioindicator_tables(base, point_campaign, output_dir),
        "pcoa": build_pcoa(base, output_dir),
        "darwin_core": build_darwin_core(base, output_dir),
    }
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": "BRAAVG002",
        "group": "Zoobentos",
        "status": "generated_for_review",
        "source_analytic_base": str(ANALYTIC_XLSX),
        "output_dir": str(output_dir),
        "support_dir": str(support_dir),
        "scope": [
            "composicao taxonomica",
            "riqueza taxonomica",
            "abundancia e densidade",
            "Shannon e Pielou",
            "tabela BMWP/EPT/CHOL",
            "PCoA Bray-Curtis por ano temporal",
            "Darwin Core",
        ],
        "visual_rules": {
            "composition_order_palette": ORDER_PALETTE,
            "traditional_panels": "mesmo modelo A4 por grupos de pontos aprovado na Ictiofauna",
            "taxon_synthesis": f"figura 08C com top {TOP_TAXA_SYNTHESIS} taxons por abundancia; Excel contem todos os taxons",
        },
        "outputs": outputs,
    }
    manifest_path = support_dir / "manifesto_resultados_selecionados_zoobentos_20260721.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    manifest["manifest"] = str(manifest_path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera resultados selecionados AVG Zoobentos 2026.")
    parser.add_argument("--output-dir", type=Path, default=FINAL_DIR)
    parser.add_argument("--support-dir", type=Path, default=SUPPORT_DIR)
    args = parser.parse_args()
    summary = build(args.output_dir, args.support_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
