from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Wedge
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd


DATE_TAG = "20260602"
RUN_TAG = "20260603"
PROJECT_LABEL = "Porto Estrela"
RESULTADOS_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados"
)
BASE_FILE = RESULTADOS_DIR / f"base_analitica_ictiofauna_porto_estrela_{DATE_TAG}.xlsx"
CHAR_FILE = RESULTADOS_DIR / f"caracterizacao_especies_porto_estrela_{DATE_TAG}.xlsx"
MIGRATION_FILE = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Porto Estrela/Planilha/Migra"
    "\u00e7\u00e3o/Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA_260602.xlsx"
)
OUTPUT_DIR = RESULTADOS_DIR / f"resultados_ictiofauna_porto_estrela_producao_{RUN_TAG}"

PRIMARY = "#002060"
SECONDARY = "#5B9BD5"
HIGHLIGHT = "#1F4E79"
LIGHT = "#DBE5F1"
ORANGE = "#D4672A"
GREEN = "#6BA547"
RED = "#B75D69"
GREY = "#6C757D"
GRID = "#D9D9D9"
EDGE = "black"
PALETTE = ["#002060", "#1F4E79", "#5B9BD5", "#9DC3E6", "#DBE5F1", "#808080"]
ALT_PALETTE = [
    "#2E6EA6",
    "#D4672A",
    "#6BA547",
    "#7B4EA3",
    "#C9A227",
    "#4E9A99",
    "#B75D69",
    "#6C757D",
    "#A6CEE3",
    "#FDBF6F",
]

FIGSIZE_WIDE = (18, 10.2)
FIGSIZE_PANEL = (18, 11.2)
DPI = 300
FONT_BASE = 17
FONT_AXIS = 17
FONT_TICK = 13
FONT_LEGEND = 15
FONT_PANEL = 16

POINT_ORDER_TABLE = ["P9", "P8", "P7", "P6", "P3", "P1", "P2", "P5", "P4"]
POINT_ORDER_SPATIAL = ["P4", "P5", "P2", "P1", "P3", "P6", "P7", "P8", "P9"]
POINT_TO_TRECHO = {
    "P4": "Montante",
    "P5": "Montante",
    "P2": "Montante",
    "P1": "Montante",
    "P3": "Jusante",
    "P6": "Jusante",
    "P7": "Jusante",
    "P8": "Jusante",
    "P9": "Jusante",
}
COORDINATE_OVERRIDES = {
    "P1": (-19.108602, -42.662967),
}
RECENT_AH = ["AH2324", "AH2425", "AH2526"]
OUTRAS_NATIVAS_LABEL = "Outras esp\u00e9cies nativas"
OUTRAS_ESPECIES_LABEL = "Outras esp\u00e9cies"
TRECHO_LINE_COLORS = {"Montante": PRIMARY, "Jusante": SECONDARY}
TRECHO_MAP_COLORS = {"Montante": PRIMARY, "Jusante": ORANGE}
GROUP_ORDER_MIG_ORIGIN = [
    "Migradora nativa",
    "Migradora n\u00e3o nativa",
    "N\u00e3o migradora nativa",
    "N\u00e3o migradora n\u00e3o nativa",
]
GROUP_COLORS = {
    "Migradora nativa": PRIMARY,
    "Migradora n\u00e3o nativa": SECONDARY,
    "N\u00e3o migradora nativa": GREEN,
    "N\u00e3o migradora n\u00e3o nativa": ORANGE,
    "Nativa": PRIMARY,
    "N\u00e3o nativa": SECONDARY,
}
SPECIES_CLASS_ORDER = ["MN", "MNN", "NMN", "NMNN"]
SPECIES_CLASS_LABELS = {
    "MN": "Migradora nativa",
    "MNN": "Migradora n\u00e3o nativa",
    "NMN": "N\u00e3o migradora nativa",
    "NMNN": "N\u00e3o migradora n\u00e3o nativa",
}
SPECIES_CLASS_COLORS = {
    "MN": "#00441B",
    "MNN": "#67000D",
    "NMN": "#41AB5D",
    "NMNN": "#EF6548",
}
SPECIES_CLASS_CODES = {
    ("Migradora", "Nativa"): "MN",
    ("Migradora", "N\u00e3o nativa"): "MNN",
    ("N\u00e3o migradora", "Nativa"): "NMN",
    ("N\u00e3o migradora", "N\u00e3o nativa"): "NMNN",
}
EMG_COLORS = {
    "F1": "#DBE5F1",
    "F2": "#9DC3E6",
    "F3": "#5B9BD5",
    "F4": "#002060",
}
EMG_LABELS = {
    "F1": "F1 - Repouso",
    "F2": "F2 - Matura\u00e7\u00e3o inicial",
    "F3": "F3 - Maduro",
    "F4": "F4 - Desovado",
}
BETA_BLUE_COLORS = {
    "Beta_Sorensen": PRIMARY,
    "Turnover_BetaSim": SECONDARY,
    "Nestedness_BetaNes": "#9DC3E6",
}
BETA_LABELS = {
    "Beta_Sorensen": "\u03b2-S\u00f8rensen (\u03b2-sor)",
    "Turnover_BetaSim": "Turnover (\u03b2-sim)",
    "Nestedness_BetaNes": "Nestedness (\u03b2-nes)",
}
THREAT_EXCLUDE_PORTO_ESTRELA = {"Lophiosilurus alexandri"}


def _clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _norm_ascii(value: object) -> str:
    txt = _clean_text(value).lower()
    replacements = {
        "ã": "a",
        "á": "a",
        "â": "a",
        "à": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
        "?": "a",
        "Ã£": "a",
        "Ã©": "e",
        "Ã§": "c",
    }
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt


def _class_migration(value: object) -> str:
    txt = _norm_ascii(value)
    if "migradora" not in txt and "migrador" not in txt:
        return _clean_text(value).replace("N?o", "Não").replace("Nao", "Não")
    if txt.startswith("nao") or "nao migr" in txt:
        return "Não migradora"
    return "Migradora"


def _class_origin(value: object) -> str:
    txt = _norm_ascii(value)
    if "nativa" not in txt:
        return _clean_text(value).replace("N?o", "Não").replace("Nao", "Não")
    if txt.startswith("nao") or "nao nativa" in txt:
        return "Não nativa"
    return "Nativa"


def _class_yes_no(value: object) -> str:
    txt = _norm_ascii(value)
    if txt in {"sim", "s", "true", "1"}:
        return "Sim"
    return "Não"


def _status_label(value: object) -> str:
    txt = _clean_text(value)
    if not txt or _norm_ascii(txt) in {"na", "n.a.", "nan", "none", "nao"}:
        return "N.A."
    return txt.replace("N?o", "Não").replace("Nao", "Não")


def _ah_sort_value(value: object) -> int:
    match = re.search(r"AH(\d{4})", _clean_text(value))
    return int(match.group(1)) if match else 999999


def _ah_label(value: object) -> str:
    match = re.search(r"AH(\d{4})", _clean_text(value))
    if not match:
        return _clean_text(value)
    code = match.group(1)
    return f"{code[:2]}-{code[2:]}"


def _configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": FONT_BASE,
            "axes.labelsize": FONT_AXIS,
            "axes.titlesize": FONT_PANEL,
            "xtick.labelsize": FONT_TICK,
            "ytick.labelsize": FONT_TICK,
            "legend.fontsize": FONT_LEGEND,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _style_axes(ax, grid_axis: str = "y") -> None:
    ax.grid(False)
    ax.grid(axis=grid_axis, color=GRID, alpha=0.25, linewidth=1)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(EDGE)
        spine.set_linewidth(1.2)
    ax.tick_params(colors="black")


def _save_fig(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _save_fig_preserve_layout(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _write_xlsx(path: Path, sheets: dict[str, pd.DataFrame]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
            ws = writer.book[name[:31]]
            ws.freeze_panes = "A2"
            for col_cells in ws.columns:
                letter = col_cells[0].column_letter
                width = min(max(len(str(cell.value or "")) for cell in col_cells) + 2, 48)
                ws.column_dimensions[letter].width = width
    return path


def _shade_recent(ax: plt.Axes, positions: pd.Series | np.ndarray | list[float]) -> None:
    arr = np.sort(np.unique(np.asarray(list(positions), dtype=float)))
    if len(arr) < len(RECENT_AH):
        return
    left = (arr[-4] + arr[-3]) / 2 if len(arr) >= 4 else arr[-3] - (arr[-2] - arr[-3]) / 2
    right = arr[-1] + (arr[-1] - arr[-2]) / 2
    ax.axvspan(left, right, color=LIGHT, alpha=0.90, linewidth=0, zorder=0)


def _recent_patch() -> Patch:
    return Patch(facecolor=LIGHT, alpha=0.90, edgecolor="none", label="Anos hidrol\u00f3gicos recentes")


def _species_class_code(migration: object, origin: object) -> str:
    return SPECIES_CLASS_CODES.get((_class_migration(migration), _class_origin(origin)), "NI")


def _species_display_name(species: object, migration: object = "", origin: object = "") -> str:
    return str(species)


def _species_code_note(codes: pd.Series | list[str] | set[str]) -> str:
    ordered = [code for code in SPECIES_CLASS_ORDER if code in set(pd.Series(list(codes)).dropna().astype(str))]
    return " | ".join(f"{code} = {SPECIES_CLASS_LABELS[code]}" for code in ordered)


def _add_species_code_note(fig: plt.Figure, codes: pd.Series | list[str] | set[str]) -> None:
    note = _species_code_note(codes)
    if note:
        fig.text(0.5, 0.012, note, ha="center", va="bottom", fontsize=10.5, color="#333333")


def _species_class_legend_handles(codes: pd.Series | list[str] | set[str]) -> list[Line2D]:
    present = set(pd.Series(list(codes)).dropna().astype(str))
    return [
        Line2D(
            [0],
            [0],
            color=SPECIES_CLASS_COLORS[code],
            marker="s",
            linestyle="None",
            markersize=10,
            label=SPECIES_CLASS_LABELS[code],
        )
        for code in SPECIES_CLASS_ORDER
        if code in present
    ]


def _apply_species_tick_style(ax: plt.Axes, display: pd.DataFrame, others_label: str = OUTRAS_NATIVAS_LABEL) -> None:
    classes = display.get("Classe_Biologica", pd.Series([""] * len(display)))
    for tick, species, cls in zip(ax.get_yticklabels(), display["Nome_Cientifico"], classes, strict=False):
        is_other = str(species) == others_label or str(species).startswith("Outras esp\u00e9cies")
        tick.set_fontstyle("normal" if is_other else "italic")
        if str(cls) in SPECIES_CLASS_COLORS:
            tick.set_color(SPECIES_CLASS_COLORS[str(cls)])
            tick.set_fontweight("bold")


def _load_coordinates() -> pd.DataFrame:
    coords = pd.read_excel(MIGRATION_FILE, sheet_name="Pontos_e_Campanhas")
    coords = coords[["Ponto", "Latitude", "Longitude"]].dropna().drop_duplicates("Ponto")
    coords["Ponto"] = coords["Ponto"].astype(str).str.strip()
    coords["Latitude"] = pd.to_numeric(coords["Latitude"], errors="coerce")
    coords["Longitude"] = pd.to_numeric(coords["Longitude"], errors="coerce")
    for point, (lat, lon) in COORDINATE_OVERRIDES.items():
        mask = coords["Ponto"].eq(point)
        coords.loc[mask, "Latitude"] = lat
        coords.loc[mask, "Longitude"] = lon
    coords["Trecho"] = coords["Ponto"].map(POINT_TO_TRECHO)
    coords["Ordem_Espacial"] = coords["Ponto"].map({p: i + 1 for i, p in enumerate(POINT_ORDER_SPATIAL)})
    return coords.dropna(subset=["Latitude", "Longitude", "Ordem_Espacial"]).sort_values("Ordem_Espacial")


def _point_limits(df: pd.DataFrame) -> tuple[float, float, float, float]:
    xmin, xmax = float(df["Longitude"].min()), float(df["Longitude"].max())
    ymin, ymax = float(df["Latitude"].min()), float(df["Latitude"].max())
    dx = xmax - xmin
    dy = ymax - ymin
    return xmin - dx * 0.12, xmax + dx * 0.12, ymin - dy * 0.18, ymax + dy * 0.18


def _draw_point_path(ax: plt.Axes, coords: pd.DataFrame) -> None:
    ordered = coords.sort_values("Ordem_Espacial")
    offsets = {
        "P1": (28, 18),
        "P2": (-24, 19),
        "P3": (-38, -15),
        "P4": (-27, -11),
        "P5": (24, 18),
        "P6": (34, -20),
        "P7": (25, 14),
        "P8": (25, -18),
        "P9": (24, 20),
    }
    for trecho, color in TRECHO_MAP_COLORS.items():
        subset = ordered.loc[ordered["Trecho"].eq(trecho)]
        ax.plot(subset["Longitude"], subset["Latitude"], color=color, linewidth=2.4, alpha=0.62, zorder=1)
    for _, row in ordered.iterrows():
        dx, dy = offsets.get(row["Ponto"], (6, 5))
        ax.annotate(
            row["Ponto"],
            (row["Longitude"], row["Latitude"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=10.5,
            weight="bold",
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "alpha": 0.78, "edgecolor": "none"},
            arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.75, "alpha": 0.72, "shrinkA": 0, "shrinkB": 3},
            zorder=7,
        )


def _draw_spatial_pie_panel(
    ax: plt.Axes,
    group_point: pd.DataFrame,
    point_total: pd.DataFrame,
    group_order: list[str],
    colors: dict[str, str],
) -> None:
    coords = point_total.sort_values("Ordem_Espacial").copy()
    _draw_point_path(ax, coords)
    vmax = max(float(point_total["CPUEn"].max()), 1.0)
    x_span = float(coords["Longitude"].max() - coords["Longitude"].min())
    y_span = float(coords["Latitude"].max() - coords["Latitude"].min())
    base_radius = min(x_span, y_span) * 0.035

    for _, point in coords.iterrows():
        subset = group_point.loc[group_point["Ponto"].eq(point["Ponto"])].set_index("Categoria")
        values = np.array([subset["CPUEn"].get(group, 0.0) for group in group_order], dtype=float)
        total = values.sum()
        radius = base_radius * (0.50 + 1.50 * math.sqrt(total / vmax)) if total > 0 else base_radius * 0.45
        if total <= 0:
            ax.add_patch(Wedge((point["Longitude"], point["Latitude"]), radius, 0, 360, facecolor="#E5E9F0", edgecolor=EDGE, linewidth=0.9))
            continue
        start = 90.0
        for group, value in zip(group_order, values, strict=False):
            if value <= 0:
                continue
            angle = 360.0 * value / total
            ax.add_patch(
                Wedge(
                    (point["Longitude"], point["Latitude"]),
                    radius,
                    start,
                    start + angle,
                    facecolor=colors.get(group, GREY),
                    edgecolor=EDGE,
                    linewidth=0.6,
                    alpha=0.88,
                    zorder=3,
                )
            )
            start += angle

    xmin, xmax, ymin, ymax = _point_limits(coords)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("N")
    _style_axes(ax, grid_axis="both")


def _plot_spatial_pie_map(
    group_point: pd.DataFrame,
    point_total: pd.DataFrame,
    group_order: list[str],
    colors: dict[str, str],
    path: Path,
    legend_labels: dict[str, str] | None = None,
    italic_legend: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    _draw_spatial_pie_panel(ax, group_point, point_total, group_order, colors)
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=colors.get(group, GREY),
            markeredgecolor=EDGE,
            markersize=12,
            label=(legend_labels or {}).get(group, group),
        )
        for group in group_order
    ]
    trecho_handles = [
        Line2D([0], [0], color=TRECHO_MAP_COLORS["Montante"], linewidth=3, label="Montante"),
        Line2D([0], [0], color=TRECHO_MAP_COLORS["Jusante"], linewidth=3, label="Jusante"),
    ]
    group_legend = fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.965),
        ncol=min(len(handles), 4),
        frameon=False,
        columnspacing=1.2,
        handletextpad=0.45,
    )
    if italic_legend:
        for text in group_legend.get_texts():
            text.set_fontstyle("italic")
    fig.legend(handles=trecho_handles, loc="upper center", bbox_to_anchor=(0.5, 0.865), ncol=2, frameon=False, columnspacing=1.4, handlelength=2.6)
    fig.subplots_adjust(top=0.70, bottom=0.10)
    _save_fig_preserve_layout(fig, path)


def _block_dir(code: str, label: str) -> Path:
    # Os blocos continuam separados no codigo, mas os arquivos ficam juntos
    # para facilitar revisao visual e ajustes pontuais.
    return OUTPUT_DIR


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    valid = pd.DataFrame({"v": pd.to_numeric(values, errors="coerce"), "w": weights}).dropna()
    valid = valid.loc[valid["w"].gt(0)]
    if valid.empty:
        return np.nan
    return float(np.average(valid["v"], weights=valid["w"]))


def _regression(values: pd.Series) -> tuple[float, float, float]:
    y = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    x = np.arange(1, len(y) + 1, dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return np.nan, np.nan, np.nan
    slope, intercept = np.polyfit(x[ok], y[ok], 1)
    pred = slope * x[ok] + intercept
    ss_res = np.sum((y[ok] - pred) ** 2)
    ss_tot = np.sum((y[ok] - np.mean(y[ok])) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
    return float(intercept), float(slope), float(r2)


def _prepare_inputs() -> dict[str, pd.DataFrame]:
    if not BASE_FILE.exists():
        raise FileNotFoundError(BASE_FILE)
    if not CHAR_FILE.exists():
        raise FileNotFoundError(CHAR_FILE)

    base = pd.read_excel(BASE_FILE, sheet_name="Base_Linhas")
    char = pd.read_excel(CHAR_FILE, sheet_name="Caracterizacao_Especies")

    for col in ["Numero_de_Individuos", "Biomassa_g_linha", "CPUEn_linha", "CPUEb_linha", "CT_cm", "PC_g_individual"]:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce")
    base["Numero_de_Individuos"] = base["Numero_de_Individuos"].fillna(0)
    base["Captura_Real"] = base["Numero_de_Individuos"].gt(0)
    base["Migracao_Modelo"] = base["Migradora_Nao_Migradora"].map(_class_migration)
    base["Origem_Modelo"] = base["Nativa_Nao_Nativa"].map(_class_origin)
    base["Ameaca_Modelo"] = base["Ameacada_Extincao"].map(_class_yes_no)
    base["Rotulo_AH"] = base["ano_hidrologico"].map(_ah_label)
    base["Ordem_AH"] = base["ano_hidrologico"].map(_ah_sort_value)

    char["Migracao_Modelo"] = char["Migradora_Nao_Migradora"].map(_class_migration)
    char["Origem_Modelo"] = char["Nativa_Nao_Nativa"].map(_class_origin)
    char["Ameaca_Modelo"] = char["Ameacada_Extincao"].map(_class_yes_no)
    char["Interesse_Comercial_Modelo"] = char["Valor_Economico"].map(_class_yes_no)
    for col in ["Status_Ameaca_Estadual", "Status_Ameaca_Nacional", "Status_Ameaca_Global"]:
        char[col] = char[col].map(_status_label)

    return {"base": base, "char": char}


def _ah_labels(base: pd.DataFrame) -> list[str]:
    return (
        base[["ano_hidrologico", "Rotulo_AH", "Ordem_AH"]]
        .drop_duplicates()
        .sort_values("Ordem_AH")["Rotulo_AH"]
        .tolist()
    )


def _collector_curve(base: pd.DataFrame, n_perm: int = 300, seed: int = 42) -> pd.DataFrame:
    unit_cols = ["campanha_ordem", "Campanha", "Ponto", "Ordem_Global_Montante_Jusante"]
    pa = (
        base.loc[base["Captura_Real"], unit_cols + ["Nome_Cientifico"]]
        .drop_duplicates()
        .sort_values(["campanha_ordem", "Ordem_Global_Montante_Jusante", "Ponto"])
    )
    units = pa[unit_cols].drop_duplicates().reset_index(drop=True)
    species = sorted(pa["Nome_Cientifico"].dropna().astype(str).unique())
    matrix = (
        pa.assign(Presenca=1)
        .pivot_table(index=["Campanha", "Ponto"], columns="Nome_Cientifico", values="Presenca", aggfunc="max", fill_value=0)
        .reindex(pd.MultiIndex.from_frame(units[["Campanha", "Ponto"]]), fill_value=0)
        .reindex(columns=species, fill_value=0)
        .to_numpy(dtype=int)
    )

    rng = np.random.default_rng(seed)
    n_units = matrix.shape[0]
    richness = np.zeros((n_perm, n_units), dtype=float)
    jackknife = np.zeros((n_perm, n_units), dtype=float)

    for perm_idx in range(n_perm):
        order = rng.permutation(n_units)
        counts = np.zeros(matrix.shape[1], dtype=int)
        for step, unit_idx in enumerate(order, start=1):
            counts += matrix[unit_idx]
            s_obs = int((counts > 0).sum())
            q1 = int((counts == 1).sum())
            richness[perm_idx, step - 1] = s_obs
            jackknife[perm_idx, step - 1] = s_obs + ((step - 1) / step) * q1

    return pd.DataFrame(
        {
            "Unidade_Amostral": np.arange(1, n_units + 1),
            "Riqueza_Observada_Media": richness.mean(axis=0),
            "Riqueza_Observada_DP": richness.std(axis=0),
            "Jackknife1_Medio": jackknife.mean(axis=0),
            "Jackknife1_DP": jackknife.std(axis=0),
            "Permutacoes": n_perm,
            "Unidade": "Campanha x Ponto",
        }
    )


def _plot_collector(curve: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    x = curve["Unidade_Amostral"].to_numpy()
    y_obs = curve["Riqueza_Observada_Media"].to_numpy()
    sd_obs = curve["Riqueza_Observada_DP"].to_numpy()
    y_jack = curve["Jackknife1_Medio"].to_numpy()
    sd_jack = curve["Jackknife1_DP"].to_numpy()
    ax.plot(x, y_obs, color=PRIMARY, linewidth=3.0, label="Riqueza observada (média das aleatorizações)")
    ax.fill_between(x, y_obs - sd_obs, y_obs + sd_obs, color=PRIMARY, alpha=0.12, linewidth=0, label="±1 DP observado")
    ax.plot(x, y_jack, color=SECONDARY, linewidth=2.8, linestyle="--", label="Jackknife 1 (estimativa média)")
    ax.fill_between(x, y_jack - sd_jack, y_jack + sd_jack, color=SECONDARY, alpha=0.16, linewidth=0, label="±1 DP Jackknife 1")
    ax.set_xlabel("Unidades amostrais acumuladas (campanha x ponto)")
    ax.set_ylabel("Riqueza acumulada")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=2, frameon=False)
    _style_axes(ax)
    _save_fig(fig, path)


def _richness_by_ah(base: pd.DataFrame) -> pd.DataFrame:
    pa = base.loc[base["Captura_Real"]].copy()
    rows = []
    for ah, group in pa.groupby("ano_hidrologico"):
        rows.append(
            {
                "Ano_Hidrologico": ah,
                "Rotulo": _ah_label(ah),
                "Ordem_AH": _ah_sort_value(ah),
                "Riqueza_Total": group["Nome_Cientifico"].nunique(),
                "Riqueza_Nativa": group.loc[group["Origem_Modelo"].eq("Nativa"), "Nome_Cientifico"].nunique(),
                "Riqueza_Nao_Nativa": group.loc[group["Origem_Modelo"].eq("Não nativa"), "Nome_Cientifico"].nunique(),
            }
        )
    return pd.DataFrame(rows).sort_values("Ordem_AH")


def _plot_richness(richness: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    x = np.arange(len(richness))
    _shade_recent(ax, x)
    ax.plot(x, richness["Riqueza_Total"], color=PRIMARY, marker="o", linewidth=3, markersize=7, label="Total", zorder=3)
    ax.plot(x, richness["Riqueza_Nativa"], color=SECONDARY, marker="o", linewidth=2.8, markersize=7, label="Nativas", zorder=3)
    ax.plot(x, richness["Riqueza_Nao_Nativa"], color="#808080", marker="o", linewidth=2.8, markersize=7, label="Não nativas", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(richness["Rotulo"], rotation=45, ha="right")
    ax.set_xlabel("Ano hidrológico")
    ax.set_ylabel("Riqueza de espécies")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(_recent_patch())
    labels.append("Anos hidrológicos recentes")
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.11), ncol=4, frameon=False)
    _style_axes(ax)
    fig.subplots_adjust(top=0.86, bottom=0.17, left=0.07, right=0.98)
    _save_fig_preserve_layout(fig, path)


def _cpue_ah_trecho(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    df = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
        .sort_values(["Ordem_AH", "Trecho"])
    )
    return df


def _plot_cpue_series(df: pd.DataFrame, trecho: str, metric: str, path: Path) -> dict[str, float | str]:
    group = df.loc[df["Trecho"].eq(trecho)].sort_values("Ordem_AH").copy()
    labels = group["Rotulo_AH"].tolist()
    y = group[metric].reset_index(drop=True)
    x = np.arange(len(group))
    intercept, slope, r2 = _regression(y)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    color = PRIMARY if trecho == "Montante" else SECONDARY
    ax.plot(x, y, marker="o", color=color, linewidth=3, markersize=7)
    if np.isfinite(slope):
        ax.plot(x, slope * np.arange(1, len(y) + 1) + intercept, color="#808080", linestyle="--", linewidth=2.2)
    ax.text(
        0.50,
        0.92,
        f"{trecho} | R²={r2:.2f}" if np.isfinite(r2) else trecho,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=FONT_PANEL,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 2},
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("Ano hidrológico")
    ax.set_ylabel("CPUEn (ind/100m²)" if metric == "CPUEn" else "CPUEb (g/100m²)")
    _style_axes(ax)
    _save_fig(fig, path)

    return {"Trecho": trecho, "Metrica": metric, "Intercepto_a": intercept, "Coeficiente_b": slope, "R2": r2}


def _plot_cpue_panel(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True)
    specs = [
        ("Montante", "CPUEn", "CPUEn (ind/100m²)"),
        ("Montante", "CPUEb", "CPUEb (g/100m²)"),
        ("Jusante", "CPUEn", "CPUEn (ind/100m²)"),
        ("Jusante", "CPUEb", "CPUEb (g/100m²)"),
    ]
    labels = df.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo_AH"].tolist()
    x = np.arange(len(labels))
    rows = []
    for ax, (trecho, metric, ylabel) in zip(axes.ravel(), specs, strict=False):
        group = df.loc[df["Trecho"].eq(trecho)].sort_values("Ordem_AH")
        y = group[metric].reset_index(drop=True)
        intercept, slope, r2 = _regression(y)
        color = PRIMARY if trecho == "Montante" else SECONDARY
        ax.plot(x[: len(y)], y, marker="o", color=color, linewidth=3, markersize=7)
        if np.isfinite(slope):
            ax.plot(x[: len(y)], slope * np.arange(1, len(y) + 1) + intercept, color="#808080", linestyle="--", linewidth=2.2)
        ax.text(
            0.50,
            0.92,
            f"{trecho} | R²={r2:.2f}" if np.isfinite(r2) else trecho,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=FONT_PANEL,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 2},
        )
        ax.set_ylabel(ylabel)
        _style_axes(ax)
        rows.append({"Trecho": trecho, "Metrica": metric, "Intercepto_a": intercept, "Coeficiente_b": slope, "R2": r2})
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    _save_fig(fig, path)
    return pd.DataFrame(rows)


def _cpue_percent_groups(base: pd.DataFrame, subset: str = "all") -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    if subset == "migradoras":
        q = q.loc[q["Migracao_Modelo"].eq("Migradora")].copy()
        q["Grupo"] = q["Origem_Modelo"]
    else:
        q["Grupo"] = q["Migracao_Modelo"] + " | " + q["Origem_Modelo"]

    agg = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Grupo"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )
    for metric in ["CPUEn", "CPUEb"]:
        total = agg.groupby(["ano_hidrologico", "Trecho"])[metric].transform("sum")
        agg[f"{metric}_Percentual"] = np.where(total.gt(0), agg[metric] / total * 100, 0)
    return agg.sort_values(["Ordem_AH", "Trecho", "Grupo"])


def _plot_percent_panel(df: pd.DataFrame, path: Path, title: str | None = None) -> None:
    labels = df.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo_AH"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True, sharey=True)
    specs = [
        ("Montante", "CPUEn_Percentual", "CPUEn"),
        ("Montante", "CPUEb_Percentual", "CPUEb"),
        ("Jusante", "CPUEn_Percentual", "CPUEn"),
        ("Jusante", "CPUEb_Percentual", "CPUEb"),
    ]
    handles = []
    legend_labels = []
    for ax, (trecho, metric, metric_label) in zip(axes.ravel(), specs, strict=False):
        group = df.loc[df["Trecho"].eq(trecho)].copy()
        pivot = (
            group.pivot_table(index="Rotulo_AH", columns="Grupo", values=metric, aggfunc="sum", fill_value=0)
            .reindex(labels)
            .fillna(0)
        )
        groups = pivot.columns.tolist()
        stack = ax.stackplot(x, [pivot[col].values for col in groups], labels=groups, colors=PALETTE[: len(groups)], alpha=0.95)
        handles, legend_labels = stack, groups
        ax.set_ylim(0, 100)
        ax.set_title(f"{trecho} | {metric_label}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel(f"{metric_label} (%)")
        _style_axes(ax)
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    if title:
        fig.suptitle(title, fontsize=FONT_BASE + 1, fontweight="bold", y=1.04)
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=min(4, max(1, len(legend_labels))), frameon=False)
    _save_fig(fig, path)


def _native_species_percent(base: pd.DataFrame, recent_only: bool) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa") & base["Origem_Modelo"].eq("Nativa")].copy()
    if recent_only:
        q = q.loc[q["ano_hidrologico"].isin(RECENT_AH)].copy()
    agg = (
        q.groupby(["Trecho", "Nome_Cientifico", "Migracao_Modelo", "Origem_Modelo"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )
    agg["Classe_Biologica"] = [
        _species_class_code(migration, origin)
        for migration, origin in zip(agg["Migracao_Modelo"], agg["Origem_Modelo"], strict=False)
    ]
    agg["Nome_Exibicao"] = [
        _species_display_name(name, migration, origin)
        for name, migration, origin in zip(agg["Nome_Cientifico"], agg["Migracao_Modelo"], agg["Origem_Modelo"], strict=False)
    ]
    rows = []
    for metric in ["CPUEn", "CPUEb"]:
        for trecho, group in agg.groupby("Trecho"):
            total = group[metric].sum()
            tmp = group[
                [
                    "Trecho",
                    "Nome_Cientifico",
                    "Migracao_Modelo",
                    "Origem_Modelo",
                    "Classe_Biologica",
                    "Nome_Exibicao",
                    metric,
                ]
            ].copy()
            tmp["Metrica"] = metric
            tmp["Valor_Absoluto"] = tmp[metric]
            tmp["Percentual"] = np.where(total > 0, tmp[metric] / total * 100, 0)
            tmp["Recorte"] = "AH2324-AH2526" if recent_only else "Período completo"
            rows.append(
                tmp[
                    [
                        "Recorte",
                        "Trecho",
                        "Metrica",
                        "Nome_Cientifico",
                        "Migracao_Modelo",
                        "Origem_Modelo",
                        "Classe_Biologica",
                        "Nome_Exibicao",
                        "Valor_Absoluto",
                        "Percentual",
                    ]
                ]
            )
    return pd.concat(rows, ignore_index=True).sort_values(["Trecho", "Metrica", "Percentual"], ascending=[True, True, False])


def _top_with_others(group: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    ordered = group.sort_values("Percentual", ascending=False).copy()
    top = ordered.head(top_n).copy()
    rest = ordered.iloc[top_n:]
    if not rest.empty and rest["Percentual"].sum() > 0:
        top = pd.concat(
            [
                top,
                pd.DataFrame(
                    [
                        {
                            "Recorte": ordered["Recorte"].iloc[0],
                            "Trecho": ordered["Trecho"].iloc[0],
                            "Metrica": ordered["Metrica"].iloc[0],
                            "Nome_Cientifico": OUTRAS_NATIVAS_LABEL,
                            "Migracao_Modelo": "",
                            "Origem_Modelo": "Nativa",
                            "Classe_Biologica": "",
                            "Nome_Exibicao": OUTRAS_NATIVAS_LABEL,
                            "Valor_Absoluto": rest["Valor_Absoluto"].sum(),
                            "Percentual": rest["Percentual"].sum(),
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return top.sort_values("Percentual", ascending=True).reset_index(drop=True)


def _plot_lollipop_panel(native: pd.DataFrame, path: Path, title: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL)
    specs = [
        ("Montante", "CPUEn"),
        ("Montante", "CPUEb"),
        ("Jusante", "CPUEn"),
        ("Jusante", "CPUEb"),
    ]
    colors = {"CPUEn": PRIMARY, "CPUEb": SECONDARY}
    for ax, (trecho, metric) in zip(axes.ravel(), specs, strict=False):
        group = native.loc[native["Trecho"].eq(trecho) & native["Metrica"].eq(metric)].copy()
        display = _top_with_others(group, top_n=8)
        y = np.arange(len(display))
        ax.hlines(y, 0, display["Percentual"], color="#D9D9D9", linewidth=2.4)
        ax.scatter(display["Percentual"], y, s=140, color=colors[metric], edgecolor=EDGE, linewidth=1.1, zorder=3)
        for yi, value in zip(y, display["Percentual"], strict=False):
            ax.text(value + 0.8, yi, f"{value:.1f}%", va="center", ha="left", fontsize=12)
        ax.set_yticks(y)
        labels = display["Nome_Exibicao"] if "Nome_Exibicao" in display else display["Nome_Cientifico"]
        ax.set_yticklabels(labels, fontstyle="italic", fontsize=12)
        for tick, species, cls in zip(
            ax.get_yticklabels(),
            display["Nome_Cientifico"],
            display.get("Classe_Biologica", pd.Series([""] * len(display))),
            strict=False,
        ):
            tick.set_fontstyle("normal" if str(species).startswith("Outras espécies") else "italic")
            if str(cls) in SPECIES_CLASS_COLORS:
                tick.set_color(SPECIES_CLASS_COLORS[str(cls)])
        ax.set_xlabel(f"{metric} (%)")
        ax.set_title(f"{trecho} | {metric}", loc="center", fontweight="bold", pad=10)
        ax.set_xlim(0, max(5, min(100, display["Percentual"].max() * 1.25)))
        _style_axes(ax, grid_axis="x")
        _apply_species_tick_style(ax, display)
    fig.suptitle(title, fontsize=FONT_BASE + 1, fontweight="bold", y=1.01)
    if "Classe_Biologica" in native:
        handles = _species_class_legend_handles(native["Classe_Biologica"])
        if handles:
            legend = fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.045), ncol=len(handles), frameon=False)
            for text in legend.get_texts():
                text.set_fontweight("bold")
    _save_fig(fig, path)


def _native_butterfly_data(
    native: pd.DataFrame,
    top_n: int = 10,
    others_label: str = OUTRAS_NATIVAS_LABEL,
    include_others: bool = True,
) -> pd.DataFrame:
    rows = []
    for metric in ["CPUEn", "CPUEb"]:
        metric_group = native.loc[native["Metrica"].eq(metric)].copy()
        if metric_group.empty:
            continue
        totals = (
            metric_group.groupby(
                ["Nome_Cientifico", "Migracao_Modelo", "Origem_Modelo", "Classe_Biologica", "Nome_Exibicao"],
                as_index=False,
            )["Valor_Absoluto"]
            .sum()
            .sort_values("Valor_Absoluto", ascending=False)
        )
        top_species = totals.head(top_n)["Nome_Cientifico"].tolist()
        display_species = top_species + ([others_label] if include_others else [])

        for order, species in enumerate(display_species, start=1):
            if species == others_label:
                subset = metric_group.loc[~metric_group["Nome_Cientifico"].isin(top_species)].copy()
            else:
                subset = metric_group.loc[metric_group["Nome_Cientifico"].eq(species)].copy()
            if subset.empty and (not include_others or species != others_label):
                continue

            by_trecho = (
                subset.groupby("Trecho", as_index=False)
                .agg(Valor_Absoluto=("Valor_Absoluto", "sum"), Percentual=("Percentual", "sum"))
                .set_index("Trecho")
            )
            if species == others_label:
                migration = ""
                origin = ""
                cls = ""
                display_name = others_label
            else:
                first = subset.iloc[0]
                migration = first.get("Migracao_Modelo", "")
                origin = first.get("Origem_Modelo", "")
                cls = first.get("Classe_Biologica", _species_class_code(migration, origin))
                display_name = first.get("Nome_Exibicao", _species_display_name(species, migration, origin))
            rows.append(
                {
                    "Recorte": metric_group["Recorte"].iloc[0] if not metric_group.empty else "AH2324-AH2526",
                    "Metrica": metric,
                    "Ordem_Exibicao": order,
                    "Nome_Cientifico": species,
                    "Migracao_Modelo": migration,
                    "Origem_Modelo": origin,
                    "Classe_Biologica": cls,
                    "Nome_Exibicao": display_name,
                    "Valor_Montante": float(by_trecho["Valor_Absoluto"].get("Montante", 0.0)),
                    "Percentual_Montante": float(by_trecho["Percentual"].get("Montante", 0.0)),
                    "Valor_Jusante": float(by_trecho["Valor_Absoluto"].get("Jusante", 0.0)),
                    "Percentual_Jusante": float(by_trecho["Percentual"].get("Jusante", 0.0)),
                }
            )
    return pd.DataFrame(rows)


def _plot_native_butterfly(butterfly: pd.DataFrame, path: Path, others_label: str = OUTRAS_NATIVAS_LABEL) -> None:
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_PANEL, sharex=False)
    colors = {"Montante": PRIMARY, "Jusante": SECONDARY}
    metric_labels = {
        "CPUEn": "CPUEn",
        "CPUEb": "CPUEb",
    }

    for ax, metric in zip(axes, ["CPUEn", "CPUEb"], strict=False):
        display = butterfly.loc[butterfly["Metrica"].eq(metric)].sort_values("Ordem_Exibicao").copy()
        y = np.arange(len(display))
        montante = display["Percentual_Montante"].to_numpy(dtype=float)
        jusante = display["Percentual_Jusante"].to_numpy(dtype=float)
        max_value = max(float(np.nanmax(np.r_[montante, jusante])), 1.0)
        limit = min(100.0, max(5.0, math.ceil(max_value * 1.18 / 5) * 5))

        ax.barh(y, -montante, color=colors["Montante"], edgecolor=EDGE, linewidth=0.4, height=0.68, label="Montante")
        ax.barh(y, jusante, color=colors["Jusante"], edgecolor=EDGE, linewidth=0.4, height=0.68, label="Jusante")
        ax.axvline(0, color=EDGE, linewidth=1.2)

        for yi, left, right in zip(y, montante, jusante, strict=False):
            ax.text(-left - limit * 0.018, yi, f"{left:.1f}%", va="center", ha="right", fontsize=12)
            ax.text(right + limit * 0.018, yi, f"{right:.1f}%", va="center", ha="left", fontsize=12)

        ax.set_yticks(y)
        labels = display["Nome_Exibicao"] if "Nome_Exibicao" in display else display["Nome_Cientifico"]
        ax.set_yticklabels(labels, fontsize=12)
        for tick, species, cls in zip(
            ax.get_yticklabels(),
            display["Nome_Cientifico"],
            display.get("Classe_Biologica", pd.Series([""] * len(display))),
            strict=False,
        ):
            tick.set_fontstyle("normal" if str(species) == others_label or str(species).startswith("Outras espécies") else "italic")
            if str(cls) in SPECIES_CLASS_COLORS:
                tick.set_color(SPECIES_CLASS_COLORS[str(cls)])

        ax.invert_yaxis()
        ax.set_xlim(-limit, limit)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{abs(value):.0f}%"))
        ax.set_xlabel("Percentual da CPUE no trecho (%)")
        ax.text(0.01, 0.94, metric_labels[metric], transform=ax.transAxes, ha="left", va="top", fontsize=FONT_PANEL, color=PRIMARY, weight="bold")
        ax.text(0.23, 1.02, "Montante", transform=ax.transAxes, ha="center", va="bottom", fontsize=FONT_LEGEND, color=PRIMARY, weight="bold")
        ax.text(0.77, 1.02, "Jusante", transform=ax.transAxes, ha="center", va="bottom", fontsize=FONT_LEGEND, color=SECONDARY, weight="bold")
        _style_axes(ax, grid_axis="x")
        _apply_species_tick_style(ax, display, others_label=others_label)

    if "Classe_Biologica" in butterfly:
        handles = _species_class_legend_handles(butterfly["Classe_Biologica"])
        if handles:
            legend = fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.015), ncol=len(handles), frameon=False)
            for text in legend.get_texts():
                text.set_fontweight("bold")
    _save_fig(fig, path)


def _species_percent(base: pd.DataFrame, filter_mode: str = "all", recent_only: bool = False) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    if recent_only:
        q = q.loc[q["ano_hidrologico"].isin(RECENT_AH)].copy()
    if filter_mode == "nativas":
        q = q.loc[q["Origem_Modelo"].eq("Nativa")].copy()
    elif filter_mode == "migradoras":
        q = q.loc[q["Migracao_Modelo"].eq("Migradora")].copy()
    elif filter_mode == "ameacadas":
        q = q.loc[q["Ameaca_Modelo"].eq("Sim") & ~q["Nome_Cientifico"].isin(THREAT_EXCLUDE_PORTO_ESTRELA)].copy()

    agg = (
        q.groupby(["Trecho", "Nome_Cientifico", "Migracao_Modelo", "Origem_Modelo"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )
    agg["Classe_Biologica"] = [
        _species_class_code(migration, origin)
        for migration, origin in zip(agg["Migracao_Modelo"], agg["Origem_Modelo"], strict=False)
    ]
    agg["Nome_Exibicao"] = [
        _species_display_name(name, migration, origin)
        for name, migration, origin in zip(agg["Nome_Cientifico"], agg["Migracao_Modelo"], agg["Origem_Modelo"], strict=False)
    ]
    rows = []
    for metric in ["CPUEn", "CPUEb"]:
        for trecho, group in agg.groupby("Trecho"):
            total = group[metric].sum()
            tmp = group[
                [
                    "Trecho",
                    "Nome_Cientifico",
                    "Migracao_Modelo",
                    "Origem_Modelo",
                    "Classe_Biologica",
                    "Nome_Exibicao",
                    metric,
                ]
            ].copy()
            tmp["Metrica"] = metric
            tmp["Valor_Absoluto"] = tmp[metric]
            tmp["Percentual"] = np.where(total > 0, tmp[metric] / total * 100, 0)
            tmp["Recorte"] = "AH2324-AH2526" if recent_only else "Periodo completo"
            rows.append(
                tmp[
                    [
                        "Recorte",
                        "Trecho",
                        "Metrica",
                        "Nome_Cientifico",
                        "Migracao_Modelo",
                        "Origem_Modelo",
                        "Classe_Biologica",
                        "Nome_Exibicao",
                        "Valor_Absoluto",
                        "Percentual",
                    ]
                ]
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "Recorte",
                "Trecho",
                "Metrica",
                "Nome_Cientifico",
                "Migracao_Modelo",
                "Origem_Modelo",
                "Classe_Biologica",
                "Nome_Exibicao",
                "Valor_Absoluto",
                "Percentual",
            ]
        )
    return pd.concat(rows, ignore_index=True).sort_values(["Trecho", "Metrica", "Percentual"], ascending=[True, True, False])


def _mig_origin_label(migration: object, origin: object) -> str:
    mig = _class_migration(migration)
    ori = _class_origin(origin)
    return f"{mig} {ori.lower()}"


def _category_series(base: pd.DataFrame, mode: str) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    if mode == "mig_origin":
        q["Categoria"] = [_mig_origin_label(m, o) for m, o in zip(q["Migradora_Nao_Migradora"], q["Nativa_Nao_Nativa"], strict=False)]
        order = GROUP_ORDER_MIG_ORIGIN
    elif mode == "origin":
        q["Categoria"] = q["Origem_Modelo"]
        order = ["Nativa", "N\u00e3o nativa"]
    elif mode == "migradoras":
        q = q.loc[q["Migracao_Modelo"].eq("Migradora")].copy()
        q["Categoria"] = ["Migradora " + str(o).lower() for o in q["Origem_Modelo"]]
        order = ["Migradora nativa", "Migradora n\u00e3o nativa"]
    elif mode == "ameacadas":
        q = q.loc[q["Ameaca_Modelo"].eq("Sim") & ~q["Nome_Cientifico"].isin(THREAT_EXCLUDE_PORTO_ESTRELA)].copy()
        q["Categoria"] = q["Nome_Cientifico"]
        order = q.groupby("Categoria")["CPUEn_linha"].sum().sort_values(ascending=False).index.tolist()
    else:
        raise ValueError(f"Modo desconhecido: {mode}")

    agg = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Categoria"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
    )
    agg["Ordem_Categoria"] = agg["Categoria"].map({cat: i for i, cat in enumerate(order)})
    return agg.sort_values(["Ordem_Categoria", "Trecho", "Ordem_AH"])


def _fit_piecewise(x: np.ndarray, y: np.ndarray, min_size: int = 5) -> dict[str, float | bool]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x = x[ok]
    y = y[ok]
    n = len(y)
    if n < min_size * 2 + 1 or np.allclose(y, y[0]):
        return {"Breakpoint_X": np.nan, "Delta_BIC": np.nan, "Melhora_Forte": False}

    x0 = x - x.min()
    linear_design = np.column_stack([np.ones(n), x0])
    coef_lin, *_ = np.linalg.lstsq(linear_design, y, rcond=None)
    resid_lin = y - linear_design @ coef_lin
    sse_lin = float(np.sum(resid_lin**2))
    bic_lin = n * np.log(max(sse_lin / n, 1e-12)) + 2 * np.log(n)

    best: tuple[float, float] | None = None
    for bp in x0[min_size:-min_size]:
        hinge = np.maximum(0, x0 - bp)
        design = np.column_stack([np.ones(n), x0, hinge])
        coef, *_ = np.linalg.lstsq(design, y, rcond=None)
        resid = y - design @ coef
        sse = float(np.sum(resid**2))
        bic = n * np.log(max(sse / n, 1e-12)) + 3 * np.log(n)
        if best is None or bic < best[0]:
            best = (bic, float(bp + x.min()))
    if best is None:
        return {"Breakpoint_X": np.nan, "Delta_BIC": np.nan, "Melhora_Forte": False}
    delta_bic = bic_lin - best[0]
    return {"Breakpoint_X": best[1], "Delta_BIC": float(delta_bic), "Melhora_Forte": bool(delta_bic > 2)}


def _category_inflexions(series: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (trecho, category, metric), group in series.melt(
        id_vars=["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Categoria"],
        value_vars=["CPUEn", "CPUEb"],
        var_name="Metrica",
        value_name="Valor",
    ).groupby(["Trecho", "Categoria", "Metrica"]):
        group = group.sort_values("Ordem_AH")
        fit = _fit_piecewise(group["Ordem_AH"].to_numpy(), group["Valor"].to_numpy())
        bp_label = None
        if pd.notna(fit["Breakpoint_X"]):
            nearest = group.iloc[(group["Ordem_AH"] - float(fit["Breakpoint_X"])).abs().argsort().iloc[0]]
            bp_label = nearest["ano_hidrologico"]
        rows.append(
            {
                "Trecho": trecho,
                "Categoria": category,
                "Metrica": metric,
                "Breakpoint_Ordem_AH": fit["Breakpoint_X"],
                "Breakpoint_AH": bp_label,
                "Delta_BIC": fit["Delta_BIC"],
                "Melhora_Forte": fit["Melhora_Forte"],
            }
        )
    return pd.DataFrame(rows).sort_values(["Metrica", "Trecho", "Categoria"])


def _ols_fit(x: np.ndarray, y: np.ndarray) -> dict[str, np.ndarray | float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ coef
    resid = y - pred
    sse = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = float(1 - sse / ss_tot) if ss_tot > 0 else np.nan
    return {"coef": coef, "pred": pred, "resid": resid, "sse": sse, "r2": r2}


def _segmented_fit_for_break(x: np.ndarray, y: np.ndarray, bp: float) -> dict[str, np.ndarray | float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    hinge = np.maximum(0, x - bp)
    design = np.column_stack([np.ones(len(x)), x, hinge])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ coef
    resid = y - pred
    sse = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = float(1 - sse / ss_tot) if ss_tot > 0 else np.nan
    return {"coef": coef, "pred": pred, "resid": resid, "sse": sse, "r2": r2}


def _best_segmented_fit(x: np.ndarray, y: np.ndarray, min_size: int = 5) -> dict[str, object]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    null = _ols_fit(x, y)
    n = len(y)
    if n < min_size * 2 + 1 or np.allclose(y, y[0]):
        return {"ok": False, "null": null}

    candidates = x[min_size:-min_size]
    best: dict[str, object] | None = None
    for bp in candidates:
        fit = _segmented_fit_for_break(x, y, float(bp))
        sse = float(fit["sse"])
        if best is None or sse < float(best["fit"]["sse"]):  # type: ignore[index]
            best = {"bp": float(bp), "fit": fit}
    if best is None:
        return {"ok": False, "null": null}

    sse_null = float(null["sse"])
    sse_seg = float(best["fit"]["sse"])  # type: ignore[index]
    df_num = 1
    df_den = max(n - 3, 1)
    f_sup = ((sse_null - sse_seg) / df_num) / max(sse_seg / df_den, 1e-12)
    bic_null = n * np.log(max(sse_null / n, 1e-12)) + 2 * np.log(n)
    bic_seg = n * np.log(max(sse_seg / n, 1e-12)) + 3 * np.log(n)
    return {
        "ok": True,
        "bp": best["bp"],
        "fit": best["fit"],
        "null": null,
        "f_sup": float(f_sup),
        "delta_bic": float(bic_null - bic_seg),
    }


def _bh_adjust(p_values: list[float]) -> list[float]:
    p = np.asarray(p_values, dtype=float)
    out = np.full(len(p), np.nan, dtype=float)
    ok = np.isfinite(p)
    if ok.sum() == 0:
        return out.tolist()
    idx = np.where(ok)[0]
    order = idx[np.argsort(p[idx])]
    ranked = p[order]
    m = len(ranked)
    adjusted = ranked * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    out[order] = np.clip(adjusted, 0, 1)
    return out.tolist()


def _breakpoint_permutation_test(
    x: np.ndarray,
    y: np.ndarray,
    min_size: int = 5,
    n_perm: int = 999,
    n_boot: int = 499,
    seed: int = 20260603,
) -> dict[str, object]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x = x[ok]
    y = y[ok]
    n = len(y)
    best = _best_segmented_fit(x, y, min_size=min_size)
    if not best.get("ok", False):
        return {"ok": False, "n": n}

    rng = np.random.default_rng(seed)
    null = best["null"]  # type: ignore[index]
    fitted_null = np.asarray(null["pred"], dtype=float)  # type: ignore[index]
    resid_null = np.asarray(null["resid"], dtype=float)  # type: ignore[index]
    obs_f = float(best["f_sup"])
    perm_stats = np.zeros(n_perm, dtype=float)
    for i in range(n_perm):
        y_perm = fitted_null + rng.permutation(resid_null)
        perm_fit = _best_segmented_fit(x, y_perm, min_size=min_size)
        perm_stats[i] = float(perm_fit.get("f_sup", 0.0)) if perm_fit.get("ok", False) else 0.0
    p_perm = float((np.sum(perm_stats >= obs_f) + 1) / (n_perm + 1))

    fit = best["fit"]  # type: ignore[index]
    fitted_seg = np.asarray(fit["pred"], dtype=float)  # type: ignore[index]
    resid_seg = np.asarray(fit["resid"], dtype=float)  # type: ignore[index]
    boot_bp: list[float] = []
    for _ in range(n_boot):
        y_boot = fitted_seg + rng.choice(resid_seg, size=len(resid_seg), replace=True)
        boot_fit = _best_segmented_fit(x, y_boot, min_size=min_size)
        if boot_fit.get("ok", False):
            boot_bp.append(float(boot_fit["bp"]))
    bp_ci_low = float(np.percentile(boot_bp, 2.5)) if boot_bp else np.nan
    bp_ci_high = float(np.percentile(boot_bp, 97.5)) if boot_bp else np.nan

    null_coef = np.asarray(null["coef"], dtype=float)  # type: ignore[index]
    seg_coef = np.asarray(fit["coef"], dtype=float)  # type: ignore[index]
    return {
        "ok": True,
        "n": n,
        "Breakpoint_Ordem_AH": float(best["bp"]),
        "Breakpoint_CI95_Low_Ordem_AH": bp_ci_low,
        "Breakpoint_CI95_High_Ordem_AH": bp_ci_high,
        "F_sup": obs_f,
        "p_perm": p_perm,
        "Delta_BIC": float(best["delta_bic"]),
        "SSE_Linear": float(null["sse"]),  # type: ignore[index]
        "SSE_Segmentado": float(fit["sse"]),  # type: ignore[index]
        "R2_Linear": float(null["r2"]),  # type: ignore[index]
        "R2_Segmentado": float(fit["r2"]),  # type: ignore[index]
        "Slope_Linear": float(null_coef[1]),
        "Slope_Pre": float(seg_coef[1]),
        "Slope_Post": float(seg_coef[1] + seg_coef[2]),
        "Delta_Slope": float(seg_coef[2]),
        "Permutacoes": n_perm,
        "Bootstraps_IC": len(boot_bp),
    }


def _breakpoint_tests_for_series(
    series: pd.DataFrame,
    metric: str = "CPUEb",
    min_size: int = 5,
    n_perm: int = 999,
    n_boot: int = 499,
    seed: int = 20260603,
) -> pd.DataFrame:
    rows = []
    for i, ((category, trecho), group) in enumerate(series.groupby(["Categoria", "Trecho"])):
        group = group.sort_values("Ordem_AH")
        result = _breakpoint_permutation_test(
            group["Ordem_AH"].to_numpy(dtype=float),
            group[metric].to_numpy(dtype=float),
            min_size=min_size,
            n_perm=n_perm,
            n_boot=n_boot,
            seed=seed + i * 101,
        )
        row = {"Categoria": category, "Trecho": trecho, "Metrica": metric, **result}
        if result.get("ok", False):
            bp = float(result["Breakpoint_Ordem_AH"])
            low = float(result.get("Breakpoint_CI95_Low_Ordem_AH", np.nan))
            high = float(result.get("Breakpoint_CI95_High_Ordem_AH", np.nan))
            nearest = group.iloc[(group["Ordem_AH"] - bp).abs().argsort().iloc[0]]
            row["Breakpoint_AH"] = nearest["ano_hidrologico"]
            if np.isfinite(low):
                row["Breakpoint_CI95_Low_AH"] = group.iloc[(group["Ordem_AH"] - low).abs().argsort().iloc[0]]["ano_hidrologico"]
            if np.isfinite(high):
                row["Breakpoint_CI95_High_AH"] = group.iloc[(group["Ordem_AH"] - high).abs().argsort().iloc[0]]["ano_hidrologico"]
        rows.append(row)
    out = pd.DataFrame(rows)
    out["p_BH"] = _bh_adjust(out["p_perm"].astype(float).tolist()) if "p_perm" in out else np.nan
    out["Significativo_BH_0_05"] = np.where(out["p_BH"].le(0.05), "Sim", "N\u00e3o")
    out["Decisao"] = np.where(
        out["Significativo_BH_0_05"].eq("Sim"),
        "Ponto de inflex\u00e3o significativo",
        "Ponto de inflex\u00e3o n\u00e3o suportado",
    )
    return out.sort_values(["Categoria", "Trecho"])


def _plot_category_temporal(series: pd.DataFrame, infl: pd.DataFrame, metric: str, path: Path, category_order: list[str] | None = None) -> None:
    if category_order is None:
        category_order = series.groupby("Categoria")[metric].sum().sort_values(ascending=False).index.tolist()
    categories = [cat for cat in category_order if cat in set(series["Categoria"])]
    n = max(len(categories), 1)
    ncols = 2 if n > 1 else 1
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 6.1 * nrows), sharex=True, squeeze=False)
    axes_flat = axes.ravel()
    labels = series.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")

    for ax, category in zip(axes_flat, categories, strict=False):
        subset = series.loc[series["Categoria"].eq(category)]
        for trecho in ["Montante", "Jusante"]:
            group = subset.loc[subset["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            if group.empty:
                continue
            ax.plot(group["Ordem_AH"], group[metric], color=TRECHO_LINE_COLORS[trecho], marker="o", linewidth=2.4, alpha=0.82, label=trecho)
            fit_row = infl.loc[(infl["Categoria"].eq(category)) & (infl["Trecho"].eq(trecho)) & (infl["Metrica"].eq(metric))]
            if not fit_row.empty and bool(fit_row.iloc[0]["Melhora_Forte"]):
                bp = float(fit_row.iloc[0]["Breakpoint_Ordem_AH"])
                ax.axvline(bp, color=TRECHO_LINE_COLORS[trecho], linestyle=":", linewidth=1.9, alpha=0.72)
                ax.text(
                    bp,
                    ax.get_ylim()[1],
                    str(fit_row.iloc[0]["Breakpoint_AH"]),
                    color=TRECHO_LINE_COLORS[trecho],
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=10,
                    bbox={"facecolor": "white", "alpha": 0.65, "edgecolor": "none", "pad": 1.0},
                )
        ax.set_title(category, color=PRIMARY)
        ax.set_ylabel(metric)
        _shade_recent(ax, labels["Ordem_AH"])
        _style_axes(ax)

    for ax in axes_flat[len(categories):]:
        ax.axis("off")
    for ax in axes_flat[: len(categories)]:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    for ax in axes[-1]:
        if ax.has_data():
            ax.set_xlabel("Ano hidrol\u00f3gico")
    handles = [
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Montante"], marker="o", linewidth=2.4, label="Montante"),
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Jusante"], marker="o", linewidth=2.4, label="Jusante"),
        Line2D([0], [0], color=GREY, linewidth=1.9, linestyle=":", label="Ponto de inflex\u00e3o forte"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3, frameon=False)
    fig.subplots_adjust(top=0.88 if nrows == 1 else 0.91, bottom=0.10, hspace=0.30, wspace=0.12)
    _save_fig_preserve_layout(fig, path)


def _plot_category_temporal_breaktest(
    series: pd.DataFrame,
    tests: pd.DataFrame,
    metric: str,
    path: Path,
    category_order: list[str] | None = None,
    italic_titles: bool = False,
) -> None:
    if category_order is None:
        category_order = series.groupby("Categoria")[metric].sum().sort_values(ascending=False).index.tolist()
    categories = [cat for cat in category_order if cat in set(series["Categoria"])]
    n = max(len(categories), 1)
    ncols = 2 if n > 1 else 1
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(18.5, 6.6 * nrows), sharex=True, squeeze=False)
    axes_flat = axes.ravel()
    labels = series.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")

    for ax, category in zip(axes_flat, categories, strict=False):
        subset = series.loc[series["Categoria"].eq(category)]
        for trecho in ["Montante", "Jusante"]:
            group = subset.loc[subset["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            if group.empty:
                continue
            color = TRECHO_LINE_COLORS[trecho]
            ax.plot(group["Ordem_AH"], group[metric], color=color, marker="o", linewidth=2.4, alpha=0.82, label=trecho)
            test_row = tests.loc[
                tests["Categoria"].eq(category)
                & tests["Trecho"].eq(trecho)
                & tests["Metrica"].eq(metric)
                & tests["Significativo_BH_0_05"].eq("Sim")
            ]
            if not test_row.empty:
                row = test_row.iloc[0]
                bp = float(row["Breakpoint_Ordem_AH"])
                ax.axvline(bp, color=color, linestyle=":", linewidth=2.2, alpha=0.88)
                label = f"{row['Breakpoint_AH']} | p={row['p_BH']:.3f}"
                ax.text(
                    bp,
                    ax.get_ylim()[1],
                    label,
                    color=color,
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=10,
                    bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "none", "pad": 1.0},
                )
        ax.set_title(category, color=PRIMARY, fontweight="bold", fontstyle="italic" if italic_titles else "normal", pad=16)
        _shade_recent(ax, labels["Ordem_AH"])
        _style_axes(ax)

    for ax in axes_flat[len(categories):]:
        ax.axis("off")
    for ax in axes_flat[: len(categories)]:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    for ax in axes[-1]:
        if ax.has_data():
            ax.set_xlabel("Ano hidrol\u00f3gico")
    fig.supylabel(metric, x=0.022, fontsize=FONT_AXIS)

    handles = [
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Montante"], marker="o", linewidth=2.4, label="Montante"),
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Jusante"], marker="o", linewidth=2.4, label="Jusante"),
        Line2D([0], [0], color=GREY, linewidth=2.2, linestyle=":", label="Ponto de inflex\u00e3o significativo (BH p\u22640,05)"),
        Patch(facecolor=LIGHT, alpha=0.90, edgecolor="none", label="Anos hidrol\u00f3gicos recentes"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.992), ncol=4, frameon=False)
    fig.subplots_adjust(
        top=0.76 if nrows == 1 else 0.86,
        bottom=0.19 if nrows == 1 else 0.11,
        left=0.07,
        right=0.985,
        hspace=0.38,
        wspace=0.24,
    )
    _save_fig_preserve_layout(fig, path)


def gerar_teste_secao_661_cpueb_quebra(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = OUTPUT_DIR
    base = ctx["base"]
    series = _category_series(base, "mig_origin")
    tests = _breakpoint_tests_for_series(series, metric="CPUEb", min_size=5, n_perm=999, n_boot=499)
    category_order = GROUP_ORDER_MIG_ORIGIN
    xlsx = _write_xlsx(
        folder / "teste_estatistico_661_cpue_todas_especies_cpueb_ponto_inflexao_dados.xlsx",
        {
            "Temporal_CPUEb": series,
            "Teste_Inflexao": tests,
            "Metodo": pd.DataFrame(
                [
                    {
                        "Item": "Modelo nulo",
                        "Descricao": "Regressao linear simples: CPUEb ~ ordem do ano hidrologico.",
                    },
                    {
                        "Item": "Modelo alternativo",
                        "Descricao": "Regressao segmentada com termo hinge e ponto de inflexao escolhido por menor SSE, com minimo de 5 anos por segmento.",
                    },
                    {
                        "Item": "Teste",
                        "Descricao": "Teste global por permutacao dos residuos sob o modelo linear nulo; estatistica F-sup sobre todos os pontos candidatos.",
                    },
                    {
                        "Item": "Multiplicidade",
                        "Descricao": "p-valores ajustados por Benjamini-Hochberg entre as series testadas.",
                    },
                    {
                        "Item": "Criterio grafico",
                        "Descricao": "A linha vertical do ponto de inflexao e exibida apenas quando p_BH <= 0,05.",
                    },
                ]
            ),
        },
    )
    png = folder / "teste_estatistico_661_cpue_todas_especies_cpueb_ponto_inflexao.png"
    _plot_category_temporal_breaktest(series, tests, "CPUEb", png, category_order=category_order)
    return [xlsx, png]


def _mad_scale(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad > 0:
        return 1.4826 * mad
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return std if std > 0 else np.nan


def _abrupt_events_for_series(
    series: pd.DataFrame,
    metric: str = "CPUEb",
    n_perm: int = 999,
    seed: int = 20260603,
) -> pd.DataFrame:
    rows = []
    for i, ((category, trecho), group) in enumerate(series.groupby(["Categoria", "Trecho"])):
        group = group.sort_values("Ordem_AH").reset_index(drop=True)
        y = group[metric].to_numpy(dtype=float)
        if len(y) < 4 or np.allclose(y, y[0]):
            continue
        delta = np.diff(y)
        scale = _mad_scale(delta)
        median_delta = float(np.median(delta))
        robust_z = (delta - median_delta) / scale if np.isfinite(scale) and scale > 0 else np.full_like(delta, np.nan, dtype=float)

        rng = np.random.default_rng(seed + i * 101)
        perm_abs = np.zeros((n_perm, len(delta)), dtype=float)
        for perm_idx in range(n_perm):
            perm_abs[perm_idx] = np.abs(np.diff(rng.permutation(y)))
        p_perm = [
            float((np.sum(perm_abs[:, j] >= abs(delta[j])) + 1) / (n_perm + 1))
            for j in range(len(delta))
        ]
        p_bh_series = _bh_adjust(p_perm)

        for j, (raw_p, adj_p) in enumerate(zip(p_perm, p_bh_series, strict=False), start=1):
            previous = group.iloc[j - 1]
            current = group.iloc[j]
            previous_value = float(previous[metric])
            current_value = float(current[metric])
            change = current_value - previous_value
            rows.append(
                {
                    "Categoria": category,
                    "Trecho": trecho,
                    "Metrica": metric,
                    "Ano_Hidrologico_Anterior": previous["ano_hidrologico"],
                    "Rotulo_AH_Anterior": previous["Rotulo_AH"],
                    "Ano_Hidrologico": current["ano_hidrologico"],
                    "Rotulo_AH": current["Rotulo_AH"],
                    "Ordem_AH": current["Ordem_AH"],
                    "Valor_Anterior": previous_value,
                    "Valor_Atual": current_value,
                    "Delta": change,
                    "Delta_Absoluto": abs(change),
                    "Delta_Percentual": (change / previous_value * 100) if previous_value > 0 else np.nan,
                    "Razao_Atual_Anterior": (current_value / previous_value) if previous_value > 0 else np.nan,
                    "Z_MAD_Delta": float(robust_z[j - 1]) if np.isfinite(robust_z[j - 1]) else np.nan,
                    "p_perm": raw_p,
                    "p_BH_serie": adj_p,
                    "Direcao": "Aumento abrupto" if change > 0 else "Queda abrupta",
                    "Evento_Significativo_Serie_0_05": "Sim" if adj_p <= 0.05 else "N\u00e3o",
                    "Permutacoes": n_perm,
                    "Metodo_p": "Permutacao da ordem temporal dentro da serie; p ajustado por BH dentro da serie.",
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_BH_global"] = _bh_adjust(out["p_perm"].astype(float).tolist())
    out["Evento_Significativo_Global_0_05"] = np.where(out["p_BH_global"].le(0.05), "Sim", "N\u00e3o")
    return out.sort_values(["Categoria", "Trecho", "Ordem_AH"])


def _plot_category_temporal_abrupt_events(
    series: pd.DataFrame,
    events: pd.DataFrame,
    metric: str,
    path: Path,
    category_order: list[str] | None = None,
) -> None:
    if category_order is None:
        category_order = series.groupby("Categoria")[metric].sum().sort_values(ascending=False).index.tolist()
    categories = [cat for cat in category_order if cat in set(series["Categoria"])]
    n = max(len(categories), 1)
    ncols = 2 if n > 1 else 1
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 6.1 * nrows), sharex=True, squeeze=False)
    axes_flat = axes.ravel()
    labels = series.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")

    for ax, category in zip(axes_flat, categories, strict=False):
        subset = series.loc[series["Categoria"].eq(category)]
        for trecho in ["Montante", "Jusante"]:
            group = subset.loc[subset["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            if group.empty:
                continue
            color = TRECHO_LINE_COLORS[trecho]
            ax.plot(group["Ordem_AH"], group[metric], color=color, marker="o", linewidth=2.4, alpha=0.82, label=trecho)
            marked = events.loc[
                events["Categoria"].eq(category)
                & events["Trecho"].eq(trecho)
                & events["Metrica"].eq(metric)
                & events["Evento_Significativo_Serie_0_05"].eq("Sim")
            ].copy()
            for _, event in marked.iterrows():
                marker = "^" if event["Delta"] > 0 else "v"
                ax.scatter(
                    event["Ordem_AH"],
                    event["Valor_Atual"],
                    marker=marker,
                    s=145,
                    color=color,
                    edgecolor=EDGE,
                    linewidth=0.8,
                    zorder=5,
                )
                ax.text(
                    event["Ordem_AH"],
                    event["Valor_Atual"],
                    f"p={event['p_BH_serie']:.3f}",
                    color=color,
                    fontsize=9,
                    ha="left",
                    va="bottom",
                    bbox={"facecolor": "white", "alpha": 0.70, "edgecolor": "none", "pad": 1.0},
                )
        ax.set_title(category, color=PRIMARY)
        ax.set_ylabel(metric)
        _shade_recent(ax, labels["Ordem_AH"])
        _style_axes(ax)

    for ax in axes_flat[len(categories):]:
        ax.axis("off")
    for ax in axes_flat[: len(categories)]:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    for ax in axes[-1]:
        if ax.has_data():
            ax.set_xlabel("Ano hidrol\u00f3gico")

    handles = [
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Montante"], marker="o", linewidth=2.4, label="Montante"),
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Jusante"], marker="o", linewidth=2.4, label="Jusante"),
        Line2D([0], [0], color=EDGE, marker="^", linestyle="None", markersize=9, label="Aumento abrupto significativo"),
        Line2D([0], [0], color=EDGE, marker="v", linestyle="None", markersize=9, label="Queda abrupta significativa"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=4, frameon=False)
    fig.subplots_adjust(top=0.91, bottom=0.10, hspace=0.30, wspace=0.12)
    _save_fig_preserve_layout(fig, path)


def _robust_alerts_from_events(events: pd.DataFrame, threshold: float = 3.0, strong_threshold: float = 3.5) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    alerts = events.copy()
    alerts["Z_MAD_Delta_Abs"] = alerts["Z_MAD_Delta"].abs()
    alerts["Alerta_Robusto_MAD"] = np.where(alerts["Z_MAD_Delta_Abs"].ge(threshold), "Sim", "N\u00e3o")
    alerts["Classe_Alerta_Robusto"] = np.select(
        [
            alerts["Z_MAD_Delta_Abs"].ge(strong_threshold),
            alerts["Z_MAD_Delta_Abs"].ge(threshold),
        ],
        [
            f"|Z_MAD| >= {strong_threshold:.1f}",
            f"{threshold:.1f} <= |Z_MAD| < {strong_threshold:.1f}",
        ],
        default="Sem alerta",
    )
    return alerts.sort_values(["Categoria", "Trecho", "Ordem_AH"])


def _plot_category_temporal_robust_alerts(
    series: pd.DataFrame,
    alerts: pd.DataFrame,
    metric: str,
    path: Path,
    category_order: list[str] | None = None,
) -> None:
    if category_order is None:
        category_order = series.groupby("Categoria")[metric].sum().sort_values(ascending=False).index.tolist()
    categories = [cat for cat in category_order if cat in set(series["Categoria"])]
    n = max(len(categories), 1)
    ncols = 2 if n > 1 else 1
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 6.1 * nrows), sharex=True, squeeze=False)
    axes_flat = axes.ravel()
    labels = series.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")

    for ax, category in zip(axes_flat, categories, strict=False):
        subset = series.loc[series["Categoria"].eq(category)]
        for trecho in ["Montante", "Jusante"]:
            group = subset.loc[subset["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            if group.empty:
                continue
            color = TRECHO_LINE_COLORS[trecho]
            ax.plot(group["Ordem_AH"], group[metric], color=color, marker="o", linewidth=2.4, alpha=0.82, label=trecho)
            marked = alerts.loc[
                alerts["Categoria"].eq(category)
                & alerts["Trecho"].eq(trecho)
                & alerts["Metrica"].eq(metric)
                & alerts["Alerta_Robusto_MAD"].eq("Sim")
            ].copy()
            for _, event in marked.iterrows():
                marker = "^" if event["Delta"] > 0 else "v"
                is_strong = event["Z_MAD_Delta_Abs"] >= 3.5
                ax.scatter(
                    event["Ordem_AH"],
                    event["Valor_Atual"],
                    marker=marker,
                    s=155 if is_strong else 125,
                    facecolor=color if is_strong else "white",
                    edgecolor=color,
                    linewidth=1.4,
                    zorder=5,
                )
                y_offset = 10 if event["Delta"] >= 0 else -14
                if is_strong:
                    ax.annotate(
                        f"{event['Ano_Hidrologico']}\nZ={event['Z_MAD_Delta_Abs']:.1f}",
                        (event["Ordem_AH"], event["Valor_Atual"]),
                        xytext=(6, y_offset),
                        textcoords="offset points",
                        color=color,
                        fontsize=8.8,
                        ha="left",
                        va="bottom" if y_offset > 0 else "top",
                        bbox={"facecolor": "white", "alpha": 0.76, "edgecolor": "none", "pad": 1.0},
                    )
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(ymin, ymax + (ymax - ymin) * 0.13)
        ax.set_title(category, color=PRIMARY)
        ax.set_ylabel(metric)
        _shade_recent(ax, labels["Ordem_AH"])
        _style_axes(ax)

    for ax in axes_flat[len(categories):]:
        ax.axis("off")
    for ax in axes_flat[: len(categories)]:
        ax.set_xticks(labels["Ordem_AH"])
        ax.set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    for ax in axes[-1]:
        if ax.has_data():
            ax.set_xlabel("Ano hidrol\u00f3gico")

    handles = [
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Montante"], marker="o", linewidth=2.4, label="Montante"),
        Line2D([0], [0], color=TRECHO_LINE_COLORS["Jusante"], marker="o", linewidth=2.4, label="Jusante"),
        Line2D([0], [0], color=EDGE, marker="^", linestyle="None", markersize=9, label="Alerta robusto |Z_MAD| \u2265 3,5"),
        Line2D(
            [0],
            [0],
            color=EDGE,
            marker="^",
            markerfacecolor="white",
            linestyle="None",
            markersize=9,
            label="Alerta robusto 3,0-3,5",
        ),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=4, frameon=False)
    fig.subplots_adjust(top=0.91, bottom=0.10, hspace=0.30, wspace=0.12)
    _save_fig_preserve_layout(fig, path)


def gerar_teste_secao_661_cpueb_eventos_abruptos(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = OUTPUT_DIR
    base = ctx["base"]
    series = _category_series(base, "mig_origin")
    events = _abrupt_events_for_series(series, metric="CPUEb", n_perm=999)
    xlsx = _write_xlsx(
        folder / "teste_estatistico_661_cpue_todas_especies_cpueb_eventos_abruptos_dados.xlsx",
        {
            "Temporal_CPUEb": series,
            "Eventos_Abruptos": events,
            "Eventos_Significativos": events.loc[events["Evento_Significativo_Serie_0_05"].eq("Sim")].copy(),
            "Metodo": pd.DataFrame(
                [
                    {
                        "Item": "Objeto do teste",
                        "Descricao": "Deteccao de eventos abruptos/pulsos em Delta CPUEb entre anos hidrologicos consecutivos.",
                    },
                    {
                        "Item": "Estatistica",
                        "Descricao": "Delta CPUEb ano-a-ano, com magnitude absoluta e z robusto por MAD.",
                    },
                    {
                        "Item": "p-valor",
                        "Descricao": "Permutacao da ordem temporal dentro de cada serie; compara o Delta absoluto observado com a distribuicao nula de deltas.",
                    },
                    {
                        "Item": "Multiplicidade",
                        "Descricao": "Benjamini-Hochberg aplicado dentro de cada serie temporal; p_BH_global tambem e fornecido como diagnostico conservador.",
                    },
                    {
                        "Item": "Criterio grafico",
                        "Descricao": "Marcadores triangulares aparecem quando p_BH_serie <= 0,05.",
                    },
                ]
            ),
        },
    )
    png = folder / "teste_estatistico_661_cpue_todas_especies_cpueb_eventos_abruptos.png"
    _plot_category_temporal_abrupt_events(series, events, "CPUEb", png, category_order=GROUP_ORDER_MIG_ORIGIN)
    return [xlsx, png]


def gerar_teste_secao_661_cpueb_alertas_robustos(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = OUTPUT_DIR
    base = ctx["base"]
    series = _category_series(base, "mig_origin")
    events = _abrupt_events_for_series(series, metric="CPUEb", n_perm=999)
    alerts = _robust_alerts_from_events(events, threshold=3.0, strong_threshold=3.5)
    alert_only = alerts.loc[alerts["Alerta_Robusto_MAD"].eq("Sim")].copy() if not alerts.empty else alerts.copy()
    xlsx = _write_xlsx(
        folder / "teste_estatistico_661_cpue_todas_especies_cpueb_alertas_robustos_mad_dados.xlsx",
        {
            "Temporal_CPUEb": series,
            "Eventos_Ano_Ano": alerts,
            "Alertas_Robustos": alert_only,
            "Metodo": pd.DataFrame(
                [
                    {
                        "Item": "Objeto",
                        "Descricao": "Triagem de pulsos abruptos em Delta CPUEb entre anos hidrologicos consecutivos.",
                    },
                    {
                        "Item": "Estatistica",
                        "Descricao": "Z robusto do Delta CPUEb calculado pela mediana e MAD da propria serie temporal.",
                    },
                    {
                        "Item": "Criterio principal",
                        "Descricao": "Alerta robusto quando |Z_MAD| >= 3,0; destaque maior quando |Z_MAD| >= 3,5.",
                    },
                    {
                        "Item": "Uso recomendado",
                        "Descricao": "Usar como triagem visual/diagnostica de pulsos; nao substituir o teste inferencial de quebra temporal por p-valor ajustado.",
                    },
                    {
                        "Item": "Controle inferencial",
                        "Descricao": "A planilha mantem p_perm, p_BH_serie e p_BH_global do teste por permutacao para comparacao com os alertas robustos.",
                    },
                ]
            ),
        },
    )
    png = folder / "teste_estatistico_661_cpue_todas_especies_cpueb_alertas_robustos_mad.png"
    _plot_category_temporal_robust_alerts(series, alerts, "CPUEb", png, category_order=GROUP_ORDER_MIG_ORIGIN)
    return [xlsx, png]


def _spatial_group_tables(base: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, str]]:
    coords = _load_coordinates()
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    if mode == "mig_origin":
        q["Categoria"] = [_mig_origin_label(m, o) for m, o in zip(q["Migradora_Nao_Migradora"], q["Nativa_Nao_Nativa"], strict=False)]
        order = GROUP_ORDER_MIG_ORIGIN
        colors = GROUP_COLORS
    elif mode == "origin":
        q["Categoria"] = q["Origem_Modelo"]
        order = ["Nativa", "N\u00e3o nativa"]
        colors = GROUP_COLORS
    elif mode == "migradoras":
        q = q.loc[q["Migracao_Modelo"].eq("Migradora")].copy()
        q["Categoria"] = ["Migradora " + str(o).lower() for o in q["Origem_Modelo"]]
        order = ["Migradora nativa", "Migradora n\u00e3o nativa"]
        colors = GROUP_COLORS
    elif mode == "ameacadas":
        q = q.loc[q["Ameaca_Modelo"].eq("Sim") & ~q["Nome_Cientifico"].isin(THREAT_EXCLUDE_PORTO_ESTRELA)].copy()
        q["Categoria"] = q["Nome_Cientifico"]
        order = q.groupby("Categoria")["CPUEn_linha"].sum().sort_values(ascending=False).index.tolist()
        colors = {cat: ALT_PALETTE[i % len(ALT_PALETTE)] for i, cat in enumerate(order)}
    else:
        raise ValueError(f"Modo desconhecido: {mode}")

    point_total = (
        q.groupby("Ponto", as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"), Abundancia=("Numero_de_Individuos", "sum"))
        .merge(coords, on="Ponto", how="right")
        .fillna({"CPUEn": 0, "CPUEb": 0, "Abundancia": 0})
        .sort_values("Ordem_Espacial")
    )
    group_point = (
        q.groupby(["Ponto", "Categoria"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"), Abundancia=("Numero_de_Individuos", "sum"))
        .merge(coords, on="Ponto", how="left")
    )
    return group_point, point_total, order, colors


def _threatened_cpue(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[
        base["Tipo_Amostragem_Base"].eq("Quantitativa")
        & base["Ameaca_Modelo"].eq("Sim")
    ].copy()
    return (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"), CPUEb=("CPUEb_linha", "sum"))
        .sort_values(["Ordem_AH", "Trecho", "Nome_Cientifico"])
    )


def _plot_species_stack(df: pd.DataFrame, path: Path, title: str) -> None:
    labels = df.drop_duplicates("ano_hidrologico").sort_values("Ordem_AH")["Rotulo_AH"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=FIGSIZE_PANEL, sharex=True)
    specs = [
        ("Montante", "CPUEn"),
        ("Montante", "CPUEb"),
        ("Jusante", "CPUEn"),
        ("Jusante", "CPUEb"),
    ]
    handles = []
    legend_labels = []
    for ax, (trecho, metric) in zip(axes.ravel(), specs, strict=False):
        group = df.loc[df["Trecho"].eq(trecho)]
        pivot = (
            group.pivot_table(index="Rotulo_AH", columns="Nome_Cientifico", values=metric, aggfunc="sum", fill_value=0)
            .reindex(labels)
            .fillna(0)
        )
        species = pivot.columns.tolist()
        stack = ax.stackplot(x, [pivot[col].values for col in species], labels=species, colors=ALT_PALETTE[: len(species)], alpha=0.90)
        handles, legend_labels = stack, species
        ax.set_title(f"{trecho} | {metric}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel("CPUEn (ind/100m²)" if metric == "CPUEn" else "CPUEb (g/100m²)")
        _style_axes(ax)
    for ax in axes[-1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_xlabel("Ano hidrológico")
    fig.suptitle(title, fontsize=FONT_BASE + 1, fontweight="bold", y=1.04)
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=min(4, max(1, len(legend_labels))), frameon=False)
    _save_fig(fig, path)


def _taxonomy_counts(char: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    species = char[["Nome_Cientifico", "Ordem", "Familia"]].drop_duplicates()
    order_counts = species.groupby("Ordem", dropna=False).size().reset_index(name="Especies")
    family_counts = species.groupby("Familia", dropna=False).size().reset_index(name="Especies")
    order_counts["Percentual"] = order_counts["Especies"] / order_counts["Especies"].sum() * 100
    family_counts["Percentual"] = family_counts["Especies"] / family_counts["Especies"].sum() * 100
    return order_counts.sort_values("Especies", ascending=False), family_counts.sort_values("Especies", ascending=False)


def _plot_donut(data: pd.DataFrame, category_col: str, path: Path, center_label: str) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    values = data["Especies"].to_numpy()
    labels = data[category_col].fillna("Não informado").astype(str).tolist()
    colors = [ALT_PALETTE[i % len(ALT_PALETTE)] for i in range(len(values))]
    wedges, _ = ax.pie(values, colors=colors, startangle=90, wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.2})
    ax.set_position([0.06, 0.08, 0.58, 0.84])
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.08, 0.5), frameon=False, fontsize=13)
    ax.text(0, 0, center_label, ha="center", va="center", fontsize=FONT_PANEL, color=PRIMARY, fontweight="bold")
    _save_fig(fig, path)


def _alpha_indices(values: pd.Series) -> dict[str, float]:
    x = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(dtype=float)
    x = x[x > 0]
    richness = int(len(x))
    total = float(x.sum())
    if richness == 0 or total <= 0:
        return {"Riqueza": 0, "Shannon": 0.0, "Pielou": 0.0}
    p = x / total
    shannon = float(-np.sum(p * np.log(p)))
    pielou = float(shannon / np.log(richness)) if richness > 1 else 0.0
    return {"Riqueza": richness, "Shannon": shannon, "Pielou": pielou}


def _diversity(base: pd.DataFrame) -> pd.DataFrame:
    q = base.loc[base["Tipo_Amostragem_Base"].eq("Quantitativa")].copy()
    agg = (
        q.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Nome_Cientifico"], as_index=False)
        .agg(CPUEn=("CPUEn_linha", "sum"))
    )
    rows = []
    for keys, group in agg.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho"]):
        ah, label, order, trecho = keys
        rows.append({"Ano_Hidrologico": ah, "Rotulo": label, "Ordem_AH": order, "Trecho": trecho, **_alpha_indices(group["CPUEn"])})
    return pd.DataFrame(rows).sort_values(["Ordem_AH", "Trecho"])


def _beta_components(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=bool)
    y = np.asarray(y, dtype=bool)
    shared = int(np.sum(x & y))
    only_x = int(np.sum(x & ~y))
    only_y = int(np.sum(~x & y))
    denom_sor = 2 * shared + only_x + only_y
    beta_sor = (only_x + only_y) / denom_sor if denom_sor else 0.0
    denom_sim = shared + min(only_x, only_y)
    beta_sim = min(only_x, only_y) / denom_sim if denom_sim else 0.0
    beta_nes = max(beta_sor - beta_sim, 0.0)
    return float(beta_sor), float(beta_sim), float(beta_nes)


def _beta_temporal_pa(base: pd.DataFrame) -> pd.DataFrame:
    pa = base.loc[base["Captura_Real"], ["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Nome_Cientifico"]].drop_duplicates()
    species = sorted(pa["Nome_Cientifico"].dropna().astype(str).unique())
    rows = []
    for trecho in ["Montante", "Jusante"]:
        subset = pa.loc[pa["Trecho"].eq(trecho)].copy()
        years = subset[["ano_hidrologico", "Rotulo_AH", "Ordem_AH"]].drop_duplicates().sort_values("Ordem_AH")
        matrix = (
            subset.assign(Presenca=1)
            .pivot_table(index="ano_hidrologico", columns="Nome_Cientifico", values="Presenca", aggfunc="max", fill_value=0)
            .reindex(years["ano_hidrologico"], fill_value=0)
            .reindex(columns=species, fill_value=0)
        )
        for i in range(1, len(years)):
            prev_year = years.iloc[i - 1]
            year = years.iloc[i]
            beta_sor, beta_sim, beta_nes = _beta_components(matrix.iloc[i - 1].to_numpy(), matrix.iloc[i].to_numpy())
            rows.append(
                {
                    "Trecho": trecho,
                    "Ano_Hidrologico_Anterior": prev_year["ano_hidrologico"],
                    "Ano_Hidrologico": year["ano_hidrologico"],
                    "Rotulo_AH": year["Rotulo_AH"],
                    "Ordem_AH": year["Ordem_AH"],
                    "Beta_Sorensen": beta_sor,
                    "Turnover_BetaSim": beta_sim,
                    "Nestedness_BetaNes": beta_nes,
                }
            )
    return pd.DataFrame(rows).sort_values(["Trecho", "Ordem_AH"])


def _plot_beta_pa_components_by_area(beta: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_PANEL, sharex=True)
    metrics = ["Beta_Sorensen", "Turnover_BetaSim", "Nestedness_BetaNes"]
    for idx, (ax, trecho) in enumerate(zip(axes, ["Montante", "Jusante"], strict=False)):
        subset = beta.loc[beta["Trecho"].eq(trecho)].sort_values("Ordem_AH")
        for metric in metrics:
            ax.plot(
                subset["Ordem_AH"],
                subset[metric],
                color=BETA_BLUE_COLORS[metric],
                marker="o",
                linewidth=2.8,
                alpha=0.86,
                label=BETA_LABELS[metric],
            )
        ax.text(0.012, 0.93, trecho, transform=ax.transAxes, ha="left", va="top", fontsize=FONT_PANEL, color=PRIMARY, weight="bold")
        ax.set_ylabel("Dissimilaridade")
        ax.set_ylim(0, 1.02)
        _shade_recent(ax, beta["Ordem_AH"].drop_duplicates())
        _style_axes(ax)
    labels = beta.drop_duplicates("Ordem_AH").sort_values("Ordem_AH")
    axes[-1].set_xlabel("Ano hidrol\u00f3gico")
    axes[-1].set_xticks(labels["Ordem_AH"])
    axes[-1].set_xticklabels(labels["Rotulo_AH"], rotation=45, ha="right")
    handles = [
        Line2D([0], [0], color=BETA_BLUE_COLORS[metric], marker="o", linewidth=2.8, label=BETA_LABELS[metric])
        for metric in metrics
    ]
    handles.append(_recent_patch())
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=4, frameon=False)
    fig.subplots_adjust(top=0.90, bottom=0.10, hspace=0.28)
    _save_fig_preserve_layout(fig, path)


def _plot_diversity(diversity: pd.DataFrame, path: Path) -> None:
    labels = diversity.drop_duplicates("Ano_Hidrologico").sort_values("Ordem_AH")["Rotulo"].tolist()
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_PANEL, sharex=True)
    colors = {"Montante": PRIMARY, "Jusante": SECONDARY}
    for ax, metric, ylabel in zip(axes, ["Shannon", "Pielou"], ["Shannon (H')", "Pielou (J')"], strict=False):
        _shade_recent(ax, x)
        for trecho in ["Montante", "Jusante"]:
            group = diversity.loc[diversity["Trecho"].eq(trecho)].sort_values("Ordem_AH")
            ax.plot(x[: len(group)], group[metric], marker="o", linewidth=3, markersize=7, color=colors[trecho], label=trecho)
        ax.set_ylabel(ylabel)
        _style_axes(ax)
    handles = [
        Line2D([0], [0], color=colors["Montante"], marker="o", linewidth=3, label="Montante"),
        Line2D([0], [0], color=colors["Jusante"], marker="o", linewidth=3, label="Jusante"),
        _recent_patch(),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=3, frameon=False)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=45, ha="right")
    axes[-1].set_xlabel("Ano hidrológico")
    fig.subplots_adjust(top=0.90, bottom=0.11, left=0.08, right=0.98, hspace=0.26)
    _save_fig_preserve_layout(fig, path)


def _reproduction_females(base: pd.DataFrame, origem: str | None = None) -> pd.DataFrame:
    df = base.loc[
        base["Sexo_Padronizado"].eq("Femea")
        & base["Migracao_Modelo"].eq("Migradora")
        & base["EMG_Codigo"].isin(["F1", "F2", "F3", "F4"])
    ].copy()
    if origem:
        df = df.loc[df["Origem_Modelo"].eq(origem)].copy()
    agg = (
        df.groupby(["ano_hidrologico", "Rotulo_AH", "Ordem_AH", "Trecho", "Origem_Modelo", "EMG_Codigo", "EMG_Estadio"], as_index=False)
        .agg(Abundancia=("Numero_de_Individuos", "sum"))
    )
    return agg.sort_values(["Origem_Modelo", "Trecho", "Ordem_AH", "EMG_Codigo"])


def _reproduction_relative(repro: pd.DataFrame) -> pd.DataFrame:
    out = repro.copy()
    total = out.groupby(["ano_hidrologico", "Trecho"])["Abundancia"].transform("sum")
    out["Abundancia_Relativa_Percentual"] = np.where(total.gt(0), out["Abundancia"] / total * 100, 0)
    return out


def _plot_reproduction(repro: pd.DataFrame, path: Path, origem: str, ah_labels: list[str]) -> None:
    x = np.arange(len(ah_labels))
    stage_order = ["F1", "F2", "F3", "F4"]
    colors = [EMG_COLORS[stage] for stage in stage_order]
    fig, axes = plt.subplots(2, 1, figsize=(18, 13.6), sharex=True, sharey=True)
    for idx, (ax, trecho) in enumerate(zip(axes, ["Montante", "Jusante"], strict=False)):
        pivot_abs = (
            repro.loc[repro["Trecho"].eq(trecho)]
            .pivot_table(index="Rotulo_AH", columns="EMG_Codigo", values="Abundancia", aggfunc="sum", fill_value=0)
            .reindex(ah_labels)
            .reindex(columns=stage_order, fill_value=0)
            .fillna(0)
        )
        totals = pivot_abs.sum(axis=1).replace(0, np.nan)
        pivot = pivot_abs.div(totals, axis=0).fillna(0) * 100
        bottom = np.zeros(len(pivot), dtype=float)
        for stage, color in zip(stage_order, colors, strict=False):
            values = pivot[stage].to_numpy(dtype=float)
            ax.bar(x, values, bottom=bottom, width=0.82, color=color, edgecolor=EDGE, linewidth=0.6, label=EMG_LABELS[stage])
            bottom += values
        origem_label = "nativas" if origem == "Nativa" else "não nativas"
        ax.set_title(f"Fêmeas migradoras {origem_label} | {trecho}", loc="center", fontweight="bold", pad=10)
        ax.set_ylabel("Abund\u00e2ncia relativa (%)")
        ax.set_ylim(0, 100)
        ax.set_xticks(x)
        ax.set_xticklabels(ah_labels, rotation=45, ha="right")
        if idx == len(axes) - 1:
            ax.set_xlabel("Ano hidrológico")
        _style_axes(ax)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=4, frameon=False)
    fig.subplots_adjust(top=0.90, bottom=0.12, left=0.075, right=0.985, hspace=0.32)
    _save_fig_preserve_layout(fig, path)


def _reproduction_emg_map_tables(base: pd.DataFrame, origem: str, coords: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = base.loc[
        base["Sexo_Padronizado"].eq("Femea")
        & base["Migracao_Modelo"].eq("Migradora")
        & base["Origem_Modelo"].eq(origem)
        & base["EMG_Codigo"].isin(["F1", "F2", "F3", "F4"])
    ].copy()
    group_point = (
        df.groupby(["Ponto", "EMG_Codigo"], as_index=False)
        .agg(Abundancia=("Numero_de_Individuos", "sum"))
        .rename(columns={"EMG_Codigo": "Categoria"})
        .merge(coords, on="Ponto", how="left")
    )
    point_total = (
        df.groupby("Ponto", as_index=False)
        .agg(Abundancia=("Numero_de_Individuos", "sum"))
        .merge(coords, on="Ponto", how="right")
        .fillna({"Abundancia": 0})
        .sort_values("Ordem_Espacial")
    )
    point_total["CPUEn"] = point_total["Abundancia"]
    group_point["CPUEn"] = group_point["Abundancia"]
    group_point["Origem_Modelo"] = origem
    point_total["Origem_Modelo"] = origem
    return group_point, point_total


def _plot_reproduction_emg_map(base: pd.DataFrame, path: Path) -> pd.DataFrame:
    coords = _load_coordinates()
    origins = [("Nativa", "Migradoras nativas"), ("Não nativa", "Migradoras não nativas")]
    stage_order = ["F1", "F2", "F3", "F4"]
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 10.6), sharex=False, sharey=False)
    outputs = []
    for ax, (origin, label) in zip(axes, origins, strict=False):
        group_point, point_total = _reproduction_emg_map_tables(base, origin, coords)
        _draw_spatial_pie_panel(ax, group_point, point_total, stage_order, EMG_COLORS)
        ax.set_title(label, loc="center", fontweight="bold", color=PRIMARY, pad=8)
        outputs.append(group_point)

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=EMG_COLORS[stage],
            markeredgecolor=EDGE,
            markersize=12,
            label=EMG_LABELS[stage],
        )
        for stage in stage_order
    ]
    trecho_handles = [
        Line2D([0], [0], color=TRECHO_MAP_COLORS["Montante"], linewidth=3, label="Montante"),
        Line2D([0], [0], color=TRECHO_MAP_COLORS["Jusante"], linewidth=3, label="Jusante"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=4, frameon=False, columnspacing=1.2, handletextpad=0.45)
    fig.legend(handles=trecho_handles, loc="upper center", bbox_to_anchor=(0.5, 0.945), ncol=2, frameon=False, columnspacing=1.4, handlelength=2.6)
    fig.subplots_adjust(top=0.82, bottom=0.08, left=0.085, right=0.98, hspace=0.36)
    _save_fig_preserve_layout(fig, path)
    return pd.concat(outputs, ignore_index=True).sort_values(["Origem_Modelo", "Ponto", "Categoria"])


def bloco_tabela_05(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    char = ctx["char"].copy()
    folder = _block_dir("05", "tabela_composicao_especies")
    out = char.sort_values(["Ordem", "Familia", "Nome_Cientifico"])[
        [
            "Ordem",
            "Familia",
            "Nome_Cientifico",
            "Autor_e_Ano",
            "Nome_Popular",
            "Origem_Modelo",
            "Status_Ameaca_Estadual",
            "Status_Ameaca_Nacional",
            "Status_Ameaca_Global",
        ]
    ].rename(
        columns={
            "Familia": "Família",
            "Nome_Cientifico": "Espécie",
            "Autor_e_Ano": "Autor",
            "Nome_Popular": "Nome popular",
            "Origem_Modelo": "Nativa/não nativa",
            "Status_Ameaca_Estadual": "Ameaça estadual",
            "Status_Ameaca_Nacional": "Ameaça federal",
            "Status_Ameaca_Global": "Ameaça mundial",
        }
    )
    path = _write_xlsx(folder / "tabela_05_composicao_especies.xlsx", {"Tabela 5": out})
    return [path]


def bloco_tabela_06(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"]
    char = ctx["char"].copy()
    folder = _block_dir("06", "tabela_caracteristicas_biologicas")
    occ = (
        base.loc[base["Captura_Real"]]
        .groupby(["Nome_Cientifico", "Trecho"], as_index=False)
        .size()
        .assign(Presenca="Presença")
        .pivot_table(index="Nome_Cientifico", columns="Trecho", values="Presenca", aggfunc="first", fill_value="Ausência")
        .reset_index()
    )
    for col in ["Jusante", "Montante"]:
        if col not in occ.columns:
            occ[col] = "Ausência"
    table = char.merge(occ[["Nome_Cientifico", "Jusante", "Montante"]], on="Nome_Cientifico", how="left")
    table[["Jusante", "Montante"]] = table[["Jusante", "Montante"]].fillna("Ausência")
    out = table.sort_values("Nome_Cientifico")[
        [
            "Nome_Cientifico",
            "Migracao_Modelo",
            "Origem_Modelo",
            "Ameaca_Modelo",
            "Interesse_Comercial_Modelo",
            "Jusante",
            "Montante",
        ]
    ].rename(
        columns={
            "Nome_Cientifico": "Espécie",
            "Migracao_Modelo": "Migração",
            "Origem_Modelo": "Distribuição",
            "Ameaca_Modelo": "Ameaçada de extinção",
            "Interesse_Comercial_Modelo": "Interesse Comercial",
        }
    )
    path = _write_xlsx(folder / "tabela_06_caracteristicas_biologicas.xlsx", {"Tabela 6": out})
    return [path]


def bloco_tabela_07(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"]
    folder = _block_dir("07", "tabela_ocorrencia")
    pa = base.loc[base["Captura_Real"], ["Nome_Cientifico", "Origem_Modelo", "Ponto"]].drop_duplicates()
    pivot = (
        pa.assign(Presenca="X")
        .pivot_table(index=["Nome_Cientifico", "Origem_Modelo"], columns="Ponto", values="Presenca", aggfunc="first", fill_value="-")
        .reset_index()
    )
    for point in POINT_ORDER_TABLE:
        if point not in pivot.columns:
            pivot[point] = "-"
    pivot["FA"] = pivot[POINT_ORDER_TABLE].eq("X").sum(axis=1)
    pivot["FR (%)"] = pivot["FA"] / len(POINT_ORDER_TABLE) * 100
    out = pivot[["Nome_Cientifico", "Origem_Modelo", *POINT_ORDER_TABLE, "FA", "FR (%)"]].rename(
        columns={"Nome_Cientifico": "Espécie", "Origem_Modelo": "Distribuição"}
    ).sort_values("Espécie")
    path = _write_xlsx(folder / "tabela_07_ocorrencia_fa_fr.xlsx", {"Tabela 7": out})
    return [path]


def bloco_tabela_08(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"].loc[ctx["base"]["Captura_Real"]].copy()
    folder = _block_dir("08", "tabela_biometria_biomassa")
    rows = []
    for species, group in base.groupby("Nome_Cientifico"):
        rows.append(
            {
                "Espécie": species,
                "N": group["Numero_de_Individuos"].sum(),
                "B": group["Biomassa_g_linha"].sum(),
                "CT_Min_cm": group["CT_cm"].min(),
                "CT_Med_cm": _weighted_mean(group["CT_cm"], group["Numero_de_Individuos"]),
                "CT_Max_cm": group["CT_cm"].max(),
                "PC_Min_g": group["PC_g_individual"].min(),
                "PC_Med_g": _weighted_mean(group["PC_g_individual"], group["Numero_de_Individuos"]),
                "PC_Max_g": group["PC_g_individual"].max(),
            }
        )
    out = pd.DataFrame(rows).sort_values("Espécie")
    path = _write_xlsx(folder / "tabela_08_biometria_biomassa.xlsx", {"Tabela 8": out})
    return [path]


def bloco_figura_10(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("10", "curva_coletor")
    curve = _collector_curve(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_10_curva_coletor_dados.xlsx", {"Curva": curve})
    png = folder / "figura_10_curva_coletor_observada_jackknife1.png"
    _plot_collector(curve, png)
    return [xlsx, png]


def bloco_figura_11(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("11", "rosca_ordem_familia")
    order_counts, family_counts = _taxonomy_counts(ctx["char"])
    xlsx = _write_xlsx(folder / "figura_11_ordem_familia_dados.xlsx", {"Ordem": order_counts, "Familia": family_counts})
    fig11a = folder / "figura_11a_percentual_ordem.png"
    fig11b = folder / "figura_11b_percentual_familia.png"
    _plot_donut(order_counts, "Ordem", fig11a, "Ordem")
    _plot_donut(family_counts.head(12), "Familia", fig11b, "Família")
    return [xlsx, fig11a, fig11b]


def bloco_figura_12(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("12", "riqueza_temporal")
    richness = _richness_by_ah(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_12_riqueza_temporal_dados.xlsx", {"Riqueza": richness})
    png = folder / "figura_12_riqueza_temporal_ano_hidrologico.png"
    _plot_richness(richness, png)
    return [xlsx, png]


def bloco_figura_13(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("13", "cpue_absoluta_regressao")
    df = _cpue_ah_trecho(ctx["base"])
    panel_png = folder / "figura_13_painel_cpue_regressao.png"
    regressions = _plot_cpue_panel(df, panel_png)
    files: list[Path] = [panel_png]
    specs = [
        ("13a", "Montante", "CPUEn"),
        ("13b", "Montante", "CPUEb"),
        ("13c", "Jusante", "CPUEn"),
        ("13d", "Jusante", "CPUEb"),
    ]
    reg_rows = regressions.to_dict("records")
    for code, trecho, metric in specs:
        path = folder / f"figura_{code}_{metric.lower()}_{trecho.lower()}_ano_hidrologico.png"
        reg_rows.append(_plot_cpue_series(df, trecho, metric, path))
        files.append(path)
    reg_df = pd.DataFrame(reg_rows).drop_duplicates(["Trecho", "Metrica"])
    xlsx = _write_xlsx(folder / "figura_13_cpue_regressao_dados.xlsx", {"CPUE": df, "Regressoes": reg_df})
    return [xlsx, *files]


def bloco_figura_14(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("14", "cpue_percentual_migracao_origem")
    df = _cpue_percent_groups(ctx["base"], subset="all")
    xlsx = _write_xlsx(folder / "figura_14_cpue_percentual_grupos_dados.xlsx", {"CPUE_percentual": df})
    png = folder / "figura_14_cpue_percentual_migracao_origem.png"
    _plot_percent_panel(df, png)
    return [xlsx, png]


def bloco_figura_15(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("15", "especies_nativas_periodo_completo")
    df = _native_species_percent(ctx["base"], recent_only=False)
    xlsx = _write_xlsx(folder / "figura_15_especies_nativas_periodo_completo_dados.xlsx", {"Nativas": df})
    png = folder / "figura_15_especies_nativas_periodo_completo.png"
    _plot_lollipop_panel(df, png, "Espécies nativas - período completo")
    return [xlsx, png]


def bloco_figura_16(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("16", "especies_nativas_recorte_atual")
    df = _native_species_percent(ctx["base"], recent_only=True)
    butterfly = _native_butterfly_data(df, top_n=10)
    xlsx = _write_xlsx(
        folder / "figura_16_especies_nativas_recorte_atual_dados.xlsx",
        {
            "Nativas_recorte": df,
            "Tornado_figura_16": butterfly,
        },
    )
    png = folder / "figura_16_especies_nativas_recorte_atual.png"
    _plot_native_butterfly(butterfly, png)
    return [xlsx, png]


def bloco_secao_663(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("663", "cpue_migradoras_nativas_nao_nativas")
    df = _cpue_percent_groups(ctx["base"], subset="migradoras")
    xlsx = _write_xlsx(folder / "secao_663_cpue_migradoras_dados.xlsx", {"Migradoras": df})
    png = folder / "secao_663_cpue_migradoras_nativas_nao_nativas.png"
    _plot_percent_panel(df, png, title="Espécies migradoras nativas e não nativas")
    return [xlsx, png]


def bloco_secao_664(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("664", "cpue_ameacadas")
    df = _threatened_cpue(ctx["base"])
    xlsx = _write_xlsx(folder / "secao_664_cpue_ameacadas_dados.xlsx", {"Ameacadas": df})
    png = folder / "secao_664_cpue_especies_ameacadas.png"
    _plot_species_stack(df, png, "Espécies ameaçadas de extinção")
    return [xlsx, png]


def _cpue_biological_block(
    ctx: dict[str, pd.DataFrame],
    code: str,
    slug: str,
    mode: str,
    species_filter: str,
    others_label: str,
    include_others: bool = True,
) -> list[Path]:
    folder = _block_dir(code, slug)
    base = ctx["base"]
    species = _species_percent(base, filter_mode=species_filter)
    butterfly = _native_butterfly_data(species, top_n=10, others_label=others_label, include_others=include_others)
    series = _category_series(base, mode)
    inflexion_cpuen = _breakpoint_tests_for_series(series, metric="CPUEn", min_size=5, n_perm=999, n_boot=499)
    inflexion_cpueb = _breakpoint_tests_for_series(series, metric="CPUEb", min_size=5, n_perm=999, n_boot=499)
    group_point, point_total, group_order, group_colors = _spatial_group_tables(base, mode)

    xlsx = _write_xlsx(
        folder / f"secao_{code}_{slug}_dados.xlsx",
        {
            "Especies_percentual": species,
            "Tornado": butterfly,
            "Temporal": series,
            "Ponto_Inflexao_CPUEn": inflexion_cpuen,
            "Ponto_Inflexao_CPUEb": inflexion_cpueb,
            "Espacial_grupos": group_point,
            "Espacial_pontos": point_total,
        },
    )
    tornado_png = folder / f"secao_{code}_{slug}_tornado_especies.png"
    temporal_cpuen_png = folder / f"secao_{code}_{slug}_temporal_cpuen.png"
    temporal_cpueb_png = folder / f"secao_{code}_{slug}_temporal_cpueb.png"
    spatial_png = folder / f"secao_{code}_{slug}_mapa_pizzas_cpuen.png"
    _plot_native_butterfly(butterfly, tornado_png, others_label=others_label)
    italic_species_labels = mode == "ameacadas"
    _plot_category_temporal_breaktest(
        series,
        inflexion_cpuen,
        "CPUEn",
        temporal_cpuen_png,
        category_order=group_order,
        italic_titles=italic_species_labels,
    )
    _plot_category_temporal_breaktest(
        series,
        inflexion_cpueb,
        "CPUEb",
        temporal_cpueb_png,
        category_order=group_order,
        italic_titles=italic_species_labels,
    )
    _plot_spatial_pie_map(group_point, point_total, group_order, group_colors, spatial_png, italic_legend=italic_species_labels)
    return [xlsx, tornado_png, temporal_cpuen_png, temporal_cpueb_png, spatial_png]


def bloco_secao_661(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    return _cpue_biological_block(ctx, "661", "cpue_todas_especies", "mig_origin", "all", OUTRAS_ESPECIES_LABEL)


def bloco_secao_662(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    return _cpue_biological_block(ctx, "662", "cpue_nativas_nao_nativas", "origin", "all", OUTRAS_ESPECIES_LABEL)


def bloco_secao_663(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    return _cpue_biological_block(ctx, "663", "cpue_migradoras_nativas_nao_nativas", "migradoras", "migradoras", "Outras esp\u00e9cies migradoras")


def bloco_secao_664(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    return _cpue_biological_block(
        ctx,
        "664",
        "cpue_ameacadas",
        "ameacadas",
        "ameacadas",
        "Outras esp\u00e9cies amea\u00e7adas",
        include_others=False,
    )


def bloco_figura_30(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("30", "diversidade_equitabilidade")
    df = _diversity(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_30_diversidade_equitabilidade_dados.xlsx", {"Diversidade": df})
    png = folder / "figura_30_diversidade_equitabilidade.png"
    _plot_diversity(df, png)
    return [xlsx, png]


def bloco_beta_temporal(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    folder = _block_dir("31", "diversidade_beta_temporal")
    beta = _beta_temporal_pa(ctx["base"])
    xlsx = _write_xlsx(folder / "figura_31_beta_temporal_pa_dados.xlsx", {"Beta_temporal_PA": beta})
    png = folder / "figura_31_beta_temporal_componentes_por_area.png"
    _plot_beta_pa_components_by_area(beta, png)
    return [xlsx, png]


def bloco_figuras_32_33(ctx: dict[str, pd.DataFrame]) -> list[Path]:
    base = ctx["base"]
    folder = _block_dir("32_33", "reproducao_femeas_migradoras")
    labels = _ah_labels(base)
    repro_all = _reproduction_females(base)
    repro_nat = _reproduction_females(base, origem="Nativa")
    repro_non = _reproduction_females(base, origem="Não nativa")
    fig34 = folder / "figura_34_mapa_pizzas_emg_femeas_migradoras.png"
    repro_map = _plot_reproduction_emg_map(base, fig34)
    xlsx = _write_xlsx(
        folder / "figuras_32_33_reproducao_femeas_migradoras_dados.xlsx",
        {
            "Todas": repro_all,
            "Nativas": repro_nat,
            "Nao_nativas": repro_non,
            "Todas_relativa": _reproduction_relative(repro_all),
            "Nativas_relativa": _reproduction_relative(repro_nat),
            "Nao_nativas_relativa": _reproduction_relative(repro_non),
            "Mapa_EMG": repro_map,
        },
    )
    fig32 = folder / "figura_32_emg_femeas_migradoras_nativas.png"
    fig33 = folder / "figura_33_emg_femeas_migradoras_nao_nativas.png"
    _plot_reproduction(repro_nat, fig32, "Nativa", labels)
    _plot_reproduction(repro_non, fig33, "Não nativa", labels)
    return [xlsx, fig32, fig33, fig34]


BLOCKS = {
    "05": ("Tabela 5 - composição de espécies", bloco_tabela_05),
    "06": ("Tabela 6 - características biológicas", bloco_tabela_06),
    "07": ("Tabela 7 - ocorrência FA/FR", bloco_tabela_07),
    "08": ("Tabela 8 - biometria e biomassa", bloco_tabela_08),
    "10": ("Figura 10 - curva do coletor", bloco_figura_10),
    "11": ("Figura 11 - roscas ordem/família", bloco_figura_11),
    "12": ("Figura 12 - riqueza temporal", bloco_figura_12),
    "13": ("Figura 13 - CPUE absoluta e regressão", bloco_figura_13),
    "14": ("Figura 14 - CPUE percentual por migração/origem", bloco_figura_14),
    "15": ("Figura 15 - espécies nativas período completo", bloco_figura_15),
    "16": ("Figura 16 - espécies nativas recorte atual", bloco_figura_16),
    "661": ("Seção 6.6.1 - todas as espécies", bloco_secao_661),
    "662": ("Seção 6.6.2 - nativas/não nativas", bloco_secao_662),
    "663": ("Seção 6.6.3 - migradoras nativas/não nativas", bloco_secao_663),
    "664": ("Seção 6.6.4 - ameaçadas", bloco_secao_664),
    "30": ("Figura 30 - diversidade e equitabilidade", bloco_figura_30),
    "31": ("Figura 31 - diversidade beta temporal", bloco_beta_temporal),
    "32_33": ("Figuras 32 e 33 - reprodução", bloco_figuras_32_33),
}

OFFICIAL_OUTPUTS_BY_BLOCK = {
    "05": ["tabela_05_composicao_especies.xlsx"],
    "06": ["tabela_06_caracteristicas_biologicas.xlsx"],
    "07": ["tabela_07_ocorrencia_fa_fr.xlsx"],
    "08": ["tabela_08_biometria_biomassa.xlsx"],
    "10": ["figura_10_curva_coletor_dados.xlsx", "figura_10_curva_coletor_observada_jackknife1.png"],
    "11": ["figura_11_ordem_familia_dados.xlsx", "figura_11a_percentual_ordem.png", "figura_11b_percentual_familia.png"],
    "12": ["figura_12_riqueza_temporal_dados.xlsx", "figura_12_riqueza_temporal_ano_hidrologico.png"],
    "13": [
        "figura_13_cpue_regressao_dados.xlsx",
        "figura_13_painel_cpue_regressao.png",
        "figura_13a_cpuen_montante_ano_hidrologico.png",
        "figura_13b_cpueb_montante_ano_hidrologico.png",
        "figura_13c_cpuen_jusante_ano_hidrologico.png",
        "figura_13d_cpueb_jusante_ano_hidrologico.png",
    ],
    "14": ["figura_14_cpue_percentual_grupos_dados.xlsx", "figura_14_cpue_percentual_migracao_origem.png"],
    "15": ["figura_15_especies_nativas_periodo_completo_dados.xlsx", "figura_15_especies_nativas_periodo_completo.png"],
    "16": ["figura_16_especies_nativas_recorte_atual_dados.xlsx", "figura_16_especies_nativas_recorte_atual.png"],
    "661": [
        "secao_661_cpue_todas_especies_dados.xlsx",
        "secao_661_cpue_todas_especies_tornado_especies.png",
        "secao_661_cpue_todas_especies_temporal_cpuen.png",
        "secao_661_cpue_todas_especies_temporal_cpueb.png",
        "secao_661_cpue_todas_especies_mapa_pizzas_cpuen.png",
    ],
    "662": [
        "secao_662_cpue_nativas_nao_nativas_dados.xlsx",
        "secao_662_cpue_nativas_nao_nativas_tornado_especies.png",
        "secao_662_cpue_nativas_nao_nativas_temporal_cpuen.png",
        "secao_662_cpue_nativas_nao_nativas_temporal_cpueb.png",
        "secao_662_cpue_nativas_nao_nativas_mapa_pizzas_cpuen.png",
    ],
    "663": [
        "secao_663_cpue_migradoras_nativas_nao_nativas_dados.xlsx",
        "secao_663_cpue_migradoras_nativas_nao_nativas_tornado_especies.png",
        "secao_663_cpue_migradoras_nativas_nao_nativas_temporal_cpuen.png",
        "secao_663_cpue_migradoras_nativas_nao_nativas_temporal_cpueb.png",
        "secao_663_cpue_migradoras_nativas_nao_nativas_mapa_pizzas_cpuen.png",
    ],
    "664": [
        "secao_664_cpue_ameacadas_dados.xlsx",
        "secao_664_cpue_ameacadas_tornado_especies.png",
        "secao_664_cpue_ameacadas_temporal_cpuen.png",
        "secao_664_cpue_ameacadas_temporal_cpueb.png",
        "secao_664_cpue_ameacadas_mapa_pizzas_cpuen.png",
    ],
    "30": ["figura_30_diversidade_equitabilidade_dados.xlsx", "figura_30_diversidade_equitabilidade.png"],
    "31": ["figura_31_beta_temporal_pa_dados.xlsx", "figura_31_beta_temporal_componentes_por_area.png"],
    "32_33": [
        "figuras_32_33_reproducao_femeas_migradoras_dados.xlsx",
        "figura_32_emg_femeas_migradoras_nativas.png",
        "figura_33_emg_femeas_migradoras_nao_nativas.png",
        "figura_34_mapa_pizzas_emg_femeas_migradoras.png",
    ],
}


def _parse_only(values: str | None) -> list[str]:
    if not values:
        return list(BLOCKS)

    raw_requested = [v.strip() for v in values.split(",") if v.strip()]
    requested = []
    for value in raw_requested:
        code = value
        if code not in BLOCKS and code.isdigit():
            code = code.zfill(2)
        requested.append(code)

    unknown = [raw for raw, code in zip(raw_requested, requested) if code not in BLOCKS]
    if unknown:
        raise ValueError(f"Blocos desconhecidos: {', '.join(unknown)}")
    return requested


def _official_manifest_results_if_complete() -> list[dict[str, object]] | None:
    results = []
    for code, filenames in OFFICIAL_OUTPUTS_BY_BLOCK.items():
        paths = [OUTPUT_DIR / filename for filename in filenames]
        if any(not path.exists() for path in paths):
            return None
        results.append({"code": code, "description": BLOCKS[code][0], "files": paths})
    return results


def _write_manifest(results: list[dict[str, object]]) -> Path:
    rows = []
    for item in results:
        for path in item["files"]:
            rows.append({"Bloco": item["code"], "Descricao": item["description"], "Arquivo": str(path)})
    df = pd.DataFrame(rows)
    xlsx = _write_xlsx(OUTPUT_DIR / "manifesto_resultados_ictiofauna_porto_estrela.xlsx", {"Manifesto": df})

    lines = [
        "# Porto Estrela - resultados ictiofauna",
        "",
        f"Gerado a partir de `{BASE_FILE.name}` e `{CHAR_FILE.name}`.",
        "",
        "## Blocos gerados",
        "",
    ]
    for item in results:
        lines.append(f"- {item['code']} - {item['description']}: {len(item['files'])} arquivo(s).")
    md = OUTPUT_DIR / "manifesto_resultados_ictiofauna_porto_estrela.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    return xlsx


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera resultados modulares de ictiofauna para Porto Estrela.")
    parser.add_argument("--only", help="Lista de blocos separados por virgula. Ex.: --only 10,13,14")
    parser.add_argument("--list-blocks", action="store_true", help="Lista os blocos disponiveis e encerra.")
    args = parser.parse_args()

    if args.list_blocks:
        for code, (description, _) in BLOCKS.items():
            print(f"{code}: {description}")
        return

    _configure_matplotlib()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = _prepare_inputs()
    selected = _parse_only(args.only)

    results = []
    for code in selected:
        description, fn = BLOCKS[code]
        print(f"[{code}] {description}")
        files = fn(ctx)
        results.append({"code": code, "description": description, "files": files})
        print(f"  {len(files)} arquivo(s) gerado(s)")

    manifest_results = _official_manifest_results_if_complete() or results
    manifest = _write_manifest(manifest_results)
    print(f"\nSaida: {OUTPUT_DIR}")
    print(f"Manifesto: {manifest}")


if __name__ == "__main__":
    main()
