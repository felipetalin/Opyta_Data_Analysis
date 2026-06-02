from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DATE_TAG = "20260602"
PROJECT_LABEL = "Porto Estrela"
RESULTADOS_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados"
)
BASE_FILE = RESULTADOS_DIR / f"base_analitica_ictiofauna_porto_estrela_{DATE_TAG}.xlsx"
CHAR_FILE = RESULTADOS_DIR / f"caracterizacao_especies_porto_estrela_{DATE_TAG}.xlsx"
OUTPUT_DIR = RESULTADOS_DIR / f"resultados_ictiofauna_porto_estrela_{DATE_TAG}"

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

POINT_ORDER_TABLE = ["P9", "P8", "P7", "P6", "P3", "P1", "P2", "P5", "P4"]
RECENT_AH = ["AH2324", "AH2425", "AH2526"]


def _clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _norm_ascii(value: object) -> str:
    txt = _clean_text(value).lower()
    replacements = {
        "ã": "a",
        "á": "a",
        "â": "a",
        "à": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
        "?": "a",
        "Ã£": "a",
        "Ã©": "e",
        "Ã§": "c",
    }
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt


def _class_migration(value: object) -> str:
    txt = _norm_ascii(value)
    if "migradora" not in txt and "migrador" not in txt:
        return _clean_text(value).replace("N?o", "Não").replace("Nao", "Não")
    if txt.startswith("nao") or "nao migr" in txt:
        return "Não migradora"
    return "Migradora"


def _class_origin(value: object) -> str:
    txt = _norm_ascii(value)
    if "nativa" not in txt:
        return _clean_text(value).replace("N?o", "Não").replace("Nao", "Não")
    if txt.startswith("nao") or "nao nativa" in txt:
        return "Não nativa"
    return "Nativa"


def _class_yes_no(value: object) -> str:
    txt = _norm_ascii(value)
    if txt in {"sim", "s", "true", "1"}:
        return "Sim"
    return "Não"


def _status_label(value: object) -> str:
    txt = _clean_text(value)
    if not txt or _norm_ascii(txt) in {"na", "n.a.", "nan", "none", "nao"}:
        return "N.A."
    return txt.replace("N?o", "Não").replace("Nao", "Não")


def _ah_sort_value(value: object) -> int:
    match = re.search(r"AH(\d{4})", _clean_text(value))
    return int(match.group(1)) if match else 999999


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


def _save_fig(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _write_xlsx(path: Path, sheets: dict[str, pd.DataFrame]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
            ws = writer.book[name[:31]]
            ws.freeze_panes = "A2"
            for col_cells in ws.columns:
                letter = col_cells[0].column_letter
                width = min(max(len(str(cell.value or "")) for cell in col_cells) + 2, 48)
                ws.column_dimensions[letter].width = width
    return path


def _block_dir(code: str, label: str) -> Path:
    # Os blocos continuam separados no codigo, mas os arquivos ficam juntos
    # para facilitar revisao visual e ajustes pontuais.
    return OUTPUT_DIR


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    valid = pd.DataFrame({"v": pd.to_numeric(values, errors="coerce"), "w": weights}).dropna()
    valid = valid.loc[valid["w"].gt(0)]
    if valid.empty:
        return np.nan
    return float(np.average(valid["v"], weights=valid["w"]))


def _regression(values: pd.Series) -> tuple[float, float, float]:
    y = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    x = np.arange(1, len(y) + 1, dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return np.nan, np.nan, np.nan
    slope, intercept = np.polyfit(x[ok], y[ok], 1)
    pred = slope * x[ok] + intercept
    ss_res = np.sum((y[ok] - pred) ** 2)
    ss_tot = np.sum((y[ok] - np.mean(y[ok])) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
    return float(intercept), float(slope), float(r2)


def _prepare_inputs() -> dict[str, pd.DataFrame]:
    if not BASE_FILE.exists():
        raise FileNotFoundError(BASE_FILE)
    if not CHAR_FILE.exists():
        raise FileNotFoundError(CHAR_FILE)

    base = pd.read_excel(BASE_FILE, sheet_name="Base_Linhas")
    char = pd.read_excel(CHAR_FILE, sheet_name="Caracterizacao_Especies")

    for col in ["Numero_de_Individuos", "Biomassa_g_linha", "CPUEn_linha", "CPUEb_linha", "CT_cm", "PC_g_individual"]:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce")
    base["Numero_de_Individuos"] = base["Numero_de_Individuos"].fillna(0)
    base["Captura_Real"] = base["Numero_de_Individuos"].gt(0)
    base["Migracao_Modelo"] = base["Migradora_Nao_Migradora"].map(_class_migration)
    base["Origem_Modelo"] = base["Nativa_Nao_Nativa"].map(_class_origin)
    base["Ameaca_Modelo"] = base["Ameacada_Extincao"].map(_class_yes_no)
    base["Rotulo_AH"] = base["ano_hidrologico"].map(_ah_label)
    base["Ordem_AH"] = base["ano_hidrologico"].map(_ah_sort_value)

    char["Migracao_Modelo"] = char["Migradora_Nao_Migradora"].map(_class_migration)
    char["Origem_Modelo"] = char["Nativa_Nao_Nativa"].map(_class_origin)
    char["Ameaca_Modelo"] = char["Ameacada_Extincao"].map(_class_yes_no)
    char["Interesse_Comercial_Modelo"] = char["Valor_Economico"].map(_class_yes_no)
    for col in ["Status_Ameaca_Estadual", "Status_Ameaca_Nacional", "Status_Ameaca_Global"]:
        char[col] = char[col].map(_status_label)

    return {"base": base, "char": char}


def _ah_labels(base: pd.DataFrame) -> list[str]:
    return (
        base[["ano_hidrologico", "Rotulo_AH", "Ordem_AH"]]
        .drop_duplicates()
        .sort_values("Ordem_AH")["Rotulo_AH"]
        .tolist()
    )


def _collector_curve(base: pd.DataFrame, n_perm: int = 300, seed: int = 42) -> pd.DataFrame:
    unit_cols = ["campanha_ordem", "Campanha", "Ponto", "Ordem_Global_Montante_Jusante"]
    pa = (
        base.loc[base["Captura_Real"], unit_cols + ["Nome_Cientifico"]]
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
            "Riqueza_Observada_DP": richness.std(axis=0),
            "Jackknife1_Medio": jackknife.mean(axis=0),
            "Jackknife1_DP": jackknife.std(axis=0),
            "Permutacoes": n_perm,
            "Unidade": "Campanha x Ponto",
        }
    )


def _plot_collector(curve: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    x = curve["Unidade_Amostral"].to_numpy()
    y_obs = curve["Riqueza_Observada_Media"].to_numpy()
    sd_obs = curve["Riqueza_Observada_DP"].to_numpy()
    y_jack = curve["Jackknife1_Medio"].to_numpy()
    sd_jack = curve["Jackknife1_DP"].to_numpy()
    ax.plot(x, y_obs, color=PRIMARY, linewidth=3.0, label="Riqueza observada (média das aleatorizações)")
    ax.fill_between(x, y_obs - sd_obs, y_obs + sd_obs, color=PRIMARY, alpha=0.12, linewidth=0, label="±1 DP observado")
    ax.plot(x, y_jack, color=SECONDARY, linewidth=2.8, linestyle="--", label="Jackknife 1 (estimativa média)")
    ax.fill_between(x, y_jack - sd_jack, y_jack + sd_jack, color=SECONDARY, alpha=0.16, linewidth=0, label="±1 DP Jackknife 1")
    ax.set_xlabel("Unidades amostrais acumuladas (campanha x ponto)")
    ax.set_ylabel("Riqueza acumulada")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=2, frameon=False)
    _style_axes(ax)
    _save_fig(fig, path)


def _richness_by_ah(base: pd.DataFrame) -> pd.DataFrame:
    pa = base.loc[base["Captura_Real"]].copy()
    rows = []
    for ah, group in pa.groupby("ano_hidrologico"):
        rows.append(
            {
                "Ano_Hidrologico": ah,
                "Rotulo": _ah_label(ah),
                "Ordem_AH": _ah_sort_value(ah),
                "Riqueza_Total": group["Nome_Cientifico"].nunique(),
                "Riqueza_Nativa": group.loc[group["Origem_Modelo"].eq("Nativa"), "Nome_Cientifico"].nunique(),
                "Riqueza_Nao_Nativa": group.loc[group["Origem_Modelo"].eq("Não nativa"), "Nome_Cientifico"].nunique(),
            }
        )
    return pd.DataFrame(rows).sort_values("Ordem_AH")


def _plot_richness(richness: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    x = np.arange(len(richness))
    ax.plot(x, richness["Riqueza_Total"], color=PRIMARY, marker="o", linewidth=3, markersize=7, label="Total")
    ax.plot(x, richness["Riqueza_Nativa"], color=SECONDARY, marker="o", linewidth=2.8, markersize=7, label="Nativas")
    ax.plot(x, richness["Riqueza_Nao_Nativa"], color="#808080", marker="o", linewidth=2.8, markersize=7, label="Não nativas")
    ax.set_xticks(x)
    ax.set_xticklabels(richness["Rotulo"], rotation=45, ha="right")
    ax.set_xlabel("Ano hidrológico")
    ax.set_ylabel("Riqueza de espécies")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=3, frameon=False)
    _style_axes(ax)
    _save_fig(fig, path)


def _cpue_ah_trecho(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    df = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
        .sort_values(["Ordem_AH", "Trecho"])
    )
    return df


def _plot_cpue_series(df: pd.DataFrame, trecho: str, metric: str, path: Path) -> dict[str, float | str]:
    group = df.loc[df["Trecho"].eq(trecho)].sort_values("Ordem_AH").copy()
    labels = group["Rotulo_AH"].tolist()
    y = group[metric].reset_index(drop=True)
    x = np.arange(len(group))
    intercept, slope, r2 = _regression(y)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    color = PRIMARY if trecho == "Montante" else SECONDARY
    ax.plot(x, y, marker="o", color=color, linewidth=3, markersize=7)
    if np.isfinite(slope):
        ax.plot(x, slope * np.arange(1, len(y) + 1) + intercept, color="#808080", linestyle="--", linewidth=2.2)
    ax.text(
        0.50,
        0.92,
        f"{trecho} | R²={r2:.2f}" if np.isfinite(r2) else trecho,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=FONT_PANEL,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 2},
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("Ano hidrológico")
    ax.set_ylabel("CPUEn (ind/100m²)" if metric == "CPUEn" else "CPUEb (g/100m²)")
    _style_axes(ax)
    _save_fig(fig, path)

    return {"Trecho": trecho, "Metrica": metric, "Intercepto_a": intercept, "Coeficiente_b": slope, "R2": r2}


def _plot_cpue_panel(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True)
    specs = [
        ("Montante", "CPUEn", "CPUEn (ind/100m²)"),
        ("Montante", "CPUEb", "CPUEb (g/100m²)"),
        ("Jusante", "CPUEn", "CPUEn (ind/100m²)"),
        ("Jusante", "CPUEb", "CPUEb (g/100m²)"),
    ]
    labels = df.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo_AH"].tolist()
    x = np.arange(len(labels))
    rows = []
    for ax, (trecho, metric, ylabel) in zip(axes.ravel(), specs, strict=False):
        group = df.loc[df["Trecho"].eq(trecho)].sort_values("Ordem_AH")
        y = group[metric].reset_index(drop=True)
        intercept, slope, r2 = _regression(y)
        color = PRIMARY if trecho == "Montante" else SECONDARY
        ax.plot(x[: len(y)], y, marker="o", color=color, linewidth=3, markersize=7)
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
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 2},
        )
        ax.set_ylabel(ylabel)
        _style_axes(ax)
        rows.append({"Trecho": trecho, "Metrica": metric, "Intercepto_a": intercept, "Coeficiente_b": slope, "R2": r2})
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    _save_fig(fig, path)
    return pd.DataFrame(rows)


def _cpue_percent_groups(base: pd.DataFrame, subset: str = "all") -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    if subset == "migradoras":
        q = q.loc[q["Migracao_Modelo"].eq("Migradora")].copy()
        q["Grupo"] = q["Origem_Modelo"]
    else:
        q["Grupo"] = q["Migracao_Modelo"] + " | " + q["Origem_Modelo"]

    agg = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Grupo"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )
    for metric in ["CPUEn", "CPUEb"]:
        total = agg.groupby(["ano_hidrologico", "Trecho"])[metric].transform("sum")
        agg[f"{metric}_Percentual"] = np.where(total.gt(0), agg[metric] / total * 100, 0)
    return agg.sort_values(["Ordem_AH", "Trecho", "Grupo"])


def _plot_percent_panel(df: pd.DataFrame, path: Path, title: str | None = None) -> None:
    labels = df.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo_AH"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True, sharey=True)
    specs = [
        ("Montante", "CPUEn_Percentual", "CPUEn"),
        ("Montante", "CPUEb_Percentual", "CPUEb"),
        ("Jusante", "CPUEn_Percentual", "CPUEn"),
        ("Jusante", "CPUEb_Percentual", "CPUEb"),
    ]
    handles = []
    legend_labels = []
    for ax, (trecho, metric, metric_label) in zip(axes.ravel(), specs, strict=False):
        group = df.loc[df["Trecho"].eq(trecho)].copy()
        pivot = (
            group.pivot_table(index="Rotulo_AH", columns="Grupo", values=metric, aggfunc="sum", fill_value=0)
            .reindex(labels)
            .fillna(0)
        )
        groups = pivot.columns.tolist()
        stack = ax.stackplot(x, [pivot[col].values for col in groups], labels=groups, colors=PALETTE[: len(groups)], alpha=0.95)
        handles, legend_labels = stack, groups
        ax.set_ylim(0, 100)
        ax.set_title(f"{trecho} | {metric_label}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel(f"{metric_label} (%)")
        _style_axes(ax)
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    if title:
        fig.suptitle(title, fontsize=FONT_BASE + 1, fontweight="bold", y=1.04)
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=min(4, max(1, len(legend_labels))), frameon=False)
    _save_fig(fig, path)


def _native_species_percent(base: pd.DataFrame, recent_only: bool) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa") & base["Origem_Modelo"].eq("Nativa")].copy()
    if recent_only:
        q = q.loc[q["ano_hidrologico"].isin(RECENT_AH)].copy()
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
            tmp["Recorte"] = "AH2324-AH2526" if recent_only else "Período completo"
            rows.append(tmp[["Recorte", "Trecho", "Metrica", "Nome_Cientifico", "Valor_Absoluto", "Percentual"]])
    return pd.concat(rows, ignore_index=True).sort_values(["Trecho", "Metrica", "Percentual"], ascending=[True, True, False])


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


def _plot_lollipop_panel(native: pd.DataFrame, path: Path, title: str) -> None:
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
    fig.suptitle(title, fontsize=FONT_BASE + 1, fontweight="bold", y=1.01)
    _save_fig(fig, path)


def _threatened_cpue(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[
        base["Tipo_Amostragem_Base"].eq("Quantitativa")
        & base["Ameaca_Modelo"].eq("Sim")
    ].copy()
    return (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
        .sort_values(["Ordem_AH", "Trecho", "Nome_Cientifico"])
    )


def _plot_species_stack(df: pd.DataFrame, path: Path, title: str) -> None:
    labels = df.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo_AH"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True)
    specs = [
        ("Montante", "CPUEn"),
        ("Montante", "CPUEb"),
        ("Jusante", "CPUEn"),
        ("Jusante", "CPUEb"),
    ]
    handles = []
    legend_labels = []
    for ax, (trecho, metric) in zip(axes.ravel(), specs, strict=False):
        group = df.loc[df["Trecho"].eq(trecho)]
        pivot = (
            group.pivot_table(index="Rotulo_AH", columns="Nome_Cientifico", values=metric, aggfunc="sum", fill_value=0)
            .reindex(labels)
            .fillna(0)
        )
        species = pivot.columns.tolist()
        stack = ax.stackplot(x, [pivot[col].values for col in species], labels=species, colors=ALT_PALETTE[: len(species)], alpha=0.90)
        handles, legend_labels = stack, species
        ax.set_title(f"{trecho} | {metric}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel("CPUEn (ind/100m²)" if metric == "CPUEn" else "CPUEb (g/100m²)")
        _style_axes(ax)
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    fig.suptitle(title, fontsize=FONT_BASE + 1, fontweight="bold", y=1.04)
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=min(4, max(1, len(legend_labels))), frameon=False)
    _save_fig(fig, path)


def _taxonomy_counts(char: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    species = char[["Nome_Cientifico", "Ordem", "Familia"]].drop_duplicates()
    order_counts = species.groupby("Ordem", dropna=False).size().reset_index(name="Especies")
    family_counts = species.groupby("Familia", dropna=False).size().reset_index(name="Especies")
    order_counts["Percentual"] = order_counts["Especies"] / order_counts["Especies"].sum() * 100
    family_counts["Percentual"] = family_counts["Especies"] / family_counts["Especies"].sum() * 100
    return order_counts.sort_values("Especies", ascending=False), family_counts.sort_values("Especies", ascending=False)


def _plot_donut(data: pd.DataFrame, category_col: str, path: Path, center_label: str) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    values = data["Especies"].to_numpy()
    labels = data[category_col].fillna("Não informado").astype(str).tolist()
    colors = [ALT_PALETTE[i % len(ALT_PALETTE)] for i in range(len(values))]
    wedges, _ = ax.pie(values, colors=colors, startangle=90, wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.2})
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.80, 0.5), frameon=False, fontsize=13)
    ax.text(0, 0, center_label, ha="center", va="center", fontsize=FONT_PANEL, color=PRIMARY, fontweight="bold")
    _save_fig(fig, path)


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


def _diversity(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    agg = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"))
    )
    rows = []
    for keys, group in agg.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho"]):
        ah, label, order, trecho = keys
        rows.append({"Ano_Hidrologico": ah, "Rotulo": label, "Ordem_AH": order, "Trecho": trecho, **_alpha_indices(group["CPUEn"])})
    return pd.DataFrame(rows).sort_values(["Ordem_AH", "Trecho"])


def _plot_diversity(diversity: pd.DataFrame, path: Path) -> None:
    labels = diversity.drop_duplicates("Ano_Hidrologico").sort_values("Ordem_AH")["Rotulo"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_PANEL, sharex=True)
    colors = {"Montante": PRIMARY, "Jusante": SECONDARY}
    for ax, metric, ylabel in zip(axes, ["Shannon", "Pielou"], ["Shannon (H')", "Pielou (J')"], strict=False):
        for trecho in ["Montante", "Jusante"]:
            group = diversity.loc[diversity["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            ax.plot(x[: len(group)], group[metric], marker="o", linewidth=3, markersize=7, color=colors[trecho], label=trecho)
        ax.set_ylabel(ylabel)
        _style_axes(ax)
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=45, ha="right")
    axes[-1].set_xlabel("Ano hidrológico")
    _save_fig(fig, path)


def _reproduction_females(base: pd.DataFrame, origem: str | None = None) -> pd.DataFrame:
    df = base.loc[
        base["Sexo_Padronizado"].eq("Femea")
        & base["Migracao_Modelo"].eq("Migradora")
        & base["EMG_Codigo"].isin(["F1", "F2", "F3", "F4"])
    ].copy()
    if origem:
        df = df.loc[df["Origem_Modelo"].eq(origem)].copy()
    agg = (
        df.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Origem_Modelo", "EMG_Codigo", "EMG_Estadio"], as_index=False)
        .agg(Abundancia=("Numero_de_Individuos", "sum"))
    )
    return agg.sort_values(["Origem_Modelo", "Trecho", "Ordem_AH", "EMG_Codigo"])


def _plot_reproduction(repro: pd.DataFrame, path: Path, origem: str, ah_labels: list[str]) -> None:
    x = np.arange(len(ah_labels))
    stage_order = ["F1", "F2", "F3", "F4"]
    stage_labels = {
        "F1": "F1 - Repouso",
        "F2": "F2 - Maturação inicial",
        "F3": "F3 - Maduro",
        "F4": "F4 - Desovado",
    }
    colors = ["#DBE5F1", "#9DC3E6", "#5B9BD5", "#002060"]
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE, sharex=True)
    for ax, trecho in zip(axes, ["Montante", "Jusante"], strict=False):
        pivot = (
            repro.loc[repro["Trecho"].eq(trecho)]
            .pivot_table(index="Rotulo_AH", columns="EMG_Codigo", values="Abundancia", aggfunc="sum", fill_value=0)
            .reindex(ah_labels)
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
        ax.set_xticks(x)
        ax.set_xticklabels(ah_labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
        _style_axes(ax)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=4, frameon=False)
    _save_fig(fig, path)


def bloco_tabela_05(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    char = ctx["char"].copy()
    folder = _block_dir("05", "tabela_composicao_especies")
    out = char.sort_values(["Ordem", "Familia", "Nome_Cientifico"])[
        [
            "Ordem",
            "Familia",
            "Nome_Cientifico",
            "Autor_e_Ano",
            "Nome_Popular",
            "Origem_Modelo",
            "Status_Ameaca_Estadual",
            "Status_Ameaca_Nacional",
            "Status_Ameaca_Global",
        ]
    ].rename(
        columns={
            "Familia": "Família",
            "Nome_Cientifico": "Espécie",
            "Autor_e_Ano": "Autor",
            "Nome_Popular": "Nome popular",
            "Origem_Modelo": "Nativa/não nativa",
            "Status_Ameaca_Estadual": "Ameaça estadual",
            "Status_Ameaca_Nacional": "Ameaça federal",
            "Status_Ameaca_Global": "Ameaça mundial",
        }
    )
    path = _write_xlsx(folder / "tabela_05_composicao_especies.xlsx", {"Tabela 5": out})
    return [path]


def bloco_tabela_06(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"]
    char = ctx["char"].copy()
    folder = _block_dir("06", "tabela_caracteristicas_biologicas")
    occ = (
        base.loc[base["Captura_Real"]]
        .groupby(["Nome_Cientifico", "Trecho"], as_index=False)
        .size()
        .assign(Presenca="Presença")
        .pivot_table(index="Nome_Cientifico", columns="Trecho", values="Presenca", aggfunc="first", fill_value="Ausência")
        .reset_index()
    )
    for col in ["Jusante", "Montante"]:
        if col not in occ.columns:
            occ[col] = "Ausência"
    table = char.merge(occ[["Nome_Cientifico", "Jusante", "Montante"]], on="Nome_Cientifico", how="left")
    table[["Jusante", "Montante"]] = table[["Jusante", "Montante"]].fillna("Ausência")
    out = table.sort_values("Nome_Cientifico")[
        [
            "Nome_Cientifico",
            "Migracao_Modelo",
            "Origem_Modelo",
            "Ameaca_Modelo",
            "Interesse_Comercial_Modelo",
            "Jusante",
            "Montante",
        ]
    ].rename(
        columns={
            "Nome_Cientifico": "Espécie",
            "Migracao_Modelo": "Migração",
            "Origem_Modelo": "Distribuição",
            "Ameaca_Modelo": "Ameaçada de extinção",
            "Interesse_Comercial_Modelo": "Interesse Comercial",
        }
    )
    path = _write_xlsx(folder / "tabela_06_caracteristicas_biologicas.xlsx", {"Tabela 6": out})
    return [path]


def bloco_tabela_07(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"]
    folder = _block_dir("07", "tabela_ocorrencia")
    pa = base.loc[base["Captura_Real"], ["Nome_Cientifico", "Origem_Modelo", "Ponto"]].drop_duplicates()
    pivot = (
        pa.assign(Presenca="X")
        .pivot_table(index=["Nome_Cientifico", "Origem_Modelo"], columns="Ponto", values="Presenca", aggfunc="first", fill_value="-")
        .reset_index()
    )
    for point in POINT_ORDER_TABLE:
        if point not in pivot.columns:
            pivot[point] = "-"
    pivot["FA"] = pivot[POINT_ORDER_TABLE].eq("X").sum(axis=1)
    pivot["FR (%)"] = pivot["FA"] / len(POINT_ORDER_TABLE) * 100
    out = pivot[["Nome_Cientifico", "Origem_Modelo", *POINT_ORDER_TABLE, "FA", "FR (%)"]].rename(
        columns={"Nome_Cientifico": "Espécie", "Origem_Modelo": "Distribuição"}
    ).sort_values("Espécie")
    path = _write_xlsx(folder / "tabela_07_ocorrencia_fa_fr.xlsx", {"Tabela 7": out})
    return [path]


def bloco_tabela_08(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"].loc[ctx["base"]["Captura_Real"]].copy()
    folder = _block_dir("08", "tabela_biometria_biomassa")
    rows = []
    for species, group in base.groupby("Nome_Cientifico"):
        rows.append(
            {
                "Espécie": species,
                "N": group["Numero_de_Individuos"].sum(),
                "B": group["Biomassa_g_linha"].sum(),
                "CT_Min_cm": group["CT_cm"].min(),
                "CT_Med_cm": _weighted_mean(group["CT_cm"], group["Numero_de_Individuos"]),
                "CT_Max_cm": group["CT_cm"].max(),
                "PC_Min_g": group["PC_g_individual"].min(),
                "PC_Med_g": _weighted_mean(group["PC_g_individual"], group["Numero_de_Individuos"]),
                "PC_Max_g": group["PC_g_individual"].max(),
            }
        )
    out = pd.DataFrame(rows).sort_values("Espécie")
    path = _write_xlsx(folder / "tabela_08_biometria_biomassa.xlsx", {"Tabela 8": out})
    return [path]


def bloco_figura_10(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("10", "curva_coletor")
    curve = _collector_curve(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_10_curva_coletor_dados.xlsx", {"Curva": curve})
    png = folder / "figura_10_curva_coletor_observada_jackknife1.png"
    _plot_collector(curve, png)
    return [xlsx, png]


def bloco_figura_11(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("11", "rosca_ordem_familia")
    order_counts, family_counts = _taxonomy_counts(ctx["char"])
    xlsx = _write_xlsx(folder / "figura_11_ordem_familia_dados.xlsx", {"Ordem": order_counts, "Familia": family_counts})
    fig11a = folder / "figura_11a_percentual_ordem.png"
    fig11b = folder / "figura_11b_percentual_familia.png"
    _plot_donut(order_counts, "Ordem", fig11a, "Ordem")
    _plot_donut(family_counts.head(12), "Familia", fig11b, "Família")
    return [xlsx, fig11a, fig11b]


def bloco_figura_12(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("12", "riqueza_temporal")
    richness = _richness_by_ah(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_12_riqueza_temporal_dados.xlsx", {"Riqueza": richness})
    png = folder / "figura_12_riqueza_temporal_ano_hidrologico.png"
    _plot_richness(richness, png)
    return [xlsx, png]


def bloco_figura_13(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("13", "cpue_absoluta_regressao")
    df = _cpue_ah_trecho(ctx["base"])
    panel_png = folder / "figura_13_painel_cpue_regressao.png"
    regressions = _plot_cpue_panel(df, panel_png)
    files: list[Path] = [panel_png]
    specs = [
        ("13a", "Montante", "CPUEn"),
        ("13b", "Montante", "CPUEb"),
        ("13c", "Jusante", "CPUEn"),
        ("13d", "Jusante", "CPUEb"),
    ]
    reg_rows = regressions.to_dict("records")
    for code, trecho, metric in specs:
        path = folder / f"figura_{code}_{metric.lower()}_{trecho.lower()}_ano_hidrologico.png"
        reg_rows.append(_plot_cpue_series(df, trecho, metric, path))
        files.append(path)
    reg_df = pd.DataFrame(reg_rows).drop_duplicates(["Trecho", "Metrica"])
    xlsx = _write_xlsx(folder / "figura_13_cpue_regressao_dados.xlsx", {"CPUE": df, "Regressoes": reg_df})
    return [xlsx, *files]


def bloco_figura_14(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("14", "cpue_percentual_migracao_origem")
    df = _cpue_percent_groups(ctx["base"], subset="all")
    xlsx = _write_xlsx(folder / "figura_14_cpue_percentual_grupos_dados.xlsx", {"CPUE_percentual": df})
    png = folder / "figura_14_cpue_percentual_migracao_origem.png"
    _plot_percent_panel(df, png)
    return [xlsx, png]


def bloco_figura_15(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("15", "especies_nativas_periodo_completo")
    df = _native_species_percent(ctx["base"], recent_only=False)
    xlsx = _write_xlsx(folder / "figura_15_especies_nativas_periodo_completo_dados.xlsx", {"Nativas": df})
    png = folder / "figura_15_especies_nativas_periodo_completo.png"
    _plot_lollipop_panel(df, png, "Espécies nativas - período completo")
    return [xlsx, png]


def bloco_figura_16(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("16", "especies_nativas_recorte_atual")
    df = _native_species_percent(ctx["base"], recent_only=True)
    xlsx = _write_xlsx(folder / "figura_16_especies_nativas_recorte_atual_dados.xlsx", {"Nativas_recorte": df})
    png = folder / "figura_16_especies_nativas_recorte_atual.png"
    _plot_lollipop_panel(df, png, "Espécies nativas - recorte atual (AH2324, AH2425 e AH2526)")
    return [xlsx, png]


def bloco_secao_663(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("663", "cpue_migradoras_nativas_nao_nativas")
    df = _cpue_percent_groups(ctx["base"], subset="migradoras")
    xlsx = _write_xlsx(folder / "secao_663_cpue_migradoras_dados.xlsx", {"Migradoras": df})
    png = folder / "secao_663_cpue_migradoras_nativas_nao_nativas.png"
    _plot_percent_panel(df, png, title="Espécies migradoras nativas e não nativas")
    return [xlsx, png]


def bloco_secao_664(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("664", "cpue_ameacadas")
    df = _threatened_cpue(ctx["base"])
    xlsx = _write_xlsx(folder / "secao_664_cpue_ameacadas_dados.xlsx", {"Ameacadas": df})
    png = folder / "secao_664_cpue_especies_ameacadas.png"
    _plot_species_stack(df, png, "Espécies ameaçadas de extinção")
    return [xlsx, png]


def bloco_figura_30(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("30", "diversidade_equitabilidade")
    df = _diversity(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_30_diversidade_equitabilidade_dados.xlsx", {"Diversidade": df})
    png = folder / "figura_30_diversidade_equitabilidade.png"
    _plot_diversity(df, png)
    return [xlsx, png]


def bloco_figuras_32_33(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"]
    folder = _block_dir("32_33", "reproducao_femeas_migradoras")
    labels = _ah_labels(base)
    repro_all = _reproduction_females(base)
    repro_nat = _reproduction_females(base, origem="Nativa")
    repro_non = _reproduction_females(base, origem="Não nativa")
    xlsx = _write_xlsx(
        folder / "figuras_32_33_reproducao_femeas_migradoras_dados.xlsx",
        {
            "Todas": repro_all,
            "Nativas": repro_nat,
            "Nao_nativas": repro_non,
        },
    )
    fig32 = folder / "figura_32_emg_femeas_migradoras_nativas.png"
    fig33 = folder / "figura_33_emg_femeas_migradoras_nao_nativas.png"
    _plot_reproduction(repro_nat, fig32, "Nativa", labels)
    _plot_reproduction(repro_non, fig33, "Não nativa", labels)
    return [xlsx, fig32, fig33]


BLOCKS = {
    "05": ("Tabela 5 - composição de espécies", bloco_tabela_05),
    "06": ("Tabela 6 - características biológicas", bloco_tabela_06),
    "07": ("Tabela 7 - ocorrência FA/FR", bloco_tabela_07),
    "08": ("Tabela 8 - biometria e biomassa", bloco_tabela_08),
    "10": ("Figura 10 - curva do coletor", bloco_figura_10),
    "11": ("Figura 11 - roscas ordem/família", bloco_figura_11),
    "12": ("Figura 12 - riqueza temporal", bloco_figura_12),
    "13": ("Figura 13 - CPUE absoluta e regressão", bloco_figura_13),
    "14": ("Figura 14 - CPUE percentual por migração/origem", bloco_figura_14),
    "15": ("Figura 15 - espécies nativas período completo", bloco_figura_15),
    "16": ("Figura 16 - espécies nativas recorte atual", bloco_figura_16),
    "663": ("Seção 6.6.3 - migradoras nativas/não nativas", bloco_secao_663),
    "664": ("Seção 6.6.4 - ameaçadas", bloco_secao_664),
    "30": ("Figura 30 - diversidade e equitabilidade", bloco_figura_30),
    "32_33": ("Figuras 32 e 33 - reprodução", bloco_figuras_32_33),
}


def _parse_only(values: str | None) -> list[str]:
    if not values:
        return list(BLOCKS)

    raw_requested = [v.strip() for v in values.split(",") if v.strip()]
    requested = []
    for value in raw_requested:
        code = value
        if code not in BLOCKS and code.isdigit():
            code = code.zfill(2)
        requested.append(code)

    unknown = [raw for raw, code in zip(raw_requested, requested) if code not in BLOCKS]
    if unknown:
        raise ValueError(f"Blocos desconhecidos: {', '.join(unknown)}")
    return requested


def _write_manifest(results: list[dict[str, object]]) -> Path:
    rows = []
    for item in results:
        for path in item["files"]:
            rows.append({"Bloco": item["code"], "Descricao": item["description"], "Arquivo": str(path)})
    df = pd.DataFrame(rows)
    xlsx = _write_xlsx(OUTPUT_DIR / "manifesto_resultados_ictiofauna_porto_estrela.xlsx", {"Manifesto": df})

    lines = [
        "# Porto Estrela - resultados ictiofauna",
        "",
        f"Gerado a partir de `{BASE_FILE.name}` e `{CHAR_FILE.name}`.",
        "",
        "## Blocos gerados",
        "",
    ]
    for item in results:
        lines.append(f"- {item['code']} - {item['description']}: {len(item['files'])} arquivo(s).")
    md = OUTPUT_DIR / "manifesto_resultados_ictiofauna_porto_estrela.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    return xlsx


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera resultados modulares de ictiofauna para Porto Estrela.")
    parser.add_argument("--only", help="Lista de blocos separados por virgula. Ex.: --only 10,13,14")
    parser.add_argument("--list-blocks", action="store_true", help="Lista os blocos disponiveis e encerra.")
    args = parser.parse_args()

    if args.list_blocks:
        for code, (description, _) in BLOCKS.items():
            print(f"{code}: {description}")
        return

    _configure_matplotlib()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = _prepare_inputs()
    selected = _parse_only(args.only)

    results = []
    for code in selected:
        description, fn = BLOCKS[code]
        print(f"[{code}] {description}")
        files = fn(ctx)
        results.append({"code": code, "description": description, "files": files})
        print(f"  {len(files)} arquivo(s) gerado(s)")

    manifest = _write_manifest(results)
    print(f"\nSaida: {OUTPUT_DIR}")
    print(f"Manifesto: {manifest}")


if __name__ == "__main__":
    main()
