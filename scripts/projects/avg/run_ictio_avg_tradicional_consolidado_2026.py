from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_ictio_avg_abril_maio as avg_runner  # noqa: E402


ROOT = avg_runner.ROOT
CONFIG_PATH = ROOT / "configs" / "projects" / "braavg002_ictiofauna_2026.json"
DEFAULT_OUTPUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados ictio"
    r"\Consolidado_2026\icitiofauna"
)
PROJECT_CODE = "BRAAVG002"
GROUP = "Ictiofauna"
START_CAMPAIGN = 1
END_CAMPAIGN = 47
TAXON_DISPLAY_OVERRIDES = {
    "Poecilia mexicana": "Poecilia cf. mexicana",
}
MONTHS = {
    "jan": (1, "Jan"),
    "janeiro": (1, "Jan"),
    "fev": (2, "Fev"),
    "fevereiro": (2, "Fev"),
    "mar": (3, "Mar"),
    "marco": (3, "Mar"),
    "abr": (4, "Abr"),
    "abril": (4, "Abr"),
    "mai": (5, "Mai"),
    "maio": (5, "Mai"),
    "jun": (6, "Jun"),
    "junho": (6, "Jun"),
    "jul": (7, "Jul"),
    "julho": (7, "Jul"),
    "ago": (8, "Ago"),
    "agosto": (8, "Ago"),
    "set": (9, "Set"),
    "setembro": (9, "Set"),
    "out": (10, "Out"),
    "outubro": (10, "Out"),
    "nov": (11, "Nov"),
    "novembro": (11, "Nov"),
    "dez": (12, "Dez"),
    "dezembro": (12, "Dez"),
}
REPORT_POINT_GROUPS = {
    "G01_AC01_PIC01_PIC03": ["PIC-01", "PIC-02", "PIC-03"],
    "G02_AC01_PIC04_PIC06": ["PIC-04", "PIC-05", "PIC-06"],
    "G03_AC01_PIC07_PIC09": ["PIC-07", "PIC-08", "PIC-09"],
    "G04_AC01_PIC11": ["PIC-11"],
    "G05_AC02_PIC10_PIC13": ["PIC-10", "PIC-12", "PIC-13"],
}
TEMPORAL_YEAR_BANDS = [
    (2023, 1, 12),
    (2024, 13, 24),
    (2025, 25, 36),
    (2026, 37, 47),
]
REPORT_SEASON_COLORS = {"CH": "#006837", "SC": "#E66101", "ND": "#555555"}
NOT_SAMPLED_CAMPAIGN_RANGES = {
    "PIC-01": [(40, None)],
    "PIC-02": [(40, 42)],
    "PIC-03": [(40, 42), (44, None)],
    "PIC-11": [(40, None)],
}


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _normalize_text(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def campaign_parts(value: object) -> tuple[int, int, str, int]:
    raw = str(value or "")
    normalized = _normalize_text(raw)
    match = re.match(r"^\s*(\d+)", normalized)
    if not match:
        raise ValueError(f"Campanha sem numero ordinal: {raw}")
    seq = int(match.group(1))
    month_num = None
    month_label = None
    year = None
    for token in normalized.split():
        if token in MONTHS:
            month_num, month_label = MONTHS[token]
        elif re.fullmatch(r"\d{2,4}", token):
            raw_year = int(token)
            year = 2000 + raw_year if raw_year < 100 else raw_year
    if month_num is None or year is None:
        raise ValueError(f"Campanha sem mes/ano reconhecidos: {raw}")
    return seq, month_num, str(month_label), year


def season_from_month(month: int) -> str:
    return "CH" if month in {10, 11, 12, 1, 2, 3} else "SC"


def standard_campaign_name(value: object) -> str:
    seq, month, _label, year = campaign_parts(value)
    return f"C{seq:03d}-{year}-{month:02d}-{season_from_month(month)}"


def standard_campaign_sequence(value: object) -> int:
    match = re.match(r"^C0*(\d+)", str(value or "").strip(), flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return campaign_parts(value)[0]


def standard_campaign_month_year(value: object) -> tuple[int, int]:
    text = str(value or "")
    match = re.match(r"^C0*\d+-(\d{4})-(\d{2})-", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(2)), int(match.group(1))
    _seq, month, _label, year = campaign_parts(value)
    return month, year


def temporal_year_from_campaign(value: object) -> int:
    month, year = standard_campaign_month_year(value)
    return year + 1 if month >= 8 else year


def temporal_year_groups(campaigns: list[str]) -> dict[int, list[str]]:
    groups: dict[int, list[str]] = {}
    for campaign in sorted(campaigns, key=standard_campaign_sequence):
        groups.setdefault(temporal_year_from_campaign(campaign), []).append(campaign)
    return groups


def selected_campaign_map(campaigns: pd.Series) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for campaign in sorted(campaigns.dropna().astype(str).unique().tolist(), key=lambda item: campaign_parts(item)[0]):
        seq, month, _label, year = campaign_parts(campaign)
        if START_CAMPAIGN <= seq <= END_CAMPAIGN:
            mapping[campaign] = f"C{seq:03d}-{year}-{month:02d}-{season_from_month(month)}"
    return mapping


def apply_taxon_overrides(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "nome_cientifico" not in out.columns:
        return out
    out["nome_cientifico_banco"] = out["nome_cientifico"]
    out["nome_cientifico"] = out["nome_cientifico"].map(
        lambda value: TAXON_DISPLAY_OVERRIDES.get(str(value).strip(), value)
    )
    return out


def add_area_control(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "nome_ponto" in out.columns:
        out["area_controle"] = out["nome_ponto"].map(avg_runner.AREA_BY_POINT)
    return out


def apply_sampling_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    """Remove ponto-campanha definido como nao amostrado da camada analitica."""
    if df.empty or "nome_campanha" not in df.columns or "nome_ponto" not in df.columns:
        return df
    out = df.copy()
    seq = out["nome_campanha"].map(standard_campaign_sequence)
    point = out["nome_ponto"].astype(str).str.strip()
    remove = pd.Series(False, index=out.index)
    for point_name, ranges in NOT_SAMPLED_CAMPAIGN_RANGES.items():
        for first_seq, last_seq in ranges:
            in_range = seq >= first_seq
            if last_seq is not None:
                in_range &= seq <= last_seq
            remove |= (point == point_name) & in_range
    return out.loc[~remove].copy()


def clean_traditional_outputs(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    removed = 0
    for item in output_dir.iterdir():
        if not item.is_file() or item.name.lower() == "desktop.ini":
            continue
        if (
            re.match(r"^(0[1-9]|1[0-4])_", item.name)
            or item.name.startswith("DarwinCore_IEF_Ictiofauna_")
            or item.name == "manifesto_braavg002_tradicional_ictiofauna_2026.json"
            or item.name == "README_analises_tradicionais_ictiofauna_01_47.md"
        ):
            item.unlink()
            removed += 1
    return removed


def build_frames() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    df_all = avg_runner._load_df_from_sql()
    if df_all.empty:
        raise RuntimeError("Sem dados consolidados para BRAAVG002/Ictiofauna.")
    df_esf = avg_runner._load_esforcos_quantitativos()
    campaign_map = selected_campaign_map(df_all["nome_campanha"])
    if not campaign_map:
        raise RuntimeError("Nenhuma campanha entre C001 e C047 encontrada.")

    df_observed = df_all[df_all["nome_campanha"].isin(campaign_map)].copy()
    df_observed["nome_campanha_original"] = df_observed["nome_campanha"]
    df_observed["nome_campanha"] = df_observed["nome_campanha"].map(campaign_map)
    df_observed = apply_taxon_overrides(add_area_control(df_observed))

    if df_esf.empty:
        df_effort = df_esf.copy()
    else:
        df_effort = df_esf[df_esf["nome_campanha"].isin(campaign_map)].copy()
        df_effort["nome_campanha_original"] = df_effort["nome_campanha"]
        df_effort["nome_campanha"] = df_effort["nome_campanha"].map(campaign_map)
        df_effort = add_area_control(df_effort)
        df_effort = apply_sampling_adjustments(df_effort)

    padded = []
    for standard_campaign in sorted(campaign_map.values(), key=lambda item: int(re.search(r"C0*(\d+)", item).group(1))):
        df_c = df_observed[df_observed["nome_campanha"] == standard_campaign].copy()
        df_esf_c = df_effort[df_effort["nome_campanha"] == standard_campaign].copy() if not df_effort.empty else df_effort
        padded.append(avg_runner._pad_zero_catch(df_c, df_esf_c))
    df_point_metrics = pd.concat(padded, ignore_index=True) if padded else df_observed.copy()
    df_point_metrics = apply_taxon_overrides(add_area_control(df_point_metrics))
    return df_observed, df_point_metrics, campaign_map


def _campaigns_from_table(table: pd.DataFrame, groups: dict[int, list[str]], year: int) -> list[str]:
    available = set(table["nome_campanha"].dropna().astype(str))
    return [campaign for campaign in groups.get(year, []) if campaign in available]


def _plot_temporal_point_metric(
    *,
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    output_dir: Path,
    filename_template: str,
    groups: dict[int, list[str]],
    theme: dict,
    points: list[str],
    decimals: int,
) -> list[str]:
    outputs: list[str] = []
    for year in sorted(groups):
        campaigns = _campaigns_from_table(table, groups, year)
        if not campaigns:
            continue
        out_png = output_dir / filename_template.format(year=year)
        avg_runner.ictio_mod._small_multiple_metric(
            table=table[table["nome_campanha"].isin(campaigns)].copy(),
            value_col=value_col,
            ylabel=ylabel,
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=decimals,
        )
        outputs.append(str(out_png))
    return outputs


def _plot_temporal_diversity(
    *,
    table: pd.DataFrame,
    output_dir: Path,
    groups: dict[int, list[str]],
    theme: dict,
    points: list[str],
    group_slug: str,
) -> list[str]:
    outputs: list[str] = []
    for year in sorted(groups):
        campaigns = _campaigns_from_table(table, groups, year)
        if not campaigns:
            continue
        out_png = output_dir / f"10_grafico_diversidade_alfa_ano_temporal_{year}_{group_slug}.png"
        avg_runner.ictio_mod._small_multiple_diversity(
            diversity=table[table["nome_campanha"].isin(campaigns)].copy(),
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
        )
        outputs.append(str(out_png))
    return outputs


def _find_taxon_column(columns: list[object]) -> str:
    for column in columns:
        text = _normalize_text(column)
        if text in {"taxon", "taxon final"} or "taxon" in text:
            return str(column)
    raise RuntimeError("Coluna de taxon nao encontrada na sintese de ocorrencia.")


def _plot_temporal_occurrence_campaign(
    *,
    output_dir: Path,
    groups: dict[int, list[str]],
    theme: dict,
    group_slug: str,
) -> list[str]:
    workbook = output_dir / f"04A_tabela_sintese_ocorrencia_{group_slug}.xlsx"
    if not workbook.exists():
        return []
    frequency = pd.read_excel(workbook, sheet_name="Freq_Campanha")
    if frequency.empty:
        return []

    taxon_col = _find_taxon_column(list(frequency.columns))
    campaign_cols = [str(column) for column in frequency.columns if re.match(r"^C0*\d+", str(column))]
    metadata_cols = [str(column) for column in frequency.columns if str(column) not in campaign_cols]
    metadata = frequency[metadata_cols].rename(columns={taxon_col: "T\xc3\xa1xon"}).copy()
    if "T\xc3\xa1xon" not in metadata.columns:
        metadata["T\xc3\xa1xon"] = frequency[taxon_col]

    group_column = "Ordem" if "Ordem" in metadata.columns else None
    outputs: list[str] = []
    for year in sorted(groups):
        campaigns = [campaign for campaign in groups[year] if campaign in campaign_cols]
        if not campaigns:
            continue
        matrix = frequency.set_index(taxon_col).reindex(columns=campaigns).fillna(0)
        generated: list[str] = []
        rendered = avg_runner.ictio_mod.export_occurrence_summary.__globals__["_render_frequency_heatmaps"](
            matrix,
            metadata=metadata,
            group_column=group_column,
            output_dir=output_dir,
            filename_prefix=f"04B_grafico_frequencia_ocorrencia_por_campanha_ano_temporal_{year}_{group_slug}",
            xlabel=f"Campanha - ano temporal {year}",
            theme=theme,
            generated_files=generated,
            campaign_columns=True,
        )
        outputs.extend(rendered)
    return outputs


def _remove_replaced_single_figures(output_dir: Path, group_slug: str) -> list[str]:
    patterns = [
        f"02_grafico_riqueza_por_ponto_{group_slug}.png",
        f"03_grafico_abundancia_por_ponto_{group_slug}.png",
        f"04B_grafico_frequencia_ocorrencia_por_campanha_{group_slug}.png",
        f"10_grafico_diversidade_alfa_{group_slug}.png",
        f"02_grafico_riqueza_por_ponto_ano_temporal_*_{group_slug}.png",
        f"03_grafico_abundancia_por_ponto_ano_temporal_*_{group_slug}.png",
        f"06_grafico_cpuen_por_ponto_ano_temporal_*_{group_slug}.png",
        f"07_grafico_cpueb_por_ponto_ano_temporal_*_{group_slug}.png",
        f"10_grafico_diversidade_alfa_ano_temporal_*_{group_slug}.png",
        f"06_grafico_cpuen_por_ano_*_{group_slug}.png",
        f"07_grafico_cpueb_por_ano_*_{group_slug}.png",
    ]
    removed: list[str] = []
    for pattern in patterns:
        for path in output_dir.glob(pattern):
            if path.is_file():
                path.unlink()
                removed.append(path.name)
    return sorted(removed)


def _campaign_short_label(value: object) -> str:
    return f"C{standard_campaign_sequence(value):02d}"


def _campaign_period(value: object) -> str:
    text = str(value or "").upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text):
        return "CH"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text):
        return "SC"
    return "ND"


def _prepare_report_table(table: pd.DataFrame) -> pd.DataFrame:
    out = table.copy()
    out["campanha_seq"] = out["nome_campanha"].map(standard_campaign_sequence)
    out["campanha_curta"] = out["nome_campanha"].map(_campaign_short_label)
    out["periodo"] = out["nome_campanha"].map(_campaign_period)
    return out


def _decorate_report_temporal_axis(ax: Any, *, ymax: float) -> None:
    for index, (year, start, end) in enumerate(TEMPORAL_YEAR_BANDS):
        if index % 2 == 0:
            ax.axvspan(start - 0.5, end + 0.5, color="#F2F8EF", zorder=0)
        ax.text(
            (start + end) / 2,
            ymax * 0.965,
            f"Ano {year}",
            ha="center",
            va="top",
            fontsize=11.5,
            color="#465B41",
            zorder=3,
        )
    for boundary in [12.5, 24.5, 36.5]:
        ax.axvline(boundary, color="#4F4F4F", linewidth=1.05, linestyle=":", zorder=2)


def _plot_report_point_group(
    *,
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    output_dir: Path,
    filename_prefix: str,
    group_name: str,
    points: list[str],
    group_slug: str,
    y_floor: float = 1.0,
) -> str:
    campaigns = (
        table[["nome_campanha", "campanha_seq", "campanha_curta", "periodo"]]
        .drop_duplicates()
        .sort_values("campanha_seq")
        .reset_index(drop=True)
    )
    x_all = campaigns["campanha_seq"].to_numpy(dtype=float)
    labels = campaigns["campanha_curta"].tolist()
    season_by_seq = campaigns.set_index("campanha_seq")["periodo"].to_dict()
    values = pd.to_numeric(table[value_col], errors="coerce").fillna(0)
    ymax = max(float(values.max()) if not values.empty else 0.0, y_floor) * 1.13

    rows = len(points)
    figure_height = {1: 2.85, 2: 4.55}.get(rows, 6.15)
    fig, axes = plt.subplots(
        rows,
        1,
        figsize=(12.9, figure_height),
        dpi=500,
        sharex=True,
        sharey=True,
    )
    axes_flat = np.asarray(axes, dtype=object).reshape(rows)

    for index, (ax, point) in enumerate(zip(axes_flat, points)):
        point_data = (
            table[table["nome_ponto"] == point]
            .set_index("campanha_seq")
            .reindex(range(START_CAMPAIGN, END_CAMPAIGN + 1))
            .reset_index()
        )
        y = pd.to_numeric(point_data[value_col], errors="coerce").to_numpy(dtype=float)
        x = point_data["campanha_seq"].to_numpy(dtype=float)
        _decorate_report_temporal_axis(ax, ymax=ymax)
        ax.plot(x, y, color="#4D4D4D", linewidth=1.25, zorder=1)
        for period, color in REPORT_SEASON_COLORS.items():
            mask = np.array([season_by_seq.get(int(seq), "ND") == period for seq in x]) & ~np.isnan(y)
            ax.scatter(
                x[mask],
                y[mask],
                s=42,
                color=color,
                edgecolor="black",
                linewidth=0.46,
                zorder=4,
            )

        ax.text(0.025, 0.82, point, transform=ax.transAxes, ha="left", va="top", fontsize=18, fontweight="bold")
        ax.set_ylim(0, ymax)
        ax.set_xlim(0.5, 47.5)
        ax.grid(axis="y", color="#D8D8D8", linewidth=0.72, alpha=0.82)
        ax.grid(axis="x", color="#EEEEEE", linewidth=0.46, alpha=0.55)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.set_xticks(x_all)
        if index < rows - 1:
            ax.tick_params(axis="x", labelbottom=False, length=3.2, width=0.8)
        else:
            ax.set_xticklabels(labels, rotation=90, fontsize=9.5)
            ax.tick_params(axis="x", labelbottom=True, pad=1.5, width=0.8)
        ax.tick_params(axis="y", labelsize=12, width=0.8)

    axes_flat[rows // 2].set_ylabel(ylabel, fontsize=14)
    axes_flat[-1].set_xlabel("Campanha", fontsize=14, labelpad=5)
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=REPORT_SEASON_COLORS["CH"],
            markeredgecolor="black",
            markersize=8.8,
            label="CH",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=REPORT_SEASON_COLORS["SC"],
            markeredgecolor="black",
            markersize=8.8,
            label="SC",
        ),
        plt.Line2D([0], [0], color="#4F4F4F", linestyle=":", linewidth=1.3, label="Ano temporal"),
    ]
    top = 0.875 if rows > 1 else 0.74
    bottom = 0.145 if rows > 1 else 0.30
    hspace = 0.16 if rows > 1 else 0.10
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=3,
        frameon=False,
        fontsize=13,
        handlelength=2.0,
        columnspacing=2.0,
    )
    fig.subplots_adjust(left=0.062, right=0.998, top=top, bottom=bottom, hspace=hspace)
    out_png = output_dir / f"{filename_prefix}_{group_name}_{group_slug}.png"
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return str(out_png)


def _plot_report_point_groups(
    *,
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    output_dir: Path,
    filename_prefix: str,
    group_slug: str,
) -> list[str]:
    data = _prepare_report_table(table)
    outputs: list[str] = []
    for group_name, points in REPORT_POINT_GROUPS.items():
        outputs.append(
            _plot_report_point_group(
                table=data,
                value_col=value_col,
                ylabel=ylabel,
                output_dir=output_dir,
                filename_prefix=filename_prefix,
                group_name=group_name,
                points=points,
                group_slug=group_slug,
            )
        )
    return outputs


def generate_report_figures(
    *,
    output_dir: Path,
    theme: dict,
    campaign_map: dict[str, str],
) -> dict[str, Any]:
    group_slug = avg_runner.ictio_mod._safe_group_name(GROUP)
    groups = temporal_year_groups(list(campaign_map.values()))
    temporal_summary = {
        str(year): {
            "campaigns": campaigns,
            "first": campaigns[0] if campaigns else None,
            "last": campaigns[-1] if campaigns else None,
            "count": len(campaigns),
        }
        for year, campaigns in groups.items()
    }

    generated: dict[str, list[str]] = {}
    richness = pd.read_excel(output_dir / f"02_df_riqueza_por_ponto_{group_slug}.xlsx")
    abundance = pd.read_excel(output_dir / f"03_df_abundancia_por_ponto_{group_slug}.xlsx")
    cpue = pd.read_excel(output_dir / f"06_df_cpue_por_ponto_{group_slug}.xlsx")
    diversity = pd.read_excel(output_dir / f"10_df_diversidade_alfa_{group_slug}.xlsx")
    diversity = diversity[diversity["nome_ponto"].isin(sum(REPORT_POINT_GROUPS.values(), []))].copy()

    removed = _remove_replaced_single_figures(output_dir, group_slug)
    generated["02_riqueza_a4_c001_c047"] = _plot_report_point_groups(
        table=richness,
        value_col="riqueza",
        ylabel="Riqueza taxonômica",
        output_dir=output_dir,
        filename_prefix="02_grafico_riqueza_por_ponto_c001_c047",
        group_slug=group_slug,
    )
    generated["03_abundancia_a4_c001_c047"] = _plot_report_point_groups(
        table=abundance,
        value_col="abundancia_total",
        ylabel="Abundância total (número de indivíduos)",
        output_dir=output_dir,
        filename_prefix="03_grafico_abundancia_por_ponto_c001_c047",
        group_slug=group_slug,
    )
    generated["04B_ocorrencia_campanha_ano_temporal"] = _plot_temporal_occurrence_campaign(
        output_dir=output_dir,
        groups=groups,
        theme=theme,
        group_slug=group_slug,
    )
    generated["06_cpuen_a4_c001_c047"] = _plot_report_point_groups(
        table=cpue,
        value_col="cpuen",
        ylabel="CPUEn (ind./100 m²)",
        output_dir=output_dir,
        filename_prefix="06_grafico_cpuen_por_ponto_c001_c047",
        group_slug=group_slug,
    )
    generated["07_cpueb_a4_c001_c047"] = _plot_report_point_groups(
        table=cpue,
        value_col="cpueb",
        ylabel="CPUEb (g/100 m²)",
        output_dir=output_dir,
        filename_prefix="07_grafico_cpueb_por_ponto_c001_c047",
        group_slug=group_slug,
    )
    generated["10A_shannon_a4_c001_c047"] = _plot_report_point_groups(
        table=diversity,
        value_col="Shannon_H",
        ylabel="Shannon (H')",
        output_dir=output_dir,
        filename_prefix="10A_grafico_shannon_por_ponto_c001_c047",
        group_slug=group_slug,
    )
    generated["10B_pielou_a4_c001_c047"] = _plot_report_point_groups(
        table=diversity,
        value_col="Pielou_J",
        ylabel="Pielou (J')",
        output_dir=output_dir,
        filename_prefix="10B_grafico_pielou_por_ponto_c001_c047",
        group_slug=group_slug,
    )

    readme = output_dir / "README_analises_tradicionais_ictiofauna_01_47.md"
    readme.write_text(
        "\n".join(
            [
                "# Análises tradicionais de ictiofauna - C001 a C047",
                "",
                "As planilhas tradicionais foram geradas com a base histórica completa C001-C047.",
                "As figuras por ponto adotam o modelo A4 paisagem aprovado para o relatório.",
                "Cada prancha usa um ponto por linha, eixo de campanha C01-C47 somente no painel inferior, cores fortes para CH/SC e marcação dos anos temporais.",
                "",
                "- Ano temporal 2023: C001 a C012.",
                "- Ano temporal 2024: C013 a C024.",
                "- Ano temporal 2025: C025 a C036.",
                "- Ano temporal 2026: C037 a C047; julho/2026 ainda não entrou na base.",
                "",
                "A taxonomia de saída apresenta Poecilia mexicana como Poecilia cf. mexicana.",
                "Banco de dados, coordenadas e categorias ecológicas mestre não foram alterados.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    generated["readme"] = [str(readme)]

    return {
        "temporal_years": temporal_summary,
        "generated": generated,
        "generated_count": sum(len(files) for files in generated.values()),
        "removed_replaced_single_figures": removed,
    }


def rewrite_point_metric_tables(output_dir: Path, df_point_metrics: pd.DataFrame) -> dict[str, Any]:
    group_slug = avg_runner.ictio_mod._safe_group_name(GROUP)
    df = df_point_metrics.copy()
    df["contagem"] = pd.to_numeric(df.get("contagem", 0), errors="coerce").fillna(0)
    df["nome_cientifico"] = df["nome_cientifico"].fillna("").astype(str).str.strip()

    valid_taxa = df[(df["contagem"] > 0) & (df["nome_cientifico"] != "")].copy()
    richness = (
        valid_taxa.groupby(["nome_campanha", "nome_ponto"], dropna=False)["nome_cientifico"]
        .nunique()
        .reset_index(name="riqueza")
    )
    sampled_pairs = df[["nome_campanha", "nome_ponto"]].drop_duplicates()
    richness = sampled_pairs.merge(richness, on=["nome_campanha", "nome_ponto"], how="left")
    richness["riqueza"] = pd.to_numeric(richness["riqueza"], errors="coerce").fillna(0).astype(int)

    abundance = (
        df.groupby(["nome_campanha", "nome_ponto"], dropna=False)["contagem"]
        .sum()
        .reset_index(name="abundancia_total")
    )

    sort_cols = ["campaign_seq", "point_order"]
    point_order_map = {point: idx for idx, point in enumerate(sum(REPORT_POINT_GROUPS.values(), []))}
    for table in (richness, abundance):
        table["campaign_seq"] = table["nome_campanha"].map(standard_campaign_sequence)
        table["point_order"] = table["nome_ponto"].map(point_order_map)
        table.sort_values(sort_cols, inplace=True)
        table.drop(columns=sort_cols, inplace=True)

    richness.to_excel(output_dir / f"02_df_riqueza_por_ponto_{group_slug}.xlsx", index=False, engine="openpyxl")
    abundance.to_excel(output_dir / f"03_df_abundancia_por_ponto_{group_slug}.xlsx", index=False, engine="openpyxl")

    return {
        "richness_rows": int(len(richness)),
        "abundance_rows": int(len(abundance)),
        "sampled_point_campaigns": int(len(sampled_pairs)),
    }


def run(output_dir: Path, clean: bool) -> dict[str, Any]:
    recipe = avg_runner._load_recipe(CONFIG_PATH)
    avg_runner._apply_recipe(recipe)
    theme = avg_runner.load_theme(ROOT / "configs", avg_runner.CLIENT)

    removed = clean_traditional_outputs(output_dir) if clean else 0
    df_observed, df_point_metrics, campaign_map = build_frames()
    details = avg_runner._run_blocks_for_df(
        df_observed=df_observed,
        df_point_metrics=df_point_metrics,
        group=GROUP,
        theme=theme,
        output_dir=output_dir,
    )
    point_metric_tables = rewrite_point_metric_tables(output_dir, df_point_metrics)
    report_figures = generate_report_figures(
        output_dir=output_dir,
        theme=theme,
        campaign_map=campaign_map,
    )
    if isinstance(details.get("generated_files"), list):
        details["generated_files"] = [
            file_path for file_path in details["generated_files"] if Path(file_path).exists()
        ]

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "status": "generated",
        "output_dir": str(output_dir),
        "campaign_scope": "C001 a C047",
        "campaigns": [{"original": key, "standard": value} for key, value in campaign_map.items()],
        "temporal_year_policy": "agosto a julho",
        "rows_observed": int(len(df_observed)),
        "rows_with_zero_capture_points": int(len(df_point_metrics)),
        "points": int(df_point_metrics["nome_ponto"].nunique()),
        "species": int(df_observed["nome_cientifico"].nunique()),
        "taxonomy_display_overrides": TAXON_DISPLAY_OVERRIDES,
        "removed_previous_traditional_files": int(removed),
        "report_figures": report_figures,
        "point_metric_tables": point_metric_tables,
        "details": details,
    }
    manifest = output_dir / "manifesto_braavg002_tradicional_ictiofauna_2026.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera analises tradicionais C001-C047 da Ictiofauna AVG.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-clean", action="store_true", help="Nao remove arquivos tradicionais antigos antes de gerar.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run(Path(args.output_dir), clean=not args.no_clean)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
