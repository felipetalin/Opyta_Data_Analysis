from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import (
    apply_theme,
    get_figsize_by_complexity,
    get_tight_layout_rect,
    green_palette_from_hex,
    place_legend_below_x_axis,
)
from opyta_analysis.validators import validate_axes_style


def _normalize_text(value: str) -> str:
    txt = str(value).strip().lower()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    txt = re.sub(r"[^a-z0-9]+", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def _group_matches(group_db: str, group_target: str) -> bool:
    db = _normalize_text(group_db)
    target = _normalize_text(group_target)

    if "ictio" in target or "ichth" in target:
        return "ictio" in db or "ichth" in db
    if "zooplan" in target or "zoo plan" in target:
        return "zoo" in db and "plan" in db
    if "fito" in target:
        return "fito" in db

    return db == target


def _get_col(df_: pd.DataFrame, *cands: str) -> str | None:
    for c in cands:
        if c in df_.columns:
            return c
    return None


def _safe_group_name(group: str) -> str:
    normalized = _normalize_text(group).replace(" ", "_")
    return re.sub(r"[^a-z0-9_]+", "", normalized)


def _apply_project_fallback_filter(df: pd.DataFrame, project_id: int) -> pd.DataFrame:
    if "id_projeto" in df.columns:
        return df

    project_hints = {
        62: {
            "nome_empresa_contains": "rocha consultoria",
            "nome_projeto_contains": "sam metais",
        }
    }

    hint = project_hints.get(int(project_id))
    if not hint:
        return df

    if "nome_empresa" not in df.columns or "nome_projeto" not in df.columns:
        return df

    empresa_norm = df["nome_empresa"].astype(str).map(_normalize_text)
    projeto_norm = df["nome_projeto"].astype(str).map(_normalize_text)
    mask = empresa_norm.str.contains(hint["nome_empresa_contains"], na=False) & projeto_norm.str.contains(
        hint["nome_projeto_contains"], na=False
    )
    return df[mask].copy()


def _load_ictio_df(project_id: int, group: str, env_file: str | None) -> pd.DataFrame:
    sb = get_client(env_file)

    # Fast path: request only the target biological group from the backend.
    rows = paginate(
        sb,
        "biota_analise_consolidada",
        filters={"grupo_biologico": group},
        select="*",
    )
    if not rows:
        rows = paginate(
            sb,
            "biota_analise_consolidada",
            select="*",
        )
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "id_projeto" in df.columns:
        df = df[pd.to_numeric(df["id_projeto"], errors="coerce") == int(project_id)].copy()
    else:
        df = _apply_project_fallback_filter(df, project_id)

    if "grupo_biologico" not in df.columns:
        return pd.DataFrame()

    df = df[df["grupo_biologico"].astype(str).map(lambda x: _group_matches(x, group))].copy()
    return df.reset_index(drop=True)


def _mode_or_first(series: pd.Series):
    s = series.dropna()
    if s.empty:
        return np.nan
    modes = s.mode()
    return modes.iloc[0] if not modes.empty else s.iloc[0]


def _extrair_numero(txt: str) -> int:
    m = re.search(r"(\d+)", str(txt))
    return int(m.group(1)) if m else 999999


def _ordenar_pontos(lista_pontos: list[str]) -> list[str]:
    return sorted(lista_pontos, key=lambda x: (_extrair_numero(x), str(x)))


def _campanha_sort_key(campaign: str) -> tuple[int, str]:
    c_norm = _normalize_text(campaign)
    if "1" in c_norm and "seca" in c_norm:
        return (1, c_norm)
    if "2" in c_norm and "chuva" in c_norm:
        return (2, c_norm)
    if "seca" in c_norm:
        return (1, c_norm)
    if "chuva" in c_norm:
        return (2, c_norm)
    return (99, c_norm)


def _normalizar_tipo_amostragem(valor: str) -> str:
    s = _normalize_text(valor)
    if "quantit" in s:
        return "quantitativo"
    if "qualit" in s:
        return "qualitativo"
    return "outro"


def _run_block_3(df_projeto: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)
    out_xlsx = output_dir / f"01_tabela_composicao_{group_slug}.xlsx"

    if df_projeto.empty:
        pd.DataFrame(columns=["Nome Cientifico", "Ocorrencia (Campanhas)"]).to_excel(
            out_xlsx, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_xlsx))
        return {"taxa_total": 0, "warning": "dataset vazio"}

    if "nome_campanha" not in df_projeto.columns or "nome_cientifico" not in df_projeto.columns:
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 3 ICTIO: nome_campanha, nome_cientifico")

    def _camp_short(c: str) -> str:
        cn = _normalize_text(c)
        if "1" in cn and "seca" in cn:
            return "C1"
        if "2" in cn and "chuva" in cn:
            return "C2"
        return str(c).strip()

    df_tmp = df_projeto.copy()
    df_tmp["nome_campanha"] = df_tmp["nome_campanha"].astype(str).str.strip()
    df_tmp["nome_cientifico"] = df_tmp["nome_cientifico"].astype(str).str.strip()

    ocorrencia = (
        df_tmp.groupby("nome_cientifico")["nome_campanha"]
        .apply(lambda s: sorted({_camp_short(x) for x in s.dropna().unique().tolist()}))
        .reset_index(name="ocorr_lista")
    )
    ocorrencia["Ocorrencia (Campanhas)"] = ocorrencia["ocorr_lista"].apply(lambda lst: " e ".join(lst))
    ocorrencia = ocorrencia.drop(columns=["ocorr_lista"])

    agg_dict: dict = {}
    if "ordem" in df_tmp.columns:
        agg_dict["ordem"] = ("ordem", _mode_or_first)
    if "familia" in df_tmp.columns:
        agg_dict["familia"] = ("familia", _mode_or_first)
    if "nome_popular" in df_tmp.columns:
        agg_dict["nome_popular"] = ("nome_popular", _mode_or_first)
    if "origem" in df_tmp.columns:
        agg_dict["origem"] = ("origem", _mode_or_first)

    if agg_dict:
        tabela = df_tmp.groupby("nome_cientifico", as_index=False).agg(**agg_dict)
    else:
        tabela = df_tmp[["nome_cientifico"]].drop_duplicates().reset_index(drop=True)

    tabela = tabela.merge(ocorrencia, on="nome_cientifico", how="left")

    tabela = tabela.rename(
        columns={
            "ordem": "Ordem",
            "familia": "Familia",
            "nome_popular": "Nome Popular",
            "origem": "Origem",
            "nome_cientifico": "Nome Cientifico",
        }
    )

    desired = ["Ordem", "Familia", "Nome Popular", "Origem", "Nome Cientifico", "Ocorrencia (Campanhas)"]
    existing = [c for c in desired if c in tabela.columns]
    tabela = tabela[existing]

    sort_cols = [c for c in ["Ordem", "Familia", "Nome Cientifico"] if c in tabela.columns]
    if sort_cols:
        tabela = tabela.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    tabela.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    return {"taxa_total": int(len(tabela))}


def _run_block_5(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df = output_dir / f"02_df_riqueza_por_ponto_{group_slug}.xlsx"
    out_png = output_dir / f"02_grafico_riqueza_por_ponto_{group_slug}.png"

    if df_projeto.empty:
        pd.DataFrame(columns=["nome_campanha", "nome_ponto", "riqueza"]).to_excel(out_df, index=False, engine="openpyxl")
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_ponto", "nome_cientifico"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 5 ICTIO: {', '.join(missing)}")

    richness = (
        df_projeto.groupby(["nome_campanha", "nome_ponto"])["nome_cientifico"]
        .nunique()
        .reset_index()
        .rename(columns={"nome_cientifico": "riqueza"})
    )

    richness["nome_campanha"] = richness["nome_campanha"].astype(str).str.strip()
    richness["nome_ponto"] = richness["nome_ponto"].astype(str).str.strip()

    campaigns = sorted(richness["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    points = _ordenar_pontos(richness["nome_ponto"].dropna().unique().tolist())

    richness.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if not campaigns or not points:
        return {"campaigns": campaigns, "points": points}

    color_list = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), max(len(campaigns), 1))
    color_map = {c: color_list[i] for i, c in enumerate(campaigns)}

    pivot = (
        richness.pivot_table(index="nome_ponto", columns="nome_campanha", values="riqueza", aggfunc="sum", fill_value=0)
        .reindex(index=points, columns=campaigns, fill_value=0)
    )

    size = get_figsize_by_complexity(theme, n_categories=len(points), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))

    x = np.arange(len(points))
    n = max(len(campaigns), 1)
    width = 0.8 / n

    for i, campaign in enumerate(campaigns):
        values = pivot[campaign].values
        bars = ax.bar(
            x + (i - (n - 1) / 2) * width,
            values,
            width=width,
            label=campaign,
            color=color_map[campaign],
            edgecolor="black",
            linewidth=0.8,
        )
        for bar, v in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                float(v),
                f"{int(v)}",
                ha="center",
                va="bottom",
                fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
            )

    ax.set_xticks(x)
    ax.set_xticklabels(points, ha="right")
    apply_theme(
        ax,
        theme,
        xlabel="Ponto amostral",
        ylabel="Riqueza taxonomica",
        x_tick_rotation=45,
    )
    place_legend_below_x_axis(fig, ax, theme, ncol=min(len(campaigns), int(theme.get("legend_max_cols", 2))))
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.0))

    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"campaigns": campaigns, "points": points}


def _run_block_6(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df = output_dir / f"03_df_abundancia_por_ponto_{group_slug}.xlsx"
    out_png = output_dir / f"03_grafico_abundancia_por_ponto_{group_slug}.png"

    if df_projeto.empty:
        pd.DataFrame(columns=["nome_campanha", "nome_ponto", "abundancia_total"]).to_excel(
            out_df, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_ponto", "contagem"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 6 ICTIO: {', '.join(missing)}")

    df_quant = df_projeto.copy()
    if "tipo_amostragem" in df_quant.columns:
        tipo_norm = df_quant["tipo_amostragem"].astype(str).map(_normalizar_tipo_amostragem)
        df_quant = df_quant[tipo_norm == "quantitativo"].copy()

    df_quant["contagem"] = pd.to_numeric(df_quant["contagem"], errors="coerce").fillna(0)

    abundancia = (
        df_quant.groupby(["nome_campanha", "nome_ponto"], dropna=False)["contagem"]
        .sum()
        .reset_index()
        .rename(columns={"contagem": "abundancia_total"})
    )

    abundancia["nome_campanha"] = abundancia["nome_campanha"].astype(str).str.strip()
    abundancia["nome_ponto"] = abundancia["nome_ponto"].astype(str).str.strip()

    campaigns = sorted(abundancia["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    points = _ordenar_pontos(abundancia["nome_ponto"].dropna().unique().tolist())

    abundancia.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if abundancia.empty or not campaigns or not points:
        return {"campaigns": campaigns, "points": points}

    color_list = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), max(len(campaigns), 1))
    color_map = {c: color_list[i] for i, c in enumerate(campaigns)}

    pivot = (
        abundancia.pivot_table(
            index="nome_ponto",
            columns="nome_campanha",
            values="abundancia_total",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(index=points, columns=campaigns, fill_value=0)
    )

    size = get_figsize_by_complexity(theme, n_categories=len(points), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))

    x = np.arange(len(points))
    n = max(len(campaigns), 1)
    width = 0.8 / n

    for i, campaign in enumerate(campaigns):
        values = pivot[campaign].values
        bars = ax.bar(
            x + (i - (n - 1) / 2) * width,
            values,
            width=width,
            label=campaign,
            color=color_map[campaign],
            edgecolor="black",
            linewidth=0.8,
        )
        for bar, v in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                float(v),
                f"{int(v)}",
                ha="center",
                va="bottom",
                fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
            )

    ax.set_xticks(x)
    ax.set_xticklabels(points, ha="right")
    apply_theme(
        ax,
        theme,
        xlabel="Ponto amostral",
        ylabel="Abundancia total (n de individuos)",
        x_tick_rotation=45,
    )
    place_legend_below_x_axis(fig, ax, theme, ncol=min(len(campaigns), int(theme.get("legend_max_cols", 2))))
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.0))

    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"campaigns": campaigns, "points": points}


def _run_block_8(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df = output_dir / f"06_df_cpue_por_ponto_{group_slug}.xlsx"
    out_png_cpuen = output_dir / f"06_grafico_cpuen_por_ponto_{group_slug}.png"
    out_png_cpueb = output_dir / f"07_grafico_cpueb_por_ponto_{group_slug}.png"

    if df_projeto.empty:
        pd.DataFrame(columns=["nome_campanha", "nome_ponto", "cpuen", "cpueb"]).to_excel(
            out_df, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_ponto", "tipo_amostragem", "esforco", "contagem", "biomassa"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 8 ICTIO: {', '.join(missing)}")

    df_quant = df_projeto.copy()
    tipo_norm = df_quant["tipo_amostragem"].astype(str).map(_normalizar_tipo_amostragem)
    df_quant = df_quant[tipo_norm == "quantitativo"].copy()

    if df_quant.empty:
        pd.DataFrame(columns=["nome_campanha", "nome_ponto", "cpuen", "cpueb"]).to_excel(
            out_df, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "sem registros quantitativos para CPUE"}

    df_quant["esforco"] = pd.to_numeric(df_quant["esforco"], errors="coerce")
    df_quant["contagem"] = pd.to_numeric(df_quant["contagem"], errors="coerce")
    df_quant["biomassa"] = pd.to_numeric(df_quant["biomassa"], errors="coerce")

    df_quant = df_quant.dropna(subset=["esforco"]).copy()
    df_quant = df_quant[df_quant["esforco"] > 0].copy()

    if df_quant.empty:
        pd.DataFrame(columns=["nome_campanha", "nome_ponto", "cpuen", "cpueb"]).to_excel(
            out_df, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "esforco invalido para CPUE"}

    df_quant["cpuen"] = (df_quant["contagem"].fillna(0) / df_quant["esforco"]) * 100
    df_quant["cpueb"] = (df_quant["biomassa"].fillna(0) / df_quant["esforco"]) * 100

    df_cpue = (
        df_quant.groupby(["nome_campanha", "nome_ponto"], dropna=False)[["cpuen", "cpueb"]]
        .sum()
        .reset_index()
    )

    df_cpue["nome_campanha"] = df_cpue["nome_campanha"].astype(str).str.strip()
    df_cpue["nome_ponto"] = df_cpue["nome_ponto"].astype(str).str.strip()

    campaigns = sorted(df_cpue["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    points = _ordenar_pontos(df_cpue["nome_ponto"].dropna().unique().tolist())

    df_cpue.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if df_cpue.empty or not campaigns or not points:
        return {"campaigns": campaigns, "points": points}

    color_list = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), max(len(campaigns), 1))
    color_map = {c: color_list[i] for i, c in enumerate(campaigns)}

    def _plot_metric(metric_col: str, ylabel: str, out_png: Path, decimals: int) -> None:
        pivot = (
            df_cpue.pivot_table(
                index="nome_ponto",
                columns="nome_campanha",
                values=metric_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reindex(index=points, columns=campaigns, fill_value=0)
        )

        size = get_figsize_by_complexity(theme, n_categories=len(points), prefer_landscape=True)
        fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))

        x = np.arange(len(points))
        n = max(len(campaigns), 1)
        width = 0.8 / n

        for i, campaign in enumerate(campaigns):
            values = pivot[campaign].values
            bars = ax.bar(
                x + (i - (n - 1) / 2) * width,
                values,
                width=width,
                label=campaign,
                color=color_map[campaign],
                edgecolor="black",
                linewidth=0.8,
            )
            for bar, v in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    float(v),
                    f"{float(v):.{decimals}f}",
                    ha="center",
                    va="bottom",
                    fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
                )

        ax.set_xticks(x)
        ax.set_xticklabels(points, ha="right")
        apply_theme(
            ax,
            theme,
            xlabel="Ponto amostral",
            ylabel=ylabel,
            x_tick_rotation=45,
        )
        place_legend_below_x_axis(fig, ax, theme, ncol=min(len(campaigns), int(theme.get("legend_max_cols", 2))))
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.0))

        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))

    _plot_metric("cpuen", "CPUEn (ind/100m2)", out_png_cpuen, decimals=2)
    _plot_metric("cpueb", "CPUEb (g/100m2)", out_png_cpueb, decimals=2)

    return {"campaigns": campaigns, "points": points}


def _run_block_9(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df_cpuen = output_dir / f"08_df_cpuen_por_especie_{group_slug}.xlsx"
    out_df_cpueb = output_dir / f"09_df_cpueb_por_especie_{group_slug}.xlsx"
    out_png_cpuen = output_dir / f"08_grafico_cpuen_por_especie_{group_slug}.png"
    out_png_cpueb = output_dir / f"09_grafico_cpueb_por_especie_{group_slug}.png"

    base_cols = ["nome_cientifico", "campanha_1", "campanha_2"]
    if df_projeto.empty:
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb, index=False, engine="openpyxl")
        generated_files.extend([str(out_df_cpuen), str(out_df_cpueb)])
        return {"campaigns": [], "species": 0, "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_cientifico", "tipo_amostragem", "esforco", "contagem", "biomassa"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 9 ICTIO: {', '.join(missing)}")

    df_quant = df_projeto.copy()
    tipo_norm = df_quant["tipo_amostragem"].astype(str).map(_normalizar_tipo_amostragem)
    df_quant = df_quant[tipo_norm == "quantitativo"].copy()

    df_quant["esforco"] = pd.to_numeric(df_quant["esforco"], errors="coerce")
    df_quant["contagem"] = pd.to_numeric(df_quant["contagem"], errors="coerce").fillna(0)
    df_quant["biomassa"] = pd.to_numeric(df_quant["biomassa"], errors="coerce").fillna(0)
    df_quant = df_quant[df_quant["esforco"].notna() & (df_quant["esforco"] > 0)].copy()

    if df_quant.empty:
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb, index=False, engine="openpyxl")
        generated_files.extend([str(out_df_cpuen), str(out_df_cpueb)])
        return {"campaigns": [], "species": 0, "warning": "sem dados quantitativos validos para CPUE por especie"}

    df_quant["cpuen"] = (df_quant["contagem"] / df_quant["esforco"]) * 100
    df_quant["cpueb"] = (df_quant["biomassa"] / df_quant["esforco"]) * 100

    df_cpue_sp = (
        df_quant.groupby(["nome_campanha", "nome_cientifico"], dropna=False)[["cpuen", "cpueb"]]
        .sum()
        .reset_index()
    )
    df_cpue_sp["nome_campanha"] = df_cpue_sp["nome_campanha"].astype(str).str.strip()
    df_cpue_sp["nome_cientifico"] = df_cpue_sp["nome_cientifico"].astype(str).str.strip()

    campaigns = sorted(df_cpue_sp["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    if len(campaigns) < 2:
        campaigns = campaigns + ["campanha_2"]

    cpuen_sp = (
        df_cpue_sp.pivot_table(
            index="nome_cientifico",
            columns="nome_campanha",
            values="cpuen",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=campaigns[:2], fill_value=0)
        .fillna(0)
    )

    cpueb_sp = (
        df_cpue_sp.pivot_table(
            index="nome_cientifico",
            columns="nome_campanha",
            values="cpueb",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=campaigns[:2], fill_value=0)
        .fillna(0)
    )

    order_species = cpuen_sp.sum(axis=1).sort_values(ascending=True).index.tolist()
    cpuen_sp = cpuen_sp.loc[order_species].reset_index()
    cpueb_sp = cpueb_sp.loc[order_species].reset_index()

    cpuen_sp.to_excel(out_df_cpuen, index=False, engine="openpyxl")
    cpueb_sp.to_excel(out_df_cpueb, index=False, engine="openpyxl")
    generated_files.extend([str(out_df_cpuen), str(out_df_cpueb)])

    c1 = campaigns[0]
    c2 = campaigns[1]
    colors = green_palette_from_hex(str(theme.get("primary_hex", "#11420C")), 2)

    def _plot_horizontal(df_plot: pd.DataFrame, metric_label: str, out_png: Path) -> None:
        labels = df_plot["nome_cientifico"].tolist()
        y = np.arange(len(labels))
        height = 0.38

        fig_h = max(8.0, 0.32 * max(len(labels), 10))
        fig, ax = plt.subplots(figsize=(15, fig_h), dpi=int(theme.get("dpi", 600)))

        bars_1 = ax.barh(y - height / 2, df_plot[c1].values, height, label=c1, color=colors[0], edgecolor="black")
        bars_2 = ax.barh(y + height / 2, df_plot[c2].values, height, label=c2, color=colors[1], edgecolor="black")

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontstyle="italic")
        apply_theme(
            ax,
            theme,
            xlabel=metric_label,
            ylabel="Especie",
            x_tick_rotation=0,
        )
        ax.grid(axis="y", linestyle="-", linewidth=0.7, alpha=0.35)
        ax.grid(axis="x", visible=False)

        for bars in (bars_1, bars_2):
            xmax = max((b.get_width() for b in bars), default=0)
            offset = xmax * 0.02 if xmax > 0 else 0.1
            for b in bars:
                w = b.get_width()
                ax.text(
                    w + offset,
                    b.get_y() + b.get_height() / 2,
                    f"{float(w):.2f}",
                    va="center",
                    ha="left",
                    fontsize=int(theme.get("annotation_size", 11)),
                )

        place_legend_below_x_axis(fig, ax, theme, ncol=2)
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.0))
        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))

    _plot_horizontal(cpuen_sp, "CPUEn (ind/100m2)", out_png_cpuen)
    _plot_horizontal(cpueb_sp, "CPUEb (g/100m2)", out_png_cpueb)

    return {"campaigns": campaigns[:2], "species": int(len(order_species))}


def _shannon(counts: np.ndarray) -> float:
    c = np.array(counts, dtype=float)
    c = c[c > 0]
    if len(c) == 0:
        return 0.0
    p = c / c.sum()
    return float(-np.sum(p * np.log(p)))


def _pielou(counts: np.ndarray) -> float:
    c = np.array(counts, dtype=float)
    c = c[c > 0]
    if len(c) <= 1:
        return 0.0
    return float(_shannon(c) / np.log(len(c)))


def _jackknife_1(pa_matrix: np.ndarray) -> float:
    k = int(pa_matrix.shape[0])
    if k == 0:
        return 0.0
    spp_occ = pa_matrix.sum(axis=0)
    s_obs = int((spp_occ > 0).sum())
    q1 = int((spp_occ == 1).sum())
    return float(s_obs + q1 * ((k - 1) / k))


def _run_block_10(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "tipo_amostragem"]
    if any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 10 ICTIO")

    df_div = df_projeto[df_projeto["tipo_amostragem"].astype(str).str.contains("quantit", case=False, na=False)].copy()
    if df_div.empty:
        return {"campaigns": [], "warning": "sem dados quantitativos"}

    for c in ["nome_campanha", "nome_ponto", "nome_cientifico"]:
        df_div[c] = df_div[c].astype(str).str.strip()
    df_div["contagem"] = pd.Series(pd.to_numeric(df_div["contagem"], errors="coerce"), index=df_div.index).fillna(0)

    campaigns = sorted(df_div["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    rows = []
    for camp in campaigns:
        df_c = df_div[df_div["nome_campanha"] == camp].copy()
        if df_c.empty:
            continue
        mat = df_c.pivot_table(
            index="nome_ponto",
            columns="nome_cientifico",
            values="contagem",
            aggfunc="sum",
            fill_value=0,
            observed=False,
        )
        for p in mat.index:
            vec = mat.loc[p].values
            rows.append({"nome_campanha": camp, "nome_ponto": p, "Shannon_H": _shannon(vec), "Pielou_J": _pielou(vec)})

        total_vec = mat.sum(axis=0).values
        rows.append(
            {
                "nome_campanha": camp,
                "nome_ponto": f"{camp} (Geral)",
                "Shannon_H": _shannon(total_vec),
                "Pielou_J": _pielou(total_vec),
            }
        )

    df_out = pd.DataFrame(rows)
    if df_out.empty:
        return {"campaigns": campaigns, "warning": "sem resultados calculaveis"}

    out_df = output_dir / f"10_df_diversidade_alfa_{group_slug}.xlsx"
    df_out.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    x = np.arange(len(df_out))
    labels = df_out["nome_ponto"].tolist()
    sh = df_out["Shannon_H"].tolist()
    pj = df_out["Pielou_J"].tolist()

    size = get_figsize_by_complexity(theme, n_categories=len(labels), prefer_landscape=True)
    fig, ax1 = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    bars = ax1.bar(
        x,
        sh,
        color=str(theme.get("primary_hex", "#11420C")),
        edgecolor="black",
        linewidth=0.8,
        label="Diversidade (H')",
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, ha="right")
    apply_theme(ax1, theme, xlabel="Ponto amostral", ylabel="Shannon (H')", x_tick_rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        pj,
        marker="o",
        linestyle="None",
        color=str(theme.get("secondary_hex", "#6A8F63")),
        markersize=6,
        label="Equitabilidade (J')",
    )
    ax2.set_ylabel("Pielou (J')")
    ax2.set_ylim(0, 1.1)

    if campaigns:
        split_n = df_out[df_out["nome_campanha"] == campaigns[0]].shape[0]
        if 0 < split_n < len(x):
            ax1.axvline(x=split_n - 0.5, color="#888888", linestyle="--", linewidth=1.2)

    for b, v in zip(bars, sh):
        ax1.text(
            b.get_x() + b.get_width() / 2,
            float(v),
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=int(theme.get("annotation_size", 14)),
        )

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    place_legend_below_x_axis(fig, ax1, theme, handles=h1 + h2, labels=l1 + l2, ncol=2)
    validate_axes_style(ax1, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.06))

    out_png = output_dir / f"10_grafico_diversidade_alfa_{group_slug}.png"
    fig.savefig(str(out_png), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"campaigns": campaigns}


def _run_block_11(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "tipo_amostragem"]
    if any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 11 ICTIO")

    df_sim = df_projeto[df_projeto["tipo_amostragem"].astype(str).str.contains("quantit", case=False, na=False)].copy()
    if df_sim.empty:
        return {"points": 0, "warning": "sem dados quantitativos"}

    for c in ["nome_campanha", "nome_ponto", "nome_cientifico"]:
        df_sim[c] = df_sim[c].astype(str).str.strip()
    df_sim["contagem"] = pd.Series(pd.to_numeric(df_sim["contagem"], errors="coerce"), index=df_sim.index).fillna(0)

    mat = df_sim.pivot_table(
        index="nome_ponto",
        columns="nome_cientifico",
        values="contagem",
        aggfunc="sum",
        fill_value=0,
        observed=False,
    )
    mat = mat.loc[mat.sum(axis=1) > 0]
    if mat.shape[0] < 2:
        return {"points": int(mat.shape[0]), "warning": "pontos insuficientes para dendrograma"}

    dist_cond = pdist(mat.values, metric="braycurtis")
    dist_sq = squareform(dist_cond)
    z = linkage(dist_cond, method="average")

    out_mat = output_dir / f"11_df_matriz_comunidade_{group_slug}_seca_chuva_somadas.xlsx"
    mat.to_excel(out_mat, engine="openpyxl")
    generated_files.append(str(out_mat))

    out_dist = output_dir / f"11_df_distancias_braycurtis_{group_slug}_seca_chuva_somadas.xlsx"
    pd.DataFrame(dist_sq, index=mat.index, columns=mat.index).to_excel(out_dist, engine="openpyxl")
    generated_files.append(str(out_dist))

    size = get_figsize_by_complexity(theme, n_categories=int(mat.shape[0]), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    dendrogram(z, labels=mat.index.tolist(), orientation="right", ax=ax, color_threshold=None)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.0, 0.0)

    ticks_sim = np.arange(0, 101, 10)
    ticks_dist = 1 - (ticks_sim / 100.0)
    ax.set_xticks(ticks_dist)
    ax.set_xticklabels([str(t) for t in ticks_sim])

    apply_theme(ax, theme, xlabel="Similaridade de Bray-Curtis (%)", ylabel="")
    validate_axes_style(ax, theme)
    fig.tight_layout()

    out_png = output_dir / f"11_dendrograma_similaridade_{group_slug}_seca_chuva_somadas.png"
    fig.savefig(str(out_png), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))
    return {"points": int(mat.shape[0])}


def _run_block_12(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "tipo_amostragem"]
    if any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 12 ICTIO")

    df_suf = df_projeto[df_projeto["tipo_amostragem"].astype(str).str.contains("quantit", case=False, na=False)].copy()
    if df_suf.empty:
        return {"samples": 0, "warning": "sem dados quantitativos"}

    for c in ["nome_campanha", "nome_ponto", "nome_cientifico"]:
        df_suf[c] = df_suf[c].astype(str).str.strip()
    df_suf["contagem"] = pd.Series(pd.to_numeric(df_suf["contagem"], errors="coerce"), index=df_suf.index).fillna(0)
    df_suf["amostra_id"] = df_suf["nome_campanha"] + " | " + df_suf["nome_ponto"]

    mat = df_suf.pivot_table(
        index="amostra_id",
        columns="nome_cientifico",
        values="contagem",
        aggfunc="sum",
        fill_value=0,
        observed=False,
    )
    mat = mat.loc[mat.sum(axis=1) > 0]
    if mat.empty:
        return {"samples": 0, "warning": "amostras sem abundancia"}

    mat_pa = (mat > 0).astype(int)
    mat_pa = mat_pa.loc[mat_pa.sum(axis=1) > 0]
    n_samples = int(mat_pa.shape[0])
    if n_samples < 2:
        return {"samples": n_samples, "warning": "amostras insuficientes"}

    n_random = 200
    rng = np.random.default_rng(42)
    values = mat_pa.values
    sobs_curves = np.zeros((n_random, n_samples), dtype=float)
    sest_curves = np.zeros((n_random, n_samples), dtype=float)

    for r in range(n_random):
        idx = rng.permutation(n_samples)
        shuffled = values[idx, :]
        for i in range(1, n_samples + 1):
            subset = shuffled[:i, :]
            spp_occ = subset.sum(axis=0)
            sobs_curves[r, i - 1] = float((spp_occ > 0).sum())
            sest_curves[r, i - 1] = _jackknife_1(subset)

    mean_sobs = sobs_curves.mean(axis=0)
    mean_sest = sest_curves.mean(axis=0)
    std_sest = sest_curves.std(axis=0)
    x_axis = np.arange(1, n_samples + 1)

    df_curve = pd.DataFrame(
        {
            "n_amostras": x_axis,
            "riqueza_obs_media": mean_sobs,
            "riqueza_est_jackknife1_media": mean_sest,
            "jackknife1_desvio_padrao": std_sest,
            "jackknife1_inf": mean_sest - std_sest,
            "jackknife1_sup": mean_sest + std_sest,
        }
    )

    out_df = output_dir / f"12_df_curva_suficiencia_{group_slug}.xlsx"
    df_curve.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    size = get_figsize_by_complexity(theme, n_categories=n_samples, prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))

    obs_color = str(theme.get("primary_hex", "#11420C"))
    est_color = str(theme.get("secondary_hex", "#6A8F63"))

    ax.plot(x_axis, mean_sobs, linewidth=2.2, label="Riqueza observada", color=obs_color)
    ax.plot(x_axis, mean_sest, linewidth=2.2, label="Riqueza estimada (Jackknife 1)", color=est_color)
    ax.fill_between(x_axis, mean_sest - std_sest, mean_sest + std_sest, alpha=0.18, color=est_color)

    apply_theme(ax, theme, xlabel="Numero de unidades amostrais", ylabel="Riqueza")
    ax.text(
        x_axis[-1] + 0.15,
        mean_sobs[-1],
        f"{mean_sobs[-1]:.0f}",
        color="black",
        va="center",
        fontsize=int(theme.get("annotation_size", 14)),
    )
    ax.text(
        x_axis[-1] + 0.15,
        mean_sest[-1],
        f"{mean_sest[-1]:.1f}",
        color="black",
        va="center",
        fontsize=int(theme.get("annotation_size", 14)),
    )

    place_legend_below_x_axis(fig, ax, theme, ncol=2)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.04))

    out_png = output_dir / f"12_curva_suficiencia_amostral_{group_slug}.png"
    fig.savefig(str(out_png), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"samples": n_samples, "observed_final": float(mean_sobs[-1]), "jackknife_final": float(mean_sest[-1])}


def _run_block_13(df_projeto: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    if df_projeto.empty:
        out = pd.DataFrame(
            columns=[
                "occurrenceID",
                "basisOfRecord",
                "scientificName",
                "individualCount",
                "organismQuantity",
                "organismQuantityType",
            ]
        )
    else:
        c_proj = _get_col(df_projeto, "nome_projeto")
        c_emp = _get_col(df_projeto, "nome_empresa")
        c_camp = _get_col(df_projeto, "nome_campanha")
        c_ponto = _get_col(df_projeto, "nome_ponto")
        c_sci = _get_col(df_projeto, "nome_cientifico")
        c_reino = _get_col(df_projeto, "reino", "kingdom")
        c_filo = _get_col(df_projeto, "filo", "phylum")
        c_classe = _get_col(df_projeto, "classe", "class")
        c_ordem = _get_col(df_projeto, "ordem", "order")
        c_familia = _get_col(df_projeto, "familia", "family")
        c_genero = _get_col(df_projeto, "genero", "genus")
        c_lat = _get_col(df_projeto, "latitude", "lat", "decimalLatitude")
        c_lon = _get_col(df_projeto, "longitude", "lon", "decimalLongitude")
        c_date = _get_col(df_projeto, "data_campanha", "data_coleta", "eventDate")
        c_method = _get_col(df_projeto, "metodo", "metodo_amostragem", "samplingProtocol")
        c_count = _get_col(df_projeto, "contagem", "numero_de_individuos")
        c_bio = _get_col(df_projeto, "biomassa")
        c_effort = _get_col(df_projeto, "esforco")

        records = []
        for _, row in df_projeto.iterrows():
            proj = str(row.get(c_proj, "")) if c_proj else ""
            camp = str(row.get(c_camp, "")) if c_camp else ""
            ponto = str(row.get(c_ponto, "")) if c_ponto else ""
            sci = str(row.get(c_sci, "")) if c_sci else ""
            occurrence_id = "|".join([x for x in [proj, camp, ponto, sci] if x])

            count_val = pd.to_numeric(row.get(c_count), errors="coerce") if c_count else np.nan
            bio_val = pd.to_numeric(row.get(c_bio), errors="coerce") if c_bio else np.nan
            effort_val = pd.to_numeric(row.get(c_effort), errors="coerce") if c_effort else np.nan
            effort = "" if pd.isna(effort_val) else float(effort_val)

            records.append(
                {
                    "occurrenceID": occurrence_id,
                    "basisOfRecord": "HumanObservation",
                    "institutionCode": "Opyta",
                    "recordedBy": str(row.get(c_emp, "")) if c_emp else "",
                    "eventDate": str(row.get(c_date, "")) if c_date else "",
                    "locality": ponto,
                    "samplingProtocol": str(row.get(c_method, "")) if c_method else "",
                    "samplingEffort": effort,
                    "decimalLatitude": row.get(c_lat, "") if c_lat else "",
                    "decimalLongitude": row.get(c_lon, "") if c_lon else "",
                    "scientificName": sci,
                    "kingdom": str(row.get(c_reino, "")) if c_reino else "",
                    "phylum": str(row.get(c_filo, "")) if c_filo else "",
                    "class": str(row.get(c_classe, "")) if c_classe else "",
                    "order": str(row.get(c_ordem, "")) if c_ordem else "",
                    "family": str(row.get(c_familia, "")) if c_familia else "",
                    "genus": str(row.get(c_genero, "")) if c_genero else "",
                    "individualCount": "" if pd.isna(count_val) else int(count_val),
                    "organismQuantity": "" if pd.isna(bio_val) else float(bio_val),
                    "organismQuantityType": "grams" if not pd.isna(bio_val) else "",
                    "occurrenceRemarks": "",
                }
            )

        out = pd.DataFrame(records)

    group_clean = _safe_group_name(group)
    proj_name = "project"
    if not df_projeto.empty and "nome_projeto" in df_projeto.columns:
        proj_vals = df_projeto["nome_projeto"].dropna().astype(str)
        if not proj_vals.empty:
            proj_name = _safe_group_name(proj_vals.iloc[0])

    out_file = output_dir / f"DarwinCore_{group_clean}_{proj_name}.xlsx"
    out.to_excel(out_file, index=False, engine="openpyxl")
    generated_files.append(str(out_file))
    return {"rows": int(len(out)), "file": str(out_file)}


def run_ictio_pipeline(
    *,
    project_id: int,
    group: str,
    theme: dict,
    output_dir: Path,
    env_file: str | None = None,
    block: str = "all",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = _load_ictio_df(project_id=project_id, group=group, env_file=env_file)

    block_sel = str(block).strip().lower()
    executed_blocks: list[str] = []
    generated_files: list[str] = []

    details: dict = {
        "rows_loaded": int(len(df)),
        "group": group,
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist())
        if "nome_campanha" in df.columns
        else [],
        "points": sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()) if "nome_ponto" in df.columns else [],
    }

    if block_sel in {"3", "all"}:
        details["block_3"] = _run_block_3(
            df_projeto=df,
            group=group,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("3")

    if block_sel in {"5", "all"}:
        details["block_5"] = _run_block_5(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("5")

    if block_sel in {"6", "all"}:
        details["block_6"] = _run_block_6(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("6")

    if block_sel in {"8", "all"}:
        details["block_8"] = _run_block_8(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("8")

    if block_sel in {"9", "all"}:
        details["block_9"] = _run_block_9(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("9")

    if block_sel in {"10", "all"}:
        details["block_10"] = _run_block_10(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("10")

    if block_sel in {"11", "all"}:
        details["block_11"] = _run_block_11(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("11")

    if block_sel in {"12", "all"}:
        details["block_12"] = _run_block_12(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("12")

    if block_sel in {"13", "all"}:
        details["block_13"] = _run_block_13(
            df_projeto=df,
            group=group,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("13")

    if not executed_blocks:
        raise ValueError("Unsupported block for ictio pipeline. Use '3', '5', '6', '8', '9', '10', '11', '12', '13' or 'all'.")

    details["executed_blocks"] = executed_blocks
    details["generated_files"] = generated_files
    return details
