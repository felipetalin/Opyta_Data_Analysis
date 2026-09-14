from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_bentos_avg_bioindicator_minimaps_ictio_layout as bio_maps  # noqa: E402


BASE_DIR = bio_maps.BASE_DIR
ANALYTIC_XLSX = bio_maps.ANALYTIC_XLSX
FINAL_DIR = bio_maps.FINAL_DIR
SUPPORT_DIR = BASE_DIR / "zoobentos_exotic_associated_taxa_minimaps_20260722"

TARGET_TAXA = ["Melanoides sp.", "Corbicula sp.", "Physa sp."]
TAXON_COLORS = {
    "Melanoides sp.": "#D7301F",
    "Corbicula sp.": "#F07D00",
    "Physa sp.": "#FFD34E",
}
TAXON_LABELS = {
    "Melanoides sp.": r"$\it{Melanoides}$ sp.",
    "Corbicula sp.": r"$\it{Corbicula}$ sp.",
    "Physa sp.": r"$\it{Physa}$ sp.",
}
YEARS = [2023, 2024, 2025, 2026]


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


def _bubble_size(value: float, max_value: float) -> float:
    if value <= 0 or max_value <= 0:
        return 0.0
    return 70 + np.sqrt(value / max_value) * 380


def build_annual_taxa(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monitored = base[base["Status_Monitoramento"].eq("Monitorado")].copy()
    coords = monitored[["Ponto", "Area_Controle", "Latitude", "Longitude"]].drop_duplicates("Ponto")
    positive = monitored[
        monitored["Nome_Cientifico"].isin(TARGET_TAXA)
        & (monitored["Numero_de_Individuos"].fillna(0) > 0)
    ].copy()
    annual = (
        positive.groupby(["Ano_Temporal", "Ponto", "Nome_Cientifico"], as_index=False)
        .agg(
            abundancia_anual=("Numero_de_Individuos", "sum"),
            campanhas_ocorrencia=("Campanha", "nunique"),
            primeira_campanha=("Campanha", "min"),
            ultima_campanha=("Campanha", "max"),
        )
        .merge(coords, on="Ponto", how="left")
        .sort_values(["Ano_Temporal", "Nome_Cientifico", "Ponto"])
        .reset_index(drop=True)
    )
    summary = (
        positive.groupby("Nome_Cientifico", as_index=False)
        .agg(
            abundancia_total=("Numero_de_Individuos", "sum"),
            campanhas_ocorrencia=("Campanha", "nunique"),
            pontos_ocorrencia=("Ponto", "nunique"),
            anos_ocorrencia=("Ano_Temporal", "nunique"),
        )
        .set_index("Nome_Cientifico")
        .reindex(TARGET_TAXA)
        .fillna(0)
        .reset_index()
    )
    summary["constancia_percentual"] = summary["campanhas_ocorrencia"] / 47 * 100
    status = {
        "Melanoides sp.": "Provavelmente exotico",
        "Corbicula sp.": "Exotico",
        "Physa sp.": "Origem indeterminada",
    }
    summary["status_adotado"] = summary["Nome_Cientifico"].map(status)
    return annual, summary


def plot_panel(annual: pd.DataFrame, coords: pd.DataFrame, output_png: Path) -> None:
    context = bio_maps._spatial_context(coords[["Ponto", "Longitude", "Latitude"]].drop_duplicates())
    max_value = float(annual["abundancia_anual"].max()) if not annual.empty else 0.0
    fig, axes_grid = plt.subplots(2, 2, figsize=(16.54, 11.69), dpi=420, sharex=True, sharey=True)
    axes = axes_grid.ravel()

    for ax, year in zip(axes, YEARS, strict=True):
        bio_maps._base_map(ax, coords[["Ponto", "Longitude", "Latitude"]].drop_duplicates(), context)
        data = annual[annual["Ano_Temporal"].eq(year)].copy()
        for taxon in TARGET_TAXA:
            subset = data[data["Nome_Cientifico"].eq(taxon)]
            if subset.empty:
                continue
            ax.scatter(
                subset["Longitude"],
                subset["Latitude"],
                s=[_bubble_size(v, max_value) for v in subset["abundancia_anual"]],
                color=TAXON_COLORS[taxon],
                edgecolor="#1F1F1F",
                linewidth=0.75,
                alpha=0.86,
                zorder=3,
            )
        ax.set_title(str(year), fontsize=17, fontweight="bold", pad=10)

    axes[0].set_ylabel("Latitude", fontsize=11)
    axes[2].set_ylabel("Latitude", fontsize=11)
    axes[2].set_xlabel("Longitude", fontsize=11)
    axes[3].set_xlabel("Longitude", fontsize=11)

    taxon_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=TAXON_COLORS[taxon],
            markeredgecolor="#1F1F1F",
            markersize=8.5,
            label=TAXON_LABELS[taxon],
        )
        for taxon in TARGET_TAXA
    ]
    area_handles = [
        Line2D([0], [0], color=bio_maps.CONTROL_AREA_COLORS["Area de controle 01"], lw=1.2, ls="--", label="Área de controle 01"),
        Line2D([0], [0], color=bio_maps.CONTROL_AREA_COLORS["Area de controle 02"], lw=1.2, ls="--", label="Área de controle 02"),
    ]
    scale_values = [1, 4, int(max_value)] if max_value > 4 else sorted({1, int(max_value)})
    size_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="#7BAA4D",
            markeredgecolor="#1F1F1F",
            alpha=0.72,
            markersize=np.sqrt(_bubble_size(value, max_value)) / 1.7,
            label=str(value),
        )
        for value in scale_values
        if value > 0
    ]
    fig.legend(handles=taxon_handles, loc="lower center", ncol=3, frameon=False, fontsize=11.0, bbox_to_anchor=(0.5, 0.071))
    fig.legend(handles=size_handles, title="Abundância anual", loc="lower center", ncol=len(size_handles), frameon=False, fontsize=10.3, title_fontsize=10.7, bbox_to_anchor=(0.5, 0.038))
    fig.legend(handles=area_handles, loc="lower center", ncol=2, frameon=False, fontsize=10.3, bbox_to_anchor=(0.5, 0.012))
    fig.tight_layout(rect=(0.03, 0.125, 0.99, 0.96))
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300)
    plt.close(fig)


def build(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(ANALYTIC_XLSX, sheet_name="base_analitica")
    coords = base[base["Status_Monitoramento"].eq("Monitorado")][["Ponto", "Area_Controle", "Latitude", "Longitude"]].drop_duplicates("Ponto")
    annual, summary = build_annual_taxa(base)

    output_png = output_dir / "13_mini_mapas_anuais_taxons_associados_fauna_exotica_zoobentos.png"
    output_xlsx = output_dir / "13_df_mini_mapas_anuais_taxons_associados_fauna_exotica_zoobentos.xlsx"
    plot_panel(annual, coords, output_png)

    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        annual.to_excel(writer, sheet_name="abundancia_anual_ponto", index=False)
        summary.to_excel(writer, sheet_name="resumo_taxons", index=False)
        pd.DataFrame({"taxon": TARGET_TAXA, "cor_hex": [TAXON_COLORS[taxon] for taxon in TARGET_TAXA]}).to_excel(
            writer, sheet_name="legenda_taxons", index=False
        )

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": "BRAAVG002",
        "group": "Zoobentos",
        "layout": "A3 paisagem; painel anual 2x2 no padrao dos minimapas BMWP",
        "taxa": TARGET_TAXA,
        "outputs": {"figure": output_png, "table": output_xlsx},
    }
    manifest_path = support_dir / "manifesto_13_minimapas_taxons_associados_fauna_exotica_zoobentos_20260722.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    manifest["manifest"] = manifest_path
    return manifest


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
