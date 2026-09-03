from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

from opyta_analysis.pipelines.diagnostico.darwincore_ief import export_darwincore_ief
from opyta_analysis.pipelines.diagnostico.occurrence_summary import export_occurrence_summary
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


def _campaign_short_label(campaign: str) -> str:
    campaign_text = str(campaign).strip()
    match = re.match(r"^C0*(\d+)", campaign_text, flags=re.IGNORECASE)
    if match:
        return f"C{int(match.group(1)):02d}"
    hydrologic = re.match(
        r"^([A-Z0-9]+)_AH\d{4}_(\d{4})(\d{2})(?:_R\d+)?$",
        campaign_text,
        flags=re.IGNORECASE,
    )
    if hydrologic:
        return f"{hydrologic.group(1)}\n{hydrologic.group(3)}/{hydrologic.group(2)}"
    return campaign_text


def _campaign_year(campaign: str) -> int | None:
    match = re.search(r"(20\d{2}|19\d{2})", str(campaign))
    return int(match.group(1)) if match else None


def _campaign_season(campaign: str) -> str:
    text = str(campaign).upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text):
        return "CH"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text):
        return "SC"
    norm = _normalize_text(campaign)
    if "chuva" in norm:
        return "CH"
    if "seca" in norm:
        return "SC"
    return "ND"


def _season_colors(theme: dict) -> dict[str, str]:
    return {
        "CH": str(theme.get("primary_hex", "#002060")),
        "SC": str(theme.get("secondary_hex", "#5B9BD5")),
        "ND": str(theme.get("highlight_hex", theme.get("primary_hex", "#1F4E79"))),
    }


def _season_label(season: str) -> str:
    return {"CH": "CH", "SC": "SC", "ND": "Campanha"}.get(season, season)


def _mean_label(value: float, decimals: int = 1) -> str:
    return f"Média geral ({value:.{decimals}f})"


def _add_year_separators(ax, campaigns: list[str]) -> None:
    years = [_campaign_year(c) for c in campaigns]
    for i in range(1, len(years)):
        if years[i] != years[i - 1]:
            ax.axvline(i - 0.5, color="#D0D0D0", linewidth=0.7, linestyle="-", zorder=0)


def _campaign_tick_step(total_campaigns: int) -> int:
    if total_campaigns <= 10:
        return 1
    if total_campaigns <= 16:
        return 2
    return 4


def _campaign_axis_ticks(campaigns: list[str], theme: dict) -> tuple[np.ndarray, list[str], int, str, int]:
    x = np.arange(len(campaigns))
    labels = [_campaign_short_label(c) for c in campaigns]
    rotation = 90 if len(campaigns) > 4 else 0
    ha = "center" if rotation == 90 else "right"
    font_size = theme_campaign_label_size(len(campaigns), theme)
    return x, labels, rotation, ha, font_size


def theme_campaign_label_size(total_campaigns: int, theme: dict | None = None) -> int:
    base = 10 if theme is None else int(theme.get("campaign_label_size", theme.get("font_size_base", 10)))
    if total_campaigns > 16:
        if theme is not None and "dense_campaign_label_size" in theme:
            return int(theme["dense_campaign_label_size"])
        return max(5, base - 6)
    if total_campaigns > 10:
        return max(8, base - 2)
    if total_campaigns > 6:
        return max(9, base - 1)
    return base


PROJECT_FALLBACK_HINTS = {
    9: {
        "codigo_interno_opyta": "BRAAVG002",
        "nome_empresa_contains": "brandt",
        "nome_projeto_contains": "brumado",
    },
    62: {
        "nome_empresa_contains": "rocha consultoria",
        "nome_projeto_contains": "sam metais",
    },
    183: {
        "codigo_interno_opyta": "DUCGEO001",
        "nome_empresa_contains": "geomil",
        "nome_projeto_contains": "monitoramento ducal",
    },
    187: {
        "codigo_interno_opyta": "TOTVAL001",
        "nome_empresa_contains": "total",
        "nome_projeto_contains": "brucutu",
    },
}

PROJECT_CODE_BY_ID = {
    9: "BRAAVG002",
    183: "DUCGEO001",
    187: "TOTVAL001",
}

PROJECT_CAMPAIGN_OVERRIDES = {
    187: {
        "C034-2025-10-CH": "C034-2025-10-SC",
    },
}


def _apply_project_campaign_overrides(
    df: pd.DataFrame,
    project_id: int,
    group: str,
) -> tuple[pd.DataFrame, list[dict]]:
    if df.empty or "nome_campanha" not in df.columns:
        return df, []

    if "ictio" not in _normalize_text(group):
        return df, []

    replacements = PROJECT_CAMPAIGN_OVERRIDES.get(int(project_id), {})
    if not replacements:
        return df, []

    df_out = df
    applied: list[dict] = []
    campaign_values = df["nome_campanha"].astype(str).str.strip()
    for old, new in replacements.items():
        mask = campaign_values == old
        rows = int(mask.sum())
        if rows == 0:
            continue
        if df_out is df:
            df_out = df.copy()
        df_out.loc[mask, "nome_campanha"] = new
        applied.append(
            {
                "project_id": int(project_id),
                "group": group,
                "column": "nome_campanha",
                "from": old,
                "to": new,
                "rows": rows,
            }
        )

    return df_out, applied


def _apply_campaign_filter(df: pd.DataFrame, campaign_filter: list[str] | None) -> tuple[pd.DataFrame, dict]:
    requested = [str(c).strip() for c in campaign_filter or [] if str(c).strip()]
    if not requested or "nome_campanha" not in df.columns:
        return df, {"requested": requested, "matched": [], "missing": []}

    campaign_values = df["nome_campanha"].astype(str).str.strip()
    available = set(campaign_values.dropna().unique().tolist())
    matched = [campaign for campaign in requested if campaign in available]
    missing = [campaign for campaign in requested if campaign not in available]
    filtered = df[campaign_values.isin(requested)].copy()
    return filtered.reset_index(drop=True), {"requested": requested, "matched": matched, "missing": missing}


def _drop_effort_only_records(df: pd.DataFrame) -> pd.DataFrame:
    if "_effort_only_zero_record" not in df.columns:
        return df
    mask = df["_effort_only_zero_record"].fillna(False).astype(bool)
    return df[~mask].copy()


def _append_ictio_zero_effort_rows(
    df: pd.DataFrame,
    project_id: int,
    group: str,
    sb,
) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["_effort_only_zero_record"] = False

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": project_id},
        select=(
            "id_ponto_coleta,nome_ponto,id_campanha,latitude,longitude,"
            "data_hora_coleta,bacia_hidrografica,curso_d_agua,municipio"
        ),
    )
    if not pontos:
        return df

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": group},
        select=(
            "id_esforco,id_ponto_coleta,metodo_de_captura,esforco,"
            "unidade_esforco,tipo_amostragem,tipo_de_amostragem"
        ),
    )
    esforcos_proj = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos_proj:
        return df

    resultados = paginate(sb, "resultados_ictiofauna", select="id_esforco")
    effort_ids_with_results = {r.get("id_esforco") for r in resultados if r.get("id_esforco") is not None}
    zero_efforts = [e for e in esforcos_proj if e.get("id_esforco") not in effort_ids_with_results]
    if not zero_efforts:
        return df

    template_values = {}
    for col in df.columns:
        non_null = df[col].dropna()
        template_values[col] = non_null.iloc[0] if not non_null.empty else np.nan

    zero_rows = []
    for effort in zero_efforts:
        point = pontos_map.get(effort.get("id_ponto_coleta"), {})
        row = {col: np.nan for col in df.columns}
        row.update(
            {
                "id_resultado_pk": np.nan,
                "nome_empresa": template_values.get("nome_empresa", np.nan),
                "nome_projeto": template_values.get("nome_projeto", np.nan),
                "codigo_opyta": template_values.get("codigo_opyta", np.nan),
                "nome_campanha": camp_map.get(point.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": point.get("nome_ponto"),
                "latitude": point.get("latitude"),
                "longitude": point.get("longitude"),
                "grupo_biologico": group,
                "nome_cientifico": np.nan,
                "contagem": 0.0,
                "biomassa": 0.0,
                "bmwp_score": np.nan,
                "codigo_interno_opyta": template_values.get("codigo_interno_opyta", np.nan),
                "data_hora_coleta": point.get("data_hora_coleta"),
                "bacia_hidrografica": point.get("bacia_hidrografica") or point.get("curso_d_agua"),
                "metodo_de_captura": effort.get("metodo_de_captura"),
                "esforco": effort.get("esforco"),
                "unidade_esforco": effort.get("unidade_esforco"),
                "tipo_amostragem": effort.get("tipo_amostragem") or effort.get("tipo_de_amostragem"),
                "id_empreendimento": template_values.get("id_empreendimento", np.nan),
                "nome_empreendimento": template_values.get("nome_empreendimento", np.nan),
                "id_projeto": int(project_id),
                "_effort_only_zero_record": True,
            }
        )
        zero_rows.append(row)

    if not zero_rows:
        return df

    return pd.concat([df, pd.DataFrame(zero_rows, columns=df.columns)], ignore_index=True)


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
    df = _append_ictio_zero_effort_rows(df, project_id, group, sb)
    df = _enrich_ictio_species_attributes(df, sb)
    _validate_project_scope(df, project_id)
    return df.reset_index(drop=True)


def _load_ictio_detail_df(project_code: str, env_file: str | None) -> pd.DataFrame:
    """Carrega `resultados_ictiofauna_detalhe` (uma linha por individuo/lote medido).

    E a base da secao reprodutiva: a view consolidada agrega e nao expoe sexo,
    estadio de maturacao gonadal, comprimento padrao nem peso de gonada.
    """
    if not project_code:
        return pd.DataFrame()

    sb = get_client(env_file)
    rows = paginate(sb, "resultados_ictiofauna_detalhe", filters={"codigo_opyta": project_code}, select="*")
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    especies = paginate(sb, "especies", select="id_especie,nome_cientifico,nome_popular,ordem,familia")
    if especies:
        registry = pd.DataFrame(especies).drop_duplicates("id_especie")
        df = df.merge(registry, on="id_especie", how="left")

    for column in ["numero_de_individuos", "cp_cm", "ct_cm", "pc_g", "pg_g"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    if "numero_de_individuos" in df.columns:
        df["numero_de_individuos"] = df["numero_de_individuos"].fillna(0)
    return df


def _emg_stage(code: object) -> int | None:
    match = re.match(r"^[FM](\d)$", str(code or "").strip(), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _enrich_ictio_species_attributes(df: pd.DataFrame, sb) -> pd.DataFrame:
    if df.empty or "nome_cientifico" not in df.columns:
        return df

    registry_cols = [
        "id_especie",
        "nome_cientifico",
        "nome_popular",
        "reino",
        "filo",
        "classe",
        "ordem",
        "familia",
        "genero",
        "autor_e_ano",
        "bmwp_score",
        "status_estadual",
        "status_ameaca_nacional",
        "status_ameaca_global",
        "status_copam",
        "cites",
        "dependencia_florestal",
        "endemismo",
        "habito_alimentar",
        "guilda_alimentar",
        "estrategia_reprodutiva",
        "sensibilidade_ambiental",
        "migratorio",
        "raridade",
        "origem",
        "distribuicao",
        "cinegetica",
        "valor_economico",
        "xerimbabo",
        "observacoes",
    ]
    try:
        rows = paginate(sb, "especies", select=",".join(registry_cols))
    except Exception:
        rows = paginate(sb, "especies", select="*")
    if not rows:
        return df

    registry = pd.DataFrame(rows)
    if registry.empty or "nome_cientifico" not in registry.columns:
        return df

    present_cols = [col for col in registry_cols if col in registry.columns]
    registry = registry[present_cols].copy()
    registry["_species_key"] = registry["nome_cientifico"].map(_normalize_text)
    registry = registry.dropna(subset=["_species_key"]).drop_duplicates("_species_key")

    result = df.copy()
    original_cols = set(result.columns)
    result["_species_key"] = result["nome_cientifico"].map(_normalize_text)
    merge_cols = ["_species_key"] + [col for col in present_cols if col != "nome_cientifico"]
    result = result.merge(registry[merge_cols], on="_species_key", how="left", suffixes=("", "_registry"))

    for col in [col for col in present_cols if col != "nome_cientifico"]:
        registry_col = f"{col}_registry" if col in original_cols else col
        if registry_col not in result.columns:
            continue
        if col in original_cols:
            current = result[col]
            blank = current.isna()
            if current.dtype == object:
                blank = blank | current.astype(str).str.strip().isin(["", "nan", "None"])
            result.loc[blank, col] = result.loc[blank, registry_col]
            if registry_col != col:
                result = result.drop(columns=[registry_col])

    return result.drop(columns=["_species_key"], errors="ignore")


def _attach_line_level_biomass(df: pd.DataFrame, theme: dict) -> pd.DataFrame:
    source_value = theme.get("ictio_line_level_source_excel")
    if not source_value:
        return df

    source = Path(str(source_value))
    if not source.exists():
        raise FileNotFoundError(f"Planilha de biomassa analitica nao encontrada: {source}")

    source_df = pd.read_excel(source, sheet_name="Resultados_Ictiofauna")
    required = [
        "Campanha",
        "Ponto",
        "Metodo_de_Captura",
        "Tipo_de_Amostragem",
        "Nome_Cientifico",
        "Numero_de_Individuos",
        "PC_g",
    ]
    missing = [column for column in required if column not in source_df.columns]
    if missing:
        raise RuntimeError(
            "Planilha de biomassa analitica sem colunas obrigatorias: "
            + ", ".join(missing)
        )

    source_df = source_df[required].dropna(subset=["Nome_Cientifico"]).copy()
    source_df["Numero_de_Individuos"] = pd.to_numeric(
        source_df["Numero_de_Individuos"], errors="coerce"
    ).fillna(0)
    source_df["PC_g"] = pd.to_numeric(source_df["PC_g"], errors="coerce")
    source_df["biomassa_total_analitica"] = (
        source_df["Numero_de_Individuos"] * source_df["PC_g"]
    )

    source_keys = {
        "Campanha": "nome_campanha",
        "Ponto": "nome_ponto",
        "Metodo_de_Captura": "metodo_de_captura",
        "Tipo_de_Amostragem": "tipo_amostragem",
        "Nome_Cientifico": "nome_cientifico",
    }
    grouped = (
        source_df.rename(columns=source_keys)
        .groupby(list(source_keys.values()), dropna=False)["biomassa_total_analitica"]
        .sum(min_count=1)
        .reset_index()
    )

    merge_keys = list(source_keys.values())
    result = df.merge(grouped, on=merge_keys, how="left")
    result.attrs["biomass_source"] = str(source)
    result.attrs["biomass_formula"] = "Numero_de_Individuos * PC_g por linha, agregado por soma"
    return result


def _resolve_line_biomass(df_quant: pd.DataFrame, theme: dict) -> tuple[str, str]:
    """Cria `_biomassa_linha` em `df_quant` e devolve (coluna, formula aplicada).

    A coluna `biomassa` de `biota_analise_consolidada` recebe o `pc_g` da origem,
    que e o peso medio por individuo do lote e nao a biomassa total da linha.
    Somar essa coluna direto subestima CPUEb sempre que `contagem > 1`. Quando o
    projeto declara `ictio_biomass_from_mean_weight`, a biomassa total da linha e
    reconstruida como `contagem * biomassa` antes de qualquer agregacao.
    """
    if "biomassa_total_analitica" in df_quant.columns:
        df_quant["_biomassa_linha"] = df_quant["biomassa_total_analitica"]
        return "_biomassa_linha", "biomassa_total_analitica (planilha linha a linha)"

    if bool(theme.get("ictio_biomass_from_mean_weight", False)):
        df_quant["_biomassa_linha"] = df_quant["contagem"] * df_quant["biomassa"]
        return "_biomassa_linha", "contagem * biomassa (peso medio por individuo)"

    df_quant["_biomassa_linha"] = df_quant["biomassa"]
    return "_biomassa_linha", "biomassa (coluna consolidada, sem reconstrucao)"


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    numeric_values = pd.to_numeric(values, errors="coerce")
    numeric_weights = pd.to_numeric(weights, errors="coerce").fillna(0)
    mask = numeric_values.notna() & numeric_weights.gt(0)
    if not bool(mask.any()):
        return float("nan")
    return float(np.average(numeric_values[mask], weights=numeric_weights[mask]))


def _write_biometry_workbook(table: pd.DataFrame, out_xlsx: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Biometria"

    ws.merge_cells("A1:A2")
    ws.merge_cells("B1:B2")
    ws.merge_cells("C1:E1")
    ws.merge_cells("F1:H1")
    headers = {
        "A1": "ESPÉCIE",
        "B1": "N",
        "C1": "COMPRIMENTO PADRÃO (CP) CM",
        "F1": "PESO CORPORAL (PC) GRAMAS",
        "C2": "MÍNIMO",
        "D2": "MÉDIA",
        "E2": "MÁXIMO",
        "F2": "MÍNIMO",
        "G2": "MÁXIMO",
        "H2": "BIOMASSA",
    }
    for cell, value in headers.items():
        ws[cell] = value

    header_fill = PatternFill("solid", fgColor="D9EAD3")
    subheader_fill = PatternFill("solid", fgColor="EEF5EC")
    thin = Side(style="thin", color="B7B7B7")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for row in ws.iter_rows(min_row=1, max_row=2, min_col=1, max_col=8):
        for cell in row:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.fill = header_fill if cell.row == 1 else subheader_fill
            cell.border = border

    ordered_cols = [
        "especie",
        "n",
        "cp_min_cm",
        "cp_media_cm",
        "cp_max_cm",
        "pc_min_g",
        "pc_max_g",
        "biomassa_g",
    ]
    for row_index, row in enumerate(table[ordered_cols].itertuples(index=False), start=3):
        for col_index, value in enumerate(row, start=1):
            ws.cell(row=row_index, column=col_index, value=value)
            ws.cell(row=row_index, column=col_index).border = border
            if col_index == 1:
                ws.cell(row=row_index, column=col_index).alignment = Alignment(horizontal="left")
            else:
                ws.cell(row=row_index, column=col_index).alignment = Alignment(horizontal="right")

    for col in range(2, 9):
        for cell in ws.iter_cols(min_col=col, max_col=col, min_row=3, max_row=ws.max_row):
            for item in cell:
                item.number_format = "0.00" if col != 2 else "0"

    widths = [36, 8, 12, 12, 12, 12, 12, 13]
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:H{max(ws.max_row, 2)}"

    data_ws = wb.create_sheet("Dados")
    flat_headers = [
        "especie",
        "n",
        "cp_min_cm",
        "cp_media_cm",
        "cp_max_cm",
        "pc_min_g",
        "pc_max_g",
        "biomassa_g",
    ]
    data_ws.append(flat_headers)
    for row in table[flat_headers].itertuples(index=False):
        data_ws.append(list(row))
    for index, width in enumerate(widths, start=1):
        data_ws.column_dimensions[get_column_letter(index)].width = width
    data_ws.freeze_panes = "A2"

    wb.save(out_xlsx)


def _run_block_biometry(
    df_projeto: pd.DataFrame,
    group: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
    group_slug = _safe_group_name(group)
    out_xlsx = output_dir / f"13_tabela_biometria_biomassa_{group_slug}.xlsx"
    source_value = theme.get("ictio_line_level_source_excel")

    empty = pd.DataFrame(
        columns=[
            "especie",
            "n",
            "cp_min_cm",
            "cp_media_cm",
            "cp_max_cm",
            "pc_min_g",
            "pc_max_g",
            "biomassa_g",
        ]
    )
    if not source_value:
        _write_biometry_workbook(empty, out_xlsx)
        generated_files.append(str(out_xlsx))
        return {"species": 0, "warning": "fonte linha a linha nao configurada"}

    source = Path(str(source_value))
    if not source.exists():
        raise FileNotFoundError(f"Planilha de biometria nao encontrada: {source}")

    source_df = pd.read_excel(source, sheet_name="Resultados_Ictiofauna")
    required = ["Campanha", "Nome_Cientifico", "Numero_de_Individuos", "CP_cm", "PC_g"]
    missing = [column for column in required if column not in source_df.columns]
    if missing:
        raise RuntimeError(
            "Planilha de biometria sem colunas obrigatorias: " + ", ".join(missing)
        )

    source_df = source_df[required].dropna(subset=["Nome_Cientifico"]).copy()
    campaigns = sorted(df_projeto["nome_campanha"].dropna().astype(str).str.strip().unique().tolist())
    if campaigns:
        source_df = source_df[source_df["Campanha"].astype(str).str.strip().isin(campaigns)].copy()

    source_df["Numero_de_Individuos"] = pd.to_numeric(
        source_df["Numero_de_Individuos"], errors="coerce"
    ).fillna(0)
    source_df["CP_cm"] = pd.to_numeric(source_df["CP_cm"], errors="coerce")
    source_df["PC_g"] = pd.to_numeric(source_df["PC_g"], errors="coerce")
    source_df = source_df[source_df["Numero_de_Individuos"] > 0].copy()
    source_df["biomassa_g"] = source_df["Numero_de_Individuos"] * source_df["PC_g"]

    rows = []
    for species, group_df in source_df.groupby("Nome_Cientifico", dropna=False):
        rows.append(
            {
                "especie": str(species).strip(),
                "n": int(group_df["Numero_de_Individuos"].sum()),
                "cp_min_cm": float(group_df["CP_cm"].min()),
                "cp_media_cm": _weighted_mean(group_df["CP_cm"], group_df["Numero_de_Individuos"]),
                "cp_max_cm": float(group_df["CP_cm"].max()),
                "pc_min_g": float(group_df["PC_g"].min()),
                "pc_max_g": float(group_df["PC_g"].max()),
                "biomassa_g": float(group_df["biomassa_g"].sum()),
            }
        )

    table = pd.DataFrame(rows)
    if table.empty:
        table = empty
    else:
        table = table.sort_values("especie").reset_index(drop=True)

    _write_biometry_workbook(table, out_xlsx)
    generated_files.append(str(out_xlsx))

    astyanax = table[table["especie"].astype(str).str.lower().eq("astyanax lacustris")]
    return {
        "species": int(len(table)),
        "campaigns": campaigns,
        "source": str(source),
        "astyanax_lacustris": astyanax.iloc[0].to_dict() if not astyanax.empty else None,
    }


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


def _normalize_point_id(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def _get_control_points(theme: dict) -> list[str]:
    pts = theme.get("control_points")
    if not isinstance(pts, list):
        return []
    return [str(p).strip() for p in pts if str(p).strip()]


def _get_control_indices(points: list[str], control_points: list[str]) -> list[int]:
    if not points or not control_points:
        return []
    control_norm = {_normalize_point_id(p) for p in control_points}
    return [i for i, p in enumerate(points) if _normalize_point_id(p) in control_norm]


def _get_control_groups(theme: dict) -> list[dict]:
    """Returns list of {label, points} dicts for grouped control area brackets.

    Falls back to a single group from ``control_points`` if ``control_groups`` is absent.
    """
    raw = theme.get("control_groups")
    if isinstance(raw, list) and raw:
        out = []
        for g in raw:
            if not isinstance(g, dict):
                continue
            label = str(g.get("label", "")).strip()
            pts = g.get("points") or []
            if not isinstance(pts, list):
                continue
            pts_clean = [str(p).strip() for p in pts if str(p).strip()]
            if label and pts_clean:
                out.append({"label": label, "points": pts_clean})
        return out
    legacy = _get_control_points(theme)
    if legacy:
        return [{"label": "Area controle", "points": legacy}]
    return []


def _draw_control_brackets(ax, points: list[str], theme: dict) -> bool:
    """Draws bracket-style group labels under x-tick labels for control area groups.

    Returns True if any bracket was drawn, False otherwise.
    """
    groups = _get_control_groups(theme)
    if not points or not groups:
        return False
    from matplotlib.transforms import blended_transform_factory

    trans = blended_transform_factory(ax.transData, ax.transAxes)
    text_color = str(theme.get("control_area_text_hex", "#0B3D20"))
    fontsize = int(theme.get("label_size", theme.get("font_size_base", 14)))
    y_bracket = -0.18
    y_label = -0.22
    tick = 0.018
    drew = False
    for grp in groups:
        norm = {_normalize_point_id(p) for p in grp.get("points", [])}
        idxs = [i for i, p in enumerate(points) if _normalize_point_id(p) in norm]
        if not idxs:
            continue
        x0 = min(idxs) - 0.4
        x1 = max(idxs) + 0.4
        ax.plot([x0, x1], [y_bracket, y_bracket], color=text_color, lw=1.4,
                transform=trans, clip_on=False, solid_capstyle="butt")
        ax.plot([x0, x0], [y_bracket, y_bracket + tick], color=text_color, lw=1.4,
                transform=trans, clip_on=False)
        ax.plot([x1, x1], [y_bracket, y_bracket + tick], color=text_color, lw=1.4,
                transform=trans, clip_on=False)
        ax.text((x0 + x1) / 2, y_label, str(grp.get("label", "")),
                ha="center", va="top", transform=trans,
                fontsize=fontsize, color=text_color)
        drew = True
    return drew


def _small_multiple_metric(
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
    *,
    decimals: int = 1,
) -> None:
    if not points or not campaigns:
        return

    colors = _season_colors(theme)
    marker_size = float(theme.get("small_multiple_marker_size", 24))
    line_width = float(theme.get("small_multiple_linewidth", 1.0))
    point_label_size = int(theme.get("point_label_size", theme.get("font_size_base", 11)))
    axis_label_size = max(8, int(theme.get("label_size", int(theme.get("font_size_base", 11)) + 2)) - 2)
    ncols = min(4, max(1, len(points)))
    nrows = int(np.ceil(len(points) / ncols))
    base_size = theme.get("figsize_standard", [11.69, 8.27])
    fig_width = float(base_size[0])
    fig_height = max(float(base_size[1]), 3.0 * nrows)
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(fig_width, fig_height),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
        squeeze=False,
    )

    x, labels, label_rotation, label_ha, label_font_size = _campaign_axis_ticks(campaigns, theme)
    season_order = ["CH", "SC", "ND"]
    seasons_present = [season for season in season_order if season in {_campaign_season(c) for c in campaigns}]
    values_all = pd.to_numeric(table[value_col], errors="coerce").fillna(0)
    overall_mean = float(values_all.mean()) if not values_all.empty else 0.0
    ymax = max(float(values_all.max()) if not values_all.empty else 0.0, overall_mean)
    ymax = max(ymax * 1.15, 1.0)

    for ax, point in zip(axes.ravel(), points):
        point_data = table[table["nome_ponto"] == point].set_index("nome_campanha").reindex(campaigns).reset_index()
        values = pd.to_numeric(point_data[value_col], errors="coerce").fillna(0).to_numpy(dtype=float)
        seasons = [_campaign_season(c) for c in campaigns]

        ax.plot(x, values, color="#606060", linewidth=line_width, zorder=1)
        for season in seasons_present:
            mask = np.array([s == season for s in seasons])
            ax.scatter(
                x[mask],
                values[mask],
                s=marker_size,
                color=colors[season],
                edgecolor="black",
                linewidth=0.4,
                zorder=2,
            )
        ax.axhline(overall_mean, color="#7F7F7F", linewidth=0.9, linestyle="--", zorder=0)
        ax.text(
            0.02,
            0.92,
            point,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontweight="bold",
            fontsize=point_label_size,
        )
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=label_rotation, ha=label_ha)
        _add_year_separators(ax, campaigns)
        apply_theme(ax, theme, xlabel="", ylabel="")
        ax.tick_params(axis="x", labelsize=label_font_size, labelbottom=True, pad=1)

    for ax in axes.ravel()[len(points):]:
        ax.axis("off")
    for ax in axes[-1, :]:
        ax.set_xlabel("Campanha")
        ax.xaxis.label.set_size(axis_label_size)
    # Garantir rótulos do eixo X mesmo quando o painel inferior do grid está desligado
    for ax in axes.ravel()[:len(points)]:
        ax.tick_params(axis="x", labelsize=label_font_size, labelbottom=True, pad=1)
        ax.set_xlabel("Campanha")
        ax.xaxis.label.set_size(axis_label_size)

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=colors[season],
            markeredgecolor="black",
            label=_season_label(season),
        )
        for season in seasons_present
    ]
    handles.append(
        Line2D(
            [0],
            [0],
            color="#7F7F7F",
            linestyle="--",
            linewidth=0.9,
            label=_mean_label(overall_mean, decimals),
        )
    )
    fig.legend(handles=handles, loc="upper center", ncol=len(handles), frameon=False)
    fig.supylabel(ylabel, x=0.01, fontsize=axis_label_size)
    extra_bottom = 0.08 if len(campaigns) > 10 else 0.03
    fig.tight_layout(rect=[0.05, extra_bottom, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _plot_grouped_campaign_bars(
    *,
    table: pd.DataFrame,
    value_col: str,
    ylabel: str,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
    decimals: int,
) -> None:
    pivot = (
        table.pivot_table(
            index="nome_ponto",
            columns="nome_campanha",
            values=value_col,
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(index=points, columns=campaigns, fill_value=0)
    )
    colors = palette_from_theme(theme, max(len(campaigns), 1))
    size = get_figsize_by_complexity(theme, n_categories=len(points), prefer_landscape=True)
    fig, ax = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(points))
    width = 0.8 / max(len(campaigns), 1)

    for index, campaign in enumerate(campaigns):
        values = pivot[campaign].to_numpy(dtype=float)
        bars = ax.bar(
            x + (index - (len(campaigns) - 1) / 2) * width,
            values,
            width=width,
            label=_campaign_short_label(campaign).replace("\n", " - "),
            color=colors[index],
            edgecolor="black",
            linewidth=0.8,
        )
        for bar, value in zip(bars, values):
            if decimals == 0:
                label = f"{int(round(float(value)))}"
            else:
                label = f"{float(value):.{decimals}f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                float(value),
                label,
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


def _small_multiple_diversity(
    diversity: pd.DataFrame,
    out_png: Path,
    theme: dict,
    points: list[str],
    campaigns: list[str],
) -> None:
    if not points or not campaigns:
        return

    primary = str(theme.get("primary_hex", "#002060"))
    secondary = str(theme.get("secondary_hex", "#5B9BD5"))
    marker_size = max(float(theme.get("small_multiple_marker_size", 38)) ** 0.5, 3.0)
    line_width = float(theme.get("small_multiple_linewidth", 1.1))
    point_label_size = int(theme.get("point_label_size", theme.get("font_size_base", 11)))
    axis_label_size = max(8, int(theme.get("label_size", int(theme.get("font_size_base", 11)) + 2)) - 2)
    plot_data = diversity[diversity["nome_ponto"].isin(points)].copy()
    shannon_all = pd.to_numeric(plot_data["Shannon_H"], errors="coerce").fillna(0)
    pielou_all = pd.to_numeric(plot_data["Pielou_J"], errors="coerce").fillna(0)
    shannon_mean = float(shannon_all.mean()) if not shannon_all.empty else 0.0
    pielou_mean = float(pielou_all.mean()) if not pielou_all.empty else 0.0
    ymax = max(
        float(shannon_all.max()) if not shannon_all.empty else 0.0,
        float(pielou_all.max()) if not pielou_all.empty else 0.0,
        shannon_mean,
        pielou_mean,
        1.0,
    ) * 1.15

    ncols = min(4, max(1, len(points)))
    nrows = int(np.ceil(len(points) / ncols))
    base_size = theme.get("figsize_standard", [11.69, 8.27])
    fig_width = float(base_size[0])
    fig_height = max(float(base_size[1]), 3.0 * nrows)
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(fig_width, fig_height),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
        squeeze=False,
    )

    x, labels, label_rotation, label_ha, label_font_size = _campaign_axis_ticks(campaigns, theme)
    label_font_size = int(theme.get("diversity_campaign_label_size", label_font_size))
    for ax, point in zip(axes.ravel(), points):
        point_data = plot_data[plot_data["nome_ponto"] == point].set_index("nome_campanha").reindex(campaigns).reset_index()
        shannon = pd.to_numeric(point_data["Shannon_H"], errors="coerce").fillna(0).to_numpy(dtype=float)
        pielou = pd.to_numeric(point_data["Pielou_J"], errors="coerce").fillna(0).to_numpy(dtype=float)
        ax.plot(x, shannon, color=primary, marker="o", markersize=marker_size, linewidth=line_width)
        ax.plot(x, pielou, color=secondary, marker="s", markersize=marker_size, linewidth=line_width)
        ax.axhline(shannon_mean, color=primary, linewidth=0.8, linestyle="--", alpha=0.75)
        ax.axhline(pielou_mean, color=secondary, linewidth=0.8, linestyle="--", alpha=0.75)
        ax.text(
            0.02,
            0.92,
            point,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontweight="bold",
            fontsize=point_label_size,
        )
        ax.set_ylim(0, ymax)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=label_rotation, ha=label_ha)
        _add_year_separators(ax, campaigns)
        apply_theme(ax, theme, xlabel="", ylabel="")
        ax.tick_params(axis="x", labelsize=label_font_size, labelbottom=True, pad=1)

    for ax in axes.ravel()[len(points):]:
        ax.axis("off")
    for ax in axes[-1, :]:
        ax.set_xlabel("Campanha")
        ax.xaxis.label.set_size(axis_label_size)
    # Garantir rótulos do eixo X mesmo quando o painel inferior do grid está desligado
    for ax in axes.ravel()[:len(points)]:
        ax.tick_params(axis="x", labelsize=label_font_size, labelbottom=True, pad=1)
        ax.set_xlabel("Campanha")
        ax.xaxis.label.set_size(axis_label_size)

    handles = [
        Line2D([0], [0], marker="o", color=primary, label="Shannon"),
        Line2D([0], [0], marker="s", color=secondary, label="Pielou"),
        Line2D([0], [0], color=primary, linestyle="--", linewidth=0.8, label=f"Média Shannon ({shannon_mean:.2f})"),
        Line2D([0], [0], color=secondary, linestyle="--", linewidth=0.8, label=f"Média Pielou ({pielou_mean:.2f})"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False)
    fig.supylabel("Índice", x=0.01, fontsize=axis_label_size)
    extra_bottom = 0.08 if len(campaigns) > 10 else 0.03
    fig.tight_layout(rect=[0.05, extra_bottom, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _plot_few_campaign_diversity(
    *,
    diversity: pd.DataFrame,
    out_png: Path,
    theme: dict,
    campaigns: list[str],
) -> None:
    x = np.arange(len(diversity))
    labels = []
    for _, row in diversity.iterrows():
        point = str(row["nome_ponto"])
        if point.endswith("(Geral)"):
            campaign_label = _campaign_short_label(str(row["nome_campanha"])).replace("\n", " - ")
            labels.append(f"{campaign_label} (Geral)")
        else:
            labels.append(point)
    shannon = pd.to_numeric(diversity["Shannon_H"], errors="coerce").fillna(0).to_numpy(dtype=float)
    pielou = pd.to_numeric(diversity["Pielou_J"], errors="coerce").fillna(0).to_numpy(dtype=float)

    size = get_figsize_by_complexity(theme, n_categories=len(labels), prefer_landscape=True)
    fig, ax1 = plt.subplots(figsize=size, dpi=int(theme.get("dpi", 600)))
    bars = ax1.bar(
        x,
        shannon,
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
        pielou,
        marker="o",
        linestyle="None",
        color=str(theme.get("secondary_hex", "#6A8F63")),
        markersize=7,
        label="Equitabilidade (J')",
    )
    ax2.set_ylabel("Pielou (J')")
    ax2.set_ylim(0, 1.1)

    for campaign in campaigns[:-1]:
        split_n = diversity[diversity["nome_campanha"].isin(campaigns[: campaigns.index(campaign) + 1])].shape[0]
        if 0 < split_n < len(x):
            ax1.axvline(x=split_n - 0.5, color="#888888", linestyle="--", linewidth=1.2)

    for bar, value in zip(bars, shannon):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            float(value),
            f"{float(value):.2f}",
            ha="center",
            va="bottom",
            fontsize=int(theme.get("annotation_size", 14)),
        )

    handles_1, labels_1 = ax1.get_legend_handles_labels()
    handles_2, labels_2 = ax2.get_legend_handles_labels()
    place_legend_below_x_axis(
        fig,
        ax1,
        theme,
        handles=handles_1 + handles_2,
        labels=labels_1 + labels_2,
        ncol=2,
    )
    validate_axes_style(ax1, theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=True, extra_bottom=0.06))
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _plot_yearly_metric_panels(
    table: pd.DataFrame,
    metric_col: str,
    ylabel: str,
    output_dir: Path,
    group_slug: str,
    file_prefix: str,
    theme: dict,
    points: list[str],
    campaigns: list[str],
    generated_files: list[str],
    *,
    decimals: int = 2,
) -> None:
    if table.empty or not points or not campaigns:
        return

    season_colors = _season_colors(theme)
    base_size = theme.get("figsize_standard", [11.69, 8.27])
    panel_title_size = int(theme.get("point_label_size", theme.get("font_size_base", 11)))
    for year in sorted({year for year in (_campaign_year(c) for c in campaigns) if year is not None}):
        year_campaigns = [campaign for campaign in campaigns if _campaign_year(campaign) == year]
        if not year_campaigns:
            continue

        pivots: dict[str, pd.DataFrame] = {}
        max_value = 0.0
        for campaign in year_campaigns:
            pivot = (
                table[table["nome_campanha"] == campaign]
                .pivot_table(index="nome_ponto", values=metric_col, aggfunc="sum", fill_value=0)
                .reindex(index=points, fill_value=0)
            )
            pivots[campaign] = pivot
            if metric_col in pivot.columns:
                max_value = max(max_value, float(pivot[metric_col].max()))

        # O grid precisa comportar todas as campanhas do ano; fixar 2x2 descartava
        # silenciosamente a partir da quinta (zip para na sequencia mais curta).
        ncols = 2
        nrows = max(2, int(np.ceil(len(year_campaigns) / ncols)))
        fig, axes = plt.subplots(
            nrows,
            ncols,
            figsize=(float(base_size[0]), float(base_size[1]) * nrows / 2),
            dpi=int(theme.get("dpi", 600)),
            sharey=True,
            squeeze=False,
        )
        for ax, campaign in zip(axes.ravel(), year_campaigns):
            values = pivots[campaign][metric_col].to_numpy(dtype=float) if metric_col in pivots[campaign].columns else np.zeros(len(points))
            x = np.arange(len(points))
            season = _campaign_season(campaign)
            bar_color = season_colors.get(season, str(theme.get("primary_hex", "#002060")))
            bars = ax.bar(
                x,
                values,
                color=bar_color,
                edgecolor="black",
                linewidth=0.6,
                width=0.72,
            )
            for bar, value in zip(bars, values):
                if abs(float(value)) < 1e-12:
                    continue
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    float(value),
                    f"{float(value):.{decimals}f}",
                    ha="center",
                    va="bottom",
                    fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 9))),
            )
            ax.set_xticks(x)
            ax.set_xticklabels(points, rotation=90, ha="center")
            ax.set_ylim(0, max(max_value * 1.15, 1.0))
            apply_theme(ax, theme, xlabel="", ylabel="")
            ax.tick_params(
                axis="x",
                labelsize=max(6, int(theme.get("point_label_size", theme.get("font_size_base", 11))) - 4),
                pad=1,
            )
            ax.set_title(
                _campaign_short_label(campaign),
                loc="left",
                fontsize=panel_title_size,
                fontweight="bold",
                pad=6,
            )

        for ax in axes.ravel()[len(year_campaigns):]:
            ax.axis("off")
        for ax in axes[:, 0]:
            ax.set_ylabel(ylabel)
        for ax in axes[-1, :]:
            ax.set_xlabel("Ponto amostral")

        season_order = ["CH", "SC", "ND"]
        seasons_present = [
            season
            for season in season_order
            if season in {_campaign_season(campaign) for campaign in year_campaigns}
        ]
        handles = [
            Line2D(
                [0],
                [0],
                marker="s",
                color="none",
                markerfacecolor=season_colors[season],
                markeredgecolor="black",
                label=_season_label(season),
            )
            for season in seasons_present
        ]
        fig.legend(handles=handles, loc="upper center", ncol=max(len(handles), 1), frameon=False)
        fig.tight_layout(rect=[0.02, 0.12, 1.0, 0.94])

        out_png = output_dir / f"{file_prefix}_por_ano_{year}_{group_slug}.png"
        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))


def _campaign_index(campaign: str) -> int | None:
    match = re.match(r"^C0*(\d+)", str(campaign).strip(), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _resolve_point_sections(theme: dict, points: list[str]) -> list[dict]:
    """Agrupa pontos em trechos declarados em `ictio_point_sections`."""
    raw = theme.get("ictio_point_sections")
    if not isinstance(raw, list):
        return []

    normalized = [_normalize_point_id(point) for point in points]
    groups: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        members = {_normalize_point_id(p) for p in (item.get("points") or [])}
        indices = [i for i, point in enumerate(normalized) if point in members]
        if label and indices:
            groups.append({"label": label, "indices": indices})
    return groups


def _resolve_campaign_phases(theme: dict, campaigns: list[str]) -> list[dict]:
    """Agrupa campanhas em fases declaradas em `ictio_campaign_phases` (faixas from/to)."""
    raw = theme.get("ictio_campaign_phases")
    if not isinstance(raw, list):
        return []

    numbers = [_campaign_index(campaign) for campaign in campaigns]
    groups: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        start = _campaign_index(item["from"]) if item.get("from") else None
        end = _campaign_index(item["to"]) if item.get("to") else None
        indices = [
            i
            for i, number in enumerate(numbers)
            if number is not None
            and (start is None or number >= start)
            and (end is None or number <= end)
        ]
        if label and indices:
            groups.append({"label": label, "indices": indices})
    return groups


def _draw_group_boxes(
    ax,
    groups: list[dict],
    theme: dict,
    *,
    y_top: float,
    height: float,
) -> None:
    """Desenha caixas rotuladas sob o eixo X, no estilo de tabela usado no relatorio.

    Cada grupo vira um retangulo com o rotulo centralizado; grupos vizinhos
    compartilham a aresta, produzindo as divisorias verticais do relatorio.
    """
    if not groups:
        return

    from matplotlib.patches import Rectangle
    from matplotlib.transforms import blended_transform_factory

    trans = blended_transform_factory(ax.transData, ax.transAxes)
    color = str(theme.get("axis_group_edge_hex", "#808080"))
    text_color = str(theme.get("axis_group_text_hex", "#3F3F3F"))
    fontsize = max(7, int(theme.get("label_size", theme.get("font_size_base", 12))) - 2)
    for group in groups:
        indices = group["indices"]
        x0, x1 = min(indices) - 0.5, max(indices) + 0.5
        ax.add_patch(
            Rectangle(
                (x0, y_top - height), x1 - x0, height,
                transform=trans, facecolor="none", edgecolor=color,
                linewidth=0.8, clip_on=False, zorder=3,
            )
        )
        ax.text((x0 + x1) / 2, y_top - height / 2, group["label"],
                ha="center", va="center", transform=trans,
                fontsize=fontsize, color=text_color, clip_on=False, zorder=4)


def _report_bar_color(theme: dict) -> str:
    return str(theme.get("ictio_report_bar_hex", theme.get("primary_hex", "#8DC63F")))


def _theme_with(theme: dict, **overrides) -> dict:
    """Copia o tema com ajustes locais de uma figura.

    O conjunto do relatorio mistura estilos: as barras nao tem grade nem
    legenda, enquanto a figura de diversidade tem grade e legenda no topo.
    Sobrepor por figura evita fixar essas chaves no config do cliente, onde
    afetariam todos os demais blocos.
    """
    merged = dict(theme)
    merged.update(overrides)
    return merged


def _plot_report_cpue_by_point(
    df_cpue: pd.DataFrame,
    metric_col: str,
    ylabel: str,
    theme: dict,
    points: list[str],
    out_png: Path,
    generated_files: list[str],
) -> None:
    """Figura 12 do relatorio: CPUEn ou CPUEb por ponto, agregando todas as campanhas."""
    totals = (
        df_cpue.groupby("nome_ponto", dropna=False)[metric_col]
        .sum()
        .reindex(points)
        .fillna(0.0)
    )
    size = theme.get("figsize_standard", [11.69, 8.27])
    fig, ax = plt.subplots(figsize=(float(size[0]), float(size[1])), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(points))
    ax.bar(x, totals.to_numpy(dtype=float), color=_report_bar_color(theme), width=0.45)
    ax.set_xticks(x)
    ax.set_xticklabels(points, ha="center")
    fig_theme = _theme_with(theme, grid_y=False, spine_sides=["left", "bottom"])
    apply_theme(ax, fig_theme, xlabel="", ylabel=ylabel, x_tick_rotation=90)
    validate_axes_style(ax, fig_theme)

    _draw_group_boxes(
        ax,
        _resolve_point_sections(theme, points),
        theme,
        y_top=float(theme.get("ictio_report_section_box_top", -0.30)),
        height=float(theme.get("ictio_report_section_box_height", 0.09)),
    )
    fig.tight_layout(rect=[0.0, 0.12, 1.0, 1.0])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


def _plot_report_cpue_by_campaign(
    df_cpue: pd.DataFrame,
    metric_col: str,
    ylabel: str,
    theme: dict,
    campaigns: list[str],
    out_png: Path,
    generated_files: list[str],
) -> None:
    """Figuras 14 e 15 do relatorio: CPUEn/CPUEb por campanha, agregando todos os pontos."""
    totals = (
        df_cpue.groupby("nome_campanha", dropna=False)[metric_col]
        .sum()
        .reindex(campaigns)
        .fillna(0.0)
    )
    size = theme.get("figsize_standard", [11.69, 8.27])
    fig, ax = plt.subplots(figsize=(float(size[0]), float(size[1])), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(campaigns))
    ax.bar(x, totals.to_numpy(dtype=float), color=_report_bar_color(theme), width=0.62)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [str(_campaign_index(campaign) or campaign) for campaign in campaigns],
        ha="center",
    )
    fig_theme = _theme_with(theme, grid_y=False, spine_sides=["left", "bottom"])
    apply_theme(ax, fig_theme, xlabel="", ylabel=ylabel)
    validate_axes_style(ax, fig_theme)

    _draw_group_boxes(
        ax,
        _resolve_campaign_phases(theme, campaigns),
        theme,
        y_top=float(theme.get("ictio_report_phase_box_top", -0.06)),
        height=float(theme.get("ictio_report_phase_box_height", 0.07)),
    )
    fig.tight_layout(rect=[0.0, 0.08, 1.0, 1.0])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


def _point_section_map(theme: dict, points: list[str]) -> dict[str, str]:
    return {
        points[index]: group["label"]
        for group in _resolve_point_sections(theme, points)
        for index in group["indices"]
    }


def _plot_report_richness_by_section(
    df_projeto: pd.DataFrame,
    theme: dict,
    points: list[str],
    output_dir: Path,
    group_slug: str,
    generated_files: list[str],
) -> dict:
    """Figura 11 e Quadro 7 do relatorio: riqueza por trecho e matriz especie x ponto."""
    sections = _resolve_point_sections(theme, points)
    if not sections:
        return {}

    labels = [group["label"] for group in sections]
    section_of = _point_section_map(theme, points)

    df = _drop_effort_only_records(df_projeto).copy()
    for column in ["nome_ponto", "nome_cientifico"]:
        df[column] = df[column].astype(str).str.strip()
    df = df[~df["nome_cientifico"].isin(["", "nan", "None"])].copy()
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    df["trecho"] = df["nome_ponto"].map(section_of)

    resumo = (
        df.dropna(subset=["trecho"])
        .groupby("trecho")
        .agg(
            riqueza=("nome_cientifico", "nunique"),
            abundancia=("contagem", "sum"),
            pontos=("nome_ponto", "nunique"),
        )
        .reindex(labels)
        .fillna(0)
        .reset_index()
    )
    total = float(resumo["riqueza"].sum()) or 1.0
    resumo["riqueza_relativa_pct"] = resumo["riqueza"] / total * 100

    abundancia = (
        df.pivot_table(index="nome_cientifico", columns="nome_ponto", values="contagem",
                       aggfunc="sum", fill_value=0)
        .reindex(columns=points, fill_value=0)
    )
    quadro = abundancia.apply(lambda col: col.map(lambda v: "X" if float(v) > 0 else ""))
    quadro.columns = [f"{section_of.get(point, '-')} | {point}" for point in points]
    quadro["OC"] = (abundancia > 0).sum(axis=1)
    quadro["CO (%)"] = (quadro["OC"] / max(len(points), 1) * 100).round(0)
    quadro["N"] = abundancia.sum(axis=1)
    quadro = quadro.sort_index().reset_index().rename(columns={"nome_cientifico": "Espécie"})

    out_xlsx = output_dir / f"05_tabela_ocorrencia_por_trecho_{group_slug}.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        quadro.to_excel(writer, sheet_name="Especie_x_Ponto", index=False)
        resumo.to_excel(writer, sheet_name="Resumo_trecho", index=False)
    generated_files.append(str(out_xlsx))

    out_png = output_dir / f"05_grafico_riqueza_por_trecho_{group_slug}.png"
    fig, ax = plt.subplots(
        figsize=get_figsize_by_complexity(theme, n_categories=len(labels), prefer_landscape=True),
        dpi=int(theme.get("dpi", 600)),
    )
    x = np.arange(len(labels))
    values = resumo["riqueza_relativa_pct"].to_numpy(dtype=float)
    bars = ax.bar(x, values, color=_report_bar_color(theme), width=0.55)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, float(value), f"{value:.1f}%".replace(".", ","),
                ha="center", va="bottom",
                fontsize=int(theme.get("annotation_size", theme.get("font_size_base", 12))))
    ax.set_xticks(x)
    ax.set_xticklabels(labels, ha="center")
    fig_theme = _theme_with(theme, grid_y=False, spine_sides=["left", "bottom"])
    apply_theme(ax, fig_theme, xlabel="Trecho", ylabel="Frequência relativa da riqueza (%)")
    validate_axes_style(ax, fig_theme)
    fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=False, extra_bottom=0.0))
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {
        "trechos": {
            str(row["trecho"]): {
                "riqueza": int(row["riqueza"]),
                "abundancia": float(row["abundancia"]),
                "riqueza_relativa_pct": round(float(row["riqueza_relativa_pct"]), 1),
            }
            for _, row in resumo.iterrows()
        },
        "taxa_no_quadro": int(len(quadro)),
    }


def _report_occurrence_by_campaign(
    df_projeto: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    group_slug: str,
    generated_files: list[str],
) -> dict:
    """Quadro 8 do relatorio: matriz especie x campanha com ocorrencia (X).

    Espelha o modelo entregue: colunas ordinais por campanha, OC (numero de
    campanhas em que a especie ocorreu), CO (%) e N (abundancia da especie),
    com as linhas de Abundancia e Riqueza no rodape. Considera todos os metodos
    de captura, que e a base usada no relatorio.
    """
    df = _drop_effort_only_records(df_projeto).copy()
    for column in ["nome_campanha", "nome_cientifico"]:
        df[column] = df[column].astype(str).str.strip()
    df = df[~df["nome_cientifico"].isin(["", "nan", "None"])].copy()
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    if df.empty:
        return {}

    campaigns = sorted(df["nome_campanha"].unique())
    ordinals = [
        f"{_campaign_index(campaign) or index + 1}º"
        for index, campaign in enumerate(campaigns)
    ]

    abundancia = (
        df.pivot_table(index="nome_cientifico", columns="nome_campanha", values="contagem",
                       aggfunc="sum", fill_value=0)
        .reindex(columns=campaigns, fill_value=0)
        .sort_index()
    )
    quadro = abundancia.apply(lambda col: col.map(lambda v: "X" if float(v) > 0 else ""))
    quadro.columns = ordinals
    quadro.insert(0, "Espécie", quadro.index)
    quadro["OC"] = (abundancia > 0).sum(axis=1).to_numpy()
    quadro["CO (%)"] = (quadro["OC"] / max(len(campaigns), 1) * 100).round(0)
    quadro["N"] = abundancia.sum(axis=1).to_numpy()
    quadro = quadro.reset_index(drop=True)

    abundancia_campanha = abundancia.sum(axis=0)
    riqueza_campanha = (abundancia > 0).sum(axis=0)
    rodape = pd.DataFrame(
        [
            ["Abundância", *abundancia_campanha.to_list(), "", "", int(abundancia.to_numpy().sum())],
            ["Riqueza", *riqueza_campanha.to_list(), "", "", int(abundancia.shape[0])],
        ],
        columns=quadro.columns,
    )
    quadro = pd.concat([quadro, rodape], ignore_index=True)

    resumo = pd.DataFrame(
        {
            "ordem": ordinals,
            "campanha": campaigns,
            "abundancia": abundancia_campanha.to_numpy(),
            "riqueza": riqueza_campanha.to_numpy(),
        }
    )
    partes = resumo["campanha"].str.split("-")
    resumo["ano"] = partes.str[1]
    resumo["estacao"] = partes.str[3].map(SEASON_LABELS).fillna("")

    out_xlsx = output_dir / f"05_tabela_ocorrencia_por_campanha_{group_slug}.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        quadro.to_excel(writer, sheet_name="Especie_x_Campanha", index=False)
        resumo.to_excel(writer, sheet_name="Resumo_campanha", index=False)
    generated_files.append(str(out_xlsx))

    return {
        "campanhas": int(len(campaigns)),
        "taxa_no_quadro": int(abundancia.shape[0]),
        "abundancia_total": int(abundancia.to_numpy().sum()),
        "base": "todos os metodos de captura",
    }


def _plot_report_diversity_by_year(
    df_projeto: pd.DataFrame,
    theme: dict,
    output_dir: Path,
    group_slug: str,
    generated_files: list[str],
) -> dict:
    """Figura 16 do relatorio: Shannon (H') e Pielou (J) agregados por ano."""
    df_div = _cpuen_por_especie_ponto(df_projeto)
    if df_div.empty:
        return {}

    df_div = df_div.copy()
    df_div["ano"] = df_div["nome_campanha"].map(_campaign_year)
    df_div = df_div[df_div["ano"].notna()].copy()
    if df_div.empty:
        return {}

    rows = []
    for ano, frame in df_div.groupby("ano"):
        vector = frame.groupby("nome_cientifico")["cpuen"].sum().to_numpy(dtype=float)
        rows.append(
            {
                "ano": int(ano),
                "riqueza": int((vector > 0).sum()),
                "Shannon_H": _shannon(vector),
                "Pielou_J": _pielou(vector),
            }
        )
    table = pd.DataFrame(rows).sort_values("ano").reset_index(drop=True)

    out_xlsx = output_dir / f"10_df_diversidade_por_ano_{group_slug}.xlsx"
    table.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    # A Figura 16 e a unica do conjunto com grade e legenda no topo; as demais
    # sao barras sem grade. Sobrepoe o tema so nesta figura em vez de fixar as
    # chaves no config do cliente.
    fig_theme = _theme_with(
        theme,
        grid_y=True,
        spine_sides=["left", "bottom"],
        legend_below_x_axis=False,
        legend_loc="upper center",
        legend_figure_loc="upper center",
    )

    size = theme.get("figsize_standard", [11.69, 8.27])
    fig, ax = plt.subplots(figsize=(float(size[0]), float(size[1])), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(table))
    series = [
        ("Shannon_H", str(theme.get("ictio_report_line_hex", "#00A651")), "Shannon_H"),
        ("Pielou_J", _report_bar_color(theme), "Equitability_J"),
    ]
    for column, color, label in series:
        ax.plot(x, table[column].to_numpy(dtype=float), color=color,
                linewidth=float(theme.get("ictio_report_linewidth", 2.4)), label=label)

    ax.set_xticks(x)
    ax.set_xticklabels([str(int(ano)) for ano in table["ano"]], ha="center")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    apply_theme(ax, fig_theme, xlabel="Ano", ylabel="Diversidade (Shannon H')", x_tick_rotation=90)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.10),
        ncol=2,
        frameon=False,
        fontsize=int(theme.get("legend_size", theme.get("font_size_base", 12))),
    )
    validate_axes_style(ax, fig_theme)

    out_png = output_dir / f"10_grafico_diversidade_por_ano_{group_slug}.png"
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"anos": int(len(table)), "base_quantitativa": "CPUEn (ind/100m2)"}


def _plot_report_cpue_species(
    table: pd.DataFrame,
    campaigns: list[str],
    xlabel: str,
    theme: dict,
    out_png: Path,
    generated_files: list[str],
) -> None:
    """Figuras 9 e 10 do relatorio: CPUE por especie em barras horizontais.

    Agrega todas as campanhas numa barra por especie e ordena do maior para o
    menor, com o maior no topo.
    """
    values = (
        table.set_index("nome_cientifico")[[c for c in campaigns if c in table.columns]]
        .sum(axis=1)
        .sort_values(ascending=False)
    )
    limit = int(theme.get("ictio_report_species_limit", 20))
    if limit > 0:
        values = values.head(limit)
    values = values.sort_values(ascending=True)  # barh desenha de baixo para cima

    fig_theme = _theme_with(theme, grid_y=False, spine_sides=["left", "bottom"])
    size = theme.get("figsize_standard", [11.69, 8.27])
    height = max(float(size[1]), 0.42 * max(len(values), 8))
    fig, ax = plt.subplots(figsize=(float(size[0]), height), dpi=int(theme.get("dpi", 600)))
    y = np.arange(len(values))
    ax.barh(y, values.to_numpy(dtype=float), height=0.62, color=_report_bar_color(theme))
    ax.set_yticks(y)
    ax.set_yticklabels(values.index.tolist(), fontstyle="italic")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    apply_theme(ax, fig_theme, xlabel=xlabel, ylabel="")
    ax.grid(axis="x", visible=False)
    validate_axes_style(ax, fig_theme)
    fig.tight_layout()
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


REPORT_CATEGORICAL_PALETTE = [
    "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5", "#4472C4",
    "#70AD47", "#264478", "#9E480E", "#636363", "#997300",
    "#255E91", "#43682B", "#698ED0", "#F1975A", "#B7B7B7",
    "#FFCD33", "#7CAFDD", "#8ED973", "#C55A11", "#7B4EA3",
]


def _resolve_year_phases(theme: dict, years: list[int], campaigns: list[str]) -> list[dict]:
    """Traduz as fases declaradas por campanha para o eixo de anos."""
    phases = _resolve_campaign_phases(theme, campaigns)
    if not phases:
        return []

    year_of = {index: _campaign_year(campaign) for index, campaign in enumerate(campaigns)}
    groups: list[dict] = []
    for phase in phases:
        phase_years = {year_of[i] for i in phase["indices"] if year_of.get(i) is not None}
        indices = [i for i, year in enumerate(years) if year in phase_years]
        if indices:
            groups.append({"label": phase["label"], "indices": indices})
    return groups


def _plot_report_richness_stacked_by_year(
    df_projeto: pd.DataFrame,
    theme: dict,
    taxon_col: str,
    out_png: Path,
    generated_files: list[str],
    ylabel: str = "Número de espécies",
) -> dict:
    """Composicao da riqueza por ano, empilhada a 100%, agrupada por fase.

    Cada barra e um ano e cada fatia a participacao de um taxon na riqueza
    daquele ano (numero de especies distintas).
    """
    df = _drop_effort_only_records(df_projeto).copy()
    df["nome_cientifico"] = df["nome_cientifico"].astype(str).str.strip()
    df = df[~df["nome_cientifico"].isin(["", "nan", "None"])].copy()
    df[taxon_col] = df[taxon_col].astype(str).str.strip()
    df = df[~df[taxon_col].isin(["", "nan", "None"])].copy()
    df["ano"] = df["nome_campanha"].map(_campaign_year)
    df = df[df["ano"].notna()].copy()
    if df.empty:
        return {}

    counts = (
        df.groupby(["ano", taxon_col])["nome_cientifico"].nunique()
        .unstack(taxon_col).fillna(0.0).sort_index()
    )
    counts = counts.reindex(columns=sorted(counts.columns))
    percent = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0) * 100
    years = [int(year) for year in percent.index]
    taxa = list(percent.columns)

    palette = list(theme.get("ictio_report_categorical_palette", REPORT_CATEGORICAL_PALETTE))
    on_top = len(taxa) > 6
    # Nos dois casos a legenda e ancorada pelo topo e cresce para baixo, para
    # nao invadir o rotulo do eixo nem as caixas de fase.
    fig_theme = _theme_with(
        theme, grid_y=True, spine_sides=["left", "bottom"],
        legend_below_x_axis=not on_top,
        legend_loc="upper center",
        legend_figure_loc="upper center",
    )

    size = theme.get("figsize_standard", [11.69, 8.27])
    fig, ax = plt.subplots(figsize=(float(size[0]), float(size[1])), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(years))
    bottom = np.zeros(len(years), dtype=float)
    for index, taxon in enumerate(taxa):
        values = percent[taxon].to_numpy(dtype=float)
        ax.bar(x, values, bottom=bottom, width=0.62,
               color=palette[index % len(palette)], label=str(taxon))
        bottom += values

    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.set_xticks(x)
    ax.set_xticklabels([str(year) for year in years], ha="center")
    apply_theme(ax, fig_theme, xlabel="Fase/Ano", ylabel=ylabel, x_tick_rotation=90)

    box_top = float(theme.get("ictio_report_year_box_top", -0.20))
    box_height = float(theme.get("ictio_report_year_box_height", 0.07))
    _draw_group_boxes(
        ax, _resolve_year_phases(theme, years, sorted(
            df["nome_campanha"].dropna().astype(str).unique().tolist(), key=_campanha_sort_key)),
        theme, y_top=box_top, height=box_height,
    )
    label_y = box_top - box_height - 0.05
    ax.xaxis.set_label_coords(0.5, label_y)

    ncol = min(len(taxa), int(theme.get("ictio_report_legend_ncol", 5)))
    legend_fontsize = int(theme.get("legend_size", theme.get("font_size_base", 11)))
    if on_top:
        # Muitas categorias: a legenda vai para uma faixa reservada acima do
        # eixo, senao invade a area de plotagem.
        nrows = int(np.ceil(len(taxa) / ncol))
        fig.legend(*ax.get_legend_handles_labels(), loc="upper center",
                   bbox_to_anchor=(0.5, 0.995), ncol=ncol, frameon=False, fontsize=legend_fontsize)
        top = max(0.62, 1.0 - 0.05 * nrows)
    else:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, label_y - 0.06),
                  ncol=ncol, frameon=False, fontsize=legend_fontsize)
        top = 1.0
    validate_axes_style(ax, fig_theme)
    fig.tight_layout(rect=[0.0, 0.10, 1.0, top])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))

    return {"anos": len(years), "categorias": len(taxa)}


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

    df_tmp = _drop_effort_only_records(df_projeto).copy()
    df_tmp["nome_campanha"] = df_tmp["nome_campanha"].astype(str).str.strip()
    df_tmp["nome_cientifico"] = df_tmp["nome_cientifico"].astype(str).str.strip()
    df_tmp = df_tmp[
        df_tmp["nome_cientifico"].notna()
        & ~df_tmp["nome_cientifico"].astype(str).str.strip().isin(["", "nan", "None"])
    ].copy()

    ocorrencia = (
        df_tmp.groupby("nome_cientifico")["nome_campanha"]
        .apply(lambda s: sorted({_camp_short(x) for x in s.dropna().unique().tolist()}, key=_campanha_sort_key))
        .reset_index(name="ocorr_lista")
    )
    ocorrencia["Ocorrencia (Campanhas)"] = ocorrencia["ocorr_lista"].apply(lambda lst: "; ".join(lst))
    ocorrencia = ocorrencia.drop(columns=["ocorr_lista"])

    campanhas = (
        df_tmp.groupby("nome_cientifico")["nome_campanha"]
        .nunique()
        .reset_index(name="Numero de Campanhas")
    )
    if "nome_ponto" in df_tmp.columns:
        pontos = (
            df_tmp.groupby("nome_cientifico")["nome_ponto"]
            .apply(lambda s: _ordenar_pontos(sorted({str(x).strip() for x in s.dropna().tolist() if str(x).strip()})))
            .reset_index(name="pontos_lista")
        )
        pontos["Ocorrencia (Pontos)"] = pontos["pontos_lista"].apply(lambda lst: "; ".join(lst))
        pontos["Numero de Pontos"] = pontos["pontos_lista"].apply(len)
        pontos = pontos.drop(columns=["pontos_lista"])
    else:
        pontos = pd.DataFrame(columns=["nome_cientifico", "Ocorrencia (Pontos)", "Numero de Pontos"])

    if "contagem" in df_tmp.columns:
        abundancia = (
            df_tmp.assign(contagem=pd.to_numeric(df_tmp["contagem"], errors="coerce").fillna(0))
            .groupby("nome_cientifico", as_index=False)["contagem"]
            .sum()
            .rename(columns={"contagem": "Abundancia Total"})
        )
    else:
        abundancia = pd.DataFrame(columns=["nome_cientifico", "Abundancia Total"])

    attribute_specs = [
        ("id_especie", "ID Especie"),
        ("reino", "Reino"),
        ("filo", "Filo"),
        ("classe", "Classe"),
        ("ordem", "Ordem"),
        ("familia", "Familia"),
        ("genero", "Genero"),
        ("autor_e_ano", "Autor e Ano"),
        ("nome_popular", "Nome Popular"),
        ("origem", "Origem"),
        ("status_estadual", "Status Ameaça Estadual"),
        ("status_ameaca_nacional", "Status Ameaça Nacional"),
        ("status_ameaca_global", "Status Ameaça Global"),
        ("status_copam", "Status COPAM"),
        ("cites", "CITES"),
        ("endemismo", "Endemismo"),
        ("distribuicao", "Distribuição"),
        ("habito_alimentar", "Habito Alimentar"),
        ("guilda_alimentar", "Guilda Alimentar"),
        ("estrategia_reprodutiva", "Estrategia Reprodutiva"),
        ("migratorio", "Migratorio"),
        ("raridade", "Raridade"),
        ("sensibilidade_ambiental", "Sensibilidade Ambiental"),
        ("dependencia_florestal", "Dependencia Florestal"),
        ("cinegetica", "Cinegetica"),
        ("valor_economico", "Valor Economico"),
        ("xerimbabo", "Xerimbabo"),
        ("bmwp_score", "BMWP Score"),
        ("observacoes", "Observacoes"),
    ]
    agg_dict: dict = {}
    for source_col, _output_col in attribute_specs:
        if source_col in df_tmp.columns:
            agg_dict[source_col] = (source_col, _mode_or_first)

    if agg_dict:
        tabela = df_tmp.groupby("nome_cientifico", as_index=False).agg(**agg_dict)
    else:
        tabela = df_tmp[["nome_cientifico"]].drop_duplicates().reset_index(drop=True)

    tabela = tabela.merge(ocorrencia, on="nome_cientifico", how="left")
    tabela = tabela.merge(campanhas, on="nome_cientifico", how="left")
    tabela = tabela.merge(pontos, on="nome_cientifico", how="left")
    tabela = tabela.merge(abundancia, on="nome_cientifico", how="left")

    tabela = tabela.rename(
        columns={
            **{source_col: output_col for source_col, output_col in attribute_specs},
            "nome_cientifico": "Nome Cientifico",
        }
    )

    desired = [
        "ID Especie",
        "Reino",
        "Filo",
        "Classe",
        "Ordem",
        "Familia",
        "Genero",
        "Nome Cientifico",
        "Autor e Ano",
        "Nome Popular",
        "Origem",
        "Status Ameaça Estadual",
        "Status Ameaça Nacional",
        "Status Ameaça Global",
        "Status COPAM",
        "CITES",
        "Endemismo",
        "Distribuição",
        "Habito Alimentar",
        "Guilda Alimentar",
        "Estrategia Reprodutiva",
        "Migratorio",
        "Raridade",
        "Sensibilidade Ambiental",
        "Dependencia Florestal",
        "Cinegetica",
        "Valor Economico",
        "Xerimbabo",
        "BMWP Score",
        "Observacoes",
        "Ocorrencia (Campanhas)",
        "Numero de Campanhas",
        "Ocorrencia (Pontos)",
        "Numero de Pontos",
        "Abundancia Total",
    ]
    existing = [c for c in desired if c in tabela.columns]
    tabela = tabela[existing]

    sort_cols = [c for c in ["Ordem", "Familia", "Nome Cientifico"] if c in tabela.columns]
    if sort_cols:
        tabela = tabela.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    text_cols = [col for col in tabela.columns if col not in {"Numero de Campanhas", "Numero de Pontos", "Abundancia Total"}]
    for col in text_cols:
        tabela[col] = tabela[col].replace({None: "N.A.", "": "N.A.", "nan": "N.A.", "None": "N.A."}).fillna("N.A.")
    for col in ["Numero de Campanhas", "Numero de Pontos", "Abundancia Total"]:
        if col in tabela.columns:
            tabela[col] = pd.to_numeric(tabela[col], errors="coerce").fillna(0).astype(int)

    tabela.to_excel(out_xlsx, index=False, engine="openpyxl")
    generated_files.append(str(out_xlsx))

    return {"taxa_total": int(len(tabela)), "colunas": int(len(tabela.columns))}


def _export_occurrence_summary_when_needed(**kwargs) -> dict:
    records = kwargs.get("records")
    campaign_col = str(kwargs.get("campaign_col", "nome_campanha"))
    campaign_count = (
        int(records[campaign_col].dropna().astype(str).str.strip().nunique())
        if isinstance(records, pd.DataFrame) and campaign_col in records.columns
        else 0
    )
    if campaign_count <= 2:
        return {
            "status": "not_required",
            "reason": "A tabela completa de distribuicao e suficiente para ate duas campanhas.",
        }
    return export_occurrence_summary(**kwargs)


def _run_block_4(
    df_projeto: pd.DataFrame,
    group: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
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

    layout_df = df_projeto.copy()
    df_tmp = _drop_effort_only_records(df_projeto).copy()
    for c in ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem"]:
        df_tmp[c] = df_tmp[c].astype(str).str.strip()
    for c in ["nome_campanha", "nome_ponto"]:
        layout_df[c] = layout_df[c].astype(str).str.strip()
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

    layout_df["campanha_layout"] = layout_df["nome_campanha"].map(_rotulo_campanha)
    campaigns = sorted(layout_df["campanha_layout"].dropna().unique().tolist(), key=_campanha_sort_key)
    points_by_campaign = {
        camp: _ordenar_pontos(
            layout_df.loc[layout_df["campanha_layout"] == camp, "nome_ponto"].dropna().unique().tolist()
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
    occurrence_summary = _export_occurrence_summary_when_needed(
        records=df_tmp,
        sampling_units=layout_df[["nome_campanha", "nome_ponto"]].drop_duplicates(),
        taxon_col="nome_cientifico",
        campaign_col="nome_campanha",
        point_col="nome_ponto",
        abundance_col="contagem",
        metadata_map={
            "ordem": "Ordem",
            "familia": "Família",
            "nome_popular": "Nome popular",
        },
        group_slug=group_slug,
        output_dir=output_dir,
        theme=theme,
        generated_files=generated_files,
    )
    return {
        "rows_input": int(len(df_projeto)),
        "rows_valid": int(len(df_tmp)),
        "taxa_total": int(len(tabela_final)),
        "pontos_por_campanha": {camp: len(points) for camp, points in points_by_campaign.items()},
        "sintese_ocorrencia": occurrence_summary,
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
    if campaigns and points:
        full_index = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"])
        richness = richness.set_index(["nome_campanha", "nome_ponto"]).reindex(full_index, fill_value=0).reset_index()

    richness.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if not campaigns or not points:
        return {"campaigns": campaigns, "points": points}

    if len(campaigns) <= 2:
        _plot_grouped_campaign_bars(
            table=richness,
            value_col="riqueza",
            ylabel="Riqueza taxonomica",
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=0,
        )
    else:
        _small_multiple_metric(
            table=richness,
            value_col="riqueza",
            ylabel="Riqueza taxonomica",
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=1,
        )
    generated_files.append(str(out_png))

    details: dict = {"campaigns": campaigns, "points": points}
    if bool(theme.get("ictio_report_layout", False)):
        details["por_trecho"] = _plot_report_richness_by_section(
            df_projeto=df_projeto,
            theme=theme,
            points=points,
            output_dir=output_dir,
            group_slug=group_slug,
            generated_files=generated_files,
        )
        details["por_campanha"] = _report_occurrence_by_campaign(
            df_projeto=df_projeto,
            theme=theme,
            output_dir=output_dir,
            group_slug=group_slug,
            generated_files=generated_files,
        )
        df_trecho = df_projeto.copy()
        df_trecho["trecho"] = (
            df_trecho["nome_ponto"].astype(str).str.strip().map(_point_section_map(theme, points))
        )
        details["composicao_trecho_por_ano"] = _plot_report_richness_stacked_by_year(
            df_projeto=df_trecho,
            theme=theme,
            taxon_col="trecho",
            out_png=output_dir / f"05_grafico_composicao_trecho_por_ano_{group_slug}.png",
            generated_files=generated_files,
            ylabel="Percentual de espécies",
        )
    return details


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
    if campaigns and points:
        full_index = pd.MultiIndex.from_product([campaigns, points], names=["nome_campanha", "nome_ponto"])
        abundancia = (
            abundancia.set_index(["nome_campanha", "nome_ponto"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )

    abundancia.to_excel(out_df, index=False, engine="openpyxl")
    generated_files.append(str(out_df))

    if abundancia.empty or not campaigns or not points:
        return {"campaigns": campaigns, "points": points}

    if len(campaigns) <= 2:
        _plot_grouped_campaign_bars(
            table=abundancia,
            value_col="abundancia_total",
            ylabel="Abundância total (nº de indivíduos)",
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=0,
        )
    else:
        _small_multiple_metric(
            table=abundancia,
            value_col="abundancia_total",
            ylabel="Abundância total (nº de indivíduos)",
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=1,
        )
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
    df_tmp = _drop_effort_only_records(df_projeto).copy()
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
    apply_theme(ax, theme, xlabel=tax_label, ylabel="Número de espécies", x_tick_rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
        label.set_rotation_mode("anchor")
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
        wedgeprops={"width": 0.45, "edgecolor": str(theme.get("background_color", "white")), "linewidth": 1.2},
        autopct=_autopct_visible,
        pctdistance=0.78,
        textprops={"fontsize": int(theme.get("font_size_base", 10))},
    )
    # Improve label contrast on dark/light slices.
    for w, t in zip(wedges, ax.texts[-len(wedges):]):
        txt = t.get_text().strip()
        if not txt:
            continue
        r, g, b = mcolors.to_rgb(w.get_facecolor())
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        t.set_color("white" if luminance < 0.50 else "black")
        t.set_fontweight("bold")
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
        tax_label="Família",
        theme=theme,
        output_dir=output_dir,
        generated_files=generated_files,
    )
    details = {"ordens": ordem["categorias"], "familias": familia["categorias"]}
    if bool(theme.get("ictio_report_layout", False)):
        for tax_col, slug in [("ordem", "ordem"), ("familia", "familia")]:
            details[f"composicao_por_ano_{slug}"] = _plot_report_richness_stacked_by_year(
                df_projeto=df_projeto,
                theme=theme,
                taxon_col=tax_col,
                out_png=output_dir / f"04_grafico_composicao_{slug}_por_ano_{group_slug}.png",
                generated_files=generated_files,
            )
    return details


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
    if "biomassa_total_analitica" in df_quant.columns:
        df_quant["biomassa_total_analitica"] = pd.to_numeric(
            df_quant["biomassa_total_analitica"], errors="coerce"
        ).fillna(0)

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

    biomass_col, biomass_formula = _resolve_line_biomass(df_quant, theme)
    df_totals = (
        df_quant.groupby(["nome_campanha", "nome_ponto"], dropna=False)
        .agg(
            abundancia_total=("contagem", "sum"),
            biomassa_total=(biomass_col, "sum"),
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

    if bool(theme.get("ictio_report_layout", False)):
        _plot_report_cpue_by_point(
            df_cpue=df_cpue,
            metric_col="cpuen",
            ylabel="CPUE n (ind./100 m²)",
            theme=theme,
            points=points,
            out_png=output_dir / f"06_grafico_cpuen_por_ponto_{group_slug}.png",
            generated_files=generated_files,
        )
        _plot_report_cpue_by_point(
            df_cpue=df_cpue,
            metric_col="cpueb",
            ylabel="CPUE b (g./100 m²)",
            theme=theme,
            points=points,
            out_png=output_dir / f"07_grafico_cpueb_por_ponto_{group_slug}.png",
            generated_files=generated_files,
        )
        _plot_report_cpue_by_campaign(
            df_cpue=df_cpue,
            metric_col="cpuen",
            ylabel="CPUE n (ind./100 m²)",
            theme=theme,
            campaigns=campaigns,
            out_png=output_dir / f"06_grafico_cpuen_por_campanha_{group_slug}.png",
            generated_files=generated_files,
        )
        _plot_report_cpue_by_campaign(
            df_cpue=df_cpue,
            metric_col="cpueb",
            ylabel="CPUE b (g./100 m²)",
            theme=theme,
            campaigns=campaigns,
            out_png=output_dir / f"07_grafico_cpueb_por_campanha_{group_slug}.png",
            generated_files=generated_files,
        )
    elif len(campaigns) <= 2:
        _plot_grouped_campaign_bars(
            table=df_cpue,
            value_col="cpuen",
            ylabel="CPUEn (ind/100m2)",
            out_png=out_png_cpuen,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=2,
        )
        _plot_grouped_campaign_bars(
            table=df_cpue,
            value_col="cpueb",
            ylabel="CPUEb (g/100m2)",
            out_png=out_png_cpueb,
            theme=theme,
            points=points,
            campaigns=campaigns,
            decimals=2,
        )
        generated_files.extend([str(out_png_cpuen), str(out_png_cpueb)])
    else:
        _plot_yearly_metric_panels(
            table=df_cpue,
            metric_col="cpuen",
            ylabel="CPUEn (ind/100m2)",
            output_dir=output_dir,
            group_slug=group_slug,
            file_prefix="06_grafico_cpuen",
            theme=theme,
            points=points,
            campaigns=campaigns,
            generated_files=generated_files,
            decimals=2,
        )
        _plot_yearly_metric_panels(
            table=df_cpue,
            metric_col="cpueb",
            ylabel="CPUEb (g/100m2)",
            output_dir=output_dir,
            group_slug=group_slug,
            file_prefix="07_grafico_cpueb",
            theme=theme,
            points=points,
            campaigns=campaigns,
            generated_files=generated_files,
            decimals=2,
        )

    return {
        "campaigns": campaigns,
        "points": points,
        "cpue_formula": "(sum_abundance_or_biomass / sum_distinct_effort_by_campaign_point) * 100",
        "biomass_formula": biomass_formula,
    }


def _run_block_9(df_projeto: pd.DataFrame, group: str, theme: dict, output_dir: Path, generated_files: list[str]) -> dict:
    group_slug = _safe_group_name(group)

    out_df_cpuen = output_dir / f"08_df_cpuen_por_especie_{group_slug}.xlsx"
    out_df_cpueb = output_dir / f"09_df_cpueb_por_especie_{group_slug}.xlsx"
    out_df_cpuen_point = output_dir / f"08B_df_cpuen_por_especie_ponto_{group_slug}.xlsx"
    out_df_cpueb_point = output_dir / f"09B_df_cpueb_por_especie_ponto_{group_slug}.xlsx"
    out_png_cpuen = output_dir / f"08_grafico_cpuen_por_especie_{group_slug}.png"
    out_png_cpuen_point = output_dir / f"08B_grafico_cpuen_por_especie_ponto_{group_slug}.png"
    out_png_cpueb = output_dir / f"09_grafico_cpueb_por_especie_{group_slug}.png"
    out_png_cpueb_point = output_dir / f"09B_grafico_cpueb_por_especie_ponto_{group_slug}.png"

    base_cols = ["nome_cientifico"]
    if df_projeto.empty:
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen_point, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb_point, index=False, engine="openpyxl")
        generated_files.extend([str(out_df_cpuen), str(out_df_cpueb), str(out_df_cpuen_point), str(out_df_cpueb_point)])
        return {"campaigns": [], "species": 0, "warning": "dataset vazio para os filtros informados"}

    required = ["nome_campanha", "nome_ponto", "nome_cientifico", "tipo_amostragem", "esforco", "contagem", "biomassa"]
    missing = [c for c in required if c not in df_projeto.columns]
    if missing:
        raise RuntimeError(f"[ERRO] Colunas obrigatorias ausentes no Bloco 9 ICTIO: {', '.join(missing)}")

    df_quant = _drop_effort_only_records(df_projeto).copy()
    tipo_norm = df_quant["tipo_amostragem"].astype(str).map(_normalizar_tipo_amostragem)
    df_quant = df_quant[tipo_norm == "quantitativo"].copy()

    df_quant["esforco"] = pd.to_numeric(df_quant["esforco"], errors="coerce")
    df_quant["contagem"] = pd.to_numeric(df_quant["contagem"], errors="coerce").fillna(0)
    df_quant["biomassa"] = pd.to_numeric(df_quant["biomassa"], errors="coerce").fillna(0)
    if "biomassa_total_analitica" in df_quant.columns:
        df_quant["biomassa_total_analitica"] = pd.to_numeric(
            df_quant["biomassa_total_analitica"], errors="coerce"
        ).fillna(0)
    df_quant = df_quant[df_quant["esforco"].notna() & (df_quant["esforco"] > 0)].copy()

    if df_quant.empty:
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpuen_point, index=False, engine="openpyxl")
        pd.DataFrame(columns=base_cols).to_excel(out_df_cpueb_point, index=False, engine="openpyxl")
        generated_files.extend([str(out_df_cpuen), str(out_df_cpueb), str(out_df_cpuen_point), str(out_df_cpueb_point)])
        return {"campaigns": [], "species": 0, "warning": "sem dados quantitativos validos para CPUE por especie"}

    biomass_col, biomass_formula = _resolve_line_biomass(df_quant, theme)
    df_species_point = (
        df_quant.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], dropna=False)
        .agg(
            contagem=("contagem", "sum"),
            biomassa=(biomass_col, "sum"),
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
    df_species_point["nome_ponto"] = df_species_point["nome_ponto"].astype(str).str.strip()
    df_species_point["nome_cientifico"] = df_species_point["nome_cientifico"].astype(str).str.strip()

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
    points = _ordenar_pontos(df_species_point["nome_ponto"].dropna().astype(str).str.strip().unique().tolist())

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
    cpuen_point = (
        df_species_point.pivot_table(
            index="nome_cientifico",
            columns="nome_ponto",
            values="cpuen",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=points, fill_value=0)
        .fillna(0)
    )
    cpueb_point = (
        df_species_point.pivot_table(
            index="nome_cientifico",
            columns="nome_ponto",
            values="cpueb",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=points, fill_value=0)
        .fillna(0)
    )

    order_species = cpuen_sp.sum(axis=1).sort_values(ascending=True).index.tolist()
    cpuen_sp = cpuen_sp.loc[order_species].reset_index()
    cpueb_sp = cpueb_sp.loc[order_species].reset_index()
    cpuen_point = cpuen_point.reindex(index=order_species).reset_index()
    cpueb_point = cpueb_point.reindex(index=order_species).reset_index()

    cpuen_sp.to_excel(out_df_cpuen, index=False, engine="openpyxl")
    cpueb_sp.to_excel(out_df_cpueb, index=False, engine="openpyxl")
    cpuen_point.to_excel(out_df_cpuen_point, index=False, engine="openpyxl")
    cpueb_point.to_excel(out_df_cpueb_point, index=False, engine="openpyxl")
    generated_files.extend([str(out_df_cpuen), str(out_df_cpueb), str(out_df_cpuen_point), str(out_df_cpueb_point)])

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
            ylabel="Espécie",
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

        if len(campaigns) > 1:
            place_legend_below_x_axis(
                fig,
                ax,
                theme,
                ncol=min(len(campaigns), int(theme.get("legend_max_cols", 2))),
            )
        validate_axes_style(ax, theme)
        fig.tight_layout(rect=get_tight_layout_rect(theme, has_legend=len(campaigns) > 1, extra_bottom=0.0))
        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))

    def _plot_heatmap(
        df_plot: pd.DataFrame,
        metric_label: str,
        out_png: Path,
        *,
        columns: list[str],
        xlabel: str,
        xlabels: list[str] | None = None,
        x_rotation: int = 0,
    ) -> None:
        labels = df_plot["nome_cientifico"].tolist()
        values = df_plot[columns].to_numpy(dtype=float)
        vmax = float(np.nanmax(values)) if values.size else 0.0

        configured_size = theme.get("figsize_heatmap", theme.get("figsize_standard", [11.69, 7.2]))
        fig_w = float(configured_size[0])
        fig_h = max(float(configured_size[1]), 0.58 * max(len(labels), 10))
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=int(theme.get("dpi", 600)))
        im = ax.imshow(values, aspect="auto", cmap=_theme_gradient_cmap(theme), vmin=0, vmax=vmax if vmax > 0 else 1)

        ax.set_xticks(np.arange(len(columns)))
        ax.set_xticklabels(xlabels or columns, rotation=x_rotation, ha="center")
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels, fontstyle="italic")
        apply_theme(ax, theme, xlabel=xlabel, ylabel="Espécie", x_tick_rotation=None)
        ax.tick_params(
            axis="both",
            labelsize=int(theme.get("heatmap_tick_size", theme.get("font_size_base", 11))),
        )
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
                    fontsize=int(theme.get("heatmap_annotation_size", theme.get("annotation_size", 11))),
                    color=_annotation_color_for_value(float(v), vmax),
                )

        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cbar.set_label(metric_label)
        validate_axes_style(ax, theme)
        fig.tight_layout()
        fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close(fig)
        generated_files.append(str(out_png))

    if bool(theme.get("ictio_report_layout", False)):
        _plot_report_cpue_species(
            table=cpuen_sp, campaigns=campaigns, xlabel="CPUE n", theme=theme,
            out_png=out_png_cpuen, generated_files=generated_files,
        )
        _plot_report_cpue_species(
            table=cpueb_sp, campaigns=campaigns, xlabel="CPUE b", theme=theme,
            out_png=out_png_cpueb, generated_files=generated_files,
        )
    elif len(campaigns) > 3:
        _plot_heatmap(
            cpuen_sp,
            "CPUEn (ind/100m2)",
            out_png_cpuen,
            columns=campaigns,
            xlabel="Campanha",
            xlabels=[_campaign_short_label(c) for c in campaigns],
        )
        _plot_heatmap(
            cpueb_sp,
            "CPUEb (g/100m2)",
            out_png_cpueb,
            columns=campaigns,
            xlabel="Campanha",
            xlabels=[_campaign_short_label(c) for c in campaigns],
        )
    else:
        _plot_horizontal(cpuen_sp, "CPUEn (ind/100m2)", out_png_cpuen)
        _plot_horizontal(cpueb_sp, "CPUEb (g/100m2)", out_png_cpueb)

    if points:
        _plot_heatmap(
            cpuen_point,
            "CPUEn (ind/100m2)",
            out_png_cpuen_point,
            columns=points,
            xlabel="Ponto amostral",
            xlabels=points,
            x_rotation=90,
        )
        _plot_heatmap(
            cpueb_point,
            "CPUEb (g/100m2)",
            out_png_cpueb_point,
            columns=points,
            xlabel="Ponto amostral",
            xlabels=points,
            x_rotation=90,
        )

    return {
        "campaigns": campaigns,
        "points": points,
        "species": int(len(order_species)),
        "cpue_formula": "(species_abundance_or_biomass_at_point / sum_distinct_effort_by_campaign_point) * 100",
        "biomass_formula": biomass_formula,
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

    out_png = output_dir / f"10_grafico_diversidade_alfa_{group_slug}.png"
    points = _ordenar_pontos(df_projeto["nome_ponto"].dropna().astype(str).str.strip().unique().tolist())
    points = [point for point in points if point and point.lower() != "nan"]
    if len(campaigns) <= 2:
        _plot_few_campaign_diversity(
            diversity=df_out,
            out_png=out_png,
            theme=theme,
            campaigns=campaigns,
        )
    else:
        _small_multiple_diversity(
            diversity=df_out,
            out_png=out_png,
            theme=theme,
            points=points,
            campaigns=campaigns,
        )
    generated_files.append(str(out_png))

    details: dict = {"campaigns": campaigns, "base_quantitativa": "CPUEn (ind/100m2)"}
    if bool(theme.get("ictio_report_layout", False)):
        details["por_ano"] = _plot_report_diversity_by_year(
            df_projeto=df_projeto,
            theme=theme,
            output_dir=output_dir,
            group_slug=group_slug,
            generated_files=generated_files,
        )
    return details


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

    # A curva do coletor mede deteccao de especies, nao esforco padronizado.
    # `ictio_suficiencia_inclui_qualitativa` permite contar tambem os registros
    # qualitativos, que detectam especie da mesma forma; o padrao segue restrito
    # ao quantitativo para nao alterar entregas anteriores.
    inclui_quali = bool(theme.get("ictio_suficiencia_inclui_qualitativa", False))
    escopo = "quantitativa + qualitativa" if inclui_quali else "somente quantitativa"
    df_suf = _drop_effort_only_records(df_projeto)
    if not inclui_quali:
        df_suf = df_suf[df_suf["tipo_amostragem"].astype(str).str.contains("quantit", case=False, na=False)]
    df_suf = df_suf.copy()
    if df_suf.empty:
        return {"samples": 0, "warning": f"sem dados ({escopo})"}

    for c in ["nome_campanha", "nome_ponto", "nome_cientifico"]:
        df_suf[c] = df_suf[c].astype(str).str.strip()
    df_suf = df_suf[~df_suf["nome_cientifico"].isin(["", "nan", "None"])].copy()
    if df_suf.empty:
        return {"samples": 0, "warning": f"sem taxons identificados ({escopo})"}
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
    if mat.empty:
        return {"samples": 0, "warning": "amostras sem dados"}

    mat_pa = (mat > 0).astype(int)
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

    apply_theme(ax, theme, xlabel="Número de unidades amostrais", ylabel="Riqueza")
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

    return {
        "samples": n_samples,
        "observed_final": float(mean_sobs[-1]),
        "jackknife_final": float(mean_sest[-1]),
        "escopo_amostral": escopo,
    }


def _run_block_13(df_projeto: pd.DataFrame, group: str, output_dir: Path, generated_files: list[str]) -> dict:
    return export_darwincore_ief(
        df=_drop_effort_only_records(df_projeto),
        group=group,
        output_dir=output_dir,
        generated_files=generated_files,
        include_fish_biometrics=True,
    )


EMG_STAGE_LABELS = {
    "F": ["Repouso", "Maturação", "Maduro", "Desovado"],
    "M": ["Repouso", "Maturação", "Maduro", "Espermeado"],
}
EMG_STAGE_COLORS = {
    "F": ["#4472C4", "#C0504D", "#9BBB59", "#8064A2"],
    "M": ["#4472C4", "#C0504D", "#9BBB59", "#4BACC6"],
}
SEASON_LABELS = {"CH": "Chuva", "SC": "Seca", "ND": ""}


def _plot_report_emg_stacked(
    sexed: pd.DataFrame,
    sexo: str,
    theme: dict,
    campaigns: list[str],
    out_png: Path,
    generated_files: list[str],
) -> None:
    """Figura 18 do relatorio: EMG empilhado a 100% por campanha, para um sexo.

    O quarto estadio muda de nome conforme o sexo (`Desovado` para femeas,
    `Espermeado` para machos), como no relatorio.
    """
    stages = [1, 2, 3, 4]
    counts = (
        sexed[sexed["sexo"] == sexo]
        .pivot_table(index="campanha", columns="estadio", values="numero_de_individuos",
                     aggfunc="sum", fill_value=0)
        .reindex(index=campaigns, columns=stages, fill_value=0)
        .fillna(0.0)
    )
    percent = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0) * 100

    fig_theme = _theme_with(
        theme, grid_y=False, spine_sides=["left", "bottom"],
        legend_below_x_axis=False, legend_loc="upper center", legend_figure_loc="upper center",
    )
    size = theme.get("figsize_standard", [11.69, 8.27])
    fig, ax = plt.subplots(figsize=(float(size[0]), float(size[1])), dpi=int(theme.get("dpi", 600)))
    x = np.arange(len(campaigns))
    bottom = np.zeros(len(campaigns), dtype=float)
    for stage, label, color in zip(stages, EMG_STAGE_LABELS[sexo], EMG_STAGE_COLORS[sexo]):
        values = percent[stage].fillna(0.0).to_numpy(dtype=float)
        ax.bar(x, values, bottom=bottom, width=0.7, color=color, label=label)
        bottom += values

    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.set_xticks(x)
    ax.set_xticklabels([SEASON_LABELS.get(_campaign_season(c), "") for c in campaigns], ha="center")
    apply_theme(
        ax, fig_theme,
        xlabel="Campanha/Período",
        ylabel=f"{'Fêmeas' if sexo == 'F' else 'Machos'} - Percentual de EMG",
        x_tick_rotation=90,
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.09), ncol=4, frameon=False,
              fontsize=int(theme.get("legend_size", theme.get("font_size_base", 12))))
    validate_axes_style(ax, fig_theme)

    box_top = float(theme.get("ictio_report_campaign_box_top", -0.16))
    box_height = float(theme.get("ictio_report_campaign_box_height", 0.06))
    _draw_group_boxes(
        ax,
        [{"label": str(_campaign_index(c) or c), "indices": [i]} for i, c in enumerate(campaigns)],
        theme,
        y_top=box_top,
        height=box_height,
    )
    # O rotulo do eixo tem de ficar abaixo das caixas, nao sobre os rotulos de estacao.
    ax.xaxis.set_label_coords(0.5, box_top - box_height - 0.04)
    fig.tight_layout(rect=[0.0, 0.06, 1.0, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_png))


def _run_block_reproducao(
    df_detalhe: pd.DataFrame,
    group: str,
    theme: dict,
    output_dir: Path,
    generated_files: list[str],
) -> dict:
    """Figura 18 e Quadros 9 e 10: EMG por sexo, EMG por especie e IGS medio."""
    group_slug = _safe_group_name(group)
    if df_detalhe.empty:
        return {"warning": "sem dados em resultados_ictiofauna_detalhe"}

    df = df_detalhe.copy()
    df["sexo"] = df.get("sexo_padronizado", pd.Series(dtype=object)).astype(str).str.strip().str.upper()
    df["estadio"] = df.get("emg_codigo", pd.Series(dtype=object)).map(_emg_stage)
    df["nome_cientifico"] = df.get("nome_cientifico", pd.Series(dtype=object)).astype(str).str.strip()

    sexed = df[df["sexo"].isin(["F", "M"]) & df["estadio"].notna()].copy()
    if sexed.empty:
        return {"warning": "sem registros com sexo e estadio de maturacao gonadal"}
    sexed["estadio"] = sexed["estadio"].astype(int)

    stages = [1, 2, 3, 4]
    sex_label = {"F": "Fêmeas", "M": "Machos"}

    # ---------- Figura 18: EMG empilhado 100% por campanha, uma figura por sexo ----------
    # O eixo usa todas as campanhas do projeto, nao so as que tem individuos
    # sexados: campanhas sem material reprodutivo aparecem como coluna vazia,
    # como no relatorio, em vez de sumirem e desalinhar a numeracao.
    campaigns = sorted(
        df["campanha"].dropna().astype(str).str.strip().unique().tolist(),
        key=_campanha_sort_key,
    )
    geral = (
        sexed.pivot_table(index="sexo", columns="estadio", values="numero_de_individuos",
                          aggfunc="sum", fill_value=0)
        .reindex(index=["F", "M"], columns=stages, fill_value=0)
    )
    geral_pct = geral.div(geral.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0) * 100

    for sexo in ["F", "M"]:
        _plot_report_emg_stacked(
            sexed=sexed,
            sexo=sexo,
            theme=theme,
            campaigns=campaigns,
            out_png=output_dir / f"14_grafico_emg_{'femeas' if sexo == 'F' else 'machos'}_{group_slug}.png",
            generated_files=generated_files,
        )

    # ---------- Quadro 9: EMG relativo por especie e sexo + juvenis ----------
    juvenis = (
        df[df["sexo"] == "IMAT"].groupby("nome_cientifico")["numero_de_individuos"].sum()
    )
    index = sorted(set(sexed["nome_cientifico"]) | set(juvenis.index))
    quadro9 = pd.DataFrame(index=pd.Index(index, name="Espécie"))
    for sexo in ["F", "M"]:
        counts = (
            sexed[sexed["sexo"] == sexo]
            .pivot_table(index="nome_cientifico", columns="estadio", values="numero_de_individuos",
                         aggfunc="sum", fill_value=0)
            .reindex(index=index, columns=stages, fill_value=0)
        )
        percent = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0) * 100
        for stage in stages:
            quadro9[f"{sex_label[sexo]} {stage}"] = percent[stage].round(0)
    quadro9["Juvenis (abund.)"] = juvenis.reindex(index).fillna(0).astype(int)

    # ---------- Quadro 10: IGS medio (%) por especie, sexo e estadio ----------
    # A coluna `igs` do banco guarda a fracao e recebe 0 onde falta peso de gonada;
    # recalcular a partir de pg_g/pc_g evita as duas armadilhas.
    igs_base = sexed[sexed["pg_g"].notna() & sexed["pc_g"].notna() & sexed["pc_g"].gt(0)].copy()
    igs_base["igs_pct"] = igs_base["pg_g"] / igs_base["pc_g"] * 100
    quadro10 = pd.DataFrame(index=pd.Index(index, name="Espécie"))
    for sexo in ["F", "M"]:
        medias = (
            igs_base[igs_base["sexo"] == sexo]
            .pivot_table(index="nome_cientifico", columns="estadio", values="igs_pct", aggfunc="mean")
            .reindex(index=index, columns=stages)
        )
        for stage in stages:
            quadro10[f"{sex_label[sexo]} {stage}"] = medias[stage].round(1)

    out_q9 = output_dir / f"14_tabela_emg_por_especie_{group_slug}.xlsx"
    with pd.ExcelWriter(out_q9, engine="openpyxl") as writer:
        quadro9.reset_index().to_excel(writer, sheet_name="EMG_por_especie", index=False)
        (geral_pct.round(1).rename(index=sex_label)
         .rename_axis("Sexo").reset_index()).to_excel(writer, sheet_name="EMG_geral", index=False)
    generated_files.append(str(out_q9))

    out_q10 = output_dir / f"15_tabela_igs_por_especie_{group_slug}.xlsx"
    quadro10.reset_index().to_excel(out_q10, index=False, engine="openpyxl")
    generated_files.append(str(out_q10))

    return {
        "individuos_sexados": int(sexed["numero_de_individuos"].sum()),
        "femeas": int(sexed.loc[sexed["sexo"] == "F", "numero_de_individuos"].sum()),
        "machos": int(sexed.loc[sexed["sexo"] == "M", "numero_de_individuos"].sum()),
        "juvenis_imat": int(juvenis.sum()) if not juvenis.empty else 0,
        "especies_no_quadro": int(len(index)),
        "linhas_com_peso_de_gonada": int(len(igs_base)),
        "igs_formula": "pg_g / pc_g * 100 (recalculado; coluna igs do banco e fracao e traz zeros espurios)",
    }


def run_ictio_pipeline(
    *,
    project_id: int,
    group: str,
    theme: dict,
    output_dir: Path,
    env_file: str | None = None,
    block: str = "all",
    campaign_filter: list[str] | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = _load_ictio_df(project_id=project_id, group=group, env_file=env_file)
    df = _attach_line_level_biomass(df, theme)
    df, campaign_overrides = _apply_project_campaign_overrides(df, project_id, group)
    df, campaign_filter_details = _apply_campaign_filter(df, campaign_filter)
    if df.empty:
        raise RuntimeError("No rows loaded from Supabase for the selected project/group/campaign filter")

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
        "campaign_overrides": campaign_overrides,
        "campaign_filter": campaign_filter_details,
        "biomass_source": df.attrs.get("biomass_source"),
        "biomass_formula": df.attrs.get("biomass_formula"),
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
            theme=theme,
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

    if block_sel in {"9b", "biometria", "all"}:
        details["block_9b"] = _run_block_biometry(
            df_projeto=df,
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("9b")

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

    if block_sel in {"14", "reproducao", "all"}:
        project_code = ""
        if "codigo_interno_opyta" in df.columns:
            codes = df["codigo_interno_opyta"].dropna().astype(str).unique().tolist()
            project_code = codes[0] if len(codes) == 1 else ""
        details["block_14"] = _run_block_reproducao(
            df_detalhe=_load_ictio_detail_df(project_code, env_file),
            group=group,
            theme=theme,
            output_dir=output_dir,
            generated_files=generated_files,
        )
        executed_blocks.append("14")

    if not executed_blocks:
        raise ValueError(
            "Unsupported block for ictio pipeline. Use '3', '4', '5', '6', '7', '8', '9', '9b', "
            "'biometria', '10', '11', '12', '13', '14', 'reproducao' or 'all'."
        )

    details["executed_blocks"] = executed_blocks
    details["generated_files"] = generated_files
    return details
