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
    / "species_cpuen_synthesis_20260715"
)
GROUP = "Ictiofauna"
POINT_ORDER = sum(traditional.REPORT_POINT_GROUPS.values(), [])
AREA_01 = traditional.avg_runner.AREA_01
AREA_02 = traditional.avg_runner.AREA_02
AREA_COLORS = {AREA_01: "#16803A", AREA_02: "#6A8F2F"}
BAR_COLOR = "#6DBA18"
BAR_EDGE = "#38620E"
ABSENT_COLOR = "#EDEDED"
PRESENT_COLOR = "#208045"
YEAR_BANDS = traditional.TEMPORAL_YEAR_BANDS


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


def _clean_species(value: object) -> str:
    return str(value or "").strip()


def _campaign_short(value: object) -> str:
    return f"C{traditional.standard_campaign_sequence(value):02d}"


def build_cpuen_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _observed, df_point_metrics, _campaign_map = traditional.build_frames()
    df = df_point_metrics.copy()
    for col in ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem"]:
        df[col] = df[col].astype(str).str.strip()
    df["nome_cientifico"] = df["nome_cientifico"].replace({"None": "", "nan": ""})
    df["contagem"] = pd.to_numeric(df.get("contagem", 0), errors="coerce").fillna(0)
    df["esforco"] = pd.to_numeric(df.get("esforco", np.nan), errors="coerce")

    tipo_norm = df["tipo_amostragem"].map(traditional.avg_runner.ictio_mod._normalizar_tipo_amostragem)
    quant = df[(tipo_norm == "quantitativo") & df["esforco"].notna() & (df["esforco"] > 0)].copy()
    if quant.empty:
        raise RuntimeError("Sem dados quantitativos validos para sintese de CPUEn por especie.")

    effort_cols = ["nome_campanha", "nome_ponto"]
    method_cols = [col for col in ["metodo_de_captura", "unidade_esforco"] if col in quant.columns]
    effort = (
        quant[effort_cols + method_cols + ["esforco"]]
        .drop_duplicates()
        .groupby(effort_cols, dropna=False)["esforco"]
        .sum()
        .reset_index(name="esforco_total_ponto")
    )

    observed = quant[(quant["contagem"] > 0) & (quant["nome_cientifico"] != "")].copy()
    species_point_campaign = (
        observed.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], dropna=False)["contagem"]
        .sum()
        .reset_index()
        .merge(effort, on=["nome_campanha", "nome_ponto"], how="left")
    )
    species_point_campaign = species_point_campaign[
        species_point_campaign["esforco_total_ponto"].notna()
        & (species_point_campaign["esforco_total_ponto"] > 0)
    ].copy()
    species_point_campaign["cpuen"] = (
        species_point_campaign["contagem"] / species_point_campaign["esforco_total_ponto"]
    ) * 100
    species_point_campaign["campanha_seq"] = species_point_campaign["nome_campanha"].map(
        traditional.standard_campaign_sequence
    )
    species_point_campaign["campanha_curta"] = species_point_campaign["nome_campanha"].map(_campaign_short)
    species_point_campaign["area_controle"] = species_point_campaign["nome_ponto"].map(traditional.avg_runner.AREA_BY_POINT)

    totals = (
        species_point_campaign.groupby("nome_cientifico", dropna=False)
        .agg(
            cpuen_total=("cpuen", "sum"),
            campanhas_ocorrencia=("nome_campanha", "nunique"),
            pontos_ocorrencia=("nome_ponto", "nunique"),
            registros=("cpuen", "size"),
        )
        .reset_index()
    )
    grand_total = float(totals["cpuen_total"].sum())
    totals["cpuen_percentual"] = np.where(grand_total > 0, (totals["cpuen_total"] / grand_total) * 100, 0.0)
    totals = totals.sort_values(["cpuen_percentual", "cpuen_total"], ascending=False).reset_index(drop=True)
    totals["ordem"] = np.arange(1, len(totals) + 1)

    campaigns = sorted(
        species_point_campaign["nome_campanha"].dropna().unique().tolist(),
        key=traditional.standard_campaign_sequence,
    )
    presence = (
        species_point_campaign.assign(presente=1)
        .pivot_table(index="nome_cientifico", columns="nome_campanha", values="presente", aggfunc="max", fill_value=0)
        .reindex(index=totals["nome_cientifico"], columns=campaigns, fill_value=0)
        .reset_index()
    )
    points = [point for point in POINT_ORDER if point in set(species_point_campaign["nome_ponto"])]
    spatial = (
        species_point_campaign.pivot_table(
            index="nome_cientifico",
            columns="nome_ponto",
            values="cpuen",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(index=totals["nome_cientifico"], columns=points, fill_value=0)
        .reset_index()
    )
    return totals, presence, spatial


def _decorate_year_bands(ax: Any, campaigns: list[str], n_species: int) -> None:
    seq_by_idx = {idx: traditional.standard_campaign_sequence(campaign) for idx, campaign in enumerate(campaigns)}
    for year, start, end in YEAR_BANDS:
        indices = [idx for idx, seq in seq_by_idx.items() if start <= seq <= end]
        if not indices:
            continue
        left = min(indices) - 0.5
        right = max(indices) + 0.5
        if year in {2023, 2025}:
            ax.axvspan(left, right, color="#F3F8EF", zorder=0)
        ax.text((left + right) / 2, -0.95, f"Ano {year}", ha="center", va="bottom", fontsize=8.5, color="#50614A")
        ax.axvline(right, color="#B8B8B8", linestyle=":", linewidth=0.8, zorder=3)
    ax.set_ylim(n_species - 0.5, -1.05)


def plot_synthesis(totals: pd.DataFrame, presence: pd.DataFrame, spatial: pd.DataFrame, output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    species = totals["nome_cientifico"].tolist()
    n_species = len(species)
    campaigns = [col for col in presence.columns if col != "nome_cientifico"]
    points = [col for col in spatial.columns if col != "nome_cientifico"]

    fig = plt.figure(figsize=(16.4, 8.5), dpi=450)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1.35, 1.05], wspace=0.055)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_time = fig.add_subplot(gs[0, 1], sharey=ax_bar)
    ax_space = fig.add_subplot(gs[0, 2], sharey=ax_bar)

    y = np.arange(n_species)
    labels = species

    bars = ax_bar.barh(y, totals["cpuen_percentual"], color=BAR_COLOR, edgecolor=BAR_EDGE, height=0.62)
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(labels, fontsize=10.2)
    for label in ax_bar.get_yticklabels():
        label.set_fontstyle("italic")
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel("Contribuição relativa da CPUEn (%)", fontsize=10.5)
    ax_bar.set_xlim(0, max(5.0, float(totals["cpuen_percentual"].max()) * 1.18))
    ax_bar.grid(axis="x", color="#D9D9D9", linewidth=0.75, alpha=0.85)
    ax_bar.grid(axis="y", visible=False)
    for spine in ["top", "right", "left"]:
        ax_bar.spines[spine].set_visible(False)
    ax_bar.tick_params(axis="x", labelsize=9.5)
    ax_bar.tick_params(axis="y", length=0)
    for bar, value in zip(bars, totals["cpuen_percentual"]):
        ax_bar.text(
            bar.get_width() + max(float(totals["cpuen_percentual"].max()) * 0.012, 0.12),
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            ha="left",
            fontsize=9.4,
            color="#222222",
        )

    presence_values = presence[campaigns].to_numpy(dtype=float)
    cmap = matplotlib.colors.ListedColormap([ABSENT_COLOR, PRESENT_COLOR])
    ax_time.imshow(presence_values, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=1, zorder=1)
    _decorate_year_bands(ax_time, campaigns, n_species)
    ax_time.set_xticks(np.arange(len(campaigns)))
    ax_time.set_xticklabels([_campaign_short(campaign) for campaign in campaigns], rotation=90, fontsize=6.2)
    ax_time.tick_params(axis="y", left=False, labelleft=False)
    ax_time.set_xlabel("Constância temporal (C001-C047)", fontsize=10.5)
    for spine in ["top", "right", "left"]:
        ax_time.spines[spine].set_visible(False)
    ax_time.set_yticks(y)
    ax_time.set_xticks(np.arange(-0.5, len(campaigns), 1), minor=True)
    ax_time.set_yticks(np.arange(-0.5, n_species, 1), minor=True)
    ax_time.grid(which="minor", color="white", linewidth=0.35)
    ax_time.tick_params(which="minor", bottom=False, left=False)

    max_spatial = float(spatial[points].to_numpy(dtype=float).max()) if points else 0.0
    for x, point in enumerate(points):
        values = spatial[point].to_numpy(dtype=float)
        sizes = np.where(values > 0, 28 + (values / max_spatial) * 230 if max_spatial > 0 else 28, 0)
        color = AREA_COLORS.get(traditional.avg_runner.AREA_BY_POINT.get(point), "#777777")
        ax_space.scatter(
            np.full(n_species, x),
            y,
            s=sizes,
            color=color,
            edgecolor="#1F1F1F",
            linewidth=0.38,
            alpha=0.82,
        )
    boundary = points.index("PIC-10") - 0.5 if "PIC-10" in points else None
    if boundary is not None:
        ax_space.axvline(boundary, color="#4F4F4F", linestyle=":", linewidth=1.0)
    ax_space.set_xlim(-0.6, len(points) - 0.4)
    ax_space.set_xticks(np.arange(len(points)))
    ax_space.set_xticklabels(points, rotation=90, fontsize=8.8)
    ax_space.tick_params(axis="y", left=False, labelleft=False)
    ax_space.set_xlabel("Distribuição espacial por ponto", fontsize=10.5)
    ax_space.grid(axis="y", color="#EEEEEE", linewidth=0.55)
    for spine in ["top", "right", "left"]:
        ax_space.spines[spine].set_visible(False)

    area_handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=AREA_COLORS[AREA_01], markeredgecolor="#1F1F1F", markersize=7.5, label="Área de controle 01"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=AREA_COLORS[AREA_02], markeredgecolor="#1F1F1F", markersize=7.5, label="Área de controle 02"),
    ]
    size_values = [max_spatial * p for p in [0.25, 0.55, 0.90] if max_spatial > 0]
    size_handles = [
        plt.scatter([], [], s=28 + (value / max_spatial) * 230, color="#9EB77E", edgecolor="#1F1F1F", linewidth=0.38, label=f"{value:.0f}")
        for value in size_values
    ]
    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(labels, fontsize=10.2)
    for label in ax_bar.get_yticklabels():
        label.set_fontstyle("italic")
    ax_bar.tick_params(axis="y", length=0, labelleft=True)

    legend1 = fig.legend(
        handles=area_handles,
        loc="upper right",
        bbox_to_anchor=(0.985, 0.985),
        frameon=False,
        fontsize=8.8,
    )
    if size_handles:
        ax_space.legend(handles=size_handles, title="CPUEn no ponto", loc="lower right", frameon=False, fontsize=8.0, title_fontsize=8.5)

    fig.subplots_adjust(left=0.19, right=0.985, top=0.90, bottom=0.16)
    out_png = output_dir / "08C_grafico_sintese_cpuen_especies_temporal_espacial_ictiofauna.png"
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return str(out_png)


def write_tables(totals: pd.DataFrame, presence: pd.DataFrame, spatial: pd.DataFrame, output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_xlsx = output_dir / "08C_df_sintese_cpuen_especies_temporal_espacial_ictiofauna.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        totals.to_excel(writer, sheet_name="ranking_cpuen", index=False)
        presence.to_excel(writer, sheet_name="presenca_temporal", index=False)
        spatial.to_excel(writer, sheet_name="cpuen_por_ponto", index=False)
    return str(out_xlsx)


def build(output_dir: Path = FINAL_DIR, support_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    totals, presence, spatial = build_cpuen_tables()
    figure = plot_synthesis(totals, presence, spatial, output_dir)
    table = write_tables(totals, presence, spatial, output_dir)
    support_dir.mkdir(parents=True, exist_ok=True)
    support_table = write_tables(totals, presence, spatial, support_dir)
    support_figure = plot_synthesis(totals, presence, spatial, support_dir)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": traditional.PROJECT_CODE,
        "group": GROUP,
        "status": "generated",
        "metric": "CPUEn",
        "output_dir": str(output_dir),
        "support_dir": str(support_dir),
        "figure": figure,
        "table": table,
        "support_figure": support_figure,
        "support_table": support_table,
        "species": int(len(totals)),
        "campaigns": int(len([col for col in presence.columns if col != "nome_cientifico"])),
        "points": int(len([col for col in spatial.columns if col != "nome_cientifico"])),
        "sampling_rule": "Regra revisada em 2026-07-15; nao-amostragem como ausencia.",
    }
    manifest = support_dir / "manifesto_08C_sintese_cpuen_especies.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
