"""
Pipeline — Meio Físico (Diagnóstico / Monitoramento)
=====================================================
Fonte de dados : tabela desnormalizada `fisico_analise_consolidada`
                 filtrada por `codigo_interno_opyta`.

Saídas por matriz
-----------------
  01  Tabela de Conformidade  (Excel, aba por campanha, células vermelhas = violação)
  02  Gráfico % Violação       (barras, por parâmetro × campanha)
    03  Séries Temporais         (PNG 600dpi, layout multi-ponto, VMPs como linhas/sombras)
  04  IQA — IGAM               (Água Superficial)
  05  IET — Lamparelli 2004    (Água Superficial)
  06  IQASB — ABAS             (Água Subterrânea)
  07  m-PEL-q — CETESB         (Sedimento)

Uso via runner
--------------
  python scripts/run_pipeline.py \\
      --project-id 115 --group "meio_fisico" --pipeline meio_fisico \\
      --client braang01 --output-dir outputs/...
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from opyta_analysis.theme import apply_theme, get_figsize, style_legend

# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

_BLOCOS = {
    "1": "Tabela de Conformidade (Excel)",
    "2": "Gráfico % Violação",
    "3": "Séries Temporais",
    "4": "IQA (IGAM) — Água Superficial",
    "5": "IET (Lamparelli) — Água Superficial",
    "6": "IQASB (ABAS) — Água Subterrânea",
    "7": "m-PEL-q (CETESB) — Sedimento",
}

# Colunas de VMP disponíveis na tabela consolidada
_VMP_COLS = [
    "vmp_357_cl1_min", "vmp_357_cl1_max",
    "vmp_357_cl2_min", "vmp_357_cl2_max",
    "vmp_amonia_dinamico",
    "vmp_454_n1", "vmp_454_n2",
    "vmp_396_consumo_humano", "vmp_396_dessedentacao_animal",
    "vmp_396_irrigacao", "vmp_396_recreacao",
    "vmp_430_padrao",
]

# Mapeamento: matriz → colunas VMP relevantes para a tabela de conformidade
_VMP_BY_MATRIZ: Dict[str, List[str]] = {
    "Água Superficial": [
        "vmp_357_cl1_min", "vmp_357_cl1_max",
        "vmp_357_cl2_min", "vmp_357_cl2_max",
        "vmp_amonia_dinamico",
    ],
    "Água Subterrânea": [
        "vmp_396_consumo_humano", "vmp_396_dessedentacao_animal",
        "vmp_396_irrigacao", "vmp_396_recreacao",
    ],
    "Sedimento": ["vmp_454_n1", "vmp_454_n2"],
    "Efluente": ["vmp_430_padrao"],
}

# Metais considerados no m-PEL-q (CETESB) — nomes canônicos da tabela
_METAIS_PELQ = [
    "Arsênio Total", "Cádmio Total", "Chumbo Total",
    "Cromo Total", "Mercúrio Total", "Cobre", "Níquel", "Zinco",
]

# Parâmetros e pesos para IQA-IGAM
_IQA_PESOS: Dict[str, float] = {
    "Oxigênio Dissolvido In Situ":                          0.17,
    "pH In Situ":                                          0.12,
    "Demanda Bioquímica de Oxigênio":                      0.10,
    "Nitrogênio Total":                                    0.10,
    "Fósforo Total":                                       0.10,
    "Temperatura da Amostra":                              0.10,
    "Turbidez":                                            0.08,
    "Sólidos Totais":                                      0.08,
    "Coliformes Termotolerantes por tubos múltiplos - NMP": 0.15,
}

# Pesos IQASB — ABAS
_IQASB_PESOS: Dict[str, int] = {
    "Arsênio Total": 5, "Cádmio Total": 5, "Chumbo Total": 5,
    "Cromo Total": 5, "Mercúrio Total": 5, "Níquel Total": 5, "Cianeto Total": 5,
    "Nitrato": 4, "Bário Total": 4,
    "Ferro Total": 2, "Manganês Total": 2, "Alumínio Total": 2,
    "Cobre Total": 2, "Zinco Total": 2, "Cloretos": 2, "Sólidos Dissolvidos Totais": 2,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


def _tc(theme: Dict[str, Any], key: str, default: str) -> str:
    """Retorna cor técnica do tema com fallback seguro."""
    return str(theme.get(key, default))


def _sort_key_campanha(nome: str) -> int:
    """
    Ordena campanhas cronologicamente.
    Suporta dois padrões:
      - legado: 'mes-ano'  (ex: 'jan-2021')
      - novo:   'CNNN-YYYY-MM-SC|CH' (ex: 'C028-2026-04-SC')
    """
    nome = str(nome).strip().lower()
    # novo padrão: C028-2026-04-SC → 20260428
    m = re.match(r"c(\d+)-(\d{4})-(\d{2})", nome)
    if m:
        return int(m.group(2)) * 10000 + int(m.group(3)) * 100 + int(m.group(1))
    # legado: jan-2021 → 202101
    meses = {"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,
              "jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12,
              "janeiro":1,"fevereiro":2,"março":3,"abril":4,"maio":5,"junho":6,
              "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
    parts = nome.split("-")
    try:
        return int(parts[1]) * 100 + meses.get(parts[0], 0)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Conexão e carga de dados
# ---------------------------------------------------------------------------

def _get_engine(env_file: Optional[str]):
    import os
    if env_file:
        load_dotenv(env_file, override=True)
    else:
        load_dotenv()

    db_url = os.getenv("FISICO_DB_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "Variável FISICO_DB_URL (ou DATABASE_URL) não encontrada no .env. "
            "Exemplo: postgresql://user:pass@host:5432/postgres"
        )
    return create_engine(db_url)


def _load_fisico_df(codigo_projeto: str, env_file: Optional[str]) -> pd.DataFrame:
    """Carrega todos os dados do projeto a partir de fisico_analise_consolidada."""
    engine = _get_engine(env_file)
    query = text(
        "SELECT * FROM fisico_analise_consolidada "
        "WHERE codigo_interno_opyta = :cod"
    )
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '5min'"))
        df = pd.read_sql(query, conn, params={"cod": codigo_projeto})

    # Garantir tipos numéricos nas colunas de valor e VMP
    num_cols = ["valor_medido"] + _VMP_COLS
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ordem cronológica
    df["_ordem_cron"] = df["nome_campanha"].apply(_sort_key_campanha)
    df = df.sort_values(["nome_ponto", "_ordem_cron"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Bloco 1 — Tabela de Conformidade (Excel)
# ---------------------------------------------------------------------------

def _violou(valor: float, limites: dict, matriz: str) -> bool:
    if pd.isna(valor):
        return False
    if "Superficial" in matriz:
        v_max = limites.get("vmp_357_cl2_max")
        v_min = limites.get("vmp_357_cl2_min")
        v_amo = limites.get("vmp_amonia_dinamico")
        if pd.notna(v_max) and valor > v_max:
            return True
        if pd.notna(v_min) and valor < v_min:
            return True
        if pd.notna(v_amo) and valor > v_amo:
            return True
    elif "Subterrânea" in matriz:
        v_ch = limites.get("vmp_396_consumo_humano")
        if pd.notna(v_ch) and valor > v_ch:
            return True
    elif "Sedimento" in matriz:
        v_n1 = limites.get("vmp_454_n1")
        if pd.notna(v_n1) and valor > v_n1:
            return True
    elif "Efluente" in matriz:
        v_430 = limites.get("vmp_430_padrao")
        if pd.notna(v_430) and valor > v_430:
            return True
    return False


def _bloco_01_conformidade(df_matriz: pd.DataFrame, matriz: str, output_dir: Path) -> List[str]:
    try:
        import xlsxwriter  # noqa: F401
    except ImportError:
        raise ImportError("Instale xlsxwriter: pip install xlsxwriter")

    cols_vmp = _VMP_BY_MATRIZ.get(matriz, [])
    nome_sub = _safe_name(matriz)
    path_out = output_dir / f"01_Conformidade_{nome_sub}.xlsx"

    vmp_map = (
        df_matriz[["nome_parametro"] + [c for c in cols_vmp if c in df_matriz.columns]]
        .drop_duplicates("nome_parametro")
        .set_index("nome_parametro")
        .to_dict("index")
    )

    with pd.ExcelWriter(str(path_out), engine="xlsxwriter") as writer:
        for camp in sorted(df_matriz["nome_campanha"].unique(),
                           key=_sort_key_campanha):
            df_c = df_matriz[df_matriz["nome_campanha"] == camp]

            pivot = df_c.pivot_table(
                index=["nome_parametro", "unidade_medida"],
                columns="nome_ponto",
                values="valor_medido",
                aggfunc="first",
            ).reset_index()

            df_vmp = (
                df_c[["nome_parametro", "unidade_medida"]
                     + [c for c in cols_vmp if c in df_c.columns]]
                .drop_duplicates()
            )
            tabela = pd.merge(
                df_vmp, pivot,
                on=["nome_parametro", "unidade_medida"],
                how="left",
            )

            sheet = re.sub(r'[\\/*?:"<>|]', "", str(camp))[:31]
            tabela.to_excel(writer, sheet_name=sheet, index=False)

            wb = writer.book
            ws = writer.sheets[sheet]
            fmt_red = wb.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1})

            inicio_pontos = 2 + len([c for c in cols_vmp if c in df_c.columns])
            for i in range(len(tabela)):
                param = tabela.iloc[i]["nome_parametro"]
                lims = vmp_map.get(param, {})
                for col_idx in range(inicio_pontos, len(tabela.columns)):
                    val = tabela.iloc[i, col_idx]
                    if _violou(val, lims, matriz):
                        ws.write(i + 1, col_idx, val, fmt_red)

            ws.set_column(0, 0, 35)
            ws.set_column(1, 1, 15)

    return [str(path_out)]


# ---------------------------------------------------------------------------
# Bloco 2 — % Violação
# ---------------------------------------------------------------------------

def _bloco_02_violacao(df_matriz: pd.DataFrame, matriz: str,
                       output_dir: Path, theme: Dict) -> List[str]:
    df = df_matriz.copy()

    def _viol_row(row):
        return _violou(row["valor_medido"],
                       {c: row.get(c) for c in _VMP_COLS if c in row.index},
                       matriz)

    df["violou"] = df.apply(_viol_row, axis=1)
    resumo = (
        df.groupby(["nome_parametro", "nome_campanha"])["violou"]
        .agg(["sum", "count"])
        .reset_index()
    )
    resumo["percentual"] = (resumo["sum"] / resumo["count"]) * 100
    resumo = resumo[resumo["percentual"] > 0]
    if resumo.empty:
        return []

    fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"))
    apply_theme(ax, theme)

    paleta = theme.get(
        "mf_violation_palette",
        ["#c0392b", "#e74c3c", "#f39c12", "#e67e22"],
    )
    camps_ord = sorted(resumo["nome_campanha"].unique(), key=_sort_key_campanha)
    colors = {c: paleta[i % len(paleta)] for i, c in enumerate(camps_ord)}

    for camp in camps_ord:
        sub = resumo[resumo["nome_campanha"] == camp]
        ax.barh(sub["nome_parametro"], sub["percentual"],
                label=camp, color=colors[camp], alpha=0.82)

    ax.set_xlabel("Pontos com Violacao (%)")
    ax.set_xlim(0, 115)
    legend = ax.legend(
        loc=theme.get("legend_loc", "upper center"),
        ncol=min(int(theme.get("legend_max_cols", 2)), max(1, len(camps_ord))),
        frameon=bool(theme.get("legend_frame", False)),
    )
    style_legend(legend, theme)

    nome_sub = _safe_name(matriz)
    path_out = output_dir / f"02_Percentual_Violacao_{nome_sub}.png"
    fig.savefig(str(path_out), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    return [str(path_out)]


# ---------------------------------------------------------------------------
# Bloco 3 — Séries Temporais
# ---------------------------------------------------------------------------

def _bloco_03_series_temporais(df_matriz: pd.DataFrame, matriz: str,
                               output_dir: Path, theme: Dict) -> List[str]:
    gerados = []
    params = df_matriz["nome_parametro"].unique()

    for param in params:
        df_p = df_matriz[df_matriz["nome_parametro"] == param].copy()
        df_p = df_p.sort_values("_ordem_cron")
        if df_p["valor_medido"].dropna().empty:
            continue

        unidade = df_p["unidade_medida"].iloc[0] if pd.notna(df_p["unidade_medida"].iloc[0]) else "-"
        pontos = sorted(df_p["nome_ponto"].unique())
        grupos = [pontos[i:i + 3] for i in range(0, len(pontos), 3)]

        for idx_g, grupo in enumerate(grupos):
            n = len(grupo)
            base_w, base_h = get_figsize(theme, "wide")
            fig, axes = plt.subplots(n, 1, figsize=(base_w, base_h * n), squeeze=False)

            for ax_i, ponto in enumerate(grupo):
                ax = axes[ax_i][0]
                apply_theme(ax, theme)
                df_pt = df_p[df_p["nome_ponto"] == ponto]
                camps = sorted(df_pt["nome_campanha"].unique(), key=_sort_key_campanha)

                x = range(len(camps))
                vals = [df_pt[df_pt["nome_campanha"] == c]["valor_medido"].mean()
                        for c in camps]

                ax.plot(x, vals, marker="o", linewidth=2.0, markersize=7,
                    color=theme.get("primary_hex", "#2E6F95"))
                ax.set_xticks(list(x))
                ax.set_xticklabels(camps, rotation=45, ha="right")
                ax.set_ylabel(unidade)

                # --- VMPs como linhas + sombra ---
                lims_visiveis: list[float] = []

                if "Subterrânea" in matriz:
                    usos = {
                        "vmp_396_consumo_humano":       (_tc(theme, "mf_vmp_consumo_humano", "#e74c3c"), "VMP - Consumo"),
                        "vmp_396_dessedentacao_animal": (_tc(theme, "mf_vmp_dessedentacao", "#8B4513"), "VMP - Dessedentação"),
                        "vmp_396_irrigacao":            (_tc(theme, "mf_vmp_irrigacao", "#006400"), "VMP - Irrigação"),
                        "vmp_396_recreacao":            (_tc(theme, "mf_vmp_recreacao", "#2980b9"), "VMP - Recreação"),
                    }
                    for col, (cor, label_uso) in usos.items():
                        if col in df_pt.columns:
                            vv = df_pt[col].iloc[0]
                            if pd.notna(vv):
                                ax.axhline(vv, color=cor, ls="--", lw=2.5,
                                           label=f"{label_uso}: {vv}")
                                lims_visiveis.append(float(vv))

                elif "pH" in param:
                    v_min = df_pt["vmp_357_cl2_min"].iloc[0] if "vmp_357_cl2_min" in df_pt else np.nan
                    v_max = df_pt["vmp_357_cl2_max"].iloc[0] if "vmp_357_cl2_max" in df_pt else np.nan
                    if pd.notna(v_min):
                        ax.axhline(v_min, color=_tc(theme, "mf_vmp_default", "#e74c3c"), ls="--", lw=2.5,
                                   label=f"VMP mín: {v_min}")
                        lims_visiveis.append(float(v_min))
                    if pd.notna(v_max):
                        ax.axhline(v_max, color=_tc(theme, "mf_vmp_default", "#e74c3c"), ls="--", lw=2.5,
                                   label=f"VMP máx: {v_max}")
                        lims_visiveis.append(float(v_max))

                elif "Sedimento" in matriz:
                    for col, label in [("vmp_454_n1", "N1"), ("vmp_454_n2", "N2")]:
                        if col in df_pt.columns:
                            vv = df_pt[col].iloc[0]
                            if pd.notna(vv):
                                cor = _tc(theme, "mf_vmp_n1", "#f39c12") if "n1" in col else _tc(theme, "mf_vmp_n2", "#e74c3c")
                                ax.axhline(vv, color=cor, ls="--", lw=2.5,
                                           label=f"VMP {label}: {vv}")
                                lims_visiveis.append(float(vv))

                else:
                    # Superficial ou Efluente: lógica padrão
                    col_vmp = ("vmp_430_padrao" if "Efluente" in matriz
                               else "vmp_357_cl2_max")
                    v_amo = df_pt["vmp_amonia_dinamico"].iloc[0] if "vmp_amonia_dinamico" in df_pt else np.nan
                    col_val = df_pt[col_vmp].iloc[0] if col_vmp in df_pt.columns else np.nan
                    v_ref = float(v_amo) if pd.notna(v_amo) else (float(col_val) if pd.notna(col_val) else None)
                    if v_ref is not None:
                        ax.axhline(v_ref, color=_tc(theme, "mf_vmp_default", "#e74c3c"), ls="--", lw=2.5,
                                   label=f"VMP: {v_ref}")
                        lims_visiveis.append(v_ref)

                # Sombra acima do VMP máximo
                if lims_visiveis:
                    ymax_lim = max(lims_visiveis)
                    y_top = ax.get_ylim()[1] * 1.5
                    ax.axhspan(
                        ymax_lim,
                        y_top,
                        color=_tc(theme, "mf_vmp_shade", "#e74c3c"),
                        alpha=float(theme.get("mf_vmp_shade_alpha", 0.06)),
                        zorder=0,
                    )

                if lims_visiveis or len(df_pt["nome_campanha"].unique()) > 1:
                    legend = ax.legend(
                        loc=theme.get("legend_loc", "upper center"),
                        ncol=min(int(theme.get("legend_max_cols", 2)), 2),
                        frameon=bool(theme.get("legend_frame", False)),
                    )
                    style_legend(legend, theme)

            fig.tight_layout()

            nome_seg = _safe_name(param)
            nome_sub = _safe_name(matriz)
            path_out = output_dir / f"03_ST_{nome_sub}_{nome_seg}_P{idx_g + 1}.png"
            fig.savefig(str(path_out), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
            plt.close(fig)
            gerados.append(str(path_out))

    return gerados


# ---------------------------------------------------------------------------
# Bloco 4 — IQA (IGAM)
# ---------------------------------------------------------------------------

def _qi_igam(parametro: str, valor: float) -> float:
    try:
        v = float(valor)
        if v < 0:
            v = 0
        p = parametro
        if "pH" in p:
            if v <= 2:  return 2.0
            if v <= 4:  return 5.0  + (v - 2)  * 11.0
            if v <= 5:  return 27.0 + (v - 4)  * 28.0
            if v <= 6:  return 55.0 + (v - 5)  * 25.0
            if v <= 7:  return 80.0 + (v - 6)  * 12.0
            if v <= 8:  return 92.0
            if v <= 8.5: return 92.0 - (v - 8)   * 4.0
            if v <= 9:  return 90.0 - (v - 8.5) * 10.0
            if v <= 10: return 80.0 - (v - 9)   * 35.0
            return 3.0
        if "Oxigênio Dissolvido" in p:
            sat = (v / 8.26) * 100
            if sat <= 20:  return 5.0  + sat            * 0.50
            if sat <= 50:  return 15.0 + (sat - 20)     * 0.63
            if sat <= 85:  return 34.0 + (sat - 50)     * 0.71
            if sat <= 100: return 59.0 + (sat - 85)     * 2.73
            if sat <= 140: return 100.0 - (sat - 100)   * 0.43
            return 83.0
        if "Coliformes" in p:
            if v <= 1: return 100.0
            log_v = math.log10(v)
            qi = 98.03 - 36.45 * log_v + 3.138 * log_v**2 + 0.067 * log_v**3
            return max(2.0, min(100.0, qi))
        if "Demanda Bioquímica" in p:
            if v <= 2:  return 100.0 - v       * 10.0
            if v <= 5:  return 80.0  - (v - 2) * 12.0
            if v <= 10: return 44.0  - (v - 5) * 6.0
            if v <= 20: return 14.0  - (v - 10)* 0.5
            return 2.0
        if "Nitrogênio Total" in p:
            if v <= 1:   return 100.0 - v       * 10.0
            if v <= 5:   return 90.0  - (v - 1) * 15.0
            if v <= 10:  return 30.0  - (v - 5) * 4.0
            if v <= 100: return 10.0  - (v - 10)* 0.08
            return 1.0
        if "Fósforo Total" in p:
            if v <= 0.1: return 100.0 - v       * 400.0
            if v <= 0.5: return 60.0  - (v - 0.1) * 125.0
            if v <= 1.0: return 10.0  - (v - 0.5) * 10.0
            return 5.0
        if "Turbidez" in p:
            if v <= 5:   return 100.0 - v       * 3.0
            if v <= 10:  return 85.0  - (v - 5) * 2.0
            if v <= 40:  return 75.0  - (v - 10)* 1.3
            if v <= 100: return 36.0  - (v - 40)* 0.48
            return 5.0
        if "Sólidos Totais" in p:
            if v <= 50:  return 100.0 - v       * 0.4
            if v <= 100: return 80.0  - (v - 50) * 0.1
            if v <= 500: return 75.0  - (v - 100)* 0.11
            return 30.0
        return 100.0
    except Exception:
        return 100.0


def _bloco_04_iqa(df_total: pd.DataFrame, output_dir: Path, theme: Dict) -> List[str]:
    df_agua = df_total[df_total["matriz"] == "Água Superficial"].copy()
    if df_agua.empty:
        return []

    df_piv = df_agua.pivot_table(
        index=["nome_campanha", "nome_ponto"],
        columns="nome_parametro",
        values="valor_medido",
    ).reset_index()

    def _calc_iqa(row) -> Optional[float]:
        prod, w_sum = 1.0, 0.0
        for param, w in _IQA_PESOS.items():
            val = row.get(param)
            if pd.notna(val):
                prod *= (_qi_igam(param, val) ** w)
                w_sum += w
        return round(prod ** (1 / w_sum), 2) if w_sum > 0 else None

    df_piv["IQA"] = df_piv.apply(_calc_iqa, axis=1)
    df_piv["IQA_Classe"] = df_piv["IQA"].apply(
        lambda v: "Excelente" if v and v >= 79 else
                  "Bom"       if v and v >= 51 else
                  "Médio"     if v and v >= 36 else
                  "Ruim"      if v and v >= 19 else "Muito Ruim"
    )

    faixas = [
        (0,  25, _tc(theme, "mf_iqa_muito_ruim", "#e74c3c"), "Muito Ruim (<25)"),
        (25, 50, _tc(theme, "mf_iqa_ruim", "#f39c12"), "Ruim (26-50)"),
        (50, 70, _tc(theme, "mf_iqa_medio", "#f1c40f"), "Médio (51-70)"),
        (70, 90, _tc(theme, "mf_iqa_bom", "#27ae60"), "Bom (71-90)"),
        (90, 100, _tc(theme, "mf_iqa_excelente", "#2980b9"), "Excelente (>90)"),
    ]

    gerados: List[str] = []
    for camp in sorted(df_piv["nome_campanha"].unique(), key=_sort_key_campanha):
        df_c = df_piv[df_piv["nome_campanha"] == camp].dropna(subset=["IQA"])
        if df_c.empty:
            continue

        fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"))
        apply_theme(ax, theme)
        patches = []
        for low, high, cor, lbl in faixas:
            ax.axhspan(low, high, color=cor, alpha=0.85, zorder=0)
            patches.append(mpatches.Patch(color=cor, label=lbl))

        xi = list(range(len(df_c)))
        ax.scatter(xi, df_c["IQA"], color=_tc(theme, "mf_marker_color", "black"), s=90, zorder=5)
        patches.append(plt.Line2D([0], [0], marker="o", color="w",
                      markerfacecolor=_tc(theme, "mf_marker_color", "black"), markersize=10, label="IQA"))
        for i, (_, row) in enumerate(df_c.reset_index().iterrows()):
            txt = ax.annotate(str(row["IQA"]), (i, row["IQA"]),
                              xytext=(8, 8), textcoords="offset points",
                              fontsize=int(theme.get("annotation_size", theme.get("label_size", 12))),
                              fontweight="bold", zorder=10)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground="white")])

        ax.set_ylim(0, 105)
        ax.set_xticks(xi)
        ax.set_xticklabels(df_c["nome_ponto"].tolist(), rotation=45, ha="right")
        legend = ax.legend(
            handles=patches,
            loc=theme.get("legend_loc", "upper center"),
            ncol=min(int(theme.get("legend_max_cols", 2)), 2),
            frameon=bool(theme.get("legend_frame", False)),
        )
        style_legend(legend, theme)

        nome_c = _safe_name(camp)
        path_out = output_dir / f"04_IQA_{nome_c}.png"
        fig.savefig(str(path_out), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)

        resumo_path = output_dir / f"04_Resumo_IQA_{nome_c}.xlsx"
        df_c[["nome_campanha", "nome_ponto", "IQA", "IQA_Classe"]].to_excel(
            str(resumo_path), index=False
        )
        gerados += [str(path_out), str(resumo_path)]

    return gerados


# ---------------------------------------------------------------------------
# Bloco 5 — IET (Lamparelli 2004)
# ---------------------------------------------------------------------------

def _bloco_05_iet(df_total: pd.DataFrame, output_dir: Path, theme: Dict) -> List[str]:
    df_agua = df_total[df_total["matriz"] == "Água Superficial"].copy()
    if df_agua.empty:
        return []

    df_piv = df_agua.pivot_table(
        index=["nome_campanha", "nome_ponto"],
        columns="nome_parametro",
        values="valor_medido",
    ).reset_index()

    col_pt = next((c for c in df_piv.columns if "Fósforo Total" in c), None)
    col_cl = next((c for c in df_piv.columns if "Clorofila" in c), None)
    if col_pt is None or col_cl is None:
        print("[meio_fisico] IET ignorado — sem dados de Fósforo Total ou Clorofila.")
        return []

    def _calc_iet(row) -> Optional[float]:
        try:
            pt_ug = float(row[col_pt]) * 1000
            cl_ug = float(row[col_cl]) * 1000
            iet_pt = 10 * (6 - ((1.77 - 0.42 * math.log(pt_ug)) / math.log(2)))
            iet_cl = 10 * (6 - ((-0.70 - 0.60 * math.log(cl_ug)) / math.log(2)))
            return round((iet_pt + iet_cl) / 2, 2)
        except Exception:
            return None

    df_piv["IET"] = df_piv.apply(_calc_iet, axis=1)
    df_piv["IET_Classe"] = df_piv["IET"].apply(
        lambda v: "Ultraoligotrófico" if v and v <= 47 else
                  "Oligotrófico"      if v and v <= 52 else
                  "Mesotrófico"       if v and v <= 59 else
                  "Eutrófico"         if v and v <= 63 else
                  "Supereutrófico"    if v and v <= 67 else "Hipereutrófico"
    )

    faixas = [
        (0,  47, _tc(theme, "mf_iet_ultraoligotrofico", "#2980b9"), "Ultraoligotrófico (<47)"),
        (47, 52, _tc(theme, "mf_iet_oligotrofico", "#d35400"), "Oligotrófico (47-52)"),
        (52, 59, _tc(theme, "mf_iet_mesotrofico", "#f1c40f"), "Mesotrófico (52-59)"),
        (59, 63, _tc(theme, "mf_iet_eutrofico", "#8e44ad"), "Eutrófico (59-63)"),
        (63, 67, _tc(theme, "mf_iet_supereutrofico", "#e74c3c"), "Supereutrófico (63-67)"),
        (67, 100, _tc(theme, "mf_iet_hipereutrofico", "#e91e8c"), "Hipereutrófico (>67)"),
    ]

    gerados: List[str] = []
    for camp in sorted(df_piv["nome_campanha"].unique(), key=_sort_key_campanha):
        df_c = df_piv[df_piv["nome_campanha"] == camp].dropna(subset=["IET"])
        if df_c.empty:
            continue

        fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"))
        apply_theme(ax, theme)
        patches = []
        for low, high, cor, lbl in faixas:
            ax.axhspan(low, high, color=cor, alpha=0.85, zorder=0)
            patches.append(mpatches.Patch(color=cor, label=lbl))

        xi = list(range(len(df_c)))
        ax.scatter(xi, df_c["IET"], color=_tc(theme, "mf_marker_color", "black"), s=100, zorder=5)
        patches.append(plt.Line2D([0], [0], marker="o", color="w",
                      markerfacecolor=_tc(theme, "mf_marker_color", "black"), markersize=10, label="IET"))
        for i, (_, row) in enumerate(df_c.reset_index().iterrows()):
            txt = ax.annotate(str(row["IET"]), (i, row["IET"]),
                              xytext=(10, 10), textcoords="offset points",
                              fontsize=int(theme.get("annotation_size", theme.get("label_size", 12))),
                              fontweight="bold", zorder=10)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground="white")])

        ax.set_ylim(30, 90)
        ax.set_xticks(xi)
        ax.set_xticklabels(df_c["nome_ponto"].tolist(), rotation=45, ha="right")
        legend = ax.legend(
            handles=patches,
            loc=theme.get("legend_loc", "upper center"),
            ncol=min(int(theme.get("legend_max_cols", 2)), 2),
            frameon=bool(theme.get("legend_frame", False)),
        )
        style_legend(legend, theme)

        nome_c = _safe_name(camp)
        path_out = output_dir / f"05_IET_{nome_c}.png"
        fig.savefig(str(path_out), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)

        resumo_path = output_dir / f"05_Resumo_IET_{nome_c}.xlsx"
        df_c[["nome_campanha", "nome_ponto", "IET", "IET_Classe"]].to_excel(
            str(resumo_path), index=False
        )
        gerados += [str(path_out), str(resumo_path)]

    return gerados


# ---------------------------------------------------------------------------
# Bloco 6 — IQASB (ABAS) — Água Subterrânea
# ---------------------------------------------------------------------------

def _bloco_06_iqasb(df_total: pd.DataFrame, output_dir: Path, theme: Dict) -> List[str]:
    df_sub = df_total[df_total["matriz"] == "Água Subterrânea"].copy()
    if df_sub.empty:
        return []

    df_piv = df_sub.pivot_table(
        index=["nome_campanha", "nome_ponto"],
        columns="nome_parametro",
        values=["valor_medido", "vmp_396_consumo_humano", "sinal_limite"],
        aggfunc="first",
    )
    df_piv.columns = [f"{c[0]}__{c[1]}" for c in df_piv.columns]
    df_piv = df_piv.reset_index()

    def _calc_iqasb(row) -> tuple[Optional[float], int]:
        soma, soma_w, n = 0.0, 0, 0
        for param, wi in _IQASB_PESOS.items():
            val_col = f"valor_medido__{param}"
            vmp_col = f"vmp_396_consumo_humano__{param}"
            sig_col = f"sinal_limite__{param}"
            if val_col not in row or pd.isna(row[val_col]):
                continue
            try:
                val = float(row[val_col])
                vmp = float(row[vmp_col]) if (vmp_col in row and pd.notna(row[vmp_col])) else None
                if sig_col in row and row[sig_col] == "<":
                    val = val / 2.0
                if vmp and vmp > 0:
                    soma += (val / vmp) * 100 * wi
                    soma_w += wi
                    n += 1
            except Exception:
                continue
        return (round(soma / soma_w, 2), n) if soma_w > 0 else (None, 0)

    calc = df_piv.apply(_calc_iqasb, axis=1)
    df_piv["IQASB"] = [x[0] for x in calc]
    df_piv["Qtd_Params"] = [x[1] for x in calc]
    df_piv["IQASB_Classe"] = df_piv["IQASB"].apply(
        lambda v: "N/A"       if v is None else
                  "Ótima"     if v <= 25  else
                  "Boa"       if v <= 50  else
                  "Regular"   if v <= 75  else
                  "Ruim"      if v <= 100 else "Imprópria"
    )

    faixas = [
        (0,   25, _tc(theme, "mf_iqasb_otima", "#27ae60"), "Ótima (0-25)"),
        (25,  50, _tc(theme, "mf_iqasb_boa", "#82e0aa"), "Boa (26-50)"),
        (50,  75, _tc(theme, "mf_iqasb_regular", "#f1c40f"), "Regular (51-75)"),
        (75, 100, _tc(theme, "mf_iqasb_ruim", "#f39c12"), "Ruim (76-100)"),
        (100, 300, _tc(theme, "mf_iqasb_impropria", "#e74c3c"), "Imprópria (>100)"),
    ]

    gerados: List[str] = []
    for camp in sorted(df_piv["nome_campanha"].unique(), key=_sort_key_campanha):
        df_c = df_piv[df_piv["nome_campanha"] == camp].dropna(subset=["IQASB"])
        if df_c.empty:
            continue

        fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"))
        apply_theme(ax, theme)
        patches = []
        for low, high, cor, lbl in faixas:
            ax.axhspan(low, high, color=cor, alpha=0.8, zorder=0)
            patches.append(mpatches.Patch(color=cor, label=lbl))

        xi = list(range(len(df_c)))
        ax.scatter(xi, df_c["IQASB"], color=_tc(theme, "mf_marker_color", "black"), s=100, zorder=5)
        patches.append(plt.Line2D([0], [0], marker="o", color="w",
                      markerfacecolor=_tc(theme, "mf_marker_color", "black"), markersize=10, label="IQASB"))
        for i, (_, row) in enumerate(df_c.reset_index().iterrows()):
            txt = ax.annotate(str(row["IQASB"]), (i, row["IQASB"]),
                              xytext=(10, 10), textcoords="offset points",
                              fontsize=int(theme.get("annotation_size", theme.get("label_size", 12))),
                              fontweight="bold", zorder=10)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground="white")])

        ax.set_ylim(0, max(110, df_c["IQASB"].max() * 1.3))
        ax.set_xticks(xi)
        ax.set_xticklabels(df_c["nome_ponto"].tolist(), rotation=45, ha="right")
        legend = ax.legend(
            handles=patches,
            loc=theme.get("legend_loc", "upper center"),
            ncol=min(int(theme.get("legend_max_cols", 2)), 2),
            frameon=bool(theme.get("legend_frame", False)),
        )
        style_legend(legend, theme)

        nome_c = _safe_name(camp)
        path_out = output_dir / f"06_IQASB_{nome_c}.png"
        fig.savefig(str(path_out), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)

        resumo_path = output_dir / f"06_Resumo_IQASB_{nome_c}.xlsx"
        df_c[["nome_campanha", "nome_ponto", "IQASB", "IQASB_Classe", "Qtd_Params"]].to_excel(
            str(resumo_path), index=False
        )
        gerados += [str(path_out), str(resumo_path)]

    return gerados


# ---------------------------------------------------------------------------
# Bloco 7 — m-PEL-q (CETESB) — Sedimento
# ---------------------------------------------------------------------------

def _bloco_07_mpelq(df_total: pd.DataFrame, output_dir: Path, theme: Dict) -> List[str]:
    df_sed = df_total[df_total["matriz"] == "Sedimento"].copy()
    if df_sed.empty:
        return []

    df_piv = df_sed.pivot_table(
        index=["nome_campanha", "nome_ponto"],
        columns="nome_parametro",
        values=["valor_medido", "vmp_454_n2", "sinal_limite"],
        aggfunc="first",
    )
    df_piv.columns = [f"{c[0]}__{c[1]}" for c in df_piv.columns]
    df_piv = df_piv.reset_index()

    def _calc_mpelq(row) -> Optional[float]:
        soma, n = 0.0, 0
        for metal in _METAIS_PELQ:
            val_col = f"valor_medido__{metal}"
            n2_col  = f"vmp_454_n2__{metal}"
            sig_col = f"sinal_limite__{metal}"
            if val_col not in row or pd.isna(row[val_col]):
                continue
            if n2_col not in row or pd.isna(row[n2_col]):
                continue
            try:
                val = float(row[val_col])
                n2  = float(row[n2_col])
                if sig_col in row and row[sig_col] == "<":
                    val = val / 2.0
                if n2 > 0:
                    soma += val / n2
                    n += 1
            except Exception:
                continue
        return round(soma / n, 4) if n > 0 else None

    df_piv["m_PEL_q"] = df_piv.apply(_calc_mpelq, axis=1)
    df_piv["Toxicidade"] = df_piv["m_PEL_q"].apply(
        lambda v: "Improvável" if v is not None and v <= 0.1 else
                  "Possível"   if v is not None and v <= 1.0 else
                  "Provável"   if v is not None else "Sem dados"
    )

    faixas = [
        (0,   0.1, _tc(theme, "mf_mpelq_improvavel", "#2980b9"), "Improvável (≤0.1)"),
        (0.1, 1.0, _tc(theme, "mf_mpelq_possivel", "#f1c40f"), "Possível (0.1-1.0)"),
        (1.0, 5.0, _tc(theme, "mf_mpelq_provavel", "#e74c3c"), "Provável (>1.0)"),
    ]

    gerados: List[str] = []
    for camp in sorted(df_piv["nome_campanha"].unique(), key=_sort_key_campanha):
        df_c = df_piv[df_piv["nome_campanha"] == camp].dropna(subset=["m_PEL_q"])
        if df_c.empty:
            continue

        fig, ax = plt.subplots(figsize=get_figsize(theme, "wide"))
        apply_theme(ax, theme)
        patches = []
        for low, high, cor, lbl in faixas:
            ax.axhspan(low, high, color=cor, alpha=0.8, zorder=0)
            patches.append(mpatches.Patch(color=cor, label=lbl))

        xi = list(range(len(df_c)))
        ax.scatter(xi, df_c["m_PEL_q"], color=_tc(theme, "mf_marker_color", "black"), s=120, zorder=5)
        for i, (_, row) in enumerate(df_c.reset_index().iterrows()):
            txt = ax.annotate(str(row["m_PEL_q"]), (i, row["m_PEL_q"]),
                              xytext=(10, 10), textcoords="offset points",
                              fontsize=int(theme.get("annotation_size", theme.get("label_size", 12))),
                              fontweight="bold", zorder=10)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground="white")])

        ax.set_ylim(0, max(1.2, df_c["m_PEL_q"].max() * 1.5))
        ax.set_xticks(xi)
        ax.set_xticklabels(df_c["nome_ponto"].tolist(), rotation=45, ha="right")
        legend = ax.legend(
            handles=patches,
            title="Risco Efeitos Adversos (CETESB)",
            loc=theme.get("legend_loc", "upper center"),
            ncol=min(int(theme.get("legend_max_cols", 2)), 2),
            frameon=bool(theme.get("legend_frame", False)),
        )
        style_legend(legend, theme)

        nome_c = _safe_name(camp)
        path_out = output_dir / f"07_mPELq_{nome_c}.png"
        fig.savefig(str(path_out), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)

        resumo_path = output_dir / f"07_Resumo_mPELq_{nome_c}.xlsx"
        df_c[["nome_campanha", "nome_ponto", "m_PEL_q", "Toxicidade"]].to_excel(
            str(resumo_path), index=False
        )
        gerados += [str(path_out), str(resumo_path)]

    return gerados


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def run_meio_fisico_pipeline(
    *,
    codigo_projeto: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
    # Parâmetros ignorados mas aceitos pelo runner genérico
    project_id: int = 0,
    group: str = "meio_fisico",
    **kwargs,
) -> Dict[str, Any]:
    """
    Executa o pipeline de Meio Físico para um projeto.

    Parameters
    ----------
    codigo_projeto : str
        Código interno do projeto (ex: 'FERSAM001', 'BRAANG01').
    theme : dict
        Tema Gold carregado via ``load_theme()``.
    output_dir : Path
        Pasta raiz de saída; subpastas por matriz são criadas automaticamente.
    env_file : str | None
        Caminho opcional para arquivo .env com FISICO_DB_URL.
    block : str
        '1'–'7' para bloco específico, ou 'all' para todos.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[meio_fisico] Carregando dados — projeto: {codigo_projeto}")
    df_total = _load_fisico_df(codigo_projeto, env_file)

    if df_total.empty:
        raise RuntimeError(
            f"Nenhum dado encontrado em fisico_analise_consolidada "
            f"para codigo_interno_opyta='{codigo_projeto}'."
        )

    matrizes = df_total["matriz"].unique().tolist()
    print(f"[meio_fisico] {len(df_total)} registros | matrizes: {matrizes}")

    blocos_executar = (
        list(_BLOCOS.keys()) if block == "all"
        else [b.strip() for b in str(block).split(",")]
    )

    generated_files: List[str] = []
    executed_blocks: List[str] = []

    for b in blocos_executar:
        label = _BLOCOS.get(b, f"Bloco {b}")
        print(f"  → Bloco {b}: {label}")

        try:
            if b == "1":
                for m in matrizes:
                    sub_dir = output_dir / _safe_name(m)
                    sub_dir.mkdir(exist_ok=True)
                    generated_files += _bloco_01_conformidade(
                        df_total[df_total["matriz"] == m], m, sub_dir
                    )

            elif b == "2":
                for m in matrizes:
                    sub_dir = output_dir / _safe_name(m)
                    sub_dir.mkdir(exist_ok=True)
                    generated_files += _bloco_02_violacao(
                        df_total[df_total["matriz"] == m], m, sub_dir, theme
                    )

            elif b == "3":
                for m in matrizes:
                    sub_dir = output_dir / _safe_name(m)
                    sub_dir.mkdir(exist_ok=True)
                    generated_files += _bloco_03_series_temporais(
                        df_total[df_total["matriz"] == m], m, sub_dir, theme
                    )

            elif b == "4":
                sub_dir = output_dir / "Agua_Superficial"
                sub_dir.mkdir(exist_ok=True)
                generated_files += _bloco_04_iqa(df_total, sub_dir, theme)

            elif b == "5":
                sub_dir = output_dir / "Agua_Superficial"
                sub_dir.mkdir(exist_ok=True)
                generated_files += _bloco_05_iet(df_total, sub_dir, theme)

            elif b == "6":
                sub_dir = output_dir / "Agua_Subterranea"
                sub_dir.mkdir(exist_ok=True)
                generated_files += _bloco_06_iqasb(df_total, sub_dir, theme)

            elif b == "7":
                sub_dir = output_dir / "Sedimento"
                sub_dir.mkdir(exist_ok=True)
                generated_files += _bloco_07_mpelq(df_total, sub_dir, theme)

            else:
                print(f"  [AVISO] Bloco '{b}' desconhecido — ignorado.")
                continue

            executed_blocks.append(b)

        except Exception as exc:
            print(f"  [ERRO] Bloco {b} falhou: {exc}")

    print(f"[meio_fisico] Concluído. {len(generated_files)} arquivo(s) gerado(s).")

    return {
        "project_name": codigo_projeto,
        "rows_loaded": len(df_total),
        "campaigns": sorted(df_total["nome_campanha"].unique().tolist(),
                            key=_sort_key_campanha),
        "points": sorted(df_total["nome_ponto"].unique().tolist()),
        "executed_blocks": executed_blocks,
        "generated_files": generated_files,
    }
