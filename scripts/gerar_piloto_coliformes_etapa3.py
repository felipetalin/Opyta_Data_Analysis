"""
Etapa 3 — Piloto Gold Fauna: Coliformes Termotolerantes nas 3 matrizes.

Aplica o contrato visual aprovado (registrado em
`/memories/repo/meio_fisico_modelo_definitivo_coliformes.md`):
- Pontos por campanha, sem linhas de conexao.
- Paleta verde fauna por campanha (#11420C derivada).
- Legenda no topo, fora da area do plot.
- Linha horizontal de VMP + faixa sombreada acima do limite.
- Linha tracejada de Limite de Quantificacao.
- Grade horizontal + vertical com mesmo estilo.
- Spines pretas, dpi 600, sem titulo no corpo.

Regras de VMP por matriz (definicao do usuario):
- Agua Superficial:  apenas Classe 2 (1 linha vermelha).
- Agua Subterranea:  4 linhas — Consumo Humano, Dessedentacao Animal,
                     Irrigacao, Recreacao (cores do tema).
- Sedimento:         2 linhas — N1 e N2.

Saidas:
  Resultados/Meio_físico/<Superficial|Subterrânea|Sedimentos>/
    02_PILOTO_Coliformes_Gold_Fauna.png

Uso:
    python scripts/gerar_piloto_coliformes_etapa3.py
"""

from __future__ import annotations

import colorsys
import json
import re
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # evita problemas de backend em Windows
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_FILE = REPO_ROOT / "configs" / "theme_gold_approved.json"

CLIENT_ROOT = Path(
    r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"
)
SRC_RESULTADOS = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
SRC_CADASTRO = CLIENT_ROOT / "Migração" / "Físico" / "cadastro_parametros_opyta.xlsx"
OUT_ROOT = CLIENT_ROOT / "Resultados" / "Meio_físico"

PARAM_ALVO = "Coliformes Termotolerantes por tubos múltiplos - NMP"
PARAM_UNIDADE = "NMP/100 mL"
FAUNA_CAMPAIGN_BASE_HEX = "#11420C"


# ----------------------------------------------------------------------------
# Configuracao por matriz
# ----------------------------------------------------------------------------
MATRIZ_CFG = {
    "Água Superficial": {
        "subpasta": "Superficial",
        "aba_cad": "Aguas_Superficiais",
        "vmps": [
            ("VMP_357_Cl2_Max", "VMP CONAMA 357 — Classe 2", "mf_vmp_default"),
        ],
    },
    "Água Subterrânea": {
        "subpasta": "Subterrânea",
        "aba_cad": "Aguas_Subterraneas",
        "vmps": [
            ("VMP_396_Consumo_Humano", "VMP CONAMA 396 — Consumo Humano", "mf_vmp_consumo_humano"),
            ("VMP_396_Dessedentacao_Animal", "VMP CONAMA 396 — Dessedentação Animal", "mf_vmp_dessedentacao"),
            ("VMP_396_Irrigacao", "VMP CONAMA 396 — Irrigação", "mf_vmp_irrigacao"),
            ("VMP_396_Recreacao", "VMP CONAMA 396 — Recreação", "mf_vmp_recreacao"),
        ],
    },
    "Sedimento": {
        "subpasta": "Sedimentos",
        "aba_cad": "Sedimento",
        "vmps": [
            ("VMP_454_N1", "VMP CONAMA 454 — Nível 1", "mf_vmp_n1"),
            ("VMP_454_N2", "VMP CONAMA 454 — Nível 2", "mf_vmp_n2"),
        ],
    },
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _norm(s: str) -> str:
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_valor(val) -> tuple[float | None, str]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None, ""
    s = str(val).strip()
    sinal = ""
    if s.startswith("<="):
        sinal = "<="; s = s[2:].strip()
    elif s.startswith(">="):
        sinal = ">="; s = s[2:].strip()
    elif s.startswith("<"):
        sinal = "<"; s = s[1:].strip()
    elif s.startswith(">"):
        sinal = ">"; s = s[1:].strip()
    s = s.replace(",", ".").replace(" ", "")
    if not s:
        return None, sinal
    try:
        return float(s), sinal
    except ValueError:
        return None, sinal


def _parse_vmp(val) -> float | None:
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


def _campanha_sort_key(c):
    s = str(c)
    m = re.search(r"(\d+)", s)
    return (0, int(m.group(1)), s) if m else (1, 9999, s)


def _hex_to_rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


def _green_palette(base_hex: str, n: int):
    rgb = _hex_to_rgb(base_hex)
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    out = []
    for i in range(max(n, 1)):
        t = i / max(n - 1, 1)
        new_v = 0.5 + 0.5 * t
        new_s = 0.8 + 0.2 * t
        out.append(_rgb_to_hex(colorsys.hsv_to_rgb(h, new_s, new_v)))
    return out


# ----------------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------------
def gerar_piloto(df_res: pd.DataFrame, matriz: str, cfg: dict, theme: dict) -> Path | None:
    d = df_res[df_res["Matriz"].astype(str).str.strip() == matriz].copy()
    d["_pnorm"] = d["Parametro"].map(_norm)
    d = d[d["_pnorm"] == _norm(PARAM_ALVO)].copy()
    if d.empty:
        print(f"  ! sem dados de Coliformes para {matriz}")
        return None

    parsed = d["Resultado"].map(_parse_valor)
    d["_valor"] = parsed.map(lambda t: t[0])
    d["_sinal"] = parsed.map(lambda t: t[1])
    d = d.dropna(subset=["_valor"]).copy()
    if d.empty:
        print(f"  ! todos resultados nulos em {matriz}")
        return None

    d["Campanha"] = d["Campanha"].astype(str).str.strip()
    d["Ponto"] = d["Ponto"].astype(str).str.strip()

    campaigns = sorted(d["Campanha"].unique().tolist(), key=_campanha_sort_key)
    points = sorted(d["Ponto"].unique().tolist())

    pivot = (
        d.groupby(["Ponto", "Campanha"])["_valor"]
        .mean()
        .reset_index()
        .pivot_table(index="Ponto", columns="Campanha", values="_valor", aggfunc="mean")
        .reindex(index=points, columns=campaigns)
    )

    # VMPs aplicaveis (do cadastro)
    df_cad = pd.read_excel(SRC_CADASTRO, sheet_name=cfg["aba_cad"])
    cad_idx = df_cad.set_index("Parametro")
    param_cad = d["Parametro"].mode().iloc[0]
    vmps_ativos: list[tuple[str, float, str]] = []  # (label, value, color_hex)
    for col_cad, label, theme_key in cfg["vmps"]:
        if col_cad not in df_cad.columns or param_cad not in cad_idx.index:
            continue
        v = _parse_vmp(cad_idx.loc[param_cad, col_cad])
        if v is not None:
            color = str(theme.get(theme_key, "#e74c3c"))
            vmps_ativos.append((f"{label} ({v:g})", v, color))

    # Paleta verde por campanha
    palette = _green_palette(FAUNA_CAMPAIGN_BASE_HEX, len(campaigns))
    color_map = {c: palette[i] for i, c in enumerate(campaigns)}

    fig, ax = plt.subplots(
        figsize=tuple(theme.get("figsize_standard", [15, 10])),
        dpi=int(theme.get("dpi", 600)),
    )

    x = np.arange(len(points), dtype=float)
    n_camps = max(len(campaigns), 1)
    offsets = np.linspace(-0.15, 0.15, n_camps) if n_camps > 1 else np.array([0.0])

    for i, camp in enumerate(campaigns):
        vals = pivot[camp].values.astype(float)
        valid = ~np.isnan(vals)
        if not np.any(valid):
            continue
        ax.scatter(
            x[valid] + offsets[i],
            vals[valid],
            s=70, marker="o", label=camp,
            color=color_map[camp], edgecolors="black", linewidths=0.4, zorder=4,
        )

    # Linhas de VMP + faixa de violacao acima do MENOR limite
    if vmps_ativos:
        y_max_dados = float(np.nanmax(pivot.values))
        min_vmp = min(v for _l, v, _c in vmps_ativos)
        topo = max(y_max_dados, max(v for _l, v, _c in vmps_ativos)) * 1.10
        ax.axhspan(
            min_vmp, topo,
            color=str(theme.get("mf_vmp_shade", "#e74c3c")),
            alpha=float(theme.get("mf_vmp_shade_alpha", 0.06)),
            zorder=1,
        )
        for label, v, color in vmps_ativos:
            ax.axhline(v, color=color, linewidth=2.0, label=label, zorder=2)

    # LOQ (maior valor abaixo do LOQ reportado com '<')
    loq_vals = d.loc[d["_sinal"] == "<", "_valor"].dropna().astype(float)
    if not loq_vals.empty:
        loq = float(np.nanmax(loq_vals.values))
        ax.axhline(
            loq, color="#7f7f7f", linewidth=1.6, linestyle="--",
            label=f"Limite de Quantificação ({loq:g})", zorder=2,
        )

    # Eixos
    ax.set_xticks(x)
    ax.set_xticklabels(
        points, rotation=45, ha="right",
        fontsize=int(theme.get("campaign_label_size", 14)),
    )
    ax.set_xlabel("Ponto", fontsize=int(theme.get("font_size_base", 14)))
    ax.set_ylabel(
        f"Coliformes Termotolerantes ({PARAM_UNIDADE})",
        fontsize=int(theme.get("font_size_base", 14)),
    )
    ax.set_title("")

    # Grade horizontal + vertical mesmo estilo
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

    # Legenda no topo, fora do plot
    handles, labels = ax.get_legend_handles_labels()
    ncol = min(max(2, len(handles)), 4)
    legend = fig.legend(
        handles, labels,
        loc="upper center", bbox_to_anchor=(0.5, 0.99),
        ncol=ncol, frameon=False,
    )
    for t in legend.get_texts():
        t.set_fontsize(int(theme.get("legend_size", 13)))

    fig.tight_layout(rect=[0, 0, 1, 0.90])

    out_dir = OUT_ROOT / cfg["subpasta"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "02_PILOTO_Coliformes_Gold_Fauna.png"
    try:
        fig.savefig(out_path, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    except PermissionError:
        alt = out_path.with_name(out_path.stem + "_NEW" + out_path.suffix)
        fig.savefig(alt, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        print(f"  ! arquivo bloqueado; salvo em {alt.name}")
        out_path = alt
    plt.close(fig)
    return out_path


def main() -> None:
    with open(THEME_FILE, encoding="utf-8") as f:
        theme = json.load(f)

    print(f"[etapa-3] Lendo {SRC_RESULTADOS.name} ...")
    df_res = pd.read_excel(SRC_RESULTADOS, sheet_name="Resultados_Meio_Fisico", dtype=str)
    print(f"  -> {len(df_res)} linhas\n")

    for matriz, cfg in MATRIZ_CFG.items():
        print(f"[etapa-3] Piloto Coliformes — {matriz} ...")
        out = gerar_piloto(df_res, matriz, cfg, theme)
        if out:
            print(f"  -> {out}\n")

    print("[etapa-3] OK")


if __name__ == "__main__":
    main()
