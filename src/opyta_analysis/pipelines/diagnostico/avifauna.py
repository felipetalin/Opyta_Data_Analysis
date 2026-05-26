from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import apply_theme, place_legend_below_x_axis
from opyta_analysis.validators import validate_axes_style
from . import mastofauna as masto


TARGET_PCH_NAME = "Dores de Guanh\u00e3es"
TARGET_CONTROL_NAME = "\u00c1rea Controle"


def _infer_empreendimento_from_avifauna_point(point_name: object) -> str | None:
    """Fallback para pontos de Avifauna sem id_empreendimento no banco."""
    point = masto._norm(point_name).upper()
    point = re.sub(r"[^A-Z0-9]+", "", point)

    if point.startswith("CO"):
        return "\u00c1rea Controle"
    if point.startswith("RNDG") or point.startswith("DG"):
        return "Dores de Guanh\u00e3es"
    if point.startswith("RNFO") or point.startswith("FO"):
        return "Fortuna II"
    if point.startswith("RNJC") or point.startswith("JC"):
        return "Jacar\u00e9"
    if point.startswith("RNSP") or point.startswith("SP"):
        return "Senhora do Porto"
    return None


def _resolve_empreendimento(
    point_name: object,
    id_empreendimento: object,
    emp_map: dict[object, str],
) -> tuple[str, str]:
    if id_empreendimento in emp_map:
        return emp_map[id_empreendimento], "id_empreendimento"

    inferred = _infer_empreendimento_from_avifauna_point(point_name)
    if inferred:
        return inferred, "prefixo_ponto_avifauna"

    return "Sem empreendimento", "nao_classificado"


def _load_avifauna_df(project_id: int, env_file: Optional[str]) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    empreendimentos = paginate(
        sb,
        "empreendimentos",
        filters={"id_projeto": int(project_id)},
        select="id_empreendimento,nome",
    )
    emp_map = {e["id_empreendimento"]: e["nome"] for e in empreendimentos}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Avifauna"},
        select="id_esforco,id_ponto_coleta,metodo_de_captura,tipo_amostragem,tipo_de_amostragem,esforco,unidade_esforco",
    )
    esforcos = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos:
        return pd.DataFrame()

    esforco_map = {e["id_esforco"]: e for e in esforcos}
    esforco_ids = set(esforco_map.keys())

    resultados = paginate(
        sb,
        "resultados_avifauna",
        select="id_esforco,id_especie,numero_de_individuos,tipo_amostragem,observacoes",
    )
    resultados = [r for r in resultados if r.get("id_esforco") in esforco_ids]
    if not resultados:
        return pd.DataFrame()

    especies = paginate(
        sb,
        "especies",
        select="id_especie,nome_cientifico,nome_popular,ordem,familia,status_ameaca_global,status_ameaca_nacional,status_copam,cites,dependencia_florestal,endemismo,habito_alimentar,guilda_alimentar,sensibilidade_ambiental,migratorio,raridade,origem,distribuicao,cinegetica,xerimbabo,observacoes",
    )
    esp_map = {e["id_especie"]: e for e in especies}

    rows: list[dict[str, Any]] = []
    for result in resultados:
        esforco = esforco_map.get(result.get("id_esforco"), {})
        ponto = pontos_map.get(esforco.get("id_ponto_coleta"), {})
        especie = esp_map.get(result.get("id_especie"), {})
        empreendimento, assignment_source = _resolve_empreendimento(
            ponto.get("nome_ponto"),
            ponto.get("id_empreendimento"),
            emp_map,
        )

        rows.append(
            {
                "nome_campanha": camp_map.get(ponto.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": ponto.get("nome_ponto"),
                "empreendimento": empreendimento,
                "empreendimento_assignment_source": assignment_source,
                "nome_cientifico": especie.get("nome_cientifico"),
                "nome_popular": especie.get("nome_popular"),
                "ordem": especie.get("ordem"),
                "familia": especie.get("familia"),
                "status_ameaca_global": especie.get("status_ameaca_global"),
                "status_ameaca_nacional": especie.get("status_ameaca_nacional"),
                "status_copam": especie.get("status_copam"),
                "cites": especie.get("cites"),
                "dependencia_florestal": especie.get("dependencia_florestal"),
                "endemismo": especie.get("endemismo"),
                "habito_alimentar": especie.get("habito_alimentar"),
                "guilda_alimentar": especie.get("guilda_alimentar"),
                "sensibilidade_ambiental": especie.get("sensibilidade_ambiental"),
                "migratorio": especie.get("migratorio"),
                "raridade": especie.get("raridade"),
                "origem": especie.get("origem"),
                "distribuicao": especie.get("distribuicao"),
                "cinegetica_db": especie.get("cinegetica"),
                "xerimbabo_db": especie.get("xerimbabo"),
                "especie_obs": especie.get("observacoes"),
                "metodo_de_captura": esforco.get("metodo_de_captura"),
                "tipo_amostragem": (
                    result.get("tipo_amostragem")
                    or esforco.get("tipo_amostragem")
                    or esforco.get("tipo_de_amostragem")
                ),
                "id_esforco": esforco.get("id_esforco"),
                "esforco": esforco.get("esforco"),
                "unidade_esforco": esforco.get("unidade_esforco"),
                "contagem": result.get("numero_de_individuos"),
                "obs_resultado": result.get("observacoes"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    text_cols = [
        "nome_campanha",
        "nome_ponto",
        "empreendimento",
        "empreendimento_assignment_source",
        "nome_cientifico",
        "nome_popular",
        "ordem",
        "familia",
    ]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
    df["id_esforco"] = pd.to_numeric(df["id_esforco"], errors="coerce").fillna(-1).astype(int)
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    df["esforco"] = pd.to_numeric(df["esforco"], errors="coerce")
    return df


def _load_sampling_units_df(project_id: int, env_file: Optional[str]) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    empreendimentos = paginate(
        sb,
        "empreendimentos",
        filters={"id_projeto": int(project_id)},
        select="id_empreendimento,nome",
    )
    emp_map = {e["id_empreendimento"]: e["nome"] for e in empreendimentos}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Avifauna"},
        select="id_esforco,id_ponto_coleta,esforco,unidade_esforco",
    )
    esforcos = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for esforco in esforcos:
        ponto = pontos_map.get(esforco.get("id_ponto_coleta"), {})
        empreendimento, assignment_source = _resolve_empreendimento(
            ponto.get("nome_ponto"),
            ponto.get("id_empreendimento"),
            emp_map,
        )
        rows.append(
            {
                "id_esforco": esforco.get("id_esforco"),
                "nome_campanha": camp_map.get(ponto.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": ponto.get("nome_ponto"),
                "empreendimento": empreendimento,
                "empreendimento_assignment_source": assignment_source,
                "esforco": esforco.get("esforco"),
                "unidade_esforco": esforco.get("unidade_esforco"),
            }
        )

    df_units = pd.DataFrame(rows)
    if df_units.empty:
        return df_units

    for col in ["nome_campanha", "nome_ponto", "empreendimento", "empreendimento_assignment_source"]:
        df_units[col] = df_units[col].astype(str).str.strip()
    df_units["id_esforco"] = pd.to_numeric(df_units["id_esforco"], errors="coerce").fillna(-1).astype(int)
    df_units["esforco"] = pd.to_numeric(df_units["esforco"], errors="coerce")
    return df_units


def _save_premises_table(df: pd.DataFrame, output_dir: Path, generated_files: list[str]) -> None:
    premises = (
        df[["nome_ponto", "empreendimento", "empreendimento_assignment_source"]]
        .drop_duplicates()
        .sort_values(["empreendimento", "nome_ponto"])
        .reset_index(drop=True)
    )
    out = output_dir / "00_premissas_pontos_empreendimentos_avifauna.xlsx"
    premises.to_excel(out, index=False, engine="openpyxl")
    generated_files.append(str(out))


def _save_abundance_figures_avifauna(
    df_area: pd.DataFrame,
    theme: dict,
    output_png: Path,
    *,
    top_n: int = 25,
) -> dict[str, float]:
    grouped = (
        df_area.groupby("nome_cientifico", as_index=False)["contagem"]
        .sum()
        .sort_values(["contagem", "nome_cientifico"], ascending=[False, True])
        .reset_index(drop=True)
    )
    total = float(grouped["contagem"].sum()) if not grouped.empty else 0.0
    richness = int(grouped["nome_cientifico"].nunique()) if not grouped.empty else 0

    plot_df = grouped.copy()
    if len(plot_df) > top_n:
        top = plot_df.head(top_n).copy()
        remainder = plot_df.iloc[top_n:].copy()
        remainder_count = float(remainder["contagem"].sum())
        plot_df = pd.concat(
            [
                top,
                pd.DataFrame(
                    [
                        {
                            "nome_cientifico": f"Demais esp\u00e9cies (n={len(remainder)})",
                            "contagem": remainder_count,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    if total > 0:
        plot_df["abund_relativa_pct"] = plot_df["contagem"] / total * 100.0
    else:
        plot_df["abund_relativa_pct"] = 0.0

    n_rows = max(len(plot_df), 1)
    fig_h = min(max(7.5, 0.34 * n_rows + 2.2), 13.5)
    fig, ax = plt.subplots(figsize=(15, fig_h), dpi=int(theme.get("dpi", 600)))

    y = np.arange(n_rows)
    color = str(theme.get("primary_hex", "#11420C"))
    bars = ax.barh(
        y,
        plot_df["abund_relativa_pct"].values,
        height=0.62,
        color=color,
        edgecolor="black",
        linewidth=0.7,
        zorder=2,
    )

    labels = [str(value) for value in plot_df["nome_cientifico"].tolist()]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    for tick in ax.get_yticklabels():
        if tick.get_text().startswith("Demais esp\u00e9cies"):
            tick.set_fontstyle("normal")
            tick.set_fontweight("bold")
        else:
            tick.set_fontstyle("italic")
        tick.set_fontsize(11 if n_rows > 20 else 12)
    ax.invert_yaxis()

    max_pct = float(plot_df["abund_relativa_pct"].max()) if not plot_df.empty else 0.0
    ax.set_xlim(0, max(max_pct * 1.28, 5.0))

    for bar, pct, count in zip(bars, plot_df["abund_relativa_pct"].values, plot_df["contagem"].values):
        ax.text(
            float(bar.get_width()) + max(max_pct * 0.012, 0.08),
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}% | N={int(count)}",
            ha="left",
            va="center",
            fontsize=11,
            color="black",
        )

    apply_theme(ax, theme, xlabel="Abund\u00e2ncia relativa (%)", ylabel="Esp\u00e9cie")
    place_legend_below_x_axis(
        fig,
        ax,
        theme,
        handles=[Patch(facecolor=color, edgecolor="black", label="Abund\u00e2ncia relativa (%) e N")],
        labels=["Abund\u00e2ncia relativa (%) e N"],
        ncol=1,
    )
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(output_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)

    return {
        "riqueza_observada": float(richness),
        "abundancia_total": float(total),
        "species_plotted": float(len(plot_df)),
        "top_n": float(top_n),
    }


def _save_descriptive_report(details: dict[str, Any], output_dir: Path, generated_files: list[str]) -> None:
    text_lines = [
        "Relatorio descritivo - Avifauna",
        "",
        f"Area de estudo analisada: {TARGET_PCH_NAME}",
        f"Area Controle analisada: {TARGET_CONTROL_NAME}",
        f"Registros utilizados: {details.get('rows_loaded', 0)}",
        f"Especies totais: {details.get('species_total', 0)}",
        "",
        "Premissas:",
        "- Pontos com id_empreendimento preenchido usam o cadastro do banco.",
        "- Pontos de Avifauna sem id_empreendimento foram classificados por prefixo do ponto.",
        "- Prefixos: CO=Area Controle; DG/RNDG=Dores de Guanhaes; FO/RNFO=Fortuna II; JC/RNJC=Jacare; SP/RNSP=Senhora do Porto.",
        "",
        "6.1 Riqueza, composicao e abundancia:",
        "- Tabelas de especies por area geradas em excel.",
        "- Figuras de abundancia total e relativa geradas para area de estudo e controle.",
        "",
        "6.2 Suficiencia amostral:",
        "- Estimadores (Sobs, Jackknife 1, Bootstrap) calculados para area de estudo e controle.",
        "- Curvas do coletor geradas para as duas areas.",
        "",
        "6.3 Indices de diversidade:",
        "- Shannon, Pielou e Simpson calculados em excel e figura comparativa.",
        "",
        "6.4 Similaridade:",
        "- Indice de Jaccard calculado entre area de estudo e controle.",
        "- Dendrogramas de similaridade gerados.",
        "",
        "6.5 Diagrama de Venn:",
        "- Sobreposicao de especies entre area de estudo e controle gerada.",
        "",
        "6.6-6.8 Tabela geral:",
        "- Consolidacao de ameacadas/endemicas/raras/exoticas/cinegeticas/xerimbabo gerada.",
    ]
    out_txt = output_dir / "6_relatorio_descritivo_avifauna.txt"
    out_txt.write_text("\n".join(text_lines), encoding="utf-8")
    generated_files.append(str(out_txt))


def run_avifauna_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    masto.TARGET_PCH_NAME = TARGET_PCH_NAME
    masto.TARGET_CONTROL_NAME = TARGET_CONTROL_NAME

    df = _load_avifauna_df(project_id=project_id, env_file=env_file)
    if df.empty:
        return {
            "rows_loaded": 0,
            "executed_blocks": [],
            "generated_files": [],
            "warning": "Sem dados de avifauna para o projeto informado.",
        }

    block_sel = str(block).strip().lower()
    generated_files: list[str] = []
    executed_blocks: list[str] = []

    df_pch = masto._subset_by_empreendimento(df, TARGET_PCH_NAME)
    df_control = masto._subset_by_empreendimento(df, TARGET_CONTROL_NAME)

    details: dict[str, Any] = {
        "rows_loaded": int(len(df)),
        "species_total": int(df["nome_cientifico"].nunique()),
        "pch_rows": int(len(df_pch)),
        "control_rows": int(len(df_control)),
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()),
        "empreendimentos": sorted(df["empreendimento"].dropna().astype(str).unique().tolist()),
        "assignment_sources": sorted(
            df["empreendimento_assignment_source"].dropna().astype(str).unique().tolist()
        ),
    }

    _save_premises_table(df, output_dir, generated_files)

    if block_sel in {"6.1", "61", "all"}:
        tab_pch = masto._build_species_list(df_pch)
        tab_ctrl = masto._build_species_list(df_control)
        pch_slug = masto._area_slug(TARGET_PCH_NAME)
        ctrl_slug = masto._area_slug(TARGET_CONTROL_NAME)

        out_pch = output_dir / f"6_1_tabela_especies_{pch_slug}.xlsx"
        out_ctrl = output_dir / f"6_1_tabela_especies_{ctrl_slug}.xlsx"
        tab_pch.to_excel(out_pch, index=False, engine="openpyxl")
        tab_ctrl.to_excel(out_ctrl, index=False, engine="openpyxl")
        generated_files.extend([str(out_pch), str(out_ctrl)])

        out_fig_pch = output_dir / f"6_1_figura_abundancia_total_relativa_avifauna_{pch_slug}.png"
        out_fig_ctrl = output_dir / f"6_1_figura_abundancia_avifauna_{ctrl_slug}.png"

        metrics_pch = _save_abundance_figures_avifauna(df_area=df_pch, theme=theme, output_png=out_fig_pch)
        _save_abundance_figures_avifauna(df_area=df_control, theme=theme, output_png=out_fig_ctrl)
        generated_files.extend([str(out_fig_pch), str(out_fig_ctrl)])

        details["block_6_1"] = metrics_pch
        executed_blocks.append("6.1")

    if block_sel in {"6.2", "62", "all"}:
        df_units = _load_sampling_units_df(project_id=project_id, env_file=env_file)
        df_units_pch = masto._subset_by_empreendimento(df_units, TARGET_PCH_NAME) if not df_units.empty else pd.DataFrame()
        df_units_ctrl = masto._subset_by_empreendimento(df_units, TARGET_CONTROL_NAME) if not df_units.empty else pd.DataFrame()

        est_pch = masto._save_estimators_and_curve(
            df_pch,
            masto._area_slug(TARGET_PCH_NAME),
            theme,
            output_dir,
            generated_files,
            sampling_units_df=df_units_pch,
        )
        est_ctrl = masto._save_estimators_and_curve(
            df_control,
            masto._area_slug(TARGET_CONTROL_NAME),
            theme,
            output_dir,
            generated_files,
            sampling_units_df=df_units_ctrl,
        )
        details["block_6_2"] = {"estudo": est_pch, "controle": est_ctrl}
        executed_blocks.append("6.2")

    if block_sel in {"6.3", "63", "all"}:
        masto._save_diversity(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.3")

    if block_sel in {"6.4", "64", "all"}:
        masto._save_similarity_and_venn(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.4")
        if block_sel in {"all"}:
            executed_blocks.append("6.5")

    if block_sel in {"6.5", "65"}:
        masto._save_similarity_and_venn(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.5")

    if block_sel in {"6.6", "66", "6.7", "67", "6.8", "68", "all"}:
        masto._save_general_status_tables(df, output_dir, generated_files)
        executed_blocks.extend(["6.6", "6.7", "6.8"])

    if block_sel in {"all"}:
        _save_descriptive_report(details, output_dir, generated_files)

    if not executed_blocks:
        raise ValueError(
            "Unsupported block for avifauna pipeline. "
            "Use '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '6.8' or 'all'."
        )

    details["executed_blocks"] = sorted(set(executed_blocks), key=lambda item: float(item))
    details["generated_files"] = generated_files
    return details
