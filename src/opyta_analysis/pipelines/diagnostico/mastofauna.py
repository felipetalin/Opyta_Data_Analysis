from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyBboxPatch, Patch
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import (
    apply_theme,
    get_figsize_by_complexity,
    get_tight_layout_rect,
    green_palette_from_hex,
    place_legend_below_x_axis,
)
from opyta_analysis.validators import validate_axes_style


TARGET_PCH_NAME = "Dores de Guanhaes"
TARGET_CONTROL_NAME = "Area Controle"


def _norm(value: object) -> str:
    txt = str(value or "").strip().lower()
    txt = txt.replace("á", "a").replace("ã", "a").replace("â", "a")
    txt = txt.replace("é", "e").replace("ê", "e")
    txt = txt.replace("í", "i")
    txt = txt.replace("ó", "o").replace("õ", "o").replace("ô", "o")
    txt = txt.replace("ú", "u")
    txt = txt.replace("ç", "c")
    txt = re.sub(r"\s+", " ", txt)
    return txt


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


def _is_primata(row: pd.Series) -> bool:
    ordem = _norm(row.get("ordem"))
    if ordem == "primates":
        return True
    sci = _norm(row.get("nome_cientifico"))
    return bool(re.search(r"(callithrix|callicebus|cebus|alouatta|sapajus|saimiri)", sci))


def _shannon(counts: np.ndarray) -> float:
    c = np.asarray(counts, dtype=float)
    c = c[c > 0]
    if c.size == 0:
        return 0.0
    p = c / c.sum()
    return float(-np.sum(p * np.log(p)))


def _simpson_1_d(counts: np.ndarray) -> float:
    c = np.asarray(counts, dtype=float)
    c = c[c > 0]
    if c.size == 0:
        return 0.0
    p = c / c.sum()
    return float(1.0 - np.sum(p**2))


def _pielou(counts: np.ndarray) -> float:
    c = np.asarray(counts, dtype=float)
    c = c[c > 0]
    if c.size <= 1:
        return 0.0
    return float(_shannon(c) / np.log(c.size))


def _jackknife_1(pa_matrix: np.ndarray) -> float:
    k = int(pa_matrix.shape[0])
    if k == 0:
        return 0.0
    spp_occ = pa_matrix.sum(axis=0)
    s_obs = int((spp_occ > 0).sum())
    q1 = int((spp_occ == 1).sum())
    return float(s_obs + q1 * ((k - 1) / k))


def _bootstrap_richness(pa_matrix: np.ndarray) -> float:
    if pa_matrix.size == 0:
        return 0.0
    s_obs = int((pa_matrix.sum(axis=0) > 0).sum())
    n = pa_matrix.shape[0]
    if n <= 0:
        return float(s_obs)
    pj = pa_matrix.sum(axis=0) / n
    unseen_prob = (1 - pj) ** n
    return float(s_obs + np.sum(unseen_prob))


def _load_mastofauna_df(project_id: int, env_file: Optional[str]) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    empreendimentos = paginate(sb, "empreendimentos", filters={"id_projeto": int(project_id)}, select="id_empreendimento,nome")
    emp_map = {e["id_empreendimento"]: e["nome"] for e in empreendimentos}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Mastofauna"},
        select="id_esforco,id_ponto_coleta,metodo_de_captura,tipo_amostragem,tipo_de_amostragem,esforco,unidade_esforco",
    )
    esforcos = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos:
        return pd.DataFrame()

    esforco_map = {e["id_esforco"]: e for e in esforcos}
    esforco_ids = set(esforco_map.keys())

    resultados = paginate(
        sb,
        "resultados_mastofauna",
        select="id_esforco,id_especie,numero_de_individuos,tipo_amostragem,observacoes",
    )
    resultados = [r for r in resultados if r.get("id_esforco") in esforco_ids]
    if not resultados:
        return pd.DataFrame()

    especies = paginate(
        sb,
        "especies",
        select="id_especie,nome_cientifico,nome_popular,ordem,familia,status_ameaca_global,status_ameaca_nacional,status_copam,cites,dependencia_florestal,endemismo,habito_alimentar,guilda_alimentar,sensibilidade_ambiental,migratorio,raridade,origem,observacoes",
    )
    esp_map = {e["id_especie"]: e for e in especies}

    rows: list[dict[str, Any]] = []
    for r in resultados:
        esf = esforco_map.get(r.get("id_esforco"), {})
        ponto = pontos_map.get(esf.get("id_ponto_coleta"), {})
        esp = esp_map.get(r.get("id_especie"), {})
        id_emp = ponto.get("id_empreendimento")
        rows.append(
            {
                "nome_campanha": camp_map.get(ponto.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": ponto.get("nome_ponto"),
                "empreendimento": emp_map.get(id_emp, "Sem empreendimento"),
                "nome_cientifico": esp.get("nome_cientifico"),
                "nome_popular": esp.get("nome_popular"),
                "ordem": esp.get("ordem"),
                "familia": esp.get("familia"),
                "status_ameaca_global": esp.get("status_ameaca_global"),
                "status_ameaca_nacional": esp.get("status_ameaca_nacional"),
                "status_copam": esp.get("status_copam"),
                "cites": esp.get("cites"),
                "dependencia_florestal": esp.get("dependencia_florestal"),
                "endemismo": esp.get("endemismo"),
                "habito_alimentar": esp.get("habito_alimentar"),
                "guilda_alimentar": esp.get("guilda_alimentar"),
                "sensibilidade_ambiental": esp.get("sensibilidade_ambiental"),
                "migratorio": esp.get("migratorio"),
                "raridade": esp.get("raridade"),
                "origem": esp.get("origem"),
                "especie_obs": esp.get("observacoes"),
                "metodo_de_captura": esf.get("metodo_de_captura"),
                "tipo_amostragem": r.get("tipo_amostragem") or esf.get("tipo_amostragem") or esf.get("tipo_de_amostragem"),
                "id_esforco": esf.get("id_esforco"),
                "esforco": esf.get("esforco"),
                "unidade_esforco": esf.get("unidade_esforco"),
                "contagem": r.get("numero_de_individuos"),
                "obs_resultado": r.get("observacoes"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for c in ["nome_campanha", "nome_ponto", "empreendimento", "nome_cientifico", "nome_popular", "ordem", "familia"]:
        df[c] = df[c].astype(str).str.strip()
    df["id_esforco"] = pd.to_numeric(df["id_esforco"], errors="coerce").fillna(-1).astype(int)
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    df["esforco"] = pd.to_numeric(df["esforco"], errors="coerce")
    return df


def _load_sampling_units_df(project_id: int, env_file: Optional[str]) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    empreendimentos = paginate(sb, "empreendimentos", filters={"id_projeto": int(project_id)}, select="id_empreendimento,nome")
    emp_map = {e["id_empreendimento"]: e["nome"] for e in empreendimentos}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Mastofauna"},
        select="id_esforco,id_ponto_coleta,esforco,unidade_esforco",
    )
    esforcos = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for esf in esforcos:
        ponto = pontos_map.get(esf.get("id_ponto_coleta"), {})
        id_emp = ponto.get("id_empreendimento")
        rows.append(
            {
                "id_esforco": esf.get("id_esforco"),
                "nome_campanha": camp_map.get(ponto.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": ponto.get("nome_ponto"),
                "empreendimento": emp_map.get(id_emp, "Sem empreendimento"),
                "esforco": esf.get("esforco"),
                "unidade_esforco": esf.get("unidade_esforco"),
            }
        )

    df_units = pd.DataFrame(rows)
    if df_units.empty:
        return df_units

    for c in ["nome_campanha", "nome_ponto", "empreendimento"]:
        df_units[c] = df_units[c].astype(str).str.strip()
    df_units["id_esforco"] = pd.to_numeric(df_units["id_esforco"], errors="coerce").fillna(-1).astype(int)
    df_units["esforco"] = pd.to_numeric(df_units["esforco"], errors="coerce")
    return df_units


def _subset_by_empreendimento(df: pd.DataFrame, empreendimento_norm: str) -> pd.DataFrame:
    return df[df["empreendimento"].map(_norm) == _norm(empreendimento_norm)].copy()


def _build_species_list(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "Ordem",
                "Familia",
                "Especie",
                "Nome popular",
                "IUCN (2025)",
                "MMA (2022)",
                "COPAM (2010)",
                "Habito alimentar",
                "CITES (2025)",
                "Dependencia florestal",
                "Endemico",
            ]
        )

    table = (
        df.groupby("nome_cientifico", as_index=False)
        .agg(
            ordem=("ordem", "first"),
            familia=("familia", "first"),
            nome_popular=("nome_popular", "first"),
            iucn=("status_ameaca_global", "first"),
            mma=("status_ameaca_nacional", "first"),
            copam=("status_copam", "first"),
            habito=("habito_alimentar", "first"),
            cites=("cites", "first"),
            dependencia_florestal=("dependencia_florestal", "first"),
            endemismo=("endemismo", "first"),
        )
        .sort_values(["ordem", "familia", "nome_cientifico"], na_position="last")
        .reset_index(drop=True)
    )

    table = table.rename(
        columns={
            "ordem": "Ordem",
            "familia": "Familia",
            "nome_cientifico": "Especie",
            "nome_popular": "Nome popular",
            "iucn": "IUCN (2025)",
            "mma": "MMA (2022)",
            "copam": "COPAM (2010)",
            "habito": "Habito alimentar",
            "cites": "CITES (2025)",
            "dependencia_florestal": "Dependencia florestal",
            "endemismo": "Endemico",
        }
    )
    for col in [
        "IUCN (2025)",
        "MMA (2022)",
        "COPAM (2010)",
        "Habito alimentar",
        "CITES (2025)",
        "Dependencia florestal",
        "Endemico",
    ]:
        table[col] = table[col].replace({None: "-", "": "-"}).fillna("-")
    return table[
        [
            "Ordem",
            "Familia",
            "Especie",
            "Nome popular",
            "IUCN (2025)",
            "MMA (2022)",
            "COPAM (2010)",
            "Habito alimentar",
            "CITES (2025)",
            "Dependencia florestal",
            "Endemico",
        ]
    ]


def _save_abundance_figures(df_area: pd.DataFrame, theme: dict, output_png: Path) -> dict[str, float]:
    grouped = (
        df_area.groupby("nome_cientifico", as_index=False)["contagem"]
        .sum()
        .sort_values("contagem", ascending=False)
        .reset_index(drop=True)
    )
    grouped["abund_relativa_pct"] = grouped["contagem"] / grouped["contagem"].sum() * 100 if not grouped.empty else 0.0

    size = get_figsize_by_complexity(theme, n_categories=max(len(grouped), 1), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    ax_total = ax.twiny()

    y = np.arange(len(grouped))
    rel_color = str(theme.get("primary_hex", "#2E6F95"))
    total_color = str(theme.get("secondary_hex", "#E07A5F"))

    # Barras lado a lado (verticalmente deslocadas) para evitar qualquer sobreposição.
    y_rel = y - 0.19
    y_total = y + 0.19

    bars_rel = ax.barh(
        y_rel,
        grouped["abund_relativa_pct"].values,
        height=0.30,
        color=rel_color,
        edgecolor="black",
        linewidth=0.8,
        zorder=2,
    )
    bars_total = ax_total.barh(
        y_total,
        grouped["contagem"].values,
        height=0.30,
        color=total_color,
        edgecolor="black",
        linewidth=0.7,
        alpha=0.75,
        zorder=3,
    )

    scientific_labels = [str(v) for v in grouped["nome_cientifico"].tolist()]
    ax.set_yticks(y)
    ax.set_yticklabels(scientific_labels, fontstyle="italic")
    ax.invert_yaxis()

    max_rel = float(grouped["abund_relativa_pct"].max()) if not grouped.empty else 0.0
    max_tot = float(grouped["contagem"].max()) if not grouped.empty else 0.0
    ax.set_xlim(0, max(100.0, max_rel * 1.15, 1.0))
    ax_total.set_xlim(0, max(max_tot * 1.20, 1.0))

    apply_theme(ax, theme, xlabel="Abundância relativa (%)", ylabel="Espécie")
    ax_total.set_xlabel("Abundância total (N)")
    ax_total.tick_params(axis="x", direction=str(theme.get("tick_direction", "out")))
    ax_total.grid(False)
    ax_total.spines["top"].set_visible(True)
    ax_total.spines["top"].set_color(str(theme.get("spine_color", "#000000")))
    ax_total.spines["top"].set_linewidth(float(theme.get("spine_linewidth", 1.2)))
    for side in ["left", "right", "bottom"]:
        ax_total.spines[side].set_visible(False)

    for bar, pct in zip(bars_rel, grouped["abund_relativa_pct"].values):
        pct_text = f"{pct:.0f}%" if abs(pct - round(pct)) < 1e-6 else f"{pct:.1f}%"
        ax.text(
            float(bar.get_width()) + 0.6,
            bar.get_y() + bar.get_height() / 2,
            pct_text,
            ha="left",
            va="center",
            fontsize=int(theme.get("annotation_size", 14)),
        )

    for bar, total_n in zip(bars_total, grouped["contagem"].values):
        ax_total.text(
            float(bar.get_width()) + max(0.02 * max_tot, 0.1),
            bar.get_y() + bar.get_height() / 2,
            f"N={int(total_n)}",
            ha="left",
            va="center",
            fontsize=int(theme.get("annotation_size", 14)),
        )

    handles = [
        Patch(facecolor=rel_color, edgecolor="black", label="Abundância relativa (%)"),
        Patch(facecolor=total_color, edgecolor="black", label="Abundância total (N)"),
    ]
    place_legend_below_x_axis(
        fig,
        ax,
        theme,
        handles=handles,
        labels=[h.get_label() for h in handles],
        ncol=2,
    )

    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.02))
    fig.savefig(output_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)

    return {
        "riqueza_observada": float(grouped["nome_cientifico"].nunique()),
        "abundancia_total": float(grouped["contagem"].sum()),
    }


def _save_estimators_and_curve(
    df_area: pd.DataFrame,
    area_slug: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
    sampling_units_df: Optional[pd.DataFrame] = None,
) -> dict[str, float]:
    samples = (
        df_area.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], as_index=False)["contagem"]
        .sum()
    )
    if samples.empty and (sampling_units_df is None or sampling_units_df.empty):
        est = pd.DataFrame(
            [
                {
                    "Area": area_slug,
                    "Riqueza observada": 0,
                    "Abundancia": 0,
                    "Jackknife 1 estimada": 0.0,
                    "Completude Jackknife 1 (%)": 0.0,
                    "Bootstrap estimada": 0.0,
                    "Completude Bootstrap (%)": 0.0,
                }
            ]
        )
        out_est = output_dir / f"6_2_tabela_estimadores_{area_slug}.xlsx"
        est.to_excel(out_est, index=False, engine="openpyxl")
        generated_files.append(str(out_est))
        return {"sobs": 0.0, "jack1": 0.0, "boot": 0.0}

    mat_obs = samples.pivot_table(index="nome_ponto", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0)

    point_meta: pd.DataFrame
    if sampling_units_df is not None and not sampling_units_df.empty:
        point_meta = (
            sampling_units_df.groupby(["nome_campanha", "nome_ponto"], as_index=False)
            .agg(id_esforco=("id_esforco", "min"))
            .sort_values(["nome_campanha", "id_esforco", "nome_ponto"])
            .reset_index(drop=True)
        )
    else:
        point_meta = (
            samples[["nome_campanha", "nome_ponto"]]
            .drop_duplicates()
            .sort_values(["nome_campanha", "nome_ponto"])
            .reset_index(drop=True)
        )

    ordered_points = point_meta["nome_ponto"].astype(str).tolist()
    if mat_obs.empty:
        mat = pd.DataFrame(index=ordered_points)
    else:
        mat = mat_obs.reindex(index=ordered_points, fill_value=0)

    pa = (mat > 0).astype(int)

    sobs = float((pa.sum(axis=0) > 0).sum())
    abundance = float(mat.sum().sum())
    jack1 = float(_jackknife_1(pa.values))
    boot = float(_bootstrap_richness(pa.values))

    est = pd.DataFrame(
        [
            {
                "Area": area_slug,
                "Riqueza observada": int(sobs),
                "Abundancia": int(abundance),
                "Jackknife 1 estimada": round(jack1, 2),
                "Completude Jackknife 1 (%)": round((sobs / jack1) * 100, 2) if jack1 > 0 else 0.0,
                "Bootstrap estimada": round(boot, 2),
                "Completude Bootstrap (%)": round((sobs / boot) * 100, 2) if boot > 0 else 0.0,
            }
        ]
    )
    out_est = output_dir / f"6_2_tabela_estimadores_{area_slug}.xlsx"
    est.to_excel(out_est, index=False, engine="openpyxl")
    generated_files.append(str(out_est))

    n_samples = int(pa.shape[0])
    if n_samples == 0:
        n_samples = 1
        values = np.zeros((1, pa.shape[1] if pa.shape[1] > 0 else 1), dtype=int)
    else:
        values = pa.values

    n_random = 200
    rng = np.random.default_rng(42)
    sobs_curves = np.zeros((n_random, n_samples), dtype=float)
    jack_curves = np.zeros((n_random, n_samples), dtype=float)

    for r in range(n_random):
        idx = rng.permutation(n_samples)
        shuffled = values[idx, :]
        for i in range(1, n_samples + 1):
            subset = shuffled[:i, :]
            spp_occ = subset.sum(axis=0)
            sobs_curves[r, i - 1] = float((spp_occ > 0).sum())
            jack_curves[r, i - 1] = _jackknife_1(subset)

    mean_sobs = sobs_curves.mean(axis=0)
    mean_jack = jack_curves.mean(axis=0)
    std_jack = jack_curves.std(axis=0)
    x = np.arange(1, n_samples + 1)

    df_curve = pd.DataFrame(
        {
            "n_unidades_amostrais": x,
            "riqueza_obs_media": mean_sobs,
            "riqueza_jack1_media": mean_jack,
            "jack1_sd": std_jack,
            "jack1_inf": mean_jack - std_jack,
            "jack1_sup": mean_jack + std_jack,
        }
    )
    out_curve_xlsx = output_dir / f"6_2_curva_coletor_dados_{area_slug}.xlsx"
    df_curve.to_excel(out_curve_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_curve_xlsx))

    size = get_figsize_by_complexity(theme, n_categories=n_samples, prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    obs_color = str(theme.get("primary_hex", "#11420C"))
    est_color = str(theme.get("secondary_hex", "#6A8F63"))
    ax.plot(x, mean_sobs, linewidth=2.2, label="Riqueza observada", color=obs_color)
    ax.plot(x, mean_jack, linewidth=2.2, label="Riqueza estimada (Jackknife 1)", color=est_color)
    ax.fill_between(x, mean_jack - std_jack, mean_jack + std_jack, alpha=0.18, color=est_color)
    apply_theme(ax, theme, xlabel="Numero de unidades amostrais", ylabel="Riqueza")

    ax.text(
        x[-1] + 0.15,
        mean_sobs[-1],
        f"{mean_sobs[-1]:.0f}",
        color="black",
        va="center",
        fontsize=int(theme.get("annotation_size", 14)),
    )
    ax.text(
        x[-1] + 0.15,
        mean_jack[-1],
        f"{mean_jack[-1]:.1f}",
        color="black",
        va="center",
        fontsize=int(theme.get("annotation_size", 14)),
    )

    place_legend_below_x_axis(fig, ax, theme, ncol=2)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.04))
    out_curve_png = output_dir / f"6_2_curva_coletor_{area_slug}.png"
    fig.savefig(out_curve_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_curve_png))

    return {"sobs": sobs, "jack1": jack1, "boot": boot}


def _save_diversity(df_pch: pd.DataFrame, df_control: pd.DataFrame, theme: dict, output_dir: Path, generated_files: list[str]) -> None:
    rows = []
    for label, frame in [(TARGET_PCH_NAME, df_pch), (TARGET_CONTROL_NAME, df_control)]:
        vec = frame.groupby("nome_cientifico")["contagem"].sum().values
        rows.append(
            {
                "Area": label,
                "Shannon (H')": _shannon(vec),
                "Pielou (J')": _pielou(vec),
                "Simpson (1-D)": _simpson_1_d(vec),
            }
        )
    div = pd.DataFrame(rows)
    out_xlsx = output_dir / "6_3_indices_diversidade.xlsx"
    div.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    size = get_figsize_by_complexity(theme, n_categories=2, prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(div))
    width = 0.25
    metrics = ["Shannon (H')", "Pielou (J')", "Simpson (1-D)"]
    colors = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), len(metrics))
    for i, metric in enumerate(metrics):
        vals = div[metric].values
        bars = ax.bar(x + (i - 1) * width, vals, width=width, label=metric, color=colors[i], edgecolor="black", linewidth=0.8)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, float(val), f"{val:.2f}", ha="center", va="bottom", fontsize=int(theme.get("annotation_size", 11)))
    ax.set_xticks(x)
    ax.set_xticklabels(div["Area"].tolist())
    apply_theme(ax, theme, xlabel="Area", ylabel="Indice", x_tick_rotation=0)
    place_legend_below_x_axis(fig, ax, theme, ncol=3)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.03))
    out_png = output_dir / "6_3_indices_diversidade.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


def _save_similarity_and_venn(df_pch: pd.DataFrame, df_control: pd.DataFrame, theme: dict, output_dir: Path, generated_files: list[str]) -> None:
    set_pch = set(df_pch["nome_cientifico"].dropna().astype(str).tolist())
    set_ctrl = set(df_control["nome_cientifico"].dropna().astype(str).tolist())
    inter = set_pch & set_ctrl
    union = set_pch | set_ctrl
    jacc = (len(inter) / len(union)) if union else 0.0

    table = pd.DataFrame(
        [
            {
                "Area A": TARGET_PCH_NAME,
                "Area B": TARGET_CONTROL_NAME,
                "Spp_A": len(set_pch),
                "Spp_B": len(set_ctrl),
                "Spp_intersecao": len(inter),
                "Jaccard": round(jacc, 4),
            }
        ]
    )
    out_xlsx = output_dir / "6_4_tabela_jaccard_pch_vs_controle.xlsx"
    table.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    # ===== DENDROGRAMA POR PONTOS AMOSTRAIS (Melhorado) =====
    df_all = pd.concat([df_pch.assign(area=TARGET_PCH_NAME), df_control.assign(area=TARGET_CONTROL_NAME)], ignore_index=True)
    
    # Criar matriz de presença/ausência por ponto amostral
    pontos_unicos = sorted(df_all["nome_ponto"].dropna().unique().tolist())
    todas_especies = sorted(union)
    
    pa_points = []
    ponto_area_map = {}
    
    for ponto in pontos_unicos:
        df_ponto = df_all[df_all["nome_ponto"] == ponto]
        area = df_ponto["area"].iloc[0] if len(df_ponto) > 0 else "Desconhecido"
        ponto_area_map[ponto] = area
        
        presence = [1 if spp in set(df_ponto["nome_cientifico"].dropna().tolist()) else 0 for spp in todas_especies]
        pa_points.append(presence)
    
    if len(pa_points) > 1:
        pa_mat = np.array(pa_points, dtype=float)
        dist_points = pdist(pa_mat, metric="jaccard")
        z_points = linkage(dist_points, method="average")

        # Exporta matriz de similaridade (Jaccard) ponto a ponto para Excel.
        sim_points = 1.0 - squareform(dist_points)
        np.fill_diagonal(sim_points, 1.0)
        sim_df = pd.DataFrame(sim_points, index=pontos_unicos, columns=pontos_unicos)
        sim_df.index.name = "Ponto"
        area_df = pd.DataFrame(
            {
                "Ponto": pontos_unicos,
                "Area": [ponto_area_map[p] for p in pontos_unicos],
            }
        )
        out_sim_matrix = output_dir / "6_4_matriz_similaridade_jaccard_por_pontos.xlsx"
        with pd.ExcelWriter(out_sim_matrix, engine="openpyxl") as writer:
            sim_df.to_excel(writer, sheet_name="Matriz Jaccard")
            area_df.to_excel(writer, sheet_name="Pontos e Areas", index=False)
        generated_files.append(str(out_sim_matrix))
        
        # Dendrograma com todos os pontos
        n_pts = len(pontos_unicos)
        fig_height = min(max(4 + n_pts * 0.4, 8), 16)
        fig, ax = plt.subplots(figsize=(12, fig_height), dpi=int(theme.get("dpi", 600)))
        
        dendro = dendrogram(z_points, labels=pontos_unicos, orientation="right", ax=ax, color_threshold=None)
        
        # Colorir labels dos pontos: azul para PCH, laranja para Controle
        color_pch = str(theme.get("primary_hex", "#1f77b4"))
        color_ctrl = str(theme.get("secondary_hex", "#ff7f0e"))
        
        yticklabels = ax.get_yticklabels()
        for i, label in enumerate(yticklabels):
            ponto_label = label.get_text()
            if ponto_label in ponto_area_map:
                color = color_pch if ponto_area_map[ponto_label] == TARGET_PCH_NAME else color_ctrl
                label.set_color(color)
                label.set_fontweight("bold")
        
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position("top")
        ax.set_xlim(1.0, 0.0)
        
        ticks_sim = np.arange(0, 101, 10)
        ticks_dist = 1 - (ticks_sim / 100.0)
        ax.set_xticks(ticks_dist)
        ax.set_xticklabels([str(t) for t in ticks_sim], fontsize=10)
        
        apply_theme(ax, theme, xlabel="Similaridade de Jaccard (%)", ylabel="Pontos Amostrais")
        validate_axes_style(ax, theme)
        
        # Legenda centralizada no topo (sem titulo)
        fig.text(0.495, 0.96, f"■ {TARGET_PCH_NAME}", ha="right", va="top", fontsize=11,
             fontweight="bold", color=color_pch)
        fig.text(0.5, 0.96, "|", ha="center", va="top", fontsize=11,
             fontweight="bold", color="black")
        fig.text(0.505, 0.96, f"■ {TARGET_CONTROL_NAME}", ha="left", va="top", fontsize=11,
             fontweight="bold", color=color_ctrl)
        
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        out_dendro_pts = output_dir / "6_4_dendrograma_jaccard_por_pontos.png"
        fig.savefig(out_dendro_pts, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_dendro_pts))
    
    # ===== DENDROGRAMA POR EMPREENDIMENTO (Mantido para compatibilidade) =====
    pa = pd.DataFrame(
        {
            "nome_cientifico": sorted(union),
            TARGET_PCH_NAME: [1 if s in set_pch else 0 for s in sorted(union)],
            TARGET_CONTROL_NAME: [1 if s in set_ctrl else 0 for s in sorted(union)],
        }
    )
    pa_mat = pa[[TARGET_PCH_NAME, TARGET_CONTROL_NAME]].T.values
    dist_cond = pdist(pa_mat, metric="jaccard")
    z = linkage(dist_cond, method="average")

    fig, ax = plt.subplots(figsize=get_figsize_by_complexity(theme, n_categories=2, prefer_landscape=True), dpi=int(theme.get("dpi", 600)))
    dendrogram(z, labels=[TARGET_PCH_NAME, TARGET_CONTROL_NAME], orientation="right", ax=ax, color_threshold=None)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.0, 0.0)
    ticks_sim = np.arange(0, 101, 10)
    ticks_dist = 1 - (ticks_sim / 100.0)
    ax.set_xticks(ticks_dist)
    ax.set_xticklabels([str(t) for t in ticks_sim])
    apply_theme(ax, theme, xlabel="Similaridade de Jaccard (%)", ylabel="")
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_dendro = output_dir / "6_4_dendrograma_jaccard_pch_vs_controle.png"
    fig.savefig(out_dendro, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_dendro))

    only_pch = len(set_pch - set_ctrl)
    only_ctrl = len(set_ctrl - set_pch)
    both = len(inter)
    fig, ax = plt.subplots(figsize=(11, 7.4), dpi=int(theme.get("dpi", 600)))

    pch_label = "PCH DGN"
    ctrl_label = "Área Controle"
    pch_color = str(theme.get("primary_hex", "#11420C"))
    ctrl_color = str(theme.get("secondary_hex", "#5B8E53"))
    dark_text = "#0D2A1D"

    # Círculos com sobreposição moderada e melhor equilíbrio visual.
    c1 = Circle((0.39, 0.67), 0.22, color=pch_color, alpha=0.24, ec="#0E3A22", lw=1.4)
    c2 = Circle((0.61, 0.67), 0.22, color=ctrl_color, alpha=0.22, ec="#4C8642", lw=1.4)
    ax.add_patch(c1)
    ax.add_patch(c2)

    # Sem título no gráfico: padrão técnico do projeto.

    # Valores e descrições internas com alinhamento vertical consistente.
    y_num = 0.69
    y_desc = 0.63
    ax.text(0.33, y_num, str(only_pch), ha="center", va="center", fontsize=32, fontweight="bold", color=dark_text)
    ax.text(0.33, y_desc, "Espécies\nexclusivas", ha="center", va="center", fontsize=13.2, color=dark_text)

    ax.text(0.50, y_num, str(both), ha="center", va="center", fontsize=34, fontweight="bold", color=dark_text)
    ax.text(0.50, y_desc, "Espécie\ncompartilhada" if both == 1 else "Espécies\ncompartilhadas", ha="center", va="center", fontsize=13.2, color=dark_text)

    ax.text(0.67, y_num, str(only_ctrl), ha="center", va="center", fontsize=32, fontweight="bold", color="#2F6A34")
    ax.text(0.67, y_desc, "Espécies\nexclusivas", ha="center", va="center", fontsize=13.2, color="#2F6A34")

    # Nomes das áreas com menor peso para não competir com os valores centrais.
    ax.plot([0.27, 0.35], [0.50, 0.50], color="#0E3A22", linewidth=1.8)
    ax.text(0.31, 0.47, pch_label, ha="center", va="center", fontsize=14.2, fontweight="semibold", color="#0E3A22")
    ax.text(0.31, 0.44, f"{len(set_pch)} espécies", ha="center", va="center", fontsize=11.2, color="#1A3D25")

    ax.plot([0.65, 0.73], [0.50, 0.50], color="#4C8642", linewidth=1.8)
    ax.text(0.69, 0.47, ctrl_label, ha="center", va="center", fontsize=14.2, fontweight="semibold", color="#3E7E3A")
    ax.text(0.69, 0.44, f"{len(set_ctrl)} espécies", ha="center", va="center", fontsize=11.2, color="#2C6031")

    # Caixa resumo inferior mais discreta.
    box = FancyBboxPatch(
        (0.18, 0.34),
        0.64,
        0.042,
        boxstyle="round,pad=0.012,rounding_size=0.01",
        linewidth=0.9,
        edgecolor="#1E4D2E",
        facecolor="#F7F7F7",
        alpha=0.90,
    )
    ax.add_patch(box)
    ax.text(0.50, 0.360, f"RIQUEZA TOTAL: {len(union)} ESPÉCIES", ha="center", va="center", fontsize=14.5, fontweight="bold", color=dark_text)
    ax.set_xlim(0.08, 0.92)
    ax.set_ylim(0.32, 0.90)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.set_xticklabels(["", "", ""])
    ax.set_yticklabels(["", "", ""])
    apply_theme(ax, theme, xlabel="", ylabel="")
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_venn = output_dir / "6_5_diagrama_venn_pch_vs_controle.png"
    fig.savefig(out_venn, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_venn))


def _save_general_status_tables(df_all: pd.DataFrame, output_dir: Path, generated_files: list[str]) -> None:
    species = (
        df_all.groupby("nome_cientifico", as_index=False)
        .agg(
            nome_popular=("nome_popular", "first"),
            ordem=("ordem", "first"),
            familia=("familia", "first"),
            iucn=("status_ameaca_global", "first"),
            mma=("status_ameaca_nacional", "first"),
            origem=("origem", "first"),
            habito=("habito_alimentar", "first"),
        )
    )

    def _is_threatened(x: object) -> bool:
        txt = _norm(x)
        return txt in {"vu", "en", "cr", "nt", "quase ameacada", "ameacada"}

    species["Ameacada"] = species["iucn"].map(_is_threatened) | species["mma"].map(_is_threatened)
    species["Endemica"] = False
    species["Rara"] = False
    species["Exotica"] = ~species["origem"].astype(str).str.contains("nativa", case=False, na=False)
    species["Cinegetica"] = species["habito"].astype(str).str.contains("herb|oniv|carn", case=False, na=False)
    species["Xerimbabo"] = False

    out_68 = output_dir / "6_6_6_8_tabela_geral_status.xlsx"
    species.to_excel(out_68, index=False, engine="openpyxl")
    generated_files.append(str(out_68))


def _save_descriptive_report(details: dict[str, Any], output_dir: Path, generated_files: list[str]) -> None:
    text_lines = [
        "Relatorio descritivo - Mastofauna sem primatas",
        "",
        f"Area PCH analisada: {TARGET_PCH_NAME}",
        f"Area Controle analisada: {TARGET_CONTROL_NAME}",
        f"Registros utilizados: {details.get('rows_loaded', 0)}",
        f"Especies totais (sem primatas): {details.get('species_total_no_primates', 0)}",
        "",
        "6.1 Riqueza, composicao e abundancia:",
        "- Tabela completa de especies gerada em excel.",
        "- Figuras de abundancia total e relativa geradas para PCH e Area Controle.",
        "",
        "6.2 Suficiencia amostral:",
        "- Estimadores (Sobs, Jackknife 1, Bootstrap) calculados para PCH e Controle.",
        "- Curvas do coletor geradas para as duas areas.",
        "",
        "6.3 Indices de diversidade:",
        "- Shannon, Pielou e Simpson calculados em excel e figura comparativa.",
        "",
        "6.4 Similaridade:",
        "- Indice de Jaccard calculado entre PCH e Controle.",
        "- Dendrograma de similaridade gerado.",
        "",
        "6.5 Diagrama de Venn:",
        "- Sobreposicao de especies entre PCH e Controle gerada.",
        "",
        "6.6-6.8 Tabela geral:",
        "- Consolidacao de ameacadas/endemicas/raras/exoticas/cinegeticas/xerimbabo gerada.",
        "",
        "Observacao: campos COPAM/CITES/Dependencia florestal/Endemismo nao estao estruturados no banco atual e foram sinalizados com '-' ou falso nas tabelas.",
    ]
    out_txt = output_dir / "6_relatorio_descritivo_mastofauna_sem_primatas.txt"
    out_txt.write_text("\n".join(text_lines), encoding="utf-8")
    generated_files.append(str(out_txt))


def run_mastofauna_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = _load_mastofauna_df(project_id=project_id, env_file=env_file)

    if df.empty:
        return {
            "rows_loaded": 0,
            "executed_blocks": [],
            "generated_files": [],
            "warning": "Sem dados de mastofauna para o projeto informado.",
        }

    # Regra solicitada: mastofauna sem primatas.
    df = df[~df.apply(_is_primata, axis=1)].copy()

    block_sel = str(block).strip().lower()
    generated_files: list[str] = []
    executed_blocks: list[str] = []

    df_pch = _subset_by_empreendimento(df, TARGET_PCH_NAME)
    df_control = _subset_by_empreendimento(df, TARGET_CONTROL_NAME)

    details: dict[str, Any] = {
        "rows_loaded": int(len(df)),
        "species_total_no_primates": int(df["nome_cientifico"].nunique()),
        "pch_rows": int(len(df_pch)),
        "control_rows": int(len(df_control)),
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()),
    }

    if block_sel in {"6.1", "61", "all"}:
        tab_pch = _build_species_list(df_pch)
        tab_ctrl = _build_species_list(df_control)
        out_pch = output_dir / "6_1_tabela_especies_pch_dores_de_guanhaes.xlsx"
        out_ctrl = output_dir / "6_1_tabela_especies_area_controle.xlsx"
        tab_pch.to_excel(out_pch, index=False, engine="openpyxl")
        tab_ctrl.to_excel(out_ctrl, index=False, engine="openpyxl")
        generated_files.extend([str(out_pch), str(out_ctrl)])

        metrics_pch = _save_abundance_figures(
            df_area=df_pch,
            theme=theme,
            output_png=output_dir / "6_1_figura_abundancia_total_relativa_mastofauna_pch_dgn.png",
        )
        generated_files.append(str(output_dir / "6_1_figura_abundancia_total_relativa_mastofauna_pch_dgn.png"))

        _save_abundance_figures(
            df_area=df_control,
            theme=theme,
            output_png=output_dir / "6_1_figura_abundancia_mastofauna_area_controle.png",
        )
        generated_files.append(str(output_dir / "6_1_figura_abundancia_mastofauna_area_controle.png"))
        details["block_6_1"] = metrics_pch
        executed_blocks.append("6.1")

    if block_sel in {"6.2", "62", "all"}:
        df_units = _load_sampling_units_df(project_id=project_id, env_file=env_file)
        df_units_pch = _subset_by_empreendimento(df_units, TARGET_PCH_NAME) if not df_units.empty else pd.DataFrame()
        df_units_ctrl = _subset_by_empreendimento(df_units, TARGET_CONTROL_NAME) if not df_units.empty else pd.DataFrame()
        est_pch = _save_estimators_and_curve(
            df_pch,
            "pch_dores_de_guanhaes",
            theme,
            output_dir,
            generated_files,
            sampling_units_df=df_units_pch,
        )
        est_ctrl = _save_estimators_and_curve(
            df_control,
            "area_controle",
            theme,
            output_dir,
            generated_files,
            sampling_units_df=df_units_ctrl,
        )
        details["block_6_2"] = {"pch": est_pch, "controle": est_ctrl}
        executed_blocks.append("6.2")

    if block_sel in {"6.3", "63", "all"}:
        _save_diversity(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.3")

    if block_sel in {"6.4", "64", "all"}:
        _save_similarity_and_venn(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.4")
        if block_sel in {"all"}:
            executed_blocks.append("6.5")

    if block_sel in {"6.5", "65"}:
        _save_similarity_and_venn(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.5")

    if block_sel in {"6.6", "66", "6.7", "67", "6.8", "68", "all"}:
        _save_general_status_tables(df, output_dir, generated_files)
        executed_blocks.extend(["6.6", "6.7", "6.8"])

    if block_sel in {"all"}:
        _save_descriptive_report(details, output_dir, generated_files)

    if not executed_blocks:
        raise ValueError("Unsupported block for mastofauna pipeline. Use '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '6.8' or 'all'.")

    details["executed_blocks"] = sorted(set(executed_blocks), key=lambda x: float(x))
    details["generated_files"] = generated_files
    return details
