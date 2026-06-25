from __future__ import annotations

import re
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

from opyta_analysis.pipelines.diagnostico.darwincore_ief import export_darwincore_ief
from opyta_analysis.pipelines.diagnostico.occurrence_summary import export_occurrence_summary
from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import (
    apply_theme,
    get_figsize,
    get_figsize_by_complexity,
    get_tight_layout_rect,
    palette_from_theme,
    place_legend_below_x_axis,
)
from opyta_analysis.validators import validate_axes_style


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


def _taxon_final(row: pd.Series) -> str:
    for col in ["nome_cientifico", "genero", "familia", "ordem", "classe", "filo"]:
        value = row.get(col)
        if pd.notna(value) and str(value).strip() and str(value).strip().lower() != "nan":
            return str(value).strip()
    return "Taxon nao identificado"


def _load_zoobentos_df(project_id: int, group: str, env_file: str | None) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": project_id},
        select=(
            "id_ponto_coleta,nome_ponto,id_campanha,latitude,longitude,"
            "data_hora_coleta,bacia_hidrografica,curso_d_agua,municipio"
        ),
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}
    projetos = paginate(sb, "projetos", filters={"id_projeto": project_id}, select="nome_projeto")
    nome_projeto = projetos[0].get("nome_projeto") if projetos else "Projeto"

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": group},
        select=(
            "id_esforco,id_ponto_coleta,metodo_de_captura,esforco,"
            "unidade_esforco,tipo_amostragem,tipo_de_amostragem"
        ),
    )
    esforcos_proj = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos_proj:
        return pd.DataFrame()

    esforcos_map = {e["id_esforco"]: e for e in esforcos_proj}
    esforco_ids = set(esforcos_map.keys())

    table_by_group = {
        "zoobentos": ("resultados_zoobentos", "abundancia"),
    }
    group_key = group.strip().lower()
    if group_key not in table_by_group:
        raise ValueError(f"Unsupported group for this pipeline: {group}")

    result_table, abundance_col = table_by_group[group_key]
    resultados = paginate(
        sb,
        result_table,
        select=f"id_resultado_bento,id_esforco,id_especie,{abundance_col},tipo_amostragem",
    )
    resultados_proj = [r for r in resultados if r.get("id_esforco") in esforco_ids]
    if not resultados_proj:
        return pd.DataFrame()

    especies = paginate(
        sb,
        "especies",
        select="id_especie,nome_cientifico,reino,filo,classe,ordem,familia,genero,bmwp_score",
    )
    esp_map = {e["id_especie"]: e for e in especies}

    rows = []
    for r in resultados_proj:
        e = esforcos_map.get(r.get("id_esforco"), {})
        p = pontos_map.get(e.get("id_ponto_coleta"), {})
        s = esp_map.get(r.get("id_especie"), {})
        rows.append(
            {
                "id_resultado_pk": r.get("id_resultado_bento"),
                "nome_projeto": nome_projeto,
                "nome_ponto": p.get("nome_ponto"),
                "nome_campanha": camp_map.get(p.get("id_campanha"), "Campanha desconhecida"),
                "latitude": p.get("latitude"),
                "longitude": p.get("longitude"),
                "data_hora_coleta": p.get("data_hora_coleta"),
                "bacia_hidrografica": p.get("bacia_hidrografica") or p.get("curso_d_agua"),
                "metodo_de_captura": e.get("metodo_de_captura"),
                "esforco": e.get("esforco"),
                "unidade_esforco": e.get("unidade_esforco"),
                "tipo_amostragem": r.get("tipo_amostragem") or e.get("tipo_amostragem") or e.get("tipo_de_amostragem"),
                "nome_cientifico": s.get("nome_cientifico"),
                "reino": s.get("reino"),
                "filo": s.get("filo"),
                "classe": s.get("classe"),
                "ordem": s.get("ordem"),
                "familia": s.get("familia"),
                "genero": s.get("genero"),
                "bmwp_score": s.get("bmwp_score", 0),
                "contagem": r.get(abundance_col, 0),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    df["nome_ponto"] = df["nome_ponto"].astype(str).str.strip()
    df["nome_campanha"] = df["nome_campanha"].astype(str).str.strip()
    df["bmwp_score"] = pd.to_numeric(df["bmwp_score"], errors="coerce").fillna(0)
    df["taxon_final"] = df.apply(_taxon_final, axis=1)
    return df


def _apply_campaign_filter(df: pd.DataFrame, campaign_filter: list[str] | None) -> tuple[pd.DataFrame, dict]:
    requested = [str(c).strip() for c in campaign_filter or [] if str(c).strip()]
    if not requested or "nome_campanha" not in df.columns:
        return df, {"requested": requested, "matched": [], "missing": []}

    campaign_values = df["nome_campanha"].astype(str).str.strip()
    available = set(campaign_values.dropna().unique().tolist())
    matched = [campaign for campaign in requested if campaign in available]
    missing = [campaign for campaign in requested if campaign not in available]
    filtered = df[campaign_values.isin(requested)].copy()
    return filtered.reset_index(drop=True), {"requested": requested, "matched": matched, "missing": missing}


def _campaign_boundaries(campaigns: list[str]) -> list[int]:
    boundaries = [0]
    for i in range(1, len(campaigns)):
        if campaigns[i] != campaigns[i - 1]:
            boundaries.append(i)
    boundaries.append(len(campaigns))
    return boundaries


def _font_annotation(theme: dict) -> int:
    return int(theme.get("annotation_size", theme.get("font_size_base", 10)))


def _font_campaign(theme: dict) -> int:
    return int(theme.get("campaign_label_size", theme.get("font_size_base", 10)))


def _theme_palette(theme: dict, n: int) -> list[str]:
    return palette_from_theme(theme, max(n, 1))


def _theme_taxonomy_palette(theme: dict, n: int) -> list[str]:
    return _theme_palette(theme, n)


def _theme_stacked_contrast_palette(theme: dict, n: int) -> list[str]:
    colors = _theme_palette(theme, n)
    order: list[int] = []
    left = 0
    right = len(colors) - 1
    while left <= right:
        order.append(left)
        if left != right:
            order.append(right)
        left += 1
        right -= 1
    return [colors[i] for i in order]


def _campaign_short_label(campaign: str) -> str:
    match = re.match(r"^C0*(\d+)", str(campaign).strip(), flags=re.IGNORECASE)
    if match:
        return f"C{int(match.group(1)):02d}"
    return str(campaign).strip()


def _campaign_year(campaign: str) -> int | None:
    match = re.search(r"(20\d{2}|19\d{2})", str(campaign))
    return int(match.group(1)) if match else None


def _campaign_season(campaign: str) -> str:
    text = str(campaign).upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text):
        return "CH"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text):
        return "SC"
    return ""


def _season_colors(theme: dict) -> dict[str, str]:
    return {
        "CH": str(theme.get("primary_hex", "#002060")),
        "SC": str(theme.get("secondary_hex", "#5B9BD5")),
    }


def _mean_label(value: float, decimals: int = 1) -> str:
    return f"Media geral ({value:.{decimals}f})"


def _add_year_separators(ax, campaigns: list[str]) -> None:
    years = [_campaign_year(campaign) for campaign in campaigns]
    for i in range(1, len(years)):
        if years[i] != years[i - 1]:
            ax.axvline(i - 0.5, color="#D0D0D0", linewidth=0.7, linestyle="-", zorder=0)


def _category_label(value, fallback: str = "Nao informado") -> str:
    if pd.isna(value):
        return fallback
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return fallback
    return text


def _category_label_from_row(row: pd.Series, primary_col: str, fallback_cols: list[str]) -> str:
    primary = _category_label(row.get(primary_col), fallback="")
    if primary:
        return primary
    for col in fallback_cols:
        fallback = _category_label(row.get(col), fallback="")
        if fallback:
            return fallback
    return "Taxon nao identificado"


def _ordered_points_from_df(df: pd.DataFrame) -> list[str]:
    if "ordem_ponto" in df.columns:
        meta = df[["nome_ponto", "ordem_ponto"]].dropna(subset=["nome_ponto"]).copy()
        if not meta.empty:
            meta["nome_ponto"] = meta["nome_ponto"].astype(str).str.strip()
            meta["ordem_ponto"] = pd.to_numeric(meta["ordem_ponto"], errors="coerce")
            order = (
                meta.dropna(subset=["ordem_ponto"])
                .groupby("nome_ponto", as_index=False)["ordem_ponto"]
                .min()
                .sort_values(["ordem_ponto", "nome_ponto"])
            )
            if not order.empty:
                return order["nome_ponto"].tolist()
    return sorted(
        df["nome_ponto"].dropna().astype(str).str.strip().unique().tolist(),
        key=lambda value: (int(match.group(1)) if (match := re.search(r"(\d+)", str(value))) else 999999, str(value)),
    )


def _taxon_present(value: object) -> bool:
    return bool(_category_label(value, fallback=""))


def _nonzero_taxon_rows(df: pd.DataFrame) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if "contagem" in df.columns:
        mask &= pd.to_numeric(df["contagem"], errors="coerce").fillna(0) > 0
    if "taxon_final" in df.columns:
        mask &= df["taxon_final"].map(_taxon_present)
    return df.loc[mask].copy()


def _point_area_meta(df: pd.DataFrame) -> dict[str, str]:
    if "area_controle" not in df.columns:
        return {}
    meta = df[["nome_ponto", "area_controle"]].dropna(subset=["nome_ponto", "area_controle"]).copy()
    if meta.empty:
        return {}
    meta["nome_ponto"] = meta["nome_ponto"].astype(str).str.strip()
    meta["area_controle"] = meta["area_controle"].astype(str).str.strip()
    meta = meta[(meta["nome_ponto"] != "") & (meta["area_controle"] != "")]
    return meta.drop_duplicates("nome_ponto").set_index("nome_ponto")["area_controle"].to_dict()


def _area_color_map(theme: dict, labels: list[str]) -> dict[str, str]:
    base = _theme_palette(theme, max(len(labels), 1))
    return {label: base[i % len(base)] for i, label in enumerate(labels)}


def _draw_area_groups(ax, points: list[str], df: pd.DataFrame, theme: dict, *, y: float = -0.13) -> bool:
    area_by_point = _point_area_meta(df)
    if not points or not area_by_point:
        return False

    labels = [area_by_point.get(str(point)) for point in points]
    if not any(labels):
        return False

    unique_labels = []
    for label in labels:
        if label and label not in unique_labels:
            unique_labels.append(label)
    colors = _area_color_map(theme, unique_labels)

    start = None
    current = None
    for i, label in enumerate(labels + [None]):
        if label != current:
            if current is not None and start is not None:
                end = i - 1
                x_mid = (start + end) / 2
                ax.text(
                    x_mid,
                    y,
                    current,
                    transform=ax.get_xaxis_transform(),
                    ha="center",
                    va="top",
                    fontsize=_font_campaign(theme),
                    color=colors.get(current, str(theme.get("primary_hex", "#002060"))),
                )
            if i > 0 and i < len(labels):
                ax.axvline(
                    i - 0.5,
                    color=str(theme.get("highlight_hex", theme.get("primary_hex", "#002060"))),
                    linewidth=1.2,
                    linestyle="--",
                    ymin=0.0,
                    ymax=0.96,
                )
            start = i
            current = label
    return True


def _point_area_colors(points: list[str], df: pd.DataFrame, theme: dict) -> list[str] | None:
    area_by_point = _point_area_meta(df)
    if not area_by_point:
        return None
    ordered_labels = []
    for point in points:
        label = area_by_point.get(str(point))
        if label and label not in ordered_labels:
            ordered_labels.append(label)
    colors = _area_color_map(theme, ordered_labels)
    return [colors.get(area_by_point.get(str(point), ""), str(theme.get("primary_hex", "#002060"))) for point in points]


def _render_campaign_labels(ax, campaigns: list[str], boundaries: list[int], fontsize: int = 12, y: float = -0.24):
    for i in range(len(boundaries) - 1):
        mid = boundaries[i] + (boundaries[i + 1] - boundaries[i]) / 2 - 0.5
        ax.text(mid, y, campaigns[boundaries[i]], ha="center", transform=ax.get_xaxis_transform(), fontsize=fontsize)


def _classify_bmwp(score: float) -> str:
    if score > 85:
        return "Muito boa"
    if score >= 64:
        return "Boa"
    if score >= 37:
        return "Regular"
    if score >= 17:
        return "Ruim"
    return "Pessima"


def _shannon(counts: np.ndarray) -> float:
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size == 0:
        return 0.0
    p = counts / counts.sum()
    return float(-np.sum(p * np.log(p)))


def _pielou(counts: np.ndarray) -> float:
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size <= 1:
        return 0.0
    return float(_shannon(counts) / np.log(counts.size))


def _jackknife_1(pres_abs: np.ndarray) -> float:
    k = pres_abs.shape[0]
    if k == 0:
        return 0.0
    spp_occ = pres_abs.sum(axis=0)
    s_obs = int((spp_occ > 0).sum())
    q1 = int((spp_occ == 1).sum())
    return float(s_obs + q1 * ((k - 1) / k))


def _small_multiple_metric(
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
    *,
    decimals: int = 1,
) -> None:
    if not points or not campaigns:
        return

    colors = _season_colors(theme)
    marker_size = float(theme.get("small_multiple_marker_size", 24))
    line_width = float(theme.get("small_multiple_linewidth", 1.0))
    point_label_size = int(theme.get("point_label_size", theme.get("font_size_base", 11)))
    ncols = min(4, max(1, len(points)))
    nrows = int(np.ceil(len(points) / ncols))
    base_size = theme.get("figsize_standard", [11.69, 8.27])
    fig_width = float(base_size[0])
    fig_height = max(float(base_size[1]), 3.0 * nrows)
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(fig_width, fig_height),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
        squeeze=False,
    )

    x = np.arange(len(campaigns))
    labels = [_campaign_short_label(c) for c in campaigns]
    values_all = pd.to_numeric(table[value_col], errors="coerce").fillna(0)
    overall_mean = float(values_all.mean()) if not values_all.empty else 0.0
    ymax = max(float(values_all.max()) if not values_all.empty else 0.0, overall_mean)
    ymax = max(ymax * 1.15, 1.0)

    for ax, point in zip(axes.ravel(), points):
        point_data = table[table["nome_ponto"] == point].set_index("nome_campanha").reindex(campaigns).reset_index()
        values = pd.to_numeric(point_data[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        seasons = [_campaign_season(c) for c in campaigns]
        ax.plot(x, values, color="#606060", linewidth=line_width, zorder=1)
        for season in ["CH", "SC"]:
            mask = np.array([s == season for s in seasons])
            ax.scatter(
                x[mask],
                values[mask],
                s=marker_size,
                color=colors[season],
                edgecolor="black",
                linewidth=0.4,
                zorder=2,
            )
        unknown_mask = np.array([s not in {"CH", "SC"} for s in seasons])
        if unknown_mask.any():
            ax.scatter(
                x[unknown_mask],
                values[unknown_mask],
                s=marker_size,
                color=str(theme.get("primary_hex", "#11420C")),
                edgecolor="black",
                linewidth=0.4,
                zorder=2,
            )
        ax.axhline(overall_mean, color="#7F7F7F", linewidth=0.9, linestyle="--", zorder=0)
        ax.text(
            0.02,
            0.92,
            point,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontweight="bold",
            fontsize=point_label_size,
        )
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90)
        _add_year_separators(ax, campaigns)
        apply_theme(ax, theme, xlabel="", ylabel="")

    for ax in axes.ravel()[len(points):]:
        ax.axis("off")
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)
    for ax in axes[-1, :]:
        ax.set_xlabel("Campanha")

    seasons_present = {_campaign_season(c) for c in campaigns}
    handles = []
    if "CH" in seasons_present:
        handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=colors["CH"],
                markeredgecolor="black",
                label="CH",
            )
        )
    if "SC" in seasons_present:
        handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=colors["SC"],
                markeredgecolor="black",
                label="SC",
            )
        )
    if seasons_present - {"CH", "SC"}:
        handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=str(theme.get("primary_hex", "#11420C")),
                markeredgecolor="black",
                label="Campanha",
            )
        )
    handles.append(
        Line2D(
            [0],
            [0],
            color="#7F7F7F",
            linestyle="--",
            linewidth=0.9,
            label=_mean_label(overall_mean, decimals),
        )
    )
    fig.legend(handles=handles, loc="upper center", ncol=min(3, len(handles)), frameon=False)
    fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _few_campaign_metric(
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
    df: pd.DataFrame,
) -> None:
    if not points or not campaigns:
        return

    pivot = (
        table.pivot_table(
            index="nome_ponto",
            columns="nome_campanha",
            values=value_col,
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(index=points, columns=campaigns, fill_value=0)
    )
    campaign_colors = _theme_palette(theme, len(campaigns))
    size = get_figsize_by_complexity(theme, n_categories=len(points), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(points))
    width = 0.8 / max(len(campaigns), 1)
    ymax = max(float(pivot.to_numpy(dtype=float).max()), 1.0)
    ax.set_ylim(0, ymax * 1.14)

    for i, campaign in enumerate(campaigns):
        values = pivot[campaign].to_numpy(dtype=float)
        bar_colors = _point_area_colors(points, df, theme) if len(campaigns) == 1 else campaign_colors[i]
        bars = ax.bar(
            x + (i - (len(campaigns) - 1) / 2) * width,
            values,
            width=width,
            label=campaign,
            color=bar_colors,
            edgecolor="black",
            linewidth=0.8,
        )
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                float(value) if value > 0 else ymax * 0.015,
                f"{int(round(value))}",
                ha="center",
                va="bottom",
                fontsize=_font_annotation(theme),
                color="black" if value > 0 else "#666666",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(points, ha="right")
    apply_theme(
        ax,
        theme,
        xlabel="Ponto amostral",
        ylabel=ylabel,
        x_tick_rotation=0 if _point_area_meta(df) else 45,
    )
    area_drawn = _draw_area_groups(ax, points, df, theme, y=-0.13)
    has_legend = len(campaigns) > 1
    if has_legend:
        place_legend_below_x_axis(fig, ax, theme)
    validate_axes_style(ax, theme)
    fig.tight_layout(
        rect=get_tight_layout_rect(
            theme,
            has_legend=has_legend,
            extra_bottom=0.12 if area_drawn else 0.04,
        )
    )
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _small_multiple_diversity(
    diversity: pd.DataFrame,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
) -> None:
    if not points or not campaigns:
        return

    primary = str(theme.get("primary_hex", "#002060"))
    secondary = str(theme.get("secondary_hex", "#5B9BD5"))
    marker_size = max(float(theme.get("small_multiple_marker_size", 38)) ** 0.5, 3.0)
    line_width = float(theme.get("small_multiple_linewidth", 1.1))
    point_label_size = int(theme.get("point_label_size", theme.get("font_size_base", 11)))
    plot_data = diversity[diversity["nome_ponto"].isin(points)].copy()
    shannon_all = pd.to_numeric(plot_data["Shannon_H"], errors="coerce").fillna(0)
    pielou_all = pd.to_numeric(plot_data["Pielou_J"], errors="coerce").fillna(0)
    shannon_mean = float(shannon_all.mean()) if not shannon_all.empty else 0.0
    pielou_mean = float(pielou_all.mean()) if not pielou_all.empty else 0.0
    ymax = max(
        float(shannon_all.max()) if not shannon_all.empty else 0.0,
        float(pielou_all.max()) if not pielou_all.empty else 0.0,
        shannon_mean,
        pielou_mean,
        1.0,
    ) * 1.15

    ncols = min(4, max(1, len(points)))
    nrows = int(np.ceil(len(points) / ncols))
    base_size = theme.get("figsize_standard", [11.69, 8.27])
    fig_width = float(base_size[0])
    fig_height = max(float(base_size[1]), 3.0 * nrows)
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(fig_width, fig_height),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
        squeeze=False,
    )

    x = np.arange(len(campaigns))
    labels = [_campaign_short_label(c) for c in campaigns]
    for ax, point in zip(axes.ravel(), points):
        point_data = plot_data[plot_data["nome_ponto"] == point].set_index("nome_campanha").reindex(campaigns).reset_index()
        shannon = pd.to_numeric(point_data["Shannon_H"], errors="coerce").fillna(0).to_numpy(dtype=float)
        pielou = pd.to_numeric(point_data["Pielou_J"], errors="coerce").fillna(0).to_numpy(dtype=float)
        ax.plot(x, shannon, color=primary, marker="o", markersize=marker_size, linewidth=line_width)
        ax.plot(x, pielou, color=secondary, marker="s", markersize=marker_size, linewidth=line_width)
        ax.axhline(shannon_mean, color=primary, linewidth=0.8, linestyle="--", alpha=0.75)
        ax.axhline(pielou_mean, color=secondary, linewidth=0.8, linestyle="--", alpha=0.75)
        ax.text(
            0.02,
            0.92,
            point,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontweight="bold",
            fontsize=point_label_size,
        )
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=90)
        _add_year_separators(ax, campaigns)
        apply_theme(ax, theme, xlabel="", ylabel="")

    for ax in axes.ravel()[len(points):]:
        ax.axis("off")
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
    df_plot_base: pd.DataFrame,
    group: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
    points_order: list[str],
    campaign_order: list[str],
) -> dict:
    if df_plot_base.empty or not points_order or not campaign_order:
        return {"years": []}

    group_slug = group.lower()
    work = df_plot_base.copy()
    work["ordem_plot"] = work.apply(
        lambda row: _category_label_from_row(row, "ordem", ["taxon_final", "familia", "classe", "filo"]),
        axis=1,
    )
    work["ano"] = work["nome_campanha"].map(_campaign_year)

    absolute_rows: list[pd.DataFrame] = []
    relative_rows: list[pd.DataFrame] = []
    years: list[int] = []
    base_size = theme.get("figsize_standard", [11.69, 8.27])
    panel_title_size = int(theme.get("point_label_size", theme.get("font_size_base", 11)))

    for year in sorted(work["ano"].dropna().astype(int).unique().tolist()):
        year_campaigns = [campaign for campaign in campaign_order if _campaign_year(campaign) == year]
        if not year_campaigns:
            continue
        years.append(int(year))

        df_year = work[work["nome_campanha"].isin(year_campaigns)].copy()
        df_year, categories = _group_low_abundance_orders(df_year)
        palette = _theme_stacked_contrast_palette(theme, len(categories))
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
                .reindex(index=points_order, columns=categories, fill_value=0)
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
            ("06B_grafico_abundancia_ordem_por_ano", abs_tables, "Abundancia", False),
            ("06C_grafico_abundancia_relativa_ordem_por_ano", rel_tables, "Abundancia relativa (%)", True),
        ]:
            fig, axes = plt.subplots(
                2,
                2,
                figsize=(float(base_size[0]), float(base_size[1])),
                dpi=int(theme.get("dpi", 600)),
                sharey=True,
            )
            for ax, campaign in zip(axes.ravel(), year_campaigns):
                pivot = tables[campaign]
                x = np.arange(len(points_order))
                bottom = np.zeros(len(points_order))
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
                ax.set_xticks(x)
                ax.set_xticklabels(points_order, rotation=0)
                ax.set_ylim(0, 100 if relative else max(max_total * 1.12, 1.0))
                apply_theme(ax, theme, xlabel="", ylabel="")
                ax.set_title(
                    _campaign_short_label(campaign),
                    loc="left",
                    fontsize=panel_title_size,
                    fontweight="bold",
                    pad=6,
                )

            for ax in axes[:, 0]:
                ax.set_ylabel(ylabel)
            for ax in axes[-1, :]:
                ax.set_xlabel("Ponto amostral")
            for ax in axes.ravel()[len(year_campaigns):]:
                ax.axis("off")

            handles = [Patch(facecolor=color_map[category], edgecolor="black", label=category) for category in categories]
            fig.legend(handles=handles, loc="upper center", ncol=min(4, max(1, len(categories))), frameon=False)
            fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.90])
            out_png = output_dir / f"{suffix}_{year}_{group_slug}.png"
            fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
            plt.close(fig)
            generated_files.append(str(out_png))

    absolute = pd.concat(absolute_rows, ignore_index=True) if absolute_rows else pd.DataFrame()
    relative = pd.concat(relative_rows, ignore_index=True) if relative_rows else pd.DataFrame()
    if not absolute.empty:
        out_abs = output_dir / f"06B_df_abundancia_ordem_por_ano_{group_slug}.xlsx"
        absolute.to_excel(out_abs, index=False, engine="openpyxl")
        generated_files.append(str(out_abs))
    if not relative.empty:
        out_rel = output_dir / f"06C_df_abundancia_relativa_ordem_por_ano_{group_slug}.xlsx"
        relative.to_excel(out_rel, index=False, engine="openpyxl")
        generated_files.append(str(out_rel))

    return {"years": years}


def _run_block_6(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    points_order = _ordered_points_from_df(df)
    campaign_order = sorted(df["nome_campanha"].dropna().unique().tolist())

    df_rich = (
        df.groupby("nome_ponto")["taxon_final"]
        .nunique()
        .reset_index()
        .rename(columns={"taxon_final": "riqueza_taxons"})
    )
    if points_order:
        df_rich = (
            df_rich.set_index("nome_ponto")
            .reindex(points_order, fill_value=0)
            .reset_index()
        )
    xlsx_06a = output_dir / f"06A_df_riqueza_total_por_ponto_{group.lower()}.xlsx"
    df_rich.to_excel(xlsx_06a, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_06a))

    size_06a = get_figsize_by_complexity(theme, n_categories=len(df_rich), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=(size_06a[0], size_06a[1]), dpi=int(theme.get("dpi", 600)))
    area_colors = _point_area_colors(df_rich["nome_ponto"].astype(str).tolist(), df, theme)
    bars = ax.bar(
        df_rich["nome_ponto"].tolist(),
        df_rich["riqueza_taxons"].tolist(),
        color=area_colors or str(theme.get("primary_hex", "#11420C")),
        edgecolor="black",
        linewidth=1.0,
    )
    apply_theme(
        ax,
        theme,
        xlabel="Ponto amostral",
        ylabel="Numero de taxons",
        x_tick_rotation=0 if area_colors else 45,
    )
    for bar, value in zip(bars, df_rich["riqueza_taxons"].tolist()):
        y_top = ax.get_ylim()[1]
        y_value = float(value)
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y_value if y_value > 0 else y_top * 0.025,
            f"{int(value)}",
            ha="center",
            va="bottom",
            fontsize=_font_annotation(theme),
            color="black" if y_value > 0 else "#666666",
        )

    area_drawn = _draw_area_groups(ax, df_rich["nome_ponto"].astype(str).tolist(), df, theme, y=-0.13)
    validate_axes_style(ax, theme)
    if area_drawn:
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=False, extra_bottom=0.10))
    png_06a = output_dir / f"06A_grafico_riqueza_total_por_ponto_{group.lower()}.png"
    fig.savefig(png_06a, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_06a))

    df_plot_base = _nonzero_taxon_rows(df)
    year_result = _plot_06_year_panels(
        df_plot_base=df_plot_base,
        group=group,
        theme=theme,
        output_dir=output_dir,
        generated_files=generated_files,
        points_order=points_order,
        campaign_order=campaign_order,
    )

    return {"campaigns": campaign_order, **year_result}


def _run_block_3(df: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    def _mode_or_first(series: pd.Series):
        s = series.dropna().astype(str).str.strip()
        s = s[(s != "") & (s.str.lower() != "nan")]
        if s.empty:
            return np.nan
        modes = s.mode()
        return modes.iloc[0] if not modes.empty else s.iloc[0]

    map_campaign = {
        "Campanha-01-Seca": "C1",
        "Campanha-02-Chuva": "C2",
        "1º Campanha (Seca)": "C1",
        "2º Campanha (Chuva)": "C2",
    }

    occ = (
        df.groupby("taxon_final")["nome_campanha"]
        .apply(lambda s: sorted({map_campaign.get(str(x).strip(), str(x).strip()) for x in s.dropna().unique()}))
        .reset_index(name="occ_list")
    )
    occ["Ocorrência (Campanhas)"] = occ["occ_list"].apply(lambda lst: " e ".join(lst))
    occ = occ.drop(columns=["occ_list"])

    table = (
        df.groupby("taxon_final", as_index=False)
        .agg(
            filo=("filo", _mode_or_first),
            classe=("classe", _mode_or_first),
            ordem=("ordem", _mode_or_first),
            familia=("familia", _mode_or_first),
            genero=("genero", _mode_or_first),
        )
        .merge(occ, on="taxon_final", how="left")
    )

    table = table.rename(
        columns={
            "filo": "Filo",
            "classe": "Classe",
            "ordem": "Ordem",
            "familia": "Família",
            "genero": "Gênero",
            "taxon_final": "Táxon",
        }
    )
    cols = ["Filo", "Classe", "Ordem", "Família", "Gênero", "Táxon", "Ocorrência (Campanhas)"]
    table = table[[c for c in cols if c in table.columns]]
    for c in ["Filo", "Classe", "Ordem", "Família", "Gênero"]:
        if c in table.columns:
            table[c] = table[c].fillna("-").replace("", "-")
    sort_cols = [c for c in ["Filo", "Classe", "Ordem", "Família", "Gênero", "Táxon"] if c in table.columns]
    table = table.sort_values(sort_cols).reset_index(drop=True)

    out = output_dir / f"01_tabela_composicao_{group.lower()}.xlsx"
    table.to_excel(out, index=False, engine="openpyxl")
    generated_files.append(str(out))
    return {"taxa": int(len(table))}


def _run_block_4(
    df: pd.DataFrame,
    group: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
    base = df.copy()
    campaign_order = sorted(base["nome_campanha"].dropna().unique().tolist())
    points_all = sorted(base["nome_ponto"].dropna().unique().tolist())
    taxa_all = sorted(base["taxon_final"].dropna().unique().tolist())

    blocks = []
    for campaign in campaign_order:
        d = base[base["nome_campanha"] == campaign].copy()
        if d.empty:
            continue
        points_c = sorted(d["nome_ponto"].dropna().unique().tolist())
        pivot = (
            d.pivot_table(index="taxon_final", columns="nome_ponto", values="contagem", aggfunc="sum", fill_value=0)
            .reindex(index=taxa_all, columns=points_all, fill_value=0)
        )

        valid_points = [p for p in points_all if p in points_c]
        total_points = max(1, len(valid_points))
        if valid_points:
            pivot["OC"] = (pivot[valid_points] > 0).sum(axis=1)
            pivot["%OC"] = (pivot["OC"] / total_points) * 100
        else:
            pivot["OC"] = 0
            pivot["%OC"] = 0

        abundance = pivot[points_all].sum(axis=0)
        abundance.name = "Abundância"
        richness = (pivot[points_all] > 0).sum(axis=0)
        richness.name = "Riqueza"
        campaign_table = pd.concat([pivot, abundance.to_frame().T, richness.to_frame().T], axis=0)
        blocks.append((campaign, campaign_table))

    if not blocks:
        return {"campaigns": campaign_order}

    campaigns_ok = [c for c, _t in blocks]
    tables = [_t for _c, _t in blocks]
    final = pd.concat(tables, axis=1, keys=campaigns_ok)
    final.index.name = "Táxon"
    final = final.fillna("")
    for c in campaigns_ok:
        if (c, "%OC") in final.columns:
            final[(c, "%OC")] = final[(c, "%OC")].apply(
                lambda x: f"{int(round(x))}%" if isinstance(x, (int, float, np.integer, np.floating)) else x
            )

    out = output_dir / f"04_5_tabela_ocorrencia_{group.lower()}.xlsx"
    final.to_excel(out, sheet_name="Ocorrencia")
    generated_files.append(str(out))
    complete_sampling_units = pd.DataFrame(
        pd.MultiIndex.from_product(
            [campaign_order, points_all],
            names=["nome_campanha", "nome_ponto"],
        ).tolist(),
        columns=["nome_campanha", "nome_ponto"],
    )
    occurrence_summary = export_occurrence_summary(
        records=base,
        sampling_units=complete_sampling_units,
        taxon_col="taxon_final",
        campaign_col="nome_campanha",
        point_col="nome_ponto",
        abundance_col="contagem",
        metadata_map={
            "filo": "Filo",
            "classe": "Classe",
            "ordem": "Ordem",
            "familia": "Família",
            "genero": "Gênero",
        },
        group_slug=group.lower(),
        output_dir=output_dir,
        theme=theme,
        generated_files=generated_files,
    )
    return {
        "campaigns": campaigns_ok,
        "sintese_ocorrencia": occurrence_summary,
    }


def _run_block_5(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    richness = (
        df.groupby(["nome_campanha", "nome_ponto"])["taxon_final"]
        .nunique()
        .reset_index()
        .rename(columns={"taxon_final": "riqueza"})
    )
    richness["nome_campanha"] = richness["nome_campanha"].astype(str).str.strip()
    richness["nome_ponto"] = richness["nome_ponto"].astype(str).str.strip()

    campaigns = sorted(richness["nome_campanha"].dropna().unique().tolist())
    points = _ordered_points_from_df(df)
    if campaigns and points:
        full_index = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"])
        richness = (
            richness.set_index(["nome_campanha", "nome_ponto"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )
    point_rank = {point: i for i, point in enumerate(points)}
    richness["_ordem_ponto"] = richness["nome_ponto"].map(point_rank).fillna(len(point_rank))
    richness = richness.sort_values(["nome_campanha", "_ordem_ponto", "nome_ponto"]).drop(columns="_ordem_ponto")

    out_df = output_dir / f"02_df_riqueza_por_ponto_{group.lower()}.xlsx"
    richness.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    out_png = output_dir / f"02_grafico_riqueza_por_ponto_{group.lower()}.png"
    if len(campaigns) <= 2:
        _few_campaign_metric(
            table=richness,
            value_col="riqueza",
            ylabel="Riqueza",
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            df=df,
        )
    else:
        _small_multiple_metric(
            table=richness,
            value_col="riqueza",
            ylabel="Riqueza",
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=1,
        )
    generated_files.append(str(out_png))

    abundance = (
        df.groupby(["nome_campanha", "nome_ponto"], dropna=False)["contagem"]
        .sum()
        .reset_index()
        .rename(columns={"contagem": "abundancia_total"})
    )
    abundance["nome_campanha"] = abundance["nome_campanha"].astype(str).str.strip()
    abundance["nome_ponto"] = abundance["nome_ponto"].astype(str).str.strip()
    if campaigns and points:
        full_index = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"])
        abundance = (
            abundance.set_index(["nome_campanha", "nome_ponto"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )
    out_abundance_df = output_dir / f"03_df_abundancia_por_ponto_{group.lower()}.xlsx"
    abundance.to_excel(out_abundance_df, index=False, engine="openpyxl")
    generated_files.append(str(out_abundance_df))

    out_abundance_png = output_dir / f"03_grafico_abundancia_por_ponto_{group.lower()}.png"
    if len(campaigns) <= 2:
        _few_campaign_metric(
            table=abundance,
            value_col="abundancia_total",
            ylabel="Abundancia total",
            out_png=out_abundance_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            df=df,
        )
    else:
        _small_multiple_metric(
            table=abundance,
            value_col="abundancia_total",
            ylabel="Abundancia total",
            out_png=out_abundance_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=1,
        )
    generated_files.append(str(out_abundance_png))
    return {"campaigns": campaigns}


def _run_block_7(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    df_ordem = df.copy()
    df_ordem["ordem"] = df_ordem.apply(
        lambda row: _category_label_from_row(row, "ordem", ["taxon_final", "familia", "classe", "filo"]),
        axis=1,
    )
    ordem_df = (
        df_ordem.groupby("ordem")["taxon_final"]
        .nunique()
        .reset_index()
        .rename(columns={"ordem": "ordem", "taxon_final": "numero_de_taxons"})
        .sort_values("numero_de_taxons", ascending=False)
        .reset_index(drop=True)
    )
    total_taxa = int(ordem_df["numero_de_taxons"].sum())

    out_df = output_dir / f"04_df_riqueza_por_ordem_{group.lower()}.xlsx"
    ordem_df.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    # Bar chart
    size_bar = get_figsize_by_complexity(theme, n_categories=len(ordem_df), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size_bar, dpi=int(theme.get("dpi", 600)))
    bars = ax.bar(ordem_df["ordem"], ordem_df["numero_de_taxons"], color=str(theme.get("primary_hex", "#11420C")), edgecolor="black", linewidth=0.8)
    apply_theme(ax, theme, xlabel="Ordem/taxon", ylabel="Número de táxons", x_tick_rotation=45)
    for b, v in zip(bars, ordem_df["numero_de_taxons"].tolist()):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{int(v)}", ha="center", va="bottom", fontsize=_font_annotation(theme))
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_bar = output_dir / f"04_grafico_riqueza_ordem_barras_{group.lower()}.png"
    fig.savefig(out_bar, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_bar))

    # Donut chart
    ordem_categories = sorted(ordem_df["ordem"].astype(str).tolist())
    donut_color_map = {
        cat: color for cat, color in zip(ordem_categories, _theme_taxonomy_palette(theme, len(ordem_categories)))
    }
    donut_colors = [donut_color_map[str(name)] for name in ordem_df["ordem"].tolist()]
    size_donut = get_figsize_by_complexity(theme, n_categories=len(ordem_df), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size_donut, dpi=int(theme.get("dpi", 600)))

    def _autopct_visible(pct: float) -> str:
        return f"{pct:.1f}%" if pct >= 4.0 else ""

    wedges, texts, autotexts = ax.pie(
        ordem_df["numero_de_taxons"].values,
        labels=None,
        colors=donut_colors,
        startangle=90,
        wedgeprops={"width": 0.45, "edgecolor": "black", "linewidth": 0.8},
        autopct=_autopct_visible,
        pctdistance=0.8,
        textprops={"fontsize": int(theme.get("font_size_base", 10))},
    )

    # Add external labels with smooth leader lines and simple collision-avoidance.
    label_data = []
    for i, wedge in enumerate(wedges):
        angle = 0.5 * (wedge.theta1 + wedge.theta2)
        angle_rad = np.deg2rad(angle)
        x = np.cos(angle_rad)
        y = np.sin(angle_rad)
        side = 1 if x >= 0 else -1
        label_data.append(
            {
                "idx": i,
                "name": str(ordem_df["ordem"].iloc[i]),
                "anchor": (0.82 * x, 0.82 * y),
                "target_y": 1.10 * y,
                "side": side,
            }
        )

    min_gap = 0.11
    y_lim = 1.34
    for side in (-1, 1):
        side_items = [d for d in label_data if d["side"] == side]
        side_items.sort(key=lambda d: d["target_y"])
        prev_y = -y_lim
        for item in side_items:
            y_adj = max(item["target_y"], prev_y + min_gap)
            y_adj = min(y_adj, y_lim)
            item["text_y"] = y_adj
            prev_y = y_adj

        for j in range(len(side_items) - 2, -1, -1):
            if side_items[j]["text_y"] > side_items[j + 1]["text_y"] - min_gap:
                side_items[j]["text_y"] = side_items[j + 1]["text_y"] - min_gap

        for item in side_items:
            text_x = 1.56 * side
            ha = "left" if side > 0 else "right"
            rad = 0.08 if side > 0 else -0.08
            ax.annotate(
                item["name"],
                xy=item["anchor"],
                xytext=(text_x, item["text_y"]),
                ha=ha,
                va="center",
                fontsize=int(theme.get("font_size_base", 10)),
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#555555",
                    "linewidth": 0.7,
                    "alpha": 0.8,
                    "shrinkA": 0,
                    "shrinkB": 0,
                    "connectionstyle": f"arc3,rad={rad}",
                },
            )

    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.35, 1.35)

    ax.text(0, 0, f"Total\n{total_taxa}", ha="center", va="center", fontsize=_font_annotation(theme), fontweight=str(theme.get("title_weight", "bold")))
    ax.set_facecolor(str(theme.get("background_color", "white")))
    ax.figure.set_facecolor(str(theme.get("background_color", "white")))
    fig.tight_layout()
    out_donut = output_dir / f"05_grafico_riqueza_ordem_rosca_{group.lower()}.png"
    fig.savefig(out_donut, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_donut))
    return {"ordens": int(len(ordem_df))}


def _run_block_9(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    mat = df.pivot_table(index="nome_ponto", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0, observed=False)
    mat = mat.loc[mat.sum(axis=1) > 0]
    if mat.shape[0] < 2:
        return {"points": int(mat.shape[0])}

    dist_cond = pdist(mat.values, metric="braycurtis")
    dist_sq = squareform(dist_cond)
    z = linkage(dist_cond, method="average")

    out_mat = output_dir / f"11_df_matriz_comunidade_{group.lower()}.xlsx"
    mat.to_excel(out_mat, engine="openpyxl")
    generated_files.append(str(out_mat))

    dist_df = pd.DataFrame(dist_sq, index=mat.index, columns=mat.index)
    out_dist = output_dir / f"11_df_distancias_braycurtis_{group.lower()}.xlsx"
    dist_df.to_excel(out_dist, engine="openpyxl")
    generated_files.append(str(out_dist))

    size_9 = get_figsize(theme, "wide")
    fig, ax = plt.subplots(figsize=size_9, dpi=int(theme.get("dpi", 600)))
    dendrogram(z, labels=mat.index.tolist(), orientation="right", ax=ax, color_threshold=None)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.0, 0.0)
    ticks_sim = np.arange(0, 101, 10)
    ticks_dist = 1 - (ticks_sim / 100.0)
    ax.set_xticks(ticks_dist)
    ax.set_xticklabels([str(t) for t in ticks_sim])
    apply_theme(
        ax,
        theme,
        xlabel="Similaridade de Bray-Curtis (%)",
        ylabel="",
    )
    validate_axes_style(ax, theme)
    fig.tight_layout()

    out_png = output_dir / f"11_dendrograma_similaridade_{group.lower()}.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))
    return {"points": int(mat.shape[0])}


def _run_block_8(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    species_col = "nome_cientifico"
    campaign_order = sorted(df["nome_campanha"].dropna().unique().tolist())
    points_order = _ordered_points_from_df(df)

    results: list[dict] = []
    for campaign in campaign_order:
        df_c = df[df["nome_campanha"] == campaign].copy()
        if df_c.empty:
            continue
        df_c_calc = _nonzero_taxon_rows(df_c)
        if df_c_calc.empty:
            mat = pd.DataFrame(index=points_order)
        else:
            mat = df_c_calc.pivot_table(
                index="nome_ponto",
                columns=species_col,
                values="contagem",
                aggfunc="sum",
                fill_value=0,
                observed=False,
            )
            if points_order:
                mat = mat.reindex(points_order, fill_value=0)
        for point in mat.index:
            row = mat.loc[point].values
            results.append(
                {
                    "nome_campanha": campaign,
                    "nome_ponto": point,
                    "Shannon_H": _shannon(row),
                    "Pielou_J": _pielou(row),
                }
            )
        total = mat.sum(axis=0).values
        results.append(
            {
                "nome_campanha": campaign,
                "nome_ponto": f"{campaign} (Geral)",
                "Shannon_H": _shannon(total),
                "Pielou_J": _pielou(total),
            }
        )

    df_div = pd.DataFrame(results)
    if df_div.empty:
        return {"campaigns": campaign_order}

    xlsx_10 = output_dir / f"10_df_diversidade_alfa_{group.lower()}.xlsx"
    df_div.to_excel(xlsx_10, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_10))

    png_10 = output_dir / f"10_grafico_diversidade_alfa_{group.lower()}.png"
    if len(campaign_order) <= 2:
        labels = df_div["nome_ponto"].tolist()
        shannon_vals = df_div["Shannon_H"].tolist()
        pielou_vals = df_div["Pielou_J"].tolist()
        x = np.arange(len(labels))

        size = get_figsize_by_complexity(theme, n_categories=len(labels), prefer_landscape=True)
        fig, ax1 = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
        ax1.bar(
            x,
            shannon_vals,
            color=str(theme.get("primary_hex", "#11420C")),
            edgecolor="black",
            linewidth=1.0,
            label="Diversidade (H')",
        )
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, ha="right")
        apply_theme(
            ax1,
            theme,
            xlabel="Ponto amostral",
            ylabel="Shannon (H')",
            x_tick_rotation=45,
        )

        ax2 = ax1.twinx()
        ax2.plot(
            x,
            pielou_vals,
            marker="o",
            linestyle="None",
            color=str(theme.get("secondary_hex", "#6A8F63")),
            markersize=6,
            label="Equitabilidade (J')",
        )
        ax2.set_ylabel("Pielou (J')")
        ax2.set_ylim(0, 1.1)

        split_n = 0
        for campaign in campaign_order[:-1]:
            split_n += df_div[df_div["nome_campanha"] == campaign].shape[0]
            if 0 < split_n < len(x):
                ax1.axvline(x=split_n - 0.5, color="#888888", linestyle="--", linewidth=1.5)

        handles_1, labels_1 = ax1.get_legend_handles_labels()
        handles_2, labels_2 = ax2.get_legend_handles_labels()
        place_legend_below_x_axis(
            fig,
            ax1,
            theme,
            handles=handles_1 + handles_2,
            labels=labels_1 + labels_2,
        )
        validate_axes_style(ax1, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.06))
        fig.savefig(png_10, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
    else:
        _small_multiple_diversity(
            diversity=df_div,
            out_png=png_10,
            theme=theme,
            points=points_order,
            campaigns=campaign_order,
        )
    generated_files.append(str(png_10))

    return {"campaigns": campaign_order}


def _run_block_10(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    species_col = "nome_cientifico"

    # Sampling units must be campaign-specific: same point in different campaigns counts as two samples.
    df_samples = df.copy()
    df_samples["amostra_id"] = (
        df_samples["nome_campanha"].astype(str).str.strip()
        + " | "
        + df_samples["nome_ponto"].astype(str).str.strip()
    )

    mat = df_samples.pivot_table(
        index="amostra_id",
        columns=species_col,
        values="contagem",
        aggfunc="sum",
        fill_value=0,
        observed=False,
    )
    mat_pa = (mat > 0).astype(int)
    mat_pa = mat_pa.loc[mat_pa.sum(axis=1) > 0]
    n_samples = mat_pa.shape[0]
    if n_samples < 2:
        return {"samples": int(n_samples)}

    n_random = 200
    rng = np.random.default_rng(42)
    mat_values = mat_pa.values
    sobs_curves = np.zeros((n_random, n_samples), dtype=float)
    sest_curves = np.zeros((n_random, n_samples), dtype=float)

    for r in range(n_random):
        idx = rng.permutation(n_samples)
        shuffled = mat_values[idx, :]
        for i in range(1, n_samples + 1):
            subset = shuffled[:i, :]
            spp_occ = subset.sum(axis=0)
            sobs_curves[r, i - 1] = float((spp_occ > 0).sum())
            sest_curves[r, i - 1] = _jackknife_1(subset)

    mean_sobs = sobs_curves.mean(axis=0)
    mean_sest = sest_curves.mean(axis=0)
    std_sest = sest_curves.std(axis=0)
    x_axis = np.arange(1, n_samples + 1)

    df_curve = pd.DataFrame(
        {
            "n_amostras": x_axis,
            "riqueza_obs_media": mean_sobs,
            "riqueza_est_jackknife1_media": mean_sest,
            "jackknife1_desvio_padrao": std_sest,
            "jackknife1_inf": mean_sest - std_sest,
            "jackknife1_sup": mean_sest + std_sest,
        }
    )

    xlsx_12 = output_dir / f"12_df_curva_suficiencia_{group.lower()}.xlsx"
    df_curve.to_excel(xlsx_12, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_12))

    size_10 = get_figsize_by_complexity(theme, n_categories=n_samples, prefer_landscape=True)
    fig, ax = plt.subplots(figsize=(size_10[0], size_10[1]), dpi=int(theme.get("dpi", 600)))
    ax.plot(
        x_axis,
        mean_sobs,
        linewidth=2.2,
        label="Riqueza observada",
        color=str(theme.get("primary_hex", "#11420C")),
    )
    ax.plot(
        x_axis,
        mean_sest,
        linewidth=2.2,
        label="Riqueza estimada (Jackknife 1)",
        color=str(theme.get("secondary_hex", "#6A8F63")),
    )
    ax.fill_between(
        x_axis,
        mean_sest - std_sest,
        mean_sest + std_sest,
        alpha=0.18,
        color=str(theme.get("secondary_hex", "#6A8F63")),
    )

    apply_theme(
        ax,
        theme,
        xlabel="Numero de unidades amostrais",
        ylabel="Riqueza",
    )
    ax.text(x_axis[-1] + 0.15, mean_sobs[-1], f"{mean_sobs[-1]:.0f}", color="black", va="center", fontsize=_font_annotation(theme))
    ax.text(x_axis[-1] + 0.15, mean_sest[-1], f"{mean_sest[-1]:.1f}", color="black", va="center", fontsize=_font_annotation(theme))

    place_legend_below_x_axis(fig, ax, theme)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.04))

    png_12 = output_dir / f"12_curva_suficiencia_amostral_{group.lower()}.png"
    fig.savefig(png_12, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_12))

    return {"samples": int(n_samples)}


def _run_block_11(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    points_order = _ordered_points_from_df(df)
    point_rank = {point: i for i, point in enumerate(points_order)}
    df_bmwp = df.drop_duplicates(subset=["nome_campanha", "nome_ponto", "taxon_final"]).copy()
    df_bmwp["bmwp_score"] = pd.to_numeric(df_bmwp["bmwp_score"], errors="coerce").fillna(0)

    bmwp_scores = df_bmwp.groupby(["nome_campanha", "nome_ponto"], as_index=False)["bmwp_score"].sum()
    campaign_order = sorted(bmwp_scores["nome_campanha"].dropna().unique().tolist())
    if points_order and campaign_order:
        full_index = pd.MultiIndex.from_product([campaign_order, points_order], names=["nome_campanha", "nome_ponto"])
        bmwp_scores = (
            bmwp_scores.set_index(["nome_campanha", "nome_ponto"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )
    bmwp_scores["nome_campanha"] = pd.Categorical(bmwp_scores["nome_campanha"], categories=campaign_order, ordered=True)
    bmwp_scores["_ordem_ponto"] = bmwp_scores["nome_ponto"].map(point_rank).fillna(len(point_rank))
    bmwp_scores = bmwp_scores.sort_values(["nome_campanha", "_ordem_ponto", "nome_ponto"]).drop(columns="_ordem_ponto").reset_index(drop=True)
    bmwp_scores["classificacao"] = bmwp_scores["bmwp_score"].apply(_classify_bmwp)

    xlsx_11 = output_dir / f"11_df_bmwp_{group.lower()}.xlsx"
    bmwp_scores.to_excel(xlsx_11, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_11))

    legend_order = ["Muito boa", "Boa", "Regular", "Ruim", "Pessima"]
    use_technical = bool(theme.get("use_technical_colors", True))
    if use_technical:
        colors_map = {
            "Muito boa": str(theme.get("bmwp_color_muito_boa", "#00b0f0")),
            "Boa": str(theme.get("bmwp_color_boa", "#92d050")),
            "Regular": str(theme.get("bmwp_color_regular", "#ffff00")),
            "Ruim": str(theme.get("bmwp_color_ruim", "#ffc000")),
            "Pessima": str(theme.get("bmwp_color_pessima", "#ff0000")),
        }
    else:
        theme_colors = _theme_palette(theme, len(legend_order))
        colors_map = {
            label: theme_colors[i]
            for i, label in enumerate(legend_order)
        }

    dense_threshold = int(theme.get("dense_indicator_heatmap_threshold", 80))
    if len(bmwp_scores) > dense_threshold and campaign_order and points_order:
        score_mat = (
            bmwp_scores.pivot_table(
                index="nome_campanha",
                columns="nome_ponto",
                values="bmwp_score",
                aggfunc="sum",
                fill_value=0,
                observed=False,
            )
            .reindex(index=campaign_order, columns=points_order, fill_value=0)
        )
        class_mat = score_mat.applymap(_classify_bmwp)
        class_index = {label: i for i, label in enumerate(legend_order)}
        color_values = class_mat.replace(class_index).to_numpy(dtype=float)

        cmap = mcolors.ListedColormap([colors_map[label] for label in legend_order])
        norm = mcolors.BoundaryNorm(np.arange(len(legend_order) + 1) - 0.5, cmap.N)

        fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"), dpi=int(theme.get("dpi", 600)))
        ax.imshow(color_values, cmap=cmap, norm=norm, aspect="auto")
        ax.set_xticks(np.arange(len(points_order)))
        ax.set_xticklabels(points_order, rotation=0)
        ax.set_yticks(np.arange(len(campaign_order)))
        ax.set_yticklabels([_campaign_short_label(c) for c in campaign_order])
        apply_theme(ax, theme, xlabel="Ponto amostral", ylabel="Campanha")
        ax.grid(False)
        ax.set_xticks(np.arange(-0.5, len(points_order), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(campaign_order), 1), minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)

        for y, campaign in enumerate(campaign_order):
            for x, point in enumerate(points_order):
                value = float(score_mat.loc[campaign, point])
                label = class_mat.loc[campaign, point]
                face = colors_map.get(label, "#cccccc")
                r, g, b = mcolors.to_rgb(face)
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                ax.text(
                    x,
                    y,
                    f"{value:.0f}",
                    ha="center",
                    va="center",
                    fontsize=_font_annotation(theme),
                    color="white" if luminance < 0.45 else "black",
                )

        handles = [Patch(facecolor=colors_map[k], edgecolor="black", label=k) for k in legend_order]
        place_legend_below_x_axis(fig, ax, theme, handles=handles, labels=legend_order, ncol=len(legend_order))
        validate_axes_style(ax, {**theme, "grid_y": False, "grid_x": False})
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.02))

        png_11 = output_dir / f"11_grafico_bmwp_{group.lower()}.png"
        fig.savefig(png_11, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(png_11))
        return {"campaigns": campaign_order, "visual_layout": "heatmap"}

    fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(bmwp_scores))
    bar_colors = [colors_map.get(v, "#cccccc") for v in bmwp_scores["classificacao"]]
    bars = ax.bar(x, bmwp_scores["bmwp_score"].values, color=bar_colors, edgecolor="black", linewidth=0.8)

    apply_theme(
        ax,
        theme,
        xlabel="",
        ylabel="BMWP",
    )
    labels = bmwp_scores["nome_ponto"].astype(str).tolist()
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0 if _point_area_meta(df) else 90, ha="center")

    for i, (bar, val) in enumerate(zip(bars, bmwp_scores["bmwp_score"].values)):
        ax.text(i, bar.get_height() + 2, f"{val:.0f}", ha="center", fontsize=_font_annotation(theme))

    if _point_area_meta(df):
        _draw_area_groups(ax, labels, df, theme, y=-0.15)
    else:
        campaigns = bmwp_scores["nome_campanha"].astype(str).tolist()
        boundaries = _campaign_boundaries(campaigns)
        for boundary in boundaries[1:-1]:
            ax.axvline(x=boundary - 0.5, color="#888888", linestyle="--", linewidth=1.5)
        _render_campaign_labels(ax, campaigns, boundaries, fontsize=_font_campaign(theme), y=-0.20)

    handles = [Patch(facecolor=colors_map[k], edgecolor="black", label=k) for k in legend_order]
    place_legend_below_x_axis(fig, ax, theme, handles=handles, labels=legend_order, ncol=len(legend_order))
    validate_axes_style(ax, theme)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.28 if _point_area_meta(df) else 0.22)

    png_11 = output_dir / f"11_grafico_bmwp_{group.lower()}.png"
    fig.savefig(png_11, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_11))

    return {"campaigns": campaign_order}


def _run_block_12(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    points_order = _ordered_points_from_df(df)
    point_rank = {point: i for i, point in enumerate(points_order)}
    ordens_ept = {"ephemeroptera", "plecoptera", "trichoptera"}
    familias_chironomidae = {"chironomidae"}
    oligochaeta_terms = {"oligochaeta", "oligoqueta"}

    df_ept = df.copy()
    for col in ["classe", "ordem", "familia", "nome_cientifico", "taxon_final"]:
        if col not in df_ept.columns:
            df_ept[col] = ""
        df_ept[col] = df_ept[col].astype(str).str.strip().str.lower()
    df_ept["eh_ept"] = df_ept["ordem"].isin(ordens_ept)
    df_ept["eh_chironomidae"] = df_ept["familia"].isin(familias_chironomidae)
    df_ept["eh_oligochaeta"] = df_ept[["classe", "ordem", "familia", "nome_cientifico", "taxon_final"]].isin(
        oligochaeta_terms
    ).any(axis=1)
    df_ept["eh_chol"] = df_ept["eh_chironomidae"] | df_ept["eh_oligochaeta"]

    grp = df_ept.groupby(["nome_campanha", "nome_ponto"])
    total = grp["contagem"].sum().rename("total")
    ept_ab = grp.apply(lambda d: d.loc[d["eh_ept"], "contagem"].sum()).rename("ept")
    chir_ab = grp.apply(lambda d: d.loc[d["eh_chironomidae"], "contagem"].sum()).rename("chironomidae")
    oligo_ab = grp.apply(lambda d: d.loc[d["eh_oligochaeta"], "contagem"].sum()).rename("oligochaeta")
    chol_ab = grp.apply(lambda d: d.loc[d["eh_chol"], "contagem"].sum()).rename("chol")

    df_index = pd.concat([total, ept_ab, chir_ab, oligo_ab, chol_ab], axis=1).reset_index()
    campaign_order = sorted(df_index["nome_campanha"].dropna().unique().tolist())
    if points_order and campaign_order:
        full_index = pd.MultiIndex.from_product([campaign_order, points_order], names=["nome_campanha", "nome_ponto"])
        df_index = (
            df_index.set_index(["nome_campanha", "nome_ponto"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )
    df_index["pct_ept"] = (df_index["ept"] / df_index["total"].replace(0, np.nan) * 100).fillna(0)
    df_index["pct_chol"] = (df_index["chol"] / df_index["total"].replace(0, np.nan) * 100).fillna(0)

    df_index["nome_campanha"] = pd.Categorical(df_index["nome_campanha"], categories=campaign_order, ordered=True)
    df_index["_ordem_ponto"] = df_index["nome_ponto"].map(point_rank).fillna(len(point_rank))
    df_index = df_index.sort_values(["nome_campanha", "_ordem_ponto", "nome_ponto"]).drop(columns="_ordem_ponto").reset_index(drop=True)

    xlsx_12 = output_dir / f"12_df_ept_chol_{group.lower()}.xlsx"
    df_index.to_excel(xlsx_12, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_12))

    # Figura 12: EPT em azul (indicador positivo) e CHOL em vermelho (pressao organica).
    ept_color = str(theme.get("ept_good_hex", "#1F77B4"))
    chol_color = str(theme.get("chol_bad_hex", theme.get("chironomidae_bad_hex", "#C00000")))

    dense_threshold = int(theme.get("dense_indicator_heatmap_threshold", 80))
    if len(df_index) > dense_threshold and campaign_order and points_order:
        ept_mat = (
            df_index.pivot_table(
                index="nome_campanha",
                columns="nome_ponto",
                values="pct_ept",
                aggfunc="sum",
                fill_value=0,
                observed=False,
            )
            .reindex(index=campaign_order, columns=points_order, fill_value=0)
        )
        chol_mat = (
            df_index.pivot_table(
                index="nome_campanha",
                columns="nome_ponto",
                values="pct_chol",
                aggfunc="sum",
                fill_value=0,
                observed=False,
            )
            .reindex(index=campaign_order, columns=points_order, fill_value=0)
        )

        cmap_ept = mcolors.LinearSegmentedColormap.from_list("ept_heatmap", ["#ffffff", ept_color])
        cmap_chol = mcolors.LinearSegmentedColormap.from_list("chol_heatmap", ["#ffffff", chol_color])
        fig, axes = plt.subplots(
            1,
            2,
            figsize=get_figsize(theme, "wide"),
            dpi=int(theme.get("dpi", 600)),
            sharex=True,
            sharey=True,
        )
        for idx, (ax, mat, cmap, label) in enumerate([
            (axes[0], ept_mat, cmap_ept, "%EPT"),
            (axes[1], chol_mat, cmap_chol, "%CHOL"),
        ]):
            im = ax.imshow(mat.to_numpy(dtype=float), cmap=cmap, vmin=0, vmax=100, aspect="auto")
            ax.set_yticks(np.arange(len(campaign_order)))
            ax.set_yticklabels([_campaign_short_label(c) for c in campaign_order])
            ax.set_xticks(np.arange(len(points_order)))
            ax.set_xticklabels(points_order, rotation=0)
            apply_theme(
                ax,
                theme,
                title=label,
                xlabel="Ponto amostral",
                ylabel="Campanha" if idx == 0 else "",
            )
            ax.tick_params(
                axis="both",
                labelsize=int(theme.get("heatmap_tick_size", theme.get("font_size_base", 11))),
            )
            ax.grid(False)
            ax.set_xticks(np.arange(-0.5, len(points_order), 1), minor=True)
            ax.set_yticks(np.arange(-0.5, len(campaign_order), 1), minor=True)
            ax.grid(which="minor", color="#D9D9D9", linestyle="-", linewidth=0.7)
            ax.tick_params(which="minor", bottom=False, left=False)

            values = mat.to_numpy(dtype=float)
            for y in range(values.shape[0]):
                for x in range(values.shape[1]):
                    value = float(values[y, x])
                    if abs(value) < 1e-12:
                        continue
                    ax.text(
                        x,
                        y,
                        f"{value:.0f}",
                        ha="center",
                        va="center",
                        fontsize=int(theme.get("heatmap_annotation_size", _font_annotation(theme))),
                        color="white" if value >= 65 else "black",
                    )
            cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
            cbar.set_label(label)

        validate_axes_style(axes[0], {**theme, "grid_y": False, "grid_x": False})
        validate_axes_style(axes[1], {**theme, "grid_y": False, "grid_x": False})
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=False, extra_bottom=0.02))

        png_12 = output_dir / f"12_grafico_ept_chol_{group.lower()}.png"
        fig.savefig(png_12, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(png_12))
        return {"campaigns": campaign_order, "visual_layout": "heatmap"}

    fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(df_index))
    width = 0.72
    ax.bar(
        x,
        df_index["pct_ept"].values,
        width=width,
        label="%EPT",
        color=ept_color,
        edgecolor="black",
        linewidth=0.8,
    )
    ax.bar(
        x,
        df_index["pct_chol"].values,
        bottom=df_index["pct_ept"].values,
        width=width,
        label="%CHOL",
        color=chol_color,
        edgecolor="black",
        linewidth=0.8,
    )

    apply_theme(
        ax,
        theme,
        xlabel="",
        ylabel="% por ponto",
    )
    ax.set_xticks(x)
    point_labels = df_index["nome_ponto"].astype(str).tolist()
    ax.set_xticklabels(point_labels, rotation=0 if _point_area_meta(df) else 90, ha="center")

    if _point_area_meta(df):
        _draw_area_groups(ax, point_labels, df, theme, y=-0.15)
    else:
        campaigns = df_index["nome_campanha"].astype(str).tolist()
        boundaries = _campaign_boundaries(campaigns)
        for boundary in boundaries[1:-1]:
            ax.axvline(x=boundary - 0.5, color="#888888", linestyle="--", linewidth=1.5)
        _render_campaign_labels(ax, campaigns, boundaries, fontsize=_font_campaign(theme), y=-0.20)

    place_legend_below_x_axis(fig, ax, theme, ncol=2)
    validate_axes_style(ax, theme)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.28 if _point_area_meta(df) else 0.22)

    png_12 = output_dir / f"12_grafico_ept_chol_{group.lower()}.png"
    fig.savefig(png_12, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_12))

    return {"campaigns": campaign_order}


def _run_block_13(df: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    return export_darwincore_ief(
        df=df,
        group=group,
        output_dir=output_dir,
        generated_files=generated_files,
    )


def run_zoobentos_pipeline(
    project_id: int,
    group: str,
    theme: dict,
    output_dir: Path,
    env_file: str | None,
    block: str = "all",
    campaign_filter: list[str] | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    if block not in {"all", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"}:
        raise ValueError("Supported block values for zoobentos: all, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13")

    df = _load_zoobentos_df(project_id=project_id, group=group, env_file=env_file)
    df, campaign_filter_details = _apply_campaign_filter(df, campaign_filter)
    if df.empty:
        raise RuntimeError("No rows loaded from Supabase for the selected project/group/campaign filter")

    generated_files: list[str] = []

    executed_blocks: list[str] = []
    if block in {"all", "3"}:
        _run_block_3(df=df, group=group, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("3")

    if block in {"all", "4"}:
        _run_block_4(
            df=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("4")

    if block in {"all", "5"}:
        _run_block_5(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("5")

    if block in {"all", "6"}:
        _run_block_6(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("6")

    if block in {"all", "7"}:
        _run_block_7(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("7")

    if block in {"all", "8"}:
        _run_block_8(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("8")

    if block in {"all", "9"}:
        _run_block_9(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("9")

    if block in {"all", "10"}:
        _run_block_10(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("10")

    if block in {"all", "11"}:
        _run_block_11(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("11")

    if block in {"all", "12"}:
        _run_block_12(df=df, group=group, theme=theme, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("12")

    if block in {"all", "13"}:
        _run_block_13(df=df, group=group, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("13")

    campaign_order = sorted(df["nome_campanha"].dropna().unique().tolist())
    points_order = sorted(df["nome_ponto"].dropna().unique().tolist())
    rows_loaded = int(len(df))
    return {
        "records": rows_loaded,
        "rows_loaded": rows_loaded,
        "campaigns": campaign_order,
        "points": points_order,
        "campaign_filter": campaign_filter_details,
        "executed_blocks": executed_blocks,
        "generated_files": generated_files,
    }
