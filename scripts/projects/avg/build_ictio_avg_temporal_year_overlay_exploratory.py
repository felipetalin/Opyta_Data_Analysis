from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
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
    / "traditional_temporal_overlay_exploratory_20260714"
)

AC01_POINTS = [
    "PIC-01",
    "PIC-02",
    "PIC-03",
    "PIC-04",
    "PIC-05",
    "PIC-06",
    "PIC-07",
    "PIC-08",
    "PIC-09",
    "PIC-11",
]
AC02_POINTS = ["PIC-10", "PIC-12", "PIC-13"]
POINT_ORDER = AC01_POINTS + AC02_POINTS
MONTH_ORDER = [8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7]
MONTH_LABELS = ["Ago", "Set", "Out", "Nov", "Dez", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul"]
YEAR_COLORS = {
    2023: "#0B7A3B",
    2024: "#7FA33A",
    2025: "#1F5A91",
    2026: "#C27A24",
}


def campaign_parts(value: object) -> tuple[int, int, int]:
    text = str(value or "")
    match = re.match(r"^C0*(\d+)-(\d{4})-(\d{2})-", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Campanha padrao nao reconhecida: {text}")
    return int(match.group(1)), int(match.group(3)), int(match.group(2))


def add_temporal_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    parsed = out["nome_campanha"].map(campaign_parts)
    out["campanha_seq"] = parsed.map(lambda item: item[0])
    out["mes"] = parsed.map(lambda item: item[1])
    out["ano_calendario"] = parsed.map(lambda item: item[2])
    out["ano_temporal"] = np.where(out["mes"] >= 8, out["ano_calendario"] + 1, out["ano_calendario"])
    out["mes_ordem"] = out["mes"].map({month: index + 1 for index, month in enumerate(MONTH_ORDER)})
    return out


def setup_axes() -> tuple[plt.Figure, np.ndarray]:
    fig, axes = plt.subplots(4, 4, figsize=(17.2, 11.2), dpi=450, sharex=True, sharey=True)
    for ax in axes.ravel()[len(POINT_ORDER) :]:
        ax.axis("off")
    return fig, axes


def plot_overlay(
    df: pd.DataFrame,
    *,
    value_col: str,
    ylabel: str,
    filename: str,
    decimals: int,
    fill_missing: float = 0.0,
) -> str:
    data = add_temporal_fields(df)
    years = sorted(int(year) for year in data["ano_temporal"].dropna().unique())
    fig, axes = setup_axes()
    x = np.arange(1, 13)

    values = pd.to_numeric(data[value_col], errors="coerce").fillna(0)
    ymax = max(float(values.max()) if not values.empty else 0.0, 1.0) * 1.15

    handles = []
    labels = []
    for ax, point in zip(axes.ravel(), POINT_ORDER):
        point_data = data[data["nome_ponto"] == point].copy()
        for year in years:
            year_data = (
                point_data[point_data["ano_temporal"] == year]
                .set_index("mes_ordem")
                .reindex(range(1, 13))
            )
            y = pd.to_numeric(year_data[value_col], errors="coerce").fillna(fill_missing).to_numpy(dtype=float)
            if year == max(years):
                y[np.array(MONTH_ORDER) == 7] = np.nan
            line = ax.plot(
                x,
                y,
                marker="o",
                markersize=3.8,
                linewidth=1.5,
                color=YEAR_COLORS.get(year, "#555555"),
                label=f"AT {year}",
            )[0]
            if point == POINT_ORDER[0]:
                handles.append(line)
                labels.append(f"AT {year}")

        ax.text(0.03, 0.92, point, transform=ax.transAxes, ha="left", va="top", fontsize=13, fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(MONTH_LABELS, rotation=90)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.6, alpha=0.7)
        ax.grid(axis="x", color="#EEEEEE", linewidth=0.45, alpha=0.65)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

    for ax in axes[-1, :]:
        ax.set_xlabel("Mes do ano temporal")
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)

    fig.legend(handles, labels, loc="upper center", ncol=len(handles), frameon=False, fontsize=13)
    fig.tight_layout(rect=[0.02, 0.03, 1.0, 0.94])
    out_png = OUTPUT_DIR / filename
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    return str(out_png)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    richness = pd.read_excel(FINAL_DIR / "02_df_riqueza_por_ponto_ictiofauna.xlsx")
    abundance = pd.read_excel(FINAL_DIR / "03_df_abundancia_por_ponto_ictiofauna.xlsx")
    cpue = pd.read_excel(FINAL_DIR / "06_df_cpue_por_ponto_ictiofauna.xlsx")
    diversity = pd.read_excel(FINAL_DIR / "10_df_diversidade_alfa_ictiofauna.xlsx")
    diversity = diversity[diversity["nome_ponto"].isin(POINT_ORDER)].copy()

    outputs = {
        "02_riqueza": plot_overlay(
            richness,
            value_col="riqueza",
            ylabel="Riqueza taxonomica",
            filename="EXP_02_riqueza_por_ponto_curvas_anos_temporais.png",
            decimals=0,
        ),
        "03_abundancia": plot_overlay(
            abundance,
            value_col="abundancia_total",
            ylabel="Abundancia total",
            filename="EXP_03_abundancia_por_ponto_curvas_anos_temporais.png",
            decimals=0,
        ),
        "06_cpuen": plot_overlay(
            cpue,
            value_col="cpuen",
            ylabel="CPUEn (ind/100m2)",
            filename="EXP_06_cpuen_por_ponto_curvas_anos_temporais.png",
            decimals=2,
        ),
        "07_cpueb": plot_overlay(
            cpue,
            value_col="cpueb",
            ylabel="CPUEb (g/100m2)",
            filename="EXP_07_cpueb_por_ponto_curvas_anos_temporais.png",
            decimals=2,
        ),
        "10_shannon": plot_overlay(
            diversity,
            value_col="Shannon_H",
            ylabel="Shannon (H')",
            filename="EXP_10A_shannon_por_ponto_curvas_anos_temporais.png",
            decimals=2,
        ),
        "10_pielou": plot_overlay(
            diversity,
            value_col="Pielou_J",
            ylabel="Pielou (J')",
            filename="EXP_10B_pielou_por_ponto_curvas_anos_temporais.png",
            decimals=2,
        ),
    }

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "exploratory_not_final",
        "source_dir": str(FINAL_DIR),
        "output_dir": str(OUTPUT_DIR),
        "idea": "Uma figura por metrica, com pontos em paineis e anos temporais como curvas.",
        "temporal_year_axis": "Ago-Jul",
        "outputs": outputs,
        "recommendation": "Avaliar visualmente; se aprovado, substituir os PNGs anuais temporais por estes overlays para 02, 03, 06, 07 e 10.",
    }
    (OUTPUT_DIR / "manifesto_overlay_anos_temporais_ictiofauna.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "README_overlay_anos_temporais_ictiofauna.md").write_text(
        "\n".join(
            [
                "# Exploratorio - curvas por ano temporal",
                "",
                "Este teste usa uma figura por metrica. Cada painel representa um ponto amostral e cada linha representa um ano temporal.",
                "",
                "- Eixo X: meses do ano temporal, de agosto a julho.",
                "- Linhas: anos temporais 2023, 2024, 2025 e 2026.",
                "- Ano temporal 2026 ainda nao possui julho.",
                "",
                "Uso recomendado: substituir as figuras anuais temporais de 02, 03, 06, 07 e 10 caso a leitura seja aprovada.",
                "A matriz 04B nao foi substituida neste teste, porque ela compara taxons por campanha e nao metricas por ponto.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
