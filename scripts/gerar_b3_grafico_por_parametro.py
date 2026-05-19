"""
B3 (Etapa 4) — Gráfico Gold Fauna por parâmetro, para as 3 matrizes.

Reusa o contrato visual do piloto (Etapa 3) e itera sobre todos os parâmetros.
Regras de VMP por matriz:
- Água Superficial:  apenas Classe 2 (1 linha).
- Água Subterrânea:  4 VMPs CONAMA 396 (Consumo Humano, Dessedentação, Irrigação, Recreação).
- Sedimento:         N1 e N2 (CONAMA 454).

Saídas:
  Resultados/Meio_físico/<subpasta>/03_<nome_parametro>.png

Uso:
    python scripts/gerar_b3_grafico_por_parametro.py
"""

from __future__ import annotations

import os

import colorsys
import json
import re
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"

CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
SRC_RESULTADOS = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
SRC_CADASTRO = CLIENT_ROOT / "Migração" / "Físico" / "cadastro_parametros_opyta.xlsx"
OUT_ROOT = CLIENT_ROOT / "Resultados" / "Meio_físico"

FAUNA_CAMPAIGN_BASE_HEX = "#11420C"

# Parâmetros que se beneficiam de escala log (alta amplitude dinâmica)
LOG_HINTS = ["coliforme", "escherichia", "e. coli"]

MATRIZ_CFG = {
    "Água Superficial": {
        "subpasta": "Superficial",
        "aba_cad": "Aguas_Superficiais",
        "vmps": [
            ("VMP_357_Cl2_Max", "VMP CONAMA 357 — Classe 2 (máx)", "mf_vmp_default"),
            ("VMP_357_Cl2_Min", "VMP CONAMA 357 — Classe 2 (mín)", "mf_vmp_default"),
        ],
    },
    "Água Subterrânea": {
        "subpasta": "Subterrânea",
        "aba_cad": "Aguas_Subterraneas",
        "vmps": [
            ("VMP_396_Consumo_Humano", "Consumo Humano", "mf_vmp_consumo_humano"),
            ("VMP_396_Dessedentacao_Animal", "Dessedentação Animal", "mf_vmp_dessedentacao"),
            ("VMP_396_Irrigacao", "Irrigação", "mf_vmp_irrigacao"),
            ("VMP_396_Recreacao", "Recreação", "mf_vmp_recreacao"),
        ],
    },
    "Sedimento": {
        "subpasta": "Sedimentos",
        "aba_cad": "Sedimento",
        "vmps": [
            ("VMP_454_N1", "CONAMA 454 — Nível 1", "mf_vmp_n1"),
            ("VMP_454_N2", "CONAMA 454 — Nível 2", "mf_vmp_n2"),
        ],
    },
}


# ----------------------------------------------------------------------------
def _norm(s):
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_valor(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None, ""
    s = str(val).strip()
    sinal = ""
    for sym in ("<=", ">=", "<", ">"):
        if s.startswith(sym):
            sinal = sym
            s = s[len(sym):].strip()
            break
    s = s.replace(",", ".").replace(" ", "")
    if not s:
        return None, sinal
    try:
        return float(s), sinal
    except ValueError:
        return None, sinal


def _parse_vmp(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    s = str(val).strip()
    if s in {"", "-", "—", "NA", "N/A"}:
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

_UNIT_FACTORS_TO_MGL = {
    "mg/l": 1.0,
    "\u00b5g/l": 1e-3,
    "ug/l": 1e-3,
    "ng/l": 1e-6,
    "mg/kg": 1.0,
    "\u00b5g/kg": 1e-3,
    "ug/kg": 1e-3,
}


def _unit_norm(u):
    """Normaliza unidade para chave de _UNIT_FACTORS_TO_MGL."""
    if u is None:
        return ""
    s = str(u).strip().lower().replace(" ", "")
    # tratar 'ug' como microgramas
    return s


def _conv_factor(from_u, to_u):
    """Fator multiplicativo para X[from_u] -> X[to_u]. None se incomparavel."""
    a = _UNIT_FACTORS_TO_MGL.get(_unit_norm(from_u))
    b = _UNIT_FACTORS_TO_MGL.get(_unit_norm(to_u))
    if a is None or b is None:
        return None
    return a / b

def _camp_sort(c):
    s = str(c)
    m = re.search(r"(\d+)", s)
    return (0, int(m.group(1)), s) if m else (1, 9999, s)


def _hex_to_rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


def _green_palette(base, n):
    rgb = _hex_to_rgb(base)
    h, s, _ = colorsys.rgb_to_hsv(*rgb)
    out = []
    for i in range(max(n, 1)):
        t = i / max(n - 1, 1)
        out.append(_rgb_to_hex(colorsys.hsv_to_rgb(h, 0.8 + 0.2 * t, 0.5 + 0.5 * t)))
    return out


def _safe_filename(name):
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    return s.strip("_")


# ----------------------------------------------------------------------------
def gerar_grafico(
    df_param, param, unidade, vmps_ativos, matriz_subpasta, theme, use_log=False
):
    d = df_param.copy()
    d["Campanha"] = d["Campanha"].astype(str).str.strip()
    d["Ponto"] = d["Ponto"].astype(str).str.strip()
    parsed = d["Resultado"].map(_parse_valor)
    d["_valor"] = parsed.map(lambda t: t[0])
    d["_sinal"] = parsed.map(lambda t: t[1])
    d = d.dropna(subset=["_valor"]).copy()
    if d.empty:
        return None

    campaigns = sorted(d["Campanha"].unique(), key=_camp_sort)
    points = sorted(d["Ponto"].unique())

    pivot = (
        d.groupby(["Ponto", "Campanha"])["_valor"]
        .mean()
        .reset_index()
        .pivot_table(index="Ponto", columns="Campanha", values="_valor", aggfunc="mean")
        .reindex(index=points, columns=campaigns)
    )

    palette = _green_palette(FAUNA_CAMPAIGN_BASE_HEX, len(campaigns))
    color_map = {c: palette[i] for i, c in enumerate(campaigns)}

    fig, ax = plt.subplots(
        figsize=tuple(theme.get("figsize_standard", [15, 10])),
        dpi=int(theme.get("dpi", 600)),
    )
    x = np.arange(len(points), dtype=float)
    offsets = np.linspace(-0.15, 0.15, max(len(campaigns), 1)) if len(campaigns) > 1 else np.array([0.0])

    for i, camp in enumerate(campaigns):
        vals = pivot[camp].values.astype(float)
        valid = ~np.isnan(vals)
        if not np.any(valid):
            continue
        ax.scatter(
            x[valid] + offsets[i], vals[valid],
            s=70, marker="o", label=camp,
            color=color_map[camp], edgecolors="black", linewidths=0.4, zorder=4,
        )

    if vmps_ativos:
        y_max = float(np.nanmax(pivot.values))
        y_min = float(np.nanmin(pivot.values))
        lowers = [(l, v, c) for (l, v, c) in vmps_ativos if "mín" in l.lower() or "min" in l.lower()]
        uppers = [(l, v, c) for (l, v, c) in vmps_ativos if not ("mín" in l.lower() or "min" in l.lower())]
        shade_color = str(theme.get("mf_vmp_shade", "#e74c3c"))
        shade_alpha = float(theme.get("mf_vmp_shade_alpha", 0.06))
        if uppers:
            min_upper = min(v for _l, v, _c in uppers)
            topo = max(y_max, max(v for _l, v, _c in uppers)) * 1.10
            ax.axhspan(min_upper, topo, color=shade_color, alpha=shade_alpha, zorder=1)
        if lowers:
            max_lower = max(v for _l, v, _c in lowers)
            base = min(y_min, min(v for _l, v, _c in lowers)) - abs(max_lower) * 0.10
            ax.axhspan(base, max_lower, color=shade_color, alpha=shade_alpha, zorder=1)
        for label, v, color in vmps_ativos:
            ax.axhline(v, color=color, linewidth=2.0, label=f"{label} ({v:g})", zorder=2)

    loq_vals = d.loc[d["_sinal"] == "<", "_valor"].dropna().astype(float)
    if not loq_vals.empty:
        loq = float(np.nanmax(loq_vals.values))
        ax.axhline(
            loq, color="#7f7f7f", linewidth=1.6, linestyle="--",
            label=f"LOQ ({loq:g})", zorder=2,
        )

    if use_log:
        # Garante limite inferior > 0
        positivos = d.loc[d["_valor"] > 0, "_valor"]
        if not positivos.empty:
            ax.set_yscale("log")

    ax.set_xticks(x)
    ax.set_xticklabels(
        points, rotation=45, ha="right",
        fontsize=int(theme.get("campaign_label_size", 14)),
    )
    ax.set_xlabel("Ponto", fontsize=int(theme.get("font_size_base", 14)))
    ylabel = f"{param} ({unidade})" if unidade else param
    ax.set_ylabel(ylabel, fontsize=int(theme.get("font_size_base", 14)))
    ax.set_title("")

    for axis_name in ("y", "x"):
        ax.grid(
            axis=axis_name,
            linestyle=str(theme.get("grid_linestyle", "--")),
            linewidth=float(theme.get("grid_linewidth", 0.6)),
            alpha=float(theme.get("grid_alpha", 0.25)),
        )

    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(str(theme.get("spine_color", "#000000")))
        ax.spines[side].set_linewidth(float(theme.get("spine_linewidth", 1.2)))

    handles, labels = ax.get_legend_handles_labels()
    legend = fig.legend(
        handles, labels,
        loc="upper center", bbox_to_anchor=(0.5, 0.99),
        ncol=min(max(2, len(handles)), 4), frameon=False,
    )
    for t in legend.get_texts():
        t.set_fontsize(int(theme.get("legend_size", 13)))

    fig.tight_layout(rect=[0, 0, 1, 0.90])

    out_dir = OUT_ROOT / matriz_subpasta
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"03_{_safe_filename(param)}.png"
    try:
        fig.savefig(out_path, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        alt = out_path.with_name(out_path.stem + "_NEW" + out_path.suffix)
        fig.savefig(alt, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        out_path = alt
    plt.close(fig)
    return out_path


def main():
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)

    print(f"[B3] Lendo {SRC_RESULTADOS.name} ...")
    df_res = pd.read_excel(SRC_RESULTADOS, sheet_name="Resultados_Meio_Fisico", dtype=str)
    df_res["Matriz"] = df_res["Matriz"].astype(str).str.strip()
    df_res["Parametro"] = df_res["Parametro"].astype(str).str.strip()
    df_res["Unidade_Medida"] = df_res["Unidade_Medida"].astype(str).str.strip()

    total = 0
    for matriz, cfg in MATRIZ_CFG.items():
        df_cad = pd.read_excel(SRC_CADASTRO, sheet_name=cfg["aba_cad"])
        df_cad["Parametro"] = df_cad["Parametro"].astype(str).str.strip()
        df_cad = df_cad.drop_duplicates(subset=["Parametro"], keep="first")
        cad_idx = df_cad.set_index("Parametro")

        sub = df_res[df_res["Matriz"] == matriz]
        params = sorted(sub["Parametro"].unique())
        print(f"\n[B3] {matriz} — {len(params)} parâmetros")

        for p in params:
            df_p = sub[sub["Parametro"] == p]
            unidade = df_p["Unidade_Medida"].iloc[0] if len(df_p) else ""
            if unidade is None or (isinstance(unidade, float) and np.isnan(unidade)):
                unidade = ""
            unidade = str(unidade)
            if unidade.lower() in {"nan", ""}:
                unidade = ""

            vmps_ativos = []
            unidade_cad = ""
            if p in cad_idx.index:
                if "Unidade_Medida" in df_cad.columns:
                    uc = cad_idx.loc[p, "Unidade_Medida"]
                    if isinstance(uc, pd.Series):
                        uc = uc.iloc[0]
                    if uc is not None and not (isinstance(uc, float) and np.isnan(uc)):
                        unidade_cad = str(uc)
                # fator de conversao VMP(cadastro) -> unidade dos dados
                factor = _conv_factor(unidade_cad, unidade) if unidade and unidade_cad else 1.0
                if factor is None:
                    factor = 1.0
                for col_cad, label, theme_key in cfg["vmps"]:
                    if col_cad in df_cad.columns:
                        v = _parse_vmp(cad_idx.loc[p, col_cad])
                        if v is None or v <= 0:
                            # ignora VMP ausente, '-' ou zero (ex.: Arsenio irrigacao = 0)
                            continue
                        v_conv = v * factor
                        vmps_ativos.append((label, v_conv, str(theme.get(theme_key, "#e74c3c"))))

            # Caso especial: Nitrogenio Amoniacal (Sup) -> VMPs dependem do pH (CONAMA 357 art.34)
            if matriz == "Água Superficial" and p.lower().startswith("nitrogênio amon"):
                vmps_ativos = [
                    ("VMP pH ≤ 7,5 (3,7 mg/L)", 3.7, str(theme.get("mf_vmp_consumo_humano", "#e74c3c"))),
                    ("VMP 7,5 < pH ≤ 8,0 (2,0 mg/L)", 2.0, str(theme.get("mf_vmp_dessedentacao", "#8B4513"))),
                    ("VMP 8,0 < pH ≤ 8,5 (1,0 mg/L)", 1.0, str(theme.get("mf_vmp_irrigacao", "#006400"))),
                    ("VMP pH > 8,5 (0,5 mg/L)", 0.5, str(theme.get("mf_vmp_recreacao", "#2980b9"))),
                ]

            use_log = any(h in p.lower() for h in LOG_HINTS)

            out = gerar_grafico(df_p, p, unidade, vmps_ativos, cfg["subpasta"], theme, use_log)
            if out:
                total += 1

        print(f"  -> {len(params)} processados")

    print(f"\n[B3] OK — {total} PNGs gerados")


if __name__ == "__main__":
    main()
