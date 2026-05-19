"""
B7 - IQASB parcial 4/5 (Aguas Subterraneas).

IQASB completo: pH (0.22), OD (0.22), CE (0.20), NO3 (0.20), SO4 (0.16).
Como SO4 nao foi analisado, calculamos IQASB PARCIAL com 4 parametros e
pesos renormalizados pela soma 0.84.

Curvas q-i simplificadas baseadas em adaptacoes da literatura.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, BoundaryNorm

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"
CLIENT_ROOT = Path(r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos")
SRC = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
OUT = CLIENT_ROOT / "Resultados" / "Meio_físico" / "Subterrânea"

PARAM = {"PH": "pH In Situ", "OD": "Oxigênio Dissolvido In Situ",
         "CE": "Condutividade Elétrica", "NO3": "Nitrato"}
W_FULL = {"PH": 0.22, "OD": 0.22, "CE": 0.20, "NO3": 0.20, "SO4": 0.16}
W_SUB = {k: v / (1.0 - W_FULL["SO4"]) for k, v in W_FULL.items() if k != "SO4"}

Q = {
    "PH": [(2, 2), (3, 5), (4, 11), (5, 26), (6, 60), (7, 92), (7.5, 95),
           (8, 88), (9, 50), (10, 22), (11, 5), (12, 2)],
    "OD": [(0, 3), (1, 15), (2, 30), (3, 50), (4, 70), (5, 85), (6, 92),
           (8, 98), (10, 100)],
    "CE": [(0, 100), (100, 95), (250, 88), (500, 75), (1000, 55),
           (2000, 30), (5000, 10), (10000, 2)],
    "NO3": [(0, 99), (1, 95), (5, 85), (10, 65), (20, 40), (30, 22),
            (45, 12), (50, 8), (100, 2)],
}


def qi(key, x):
    pts = Q[key]; xs = [p[0] for p in pts]; qs = [p[1] for p in pts]
    if x <= xs[0]: return float(qs[0])
    if x >= xs[-1]: return float(qs[-1])
    return float(np.interp(x, xs, qs))


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
    if v > 79: return "Otima"
    if v > 51: return "Boa"
    if v > 36: return "Regular"
    if v > 19: return "Ruim"
    return "Pessima"


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)
    df = pd.read_excel(SRC, sheet_name="Resultados_Meio_Fisico", dtype=str)
    for c in ["Matriz", "Parametro", "Ponto", "Campanha"]:
        df[c] = df[c].astype(str).str.strip()
    sub = df[df["Matriz"] == "Água Subterrânea"].copy()
    sub["_v"] = sub["Resultado"].map(parse)

    def pv(nome):
        return sub[sub["Parametro"] == nome].groupby(["Ponto", "Campanha"])["_v"].mean()

    p_ph = pv(PARAM["PH"]); p_od = pv(PARAM["OD"])
    p_ce = pv(PARAM["CE"]); p_no3 = pv(PARAM["NO3"])

    rows = []
    keys = sorted(set(p_ph.index) | set(p_od.index) | set(p_ce.index) | set(p_no3.index))
    for ponto, camp in keys:
        vals = {
            "PH": p_ph.get((ponto, camp)),
            "OD": p_od.get((ponto, camp)),
            "CE": p_ce.get((ponto, camp)),
            "NO3": p_no3.get((ponto, camp)),
        }
        qs = {k: qi(k, v) for k, v in vals.items() if v is not None and not pd.isna(v)}
        if not qs: continue
        wsum = sum(W_SUB[k] for k in qs)
        iq = 1.0
        for k, q in qs.items():
            iq *= max(q, 1.0) ** (W_SUB[k] / wsum)
        iq = float(iq)
        rows.append({
            "Ponto": ponto, "Campanha": camp, "IQASB_parcial": iq,
            "Classe": classe(iq), "N_params": len(qs),
            "Params": ",".join(sorted(qs.keys())),
            "pH": vals["PH"], "OD_mgL": vals["OD"], "CE_uScm": vals["CE"], "NO3_mgL": vals["NO3"],
        })
    df_out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    xlsx = OUT / "07_IQASB_parcial_Tabela.xlsx"
    try: df_out.to_excel(xlsx, index=False)
    except PermissionError:
        xlsx = xlsx.with_name(xlsx.stem + "_NEW.xlsx"); df_out.to_excel(xlsx, index=False)

    pivot = df_out.pivot_table(index="Ponto", columns="Campanha", values="IQASB_parcial", aggfunc="mean")
    if pivot.empty: print("[B7] sem dados"); return
    def ck(c):
        m = re.search(r"(\d+)", str(c))
        return (int(m.group(1)), str(c)) if m else (9999, str(c))
    pivot = pivot[sorted(pivot.columns, key=ck)].sort_index()

    cmap = ListedColormap(["#8B0000", "#e74c3c", "#f39c12", "#3498db", "#2ecc71"])
    norm = BoundaryNorm([0, 19, 36, 51, 79, 100], cmap.N)
    fig, ax = plt.subplots(figsize=tuple(theme.get("figsize_standard", [15, 10])),
                           dpi=int(theme.get("dpi", 600)))
    im = ax.imshow(pivot.values, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right",
                       fontsize=int(theme.get("font_size_base", 14)) - 2)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=int(theme.get("font_size_base", 14)) - 2)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        color="white" if v < 36 else "black", fontsize=11)
    cbar = fig.colorbar(im, ax=ax, ticks=[10, 27, 43, 65, 90])
    cbar.ax.set_yticklabels(["Péssima", "Ruim", "Regular", "Boa", "Ótima"])
    ax.set_xlabel("Campanha", fontsize=int(theme.get("font_size_base", 14)))
    ax.set_ylabel("Ponto", fontsize=int(theme.get("font_size_base", 14)))
    ax.set_title("IQASB parcial 4/5 (sem SO4 — pesos renormalizados)",
                 fontsize=int(theme.get("font_size_base", 14)))
    fig.tight_layout()
    png = OUT / "07_IQASB_parcial_Heatmap.png"
    try: fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        png = png.with_name(png.stem + "_NEW.png")
        fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    print(f"[B7] OK - {len(df_out)} amostras | media={df_out['IQASB_parcial'].mean():.1f} | classes: {df_out['Classe'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
