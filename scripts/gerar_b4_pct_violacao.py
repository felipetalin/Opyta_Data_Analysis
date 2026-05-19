"""
B4 (Etapa 5) — % Violacao por parametro, barras horizontais.

Para cada matriz, calcula a % de amostras em violacao por parametro
(considerando o VMP mais restritivo da matriz/cadastro):
- Superficial: VMP_357_Cl2_Max
- Subterranea: minimo entre 4 VMPs CONAMA 396 (mais restritivo).
- Sedimento: VMP_454_N1.

Saida: Resultados/Meio_físico/<sub>/04_Pct_Violacao.png e 04_Pct_Violacao.xlsx
"""

from __future__ import annotations

import os

import json
import re
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"
CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
SRC_RES = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
SRC_CAD = CLIENT_ROOT / "Migração" / "Físico" / "cadastro_parametros_opyta.xlsx"
OUT_ROOT = CLIENT_ROOT / "Resultados" / "Meio_físico"

MATRIZ_CFG = {
    "Água Superficial": {
        "subpasta": "Superficial",
        "aba_cad": "Aguas_Superficiais",
        "vmp_cols": ["VMP_357_Cl2_Max"],
        "modo": "min",
    },
    "Água Subterrânea": {
        "subpasta": "Subterrânea",
        "aba_cad": "Aguas_Subterraneas",
        "vmp_cols": [
            "VMP_396_Consumo_Humano",
            "VMP_396_Dessedentacao_Animal",
            "VMP_396_Irrigacao",
            "VMP_396_Recreacao",
        ],
        "modo": "min",
    },
    "Sedimento": {
        "subpasta": "Sedimentos",
        "aba_cad": "Sedimento",
        "vmp_cols": ["VMP_454_N1"],
        "modo": "min",
    },
}

# Amonia em Superficial depende de pH (357 Art.16): 3.7 / 2.0 / 1.0 / 0.5 mg/L
def limite_amonia(ph):
    if ph is None or np.isnan(ph):
        return 3.7
    if ph <= 7.5: return 3.7
    if ph <= 8.0: return 2.0
    if ph <= 8.5: return 1.0
    return 0.5


def _parse_valor(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None, ""
    s = str(v).strip()
    sinal = ""
    for sym in ("<=", ">=", "<", ">"):
        if s.startswith(sym):
            sinal = sym; s = s[len(sym):].strip(); break
    s = s.replace(",", ".").replace(" ", "")
    try:
        return float(s), sinal
    except ValueError:
        return None, sinal


def _parse_vmp(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return None
    s = str(v).strip().replace(",", ".")
    if s in {"", "-", "—", "NA", "N/A"}: return None
    try: return float(s)
    except ValueError: return None


_UNIT_FACTORS_TO_MGL = {
    "mg/l": 1.0,
    "µg/l": 1e-3,
    "μg/l": 1e-3,
    "ug/l": 1e-3,
    "ng/l": 1e-6,
    "mg/kg": 1.0,
    "µg/kg": 1e-3,
    "μg/kg": 1e-3,
    "ug/kg": 1e-3,
}


def _unit_norm(u):
    if u is None:
        return ""
    return str(u).strip().lower().replace(" ", "")


def _conv_factor(from_u, to_u):
    """Fator multiplicativo para X[from_u] -> X[to_u]. None se incomparavel."""
    a = _UNIT_FACTORS_TO_MGL.get(_unit_norm(from_u))
    b = _UNIT_FACTORS_TO_MGL.get(_unit_norm(to_u))
    if a is None or b is None:
        return None
    return a / b


def _safe(name):
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_")


def calcular_violacao_matriz(matriz, cfg, df_res, theme):
    df = df_res[df_res["Matriz"] == matriz].copy()
    df["Parametro"] = df["Parametro"].astype(str).str.strip()
    df_cad = pd.read_excel(SRC_CAD, sheet_name=cfg["aba_cad"])
    df_cad["Parametro"] = df_cad["Parametro"].astype(str).str.strip()
    # remove parametros duplicados no cadastro (mantém primeiro)
    df_cad = df_cad.drop_duplicates(subset=["Parametro"], keep="first")
    cad_idx = df_cad.set_index("Parametro")

    # ph map para Superficial
    ph_map = {}
    if matriz == "Água Superficial":
        df_ph = df[df["Parametro"].str.lower() == "ph"].copy()
        for _, r in df_ph.iterrows():
            v, _ = _parse_valor(r["Resultado"])
            if v is not None:
                ph_map[(str(r["Ponto"]).strip(), str(r["Campanha"]).strip())] = v

    rows = []
    for p in sorted(df["Parametro"].unique()):
        sub = df[df["Parametro"] == p]
        if p not in cad_idx.index:
            continue
        # Unidade autoritativa = moda dos dados; converte VMP cad->dados
        unidade_cad = cad_idx.loc[p, "Unidade_Medida"] if "Unidade_Medida" in df_cad.columns else None
        try:
            unidade_dados = sub["Unidade_Medida"].dropna().mode().iloc[0]
        except Exception:
            unidade_dados = unidade_cad
        factor = _conv_factor(unidade_cad, unidade_dados) if unidade_cad and unidade_dados else 1.0
        if factor is None:
            factor = 1.0
        vmps = []
        for c in cfg["vmp_cols"]:
            if c in df_cad.columns:
                v = _parse_vmp(cad_idx.loc[p, c])
                if v is None: continue
                if v <= 0: continue  # ignora VMP=0 (ex.: Arsênio Irrigação)
                vmps.append(v * factor)
        if not vmps and not (matriz == "Água Superficial" and p.lower().startswith("nitrogênio amon")):
            continue
        vmp_ref = min(vmps) if vmps else None

        n_total = 0; n_viol = 0
        for _, r in sub.iterrows():
            val, sinal = _parse_valor(r["Resultado"])
            if val is None: continue
            n_total += 1
            limite = vmp_ref
            if matriz == "Água Superficial" and p.lower().startswith("nitrogênio amon"):
                ph_v = ph_map.get((str(r["Ponto"]).strip(), str(r["Campanha"]).strip()))
                limite = limite_amonia(ph_v)
            if limite is None: continue
            if sinal in ("<", "<="):
                viola = val > limite
            else:
                viola = val > limite
            if viola: n_viol += 1
        if n_total == 0: continue
        rows.append({
            "Parametro": p,
            "VMP_ref": vmp_ref,
            "N_amostras": n_total,
            "N_violacoes": n_viol,
            "Pct_Violacao": (n_viol / n_total) * 100.0,
        })

    df_out = pd.DataFrame(rows).sort_values("Pct_Violacao", ascending=True)
    if df_out.empty:
        print(f"  [{matriz}] sem dados para B4")
        return

    # Excel
    out_dir = OUT_ROOT / cfg["subpasta"]
    out_dir.mkdir(parents=True, exist_ok=True)
    xlsx = out_dir / "04_Pct_Violacao.xlsx"
    try:
        df_out.to_excel(xlsx, index=False)
    except PermissionError:
        xlsx = xlsx.with_name(xlsx.stem + "_NEW.xlsx")
        df_out.to_excel(xlsx, index=False)

    # PNG
    fig, ax = plt.subplots(
        figsize=tuple(theme.get("figsize_standard", [15, 10])),
        dpi=int(theme.get("dpi", 600)),
    )
    pal = theme.get("mf_violation_palette_green", ["#A5D6A7", "#66BB6A", "#2E7D32", "#11420C"])
    def cor(pct):
        if pct <= 5: return pal[0]
        if pct <= 25: return pal[1]
        if pct <= 50: return pal[2]
        return pal[3]
    cores = [cor(p) for p in df_out["Pct_Violacao"]]
    y = np.arange(len(df_out))
    ax.barh(y, df_out["Pct_Violacao"], color=cores, edgecolor="black", linewidth=0.5)
    for i, (pct, nv, nt) in enumerate(zip(df_out["Pct_Violacao"], df_out["N_violacoes"], df_out["N_amostras"])):
        ax.text(pct + 0.5, i, f"{pct:.1f}% ({nv}/{nt})", va="center",
                fontsize=int(theme.get("font_size_base", 14)) - 2)
    ax.set_yticks(y)
    ax.set_yticklabels(df_out["Parametro"], fontsize=int(theme.get("font_size_base", 14)) - 2)
    ax.set_xlabel("% de amostras em violação", fontsize=int(theme.get("font_size_base", 14)))
    ax.set_xlim(0, max(100, df_out["Pct_Violacao"].max() * 1.15))
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_color("#000"); ax.spines[side].set_linewidth(1.2)
    fig.tight_layout()
    png = out_dir / "04_Pct_Violacao.png"
    try:
        fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        png = png.with_name(png.stem + "_NEW.png")
        fig.savefig(png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    print(f"  [{matriz}] {len(df_out)} parametros | top: {df_out.iloc[-1]['Parametro']} ({df_out.iloc[-1]['Pct_Violacao']:.1f}%)")


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)
    # paleta padrao se nao houver no tema
    theme.setdefault("mf_violation_palette", ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"])
    df_res = pd.read_excel(SRC_RES, sheet_name="Resultados_Meio_Fisico", dtype=str)
    df_res["Matriz"] = df_res["Matriz"].astype(str).str.strip()
    df_res["Parametro"] = df_res["Parametro"].astype(str).str.strip()
    print("[B4] Calculando % violacao...")
    for matriz, cfg in MATRIZ_CFG.items():
        calcular_violacao_matriz(matriz, cfg, df_res, theme)
    print("[B4] OK")


if __name__ == "__main__":
    main()
