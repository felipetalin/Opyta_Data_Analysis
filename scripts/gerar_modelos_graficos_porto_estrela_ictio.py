from __future__ import annotations

import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DATE_TAG = "20260602"
RESULTADOS_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados"
)
BASE_FILE = RESULTADOS_DIR / f"base_analitica_ictiofauna_porto_estrela_{DATE_TAG}.xlsx"
OUT_DIR = RESULTADOS_DIR / f"modelos_graficos_porto_estrela_{DATE_TAG}"
OUT_XLSX = OUT_DIR / f"modelos_graficos_porto_estrela_{DATE_TAG}.xlsx"

PRIMARY = "#002060"
SECONDARY = "#5B9BD5"
HIGHLIGHT = "#1F4E79"
LIGHT = "#DBE5F1"
GRID = "#D9D9D9"
EDGE = "black"
PALETTE = ["#002060", "#1F4E79", "#5B9BD5", "#9DC3E6", "#DBE5F1", "#808080"]
ALT_PALETTE = [
    "#2E6EA6",
    "#D4672A",
    "#6BA547",
    "#7B4EA3",
    "#C9A227",
    "#4E9A99",
    "#B75D69",
    "#6C757D",
    "#A6CEE3",
    "#FDBF6F",
]
FIGSIZE_WIDE = (18, 10.2)
FIGSIZE_PANEL = (18, 11.2)
DPI = 300
FONT_BASE = 17
FONT_AXIS = 17
FONT_TICK = 13
FONT_LEGEND = 15
FONT_PANEL = 16


def _clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _norm_bool_label(value: object) -> str:
    text = _clean_text(value).lower()
    text = text.replace("?", "a")
    if text in {"sim", "s", "true", "1"}:
        return "Sim"
    if text in {"nao", "não", "n", "false", "0"}:
        return "Nao"
    return _clean_text(value)


def _class_migration(value: object) -> str:
    text = _clean_text(value).lower().replace("?", "a")
    if "migradora" not in text and "migrador" not in text:
        return _clean_text(value).replace("N?o", "Nao")
    if text.startswith("nao") or text.startswith("n?o") or "nao migr" in text:
        return "Nao migradora"
    return "Migradora"


def _class_origin(value: object) -> str:
    text = _clean_text(value).lower().replace("?", "a")
    if "nativa" not in text:
        return _clean_text(value).replace("N?o", "Nao")
    if text.startswith("nao") or text.startswith("n?o") or "nao nativa" in text:
        return "Nao nativa"
    return "Nativa"


def _ah_sort_value(value: object) -> int:
    match = re.search(r"AH(\d{4})", _clean_text(value))
    if not match:
        return 999999
    return int(match.group(1))


def _ah_label(value: object) -> str:
    match = re.search(r"AH(\d{4})", _clean_text(value))
    if not match:
        return _clean_text(value)
    code = match.group(1)
    return f"{code[:2]}-{code[2:]}"


def _configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": FONT_BASE,
            "axes.labelsize": FONT_AXIS,
            "axes.titlesize": FONT_PANEL,
            "xtick.labelsize": FONT_TICK,
            "ytick.labelsize": FONT_TICK,
            "legend.fontsize": FONT_LEGEND,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _style_axes(ax, grid_axis: str = "y") -> None:
    ax.grid(False)
    ax.grid(axis=grid_axis, color=GRID, alpha=0.25, linewidth=1)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(EDGE)
        spine.set_linewidth(1.2)
    ax.tick_params(colors="black")


def _save(fig: plt.Figure, name: str) -> Path:
    path = OUT_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _clean_previous_outputs() -> None:
    for path in OUT_DIR.glob("modelo_*.png"):
        path.unlink()


def _write_sheet(writer: pd.ExcelWriter, name: str, df: pd.DataFrame) -> None:
    df.to_excel(writer, sheet_name=name[:31], index=False)


def _collector_curve(base: pd.DataFrame, n_perm: int = 300, seed: int = 42) -> pd.DataFrame:
    unit_cols = ["campanha_ordem", "Campanha", "Ponto", "Ordem_Global_Montante_Jusante"]
    pa = (
        base.loc[base["Numero_de_Individuos"].gt(0), unit_cols + ["Nome_Cientifico"]]
        .drop_duplicates()
        .sort_values(["campanha_ordem", "Ordem_Global_Montante_Jusante", "Ponto"])
    )
    units = pa[unit_cols].drop_duplicates().reset_index(drop=True)
    species = sorted(pa["Nome_Cientifico"].dropna().astype(str).unique())
    matrix = (
        pa.assign(Presenca=1)
        .pivot_table(index=["Campanha", "Ponto"], columns="Nome_Cientifico", values="Presenca", aggfunc="max", fill_value=0)
        .reindex(pd.MultiIndex.from_frame(units[["Campanha", "Ponto"]]), fill_value=0)
        .reindex(columns=species, fill_value=0)
        .to_numpy(dtype=int)
    )

    rng = np.random.default_rng(seed)
    n_units = matrix.shape[0]
    richness = np.zeros((n_perm, n_units), dtype=float)
    jackknife = np.zeros((n_perm, n_units), dtype=float)

    for perm_idx in range(n_perm):
        order = rng.permutation(n_units)
        counts = np.zeros(matrix.shape[1], dtype=int)
        for step, unit_idx in enumerate(order, start=1):
            counts += matrix[unit_idx]
            s_obs = int((counts > 0).sum())
            q1 = int((counts == 1).sum())
            richness[perm_idx, step - 1] = s_obs
            jackknife[perm_idx, step - 1] = s_obs + ((step - 1) / step) * q1

    return pd.DataFrame(
        {
            "Unidade_Amostral": np.arange(1, n_units + 1),
            "Riqueza_Observada_Media": richness.mean(axis=0),
            "Riqueza_Observada_SD": richness.std(axis=0),
            "Jackknife1_Medio": jackknife.mean(axis=0),
            "Jackknife1_SD": jackknife.std(axis=0),
            "Permutacoes": n_perm,
            "Unidade": "Campanha x Ponto",
        }
    )


def plot_collector(curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    x = curve["Unidade_Amostral"].to_numpy()
    y_obs = curve["Riqueza_Observada_Media"].to_numpy()
    sd_obs = curve["Riqueza_Observada_SD"].to_numpy()
    y_jack = curve["Jackknife1_Medio"].to_numpy()
    sd_jack = curve["Jackknife1_SD"].to_numpy()
    ax.plot(
        x,
        y_obs,
        color=PRIMARY,
        linewidth=3.0,
        label="Riqueza observada média",
    )
    ax.fill_between(x, y_obs - sd_obs, y_obs + sd_obs, color=PRIMARY, alpha=0.12, linewidth=0, label="DP observado")
    ax.plot(
        x,
        y_jack,
        color=SECONDARY,
        linewidth=2.8,
        linestyle="--",
        label="Jackknife 1 médio",
    )
    ax.fill_between(x, y_jack - sd_jack, y_jack + sd_jack, color=SECONDARY, alpha=0.16, linewidth=0, label="DP Jackknife 1")
    ax.set_xlabel("Unidades amostrais acumuladas (campanha x ponto)")
    ax.set_ylabel("Riqueza acumulada")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=4, frameon=False)
    _style_axes(ax)
    _save(fig, "modelo_01_curva_coletor_observada_jackknife1.png")


def _richness_by_ah(base: pd.DataFrame) -> pd.DataFrame:
    pa = base.loc[base["Numero_de_Individuos"].gt(0)].copy()
    pa["Origem_Modelo"] = pa["Nativa_Nao_Nativa"].map(_class_origin)
    rows = []
    for ah, g in pa.groupby("ano_hidrologico"):
        species_total = set(g["Nome_Cientifico"])
        species_native = set(g.loc[g["Origem_Modelo"].eq("Nativa"), "Nome_Cientifico"])
        species_non_native = set(g.loc[g["Origem_Modelo"].ne("Nativa"), "Nome_Cientifico"])
        rows.append(
            {
                "ano_hidrologico": ah,
                "Rotulo": _ah_label(ah),
                "Ordem_AH": _ah_sort_value(ah),
                "Riqueza_Total": len(species_total),
                "Riqueza_Nativa": len(species_native),
                "Riqueza_Nao_Nativa": len(species_non_native),
            }
        )
    return pd.DataFrame(rows).sort_values("Ordem_AH")


def plot_richness(richness: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    x = np.arange(len(richness))
    ax.plot(x, richness["Riqueza_Total"], color=PRIMARY, marker="o", linewidth=3.0, markersize=7, label="Total")
    ax.plot(x, richness["Riqueza_Nativa"], color=SECONDARY, marker="o", linewidth=2.8, markersize=7, label="Nativas")
    ax.plot(
        x,
        richness["Riqueza_Nao_Nativa"],
        color="#808080",
        marker="o",
        linewidth=2.8,
        markersize=7,
        label="Não nativas",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(richness["Rotulo"], rotation=45, ha="right")
    ax.set_xlabel("Ano hidrológico")
    ax.set_ylabel("Riqueza de espécies")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=3, frameon=False)
    _style_axes(ax)
    _save(fig, "modelo_02_riqueza_temporal_ano_hidrologico.png")


def _cpue_by_ah_trecho(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    ah = (
        q.groupby(["ano_hidrologico", "Trecho"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
        .sort_values(["ano_hidrologico", "Trecho"])
    )
    ah["Ordem_AH"] = ah["ano_hidrologico"].map(_ah_sort_value)
    ah["Rotulo"] = ah["ano_hidrologico"].map(_ah_label)

    camp = (
        q.groupby(["campanha_ordem", "Campanha", "Trecho"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
        .sort_values(["campanha_ordem", "Trecho"])
    )
    return ah.sort_values(["Ordem_AH", "Trecho"]), camp


def _regression(y: pd.Series) -> tuple[float, float, float]:
    x = np.arange(1, len(y) + 1, dtype=float)
    yv = y.to_numpy(dtype=float)
    ok = np.isfinite(yv)
    if ok.sum() < 2:
        return np.nan, np.nan, np.nan
    slope, intercept = np.polyfit(x[ok], yv[ok], 1)
    pred = slope * x[ok] + intercept
    ss_res = np.sum((yv[ok] - pred) ** 2)
    ss_tot = np.sum((yv[ok] - np.mean(yv[ok])) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
    return float(intercept), float(slope), float(r2)


def plot_cpue_ah_panel(cpue_ah: pd.DataFrame) -> pd.DataFrame:
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True)
    rows = []
    specs = [
        ("Montante", "CPUEn", "CPUEn (ind/100m²)"),
        ("Montante", "CPUEb", "CPUEb (g/100m²)"),
        ("Jusante", "CPUEn", "CPUEn (ind/100m²)"),
        ("Jusante", "CPUEb", "CPUEb (g/100m²)"),
    ]
    labels = cpue_ah.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo"].tolist()
    x = np.arange(len(labels))
    for ax, (trecho, metric, ylabel) in zip(axes.ravel(), specs, strict=False):
        g = cpue_ah.loc[cpue_ah["Trecho"].eq(trecho)].sort_values("Ordem_AH")
        y = g[metric].reset_index(drop=True)
        ax.plot(x[: len(y)], y, marker="o", color=PRIMARY if trecho == "Montante" else SECONDARY, linewidth=3.0, markersize=7)
        intercept, slope, r2 = _regression(y)
        if np.isfinite(slope):
            ax.plot(x[: len(y)], slope * np.arange(1, len(y) + 1) + intercept, color="#808080", linestyle="--", linewidth=2.2)
        ax.text(
            0.50,
            0.92,
            f"{trecho} | R²={r2:.2f}" if np.isfinite(r2) else trecho,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=FONT_PANEL,
            color="black",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 2},
        )
        ax.set_ylabel(ylabel)
        _style_axes(ax)
        rows.append({"Trecho": trecho, "Metrica": metric, "Intercepto_a": intercept, "Coeficiente_b": slope, "R2": r2})
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    _save(fig, "modelo_03_fig13_painel_cpue_absoluta_regressao_ano_hidrologico.png")
    return pd.DataFrame(rows)


def plot_cpue_campaign_option(cpue_campaign: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(16, 9))
    for trecho, color in [("Montante", PRIMARY), ("Jusante", SECONDARY)]:
        g = cpue_campaign.loc[cpue_campaign["Trecho"].eq(trecho)].sort_values("campanha_ordem")
        ax.plot(g["campanha_ordem"], g["CPUEn"], color=color, linewidth=1.8, marker="o", markersize=3, label=trecho)
    ticks = cpue_campaign["campanha_ordem"].drop_duplicates().sort_values().tolist()
    shown = ticks[::5]
    ax.set_xticks(shown)
    ax.set_xlabel("Campanha individual")
    ax.set_ylabel("CPUEn (ind/100m2)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False)
    _style_axes(ax)
    _save(fig, "modelo_04_opcao_cpuen_por_campanha_individual.png")


def _cpue_percent_groups(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    q["Grupo"] = (
        q["Migradora_Nao_Migradora"].map(_class_migration).str.replace("Nao", "Não", regex=False)
        + " | "
        + q["Nativa_Nao_Nativa"].map(_class_origin).str.replace("Nao", "Não", regex=False)
    )
    agg = (
        q.groupby(["ano_hidrologico", "Trecho", "Grupo"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )
    agg["Ordem_AH"] = agg["ano_hidrologico"].map(_ah_sort_value)
    agg["Rotulo"] = agg["ano_hidrologico"].map(_ah_label)
    for metric in ["CPUEn", "CPUEb"]:
        total = agg.groupby(["ano_hidrologico", "Trecho"])[metric].transform("sum")
        agg[f"{metric}_pct"] = np.where(total.gt(0), agg[metric] / total * 100, 0)
    return agg.sort_values(["Ordem_AH", "Trecho", "Grupo"])


def plot_percent_groups(percent: pd.DataFrame) -> None:
    labels = percent.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True, sharey=True)
    specs = [
        ("Montante", "CPUEn_pct"),
        ("Montante", "CPUEb_pct"),
        ("Jusante", "CPUEn_pct"),
        ("Jusante", "CPUEb_pct"),
    ]
    for ax, (trecho, metric) in zip(axes.ravel(), specs, strict=False):
        g = percent.loc[percent["Trecho"].eq(trecho)].copy()
        pivot = (
            g.pivot_table(index="Rotulo", columns="Grupo", values=metric, aggfunc="sum", fill_value=0)
            .reindex(labels)
            .fillna(0)
        )
        groups = pivot.columns.tolist()
        ax.stackplot(x, [pivot[col].values for col in groups], labels=groups, colors=PALETTE[: len(groups)], alpha=0.95)
        ax.set_ylim(0, 100)
        metric_label = metric.replace("_pct", "")
        ax.set_title(f"{trecho} | {metric_label}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel(f"{metric_label} (%)")
        _style_axes(ax)
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    handles, labels_legend = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels_legend, loc="upper center", bbox_to_anchor=(0.5, 1.03), ncol=4, frameon=False)
    _save(fig, "modelo_05_fig14_cpue_percentual_grupos_area_empilhada.png")


def _native_species_heatmap(base: pd.DataFrame, recent_only: bool) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    q["Origem_Modelo"] = q["Nativa_Nao_Nativa"].map(_class_origin)
    q = q.loc[q["Origem_Modelo"].eq("Nativa")].copy()
    if recent_only:
        q = q.loc[q["ano_hidrologico"].isin(["AH2324", "AH2425", "AH2526"])].copy()
    agg = (
        q.groupby(["ano_hidrologico", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"))
    )
    total_by_species = agg.groupby("Nome_Cientifico")["CPUEn"].sum().sort_values(ascending=False)
    top_species = total_by_species.head(18).index.tolist()
    agg = agg.loc[agg["Nome_Cientifico"].isin(top_species)].copy()
    total_ah = agg.groupby("ano_hidrologico")["CPUEn"].transform("sum")
    agg["CPUEn_pct"] = np.where(total_ah.gt(0), agg["CPUEn"] / total_ah * 100, 0)
    agg["Ordem_AH"] = agg["ano_hidrologico"].map(_ah_sort_value)
    agg["Rotulo"] = agg["ano_hidrologico"].map(_ah_label)
    return agg.sort_values(["Nome_Cientifico", "Ordem_AH"])


def plot_native_heatmap(native: pd.DataFrame, filename: str) -> None:
    labels = native.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo"].tolist()
    species = native.groupby("Nome_Cientifico")["CPUEn"].sum().sort_values(ascending=True).index.tolist()
    matrix = (
        native.pivot_table(index="Nome_Cientifico", columns="Rotulo", values="CPUEn_pct", aggfunc="sum", fill_value=0)
        .reindex(index=species, columns=labels)
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(16, 10))
    im = ax.imshow(matrix.values, aspect="auto", cmap="Blues", vmin=0)
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=9)
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
    ax.set_xlabel("Ano hidrologico")
    ax.set_ylabel("Especies nativas com maior CPUEn")
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("CPUEn (%)")
    _style_axes(ax, grid_axis="both")
    _save(fig, filename)


def _native_species_percent(base: pd.DataFrame, recent_only: bool) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    q["Origem_Modelo"] = q["Nativa_Nao_Nativa"].map(_class_origin)
    q = q.loc[q["Origem_Modelo"].eq("Nativa")].copy()
    if recent_only:
        q = q.loc[q["ano_hidrologico"].isin(["AH2324", "AH2425", "AH2526"])].copy()

    agg = (
        q.groupby(["Trecho", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )

    rows = []
    for metric in ["CPUEn", "CPUEb"]:
        for trecho, group in agg.groupby("Trecho"):
            total = group[metric].sum()
            tmp = group[["Trecho", "Nome_Cientifico", metric]].copy()
            tmp["Metrica"] = metric
            tmp["Valor_Absoluto"] = tmp[metric]
            tmp["Percentual"] = np.where(total > 0, tmp[metric] / total * 100, 0)
            tmp["Recorte"] = "AH2324-AH2526" if recent_only else "Periodo completo"
            rows.append(tmp[["Recorte", "Trecho", "Metrica", "Nome_Cientifico", "Valor_Absoluto", "Percentual"]])
    return pd.concat(rows, ignore_index=True).sort_values(["Recorte", "Trecho", "Metrica", "Percentual"], ascending=[True, True, True, False])


def _top_with_others(group: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    ordered = group.sort_values("Percentual", ascending=False).copy()
    top = ordered.head(top_n).copy()
    rest = ordered.iloc[top_n:]
    if not rest.empty and rest["Percentual"].sum() > 0:
        top = pd.concat(
            [
                top,
                pd.DataFrame(
                    [
                        {
                            "Recorte": ordered["Recorte"].iloc[0],
                            "Trecho": ordered["Trecho"].iloc[0],
                            "Metrica": ordered["Metrica"].iloc[0],
                            "Nome_Cientifico": "Outras espécies nativas",
                            "Valor_Absoluto": rest["Valor_Absoluto"].sum(),
                            "Percentual": rest["Percentual"].sum(),
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return top.sort_values("Percentual", ascending=True).reset_index(drop=True)


def plot_native_lollipop_panels(native: pd.DataFrame, filename: str, recorte_label: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL)
    specs = [
        ("Montante", "CPUEn"),
        ("Montante", "CPUEb"),
        ("Jusante", "CPUEn"),
        ("Jusante", "CPUEb"),
    ]
    colors = {"CPUEn": PRIMARY, "CPUEb": SECONDARY}
    for ax, (trecho, metric) in zip(axes.ravel(), specs, strict=False):
        group = native.loc[native["Trecho"].eq(trecho) & native["Metrica"].eq(metric)].copy()
        display = _top_with_others(group, top_n=8)
        y = np.arange(len(display))
        ax.hlines(y, 0, display["Percentual"], color="#D9D9D9", linewidth=2.4)
        ax.scatter(display["Percentual"], y, s=140, color=colors[metric], edgecolor=EDGE, linewidth=1.1, zorder=3)
        for yi, value in zip(y, display["Percentual"], strict=False):
            ax.text(value + 0.8, yi, f"{value:.1f}%", va="center", ha="left", fontsize=12)
        ax.set_yticks(y)
        ax.set_yticklabels(display["Nome_Cientifico"], fontstyle="italic", fontsize=12)
        ax.set_xlabel(f"{metric} (%)")
        ax.set_title(f"{trecho} | {metric}", loc="center", fontweight="bold", pad=10)
        ax.set_xlim(0, max(5, min(100, display["Percentual"].max() * 1.25)))
        _style_axes(ax, grid_axis="x")
    fig.suptitle(recorte_label, fontsize=FONT_BASE + 1, fontweight="bold", y=1.01)
    _save(fig, filename)


def _taxonomy_counts(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    species = base[["Nome_Cientifico"]].drop_duplicates().copy()
    char_file = RESULTADOS_DIR / f"caracterizacao_especies_porto_estrela_{DATE_TAG}.xlsx"
    char = pd.read_excel(char_file, sheet_name="Caracterizacao_Especies")
    cols = ["Nome_Cientifico", "Ordem", "Familia"]
    merged = species.merge(char[cols], on="Nome_Cientifico", how="left")
    order_counts = merged.groupby("Ordem", dropna=False).size().reset_index(name="Especies")
    family_counts = merged.groupby("Familia", dropna=False).size().reset_index(name="Especies")
    order_counts["Percentual"] = order_counts["Especies"] / order_counts["Especies"].sum() * 100
    family_counts["Percentual"] = family_counts["Especies"] / family_counts["Especies"].sum() * 100
    return order_counts.sort_values("Especies", ascending=False), family_counts.sort_values("Especies", ascending=False)


def plot_donuts(order_counts: pd.DataFrame, family_counts: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(18, 8.8))
    for ax, data, label in [(axes[0], order_counts, "Ordem"), (axes[1], family_counts.head(10), "Familia")]:
        values = data["Especies"].to_numpy()
        labels = data[label].fillna("Nao informado").astype(str).tolist()
        colors = [ALT_PALETTE[i % len(ALT_PALETTE)] for i in range(len(values))]
        wedges, _ = ax.pie(values, colors=colors, startangle=90, wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.2})
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.94, 0.5), frameon=False, fontsize=12)
        ax.text(0, 0, label, ha="center", va="center", fontsize=FONT_PANEL, color=PRIMARY, fontweight="bold")
    _save(fig, "modelo_07_fig11_rosca_ordem_familia.png")


def _alpha_indices(values: pd.Series) -> dict[str, float]:
    x = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(dtype=float)
    x = x[x > 0]
    richness = int(len(x))
    total = float(x.sum())
    if richness == 0 or total <= 0:
        return {"Riqueza": 0, "Shannon": 0.0, "Pielou": 0.0}
    p = x / total
    shannon = float(-np.sum(p * np.log(p)))
    pielou = float(shannon / np.log(richness)) if richness > 1 else 0.0
    return {"Riqueza": richness, "Shannon": shannon, "Pielou": pielou}


def _diversity_by_ah_trecho(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    agg = (
        q.groupby(["ano_hidrologico", "Trecho", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"))
    )
    rows = []
    for (ah, trecho), group in agg.groupby(["ano_hidrologico", "Trecho"]):
        indices = _alpha_indices(group["CPUEn"])
        rows.append(
            {
                "ano_hidrologico": ah,
                "Rotulo": _ah_label(ah),
                "Ordem_AH": _ah_sort_value(ah),
                "Trecho": trecho,
                **indices,
            }
        )
    return pd.DataFrame(rows).sort_values(["Ordem_AH", "Trecho"])


def plot_diversity(diversity: pd.DataFrame) -> None:
    labels = diversity.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_PANEL, sharex=True)
    specs = [("Shannon", "Shannon (H')"), ("Pielou", "Pielou (J')")]
    colors = {"Montante": PRIMARY, "Jusante": SECONDARY}
    for ax, (metric, ylabel) in zip(axes, specs, strict=False):
        for trecho in ["Montante", "Jusante"]:
            g = diversity.loc[diversity["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            ax.plot(x[: len(g)], g[metric], marker="o", linewidth=3.0, markersize=7, color=colors[trecho], label=trecho)
        ax.set_ylabel(ylabel)
        _style_axes(ax)
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=45, ha="right")
    axes[-1].set_xlabel("Ano hidrológico")
    _save(fig, "modelo_08_fig30_diversidade_equitabilidade_ano_hidrologico.png")


def _reproduction_females(base: pd.DataFrame) -> pd.DataFrame:
    df = base.copy()
    df["Migracao_Modelo"] = df["Migradora_Nao_Migradora"].map(_class_migration)
    df["Origem_Modelo"] = df["Nativa_Nao_Nativa"].map(_class_origin)
    df = df.loc[
        df["Sexo_Padronizado"].eq("Femea")
        & df["Migracao_Modelo"].eq("Migradora")
        & df["EMG_Codigo"].isin(["F1", "F2", "F3", "F4"])
    ].copy()
    agg = (
        df.groupby(["ano_hidrologico", "Trecho", "Origem_Modelo", "EMG_Codigo", "EMG_Estadio"], as_index=False)
        .agg(Abundancia=("Numero_de_Individuos", "sum"))
    )
    agg["Rotulo"] = agg["ano_hidrologico"].map(_ah_label)
    agg["Ordem_AH"] = agg["ano_hidrologico"].map(_ah_sort_value)
    return agg.sort_values(["Origem_Modelo", "Ordem_AH", "EMG_Codigo"])


def plot_reproduction(repro: pd.DataFrame, ah_labels: list[str]) -> None:
    labels = ah_labels
    x = np.arange(len(labels))
    stage_order = ["F1", "F2", "F3", "F4"]
    stage_labels = {
        "F1": "F1 - Repouso",
        "F2": "F2 - Maturação inicial",
        "F3": "F3 - Maduro",
        "F4": "F4 - Desovado",
    }
    colors = ["#DBE5F1", "#9DC3E6", "#5B9BD5", "#002060"]
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True)
    specs = [
        ("Nativa", "Montante"),
        ("Nativa", "Jusante"),
        ("Nao nativa", "Montante"),
        ("Nao nativa", "Jusante"),
    ]
    for ax, (origem, trecho) in zip(axes.ravel(), specs, strict=False):
        pivot = (
            repro.loc[repro["Origem_Modelo"].eq(origem) & repro["Trecho"].eq(trecho)]
            .pivot_table(index="Rotulo", columns="EMG_Codigo", values="Abundancia", aggfunc="sum", fill_value=0)
            .reindex(labels)
            .reindex(columns=stage_order, fill_value=0)
            .fillna(0)
        )
        bottom = np.zeros(len(pivot), dtype=float)
        for stage, color in zip(stage_order, colors, strict=False):
            values = pivot[stage].to_numpy(dtype=float)
            ax.bar(x, values, bottom=bottom, width=0.82, color=color, edgecolor=EDGE, linewidth=0.6, label=stage_labels[stage])
            bottom += values
        origem_label = "nativas" if origem == "Nativa" else "não nativas"
        ax.set_title(f"Fêmeas migradoras {origem_label} | {trecho}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel("Abundância")
        _style_axes(ax)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.03), ncol=4, frameon=False)
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    _save(fig, "modelo_09_fig32_33_reproducao_femeas_migradoras_emg.png")


def main() -> None:
    if not BASE_FILE.exists():
        raise FileNotFoundError(BASE_FILE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _clean_previous_outputs()
    _configure_matplotlib()

    base = pd.read_excel(BASE_FILE, sheet_name="Base_Linhas")
    base["Numero_de_Individuos"] = pd.to_numeric(base["Numero_de_Individuos"], errors="coerce").fillna(0)
    for col in ["CPUEn_linha", "CPUEb_linha"]:
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    curve = _collector_curve(base)
    richness = _richness_by_ah(base)
    cpue_ah, cpue_campaign = _cpue_by_ah_trecho(base)
    regressions = plot_cpue_ah_panel(cpue_ah)
    percent = _cpue_percent_groups(base)
    native_all = _native_species_percent(base, recent_only=False)
    native_recent = _native_species_percent(base, recent_only=True)
    order_counts, family_counts = _taxonomy_counts(base)
    diversity = _diversity_by_ah_trecho(base)
    reproduction = _reproduction_females(base)
    ah_labels = (
        base[["ano_hidrologico"]]
        .drop_duplicates()
        .assign(Ordem_AH=lambda df: df["ano_hidrologico"].map(_ah_sort_value), Rotulo=lambda df: df["ano_hidrologico"].map(_ah_label))
        .sort_values("Ordem_AH")["Rotulo"]
        .tolist()
    )

    plot_collector(curve)
    plot_richness(richness)
    plot_percent_groups(percent)
    plot_native_lollipop_panels(
        native_all,
        "modelo_06a_fig15_lollipop_especies_nativas_periodo_completo.png",
        "Espécies nativas - período completo",
    )
    plot_native_lollipop_panels(
        native_recent,
        "modelo_06b_fig16_lollipop_especies_nativas_recorte_atual.png",
        "Espécies nativas - recorte atual (AH2324, AH2425 e AH2526)",
    )
    plot_donuts(order_counts, family_counts)
    plot_diversity(diversity)
    plot_reproduction(reproduction, ah_labels)

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        _write_sheet(writer, "curva_coletor", curve)
        _write_sheet(writer, "riqueza_ano_hidrologico", richness)
        _write_sheet(writer, "cpue_ano_trecho", cpue_ah)
        _write_sheet(writer, "cpue_campanha_trecho", cpue_campaign)
        _write_sheet(writer, "regressoes_modelo_fig13", regressions)
        _write_sheet(writer, "cpue_percentual_grupos", percent)
        _write_sheet(writer, "nativas_periodo_completo", native_all)
        _write_sheet(writer, "nativas_recorte_atual", native_recent)
        _write_sheet(writer, "ordens", order_counts)
        _write_sheet(writer, "familias", family_counts)
        _write_sheet(writer, "diversidade", diversity)
        _write_sheet(writer, "repro_femeas_migradoras", reproduction)

    print(f"Modelos gerados em: {OUT_DIR}")
    print(f"Planilha de apoio: {OUT_XLSX}")


if __name__ == "__main__":
    main()
