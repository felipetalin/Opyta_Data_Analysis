from __future__ import annotations

import argparse
import base64
import json
import math
import re
import sys
import unicodedata
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from opyta_analysis.supabase_client import get_client, paginate  # noqa: E402


PROJECT_ID = 165
PROJECT_CODE = "ITAGUA001"
GROUP = "Ictiofauna"
CUTOFF = pd.Timestamp("2017-07-01")
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "outputs"
    / "_project_scripts"
    / "ITAGUA001__monitoramento_da_fauna"
    / "ictiofauna"
    / "dashboard_performance_ambiental"
)
EXTERNAL_ENV = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")

EMP_ORDER = ["Jacaré", "Senhora do Porto", "Dores de Guanhães", "Fortuna II"]
EMP_COLORS = {
    "Jacaré": "#386FA4",
    "Senhora do Porto": "#2A9D8F",
    "Dores de Guanhães": "#8F5D2A",
    "Fortuna II": "#C44E52",
}
CASCADE_POSITION = {
    "Jacaré": 1,
    "Senhora do Porto": 2,
    "Dores de Guanhães": 3,
}


def _norm(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _campaign_date(value: object) -> pd.Timestamp | pd.NaT:
    match = re.search(r"^(?:CR|C)0*\d+-(\d{4})-(\d{2})-[A-Z]+$", str(value).strip(), flags=re.I)
    if not match:
        return pd.NaT
    return pd.Timestamp(year=int(match.group(1)), month=int(match.group(2)), day=1)


def _campaign_sort_key(value: object) -> tuple[pd.Timestamp, str]:
    date = _campaign_date(value)
    if pd.isna(date):
        date = pd.Timestamp.max
    return date, str(value)


def _fmt_int(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}".replace(",", ".")


def _fmt_num(value: object, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: object, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{_fmt_num(value, digits)}%"


def _status_score(status: str) -> int:
    return {"Não atendido": 0, "Atenção": 1, "Atendido": 2}.get(status, -1)


def _status_class(status: str) -> str:
    return {
        "Atendido": "ok",
        "Atenção": "warn",
        "Não atendido": "bad",
        "Sem dado": "neutral",
    }.get(status, "neutral")


def _trend(x_dates: pd.Series, y_values: pd.Series) -> dict[str, Any]:
    data = pd.DataFrame({"date": x_dates, "y": pd.to_numeric(y_values, errors="coerce")}).dropna()
    if len(data) < 4:
        return {"n": int(len(data)), "slope": np.nan, "p": np.nan, "r2": np.nan}
    x = data["date"].map(lambda d: d.year + (d.month - 1) / 12.0).to_numpy(dtype=float)
    y = data["y"].to_numpy(dtype=float)
    result = stats.linregress(x, y)
    return {
        "n": int(len(data)),
        "slope": float(result.slope),
        "p": float(result.pvalue),
        "r2": float(result.rvalue**2),
    }


def _shannon(values: pd.Series) -> tuple[float, float, float]:
    x = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(dtype=float)
    x = x[x > 0]
    if x.size == 0 or x.sum() <= 0:
        return 0.0, 0.0, 0.0
    p = x / x.sum()
    h = float(-(p * np.log(p)).sum())
    simpson = float(1.0 - np.sum(p**2))
    pielou = float(h / np.log(x.size)) if x.size > 1 else 0.0
    return h, simpson, pielou


def _chao2(presabs: np.ndarray) -> tuple[float, float, float]:
    if presabs.size == 0:
        return 0.0, np.nan, np.nan
    incidence = presabs.sum(axis=0)
    s_obs = float((incidence > 0).sum())
    q1 = float((incidence == 1).sum())
    q2 = float((incidence == 2).sum())
    samples = presabs.shape[0]
    if samples < 2:
        return s_obs, s_obs, 1.0 if s_obs else np.nan
    if q2 > 0:
        chao = s_obs + ((samples - 1) / samples) * (q1**2) / (2 * q2)
    else:
        chao = s_obs + ((samples - 1) / samples) * q1 * (q1 - 1) / 2.0
    coverage = s_obs / chao if chao and chao > 0 else np.nan
    return s_obs, float(chao), float(coverage)


def _beta_pair(prev: np.ndarray, curr: np.ndarray) -> tuple[float, float, float]:
    prev = prev.astype(bool)
    curr = curr.astype(bool)
    a = float(np.logical_and(prev, curr).sum())
    b = float(np.logical_and(prev, ~curr).sum())
    c = float(np.logical_and(~prev, curr).sum())
    sor_denom = 2 * a + b + c
    sor = (b + c) / sor_denom if sor_denom > 0 else np.nan
    sim_denom = a + min(b, c)
    turnover = min(b, c) / sim_denom if sim_denom > 0 else np.nan
    nestedness = sor - turnover if np.isfinite(sor) and np.isfinite(turnover) else np.nan
    return float(sor), float(turnover), float(max(nestedness, 0.0)) if np.isfinite(nestedness) else np.nan


def _img_data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _save_fig(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def load_data(env_file: str | None) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    sb = get_client(env_file)
    rows = paginate(
        sb,
        "biota_analise_consolidada",
        filters={"codigo_interno_opyta": PROJECT_CODE, "grupo_biologico": GROUP},
        select="*",
    )
    if not rows:
        raise RuntimeError("Nenhum registro encontrado em biota_analise_consolidada para ITAGUA001/Ictiofauna.")

    df = pd.DataFrame(rows)
    for col in ["contagem", "biomassa", "esforco"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["data_campanha"] = df["nome_campanha"].map(_campaign_date)
    df = df[df["data_campanha"].notna()].copy()
    df["fase"] = np.where(df["data_campanha"] <= CUTOFF, "Pré", "Pós")

    species_names = sorted(df["nome_cientifico"].dropna().astype(str).unique().tolist())
    species_rows = paginate(
        sb,
        "especies",
        select=(
            "nome_cientifico,status_ameaca_global,status_ameaca_nacional,status_copam,"
            "cites,migratorio,origem,valor_economico"
        ),
    )
    species = pd.DataFrame([row for row in species_rows if row.get("nome_cientifico") in species_names])
    if not species.empty:
        species = species.drop_duplicates("nome_cientifico")
        species = species.rename(columns={"origem": "origem_cadastro"})
        df = df.merge(species, on="nome_cientifico", how="left")
    else:
        for col in [
            "status_ameaca_global",
            "status_ameaca_nacional",
            "status_copam",
            "cites",
            "migratorio",
            "origem_cadastro",
            "valor_economico",
        ]:
            df[col] = np.nan

    origem_norm = df["origem"].where(df["origem"].notna(), df["origem_cadastro"]).map(_norm)
    df["origem_norm"] = origem_norm
    df["is_native"] = origem_norm.str.contains("nativo", na=False) & ~origem_norm.str.contains("nao", na=False)
    df["is_nonnative"] = origem_norm.str.contains("nao nativ", na=False)

    threat_cols = ["status_ameaca_global", "status_ameaca_nacional", "status_copam"]
    threat_values = {"VU", "EN", "CR", "EW", "RE"}
    df["is_threatened"] = False
    for col in threat_cols:
        if col in df.columns:
            df["is_threatened"] |= df[col].fillna("").astype(str).str.upper().str.strip().isin(threat_values)

    df["cpue_n"] = np.where(df["esforco"] > 0, df["contagem"] / df["esforco"] * 100.0, np.nan)
    df["cpue_b"] = np.where(df["esforco"] > 0, df["biomassa"] / df["esforco"] * 100.0, np.nan)

    campaigns = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    campaign_map = {row.get("id_campanha"): row.get("nome_campanha") for row in campaigns}
    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": PROJECT_ID},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    registered_campaigns = {
        campaign_map.get(row.get("id_campanha"))
        for row in pontos
        if campaign_map.get(row.get("id_campanha"))
    }
    quality = {
        "registered_campaigns": sorted(registered_campaigns, key=_campaign_sort_key),
        "result_campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist(), key=_campaign_sort_key),
    }
    quality["quantitative_campaigns"] = sorted(
        df.loc[df["tipo_amostragem"].eq("Quantitativa"), "nome_campanha"].dropna().astype(str).unique().tolist(),
        key=_campaign_sort_key,
    )
    quality["registered_without_results"] = sorted(
        set(quality["registered_campaigns"]) - set(quality["result_campaigns"]),
        key=_campaign_sort_key,
    )
    quality["results_without_quantitative"] = sorted(
        set(quality["result_campaigns"]) - set(quality["quantitative_campaigns"]),
        key=_campaign_sort_key,
    )
    quality["quantitative_without_qualitative"] = sorted(
        set(quality["quantitative_campaigns"])
        - set(df.loc[df["tipo_amostragem"].eq("Qualitativa"), "nome_campanha"].dropna().astype(str).unique()),
        key=_campaign_sort_key,
    )

    return df, species, quality


def build_alpha(df: pd.DataFrame) -> pd.DataFrame:
    quant = df[df["tipo_amostragem"].eq("Quantitativa")].copy()
    records: list[dict[str, Any]] = []
    keys = ["nome_empreendimento", "nome_campanha", "data_campanha", "fase"]
    for (emp, campaign, date, phase), group in quant.groupby(keys, dropna=False):
        species_counts = group.groupby("nome_cientifico", dropna=False)["contagem"].sum().sort_values(ascending=False)
        total = float(species_counts.sum())
        richness = int((species_counts > 0).sum())
        h, simpson, pielou = _shannon(species_counts)
        native = float(group.loc[group["is_native"], "contagem"].sum())
        nonnative = float(group.loc[group["is_nonnative"], "contagem"].sum())
        threatened = float(group.loc[group["is_threatened"], "contagem"].sum())
        records.append(
            {
                "empreendimento": emp,
                "campanha": campaign,
                "data_campanha": date,
                "fase": phase,
                "riqueza": richness,
                "abundancia": total,
                "shannon": h,
                "simpson": simpson,
                "pielou": pielou,
                "CPUEn": float(group["cpue_n"].sum(skipna=True)),
                "CPUEb": float(group["cpue_b"].sum(skipna=True)),
                "nativas_pct": native / total * 100.0 if total else np.nan,
                "nao_nativas_pct": nonnative / total * 100.0 if total else np.nan,
                "ameacadas_ind": threatened,
                "top1_pct": float(species_counts.iloc[0] / total * 100.0) if total and not species_counts.empty else np.nan,
                "top3_pct": float(species_counts.head(3).sum() / total * 100.0) if total and not species_counts.empty else np.nan,
            }
        )
    alpha = pd.DataFrame(records)
    if not alpha.empty:
        alpha["empreendimento"] = pd.Categorical(alpha["empreendimento"], EMP_ORDER, ordered=True)
        alpha = alpha.sort_values(["empreendimento", "data_campanha", "campanha"]).reset_index(drop=True)
    return alpha


def build_coverage(df: pd.DataFrame) -> pd.DataFrame:
    quant = df[df["tipo_amostragem"].eq("Quantitativa")].copy()
    records: list[dict[str, Any]] = []
    for emp, emp_df in quant.groupby("nome_empreendimento"):
        for phase_label, phase_df in [("Global", emp_df), ("Pós", emp_df[emp_df["fase"].eq("Pós")])]:
            matrix = (
                phase_df.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], dropna=False)["contagem"]
                .sum()
                .unstack(fill_value=0)
            )
            presabs = (matrix.to_numpy(dtype=float) > 0).astype(int)
            s_obs, chao, coverage = _chao2(presabs)
            records.append(
                {
                    "empreendimento": emp,
                    "fase": phase_label,
                    "unidades_campanha_ponto": int(matrix.shape[0]),
                    "riqueza_obs": s_obs,
                    "chao2": chao,
                    "cobertura": coverage,
                }
            )
    out = pd.DataFrame(records)
    if not out.empty:
        out["empreendimento"] = pd.Categorical(out["empreendimento"], EMP_ORDER, ordered=True)
        out = out.sort_values(["empreendimento", "fase"]).reset_index(drop=True)
    return out


def build_beta(df: pd.DataFrame) -> pd.DataFrame:
    quant = df[df["tipo_amostragem"].eq("Quantitativa")].copy()
    records: list[dict[str, Any]] = []
    for emp, emp_df in quant.groupby("nome_empreendimento"):
        matrix = (
            emp_df.groupby(["data_campanha", "nome_campanha", "nome_cientifico"], dropna=False)["contagem"]
            .sum()
            .unstack(fill_value=0)
        )
        if matrix.shape[0] < 2:
            continue
        matrix = matrix.sort_index(level=0)
        pres = (matrix.to_numpy(dtype=float) > 0).astype(int)
        meta = matrix.index.to_frame(index=False)
        for idx in range(1, len(meta)):
            prev = pres[idx - 1]
            curr = pres[idx]
            sorensen, turnover, nestedness = _beta_pair(prev, curr)
            prev_date = pd.Timestamp(meta.iloc[idx - 1]["data_campanha"])
            curr_date = pd.Timestamp(meta.iloc[idx]["data_campanha"])
            pair_phase = "Pós" if prev_date > CUTOFF and curr_date > CUTOFF else "Transição/Pré"
            records.append(
                {
                    "empreendimento": emp,
                    "campanha_anterior": meta.iloc[idx - 1]["nome_campanha"],
                    "campanha_atual": meta.iloc[idx]["nome_campanha"],
                    "data_atual": curr_date,
                    "fase_par": pair_phase,
                    "beta_sorensen": sorensen,
                    "turnover_simpson": turnover,
                    "nestedness": nestedness,
                }
            )
    beta = pd.DataFrame(records)
    if not beta.empty:
        beta["empreendimento"] = pd.Categorical(beta["empreendimento"], EMP_ORDER, ordered=True)
        beta = beta.sort_values(["empreendimento", "data_atual"]).reset_index(drop=True)
    return beta


def build_trends(alpha: pd.DataFrame, beta: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for emp in EMP_ORDER:
        emp_alpha = alpha[(alpha["empreendimento"].astype(str) == emp) & alpha["fase"].eq("Pós")]
        emp_beta = beta[(beta["empreendimento"].astype(str) == emp) & beta["fase_par"].eq("Pós")]
        for metric in ["riqueza", "shannon", "CPUEn", "nao_nativas_pct", "top3_pct"]:
            tr = _trend(emp_alpha["data_campanha"], emp_alpha[metric])
            records.append({"empreendimento": emp, "indicador": metric, **tr})
        if not emp_beta.empty:
            tr = _trend(emp_beta["data_atual"], emp_beta["beta_sorensen"])
            records.append({"empreendimento": emp, "indicador": "beta_sorensen", **tr})
    return pd.DataFrame(records)


def build_indicator_table(alpha: pd.DataFrame, coverage: pd.DataFrame, beta: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for emp in EMP_ORDER:
        post_alpha = alpha[(alpha["empreendimento"].astype(str) == emp) & alpha["fase"].eq("Pós")]
        emp_cov = coverage[(coverage["empreendimento"].astype(str) == emp) & coverage["fase"].eq("Pós")]
        emp_beta = beta[(beta["empreendimento"].astype(str) == emp) & beta["fase_par"].eq("Pós")]
        emp_trends = trends[trends["empreendimento"].astype(str) == emp].set_index("indicador")

        cov = float(emp_cov["cobertura"].iloc[0]) if not emp_cov.empty else np.nan
        cov_status = "Atendido" if cov >= 0.85 else "Atenção" if cov >= 0.70 else "Não atendido"

        def trend_status(metric: str, mode: str) -> tuple[str, str]:
            if metric not in emp_trends.index:
                return "Sem dado", "n insuficiente"
            row = emp_trends.loc[metric]
            slope = float(row["slope"])
            p = float(row["p"])
            if mode == "no_decline":
                if p < 0.05 and slope < 0:
                    return "Não atendido", f"queda significativa (p={p:.3g})"
                if p < 0.10 and slope < 0:
                    return "Atenção", f"queda marginal (p={p:.3g})"
                return "Atendido", "sem queda significativa"
            if mode == "no_increase":
                if p < 0.05 and slope > 0:
                    return "Não atendido", f"aumento significativo (p={p:.3g})"
                if p < 0.10 and slope > 0:
                    return "Atenção", f"aumento marginal (p={p:.3g})"
                return "Atendido", "sem aumento significativo"
            return "Sem dado", "-"

        richness_status, richness_note = trend_status("riqueza", "no_decline")
        cpuen_status, cpuen_note = trend_status("CPUEn", "no_decline")
        exotics_status, exotics_note = trend_status("nao_nativas_pct", "no_increase")

        native_post = float(post_alpha["nativas_pct"].median()) if not post_alpha.empty else np.nan
        if native_post >= 95:
            native_status = "Atendido"
        elif native_post >= 90:
            native_status = "Atenção"
        else:
            native_status = "Não atendido"

        beta_med = float(emp_beta["beta_sorensen"].median()) if not emp_beta.empty else np.nan
        turnover_med = float(emp_beta["turnover_simpson"].median()) if not emp_beta.empty else np.nan
        nested_med = float(emp_beta["nestedness"].median()) if not emp_beta.empty else np.nan
        beta_tr_status, beta_tr_note = trend_status("beta_sorensen", "no_increase")
        if np.isfinite(beta_med) and beta_med <= 0.40 and beta_tr_status != "Não atendido":
            beta_status = "Atendido"
        elif np.isfinite(beta_med) and beta_med <= 0.55:
            beta_status = "Atenção"
        else:
            beta_status = "Não atendido"
        turnover_status = "Atendido" if turnover_med > nested_med else "Não atendido"

        indicator_defs = [
            ("Suficiência amostral pós", cov_status, f"Chao2 cobertura={_fmt_pct(cov * 100, 1)}"),
            ("Riqueza sem queda pós", richness_status, richness_note),
            ("CPUEn sem queda pós", cpuen_status, cpuen_note),
            ("Beta temporal controlada", beta_status, f"β-Sor mediana={_fmt_num(beta_med, 2)}; {beta_tr_note}"),
            ("Turnover > nestedness", turnover_status, f"turnover={_fmt_num(turnover_med, 2)}; nestedness={_fmt_num(nested_med, 2)}"),
            ("Dominância nativa", native_status, f"mediana pós={_fmt_pct(native_post, 1)}"),
            ("Não nativas sem aumento", exotics_status, exotics_note),
        ]
        for name, status, evidence in indicator_defs:
            records.append(
                {
                    "empreendimento": emp,
                    "indicador": name,
                    "status": status,
                    "score": _status_score(status),
                    "evidencia": evidence,
                }
            )
    return pd.DataFrame(records)


def build_summary_tables(df: pd.DataFrame, alpha: pd.DataFrame, beta: pd.DataFrame, indicators: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    post_pre = (
        alpha.groupby(["empreendimento", "fase"], observed=False)
        .agg(
            campanhas=("campanha", "nunique"),
            riqueza_mediana=("riqueza", "median"),
            shannon_mediana=("shannon", "median"),
            CPUEn_mediana=("CPUEn", "median"),
            nao_nativas_mediana_pct=("nao_nativas_pct", "median"),
            top3_mediana_pct=("top3_pct", "median"),
        )
        .reset_index()
    )

    latest_date = alpha["data_campanha"].max()
    latest = alpha[alpha["data_campanha"].eq(latest_date)].copy()
    post_median = (
        alpha[alpha["fase"].eq("Pós")]
        .groupby("empreendimento", observed=False)
        .agg(
            riqueza_pos_mediana=("riqueza", "median"),
            CPUEn_pos_mediana=("CPUEn", "median"),
            nao_nativas_pos_mediana_pct=("nao_nativas_pct", "median"),
        )
        .reset_index()
    )
    latest = latest.merge(post_median, on="empreendimento", how="left")

    indicator_score = (
        indicators.groupby("empreendimento", observed=False)
        .agg(
            indicadores_atendidos=("status", lambda values: int((pd.Series(values) == "Atendido").sum())),
            indicadores_alerta=("status", lambda values: int((pd.Series(values) == "Atenção").sum())),
            indicadores_nao_atendidos=("status", lambda values: int((pd.Series(values) == "Não atendido").sum())),
            media_score=("score", "mean"),
        )
        .reset_index()
    )
    indicator_score["classe"] = np.select(
        [
            indicator_score["media_score"] >= 1.65,
            indicator_score["media_score"] >= 1.15,
        ],
        ["Desempenho favorável com ressalvas", "Desempenho parcial / atenção"],
        default="Desempenho insuficiente",
    )

    species_pressure = (
        df[df["tipo_amostragem"].eq("Quantitativa")]
        .groupby(["nome_cientifico", "origem"], dropna=False)
        .agg(
            abundancia=("contagem", "sum"),
            campanhas=("nome_campanha", "nunique"),
            empreendimentos=("nome_empreendimento", "nunique"),
            ameacada=("is_threatened", "max"),
            nao_nativa=("is_nonnative", "max"),
        )
        .reset_index()
        .sort_values("abundancia", ascending=False)
    )
    return post_pre, latest, indicator_score, species_pressure


def plot_timeline(alpha: pd.DataFrame, out: Path) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), sharex=True)
    axes = axes.ravel()
    metrics = [
        ("riqueza", "Riqueza por campanha"),
        ("CPUEn", "CPUEn total"),
        ("shannon", "Shannon (H')"),
        ("nao_nativas_pct", "Não nativas (%)"),
    ]
    for ax, (metric, label) in zip(axes, metrics):
        for emp in EMP_ORDER:
            data = alpha[alpha["empreendimento"].astype(str).eq(emp)]
            if data.empty:
                continue
            ax.plot(
                data["data_campanha"],
                data[metric],
                marker="o",
                markersize=3.2,
                linewidth=1.3,
                label=emp,
                color=EMP_COLORS[emp],
            )
        ax.axvline(CUTOFF, color="#555555", linestyle="--", linewidth=1, alpha=0.8)
        ax.set_title(label, loc="left", fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].set_ylabel("ind/100 m²")
    axes[3].set_ylabel("% da abundância")
    axes[0].legend(ncol=2, loc="upper left", frameon=False)
    fig.suptitle("Indicadores temporais da ictiofauna quantitativa", x=0.02, y=0.995, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.02, 0.02, "Linha tracejada: corte Pré/Pós (2017-07-01).", fontsize=9, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    return _save_fig(fig, out / "01_timeline_indicadores.png")


def plot_indicator_heatmap(indicators: pd.DataFrame, out: Path) -> Path:
    pivot = indicators.pivot(index="empreendimento", columns="indicador", values="score").reindex(EMP_ORDER)
    columns = list(pivot.columns)
    data = pivot.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(15.5, 4.8))
    cmap = ListedColormap(["#C84C4C", "#F1C75B", "#3E8F5A", "#D4D8DD"])
    masked = np.where(np.isfinite(data), data, 3)
    ax.imshow(masked, cmap=cmap, vmin=0, vmax=3)
    ax.set_xticks(np.arange(len(columns)), labels=columns, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(np.arange(len(EMP_ORDER)), labels=EMP_ORDER, fontsize=10)
    for i, emp in enumerate(EMP_ORDER):
        for j, col in enumerate(columns):
            row = indicators[(indicators["empreendimento"].eq(emp)) & (indicators["indicador"].eq(col))]
            status = row["status"].iloc[0] if not row.empty else "Sem dado"
            text = {"Atendido": "OK", "Atenção": "AT", "Não atendido": "NÃO", "Sem dado": "S/D"}.get(status, "")
            color = "white" if status in {"Atendido", "Não atendido"} else "#1F2933"
            ax.text(j, i, text, ha="center", va="center", fontsize=9, fontweight="bold", color=color)
    ax.tick_params(length=0)
    ax.set_title("Semáforo de alcance dos indicadores ambientais", loc="left", fontsize=14, fontweight="bold")
    ax.text(
        0,
        -0.55,
        "OK = atendido; AT = atenção; NÃO = não atendido. Critérios calculados sobre a série quantitativa pós-2017.",
        transform=ax.transAxes,
        fontsize=9,
        color="#555",
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return _save_fig(fig, out / "02_semaforo_indicadores.png")


def plot_latest_vs_median(latest: pd.DataFrame, out: Path) -> Path:
    data = latest.copy()
    data["empreendimento"] = pd.Categorical(data["empreendimento"].astype(str), EMP_ORDER, ordered=True)
    data = data.sort_values("empreendimento")
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))
    specs = [
        ("riqueza", "riqueza_pos_mediana", "Riqueza", "espécies"),
        ("CPUEn", "CPUEn_pos_mediana", "CPUEn", "ind/100 m²"),
        ("nao_nativas_pct", "nao_nativas_pos_mediana_pct", "Não nativas", "%"),
    ]
    x = np.arange(len(data))
    width = 0.36
    for ax, (latest_col, median_col, title, ylabel) in zip(axes, specs):
        latest_vals = data[latest_col].to_numpy(dtype=float)
        median_vals = data[median_col].to_numpy(dtype=float)
        ax.bar(x - width / 2, median_vals, width, label="Mediana pós", color="#D7DEE8")
        ax.bar(x + width / 2, latest_vals, width, label="Última campanha", color=[EMP_COLORS[e] for e in data["empreendimento"].astype(str)])
        ax.set_xticks(x, labels=data["empreendimento"].astype(str), rotation=20, ha="right")
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, loc="upper left")
    campaign = str(data["campanha"].iloc[0]) if not data.empty else "última campanha"
    fig.suptitle(f"Última campanha ({campaign}) versus mediana pós-2017", x=0.02, y=1.02, ha="left", fontsize=15, fontweight="bold")
    fig.tight_layout()
    return _save_fig(fig, out / "03_ultima_vs_mediana_pos.png")


def plot_species_pressure(df: pd.DataFrame, alpha: pd.DataFrame, out: Path) -> Path:
    quant = df[df["tipo_amostragem"].eq("Quantitativa")].copy()
    top = (
        quant.groupby(["nome_cientifico", "is_nonnative", "is_threatened"], dropna=False)["contagem"]
        .sum()
        .sort_values(ascending=False)
        .head(12)
        .reset_index()
        .sort_values("contagem")
    )
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.3))
    colors = np.where(top["is_nonnative"], "#C44E52", np.where(top["is_threatened"], "#7B4EA3", "#3E8F5A"))
    axes[0].barh(top["nome_cientifico"], top["contagem"], color=colors)
    axes[0].set_title("Espécies mais abundantes", loc="left", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Indivíduos registrados")
    axes[0].grid(axis="x", alpha=0.2)
    axes[0].spines[["top", "right"]].set_visible(False)
    for label in axes[0].get_yticklabels():
        label.set_fontstyle("italic")

    for emp in EMP_ORDER:
        data = alpha[alpha["empreendimento"].astype(str).eq(emp)]
        axes[1].plot(
            data["data_campanha"],
            data["nao_nativas_pct"],
            marker="o",
            markersize=3,
            linewidth=1.2,
            color=EMP_COLORS[emp],
            label=emp,
        )
    axes[1].axvline(CUTOFF, color="#555555", linestyle="--", linewidth=1, alpha=0.8)
    axes[1].set_title("Pressão de espécies não nativas", loc="left", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("% da abundância por campanha")
    axes[1].grid(True, alpha=0.2)
    axes[1].spines[["top", "right"]].set_visible(False)
    axes[1].legend(frameon=False, ncol=1, loc="upper left")

    fig.suptitle("Composição e sinais de pressão biológica", x=0.02, y=1.02, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.02, 0.01, "Verde = nativa; vermelho = não nativa; roxo = ameaçada.", fontsize=9, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    return _save_fig(fig, out / "04_pressao_especies.png")


def plot_beta_cascade(alpha: pd.DataFrame, beta: pd.DataFrame, out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 5.5))
    for emp in EMP_ORDER:
        data = beta[(beta["empreendimento"].astype(str).eq(emp)) & beta["fase_par"].eq("Pós")]
        axes[0].plot(
            data["data_atual"],
            data["beta_sorensen"],
            marker="o",
            markersize=3,
            linewidth=1.2,
            color=EMP_COLORS[emp],
            label=emp,
        )
    axes[0].axhline(0.40, color="#7A3030", linestyle=":", linewidth=1.2, label="referência 0,40")
    axes[0].set_title("β-Sorensen consecutivo pós-2017", loc="left", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Dissimilaridade")
    axes[0].grid(True, alpha=0.2)
    axes[0].spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8)

    cascade = (
        alpha[(alpha["fase"].eq("Pós")) & alpha["empreendimento"].astype(str).isin(CASCADE_POSITION)]
        .assign(posicao=lambda d: d["empreendimento"].astype(str).map(CASCADE_POSITION))
        .groupby(["empreendimento", "posicao"], observed=False)
        .agg(riqueza_mediana=("riqueza", "median"), CPUEn_mediana=("CPUEn", "median"))
        .reset_index()
        .sort_values("posicao")
    )
    axes[1].plot(cascade["posicao"], cascade["riqueza_mediana"], marker="o", linewidth=2, color="#386FA4", label="Riqueza")
    ax2 = axes[1].twinx()
    ax2.plot(cascade["posicao"], cascade["CPUEn_mediana"], marker="s", linewidth=2, color="#C44E52", label="CPUEn")
    axes[1].set_xticks(cascade["posicao"], labels=cascade["empreendimento"].astype(str), rotation=15, ha="right")
    axes[1].set_title("Gradiente da cascata do rio Guanhães", loc="left", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Riqueza mediana pós")
    ax2.set_ylabel("CPUEn mediana pós")
    axes[1].grid(True, axis="y", alpha=0.2)
    axes[1].spines[["top", "right"]].set_visible(False)
    ax2.spines["top"].set_visible(False)
    lines, labels = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    axes[1].legend(lines + lines2, labels + labels2, frameon=False, loc="upper right")

    fig.suptitle("Estabilidade temporal e leitura espacial", x=0.02, y=1.02, ha="left", fontsize=15, fontweight="bold")
    fig.tight_layout()
    return _save_fig(fig, out / "05_beta_cascata.png")


def plot_coverage(coverage: pd.DataFrame, out: Path) -> Path:
    post = coverage[coverage["fase"].eq("Pós")].copy()
    post["empreendimento"] = pd.Categorical(post["empreendimento"].astype(str), EMP_ORDER, ordered=True)
    post = post.sort_values("empreendimento")
    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    vals = post["cobertura"] * 100.0
    colors = ["#3E8F5A" if v >= 85 else "#F1C75B" if v >= 70 else "#C84C4C" for v in vals]
    ax.bar(post["empreendimento"].astype(str), vals, color=colors)
    ax.axhline(85, color="#4E6E58", linestyle="--", linewidth=1, label="referência 85%")
    ax.set_ylim(0, max(100, float(vals.max()) + 8 if len(vals) else 100))
    ax.set_ylabel("Cobertura Chao2 (%)")
    ax.set_title("Suficiência amostral pós-2017 por empreendimento", loc="left", fontsize=13, fontweight="bold")
    ax.grid(axis="y", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    for idx, row in post.reset_index(drop=True).iterrows():
        ax.text(idx, row["cobertura"] * 100.0 + 1.2, _fmt_pct(row["cobertura"] * 100.0, 1), ha="center", fontsize=9)
    fig.tight_layout()
    return _save_fig(fig, out / "06_suficiencia_amostral.png")


def _table_html(df: pd.DataFrame, columns: list[str], headers: list[str], formatters: dict[str, Any] | None = None) -> str:
    formatters = formatters or {}
    lines = ["<table>", "<thead><tr>"]
    for header in headers:
        lines.append(f"<th>{escape(header)}</th>")
    lines.append("</tr></thead><tbody>")
    for _, row in df.iterrows():
        lines.append("<tr>")
        for col in columns:
            value = row.get(col)
            if col in formatters:
                rendered = formatters[col](value)
            else:
                rendered = "-" if pd.isna(value) else str(value)
            lines.append(f"<td>{escape(str(rendered))}</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "".join(lines)


def _indicator_cards(indicator_score: pd.DataFrame) -> str:
    cards = []
    for _, row in indicator_score.iterrows():
        score = float(row["media_score"])
        status = "ok" if score >= 1.65 else "warn" if score >= 1.15 else "bad"
        cards.append(
            f"""
            <div class="score-card {status}">
              <div class="card-title">{escape(str(row['empreendimento']))}</div>
              <div class="score">{_fmt_num(score, 2)} / 2</div>
              <div class="muted">{escape(str(row['classe']))}</div>
              <div class="mini-line">
                <span>OK {_fmt_int(row['indicadores_atendidos'])}</span>
                <span>Atenção {_fmt_int(row['indicadores_alerta'])}</span>
                <span>Não {_fmt_int(row['indicadores_nao_atendidos'])}</span>
              </div>
            </div>
            """
        )
    return "\n".join(cards)


def _find_evidence(indicators: pd.DataFrame, emp: str, indicator: str) -> str:
    row = indicators[(indicators["empreendimento"].eq(emp)) & (indicators["indicador"].eq(indicator))]
    if row.empty:
        return "-"
    return str(row["evidencia"].iloc[0])


def build_findings(
    quality: dict[str, Any],
    alpha: pd.DataFrame,
    trends: pd.DataFrame,
    species_pressure: pd.DataFrame,
    latest: pd.DataFrame,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    cpuen_alerts = []
    richness_alerts = []
    nonnative_alerts = []
    trends_idx = trends.set_index(["empreendimento", "indicador"])
    for emp in EMP_ORDER:
        if (emp, "CPUEn") in trends_idx.index:
            row = trends_idx.loc[(emp, "CPUEn")]
            if float(row["p"]) < 0.05 and float(row["slope"]) < 0:
                cpuen_alerts.append(f"{emp} (slope={_fmt_num(row['slope'], 2)}; p={float(row['p']):.3g})")
        if (emp, "riqueza") in trends_idx.index:
            row = trends_idx.loc[(emp, "riqueza")]
            if float(row["p"]) < 0.05 and float(row["slope"]) < 0:
                richness_alerts.append(f"{emp} (slope={_fmt_num(row['slope'], 2)}; p={float(row['p']):.3g})")
        if (emp, "nao_nativas_pct") in trends_idx.index:
            row = trends_idx.loc[(emp, "nao_nativas_pct")]
            if float(row["p"]) < 0.05 and float(row["slope"]) > 0:
                nonnative_alerts.append(f"{emp} (slope={_fmt_num(row['slope'], 2)} p.p./ano; p={float(row['p']):.3g})")

    if cpuen_alerts:
        findings.append(
            {
                "severity": "bad",
                "title": "CPUEn em queda significativa nas quatro PCHs",
                "text": "O indicador de captura por esforço cai no período pós-2017 em " + "; ".join(cpuen_alerts) + ". Isso impede concluir alcance pleno de estabilidade.",
            }
        )
    if richness_alerts:
        findings.append(
            {
                "severity": "bad",
                "title": "Riqueza com queda significativa em parte da série",
                "text": "A tendência pós-2017 de riqueza é negativa e significativa em " + "; ".join(richness_alerts) + ".",
            }
        )
    if nonnative_alerts:
        findings.append(
            {
                "severity": "warn",
                "title": "Não nativas ainda baixas, mas com aumento temporal",
                "text": "A participação atual é baixa, porém há aumento pós-2017 em " + "; ".join(nonnative_alerts) + ". O sinal merece acompanhamento específico.",
            }
        )

    threat = species_pressure[species_pressure["ameacada"].astype(bool)]
    if not threat.empty:
        names = ", ".join(f"<i>{escape(str(v))}</i>" for v in threat["nome_cientifico"].head(5))
        findings.append(
            {
                "severity": "warn",
                "title": "Espécie ameaçada presente no lastro",
                "text": f"A base registra {names}. O dashboard trata presença de ameaçadas como ponto de atenção, não como indicador de melhoria isolada.",
            }
        )

    if quality.get("registered_without_results"):
        findings.append(
            {
                "severity": "warn",
                "title": "Há campanha cadastrada sem resultado de ictiofauna",
                "text": "Campanha(s): " + ", ".join(quality["registered_without_results"]) + ". Recomenda-se verificar se é duplicidade, campanha reprogramada ou lacuna de consolidação.",
            }
        )
    if quality.get("results_without_quantitative"):
        findings.append(
            {
                "severity": "neutral",
                "title": "Uma campanha tem resultado apenas qualitativo",
                "text": "Campanha(s): " + ", ".join(quality["results_without_quantitative"]) + ". Ela entra no inventário de ocorrência, mas não deve compor CPUE.",
            }
        )

    latest_low = latest[
        (latest["riqueza"] < latest["riqueza_pos_mediana"])
        | (latest["CPUEn"] < latest["CPUEn_pos_mediana"])
    ]
    if not latest_low.empty:
        details = []
        for _, row in latest_low.iterrows():
            details.append(
                f"{row['empreendimento']}: S {_fmt_num(row['riqueza'], 0)} vs mediana {_fmt_num(row['riqueza_pos_mediana'], 0)}, "
                f"CPUEn {_fmt_num(row['CPUEn'], 1)} vs {_fmt_num(row['CPUEn_pos_mediana'], 1)}"
            )
        findings.append(
            {
                "severity": "warn",
                "title": "Última campanha não supera a referência pós em todos os eixos",
                "text": "; ".join(details) + ".",
            }
        )

    findings.append(
        {
            "severity": "neutral",
            "title": "Lacunas cadastrais limitam indicadores funcionais",
            "text": "Os campos migratório, guilda alimentar e sensibilidade ambiental não estão preenchidos para as 29 espécies do recorte. A avaliação funcional deve ser tratada como etapa futura.",
        }
    )
    return findings


def render_html(
    output_dir: Path,
    figures: dict[str, Path],
    df: pd.DataFrame,
    species: pd.DataFrame,
    quality: dict[str, Any],
    alpha: pd.DataFrame,
    coverage: pd.DataFrame,
    beta: pd.DataFrame,
    trends: pd.DataFrame,
    indicators: pd.DataFrame,
    post_pre: pd.DataFrame,
    latest: pd.DataFrame,
    indicator_score: pd.DataFrame,
    species_pressure: pd.DataFrame,
) -> str:
    generated_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    quant = df[df["tipo_amostragem"].eq("Quantitativa")]
    latest_campaign = str(alpha.loc[alpha["data_campanha"].idxmax(), "campanha"]) if not alpha.empty else "-"
    total_ind = float(quant["contagem"].sum())
    native_ind = float(quant.loc[quant["is_native"], "contagem"].sum())
    nonnative_ind = float(quant.loc[quant["is_nonnative"], "contagem"].sum())
    top3_total = float(species_pressure.head(3)["abundancia"].sum())
    top3_pct = top3_total / total_ind * 100.0 if total_ind else np.nan

    findings = build_findings(quality, alpha, trends, species_pressure, latest)

    campaign_quality = pd.DataFrame(
        [
            {
                "métrica": "Campanhas cadastradas em pontos_coleta",
                "valor": len(quality["registered_campaigns"]),
                "observação": ", ".join(quality.get("registered_without_results") or ["sem lacuna de cadastro sem resultado"]),
            },
            {
                "métrica": "Campanhas com resultado de ictiofauna",
                "valor": len(quality["result_campaigns"]),
                "observação": "inclui quantitativas e qualitativas",
            },
            {
                "métrica": "Campanhas quantitativas para CPUE",
                "valor": len(quality["quantitative_campaigns"]),
                "observação": ", ".join(quality.get("results_without_quantitative") or ["todas com quantitativo"]),
            },
            {
                "métrica": "Registros consolidados",
                "valor": len(df),
                "observação": "biota_analise_consolidada",
            },
            {
                "métrica": "Espécies no recorte",
                "valor": df["nome_cientifico"].nunique(),
                "observação": "29 táxons no recorte total",
            },
        ]
    )

    latest_table = latest.copy()
    latest_table["empreendimento"] = latest_table["empreendimento"].astype(str)
    latest_table = latest_table.sort_values("empreendimento", key=lambda s: s.map({v: i for i, v in enumerate(EMP_ORDER)}))

    species_top = species_pressure.head(12).copy()
    species_top["tipo"] = np.where(species_top["nao_nativa"], "Não nativa", np.where(species_top["ameacada"], "Ameaçada", "Nativa"))

    css = """
    :root {
      --ink: #1f2933;
      --muted: #5f6b76;
      --line: #d8dee6;
      --paper: #ffffff;
      --soft: #f4f6f8;
      --ok: #2f855a;
      --warn: #b7791f;
      --bad: #b83232;
      --blue: #24537a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: #eef2f5;
      line-height: 1.5;
    }
    .shell { max-width: 1220px; margin: 0 auto; background: var(--paper); min-height: 100vh; }
    header { padding: 28px 34px 20px; border-bottom: 1px solid var(--line); }
    .eyebrow { color: var(--blue); font-weight: 700; text-transform: uppercase; letter-spacing: .04em; font-size: 12px; }
    h1 { margin: 6px 0 8px; font-size: 30px; line-height: 1.15; letter-spacing: 0; }
    h2 { margin: 34px 0 12px; font-size: 22px; color: var(--blue); border-bottom: 1px solid var(--line); padding-bottom: 6px; }
    h3 { margin: 18px 0 8px; font-size: 16px; }
    p { margin: 0 0 10px; }
    .meta { color: var(--muted); font-size: 13px; }
    .content { padding: 22px 34px 42px; }
    .kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 18px; }
    .kpi, .score-card, .finding, .note { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fff; }
    .kpi span { display: block; color: var(--muted); font-size: 12px; }
    .kpi strong { display: block; font-size: 24px; margin-top: 3px; }
    .verdict { border-left: 5px solid var(--bad); background: #fff7f7; padding: 14px 16px; margin: 18px 0; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .score-card.ok { border-top: 4px solid var(--ok); }
    .score-card.warn { border-top: 4px solid var(--warn); }
    .score-card.bad { border-top: 4px solid var(--bad); }
    .card-title { font-weight: 700; }
    .score { font-size: 23px; font-weight: 800; margin: 6px 0 2px; }
    .muted { color: var(--muted); font-size: 13px; }
    .mini-line { display: flex; flex-wrap: wrap; gap: 8px; color: var(--muted); font-size: 12px; margin-top: 8px; }
    .finding { margin-bottom: 10px; }
    .finding.bad { border-left: 5px solid var(--bad); }
    .finding.warn { border-left: 5px solid var(--warn); }
    .finding.neutral { border-left: 5px solid #718096; }
    .finding h3 { margin-top: 0; }
    figure { margin: 12px 0 22px; }
    figure img { width: 100%; height: auto; border: 1px solid var(--line); border-radius: 6px; background: #fff; }
    figcaption { color: var(--muted); font-size: 12px; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0 20px; font-size: 13px; }
    th, td { border: 1px solid var(--line); padding: 7px 8px; vertical-align: top; }
    th { background: var(--soft); text-align: left; color: #243b53; }
    .pill { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .pill.ok { background: #e6f4ea; color: var(--ok); }
    .pill.warn { background: #fff4d6; color: var(--warn); }
    .pill.bad { background: #fde8e8; color: var(--bad); }
    .pill.neutral { background: #edf2f7; color: #4a5568; }
    .indicator-table td:nth-child(3) { white-space: nowrap; }
    .small { font-size: 12px; color: var(--muted); }
    .refs { background: var(--soft); padding: 12px 14px; border-radius: 8px; color: var(--muted); font-size: 12px; }
    @media (max-width: 900px) {
      .kpis, .grid-4, .grid-2 { grid-template-columns: 1fr; }
      header, .content { padding-left: 18px; padding-right: 18px; }
      h1 { font-size: 24px; }
    }
    """

    indicator_rows = []
    for _, row in indicators.iterrows():
        status = str(row["status"])
        indicator_rows.append(
            "<tr>"
            f"<td>{escape(str(row['empreendimento']))}</td>"
            f"<td>{escape(str(row['indicador']))}</td>"
            f"<td><span class='pill {_status_class(status)}'>{escape(status)}</span></td>"
            f"<td>{escape(str(row['evidencia']))}</td>"
            "</tr>"
        )

    finding_html = "\n".join(
        f"""
        <article class="finding {item['severity']}">
          <h3>{escape(item['title'])}</h3>
          <p>{item['text']}</p>
        </article>
        """
        for item in findings
    )

    figure_html = "\n".join(
        f"""
        <figure>
          <img src="{_img_data_uri(path)}" alt="{escape(title)}">
          <figcaption>{escape(title)}</figcaption>
        </figure>
        """
        for title, path in [
            ("Indicadores temporais: riqueza, CPUEn, Shannon e não nativas", figures["timeline"]),
            ("Semáforo dos indicadores ambientais por empreendimento", figures["heatmap"]),
            ("Última campanha frente à mediana pós-2017", figures["latest"]),
            ("Composição dominante e pressão de espécies não nativas", figures["species"]),
            ("β-diversidade temporal e gradiente da cascata", figures["beta_cascade"]),
            ("Suficiência amostral pós-2017", figures["coverage"]),
        ]
    )

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ITAGUA001 - Dashboard ambiental de ictiofauna</title>
  <style>{css}</style>
</head>
<body>
<main class="shell">
  <header>
    <div class="eyebrow">ITAGUA001 | Guanhães Energia | Ictiofauna</div>
    <h1>Dashboard crítico de performance ambiental da ictiofauna</h1>
    <p class="meta">Gerado em {escape(generated_at)} a partir de <code>biota_analise_consolidada</code> e tabelas de lastro do Supabase. Corte Pré/Pós: 2017-07-01.</p>
    <section class="kpis">
      <div class="kpi"><span>Campanhas cadastradas</span><strong>{len(quality["registered_campaigns"])}</strong></div>
      <div class="kpi"><span>Com resultado ictio</span><strong>{len(quality["result_campaigns"])}</strong></div>
      <div class="kpi"><span>Quantitativas para CPUE</span><strong>{len(quality["quantitative_campaigns"])}</strong></div>
      <div class="kpi"><span>Registros consolidados</span><strong>{_fmt_int(len(df))}</strong></div>
      <div class="kpi"><span>Espécies</span><strong>{_fmt_int(df["nome_cientifico"].nunique())}</strong></div>
    </section>
  </header>

  <section class="content">
    <div class="verdict">
      <h2 style="margin-top:0;border:0;padding:0">Conclusão objetiva</h2>
      <p><strong>Os indicadores ambientais não sustentam uma conclusão de alcance pleno.</strong> O resultado é parcial: a comunidade permanece majoritariamente nativa ({_fmt_pct(native_ind / total_ind * 100.0 if total_ind else np.nan, 1)} dos indivíduos quantitativos), mas há queda significativa de CPUEn no período pós-2017, sinais de reorganização temporal e aumento de não nativas em parte dos empreendimentos.</p>
      <p>Em termos de comunicação ao cliente: a série é robusta e informativa, porém ainda aponta <strong>atenção ecológica</strong>, não estabilidade consolidada para redução ampla de esforço.</p>
    </div>

    <h2>1. Semáforo executivo</h2>
    <div class="grid-4">{_indicator_cards(indicator_score)}</div>

    <h2>2. Achados críticos</h2>
    <div class="grid-2">{finding_html}</div>

    <h2>3. Painéis visuais</h2>
    {figure_html}

    <h2>4. Auditoria rápida do banco</h2>
    {_table_html(campaign_quality, ["métrica", "valor", "observação"], ["Métrica", "Valor", "Observação"])}

    <h2>5. Indicadores por empreendimento</h2>
    <table class="indicator-table">
      <thead><tr><th>Empreendimento</th><th>Indicador</th><th>Status</th><th>Evidência</th></tr></thead>
      <tbody>{''.join(indicator_rows)}</tbody>
    </table>

    <h2>6. Última campanha ({escape(latest_campaign)})</h2>
    {_table_html(
        latest_table,
        ["empreendimento", "riqueza", "riqueza_pos_mediana", "CPUEn", "CPUEn_pos_mediana", "nao_nativas_pct", "nao_nativas_pos_mediana_pct"],
        ["Empreendimento", "S atual", "S mediana pós", "CPUEn atual", "CPUEn mediana pós", "Não nativas atual", "Não nativas mediana pós"],
        {
            "riqueza": lambda v: _fmt_num(v, 0),
            "riqueza_pos_mediana": lambda v: _fmt_num(v, 0),
            "CPUEn": lambda v: _fmt_num(v, 1),
            "CPUEn_pos_mediana": lambda v: _fmt_num(v, 1),
            "nao_nativas_pct": lambda v: _fmt_pct(v, 1),
            "nao_nativas_pos_mediana_pct": lambda v: _fmt_pct(v, 1),
        },
    )}

    <h2>7. Síntese Pré/Pós</h2>
    {_table_html(
        post_pre.sort_values(["empreendimento", "fase"], key=lambda s: s.astype(str)),
        ["empreendimento", "fase", "campanhas", "riqueza_mediana", "shannon_mediana", "CPUEn_mediana", "nao_nativas_mediana_pct", "top3_mediana_pct"],
        ["Empreendimento", "Fase", "Campanhas", "S mediana", "Shannon mediana", "CPUEn mediana", "Não nativas mediana", "Top 3 mediana"],
        {
            "campanhas": _fmt_int,
            "riqueza_mediana": lambda v: _fmt_num(v, 0),
            "shannon_mediana": lambda v: _fmt_num(v, 2),
            "CPUEn_mediana": lambda v: _fmt_num(v, 1),
            "nao_nativas_mediana_pct": lambda v: _fmt_pct(v, 1),
            "top3_mediana_pct": lambda v: _fmt_pct(v, 1),
        },
    )}

    <h2>8. Espécies sentinelas e pressão de dominância</h2>
    <p>As três espécies mais abundantes respondem por {_fmt_pct(top3_pct, 1)} dos indivíduos quantitativos. Dominância alta não é automaticamente negativa, mas reduz a margem para interpretar riqueza e abundância como estabilidade ecológica ampla.</p>
    {_table_html(
        species_top,
        ["nome_cientifico", "tipo", "origem", "abundancia", "campanhas", "empreendimentos"],
        ["Espécie", "Tipo", "Origem", "Indivíduos", "Campanhas", "Empreendimentos"],
        {"abundancia": _fmt_int, "campanhas": _fmt_int, "empreendimentos": _fmt_int},
    )}

    <h2>9. Recomendações objetivas</h2>
    <div class="note">
      <p><strong>1.</strong> Não recomendar redução ampla do esforço apenas com a evidência atual. A decisão pode ser discutida por empreendimento, com Jacaré em posição relativamente melhor, mas ainda com alerta para não nativas.</p>
      <p><strong>2.</strong> Tratar <code>C028-2026-04-SC</code> e <code>C028-2026-05-SC</code> como ponto de auditoria: uma está cadastrada sem resultado e a outra concentra a última campanha efetiva.</p>
      <p><strong>3.</strong> Completar cadastro funcional das espécies: migratório, guilda alimentar, sensibilidade ambiental e habitat. Sem isso, a performance funcional fica subavaliada.</p>
      <p><strong>4.</strong> Monitorar especificamente <i>Cichla kelberi</i>, <i>Coptodon rendalli</i>, <i>Oreochromis niloticus</i> e demais não nativas, principalmente onde a tendência pós-2017 é crescente.</p>
      <p><strong>5.</strong> Manter leitura espacial da cascata Jacaré → Senhora do Porto → Dores de Guanhães; o gradiente sugere reorganização longitudinal e deve ser interpretado separadamente de Fortuna II.</p>
    </div>

    <h2>10. Limitações declaradas</h2>
    <div class="refs">
      A análise usa a base consolidada disponível no banco em {escape(generated_at)}. CPUE foi calculada somente para registros quantitativos. Campanhas qualitativas compõem o inventário, mas não os indicadores de esforço. Os indicadores funcionais de migração/guilda/sensibilidade não foram calculados por ausência de preenchimento cadastral no recorte. Os limiares de semáforo são exploratórios e devem ser formalizados como meta contratual se o cliente desejar acompanhamento por SLA ambiental.
    </div>

    <p class="small">Arquivos de apoio salvos em: <code>{escape(str(output_dir))}</code></p>
  </section>
</main>
</body>
</html>
"""
    return html


def write_outputs(
    output_dir: Path,
    df: pd.DataFrame,
    species: pd.DataFrame,
    quality: dict[str, Any],
    alpha: pd.DataFrame,
    coverage: pd.DataFrame,
    beta: pd.DataFrame,
    trends: pd.DataFrame,
    indicators: pd.DataFrame,
    post_pre: pd.DataFrame,
    latest: pd.DataFrame,
    indicator_score: pd.DataFrame,
    species_pressure: pd.DataFrame,
    html: str,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "dashboard_performance_ambiental_ictiofauna_itagua001.html"
    html_path.write_text(html, encoding="utf-8")

    xlsx_path = output_dir / "dados_dashboard_performance_ambiental_ictiofauna_itagua001.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        alpha.to_excel(writer, sheet_name="alpha_campanha", index=False)
        coverage.to_excel(writer, sheet_name="suficiencia", index=False)
        beta.to_excel(writer, sheet_name="beta_consecutiva", index=False)
        trends.to_excel(writer, sheet_name="tendencias_pos", index=False)
        indicators.to_excel(writer, sheet_name="semaforo", index=False)
        post_pre.to_excel(writer, sheet_name="pre_pos", index=False)
        latest.to_excel(writer, sheet_name="ultima_campanha", index=False)
        indicator_score.to_excel(writer, sheet_name="score_emp", index=False)
        species_pressure.to_excel(writer, sheet_name="especies_pressao", index=False)
        pd.DataFrame(
            [
                {"classe": "registered_campaigns", "campanha": c}
                for c in quality["registered_campaigns"]
            ]
            + [{"classe": "result_campaigns", "campanha": c} for c in quality["result_campaigns"]]
            + [{"classe": "quantitative_campaigns", "campanha": c} for c in quality["quantitative_campaigns"]]
        ).to_excel(writer, sheet_name="campanhas", index=False)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": PROJECT_ID,
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "outputs": {
            "html": str(html_path),
            "xlsx": str(xlsx_path),
        },
        "counts": {
            "rows_total": int(len(df)),
            "species": int(df["nome_cientifico"].nunique()),
            "registered_campaigns": int(len(quality["registered_campaigns"])),
            "result_campaigns": int(len(quality["result_campaigns"])),
            "quantitative_campaigns": int(len(quality["quantitative_campaigns"])),
        },
        "quality_flags": {
            "registered_without_results": quality.get("registered_without_results", []),
            "results_without_quantitative": quality.get("results_without_quantitative", []),
        },
    }
    manifest_path = output_dir / "manifesto_dashboard_performance_ambiental_ictiofauna_itagua001.json"
    manifest["outputs"]["manifest"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return html_path, xlsx_path, manifest_path


def run(env_file: str | None, output_dir: Path) -> tuple[Path, Path, Path]:
    df, species, quality = load_data(env_file)
    alpha = build_alpha(df)
    coverage = build_coverage(df)
    beta = build_beta(df)
    trends = build_trends(alpha, beta)
    indicators = build_indicator_table(alpha, coverage, beta, trends)
    post_pre, latest, indicator_score, species_pressure = build_summary_tables(df, alpha, beta, indicators)

    assets = output_dir / "assets"
    figures = {
        "timeline": plot_timeline(alpha, assets),
        "heatmap": plot_indicator_heatmap(indicators, assets),
        "latest": plot_latest_vs_median(latest, assets),
        "species": plot_species_pressure(df, alpha, assets),
        "beta_cascade": plot_beta_cascade(alpha, beta, assets),
        "coverage": plot_coverage(coverage, assets),
    }
    html = render_html(
        output_dir,
        figures,
        df,
        species,
        quality,
        alpha,
        coverage,
        beta,
        trends,
        indicators,
        post_pre,
        latest,
        indicator_score,
        species_pressure,
    )
    return write_outputs(
        output_dir,
        df,
        species,
        quality,
        alpha,
        coverage,
        beta,
        trends,
        indicators,
        post_pre,
        latest,
        indicator_score,
        species_pressure,
        html,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera dashboard HTML de performance ambiental da ictiofauna ITAGUA001.")
    parser.add_argument("--env-file", default=str(EXTERNAL_ENV if EXTERNAL_ENV.exists() else REPO_ROOT / ".env"))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    html_path, xlsx_path, manifest_path = run(args.env_file, Path(args.output_dir))
    print(f"html={html_path}")
    print(f"xlsx={xlsx_path}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
