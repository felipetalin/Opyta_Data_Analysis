"""
B5 - IQA CETESB (Aguas Superficiais).

IQA = produto(qi^wi) com 9 parametros:
  OD (%SAT), Coliformes Term, pH, DBO5, N total, P total, dT, Turbidez, Solidos totais

Curvas q-i aproximadas por interpolacao linear de pontos tabulados (CETESB Apendice E).
Saida:
  Resultados/Meio_físico/Superficial/05_IQA_Heatmap.png
  Resultados/Meio_físico/Superficial/05_IQA_Tabela.xlsx
"""

from __future__ import annotations

import json
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
SRC_RES = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
OUT_DIR = CLIENT_ROOT / "Resultados" / "Meio_físico" / "Superficial"

PARAM_MAP = {
    "OD": "Oxigênio Dissolvido In Situ",
    "DBO": "Demanda Bioquímica de Oxigênio",
    "COLI": "Coliformes Termotolerantes por tubos múltiplos - NMP",
    "PH": "pH In Situ",
    "NT": "Nitrogênio Total",
    "PT": "Fósforo Total",
    "TEMP": "Temperatura da Amostra - in situ",
    "TURB": "Turbidez",
    "ST": "Sólidos Totais",
}

WEIGHTS = {"OD": 0.17, "COLI": 0.15, "PH": 0.12, "DBO": 0.10, "NT": 0.10,
           "PT": 0.10, "TEMP": 0.10, "TURB": 0.08, "ST": 0.08}

# Curvas q-i (pontos tabulados x,q). Fora do range: q=1 ou q=cauda.
Q_CURVES = {
    # OD: %SAT
    "OD": [(0, 3), (10, 6), (20, 11), (30, 17), (40, 27), (50, 41), (60, 56),
           (70, 73), (80, 86), (90, 95), (100, 100), (110, 95), (120, 85),
           (130, 75), (140, 65), (150, 56)],
    # Coliformes Termo NMP/100mL — eixo x em log10
    "COLI_LOG": [(0, 99), (1, 90), (2, 70), (3, 45), (4, 22), (5, 7), (6, 3)],
    # pH
    "PH": [(2, 2), (3, 5), (4, 11), (5, 26), (6, 60), (7, 92), (7.5, 95),
           (8, 88), (9, 50), (10, 22), (11, 5), (12, 2)],
    # DBO5 mg/L
    "DBO": [(0, 99), (1, 90), (2, 80), (3, 71), (4, 64), (5, 58), (8, 41),
           (10, 32), (15, 20), (20, 12), (30, 5)],
    # N total mg/L
    "NT": [(0, 100), (1, 88), (2, 75), (3, 62), (5, 45), (10, 30), (20, 12),
           (50, 4), (100, 1)],
    # P total mg/L
    "PT": [(0, 99), (0.1, 88), (0.2, 75), (0.5, 50), (1, 28), (2, 13),
           (5, 5), (10, 1)],
    # dT em °C
    "TEMP": [(-10, 50), (-5, 78), (-3, 88), (-1, 93), (0, 93), (1, 92),
             (3, 78), (5, 56), (8, 30), (10, 18), (15, 5)],
    # Turbidez NTU
    "TURB": [(0, 97), (5, 84), (10, 72), (25, 47), (50, 28), (75, 15),
             (100, 8), (150, 3), (200, 2)],
    # Solidos totais mg/L
    "ST": [(0, 80), (50, 86), (100, 90), (150, 88), (200, 82), (300, 70),
            (400, 56), (500, 42), (750, 22), (1000, 12), (1500, 5)],
}


def q_interp(key, x):
    pts = Q_CURVES[key]
    xs = [p[0] for p in pts]; qs = [p[1] for p in pts]
    if x <= xs[0]: return float(qs[0])
    if x >= xs[-1]: return float(qs[-1])
    return float(np.interp(x, xs, qs))


def od_sat_mgL(temp_c):
    T = temp_c
    return 14.652 - 0.41022 * T + 0.0079910 * T**2 - 0.000077774 * T**3


def parse_valor(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    s = str(v).strip()
    for sym in ("<=", ">=", "<", ">"):
        if s.startswith(sym): s = s[len(sym):].strip(); break
    s = s.replace(",", ".").replace(" ", "")
    try: return float(s)
    except ValueError: return None


def classe_iqa(v):
    if np.isnan(v): return ""
    if v > 79: return "Otima"
    if v > 51: return "Boa"
    if v > 36: return "Regular"
    if v > 19: return "Ruim"
    return "Pessima"


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)

    df = pd.read_excel(SRC_RES, sheet_name="Resultados_Meio_Fisico", dtype=str)
    df["Matriz"] = df["Matriz"].astype(str).str.strip()
    df["Parametro"] = df["Parametro"].astype(str).str.strip()
    df["Ponto"] = df["Ponto"].astype(str).str.strip()
    df["Campanha"] = df["Campanha"].astype(str).str.strip()
    sup = df[df["Matriz"] == "Água Superficial"].copy()

    # pivot por parametro
    def pivot_param(nome):
        sub = sup[sup["Parametro"] == nome].copy()
        sub["_v"] = sub["Resultado"].map(parse_valor)
        return sub.groupby(["Ponto", "Campanha"])["_v"].mean()

    s_OD = pivot_param(PARAM_MAP["OD"])
    s_TEMP = pivot_param(PARAM_MAP["TEMP"])
    s_DBO = pivot_param(PARAM_MAP["DBO"])
    s_COLI = pivot_param(PARAM_MAP["COLI"])
    s_PH = pivot_param(PARAM_MAP["PH"])
    s_NT = pivot_param(PARAM_MAP["NT"])
    s_PT = pivot_param(PARAM_MAP["PT"])
    s_TURB = pivot_param(PARAM_MAP["TURB"])
    s_ST = pivot_param(PARAM_MAP["ST"])

    keys = sorted(set(s_OD.index) | set(s_PH.index) | set(s_DBO.index),
                  key=lambda k: (str(k[1]), str(k[0])))
    rows = []
    for ponto, camp in keys:
        try:
            od = s_OD.get((ponto, camp))
            temp = s_TEMP.get((ponto, camp))
            dbo = s_DBO.get((ponto, camp))
            coli = s_COLI.get((ponto, camp))
            ph = s_PH.get((ponto, camp))
            nt = s_NT.get((ponto, camp))
            pt = s_PT.get((ponto, camp))
            turb = s_TURB.get((ponto, camp))
            st = s_ST.get((ponto, camp))

            qs = {}
            # OD -> %SAT
            if od is not None and not pd.isna(od) and temp is not None and not pd.isna(temp):
                sat = od / od_sat_mgL(temp) * 100.0
                qs["OD"] = q_interp("OD", sat)
            if coli is not None and not pd.isna(coli) and coli > 0:
                qs["COLI"] = q_interp("COLI_LOG", np.log10(coli))
            if ph is not None and not pd.isna(ph): qs["PH"] = q_interp("PH", ph)
            if dbo is not None and not pd.isna(dbo): qs["DBO"] = q_interp("DBO", dbo)
            if nt is not None and not pd.isna(nt): qs["NT"] = q_interp("NT", nt)
            if pt is not None and not pd.isna(pt): qs["PT"] = q_interp("PT", pt)
            # TEMP: dT desconhecido -> dT=0 (q=93)
            qs["TEMP"] = q_interp("TEMP", 0)
            if turb is not None and not pd.isna(turb): qs["TURB"] = q_interp("TURB", turb)
            if st is not None and not pd.isna(st): qs["ST"] = q_interp("ST", st)

            # renormalizar pesos pelos disponiveis
            wsum = sum(WEIGHTS[k] for k in qs)
            if wsum == 0: continue
            iqa = 1.0
            for k, q in qs.items():
                w_norm = WEIGHTS[k] / wsum
                iqa *= max(q, 1.0) ** w_norm
            iqa = float(iqa)
            rows.append({
                "Ponto": ponto, "Campanha": camp, "IQA": iqa,
                "Classe": classe_iqa(iqa),
                "N_params": len(qs),
                "Params_usados": ",".join(sorted(qs.keys())),
            })
        except Exception as e:
            print(f"  warn {ponto}/{camp}: {e}")

    df_out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    xlsx = OUT_DIR / "05_IQA_Tabela.xlsx"
    try: df_out.to_excel(xlsx, index=False)
    except PermissionError:
        xlsx = xlsx.with_name(xlsx.stem + "_NEW.xlsx"); df_out.to_excel(xlsx, index=False)

    # Heatmap
    pivot = df_out.pivot_table(index="Ponto", columns="Campanha", values="IQA", aggfunc="mean")
    if pivot.empty:
        print("[B5] sem dados"); return
    # ordem campanhas
    def camp_key(c):
        import re
        m = re.search(r"(\d+)", str(c))
        return (int(m.group(1)), str(c)) if m else (9999, str(c))
    cols = sorted(pivot.columns, key=camp_key)
    pivot = pivot[cols].sort_index()

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
    fig.tight_layout()
    png = OUT_DIR / "05_IQA_Heatmap.png"
    try: fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        png = png.with_name(png.stem + "_NEW.png")
        fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    print(f"[B5] OK - {len(df_out)} amostras IQA | media={df_out['IQA'].mean():.1f} | classes: {df_out['Classe'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
