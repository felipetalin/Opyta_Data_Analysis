from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial import ConvexHull
from scipy.spatial.distance import squareform


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_ictio_avg_tradicional_consolidado_2026 as traditional  # noqa: E402


ROOT = traditional.ROOT
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados ictio"
    r"\Consolidado_2026\icitiofauna"
)
OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "bray_spatial_temporal_exploratory_20260715"
)
POINT_ORDER = sum(traditional.REPORT_POINT_GROUPS.values(), [])
YEAR_BANDS = traditional.TEMPORAL_YEAR_BANDS
AREA_COLORS = {
    traditional.avg_runner.AREA_01: "#16803A",
    traditional.avg_runner.AREA_02: "#6A8F2F",
}
GROUP_COLORS = ["#0B7A3B", "#6A8F2F", "#2A78B8", "#B1782C", "#7A4FA3", "#C43B3B", "#4C4C4C"]
CUT_HEIGHT = 0.80


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


def _campaign_year(seq: int) -> int | None:
    for year, start, end in YEAR_BANDS:
        if start <= seq <= end:
            return int(year)
    return None


def _bray_curtis_matrix(values: np.ndarray) -> np.ndarray:
    n = values.shape[0]
    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            denom = float(np.sum(values[i] + values[j]))
            d = 0.0 if denom == 0 else float(np.sum(np.abs(values[i] - values[j])) / denom)
            dist[i, j] = d
            dist[j, i] = d
    return dist


def _pcoa(distance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = distance.shape[0]
    if n == 0:
        return np.empty((0, 2)), np.array([0.0, 0.0])
    d2 = distance**2
    centering = np.eye(n) - np.ones((n, n)) / n
    b_matrix = -0.5 * centering @ d2 @ centering
    eigvals, eigvecs = np.linalg.eigh(b_matrix)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    positive = np.maximum(eigvals[:2], 0)
    coords = eigvecs[:, :2] * np.sqrt(positive)
    explained = positive / np.sum(eigvals[eigvals > 0]) if np.any(eigvals > 0) else np.array([0.0, 0.0])
    if coords.shape[1] < 2:
        coords = np.pad(coords, ((0, 0), (0, 2 - coords.shape[1])))
    return coords, explained[:2]


def build_point_species_year_tables() -> dict[int, pd.DataFrame]:
    _observed, df_point_metrics, _campaign_map = traditional.build_frames()
    df = df_point_metrics.copy()
    for col in ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem"]:
        df[col] = df[col].astype(str).str.strip()
    df["nome_cientifico"] = df["nome_cientifico"].replace({"None": "", "nan": ""})
    df["contagem"] = pd.to_numeric(df.get("contagem", 0), errors="coerce").fillna(0)
    df["esforco"] = pd.to_numeric(df.get("esforco", np.nan), errors="coerce")
    df["campanha_seq"] = df["nome_campanha"].map(traditional.standard_campaign_sequence)
    df["ano_temporal"] = df["campanha_seq"].map(_campaign_year)

    tipo_norm = df["tipo_amostragem"].map(traditional.avg_runner.ictio_mod._normalizar_tipo_amostragem)
    quant = df[(tipo_norm == "quantitativo") & df["esforco"].notna() & (df["esforco"] > 0)].copy()
    if quant.empty:
        raise RuntimeError("Sem dados quantitativos validos para exploratoria Bray-Curtis.")

    effort = (
        quant[["ano_temporal", "nome_campanha", "nome_ponto", "esforco"]]
        .drop_duplicates()
        .groupby(["ano_temporal", "nome_campanha", "nome_ponto"], dropna=False)["esforco"]
        .sum()
        .reset_index(name="esforco_total_ponto")
    )
    sampled_points = (
        effort.groupby(["ano_temporal", "nome_ponto"], dropna=False)["esforco_total_ponto"]
        .sum()
        .reset_index()
    )

    observed = quant[(quant["contagem"] > 0) & (quant["nome_cientifico"] != "")].copy()
    species_campaign = (
        observed.groupby(["ano_temporal", "nome_campanha", "nome_ponto", "nome_cientifico"], dropna=False)[
            "contagem"
        ]
        .sum()
        .reset_index()
        .merge(effort, on=["ano_temporal", "nome_campanha", "nome_ponto"], how="left")
    )
    species_campaign["cpuen"] = (
        species_campaign["contagem"] / species_campaign["esforco_total_ponto"]
    ) * 100
    species_year = (
        species_campaign.groupby(["ano_temporal", "nome_ponto", "nome_cientifico"], dropna=False)["cpuen"]
        .sum()
        .reset_index()
    )
    species = sorted(species_year["nome_cientifico"].dropna().unique().tolist())

    tables: dict[int, pd.DataFrame] = {}
    for year, _start, _end in YEAR_BANDS:
        points = [
            point
            for point in POINT_ORDER
            if point in set(sampled_points.loc[sampled_points["ano_temporal"] == year, "nome_ponto"])
        ]
        if not points:
            continue
        table = (
            species_year[species_year["ano_temporal"] == year]
            .pivot_table(index="nome_ponto", columns="nome_cientifico", values="cpuen", aggfunc="sum", fill_value=0)
            .reindex(index=points, columns=species, fill_value=0)
        )
        tables[int(year)] = table
    return tables


def plot_exploratory(tables: dict[int, pd.DataFrame], output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    years = list(tables)
    fig, axes = plt.subplots(
        len(years),
        2,
        figsize=(16.54, 11.69),
        dpi=300,
        gridspec_kw={"width_ratios": [0.85, 1.25], "hspace": 0.38, "wspace": 0.08},
    )
    if len(years) == 1:
        axes = np.array([axes])

    for row, year in enumerate(years):
        table = tables[year]
        points = table.index.tolist()
        dist = _bray_curtis_matrix(table.to_numpy(dtype=float))
        condensed = squareform(dist, checks=False)
        if len(points) > 1:
            z = linkage(condensed, method="average")
            clusters = fcluster(z, t=CUT_HEIGHT, criterion="distance")
            dendro = dendrogram(
                z,
                labels=points,
                orientation="left",
                ax=axes[row, 0],
                color_threshold=CUT_HEIGHT,
                above_threshold_color="#4C4C4C",
                leaf_font_size=8.5,
            )
            order = dendro["ivl"]
        else:
            axes[row, 0].text(0.5, 0.5, points[0], ha="center", va="center")
            order = points
            clusters = np.array([1])
        axes[row, 0].axvline(CUT_HEIGHT, color="#C43B3B", linestyle="--", linewidth=0.9)
        axes[row, 0].set_title(f"Ano {year} - agrupamento dos pontos (corte={CUT_HEIGHT:.2f})", fontsize=10.5)
        axes[row, 0].tick_params(axis="x", labelsize=8)

        ordered_idx = [points.index(point) for point in order]
        ordered_dist = dist[np.ix_(ordered_idx, ordered_idx)]
        im = axes[row, 1].imshow(ordered_dist, cmap="YlGnBu", vmin=0, vmax=1)
        axes[row, 1].set_title(f"Ano {year} - Bray-Curtis entre pontos", fontsize=10.5)
        axes[row, 1].set_xticks(np.arange(len(order)))
        axes[row, 1].set_yticks(np.arange(len(order)))
        axes[row, 1].set_xticklabels(order, rotation=90, fontsize=8)
        axes[row, 1].set_yticklabels(order, fontsize=8)
        for idx, point in enumerate(order):
            area = traditional.avg_runner.AREA_BY_POINT.get(point)
            axes[row, 1].get_xticklabels()[idx].set_color(AREA_COLORS.get(area, "#222222"))
            axes[row, 1].get_yticklabels()[idx].set_color(AREA_COLORS.get(area, "#222222"))
        axes[row, 1].set_xticks(np.arange(-0.5, len(order), 1), minor=True)
        axes[row, 1].set_yticks(np.arange(-0.5, len(order), 1), minor=True)
        axes[row, 1].grid(which="minor", color="white", linewidth=0.8)
        axes[row, 1].tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(im, ax=axes[:, 1], fraction=0.018, pad=0.018)
    cbar.set_label("Dissimilaridade de Bray-Curtis", fontsize=10)
    fig.suptitle(
        "Exploratoria: agrupamento espacial dos pontos por Bray-Curtis (CPUEn por especie)",
        fontsize=14,
        y=0.985,
    )
    out_png = output_dir / "EXP_bray_curtis_agrupamento_pontos_por_ano_temporal.png"
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return str(out_png)


def plot_pcoa_groups(tables: dict[int, pd.DataFrame], output_dir: Path) -> tuple[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    years = list(tables)
    fig, axes = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=300)
    axes = axes.ravel()
    records: list[dict[str, Any]] = []

    for ax, year in zip(axes, years):
        table = tables[year]
        points = table.index.tolist()
        dist = _bray_curtis_matrix(table.to_numpy(dtype=float))
        if len(points) > 1:
            z = linkage(squareform(dist, checks=False), method="average")
            clusters = fcluster(z, t=CUT_HEIGHT, criterion="distance")
        else:
            clusters = np.array([1])
        coords, explained = _pcoa(dist)

        for cluster_id in sorted(set(clusters)):
            idx = np.where(clusters == cluster_id)[0]
            color = GROUP_COLORS[(int(cluster_id) - 1) % len(GROUP_COLORS)]
            ax.scatter(
                coords[idx, 0],
                coords[idx, 1],
                s=90,
                color=color,
                edgecolor="#1F1F1F",
                linewidth=0.6,
                label=f"G{int(cluster_id)}",
                zorder=3,
            )
            if len(idx) >= 3:
                hull = ConvexHull(coords[idx, :2])
                hull_points = coords[idx, :2][hull.vertices]
                ax.fill(hull_points[:, 0], hull_points[:, 1], color=color, alpha=0.14, zorder=1)
                ax.plot(
                    np.r_[hull_points[:, 0], hull_points[0, 0]],
                    np.r_[hull_points[:, 1], hull_points[0, 1]],
                    color=color,
                    linewidth=1.0,
                    alpha=0.7,
                    zorder=2,
                )
            for i in idx:
                ax.text(coords[i, 0], coords[i, 1], points[i], fontsize=8.5, ha="left", va="bottom")

        ax.axhline(0, color="#D0D0D0", linewidth=0.7)
        ax.axvline(0, color="#D0D0D0", linewidth=0.7)
        ax.set_title(f"Ano {year} - PCoA por grupos Bray-Curtis", fontsize=12)
        ax.set_xlabel(f"PCoA1 ({explained[0] * 100:.1f}%)", fontsize=10)
        ax.set_ylabel(f"PCoA2 ({explained[1] * 100:.1f}%)", fontsize=10)
        ax.legend(loc="best", fontsize=8, frameon=False, ncol=2)

        for point, cluster_id, x, y in zip(points, clusters, coords[:, 0], coords[:, 1]):
            records.append(
                {
                    "ano_temporal": year,
                    "nome_ponto": point,
                    "grupo_bray": int(cluster_id),
                    "pcoa1": float(x),
                    "pcoa2": float(y),
                    "area_controle": traditional.avg_runner.AREA_BY_POINT.get(point, ""),
                }
            )

    for ax in axes[len(years) :]:
        ax.axis("off")
    fig.suptitle(
        f"Exploratoria: PCoA Bray-Curtis com grupos do dendrograma (corte={CUT_HEIGHT:.2f})",
        fontsize=15,
        y=0.985,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    out_png = output_dir / "EXP_pcoa_bray_curtis_grupos_por_ano_temporal.png"
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return str(out_png), pd.DataFrame(records)


def species_vectors(table: pd.DataFrame, coords: np.ndarray, min_strength: float = 0.55, max_species: int = 4) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for species in table.columns:
        values = table[species].to_numpy(dtype=float)
        if np.nanstd(values) == 0:
            corr1 = 0.0
            corr2 = 0.0
        else:
            corr1 = float(np.corrcoef(values, coords[:, 0])[0, 1]) if np.nanstd(coords[:, 0]) > 0 else 0.0
            corr2 = float(np.corrcoef(values, coords[:, 1])[0, 1]) if np.nanstd(coords[:, 1]) > 0 else 0.0
        corr1 = 0.0 if np.isnan(corr1) else corr1
        corr2 = 0.0 if np.isnan(corr2) else corr2
        strength = float(np.sqrt(corr1**2 + corr2**2))
        records.append(
            {
                "nome_cientifico": species,
                "corr_pcoa1": corr1,
                "corr_pcoa2": corr2,
                "forca_associacao": strength,
            }
        )
    vectors = pd.DataFrame(records).sort_values("forca_associacao", ascending=False)
    selected = vectors[vectors["forca_associacao"] >= min_strength].head(max_species)
    if selected.empty:
        selected = vectors.head(min(3, len(vectors)))
    return selected.reset_index(drop=True)


def plot_pcoa_biplot(
    tables: dict[int, pd.DataFrame],
    output_dir: Path,
    *,
    final_layout: bool = False,
) -> tuple[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    years = list(tables)
    fig, axes = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=300)
    axes = axes.ravel()
    vector_records: list[pd.DataFrame] = []

    for ax, year in zip(axes, years):
        table = tables[year]
        points = table.index.tolist()
        dist = _bray_curtis_matrix(table.to_numpy(dtype=float))
        if len(points) > 1:
            z = linkage(squareform(dist, checks=False), method="average")
            clusters = fcluster(z, t=CUT_HEIGHT, criterion="distance")
        else:
            clusters = np.array([1])
        coords, explained = _pcoa(dist)
        vectors = species_vectors(table, coords)
        vectors.insert(0, "ano_temporal", year)
        vector_records.append(vectors)

        for cluster_id in sorted(set(clusters)):
            idx = np.where(clusters == cluster_id)[0]
            color = GROUP_COLORS[(int(cluster_id) - 1) % len(GROUP_COLORS)]
            ax.scatter(
                coords[idx, 0],
                coords[idx, 1],
                s=84,
                color=color,
                edgecolor="#1F1F1F",
                linewidth=0.55,
                label=f"G{int(cluster_id)}",
                zorder=3,
            )
            if len(idx) >= 3:
                hull = ConvexHull(coords[idx, :2])
                hull_points = coords[idx, :2][hull.vertices]
                ax.fill(hull_points[:, 0], hull_points[:, 1], color=color, alpha=0.12, zorder=1)
            for i in idx:
                ax.text(coords[i, 0], coords[i, 1], points[i], fontsize=8.2, ha="left", va="bottom")

        x_span = max(np.ptp(coords[:, 0]), 0.1)
        y_span = max(np.ptp(coords[:, 1]), 0.1)
        scale = 0.36 * min(x_span, y_span)
        for row in vectors.itertuples(index=False):
            dx = row.corr_pcoa1 * scale
            dy = row.corr_pcoa2 * scale
            ax.arrow(
                0,
                0,
                dx,
                dy,
                color="#333333",
                linewidth=1.1,
                head_width=0.018,
                length_includes_head=True,
                alpha=0.85,
                zorder=4,
            )
            ax.text(
                dx * 1.08,
                dy * 1.08,
                row.nome_cientifico,
                fontsize=8.0,
                fontstyle="italic",
                color="#222222",
                ha="left" if dx >= 0 else "right",
                va="bottom" if dy >= 0 else "top",
            )

        ax.axhline(0, color="#D0D0D0", linewidth=0.7)
        ax.axvline(0, color="#D0D0D0", linewidth=0.7)
        ax.set_title(f"Ano {year}", fontsize=12)
        ax.set_xlabel(f"PCoA1 ({explained[0] * 100:.1f}%)", fontsize=10)
        ax.set_ylabel(f"PCoA2 ({explained[1] * 100:.1f}%)", fontsize=10)
        ax.legend(loc="best", fontsize=7.8, frameon=False, ncol=2)

    for ax in axes[len(years) :]:
        ax.axis("off")
    if final_layout:
        fig.tight_layout(rect=[0, 0, 1, 1])
        out_png = output_dir / "09_grafico_pcoa_biplot_bray_curtis_vetores_especies_ictiofauna.png"
    else:
        fig.suptitle(
            f"Exploratoria: biplot PCoA Bray-Curtis com vetores de espécies (corte={CUT_HEIGHT:.2f})",
            fontsize=15,
            y=0.985,
        )
        fig.tight_layout(rect=[0, 0, 1, 0.965])
        out_png = output_dir / "EXP_pcoa_biplot_bray_species_vectors_por_ano_temporal.png"
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return str(out_png), pd.concat(vector_records, ignore_index=True)


def representative_species(tables: dict[int, pd.DataFrame], groups: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for year, table in tables.items():
        year_groups = groups[groups["ano_temporal"] == year]
        for cluster_id in sorted(year_groups["grupo_bray"].unique()):
            points = year_groups.loc[year_groups["grupo_bray"] == cluster_id, "nome_ponto"].tolist()
            in_group = table.loc[points]
            out_group = table.drop(index=points, errors="ignore")
            group_sum = in_group.sum(axis=0)
            total = float(group_sum.sum())
            group_mean = in_group.mean(axis=0)
            out_mean = out_group.mean(axis=0) if not out_group.empty else pd.Series(0.0, index=table.columns)
            diff = group_mean - out_mean
            species_rank = (
                pd.DataFrame(
                    {
                        "nome_cientifico": table.columns,
                        "cpuen_grupo": group_sum.to_numpy(dtype=float),
                        "cpuen_percentual_grupo": np.where(total > 0, (group_sum / total) * 100, 0.0),
                        "media_cpuen_grupo": group_mean.to_numpy(dtype=float),
                        "media_cpuen_demais": out_mean.reindex(table.columns).to_numpy(dtype=float),
                        "diferenca_media_grupo_vs_demais": diff.reindex(table.columns).to_numpy(dtype=float),
                    }
                )
                .query("cpuen_grupo > 0")
                .sort_values(
                    ["cpuen_percentual_grupo", "diferenca_media_grupo_vs_demais"],
                    ascending=False,
                )
                .head(top_n)
            )
            for rank, row in enumerate(species_rank.itertuples(index=False), start=1):
                records.append(
                    {
                        "ano_temporal": year,
                        "grupo_bray": int(cluster_id),
                        "pontos": ", ".join(points),
                        "n_pontos": len(points),
                        "rank": rank,
                        "nome_cientifico": row.nome_cientifico,
                        "cpuen_grupo": float(row.cpuen_grupo),
                        "cpuen_percentual_grupo": float(row.cpuen_percentual_grupo),
                        "media_cpuen_grupo": float(row.media_cpuen_grupo),
                        "media_cpuen_demais": float(row.media_cpuen_demais),
                        "diferenca_media_grupo_vs_demais": float(row.diferenca_media_grupo_vs_demais),
                    }
                )
    return pd.DataFrame(records)


def plot_representative_species(representatives: pd.DataFrame, output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    top = representatives[(representatives["rank"] <= 3) & (representatives["cpuen_grupo"] > 0)].copy()
    years = sorted(top["ano_temporal"].unique())
    fig, axes = plt.subplots(len(years), 1, figsize=(16.54, 11.69), dpi=300, sharex=True)
    if len(years) == 1:
        axes = np.array([axes])
    for ax, year in zip(axes, years):
        df = top[top["ano_temporal"] == year].copy()
        df["label"] = df.apply(lambda r: f"G{int(r['grupo_bray'])} | {r['nome_cientifico']}", axis=1)
        df = df.sort_values(["grupo_bray", "rank"], ascending=[True, False])
        colors = [GROUP_COLORS[(int(group) - 1) % len(GROUP_COLORS)] for group in df["grupo_bray"]]
        ax.barh(df["label"], df["cpuen_percentual_grupo"], color=colors, edgecolor="#333333", linewidth=0.4)
        ax.set_title(f"Ano {year} - espécies mais representativas por grupo", fontsize=12)
        ax.set_xlabel("% da CPUEn do grupo", fontsize=10)
        ax.tick_params(axis="y", labelsize=8.5)
        ax.grid(axis="x", color="#DDDDDD", linewidth=0.6)
        for y_pos, value in enumerate(df["cpuen_percentual_grupo"]):
            ax.text(value + 0.5, y_pos, f"{value:.1f}", va="center", fontsize=8)
    fig.suptitle("Exploratoria: espécies representativas dos grupos Bray-Curtis", fontsize=15, y=0.985)
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    out_png = output_dir / "EXP_especies_representativas_grupos_bray.png"
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return str(out_png)


def write_tables(
    tables: dict[int, pd.DataFrame],
    groups: pd.DataFrame,
    representatives: pd.DataFrame,
    vectors: pd.DataFrame,
    output_dir: Path,
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_xlsx = output_dir / "EXP_bray_curtis_matrizes_ponto_ano_temporal.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        for year, table in tables.items():
            dist = pd.DataFrame(
                _bray_curtis_matrix(table.to_numpy(dtype=float)),
                index=table.index,
                columns=table.index,
            )
            table.reset_index(names="nome_ponto").to_excel(writer, sheet_name=f"cpuen_{year}", index=False)
            dist.reset_index(names="nome_ponto").to_excel(writer, sheet_name=f"bray_{year}", index=False)
        groups.to_excel(writer, sheet_name="grupos_pcoa", index=False)
        representatives.to_excel(writer, sheet_name="especies_representativas", index=False)
        vectors.to_excel(writer, sheet_name="vetores_especies_pcoa", index=False)
    return str(out_xlsx)


def build(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    tables = build_point_species_year_tables()
    figure = plot_exploratory(tables, output_dir)
    pcoa_figure, groups = plot_pcoa_groups(tables, output_dir)
    biplot_figure, vectors = plot_pcoa_biplot(tables, output_dir)
    final_biplot_figure, _vectors_final = plot_pcoa_biplot(tables, FINAL_DIR, final_layout=True)
    representatives = representative_species(tables, groups)
    representatives_figure = plot_representative_species(representatives, output_dir)
    workbook = write_tables(tables, groups, representatives, vectors, output_dir)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": traditional.PROJECT_CODE,
        "analysis": "exploratoria_bray_curtis_agrupamento_espacial_temporal",
        "metric": "CPUEn por ponto x especie agregado por ano temporal",
        "distance": "Bray-Curtis",
        "cluster_method": "UPGMA/average linkage",
        "cluster_cut_height": CUT_HEIGHT,
        "years": {str(year): {"points": int(len(table)), "species": int(table.shape[1])} for year, table in tables.items()},
        "figure": figure,
        "pcoa_figure": pcoa_figure,
        "biplot_figure": biplot_figure,
        "final_biplot_figure": final_biplot_figure,
        "representatives_figure": representatives_figure,
        "workbook": workbook,
        "notes": [
            "Pontos sem captura e com esforco quantitativo entram como vetor zero.",
            "Distancia zero-zero definida como 0 para evitar indeterminacao.",
            "PIC-02 e tratado pelo nome operacional disponivel na base; a realocacao deve ser descrita no texto metodologico.",
        ],
    }
    manifest = output_dir / "manifesto_EXP_bray_curtis_agrupamento_pontos.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
