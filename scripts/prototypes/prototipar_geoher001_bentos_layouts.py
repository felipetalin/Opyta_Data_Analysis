from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import load_theme
from opyta_analysis.pipelines.diagnostico.zoobentos import (
    _apply_campaign_filter,
    _load_zoobentos_df,
    _nonzero_taxon_rows,
    _ordered_points_from_df,
    _pielou,
    _shannon,
)
from opyta_analysis.theme import apply_rcparams, apply_theme, palette_from_theme


CAMPAIGNS_2022_2025 = [
    "C21-03-2022-CH",
    "C22-05-2022-SC",
    "C23-08-2022-SC",
    "C24-11-2022-CH",
    "C25-02-2023-CH",
    "C26-05-2023-SC",
    "C27-08-2023-SC",
    "C28-11-2023-CH",
    "C29-02-2024-CH",
    "C30-05-2024-SC",
    "C31-08-2024-SC",
    "C32-11-2024-CH",
    "C33-02-2025-CH",
    "C34-05-2025-SC",
    "C35-08-2025-SC",
    "C36-11-2025-CH",
]


def _campaign_number(campaign: str) -> int:
    match = re.search(r"C(\d+)", str(campaign))
    return int(match.group(1)) if match else 999999


def _campaign_short(campaign: str) -> str:
    match = re.search(r"C(\d+)", str(campaign))
    return f"C{int(match.group(1)):02d}" if match else str(campaign)


def _campaign_year(campaign: str) -> str:
    match = re.search(r"-(\d{4})-", str(campaign))
    return match.group(1) if match else ""


def _campaign_season(campaign: str) -> str:
    text = str(campaign).upper().strip()
    if text.endswith("-CH"):
        return "CH"
    if text.endswith("-SC"):
        return "SC"
    return ""


def _clean_category(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except TypeError:
        pass
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return fallback
    return text


def _order_label(row: pd.Series) -> str:
    for column in ["ordem", "familia", "classe", "filo", "taxon_final"]:
        label = _clean_category(row.get(column), fallback="")
        if label:
            return label
    return "Taxon nao identificado"


def _prepare_base(env_file: str | None) -> tuple[pd.DataFrame, list[str], list[str]]:
    df = _load_zoobentos_df(project_id=30, group="Zoobentos", env_file=env_file)
    df, filter_info = _apply_campaign_filter(df, CAMPAIGNS_2022_2025)
    if filter_info["missing"]:
        missing = ", ".join(filter_info["missing"])
        raise RuntimeError(f"Campanhas ausentes no recorte de teste: {missing}")
    if df.empty:
        raise RuntimeError("Nenhum dado de Zoobentos carregado para o recorte.")

    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    campaigns = sorted(df["nome_campanha"].dropna().astype(str).unique().tolist(), key=_campaign_number)
    points = _ordered_points_from_df(df)
    return df, campaigns, points


def _full_index(campaigns: list[str], points: list[str]) -> pd.MultiIndex:
    return pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"])


def _metric_tables(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> dict[str, pd.DataFrame]:
    df_present = _nonzero_taxon_rows(df)
    full_idx = _full_index(campaigns, points)

    richness = (
        df_present.groupby(["nome_campanha", "nome_ponto"])["taxon_final"]
        .nunique()
        .rename("riqueza")
        .reindex(full_idx, fill_value=0)
        .reset_index()
    )

    abundance = (
        df.groupby(["nome_campanha", "nome_ponto"])["contagem"]
        .sum()
        .rename("abundancia_total")
        .reindex(full_idx, fill_value=0)
        .reset_index()
    )

    div_rows: list[dict] = []
    for campaign in campaigns:
        df_campaign = df_present[df_present["nome_campanha"] == campaign].copy()
        if df_campaign.empty:
            for point in points:
                div_rows.append({"nome_campanha": campaign, "nome_ponto": point, "Shannon_H": 0.0, "Pielou_J": 0.0})
            continue

        mat = df_campaign.pivot_table(
            index="nome_ponto",
            columns="taxon_final",
            values="contagem",
            aggfunc="sum",
            fill_value=0,
            observed=False,
        ).reindex(points, fill_value=0)
        for point in points:
            values = mat.loc[point].to_numpy(dtype=float) if point in mat.index else np.array([], dtype=float)
            div_rows.append(
                {
                    "nome_campanha": campaign,
                    "nome_ponto": point,
                    "Shannon_H": _shannon(values),
                    "Pielou_J": _pielou(values),
                }
            )
    diversity = pd.DataFrame(div_rows)

    for table in [richness, abundance, diversity]:
        table["campanha_curta"] = table["nome_campanha"].map(_campaign_short)
        table["ano"] = table["nome_campanha"].map(_campaign_year)
        table["estacao"] = table["nome_campanha"].map(_campaign_season)

    return {"riqueza": richness, "abundancia": abundance, "diversidade": diversity}


def _style_theme(theme: dict) -> dict:
    styled = dict(theme)
    styled.update(
        {
            "font_size_base": 8,
            "label_size": 9,
            "legend_size": 8,
            "annotation_size": 7,
            "figsize_standard": [11.69, 8.27],
            "tight_layout_top": 0.91,
        }
    )
    return styled


def _season_colors(theme: dict) -> dict[str, str]:
    return {
        "CH": str(theme.get("primary_hex", "#002060")),
        "SC": str(theme.get("secondary_hex", "#5B9BD5")),
    }


def _mean_label(value: float) -> str:
    return f"Media geral ({value:.1f})"


def _add_year_separators(ax) -> None:
    for xpos in [3.5, 7.5, 11.5]:
        ax.axvline(xpos, color="#D0D0D0", linewidth=0.7, linestyle="-", zorder=0)


def _small_multiple_metric(
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
) -> None:
    apply_rcparams(theme)
    colors = _season_colors(theme)
    x = np.arange(len(campaigns))
    labels = [_campaign_short(c) for c in campaigns]
    overall_mean = float(pd.to_numeric(table[value_col], errors="coerce").fillna(0).mean())
    ymax = float(table[value_col].max())
    ymax = max(ymax, overall_mean) * 1.15 if ymax > 0 else max(overall_mean * 1.15, 1.0)

    fig, axes = plt.subplots(2, 4, figsize=(11.69, 8.27), dpi=int(theme.get("dpi", 600)), sharex=True, sharey=True)
    for ax, point in zip(axes.ravel(), points):
        point_data = table[table["nome_ponto"] == point].set_index("nome_campanha").reindex(campaigns).reset_index()
        values = pd.to_numeric(point_data[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        seasons = point_data["nome_campanha"].map(_campaign_season).tolist()
        ax.plot(x, values, color="#606060", linewidth=1.0, zorder=1)
        for season in ["CH", "SC"]:
            mask = np.array([s == season for s in seasons])
            ax.scatter(x[mask], values[mask], s=24, color=colors[season], edgecolor="black", linewidth=0.4, zorder=2)
        ax.axhline(overall_mean, color="#7F7F7F", linewidth=0.9, linestyle="--", zorder=0)
        ax.text(0.02, 0.92, point, transform=ax.transAxes, ha="left", va="top", fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90)
        _add_year_separators(ax)
        apply_theme(ax, theme, xlabel="", ylabel="")

    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)
    for ax in axes[-1, :]:
        ax.set_xlabel("Campanha")

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["CH"], markeredgecolor="black", label="CH"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors["SC"], markeredgecolor="black", label="SC"),
        Line2D([0], [0], color="#7F7F7F", linestyle="--", linewidth=0.9, label=_mean_label(overall_mean)),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False)
    fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _box_strip_metric(
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    theme: dict,
    points: list[str],
) -> None:
    apply_rcparams(theme)
    colors = _season_colors(theme)
    fig, ax = plt.subplots(figsize=(11.69, 8.27), dpi=int(theme.get("dpi", 600)))
    values_by_point = [
        pd.to_numeric(table.loc[table["nome_ponto"] == point, value_col], errors="coerce").fillna(0).to_numpy()
        for point in points
    ]
    bp = ax.boxplot(values_by_point, positions=np.arange(len(points)), widths=0.52, patch_artist=True, showfliers=False)
    for patch in bp["boxes"]:
        patch.set_facecolor("#DBE5F1")
        patch.set_edgecolor("black")
        patch.set_linewidth(0.9)
    for element in ["whiskers", "caps", "medians"]:
        for item in bp[element]:
            item.set_color("black")
            item.set_linewidth(0.9)

    rng = np.random.default_rng(42)
    for i, point in enumerate(points):
        point_data = table[table["nome_ponto"] == point].copy()
        jitter = rng.uniform(-0.16, 0.16, size=len(point_data))
        for season in ["CH", "SC"]:
            d = point_data[point_data["estacao"] == season]
            idx = d.index.to_numpy()
            local_jitter = jitter[[list(point_data.index).index(j) for j in idx]]
            ax.scatter(
                np.full(len(d), i) + local_jitter,
                pd.to_numeric(d[value_col], errors="coerce").fillna(0),
                s=24,
                color=colors[season],
                edgecolor="black",
                linewidth=0.35,
                alpha=0.9,
                label=season if i == 0 else None,
            )

    ax.set_xticks(np.arange(len(points)))
    ax.set_xticklabels(points)
    apply_theme(ax, theme, xlabel="Ponto amostral", ylabel=ylabel, x_tick_rotation=0)
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False)
    fig.tight_layout(rect=[0.02, 0.02, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _small_multiple_diversity(
    diversity: pd.DataFrame,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
) -> None:
    apply_rcparams(theme)
    primary = str(theme.get("primary_hex", "#002060"))
    secondary = str(theme.get("secondary_hex", "#5B9BD5"))
    x = np.arange(len(campaigns))
    labels = [_campaign_short(c) for c in campaigns]
    shannon_mean = float(pd.to_numeric(diversity["Shannon_H"], errors="coerce").fillna(0).mean())
    pielou_mean = float(pd.to_numeric(diversity["Pielou_J"], errors="coerce").fillna(0).mean())
    ymax = max(float(diversity["Shannon_H"].max()), float(diversity["Pielou_J"].max()), shannon_mean, pielou_mean, 1.0) * 1.15

    fig, axes = plt.subplots(2, 4, figsize=(11.69, 8.27), dpi=int(theme.get("dpi", 600)), sharex=True, sharey=True)
    for ax, point in zip(axes.ravel(), points):
        point_data = diversity[diversity["nome_ponto"] == point].set_index("nome_campanha").reindex(campaigns).reset_index()
        shannon = pd.to_numeric(point_data["Shannon_H"], errors="coerce").fillna(0).to_numpy(dtype=float)
        pielou = pd.to_numeric(point_data["Pielou_J"], errors="coerce").fillna(0).to_numpy(dtype=float)
        ax.plot(x, shannon, color=primary, marker="o", markersize=3, linewidth=1.1, label="Shannon")
        ax.plot(x, pielou, color=secondary, marker="s", markersize=3, linewidth=1.1, label="Pielou")
        ax.axhline(shannon_mean, color=primary, linewidth=0.8, linestyle="--", alpha=0.75)
        ax.axhline(pielou_mean, color=secondary, linewidth=0.8, linestyle="--", alpha=0.75)
        ax.text(0.02, 0.92, point, transform=ax.transAxes, ha="left", va="top", fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90)
        _add_year_separators(ax)
        apply_theme(ax, theme, xlabel="", ylabel="")

    for ax in axes[:, 0]:
        ax.set_ylabel("Indice")
    for ax in axes[-1, :]:
        ax.set_xlabel("Campanha")

    handles = [
        Line2D([0], [0], marker="o", color=primary, label="Shannon"),
        Line2D([0], [0], marker="s", color=secondary, label="Pielou"),
        Line2D([0], [0], color=primary, linestyle="--", linewidth=0.8, label=f"Media Shannon ({shannon_mean:.2f})"),
        Line2D([0], [0], color=secondary, linestyle="--", linewidth=0.8, label=f"Media Pielou ({pielou_mean:.2f})"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _group_low_abundance_orders(df_year: pd.DataFrame, max_categories: int = 8) -> tuple[pd.DataFrame, list[str]]:
    totals = df_year.groupby("ordem_plot")["contagem"].sum().sort_values(ascending=False)
    top_orders = totals.head(max_categories).index.tolist()
    has_other = len(totals) > len(top_orders)

    df_grouped = df_year.copy()
    df_grouped["ordem_plot_agrupada"] = np.where(
        df_grouped["ordem_plot"].isin(top_orders),
        df_grouped["ordem_plot"],
        "Demais ordens",
    )
    categories = top_orders + (["Demais ordens"] if has_other else [])
    return df_grouped, categories


def _plot_06_year_panels(
    df: pd.DataFrame,
    campaigns: list[str],
    points: list[str],
    output_dir: Path,
    theme: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    apply_rcparams(theme)
    work = df.copy()
    work["ordem_plot"] = work.apply(_order_label, axis=1)
    work["ano"] = work["nome_campanha"].map(_campaign_year)

    absolute_rows: list[pd.DataFrame] = []
    relative_rows: list[pd.DataFrame] = []

    for year in sorted(work["ano"].dropna().unique().tolist()):
        year_campaigns = [campaign for campaign in campaigns if _campaign_year(campaign) == year]
        if not year_campaigns:
            continue
        df_year = work[work["nome_campanha"].isin(year_campaigns)].copy()
        df_year, categories = _group_low_abundance_orders(df_year)
        palette = palette_from_theme(theme, len(categories))
        color_map = {category: palette[i] for i, category in enumerate(categories)}

        grouped = (
            df_year.groupby(["nome_campanha", "nome_ponto", "ordem_plot_agrupada"], as_index=False)["contagem"]
            .sum()
            .rename(columns={"ordem_plot_agrupada": "ordem"})
        )

        abs_tables: dict[str, pd.DataFrame] = {}
        rel_tables: dict[str, pd.DataFrame] = {}
        max_total = 0.0
        for campaign in year_campaigns:
            pivot = (
                grouped[grouped["nome_campanha"] == campaign]
                .pivot_table(index="nome_ponto", columns="ordem", values="contagem", aggfunc="sum", fill_value=0)
                .reindex(index=points, columns=categories, fill_value=0)
            )
            abs_tables[campaign] = pivot
            max_total = max(max_total, float(pivot.sum(axis=1).max()))
            rel_tables[campaign] = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100

            abs_export = pivot.reset_index().melt(id_vars="nome_ponto", var_name="ordem", value_name="abundancia")
            abs_export.insert(0, "nome_campanha", campaign)
            abs_export.insert(0, "ano", year)
            absolute_rows.append(abs_export)

            rel_export = rel_tables[campaign].reset_index().melt(
                id_vars="nome_ponto",
                var_name="ordem",
                value_name="abundancia_relativa_pct",
            )
            rel_export.insert(0, "nome_campanha", campaign)
            rel_export.insert(0, "ano", year)
            relative_rows.append(rel_export)

        for suffix, tables, ylabel, relative in [
            ("06B_teste_abundancia_ordem_por_ano", abs_tables, "Abundancia", False),
            ("06C_teste_abundancia_relativa_ordem_por_ano", rel_tables, "Abundancia relativa (%)", True),
        ]:
            fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27), dpi=int(theme.get("dpi", 600)), sharey=True)
            for ax, campaign in zip(axes.ravel(), year_campaigns):
                pivot = tables[campaign]
                x = np.arange(len(points))
                bottom = np.zeros(len(points))
                for category in categories:
                    values = pivot[category].to_numpy(dtype=float)
                    ax.bar(
                        x,
                        values,
                        bottom=bottom,
                        color=color_map[category],
                        edgecolor="black",
                        linewidth=0.45,
                        width=0.72,
                    )
                    bottom += values
                ax.text(0.02, 0.92, _campaign_short(campaign), transform=ax.transAxes, ha="left", va="top", fontweight="bold")
                ax.set_xticks(x)
                ax.set_xticklabels(points, rotation=0)
                if relative:
                    ax.set_ylim(0, 100)
                else:
                    ax.set_ylim(0, max(max_total * 1.12, 1.0))
                apply_theme(ax, theme, xlabel="", ylabel="")

            for ax in axes[:, 0]:
                ax.set_ylabel(ylabel)
            for ax in axes[-1, :]:
                ax.set_xlabel("Ponto amostral")
            for ax in axes.ravel()[len(year_campaigns):]:
                ax.axis("off")

            handles = [Patch(facecolor=color_map[category], edgecolor="black", label=category) for category in categories]
            fig.legend(handles=handles, loc="upper center", ncol=min(4, max(1, len(categories))), frameon=False)
            fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.90])
            fig.savefig(output_dir / f"{suffix}_{year}_zoobentos.png", dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
            plt.close(fig)

    absolute = pd.concat(absolute_rows, ignore_index=True) if absolute_rows else pd.DataFrame()
    relative = pd.concat(relative_rows, ignore_index=True) if relative_rows else pd.DataFrame()
    return absolute, relative


def run(output_dir: Path, env_file: str | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = _style_theme(load_theme(ROOT / "configs", "geoher001"))
    df, campaigns, points = _prepare_base(env_file)
    tables = _metric_tables(df, campaigns, points)
    abs_06, rel_06 = _plot_06_year_panels(df, campaigns, points, output_dir, theme)

    xlsx = output_dir / "00_base_metricas_teste_layout_bentos.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        tables["riqueza"].to_excel(writer, sheet_name="riqueza", index=False)
        tables["abundancia"].to_excel(writer, sheet_name="abundancia", index=False)
        tables["diversidade"].to_excel(writer, sheet_name="diversidade", index=False)
        abs_06.to_excel(writer, sheet_name="06_abund_ordem", index=False)
        rel_06.to_excel(writer, sheet_name="06_pct_ordem", index=False)

    _small_multiple_metric(
        tables["riqueza"],
        "riqueza",
        "Riqueza",
        output_dir / "02A_teste_minigraficos_riqueza_temporal_por_ponto_zoobentos.png",
        theme,
        points,
        campaigns,
    )
    _box_strip_metric(
        tables["riqueza"],
        "riqueza",
        "Riqueza",
        output_dir / "02B_teste_boxplot_riqueza_por_ponto_zoobentos.png",
        theme,
        points,
    )
    _small_multiple_metric(
        tables["abundancia"],
        "abundancia_total",
        "Abundancia total",
        output_dir / "03A_teste_minigraficos_abundancia_temporal_por_ponto_zoobentos.png",
        theme,
        points,
        campaigns,
    )
    _box_strip_metric(
        tables["abundancia"],
        "abundancia_total",
        "Abundancia total",
        output_dir / "03B_teste_boxplot_abundancia_por_ponto_zoobentos.png",
        theme,
        points,
    )
    _small_multiple_diversity(
        tables["diversidade"],
        output_dir / "10A_teste_minigraficos_diversidade_temporal_por_ponto_zoobentos.png",
        theme,
        points,
        campaigns,
    )

    manifest = output_dir / "README_teste_layout_bentos.md"
    manifest.write_text(
        "\n".join(
            [
                "# Teste de layouts - Zoobentos GEOHER001",
                "",
                "Recorte: C21-03-2022-CH a C36-11-2025-CH.",
                "Objetivo: testar alternativas aos graficos de barras agrupadas para muitas campanhas.",
                "",
                "Arquivos gerados:",
                "- 00_base_metricas_teste_layout_bentos.xlsx",
                "- 02A_teste_minigraficos_riqueza_temporal_por_ponto_zoobentos.png",
                "- 02B_teste_boxplot_riqueza_por_ponto_zoobentos.png",
                "- 03A_teste_minigraficos_abundancia_temporal_por_ponto_zoobentos.png",
                "- 03B_teste_boxplot_abundancia_por_ponto_zoobentos.png",
                "- 06B_teste_abundancia_ordem_por_ano_YYYY_zoobentos.png",
                "- 06C_teste_abundancia_relativa_ordem_por_ano_YYYY_zoobentos.png",
                "- 10A_teste_minigraficos_diversidade_temporal_por_ponto_zoobentos.png",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate GEOHER001 Zoobentos layout prototypes.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    run(Path(args.output_dir), args.env_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
