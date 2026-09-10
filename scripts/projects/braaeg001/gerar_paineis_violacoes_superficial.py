from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CLIENT_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
PROJECT_DIR = next(path for path in CLIENT_ROOT.iterdir() if path.name.startswith("A&G"))
CONSOLIDATED = (
    PROJECT_DIR
    / "resultados"
    / "Meio_fisico"
    / "migracao"
    / "consolidacao_pos_c02"
    / "20260729T183622Z_consolidado_meio_fisico_braaeg001_pos_c02.xlsx"
)
OUTPUT_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "resultados" / "superficial"

CAMPAIGN_LABELS = {
    "C001-2026-02-CH": "Campanha-01-Chuva",
    "C002-2026-06-SC": "Campanha-02-Seca",
}
GREEN = "#1B7F22"
LIGHT_GREEN = "#19FF19"
RED = "#F04438"
GRID = "#D7DDE0"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def fold(value: Any) -> str:
    text = clean_text(value).replace("ę", "e").replace("Ę", "E")
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm(value: Any) -> str:
    text = fold(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fix_ptbr_label(value: Any) -> str:
    out = clean_text(value)
    if "Ã" in out or "Â" in out:
        try:
            out = out.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    replacements = {
        "Arsęnio": "Arsênio",
        "Manganęs": "Manganês",
        "Nitrogęnio": "Nitrogênio",
        "Oxigęnio": "Oxigênio",
        "Bioquimica": "Bioquímica",
        "Quimica": "Química",
        "Solidos": "Sólidos",
    }
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    out = out.replace(chr(281), chr(234))
    return out


def effective_limits(parameter: str, vmin: Any, vmax: Any, vdyn: Any) -> tuple[Any, Any, Any]:
    p_norm = norm(parameter)
    if "manganes dissolvido" in p_norm:
        return None, None, None
    if p_norm == "amonia":
        return None, None, None
    return vmin, vmax, vdyn


def violates(parameter: str, value: Any, sign: Any, vmin: Any, vmax: Any, vdyn: Any) -> bool:
    if value is None or pd.isna(value) or clean_text(sign) in {"<", "<="}:
        return False
    vmin, vmax, vdyn = effective_limits(parameter, vmin, vmax, vdyn)
    if vmin is None and vmax is None and vdyn is None:
        return False
    value = float(value)
    if vmin is not None and pd.notna(vmin) and value < float(vmin):
        return True
    upper_candidates = [v for v in [vmax, vdyn] if v is not None and pd.notna(v)]
    if upper_candidates and value > min(map(float, upper_candidates)):
        return True
    return False


def load_surface() -> pd.DataFrame:
    df = pd.read_excel(CONSOLIDATED, sheet_name="fisico_analise_consolidada")
    surface = df[df["matriz"].astype(str).str.contains("Superficial", na=False)].copy()
    for col in ["valor_medido", "vmp_357_cl2_min", "vmp_357_cl2_max", "vmp_amonia_dinamico"]:
        surface[col] = pd.to_numeric(surface[col], errors="coerce")
    surface["parametro_display"] = surface["nome_parametro"].map(fix_ptbr_label)
    surface["campanha_display"] = surface["nome_campanha"].map(lambda x: CAMPAIGN_LABELS.get(clean_text(x), clean_text(x)))
    surface["violacao"] = False
    for _, group in surface.groupby("nome_parametro"):
        parameter = clean_text(group["parametro_display"].iloc[0])
        vmin = group["vmp_357_cl2_min"].dropna().iloc[0] if not group["vmp_357_cl2_min"].dropna().empty else None
        vmax = group["vmp_357_cl2_max"].dropna().iloc[0] if not group["vmp_357_cl2_max"].dropna().empty else None
        vdyn = group["vmp_amonia_dinamico"].dropna().iloc[0] if not group["vmp_amonia_dinamico"].dropna().empty else None
        surface.loc[group.index, "violacao"] = [
            violates(parameter, row.valor_medido, row.sinal_limite, vmin, vmax, vdyn)
            for row in group.itertuples(index=False)
        ]
    return surface


def build_summary(surface: pd.DataFrame) -> pd.DataFrame:
    numeric = surface[surface["valor_medido"].notna()].copy()
    summary = (
        numeric.groupby(["campanha_display", "parametro_display"], dropna=False)
        .agg(
            registros=("valor_medido", "size"),
            violacoes=("violacao", "sum"),
        )
        .reset_index()
    )
    summary["percentual_violacao"] = np.where(
        summary["registros"] > 0,
        summary["violacoes"] / summary["registros"] * 100,
        0,
    )
    return summary[summary["violacoes"] > 0].copy()


def plot_campaign(summary: pd.DataFrame, campaign: str) -> dict[str, Any]:
    data = summary[summary["campanha_display"].eq(campaign)].copy()
    out_png = OUTPUT_DIR / f"04_painel_violacoes_{safe_filename(campaign)}.png"
    if data.empty:
        fig, ax = plt.subplots(figsize=(14, 7), dpi=600)
        ax.text(0.5, 0.5, "Sem violações registradas", ha="center", va="center", fontsize=18)
        ax.axis("off")
        fig.savefig(out_png, facecolor="white")
        plt.close(fig)
        return {"campanha": campaign, "png": str(out_png), "parametros": 0, "violacoes": 0}

    data = data.sort_values(["percentual_violacao", "violacoes", "parametro_display"], ascending=[True, True, True])
    colors = [
        RED if pct >= 50 else LIGHT_GREEN if pct < 10 else GREEN
        for pct in data["percentual_violacao"]
    ]
    fig, ax = plt.subplots(figsize=(14, max(7, 0.48 * len(data))), dpi=600)
    y = np.arange(len(data))
    ax.barh(y, data["percentual_violacao"], color=colors, edgecolor="#0B4F12", linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(data["parametro_display"], fontsize=12)
    ax.set_xlabel("Percentual de amostras com violação (%)", fontsize=15)
    ax.set_xlim(0, max(100, float(data["percentual_violacao"].max()) * 1.15))
    ax.grid(True, axis="x", alpha=0.35, linestyle="--", color=GRID)
    ax.tick_params(axis="x", labelsize=12)
    for i, row in enumerate(data.itertuples(index=False)):
        ax.text(
            row.percentual_violacao + 1,
            i,
            f"{row.percentual_violacao:.0f}% ({int(row.violacoes)}/{int(row.registros)})",
            va="center",
            fontsize=11,
            color="#222222",
        )
    fig.tight_layout()
    fig.savefig(out_png, facecolor="white")
    plt.close(fig)
    return {
        "campanha": campaign,
        "png": str(out_png),
        "parametros": int(len(data)),
        "violacoes": int(data["violacoes"].sum()),
    }


def plot_combined(summary: pd.DataFrame) -> dict[str, Any]:
    campaigns = list(CAMPAIGN_LABELS.values())
    params = (
        summary.groupby("parametro_display", as_index=False)["violacoes"].sum()
        .sort_values(["violacoes", "parametro_display"], ascending=[True, True])
        ["parametro_display"]
        .tolist()
    )
    out_png = OUTPUT_DIR / "04_painel_violacoes_chuva_seca.png"
    if not params:
        fig, ax = plt.subplots(figsize=(14, 7), dpi=600)
        ax.text(0.5, 0.5, "Sem violações registradas", ha="center", va="center", fontsize=18)
        ax.axis("off")
        fig.savefig(out_png, facecolor="white")
        plt.close(fig)
        return {"png": str(out_png), "parametros": 0, "violacoes": 0}

    fig, axes = plt.subplots(1, len(campaigns), figsize=(14, max(7, 0.48 * len(params))), dpi=600, sharey=True)
    if len(campaigns) == 1:
        axes = [axes]
    y = np.arange(len(params))
    max_pct = max(float(summary["percentual_violacao"].max()), 1.0)
    x_max = max(100, max_pct * 1.15)

    for ax, campaign in zip(axes, campaigns):
        data = summary[summary["campanha_display"].eq(campaign)].set_index("parametro_display")
        pcts = [float(data.loc[param, "percentual_violacao"]) if param in data.index else 0.0 for param in params]
        viols = [int(data.loc[param, "violacoes"]) if param in data.index else 0 for param in params]
        regs = [int(data.loc[param, "registros"]) if param in data.index else 12 for param in params]
        colors = [GREEN if value > 0 else "#E8F5E9" for value in pcts]
        ax.barh(y, pcts, color=colors, edgecolor="#0B4F12", linewidth=0.35)
        ax.set_title(campaign, fontsize=16, fontweight="bold", pad=12)
        ax.set_xlim(0, x_max)
        ax.grid(True, axis="x", alpha=0.35, linestyle="--", color=GRID)
        ax.tick_params(axis="x", labelsize=11)
        ax.set_xlabel("Violação (%)", fontsize=13)
        for i, (pct, viol, reg) in enumerate(zip(pcts, viols, regs)):
            if viol:
                ax.text(pct + 1, i, f"{pct:.0f}% ({viol}/{reg})", va="center", fontsize=10, color="#222222")

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(params, fontsize=11)
    fig.subplots_adjust(left=0.29, right=0.985, top=0.92, bottom=0.12, wspace=0.08)
    fig.savefig(out_png, facecolor="white")
    plt.close(fig)
    return {"png": str(out_png), "parametros": int(len(params)), "violacoes": int(summary["violacoes"].sum())}


def safe_filename(value: str) -> str:
    text = fold(value)
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "_", text).strip("_")


def main() -> int:
    surface = load_surface()
    summary = build_summary(surface)
    out_xlsx = OUTPUT_DIR / "04_Painel_Violacoes_por_Campanha.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="dados_painel", index=False)
    results = []
    combined = plot_combined(summary)
    print({"xlsx": str(out_xlsx), "resultados": results, "painel_unico": combined})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
