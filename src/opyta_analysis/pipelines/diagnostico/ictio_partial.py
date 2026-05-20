"""Relatorio parcial Ictiofauna por empreendimento (campanha unica).

Espelha a estrutura Herp/Masto/Primatas (blocos 6.1-6.8), com adaptacoes:
- Sem Area Controle (ictio nao possui pontos controle no projeto 165).
- Dados Quantitativos (RP*) + Qualitativos (TR*).
- 6.1 separa tabelas/figuras por tipo_amostragem (Quanti CPUE vs Quali presenca).
- 6.3 Diversidade calculada sobre CPUEn (Quantitativos); Quali so reporta riqueza.
- 6.4 Jaccard entre pontos Quantitativos do empreendimento (sem Controle).
- 6.5 Diagrama de Venn substitui PCH x Controle por RP x TR (ambientes).
- 6.6-6.8 reaproveita `mastofauna._save_general_status_tables` (compativel).

CPUEn = numero_de_individuos / esforco * 100   (memoria do projeto)
CPUEb = pc_g / esforco * 100                   (peso corporal em g)

Uso (via script multi-empreendimento):

    import opyta_analysis.pipelines.diagnostico.ictio_partial as ictio_part
    ictio_part.TARGET_PCH_NAME = "Senhora do Porto"
    ictio_part.TARGET_CAMPANHA = "C028-2026-05-SC"
    ictio_part.run_ictio_partial_pipeline(
        project_id=165, theme=theme, output_dir=out, env_file=env, block="all",
    )
"""
from __future__ import annotations

import re
import unicodedata
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
    place_legend_below_x_axis,
)
from opyta_analysis.validators import validate_axes_style

from . import mastofauna as masto


# --------------------------------------------------------------------------- #
# Configuracao por execucao (setada externamente pelo runner multi-emp)
# --------------------------------------------------------------------------- #
TARGET_PCH_NAME = "Senhora do Porto"
TARGET_CAMPANHA = "C028-2026-05-SC"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _norm(value: object) -> str:
    txt = str(value or "").strip().lower()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", txt)


def _area_slug(text: str) -> str:
    n = _norm(text).replace(" ", "_")
    return re.sub(r"[^a-z0-9_]+", "", n)


def _ambiente_from_ponto(nome_ponto: str) -> str:
    """Retorna 'RP' ou 'TR' a partir do prefixo do nome do ponto."""
    p = str(nome_ponto or "").strip().upper()
    if p.startswith("RP"):
        return "RP"
    if p.startswith("TR"):
        return "TR"
    return "?"


# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #
def _load_ictio_partial_df(
    project_id: int,
    campanha_alvo: str,
    env_file: Optional[str],
) -> pd.DataFrame:
    """Carrega ictio do projeto restrito a uma campanha."""
    sb = get_client(env_file)

    # Campanha alvo
    camps = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    alvo = [c for c in camps if str(c.get("nome_campanha")) == campanha_alvo]
    if not alvo:
        return pd.DataFrame()
    id_camp = alvo[0]["id_campanha"]
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in camps}

    # Pontos do projeto NA campanha alvo
    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id), "id_campanha": int(id_camp)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}
    ponto_ids = set(pontos_map)

    # Empreendimentos
    emps = paginate(
        sb,
        "empreendimentos",
        filters={"id_projeto": int(project_id)},
        select="id_empreendimento,nome",
    )
    emp_map = {e["id_empreendimento"]: e["nome"] for e in emps}

    # Esforcos (Ictiofauna) restritos aos pontos
    esfs = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Ictiofauna"},
        select="id_esforco,id_ponto_coleta,esforco,unidade_esforco,metodo_de_captura,tipo_amostragem,tipo_de_amostragem",
    )
    esfs = [e for e in esfs if e.get("id_ponto_coleta") in ponto_ids]
    if not esfs:
        return pd.DataFrame()
    esf_map = {e["id_esforco"]: e for e in esfs}
    esf_ids = set(esf_map)

    # Resultados
    res = paginate(
        sb,
        "resultados_ictiofauna",
        select="id_esforco,id_especie,numero_de_individuos,pc_g,ct_cm,cp_cm,tipo_amostragem",
    )
    res = [r for r in res if r.get("id_esforco") in esf_ids]
    if not res:
        return pd.DataFrame()

    # Especies
    esp_rows = paginate(
        sb,
        "especies",
        select=(
            "id_especie,nome_cientifico,nome_popular,filo,classe,ordem,familia,genero,"
            "status_ameaca_global,status_ameaca_nacional,status_copam,cites,"
            "dependencia_florestal,endemismo,habito_alimentar,guilda_alimentar,"
            "sensibilidade_ambiental,migratorio,raridade,origem,distribuicao,cinegetica,"
            "xerimbabo,observacoes"
        ),
    )
    esp_map = {e["id_especie"]: e for e in esp_rows}

    rows: list[dict[str, Any]] = []
    for r in res:
        esf = esf_map.get(r["id_esforco"], {})
        p = pontos_map.get(esf.get("id_ponto_coleta"), {})
        esp = esp_map.get(r.get("id_especie"), {})
        id_emp = p.get("id_empreendimento")
        nome_ponto = p.get("nome_ponto")
        tipo = r.get("tipo_amostragem") or esf.get("tipo_amostragem") or esf.get("tipo_de_amostragem")
        rows.append(
            {
                "nome_campanha": camp_map.get(p.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": nome_ponto,
                "ambiente": _ambiente_from_ponto(nome_ponto),
                "empreendimento": emp_map.get(id_emp, "Sem empreendimento"),
                "tipo_amostragem": tipo,
                "id_esforco": esf.get("id_esforco"),
                "esforco": esf.get("esforco"),
                "unidade_esforco": esf.get("unidade_esforco"),
                "metodo_de_captura": esf.get("metodo_de_captura"),
                "id_especie": r.get("id_especie"),
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
                "migratorio": esp.get("migratorio"),
                "raridade": esp.get("raridade"),
                "origem": esp.get("origem"),
                "distribuicao": esp.get("distribuicao"),
                "cinegetica_db": esp.get("cinegetica"),
                "xerimbabo_db": esp.get("xerimbabo"),
                "especie_obs": esp.get("observacoes"),
                "contagem": r.get("numero_de_individuos"),
                "biomassa_g": r.get("pc_g"),
                "ct_cm": r.get("ct_cm"),
                "cp_cm": r.get("cp_cm"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for col in ["nome_campanha", "nome_ponto", "empreendimento", "tipo_amostragem", "nome_cientifico", "nome_popular", "ordem", "familia", "ambiente"]:
        df[col] = df[col].astype(str).str.strip()

    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0.0)
    df["biomassa_g"] = pd.to_numeric(df["biomassa_g"], errors="coerce").fillna(0.0)
    df["esforco"] = pd.to_numeric(df["esforco"], errors="coerce")

    # CPUEs (apenas faz sentido para Quanti; preserva NaN onde esforco ausente)
    df["cpue_n"] = np.where(df["esforco"].fillna(0) > 0, df["contagem"] / df["esforco"] * 100.0, np.nan)
    df["cpue_b"] = np.where(df["esforco"].fillna(0) > 0, df["biomassa_g"] / df["esforco"] * 100.0, np.nan)
    return df


def _subset_emp(df: pd.DataFrame, emp_name: str) -> pd.DataFrame:
    if df.empty or "empreendimento" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df["empreendimento"].map(_norm) == _norm(emp_name)].copy()


def _split_quanti_quali(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df.copy(), df.copy()
    tipo = df["tipo_amostragem"].astype(str).str.lower()
    df_quanti = df[tipo.str.startswith("quanti")].copy()
    df_quali = df[tipo.str.startswith("quali")].copy()
    return df_quanti, df_quali


# --------------------------------------------------------------------------- #
# 6.1 Tabela de especies + figura abundancia
# --------------------------------------------------------------------------- #
def _build_species_list_ictio(df: pd.DataFrame) -> pd.DataFrame:
    """Lista de especies adaptada a peixes (sem 'Dependencia florestal')."""
    if df.empty:
        return pd.DataFrame(
            columns=["Ordem", "Familia", "Especie", "Nome popular", "IUCN (2025)", "MMA (2022)", "COPAM (2010)", "Origem", "Migratorio"]
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
            origem=("origem", "first"),
            migratorio=("migratorio", "first"),
        )
        .sort_values(["ordem", "familia", "nome_cientifico"], na_position="last")
        .reset_index(drop=True)
        .rename(
            columns={
                "ordem": "Ordem",
                "familia": "Familia",
                "nome_cientifico": "Especie",
                "nome_popular": "Nome popular",
                "iucn": "IUCN (2025)",
                "mma": "MMA (2022)",
                "copam": "COPAM (2010)",
                "origem": "Origem",
                "migratorio": "Migratorio",
            }
        )
    )
    for col in ["IUCN (2025)", "MMA (2022)", "COPAM (2010)", "Origem", "Migratorio"]:
        table[col] = table[col].replace({None: "-", "": "-"}).fillna("-")
    return table[["Ordem", "Familia", "Especie", "Nome popular", "IUCN (2025)", "MMA (2022)", "COPAM (2010)", "Origem", "Migratorio"]]


def _abundance_metric(df: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, str, str]:
    """Retorna df agregado por especie com colunas (valor, pct) + rotulos.

    mode: 'cpue' (Quanti) -> soma CPUE-N por especie
          'pres' (Quali)  -> ocorrencias (em quantos pontos ocorreu)
    """
    if df.empty:
        return pd.DataFrame(columns=["nome_cientifico", "valor", "abund_relativa_pct"]), "valor", "Abundancia"
    if mode == "cpue":
        grp = (
            df.groupby("nome_cientifico", as_index=False)["cpue_n"].sum()
            .rename(columns={"cpue_n": "valor"})
        )
        total_label = "CPUE-N (ind/100m^2)"
    else:
        ocor = (
            df.groupby(["nome_cientifico", "nome_ponto"]).size().reset_index().rename(columns={0: "n"})
        )
        grp = ocor.groupby("nome_cientifico", as_index=False)["n"].count().rename(columns={"n": "valor"})
        total_label = "Pontos com ocorrencia (N)"

    total = float(grp["valor"].sum())
    grp["abund_relativa_pct"] = (grp["valor"] / total * 100.0) if total > 0 else 0.0
    grp = grp.sort_values("valor", ascending=False).reset_index(drop=True)
    return grp, "valor", total_label


def _save_abundance_figure(
    df_subset: pd.DataFrame,
    mode: str,
    theme: dict,
    output_png: Path,
    title_suffix: str = "",
) -> dict:
    grouped, vcol, total_label = _abundance_metric(df_subset, mode)
    if grouped.empty:
        return {"riqueza_observada": 0.0, "abundancia_total": 0.0}

    size = get_figsize_by_complexity(theme, n_categories=max(len(grouped), 1), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    ax_total = ax.twiny()

    y = np.arange(len(grouped))
    rel_color = str(theme.get("primary_hex", "#2E6F95"))
    total_color = str(theme.get("secondary_hex", "#E07A5F"))

    y_rel = y - 0.19
    y_total = y + 0.19

    bars_rel = ax.barh(
        y_rel, grouped["abund_relativa_pct"].values, height=0.30,
        color=rel_color, edgecolor="black", linewidth=0.8, zorder=2,
    )
    bars_total = ax_total.barh(
        y_total, grouped[vcol].values, height=0.30,
        color=total_color, edgecolor="black", linewidth=0.7, alpha=0.75, zorder=3,
    )
    ax.set_yticks(y)
    ax.set_yticklabels([str(v) for v in grouped["nome_cientifico"].tolist()], fontstyle="italic")
    ax.invert_yaxis()

    max_rel = float(grouped["abund_relativa_pct"].max() or 0.0)
    max_tot = float(grouped[vcol].max() or 0.0)
    ax.set_xlim(0, max(100.0, max_rel * 1.15, 1.0))
    ax_total.set_xlim(0, max(max_tot * 1.20, 1.0))

    apply_theme(ax, theme, xlabel="Abundancia relativa (%)", ylabel="Especie")
    ax_total.set_xlabel(total_label)
    ax_total.tick_params(axis="x", direction=str(theme.get("tick_direction", "out")))
    ax_total.grid(False)
    ax_total.spines["top"].set_visible(True)
    ax_total.spines["top"].set_color(str(theme.get("spine_color", "#000000")))
    ax_total.spines["top"].set_linewidth(float(theme.get("spine_linewidth", 1.2)))
    for side in ["left", "right", "bottom"]:
        ax_total.spines[side].set_visible(False)

    for bar, pct in zip(bars_rel, grouped["abund_relativa_pct"].values):
        ptxt = f"{pct:.0f}%" if abs(pct - round(pct)) < 1e-6 else f"{pct:.1f}%"
        ax.text(float(bar.get_width()) + 0.6, bar.get_y() + bar.get_height() / 2, ptxt,
                ha="left", va="center", fontsize=int(theme.get("annotation_size", 14)))

    for bar, val in zip(bars_total, grouped[vcol].values):
        v_txt = f"{val:.1f}" if mode == "cpue" else f"N={int(val)}"
        ax_total.text(
            float(bar.get_width()) + max(0.02 * max_tot, 0.1),
            bar.get_y() + bar.get_height() / 2,
            v_txt, ha="left", va="center",
            fontsize=int(theme.get("annotation_size", 14)),
        )

    handles = [
        Patch(facecolor=rel_color, edgecolor="black", label="Abundancia relativa (%)"),
        Patch(facecolor=total_color, edgecolor="black", label=total_label),
    ]
    place_legend_below_x_axis(fig, ax, theme, handles=handles, labels=[h.get_label() for h in handles], ncol=2)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.02))
    fig.savefig(output_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)

    return {
        "riqueza_observada": float(grouped["nome_cientifico"].nunique()),
        "abundancia_total": float(grouped[vcol].sum()),
    }


def _save_block_6_1(
    df_emp: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
    pch_slug = _area_slug(TARGET_PCH_NAME)
    df_quanti, df_quali = _split_quanti_quali(df_emp)

    # Tabela consolidada (todas as especies do empreendimento, com origem)
    table_all = _build_species_list_ictio(df_emp)
    out_tab = output_dir / f"6_1_tabela_especies_{pch_slug}.xlsx"
    with pd.ExcelWriter(out_tab, engine="openpyxl") as writer:
        table_all.to_excel(writer, sheet_name="Geral", index=False)
        if not df_quanti.empty:
            _build_species_list_ictio(df_quanti).to_excel(writer, sheet_name="Quantitativa", index=False)
        if not df_quali.empty:
            _build_species_list_ictio(df_quali).to_excel(writer, sheet_name="Qualitativa", index=False)
    generated_files.append(str(out_tab))

    metrics: dict[str, Any] = {}
    if not df_quanti.empty:
        out_fig_q = output_dir / f"6_1_figura_abundancia_cpue_n_{pch_slug}.png"
        metrics["quanti"] = _save_abundance_figure(df_quanti, "cpue", theme, out_fig_q)
        generated_files.append(str(out_fig_q))
    if not df_quali.empty:
        out_fig_p = output_dir / f"6_1_figura_ocorrencia_qualitativa_{pch_slug}.png"
        metrics["quali"] = _save_abundance_figure(df_quali, "pres", theme, out_fig_p)
        generated_files.append(str(out_fig_p))
    return metrics


# --------------------------------------------------------------------------- #
# 6.2 Suficiencia amostral (Sobs + Jackknife1 + Bootstrap + curva)
# --------------------------------------------------------------------------- #
def _save_block_6_2(
    df_emp: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
    pch_slug = _area_slug(TARGET_PCH_NAME)
    if df_emp.empty:
        est = pd.DataFrame([{"Area": pch_slug, "Riqueza observada": 0, "Abundancia": 0,
                             "Jackknife 1 estimada": 0.0, "Completude Jackknife 1 (%)": 0.0,
                             "Bootstrap estimada": 0.0, "Completude Bootstrap (%)": 0.0}])
        out = output_dir / f"6_2_tabela_estimadores_{pch_slug}.xlsx"
        est.to_excel(out, index=False, engine="openpyxl")
        generated_files.append(str(out))
        return {"sobs": 0.0, "jack1": 0.0, "boot": 0.0}

    # Unidade amostral = (nome_ponto, tipo_amostragem); concatena Quanti+Quali
    df_emp = df_emp.copy()
    df_emp["unidade"] = df_emp["nome_ponto"].astype(str) + " [" + df_emp["tipo_amostragem"].astype(str).str[:5] + "]"

    samples = (
        df_emp.groupby(["unidade", "nome_cientifico"], as_index=False)["contagem"].sum()
    )
    mat_obs = samples.pivot_table(index="unidade", columns="nome_cientifico", values="contagem", aggfunc="sum", fill_value=0)
    ordered_units = sorted(df_emp["unidade"].unique().tolist())
    mat = mat_obs.reindex(index=ordered_units, fill_value=0)
    pa = (mat > 0).astype(int)

    sobs = float((pa.sum(axis=0) > 0).sum())
    abundance = float(mat.sum().sum())
    jack1 = float(masto._jackknife_1(pa.values))
    boot = float(masto._bootstrap_richness(pa.values))

    est = pd.DataFrame([{
        "Area": pch_slug,
        "Riqueza observada": int(sobs),
        "Abundancia": int(abundance),
        "Jackknife 1 estimada": round(jack1, 2),
        "Completude Jackknife 1 (%)": round((sobs / jack1) * 100, 2) if jack1 > 0 else 0.0,
        "Bootstrap estimada": round(boot, 2),
        "Completude Bootstrap (%)": round((sobs / boot) * 100, 2) if boot > 0 else 0.0,
        "n_unidades_amostrais": int(pa.shape[0]),
    }])
    out_est = output_dir / f"6_2_tabela_estimadores_{pch_slug}.xlsx"
    est.to_excel(out_est, index=False, engine="openpyxl")
    generated_files.append(str(out_est))

    # Curva do coletor (200 permutacoes aleatorias)
    n_samples = int(pa.shape[0])
    if n_samples == 0:
        return {"sobs": sobs, "jack1": jack1, "boot": boot}

    rng = np.random.default_rng(42)
    sobs_curves = np.zeros((200, n_samples), dtype=float)
    jack_curves = np.zeros((200, n_samples), dtype=float)
    values = pa.values
    for r in range(200):
        idx = rng.permutation(n_samples)
        shuf = values[idx, :]
        for i in range(1, n_samples + 1):
            sub = shuf[:i, :]
            sobs_curves[r, i - 1] = float((sub.sum(axis=0) > 0).sum())
            jack_curves[r, i - 1] = masto._jackknife_1(sub)
    mean_sobs = sobs_curves.mean(axis=0)
    mean_jack = jack_curves.mean(axis=0)
    std_jack = jack_curves.std(axis=0)
    x = np.arange(1, n_samples + 1)

    df_curve = pd.DataFrame({
        "n_unidades_amostrais": x,
        "riqueza_obs_media": mean_sobs,
        "riqueza_jack1_media": mean_jack,
        "jack1_sd": std_jack,
        "jack1_inf": mean_jack - std_jack,
        "jack1_sup": mean_jack + std_jack,
    })
    out_curve_xlsx = output_dir / f"6_2_curva_coletor_dados_{pch_slug}.xlsx"
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
    ax.text(x[-1] + 0.15, mean_sobs[-1], f"{mean_sobs[-1]:.0f}", color="black", va="center",
            fontsize=int(theme.get("annotation_size", 14)))
    ax.text(x[-1] + 0.15, mean_jack[-1], f"{mean_jack[-1]:.1f}", color="black", va="center",
            fontsize=int(theme.get("annotation_size", 14)))
    place_legend_below_x_axis(fig, ax, theme, ncol=2)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.04))
    out_png = output_dir / f"6_2_curva_coletor_{pch_slug}.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"sobs": sobs, "jack1": jack1, "boot": boot, "n_unidades": n_samples}


# --------------------------------------------------------------------------- #
# 6.3 Diversidade (CPUE-N nos Quantitativos; Quali apenas riqueza)
# --------------------------------------------------------------------------- #
def _save_block_6_3(
    df_emp: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> None:
    df_quanti, df_quali = _split_quanti_quali(df_emp)

    rows: list[dict[str, Any]] = []
    if not df_quanti.empty:
        vec_q = df_quanti.groupby("nome_cientifico")["cpue_n"].sum().fillna(0).values
        rows.append({
            "Recorte": "Quantitativa (CPUE-N)",
            "Riqueza (S)": int(df_quanti["nome_cientifico"].nunique()),
            "Shannon (H')": round(masto._shannon(vec_q), 4),
            "Pielou (J')": round(masto._pielou(vec_q), 4),
            "Simpson (1-D)": round(masto._simpson_1_d(vec_q), 4),
        })
    if not df_quali.empty:
        rows.append({
            "Recorte": "Qualitativa",
            "Riqueza (S)": int(df_quali["nome_cientifico"].nunique()),
            "Shannon (H')": np.nan,
            "Pielou (J')": np.nan,
            "Simpson (1-D)": np.nan,
        })
    if not df_emp.empty:
        rows.append({
            "Recorte": "Geral (Quanti+Quali)",
            "Riqueza (S)": int(df_emp["nome_cientifico"].nunique()),
            "Shannon (H')": np.nan,
            "Pielou (J')": np.nan,
            "Simpson (1-D)": np.nan,
        })
    div = pd.DataFrame(rows)
    out_xlsx = output_dir / "6_3_indices_diversidade.xlsx"
    div.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    if div.empty:
        return

    metrics = ["Shannon (H')", "Pielou (J')", "Simpson (1-D)"]
    base_w, base_h = get_figsize_by_complexity(theme, n_categories=len(div), prefer_landscape=False)
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(base_w, max(base_h * 1.6, 9.5)),
                              dpi=int(theme.get("dpi", 600)), sharex=False)
    bar_color = str(theme.get("primary_hex", "#11420C"))
    labels = div["Recorte"].astype(str).tolist()

    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        vals = pd.to_numeric(div[metric], errors="coerce").fillna(0.0).astype(float).values
        y = np.arange(len(vals))
        bars = ax.barh(y, vals, color=bar_color, edgecolor="black", linewidth=0.8, height=0.5)
        for bar, raw, val in zip(bars, div[metric].tolist(), vals):
            label_v = "—" if pd.isna(raw) else f"{val:.2f}"
            ax.text(float(val) + (max(vals) * 0.03 if max(vals) > 0 else 0.02),
                    bar.get_y() + bar.get_height() / 2,
                    label_v, va="center", ha="left",
                    fontsize=int(theme.get("annotation_size", 12)), color="black")
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_title(metric, fontsize=int(theme.get("label_size", 14)), fontweight="bold", pad=8)
        ax.set_xlim(0, (max(vals) * 1.25) if max(vals) > 0 else 1.0)
        apply_theme(ax, theme, xlabel="", ylabel="", x_tick_rotation=0)
        validate_axes_style(ax, theme)

    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=False, extra_bottom=0.01))
    out_png = output_dir / "6_3_indices_diversidade.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


# --------------------------------------------------------------------------- #
# 6.4 Similaridade Jaccard entre pontos (Quantitativos)
# --------------------------------------------------------------------------- #
def _save_block_6_4(
    df_emp: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> None:
    df_quanti, _ = _split_quanti_quali(df_emp)
    if df_quanti.empty:
        return

    pontos = sorted(df_quanti["nome_ponto"].dropna().unique().tolist())
    species = sorted(df_quanti["nome_cientifico"].dropna().unique().tolist())
    if len(pontos) < 2 or not species:
        return

    pa_mat = np.zeros((len(pontos), len(species)), dtype=int)
    for i, p in enumerate(pontos):
        sp_p = set(df_quanti.loc[df_quanti["nome_ponto"] == p, "nome_cientifico"].dropna().astype(str).tolist())
        for j, s in enumerate(species):
            if s in sp_p:
                pa_mat[i, j] = 1

    dist = pdist(pa_mat, metric="jaccard")
    sim = 1.0 - squareform(dist)
    np.fill_diagonal(sim, 1.0)
    sim_df = pd.DataFrame(sim, index=pontos, columns=pontos)
    sim_df.index.name = "Ponto"

    out_xlsx = output_dir / "6_4_matriz_similaridade_jaccard_por_pontos.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        sim_df.to_excel(writer, sheet_name="Matriz Jaccard")
        pd.DataFrame({"Ponto": pontos,
                      "Ambiente": [_ambiente_from_ponto(p) for p in pontos]}).to_excel(
            writer, sheet_name="Pontos e Ambientes", index=False
        )
    generated_files.append(str(out_xlsx))

    # Dendrograma
    z = linkage(dist, method="average")
    n_pts = len(pontos)
    fig_height = min(max(4 + n_pts * 0.4, 8), 16)
    fig, ax = plt.subplots(figsize=(12, fig_height), dpi=int(theme.get("dpi", 600)))
    dendrogram(z, labels=pontos, orientation="right", ax=ax, color_threshold=None)

    color_rp = str(theme.get("primary_hex", "#1f77b4"))
    color_tr = str(theme.get("secondary_hex", "#ff7f0e"))
    for label in ax.get_yticklabels():
        ambient = _ambiente_from_ponto(label.get_text())
        label.set_color(color_rp if ambient == "RP" else color_tr)
        label.set_fontweight("bold")

    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.0, 0.0)
    ticks_sim = np.arange(0, 101, 10)
    ax.set_xticks(1 - ticks_sim / 100.0)
    ax.set_xticklabels([str(t) for t in ticks_sim], fontsize=10)
    apply_theme(ax, theme, xlabel="Similaridade de Jaccard (%)", ylabel="Pontos amostrais (Quantitativos)")
    validate_axes_style(ax, theme)
    fig.text(0.495, 0.96, "■ Rio Principal (RP)", ha="right", va="top", fontsize=11, fontweight="bold", color=color_rp)
    fig.text(0.505, 0.96, "■ Tributario (TR)", ha="left", va="top", fontsize=11, fontweight="bold", color=color_tr)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_png = output_dir / "6_4_dendrograma_jaccard_por_pontos.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


# --------------------------------------------------------------------------- #
# 6.5 Venn RP x TR (ambientes)
# --------------------------------------------------------------------------- #
def _save_block_6_5(
    df_emp: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> None:
    if df_emp.empty:
        return
    set_rp = set(df_emp.loc[df_emp["ambiente"] == "RP", "nome_cientifico"].dropna().astype(str).tolist())
    set_tr = set(df_emp.loc[df_emp["ambiente"] == "TR", "nome_cientifico"].dropna().astype(str).tolist())
    inter = set_rp & set_tr
    union = set_rp | set_tr
    only_rp = len(set_rp - set_tr)
    only_tr = len(set_tr - set_rp)
    both = len(inter)
    jacc = (len(inter) / len(union)) if union else 0.0

    table = pd.DataFrame([{
        "Ambiente A": "Rio Principal (RP)",
        "Ambiente B": "Tributario (TR)",
        "Spp_A": len(set_rp),
        "Spp_B": len(set_tr),
        "Spp_intersecao": both,
        "Spp_total (uniao)": len(union),
        "Jaccard": round(jacc, 4),
    }])
    out_xlsx = output_dir / "6_5_tabela_jaccard_rp_vs_tr.xlsx"
    table.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    fig, ax = plt.subplots(figsize=(11, 7.4), dpi=int(theme.get("dpi", 600)))
    rp_color = str(theme.get("primary_hex", "#11420C"))
    tr_color = str(theme.get("secondary_hex", "#5B8E53"))
    dark_text = "#0D2A1D"

    c1 = Circle((0.39, 0.67), 0.22, color=rp_color, alpha=0.24, ec="#0E3A22", lw=1.4)
    c2 = Circle((0.61, 0.67), 0.22, color=tr_color, alpha=0.22, ec="#4C8642", lw=1.4)
    ax.add_patch(c1); ax.add_patch(c2)

    y_num, y_desc = 0.69, 0.63
    ax.text(0.33, y_num, str(only_rp), ha="center", va="center", fontsize=32, fontweight="bold", color=dark_text)
    ax.text(0.33, y_desc, "Especies\nexclusivas RP", ha="center", va="center", fontsize=13.2, color=dark_text)
    ax.text(0.50, y_num, str(both), ha="center", va="center", fontsize=34, fontweight="bold", color=dark_text)
    ax.text(0.50, y_desc, "Especie\ncompartilhada" if both == 1 else "Especies\ncompartilhadas",
            ha="center", va="center", fontsize=13.2, color=dark_text)
    ax.text(0.67, y_num, str(only_tr), ha="center", va="center", fontsize=32, fontweight="bold", color="#2F6A34")
    ax.text(0.67, y_desc, "Especies\nexclusivas TR", ha="center", va="center", fontsize=13.2, color="#2F6A34")

    ax.plot([0.27, 0.35], [0.50, 0.50], color="#0E3A22", linewidth=1.8)
    ax.text(0.31, 0.47, "Rio Principal (RP)", ha="center", va="center", fontsize=14.2, fontweight="semibold", color="#0E3A22")
    ax.text(0.31, 0.44, f"{len(set_rp)} especies", ha="center", va="center", fontsize=11.2, color="#1A3D25")
    ax.plot([0.65, 0.73], [0.50, 0.50], color="#4C8642", linewidth=1.8)
    ax.text(0.69, 0.47, "Tributario (TR)", ha="center", va="center", fontsize=14.2, fontweight="semibold", color="#3E7E3A")
    ax.text(0.69, 0.44, f"{len(set_tr)} especies", ha="center", va="center", fontsize=11.2, color="#2C6031")

    box = FancyBboxPatch((0.18, 0.34), 0.64, 0.042,
                         boxstyle="round,pad=0.012,rounding_size=0.01",
                         linewidth=0.9, edgecolor="#1E4D2E",
                         facecolor="#F7F7F7", alpha=0.90)
    ax.add_patch(box)
    ax.text(0.50, 0.360, f"RIQUEZA TOTAL: {len(union)} ESPECIES", ha="center", va="center",
            fontsize=14.5, fontweight="bold", color=dark_text)
    ax.set_xlim(0.08, 0.92); ax.set_ylim(0.32, 0.90)
    ax.set_xticks([0.0, 0.5, 1.0]); ax.set_yticks([0.0, 0.5, 1.0])
    ax.set_xticklabels(["", "", ""]); ax.set_yticklabels(["", "", ""])
    apply_theme(ax, theme, xlabel="", ylabel="")
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_png = output_dir / "6_5_diagrama_venn_rp_vs_tr.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


# --------------------------------------------------------------------------- #
# 6.6-6.8 Tabela geral (reaproveita masto)
# --------------------------------------------------------------------------- #
def _save_block_6_6_8(df_emp: pd.DataFrame, output_dir: Path, generated_files: list[str]) -> None:
    if df_emp.empty:
        return
    masto._save_general_status_tables(df_emp, output_dir, generated_files)


# --------------------------------------------------------------------------- #
# Relatorio descritivo
# --------------------------------------------------------------------------- #
def _save_descriptive_report(details: dict, output_dir: Path, generated_files: list[str]) -> None:
    lines = [
        "Relatorio descritivo - Ictiofauna (parcial)",
        "",
        f"Campanha analisada: {TARGET_CAMPANHA}",
        f"Empreendimento: {TARGET_PCH_NAME}",
        f"Registros utilizados: {details.get('rows_loaded', 0)}",
        f"Especies (total no empreendimento): {details.get('species_total', 0)}",
        f"  - Quantitativa: {details.get('species_quanti', 0)}",
        f"  - Qualitativa: {details.get('species_quali', 0)}",
        f"Pontos (Quantitativos): {details.get('n_pontos_quanti', 0)}",
        f"Pontos (Qualitativos):  {details.get('n_pontos_quali', 0)}",
        "",
        "6.1 Riqueza, composicao e abundancia:",
        "- Tabela de especies (abas Geral / Quantitativa / Qualitativa).",
        "- Figura de abundancia CPUE-N (Quantitativos) e ocorrencia (Qualitativos).",
        "",
        "6.2 Suficiencia amostral:",
        "- Riqueza observada + Jackknife 1 + Bootstrap; curva do coletor com 200 permutacoes.",
        "- Unidade amostral: ponto x tipo_amostragem (consolida Quanti+Quali).",
        "",
        "6.3 Indices de diversidade:",
        "- Shannon, Pielou e Simpson calculados sobre CPUE-N (Quantitativos).",
        "- Qualitativos reportam apenas riqueza (S).",
        "",
        "6.4 Similaridade Jaccard entre pontos:",
        "- Calculada apenas com dados Quantitativos (RP).",
        "- Matriz por pontos + dendrograma com codificacao RP/TR.",
        "",
        "6.5 Diagrama de Venn RP x TR:",
        "- Sobreposicao de especies entre Rio Principal e Tributarios.",
        "",
        "6.6-6.8 Tabela geral:",
        "- Consolidacao de ameacadas/endemicas/raras/exoticas (status DB).",
        "",
        "Observacao: o projeto 165 (ictiofauna) NAO possui pontos controle. As analises",
        "deste relatorio parcial sao internas ao empreendimento.",
    ]
    out = output_dir / "6_relatorio_descritivo_ictio_parcial.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    generated_files.append(str(out))


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def run_ictio_partial_pipeline(
    project_id: int,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
    campanha_alvo: Optional[str] = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Higiene de estado matplotlib entre execucoes sequenciais (multi-empreendimento).
    # Sem isso, acumulo de figuras+axes ao longo de iteracoes pode travar a ultima rodada.
    plt.close("all")
    if campanha_alvo:
        global TARGET_CAMPANHA
        TARGET_CAMPANHA = campanha_alvo

    df = _load_ictio_partial_df(project_id=project_id, campanha_alvo=TARGET_CAMPANHA, env_file=env_file)
    if df.empty:
        return {
            "rows_loaded": 0,
            "executed_blocks": [],
            "generated_files": [],
            "warning": f"Sem dados de ictiofauna para campanha '{TARGET_CAMPANHA}' no projeto {project_id}.",
        }

    df_emp = _subset_emp(df, TARGET_PCH_NAME)
    if df_emp.empty:
        return {
            "rows_loaded": int(len(df)),
            "executed_blocks": [],
            "generated_files": [],
            "warning": f"Sem dados de '{TARGET_PCH_NAME}' na campanha '{TARGET_CAMPANHA}'.",
        }

    df_quanti, df_quali = _split_quanti_quali(df_emp)

    generated_files: list[str] = []
    executed: list[str] = []
    block_sel = str(block).strip().lower()
    details: dict[str, Any] = {
        "rows_loaded": int(len(df_emp)),
        "species_total": int(df_emp["nome_cientifico"].nunique()),
        "species_quanti": int(df_quanti["nome_cientifico"].nunique()),
        "species_quali": int(df_quali["nome_cientifico"].nunique()),
        "n_pontos_quanti": int(df_quanti["nome_ponto"].nunique()),
        "n_pontos_quali": int(df_quali["nome_ponto"].nunique()),
        "campaigns": sorted(df_emp["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": sorted(df_emp["nome_ponto"].dropna().astype(str).unique().tolist()),
    }

    if block_sel in {"6.1", "61", "all"}:
        details["block_6_1"] = _save_block_6_1(df_emp, theme, output_dir, generated_files)
        executed.append("6.1")

    if block_sel in {"6.2", "62", "all"}:
        details["block_6_2"] = _save_block_6_2(df_emp, theme, output_dir, generated_files)
        executed.append("6.2")

    if block_sel in {"6.3", "63", "all"}:
        _save_block_6_3(df_emp, theme, output_dir, generated_files)
        executed.append("6.3")

    if block_sel in {"6.4", "64", "all"}:
        _save_block_6_4(df_emp, theme, output_dir, generated_files)
        executed.append("6.4")

    if block_sel in {"6.5", "65", "all"}:
        _save_block_6_5(df_emp, theme, output_dir, generated_files)
        executed.append("6.5")

    if block_sel in {"6.6", "66", "6.7", "67", "6.8", "68", "all"}:
        _save_block_6_6_8(df_emp, output_dir, generated_files)
        executed.extend(["6.6", "6.7", "6.8"])

    if block_sel == "all":
        _save_descriptive_report(details, output_dir, generated_files)

    if not executed:
        raise ValueError(
            "Bloco invalido. Use '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '6.8' ou 'all'."
        )

    details["executed_blocks"] = sorted(set(executed), key=lambda x: float(x))
    details["generated_files"] = generated_files
    return details
