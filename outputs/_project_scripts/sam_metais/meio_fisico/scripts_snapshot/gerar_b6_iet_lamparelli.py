"""
B6 - IET Lamparelli (reservatorio).

IET(PT) = 10*(6 - (1.77 - 0.42*ln(PT))/ln(2))   # PT em mg/L
IET(CL) = 10*(6 - (0.92 - 0.34*ln(CL))/ln(2))   # CL em ug/L
IET = (IET(PT) + IET(CL)) / 2

Classes (Lamparelli 2004):
  <=47 Ultraoligotrofico | 47-52 Oligo | 52-59 Meso | 59-63 Eutrofico
  63-67 Supereutrofico | >67 Hipereutrofico

Saidas: Superficial/06_IET_Heatmap.png e 06_IET_Tabela.xlsx
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
from matplotlib.colors import ListedColormap, BoundaryNorm

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"
CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
SRC = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
OUT = CLIENT_ROOT / "Resultados" / "Meio_físico" / "Superficial"


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
    if v <= 47: return "Ultraoligotrófico"
    if v <= 52: return "Oligotrófico"
    if v <= 59: return "Mesotrófico"
    if v <= 63: return "Eutrófico"
    if v <= 67: return "Supereutrófico"
    return "Hipereutrófico"


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)
    df = pd.read_excel(SRC, sheet_name="Resultados_Meio_Fisico", dtype=str)
    for c in ["Matriz", "Parametro", "Ponto", "Campanha", "Unidade_Medida"]:
        df[c] = df[c].astype(str).str.strip()
    sup = df[df["Matriz"] == "Água Superficial"].copy()

    pt = sup[sup["Parametro"] == "Fósforo Total"].copy()
    pt["_v"] = pt["Resultado"].map(parse)
    cl = sup[sup["Parametro"] == "Clorofila A"].copy()
    cl["_v"] = cl["Resultado"].map(parse)
    # unidades: PT esperada mg/L; CL esperada ug/L
    un_pt = pt["Unidade_Medida"].iloc[0] if len(pt) else ""
    un_cl = cl["Unidade_Medida"].iloc[0] if len(cl) else ""
    print(f"  [B6] PT em '{un_pt}' | Clorofila em '{un_cl}'")

    pt_pv = pt.groupby(["Ponto", "Campanha"])["_v"].mean()
    cl_pv = cl.groupby(["Ponto", "Campanha"])["_v"].mean()

    rows = []
    keys = sorted(set(pt_pv.index) | set(cl_pv.index))
    for ponto, camp in keys:
        p = pt_pv.get((ponto, camp)); c = cl_pv.get((ponto, camp))
        iet_p = iet_c = iet = np.nan
        if p is not None and not pd.isna(p) and p > 0:
            iet_p = 10 * (6 - (1.77 - 0.42 * np.log(p)) / np.log(2))
        if c is not None and not pd.isna(c) and c > 0:
            iet_c = 10 * (6 - (0.92 - 0.34 * np.log(c)) / np.log(2))
        comp = [v for v in (iet_p, iet_c) if not np.isnan(v)]
        if comp: iet = float(np.mean(comp))
        rows.append({
            "Ponto": ponto, "Campanha": camp,
            "PT_mg_L": p, "Clorofila_ug_L": c,
            "IET_PT": iet_p, "IET_CL": iet_c, "IET": iet,
            "Classe": classe(iet) if not np.isnan(iet) else "",
        })
    df_out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    xlsx = OUT / "06_IET_Tabela.xlsx"
    try: df_out.to_excel(xlsx, index=False)
    except PermissionError:
        xlsx = xlsx.with_name(xlsx.stem + "_NEW.xlsx"); df_out.to_excel(xlsx, index=False)

    pivot = df_out.pivot_table(index="Ponto", columns="Campanha", values="IET", aggfunc="mean")
    if pivot.empty: print("[B6] sem dados"); return

    def camp_key(c):
        m = re.search(r"(\d+)", str(c))
        return (int(m.group(1)), str(c)) if m else (9999, str(c))
    pivot = pivot[sorted(pivot.columns, key=camp_key)].sort_index()

    cmap = ListedColormap(["#3498db", "#5dade2", "#f1c40f", "#e67e22", "#e74c3c", "#8B0000"])
    norm = BoundaryNorm([0, 47, 52, 59, 63, 67, 200], cmap.N)
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
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", color="black", fontsize=11)
    cbar = fig.colorbar(im, ax=ax, ticks=[40, 49.5, 55.5, 61, 65, 75])
    cbar.ax.set_yticklabels(["Ultra", "Oligo", "Meso", "Eu", "Super", "Hiper"])
    ax.set_xlabel("Campanha", fontsize=int(theme.get("font_size_base", 14)))
    ax.set_ylabel("Ponto", fontsize=int(theme.get("font_size_base", 14)))
    fig.tight_layout()
    png = OUT / "06_IET_Heatmap.png"
    try: fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        png = png.with_name(png.stem + "_NEW.png")
        fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    print(f"[B6] OK - {len(df_out)} amostras | media={df_out['IET'].mean():.1f} | classes: {df_out['Classe'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
