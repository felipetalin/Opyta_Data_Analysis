"""Gera figuras de série temporal para o ponto MCB1005 (Efluente – BRAANG01).

Estilo idêntico ao revisar_braang01_efluente_mcb907_periodicidade.py:
  - Título da figura : {param} (Efluente)
  - Subtítulo do eixo: Ponto MCB1005
  - Cores e fontes   : mesmo padrão gold (Arial, verde #2E7D32)
  - Eixo Y           : ScalarFormatter com useMathText=True (×10ⁿ)
  - Eixo X           : todas as campanhas mensais, label a cada 3
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
MATRIX = "Efluente"
POINT = "MCB1005"

DEFAULT_OUT_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados/_revisoes/"
    "R03_efluente_mcb1005_20260709"
)

MONTHS_PT = {
    "01": "jan", "02": "fev", "03": "mar", "04": "abr",
    "05": "mai", "06": "jun", "07": "jul", "08": "ago",
    "09": "set", "10": "out", "11": "nov", "12": "dez",
}

PARAMS = [
    "Ars\u00eanio Dissolvido",
    "Ars\u00eanio Total",
    "Cobalto Total",
    "Cobre Total",
    "Condutividade El\u00e9trica",
    "Cor Verdadeira",
    "Cromo Total",
    "Demanda Bioqu\u00edmica de Oxig\u00eanio",
    "Ferro Dissolvido",
    "Ferro Total",
    "Mangan\u00eas Dissolvido",
    "Mangan\u00eas Total",
    "Nitrato",
    "\u00d3leos e Graxas",
    "Oxig\u00eanio Dissolvido (OD)",
    "pH",
    "S\u00f3lidos Dissolvidos Totais",
    "S\u00f3lidos Sediment\u00e1veis",
    "S\u00f3lidos Totais Suspensos",
    "Sulfato",
    "Turbidez",
    "Zinco Total",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_filename(name: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(" ", "_")
    return safe


def format_campaign(ano_mes: str) -> str:
    """Converte '2021-01' em 'jan-2021'."""
    year, month = ano_mes.split("-")
    return f"{MONTHS_PT[month]}-{year}"


def format_limit(value: float) -> str:
    if pd.isna(value):
        return ""
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def first_notna(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    values = df[column].dropna()
    if values.empty:
        return None
    return float(values.iloc[0])


# ---------------------------------------------------------------------------
# Carregamento de dados
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    load_dotenv(REPO_ROOT / ".env")
    db_url = os.environ.get("FISICO_DB_URL")
    if not db_url:
        raise RuntimeError("FISICO_DB_URL nao encontrado no .env")

    query = text(
        """
        SELECT *
        FROM public.fisico_analise_consolidada
        WHERE codigo_interno_opyta = :code
          AND matriz = :matrix
          AND nome_ponto = :point
        """
    )
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '15min'"))
        df = pd.read_sql(
            query,
            conn,
            params={"code": PROJECT_CODE, "matrix": MATRIX, "point": POINT},
        )

    numeric_cols = [
        "valor_medido",
        "vmp_357_cl2_min",
        "vmp_357_cl2_max",
        "vmp_430_padrao",
        "vmp_amonia_dinamico",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["data_hora_coleta"] = pd.to_datetime(df["data_hora_coleta"], errors="coerce")
    df["ano_mes"] = df["data_hora_coleta"].dt.strftime("%Y-%m")
    return df.sort_values(["nome_parametro", "data_hora_coleta"])


# ---------------------------------------------------------------------------
# Limites VMP
# ---------------------------------------------------------------------------
def add_limits(ax, point_data: pd.DataFrame, param: str) -> list[float]:
    visible: list[float] = []
    if param == "pH":
        lower = first_notna(point_data, "vmp_357_cl2_min")
        upper = first_notna(point_data, "vmp_430_padrao")
        if upper is not None:
            ax.axhline(upper, color="red", linestyle="--", linewidth=3,
                       label=f"VMP - m\u00e1ximo: {format_limit(upper)}", zorder=2)
            visible.append(upper)
        if lower is not None:
            ax.axhline(lower, color="red", linestyle="--", linewidth=3,
                       label=f"VMP - m\u00ednimo: {format_limit(lower)}", zorder=2)
            visible.append(lower)
        return visible

    dynamic = first_notna(point_data, "vmp_amonia_dinamico")
    default = first_notna(point_data, "vmp_430_padrao")
    limit = dynamic if dynamic is not None else default
    if limit is not None:
        ax.axhline(limit, color="red", linestyle="--", linewidth=3.5,
                   label=f"VMP - m\u00e1ximo: {format_limit(limit)}", zorder=2)
        visible.append(limit)
    return visible


# ---------------------------------------------------------------------------
# Configuração do eixo
# ---------------------------------------------------------------------------
def configure_axis(ax, unit: str, tick_interval: int) -> None:
    ax.set_title(f"Ponto {POINT}", fontsize=28, fontweight="bold",
                 loc="left", family="Arial", pad=20)
    ax.set_ylabel(unit, fontsize=22, fontweight="bold", family="Arial")
    ax.set_xlabel("Campanhas", fontsize=20, family="Arial")
    ax.yaxis.grid(True, linestyle="-", alpha=0.40, color="#CCCCCC")
    ax.tick_params(axis="y", labelsize=16)
    ax.tick_params(axis="x", rotation=90, labelsize=16)

    # Notação matemática no multiplicador do eixo Y (×10ⁿ em vez de 1en)
    formatter = mticker.ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((-3, 4))
    ax.yaxis.set_major_formatter(formatter)
    offset_text = ax.yaxis.get_offset_text()
    offset_text.set_fontsize(13)
    offset_text.set_family("Arial")

    if tick_interval > 1:
        ticks = ax.get_xticks()
        labels = [item.get_text() for item in ax.get_xticklabels()]
        keep = set(range(0, len(labels), tick_interval))
        if labels:
            keep.add(len(labels) - 1)
        ax.set_xticks([ticks[i] for i in sorted(keep) if i < len(ticks)])
        ax.set_xticklabels([labels[i] for i in sorted(keep) if i < len(labels)])


# ---------------------------------------------------------------------------
# Plotagem de cada parâmetro
# ---------------------------------------------------------------------------
def plot_param(df: pd.DataFrame, param: str, out_dir: Path) -> dict:
    d = df[df["nome_parametro"] == param].copy().sort_values("data_hora_coleta")
    d = d.dropna(subset=["valor_medido"])
    if d.empty:
        return {"param": param, "status": "empty"}

    # Ordenação por campanha
    unique = (
        d[["ano_mes", "data_hora_coleta"]]
        .drop_duplicates("ano_mes")
        .sort_values("data_hora_coleta")
    )
    months_ordered = unique["ano_mes"].tolist()
    x_order = {m: i for i, m in enumerate(months_ordered)}
    d["_x"] = d["ano_mes"].map(x_order)
    x_ticks = list(range(len(months_ordered)))
    x_labels = [format_campaign(m) for m in months_ordered]
    tick_interval = 1  # mostrar todos os labels (padrão R01)

    unit_values = d["unidade_medida"].dropna()
    unit = str(unit_values.iloc[0]) if not unit_values.empty else "-"

    fig, ax = plt.subplots(1, 1, figsize=(19.25, 5.5))

    ax.plot(
        d["_x"],
        d["valor_medido"],
        marker="o",
        markersize=12,
        color="#2E7D32",
        linewidth=4,
        zorder=4,
    )
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels)
    configure_axis(ax, unit, tick_interval=tick_interval)

    visible_limits = add_limits(ax, d, param)

    if visible_limits:
        data_max = d["valor_medido"].max()
        if pd.isna(data_max):
            data_max = max(visible_limits)
        if param == "pH" and len(visible_limits) >= 2:
            lower = min(visible_limits)
            upper = max(visible_limits)
            ax.axhspan(-1e6, lower, color="red", alpha=0.08, zorder=0)
            ax.axhspan(upper, 1e6, color="red", alpha=0.08, zorder=0)
        else:
            base = min(visible_limits)
            ax.axhspan(base, ax.get_ylim()[1] * 20, color="red", alpha=0.07, zorder=0)
        top = max(float(data_max), max(visible_limits)) * 1.22
    else:
        data_max = d["valor_medido"].max()
        top = float(data_max) * 1.22 if pd.notna(data_max) and data_max > 0 else 1.0

    if not math.isfinite(top) or top <= 0:
        top = 1.0
    ax.set_ylim(-0.02 * top, top)

    if visible_limits:
        ax.legend(loc="upper right", frameon=True, fontsize=16,
                  facecolor="white", framealpha=1)

    fig.subplots_adjust(top=0.80)
    title = fill(f"{param} (Efluente)", width=70)
    fig.suptitle(title, fontsize=36, fontweight="bold", family="Arial", y=0.985)

    filename = f"ST_{safe_filename(param)}_MCB1005.png"
    output = out_dir / filename
    fig.savefig(output, dpi=600, bbox_inches="tight")
    plt.close(fig)

    return {
        "param": param,
        "file": output.name,
        "campaign_count": len(months_ordered),
        "rows": int(len(d)),
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
    out_root = Path(os.environ.get("BRAANG01_MCB1005_OUT_ROOT", str(DEFAULT_OUT_ROOT)))
    out_dir = out_root / "revisado" / "Efluente_MCB1005"
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
        "point": POINT,
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
