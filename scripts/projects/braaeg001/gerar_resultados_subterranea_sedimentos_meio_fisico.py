from __future__ import annotations

import json
import math
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
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
CLIENT_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt")
PROJECT_DIR = next(path for path in CLIENT_ROOT.iterdir() if path.name.startswith("A&G"))
CONSOLIDATED_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "migracao" / "consolidacao_pos_c02"
RESULTS_DIR = PROJECT_DIR / "resultados" / "Meio_fisico" / "resultados"

CAMPAIGN_LABELS = {
    "C001-2026-02-CH": "Campanha-01-Chuva",
    "C002-2026-06-SC": "Campanha-02-Seca",
}
CAMPAIGN_SHORT = {
    "C001-2026-02-CH": "Chuva",
    "C002-2026-06-SC": "Seca",
}
GREEN = "#1B7F22"
GREEN_DRY = "#19FF19"
LIGHT_GREEN = "#EAF6E8"
VMP_RED = "#F04438"
VMP_RED_LIGHT = "#FEE2E2"
VMP_YELLOW_LIGHT = "#FFF3BF"
GRID = "#D9E2D3"
BLUE = "#1F4E78"
CAMPAIGN_COLORS = {
    "C001-2026-02-CH": GREEN,
    "C002-2026-06-SC": GREEN_DRY,
}
VMP_COLORS = {
    "vmp_396_consumo_humano": "#F04438",
    "vmp_396_dessedentacao_animal": "#7B2CBF",
    "vmp_396_irrigacao": "#FF9F1C",
    "vmp_396_recreacao": "#0077B6",
    "vmp_430_padrao": "#111111",
    "vmp_454_n1": "#0077B6",
    "vmp_454_n2": "#F04438",
}

MATRIX_CONFIG = {
    "subterranea": {
        "matrix_match": "agua subterranea",
        "label": "Água Subterrânea",
        "safe_label": "Agua_Subterranea",
        "folder": "subterranea",
        "conformidade": "01_Conformidade_Agua_Subterranea.xlsx",
        "dados": "02_Dados_por_Parametro_Agua_Subterranea.xlsx",
        "vmp_cols": [
            ("vmp_396_consumo_humano", "VMP - CONAMA 396 - Consumo humano"),
            ("vmp_396_dessedentacao_animal", "VMP - CONAMA 396 - Dessedentação animal"),
            ("vmp_396_irrigacao", "VMP - CONAMA 396 - Irrigação"),
            ("vmp_396_recreacao", "VMP - CONAMA 396 - Recreação"),
            ("vmp_430_padrao", "VMP - CONAMA 430"),
        ],
        "status_order": ["Viola", "Atende", "Sem VMP"],
    },
    "sedimentos": {
        "matrix_match": "sedimento",
        "label": "Sedimentos",
        "safe_label": "Sedimentos",
        "folder": "sedimentos",
        "conformidade": "01_Conformidade_Sedimentos.xlsx",
        "dados": "02_Dados_por_Parametro_Sedimentos.xlsx",
        "vmp_cols": [
            ("vmp_454_n1", "VMP - CONAMA 454 - Nível 1"),
            ("vmp_454_n2", "VMP - CONAMA 454 - Nível 2"),
        ],
        "status_order": ["Viola", "Entre N1 e N2", "Atende", "Sem VMP"],
    },
}


def fold(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).replace("\xa0", " ").strip()
    text = text.replace("ę", "e").replace("Ę", "E").replace("ă", "ã").replace("Ă", "Ã")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def display_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).replace("\xa0", " ").strip()
    replacements = {
        "Arsęnio": "Arsênio",
        "Arsenio": "Arsênio",
        "Cadmio": "Cádmio",
        "Bario": "Bário",
        "Aluminio": "Alumínio",
        "Fosforo": "Fósforo",
        "Manganęs": "Manganês",
        "Manganes": "Manganês",
        "Mercurio": "Mercúrio",
        "Niquel": "Níquel",
        "Molibdęnio": "Molibdênio",
        "Vanadio": "Vanádio",
        "Oxigęnio": "Oxigênio",
        "Oxigenio": "Oxigênio",
        "Bioquimica": "Bioquímica",
        "Quimica": "Química",
        "Eletrica": "Elétrica",
        "Solidos": "Sólidos",
        "Sodio": "Sódio",
        "Potassio": "Potássio",
        "Calcio": "Cálcio",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def safe_name(text: str, limit: int = 90) -> str:
    base = fold(text)
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return (base[:limit] or "parametro")


def sheet_name(text: str, used: set[str]) -> str:
    name = re.sub(r"[\[\]\*:/\\?]", "_", display_text(text))[:31] or "Parametro"
    original = name
    counter = 2
    while name in used:
        suffix = f"_{counter}"
        name = f"{original[:31-len(suffix)]}{suffix}"
        counter += 1
    used.add(name)
    return name


def format_value(value: Any, signal: Any = "") -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    prefix = str(signal).strip() if signal is not None and not pd.isna(signal) else ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{prefix}{value}".strip()
    if abs(number) >= 100:
        body = f"{number:.0f}" if abs(number - round(number)) < 1e-9 else f"{number:.2f}".rstrip("0").rstrip(".")
    elif abs(number) >= 1:
        body = f"{number:.3f}".rstrip("0").rstrip(".")
    else:
        body = f"{number:.6f}".rstrip("0").rstrip(".")
    return f"{prefix}{body}".strip()


def latest_consolidated() -> Path:
    files = sorted(CONSOLIDATED_DIR.glob("*consolidado_meio_fisico_braaeg001_pos_c02.xlsx"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"Nenhum consolidado encontrado em {CONSOLIDATED_DIR}")
    return files[-1]


def read_data() -> pd.DataFrame:
    path = latest_consolidated()
    df = pd.read_excel(path)
    df["_fonte_consolidado"] = str(path)
    df["parametro_exibicao"] = df["nome_parametro"].map(display_text)
    df["unidade_exibicao"] = df["unidade_medida"].map(display_text)
    df["matriz_norm"] = df["matriz"].map(fold)
    df["parametro_norm"] = df["nome_parametro"].map(fold)
    df["campanha_label"] = df["nome_campanha"].map(lambda x: CAMPAIGN_LABELS.get(str(x), str(x)))
    df["campanha_curta"] = df["nome_campanha"].map(lambda x: CAMPAIGN_SHORT.get(str(x), str(x)))
    return df


def point_key(point: Any) -> tuple[int, str]:
    text = str(point)
    numbers = re.findall(r"\d+", text)
    return (int(numbers[-1]) if numbers else 999, text)


def fix_limit_scale(param_norm: str, unit: str, col: str, value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    unit_norm = fold(unit)
    if param_norm.startswith("nitrato") and "mg/l" in unit_norm and number > 1000:
        return number / 1000.0
    if param_norm.startswith("nitrito") and "mg/l" in unit_norm and number > 1000:
        return number / 1000.0
    return number


def limit_display_value(param_norm: str, col: str, value: Any) -> str:
    if col == "vmp_396_consumo_humano" and param_norm in {"escherichia coli", "coliformes termotolerantes"}:
        try:
            if value is not None and not pd.isna(value) and float(value) == 0:
                return "Ausentes em 100 mL"
        except (TypeError, ValueError):
            pass
    return format_value(value)


def collect_limits(group: pd.DataFrame, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    limits: list[dict[str, Any]] = []
    param_norm = group["parametro_norm"].iloc[0]
    unit = group["unidade_exibicao"].dropna().iloc[0] if group["unidade_exibicao"].notna().any() else ""
    for col, label in cfg["vmp_cols"]:
        values = [fix_limit_scale(param_norm, unit, col, value) for value in group[col].dropna().tolist()]
        values = [value for value in values if value is not None and not pd.isna(value)]
        if not values:
            continue
        limits.append({"col": col, "label": label, "value": float(values[0])})
    return limits


def classify_row(row: pd.Series, limits: list[dict[str, Any]], matrix_key: str) -> str:
    if not limits or pd.isna(row.get("valor_medido")):
        return "Sem VMP"
    sign = str(row.get("sinal_limite") or "").strip()
    if sign in {"<", "<="}:
        return "Atende"
    value = float(row["valor_medido"])
    if matrix_key == "sedimentos":
        n1 = next((item["value"] for item in limits if item["col"] == "vmp_454_n1"), None)
        n2 = next((item["value"] for item in limits if item["col"] == "vmp_454_n2"), None)
        if n2 is not None and value > n2:
            return "Viola"
        if n1 is not None and value > n1:
            return "Entre N1 e N2"
        return "Atende"
    if any(value > item["value"] for item in limits):
        return "Viola"
    return "Atende"


def prepare_matrix(df: pd.DataFrame, matrix_key: str, cfg: dict[str, Any]) -> pd.DataFrame:
    out = df[df["matriz_norm"].eq(cfg["matrix_match"])].copy()
    if out.empty:
        raise RuntimeError(f"Nenhum dado encontrado para {cfg['label']}")
    out["status_conformidade"] = "Sem VMP"
    for _, group in out.groupby("parametro_norm", sort=False):
        limits = collect_limits(group, cfg)
        out.loc[group.index, "status_conformidade"] = group.apply(lambda row: classify_row(row, limits, matrix_key), axis=1)
    return out.sort_values(["nome_campanha", "nome_ponto", "parametro_exibicao"], key=lambda col: col.map(str))


def style_workbook(path: Path) -> None:
    wb = load_workbook(path)
    fill = PatternFill("solid", fgColor=BLUE.replace("#", ""))
    font = Font(color="FFFFFF", bold=True)
    for ws in wb.worksheets:
        ws.freeze_panes = "A3" if ws.max_row > 2 else "A2"
        for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 2)):
            for cell in row:
                if cell.value:
                    cell.fill = fill
                    cell.font = font
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="center", wrap_text=True)
        for col_idx, column in enumerate(ws.columns, start=1):
            values = [str(cell.value) for cell in column if cell.value is not None]
            width = min(max([len(value) for value in values] + [10]) + 2, 42)
            ws.column_dimensions[get_column_letter(col_idx)].width = width
        ws.sheet_view.showGridLines = False
    wb.save(path)


def write_conformidade(df: pd.DataFrame, cfg: dict[str, Any], out_dir: Path) -> Path:
    path = out_dir / cfg["conformidade"]
    wb = Workbook()
    wb.remove(wb.active)
    point_order = sorted(df["nome_ponto"].dropna().unique(), key=point_key)
    for campaign in sorted(df["nome_campanha"].dropna().unique()):
        ws = wb.create_sheet(CAMPAIGN_LABELS.get(campaign, campaign)[:31])
        vmp_headers = [label for _, label in cfg["vmp_cols"]]
        first_headers = ["Parâmetros analisados", "Unidade", *vmp_headers]
        for idx, header in enumerate(first_headers, start=1):
            ws.cell(row=1, column=idx, value=header)
            ws.cell(row=2, column=idx, value=header)
        start_points = len(first_headers) + 1
        ws.cell(row=1, column=start_points, value="Pontos amostrais")
        ws.merge_cells(start_row=1, start_column=start_points, end_row=1, end_column=start_points + len(point_order) - 1)
        for offset, point in enumerate(point_order):
            ws.cell(row=2, column=start_points + offset, value=point)
        part = df[df["nome_campanha"].eq(campaign)]
        params = sorted(part["parametro_exibicao"].dropna().unique(), key=fold)
        for row_idx, param in enumerate(params, start=3):
            group = part[part["parametro_exibicao"].eq(param)]
            ws.cell(row=row_idx, column=1, value=param)
            ws.cell(row=row_idx, column=2, value=group["unidade_exibicao"].dropna().iloc[0] if group["unidade_exibicao"].notna().any() else "")
            limits = collect_limits(group, cfg)
            limit_by_col = {item["col"]: item["value"] for item in limits}
            for vmp_idx, (col, _) in enumerate(cfg["vmp_cols"], start=3):
                ws.cell(row=row_idx, column=vmp_idx, value=limit_display_value(group["parametro_norm"].iloc[0], col, limit_by_col.get(col, None)))
            for offset, point in enumerate(point_order):
                row = group[group["nome_ponto"].eq(point)]
                if row.empty:
                    value = ""
                else:
                    r = row.iloc[0]
                    value = format_value(r["valor_medido"], r.get("sinal_limite", ""))
                ws.cell(row=row_idx, column=start_points + offset, value=value)
    ws = wb.create_sheet("Observacoes_Normativas")
    notes = [
        ["Matriz", cfg["label"]],
        ["Premissa", "Os VMPs foram aplicados conforme colunas normativas específicas da matriz no consolidado pós-C02."],
        ["Sinais <", "Resultados com sinal < ou <= foram tratados como atendimento ao limite para fins gráficos."],
    ]
    if cfg["safe_label"] == "Sedimentos":
        notes.append(["Sedimentos", "Excedências acima do Nível 2 foram classificadas como violação; valores entre Nível 1 e Nível 2 foram destacados separadamente."])
    for row in notes:
        ws.append(row)
    wb.save(path)
    style_workbook(path)
    return path


def write_dados_por_parametro(df: pd.DataFrame, cfg: dict[str, Any], out_dir: Path) -> Path:
    path = out_dir / cfg["dados"]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        index = (
            df.groupby(["parametro_exibicao", "unidade_exibicao"], dropna=False)
            .agg(registros=("valor_medido", "size"), pontos=("nome_ponto", "nunique"), campanhas=("nome_campanha", "nunique"), violacoes=("status_conformidade", lambda s: int((s == "Viola").sum())))
            .reset_index()
            .rename(columns={"parametro_exibicao": "Parâmetro", "unidade_exibicao": "Unidade", "registros": "Registros", "pontos": "Pontos", "campanhas": "Campanhas", "violacoes": "Violações"})
            .sort_values("Parâmetro", key=lambda col: col.map(fold))
        )
        index.to_excel(writer, sheet_name="Indice", index=False)
        used = {"Indice"}
        for param in sorted(df["parametro_exibicao"].dropna().unique(), key=fold):
            group = df[df["parametro_exibicao"].eq(param)].copy()
            limits = collect_limits(group, cfg)
            limit_by_col = {item["col"]: item["value"] for item in limits}
            out = pd.DataFrame(
                {
                    "Campanha": group["campanha_label"],
                    "Ponto": group["nome_ponto"],
                    "Parâmetro": group["parametro_exibicao"],
                    "Unidade": group["unidade_exibicao"],
                    "Sinal": group["sinal_limite"],
                    "Valor numérico": group["valor_medido"],
                    "Valor exibido": [format_value(v, s) for v, s in zip(group["valor_medido"], group["sinal_limite"])],
                    "Status": group["status_conformidade"],
                }
            )
            for col, label in cfg["vmp_cols"]:
                out[label] = limit_by_col.get(col, np.nan)
            out.sort_values(["Campanha", "Ponto"], key=lambda col: col.map(str)).to_excel(writer, sheet_name=sheet_name(param, used), index=False)
    style_workbook(path)
    return path


def plot_parameter_panel(group: pd.DataFrame, cfg: dict[str, Any], out_dir: Path) -> Path:
    param = group["parametro_exibicao"].iloc[0]
    unit = group["unidade_exibicao"].dropna().iloc[0] if group["unidade_exibicao"].notna().any() else ""
    limits = collect_limits(group, cfg)
    out_png = out_dir / f"03_painel_{safe_name(param)}.png"
    campaigns = [c for c in CAMPAIGN_LABELS if c in set(group["nome_campanha"])]
    if not campaigns:
        campaigns = sorted(group["nome_campanha"].dropna().unique())
    points = sorted(group["nome_ponto"].dropna().unique(), key=point_key)
    pivot = (
        group.pivot_table(index="nome_ponto", columns="nome_campanha", values="valor_medido", aggfunc="first")
        .reindex(index=points, columns=campaigns)
    )
    values_array = pivot.to_numpy(dtype=float)
    clean_values = values_array[~np.isnan(values_array)]
    if len(clean_values) == 0:
        clean_values = np.array([0.0])
    y_min = float(np.nanmin(clean_values))
    y_max = float(np.nanmax(clean_values))
    for item in limits:
        y_min = min(y_min, item["value"])
        y_max = max(y_max, item["value"])
    if y_min < 0:
        pad = (y_max - y_min) * 0.15 if y_max != y_min else 1
        y_min, y_max = y_min - pad, y_max + pad
    else:
        y_min, y_max = (-0.02 * y_max if y_max else 0), (y_max * 1.22 if y_max else 1)

    fig, axes = plt.subplots(1, len(campaigns), figsize=(14, 9), dpi=600, sharey=True, squeeze=False)
    axes_flat = list(axes.ravel())
    x = np.arange(len(points), dtype=float)
    for ax, campaign in zip(axes_flat, campaigns):
        ax.set_ylim(y_min, y_max)
        if limits and cfg["safe_label"] == "Sedimentos":
            n1 = next((item["value"] for item in limits if item["col"] == "vmp_454_n1"), None)
            n2 = next((item["value"] for item in limits if item["col"] == "vmp_454_n2"), None)
            if n1 is not None and n2 is not None:
                ax.axhspan(n1, n2, color=VMP_YELLOW_LIGHT, alpha=0.42, zorder=0)
                ax.axhspan(n2, y_max, color=VMP_RED_LIGHT, alpha=0.28, zorder=0)
            elif n1 is not None:
                ax.axhspan(n1, y_max, color=VMP_YELLOW_LIGHT, alpha=0.42, zorder=0)
        elif limits:
            shade_from = min(item["value"] for item in limits)
            ax.axhspan(shade_from, y_max, color=VMP_RED_LIGHT, alpha=0.28, zorder=0)
        values = pivot[campaign].to_numpy(dtype=float)
        valid = ~np.isnan(values)
        ax.scatter(
            x[valid],
            values[valid],
            s=88,
            marker="o",
            color=CAMPAIGN_COLORS.get(campaign, GREEN),
            edgecolor="#0B4F12",
            linewidth=0.65,
            label=CAMPAIGN_LABELS.get(campaign, campaign),
            zorder=3,
        )
        for item in limits:
            color = VMP_COLORS.get(item["col"], VMP_RED)
            label_value = limit_display_value(group["parametro_norm"].iloc[0], item["col"], item["value"])
            ax.axhline(item["value"], color=color, linewidth=2.0, label=f"{item['label']}: {label_value}", zorder=2)
        ax.set_title(CAMPAIGN_LABELS.get(campaign, campaign), fontsize=17, fontweight="bold", pad=12)
        ax.set_xticks(x)
        ax.set_xticklabels(points, rotation=45, ha="right", fontsize=12)
        ax.set_xlabel("Ponto", fontsize=14)
        ax.tick_params(axis="y", labelsize=12)
        ax.grid(True, alpha=0.22, linestyle="--", zorder=1)
        formatter = mticker.ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((-3, 4))
        ax.yaxis.set_major_formatter(formatter)

    axes_flat[0].set_ylabel(f"{param} ({unit})" if unit and unit != "-" else param, fontsize=18)
    handles, labels = [], []
    for ax in axes_flat:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    unique_legend = {label: handle for handle, label in zip(handles, labels)}
    ordered_labels = [label for label in CAMPAIGN_LABELS.values() if label in unique_legend]
    ordered_labels.extend(label for label in unique_legend if label.startswith("VMP - ") and label not in ordered_labels)
    ordered_handles = [unique_legend[label] for label in ordered_labels]
    fig.legend(
        ordered_handles,
        ordered_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=min(3, len(ordered_labels)),
        frameon=False,
        fontsize=11,
    )
    top = 0.78 if len(ordered_labels) > 4 else 0.82
    fig.subplots_adjust(left=0.08, right=0.985, top=top, bottom=0.18, wspace=0.08)
    fig.savefig(out_png, facecolor="white")
    plt.close(fig)
    return out_png


def write_violation_panel(df: pd.DataFrame, cfg: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    if cfg["safe_label"] == "Agua_Subterranea":
        numeric = df[df["valor_medido"].notna()].copy()
        numeric["violacao_subterranea"] = numeric["status_conformidade"].eq("Viola")
        summary = (
            numeric.groupby(["campanha_label", "parametro_exibicao"], dropna=False)
            .agg(
                registros=("valor_medido", "size"),
                violacoes=("violacao_subterranea", "sum"),
            )
            .reset_index()
        )
        summary["percentual_violacao"] = np.where(summary["registros"] > 0, summary["violacoes"] / summary["registros"] * 100, 0)
        summary = summary[summary["violacoes"] > 0].copy()
        path_xlsx = out_dir / "04_Painel_Violacoes_por_Campanha.xlsx"
        summary.rename(
            columns={
                "campanha_label": "Campanha",
                "parametro_exibicao": "Parâmetro",
                "registros": "Registros",
                "violacoes": "Violações",
                "percentual_violacao": "Violação (%)",
            }
        ).to_excel(path_xlsx, index=False)
        style_workbook(path_xlsx)

        path_png = out_dir / "04_painel_violacoes_chuva_seca.png"
        campaigns = list(CAMPAIGN_LABELS.values())
        params = (
            summary.groupby("parametro_exibicao", as_index=False)["violacoes"].sum()
            .sort_values(["violacoes", "parametro_exibicao"], ascending=[True, True])["parametro_exibicao"]
            .tolist()
        )
        if not params:
            fig, ax = plt.subplots(figsize=(14, 7), dpi=600)
            ax.text(0.5, 0.5, "Sem violações registradas", ha="center", va="center", fontsize=18)
            ax.axis("off")
            fig.savefig(path_png, facecolor="white")
            plt.close(fig)
            return path_xlsx, path_png

        fig, axes = plt.subplots(1, len(campaigns), figsize=(14, max(7, 0.48 * len(params))), dpi=600, sharey=True)
        if len(campaigns) == 1:
            axes = [axes]
        y = np.arange(len(params))
        max_pct = max(float(summary["percentual_violacao"].max()), 1.0)
        x_max = max(115, max_pct * 1.15)
        total_points = int(df["nome_ponto"].nunique())
        for ax, campaign in zip(axes, campaigns):
            data = summary[summary["campanha_label"].eq(campaign)].set_index("parametro_exibicao")
            pcts = [float(data.loc[param, "percentual_violacao"]) if param in data.index else 0.0 for param in params]
            viols = [int(data.loc[param, "violacoes"]) if param in data.index else 0 for param in params]
            regs = [int(data.loc[param, "registros"]) if param in data.index else total_points for param in params]
            colors = [GREEN if value > 0 else "#E8F5E9" for value in pcts]
            ax.barh(y, pcts, color=colors, edgecolor="#0B4F12", linewidth=0.35)
            ax.set_title(campaign, fontsize=16, fontweight="bold", pad=12)
            ax.set_xlim(0, x_max)
            ax.grid(True, axis="x", alpha=0.35, linestyle="--", color=GRID)
            ax.tick_params(axis="x", labelsize=11)
            ax.set_xlabel("Violação (%)", fontsize=13)
            for i, (pct, viol, reg) in enumerate(zip(pcts, viols, regs)):
                if viol:
                    if pct >= 90:
                        ax.text(pct - 1.2, i, f"{pct:.0f}% ({viol}/{reg})", va="center", ha="right", fontsize=10, color="white")
                    else:
                        ax.text(pct + 1, i, f"{pct:.0f}% ({viol}/{reg})", va="center", fontsize=10, color="#222222")
        axes[0].set_yticks(y)
        axes[0].set_yticklabels(params, fontsize=11)
        fig.subplots_adjust(left=0.29, right=0.985, top=0.92, bottom=0.12, wspace=0.08)
        fig.savefig(path_png, facecolor="white")
        plt.close(fig)
        return path_xlsx, path_png

    if cfg["safe_label"] == "Sedimentos":
        numeric = df[df["valor_medido"].notna()].copy()
        numeric["violacao_sedimento"] = numeric["status_conformidade"].isin(["Viola", "Entre N1 e N2"])
        summary = (
            numeric.groupby(["campanha_label", "parametro_exibicao"], dropna=False)
            .agg(
                registros=("valor_medido", "size"),
                violacoes=("violacao_sedimento", "sum"),
                acima_n2=("status_conformidade", lambda values: int((values == "Viola").sum())),
                entre_n1_n2=("status_conformidade", lambda values: int((values == "Entre N1 e N2").sum())),
            )
            .reset_index()
        )
        summary["percentual_violacao"] = np.where(summary["registros"] > 0, summary["violacoes"] / summary["registros"] * 100, 0)
        summary = summary[summary["violacoes"] > 0].copy()
        path_xlsx = out_dir / "04_Painel_Violacoes_por_Campanha.xlsx"
        summary.rename(
            columns={
                "campanha_label": "Campanha",
                "parametro_exibicao": "Parâmetro",
                "registros": "Registros",
                "violacoes": "Violações",
                "acima_n2": "Acima do Nível 2",
                "entre_n1_n2": "Entre Nível 1 e Nível 2",
                "percentual_violacao": "Violação (%)",
            }
        ).to_excel(path_xlsx, index=False)
        style_workbook(path_xlsx)

        path_png = out_dir / "04_painel_violacoes_chuva_seca.png"
        campaigns = list(CAMPAIGN_LABELS.values())
        params = (
            summary.groupby("parametro_exibicao", as_index=False)["violacoes"].sum()
            .sort_values(["violacoes", "parametro_exibicao"], ascending=[True, True])["parametro_exibicao"]
            .tolist()
        )
        if not params:
            fig, ax = plt.subplots(figsize=(14, 7), dpi=600)
            ax.text(0.5, 0.5, "Sem violações registradas", ha="center", va="center", fontsize=18)
            ax.axis("off")
            fig.savefig(path_png, facecolor="white")
            plt.close(fig)
            return path_xlsx, path_png

        fig, axes = plt.subplots(1, len(campaigns), figsize=(14, max(7, 0.48 * len(params))), dpi=600, sharey=True)
        if len(campaigns) == 1:
            axes = [axes]
        y = np.arange(len(params))
        max_pct = max(float(summary["percentual_violacao"].max()), 1.0)
        x_max = max(115, max_pct * 1.15)
        for ax, campaign in zip(axes, campaigns):
            data = summary[summary["campanha_label"].eq(campaign)].set_index("parametro_exibicao")
            pcts = [float(data.loc[param, "percentual_violacao"]) if param in data.index else 0.0 for param in params]
            viols = [int(data.loc[param, "violacoes"]) if param in data.index else 0 for param in params]
            regs = [int(data.loc[param, "registros"]) if param in data.index else int(df["nome_ponto"].nunique()) for param in params]
            colors = [GREEN if value > 0 else "#E8F5E9" for value in pcts]
            ax.barh(y, pcts, color=colors, edgecolor="#0B4F12", linewidth=0.35)
            ax.set_title(campaign, fontsize=16, fontweight="bold", pad=12)
            ax.set_xlim(0, x_max)
            ax.grid(True, axis="x", alpha=0.35, linestyle="--", color=GRID)
            ax.tick_params(axis="x", labelsize=11)
            ax.set_xlabel("Violação (%)", fontsize=13)
            for i, (pct, viol, reg) in enumerate(zip(pcts, viols, regs)):
                if viol:
                    if pct >= 90:
                        ax.text(pct - 1.2, i, f"{pct:.0f}% ({viol}/{reg})", va="center", ha="right", fontsize=10, color="white")
                    else:
                        ax.text(pct + 1, i, f"{pct:.0f}% ({viol}/{reg})", va="center", fontsize=10, color="#222222")
        axes[0].set_yticks(y)
        axes[0].set_yticklabels(params, fontsize=11)
        fig.subplots_adjust(left=0.29, right=0.985, top=0.92, bottom=0.12, wspace=0.08)
        fig.savefig(path_png, facecolor="white")
        plt.close(fig)
        return path_xlsx, path_png

    grouped = (
        df.assign(violacao=df["status_conformidade"].eq("Viola").astype(int))
        .groupby(["nome_campanha", "nome_ponto"], dropna=False)
        .agg(violacoes=("violacao", "sum"), parametros=("parametro_exibicao", "nunique"))
        .reset_index()
    )
    grouped["Campanha"] = grouped["nome_campanha"].map(lambda x: CAMPAIGN_LABELS.get(str(x), str(x)))
    path_xlsx = out_dir / "04_Painel_Violacoes_por_Campanha.xlsx"
    grouped.rename(columns={"nome_ponto": "Ponto", "violacoes": "Violações", "parametros": "Parâmetros avaliados"})[
        ["Campanha", "Ponto", "Violações", "Parâmetros avaliados"]
    ].to_excel(path_xlsx, index=False)
    style_workbook(path_xlsx)
    path_png = out_dir / "04_painel_violacoes_chuva_seca.png"
    campaigns = [c for c in CAMPAIGN_LABELS if c in set(grouped["nome_campanha"])]
    fig, axes = plt.subplots(1, len(campaigns), figsize=(11.69, 8.27), dpi=300, sharex=True)
    if len(campaigns) == 1:
        axes = [axes]
    max_v = max(1, int(grouped["violacoes"].max()))
    for ax, campaign in zip(axes, campaigns):
        part = grouped[grouped["nome_campanha"].eq(campaign)].sort_values("nome_ponto", key=lambda col: col.map(point_key))
        colors = [GREEN if value > 0 else LIGHT_GREEN for value in part["violacoes"]]
        y = np.arange(len(part))
        ax.barh(y, part["violacoes"], color=colors, edgecolor=GREEN, linewidth=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(part["nome_ponto"], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, max_v + 1)
        ax.set_title(CAMPAIGN_SHORT.get(campaign, campaign), fontsize=12, fontweight="bold")
        ax.grid(True, axis="x", color=GRID, linestyle="--", linewidth=0.7)
        ax.set_xlabel("Número de parâmetros com violação", fontsize=10)
        for yi, value in enumerate(part["violacoes"]):
            if value > 0:
                ax.text(value + 0.05, yi, str(int(value)), va="center", fontsize=9)
    fig.tight_layout(rect=(0.03, 0.03, 0.98, 0.96))
    fig.savefig(path_png, facecolor="white")
    plt.close(fig)
    return path_xlsx, path_png


def generate_matrix_outputs(df: pd.DataFrame, matrix_key: str, cfg: dict[str, Any]) -> dict[str, Any]:
    out_dir = RESULTS_DIR / cfg["folder"]
    out_dir.mkdir(parents=True, exist_ok=True)
    matrix_df = prepare_matrix(df, matrix_key, cfg)
    conformidade = write_conformidade(matrix_df, cfg, out_dir)
    dados = write_dados_por_parametro(matrix_df, cfg, out_dir)
    figures = []
    for param in sorted(matrix_df["parametro_exibicao"].dropna().unique(), key=fold):
        group = matrix_df[matrix_df["parametro_exibicao"].eq(param)]
        if group["valor_medido"].notna().any():
            figures.append(str(plot_parameter_panel(group, cfg, out_dir)))
    viol_xlsx, viol_png = write_violation_panel(matrix_df, cfg, out_dir)
    summary = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "status": "OK",
        "projeto": "BRAAEG001",
        "matriz": cfg["label"],
        "fonte": matrix_df["_fonte_consolidado"].iloc[0],
        "saida": str(out_dir),
        "registros": int(len(matrix_df)),
        "pontos": int(matrix_df["nome_ponto"].nunique()),
        "campanhas": int(matrix_df["nome_campanha"].nunique()),
        "parametros": int(matrix_df["parametro_exibicao"].nunique()),
        "violacoes": int(matrix_df["status_conformidade"].eq("Viola").sum()),
        "entre_n1_n2": int(matrix_df["status_conformidade"].eq("Entre N1 e N2").sum()),
        "arquivos": {
            "conformidade": str(conformidade),
            "dados_por_parametro": str(dados),
            "painel_violacoes_xlsx": str(viol_xlsx),
            "painel_violacoes_png": str(viol_png),
            "paineis_parametros": figures,
        },
        "premissas": [
            "Layout derivado do template aprovado para Agua Superficial: A4 paisagem, pontos verdes sem linha de conexao, VMPs com cores distintas e faixa vermelha a partir do menor VMP aplicavel.",
            "Sem calculo de indices. IET nao e aplicado sem Clorofila a.",
            "VMPs aplicados conforme matriz: CONAMA 396 para Agua Subterranea e CONAMA 454 para Sedimentos.",
        ],
    }
    audit = out_dir / "12_Auditoria_Execucao.json"
    audit.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def neutralize_surface_iet() -> Path:
    out_dir = RESULTS_DIR / "superficial"
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = [out_dir / "06_IET_Heatmap.png", out_dir / "09_minimapa_iet_chuva_seca.png"]
    for png in pngs:
        if png.exists():
            png.unlink()
    path = out_dir / "06_IET_Tabela.xlsx"
    pd.DataFrame(
        [
            {
                "Ponto": "NÃO CALCULADO",
                "Campanha": "NÃO CALCULADO",
                "IET": np.nan,
                "Classe": "NÃO CALCULADO",
                "Observação": "IET não calculado: o índice exige Fósforo Total e Clorofila a. Não calcular com Fósforo Total isolado.",
            }
        ]
    ).to_excel(path, index=False)
    style_workbook(path)
    return path


def main() -> int:
    df = read_data()
    iet_table = neutralize_surface_iet()
    outputs = {}
    for matrix_key, cfg in MATRIX_CONFIG.items():
        outputs[matrix_key] = generate_matrix_outputs(df, matrix_key, cfg)
    manifest = {
        "status": "OK",
        "iet_superficial": str(iet_table),
        "subterranea": {k: outputs["subterranea"][k] for k in ["registros", "pontos", "campanhas", "parametros", "violacoes"]},
        "sedimentos": {k: outputs["sedimentos"][k] for k in ["registros", "pontos", "campanhas", "parametros", "violacoes", "entre_n1_n2"]},
    }
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
