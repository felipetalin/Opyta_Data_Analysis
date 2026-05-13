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

    # Handles strings with mojibake where some accents become unknown chars.
    if "fito" in target:
        return "fito" in db
    if "zooplan" in target or "zoo plan" in target:
        return "zoo" in db and "plan" in db
    if "ictio" in target:
        return "ictio" in db

    return db == target


def _get_col(df_: pd.DataFrame, *cands: str) -> str | None:
    for c in cands:
        if c in df_.columns:
            return c
    return None


def _normalizar_tipo_amostragem(valor: str) -> str:
    s = _normalize_text(valor)
    if "quantit" in s:
        return "quantitativo"
    if "qualit" in s:
        return "qualitativo"
    return "outro"


def _rotulo_campanha(campanha: str) -> str:
    c = str(campanha).strip()
    mapa = {
        "1º Campanha (Seca)": "1ª Campanha (Seca)",
        "1° Campanha (Seca)": "1ª Campanha (Seca)",
        "2º Campanha (Chuva)": "2ª Campanha (Chuva)",
        "2° Campanha (Chuva)": "2ª Campanha (Chuva)",
    }
    return mapa.get(c, c)


def _extrair_numero(txt: str) -> int:
    m = re.search(r"(\d+)", str(txt))
    return int(m.group(1)) if m else 999999


def _ordenar_pontos(lista_pontos: list[str]) -> list[str]:
    return sorted(lista_pontos, key=lambda x: (_extrair_numero(x), str(x)))


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


def _safe_group_name(group: str) -> str:
    normalized = _normalize_text(group).replace(" ", "_")
    return re.sub(r"[^a-z0-9_]+", "", normalized)


def _apply_project_fallback_filter(df: pd.DataFrame, project_id: int) -> pd.DataFrame:
    """
    Fallback when the consolidated view does not expose id_projeto.
    Keeps strict project-level reproducibility for known client deliveries.
    """
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


def _load_fitoplancton_df(project_id: int, group: str, env_file: str | None) -> pd.DataFrame:
    sb = get_client(env_file)
    rows = paginate(
        sb,
        "biota_analise_consolidada",
        select="*",
    )
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Prefer strict filtering by project id when available in the view.
    if "id_projeto" in df.columns:
        df = df[pd.to_numeric(df["id_projeto"], errors="coerce") == int(project_id)].copy()
    else:
        df = _apply_project_fallback_filter(df, project_id)

    if "grupo_biologico" not in df.columns:
        return pd.DataFrame()

    df = df[df["grupo_biologico"].astype(str).map(lambda x: _group_matches(x, group))].copy()
    return df.reset_index(drop=True)


def _run_block_4(df_projeto: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    if df_projeto.empty:
        tabela_export = pd.DataFrame(columns=["Taxon"])
        group_slug = _safe_group_name(group)
        xlsx = output_dir / f"01_tabela_ocorrencia_{group_slug}.xlsx"
        tabela_export.to_excel(xlsx, index=False, engine="openpyxl")
        generated_files.append(str(xlsx))
        return {
            "rows_input": 0,
            "rows_valid": 0,
            "taxa_total": 0,
            "warning": "dataset vazio para os filtros informados",
        }

    df_tmp = df_projeto.copy()

    col_tipo_amostragem = _get_col(df_tmp, "Tipo_de_Amostragem", "tipo_de_amostragem", "tipo_amostragem")
    col_contagem = _get_col(df_tmp, "contagem", "numero_de_individuos")
    col_ponto = _get_col(df_tmp, "nome_ponto", "codigo_ponto", "ponto")

    obrigatorias = {
        "nome_campanha": "nome_campanha" if "nome_campanha" in df_tmp.columns else None,
        "nome_cientifico": "nome_cientifico" if "nome_cientifico" in df_tmp.columns else None,
        "tipo_amostragem": col_tipo_amostragem,
        "contagem": col_contagem,
        "nome_ponto": col_ponto,
    }

    faltando = [nome for nome, col in obrigatorias.items() if col is None]
    if faltando:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 4 FITO: {', '.join(faltando)}")

    df_tmp["nome_campanha"] = df_tmp["nome_campanha"].astype(str).str.strip()
    df_tmp["nome_cientifico"] = df_tmp["nome_cientifico"].astype(str).str.strip()
    df_tmp[col_ponto] = df_tmp[col_ponto].astype(str).str.strip()
    df_tmp[col_tipo_amostragem] = df_tmp[col_tipo_amostragem].astype(str).str.strip()
    df_tmp[col_contagem] = pd.to_numeric(df_tmp[col_contagem], errors="coerce").fillna(0)

    df_tmp = df_tmp[
        df_tmp["nome_cientifico"].notna()
        & (df_tmp["nome_cientifico"] != "")
        & (df_tmp["nome_cientifico"].str.lower() != "nan")
        & df_tmp["nome_campanha"].notna()
        & (df_tmp["nome_campanha"] != "")
        & (df_tmp["nome_campanha"].str.lower() != "nan")
        & df_tmp[col_ponto].notna()
        & (df_tmp[col_ponto] != "")
        & (df_tmp[col_ponto].str.lower() != "nan")
    ].copy()

    if df_tmp.empty:
        tabela_final = pd.DataFrame(columns=["Taxon"])
    else:
        df_tmp["tipo_norm"] = df_tmp[col_tipo_amostragem].apply(_normalizar_tipo_amostragem)
        df_tmp["campanha_layout"] = df_tmp["nome_campanha"].apply(_rotulo_campanha)

        ordem_campanhas = ["1ª Campanha (Seca)", "2ª Campanha (Chuva)"]
        campanhas_presentes = [c for c in ordem_campanhas if c in df_tmp["campanha_layout"].unique().tolist()]
        campanhas_extras = [
            c for c in sorted(df_tmp["campanha_layout"].unique().tolist()) if c not in campanhas_presentes
        ]
        campanhas_presentes.extend(campanhas_extras)

        pontos_todos = _ordenar_pontos(df_tmp[col_ponto].dropna().unique().tolist())

        registros = []
        for (taxon, campanha, ponto), grupo_local in df_tmp.groupby(
            ["nome_cientifico", "campanha_layout", col_ponto], dropna=False
        ):
            registros.append(
                {
                    "Taxon": taxon,
                    "campanha_layout": campanha,
                    "ponto": ponto,
                    "valor": _valor_ocorrencia(grupo_local, col_contagem),
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

            colunas_esperadas = []
            for camp in campanhas_presentes:
                for ponto in pontos_todos:
                    colunas_esperadas.append(f"{camp}|||{ponto}")
            for c in colunas_esperadas:
                if c not in tabela_final.columns:
                    tabela_final[c] = ""

            for camp in campanhas_presentes:
                cols_camp = [f"{camp}|||{p}" for p in pontos_todos]
                tabela_final[f"{camp}|||OC"] = tabela_final.apply(
                    lambda row: _conta_ocorrencias_validas(row, cols_camp),
                    axis=1,
                )
                total_pontos_camp = len(cols_camp)
                if total_pontos_camp > 0:
                    tabela_final[f"{camp}|||%OC"] = tabela_final[f"{camp}|||OC"].apply(
                        lambda x: f"{round((x / total_pontos_camp) * 100):.0f}%"
                    )
                else:
                    tabela_final[f"{camp}|||%OC"] = "0%"

            colunas_finais = ["Taxon"]
            for camp in campanhas_presentes:
                for ponto in pontos_todos:
                    c = f"{camp}|||{ponto}"
                    if c in tabela_final.columns:
                        colunas_finais.append(c)
                oc_col = f"{camp}|||OC"
                pct_col = f"{camp}|||%OC"
                if oc_col in tabela_final.columns:
                    colunas_finais.append(oc_col)
                if pct_col in tabela_final.columns:
                    colunas_finais.append(pct_col)

            tabela_final = tabela_final[colunas_finais]
            tabela_final = tabela_final.sort_values("Taxon").reset_index(drop=True)

    tabela_export = tabela_final.copy()
    novos_nomes = []
    for col in tabela_export.columns:
        if "|||" in col:
            camp, sub = col.split("|||", 1)
            novos_nomes.append(f"{camp} - {sub}")
        else:
            novos_nomes.append(col)
    tabela_export.columns = novos_nomes

    group_slug = _safe_group_name(group)
    xlsx = output_dir / f"01_tabela_ocorrencia_{group_slug}.xlsx"
    tabela_export.to_excel(xlsx, index=False, engine="openpyxl")
    generated_files.append(str(xlsx))

    return {
        "rows_input": int(len(df_projeto)),
        "rows_valid": int(len(df_tmp)) if not df_tmp.empty else 0,
        "taxa_total": int(len(tabela_final)) if not tabela_final.empty else 0,
    }


def _mode_or_first(series: pd.Series):
    s = series.dropna()
    if s.empty:
        return np.nan
    modes = s.mode()
    return modes.iloc[0] if not modes.empty else s.iloc[0]


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
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 3 FITO: nome_campanha, nome_cientifico")

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

    c_filo = _get_col(df_tmp, "filo", "phylum")
    c_classe = _get_col(df_tmp, "classe", "class")
    c_ordem = _get_col(df_tmp, "ordem", "order")
    c_familia = _get_col(df_tmp, "familia", "family")
    c_genero = _get_col(df_tmp, "genero", "genus")

    agg_dict: dict = {}
    if c_filo:
        agg_dict["filo"] = (c_filo, _mode_or_first)
    if c_classe:
        agg_dict["classe"] = (c_classe, _mode_or_first)
    if c_ordem:
        agg_dict["ordem"] = (c_ordem, _mode_or_first)
    if c_familia:
        agg_dict["familia"] = (c_familia, _mode_or_first)
    if c_genero:
        agg_dict["genero"] = (c_genero, _mode_or_first)

    if agg_dict:
        tabela = df_tmp.groupby("nome_cientifico", as_index=False).agg(**agg_dict)
    else:
        tabela = df_tmp[["nome_cientifico"]].drop_duplicates().reset_index(drop=True)

    tabela = tabela.merge(ocorrencia, on="nome_cientifico", how="left")
    tabela = tabela.rename(
        columns={
            "filo": "Filo",
            "classe": "Classe",
            "ordem": "Ordem",
            "familia": "Familia",
            "genero": "Genero",
            "nome_cientifico": "Nome Cientifico",
        }
    )
    desired = ["Filo", "Classe", "Ordem", "Familia", "Genero", "Nome Cientifico", "Ocorrencia (Campanhas)"]
    existing = [c for c in desired if c in tabela.columns]
    tabela = tabela[existing]

    sort_cols = [c for c in ["Filo", "Classe", "Ordem", "Familia", "Genero", "Nome Cientifico"] if c in tabela.columns]
    if sort_cols:
        tabela = tabela.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    tabela.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))
    return {"taxa_total": int(len(tabela))}


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


def _run_block_5(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    if df_projeto.empty:
        out_df = output_dir / f"02_df_riqueza_por_ponto_{group_slug}.xlsx"
        pd.DataFrame(columns=["nome_campanha", "nome_ponto", "riqueza"]).to_excel(out_df, index=False, engine="openpyxl")
        generated_files.append(str(out_df))
        return {"campaigns": [], "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_ponto", "nome_cientifico"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 5 FITO: {', '.join(missing)}")

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

    out_df = output_dir / f"02_df_riqueza_por_ponto_{group_slug}.xlsx"
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

    out_png = output_dir / f"02_grafico_riqueza_por_ponto_{group_slug}.png"
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"campaigns": campaigns, "points": points}


def _safe_campaign_name(campaign: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(campaign)).strip("_")


def _calc_density_fito(df_: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    col_vol = _get_col(df_, "volume_filtrado", "volume", "vol_filtrado", "volume_l", "volume_litros")
    col_esf = _get_col(df_, "esforco")

    d = df_.copy()
    d["contagem"] = pd.Series(pd.to_numeric(d["contagem"], errors="coerce"), index=d.index).fillna(0)

    if col_vol:
        d[col_vol] = pd.to_numeric(d[col_vol], errors="coerce")
        d = d.dropna(subset=[col_vol])
        d = d[d[col_vol] > 0].copy()
        d["densidade"] = d["contagem"] / d[col_vol]
        return d, "org./volume"

    if col_esf:
        d[col_esf] = pd.to_numeric(d[col_esf], errors="coerce")
        d = d.dropna(subset=[col_esf])
        d = d[d[col_esf] > 0].copy()
        d["densidade"] = d["contagem"] / d[col_esf]
        return d, "org./esforco"

    d["densidade"] = d["contagem"]
    return d, "org./amostra (bruto)"


def _run_block_6(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    if df_projeto.empty:
        return {"campaigns": [], "warning": "dataset vazio"}

    required = ["nome_ponto", "nome_campanha", "nome_cientifico", "contagem"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 6 FITO: {', '.join(missing)}")

    col_tipo = _get_col(df_projeto, "Tipo_de_Amostragem", "tipo_de_amostragem", "tipo_amostragem")
    if col_tipo is None:
        raise RuntimeError("[ERRO] Coluna de tipo de amostragem ausente no Bloco 6 FITO")

    col_filo = _get_col(df_projeto, "filo", "phylum")
    if col_filo is None:
        raise RuntimeError("[ERRO] Coluna de filo ausente no Bloco 6 FITO")

    df_base = df_projeto.copy()
    df_base["nome_ponto"] = df_base["nome_ponto"].astype(str).str.strip()
    df_base["nome_campanha"] = df_base["nome_campanha"].astype(str).str.strip()
    df_base["nome_cientifico"] = df_base["nome_cientifico"].astype(str).str.strip()
    df_base[col_filo] = df_base[col_filo].astype(str).str.strip()
    df_base[col_tipo] = df_base[col_tipo].astype(str).str.strip()
    df_base["contagem"] = pd.Series(pd.to_numeric(df_base["contagem"], errors="coerce"), index=df_base.index).fillna(0)

    df_base = df_base[
        df_base["nome_ponto"].notna()
        & (df_base["nome_ponto"] != "")
        & (df_base["nome_ponto"].str.lower() != "nan")
        & df_base["nome_campanha"].notna()
        & (df_base["nome_campanha"] != "")
        & (df_base["nome_campanha"].str.lower() != "nan")
        & df_base["nome_cientifico"].notna()
        & (df_base["nome_cientifico"] != "")
        & (df_base["nome_cientifico"].str.lower() != "nan")
        & df_base[col_filo].notna()
        & (df_base[col_filo] != "")
        & (df_base[col_filo].str.lower() != "nan")
    ].copy()

    if df_base.empty:
        return {"campaigns": [], "warning": "sem linhas validas apos limpeza"}

    # 06A: riqueza total por ponto (todas campanhas juntas)
    df_riqueza_ponto = (
        df_base.groupby("nome_ponto")["nome_cientifico"]
        .nunique()
        .reset_index()
        .rename(columns={"nome_cientifico": "riqueza_taxons"})
    )
    pontos = _ordenar_pontos(df_riqueza_ponto["nome_ponto"].tolist())
    df_riqueza_ponto["__ord"] = df_riqueza_ponto["nome_ponto"].apply(lambda x: (_extrair_numero(x), str(x)))
    df_riqueza_ponto = df_riqueza_ponto.sort_values("__ord").drop(columns=["__ord"]).reset_index(drop=True)

    out_df_06a = output_dir / f"06A_df_riqueza_total_por_ponto_{group_slug}.xlsx"
    df_riqueza_ponto.to_excel(out_df_06a, index=False, engine="openpyxl")
    generated_files.append(str(out_df_06a))

    size = get_figsize_by_complexity(theme, n_categories=len(df_riqueza_ponto), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    bars = ax.bar(
        df_riqueza_ponto["nome_ponto"].tolist(),
        df_riqueza_ponto["riqueza_taxons"].tolist(),
        color=str(theme.get("primary_hex", "#11420C")),
        edgecolor="black",
        linewidth=0.8,
    )
    for bar, v in zip(bars, df_riqueza_ponto["riqueza_taxons"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            float(v),
            f"{int(v)}",
            ha="center",
            va="bottom",
            fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
        )
    apply_theme(ax, theme, xlabel="Ponto amostral", ylabel="Riqueza taxonomica", x_tick_rotation=45)
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_png_06a = output_dir / f"06A_grafico_riqueza_total_por_ponto_{group_slug}.png"
    fig.savefig(str(out_png_06a), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png_06a))

    # 06B/06C: densidade por filo por campanha (somente quantitativo)
    df_quant = df_base[df_base[col_tipo].astype(str).str.contains("quantit", case=False, na=False)].copy()
    if df_quant.empty:
        return {"campaigns": [], "points": pontos, "warning": "sem registros quantitativos para densidade"}

    df_den, unidade = _calc_density_fito(df_quant)
    if df_den.empty:
        return {"campaigns": [], "points": pontos, "warning": "sem base valida de densidade"}

    campaigns = sorted(df_den["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    filos_all = sorted(df_den[col_filo].dropna().astype(str).unique().tolist())
    cmap = plt.get_cmap("tab10")
    color_by_filo = {f: cmap(i % cmap.N) for i, f in enumerate(filos_all)}

    for camp in campaigns:
        df_c = df_den[df_den["nome_campanha"] == camp].copy()
        if df_c.empty:
            continue

        matriz = (
            df_c.pivot_table(index="nome_ponto", columns=col_filo, values="densidade", aggfunc="sum", fill_value=0)
            .reindex(pontos, fill_value=0)
            .fillna(0)
        )
        cols = sorted([str(c) for c in matriz.columns.tolist()])
        matriz = matriz[cols]

        camp_slug = _safe_campaign_name(camp)
        out_df_06b = output_dir / f"06B_df_densidade_filo_{camp_slug}_{group_slug}.xlsx"
        matriz.reset_index().to_excel(out_df_06b, index=False, engine="openpyxl")
        generated_files.append(str(out_df_06b))

        x = np.arange(len(matriz.index))

        fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
        bottom = np.zeros(len(matriz.index))
        for filo in cols:
            vals = matriz[filo].values
            ax.bar(
                x,
                vals,
                bottom=bottom,
                label=str(filo),
                color=color_by_filo.get(filo, cmap(0)),
                edgecolor="white",
                linewidth=0.6,
            )
            bottom += vals
        ax.set_xticks(x)
        ax.set_xticklabels(matriz.index.astype(str).tolist(), rotation=45, ha="right")
        apply_theme(ax, theme, xlabel="Ponto amostral", ylabel=f"Densidade ({unidade})")
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=min(4, len(cols)),
            frameon=False,
            fontsize=int(theme.get("font_size_legend", 13)),
        )
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.86))
        out_png_06b = output_dir / f"06B_grafico_densidade_filo_{camp_slug}_{group_slug}.png"
        fig.savefig(str(out_png_06b), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png_06b))

        matriz_pct = matriz.div(matriz.sum(axis=1).replace(0, np.nan), axis=0) * 100
        matriz_pct = matriz_pct.fillna(0)

        out_df_06c = output_dir / f"06C_df_densidade_relativa_filo_{camp_slug}_{group_slug}.xlsx"
        matriz_pct.reset_index().to_excel(out_df_06c, index=False, engine="openpyxl")
        generated_files.append(str(out_df_06c))

        fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
        bottom = np.zeros(len(matriz_pct.index))
        for filo in cols:
            vals = matriz_pct[filo].values
            ax.bar(
                x,
                vals,
                bottom=bottom,
                label=str(filo),
                color=color_by_filo.get(filo, cmap(0)),
                edgecolor="white",
                linewidth=0.6,
            )
            bottom += vals
        ax.set_xticks(x)
        ax.set_xticklabels(matriz_pct.index.astype(str).tolist(), rotation=45, ha="right")
        apply_theme(ax, theme, xlabel="Ponto amostral", ylabel="Densidade relativa (%)")
        ax.set_ylim(0, 100)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=min(4, len(cols)),
            frameon=False,
            fontsize=int(theme.get("font_size_legend", 13)),
        )
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.86))
        out_png_06c = output_dir / f"06C_grafico_densidade_relativa_filo_{camp_slug}_{group_slug}.png"
        fig.savefig(str(out_png_06c), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png_06c))

    return {"campaigns": campaigns, "points": pontos, "filos": len(filos_all)}


def _run_block_7(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    if df_projeto.empty:
        return {"filos": 0, "taxa_total": 0, "warning": "dataset vazio"}

    if "filo" not in df_projeto.columns:
        return {"filos": 0, "taxa_total": 0, "warning": "coluna filo nao encontrada"}

    df_base = df_projeto.copy()
    df_base["filo"] = df_base["filo"].astype(str).str.strip()
    if "nome_cientifico" in df_base.columns:
        df_base["nome_cientifico"] = df_base["nome_cientifico"].astype(str).str.strip()

    df_base = df_base[
        df_base["filo"].notna()
        & (df_base["filo"] != "")
        & (df_base["filo"].str.lower() != "nan")
    ].copy()

    if df_base.empty:
        return {"filos": 0, "taxa_total": 0, "warning": "sem valores de filo apos limpeza"}

    df_riqueza_filo = (
        df_base.groupby("filo")["nome_cientifico"]
        .nunique()
        .reset_index()
        .rename(columns={"filo": "filo", "nome_cientifico": "numero_de_taxons"})
        .sort_values(by="numero_de_taxons", ascending=False)
        .reset_index(drop=True)
    )

    total_taxa = int(df_riqueza_filo["numero_de_taxons"].sum())

    out_df = output_dir / f"04_df_riqueza_por_filo_{group_slug}.xlsx"
    df_riqueza_filo.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if df_riqueza_filo.empty:
        return {"filos": 0, "taxa_total": total_taxa}

    size = get_figsize_by_complexity(theme, n_categories=len(df_riqueza_filo), prefer_landscape=True)
    primary_color = str(theme.get("primary_hex", "#11420C"))

    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    bars = ax.bar(
        df_riqueza_filo["filo"].tolist(),
        df_riqueza_filo["numero_de_taxons"].tolist(),
        color=primary_color,
        edgecolor="black",
        linewidth=0.8,
    )
    apply_theme(
        ax,
        theme,
        xlabel="Filo",
        ylabel="Numero de taxons",
        x_tick_rotation=45,
    )
    for bar, val in zip(bars, df_riqueza_filo["numero_de_taxons"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            float(val),
            f"{int(val)}",
            ha="center",
            va="bottom",
            fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
        )

    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_png_bar = output_dir / f"04_grafico_riqueza_filo_barras_{group_slug}.png"
    fig.savefig(str(out_png_bar), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png_bar))

    cmap_donut = plt.get_cmap("tab20")
    colors_filo = [cmap_donut(i % cmap_donut.N) for i in range(max(len(df_riqueza_filo), 1))]
    size_donut = get_figsize_by_complexity(theme, n_categories=len(df_riqueza_filo), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size_donut, dpi=int(theme.get("dpi", 600)))

    def _autopct_visible(pct: float) -> str:
        return f"{pct:.1f}%" if pct >= 4.0 else ""

    wedges, texts, autotexts = ax.pie(
        df_riqueza_filo["numero_de_taxons"].values,
        labels=None,
        colors=colors_filo,
        startangle=90,
        autopct=_autopct_visible,
        pctdistance=0.8,
        textprops={"fontsize": int(theme.get("font_size_base", 10))},
        wedgeprops={"edgecolor": "black", "linewidth": 0.8, "width": 0.45},
    )

    label_data = []
    for i, wedge in enumerate(wedges):
        angle = 0.5 * (wedge.theta1 + wedge.theta2)
        angle_rad = np.deg2rad(angle)
        x = np.cos(angle_rad)
        y = np.sin(angle_rad)
        side = 1 if x >= 0 else -1
        label_data.append(
            {
                "name": str(df_riqueza_filo["filo"].iloc[i]),
                "anchor": (0.82 * x, 0.82 * y),
                "target_y": 1.10 * y,
                "side": side,
            }
        )

    min_gap = 0.11
    y_lim = 1.34
    for side in (-1, 1):
        side_items = [d for d in label_data if d["side"] == side]
        side_items.sort(key=lambda d: d["target_y"])
        prev_y = -y_lim
        for item in side_items:
            y_adj = max(item["target_y"], prev_y + min_gap)
            y_adj = min(y_adj, y_lim)
            item["text_y"] = y_adj
            prev_y = y_adj

        for j in range(len(side_items) - 2, -1, -1):
            if side_items[j]["text_y"] > side_items[j + 1]["text_y"] - min_gap:
                side_items[j]["text_y"] = side_items[j + 1]["text_y"] - min_gap

        for item in side_items:
            text_x = 1.56 * side
            ha = "left" if side > 0 else "right"
            rad = 0.08 if side > 0 else -0.08
            ax.annotate(
                item["name"],
                xy=item["anchor"],
                xytext=(text_x, item["text_y"]),
                ha=ha,
                va="center",
                fontsize=int(theme.get("font_size_base", 10)),
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#555555",
                    "linewidth": 0.7,
                    "alpha": 0.8,
                    "shrinkA": 0,
                    "shrinkB": 0,
                    "connectionstyle": f"arc3,rad={rad}",
                },
            )

    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.35, 1.35)

    ax.text(
        0,
        0,
        f"Total\n{total_taxa}",
        ha="center",
        va="center",
        fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 14))),
        fontweight=str(theme.get("title_weight", "bold")),
    )

    ax.set_facecolor(str(theme.get("background_color", "white")))
    ax.figure.set_facecolor(str(theme.get("background_color", "white")))
    fig.tight_layout()
    out_png_donut = output_dir / f"05_grafico_riqueza_filo_rosca_{group_slug}.png"
    fig.savefig(str(out_png_donut), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png_donut))

    return {"filos": int(len(df_riqueza_filo)), "taxa_total": total_taxa}


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
    col_tipo = _get_col(df_projeto, "Tipo_de_Amostragem", "tipo_de_amostragem", "tipo_amostragem")
    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem"]
    if col_tipo is None or any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 10 FITO")

    df_div = df_projeto[df_projeto[col_tipo].astype(str).str.contains("quantit", case=False, na=False)].copy()
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
        ax1.text(b.get_x() + b.get_width() / 2, float(v), f"{v:.2f}", ha="center", va="bottom", fontsize=int(theme.get("annotation_size", 14)))

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
    col_tipo = _get_col(df_projeto, "Tipo_de_Amostragem", "tipo_de_amostragem", "tipo_amostragem")
    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "contagem"]
    if col_tipo is None or any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 11 FITO")

    df_sim = df_projeto[df_projeto[col_tipo].astype(str).str.contains("quantit", case=False, na=False)].copy()
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
    col_tipo = _get_col(df_projeto, "Tipo_de_Amostragem", "tipo_de_amostragem", "tipo_amostragem")
    if col_tipo is None:
        raise RuntimeError("[ERRO] Coluna de tipo de amostragem ausente no Bloco 12 FITO")

    required = ["nome_ponto", "nome_cientifico", "contagem"]
    if any(c not in df_projeto.columns for c in required):
        raise RuntimeError("[ERRO] Colunas obrigatorias ausentes no Bloco 12 FITO")

    df_suf = df_projeto[df_projeto[col_tipo].astype(str).str.contains("quantit", case=False, na=False)].copy()
    if df_suf.empty:
        return {"samples": 0, "warning": "sem dados quantitativos"}

    df_suf["nome_campanha"] = df_suf["nome_campanha"].astype(str).str.strip()
    df_suf["nome_ponto"] = df_suf["nome_ponto"].astype(str).str.strip()
    df_suf["nome_cientifico"] = df_suf["nome_cientifico"].astype(str).str.strip()
    df_suf["contagem"] = pd.Series(pd.to_numeric(df_suf["contagem"], errors="coerce"), index=df_suf.index).fillna(0)

    # Unidade amostral nao pode colapsar ponto repetido em campanhas diferentes.
    df_suf["amostra_id"] = df_suf["nome_campanha"] + " | " + df_suf["nome_ponto"]

    mat = df_suf.pivot_table(
        index="amostra_id",
        columns="nome_cientifico",
        values="contagem",
        aggfunc="sum",
        fill_value=0,
        observed=False,
    )
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
    ax.plot(x_axis, mean_sobs, linewidth=2.2, label="Riqueza observada", color=str(theme.get("primary_hex", "#11420C")))
    ax.plot(
        x_axis,
        mean_sest,
        linewidth=2.2,
        label="Riqueza estimada (Jackknife 1)",
        color=str(theme.get("secondary_hex", "#6A8F63")),
    )
    ax.fill_between(
        x_axis,
        mean_sest - std_sest,
        mean_sest + std_sest,
        alpha=0.18,
        color=str(theme.get("secondary_hex", "#6A8F63")),
    )
    apply_theme(ax, theme, xlabel="Numero de unidades amostrais", ylabel="Riqueza")
    ax.text(x_axis[-1] + 0.15, mean_sobs[-1], f"{mean_sobs[-1]:.0f}", color="black", va="center", fontsize=int(theme.get("annotation_size", 14)))
    ax.text(x_axis[-1] + 0.15, mean_sest[-1], f"{mean_sest[-1]:.1f}", color="black", va="center", fontsize=int(theme.get("annotation_size", 14)))
    place_legend_below_x_axis(fig, ax, theme, ncol=2)
    validate_axes_style(ax, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.04))

    out_png = output_dir / f"12_curva_suficiencia_amostral_{group_slug}.png"
    fig.savefig(str(out_png), dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))
    return {"samples": n_samples}


def _run_block_13(df_projeto: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    if df_projeto.empty:
        return {"rows": 0, "warning": "dataset vazio"}

    group_clean = re.sub(r"[^A-Za-z0-9]+", "_", _normalize_text(group).title()).strip("_")
    if "nome_projeto" in df_projeto.columns:
        projeto = str(df_projeto["nome_projeto"].dropna().mode().iloc[0]) if not df_projeto["nome_projeto"].dropna().empty else "Projeto"
    else:
        projeto = "Projeto"
    projeto_clean = re.sub(r"[^A-Za-z0-9]+", "_", projeto).strip("_")

    cols = [
        "occurrenceID",
        "eventID",
        "basisOfRecord",
        "country",
        "stateProvince",
        "institutionCode",
        "eventDate",
        "decimalLatitude",
        "decimalLongitude",
        "samplingProtocol",
        "samplingEffort",
        "scientificName",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "individualCount",
        "organismQuantity",
        "organismQuantityType",
        "occurrenceRemarks",
    ]
    out = pd.DataFrame(columns=cols)

    c_id = _get_col(df_projeto, "id_resultado_pk")
    c_camp = _get_col(df_projeto, "nome_campanha")
    c_ponto = _get_col(df_projeto, "nome_ponto")
    c_date = _get_col(df_projeto, "data_hora_coleta")
    c_lat = _get_col(df_projeto, "latitude")
    c_lon = _get_col(df_projeto, "longitude")
    c_method = _get_col(df_projeto, "metodo_de_captura")
    c_effort = _get_col(df_projeto, "esforco")
    c_unit = _get_col(df_projeto, "unidade_esforco")
    c_sci = _get_col(df_projeto, "nome_cientifico")
    c_reino = _get_col(df_projeto, "reino")
    c_filo = _get_col(df_projeto, "filo", "phylum")
    c_classe = _get_col(df_projeto, "classe", "class")
    c_ordem = _get_col(df_projeto, "ordem", "order")
    c_familia = _get_col(df_projeto, "familia", "family")
    c_genero = _get_col(df_projeto, "genero", "genus")
    c_count = _get_col(df_projeto, "contagem")
    c_bio = _get_col(df_projeto, "biomassa")

    for i, row in enumerate(df_projeto.reset_index(drop=True).to_dict(orient="records"), start=1):
        effort = ""
        if c_effort:
            effort = str(row.get(c_effort, "") or "").strip()
            if c_unit:
                unit = str(row.get(c_unit, "") or "").strip()
                if unit:
                    effort = f"{effort} {unit}".strip()

        occurrence_id = str(row.get(c_id)) if c_id else str(i)
        event_id = f"{str(row.get(c_camp, '')).strip()}|{str(row.get(c_ponto, '')).strip()}"

        count_val = pd.to_numeric(row.get(c_count), errors="coerce") if c_count else np.nan
        bio_val = pd.to_numeric(row.get(c_bio), errors="coerce") if c_bio else np.nan

        out.loc[len(out)] = {
            "occurrenceID": occurrence_id,
            "eventID": event_id,
            "basisOfRecord": "HumanObservation",
            "country": "Brazil",
            "stateProvince": "Minas Gerais",
            "institutionCode": "Opyta",
            "eventDate": str(row.get(c_date, "")) if c_date else "",
            "decimalLatitude": row.get(c_lat, "") if c_lat else "",
            "decimalLongitude": row.get(c_lon, "") if c_lon else "",
            "samplingProtocol": str(row.get(c_method, "")) if c_method else "",
            "samplingEffort": effort,
            "scientificName": str(row.get(c_sci, "")) if c_sci else "",
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

    out_file = output_dir / f"DarwinCore_{group_clean}_{projeto_clean}.xlsx"
    out.to_excel(out_file, index=False, engine="openpyxl")
    generated_files.append(str(out_file))
    return {"rows": int(len(out)), "file": str(out_file)}


def run_fitoplancton_pipeline(
    *,
    project_id: int,
    group: str,
    theme: dict,
    output_dir: Path,
    env_file: str | None = None,
    block: str = "all",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = _load_fitoplancton_df(project_id=project_id, group=group, env_file=env_file)

    block_sel = str(block).strip().lower()
    executed_blocks: list[str] = []
    generated_files: list[str] = []

    details: dict = {
        "rows_loaded": int(len(df)),
        "group": group,
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
        raise ValueError("Unsupported block for fitoplancton pipeline. Use '3', '4', '5', '6', '7', '10', '11', '12', '13' or 'all'.")

    details["executed_blocks"] = executed_blocks
    details["generated_files"] = generated_files
    return details
