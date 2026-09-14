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
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CODE = "BRAANG01"
MATRIX = "Efluente"
POINTS = ["MCB907E", "MCB907S"]

DEFAULT_REV_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados/_revisoes/"
    "R02_efluente_mcb907_periodicidade_20260709"
)

SELECTED_CAMPAIGNS = [
    ("jan-2021", "2021-01"),
    ("mar-2021", "2021-03"),
    ("jul-2021", "2021-07"),
    ("set-2021", "2021-09"),
    ("dez-2021", "2021-12"),
    ("mar-2022", "2022-03"),
    ("jun-2022", "2022-06"),
    ("set-2022", "2022-09"),
    ("dez-2022", "2022-12"),
    ("mar-2023", "2023-03"),
    ("jun-2023", "2023-06"),
    ("set-2023", "2023-09"),
    ("nov-2023", "2023-11"),
    ("mar-2024", "2024-03"),
    ("jun-2024", "2024-06"),
    ("set-2024", "2024-09"),
    ("nov-2024", "2024-11"),
    ("mar-2025", "2025-03"),
    ("jun-2025", "2025-06"),
]

SELECTED_PARAMS = [
    "Coliformes Totais",
    "Demanda Qu\u00edmica de Oxig\u00eanio",
    "E. Coli",
    "Ferro Dissolvido",
    "F\u00f3sforo Total",
    "Nitrog\u00eanio Total",
    "Sulfeto",
    "Temperatura da \u00c1gua",
    "Oxig\u00eanio Dissolvido (OD)",
    "S\u00f3lidos Sediment\u00e1veis",
    "S\u00f3lidos Dissolvidos Totais",
    "S\u00f3lidos Totais Suspensos",
    "pH",
]

MONTHLY_PARAM = "Demanda Bioqu\u00edmica de Oxig\u00eanio"


def revision_root() -> Path:
    return Path(os.environ.get("BRAANG01_EFLUENTE_REV_ROOT", str(DEFAULT_REV_ROOT)))


def safe_filename(name: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(" ", "_")
    return safe


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
          AND nome_ponto = ANY(:points)
        """
    )
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '15min'"))
        df = pd.read_sql(
            query,
            conn,
            params={"code": PROJECT_CODE, "matrix": MATRIX, "points": POINTS},
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
    return df.sort_values(["nome_parametro", "nome_ponto", "data_hora_coleta"])


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


def add_limits(ax, point_data: pd.DataFrame, param: str) -> list[float]:
    visible: list[float] = []
    if param == "pH":
        lower = first_notna(point_data, "vmp_357_cl2_min")
        upper = first_notna(point_data, "vmp_430_padrao")
        if upper is not None:
            ax.axhline(
                upper,
                color="red",
                linestyle="--",
                linewidth=3,
                label=f"VMP - m\u00e1ximo: {format_limit(upper)}",
                zorder=2,
            )
            visible.append(upper)
        if lower is not None:
            ax.axhline(
                lower,
                color="red",
                linestyle="--",
                linewidth=3,
                label=f"VMP - m\u00ednimo: {format_limit(lower)}",
                zorder=2,
            )
            visible.append(lower)
        return visible

    dynamic = first_notna(point_data, "vmp_amonia_dinamico")
    default = first_notna(point_data, "vmp_430_padrao")
    limit = dynamic if dynamic is not None else default
    if limit is not None:
        ax.axhline(
            limit,
            color="red",
            linestyle="--",
            linewidth=3,
            label=f"VMP - m\u00e1ximo: {format_limit(limit)}",
            zorder=2,
        )
        visible.append(limit)
    return visible


def configure_axis(ax, unit: str, point: str, campaigns: list[str], tick_interval: int) -> None:
    import matplotlib.ticker as mticker
    ax.set_title(f"Ponto {point}", fontsize=28, fontweight="bold", loc="left", family="Arial", pad=20)
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
    if tick_interval > 1:
        ticks = ax.get_xticks()
        labels = [item.get_text() for item in ax.get_xticklabels()]
        keep = set(range(0, len(labels), tick_interval))
        if labels:
            keep.add(len(labels) - 1)
        ax.set_xticks([ticks[i] for i in sorted(keep) if i < len(ticks)])
        ax.set_xticklabels([labels[i] for i in sorted(keep) if i < len(labels)])


def plot_param(
    df: pd.DataFrame,
    param: str,
    out_dir: Path,
    mode: str,
    selected_months: list[str] | None = None,
) -> dict[str, object]:
    d = df[df["nome_parametro"] == param].copy()
    if selected_months is not None:
        d = d[d["ano_mes"].isin(selected_months)].copy()
        order = {month: idx for idx, month in enumerate(selected_months)}
        d["_order"] = d["ano_mes"].map(order)
        d = d.sort_values(["_order", "nome_ponto"])
        campaigns = [label for label, month in SELECTED_CAMPAIGNS if month in set(d["ano_mes"])]
        x_order = {month: idx for idx, month in enumerate(selected_months)}
        d["_x"] = d["ano_mes"].map(x_order)
        x_ticks = list(range(len(selected_months)))
        x_labels = [label for label, _month in SELECTED_CAMPAIGNS]
        tick_interval = 1
    else:
        d = d.sort_values(["data_hora_coleta", "nome_ponto"])
        unique = (
            d[["nome_campanha", "data_hora_coleta"]]
            .drop_duplicates()
            .sort_values("data_hora_coleta")
        )
        campaigns = unique["nome_campanha"].tolist()
        x_order = {campaign: idx for idx, campaign in enumerate(campaigns)}
        d["_x"] = d["nome_campanha"].map(x_order)
        x_ticks = list(range(len(campaigns)))
        x_labels = campaigns
        tick_interval = 3

    if d.empty:
        return {"param": param, "mode": mode, "status": "empty"}

    unit_values = d["unidade_medida"].dropna()
    unit = str(unit_values.iloc[0]) if not unit_values.empty else "-"

    fig, axes = plt.subplots(2, 1, figsize=(19.25, 11.0), squeeze=False)
    axes_flat = [ax for row in axes for ax in row]
    points_with_data = []

    for ax, point in zip(axes_flat, POINTS):
        point_data = d[d["nome_ponto"] == point].copy().sort_values("_x")
        point_data = point_data.dropna(subset=["valor_medido"])
        points_with_data.append({"point": point, "rows": int(len(point_data))})

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
        ax.set_xticklabels(x_labels)
        configure_axis(ax, unit, point, x_labels, tick_interval=tick_interval)

        visible_limits = add_limits(ax, point_data, param)
        if visible_limits:
            data_min = point_data["valor_medido"].min()
            data_max = point_data["valor_medido"].max()
            if pd.isna(data_min):
                data_min = min(visible_limits)
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
            data_max = point_data["valor_medido"].max()
            top = float(data_max) * 1.22 if pd.notna(data_max) and data_max > 0 else 1.0

        if not math.isfinite(top) or top <= 0:
            top = 1.0
        ax.set_ylim(-0.02 * top, top)
        if visible_limits:
            ax.legend(loc="upper right", frameon=True, fontsize=16, facecolor="white", framealpha=1)

    fig.subplots_adjust(top=0.80, hspace=0.95)
    title = fill(f"{param} (Efluente)", width=58)
    fig.suptitle(title, fontsize=36, fontweight="bold", family="Arial", y=0.985)
    filename = f"ST_{safe_filename(param)}_MCB907_{mode.lower().replace(' ', '_')}.png"
    output = out_dir / filename
    fig.savefig(output, dpi=600, bbox_inches="tight")
    plt.close(fig)
    return {
        "param": param,
        "mode": mode,
        "file": output.name,
        "campaign_count": len(campaigns),
        "points": points_with_data,
    }


def clear_output(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in out_dir.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json"}:
            item.unlink()


def main() -> None:
    rev_root = revision_root()
    out_dir = rev_root / "revisado" / "Efluente_MCB907"
    clear_output(out_dir)

    df = load_data()
    selected_months = [month for _label, month in SELECTED_CAMPAIGNS]
    results = []
    for param in SELECTED_PARAMS:
        results.append(plot_param(df, param, out_dir, "campanhas_selecionadas", selected_months))
    results.append(plot_param(df, MONTHLY_PARAM, out_dir, "mensal", selected_months=None))

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "revision": "R02_efluente_mcb907_periodicidade_20260709",
        "points": POINTS,
        "selected_campaigns_requested_from_2021": [label for label, _month in SELECTED_CAMPAIGNS],
        "selected_params": SELECTED_PARAMS,
        "monthly_param": MONTHLY_PARAM,
        "output_dir": str(out_dir),
        "png_count": len(list(out_dir.glob("*.png"))),
        "results": results,
        "notes": [
            "Campanhas de 2020 foram excluidas por aprovacao do usuario em 2026-07-09.",
            "DBO mantem todos os pontos mensais do consolidado, em grafico separado.",
            "DBO usa todos os pontos mensais, com rotulos do eixo X reduzidos para leitura.",
        ],
    }
    with (out_dir / "revision_generation_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
