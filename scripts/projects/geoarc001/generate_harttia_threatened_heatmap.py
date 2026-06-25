from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import load_theme
from opyta_analysis.pipelines.diagnostico.ictio import (
    _apply_campaign_filter,
    _apply_project_campaign_overrides,
    _campaign_short_label,
    _campanha_sort_key,
    _cpuen_por_especie_ponto,
    _load_ictio_df,
    _normalize_text,
    _ordenar_pontos,
)


TARGET_SPECIES = ["Harttia torrenticola", "Harttia leiopleura"]
TARGET_POINT = "IC-ARC-14"


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalise_source_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    rename = {}
    lower = {str(col).strip().lower(): col for col in df.columns}
    for wanted, aliases in {
        "nome_campanha": ["nome_campanha", "campanha"],
        "nome_ponto": ["nome_ponto", "ponto"],
        "especie": ["especie", "espécie", "nome_cientifico", "nome científico"],
        "CPUEn": ["cpuen", "CPUEn"],
    }.items():
        for alias in aliases:
            if alias.lower() in lower:
                rename[lower[alias.lower()]] = wanted
                break
    df = df.rename(columns=rename)
    required = ["nome_campanha", "nome_ponto", "especie", "CPUEn"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(f"Colunas obrigatorias ausentes na tabela de entrada: {', '.join(missing)}")
    return df[required].copy()


def _load_from_pipeline(project_id: int, group: str, env_file: str | None, campaigns: list[str] | None) -> pd.DataFrame:
    df = _load_ictio_df(project_id=project_id, group=group, env_file=env_file)
    df, _overrides = _apply_project_campaign_overrides(df, project_id, group)
    df, _filter = _apply_campaign_filter(df, campaigns)
    if df.empty:
        raise RuntimeError("A base consolidada do pipeline retornou vazia para o escopo informado.")

    cpuen = _cpuen_por_especie_ponto(df)
    if cpuen.empty:
        raise RuntimeError("Nao foi possivel calcular CPUEn por especie, campanha e ponto.")

    out = cpuen.rename(columns={"nome_cientifico": "especie", "cpuen": "CPUEn"})
    return out[["nome_campanha", "nome_ponto", "especie", "CPUEn"]].copy()


def _format_value(value: float) -> str:
    if value >= 10:
        return f"{value:.1f}"
    if value >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.2f}"


def _prepare_matrix(
    df: pd.DataFrame,
    species: str,
    campaigns: list[str],
    points: list[str],
) -> pd.DataFrame:
    subset = df.loc[df["especie"].astype(str).map(_normalize_text).eq(_normalize_text(species))].copy()
    if subset.empty:
        return pd.DataFrame(0.0, index=points, columns=campaigns)

    table = (
        subset.pivot_table(
            index="nome_ponto",
            columns="nome_campanha",
            values="CPUEn",
            aggfunc="sum",
            fill_value=0,
            observed=False,
        )
        .reindex(index=points, columns=campaigns, fill_value=0)
        .astype(float)
    )
    return table


def build_support_table(df: pd.DataFrame, campaigns: list[str], points: list[str]) -> pd.DataFrame:
    rows = []
    for species in TARGET_SPECIES:
        matrix = _prepare_matrix(df, species, campaigns, points)
        for point in points:
            for campaign in campaigns:
                rows.append(
                    {
                        "nome_campanha": campaign,
                        "nome_ponto": point,
                        "especie": species,
                        "CPUEn": float(matrix.loc[point, campaign]),
                    }
                )
    return pd.DataFrame(rows)


def plot_heatmap(table: pd.DataFrame, out_png: Path, theme: dict) -> None:
    campaigns = sorted(table["nome_campanha"].dropna().astype(str).unique().tolist(), key=_campanha_sort_key)
    points = _ordenar_pontos(table["nome_ponto"].dropna().astype(str).unique().tolist())
    if TARGET_POINT in points:
        points = [point for point in points if point != TARGET_POINT] + [TARGET_POINT]

    vmax = float(pd.to_numeric(table["CPUEn"], errors="coerce").fillna(0).max())
    vmax = max(vmax, 1.0)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "cpuen_threatened_harttia",
        ["#F7F7F7", "#D9E6F2", str(theme.get("secondary_hex", "#5B9BD5")), str(theme.get("primary_hex", "#002060"))],
    )

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(12.2, 7.8),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        constrained_layout=False,
    )
    if not isinstance(axes, np.ndarray):
        axes = np.asarray([axes])

    last_image = None
    xlabels = [_campaign_short_label(campaign) for campaign in campaigns]
    target_row = points.index(TARGET_POINT) if TARGET_POINT in points else None
    panel_titles = ["A) Harttia torrenticola", "B) Harttia leiopleura"]

    for ax, species, title in zip(axes, TARGET_SPECIES, panel_titles, strict=True):
        matrix = _prepare_matrix(table, species, campaigns, points)
        values = matrix.to_numpy(dtype=float)
        last_image = ax.imshow(values, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=vmax)
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", fontstyle="italic", pad=8)
        ax.set_yticks(np.arange(len(points)))
        ax.set_yticklabels(points, fontsize=10)
        ax.set_xticks(np.arange(len(campaigns)))
        ax.set_xticklabels(xlabels, rotation=90, ha="center", fontsize=10)
        ax.tick_params(axis="x", labelbottom=True, pad=1)
        ax.set_ylabel("Ponto amostral", fontsize=11)

        ax.set_xticks(np.arange(-0.5, len(campaigns), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(points), 1), minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)

        if target_row is not None:
            ax.add_patch(
                Rectangle(
                    (-0.5, target_row - 0.5),
                    len(campaigns),
                    1.0,
                    fill=False,
                    edgecolor=str(theme.get("primary_hex", "#002060")),
                    linewidth=2.0,
                    clip_on=False,
                )
            )
            for label in ax.get_yticklabels():
                if label.get_text() == TARGET_POINT:
                    label.set_fontweight("bold")
                    label.set_color(str(theme.get("primary_hex", "#002060")))

        threshold = vmax * 0.55
        for row_idx, point in enumerate(points):
            for col_idx, campaign in enumerate(campaigns):
                value = float(matrix.loc[point, campaign])
                if value <= 0:
                    continue
                color = "white" if value >= threshold else "black"
                ax.text(
                    col_idx,
                    row_idx,
                    _format_value(value),
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=color,
                    fontweight="bold",
                )

    axes[-1].set_xlabel("Campanha", fontsize=11)
    fig.text(
        0.5,
        0.02,
        "Células sem valor indicam ausência de registro quantitativo. Registros positivos concentrados em IC-ARC-14.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#404040",
    )
    cbar_ax = fig.add_axes([0.925, 0.18, 0.018, 0.70])
    cbar = fig.colorbar(last_image, cax=cbar_ax, orientation="vertical")
    cbar.set_label("CPUEn (ind./100 m²)", fontsize=11)
    cbar.ax.tick_params(labelsize=9)

    fig.subplots_adjust(left=0.12, right=0.885, top=0.95, bottom=0.17, hspace=0.28)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera heatmap espacial-temporal de Harttia ameaçadas para GEOARC001.")
    parser.add_argument("--input", default=None, help="Planilha/CSV com nome_campanha, nome_ponto, especie e CPUEn.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--project-id", type=int, default=190)
    parser.add_argument("--group", default="Ictiofauna")
    parser.add_argument("--client", default="geoarc001_arcelor")
    parser.add_argument("--campaigns", default=None, help="Campanhas separadas por virgula; se omitido, usa config do projeto.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    config_root = ROOT / "configs"
    theme = load_theme(config_root, args.client)
    project_cfg = _read_json(config_root / "projects" / "geoarc001_arcelor_ictiofauna.json")
    campaigns = (
        [c.strip() for c in str(args.campaigns).split(",") if c.strip()]
        if args.campaigns
        else [str(c).strip() for c in project_cfg.get("campaigns", []) if str(c).strip()]
    )

    if args.input:
        source = _normalise_source_table(Path(args.input))
    else:
        source = _load_from_pipeline(args.project_id, args.group, args.env_file, campaigns)

    source["nome_campanha"] = source["nome_campanha"].astype(str).str.strip()
    source["nome_ponto"] = source["nome_ponto"].astype(str).str.strip()
    source["especie"] = source["especie"].astype(str).str.strip()
    source["CPUEn"] = pd.to_numeric(source["CPUEn"], errors="coerce").fillna(0)
    source = source[source["nome_campanha"].isin(campaigns)].copy()

    all_points = _ordenar_pontos(source["nome_ponto"].dropna().astype(str).unique().tolist())
    if TARGET_POINT not in all_points:
        all_points.append(TARGET_POINT)
    support = build_support_table(source, campaigns, all_points)

    out_xlsx = output_dir / "14_df_heatmap_especies_ameacadas_harttia_ictiofauna.xlsx"
    out_png = output_dir / "14_grafico_heatmap_especies_ameacadas_harttia_ictiofauna.png"
    xlsx_written = True
    try:
        support.to_excel(out_xlsx, index=False, engine="openpyxl")
    except PermissionError:
        xlsx_written = False
    plot_heatmap(support, out_png, theme)

    positive = support.loc[support["CPUEn"] > 0].copy()
    summary = {
        "output_xlsx": str(out_xlsx),
        "xlsx_written": xlsx_written,
        "output_png": str(out_png),
        "rows": int(len(support)),
        "positive_rows": int(len(positive)),
        "positive_points": sorted(positive["nome_ponto"].dropna().astype(str).unique().tolist()),
        "species": TARGET_SPECIES,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
