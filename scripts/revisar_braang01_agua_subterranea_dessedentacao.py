from __future__ import annotations

import json
import math
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CODE = "BRAANG01"
MATRIX = "\u00c1gua Subterr\u00e2nea"
OUTPUT_SUBDIR = "\u00c1gua_Subterr\u00e2nea"
VMP_COLUMN = "vmp_396_dessedentacao_animal"
VMP_COLOR = "#8B4513"
VMP_LABEL = "VMP - Dessedenta\u00e7\u00e3o"

DEFAULT_REV_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados/_revisoes/"
    "R01_agua_subterranea_dessedentacao_20260709"
)


def revision_root() -> Path:
    return Path(os.environ.get("BRAANG01_REV_ROOT", str(DEFAULT_REV_ROOT)))


def original_results_root() -> Path:
    return revision_root().parents[1]


def safe_plot_filename(param: str, page: int) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "", str(param)).replace(" ", "_")
    return f"ST_{safe}_P{page}.png"


def campaign_key(campaign: object) -> int:
    months = {
        "jan": 1,
        "fev": 2,
        "mar": 3,
        "abr": 4,
        "mai": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8,
        "set": 9,
        "out": 10,
        "nov": 11,
        "dez": 12,
        "janeiro": 1,
        "fevereiro": 2,
        "mar\u00e7o": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }
    try:
        month, year = str(campaign).lower().split("-", 1)
        return int(year) * 100 + months.get(month, 0)
    except Exception:
        return 0


def format_limit(value: float) -> str:
    if pd.isna(value):
        return ""
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def load_data() -> pd.DataFrame:
    load_dotenv(REPO_ROOT / ".env")
    db_url = os.environ.get("FISICO_DB_URL")
    if not db_url:
        raise RuntimeError("FISICO_DB_URL nao encontrado no .env")

    engine = create_engine(db_url)
    query = text(
        """
        SELECT *
        FROM public.fisico_analise_consolidada
        WHERE codigo_interno_opyta = :code
          AND matriz = :matrix
        """
    )
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '15min'"))
        df = pd.read_sql(query, conn, params={"code": PROJECT_CODE, "matrix": MATRIX})

    required = {
        "nome_ponto",
        "nome_campanha",
        "nome_parametro",
        "valor_medido",
        "unidade_medida",
        VMP_COLUMN,
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"Colunas ausentes no consolidado: {missing}")

    df["valor_medido"] = pd.to_numeric(df["valor_medido"], errors="coerce")
    df[VMP_COLUMN] = pd.to_numeric(df[VMP_COLUMN], errors="coerce")
    df["ordem_cron"] = df["nome_campanha"].apply(campaign_key)
    return df.sort_values(["nome_ponto", "ordem_cron"])


def configure_axis(ax, unit: str, point_label: str) -> None:
    ax.set_title(
        f"Ponto {point_label}",
        fontsize=28,
        fontweight="bold",
        loc="left",
        family="Arial",
        pad=20,
    )
    ax.set_ylabel(unit, fontsize=22, fontweight="bold", family="Arial")
    ax.set_xlabel("Campanhas", fontsize=20, family="Arial")
    ax.tick_params(axis="x", rotation=90, labelsize=16)
    ax.tick_params(axis="y", labelsize=16)
    ax.yaxis.grid(True, linestyle="-", alpha=0.4, color="#CCCCCC")


def plot_param(df_param: pd.DataFrame, param: str, out_dir: Path) -> int:
    points = list(df_param["nome_ponto"].dropna().unique())
    point_groups = [points[i : i + 3] for i in range(0, len(points), 3)]
    unit_series = df_param["unidade_medida"].dropna()
    unit = str(unit_series.iloc[0]) if not unit_series.empty else "-"
    generated = 0

    for page_index, group in enumerate(point_groups, start=1):
        group_data = df_param[df_param["nome_ponto"].isin(group)].copy()
        campaigns = (
            group_data[["nome_campanha", "ordem_cron"]]
            .drop_duplicates()
            .sort_values("ordem_cron")["nome_campanha"]
            .tolist()
        )
        x_map = {campaign: idx for idx, campaign in enumerate(campaigns)}

        fig_height = 5.5 * max(len(group), 1)
        fig, axes = plt.subplots(
            len(group),
            1,
            figsize=(5.5 * 3.5, fig_height),
            squeeze=False,
        )
        axes_flat = [ax for row in axes for ax in row]

        for ax, point_label in zip(axes_flat, group):
            point_data = group_data[group_data["nome_ponto"] == point_label].sort_values(
                "ordem_cron"
            )
            point_data = point_data.dropna(subset=["valor_medido"])
            x_values = [x_map[c] for c in point_data["nome_campanha"]]

            ax.plot(
                x_values,
                point_data["valor_medido"],
                marker="o",
                markersize=12,
                color="#2E7D32",
                linewidth=4,
            )
            ax.set_xticks(range(len(campaigns)))
            ax.set_xticklabels(campaigns)
            configure_axis(ax, unit, point_label)

            visible_limits: list[float] = []
            limit_values = point_data[VMP_COLUMN].dropna()
            if not limit_values.empty:
                limit_value = float(limit_values.iloc[0])
                ax.axhline(
                    limit_value,
                    color=VMP_COLOR,
                    linestyle="--",
                    linewidth=3.5,
                    label=f"{VMP_LABEL}: {format_limit(limit_value)}",
                )
                visible_limits.append(limit_value)

            if visible_limits:
                base = min(visible_limits)
                ax.axhspan(base, ax.get_ylim()[1] * 20, color="red", alpha=0.07, zorder=0)

            data_max = point_data["valor_medido"].max()
            if pd.isna(data_max):
                data_max = 0.0
            limit_max = max(visible_limits) if visible_limits else data_max
            top = max(float(data_max), float(limit_max))
            if not math.isfinite(top) or top <= 0:
                top = 1.0
            top *= 1.3
            ax.set_ylim(-0.02 * top, top)
            if visible_limits:
                ax.legend(
                    loc="upper right",
                    frameon=True,
                    fontsize=16,
                    facecolor="white",
                    framealpha=1,
                )

        top_margin = 0.80 if len(group) <= 2 else 0.90
        hspace = 0.95 if len(group) <= 2 else 0.80
        fig.subplots_adjust(top=top_margin, hspace=hspace)
        fig.suptitle(
            f"{param} ({MATRIX})",
            fontsize=36,
            fontweight="bold",
            family="Arial",
            y=0.985,
        )
        fig.savefig(out_dir / safe_plot_filename(param, page_index), dpi=600, bbox_inches="tight")
        plt.close(fig)
        generated += 1

    return generated


def clear_revised_outputs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in out_dir.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json"}:
            item.unlink()


def copy_unchanged_percent_plot(out_dir: Path) -> bool:
    source = original_results_root() / OUTPUT_SUBDIR / "02_Percentual_Violacao.png"
    if not source.exists():
        return False
    shutil.copy2(source, out_dir / source.name)
    return True


def main() -> None:
    rev_root = revision_root()
    out_dir = rev_root / "revisado" / OUTPUT_SUBDIR
    clear_revised_outputs(out_dir)
    copied_percent = copy_unchanged_percent_plot(out_dir)

    df = load_data()
    generated_by_param: dict[str, int] = {}
    for param in df["nome_parametro"].dropna().unique():
        df_param = df[df["nome_parametro"] == param].sort_values("ordem_cron")
        count = plot_param(df_param, str(param), out_dir)
        generated_by_param[str(param)] = count

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "revision": "R01_agua_subterranea_dessedentacao_20260709",
        "output_dir": str(out_dir),
        "vmp_columns_used_in_temporal_plots": [VMP_COLUMN],
        "vmp_columns_removed_from_temporal_plots": [
            "vmp_396_consumo_humano",
            "vmp_396_irrigacao",
            "vmp_396_recreacao",
        ],
        "layout_source": "ANGLO-Meio-Fisico.ipynb / gerar_serie_temporal_perfeita",
        "copied_unchanged_percentual_violacao": copied_percent,
        "temporal_png_count": sum(generated_by_param.values()),
        "params": generated_by_param,
    }
    with (out_dir / "revision_generation_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
