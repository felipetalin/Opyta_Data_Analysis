"""
B9 - Boxplot Seca x Chuva + Mann-Whitney (2 campanhas).

Para cada matriz:
- xlsx com todos os parametros: medianas, IQR, U-stat, p-valor, significancia.
- PNG resumo (grid 4x3) com os 12 parametros de menor p-valor.
"""

from __future__ import annotations

import os

import json
import unicodedata
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"
CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
SRC = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
OUT_ROOT = CLIENT_ROOT / "Resultados" / "Meio_físico"

SUBS = {"Água Superficial": "Superficial", "Água Subterrânea": "Subterrânea", "Sedimento": "Sedimentos"}


def parse(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return None
    s = str(v).strip()
    for sym in ("<=", ">=", "<", ">"):
        if s.startswith(sym): s = s[len(sym):].strip(); break
    s = s.replace(",", ".").replace(" ", "")
    try: return float(s)
    except ValueError: return None


def sig(p):
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "ns"


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)
    df = pd.read_excel(SRC, sheet_name="Resultados_Meio_Fisico", dtype=str)
    for c in ["Matriz", "Parametro", "Ponto", "Campanha"]:
        df[c] = df[c].astype(str).str.strip()
    df["_v"] = df["Resultado"].map(parse)
    df = df.dropna(subset=["_v"])

    for matriz, sub in SUBS.items():
        d = df[df["Matriz"] == matriz].copy()
        if d.empty: continue
        rows = []
        for p, sub_p in d.groupby("Parametro"):
            seca = sub_p[sub_p["Campanha"].str.contains("Seca", case=False, na=False)]["_v"].values
            chuva = sub_p[sub_p["Campanha"].str.contains("Chuva", case=False, na=False)]["_v"].values
            if len(seca) < 3 or len(chuva) < 3:
                continue
            try:
                u, pv = mannwhitneyu(seca, chuva, alternative="two-sided")
            except ValueError:
                u, pv = np.nan, np.nan
            rows.append({
                "Parametro": p,
                "N_Seca": len(seca), "N_Chuva": len(chuva),
                "Mediana_Seca": float(np.median(seca)),
                "Mediana_Chuva": float(np.median(chuva)),
                "Delta_pct": ((float(np.median(chuva)) - float(np.median(seca)))
                              / max(abs(float(np.median(seca))), 1e-9)) * 100 if np.median(seca) else np.nan,
                "U_stat": float(u) if not pd.isna(u) else np.nan,
                "p_valor": float(pv) if not pd.isna(pv) else np.nan,
                "Significancia": sig(pv),
            })
        df_out = pd.DataFrame(rows).sort_values("p_valor")
        out_dir = OUT_ROOT / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        xlsx = out_dir / "09_Sazonal_MannWhitney.xlsx"
        try: df_out.to_excel(xlsx, index=False)
        except PermissionError:
            xlsx = xlsx.with_name(xlsx.stem + "_NEW.xlsx"); df_out.to_excel(xlsx, index=False)

        # PNG resumo: top 12 menor p-valor
        top = df_out.head(12)
        n = len(top)
        if n == 0:
            print(f"  [{matriz}] sem dados para boxplot"); continue
        cols = 3; lines = int(np.ceil(n / cols))
        fig, axes = plt.subplots(lines, cols, figsize=(15, 4 * lines),
                                 dpi=int(theme.get("dpi", 600)))
        axes = np.atleast_2d(axes).reshape(lines, cols)
        for i, (_, r) in enumerate(top.iterrows()):
            ax = axes[i // cols, i % cols]
            sub_p = d[d["Parametro"] == r["Parametro"]]
            seca = sub_p[sub_p["Campanha"].str.contains("Seca", case=False, na=False)]["_v"].values
            chuva = sub_p[sub_p["Campanha"].str.contains("Chuva", case=False, na=False)]["_v"].values
            bp = ax.boxplot([seca, chuva], labels=["Seca", "Chuva"], patch_artist=True,
                            widths=0.6, medianprops={"color": "black", "linewidth": 2})
            for box, col in zip(bp["boxes"], ["#e67e22", "#3498db"]):
                box.set_facecolor(col); box.set_edgecolor("black")
            ax.scatter(np.random.normal(1, 0.05, size=len(seca)), seca, color="#a04000",
                       s=20, alpha=0.6, zorder=3)
            ax.scatter(np.random.normal(2, 0.05, size=len(chuva)), chuva, color="#1f618d",
                       s=20, alpha=0.6, zorder=3)
            title = (r["Parametro"][:30] + "...") if len(r["Parametro"]) > 33 else r["Parametro"]
            ax.set_title(f"{title}\np={r['p_valor']:.3f} {r['Significancia']}", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.25)
            for s in ("top", "right", "left", "bottom"):
                ax.spines[s].set_color("#000"); ax.spines[s].set_linewidth(0.8)
        # esconder subplots vazios
        for j in range(n, lines * cols):
            axes[j // cols, j % cols].axis("off")
        fig.tight_layout()
        png = out_dir / "09_Sazonal_Boxplots_top12.png"
        try: fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        except PermissionError:
            png = png.with_name(png.stem + "_NEW.png")
            fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        nsig = (df_out["p_valor"] < 0.05).sum()
        print(f"  [{matriz}] {len(df_out)} parametros | {nsig} significativos (p<0.05)")


if __name__ == "__main__":
    main()
