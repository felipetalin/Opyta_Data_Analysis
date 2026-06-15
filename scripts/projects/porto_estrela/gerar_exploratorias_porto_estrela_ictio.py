from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.spatial.distance import squareform


DATE_TAG = "20260603"
PROJECT_LABEL = "Porto Estrela"
RESULTADOS_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados"
)
BASE_FILE = RESULTADOS_DIR / "base_analitica_ictiofauna_porto_estrela_20260602.xlsx"
OUTPUT_DIR = (
    RESULTADOS_DIR
    / "resultados_ictiofauna_porto_estrela_20260602"
    / f"testes_analises_exploratorias_beta_inflexao_{DATE_TAG}"
)

PRIMARY = "#002060"
SECONDARY = "#5B9BD5"
HIGHLIGHT = "#1F4E79"
GRID = "#D9D9D9"
RECENT = "#F2C94C"
ORANGE = "#D4672A"
GREEN = "#6BA547"
PURPLE = "#7B4EA3"
RED = "#B75D69"
GREY = "#6C757D"

TRECHO_COLORS = {"Montante": PRIMARY, "Jusante": ORANGE}
TRECHO_BLUE_COLORS = {"Montante": PRIMARY, "Jusante": SECONDARY}
TRECHO_LINESTYLES = {"Montante": "-", "Jusante": "-"}
BETA_BLUE_COLORS = {
    "Beta_Sorensen": PRIMARY,
    "Turnover_BetaSim": "#5B9BD5",
    "Nestedness_BetaNes": "#9DC3E6",
}
BETA_LABELS = {
    "Beta_Sorensen": "β-Sørensen (β-sor)",
    "Turnover_BetaSim": "Turnover (β-sim)",
    "Nestedness_BetaNes": "Nestedness (β-nes)",
}
GROUP_COLORS = {
    "Migradora nativa": PRIMARY,
    "Migradora não nativa": SECONDARY,
    "Não migradora nativa": GREEN,
    "Não migradora não nativa": ORANGE,
    "Ameaçada": RED,
    "Não ameaçada": GREY,
}
GROUP_BLUE_COLORS = {
    "Migradora nativa": "#002060",
    "Migradora nÃ£o nativa": "#1F4E79",
    "NÃ£o migradora nativa": "#5B9BD5",
    "NÃ£o migradora nÃ£o nativa": "#9DC3E6",
    "AmeaÃ§ada": "#244062",
    "NÃ£o ameaÃ§ada": "#7EA6D8",
}

FIG_WIDE = (18, 10.2)
FIG_TALL = (18, 12.5)
FONT_BASE = 17
FONT_AXIS = 17
FONT_TICK = 12
FONT_LEGEND = 14
FONT_PANEL = 15


def _configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": FONT_BASE,
            "axes.labelsize": FONT_AXIS,
            "axes.titlesize": FONT_PANEL,
            "xtick.labelsize": FONT_TICK,
            "ytick.labelsize": FONT_TICK,
            "legend.fontsize": FONT_LEGEND,
            "axes.edgecolor": "black",
            "axes.linewidth": 1.2,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, alpha=0.35, linewidth=1.0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.1)


def _label_text(value: object) -> str:
    text = str(value)
    text = text.replace("N?o", "Não")
    text = text.replace("Nao", "Não")
    return text


def _group_label(migration: object, origin: object) -> str:
    mig = _label_text(migration).strip().lower()
    ori = _label_text(origin).strip().lower()
    mig_label = "Migradora" if mig == "migradora" else "Não migradora"
    ori_label = "nativa" if ori == "nativa" else "não nativa"
    return f"{mig_label} {ori_label}"


def _ah_order(base: pd.DataFrame) -> pd.DataFrame:
    return (
        base[["ano_hidrologico", "ano_hidrologico_rotulo", "campanha_ordem"]]
        .dropna(subset=["ano_hidrologico"])
        .groupby(["ano_hidrologico", "ano_hidrologico_rotulo"], as_index=False)["campanha_ordem"]
        .min()
        .sort_values("campanha_ordem")
        .assign(Ordem_AH=lambda d: np.arange(1, len(d) + 1))
    )


def _bray_curtis(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    denom = np.sum(x + y)
    if denom <= 0:
        return np.nan
    return float(np.sum(np.abs(x - y)) / denom)


def _hellinger_row(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    total = np.sum(x)
    if total <= 0:
        return np.zeros_like(x, dtype=float)
    return np.sqrt(x / total)


def _hellinger_distance01(x: np.ndarray, y: np.ndarray) -> float:
    hx = _hellinger_row(x)
    hy = _hellinger_row(y)
    return float(np.linalg.norm(hx - hy) / math.sqrt(2))


def _incidence_beta(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    px = np.asarray(x, dtype=float) > 0
    py = np.asarray(y, dtype=float) > 0
    a = int(np.logical_and(px, py).sum())
    b = int(np.logical_and(px, ~py).sum())
    c = int(np.logical_and(~px, py).sum())
    denom = a + b + c
    beta_jac = (b + c) / denom if denom else np.nan
    beta_sor = (b + c) / (2 * a + b + c) if (2 * a + b + c) else np.nan
    beta_sim = min(b, c) / (a + min(b, c)) if (a + min(b, c)) else np.nan
    beta_nes = beta_sor - beta_sim if pd.notna(beta_sor) and pd.notna(beta_sim) else np.nan
    return {
        "Compartilhadas": a,
        "Exclusivas_Montante": b,
        "Exclusivas_Jusante": c,
        "Beta_Jaccard": beta_jac,
        "Beta_Sorensen": beta_sor,
        "Turnover_BetaSim": beta_sim,
        "Nestedness_BetaNes": beta_nes,
        "Jusante_Subset_Montante": a / (a + c) if (a + c) else np.nan,
        "Montante_Subset_Jusante": a / (a + b) if (a + b) else np.nan,
    }


def _community_ah_trecho(base: pd.DataFrame, metric: str = "CPUEn_linha") -> pd.DataFrame:
    q = base.loc[
        base["Tipo_Amostragem_Base"].astype(str).str.contains("Quanti", case=False, na=False)
        & base["Nome_Cientifico"].notna()
    ].copy()
    comm = (
        q.pivot_table(
            index=["ano_hidrologico", "Trecho"],
            columns="Nome_Cientifico",
            values=metric,
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
        .astype(float)
    )
    return comm


def _presence_ah_trecho(base: pd.DataFrame) -> pd.DataFrame:
    pa = base.loc[
        (base["Numero_de_Individuos"].fillna(0) > 0) & base["Nome_Cientifico"].notna()
    ].copy()
    pa["Presenca"] = 1
    comm = (
        pa.pivot_table(
            index=["ano_hidrologico", "Trecho"],
            columns="Nome_Cientifico",
            values="Presenca",
            aggfunc="max",
            fill_value=0,
        )
        .sort_index()
        .astype(float)
    )
    return comm


def _between_trechos_beta(base: pd.DataFrame, ah: pd.DataFrame) -> pd.DataFrame:
    comm_cpuen = _community_ah_trecho(base, "CPUEn_linha")
    comm_pa = _presence_ah_trecho(base)
    species = sorted(set(comm_cpuen.columns).union(comm_pa.columns))
    comm_cpuen = comm_cpuen.reindex(columns=species, fill_value=0)
    comm_pa = comm_pa.reindex(columns=species, fill_value=0)

    rows = []
    for _, row in ah.iterrows():
        ah_code = row["ano_hidrologico"]
        if (ah_code, "Montante") not in comm_cpuen.index or (ah_code, "Jusante") not in comm_cpuen.index:
            continue
        m_q = comm_cpuen.loc[(ah_code, "Montante")].to_numpy()
        j_q = comm_cpuen.loc[(ah_code, "Jusante")].to_numpy()
        m_pa = comm_pa.loc[(ah_code, "Montante")].to_numpy() if (ah_code, "Montante") in comm_pa.index else np.zeros(len(species))
        j_pa = comm_pa.loc[(ah_code, "Jusante")].to_numpy() if (ah_code, "Jusante") in comm_pa.index else np.zeros(len(species))
        inc = _incidence_beta(m_pa, j_pa)
        rows.append(
            {
                "ano_hidrologico": ah_code,
                "Rotulo_AH": row["ano_hidrologico_rotulo"],
                "Ordem_AH": row["Ordem_AH"],
                "BrayCurtis_CPUEn": _bray_curtis(m_q, j_q),
                "Similaridade_BrayCurtis_CPUEn": 1 - _bray_curtis(m_q, j_q),
                "Hellinger_Beta_CPUEn": _hellinger_distance01(m_q, j_q),
                "Riqueza_Montante": int((m_pa > 0).sum()),
                "Riqueza_Jusante": int((j_pa > 0).sum()),
                **inc,
            }
        )
    return pd.DataFrame(rows)


def _consecutive_temporal_beta(base: pd.DataFrame, ah: pd.DataFrame) -> pd.DataFrame:
    comm_cpuen = _community_ah_trecho(base, "CPUEn_linha")
    comm_pa = _presence_ah_trecho(base)
    species = sorted(set(comm_cpuen.columns).union(comm_pa.columns))
    comm_cpuen = comm_cpuen.reindex(columns=species, fill_value=0)
    comm_pa = comm_pa.reindex(columns=species, fill_value=0)
    rows = []
    ordered = ah["ano_hidrologico"].tolist()
    labels = ah.set_index("ano_hidrologico")["ano_hidrologico_rotulo"].to_dict()
    orders = ah.set_index("ano_hidrologico")["Ordem_AH"].to_dict()

    for trecho in ["Montante", "Jusante"]:
        prev = None
        for code in ordered:
            idx = (code, trecho)
            if idx not in comm_cpuen.index:
                continue
            if prev is not None:
                prev_idx = (prev, trecho)
                x_q = comm_cpuen.loc[prev_idx].to_numpy()
                y_q = comm_cpuen.loc[idx].to_numpy()
                x_pa = comm_pa.loc[prev_idx].to_numpy() if prev_idx in comm_pa.index else np.zeros(len(species))
                y_pa = comm_pa.loc[idx].to_numpy() if idx in comm_pa.index else np.zeros(len(species))
                inc = _incidence_beta(x_pa, y_pa)
                rows.append(
                    {
                        "Trecho": trecho,
                        "Ano_Anterior": prev,
                        "Ano_Atual": code,
                        "Rotulo_AH": labels[code],
                        "Ordem_AH": orders[code],
                        "BrayCurtis_CPUEn_Consecutivo": _bray_curtis(x_q, y_q),
                        "Similaridade_BrayCurtis_CPUEn_Consecutivo": 1 - _bray_curtis(x_q, y_q),
                        "Hellinger_Beta_CPUEn_Consecutivo": _hellinger_distance01(x_q, y_q),
                        **inc,
                    }
                )
            prev = code
    return pd.DataFrame(rows)


def _lcbd_by_year(base: pd.DataFrame, ah: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    q = base.loc[
        base["Tipo_Amostragem_Base"].astype(str).str.contains("Quanti", case=False, na=False)
        & base["Nome_Cientifico"].notna()
    ].copy()
    comm = (
        q.pivot_table(
            index=["ano_hidrologico", "Ponto", "Trecho"],
            columns="Nome_Cientifico",
            values="CPUEn_linha",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
        .astype(float)
    )
    meta_ah = ah.set_index("ano_hidrologico")
    rows_points = []
    rows_year = []
    for ah_code, group in comm.groupby(level=0):
        mat = group.droplevel(0)
        if mat.shape[0] < 3:
            continue
        y = np.vstack([_hellinger_row(row) for row in mat.to_numpy()])
        center = y.mean(axis=0)
        ss = np.sum((y - center) ** 2, axis=1)
        ss_total = float(ss.sum())
        beta_total = ss_total / (mat.shape[0] - 1) if mat.shape[0] > 1 else np.nan
        for (ponto, trecho), ss_i in zip(mat.index, ss):
            rows_points.append(
                {
                    "ano_hidrologico": ah_code,
                    "Rotulo_AH": meta_ah.loc[ah_code, "ano_hidrologico_rotulo"],
                    "Ordem_AH": meta_ah.loc[ah_code, "Ordem_AH"],
                    "Ponto": ponto,
                    "Trecho": trecho,
                    "LCBD": ss_i / ss_total if ss_total > 0 else np.nan,
                    "SS_Composicao": ss_i,
                    "Beta_Total_Hellinger": beta_total,
                }
            )
        rows_year.append(
            {
                "ano_hidrologico": ah_code,
                "Rotulo_AH": meta_ah.loc[ah_code, "ano_hidrologico_rotulo"],
                "Ordem_AH": meta_ah.loc[ah_code, "Ordem_AH"],
                "Pontos": mat.shape[0],
                "Beta_Total_Hellinger": beta_total,
            }
        )
    points = pd.DataFrame(rows_points)
    trecho = (
        points.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho"], as_index=False)
        .agg(LCBD_Medio=("LCBD", "mean"), LCBD_Total=("LCBD", "sum"), Pontos=("Ponto", "nunique"))
        .sort_values(["Ordem_AH", "Trecho"])
    )
    years = pd.DataFrame(rows_year)
    return points.merge(years[["ano_hidrologico", "Beta_Total_Hellinger"]], on="ano_hidrologico", suffixes=("", "_Ano")), trecho.merge(
        years, on=["ano_hidrologico", "Rotulo_AH", "Ordem_AH"], how="left"
    )


def _bray_matrix(data: pd.DataFrame) -> np.ndarray:
    arr = data.to_numpy(dtype=float)
    n = arr.shape[0]
    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            value = _bray_curtis(arr[i], arr[j])
            dist[i, j] = dist[j, i] = 0.0 if pd.isna(value) else value
    return dist


def _pcoa_from_distance(distance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = distance.shape[0]
    d2 = distance ** 2
    j = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * j @ d2 @ j
    eigvals, eigvecs = np.linalg.eigh(b)
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]
    positive = eigvals > 1e-12
    eigvals_pos = eigvals[positive]
    coords = eigvecs[:, positive] * np.sqrt(eigvals_pos)
    if coords.shape[1] < 2:
        coords = np.pad(coords, ((0, 0), (0, 2 - coords.shape[1])), constant_values=0)
    explained = eigvals_pos / eigvals_pos.sum() if eigvals_pos.sum() > 0 else np.zeros_like(eigvals_pos)
    return coords[:, :2], explained[:2]


def _pcoa_ah_trecho(base: pd.DataFrame, ah: pd.DataFrame) -> pd.DataFrame:
    comm = _community_ah_trecho(base, "CPUEn_linha")
    comm = comm.loc[comm.sum(axis=1) > 0]
    labels = comm.index.to_frame(index=False)
    labels.columns = ["ano_hidrologico", "Trecho"]
    labels = labels.merge(ah, on="ano_hidrologico", how="left")
    dist = _bray_matrix(comm)
    coords, explained = _pcoa_from_distance(dist)
    out = labels.copy()
    out["PCoA1"] = coords[:, 0]
    out["PCoA2"] = coords[:, 1]
    out["PCoA1_var_pct"] = explained[0] * 100 if len(explained) > 0 else np.nan
    out["PCoA2_var_pct"] = explained[1] * 100 if len(explained) > 1 else np.nan
    return out.sort_values(["Ordem_AH", "Trecho"])


def _series_categories(base: pd.DataFrame, ah: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[
        base["Tipo_Amostragem_Base"].astype(str).str.contains("Quanti", case=False, na=False)
        & base["Nome_Cientifico"].notna()
    ].copy()
    q["Grupo_Migracao_Origem"] = [
        _group_label(m, o) for m, o in zip(q["Migradora_Nao_Migradora"], q["Nativa_Nao_Nativa"])
    ]
    q["Grupo_Ameaca"] = np.where(q["Ameacada_Extincao"].astype(str).str.lower().str.startswith("sim"), "Ameaçada", "Não ameaçada")
    ah_cols = ["ano_hidrologico", "ano_hidrologico_rotulo", "Ordem_AH"]
    rows = []
    for group_col, group_type in [("Grupo_Migracao_Origem", "Migração x origem"), ("Grupo_Ameaca", "Ameaça")]:
        agg = (
            q.groupby(["ano_hidrologico", "Trecho", group_col], as_index=False)
            .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"), Abundancia=("Numero_de_Individuos", "sum"))
            .rename(columns={group_col: "Categoria"})
        )
        agg["Tipo_Categoria"] = group_type
        rows.append(agg)
    out = pd.concat(rows, ignore_index=True)
    return out.merge(ah[ah_cols], on="ano_hidrologico", how="left").sort_values(
        ["Tipo_Categoria", "Trecho", "Categoria", "Ordem_AH"]
    )


def _cpue_total_trecho(base: pd.DataFrame, ah: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[
        base["Tipo_Amostragem_Base"].astype(str).str.contains("Quanti", case=False, na=False)
        & base["Nome_Cientifico"].notna()
    ].copy()
    out = (
        q.groupby(["ano_hidrologico", "Trecho"], as_index=False)
        .agg(
            CPUEn=("CPUEn_linha", "sum"),
            CPUEb=("CPUEb_linha", "sum"),
            Abundancia=("Numero_de_Individuos", "sum"),
            Biomassa_g=("Biomassa_g_linha", "sum"),
            Especies=("Nome_Cientifico", "nunique"),
        )
        .merge(ah[["ano_hidrologico", "ano_hidrologico_rotulo", "Ordem_AH"]], on="ano_hidrologico", how="left")
        .sort_values(["Trecho", "Ordem_AH"])
    )
    return out


def _fit_piecewise(x: np.ndarray, y: np.ndarray, min_size: int = 5) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x = x[ok]
    y = y[ok]
    n = len(y)
    if n < min_size * 2 + 1 or np.allclose(y, y[0]):
        return {
            "Breakpoint_X": np.nan,
            "SSE_Linear": np.nan,
            "SSE_Piecewise": np.nan,
            "BIC_Linear": np.nan,
            "BIC_Piecewise": np.nan,
            "Delta_BIC": np.nan,
            "Slope_Pre": np.nan,
            "Slope_Post": np.nan,
            "Intercept": np.nan,
            "Melhora_Forte": False,
        }

    x0 = x - x.min()
    linear_design = np.column_stack([np.ones(n), x0])
    coef_lin, *_ = np.linalg.lstsq(linear_design, y, rcond=None)
    resid_lin = y - linear_design @ coef_lin
    sse_lin = float(np.sum(resid_lin**2))
    bic_lin = n * np.log(max(sse_lin / n, 1e-12)) + 2 * np.log(n)

    best = None
    candidates = x0[min_size:-min_size]
    for bp in candidates:
        hinge = np.maximum(0, x0 - bp)
        design = np.column_stack([np.ones(n), x0, hinge])
        coef, *_ = np.linalg.lstsq(design, y, rcond=None)
        resid = y - design @ coef
        sse = float(np.sum(resid**2))
        bic = n * np.log(max(sse / n, 1e-12)) + 3 * np.log(n)
        item = (bic, sse, bp, coef)
        if best is None or item[0] < best[0]:
            best = item

    bic_piece, sse_piece, bp, coef = best
    slope_pre = float(coef[1])
    slope_post = float(coef[1] + coef[2])
    return {
        "Breakpoint_X": float(bp + x.min()),
        "SSE_Linear": sse_lin,
        "SSE_Piecewise": sse_piece,
        "BIC_Linear": bic_lin,
        "BIC_Piecewise": bic_piece,
        "Delta_BIC": bic_lin - bic_piece,
        "Slope_Pre": slope_pre,
        "Slope_Post": slope_post,
        "Intercept": float(coef[0]),
        "Hinge": float(coef[2]),
        "Melhora_Forte": bool((bic_lin - bic_piece) > 2),
    }


def _piecewise_predict(x: np.ndarray, fit: dict[str, float]) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if pd.isna(fit.get("Breakpoint_X", np.nan)):
        return np.full_like(x, np.nan, dtype=float)
    x0 = x - np.nanmin(x)
    bp = fit["Breakpoint_X"] - np.nanmin(x)
    return fit["Intercept"] + fit["Slope_Pre"] * x0 + fit["Hinge"] * np.maximum(0, x0 - bp)


def _fit_linear_segment(group: pd.DataFrame, metric: str, mask: pd.Series) -> tuple[np.ndarray, np.ndarray] | None:
    segment = group.loc[mask & group[metric].notna()].sort_values("Ordem_AH")
    if len(segment) < 2 or segment["Ordem_AH"].nunique() < 2:
        return None
    x = segment["Ordem_AH"].to_numpy(dtype=float)
    y = segment[metric].to_numpy(dtype=float)
    coef = np.polyfit(x, y, 1)
    return x, np.polyval(coef, x)


def _inflexions(series: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (tipo, trecho, categoria, metrica), group in series.melt(
        id_vars=[
            "Tipo_Categoria",
            "Trecho",
            "Categoria",
            "ano_hidrologico",
            "ano_hidrologico_rotulo",
            "Ordem_AH",
        ],
        value_vars=["CPUEn", "CPUEb"],
        var_name="Metrica",
        value_name="Valor",
    ).groupby(["Tipo_Categoria", "Trecho", "Categoria", "Metrica"]):
        group = group.sort_values("Ordem_AH")
        fit = _fit_piecewise(group["Ordem_AH"].to_numpy(), group["Valor"].to_numpy())
        bp_label = None
        if pd.notna(fit["Breakpoint_X"]):
            nearest = group.iloc[(group["Ordem_AH"] - fit["Breakpoint_X"]).abs().argsort().iloc[0]]
            bp_label = nearest["ano_hidrologico"]
        rows.append(
            {
                "Tipo_Categoria": tipo,
                "Trecho": trecho,
                "Categoria": categoria,
                "Metrica": metrica,
                "Breakpoint_Ordem_AH": fit["Breakpoint_X"],
                "Breakpoint_AH": bp_label,
                **{k: v for k, v in fit.items() if k != "Breakpoint_X"},
            }
        )
    return pd.DataFrame(rows).sort_values(["Metrica", "Tipo_Categoria", "Trecho", "Categoria"])


def _inflexions_total(cpue_total: pd.DataFrame) -> pd.DataFrame:
    rows = []
    melted = cpue_total.melt(
        id_vars=["Trecho", "ano_hidrologico", "ano_hidrologico_rotulo", "Ordem_AH"],
        value_vars=["CPUEn", "CPUEb"],
        var_name="Metrica",
        value_name="Valor",
    )
    for (trecho, metric), group in melted.groupby(["Trecho", "Metrica"]):
        group = group.sort_values("Ordem_AH")
        fit = _fit_piecewise(group["Ordem_AH"].to_numpy(), group["Valor"].to_numpy())
        bp_label = None
        if pd.notna(fit["Breakpoint_X"]):
            nearest = group.iloc[(group["Ordem_AH"] - fit["Breakpoint_X"]).abs().argsort().iloc[0]]
            bp_label = nearest["ano_hidrologico"]
        rows.append(
            {
                "Trecho": trecho,
                "Metrica": metric,
                "Breakpoint_Ordem_AH": fit["Breakpoint_X"],
                "Breakpoint_AH": bp_label,
                **{k: v for k, v in fit.items() if k != "Breakpoint_X"},
            }
        )
    return pd.DataFrame(rows).sort_values(["Trecho", "Metrica"])


def _plot_beta_between(beta: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=FIG_TALL, sharex=True)
    ax = axes[0]
    ax.plot(beta["Ordem_AH"], beta["BrayCurtis_CPUEn"], color=PRIMARY, linewidth=3, marker="o", label="Bray-Curtis CPUEn")
    ax.plot(beta["Ordem_AH"], beta["Hellinger_Beta_CPUEn"], color=SECONDARY, linewidth=3, marker="s", label="Beta Hellinger CPUEn")
    ax.set_ylabel("Dissimilaridade")
    ax.set_title("Beta quantitativa entre Montante e Jusante")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
    _style_axis(ax)

    ax = axes[1]
    ax.plot(beta["Ordem_AH"], beta["Beta_Sorensen"], color=ORANGE, linewidth=3, marker="o", label="β-Sørensen")
    ax.plot(beta["Ordem_AH"], beta["Turnover_BetaSim"], color=PURPLE, linewidth=3, marker="s", label="Turnover (β-sim)")
    ax.plot(beta["Ordem_AH"], beta["Nestedness_BetaNes"], color=GREEN, linewidth=3, marker="^", label="Nestedness (β-nes)")
    ax.set_ylabel("Dissimilaridade PA")
    ax.set_xlabel("Ano hidrológico")
    ax.set_title("Decomposição presença-ausência entre Montante e Jusante")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=3, frameon=False)
    _style_axis(ax)
    ticks = beta["Ordem_AH"].tolist()
    labels = beta["Rotulo_AH"].tolist()
    axes[1].set_xticks(ticks)
    axes[1].set_xticklabels(labels, rotation=45, ha="right")
    for axis in axes:
        axis.axvspan(max(ticks) - 2.5, max(ticks) + 0.5, color=RECENT, alpha=0.10, linewidth=0)
        axis.set_ylim(bottom=0)
    _save_fig(fig, path)


def _plot_temporal_consecutive(beta: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=FIG_TALL, sharex=True)
    metrics = [
        ("BrayCurtis_CPUEn_Consecutivo", "Bray-Curtis CPUEn entre anos consecutivos"),
        ("Beta_Sorensen", "β-Sørensen entre anos consecutivos"),
    ]
    for ax, (metric, title) in zip(axes, metrics):
        for trecho, group in beta.groupby("Trecho"):
            group = group.sort_values("Ordem_AH")
            ax.plot(
                group["Ordem_AH"],
                group[metric],
                marker="o",
                linewidth=3,
                color=TRECHO_COLORS[trecho],
                label=trecho,
            )
        ax.set_ylabel("Dissimilaridade")
        ax.set_title(title)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
        ax.set_ylim(bottom=0)
        _style_axis(ax)
    labels = beta.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    axes[-1].set_xticks(labels["Ordem_AH"])
    axes[-1].set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    axes[-1].set_xlabel("Ano hidrológico")
    _save_fig(fig, path)


def _plot_beta_pa_components_combined(beta: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(18, 8.6))
    metrics = ["Beta_Sorensen", "Turnover_BetaSim", "Nestedness_BetaNes"]
    markers = {"Montante": "o", "Jusante": "s"}
    linestyles = {"Montante": "-", "Jusante": "--"}
    for metric in metrics:
        for trecho, group in beta.groupby("Trecho"):
            group = group.sort_values("Ordem_AH")
            ax.plot(
                group["Ordem_AH"],
                group[metric],
                color=BETA_BLUE_COLORS[metric],
                marker=markers.get(trecho, "o"),
                linestyle=linestyles.get(trecho, "-"),
                linewidth=2.5,
                alpha=0.82,
                label=f"{BETA_LABELS[metric]} - {trecho}",
            )
    labels = beta.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=SECONDARY, alpha=0.12, linewidth=0)
    ax.set_ylabel("Dissimilaridade")
    ax.set_xlabel("Ano hidrológico")
    ax.set_xticks(labels["Ordem_AH"])
    ax.set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    ax.set_ylim(0, 1.02)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), ncol=3, frameon=False)
    _style_axis(ax)
    _save_fig(fig, path)


def _plot_beta_pa_components_by_area(beta: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(18, 11.2), sharex=True)
    metrics = ["Beta_Sorensen", "Turnover_BetaSim", "Nestedness_BetaNes"]
    for ax, trecho in zip(axes, ["Montante", "Jusante"]):
        subset = beta.loc[beta["Trecho"] == trecho].sort_values("Ordem_AH")
        for metric in metrics:
            ax.plot(
                subset["Ordem_AH"],
                subset[metric],
                color=BETA_BLUE_COLORS[metric],
                marker="o",
                linewidth=2.8,
                alpha=0.86,
                label=BETA_LABELS[metric],
            )
        ax.text(
            0.012,
            0.93,
            trecho,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=FONT_PANEL,
            color=PRIMARY,
            weight="bold",
        )
        ax.set_ylabel("Dissimilaridade")
        ax.set_ylim(0, 1.02)
        _style_axis(ax)
    labels = beta.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    for ax in axes:
        ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=SECONDARY, alpha=0.12, linewidth=0)
    axes[-1].set_xlabel("Ano hidrológico")
    axes[-1].set_xticks(labels["Ordem_AH"])
    axes[-1].set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    handles = [
        Line2D([0], [0], color=BETA_BLUE_COLORS[metric], marker="o", linewidth=2.8, label=BETA_LABELS[metric])
        for metric in metrics
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3, frameon=False)
    _save_fig(fig, path)


def _plot_lcbd(lcbd_trecho: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=FIG_TALL, sharex=True)
    years = lcbd_trecho.drop_duplicates(["ano_hidrologico", "Ordem_AH"]).sort_values("Ordem_AH")
    axes[0].plot(
        years["Ordem_AH"],
        years["Beta_Total_Hellinger"],
        color=PRIMARY,
        marker="o",
        linewidth=3,
        label="Beta total Hellinger",
    )
    axes[0].set_ylabel("Beta total")
    axes[0].set_title("Diversidade beta espacial taxonômica por ano hidrológico")
    _style_axis(axes[0])

    for trecho, group in lcbd_trecho.groupby("Trecho"):
        group = group.sort_values("Ordem_AH")
        axes[1].plot(
            group["Ordem_AH"],
            group["LCBD_Medio"],
            color=TRECHO_COLORS[trecho],
            marker="o",
            linewidth=3,
            label=trecho,
        )
    axes[1].set_ylabel("LCBD médio")
    axes[1].set_xlabel("Ano hidrológico")
    axes[1].set_title("Contribuição local média para beta diversidade por trecho")
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
    _style_axis(axes[1])
    axes[1].set_xticks(years["Ordem_AH"])
    axes[1].set_xticklabels(years["Rotulo_AH"], rotation=45, ha="right")
    for ax in axes:
        ax.axvspan(years["Ordem_AH"].max() - 2.5, years["Ordem_AH"].max() + 0.5, color=RECENT, alpha=0.10, linewidth=0)
    _save_fig(fig, path)


def _plot_pcoa(pcoa: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIG_WIDE)
    for ah_code, group in pcoa.groupby("ano_hidrologico"):
        if set(group["Trecho"]) == {"Montante", "Jusante"}:
            group = group.sort_values("Trecho")
            ax.plot(group["PCoA1"], group["PCoA2"], color="#BFC7D5", linewidth=1.0, alpha=0.45, zorder=1)
    for trecho, group in pcoa.groupby("Trecho"):
        ax.scatter(
            group["PCoA1"],
            group["PCoA2"],
            s=90,
            color=TRECHO_COLORS[trecho],
            edgecolor="black",
            linewidth=0.7,
            label=trecho,
            zorder=3,
        )
        for _, row in group.iterrows():
            if row["ano_hidrologico"] in {"AH0304", "AH1011", "AH1718", "AH2324", "AH2425", "AH2526"}:
                ax.annotate(row["ano_hidrologico"], (row["PCoA1"], row["PCoA2"]), xytext=(5, 4), textcoords="offset points", fontsize=10)
    var1 = pcoa["PCoA1_var_pct"].dropna().iloc[0] if pcoa["PCoA1_var_pct"].notna().any() else np.nan
    var2 = pcoa["PCoA2_var_pct"].dropna().iloc[0] if pcoa["PCoA2_var_pct"].notna().any() else np.nan
    ax.axhline(0, color=GRID, linewidth=1.1)
    ax.axvline(0, color=GRID, linewidth=1.1)
    ax.set_xlabel(f"PCoA1 ({var1:.1f}% var.)")
    ax.set_ylabel(f"PCoA2 ({var2:.1f}% var.)")
    ax.set_title("Ordenação exploratória AH x trecho - Bray-Curtis sobre CPUEn")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, frameon=False)
    _style_axis(ax)
    _save_fig(fig, path)


def _plot_inflexion_groups(
    series: pd.DataFrame,
    infl: pd.DataFrame,
    metric: str,
    path: Path,
    group_type: str = "Migração x origem",
) -> None:
    data = series.loc[series["Tipo_Categoria"] == group_type].copy()
    categories = [c for c in GROUP_COLORS if c in set(data["Categoria"])]
    fig, axes = plt.subplots(2, 2, figsize=(18, 13), sharex=True)
    axes = axes.ravel()
    for ax, category in zip(axes, categories):
        for trecho, group in data.loc[data["Categoria"] == category].groupby("Trecho"):
            group = group.sort_values("Ordem_AH")
            color = TRECHO_COLORS[trecho]
            ax.plot(group["Ordem_AH"], group[metric], color=color, marker="o", linewidth=2.6, label=trecho)
            fit_row = infl.loc[
                (infl["Tipo_Categoria"] == group_type)
                & (infl["Categoria"] == category)
                & (infl["Trecho"] == trecho)
                & (infl["Metrica"] == metric)
            ]
            if not fit_row.empty and bool(fit_row.iloc[0]["Melhora_Forte"]):
                fit = fit_row.iloc[0].to_dict()
                pred = _piecewise_predict(group["Ordem_AH"].to_numpy(), fit)
                ax.plot(group["Ordem_AH"], pred, color=color, linestyle="--", linewidth=2.1)
                ax.axvline(fit["Breakpoint_Ordem_AH"], color=color, linestyle=":", linewidth=2.0, alpha=0.85)
                ax.text(
                    fit["Breakpoint_Ordem_AH"],
                    ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else group[metric].max(),
                    str(fit["Breakpoint_AH"]),
                    color=color,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=10,
                )
        ax.set_title(category)
        ax.set_ylabel(metric)
        _style_axis(ax)
    labels = data.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    for ax in axes:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["ano_hidrologico_rotulo"], rotation=45, ha="right")
        ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=RECENT, alpha=0.10, linewidth=0)
    axes[0].legend(loc="upper center", bbox_to_anchor=(1.05, 1.28), ncol=2, frameon=False)
    fig.supxlabel("Ano hidrológico", y=0.02, fontsize=FONT_AXIS)
    _save_fig(fig, path)


def _plot_inflexion_groups_fractional_blue(
    series: pd.DataFrame,
    infl: pd.DataFrame,
    metric: str,
    path: Path,
    group_type: str = "Migração x origem",
) -> None:
    data = series.loc[series["Tipo_Categoria"] == group_type].copy()
    if data.empty:
        options = [
            value
            for value in series["Tipo_Categoria"].dropna().astype(str).unique()
            if "origem" in value.lower()
        ]
        if options:
            group_type = options[0]
            data = series.loc[series["Tipo_Categoria"] == group_type].copy()
    preferred_order = [
        "Migradora nativa",
        "Migradora não nativa",
        "Não migradora nativa",
        "Não migradora não nativa",
    ]
    categories = [c for c in preferred_order if c in set(data["Categoria"])]
    categories += [c for c in data["Categoria"].dropna().unique().tolist() if c not in categories]
    category_palette = {
        category: color
        for category, color in zip(categories, ["#002060", "#1F4E79", "#5B9BD5", "#9DC3E6"])
    }
    fig, axes = plt.subplots(2, 2, figsize=(18, 12.2), sharex=True)
    axes = axes.ravel()
    for ax, category in zip(axes, categories):
        for trecho, group in data.loc[data["Categoria"] == category].groupby("Trecho"):
            group = group.sort_values("Ordem_AH")
            color = TRECHO_BLUE_COLORS[trecho]
            ax.plot(
                group["Ordem_AH"],
                group[metric],
                color=color,
                marker="o",
                linewidth=1.8,
                alpha=0.62,
                label=trecho,
            )
            fit_row = infl.loc[
                (infl["Tipo_Categoria"] == group_type)
                & (infl["Categoria"] == category)
                & (infl["Trecho"] == trecho)
                & (infl["Metrica"] == metric)
            ]
            if not fit_row.empty and bool(fit_row.iloc[0]["Melhora_Forte"]):
                fit = fit_row.iloc[0].to_dict()
                bp = fit["Breakpoint_Ordem_AH"]
                pre = _fit_linear_segment(group, metric, group["Ordem_AH"] <= bp)
                post = _fit_linear_segment(group, metric, group["Ordem_AH"] >= bp)
                if pre is not None:
                    ax.plot(pre[0], pre[1], color=color, linewidth=3.0, linestyle="-", alpha=0.96)
                if post is not None:
                    ax.plot(post[0], post[1], color=color, linewidth=3.0, linestyle="--", alpha=0.96)
                ax.axvline(bp, color=color, linestyle=":", linewidth=1.9, alpha=0.78)
                ymax = ax.get_ylim()[1]
                ax.text(
                    bp,
                    ymax,
                    str(fit["Breakpoint_AH"]),
                    color=color,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=10,
                    bbox=dict(facecolor="white", alpha=0.65, edgecolor="none", pad=1.2),
                )
        ax.set_title(category, color=PRIMARY)
        ax.set_ylabel(metric)
        _style_axis(ax)
    labels = data.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    for ax in axes:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["ano_hidrologico_rotulo"], rotation=45, ha="right")
        ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=SECONDARY, alpha=0.12, linewidth=0)
    handles = [
        Line2D([0], [0], color=TRECHO_BLUE_COLORS["Montante"], marker="o", linewidth=2.2, label="Montante"),
        Line2D([0], [0], color=TRECHO_BLUE_COLORS["Jusante"], marker="o", linewidth=2.2, label="Jusante"),
        Line2D([0], [0], color=GREY, linewidth=3.0, linestyle="-", label="Regressão até inflexão"),
        Line2D([0], [0], color=GREY, linewidth=3.0, linestyle="--", label="Regressão após inflexão"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=4, frameon=False)
    fig.supxlabel("Ano hidrológico", y=0.02, fontsize=FONT_AXIS)
    _save_fig(fig, path)


def _plot_inflexion_groups_blue_clean(
    series: pd.DataFrame,
    infl: pd.DataFrame,
    metric: str,
    path: Path,
    group_type: str = "Migração x origem",
) -> None:
    data = series.loc[series["Tipo_Categoria"] == group_type].copy()
    if data.empty:
        options = [
            value
            for value in series["Tipo_Categoria"].dropna().astype(str).unique()
            if "origem" in value.lower()
        ]
        if options:
            group_type = options[0]
            data = series.loc[series["Tipo_Categoria"] == group_type].copy()

    preferred_order = [
        "Migradora nativa",
        "Migradora não nativa",
        "Não migradora nativa",
        "Não migradora não nativa",
    ]
    categories = [c for c in preferred_order if c in set(data["Categoria"])]
    categories += [c for c in data["Categoria"].dropna().unique().tolist() if c not in categories]

    fig, axes = plt.subplots(2, 2, figsize=(18, 12.0), sharex=True)
    axes = axes.ravel()
    for ax, category in zip(axes, categories):
        for trecho, group in data.loc[data["Categoria"] == category].groupby("Trecho"):
            group = group.sort_values("Ordem_AH")
            color = TRECHO_BLUE_COLORS[trecho]
            ax.plot(
                group["Ordem_AH"],
                group[metric],
                color=color,
                marker="o",
                linewidth=2.2,
                alpha=0.78,
                label=trecho,
            )
            fit_row = infl.loc[
                (infl["Tipo_Categoria"] == group_type)
                & (infl["Categoria"] == category)
                & (infl["Trecho"] == trecho)
                & (infl["Metrica"] == metric)
            ]
            if not fit_row.empty and bool(fit_row.iloc[0]["Melhora_Forte"]):
                fit = fit_row.iloc[0].to_dict()
                bp = fit["Breakpoint_Ordem_AH"]
                ax.axvline(bp, color=color, linestyle=":", linewidth=1.9, alpha=0.72)
                ymax = ax.get_ylim()[1]
                ax.text(
                    bp,
                    ymax,
                    str(fit["Breakpoint_AH"]),
                    color=color,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=10,
                    bbox=dict(facecolor="white", alpha=0.65, edgecolor="none", pad=1.0),
                )
        ax.set_title(category, color=PRIMARY)
        ax.set_ylabel(metric)
        _style_axis(ax)

    labels = data.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    for ax in axes:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["ano_hidrologico_rotulo"], rotation=45, ha="right")
        ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=SECONDARY, alpha=0.12, linewidth=0)

    handles = [
        Line2D([0], [0], color=TRECHO_BLUE_COLORS["Montante"], marker="o", linewidth=2.4, label="Montante"),
        Line2D([0], [0], color=TRECHO_BLUE_COLORS["Jusante"], marker="o", linewidth=2.4, label="Jusante"),
        Line2D([0], [0], color=GREY, linewidth=1.9, linestyle=":", label="Ponto de inflexão forte"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3, frameon=False)
    fig.supxlabel("Ano hidrológico", y=0.02, fontsize=FONT_AXIS)
    _save_fig(fig, path)


def _plot_threat_inflexion(series: pd.DataFrame, infl: pd.DataFrame, path: Path) -> None:
    data = series.loc[series["Tipo_Categoria"] == "Ameaça"].copy()
    fig, axes = plt.subplots(2, 2, figsize=(18, 12.5), sharex=True)
    panels = [
        ("Montante", "CPUEn"),
        ("Montante", "CPUEb"),
        ("Jusante", "CPUEn"),
        ("Jusante", "CPUEb"),
    ]
    for ax, (trecho, metric) in zip(axes.ravel(), panels):
        subset = data.loc[data["Trecho"] == trecho]
        for category, group in subset.groupby("Categoria"):
            group = group.sort_values("Ordem_AH")
            color = GROUP_COLORS.get(category, GREY)
            ax.plot(group["Ordem_AH"], group[metric], color=color, marker="o", linewidth=2.6, label=category)
            fit_row = infl.loc[
                (infl["Tipo_Categoria"] == "Ameaça")
                & (infl["Categoria"] == category)
                & (infl["Trecho"] == trecho)
                & (infl["Metrica"] == metric)
            ]
            if not fit_row.empty and bool(fit_row.iloc[0]["Melhora_Forte"]):
                fit = fit_row.iloc[0].to_dict()
                pred = _piecewise_predict(group["Ordem_AH"].to_numpy(), fit)
                ax.plot(group["Ordem_AH"], pred, color=color, linestyle="--", linewidth=2.1)
                ax.axvline(fit["Breakpoint_Ordem_AH"], color=color, linestyle=":", linewidth=2.0, alpha=0.85)
        ax.set_title(f"{trecho} - {metric}")
        ax.set_ylabel(metric)
        _style_axis(ax)
    labels = data.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    for ax in axes.ravel():
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["ano_hidrologico_rotulo"], rotation=45, ha="right")
        ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=RECENT, alpha=0.10, linewidth=0)
    handles = [
        Line2D([0], [0], color=GROUP_COLORS["Ameaçada"], marker="o", linewidth=2.6, label="Ameaçada"),
        Line2D([0], [0], color=GROUP_COLORS["Não ameaçada"], marker="o", linewidth=2.6, label="Não ameaçada"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=2, frameon=False)
    fig.supxlabel("Ano hidrológico", y=0.02, fontsize=FONT_AXIS)
    _save_fig(fig, path)


def _species_delta(base: pd.DataFrame, infl: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[
        base["Tipo_Amostragem_Base"].astype(str).str.contains("Quanti", case=False, na=False)
        & base["Nome_Cientifico"].notna()
    ].copy()
    rows = []
    total_breaks = infl.loc[
        (infl["Tipo_Categoria"] == "Ameaça")
        & (infl["Categoria"] == "Não ameaçada")
        & (infl["Metrica"] == "CPUEn")
        & (infl["Melhora_Forte"])
    ]
    # If the threatened/non-threatened split does not produce a robust break,
    # use the strongest CPUEn break by trecho as an exploratory anchor.
    if total_breaks.empty:
        total_breaks = (
            infl.loc[(infl["Metrica"] == "CPUEn") & (infl["Melhora_Forte"])]
            .sort_values("Delta_BIC", ascending=False)
            .groupby("Trecho")
            .head(1)
        )
    for _, br in total_breaks.iterrows():
        trecho = br["Trecho"]
        bp = br["Breakpoint_Ordem_AH"]
        if pd.isna(bp):
            continue
        subset = q.loc[q["Trecho"] == trecho]
        agg = (
            subset.groupby(["Nome_Cientifico", "ano_hidrologico"], as_index=False)["CPUEn_linha"]
            .sum()
            .merge(_ah_order(base)[["ano_hidrologico", "Ordem_AH"]], on="ano_hidrologico", how="left")
        )
        agg["Periodo_Inflexao"] = np.where(agg["Ordem_AH"] <= bp, "Antes/ate ponto", "Depois")
        mean = (
            agg.groupby(["Nome_Cientifico", "Periodo_Inflexao"], as_index=False)["CPUEn_linha"]
            .mean()
            .pivot_table(index="Nome_Cientifico", columns="Periodo_Inflexao", values="CPUEn_linha", fill_value=0)
        )
        mean["Delta_CPUEn"] = mean.get("Depois", 0) - mean.get("Antes/ate ponto", 0)
        mean["Trecho"] = trecho
        mean["Breakpoint_AH"] = br["Breakpoint_AH"]
        rows.append(mean.reset_index())
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _plot_species_delta(delta: pd.DataFrame, path: Path) -> None:
    if delta.empty:
        return
    trechos = delta["Trecho"].dropna().unique().tolist()
    fig, axes = plt.subplots(len(trechos), 1, figsize=(18, max(8, 6.5 * len(trechos))), squeeze=False)
    for ax, trecho in zip(axes.ravel(), trechos):
        subset = delta.loc[delta["Trecho"] == trecho].copy()
        subset["Abs"] = subset["Delta_CPUEn"].abs()
        top = subset.sort_values("Abs", ascending=False).head(18).sort_values("Delta_CPUEn")
        colors = np.where(top["Delta_CPUEn"] >= 0, GREEN, RED)
        ax.barh(top["Nome_Cientifico"], top["Delta_CPUEn"], color=colors, edgecolor="black", linewidth=0.5)
        ax.axvline(0, color="black", linewidth=1.0)
        bp = top["Breakpoint_AH"].dropna().iloc[0] if top["Breakpoint_AH"].notna().any() else "NA"
        ax.set_title(f"{trecho} - espécies com maior mudança média de CPUEn após ponto exploratório ({bp})")
        ax.set_xlabel("Delta médio CPUEn (depois - antes)")
        _style_axis(ax)
    _save_fig(fig, path)


def _plot_total_cpue_inflexion(cpue_total: pd.DataFrame, infl_total: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(18, 12.5), sharex=True)
    panels = [
        ("Montante", "CPUEn", "Montante - CPUEn"),
        ("Montante", "CPUEb", "Montante - CPUEb"),
        ("Jusante", "CPUEn", "Jusante - CPUEn"),
        ("Jusante", "CPUEb", "Jusante - CPUEb"),
    ]
    for ax, (trecho, metric, title) in zip(axes.ravel(), panels):
        group = cpue_total.loc[cpue_total["Trecho"] == trecho].sort_values("Ordem_AH")
        color = TRECHO_COLORS[trecho]
        ax.plot(group["Ordem_AH"], group[metric], color=color, marker="o", linewidth=3.0, label=trecho)
        fit_row = infl_total.loc[(infl_total["Trecho"] == trecho) & (infl_total["Metrica"] == metric)]
        if not fit_row.empty:
            fit = fit_row.iloc[0].to_dict()
            if bool(fit.get("Melhora_Forte", False)):
                pred = _piecewise_predict(group["Ordem_AH"].to_numpy(), fit)
                ax.plot(group["Ordem_AH"], pred, color=color, linestyle="--", linewidth=2.4, label="Segmentada")
                ax.axvline(fit["Breakpoint_Ordem_AH"], color=color, linestyle=":", linewidth=2.2)
                ax.text(
                    fit["Breakpoint_Ordem_AH"],
                    ax.get_ylim()[1],
                    str(fit["Breakpoint_AH"]),
                    color=color,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=11,
                )
        ax.set_title(title)
        ax.set_ylabel(metric)
        _style_axis(ax)
    labels = cpue_total.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    for ax in axes.ravel():
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["ano_hidrologico_rotulo"], rotation=45, ha="right")
        ax.axvspan(labels["Ordem_AH"].max() - 2.5, labels["Ordem_AH"].max() + 0.5, color=RECENT, alpha=0.10, linewidth=0)
    handles = [
        Line2D([0], [0], color=TRECHO_COLORS["Montante"], marker="o", linewidth=3.0, label="Montante"),
        Line2D([0], [0], color=TRECHO_COLORS["Jusante"], marker="o", linewidth=3.0, label="Jusante"),
        Line2D([0], [0], color="black", linestyle="--", linewidth=2.4, label="Segmentada quando BIC melhora"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3, frameon=False)
    fig.supxlabel("Ano hidrológico", y=0.02, fontsize=FONT_AXIS)
    _save_fig(fig, path)


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)


def _write_summary(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    beta = sheets["Beta_Montante_Jusante_AH"]
    infl = sheets["Inflexoes"]
    strong = infl.loc[infl["Melhora_Forte"]].copy()
    lines = [
        "# Porto Estrela - testes exploratórios beta e inflexão",
        "",
        "Bancada separada do escopo oficial, criada para avaliar melhorias analíticas.",
        "",
        "## Referências metodológicas incorporadas",
        "",
        "- Ferreira et al. (2026, Hydrobiologia): diversidade beta taxonômica temporal, matriz sítios x espécies, transformação de Hellinger, interpretação de diferenciação/homogeneização biótica e LCBD.",
        "- Baselga (2010): decomposição de beta diversidade presença-ausência em turnover e nestedness.",
        "- Aimorés 2026: uso prático de Bray-Curtis, PCoA, SIMPER/riqueza e leitura temporal de similaridade.",
        "",
        "## Leituras rápidas dos dados gerados",
        "",
        f"- Anos hidrológicos avaliados: {beta['ano_hidrologico'].nunique()}.",
        f"- Bray-Curtis CPUEn Montante x Jusante: mediana {beta['BrayCurtis_CPUEn'].median():.3f}, mínimo {beta['BrayCurtis_CPUEn'].min():.3f}, máximo {beta['BrayCurtis_CPUEn'].max():.3f}.",
        f"- β-Sørensen Montante x Jusante: mediana {beta['Beta_Sorensen'].median():.3f}.",
        f"- Inflexões com melhora forte de BIC: {len(strong)} séries.",
        "",
        "## Arquivos principais",
        "",
    ]
    for name in sorted(path.parent.glob("*.png")):
        lines.append(f"- `{name.name}`")
    lines.extend(
        [
            "",
            "## Cautelas",
            "",
            "- As análises são exploratórias e ainda não fazem parte do escopo oficial.",
            "- A análise funcional do artigo não foi replicada porque o cadastro atual não possui matriz funcional/ecomorfológica completa.",
            "- Pontos de inflexão são triagem visual/estatística simples por regressão segmentada contínua e BIC; precisam de validação ecológica antes de entrar em relatório.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    _configure_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(BASE_FILE, sheet_name="Base_Linhas")
    ah = _ah_order(base)

    beta_between = _between_trechos_beta(base, ah)
    beta_consecutive = _consecutive_temporal_beta(base, ah)
    lcbd_points, lcbd_trecho = _lcbd_by_year(base, ah)
    pcoa = _pcoa_ah_trecho(base, ah)
    cpue_total = _cpue_total_trecho(base, ah)
    infl_total = _inflexions_total(cpue_total)
    series = _series_categories(base, ah)
    infl = _inflexions(series)
    delta = _species_delta(base, infl)

    _plot_beta_between(beta_between, OUTPUT_DIR / "exploratoria_01_beta_montante_jusante.png")
    _plot_temporal_consecutive(beta_consecutive, OUTPUT_DIR / "exploratoria_02_beta_temporal_consecutiva_trechos.png")
    _plot_beta_pa_components_combined(
        beta_consecutive,
        OUTPUT_DIR / "exploratoria_10_beta_pa_componentes_trechos_comparativo_azul.png",
    )
    _plot_beta_pa_components_by_area(
        beta_consecutive,
        OUTPUT_DIR / "exploratoria_11_beta_pa_componentes_por_area_azul.png",
    )
    _plot_lcbd(lcbd_trecho, OUTPUT_DIR / "exploratoria_03_lcbd_beta_espacial_trechos.png")
    _plot_pcoa(pcoa, OUTPUT_DIR / "exploratoria_04_pcoa_ah_trecho_bray_curtis.png")
    _plot_inflexion_groups(
        series,
        infl,
        "CPUEn",
        OUTPUT_DIR / "exploratoria_05_inflexao_cpuen_migracao_origem.png",
    )
    _plot_inflexion_groups(
        series,
        infl,
        "CPUEb",
        OUTPUT_DIR / "exploratoria_06_inflexao_cpueb_migracao_origem.png",
    )
    _plot_inflexion_groups_fractional_blue(
        series,
        infl,
        "CPUEb",
        OUTPUT_DIR / "exploratoria_06_inflexao_cpueb_migracao_origem_v2_regressao_fracionada_azul.png",
    )
    _plot_inflexion_groups_blue_clean(
        series,
        infl,
        "CPUEb",
        OUTPUT_DIR / "exploratoria_06_inflexao_cpueb_migracao_origem_v3_sem_tendencia_azul.png",
    )
    _plot_threat_inflexion(series, infl, OUTPUT_DIR / "exploratoria_07_inflexao_ameacadas_cpuen_cpueb.png")
    _plot_species_delta(delta, OUTPUT_DIR / "exploratoria_08_delta_especies_pre_pos_inflexao.png")
    _plot_total_cpue_inflexion(
        cpue_total,
        infl_total,
        OUTPUT_DIR / "exploratoria_09_fig13_cpue_total_com_inflexoes.png",
    )

    sheets = {
        "Beta_Montante_Jusante_AH": beta_between,
        "Beta_Consecutiva_Trechos": beta_consecutive,
        "LCBD_Pontos": lcbd_points,
        "LCBD_Trechos_AH": lcbd_trecho,
        "PCoA_AH_Trecho": pcoa,
        "CPUE_Total_Trecho_AH": cpue_total,
        "Inflexoes_CPUE_Total": infl_total,
        "Series_Categorias_AH": series,
        "Inflexoes": infl,
        "Delta_Especies_Pre_Pos": delta,
        "Notas_Metodo": pd.DataFrame(
            [
                {
                    "Item": "Beta quantitativa",
                    "Descricao": "Bray-Curtis e Hellinger calculados sobre matriz de CPUEn por ano hidrologico e trecho.",
                },
                {
                    "Item": "Beta PA",
                    "Descricao": "Sørensen/Jaccard, turnover e nestedness calculados sobre presenca-ausencia Montante x Jusante.",
                },
                {
                    "Item": "LCBD",
                    "Descricao": "Contribuicao local para beta diversidade calculada por ano hidrologico em matriz ponto x especie com transformacao de Hellinger.",
                },
                {
                    "Item": "Inflexao",
                    "Descricao": "Regressao segmentada continua com um ponto de quebra escolhido por BIC; Delta_BIC > 2 marcado como melhora forte.",
                },
            ]
        ),
    }
    _write_excel(OUTPUT_DIR / "dados_exploratorios_beta_inflexao_porto_estrela.xlsx", sheets)
    _write_summary(OUTPUT_DIR / "README_analises_exploratorias_porto_estrela.md", sheets)
    print(f"Saida: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
