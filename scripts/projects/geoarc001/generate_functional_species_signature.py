from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
SCRIPT_DIR = Path(__file__).resolve().parent
for path in [SRC, SCRIPT_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from opyta_analysis.config import load_theme
import generate_functional_exploratory_analysis as functional


DEFAULT_OUTPUT = functional.DEFAULT_OUTPUT
DEFAULT_SOURCE = functional.DEFAULT_SOURCE
DEFAULT_TRAITS = functional.DEFAULT_TRAITS
DEFAULT_THREATENED_TABLE = DEFAULT_OUTPUT.parent / "14_df_heatmap_especies_ameacadas_harttia_ictiofauna.xlsx"

GROUP_COLORS = {
    "especialistas_loticos_sensiveis": "#2E6F95",
    "raspadores_bentonicos_reofilicos": "#2A9D8F",
    "generalistas_tolerantes": "#E07A5F",
    "predadores": "#6D597A",
}


def _norm(value: object) -> str:
    text = "" if value is None or pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.strip().lower().split())


def _is_threatened(row: pd.Series) -> bool:
    status_cols = [
        "Status Ameaça Estadual",
        "Status Ameaça Nacional",
        "Status Ameaça Global",
        "Status COPAM",
    ]
    tokens = {"cr", "en", "vu", "vulneravel", "em perigo", "criticamente", "ameacada", "ameacado"}
    for col in status_cols:
        value = _norm(row.get(col))
        if not value or value in {"n.a.", "na", "nan", "ne", "lc", "pouco preocupante", "nao ameacada", "nao ameacado"}:
            continue
        if any(token in value for token in tokens):
            return True
    return False


def _is_exotic(row: pd.Series) -> bool:
    value = _norm(row.get("Origem"))
    return any(token in value for token in ["exot", "aloc", "nao nativ", "introduz"])


def _font_size(value: float, values: pd.Series, min_size: float = 9.0, max_size: float = 19.0) -> float:
    clean = pd.to_numeric(values, errors="coerce").fillna(0)
    vmax = float(clean.max()) if len(clean) else 0.0
    if vmax <= 0:
        return min_size
    return min_size + math.sqrt(max(value, 0.0) / vmax) * (max_size - min_size)


def _display_font_size(species: object, value: float, values: pd.Series) -> float:
    size = _font_size(value, values)
    text_len = len(str(species))
    if text_len >= 28:
        size = min(size, 15.0)
    elif text_len >= 23:
        size = min(size, 16.5)
    return size


def _group_masks(records: pd.DataFrame) -> dict[str, pd.Series]:
    data = records.copy()
    data["habitat_norm"] = data["Habitat_funcional"].map(functional._normalize_text)
    data["corrente_norm"] = data["Preferencia_correnteza"].map(functional._normalize_text)
    data["guilda_norm"] = data["Guilda_trofica"].map(functional._normalize_text)
    data["sensibilidade_norm"] = data["Sensibilidade_funcional"].map(functional._normalize_text)
    return {
        "especialistas_loticos_sensiveis": (data["corrente_norm"] == "reofilico")
        & (data["sensibilidade_norm"] == "sensivel"),
        "raspadores_bentonicos_reofilicos": (data["guilda_norm"] == "perifitivoro")
        & (data["habitat_norm"] == "bentonico")
        & (data["corrente_norm"] == "reofilico"),
        "generalistas_tolerantes": (data["guilda_norm"] == "onivoro")
        & (data["sensibilidade_norm"] == "tolerante"),
        "predadores": data["guilda_norm"] == "piscivoro",
    }


def read_threatened_reference(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    try:
        table = pd.read_excel(path)
    except Exception:
        return set()
    species_col = "especie" if "especie" in table.columns else "Nome_Cientifico" if "Nome_Cientifico" in table.columns else None
    if species_col is None:
        return set()
    return {functional._normalize_text(value) for value in table[species_col].dropna().unique().tolist()}


def build_species_signature(source: Path, traits_path: Path, threatened_table: Path | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    tables = functional.read_sources(source, traits_path)
    traits = functional.prepare_traits(tables.atributos)
    _matrix, metadata, counts = functional.build_community(tables)
    _fm, _fl, _fr, records, _categories = functional.build_functional_profiles(counts, metadata, traits)

    masks = _group_masks(records)
    trait_cols = [
        "species_key",
        "nome_cientifico",
        "Autor e Ano",
        "Familia",
        "Origem",
        "Status Ameaça Estadual",
        "Status Ameaça Nacional",
        "Status Ameaça Global",
        "Status COPAM",
        "Habitat_funcional",
        "Preferencia_correnteza",
        "Guilda_trofica",
        "Porte_corporal",
        "Sensibilidade_funcional",
    ]
    trait_cols = [col for col in trait_cols if col in traits.columns]
    trait_meta = traits[trait_cols].drop_duplicates("species_key").copy()

    rows: list[pd.DataFrame] = []
    definitions = pd.DataFrame(functional.FUNCTIONAL_GROUP_DEFINITIONS)
    definitions.insert(0, "ordem_grupo", range(1, len(definitions) + 1))
    for order, definition in enumerate(functional.FUNCTIONAL_GROUP_DEFINITIONS, start=1):
        code = definition["codigo"]
        subset = records[masks[code]].copy()
        if subset.empty:
            continue
        agg = (
            subset.groupby(["species_key", "nome_cientifico"], as_index=False)
            .agg(
                CPUEn_total_grupo=("CPUEn", "sum"),
                abundancia_total_grupo=("contagem", "sum"),
                n_amostras=("sample_id", "nunique"),
                n_pontos=("nome_ponto", "nunique"),
                n_campanhas=("nome_campanha", "nunique"),
                pontos=("nome_ponto", lambda values: "; ".join(sorted(set(map(str, values)), key=functional._point_sort_key))),
                campanhas=("nome_campanha", lambda values: "; ".join(sorted(set(map(str, values)), key=functional._campaign_sort_key))),
            )
            .merge(trait_meta, on="species_key", how="left", suffixes=("", "_atributo"))
        )
        if "nome_cientifico_atributo" in agg.columns:
            agg["nome_cientifico"] = agg["nome_cientifico_atributo"].fillna(agg["nome_cientifico"])
            agg = agg.drop(columns=["nome_cientifico_atributo"])
        agg["grupo_funcional"] = code
        agg["grupo_rotulo"] = definition["rotulo"]
        agg["criterio"] = definition["criterio"]
        agg["ordem_grupo"] = order
        rows.append(agg)

    summary = pd.concat(rows, ignore_index=True)
    threatened_reference = read_threatened_reference(threatened_table)
    summary["ameacada_status_atributos"] = summary.apply(_is_threatened, axis=1)
    summary["ameacada_referencia"] = summary["species_key"].isin(threatened_reference)
    summary["ameacada"] = summary["ameacada_status_atributos"] | summary["ameacada_referencia"]
    summary["fonte_ameaca"] = np.select(
        [summary["ameacada_status_atributos"] & summary["ameacada_referencia"], summary["ameacada_status_atributos"], summary["ameacada_referencia"]],
        ["atributos_e_referencia", "atributos", "referencia_produto_14"],
        default="",
    )
    summary["exotica"] = summary.apply(_is_exotic, axis=1)
    summary["rank_grupo"] = (
        summary.sort_values(["ordem_grupo", "CPUEn_total_grupo"], ascending=[True, False])
        .groupby("grupo_funcional")
        .cumcount()
        + 1
    )
    total_by_group = summary.groupby("grupo_funcional")["CPUEn_total_grupo"].transform("sum")
    summary["perc_CPUEn_dentro_grupo"] = np.where(total_by_group > 0, summary["CPUEn_total_grupo"] / total_by_group * 100.0, 0.0)
    summary = summary.sort_values(["ordem_grupo", "rank_grupo"]).reset_index(drop=True)
    return summary, definitions


def _draw_badge(ax, x: float, y: float, text: str, color: str) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=6.8,
        fontweight="bold",
        color="white",
        bbox=dict(boxstyle="round,pad=0.22,rounding_size=0.12", facecolor=color, edgecolor="none", alpha=0.95),
        zorder=5,
    )


def _species_y_positions(n_species: int) -> np.ndarray:
    if n_species <= 1:
        return np.array([0.50])
    if n_species == 2:
        return np.array([0.62, 0.40])
    if n_species == 3:
        return np.array([0.66, 0.46, 0.26])
    return np.linspace(0.73, 0.18, n_species)


def plot_signature(summary: pd.DataFrame, definitions: pd.DataFrame, out_png: Path, theme: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14.8, 8.2), dpi=int(theme.get("dpi", 600)))
    axes = axes.flatten()
    max_cpuen = max(float(summary["CPUEn_total_grupo"].max()), 1.0)

    for ax, definition in zip(axes, definitions.sort_values("ordem_grupo").to_dict("records"), strict=True):
        code = definition["codigo"]
        data = summary[summary["grupo_funcional"] == code].sort_values("rank_grupo").copy()
        color = GROUP_COLORS.get(code, "#2E6F95")
        ax.set_axis_off()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        panel = FancyBboxPatch(
            (0.02, 0.03),
            0.96,
            0.91,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=ax.transAxes,
            facecolor="#FAFAFA",
            edgecolor=color,
            linewidth=1.2,
            alpha=0.96,
        )
        ax.add_patch(panel)
        ax.text(0.05, 0.90, definition["rotulo"], transform=ax.transAxes, fontsize=13, fontweight="bold", color=color)
        ax.text(0.05, 0.845, definition["criterio"], transform=ax.transAxes, fontsize=7.7, color="#4A4A4A")
        ax.text(
            0.94,
            0.90,
            f"{len(data)} spp.",
            transform=ax.transAxes,
            ha="right",
            va="center",
            fontsize=9,
            color="#333333",
            fontweight="bold",
        )
        if data.empty:
            ax.text(0.50, 0.50, "Sem espécies no critério", transform=ax.transAxes, ha="center", va="center")
            continue

        y_positions = _species_y_positions(len(data))
        for y, (_, row) in zip(y_positions, data.iterrows(), strict=True):
            value = float(row["CPUEn_total_grupo"])
            size = _display_font_size(row["nome_cientifico"], value, data["CPUEn_total_grupo"])
            weight = "bold" if int(row["rank_grupo"]) == 1 else "normal"
            ax.text(
                0.08,
                y,
                row["nome_cientifico"],
                transform=ax.transAxes,
                ha="left",
                va="center",
                fontsize=size,
                fontstyle="italic",
                fontweight=weight,
                color="#202020",
                zorder=4,
            )
            bar_x0 = 0.75
            bar_width = 0.14 * math.sqrt(max(value, 0.0) / max_cpuen)
            ax.plot([bar_x0, bar_x0 + bar_width], [y, y], transform=ax.transAxes, color=color, linewidth=5.2, alpha=0.72, solid_capstyle="round")
            ax.text(
                0.95,
                y,
                f"{value:.1f}",
                transform=ax.transAxes,
                ha="right",
                va="center",
                fontsize=8,
                color="#333333",
            )
            badge_x = 0.61
            if bool(row.get("ameacada")):
                _draw_badge(ax, badge_x, y, "AME", "#B23A48")
                badge_x -= 0.075
            if bool(row.get("exotica")):
                _draw_badge(ax, badge_x, y, "EXO", "#D08C00")

        ax.text(0.75, 0.10, "CPUEn total", transform=ax.transAxes, fontsize=7.5, color="#555555")

    fig.suptitle(
        "Assinatura das espécies nos grupos funcionais sentinelas",
        x=0.02,
        y=0.985,
        ha="left",
        fontsize=17,
        fontweight="bold",
    )
    fig.text(
        0.02,
        0.025,
        "Tamanho do nome e barra = CPUEn total acumulado no grupo. AME = ameaçada; EXO = exótica. Uma espécie pode aparecer em mais de um grupo quando atende a critérios independentes.",
        ha="left",
        fontsize=8.5,
        color="#404040",
    )
    fig.subplots_adjust(left=0.035, right=0.985, top=0.92, bottom=0.08, hspace=0.14, wspace=0.08)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def write_outputs(output_dir: Path, summary: pd.DataFrame, definitions: pd.DataFrame, manifest_data: dict) -> dict[str, str]:
    xlsx = output_dir / "27_df_assinatura_especies_grupos_funcionais_ictiofauna.xlsx"
    manifest = output_dir / "27_manifesto_assinatura_especies_grupos_funcionais_ictiofauna.json"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="assinatura_especies", index=False)
        definitions.to_excel(writer, sheet_name="definicoes_grupos", index=False)
        (
            summary.groupby(["ordem_grupo", "grupo_funcional", "grupo_rotulo"], as_index=False)
            .agg(
                especies=("nome_cientifico", "nunique"),
                CPUEn_total=("CPUEn_total_grupo", "sum"),
                abundancia_total=("abundancia_total_grupo", "sum"),
                ameacadas=("ameacada", "sum"),
                exoticas=("exotica", "sum"),
            )
            .sort_values("ordem_grupo")
            .to_excel(writer, sheet_name="resumo_grupos", index=False)
        )
    manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"xlsx": str(xlsx), "manifest": str(manifest)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera painel de assinatura das espécies por grupos funcionais sentinelas.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--traits", default=str(DEFAULT_TRAITS))
    parser.add_argument("--threatened-table", default=str(DEFAULT_THREATENED_TABLE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--client", default="default")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    traits = Path(args.traits)
    threatened_table = Path(args.threatened_table) if args.threatened_table else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", args.client)

    signature, definitions = build_species_signature(source, traits, threatened_table)
    out_png = output_dir / "27_grafico_assinatura_especies_grupos_funcionais_ictiofauna.png"
    plot_signature(signature, definitions, out_png, theme)
    manifest_data = {
        "source": str(source),
        "traits": str(traits),
        "threatened_table": str(threatened_table) if threatened_table else None,
        "output_dir": str(output_dir),
        "figure": str(out_png),
        "rows": int(len(signature)),
        "groups": definitions[["codigo", "rotulo", "criterio"]].to_dict("records"),
        "species_unique": int(signature["nome_cientifico"].nunique()),
        "note": "Figura exploratória; nomes e barras são proporcionais ao CPUEn total acumulado por espécie dentro de cada grupo funcional sentinela.",
    }
    outputs = write_outputs(output_dir, signature, definitions, manifest_data)
    manifest_data["outputs"] = outputs
    (output_dir / "27_manifesto_assinatura_especies_grupos_funcionais_ictiofauna.json").write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest_data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
