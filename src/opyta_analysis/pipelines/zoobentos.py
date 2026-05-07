from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import (
    apply_theme,
    get_figsize,
    get_figsize_by_complexity,
    get_tight_layout_rect,
    green_palette_from_hex,
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
        select="id_ponto_coleta,nome_ponto,id_campanha",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": group},
        select="id_esforco,id_ponto_coleta",
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
        select=f"id_esforco,id_especie,{abundance_col}",
    )
    resultados_proj = [r for r in resultados if r.get("id_esforco") in esforco_ids]
    if not resultados_proj:
        return pd.DataFrame()

    especies = paginate(
        sb,
        "especies",
        select="id_especie,nome_cientifico,filo,classe,ordem,familia,genero,bmwp_score",
    )
    esp_map = {e["id_especie"]: e for e in especies}

    rows = []
    for r in resultados_proj:
        e = esforcos_map.get(r.get("id_esforco"), {})
        p = pontos_map.get(e.get("id_ponto_coleta"), {})
        s = esp_map.get(r.get("id_especie"), {})
        rows.append(
            {
                "nome_ponto": p.get("nome_ponto"),
                "nome_campanha": camp_map.get(p.get("id_campanha"), "Campanha desconhecida"),
                "nome_cientifico": s.get("nome_cientifico"),
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


def _run_block_6(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    points_order = sorted(df["nome_ponto"].dropna().unique().tolist())
    campaign_order = sorted(df["nome_campanha"].dropna().unique().tolist())

    df_rich = (
        df.groupby("nome_ponto")["taxon_final"]
        .nunique()
        .reset_index()
        .rename(columns={"taxon_final": "riqueza_taxons"})
        .sort_values("nome_ponto")
    )
    xlsx_06a = output_dir / f"06A_df_riqueza_total_por_ponto_{group.lower()}.xlsx"
    df_rich.to_excel(xlsx_06a, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_06a))

    size_06a = get_figsize_by_complexity(theme, n_categories=len(df_rich), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=(size_06a[0], size_06a[1]), dpi=int(theme.get("dpi", 600)))
    bars = ax.bar(
        df_rich["nome_ponto"].tolist(),
        df_rich["riqueza_taxons"].tolist(),
        color=str(theme.get("primary_hex", "#11420C")),
        edgecolor="black",
        linewidth=1.0,
    )
    apply_theme(
        ax,
        theme,
        xlabel="Ponto amostral",
        ylabel="Numero de taxons",
        x_tick_rotation=45,
    )
    for bar, value in zip(bars, df_rich["riqueza_taxons"].tolist()):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{int(value)}", ha="center", va="bottom", fontsize=_font_annotation(theme))

    validate_axes_style(ax, theme)
    png_06a = output_dir / f"06A_grafico_riqueza_total_por_ponto_{group.lower()}.png"
    fig.savefig(png_06a, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_06a))

    class_col = "classe"
    classes = sorted(df[class_col].fillna("Classe desconhecida").astype(str).unique().tolist())
    # Exception approved by user: use categorical multi-color palette to improve class separability.
    cmap_classes = plt.get_cmap("tab10")
    color_map = {klass: cmap_classes(i % cmap_classes.N) for i, klass in enumerate(classes)}

    for campaign in campaign_order:
        df_c = df[df["nome_campanha"] == campaign].copy()
        pivot = (
            df_c.pivot_table(
                index="nome_ponto",
                columns=class_col,
                values="contagem",
                aggfunc="sum",
                fill_value=0,
            )
            .reindex(points_order)
            .fillna(0)
        )
        ordered_cols = sorted(pivot.columns.astype(str).tolist())
        pivot = pivot[ordered_cols]
        campaign_safe = _safe_name(campaign)

        xlsx_06b = output_dir / f"06B_df_abundancia_classe_{campaign_safe}_{group.lower()}.xlsx"
        pivot.reset_index().to_excel(xlsx_06b, index=False, engine="openpyxl")
        generated_files.append(str(xlsx_06b))

        size_06b = get_figsize_by_complexity(theme, n_categories=len(pivot.index), prefer_landscape=True)
        fig, ax = plt.subplots(figsize=(size_06b[0], size_06b[1]), dpi=int(theme.get("dpi", 600)))
        x = np.arange(len(pivot.index))
        bottom = np.zeros(len(pivot.index))
        for klass in ordered_cols:
            values = pivot[klass].values
            ax.bar(
                x,
                values,
                bottom=bottom,
                label=klass,
                color=color_map.get(klass, str(theme.get("primary_hex", "#11420C"))),
                edgecolor="black",
                linewidth=0.4,
            )
            bottom += values

        ax.set_xticks(x)
        ax.set_xticklabels(pivot.index.astype(str), ha="right")
        apply_theme(
            ax,
            theme,
            xlabel="Ponto amostral",
            ylabel="Abundancia",
            x_tick_rotation=45,
        )
        place_legend_below_x_axis(fig, ax, theme)
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.02))

        png_06b = output_dir / f"06B_grafico_abundancia_classe_{campaign_safe}_{group.lower()}.png"
        fig.savefig(png_06b, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(png_06b))

        pivot_pct = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0) * 100
        pivot_pct = pivot_pct.fillna(0)
        xlsx_06c = output_dir / f"06C_df_abundancia_relativa_classe_{campaign_safe}_{group.lower()}.xlsx"
        pivot_pct.reset_index().to_excel(xlsx_06c, index=False, engine="openpyxl")
        generated_files.append(str(xlsx_06c))

        size_06c = get_figsize_by_complexity(theme, n_categories=len(pivot_pct.index), prefer_landscape=True)
        fig, ax = plt.subplots(figsize=(size_06c[0], size_06c[1]), dpi=int(theme.get("dpi", 600)))
        x = np.arange(len(pivot_pct.index))
        bottom = np.zeros(len(pivot_pct.index))
        for klass in ordered_cols:
            values = pivot_pct[klass].values
            ax.bar(
                x,
                values,
                bottom=bottom,
                label=klass,
                color=color_map.get(klass, str(theme.get("primary_hex", "#11420C"))),
                edgecolor="black",
                linewidth=0.4,
            )
            bottom += values

        ax.set_xticks(x)
        ax.set_xticklabels(pivot_pct.index.astype(str), ha="right")
        ax.set_ylim(0, 100)
        apply_theme(
            ax,
            theme,
            xlabel="Ponto amostral",
            ylabel="Abundancia relativa (%)",
            x_tick_rotation=45,
        )
        place_legend_below_x_axis(fig, ax, theme)
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.02))

        png_06c = output_dir / f"06C_grafico_abundancia_relativa_classe_{campaign_safe}_{group.lower()}.png"
        fig.savefig(png_06c, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(png_06c))

    return {"campaigns": campaign_order}


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


def _run_block_4(df: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
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
    return {"campaigns": campaigns_ok}


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
    points = sorted(richness["nome_ponto"].dropna().unique().tolist())

    out_df = output_dir / f"02_df_riqueza_por_ponto_{group.lower()}.xlsx"
    richness.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    color_list = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), max(len(campaigns), 1))
    color_map = {c: color_list[i] for i, c in enumerate(campaigns)}

    pivot = (
        richness.pivot_table(index="nome_ponto", columns="nome_campanha", values="riqueza", aggfunc="sum", fill_value=0)
        .reindex(index=points, columns=campaigns, fill_value=0)
    )

    size_5 = get_figsize_by_complexity(theme, n_categories=len(points), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size_5, dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(points))
    n = max(len(campaigns), 1)
    width = 0.8 / n
    for i, c in enumerate(campaigns):
        vals = pivot[c].values
        ax.bar(x + (i - (n - 1) / 2) * width, vals, width=width, label=c, color=color_map[c], edgecolor="black", linewidth=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(points, ha="right")
    apply_theme(
        ax,
        theme,
        xlabel="Ponto amostral",
        ylabel="Riqueza",
        x_tick_rotation=45,
    )
    place_legend_below_x_axis(fig, ax, theme)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.02))

    out_png = output_dir / f"02_grafico_riqueza_por_ponto_{group.lower()}.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))
    return {"campaigns": campaigns}


def _run_block_7(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    ordem_df = (
        df.groupby("ordem")["taxon_final"]
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
    apply_theme(ax, theme, xlabel="Ordem", ylabel="Número de táxons", x_tick_rotation=45)
    for b, v in zip(bars, ordem_df["numero_de_taxons"].tolist()):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{int(v)}", ha="center", va="bottom", fontsize=_font_annotation(theme))
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_bar = output_dir / f"04_grafico_riqueza_ordem_barras_{group.lower()}.png"
    fig.savefig(out_bar, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_bar))

    # Donut chart
    # Use a categorical palette for better visual separation between orders.
    cmap = plt.get_cmap("tab20")
    donut_colors = [cmap(i % cmap.N) for i in range(max(len(ordem_df), 1))]
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

    results: list[dict] = []
    for campaign in campaign_order:
        df_c = df[df["nome_campanha"] == campaign].copy()
        if df_c.empty:
            continue
        mat = df_c.pivot_table(
            index="nome_ponto",
            columns=species_col,
            values="contagem",
            aggfunc="sum",
            fill_value=0,
            observed=False,
        )
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

    labels = df_div["nome_ponto"].tolist()
    shannon_vals = df_div["Shannon_H"].tolist()
    pielou_vals = df_div["Pielou_J"].tolist()
    x = np.arange(len(labels))

    size_8 = get_figsize_by_complexity(theme, n_categories=len(labels), prefer_landscape=True)
    fig, ax1 = plt.subplots(figsize=(size_8[0], size_8[1]), dpi=int(theme.get("dpi", 600)))
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

    if campaign_order:
        first_campaign_n = df_div[df_div["nome_campanha"] == campaign_order[0]].shape[0]
        if 0 < first_campaign_n < len(x):
            ax1.axvline(x=first_campaign_n - 0.5, color="#888888", linestyle="--", linewidth=1.5)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    place_legend_below_x_axis(fig, ax1, theme, handles=h1 + h2, labels=l1 + l2)
    validate_axes_style(ax1, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.06))

    png_10 = output_dir / f"10_grafico_diversidade_alfa_{group.lower()}.png"
    fig.savefig(png_10, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
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
    df_bmwp = df.drop_duplicates(subset=["nome_campanha", "nome_ponto", "taxon_final"]).copy()
    df_bmwp["bmwp_score"] = pd.to_numeric(df_bmwp["bmwp_score"], errors="coerce").fillna(0)

    bmwp_scores = df_bmwp.groupby(["nome_campanha", "nome_ponto"], as_index=False)["bmwp_score"].sum()
    campaign_order = sorted(bmwp_scores["nome_campanha"].dropna().unique().tolist())
    bmwp_scores["nome_campanha"] = pd.Categorical(bmwp_scores["nome_campanha"], categories=campaign_order, ordered=True)
    bmwp_scores = bmwp_scores.sort_values(["nome_campanha", "nome_ponto"]).reset_index(drop=True)
    bmwp_scores["classificacao"] = bmwp_scores["bmwp_score"].apply(_classify_bmwp)

    xlsx_11 = output_dir / f"11_df_bmwp_{group.lower()}.xlsx"
    bmwp_scores.to_excel(xlsx_11, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_11))

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
        colors_map = {
            "Muito boa": str(theme.get("primary_hex", "#2E6F95")),
            "Boa": str(theme.get("secondary_hex", "#E07A5F")),
            "Regular": str(theme.get("highlight_hex", "#3D5A80")),
            "Ruim": str(theme.get("secondary_hex", "#E07A5F")),
            "Pessima": str(theme.get("highlight_hex", "#3D5A80")),
        }
    legend_order = ["Muito boa", "Boa", "Regular", "Ruim", "Pessima"]

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
    ax.set_xticklabels(labels, rotation=90, ha="center")

    for i, (bar, val) in enumerate(zip(bars, bmwp_scores["bmwp_score"].values)):
        ax.text(i, bar.get_height() + 2, f"{val:.0f}", ha="center", fontsize=_font_annotation(theme))

    campaigns = bmwp_scores["nome_campanha"].astype(str).tolist()
    boundaries = _campaign_boundaries(campaigns)
    for boundary in boundaries[1:-1]:
        ax.axvline(x=boundary - 0.5, color="#888888", linestyle="--", linewidth=1.5)
    _render_campaign_labels(ax, campaigns, boundaries, fontsize=_font_campaign(theme), y=-0.20)

    handles = [Patch(facecolor=colors_map[k], edgecolor="black", label=k) for k in legend_order]
    place_legend_below_x_axis(fig, ax, theme, handles=handles, labels=legend_order, ncol=len(legend_order))
    validate_axes_style(ax, theme)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.22)

    png_11 = output_dir / f"11_grafico_bmwp_{group.lower()}.png"
    fig.savefig(png_11, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_11))

    return {"campaigns": campaign_order}


def _run_block_12(df: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    ordens_ept = {"ephemeroptera", "plecoptera", "trichoptera"}
    familias_chol = {"chironomidae"}

    df_ept = df.copy()
    df_ept["ordem"] = df_ept["ordem"].astype(str).str.strip().str.lower()
    df_ept["familia"] = df_ept["familia"].astype(str).str.strip().str.lower()
    df_ept["eh_ept"] = df_ept["ordem"].isin(ordens_ept)
    df_ept["eh_chol"] = df_ept["familia"].isin(familias_chol)

    grp = df_ept.groupby(["nome_campanha", "nome_ponto"])
    total = grp["contagem"].sum().rename("total")
    ept_ab = grp.apply(lambda d: d.loc[d["eh_ept"], "contagem"].sum()).rename("ept")
    chol_ab = grp.apply(lambda d: d.loc[d["eh_chol"], "contagem"].sum()).rename("chol")

    df_index = pd.concat([total, ept_ab, chol_ab], axis=1).reset_index()
    df_index["pct_ept"] = (df_index["ept"] / df_index["total"].replace(0, np.nan) * 100).fillna(0)
    df_index["pct_chol"] = (df_index["chol"] / df_index["total"].replace(0, np.nan) * 100).fillna(0)

    campaign_order = sorted(df_index["nome_campanha"].dropna().unique().tolist())
    df_index["nome_campanha"] = pd.Categorical(df_index["nome_campanha"], categories=campaign_order, ordered=True)
    df_index = df_index.sort_values(["nome_campanha", "nome_ponto"]).reset_index(drop=True)

    xlsx_12 = output_dir / f"12_df_ept_chol_{group.lower()}.xlsx"
    df_index.to_excel(xlsx_12, index=False, engine="openpyxl")
    generated_files.append(str(xlsx_12))

    # Figura 12 (indice composto APT): representacao obrigatoria em barra empilhada.
    apt_colors = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), 2)
    ept_color = apt_colors[0]
    chol_color = apt_colors[1]

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
        label="%Chironomidae",
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
    ax.set_xticklabels(df_index["nome_ponto"].astype(str).tolist(), rotation=90, ha="center")

    campaigns = df_index["nome_campanha"].astype(str).tolist()
    boundaries = _campaign_boundaries(campaigns)
    for boundary in boundaries[1:-1]:
        ax.axvline(x=boundary - 0.5, color="#888888", linestyle="--", linewidth=1.5)
    _render_campaign_labels(ax, campaigns, boundaries, fontsize=_font_campaign(theme), y=-0.20)

    place_legend_below_x_axis(fig, ax, theme, ncol=2)
    validate_axes_style(ax, theme)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.22)

    png_12 = output_dir / f"12_grafico_ept_chol_{group.lower()}.png"
    fig.savefig(png_12, dpi=int(theme.get("dpi", 300)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(png_12))

    return {"campaigns": campaign_order}


def run_zoobentos_pipeline(
    project_id: int,
    group: str,
    theme: dict,
    output_dir: Path,
    env_file: str | None,
    block: str = "all",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    if block not in {"all", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"}:
        raise ValueError("Supported block values for zoobentos: all, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12")

    df = _load_zoobentos_df(project_id=project_id, group=group, env_file=env_file)
    if df.empty:
        raise RuntimeError("No rows loaded from Supabase for the selected project/group")

    generated_files: list[str] = []

    executed_blocks: list[str] = []
    if block in {"all", "3"}:
        _run_block_3(df=df, group=group, output_dir=output_dir, generated_files=generated_files)
        executed_blocks.append("3")

    if block in {"all", "4"}:
        _run_block_4(df=df, group=group, output_dir=output_dir, generated_files=generated_files)
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

    campaign_order = sorted(df["nome_campanha"].dropna().unique().tolist())
    return {
        "records": int(len(df)),
        "campaigns": campaign_order,
        "executed_blocks": executed_blocks,
        "generated_files": generated_files,
    }
