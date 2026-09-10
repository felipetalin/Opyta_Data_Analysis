from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_ictio_avg_tradicional_consolidado_2026 as traditional  # noqa: E402


ROOT = traditional.ROOT
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "_project_scripts"
    / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
    / "richness_boxplots_exploratory_20260715"
)
GROUP = "Ictiofauna"
POINT_ORDER = sum(traditional.REPORT_POINT_GROUPS.values(), [])
AREA_COLORS = {
    traditional.avg_runner.AREA_01: "#16803A",
    traditional.avg_runner.AREA_02: "#6A8F2F",
}
SEASON_COLORS = {"CH": "#006837", "SC": "#E66101", "ND": "#555555"}


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


def _season(value: object) -> str:
    text = str(value or "").upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text):
        return "CH"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text):
        return "SC"
    return "ND"


def build_richness_table() -> pd.DataFrame:
    _observed, df_point_metrics, _campaign_map = traditional.build_frames()
    df = df_point_metrics.copy()
    df["contagem"] = pd.to_numeric(df.get("contagem", 0), errors="coerce").fillna(0)
    df["nome_cientifico"] = df["nome_cientifico"].fillna("").astype(str).str.strip()

    sampled_pairs = df[["nome_campanha", "nome_ponto", "area_controle"]].drop_duplicates()
    valid_taxa = df[(df["contagem"] > 0) & (df["nome_cientifico"] != "")].copy()
    richness = (
        valid_taxa.groupby(["nome_campanha", "nome_ponto"], dropna=False)["nome_cientifico"]
        .nunique()
        .reset_index(name="riqueza")
    )
    table = sampled_pairs.merge(richness, on=["nome_campanha", "nome_ponto"], how="left")
    table["riqueza"] = pd.to_numeric(table["riqueza"], errors="coerce").fillna(0).astype(int)
    table["campanha_seq"] = table["nome_campanha"].map(traditional.standard_campaign_sequence)
    table["campanha_curta"] = table["campanha_seq"].map(lambda value: f"C{int(value):02d}")
    table["ano_temporal"] = table["nome_campanha"].map(traditional.temporal_year_from_campaign)
    table["periodo_hidrologico"] = table["nome_campanha"].map(_season)
    table["ordem_ponto"] = table["nome_ponto"].map({point: idx for idx, point in enumerate(POINT_ORDER)})
    table = table.sort_values(["campanha_seq", "ordem_ponto"]).reset_index(drop=True)
    return table


def _boxplot(ax: Any, data: list[np.ndarray], positions: list[float], colors: list[str], width: float = 0.52) -> None:
    box = ax.boxplot(
        data,
        positions=positions,
        widths=width,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "#1F1F1F", "linewidth": 1.45},
        whiskerprops={"color": "#444444", "linewidth": 1.05},
        capprops={"color": "#444444", "linewidth": 1.05},
    )
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.28)
        patch.set_edgecolor("#222222")
        patch.set_linewidth(1.05)


def _finish_axes(ax: Any, ylabel: str = "Riqueza taxon\u00f4mica") -> None:
    ax.set_ylabel(ylabel, fontsize=13)
    ax.grid(axis="y", color="#D8D8D8", linewidth=0.75, alpha=0.8)
    ax.grid(axis="x", color="#EEEEEE", linewidth=0.45, alpha=0.5)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="both", labelsize=10.5)


def plot_temporal_year(table: pd.DataFrame, output_dir: Path) -> str:
    years = sorted(table["ano_temporal"].dropna().astype(int).unique().tolist())
    fig, ax = plt.subplots(figsize=(11.69, 8.27), dpi=450)
    data = [table.loc[table["ano_temporal"].eq(year), "riqueza"].to_numpy(dtype=float) for year in years]
    positions = list(range(1, len(years) + 1))
    _boxplot(ax, data, positions, ["#4C8C4A"] * len(years), width=0.58)

    rng = np.random.default_rng(20260715)
    for pos, year in zip(positions, years):
        sub = table[table["ano_temporal"].eq(year)].copy()
        x = pos + rng.uniform(-0.18, 0.18, len(sub))
        colors = sub["periodo_hidrologico"].map(SEASON_COLORS).fillna(SEASON_COLORS["ND"]).tolist()
        ax.scatter(x, sub["riqueza"], s=22, c=colors, edgecolor="black", linewidth=0.32, alpha=0.78, zorder=3)

    ax.set_xticks(positions)
    ax.set_xticklabels([f"Ano {year}" for year in years])
    ax.set_xlabel("Ano temporal", fontsize=13)
    _finish_axes(ax)
    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=SEASON_COLORS["CH"], markeredgecolor="black", markersize=7.5, label="CH"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=SEASON_COLORS["SC"], markeredgecolor="black", markersize=7.5, label="SC"),
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=11)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.965, bottom=0.10)
    out = output_dir / "EXP_BOX_01_riqueza_por_ano_temporal_ictiofauna.png"
    fig.savefig(out, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return str(out)


def plot_area_by_year(table: pd.DataFrame, output_dir: Path) -> str:
    years = sorted(table["ano_temporal"].dropna().astype(int).unique().tolist())
    areas = [traditional.avg_runner.AREA_01, traditional.avg_runner.AREA_02]
    fig, ax = plt.subplots(figsize=(11.69, 8.27), dpi=450)
    positions: list[float] = []
    data: list[np.ndarray] = []
    colors: list[str] = []
    labels: list[str] = []
    for idx, year in enumerate(years, start=1):
        for offset, area in [(-0.18, areas[0]), (0.18, areas[1])]:
            positions.append(idx + offset)
            labels.append(area)
            data.append(table.loc[table["ano_temporal"].eq(year) & table["area_controle"].eq(area), "riqueza"].to_numpy(dtype=float))
            colors.append(AREA_COLORS.get(area, "#777777"))
    _boxplot(ax, data, positions, colors, width=0.28)

    rng = np.random.default_rng(20260715)
    for pos, year, area in zip(positions, np.repeat(years, 2), labels):
        sub = table[table["ano_temporal"].eq(year) & table["area_controle"].eq(area)].copy()
        x = pos + rng.uniform(-0.055, 0.055, len(sub))
        ax.scatter(x, sub["riqueza"], s=17, c=AREA_COLORS.get(area, "#777777"), edgecolor="black", linewidth=0.25, alpha=0.68, zorder=3)

    ax.set_xticks(range(1, len(years) + 1))
    ax.set_xticklabels([f"Ano {year}" for year in years])
    ax.set_xlabel("Ano temporal", fontsize=13)
    _finish_axes(ax)
    handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=AREA_COLORS[area], markeredgecolor="black", markersize=8, label=area)
        for area in areas
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=10.5)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.965, bottom=0.10)
    out = output_dir / "EXP_BOX_02_riqueza_area_controle_por_ano_temporal_ictiofauna.png"
    fig.savefig(out, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return str(out)


def plot_point_spatial(table: pd.DataFrame, output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(11.69, 8.27), dpi=450)
    data = [table.loc[table["nome_ponto"].eq(point), "riqueza"].to_numpy(dtype=float) for point in POINT_ORDER]
    positions = list(range(1, len(POINT_ORDER) + 1))
    colors = [
        AREA_COLORS.get(traditional.avg_runner.AREA_BY_POINT.get(point), "#777777")
        for point in POINT_ORDER
    ]
    _boxplot(ax, data, positions, colors, width=0.56)

    rng = np.random.default_rng(20260715)
    for pos, point, color in zip(positions, POINT_ORDER, colors):
        sub = table[table["nome_ponto"].eq(point)].copy()
        x = pos + rng.uniform(-0.16, 0.16, len(sub))
        ax.scatter(x, sub["riqueza"], s=14, c=color, edgecolor="black", linewidth=0.22, alpha=0.62, zorder=3)

    ax.set_xticks(positions)
    ax.set_xticklabels(POINT_ORDER, rotation=90)
    ax.set_xlabel("Ponto amostral", fontsize=13)
    _finish_axes(ax)
    handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=AREA_COLORS[area], markeredgecolor="black", markersize=8, label=area)
        for area in [traditional.avg_runner.AREA_01, traditional.avg_runner.AREA_02]
    ]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=10.5)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.965, bottom=0.16)
    out = output_dir / "EXP_BOX_03_riqueza_por_ponto_ictiofauna.png"
    fig.savefig(out, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return str(out)


def write_tables(output_dir: Path, table: pd.DataFrame) -> dict[str, str]:
    sample_path = output_dir / "EXP_BOX_df_riqueza_ponto_campanha_ictiofauna.xlsx"
    summary_path = output_dir / "EXP_BOX_resumo_riqueza_ictiofauna.xlsx"
    with pd.ExcelWriter(sample_path, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="riqueza_ponto_campanha", index=False)
    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        for sheet, cols in {
            "por_ano_temporal": ["ano_temporal"],
            "por_area_ano": ["ano_temporal", "area_controle"],
            "por_ponto": ["nome_ponto", "area_controle"],
        }.items():
            (
                table.groupby(cols, dropna=False)["riqueza"]
                .agg(n="count", media="mean", mediana="median", minimo="min", maximo="max")
                .reset_index()
                .to_excel(writer, sheet_name=sheet, index=False)
            )
    return {"sample_table": str(sample_path), "summary_table": str(summary_path)}


def build(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    table = build_richness_table()
    tables = write_tables(output_dir, table)
    figures = [
        plot_temporal_year(table, output_dir),
        plot_area_by_year(table, output_dir),
        plot_point_spatial(table, output_dir),
    ]
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": traditional.PROJECT_CODE,
        "group": GROUP,
        "status": "exploratory_generated",
        "output_dir": str(output_dir),
        "metric": "riqueza_taxonomica",
        "sampled_point_campaigns": int(len(table)),
        "campaigns": int(table["nome_campanha"].nunique()),
        "points": int(table["nome_ponto"].nunique()),
        "temporal_years": sorted(int(v) for v in table["ano_temporal"].dropna().unique()),
        "sampling_rule": "Regra revisada em 2026-07-15; nao-amostragem mantida como ausencia, nao como zero.",
        "figures": figures,
        "tables": tables,
    }
    manifest = output_dir / "manifesto_richness_boxplots_ictiofauna.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def main() -> int:
    summary = build(DEFAULT_OUTPUT_DIR)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
