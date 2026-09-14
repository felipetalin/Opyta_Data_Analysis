from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


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
OUTPUT_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "resultados" / "superficial" / "_teste_layout"
OUTPUT_PANEL_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "resultados" / "superficial" / "_teste_layout_paineis_campanha"

PARAMETERS = [
    "pH In Situ",
    "Oxig\u00eanio Dissolvido In Situ",
    "Ferro Dissolvido",
]

CAMPAIGN_LABELS = {
    "C001-2026-02-CH": "Campanha-01-Chuva",
    "C002-2026-06-SC": "Campanha-02-Seca",
}
CAMPAIGN_COLORS = {
    "C001-2026-02-CH": "#1B7F22",
    "C002-2026-06-SC": "#19FF19",
}
VMP_RED = "#F04438"
VIOLATION_SHADE = "#ffcccc"


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
    text = clean_text(value)
    text = text.replace("ę", "e").replace("Ę", "E")
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm(value: Any) -> str:
    text = fold(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fix_ptbr_label(value: str) -> str:
    replacements = {
        "ArsÄ™nio": "ArsÃªnio",
        "ManganÄ™s": "ManganÃªs",
        "NitrogÄ™nio": "NitrogÃªnio",
        "OxigÄ™nio": "OxigÃªnio",
        "Arsęnio": "Arsênio",
        "Manganęs": "Manganês",
        "Nitrogęnio": "Nitrogênio",
        "Oxigęnio": "Oxigênio",
        "Bioquimica": "BioquÃ­mica",
        "Quimica": "QuÃ­mica",
        "Solidos": "SÃ³lidos",
    }
    out = value
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def safe_filename(value: str) -> str:
    text = fold(value)
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "_", text).strip("_")


def load_surface() -> pd.DataFrame:
    df = pd.read_excel(CONSOLIDATED, sheet_name="fisico_analise_consolidada")
    surface = df[df["matriz"].astype(str).str.contains("Superficial", na=False)].copy()
    surface["valor_medido"] = pd.to_numeric(surface["valor_medido"], errors="coerce")
    for col in ["vmp_357_cl2_min", "vmp_357_cl2_max", "vmp_amonia_dinamico"]:
        if col in surface.columns:
            surface[col] = pd.to_numeric(surface[col], errors="coerce")
    surface["nome_parametro_norm"] = surface["nome_parametro"].map(norm)
    return surface


def find_parameter(surface: pd.DataFrame, target: str) -> str:
    target_norm = norm(target)
    matches = surface.loc[surface["nome_parametro_norm"].eq(target_norm), "nome_parametro"].dropna().unique()
    if len(matches):
        return str(matches[0])
    compact_target = target_norm.replace("oxigenio", "oxig nio").replace("nitrogenio", "nitrog nio")
    for value in surface["nome_parametro"].dropna().unique():
        if target_norm in norm(value) or compact_target in norm(value):
            return str(value)
    raise ValueError(f"Parametro nao encontrado: {target}")


def format_number(value: float) -> str:
    if pd.isna(value):
        return ""
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def vmp_legend_label(item: dict[str, Any]) -> str:
    kind_label = "mín" if item["kind"] == "min" else "máx"
    return f"VMP - Classe 2 ({kind_label}: {format_number(float(item['value']))})"


def ordered_legend_items(unique_legend: dict[str, Any]) -> tuple[list[Any], list[str]]:
    ordered_labels: list[str] = [
        label for label in CAMPAIGN_LABELS.values() if label in unique_legend
    ]
    ordered_labels.extend(
        label for label in unique_legend if label.startswith("VMP - Classe 2") and label not in ordered_labels
    )
    ordered_labels.extend(label for label in unique_legend if label not in ordered_labels)
    return [unique_legend[label] for label in ordered_labels], ordered_labels


def get_limits(df: pd.DataFrame) -> list[dict[str, Any]]:
    limits: list[dict[str, Any]] = []
    upper = df["vmp_357_cl2_max"].dropna()
    lower = df["vmp_357_cl2_min"].dropna()
    dynamic = df["vmp_amonia_dinamico"].dropna()
    if not upper.empty:
        value = float(upper.iloc[0])
        item = {"kind": "max", "value": value}
        item["label"] = vmp_legend_label(item)
        limits.append(item)
    if not lower.empty:
        value = float(lower.iloc[0])
        item = {"kind": "min", "value": value}
        item["label"] = vmp_legend_label(item)
        limits.append(item)
    if not dynamic.empty:
        value = float(dynamic.iloc[0])
        item = {"kind": "dynamic", "value": value}
        item["label"] = vmp_legend_label(item)
        limits.append(item)
    return limits


def point_order(points: list[str]) -> list[str]:
    def key(point: str) -> int:
        raw = point.split("_")[-1]
        return int(raw) if raw.isdigit() else 999

    return sorted(points, key=key)


def violates(value: float, sign: str, limits: list[dict[str, Any]]) -> bool:
    if pd.isna(value) or sign in {"<", "<="}:
        return False
    for item in limits:
        if item["kind"] in {"max", "dynamic"} and value > float(item["value"]):
            return True
        if item["kind"] == "min" and value < float(item["value"]):
            return True
    return False


def shade_violation(ax, limits: list[dict[str, Any]], y_min: float, y_max: float) -> None:
    lower_limits = [float(item["value"]) for item in limits if item["kind"] == "min"]
    upper_limits = [float(item["value"]) for item in limits if item["kind"] in {"max", "dynamic"}]
    if lower_limits:
        lower = max(lower_limits)
        ax.axhspan(y_min, lower, color=VMP_RED, alpha=0.08, zorder=0)
    if upper_limits:
        upper = min(upper_limits)
        ax.axhspan(upper, y_max, color=VMP_RED, alpha=0.07, zorder=0)


def plot_parameter(surface: pd.DataFrame, parameter: str) -> dict[str, Any]:
    source_param = find_parameter(surface, parameter)
    data = surface[surface["nome_parametro"].eq(source_param)].copy()
    data = data.sort_values(["nome_ponto", "nome_campanha"])
    points = point_order(data["nome_ponto"].dropna().unique().tolist())
    campaigns = [campaign for campaign in CAMPAIGN_LABELS if campaign in set(data["nome_campanha"])]
    unit = fix_ptbr_label(clean_text(data["unidade_medida"].dropna().iloc[0]) if not data["unidade_medida"].dropna().empty else "")
    display_param = fix_ptbr_label(parameter)

    pivot = data.pivot_table(index="nome_ponto", columns="nome_campanha", values="valor_medido", aggfunc="first").reindex(points)
    limits = get_limits(data)

    y_values = pivot.to_numpy(dtype=float)
    y_values = pivot.to_numpy(dtype=float)
    y_max = np.nanmax(y_values)
    y_min = np.nanmin(y_values)
    for item in limits:
        y_max = max(y_max, float(item["value"]))
        y_min = min(y_min, float(item["value"]))
    if display_param == "pH In Situ":
        global_y_min = max(0, y_min - 0.5)
        global_y_max = y_max + 0.5
    else:
        global_y_min = -0.02 * y_max if y_max else 0
        global_y_max = y_max * 1.22 if y_max else 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 9), dpi=600)
    x = np.arange(len(points), dtype=float)
    offsets = np.linspace(-0.14, 0.14, len(campaigns)) if len(campaigns) > 1 else [0]

    ax.set_ylim(global_y_min, global_y_max)
    lower_limits = [float(item["value"]) for item in limits if item["kind"] == "min"]
    upper_limits = [float(item["value"]) for item in limits if item["kind"] in {"max", "dynamic"}]
    if lower_limits:
        ax.axhspan(global_y_min, max(lower_limits), color=VIOLATION_SHADE, alpha=0.28, zorder=0)
    if upper_limits:
        ax.axhspan(min(upper_limits), global_y_max, color=VIOLATION_SHADE, alpha=0.28, zorder=0)

    for offset, campaign in zip(offsets, campaigns):
        values = pivot[campaign].to_numpy(dtype=float)
        valid = ~np.isnan(values)
        ax.scatter(
            x[valid] + offset,
            values[valid],
            s=76,
            marker="o",
            color=CAMPAIGN_COLORS[campaign],
            edgecolor="#0B4F12",
            linewidth=0.55,
            label=CAMPAIGN_LABELS[campaign],
            zorder=3,
        )
    for item in limits:
        ax.axhline(
            item["value"],
            color=VMP_RED,
            linewidth=2.0,
            label=vmp_legend_label(item),
            zorder=2,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(points, rotation=45, ha="right", fontsize=14)
    ylabel = display_param if unit == "-" else f"{display_param} ({unit})"
    ax.set_ylabel(ylabel, fontsize=18)
    ax.set_xlabel("Ponto", fontsize=16)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(True, alpha=0.22, linestyle="--", zorder=1)

    formatter = mticker.ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((-3, 4))
    ax.yaxis.set_major_formatter(formatter)

    handles, labels = ax.get_legend_handles_labels()
    unique_legend: dict[str, Any] = {}
    for handle, label in zip(handles, labels):
        unique_legend[label] = handle
    ordered_handles, ordered_labels = ordered_legend_items(unique_legend)
    ax.legend(
        ordered_handles,
        ordered_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.13),
        ncol=min(4, len(ordered_labels)),
        frameon=False,
        fontsize=13,
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.84, bottom=0.18)

    out_png = OUTPUT_DIR / f"teste_layout_{safe_filename(display_param)}.png"
    out_xlsx = OUTPUT_DIR / f"teste_layout_{safe_filename(display_param)}_dados.xlsx"
    fig.savefig(out_png, facecolor="white")
    plt.close(fig)

    export_cols = [
        "nome_ponto",
        "nome_campanha",
        "nome_parametro",
        "valor_medido",
        "sinal_limite",
        "unidade_medida",
        "vmp_357_cl2_min",
        "vmp_357_cl2_max",
        "vmp_amonia_dinamico",
    ]
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        data[export_cols].to_excel(writer, sheet_name="dados_plotados", index=False)
    style_workbook(out_xlsx)

    return {
        "parametro": display_param,
        "parametro_fonte": source_param,
        "png": str(out_png),
        "xlsx": str(out_xlsx),
        "pontos": len(points),
        "campanhas": len(campaigns),
        "vmp": [item["label"] for item in limits],
    }


def plot_parameter_campaign_panels(surface: pd.DataFrame, parameter: str) -> dict[str, Any]:
    source_param = find_parameter(surface, parameter)
    data = surface[surface["nome_parametro"].eq(source_param)].copy()
    data = data.sort_values(["nome_ponto", "nome_campanha"])
    points = point_order(data["nome_ponto"].dropna().unique().tolist())
    campaigns = [campaign for campaign in CAMPAIGN_LABELS if campaign in set(data["nome_campanha"])]
    unit = fix_ptbr_label(clean_text(data["unidade_medida"].dropna().iloc[0]) if not data["unidade_medida"].dropna().empty else "")
    display_param = fix_ptbr_label(parameter)

    pivot = data.pivot_table(index="nome_ponto", columns="nome_campanha", values="valor_medido", aggfunc="first").reindex(points)
    limits = get_limits(data)

    y_values = pivot.to_numpy(dtype=float)
    y_max = np.nanmax(y_values)
    y_min = np.nanmin(y_values)
    for item in limits:
        y_max = max(y_max, float(item["value"]))
        y_min = min(y_min, float(item["value"]))
    if display_param == "pH In Situ":
        global_y_min = max(0, y_min - 0.5)
        global_y_max = y_max + 0.5
    else:
        global_y_min = -0.02 * y_max if y_max else 0
        global_y_max = y_max * 1.22 if y_max else 1

    OUTPUT_PANEL_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, len(campaigns), figsize=(14, 9), dpi=600, sharey=True, squeeze=False)
    axes_flat = list(axes.ravel())
    x = np.arange(len(points), dtype=float)

    for ax, campaign in zip(axes_flat, campaigns):
        ax.set_ylim(global_y_min, global_y_max)
        lower_limits = [float(item["value"]) for item in limits if item["kind"] == "min"]
        upper_limits = [float(item["value"]) for item in limits if item["kind"] in {"max", "dynamic"}]
        if lower_limits:
            ax.axhspan(global_y_min, max(lower_limits), color=VIOLATION_SHADE, alpha=0.28, zorder=0)
        if upper_limits:
            ax.axhspan(min(upper_limits), global_y_max, color=VIOLATION_SHADE, alpha=0.28, zorder=0)

        values = pivot[campaign].to_numpy(dtype=float)
        valid = ~np.isnan(values)
        ax.scatter(
            x[valid],
            values[valid],
            s=88,
            marker="o",
            color=CAMPAIGN_COLORS[campaign],
            edgecolor="#0B4F12",
            linewidth=0.65,
            label=CAMPAIGN_LABELS[campaign],
            zorder=3,
        )
        for item in limits:
            ax.axhline(
                item["value"],
                color=VMP_RED,
                linewidth=2.0,
                label=vmp_legend_label(item),
                zorder=2,
            )

        ax.set_title(CAMPAIGN_LABELS[campaign], fontsize=17, fontweight="bold", pad=12)
        ax.set_xticks(x)
        ax.set_xticklabels(points, rotation=45, ha="right", fontsize=12)
        ax.set_xlabel("Ponto", fontsize=14)
        ax.tick_params(axis="y", labelsize=12)
        ax.grid(True, alpha=0.22, linestyle="--", zorder=1)

    ylabel = display_param if unit == "-" else f"{display_param} ({unit})"
    axes_flat[0].set_ylabel(ylabel, fontsize=18)

    handles, labels = [], []
    for ax in axes_flat:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    unique_legend: dict[str, Any] = {}
    for handle, label in zip(handles, labels):
        unique_legend[label] = handle
    ordered_handles, ordered_labels = ordered_legend_items(unique_legend)
    fig.legend(
        ordered_handles,
        ordered_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=min(4, len(ordered_labels)),
        frameon=False,
        fontsize=12,
    )
    fig.subplots_adjust(left=0.08, right=0.985, top=0.82, bottom=0.18, wspace=0.08)

    out_png = OUTPUT_PANEL_DIR / f"teste_painel_{safe_filename(display_param)}.png"
    out_xlsx = OUTPUT_PANEL_DIR / f"teste_painel_{safe_filename(display_param)}_dados.xlsx"
    fig.savefig(out_png, facecolor="white")
    plt.close(fig)

    export_cols = [
        "nome_ponto",
        "nome_campanha",
        "nome_parametro",
        "valor_medido",
        "sinal_limite",
        "unidade_medida",
        "vmp_357_cl2_min",
        "vmp_357_cl2_max",
        "vmp_amonia_dinamico",
    ]
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        data[export_cols].to_excel(writer, sheet_name="dados_plotados", index=False)
    style_workbook(out_xlsx)

    return {
        "parametro": display_param,
        "parametro_fonte": source_param,
        "png": str(out_png),
        "xlsx": str(out_xlsx),
        "pontos": len(points),
        "campanhas": len(campaigns),
        "vmp": [item["label"] for item in limits],
    }


def style_workbook(path: Path) -> None:
    wb = load_workbook(path)
    fill = PatternFill("solid", fgColor="1F4E78")
    font = Font(color="FFFFFF", bold=True)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.fill = fill
            cell.font = font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for col in ws.columns:
            values = [clean_text(cell.value) for cell in col]
            ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(max(map(len, values), default=0) + 2, 10), 42)
        ws.auto_filter.ref = ws.dimensions
    wb.save(path)


def main() -> int:
    surface = load_surface()
    results = [plot_parameter(surface, parameter) for parameter in PARAMETERS]
    panel_results = [plot_parameter_campaign_panels(surface, parameter) for parameter in PARAMETERS]
    manifest = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "status": "LAYOUT_TEST_GENERATED",
        "saida": str(OUTPUT_DIR),
        "figuras": results,
        "figuras_paineis_campanha": panel_results,
        "premissas": [
            "Somente Ãgua Superficial.",
            "PadrÃ£o FERSAM Superficial: grÃ¡fico Ãºnico por parÃ¢metro, pontos no eixo X e campanhas em tons de verde.",
            "Legenda superior sem caixa, no estilo Campanha-01/Campanha-02.",
            "VMP - Classe 2 em linha vermelha contínua, sem citação da legislação na legenda.",
            "Zona de violaÃ§Ã£o com preenchimento vermelho claro.",
            "Resultados com sinal < permanecem nas planilhas de dados, sem anotação no ponto para reduzir poluição visual.",
        ],
    }
    manifest_path = OUTPUT_DIR / "manifesto_teste_layout_superficial.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    panel_manifest_path = OUTPUT_PANEL_DIR / "manifesto_teste_layout_paineis_campanha.json"
    panel_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

