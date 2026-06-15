"""
Pipeline de analises ecologicas exploratorias - Ictiofauna
==========================================================

Projeto 165 (ITAGUA001) - Guanhaes Energia - 4 empreendimentos (SPT/DGN/FOR/JAC).

Objetivo: avaliar estabilizacao temporal da assembleia de peixes em reservatorios
neotropicais (UHEs Senhora do Porto, Dores de Guanhaes, Jacare, Fortuna II)
e suportar discussao sobre possivel reducao do esforco amostral.

Estrutura temporal adotada (cortes simplificados, ja validados pelo usuario):
    Pre-operacao: ate 2017-07-01
    Pos-operacao (enchimento + estabilizacao): apos 2017-07-01
    O proprio estudo dira se a fase pos pode ser refinada em transicao/estabilizacao.

Blocos analiticos:
    0) Suficiencia amostral (rarefacao Mao Tau + estimador Chao2; unidade = campanha + ponto)
    1) Diversidade alfa (riqueza, Shannon, Simpson, Pielou, abundancia, biomassa)
    2) Tendencia temporal (regressao linear ano-a-ano + comparacao Pre x Pos)
    3) Estrutura da comunidade (Bray-Curtis, PCoA, dendrograma, heatmap temporal)
    4) Diferenca entre periodos (ANOSIM + PERMANOVA - testes de permutacao)
    5) Beta-diversidade temporal (Sorensen + decomposicao Baselga: turnover + nestedness)
   5b) Beta-Legendre por campanha + LCBD por ponto + ITS (Interrupted Time Series)
    6) Sintese (.txt por empreendimento)
    7) Criterios objetivos de estabilidade (score 0-6)

Referencias-chave incorporadas:
    Legendre & De Caceres (2013) - beta como variancia + LCBD
    Baselga (2010) - decomposicao turnover/nestedness
    Ferreira et al. (2026, Hydrobiologia) - ITS aplicado a damming em reservatorios
        neotropicais (Serra da Mesa, 15 anos); achados: trophic upsurge -> equilibrio,
        diferenciacao taxonomica imediata + leve homogeneizacao no longo prazo,
        e redundancia funcional (face funcional pode permanecer estavel).

Observacao importante: este pipeline avalia apenas a face TAXONOMICA da
beta-diversidade. Conforme Ferreira et al. (2026), mudancas taxonomicas podem
nao ser acompanhadas por mudancas funcionais (redundancia funcional). Sem
traits ecomorfologicos disponiveis no banco, esta limitação e reportada na
conclusão.

No nivel raiz tambem sao gerados:
    _painel_comparativo/ - paineis comparativos entre os 4 empreendimentos
    _conclusao_estabilidade/ - tabela e parecer final de estabilidade por area

Fonte de dados: biota_analise_consolidada (Supabase, projeto ITAGUA001), filtrada para:
    - grupo_biologico = 'Ictiofauna'
    - tipo_amostragem = 'Quantitativa'  (pontos RP*, esforco padronizado)

Dependencias: pandas, numpy, scipy, matplotlib, seaborn, sqlalchemy, openpyxl, python-dotenv.
(Nao requer scikit-learn / statsmodels / scikit-bio - todas as estatisticas sao
implementadas com numpy/scipy.)

Saida: <BASE_OUTPUT>/<Empreendimento>/<bloco>/...
"""

from __future__ import annotations

import os
import re
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Windows / nbconvert safety

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from scipy import stats
from scipy.cluster import hierarchy
from scipy.spatial.distance import pdist, squareform
from sqlalchemy import text

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# Engine de banco (reaproveita core.engine de Opyta_Data, que ja le o .env)
# ---------------------------------------------------------------------------
OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from core.engine import get_engine  # noqa: E402


# ---------------------------------------------------------------------------
# Constantes do projeto
# ---------------------------------------------------------------------------
PROJETO_CODIGO = "ITAGUA001"
GRUPO = "Ictiofauna"
CORTE_PRE_POS = pd.Timestamp("2017-07-01")

OUTPUT_BASE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia"
    r"\Guanhães Energia\Resultados e análises\28_campanha-Abril_26"
    r"\Ictiofauna\Análise consolidada"
)

# Paleta categorica de alto contraste para empreendimentos / fases
COR_EMPREENDIMENTO = {
    "Senhora do Porto": "#1f77b4",
    "Dores de Guanhães": "#2ca02c",
    "Fortuna II": "#d62728",
    "Jacaré": "#9467bd",
}
COR_FASE = {"Pre": "#7f7f7f", "Pos": "#1a9850"}

# Estrutura hidrográfica (Guanhães Energia).
# Cascata do rio Guanhães (montante=1 -> jusante=3): JAC -> SPT -> DGN.
# Fortuna II está isolada no rio Corrente Grande (sem cascata acima).
# Análises de gradiente de cascata (Ganassin et al. 2021) operam SOMENTE
# nos 3 empreendimentos do Guanhães; FOR entra como referência regional
# fora-da-cascata.
BACIA_EMP = {
    "Jacaré":             {"rio": "Guanhães",        "posicao": 1, "em_cascata": True},
    "Senhora do Porto":   {"rio": "Guanhães",        "posicao": 2, "em_cascata": True},
    "Dores de Guanhães":  {"rio": "Guanhães",        "posicao": 3, "em_cascata": True},
    "Fortuna II":         {"rio": "Corrente Grande", "posicao": 1, "em_cascata": False},
}

# Padrao visual (Padrao Ouro Opyta)
plt.rcParams.update({
    "figure.figsize": (15, 10),
    "font.size": 14,
    "axes.titlesize": 15,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


# ---------------------------------------------------------------------------
# 0. Carregamento dos dados
# ---------------------------------------------------------------------------
def carregar_dados(engine) -> pd.DataFrame:
    """Carrega a fatia da biota_analise_consolidada usada no pipeline."""
    sql = text("""
        SELECT
            nome_empreendimento,
            nome_campanha,
            nome_ponto,
            nome_cientifico,
            origem,
            contagem,
            biomassa,
            esforco,
            tipo_amostragem
        FROM biota_analise_consolidada
        WHERE codigo_interno_opyta = :cod
          AND grupo_biologico = :grupo
          AND tipo_amostragem = 'Quantitativa'
          AND nome_empreendimento IS NOT NULL
          AND nome_cientifico IS NOT NULL
    """)
    df = pd.read_sql(sql, engine, params={"cod": PROJETO_CODIGO, "grupo": GRUPO})

    # Tipagem
    for col in ("contagem", "biomassa", "esforco"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Data da campanha: padrao C[R]?NNN-YYYY-MM-XX
    pat = re.compile(r"C[R]?\d+-(\d{4})-(\d{2})")
    def _to_date(nome: str) -> pd.Timestamp | pd.NaT:
        m = pat.search(str(nome))
        if not m:
            return pd.NaT
        return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=1)
    df["data_campanha"] = df["nome_campanha"].map(_to_date)
    df["ano"] = df["data_campanha"].dt.year
    df["fase"] = np.where(df["data_campanha"] <= CORTE_PRE_POS, "Pre", "Pos")

    # CPUE por linha (ind/100m^2 e g/100m^2) - regra interna
    df["cpue_n"] = (df["contagem"] / df["esforco"]) * 100.0
    df["cpue_b"] = (df["biomassa"] / df["esforco"]) * 100.0

    return df


# ---------------------------------------------------------------------------
# Utilidades de IO
# ---------------------------------------------------------------------------
def safe_name(s: str) -> str:
    s = re.sub(r"[^\w]+", "_", str(s), flags=re.UNICODE).strip("_")
    return s

def mkdirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Indices ecologicos
# ---------------------------------------------------------------------------
def indices_alfa(abund: pd.Series) -> dict:
    """Recebe abundancia (por especie) ja agregada e devolve indices alfa."""
    x = abund.to_numpy(dtype=float)
    x = x[x > 0]
    S = int((x > 0).sum())
    N = float(x.sum())
    if S == 0 or N == 0:
        return {"S": 0, "N": 0.0, "H": 0.0, "Simpson": 0.0, "Pielou": 0.0}
    p = x / N
    H = float(-np.sum(p * np.log(p)))
    D = float(1 - np.sum(p ** 2))           # Simpson (1-D)
    J = float(H / np.log(S)) if S > 1 else 0.0
    return {"S": S, "N": N, "H": H, "Simpson": D, "Pielou": J}


# ---------------------------------------------------------------------------
# Bloco 0 - Curva de suficiencia amostral (Mao Tau + Chao2)
# ---------------------------------------------------------------------------
def _chao2(presabs: np.ndarray) -> tuple[float, float]:
    """Estimador Chao2 (incidencia) + S_obs. presabs = matriz amostras x especies (0/1)."""
    incid = presabs.sum(axis=0)
    S_obs = int((incid > 0).sum())
    q1 = int((incid == 1).sum())
    q2 = int((incid == 2).sum())
    H = presabs.shape[0]
    if H < 2:
        return float(S_obs), float(S_obs)
    if q2 > 0:
        chao = S_obs + ((H - 1) / H) * (q1 ** 2) / (2 * q2)
    else:
        chao = S_obs + ((H - 1) / H) * q1 * (q1 - 1) / 2.0
    return float(S_obs), float(chao)


def _mao_tau(presabs: np.ndarray, n_perm: int = 200, seed: int = 42
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Curva de rarefacao por amostras (acumulacao via permutacoes).
    Retorna t (1..H), media, desvio padrao."""
    H = presabs.shape[0]
    rng = np.random.default_rng(seed)
    acc = np.zeros((n_perm, H))
    for k in range(n_perm):
        order = rng.permutation(H)
        cum = np.zeros(presabs.shape[1], dtype=bool)
        for i, idx in enumerate(order):
            cum |= presabs[idx] > 0
            acc[k, i] = cum.sum()
    return np.arange(1, H + 1), acc.mean(axis=0), acc.std(axis=0)


def bloco_0_suficiencia(df_emp: pd.DataFrame, pasta: Path,
                        nome_emp: str) -> dict:
    mkdirs(pasta)
    # Unidade amostral = campanha + ponto
    mat = (df_emp.groupby(["fase", "nome_campanha", "nome_ponto",
                           "nome_cientifico"], as_index=False)["contagem"].sum()
                 .pivot_table(index=["fase", "nome_campanha", "nome_ponto"],
                              columns="nome_cientifico",
                              values="contagem", fill_value=0))
    meta = mat.index.to_frame(index=False)
    pres = (mat.to_numpy(dtype=float) > 0).astype(int)

    # Global + por fase
    resumo_rows = []
    curvas = {}
    for fase_lbl, idx in [("Global", np.arange(len(meta))),
                          ("Pre", np.where(meta["fase"].eq("Pre"))[0]),
                          ("Pos", np.where(meta["fase"].eq("Pos"))[0])]:
        if len(idx) < 2:
            continue
        sub = pres[idx]
        S_obs, chao = _chao2(sub)
        cov = (S_obs / chao) if chao > 0 else np.nan
        t, mean, sd = _mao_tau(sub)
        curvas[fase_lbl] = (t, mean, sd)
        resumo_rows.append({
            "fase": fase_lbl,
            "n_amostras": int(len(idx)),
            "S_obs": int(S_obs),
            "S_Chao2": round(chao, 2),
            "cobertura": round(cov, 3),
            "suficiente_>=0.85": bool(cov >= 0.85),
        })
    resumo = pd.DataFrame(resumo_rows)
    resumo.to_excel(pasta / "00_suficiencia_resumo.xlsx", index=False)

    # Plot
    cores = {"Global": "black", "Pre": COR_FASE["Pre"], "Pos": COR_FASE["Pos"]}
    fig, ax = plt.subplots(figsize=(13, 8))
    for lbl, (t, mean, sd) in curvas.items():
        ax.plot(t, mean, "-", color=cores[lbl], lw=1.8, label=f"{lbl} (n={len(t)})")
        ax.fill_between(t, mean - sd, mean + sd, color=cores[lbl], alpha=0.15)
        # Chao2 como linha de assintota
        rr = resumo[resumo["fase"].eq(lbl)]
        if not rr.empty:
            ax.axhline(float(rr["S_Chao2"].iloc[0]), color=cores[lbl],
                       ls=":", lw=0.9, alpha=0.6)
    ax.set_xlabel("Unidades amostrais (campanha × ponto) acumuladas")
    ax.set_ylabel("Riqueza acumulada (espécies)")
    ax.legend(loc="lower right", frameon=False)
    fig.suptitle(f"{nome_emp} - Curva de suficiência (Mao Tau) + Chao2 (linhas pontilhadas)",
                 fontsize=15, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(pasta / "00a_curva_suficiencia.png")
    plt.close(fig)

    # Score de cobertura geral (Pos = referencia para decisao)
    cob_pos = float(resumo.loc[resumo["fase"].eq("Pos"), "cobertura"].iloc[0]) \
              if (resumo["fase"].eq("Pos")).any() else np.nan
    cob_global = float(resumo.loc[resumo["fase"].eq("Global"), "cobertura"].iloc[0]) \
                 if (resumo["fase"].eq("Global")).any() else np.nan
    return {"resumo": resumo, "cob_pos": cob_pos, "cob_global": cob_global}


# ---------------------------------------------------------------------------
# Bloco 1 - Diversidade alfa por campanha
# ---------------------------------------------------------------------------
def bloco_1_alfa(df_emp: pd.DataFrame, pasta: Path, nome_emp: str) -> pd.DataFrame:
    mkdirs(pasta)

    # Agregar por campanha x especie (soma sobre todos os pontos/esforcos da campanha)
    agg = (
        df_emp.groupby(["data_campanha", "nome_campanha", "fase", "nome_cientifico"],
                       as_index=False)
              .agg(abund=("contagem", "sum"),
                   bio=("biomassa", "sum"),
                   cpue_n=("cpue_n", "sum"),
                   cpue_b=("cpue_b", "sum"))
    )

    linhas = []
    for (dt, camp, fase), g in agg.groupby(["data_campanha", "nome_campanha", "fase"]):
        idx = indices_alfa(g.set_index("nome_cientifico")["abund"])
        linhas.append({
            "data_campanha": dt,
            "nome_campanha": camp,
            "fase": fase,
            **idx,
            "biomassa_total": float(g["bio"].sum()),
            "cpue_n_total":   float(g["cpue_n"].sum()),
            "cpue_b_total":   float(g["cpue_b"].sum()),
        })
    tab = pd.DataFrame(linhas).sort_values("data_campanha").reset_index(drop=True)
    tab.to_excel(pasta / "01_diversidade_alfa_por_campanha.xlsx", index=False)

    # Boxplot Pre vs Pos por metrica
    metricas = [
        ("S",         "Riqueza (S)"),
        ("H",         "Shannon (H')"),
        ("Simpson",   "Simpson (1-D)"),
        ("Pielou",    "Pielou (J')"),
        ("cpue_n_total", "CPUEn total (ind/100m²)"),
        ("cpue_b_total", "CPUEb total (g/100m²)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()
    for ax, (col, label) in zip(axes, metricas):
        sns.boxplot(data=tab, x="fase", y=col, order=["Pre", "Pos"],
                    hue="fase", palette=COR_FASE, legend=False,
                    ax=ax, width=0.55, showmeans=True,
                    meanprops={"marker": "D", "markerfacecolor": "white",
                               "markeredgecolor": "black", "markersize": 7})
        sns.stripplot(data=tab, x="fase", y=col, order=["Pre", "Pos"],
                      color="black", size=3, alpha=0.6, ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel(label)
        ax.set_title("")
    fig.suptitle(f"{nome_emp} - Diversidade alfa: Pre vs Pos", fontsize=16, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(pasta / "01a_boxplot_alfa_pre_pos.png")
    plt.close(fig)

    return tab


# ---------------------------------------------------------------------------
# Bloco 2 - Tendencia temporal
# ---------------------------------------------------------------------------
def bloco_2_tendencia(tab: pd.DataFrame, pasta: Path, nome_emp: str) -> pd.DataFrame:
    mkdirs(pasta)
    if tab.empty:
        return pd.DataFrame()

    # x = ano em float
    x = tab["data_campanha"].map(lambda d: d.year + (d.month - 1) / 12).to_numpy()

    metricas = [
        ("S",            "Riqueza (S)"),
        ("H",            "Shannon (H')"),
        ("Simpson",      "Simpson (1-D)"),
        ("Pielou",       "Pielou (J')"),
        ("cpue_n_total", "CPUEn total (ind/100m²)"),
        ("cpue_b_total", "CPUEb total (g/100m²)"),
    ]

    # Tabela de regressao Pos-operacao (a estabilizacao se da na pos)
    mask_pos = tab["fase"].eq("Pos")
    reg_rows = []
    for col, label in metricas:
        y = tab[col].to_numpy()
        # global
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() >= 3:
            r_all = stats.linregress(x[ok], y[ok])
        else:
            r_all = None
        # pos
        m = mask_pos.to_numpy() & ok
        if m.sum() >= 3:
            r_pos = stats.linregress(x[m], y[m])
        else:
            r_pos = None
        reg_rows.append({
            "metrica": label,
            "slope_global": r_all.slope if r_all else np.nan,
            "r2_global":    (r_all.rvalue ** 2) if r_all else np.nan,
            "p_global":     r_all.pvalue if r_all else np.nan,
            "n_global":     int(ok.sum()),
            "slope_pos":    r_pos.slope if r_pos else np.nan,
            "r2_pos":       (r_pos.rvalue ** 2) if r_pos else np.nan,
            "p_pos":        r_pos.pvalue if r_pos else np.nan,
            "n_pos":        int(m.sum()),
        })
    reg_tab = pd.DataFrame(reg_rows)
    reg_tab.to_excel(pasta / "02_tendencia_regressao.xlsx", index=False)

    # Painel temporal 2x3
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()
    for ax, (col, label) in zip(axes, metricas):
        y = tab[col].to_numpy()
        ax.scatter(tab["data_campanha"], y,
                   c=[COR_FASE[f] for f in tab["fase"]],
                   s=42, edgecolor="black", linewidth=0.4, zorder=3)
        # linha de tendencia (global) se houver
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() >= 3:
            r = stats.linregress(x[ok], y[ok])
            xs = np.linspace(x[ok].min(), x[ok].max(), 50)
            ax.plot(pd.to_datetime(
                        [f"{int(v)}-{int(round((v % 1) * 12 + 1)):02d}-01" for v in xs],
                        errors="coerce"),
                    r.intercept + r.slope * xs,
                    color="black", lw=1.3, ls="--", alpha=0.85)
            ax.text(0.02, 0.95,
                    f"slope={r.slope:.3g}  R²={r.rvalue**2:.2f}  p={r.pvalue:.3g}",
                    transform=ax.transAxes, ha="left", va="top",
                    fontsize=11,
                    bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.85))
        ax.axvline(CORTE_PRE_POS, color="firebrick", lw=1.0, ls=":", alpha=0.8)
        ax.set_xlabel("")
        ax.set_ylabel(label)

    # Legenda das fases
    handles = [Line2D([0], [0], marker="o", lw=0, markerfacecolor=COR_FASE["Pre"],
                      markeredgecolor="black", markersize=8, label="Pré (≤ 2017-07-01)"),
               Line2D([0], [0], marker="o", lw=0, markerfacecolor=COR_FASE["Pos"],
                      markeredgecolor="black", markersize=8, label="Pós (> 2017-07-01)"),
               Line2D([0], [0], color="black", ls="--", lw=1.3, label="Tendência (linear)")]
    fig.legend(handles=handles, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.suptitle(f"{nome_emp} - Tendência temporal dos índices alfa",
                 fontsize=16, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(pasta / "02a_painel_temporal.png")
    plt.close(fig)

    return reg_tab


# ---------------------------------------------------------------------------
# Bloco 3 - Estrutura da comunidade
# ---------------------------------------------------------------------------
def pcoa(dist: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """PCoA classica (Gower) sobre matriz de distancia simetrica."""
    n = dist.shape[0]
    A = -0.5 * dist ** 2
    J = np.eye(n) - np.ones((n, n)) / n
    B = J @ A @ J
    w, v = np.linalg.eigh(B)
    idx = np.argsort(w)[::-1]
    w = w[idx]
    v = v[:, idx]
    w_pos = np.clip(w, 0, None)
    coords = v * np.sqrt(w_pos)
    return coords, w_pos / w_pos.sum() if w_pos.sum() > 0 else w_pos


def bloco_3_estrutura(df_emp: pd.DataFrame, pasta: Path, nome_emp: str) -> pd.DataFrame:
    mkdirs(pasta)

    # Matriz campanha x especie (CPUEn agregado)
    mat = (df_emp.groupby(["nome_campanha", "data_campanha", "fase",
                           "nome_cientifico"], as_index=False)["cpue_n"].sum()
                 .pivot_table(index=["nome_campanha", "data_campanha", "fase"],
                              columns="nome_cientifico", values="cpue_n", fill_value=0))
    mat = mat.sort_index(level="data_campanha")
    if mat.shape[0] < 3:
        return pd.DataFrame()

    meta = mat.index.to_frame(index=False)
    X = mat.to_numpy(dtype=float)
    # Bray-Curtis
    D = squareform(pdist(X, metric="braycurtis"))

    # Exporta matriz e BC
    mat.to_excel(pasta / "03_matriz_campanha_x_especie_CPUEn.xlsx")
    pd.DataFrame(D, index=mat.index.get_level_values("nome_campanha"),
                 columns=mat.index.get_level_values("nome_campanha")
                 ).to_excel(pasta / "03_braycurtis_campanha.xlsx")

    # 3a - Heatmap de similaridade (1-BC) temporal
    sim = 1.0 - D
    labels = meta["nome_campanha"].tolist()
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(sim, ax=ax, cmap="YlGnBu", vmin=0, vmax=1, square=True,
                xticklabels=labels, yticklabels=labels,
                cbar_kws={"label": "Similaridade (1 - Bray-Curtis)"})
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    fig.suptitle(f"{nome_emp} - Similaridade temporal (Bray-Curtis)",
                 fontsize=16, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(pasta / "03a_heatmap_similaridade.png")
    plt.close(fig)

    # 3b - PCoA Pre vs Pos
    coords, var_exp = pcoa(D)
    fig, ax = plt.subplots(figsize=(13, 10))
    for fase, sub in meta.groupby("fase"):
        idx = sub.index
        ax.scatter(coords[idx, 0], coords[idx, 1],
                   s=85, color=COR_FASE[fase],
                   edgecolor="black", linewidth=0.5, alpha=0.85,
                   label=f"{fase} (n={len(idx)})")
    # Anotacoes leves nos pontos extremos
    for i, lab in enumerate(labels):
        if i in (0, len(labels) - 1):
            ax.annotate(lab, (coords[i, 0], coords[i, 1]),
                        fontsize=9, xytext=(5, 5), textcoords="offset points")
    ax.set_xlabel(f"PCoA1 ({var_exp[0]*100:.1f}%)")
    ax.set_ylabel(f"PCoA2 ({var_exp[1]*100:.1f}%)")
    ax.axhline(0, color="lightgray", lw=0.7)
    ax.axvline(0, color="lightgray", lw=0.7)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False)
    fig.suptitle(f"{nome_emp} - PCoA das campanhas (Bray-Curtis sobre CPUEn)",
                 fontsize=16, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(pasta / "03b_pcoa_campanhas.png")
    plt.close(fig)

    # 3c - Dendrograma temporal (UPGMA)
    Z = hierarchy.linkage(pdist(X, metric="braycurtis"), method="average")
    fig, ax = plt.subplots(figsize=(16, 8))
    hierarchy.dendrogram(Z, labels=labels, leaf_rotation=90, ax=ax,
                         color_threshold=0.7 * Z[:, 2].max())
    ax.set_ylabel("Distância Bray-Curtis (UPGMA)")
    fig.suptitle(f"{nome_emp} - Cluster temporal das campanhas",
                 fontsize=16, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(pasta / "03c_dendrograma_temporal.png")
    plt.close(fig)

    # Coordenadas PCoA para arquivo
    pd.DataFrame({
        "nome_campanha": meta["nome_campanha"],
        "data_campanha": meta["data_campanha"],
        "fase": meta["fase"],
        "PCoA1": coords[:, 0],
        "PCoA2": coords[:, 1],
        "PCoA3": coords[:, 2] if coords.shape[1] > 2 else np.nan,
    }).to_excel(pasta / "03_pcoa_coords.xlsx", index=False)

    return meta.assign(_dummy=0)  # retorno simbólico


# ---------------------------------------------------------------------------
# Bloco 4 - ANOSIM + PERMANOVA (permutacao)
# ---------------------------------------------------------------------------
def _anosim(D: np.ndarray, groups: np.ndarray, perms: int = 999, seed: int = 42) -> dict:
    """ANOSIM (R, p) classico de Clarke."""
    n = D.shape[0]
    iu = np.triu_indices(n, k=1)
    d = D[iu]
    r = stats.rankdata(d)
    same = (groups[iu[0]] == groups[iu[1]])
    rW = r[same].mean()
    rB = r[~same].mean()
    R = (rB - rW) / (n * (n - 1) / 4.0)

    rng = np.random.default_rng(seed)
    perm_R = np.empty(perms)
    g = groups.copy()
    for i in range(perms):
        rng.shuffle(g)
        same = (g[iu[0]] == g[iu[1]])
        rW_p = r[same].mean()
        rB_p = r[~same].mean()
        perm_R[i] = (rB_p - rW_p) / (n * (n - 1) / 4.0)
    p = (np.sum(perm_R >= R) + 1) / (perms + 1)
    return {"R": float(R), "p": float(p), "n_perms": perms}


def _permanova(D: np.ndarray, groups: np.ndarray, perms: int = 999, seed: int = 42) -> dict:
    """PERMANOVA (pseudo-F, p) - Anderson 2001, 1 fator."""
    n = D.shape[0]
    a, _ = np.unique(groups, return_counts=True)
    a_n = len(a)

    def _F(g):
        SS_T = (D ** 2).sum() / (2 * n)
        SS_W = 0.0
        for lvl in a:
            idx = np.where(g == lvl)[0]
            if len(idx) < 2:
                continue
            sub = D[np.ix_(idx, idx)]
            SS_W += (sub ** 2).sum() / (2 * len(idx))
        SS_A = SS_T - SS_W
        df_A = a_n - 1
        df_W = n - a_n
        if df_W <= 0 or SS_W <= 0:
            return np.nan
        return (SS_A / df_A) / (SS_W / df_W)

    F_obs = _F(groups)
    rng = np.random.default_rng(seed)
    perm_F = np.empty(perms)
    g = groups.copy()
    for i in range(perms):
        rng.shuffle(g)
        perm_F[i] = _F(g)
    perm_F = perm_F[np.isfinite(perm_F)]
    p = (np.sum(perm_F >= F_obs) + 1) / (perm_F.size + 1)
    return {"pseudoF": float(F_obs), "p": float(p),
            "n_perms": int(perm_F.size)}


def bloco_4_anosim_permanova(df_emp: pd.DataFrame, pasta: Path,
                              nome_emp: str) -> pd.DataFrame:
    mkdirs(pasta)
    mat = (df_emp.groupby(["nome_campanha", "fase", "nome_cientifico"],
                          as_index=False)["cpue_n"].sum()
                 .pivot_table(index=["nome_campanha", "fase"],
                              columns="nome_cientifico",
                              values="cpue_n", fill_value=0))
    meta = mat.index.to_frame(index=False)
    if meta["fase"].nunique() < 2 or len(meta) < 6:
        return pd.DataFrame()
    X = mat.to_numpy(dtype=float)
    D = squareform(pdist(X, metric="braycurtis"))
    groups = meta["fase"].to_numpy()

    res_an = _anosim(D, groups)
    res_pm = _permanova(D, groups)

    tab = pd.DataFrame([
        {"teste": "ANOSIM",    "estatistica": res_an["R"],
         "p_valor": res_an["p"], "n_permutacoes": res_an["n_perms"]},
        {"teste": "PERMANOVA", "estatistica": res_pm["pseudoF"],
         "p_valor": res_pm["p"], "n_permutacoes": res_pm["n_perms"]},
    ])
    tab["fator"] = "Pre vs Pos"
    tab.to_excel(pasta / "04_anosim_permanova.xlsx", index=False)

    # Plot resumo
    fig, ax = plt.subplots(figsize=(12, 6))
    xs = np.arange(2)
    vals = [res_an["R"], res_pm["pseudoF"]]
    pvals = [res_an["p"], res_pm["p"]]
    cols = ["#1f77b4", "#d62728"]
    bars = ax.bar(xs, vals, color=cols, edgecolor="black")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"ANOSIM R = {res_an['R']:.3f}",
                        f"PERMANOVA F = {res_pm['pseudoF']:.3f}"])
    for b, p in zip(bars, pvals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                f"p = {p:.3g}", ha="center", va="bottom", fontsize=12)
    ax.set_ylabel("Estatística")
    fig.suptitle(f"{nome_emp} - Diferença Pré × Pós (Bray-Curtis)",
                 fontsize=16, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(pasta / "04a_resumo_anosim_permanova.png")
    plt.close(fig)

    return tab


# ---------------------------------------------------------------------------
# Bloco 5 - Beta diversidade temporal (Sorensen + Baselga)
# ---------------------------------------------------------------------------
def _baselga_pair(p1: np.ndarray, p2: np.ndarray) -> tuple[float, float, float]:
    """Devolve (beta_sor, beta_sim_turnover, beta_nes_nestedness)."""
    p1 = p1 > 0
    p2 = p2 > 0
    a = int(np.sum(p1 & p2))
    b = int(np.sum(p1 & ~p2))
    c = int(np.sum(~p1 & p2))
    denom = (2 * a + b + c)
    if denom == 0:
        return 0.0, 0.0, 0.0
    beta_sor = (b + c) / denom
    if (a + min(b, c)) == 0:
        beta_sim = 0.0
    else:
        beta_sim = min(b, c) / (a + min(b, c))
    beta_nes = beta_sor - beta_sim
    return float(beta_sor), float(beta_sim), float(beta_nes)


def bloco_5_beta_temporal(df_emp: pd.DataFrame, pasta: Path,
                          nome_emp: str) -> pd.DataFrame:
    mkdirs(pasta)
    mat = (df_emp.groupby(["nome_campanha", "data_campanha", "fase",
                           "nome_cientifico"], as_index=False)["contagem"].sum()
                 .pivot_table(index=["nome_campanha", "data_campanha", "fase"],
                              columns="nome_cientifico",
                              values="contagem", fill_value=0))
    mat = mat.sort_index(level="data_campanha")
    if mat.shape[0] < 3:
        return pd.DataFrame()
    meta = mat.index.to_frame(index=False)
    X = mat.to_numpy(dtype=float)

    # Pares consecutivos no tempo
    rows = []
    for i in range(len(meta) - 1):
        sor, sim, nes = _baselga_pair(X[i], X[i + 1])
        rows.append({
            "campanha_t":    meta.loc[i, "nome_campanha"],
            "campanha_t1":   meta.loc[i + 1, "nome_campanha"],
            "data_t":        meta.loc[i, "data_campanha"],
            "data_t1":       meta.loc[i + 1, "data_campanha"],
            "fase_t":        meta.loc[i, "fase"],
            "fase_t1":       meta.loc[i + 1, "fase"],
            "beta_sor":      sor,
            "beta_sim_turnover":   sim,
            "beta_nes_nestedness": nes,
        })
    tab = pd.DataFrame(rows)
    tab.to_excel(pasta / "05_beta_temporal_pares_consecutivos.xlsx", index=False)

    # Plot: linha temporal de turnover x nestedness
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(tab["data_t1"], tab["beta_sor"], "-o", color="black",
            lw=1.4, ms=6, label="β Sorensen (total)")
    ax.plot(tab["data_t1"], tab["beta_sim_turnover"], "-s",
            color="#1f77b4", lw=1.2, ms=5, label="β Simpson (turnover)")
    ax.plot(tab["data_t1"], tab["beta_nes_nestedness"], "-^",
            color="#d62728", lw=1.2, ms=5, label="β Nestedness")
    ax.axvline(CORTE_PRE_POS, color="firebrick", lw=1.0, ls=":", alpha=0.7)
    ax.set_ylim(0, 1)
    ax.set_xlabel("")
    ax.set_ylabel("β-diversidade entre campanhas consecutivas")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3, frameon=False)
    fig.suptitle(f"{nome_emp} - β-diversidade temporal (Baselga)",
                 fontsize=16, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(pasta / "05a_beta_temporal.png")
    plt.close(fig)

    # Pre x Pos: medias e desvios
    res = (tab.groupby("fase_t1")[["beta_sor", "beta_sim_turnover",
                                   "beta_nes_nestedness"]]
              .agg(["mean", "std", "count"])
              .round(3))
    res.to_excel(pasta / "05_beta_resumo_por_fase.xlsx")

    return tab


# ---------------------------------------------------------------------------
# Bloco 5b - Beta-Legendre por campanha + LCBD por ponto + ITS
# (Legendre & De Caceres 2013; Ferreira et al. 2026)
# ---------------------------------------------------------------------------
def _hellinger(X: np.ndarray) -> np.ndarray:
    """Transformação de Hellinger (Legendre & Gallagher 2001)."""
    rs = X.sum(axis=1, keepdims=True)
    rs[rs == 0] = 1.0
    return np.sqrt(X / rs)


def _beta_legendre(Xh: np.ndarray) -> tuple[float, np.ndarray]:
    """Beta como variança (Legendre & De Cáceres 2013) + LCBD por amostra.
    Recebe matriz Hellinger-transformada. Retorna (beta_total, lcbd_array)."""
    n = Xh.shape[0]
    if n < 2:
        return float("nan"), np.zeros(n)
    centered = Xh - Xh.mean(axis=0, keepdims=True)
    SS_i = (centered ** 2).sum(axis=1)
    SS_total = float(SS_i.sum())
    beta = SS_total / (n - 1)
    lcbd = (SS_i / SS_total) if SS_total > 0 else np.zeros(n)
    return float(beta), lcbd


def _its_ols(y: np.ndarray, t: np.ndarray, I: np.ndarray) -> dict:
    """Interrupted Time Series por OLS: y = a + b*t + delta*I + tau*(I*t).
    Retorna coeficientes + erros padrão + p-valores + b+tau (tendência pós)."""
    mask = np.isfinite(y) & np.isfinite(t)
    y = y[mask]; t = t[mask]; I = I[mask]
    n = len(y)
    if n < 6 or len(np.unique(I)) < 2:
        return {}
    X = np.column_stack([np.ones(n), t, I, I * t])
    coefs, *_ = np.linalg.lstsq(X, y, rcond=None)
    a, b, delta, tau = coefs
    resid = y - X @ coefs
    df_res = n - X.shape[1]
    if df_res <= 0:
        return {}
    sigma2 = float((resid ** 2).sum() / df_res)
    try:
        cov = sigma2 * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(cov))
        tstat = coefs / se
        pvals = 2 * (1 - stats.t.cdf(np.abs(tstat), df_res))
    except np.linalg.LinAlgError:
        se = np.full(4, np.nan); pvals = np.full(4, np.nan)
    # SE de (b+tau) via variação: var(b+tau) = var(b) + var(tau) + 2 cov(b,tau)
    try:
        var_btau = cov[1, 1] + cov[3, 3] + 2 * cov[1, 3]
        se_btau = float(np.sqrt(max(var_btau, 0)))
        t_btau = (b + tau) / se_btau if se_btau > 0 else np.nan
        p_btau = 2 * (1 - stats.t.cdf(abs(t_btau), df_res)) if np.isfinite(t_btau) else np.nan
    except Exception:
        se_btau = np.nan; p_btau = np.nan
    # Durbin-Watson (diagnóstico de autocorrelação)
    dw = float(np.sum(np.diff(resid) ** 2) / np.sum(resid ** 2)) if (resid ** 2).sum() > 0 else np.nan
    return {
        "a": float(a), "b": float(b), "delta": float(delta), "tau": float(tau),
        "se": se.tolist() if hasattr(se, "tolist") else list(se),
        "p": pvals.tolist() if hasattr(pvals, "tolist") else list(pvals),
        "b_plus_tau": float(b + tau), "se_b_plus_tau": se_btau,
        "p_b_plus_tau": float(p_btau) if np.isfinite(p_btau) else np.nan,
        "DW": dw, "n": int(n),
        "fitted": (X @ coefs).tolist(),
        "t_used": t.tolist(), "y_used": y.tolist(), "I_used": I.tolist(),
    }


def bloco_5b_legendre_its(df_emp: pd.DataFrame, pasta: Path,
                          nome_emp: str) -> dict:
    """β-Legendre por campanha (variação entre pontos), LCBD por ponto e ITS."""
    mkdirs(pasta)

    # --- (i) beta-Legendre por campanha (variancia entre pontos) ---
    rows = []
    for (dt, camp, fase), g in df_emp.groupby(["data_campanha", "nome_campanha", "fase"]):
        M = (g.groupby(["nome_ponto", "nome_cientifico"], as_index=False)["cpue_n"].sum()
               .pivot_table(index="nome_ponto", columns="nome_cientifico",
                            values="cpue_n", fill_value=0))
        if M.shape[0] < 2 or M.shape[1] < 2:
            continue
        Xh = _hellinger(M.to_numpy(dtype=float))
        beta, _ = _beta_legendre(Xh)
        rows.append({"data_campanha": dt, "nome_campanha": camp,
                     "fase": fase, "n_pontos": int(M.shape[0]),
                     "beta_legendre": beta})
    tab_bL = pd.DataFrame(rows).sort_values("data_campanha").reset_index(drop=True)
    tab_bL.to_excel(pasta / "05b_beta_legendre_por_campanha.xlsx", index=False)

    # --- (ii) ITS sobre beta-Legendre temporal ---
    its = {}
    if not tab_bL.empty:
        y = tab_bL["beta_legendre"].to_numpy()
        # tempo em meses desde a primeira campanha
        t0 = tab_bL["data_campanha"].min()
        t = ((tab_bL["data_campanha"] - t0).dt.days / 30.0).to_numpy()
        I = tab_bL["fase"].eq("Pos").astype(int).to_numpy()
        its = _its_ols(y, t, I)
        # classificação ecológica
        if its:
            bt = its["b_plus_tau"]
            p_bt = its["p_b_plus_tau"]
            delta = its["delta"]; p_delta = its["p"][2] if its["p"] else np.nan
            if np.isfinite(p_bt) and p_bt < 0.05 and bt > 0:
                interp = "Diferenciação biótica em curso na Pós (β crescente)"
            elif np.isfinite(p_bt) and p_bt < 0.05 and bt < 0:
                interp = "Homogeneização biótica em curso na Pós (β decrescente)"
            elif np.isfinite(p_bt) and p_bt >= 0.05:
                interp = "Sem tendência direcional na Pós (compatível com equilíbrio)"
            else:
                interp = "Inconclusivo"
            its["interpretacao"] = interp
            its["salto_delta"] = ("+" if delta > 0 else "-") + f"{abs(delta):.3f}"
            its["salto_significativo"] = bool(
                np.isfinite(p_delta) and p_delta < 0.05)

        # exporta resumo
        if its:
            its_summary = pd.DataFrame([{
                "parametro": k,
                "valor": (round(v, 4) if isinstance(v, (int, float)) and np.isfinite(v) else v),
            } for k, v in its.items()
              if k not in ("fitted", "t_used", "y_used", "I_used", "se", "p")])
            its_summary.to_excel(pasta / "05b_its_resumo.xlsx", index=False)

    # plot beta-Legendre + ajuste ITS
    if not tab_bL.empty:
        fig, ax = plt.subplots(figsize=(15, 8))
        for fase, sub in tab_bL.groupby("fase"):
            ax.scatter(sub["data_campanha"], sub["beta_legendre"],
                       s=55, color=COR_FASE[fase],
                       edgecolor="black", linewidth=0.4,
                       label=f"β-Legendre (n campanhas {fase}={len(sub)})")
        ax.plot(tab_bL["data_campanha"], tab_bL["beta_legendre"],
                color="gray", lw=0.7, alpha=0.6)
        if its and "fitted" in its:
            # remapear t_used -> datas
            t0 = tab_bL["data_campanha"].min()
            datas = [t0 + pd.Timedelta(days=int(tt * 30)) for tt in its["t_used"]]
            # plotar duas linhas (pré e pós) separadamente para evitar conexão no salto
            arr_I = np.array(its["I_used"]); arr_f = np.array(its["fitted"]); arr_d = np.array(datas)
            for lvl, c in [(0, COR_FASE["Pre"]), (1, COR_FASE["Pos"])]:
                m = arr_I == lvl
                if m.sum() >= 2:
                    order = np.argsort(arr_d[m])
                    ax.plot(arr_d[m][order], arr_f[m][order],
                            color=c, lw=2.0, alpha=0.9)
            ax.text(0.02, 0.97,
                    f"ITS: δ={its['delta']:.3f} (p={its['p'][2]:.3g})  |  "
                    f"b+τ={its['b_plus_tau']:.4f}/mês (p={its['p_b_plus_tau']:.3g})\n"
                    f"DW={its['DW']:.2f}  |  {its.get('interpretacao','')}",
                    transform=ax.transAxes, ha="left", va="top", fontsize=11,
                    bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9))
        ax.axvline(CORTE_PRE_POS, color="firebrick", lw=1.0, ls=":", alpha=0.8)
        ax.set_ylabel("β-Legendre (variância entre pontos / campanha)")
        ax.set_xlabel("")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False)
        fig.suptitle(f"{nome_emp} - β-diversidade espacial (Legendre) + ITS",
                     fontsize=15, y=0.99)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(pasta / "05b_beta_legendre_its.png")
        plt.close(fig)

    # --- (iii) LCBD por ponto (separado por fase) ---
    lcbd_rows = []
    for fase in ["Pre", "Pos"]:
        sub = df_emp[df_emp["fase"].eq(fase)]
        if sub.empty:
            continue
        # cada amostra = ponto x campanha (preserva múltiplas observações por ponto)
        M = (sub.groupby(["nome_ponto", "nome_campanha", "nome_cientifico"],
                         as_index=False)["cpue_n"].sum()
                .pivot_table(index=["nome_ponto", "nome_campanha"],
                             columns="nome_cientifico",
                             values="cpue_n", fill_value=0))
        if M.shape[0] < 2 or M.shape[1] < 2:
            continue
        Xh = _hellinger(M.to_numpy(dtype=float))
        _, lcbd = _beta_legendre(Xh)
        meta = M.index.to_frame(index=False)
        meta["LCBD"] = lcbd
        meta["fase"] = fase
        # média por ponto (já que LCBD aqui é por amostra ponto+campanha)
        agg = meta.groupby(["nome_ponto", "fase"], as_index=False)["LCBD"].mean()
        lcbd_rows.append(agg)
    if lcbd_rows:
        tab_lcbd = pd.concat(lcbd_rows, ignore_index=True)
        tab_lcbd.to_excel(pasta / "05b_lcbd_por_ponto_fase.xlsx", index=False)

        # plot LCBD por ponto (Pre vs Pos)
        order_pts = (tab_lcbd.groupby("nome_ponto")["LCBD"].mean()
                              .sort_values(ascending=False).index.tolist())
        fig, ax = plt.subplots(figsize=(15, 8))
        width = 0.4
        xs = np.arange(len(order_pts))
        for i, fase in enumerate(["Pre", "Pos"]):
            vals = [float(tab_lcbd[(tab_lcbd["nome_ponto"].eq(p)) &
                                    (tab_lcbd["fase"].eq(fase))]["LCBD"].mean())
                    if ((tab_lcbd["nome_ponto"].eq(p)) &
                        (tab_lcbd["fase"].eq(fase))).any() else 0.0
                    for p in order_pts]
            ax.bar(xs + (i - 0.5) * width, vals, width=width,
                   color=COR_FASE[fase], edgecolor="black", label=fase)
        ax.set_xticks(xs)
        ax.set_xticklabels(order_pts, rotation=45, ha="right")
        ax.set_ylabel("LCBD médio (contribuição do ponto à β-total)")
        ax.legend(frameon=False)
        fig.suptitle(f"{nome_emp} - LCBD por ponto (Pré vs Pós)",
                     fontsize=15, y=0.99)
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        fig.savefig(pasta / "05c_lcbd_por_ponto.png")
        plt.close(fig)
    else:
        tab_lcbd = pd.DataFrame()

    return {"tab_bL": tab_bL, "its": its, "tab_lcbd": tab_lcbd}


# ---------------------------------------------------------------------------
# Bloco 6 - Sintese
# ---------------------------------------------------------------------------
def bloco_6_sintese(nome_emp: str, pasta: Path,
                    tab_alfa: pd.DataFrame,
                    reg_tab: pd.DataFrame,
                    tab_test: pd.DataFrame,
                    tab_beta: pd.DataFrame) -> None:
    mkdirs(pasta)
    lines = []
    lines.append(f"# Síntese - {nome_emp} (Ictiofauna, projeto ITAGUA001)")
    lines.append("Fonte: biota_analise_consolidada | tipo_amostragem=Quantitativa "
                 "| corte Pré/Pós = 2017-07-01")
    lines.append("")

    # Alfa medianas Pre x Pos
    if not tab_alfa.empty:
        agg = (tab_alfa.groupby("fase")[["S", "H", "Simpson", "Pielou",
                                         "N", "biomassa_total",
                                         "cpue_n_total", "cpue_b_total"]]
                       .median().round(3))
        lines.append("## Diversidade alfa (medianas por fase)")
        lines.append(agg.to_string())
        lines.append("")

    # Tendencia (so as significativas)
    if not reg_tab.empty:
        lines.append("## Tendência temporal (regressão linear)")
        lines.append(reg_tab.round(4).to_string(index=False))
        lines.append("")

    # ANOSIM / PERMANOVA
    if not tab_test.empty:
        lines.append("## Pré × Pós (ANOSIM + PERMANOVA - Bray-Curtis)")
        lines.append(tab_test.round(4).to_string(index=False))
        lines.append("")

    # Beta resumida
    if not tab_beta.empty:
        beta_med = (tab_beta.groupby("fase_t1")[["beta_sor",
                                                 "beta_sim_turnover",
                                                 "beta_nes_nestedness"]]
                            .median().round(3))
        lines.append("## β-diversidade temporal (medianas por fase do alvo)")
        lines.append(beta_med.to_string())
        lines.append("")

    lines.append("## Notas interpretativas")
    lines.append("- Análises restritas à amostragem Quantitativa (pontos RP*),")
    lines.append("  que padronizam o esforço (m²/100) e permitem CPUE.")
    lines.append("- O objetivo é descritivo/exploratório (estabilidade ecológica,")
    lines.append("  reorganização da assembleia, possível homogeneização biótica),")
    lines.append("  não diagnóstico de 'saúde ambiental'.")
    lines.append("- Cortes temporais adicionais (transição/estabilização) podem ser")
    lines.append("  refinados após inspeção dos painéis 02a e 05a.")
    (pasta / "06_sintese.txt").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Bloco 7 - Criterios objetivos de estabilidade
# ---------------------------------------------------------------------------
def bloco_7_estabilidade(nome_emp: str, pasta: Path,
                         suf: dict,
                         tab_alfa: pd.DataFrame,
                         reg_tab: pd.DataFrame,
                         tab_beta: pd.DataFrame,
                         tab_test: pd.DataFrame,
                         bloco5b: dict | None = None) -> dict:
    """6 criterios binários (0/1). Score 0-6: 6=altamente estável; 0-2=instável.
    Refs: Agostinho et al. (2016), Hoeinghaus et al., Petesse et al.,
    Legendre & De Cáceres (2013), Baselga (2010), Ferreira et al. (2026)."""
    mkdirs(pasta)

    crit = []
    # C1 - Suficiencia amostral na fase Pos >= 0.85 (cobertura S_obs/Chao2)
    c1_val = suf.get("cob_pos", np.nan)
    c1_ok = bool(np.isfinite(c1_val) and c1_val >= 0.85)
    crit.append(("C1 Suficiência amostral (Pós) ≥ 0.85",
                 round(float(c1_val), 3) if np.isfinite(c1_val) else np.nan, c1_ok))

    # C2 - Sem tendencia significativa na fase Pos para H' e CPUEn (p_pos > 0.05)
    c2_ok = False; c2_detail = np.nan
    if not reg_tab.empty:
        try:
            p_h   = float(reg_tab.loc[reg_tab["metrica"].eq("Shannon (H')"), "p_pos"].iloc[0])
            p_cn  = float(reg_tab.loc[reg_tab["metrica"].eq("CPUEn total (ind/100m²)"), "p_pos"].iloc[0])
            c2_ok = (p_h > 0.05) and (p_cn > 0.05)
            c2_detail = f"p(H'_pos)={p_h:.3g}; p(CPUEn_pos)={p_cn:.3g}"
        except (IndexError, KeyError, ValueError):
            pass
    crit.append(("C2 Estabilidade alfa na Pós (H' e CPUEn s/ tendência)", c2_detail, c2_ok))

    # C3 - CV (S, H') na Pos <= CV na Pre (variabilidade nao aumentou)
    c3_ok = False; c3_detail = np.nan
    if not tab_alfa.empty:
        def _cv(s):
            return float(s.std() / s.mean()) if s.mean() != 0 else np.nan
        try:
            pre = tab_alfa[tab_alfa["fase"].eq("Pre")]
            pos = tab_alfa[tab_alfa["fase"].eq("Pos")]
            cv_s_pre, cv_s_pos = _cv(pre["S"]), _cv(pos["S"])
            cv_h_pre, cv_h_pos = _cv(pre["H"]), _cv(pos["H"])
            c3_ok = (cv_s_pos <= cv_s_pre) and (cv_h_pos <= cv_h_pre)
            c3_detail = (f"CV_S Pre={cv_s_pre:.2f}, Pos={cv_s_pos:.2f}; "
                         f"CV_H Pre={cv_h_pre:.2f}, Pos={cv_h_pos:.2f}")
        except Exception:
            pass
    crit.append(("C3 CV(S,H') na Pós ≤ CV na Pré", c3_detail, c3_ok))

    # C4 - Turnover (Baselga) domina nestedness na fase Pos
    c4_ok = False; c4_detail = np.nan
    if not tab_beta.empty:
        pos_b = tab_beta[tab_beta["fase_t1"].eq("Pos")]
        if not pos_b.empty:
            m_sim = float(pos_b["beta_sim_turnover"].median())
            m_nes = float(pos_b["beta_nes_nestedness"].median())
            c4_ok = m_sim > m_nes
            c4_detail = f"β_sim_pos={m_sim:.3f}; β_nes_pos={m_nes:.3f}"
    crit.append(("C4 Turnover > Nestedness na Pós (reorganização, não perda)",
                 c4_detail, c4_ok))

    # C5 - beta_sor mediana Pos <= 0.4 (baixa rotatividade entre campanhas)
    c5_ok = False; c5_val = np.nan
    if not tab_beta.empty:
        pos_b = tab_beta[tab_beta["fase_t1"].eq("Pos")]
        if not pos_b.empty:
            c5_val = float(pos_b["beta_sor"].median())
            c5_ok = c5_val <= 0.4
    crit.append(("C5 β-Sorensen mediana Pós ≤ 0.40 (baixa rotatividade)",
                 round(c5_val, 3) if np.isfinite(c5_val) else np.nan, c5_ok))

    # C6 - ITS sobre β-Legendre: b+τ nao positivo significativo na Pós
    # (i.e., sem diferenciação biótica em curso -> compatível com equilíbrio
    # ou homogeneização; conforme Ferreira et al. 2026).
    c6_ok = False; c6_detail = np.nan
    if bloco5b and bloco5b.get("its"):
        its = bloco5b["its"]
        bt = its.get("b_plus_tau", np.nan)
        p_bt = its.get("p_b_plus_tau", np.nan)
        if np.isfinite(bt) and np.isfinite(p_bt):
            # OK se: (a) tendência pós não positiva significativa
            c6_ok = not (p_bt < 0.05 and bt > 0)
            c6_detail = (f"b+τ={bt:.4f}/mês (p={p_bt:.3g}) | "
                         + its.get("interpretacao", ""))
    crit.append(("C6 ITS β-Legendre: sem diferenciação biótica em curso",
                 c6_detail, c6_ok))

    score = int(sum(1 for _, _, ok in crit if ok))
    if score >= 6:
        classe = "Altamente estável"
    elif score == 5:
        classe = "Estável com ressalvas"
    elif score in (3, 4):
        classe = "Estabilidade parcial"
    else:
        classe = "Instável / em reorganização"

    tab = pd.DataFrame([{"criterio": k, "valor": v, "atende": ok}
                        for k, v, ok in crit])
    tab.to_excel(pasta / "07_criterios_estabilidade.xlsx", index=False)

    # Painel-resumo (6 indicadores)
    fig, ax = plt.subplots(figsize=(14, 7))
    cols = ["#2ca02c" if ok else "#d62728" for _, _, ok in crit]
    ys = np.arange(len(crit))[::-1]
    ax.barh(ys, [1] * len(crit), color=cols, edgecolor="black")
    for y, (k, v, ok) in zip(ys, crit):
        txt = f"  {'OK' if ok else 'NAO'}   {k}    [{v}]"
        ax.text(0.01, y, txt, va="center", ha="left", fontsize=12, color="white")
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    fig.suptitle(f"{nome_emp} - Estabilidade: {score}/6 ({classe})",
                 fontsize=16, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(pasta / "07a_estabilidade_score.png")
    plt.close(fig)

    return {"score": score, "classe": classe, "criterios": crit}


# ---------------------------------------------------------------------------
# Paineis comparativos (entre os 4 empreendimentos)
# ---------------------------------------------------------------------------
def painel_comparativo(resultados: dict, base: Path) -> None:
    """Painel 2x3: S, H, CPUEn, beta_sor consecutivo, beta-Legendre por campanha,
    score de estabilidade. Tudo sobreposto por empreendimento."""
    pasta = base / "_painel_comparativo"
    mkdirs(pasta)

    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    metricas = [("S",            "Riqueza (S)"),
                ("H",            "Shannon (H')"),
                ("cpue_n_total", "CPUEn total (ind/100m²)"),
                ("BETA",         "β-Sorensen entre campanhas consecutivas"),
                ("BETA_L",       "β-Legendre por campanha (Hellinger)"),
                ("SCORE",        "Score de estabilidade (0-6)")]

    for ax, (col, label) in zip(axes.ravel(), metricas):
        if col == "SCORE":
            nomes  = list(resultados.keys())
            scores = [resultados[n]["estab"]["score"] for n in nomes]
            cores  = [COR_EMPREENDIMENTO.get(n, "gray") for n in nomes]
            bars = ax.bar(nomes, scores, color=cores, edgecolor="black")
            for b, s, n in zip(bars, scores, nomes):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05,
                        f"{s}/6\n{resultados[n]['estab']['classe']}",
                        ha="center", va="bottom", fontsize=9)
            ax.set_ylim(0, 6.8)
            ax.axhline(5, color="gray", ls=":", lw=1.0, alpha=0.6)
            plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=10)
            ax.set_ylabel(label)
            continue
        for nome_emp, res in resultados.items():
            cor = COR_EMPREENDIMENTO.get(nome_emp, "gray")
            if col == "BETA":
                tb = res.get("tab_beta", pd.DataFrame())
                if tb.empty:
                    continue
                ax.plot(tb["data_t1"], tb["beta_sor"], "-o",
                        color=cor, lw=1.4, ms=4, alpha=0.85, label=nome_emp)
            elif col == "BETA_L":
                b5 = res.get("bloco5b", {})
                tb = b5.get("tab_bL", pd.DataFrame()) if b5 else pd.DataFrame()
                if tb.empty:
                    continue
                ax.plot(tb["data_campanha"], tb["beta_legendre"], "-o",
                        color=cor, lw=1.4, ms=4, alpha=0.85, label=nome_emp)
            else:
                ta = res.get("tab_alfa", pd.DataFrame())
                if ta.empty:
                    continue
                ax.plot(ta["data_campanha"], ta[col], "-o",
                        color=cor, lw=1.4, ms=4, alpha=0.85, label=nome_emp)
        ax.axvline(CORTE_PRE_POS, color="firebrick", lw=1.0, ls=":", alpha=0.7)
        ax.set_ylabel(label)
        ax.set_xlabel("")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center",
               bbox_to_anchor=(0.5, 1.02), ncol=len(labels), frameon=False)
    fig.suptitle("Painel comparativo - 4 empreendimentos (Guanhães Energia)",
                 fontsize=17, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(pasta / "painel_comparativo_metricas.png")
    plt.close(fig)

    # Painel 2: scores de estabilidade em barras (versão standalone)
    fig, ax = plt.subplots(figsize=(13, 7))
    nomes = list(resultados.keys())
    scores = [resultados[n]["estab"]["score"] for n in nomes]
    classes = [resultados[n]["estab"]["classe"] for n in nomes]
    cores = [COR_EMPREENDIMENTO.get(n, "gray") for n in nomes]
    bars = ax.bar(nomes, scores, color=cores, edgecolor="black")
    for b, s, c in zip(bars, scores, classes):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05,
                f"{s}/6\n{c}", ha="center", va="bottom", fontsize=11)
    ax.set_ylim(0, 6.8)
    ax.set_ylabel("Score de estabilidade (0-6)")
    ax.axhline(5, color="gray", ls=":", lw=1.0, alpha=0.7)
    fig.suptitle("Score de estabilidade ecológica por empreendimento",
                 fontsize=16, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(pasta / "painel_comparativo_estabilidade.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Análise de cascata (Ganassin et al. 2021, Sci. Total Environ.)
# ---------------------------------------------------------------------------
def _beta_sor_baselga(pa_i: np.ndarray, pa_j: np.ndarray) -> tuple[float, float, float]:
    """Sorensen total + componentes de Baselga (turnover + nestedness)
    entre dois vetores presença/ausência."""
    a = int(((pa_i == 1) & (pa_j == 1)).sum())
    b = int(((pa_i == 1) & (pa_j == 0)).sum())
    c = int(((pa_i == 0) & (pa_j == 1)).sum())
    if (2 * a + b + c) == 0:
        return (np.nan, np.nan, np.nan)
    b_sor = (b + c) / (2 * a + b + c)
    den = (a + min(b, c))
    b_sim = (min(b, c) / den) if den > 0 else 0.0
    b_nes = b_sor - b_sim
    return (b_sor, b_sim, b_nes)


def analise_cascata(df: pd.DataFrame, resultados: dict, base: Path) -> None:
    """Aplica framework de Ganassin et al. (2021) - efeito de cascata
    de reservatórios sobre assembleias de peixes:
        (1) tendência de S, H', N (CPUEn) ao longo da posição na cascata;
        (2) β-Sorensen + decomposição Baselga entre pares de reservatórios
            adjacentes na cascata;
        (3) padrão de nestedness (espécies de jusante ⊆ montante).
    Opera APENAS sobre os 3 reservatórios do rio Guanhães (JAC/SPT/DGN);
    FOR (rio Corrente Grande) entra como referência regional fora-da-cascata.
    Considera apenas a fase Pós-2017-07."""
    pasta = base / "_analise_cascata"
    mkdirs(pasta)

    cascata_emps = [e for e, meta in BACIA_EMP.items()
                    if meta["em_cascata"] and e in resultados]
    cascata_emps.sort(key=lambda e: BACIA_EMP[e]["posicao"])
    fora_emps = [e for e, meta in BACIA_EMP.items()
                 if (not meta["em_cascata"]) and e in resultados]

    if len(cascata_emps) < 2:
        print("   [aviso] cascata com menos de 2 empreendimentos, pulando análise de cascata")
        return

    # (1) tendência alfa ao longo da cascata - usa medianas da fase Pós
    rows = []
    for emp in cascata_emps + fora_emps:
        ta = resultados[emp].get("tab_alfa", pd.DataFrame())
        if ta.empty:
            continue
        pos = ta[ta["fase"].eq("Pos")]
        if pos.empty:
            continue
        meta = BACIA_EMP[emp]
        rows.append({
            "empreendimento": emp,
            "rio": meta["rio"],
            "em_cascata": meta["em_cascata"],
            "posicao": meta["posicao"],
            "S_med_pos": float(pos["S"].median()),
            "H_med_pos": float(pos["H"].median()),
            "CPUEn_med_pos": float(pos["cpue_n_total"].median()),
            "CPUEb_med_pos": float(pos["cpue_b_total"].median()),
        })
    tab_gradiente = pd.DataFrame(rows)
    tab_gradiente.to_excel(pasta / "01_gradiente_cascata.xlsx", index=False)

    sub_casc = tab_gradiente[tab_gradiente["em_cascata"]].sort_values("posicao")
    sub_fora = tab_gradiente[~tab_gradiente["em_cascata"]]

    # Spearman + ajuste linear (informativo; n=3 é baixo, reportar como
    # indicativo, não teste de hipótese)
    grad_stats = {}
    if len(sub_casc) >= 3:
        for col in ["S_med_pos", "H_med_pos", "CPUEn_med_pos", "CPUEb_med_pos"]:
            x = sub_casc["posicao"].to_numpy(dtype=float)
            y = sub_casc[col].to_numpy(dtype=float)
            try:
                rho, p = stats.spearmanr(x, y)
            except Exception:
                rho, p = np.nan, np.nan
            slope, intercept, r, pl, se = stats.linregress(x, y)
            grad_stats[col] = {"rho": float(rho), "p_spearman": float(p),
                               "slope": float(slope), "r2": float(r ** 2),
                               "p_linear": float(pl)}
    pd.DataFrame(grad_stats).T.to_excel(pasta / "02_gradiente_estatistica.xlsx")

    # painel: S, H', CPUEn ao longo da posição (cascata + ponto FOR como referência)
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    for ax, (col, label) in zip(axes, [
        ("S_med_pos",     "Riqueza mediana (Pós)"),
        ("H_med_pos",     "Shannon mediano (Pós)"),
        ("CPUEn_med_pos", "CPUEn mediano Pós (ind/100m²)"),
    ]):
        # cascata Guanhães: linha + pontos coloridos por empreendimento
        ax.plot(sub_casc["posicao"], sub_casc[col],
                color="#444", lw=1.4, zorder=1)
        for _, row in sub_casc.iterrows():
            ax.scatter(row["posicao"], row[col],
                       color=COR_EMPREENDIMENTO.get(row["empreendimento"], "gray"),
                       s=160, edgecolor="black", zorder=3,
                       label=f"{row['empreendimento']} (cascata Guanhães)")
        # FOR como referência regional (fora-cascata) - posição = max+0.8
        if not sub_fora.empty:
            x_fora = sub_casc["posicao"].max() + 0.8
            for _, row in sub_fora.iterrows():
                ax.scatter(x_fora, row[col],
                           color=COR_EMPREENDIMENTO.get(row["empreendimento"], "gray"),
                           s=160, marker="D", edgecolor="black", zorder=3,
                           label=f"{row['empreendimento']} (referência - Corrente Grande)")
        # anotar estatística de gradiente
        st = grad_stats.get(col)
        if st:
            ax.text(0.02, 0.95,
                    f"ρ={st['rho']:.2f} (p={st['p_spearman']:.3g})\n"
                    f"slope={st['slope']:+.2f}; R²={st['r2']:.2f}",
                    transform=ax.transAxes, ha="left", va="top", fontsize=11,
                    bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9))
        ax.set_xlabel("Posição na cascata (montante → jusante)")
        ax.set_ylabel(label)
        # ticks: 1..n_casc, FOR fora
        xt = list(sub_casc["posicao"]) + ([sub_casc["posicao"].max() + 0.8]
                                            if not sub_fora.empty else [])
        xl = [f"{int(p)}\n{e}"
              for p, e in zip(sub_casc["posicao"], sub_casc["empreendimento"])]
        if not sub_fora.empty:
            xl += [f"ref\n{sub_fora.iloc[0]['empreendimento']}"]
        ax.set_xticks(xt); ax.set_xticklabels(xl, fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    # deduplicar legenda
    seen = set(); h2, l2 = [], []
    for h, l in zip(handles, labels):
        if l in seen: continue
        seen.add(l); h2.append(h); l2.append(l)
    fig.legend(h2, l2, loc="upper center", bbox_to_anchor=(0.5, 1.04),
               ncol=min(4, len(l2)), frameon=False, fontsize=10)
    fig.suptitle("Gradiente da cascata - rio Guanhães "
                 "(FOR/Corrente Grande como referência fora-cascata) - fase Pós",
                 fontsize=15, y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(pasta / "03_gradiente_cascata.png")
    plt.close(fig)

    # (2) β-Sorensen + Baselga entre pares (presença/ausência agrupada na Pós)
    df_pos = df[df["data_campanha"] >= CORTE_PRE_POS].copy()
    todos = cascata_emps + fora_emps
    # matriz presença/ausência: empreendimento x espécie
    M = (df_pos.groupby(["nome_empreendimento", "nome_cientifico"], as_index=False)
               ["cpue_n"].sum()
               .pivot_table(index="nome_empreendimento",
                            columns="nome_cientifico",
                            values="cpue_n", fill_value=0))
    M_pa = (M > 0).astype(int)

    pares = []
    for i, e1 in enumerate(todos):
        if e1 not in M_pa.index: continue
        for e2 in todos[i + 1:]:
            if e2 not in M_pa.index: continue
            v1 = M_pa.loc[e1].to_numpy()
            v2 = M_pa.loc[e2].to_numpy()
            b_sor, b_sim, b_nes = _beta_sor_baselga(v1, v2)
            # nestedness assimétrico: prop. de espécies de e_jusante que estão em e_montante
            # (só faz sentido entre os dois da cascata Guanhães)
            if (BACIA_EMP[e1]["em_cascata"] and BACIA_EMP[e2]["em_cascata"]
                    and BACIA_EMP[e1]["rio"] == BACIA_EMP[e2]["rio"]):
                if BACIA_EMP[e1]["posicao"] < BACIA_EMP[e2]["posicao"]:
                    montante, jusante = e1, e2
                else:
                    montante, jusante = e2, e1
                jv = M_pa.loc[jusante]
                mv = M_pa.loc[montante]
                spp_jus = jv[jv > 0].index
                if len(spp_jus) > 0:
                    frac_subset = float((mv[spp_jus] > 0).sum()) / float(len(spp_jus))
                else:
                    frac_subset = np.nan
                dist_pos = abs(BACIA_EMP[e1]["posicao"] - BACIA_EMP[e2]["posicao"])
                tipo = "cascata-Guanhães"
            else:
                frac_subset = np.nan
                dist_pos = np.nan
                tipo = "entre-rios"
            pares.append({
                "emp_1": e1, "emp_2": e2,
                "tipo": tipo, "dist_posicao": dist_pos,
                "beta_sor": b_sor, "beta_sim_turnover": b_sim,
                "beta_nes_nestedness": b_nes,
                "frac_jusante_subset_montante": frac_subset,
            })
    tab_pares = pd.DataFrame(pares)
    tab_pares.to_excel(pasta / "04_pares_beta_baselga.xlsx", index=False)

    # (3) figura: β_sor / β_sim / β_nes vs distância na cascata (só Guanhães)
    casc_pairs = tab_pares[tab_pares["tipo"].eq("cascata-Guanhães")].copy()
    if not casc_pairs.empty:
        fig, ax = plt.subplots(figsize=(15, 7))
        x = casc_pairs["dist_posicao"].to_numpy(dtype=float)
        for col, lbl, cor, mk in [
            ("beta_sor",            "β-Sorensen total",            "#222",    "o"),
            ("beta_sim_turnover",   "β-sim (turnover)",            "#1f77b4", "s"),
            ("beta_nes_nestedness", "β-nes (nestedness)",          "#d62728", "^"),
        ]:
            y = casc_pairs[col].to_numpy(dtype=float)
            ax.scatter(x, y, s=120, color=cor, marker=mk,
                       edgecolor="black", label=lbl, zorder=3)
            if len(np.unique(x)) >= 2:
                sl, ic, r, p, _ = stats.linregress(x, y)
                xs_l = np.linspace(min(x), max(x), 30)
                ax.plot(xs_l, ic + sl * xs_l, ls="--", color=cor, alpha=0.6, lw=1.4)
                ax.text(max(x) + 0.05, ic + sl * max(x),
                        f" slope={sl:+.2f}, R²={r**2:.2f}",
                        color=cor, fontsize=10, va="center")
        # anotar nomes dos pares
        for _, r in casc_pairs.iterrows():
            ax.annotate(f"{r['emp_1'][:3]}-{r['emp_2'][:3]}",
                        (r["dist_posicao"], r["beta_sor"]),
                        xytext=(5, 8), textcoords="offset points", fontsize=9)
        ax.set_xlabel("Distância na cascata (nº de reservatórios)")
        ax.set_ylabel("β-diversidade pareada (presença/ausência, fase Pós)")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08),
                  ncol=3, frameon=False)
        fig.suptitle("β-diversidade ao longo da cascata Guanhães "
                     "(Ganassin et al. 2021 - turnover esperado ↑; nestedness variável)",
                     fontsize=14, y=0.99)
        fig.tight_layout(rect=(0, 0, 1, 0.91))
        fig.savefig(pasta / "05_beta_vs_distancia_cascata.png")
        plt.close(fig)

    # (4) heatmap de subset: linhas = jusante, colunas = montante.
    #     valor = prop. de espécies do jusante que estão no montante.
    casc_only = [e for e in cascata_emps if e in M_pa.index]
    if len(casc_only) >= 2:
        ord_casc = sorted(casc_only, key=lambda e: BACIA_EMP[e]["posicao"])
        mat = np.full((len(ord_casc), len(ord_casc)), np.nan)
        for i, jus in enumerate(ord_casc):
            for j, mon in enumerate(ord_casc):
                if BACIA_EMP[mon]["posicao"] >= BACIA_EMP[jus]["posicao"]:
                    continue
                jv = M_pa.loc[jus]; mv = M_pa.loc[mon]
                spp_jus = jv[jv > 0].index
                if len(spp_jus) == 0: continue
                mat[i, j] = float((mv[spp_jus] > 0).sum()) / float(len(spp_jus))
        fig, ax = plt.subplots(figsize=(11, 8))
        sns.heatmap(mat, annot=True, fmt=".2f", cmap="YlGnBu",
                    xticklabels=ord_casc, yticklabels=ord_casc,
                    cbar_kws={"label": "prop. espécies do jusante presentes no montante"},
                    ax=ax)
        ax.set_xlabel("Montante"); ax.set_ylabel("Jusante")
        fig.suptitle("Nestedness assimétrico - cascata Guanhães "
                     "(espécies de jusante ⊆ montante?)", fontsize=14, y=0.99)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(pasta / "06_nestedness_assimetrico.png")
        plt.close(fig)

    # (5) síntese textual
    lines = []
    lines.append("# Análise de cascata - Guanhães Energia")
    lines.append("Referência teórica: Ganassin et al. (2021, Sci. Total Environ.)")
    lines.append("  - Em cascatas de reservatórios neotropicais, S e diversidade")
    lines.append("    tendem a DECLINAR ao longo da posição (montante -> jusante);")
    lines.append("  - β-Sorensen total e turnover (β-sim) tendem a CRESCER;")
    lines.append("  - Nestedness varia por bacia (em São Francisco: jusante ⊆ montante).")
    lines.append("")
    lines.append("## Estrutura hidrográfica adotada")
    lines.append("  Rio Guanhães (cascata): Jacaré (1) -> Senhora do Porto (2) -> Dores de Guanhães (3)")
    lines.append("  Rio Corrente Grande (isolado, referência regional): Fortuna II")
    lines.append("")
    lines.append("## (1) Gradiente alfa ao longo da cascata (Pós-2017-07, medianas)")
    lines.append(tab_gradiente.round(3).to_string(index=False))
    if grad_stats:
        lines.append("")
        lines.append("## (2) Estatística do gradiente (Spearman + linear; n=3, indicativo)")
        for col, st in grad_stats.items():
            sig = "↓ com cascata" if st["slope"] < 0 else "↑ com cascata"
            lines.append(f"  {col}: ρ={st['rho']:+.2f} (p={st['p_spearman']:.3g}) | "
                         f"slope={st['slope']:+.3f}/posição (R²={st['r2']:.2f}) | {sig}")
    if not tab_pares.empty:
        lines.append("")
        lines.append("## (3) β-diversidade pareada (presença/ausência, fase Pós)")
        lines.append(tab_pares.round(3).to_string(index=False))
    lines.append("")
    lines.append("## Limitações")
    lines.append("- n=3 reservatórios na cascata Guanhães: regressão do gradiente é")
    lines.append("  INDICATIVA, não um teste de hipótese (Ganassin et al. 2021 usaram")
    lines.append("  cascatas de 7-9 reservatórios em Iguacu/Paranapanema/São Francisco).")
    lines.append("- FOR (Corrente Grande) entra como referência regional fora-cascata,")
    lines.append("  NAO como ponto da cascata.")
    lines.append("- Análise da face TAXONÔMICA. Redundância funcional (Ferreira et al. 2026)")
    lines.append("  exigiria matriz de traits ecomorfológicos não disponível no banco.")
    (pasta / "00_sintese_cascata.txt").write_text("\n".join(lines),
                                                   encoding="utf-8")


def conclusao_estabilidade(resultados: dict, base: Path) -> None:
    pasta = base / "_conclusao_estabilidade"
    mkdirs(pasta)

    rows = []
    for nome_emp, res in resultados.items():
        est = res["estab"]
        rows.append({
            "empreendimento": nome_emp,
            "score": est["score"],
            "classificacao": est["classe"],
            **{k: ("OK" if ok else "NAO")
               for k, _, ok in est["criterios"]}
        })
    tab = pd.DataFrame(rows).sort_values("score", ascending=False)
    tab.to_excel(pasta / "conclusao_estabilidade.xlsx", index=False)

    lines = []
    lines.append("# Conclusão - Estabilidade Ecológica da Ictiofauna")
    lines.append("Projeto ITAGUA001 (Guanhães Energia) | Corte Pré/Pós = 2017-07-01")
    lines.append("")
    lines.append("## Marco teórico")
    lines.append("A estabilização de assembleias de peixes em reservatórios neotropicais é avaliada combinando:")
    lines.append("  - Agostinho et al. (2016): trophic upsurge → equilíbrio dinâmico;")
    lines.append("  - Legendre & De Cáceres (2013): β-diversidade como variância entre")
    lines.append("    unidades amostrais + LCBD (contribuição local à β-total);")
    lines.append("  - Baselga (2010): decomposição de β-Sorensen em turnover (β-sim)")
    lines.append("    + nestedness (β-nes);")
    lines.append("  - Ferreira et al. (2026, Hydrobiologia): ITS aplicado a damming")
    lines.append("    em reservatório neotropical (Serra da Mesa, 15 anos) - achados:")
    lines.append("    diferenciação taxonômica imediata após o barramento, oscilação")
    lines.append("    com leve homogeneização no longo prazo (compatível com equilíbrio")
    lines.append("    trófico), e REDUNDÂNCIA FUNCIONAL (a face funcional pode")
    lines.append("    permanecer estável mesmo com reorganização taxonômica).")
    lines.append("  - Ganassin et al. (2021, Sci. Total Environ.): em cascatas de")
    lines.append("    reservatórios, S/diversidade DECLINAM ao longo da posição,")
    lines.append("    β-Sorensen e turnover CRESCEM, abundância tende a CAIR.")
    lines.append("")
    lines.append("Critérios objetivos adotados aqui (score 0-6):")
    lines.append("  C1 saturação da curva de suficiência (cobertura Chao2 ≥ 0,85);")
    lines.append("  C2 ausência de tendência direcional dos alfa-índices na Pós;")
    lines.append("  C3 não aumento da variabilidade temporal (CV Pós ≤ CV Pré);")
    lines.append("  C4 predomínio de turnover sobre nestedness na Pós (reorganização, não perda líquida);")
    lines.append("  C5 β-Sorensen mediana Pós ≤ 0,40 (baixa rotatividade entre campanhas);")
    lines.append("  C6 ITS sobre β-Legendre: sem diferenciação biótica em curso")
    lines.append("     (b+τ não positivo significativo na Pós).")
    lines.append("")
    lines.append("## Tabela consolidada")
    lines.append(tab.to_string(index=False))
    lines.append("")
    lines.append("## Parecer por empreendimento")
    for r in rows:
        n, s, c = r["empreendimento"], r["score"], r["classificacao"]
        lines.append(f"\n### {n}  -  {s}/6  ({c})")
        for k, v, ok in resultados[n]["estab"]["criterios"]:
            marca = "[OK] " if ok else "[--] "
            lines.append(f"  {marca}{k}  |  {v}")
        if s >= 4:
            lines.append("  >> Recomendação: assembleia estável; "
                         "viável considerar redução gradual do esforço amostral")
            lines.append("     (ex.: bianualização), mantendo verificações "
                         "periódicas e o desenho espacial vigente.")
        elif s == 3:
            lines.append("  >> Recomendação: estabilidade parcial; "
                         "manter monitoramento atual até que critérios faltantes")
            lines.append("     se confirmem por 2-3 ciclos amostrais adicionais.")
        else:
            lines.append("  >> Recomendação: assembleia em reorganização; "
                         "manter (ou reforçar) o esforço amostral atual.")
    lines.append("")
    lines.append("## Limitações")
    lines.append("- Auto-comparativo: não há grupo controle externo à cascata.")
    lines.append("- Cobertura amostral é baseada em Chao2 (incidência), sensível")
    lines.append("  ao número de singletons; aumentar o número de campanhas tende")
    lines.append("  a elevar a cobertura observada.")
    lines.append("- ANOSIM/PERMANOVA têm sensibilidade diferente a heterogeneidade")
    lines.append("  de dispersão; uma PERMANOVA significativa pode refletir tanto")
    lines.append("  diferença de centroides quanto diferença de espalhamento.")
    lines.append("- Análise apenas TAXONÔMICA - sem traits ecomorfológicos no banco")
    lines.append("  para avaliar β-funcional e a hipótese de redundância funcional")
    lines.append("  levantada por Ferreira et al. (2026). A interpretação de")
    lines.append("  'reorganização sem perda funcional' permanece como hipótese a ser")
    lines.append("  testada em futuro projeto com matrizes de traits.")
    lines.append("- Cascata Guanhães tem APENAS 3 reservatórios (JAC→SPT→DGN), enquanto")
    lines.append("  Ganassin et al. (2021) usaram cascatas de 7-9 reservatórios em")
    lines.append("  Iguacu/Paranapanema/São Francisco. O gradiente de cascata é reportado")
    lines.append("  como INDICATIVO, não como teste estatístico de hipótese.")
    lines.append("- Fortuna II está no rio Corrente Grande (não no Guanhães) e entra como")
    lines.append("  referência regional fora-cascata.")
    (pasta / "conclusao_estabilidade.txt").write_text(
        "\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------
def processar_empreendimento(df: pd.DataFrame, nome_emp: str,
                              base_dir: Path) -> dict:
    pasta_emp = base_dir / safe_name(nome_emp)
    p0 = pasta_emp / "00_suficiencia_amostral"
    p1 = pasta_emp / "01_diversidade_alfa"
    p2 = pasta_emp / "02_tendencia_temporal"
    p3 = pasta_emp / "03_estrutura_comunidade"
    p4 = pasta_emp / "04_diferenca_periodos"
    p5 = pasta_emp / "05_beta_temporal"
    p6 = pasta_emp / "06_sintese"
    p7 = pasta_emp / "07_estabilidade"
    mkdirs(pasta_emp, p0, p1, p2, p3, p4, p5, p6, p7)

    df_emp = df[df["nome_empreendimento"] == nome_emp].copy()
    if df_emp.empty:
        print(f"   [aviso] sem dados para {nome_emp}, pulando.")
        return {}

    print(f"   - 0/7 suficiência amostral (rarefação + Chao2)")
    suf      = bloco_0_suficiencia(df_emp, p0, nome_emp)
    print(f"   - 1/7 alfa por campanha ({df_emp['nome_campanha'].nunique()} campanhas)")
    tab_alfa = bloco_1_alfa(df_emp, p1, nome_emp)
    print( "   - 2/7 tendencia temporal")
    reg_tab  = bloco_2_tendencia(tab_alfa, p2, nome_emp)
    print( "   - 3/7 estrutura da comunidade (BC, PCoA, dendrograma, heatmap)")
    bloco_3_estrutura(df_emp, p3, nome_emp)
    print( "   - 4/7 ANOSIM + PERMANOVA")
    tab_test = bloco_4_anosim_permanova(df_emp, p4, nome_emp)
    print( "   - 5/7 beta-diversidade temporal (Baselga)")
    tab_beta = bloco_5_beta_temporal(df_emp, p5, nome_emp)
    print( "   - 5b/7 beta-Legendre + LCBD + ITS (Legendre, Ferreira et al. 2026)")
    bloco5b  = bloco_5b_legendre_its(df_emp, p5, nome_emp)
    print( "   - 6/7 sintese")
    bloco_6_sintese(nome_emp, p6, tab_alfa, reg_tab, tab_test, tab_beta)
    print( "   - 7/7 criterios de estabilidade")
    estab    = bloco_7_estabilidade(nome_emp, p7, suf, tab_alfa, reg_tab,
                                    tab_beta, tab_test, bloco5b=bloco5b)
    print(f"        score = {estab['score']}/6  ({estab['classe']})")

    return {"suf": suf, "tab_alfa": tab_alfa, "reg_tab": reg_tab,
            "tab_test": tab_test, "tab_beta": tab_beta,
            "bloco5b": bloco5b, "estab": estab}


def main() -> None:
    mkdirs(OUTPUT_BASE, OUTPUT_BASE / "_dados")
    engine = get_engine()
    resultados: dict = {}
    try:
        print(f"-> Carregando dados (projeto {PROJETO_CODIGO} / {GRUPO} / Quantitativa)...")
        df = carregar_dados(engine)
        df.to_excel(OUTPUT_BASE / "_dados" / "df_ictio_quantitativa.xlsx",
                    index=False)
        print(f"   {len(df)} linhas | "
              f"{df['nome_campanha'].nunique()} campanhas | "
              f"{df['nome_empreendimento'].nunique()} empreendimentos")

        for nome_emp in sorted(df["nome_empreendimento"].dropna().unique()):
            print(f"\n>> {nome_emp}")
            resultados[nome_emp] = processar_empreendimento(df, nome_emp, OUTPUT_BASE)

        print("\n>> Painel comparativo entre empreendimentos")
        painel_comparativo(resultados, OUTPUT_BASE)
        print(">> Análise de cascata (Ganassin et al. 2021)")
        analise_cascata(df, resultados, OUTPUT_BASE)
        print(">> Conclusão de estabilidade")
        conclusao_estabilidade(resultados, OUTPUT_BASE)

        print("\n--- PIPELINE CONCLUIDO ---")
        print(f"Outputs em: {OUTPUT_BASE}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
