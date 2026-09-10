from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
SUPPORT_DIR = BASE_DIR / "zoobentos_sample_sufficiency_20260722"
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados bentos"
    r"\Consolidado_2026"
)

N_PERMUTATIONS = 200
RANDOM_SEED = 20260722
OBS_COLOR = "#007032"
EST_COLOR = "#6A8F2F"
SHADE_COLOR = "#C9DDB4"


def _unit_sort_key(campaign: str, point: str) -> tuple[int, int]:
    campaign_number = int(str(campaign).replace("C", "")) if str(campaign).replace("C", "").isdigit() else 999
    point_number = int(str(point).replace("PIC-", "")) if str(point).replace("PIC-", "").isdigit() else 999
    return campaign_number, point_number


def _build_presence_matrix(base: pd.DataFrame, point_campaign: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monitored = point_campaign[point_campaign["Status_Monitoramento"].eq("Monitorado")].copy()
    monitored["Unidade_Amostral"] = monitored["Campanha"].astype(str) + "_" + monitored["Ponto"].astype(str)
    monitored = monitored.sort_values(
        ["Campanha", "Ponto"],
        key=lambda col: col.map(lambda value: _unit_sort_key(value, "PIC-999")[0])
        if col.name == "Campanha"
        else col.map(lambda value: _unit_sort_key("C999", value)[1]),
    )

    positive = base[
        base["Status_Monitoramento"].eq("Monitorado")
        & base["Nome_Cientifico"].notna()
        & (base["Numero_de_Individuos"].fillna(0) > 0)
    ].copy()
    positive["Unidade_Amostral"] = positive["Campanha"].astype(str) + "_" + positive["Ponto"].astype(str)

    matrix = (
        positive.assign(presente=1)
        .pivot_table(index="Unidade_Amostral", columns="Nome_Cientifico", values="presente", aggfunc="max", fill_value=0)
        .astype(np.uint8)
    )
    matrix = matrix.reindex(monitored["Unidade_Amostral"], fill_value=0)
    unit_table = monitored[
        [
            "Unidade_Amostral",
            "Campanha",
            "Ponto",
            "Ano_Temporal",
            "Periodo_Hidrologico",
            "riqueza",
            "abundancia",
            "Status_Monitoramento",
        ]
    ].copy()
    return matrix, unit_table


def _rarefaction_jackknife(matrix: pd.DataFrame) -> pd.DataFrame:
    data = matrix.to_numpy(dtype=np.uint8)
    n_units, n_taxa = data.shape
    rng = np.random.default_rng(RANDOM_SEED)
    obs = np.zeros((N_PERMUTATIONS, n_units), dtype=float)
    jack = np.zeros((N_PERMUTATIONS, n_units), dtype=float)

    for perm_idx in range(N_PERMUTATIONS):
        order = rng.permutation(n_units)
        counts = np.zeros(n_taxa, dtype=np.int16)
        for step, unit_idx in enumerate(order, start=1):
            counts += data[unit_idx]
            richness = float((counts > 0).sum())
            uniques = float((counts == 1).sum())
            obs[perm_idx, step - 1] = richness
            jack[perm_idx, step - 1] = richness + uniques * (step - 1) / step

    curve = pd.DataFrame(
        {
            "n_amostras": np.arange(1, n_units + 1),
            "riqueza_obs_media": obs.mean(axis=0),
            "riqueza_est_jackknife1_media": jack.mean(axis=0),
            "jackknife1_desvio_padrao": jack.std(axis=0, ddof=1),
        }
    )
    curve["jackknife1_inf"] = curve["riqueza_est_jackknife1_media"] - curve["jackknife1_desvio_padrao"]
    curve["jackknife1_sup"] = curve["riqueza_est_jackknife1_media"] + curve["jackknife1_desvio_padrao"]
    return curve


def _plot_curve(curve: pd.DataFrame, output_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(13.8, 7.1), dpi=420)
    x = curve["n_amostras"].to_numpy(dtype=float)
    obs = curve["riqueza_obs_media"].to_numpy(dtype=float)
    jack = curve["riqueza_est_jackknife1_media"].to_numpy(dtype=float)
    lower = curve["jackknife1_inf"].clip(lower=0).to_numpy(dtype=float)
    upper = curve["jackknife1_sup"].to_numpy(dtype=float)

    ax.fill_between(x, lower, upper, color=SHADE_COLOR, alpha=0.45, zorder=1)
    ax.plot(x, obs, color=OBS_COLOR, linewidth=2.0, label="Riqueza observada", zorder=3)
    ax.plot(x, jack, color=EST_COLOR, linewidth=2.0, label="Riqueza estimada (Jackknife 1)", zorder=4)

    ax.text(x[-1] + 2, obs[-1], f"{obs[-1]:.0f}", ha="left", va="center", fontsize=13)
    ax.text(x[-1] + 2, jack[-1], f"{jack[-1]:.1f}", ha="left", va="center", fontsize=13)
    ax.set_xlabel("Número de unidades amostrais", fontsize=16)
    ax.set_ylabel("Riqueza taxonômica", fontsize=16)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2, frameon=False, fontsize=15)
    ax.grid(axis="y", color="#E7E7E7", linewidth=0.6, linestyle="--", alpha=0.55)
    ax.set_xlim(0, x[-1] + 28)
    ax.set_ylim(bottom=-1)
    ax.tick_params(axis="both", labelsize=14)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
    fig.subplots_adjust(top=0.84)
    fig.savefig(output_png, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)


def build(output_dir: Path = FINAL_DIR, support_dir: Path = SUPPORT_DIR) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    support_dir.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(ANALYTIC_XLSX, sheet_name="base_analitica")
    point_campaign = pd.read_excel(ANALYTIC_XLSX, sheet_name="ponto_campanha")
    matrix, units = _build_presence_matrix(base, point_campaign)
    curve = _rarefaction_jackknife(matrix)

    output_xlsx = output_dir / "12_df_curva_suficiencia_zoobentos.xlsx"
    output_png = output_dir / "12_curva_suficiencia_amostral_zoobentos.png"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        curve.to_excel(writer, sheet_name="Sheet1", index=False)
        units.to_excel(writer, sheet_name="unidades_amostrais", index=False)
        pd.DataFrame(
            [
                {
                    "unidades_amostrais_monitoradas": int(matrix.shape[0]),
                    "taxons_observados": int((matrix.sum(axis=0) > 0).sum()),
                    "permutacoes": N_PERMUTATIONS,
                    "riqueza_observada_final": float(curve["riqueza_obs_media"].iloc[-1]),
                    "jackknife1_final": float(curve["riqueza_est_jackknife1_media"].iloc[-1]),
                    "cobertura_obs_jackknife1": float(
                        curve["riqueza_obs_media"].iloc[-1] / curve["riqueza_est_jackknife1_media"].iloc[-1]
                    ),
                }
            ]
        ).to_excel(writer, sheet_name="resumo", index=False)

    _plot_curve(curve, output_png)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": "BRAAVG002",
        "group": "Zoobentos",
        "method": "curva de suficiencia amostral por unidades campanha x ponto; riqueza observada media e Jackknife 1 por permutacoes",
        "n_permutations": N_PERMUTATIONS,
        "random_seed": RANDOM_SEED,
        "monitored_sampling_units": int(matrix.shape[0]),
        "taxa_observed": int((matrix.sum(axis=0) > 0).sum()),
        "final_observed_richness": float(curve["riqueza_obs_media"].iloc[-1]),
        "final_jackknife1": float(curve["riqueza_est_jackknife1_media"].iloc[-1]),
        "outputs": {"figure": str(output_png), "table": str(output_xlsx)},
    }
    manifest = support_dir / "manifesto_12_curva_suficiencia_zoobentos_20260722.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
