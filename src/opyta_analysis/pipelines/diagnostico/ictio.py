from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

from opyta_analysis.pipelines.diagnostico.darwincore_ief import export_darwincore_ief
from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import (
    apply_theme,
    get_figsize_by_complexity,
    get_tight_layout_rect,
    palette_from_theme,
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


def _campaign_palette(theme: dict, n: int) -> list[str]:
    return palette_from_theme(theme, max(n, 1))


def _theme_gradient_cmap(theme: dict, name: str = "opyta_theme_gradient"):
    colors = _campaign_palette(theme, 2)
    return mcolors.LinearSegmentedColormap.from_list(name, colors)


def _annotation_color_for_value(value: float, vmax: float) -> str:
    if not np.isfinite(vmax) or vmax <= 0:
        return "black"
    return "black" if value >= (0.65 * vmax) else "white"


PROJECT_FALLBACK_HINTS = {
    62: {
        "nome_empresa_contains": "rocha consultoria",
        "nome_projeto_contains": "sam metais",
    },
    183: {
        "codigo_interno_opyta": "DUCGEO001",
        "nome_empresa_contains": "geomil",
        "nome_projeto_contains": "monitoramento ducal",
    },
}

PROJECT_CODE_BY_ID = {
    183: "DUCGEO001",
}


def _apply_project_fallback_filter(df: pd.DataFrame, project_id: int) -> pd.DataFrame:
    if "id_projeto" in df.columns:
        return df

    hint = PROJECT_FALLBACK_HINTS.get(int(project_id))
    if not hint:
        raise RuntimeError(
            "A view biota_analise_consolidada nao expoe id_projeto e nao ha "
            f"fallback de escopo cadastrado para project_id={project_id}. "
            "Cadastrar codigo_interno_opyta/nome_projeto antes de executar para evitar mistura de projetos."
        )

    if hint.get("codigo_interno_opyta") and "codigo_interno_opyta" not in df.columns:
        raise RuntimeError(
            "Fallback de escopo exige codigo_interno_opyta, mas a coluna nao veio na view consolidada."
        )

    if "codigo_interno_opyta" in df.columns and hint.get("codigo_interno_opyta"):
        code_norm = _normalize_text(str(hint["codigo_interno_opyta"]))
        df = df[df["codigo_interno_opyta"].astype(str).map(_normalize_text) == code_norm].copy()

    if df.empty:
        return df

    if "nome_empresa" not in df.columns or "nome_projeto" not in df.columns:
        return df

    empresa_norm = df["nome_empresa"].astype(str).map(_normalize_text)
    projeto_norm = df["nome_projeto"].astype(str).map(_normalize_text)
    mask = empresa_norm.str.contains(hint["nome_empresa_contains"], na=False) & projeto_norm.str.contains(
        hint["nome_projeto_contains"], na=False
    )
    return df[mask].copy()


def _validate_project_scope(df: pd.DataFrame, project_id: int) -> None:
    if df.empty:
        return

    if "id_projeto" in df.columns:
        unique_ids = sorted(pd.to_numeric(df["id_projeto"], errors="coerce").dropna().astype(int).unique().tolist())
        if unique_ids != [int(project_id)]:
            raise RuntimeError(f"Escopo de projeto inconsistente: esperado {project_id}, obtido {unique_ids}.")
        return

    expected_code = PROJECT_CODE_BY_ID.get(int(project_id))
    if expected_code and "codigo_interno_opyta" in df.columns:
        codes = sorted(df["codigo_interno_opyta"].dropna().astype(str).unique().tolist())
        if codes != [expected_code]:
            raise RuntimeError(
                f"Escopo de projeto inconsistente: esperado codigo_interno_opyta={expected_code}, obtido {codes}."
            )
        return

    identity_cols = [c for c in ["codigo_interno_opyta", "nome_empresa", "nome_projeto"] if c in df.columns]
    if identity_cols:
        unique_scope = df[identity_cols].drop_duplicates()
        if len(unique_scope) > 1:
            sample = unique_scope.head(10).to_dict("records")
            raise RuntimeError(
                "Filtro de projeto retornou multiplas identidades de projeto. "
                f"project_id={project_id}; exemplos={sample}"
            )


def _load_ictio_df(project_id: int, group: str, env_file: str | None) -> pd.DataFrame:
    sb = get_client(env_file)

    # Fast path: request only the target biological group from the backend.
    filters = {"grupo_biologico": group}
    if int(project_id) in PROJECT_CODE_BY_ID:
        filters["codigo_interno_opyta"] = PROJECT_CODE_BY_ID[int(project_id)]

    rows = paginate(sb, "biota_analise_consolidada", filters=filters, select="*")
    if not rows and "codigo_interno_opyta" in filters:
        rows = paginate(
            sb,
            "biota_analise_consolidada",
            filters={"codigo_interno_opyta": filters["codigo_interno_opyta"]},
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
    _validate_project_scope(df, project_id)
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


def _rotulo_campanha(campanha: str) -> str:
    c_norm = _normalize_text(campanha)
    if "1" in c_norm and "seca" in c_norm:
        return "1a Campanha (Seca)"
    if "2" in c_norm and "chuva" in c_norm:
        return "2a Campanha (Chuva)"
    return str(campanha).strip()


def _valor_ocorrencia(grupo: pd.DataFrame, col_contagem: str):
    tem_quanti = (grupo["tipo_norm"] == "quantitativo").any()
    if tem_quanti:
        soma_quanti = pd.to_numeric(
            grupo.loc[grupo["tipo_norm"] == "quantitativo", col_contagem], errors="coerce"
        ).sum()
        if pd.isna(soma_quanti):
            return ""
        if float(soma_quanti).is_integer():
            return int(soma_quanti)
        return round(float(soma_quanti), 2)

    tem_quali = (grupo["tipo_norm"] == "qualitativo").any()
    if tem_quali:
        return "X"

    return ""


def _conta_ocorrencias_validas(row: pd.Series, colunas: list[str]) -> int:
    total = 0
    for c in colunas:
        v = row.get(c, "")
        if str(v).strip() != "" and str(v).strip() != "0":
            total += 1
    return total


def _esforco_total_por_ponto(df_quant: pd.DataFrame) -> pd.DataFrame:
    """Sum the sampling effort used at each campaign/point once per method."""
    group_cols = ["nome_campanha", "nome_ponto"]
    method_cols = [c for c in ["metodo_de_captura", "unidade_esforco"] if c in df_quant.columns]
    dedup_cols = group_cols + method_cols + ["esforco"]
    efforts = df_quant[dedup_cols].dropna(subset=["esforco"]).drop_duplicates()
    return (
        efforts.groupby(group_cols, dropna=False)
        .agg(
            esforco_total_ponto=("esforco", "sum"),
            unidades_esforco=("esforco", "size"),
        )
        .reset_index()
    )


def _cpuen_por_especie_ponto(df_projeto: pd.DataFrame) -> pd.DataFrame:
    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem", "esforco", "contagem"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes para matriz CPUEn ICTIO: {', '.join(missing)}")

    df_quant = df_projeto.copy()
    tipo_norm = df_quant["tipo_amostragem"].astype(str).map(_normalizar_tipo_amostragem)
    df_quant = df_quant[tipo_norm == "quantitativo"].copy()
    if df_quant.empty:
        return pd.DataFrame(columns=["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "esforco_total_ponto", "cpuen"])

    for c in ["nome_campanha", "nome_ponto", "nome_cientifico"]:
        df_quant[c] = df_quant[c].astype(str).str.strip()
    df_quant["esforco"] = pd.to_numeric(df_quant["esforco"], errors="coerce")
    df_quant["contagem"] = pd.to_numeric(df_quant["contagem"], errors="coerce").fillna(0)
    df_quant = df_quant[df_quant["esforco"].notna() & (df_quant["esforco"] > 0)].copy()
    if df_quant.empty:
        return pd.DataFrame(columns=["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "esforco_total_ponto", "cpuen"])

    df_species_point = (
        df_quant.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], dropna=False)
        .agg(contagem=("contagem", "sum"))
        .reset_index()
    )
    df_effort = _esforco_total_por_ponto(df_quant)
    df_species_point = df_species_point.merge(df_effort, on=["nome_campanha", "nome_ponto"], how="left")
    df_species_point = df_species_point[
        df_species_point["esforco_total_ponto"].notna() & (df_species_point["esforco_total_ponto"] > 0)
    ].copy()
    df_species_point["cpuen"] = (df_species_point["contagem"] / df_species_point["esforco_total_ponto"]) * 100
    return df_species_point


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


def _run_block_4(df_projeto: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)
    out_xlsx = output_dir / f"04_tabela_distribuicao_{group_slug}.xlsx"

    if df_projeto.empty:
        pd.DataFrame(columns=["Taxon"]).to_excel(out_xlsx, index=False, engine="openpyxl")
        generated_files.append(str(out_xlsx))
        return {"rows_input": 0, "rows_valid": 0, "taxa_total": 0, "warning": "dataset vazio"}

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem", "contagem"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 4 ICTIO: {', '.join(missing)}")

    df_tmp = df_projeto.copy()
    for c in ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem"]:
        df_tmp[c] = df_tmp[c].astype(str).str.strip()
    df_tmp["contagem"] = pd.to_numeric(df_tmp["contagem"], errors="coerce").fillna(0)
    df_tmp = df_tmp[
        df_tmp["nome_cientifico"].notna()
        & (df_tmp["nome_cientifico"] != "")
        & (df_tmp["nome_cientifico"].str.lower() != "nan")
        & df_tmp["nome_campanha"].notna()
        & (df_tmp["nome_campanha"] != "")
        & (df_tmp["nome_campanha"].str.lower() != "nan")
        & df_tmp["nome_ponto"].notna()
        & (df_tmp["nome_ponto"] != "")
        & (df_tmp["nome_ponto"].str.lower() != "nan")
    ].copy()

    if df_tmp.empty:
        pd.DataFrame(columns=["Taxon"]).to_excel(out_xlsx, index=False, engine="openpyxl")
        generated_files.append(str(out_xlsx))
        return {"rows_input": int(len(df_projeto)), "rows_valid": 0, "taxa_total": 0}

    df_tmp["tipo_norm"] = df_tmp["tipo_amostragem"].map(_normalizar_tipo_amostragem)
    df_tmp["campanha_layout"] = df_tmp["nome_campanha"].map(_rotulo_campanha)

    campaigns = sorted(df_tmp["campanha_layout"].dropna().unique().tolist(), key=_campanha_sort_key)
    points_by_campaign = {
        camp: _ordenar_pontos(
            df_tmp.loc[df_tmp["campanha_layout"] == camp, "nome_ponto"].dropna().unique().tolist()
        )
        for camp in campaigns
    }

    registros = []
    for (taxon, campanha, ponto), grupo_local in df_tmp.groupby(
        ["nome_cientifico", "campanha_layout", "nome_ponto"], dropna=False
    ):
        registros.append(
            {
                "Taxon": taxon,
                "campanha_layout": campanha,
                "ponto": ponto,
                "valor": _valor_ocorrencia(grupo_local, "contagem"),
            }
        )

    df_ocorr = pd.DataFrame(registros)
    if df_ocorr.empty:
        tabela_final = pd.DataFrame(columns=["Taxon"])
    else:
        df_ocorr["coluna"] = df_ocorr["campanha_layout"] + "|||" + df_ocorr["ponto"].astype(str)
        tabela_final = (
            df_ocorr.pivot_table(
                index="Taxon",
                columns="coluna",
                values="valor",
                aggfunc="first",
                fill_value="",
            )
            .reset_index()
        )

        for camp in campaigns:
            for point in points_by_campaign.get(camp, []):
                col = f"{camp}|||{point}"
                if col not in tabela_final.columns:
                    tabela_final[col] = ""

        for camp in campaigns:
            points_camp = points_by_campaign.get(camp, [])
            cols_camp = [f"{camp}|||{point}" for point in points_camp]
            tabela_final[f"{camp}|||OC"] = tabela_final.apply(
                lambda row: _conta_ocorrencias_validas(row, cols_camp),
                axis=1,
            )
            total_points = len(points_camp)
            tabela_final[f"{camp}|||%OC"] = tabela_final[f"{camp}|||OC"].apply(
                lambda x: f"{round((x / total_points) * 100):.0f}%" if total_points else "0%"
            )

        final_cols = ["Taxon"]
        for camp in campaigns:
            for point in points_by_campaign.get(camp, []):
                col = f"{camp}|||{point}"
                if col in tabela_final.columns:
                    final_cols.append(col)
            final_cols.extend([c for c in [f"{camp}|||OC", f"{camp}|||%OC"] if c in tabela_final.columns])
        tabela_final = tabela_final[final_cols]

    meta_cols = [c for c in ["ordem", "familia", "nome_popular"] if c in df_tmp.columns]
    if meta_cols and not tabela_final.empty:
        meta = df_tmp.groupby("nome_cientifico", as_index=False).agg(**{c: (c, _mode_or_first) for c in meta_cols})
        tabela_final = tabela_final.merge(meta, left_on="Taxon", right_on="nome_cientifico", how="left")
        tabela_final = tabela_final.drop(columns=["nome_cientifico"])
        rename = {"ordem": "Ordem", "familia": "Familia", "nome_popular": "Nome Popular"}
        tabela_final = tabela_final.rename(columns=rename)
        prefix_cols = [rename[c] for c in meta_cols if c in rename]
        tabela_final = tabela_final[prefix_cols + [c for c in tabela_final.columns if c not in prefix_cols]]

    tabela_final = tabela_final.sort_values([c for c in ["Ordem", "Familia", "Taxon"] if c in tabela_final.columns]).reset_index(drop=True)
    tabela_export = tabela_final.copy()
    tabela_export.columns = [f"{camp} - {sub}" if "|||" in col and (camp := col.split("|||", 1)[0]) and (sub := col.split("|||", 1)[1]) else col for col in tabela_export.columns]
    tabela_export.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))
    return {
        "rows_input": int(len(df_projeto)),
        "rows_valid": int(len(df_tmp)),
        "taxa_total": int(len(tabela_final)),
        "pontos_por_campanha": {camp: len(points) for camp, points in points_by_campaign.items()},
    }


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

    color_list = _campaign_palette(theme, len(campaigns))
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
            if abs(float(v)) < 1e-12:
                continue
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

    color_list = _campaign_palette(theme, len(campaigns))
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
            if abs(float(v)) < 1e-12:
                continue
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


def _save_taxon_richness_outputs(
    df_projeto: pd.DataFrame,
    group_slug: str,
    tax_col: str,
    tax_label: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
    df_tmp = df_projeto.copy()
    df_tmp["nome_cientifico"] = df_tmp["nome_cientifico"].astype(str).str.strip()
    df_tmp[tax_col] = df_tmp[tax_col].fillna("Nao informado").astype(str).str.strip()
    df_tmp.loc[df_tmp[tax_col].isin(["", "nan", "None"]), tax_col] = "Nao informado"

    richness_df = (
        df_tmp.groupby(tax_col)["nome_cientifico"]
        .nunique()
        .reset_index()
        .rename(columns={tax_col: tax_col, "nome_cientifico": "numero_de_especies"})
        .sort_values("numero_de_especies", ascending=False)
        .reset_index(drop=True)
    )
    total_species = int(richness_df["numero_de_especies"].sum())
    richness_df["percentual"] = np.where(
        total_species > 0,
        (richness_df["numero_de_especies"] / total_species) * 100,
        0,
    )

    out_df = output_dir / f"04_df_riqueza_por_{tax_col}_{group_slug}.xlsx"
    richness_df.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    size_bar = get_figsize_by_complexity(theme, n_categories=len(richness_df), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size_bar, dpi=int(theme.get("dpi", 600)))
    bars = ax.bar(
        richness_df[tax_col],
        richness_df["numero_de_especies"],
        color=str(theme.get("primary_hex", "#11420C")),
        edgecolor="black",
        linewidth=0.8,
    )
    apply_theme(ax, theme, xlabel=tax_label, ylabel="Numero de especies", x_tick_rotation=45)
    for bar, value in zip(bars, richness_df["numero_de_especies"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            float(value),
            f"{int(value)}",
            ha="center",
            va="bottom",
            fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
        )
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_bar = output_dir / f"04_grafico_riqueza_{tax_col}_barras_{group_slug}.png"
    fig.savefig(out_bar, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_bar))

    colors = _campaign_palette(theme, len(richness_df))
    size_donut = get_figsize_by_complexity(theme, n_categories=len(richness_df), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size_donut, dpi=int(theme.get("dpi", 600)))

    def _autopct_visible(pct: float) -> str:
        return f"{pct:.1f}%" if pct >= 4.0 else ""

    wedges, _, _ = ax.pie(
        richness_df["numero_de_especies"].values,
        labels=None,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.45, "edgecolor": "black", "linewidth": 0.8},
        autopct=_autopct_visible,
        pctdistance=0.78,
        textprops={"fontsize": int(theme.get("font_size_base", 10))},
    )
    labels = [str(x) for x in richness_df[tax_col].tolist()]
    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=int(theme.get("legend_font_size", theme.get("font_size_base", 10))),
    )
    ax.text(
        0,
        0,
        f"Total\n{total_species}",
        ha="center",
        va="center",
        fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
        fontweight=str(theme.get("title_weight", "bold")),
    )
    ax.set_facecolor(str(theme.get("background_color", "white")))
    fig.set_facecolor(str(theme.get("background_color", "white")))
    fig.tight_layout()
    out_donut = output_dir / f"05_grafico_riqueza_{tax_col}_rosca_{group_slug}.png"
    fig.savefig(out_donut, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_donut))
    return {"categorias": int(len(richness_df)), "especies_total_somado": total_species}


def _run_block_7(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)
    required = ["nome_cientifico", "ordem", "familia"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 7 ICTIO: {', '.join(missing)}")
    if df_projeto.empty:
        return {"ordens": 0, "familias": 0, "warning": "dataset vazio"}

    ordem = _save_taxon_richness_outputs(
        df_projeto=df_projeto,
        group_slug=group_slug,
        tax_col="ordem",
        tax_label="Ordem",
        theme=theme,
        output_dir=output_dir,
        generated_files=generated_files,
    )
    familia = _save_taxon_richness_outputs(
        df_projeto=df_projeto,
        group_slug=group_slug,
        tax_col="familia",
        tax_label="Familia",
        theme=theme,
        output_dir=output_dir,
        generated_files=generated_files,
    )
    return {"ordens": ordem["categorias"], "familias": familia["categorias"]}


def _run_block_8(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df = output_dir / f"06_df_cpue_por_ponto_{group_slug}.xlsx"
    out_png_cpuen = output_dir / f"06_grafico_cpuen_por_ponto_{group_slug}.png"
    out_png_cpueb = output_dir / f"07_grafico_cpueb_por_ponto_{group_slug}.png"

    if df_projeto.empty:
        pd.DataFrame(
            columns=[
                "nome_campanha",
                "nome_ponto",
                "abundancia_total",
                "biomassa_total",
                "esforco_total_ponto",
                "unidades_esforco",
                "cpuen",
                "cpueb",
            ]
        ).to_excel(
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
        pd.DataFrame(
            columns=[
                "nome_campanha",
                "nome_ponto",
                "abundancia_total",
                "biomassa_total",
                "esforco_total_ponto",
                "unidades_esforco",
                "cpuen",
                "cpueb",
            ]
        ).to_excel(
            out_df, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "sem registros quantitativos para CPUE"}

    df_quant["esforco"] = pd.to_numeric(df_quant["esforco"], errors="coerce")
    df_quant["contagem"] = pd.to_numeric(df_quant["contagem"], errors="coerce").fillna(0)
    df_quant["biomassa"] = pd.to_numeric(df_quant["biomassa"], errors="coerce").fillna(0)

    df_quant = df_quant.dropna(subset=["esforco"]).copy()
    df_quant = df_quant[df_quant["esforco"] > 0].copy()

    if df_quant.empty:
        pd.DataFrame(
            columns=[
                "nome_campanha",
                "nome_ponto",
                "abundancia_total",
                "biomassa_total",
                "esforco_total_ponto",
                "unidades_esforco",
                "cpuen",
                "cpueb",
            ]
        ).to_excel(
            out_df, index=False, engine="openpyxl"
        )
        generated_files.append(str(out_df))
        return {"campaigns": [], "points": [], "warning": "esforco invalido para CPUE"}

    df_totals = (
        df_quant.groupby(["nome_campanha", "nome_ponto"], dropna=False)
        .agg(
            abundancia_total=("contagem", "sum"),
            biomassa_total=("biomassa", "sum"),
        )
        .reset_index()
    )
    df_effort = _esforco_total_por_ponto(df_quant)
    df_cpue = df_totals.merge(df_effort, on=["nome_campanha", "nome_ponto"], how="left")
    df_cpue = df_cpue[df_cpue["esforco_total_ponto"].notna() & (df_cpue["esforco_total_ponto"] > 0)].copy()
    df_cpue["cpuen"] = (df_cpue["abundancia_total"] / df_cpue["esforco_total_ponto"]) * 100
    df_cpue["cpueb"] = (df_cpue["biomassa_total"] / df_cpue["esforco_total_ponto"]) * 100

    df_cpue["nome_campanha"] = df_cpue["nome_campanha"].astype(str).str.strip()
    df_cpue["nome_ponto"] = df_cpue["nome_ponto"].astype(str).str.strip()

    campaigns = sorted(df_cpue["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    points = _ordenar_pontos(df_cpue["nome_ponto"].dropna().unique().tolist())

    df_cpue.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if df_cpue.empty or not campaigns or not points:
        return {"campaigns": campaigns, "points": points}

    color_list = _campaign_palette(theme, len(campaigns))
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
                if abs(float(v)) < 1e-12:
                    continue
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

    return {
        "campaigns": campaigns,
        "points": points,
        "cpue_formula": "(sum_abundance_or_biomass / sum_distinct_effort_by_campaign_point) * 100",
    }


def _run_block_9(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df_cpuen = output_dir / f"08_df_cpuen_por_especie_{group_slug}.xlsx"
    out_df_cpueb = output_dir / f"09_df_cpueb_por_especie_{group_slug}.xlsx"
    out_png_cpuen = output_dir / f"08_grafico_cpuen_por_especie_{group_slug}.png"
    out_png_cpueb = output_dir / f"09_grafico_cpueb_por_especie_{group_slug}.png"

    base_cols = ["nome_cientifico"]
    if df_projeto.empty:
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb, index=False, engine="openpyxl")
        generated_files.extend([str(out_df_cpuen), str(out_df_cpueb)])
        return {"campaigns": [], "species": 0, "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem", "esforco", "contagem", "biomassa"]
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

    df_species_point = (
        df_quant.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], dropna=False)
        .agg(
            contagem=("contagem", "sum"),
            biomassa=("biomassa", "sum"),
        )
        .reset_index()
    )
    df_effort = _esforco_total_por_ponto(df_quant)
    df_species_point = df_species_point.merge(df_effort, on=["nome_campanha", "nome_ponto"], how="left")
    df_species_point = df_species_point[
        df_species_point["esforco_total_ponto"].notna() & (df_species_point["esforco_total_ponto"] > 0)
    ].copy()
    df_species_point["cpuen"] = (df_species_point["contagem"] / df_species_point["esforco_total_ponto"]) * 100
    df_species_point["cpueb"] = (df_species_point["biomassa"] / df_species_point["esforco_total_ponto"]) * 100

    df_cpue_sp = (
        df_species_point.groupby(["nome_campanha", "nome_cientifico"], dropna=False)[["cpuen", "cpueb"]]
        .sum()
        .reset_index()
    )
    df_cpue_sp["nome_campanha"] = df_cpue_sp["nome_campanha"].astype(str).str.strip()
    df_cpue_sp["nome_cientifico"] = df_cpue_sp["nome_cientifico"].astype(str).str.strip()

    campaigns = sorted(df_cpue_sp["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    if not campaigns:
        campaigns = ["campanha_1"]

    cpuen_sp = (
        df_cpue_sp.pivot_table(
            index="nome_cientifico",
            columns="nome_campanha",
            values="cpuen",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=campaigns, fill_value=0)
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
        .reindex(columns=campaigns, fill_value=0)
        .fillna(0)
    )

    order_species = cpuen_sp.sum(axis=1).sort_values(ascending=True).index.tolist()
    cpuen_sp = cpuen_sp.loc[order_species].reset_index()
    cpueb_sp = cpueb_sp.loc[order_species].reset_index()

    cpuen_sp.to_excel(out_df_cpuen, index=False, engine="openpyxl")
    cpueb_sp.to_excel(out_df_cpueb, index=False, engine="openpyxl")
    generated_files.extend([str(out_df_cpuen), str(out_df_cpueb)])

    colors = _campaign_palette(theme, len(campaigns))
    color_map = {c: colors[i] for i, c in enumerate(campaigns)}

    def _plot_horizontal(df_plot: pd.DataFrame, metric_label: str, out_png: Path) -> None:
        labels = df_plot["nome_cientifico"].tolist()
        y = np.arange(len(labels))
        n_campaigns = max(len(campaigns), 1)
        height = min(0.18, 0.82 / n_campaigns)

        fig_h = max(8.0, 0.32 * max(len(labels), 10))
        fig, ax = plt.subplots(figsize=(15, fig_h), dpi=int(theme.get("dpi", 600)))

        all_bars = []
        for i, campaign in enumerate(campaigns):
            offset = (i - (n_campaigns - 1) / 2) * height
            bars = ax.barh(
                y + offset,
                df_plot[campaign].values,
                height,
                label=campaign,
                color=color_map[campaign],
                edgecolor="black",
            )
            all_bars.append(bars)

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

        for bars in all_bars:
            xmax = max((b.get_width() for b in bars), default=0)
            offset = xmax * 0.02 if xmax > 0 else 0.1
            for b in bars:
                w = b.get_width()
                if abs(float(w)) < 1e-12:
                    continue
                ax.text(
                    w + offset,
                    b.get_y() + b.get_height() / 2,
                    f"{float(w):.2f}",
                    va="center",
                    ha="left",
                    fontsize=int(theme.get("annotation_size", 11)),
                )

        place_legend_below_x_axis(
            fig,
            ax,
            theme,
            ncol=min(len(campaigns), int(theme.get("legend_max_cols", 2))),
        )
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.0))
        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))

    def _plot_heatmap(df_plot: pd.DataFrame, metric_label: str, out_png: Path) -> None:
        labels = df_plot["nome_cientifico"].tolist()
        values = df_plot[campaigns].to_numpy(dtype=float)
        vmax = float(np.nanmax(values)) if values.size else 0.0

        fig_w = max(10.5, 1.35 * len(campaigns) + 4.5)
        fig_h = max(7.0, 0.42 * max(len(labels), 10))
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=int(theme.get("dpi", 600)))
        im = ax.imshow(values, aspect="auto", cmap=_theme_gradient_cmap(theme), vmin=0, vmax=vmax if vmax > 0 else 1)

        ax.set_xticks(np.arange(len(campaigns)))
        ax.set_xticklabels(campaigns, rotation=35, ha="right")
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels, fontstyle="italic")
        apply_theme(ax, theme, xlabel="Campanha", ylabel="Especie", x_tick_rotation=None)
        ax.grid(axis="y", visible=bool(theme.get("grid_y", True)), alpha=0.0)
        ax.grid(axis="x", visible=bool(theme.get("grid_x", False)))

        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                v = values[i, j]
                if abs(float(v)) < 1e-12:
                    continue
                ax.text(
                    j,
                    i,
                    f"{float(v):.2f}",
                    ha="center",
                    va="center",
                    fontsize=int(theme.get("annotation_size", 11)),
                    color=_annotation_color_for_value(float(v), vmax),
                )

        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cbar.set_label(metric_label)
        validate_axes_style(ax, theme)
        fig.tight_layout()
        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))

    if len(campaigns) > 3:
        _plot_heatmap(cpuen_sp, "CPUEn (ind/100m2)", out_png_cpuen)
        _plot_heatmap(cpueb_sp, "CPUEb (g/100m2)", out_png_cpueb)
    else:
        _plot_horizontal(cpuen_sp, "CPUEn (ind/100m2)", out_png_cpuen)
        _plot_horizontal(cpueb_sp, "CPUEb (g/100m2)", out_png_cpueb)

    return {
        "campaigns": campaigns,
        "species": int(len(order_species)),
        "cpue_formula": "(species_abundance_or_biomass_at_point / sum_distinct_effort_by_campaign_point) * 100",
    }


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

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "tipo_amostragem", "esforco"]
    if any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 10 ICTIO")

    df_div = _cpuen_por_especie_ponto(df_projeto)
    if df_div.empty:
        return {"campaigns": [], "warning": "sem dados quantitativos"}

    campaigns = sorted(df_div["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    rows = []
    for camp in campaigns:
        df_c = df_div[df_div["nome_campanha"] == camp].copy()
        if df_c.empty:
            continue
        mat = df_c.pivot_table(
            index="nome_ponto",
            columns="nome_cientifico",
            values="cpuen",
            aggfunc="sum",
            fill_value=0,
            observed=False,
        )
        for p in mat.index:
            vec = mat.loc[p].values
            rows.append(
                {
                    "nome_campanha": camp,
                    "nome_ponto": p,
                    "base_quantitativa": "CPUEn (ind/100m2)",
                    "Shannon_H": _shannon(vec),
                    "Pielou_J": _pielou(vec),
                }
            )

        total_vec = mat.sum(axis=0).values
        rows.append(
            {
                "nome_campanha": camp,
                "nome_ponto": f"{camp} (Geral)",
                "base_quantitativa": "CPUEn (ind/100m2)",
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
        split_n = 0
        for camp in campaigns[:-1]:
            split_n += df_out[df_out["nome_campanha"] == camp].shape[0]
            if 0 < split_n < len(x):
                ax1.axvline(x=split_n - 0.5, color="#888888", linestyle="--", linewidth=1.2)

    for b, v in zip(bars, sh):
        if abs(float(v)) < 1e-12:
            continue
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

    return {"campaigns": campaigns, "base_quantitativa": "CPUEn (ind/100m2)"}


def _run_block_11(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem", "tipo_amostragem", "esforco"]
    if any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 11 ICTIO")

    df_sim = _cpuen_por_especie_ponto(df_projeto)
    if df_sim.empty:
        return {"points": 0, "warning": "sem dados quantitativos"}

    mat = df_sim.pivot_table(
        index="nome_ponto",
        columns="nome_cientifico",
        values="cpuen",
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

    apply_theme(ax, theme, xlabel="Similaridade de Bray-Curtis (%) - matriz CPUEn", ylabel="")
    validate_axes_style(ax, theme)
    fig.tight_layout()

    out_png = output_dir / f"11_dendrograma_similaridade_{group_slug}_seca_chuva_somadas.png"
    fig.savefig(str(out_png), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))
    return {"points": int(mat.shape[0]), "base_quantitativa": "CPUEn (ind/100m2)"}


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
    return export_darwincore_ief(
        df=df_projeto,
        group=group,
        output_dir=output_dir,
        generated_files=generated_files,
        include_fish_biometrics=True,
    )


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

    if block_sel in {"4", "all"}:
        details["block_4"] = _run_block_4(
            df_projeto=df,
            group=group,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("4")

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

    if block_sel in {"7", "all"}:
        details["block_7"] = _run_block_7(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("7")

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
        raise ValueError("Unsupported block for ictio pipeline. Use '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13' or 'all'.")

    details["executed_blocks"] = executed_blocks
    details["generated_files"] = generated_files
    return details
