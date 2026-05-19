"""
B8 - m-PEL-q (Sedimento, 8 metais).

m-PEL-q = media aritmetica das razoes (C_i / N2_i) para metais com VMP_454_N2 no cadastro.
Adaptado de Long et al. (1998) usando CONAMA 454 N2 como equivalente PEL.

Classes:
  <0.1 Baixo | 0.1-0.5 Medio | 0.5-1.5 Alto | >1.5 Muito Alto

Saidas: Sedimentos/08_mPELq_Tabela.xlsx e 08_mPELq_Barras.png
"""

from __future__ import annotations

import os

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"
CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
SRC = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
CAD = CLIENT_ROOT / "Migração" / "Físico" / "cadastro_parametros_opyta.xlsx"
OUT = CLIENT_ROOT / "Resultados" / "Meio_físico" / "Sedimentos"

METAIS = ["Arsênio Total", "Cádmio Total", "Chumbo Total", "Cobre", "Cromo Total",
          "Mercúrio Total", "Níquel", "Zinco"]


def parse(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return None
    s = str(v).strip()
    for sym in ("<=", ">=", "<", ">"):
        if s.startswith(sym): s = s[len(sym):].strip(); break
    s = s.replace(",", ".").replace(" ", "")
    try: return float(s)
    except ValueError: return None


def classe(v):
    if np.isnan(v): return ""
    if v < 0.1: return "Baixo"
    if v < 0.5: return "Médio"
    if v < 1.5: return "Alto"
    return "Muito Alto"


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)
    df = pd.read_excel(SRC, sheet_name="Resultados_Meio_Fisico", dtype=str)
    for c in ["Matriz", "Parametro", "Ponto", "Campanha"]:
        df[c] = df[c].astype(str).str.strip()
    sed = df[df["Matriz"] == "Sedimento"].copy()
    sed["_v"] = sed["Resultado"].map(parse)

    cad = pd.read_excel(CAD, sheet_name="Sedimento")
    cad["Parametro"] = cad["Parametro"].astype(str).str.strip()
    cad_idx = cad.set_index("Parametro")

    n2 = {}
    for m in METAIS:
        if m in cad_idx.index and "VMP_454_N2" in cad.columns:
            v = cad_idx.loc[m, "VMP_454_N2"]
            try: n2[m] = float(str(v).replace(",", "."))
            except (ValueError, TypeError): pass
    print(f"  [B8] N2 carregados: {n2}")

    pv = sed.groupby(["Ponto", "Campanha", "Parametro"])["_v"].mean().unstack("Parametro")

    rows = []
    for (ponto, camp), r in pv.iterrows():
        ratios = []
        for m, n2v in n2.items():
            if m in r and not pd.isna(r[m]) and n2v > 0:
                ratios.append(r[m] / n2v)
        if not ratios: continue
        mq = float(np.mean(ratios))
        rows.append({"Ponto": ponto, "Campanha": camp, "m_PEL_q": mq,
                     "N_metais": len(ratios), "Classe": classe(mq)})

    df_out = pd.DataFrame(rows).sort_values(["Campanha", "Ponto"])
    OUT.mkdir(parents=True, exist_ok=True)
    xlsx = OUT / "08_mPELq_Tabela.xlsx"
    try: df_out.to_excel(xlsx, index=False)
    except PermissionError:
        xlsx = xlsx.with_name(xlsx.stem + "_NEW.xlsx"); df_out.to_excel(xlsx, index=False)

    if df_out.empty:
        print("[B8] sem dados"); return

    # Barras: agrupado por ponto, uma barra por campanha (cores tema)
    def ck(c):
        m = re.search(r"(\d+)", str(c))
        return (int(m.group(1)), str(c)) if m else (9999, str(c))

    pontos = sorted(df_out["Ponto"].unique())
    campanhas = sorted(df_out["Campanha"].unique(), key=ck)
    pal = ["#11420C", "#2E7D32", "#66BB6A"][:len(campanhas)] + ["#1B5E20"] * 10
    fig, ax = plt.subplots(figsize=tuple(theme.get("figsize_standard", [15, 10])),
                           dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(pontos), dtype=float)
    w = 0.8 / max(len(campanhas), 1)
    for i, camp in enumerate(campanhas):
        d = df_out[df_out["Campanha"] == camp].set_index("Ponto")
        vals = [d.loc[p, "m_PEL_q"] if p in d.index else np.nan for p in pontos]
        ax.bar(x + i * w - 0.4 + w/2, vals, w, color=pal[i], edgecolor="black", linewidth=0.5, label=camp)
    ax.axhline(0.1, color="#2ecc71", linestyle="--", linewidth=1.5, label="Limiar Baixo→Médio (0,1)")
    ax.axhline(0.5, color="#f39c12", linestyle="--", linewidth=1.5, label="Limiar Médio→Alto (0,5)")
    ax.axhline(1.5, color="#e74c3c", linestyle="--", linewidth=1.5, label="Limiar Alto→Muito Alto (1,5)")
    ax.set_xticks(x); ax.set_xticklabels(pontos, rotation=45, ha="right",
                                          fontsize=int(theme.get("font_size_base", 14)) - 2)
    ax.set_ylabel("m-PEL-q (média C/N2 — 8 metais)",
                  fontsize=int(theme.get("font_size_base", 14)))
    ax.set_xlabel("Ponto", fontsize=int(theme.get("font_size_base", 14)))
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_color("#000"); ax.spines[s].set_linewidth(1.2)
    handles, labels = ax.get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.99),
                        ncol=min(len(handles), 4), frameon=False)
    for t in legend.get_texts(): t.set_fontsize(int(theme.get("legend_size", 13)))
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    png = OUT / "08_mPELq_Barras.png"
    try: fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        png = png.with_name(png.stem + "_NEW.png")
        fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    print(f"[B8] OK - {len(df_out)} amostras | media={df_out['m_PEL_q'].mean():.3f} | classes: {df_out['Classe'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
