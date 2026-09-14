"""Gera figuras de série temporal para Água Superficial – BRAANG01.

Pontos : MCB1010, MCB1011
Matriz : Água Superficial
Estilo : padrão R01 (layout gold aprovado)
  - 2 subplots empilhados por figura (um por ponto)
  - Título: {param} (Água Superficial)
  - Subtítulo: Ponto MCB10XX (esquerda, bold)
  - Eixo Y : ScalarFormatter useMathText=True (×10ⁿ)
  - Todos os labels mensais no eixo X (tick_interval=1)
  - dpi=600
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CODE = "BRAANG01"
MATRIX = "\u00c1gua Superficial"
POINTS = ["MCB1010", "MCB1011"]

DEFAULT_OUT_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados/_revisoes/"
    "R04_agua_superficial_20260709"
)

PARAMS = [
    "Ars\u00eanio Dissolvido",
    "Ars\u00eanio Total",
    "Cianeto Livre",
    "Cianeto Total",
    "Cianeto WAD",
    "Cobalto Total",
    "Cobre Total",
    "Condutividade El\u00e9trica",
    "Cor Verdadeira",
    "Cromo Total",
    "Demanda Bioqu\u00edmica de Oxig\u00eanio",
    "Demanda Qu\u00edmica de Oxig\u00eanio",
    "Fen\u00f3is Totais",
    "Ferro Dissolvido",
    "Ferro Total",
    "\u00cdtrio (Metais Totais)",
    "Mangan\u00eas Dissolvido",
    "Mangan\u00eas Total",
    "Merc\u00fario Total",
    "N\u00edquel Total",
    "Nitrato",
    "\u00d3leos e Graxas",
    "Oxig\u00eanio Dissolvido (OD)",
    "pH",
    "Sel\u00eanio Total",
    "S\u00f3lidos Dissolvidos Totais",
    "S\u00f3lidos Sediment\u00e1veis",
    "S\u00f3lidos Totais Suspensos",
    "Sulfato",
    "Surfactantes (LAS)",
    "Temperatura da \u00c1gua",
    "Temperatura do Ar",
    "Turbidez",
    "Zinco Total",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(" ", "_")


def format_limit(value: float) -> str:
    if pd.isna(value):
        return ""
    value = float(value)
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def first_notna(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    values = df[column].dropna()
    return float(values.iloc[0]) if not values.empty else None


# ---------------------------------------------------------------------------
# Carregamento de dados
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    load_dotenv(REPO_ROOT / ".env")
    db_url = os.environ.get("FISICO_DB_URL")
    if not db_url:
        raise RuntimeError("FISICO_DB_URL nao encontrado no .env")

    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '15min'"))
        df = pd.read_sql(
            text("""
                SELECT *
                FROM public.fisico_analise_consolidada
                WHERE codigo_interno_opyta = :code
                  AND matriz = :matrix
                  AND nome_ponto = ANY(:points)
            """),
            conn,
            params={"code": PROJECT_CODE, "matrix": MATRIX, "points": POINTS},
        )

    numeric_cols = [
        "valor_medido", "vmp_357_cl2_min", "vmp_357_cl2_max",
        "vmp_430_padrao", "vmp_amonia_dinamico",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["data_hora_coleta"] = pd.to_datetime(df["data_hora_coleta"], errors="coerce")
    df["ano_mes"] = df["data_hora_coleta"].dt.strftime("%Y-%m")
    return df.sort_values(["nome_parametro", "nome_ponto", "data_hora_coleta"])


# ---------------------------------------------------------------------------
# Limites VMP
# ---------------------------------------------------------------------------
def get_vmp_limits(point_data: pd.DataFrame) -> list[dict[str, float | str]]:
    limits: list[dict[str, float | str]] = []
    lower = first_notna(point_data, "vmp_357_cl2_min")
    upper = first_notna(point_data, "vmp_357_cl2_max")
    dynamic = first_notna(point_data, "vmp_amonia_dinamico")

    if upper is not None:
        limits.append({
            "tipo": "maximo",
            "valor": upper,
            "rotulo": f"VMP - m\u00e1ximo: {format_limit(upper)}",
        })
    if lower is not None:
        limits.append({
            "tipo": "minimo",
            "valor": lower,
            "rotulo": f"VMP - m\u00ednimo: {format_limit(lower)}",
        })
    if dynamic is not None and all(dynamic != item["valor"] for item in limits):
        limits.append({
            "tipo": "amonia_dinamico",
            "valor": dynamic,
            "rotulo": f"VMP - am\u00f4nia: {format_limit(dynamic)}",
        })
    return limits


def add_limits(ax, point_data: pd.DataFrame, param: str) -> list[dict[str, float | str]]:
    visible = get_vmp_limits(point_data)
    for item in visible:
        ax.axhline(
            float(item["valor"]),
            color="red",
            linestyle="--",
            linewidth=3.5,
            label=str(item["rotulo"]),
            zorder=2,
        )
    return visible


# ---------------------------------------------------------------------------
# Configuração do eixo (padrão R01)
# ---------------------------------------------------------------------------
def configure_axis(ax, unit: str, point: str) -> None:
    ax.set_title(f"Ponto {point}", fontsize=28, fontweight="bold",
                 loc="left", family="Arial", pad=20)
    ax.set_ylabel(unit, fontsize=22, fontweight="bold", family="Arial")
    ax.set_xlabel("Campanhas", fontsize=20, family="Arial")
    ax.yaxis.grid(True, linestyle="-", alpha=0.40, color="#CCCCCC")
    ax.tick_params(axis="y", labelsize=16)
    ax.tick_params(axis="x", rotation=90, labelsize=16)

    formatter = mticker.ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((-3, 4))
    ax.yaxis.set_major_formatter(formatter)
    offset_text = ax.yaxis.get_offset_text()
    offset_text.set_fontsize(16)
    offset_text.set_family("Arial")


# ---------------------------------------------------------------------------
# Plotagem de cada parâmetro
# ---------------------------------------------------------------------------
def plot_param(df: pd.DataFrame, param: str, out_dir: Path) -> dict:
    d = df[df["nome_parametro"] == param].copy()
    d = d.dropna(subset=["valor_medido"])
    if d.empty:
        return {"param": param, "status": "empty"}

    # Ordem cronológica das campanhas
    unique = (
        d[["nome_campanha", "ano_mes", "data_hora_coleta"]]
        .drop_duplicates("ano_mes")
        .sort_values("data_hora_coleta")
    )
    campaigns_ordered = unique["nome_campanha"].tolist()
    x_order = {c: i for i, c in enumerate(campaigns_ordered)}
    d["_x"] = d["nome_campanha"].map(x_order)
    x_ticks = list(range(len(campaigns_ordered)))

    unit_values = d["unidade_medida"].dropna()
    unit = str(unit_values.iloc[0]) if not unit_values.empty else "-"

    fig, axes = plt.subplots(2, 1, figsize=(19.25, 11.0), squeeze=False)
    axes_flat = [ax for row in axes for ax in row]
    points_result = []

    for ax, point in zip(axes_flat, POINTS):
        point_data = d[d["nome_ponto"] == point].copy().sort_values("_x")
        point_data = point_data.dropna(subset=["valor_medido"])

        ax.plot(
            point_data["_x"],
            point_data["valor_medido"],
            marker="o",
            markersize=12,
            color="#2E7D32",
            linewidth=4,
            zorder=4,
        )
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(campaigns_ordered)
        configure_axis(ax, unit, point)

        visible_limits = add_limits(ax, point_data, param)
        limit_values = [float(item["valor"]) for item in visible_limits]

        if visible_limits:
            data_max = point_data["valor_medido"].max()
            if pd.isna(data_max):
                data_max = max(limit_values)
            lower = first_notna(point_data, "vmp_357_cl2_min")
            upper = first_notna(point_data, "vmp_357_cl2_max")
            dynamic = first_notna(point_data, "vmp_amonia_dinamico")
            upper_limits = [v for v in [upper, dynamic] if v is not None]
            if lower is not None:
                ax.axhspan(-1e6, lower, color="red", alpha=0.08, zorder=0)
            if upper_limits:
                ax.axhspan(min(upper_limits), 1e6, color="red", alpha=0.07, zorder=0)
            top = max(float(data_max), max(limit_values)) * 1.22
        else:
            data_max = point_data["valor_medido"].max()
            top = float(data_max) * 1.22 if pd.notna(data_max) and data_max > 0 else 1.0

        if not math.isfinite(top) or top <= 0:
            top = 1.0
        ax.set_ylim(-0.02 * top, top)

        if visible_limits:
            ax.legend(loc="upper right", frameon=True, fontsize=16,
                      facecolor="white", framealpha=1)
        points_result.append({
            "point": point,
            "rows": int(len(point_data)),
            "vmp_visible": visible_limits,
        })

    fig.subplots_adjust(top=0.80, hspace=0.95)
    title = fill(f"{param} (\u00c1gua Superficial)", width=58)
    fig.suptitle(title, fontsize=36, fontweight="bold", family="Arial", y=0.985)

    filename = f"ST_{safe_filename(param)}_P1.png"
    output = out_dir / filename
    fig.savefig(output, dpi=600, bbox_inches="tight")
    plt.close(fig)

    return {
        "param": param,
        "file": output.name,
        "campaign_count": len(campaigns_ordered),
        "points": points_result,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def clear_output(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in out_dir.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json"}:
            item.unlink()


def main() -> None:
    out_root = Path(os.environ.get("BRAANG01_SUPERF_OUT_ROOT", str(DEFAULT_OUT_ROOT)))
    out_dir = out_root / "revisado" / "\u00c1gua_Superficial"
    clear_output(out_dir)

    df = load_data()
    results = []
    for i, param in enumerate(PARAMS, 1):
        print(f"[{i:02d}/{len(PARAMS)}] {param} ...", end=" ", flush=True)
        result = plot_param(df, param, out_dir)
        results.append(result)
        print(result.get("file", result.get("status", "?")))

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "points": POINTS,
        "params": PARAMS,
        "output_dir": str(out_dir),
        "png_count": len(list(out_dir.glob("*.png"))),
        "results": results,
    }
    with (out_dir / "generation_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"\nConcluido: {metadata['png_count']} figuras em {out_dir}")


if __name__ == "__main__":
    main()
