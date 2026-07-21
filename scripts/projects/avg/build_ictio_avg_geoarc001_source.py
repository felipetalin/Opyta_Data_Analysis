from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from core.engine import get_engine  # noqa: E402
from opyta_analysis.geo_reference import read_kml_point_coordinates, read_kml_polygon_coordinates  # noqa: E402


PROJECT_ID = 9
PROJECT_CODE = "BRAAVG002"
GROUP = "Ictiofauna"
CONFIG_PATH = ROOT / "configs" / "projects" / "braavg002_ictiofauna_2026.json"
AUDIT_ROOT = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
DEFAULT_OUTPUT_DIR = AUDIT_ROOT / "geoarc001_long_study_source_20260713"
TRAITS_REVIEW = (
    AUDIT_ROOT
    / "species_traits_review_20260713"
    / "braavg002_ictiofauna_traits_funcionais_revisao.xlsx"
)
KML_STANDARD = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\Ponto amostral - AVG.kml"
)
AREA_CONTROL_LAYERS = [
    (
        "Area de controle 01",
        Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\771_area_controle_01_pl.kml"),
    ),
    (
        "Area de controle 02",
        Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\771_area_controle_02_pl.kml"),
    ),
]
MONTHS = {
    "jan": (1, "Jan"),
    "janeiro": (1, "Jan"),
    "fev": (2, "Fev"),
    "fevereiro": (2, "Fev"),
    "mar": (3, "Mar"),
    "marco": (3, "Mar"),
    "marco": (3, "Mar"),
    "abr": (4, "Abr"),
    "abri": (4, "Abr"),
    "abril": (4, "Abr"),
    "mai": (5, "Mai"),
    "maio": (5, "Mai"),
    "jun": (6, "Jun"),
    "junho": (6, "Jun"),
    "jul": (7, "Jul"),
    "julho": (7, "Jul"),
    "ago": (8, "Ago"),
    "agosto": (8, "Ago"),
    "aug": (8, "Ago"),
    "set": (9, "Set"),
    "setembro": (9, "Set"),
    "sep": (9, "Set"),
    "out": (10, "Out"),
    "outubro": (10, "Out"),
    "oct": (10, "Out"),
    "nov": (11, "Nov"),
    "novembro": (11, "Nov"),
    "dez": (12, "Dez"),
    "dezembro": (12, "Dez"),
    "dec": (12, "Dez"),
}
TRAIT_FIELDS = [
    "Habitat_funcional",
    "Preferencia_correnteza",
    "Guilda_trofica",
    "Porte_corporal",
    "Sensibilidade_funcional",
]
NOT_SAMPLED_CAMPAIGN_RANGES = {
    "PIC-01": [(40, None)],
    "PIC-02": [(40, 42)],
    "PIC-03": [(40, 42), (44, None)],
    "PIC-11": [(40, None)],
}
COORDINATE_OVERRIDES = {
    "PIC-11": {
        "latitude": -19.801526,
        "longitude": -43.700959,
        "first_campaign_seq": 1,
        "source": "ajuste_usuario_2026-07-14",
        "note": "Coordenada definida pelo usuario para PIC-11.",
    },
    "PIC-02": {
        "latitude": -19.800376,
        "longitude": -43.710610,
        "first_campaign_seq": 43,
        "source": "realocacao_fev_2026_usuario_2026-07-14",
        "note": "PIC-02 realocado a partir de fevereiro/2026.",
    },
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
    text_value = str(value or "").strip().lower()
    text_value = unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii")
    text_value = re.sub(r"[^a-z0-9]+", " ", text_value)
    return re.sub(r"\s+", " ", text_value).strip()


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def _normalize_point(value: object) -> str:
    text_value = str(value or "").strip().upper()
    text_value = unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii")
    match = re.search(r"PIC\s*-?\s*(\d+)", text_value)
    if match:
        return f"PIC-{int(match.group(1)):02d}"
    return re.sub(r"\s+", " ", text_value)


def _point_number(value: object) -> int:
    match = re.search(r"(\d+)", str(value or ""))
    return int(match.group(1)) if match else 999999


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


def temporal_cycle_from_year_month(year: int, month: int) -> tuple[int, int, str]:
    start_year = year if month >= 8 else year - 1
    end_year = start_year + 1
    return start_year, end_year, f"{start_year}/{end_year}"


def load_recipe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def point_layout(recipe: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    layout = recipe.get("point_layout") or {}
    groups = layout.get("control_groups") or []
    point_order = [str(point) for point in layout.get("point_order", [])]
    area_by_point: dict[str, str] = {}
    for group in groups:
        label = str(group.get("label", ""))
        for point in group.get("points", []):
            area_by_point[_normalize_point(point)] = label
    if not point_order:
        point_order = sorted(area_by_point, key=_point_number)
    return [_normalize_point(point) for point in point_order], area_by_point


def taxonomy_overrides(recipe: dict[str, Any]) -> dict[str, str]:
    review = (recipe.get("long_study_readiness") or {}).get("species_traits_review") or {}
    overrides = review.get("taxonomy_display_overrides") or {}
    out: dict[str, str] = {}
    for name, payload in overrides.items():
        display = payload.get("display_name") or payload.get("nome_cientifico_relatorio")
        if display:
            out[str(name)] = str(display)
    return out


def taxonomy_field_overrides(recipe: dict[str, Any]) -> dict[str, dict[str, str]]:
    review = (recipe.get("long_study_readiness") or {}).get("species_traits_review") or {}
    overrides = review.get("taxonomy_field_overrides") or {}
    out: dict[str, dict[str, str]] = {}
    for name, payload in overrides.items():
        if isinstance(payload, dict):
            fields = {
                str(field): str(value)
                for field, value in payload.items()
                if field in {"Origem", "Ordem", "Familia", "Genero"} and value
            }
            if fields:
                out[_clean_text(name)] = fields
    return out


def display_name(name: object, overrides: dict[str, str]) -> str:
    text_value = _clean_text(name)
    return overrides.get(text_value, text_value)


def apply_taxonomy_field_overrides(df: pd.DataFrame, overrides: dict[str, dict[str, str]]) -> pd.DataFrame:
    key_col = "Nome_Cientifico_Banco" if "Nome_Cientifico_Banco" in df.columns else "Nome Cientifico Banco"
    if not overrides or key_col not in df.columns:
        return df
    out = df.copy()
    keys = out[key_col].map(_clean_text)
    for name, fields in overrides.items():
        mask = keys == name
        if not mask.any():
            continue
        for field, value in fields.items():
            if field in out.columns:
                out.loc[mask, field] = value
    return out


def load_database() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    engine = get_engine()
    try:
        points = pd.read_sql(
            text(
                """
                SELECT c.id_campanha, c.nome_campanha,
                       p.nome_ponto, p.data_hora_coleta, p.latitude, p.longitude,
                       p.curso_d_agua, p.bacia_hidrografica
                FROM pontos_coleta p
                JOIN campanhas c ON c.id_campanha = p.id_campanha
                WHERE p.id_projeto = :pid
                """
            ),
            engine,
            params={"pid": PROJECT_ID},
        )
        efforts = pd.read_sql(
            text(
                """
                SELECT c.nome_campanha, p.nome_ponto,
                       e.metodo_de_captura,
                       COALESCE(e.tipo_amostragem, e.tipo_de_amostragem) AS tipo_amostragem,
                       e.unidade_esforco,
                       e.esforco
                FROM esforcos_amostragem e
                JOIN pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
                JOIN campanhas c ON c.id_campanha = p.id_campanha
                WHERE p.id_projeto = :pid
                  AND e.grupo_biologico = :group
                """
            ),
            engine,
            params={"pid": PROJECT_ID, "group": GROUP},
        )
        results = pd.read_sql(
            text(
                """
                SELECT nome_campanha, nome_ponto, data_hora_coleta,
                       metodo_de_captura, tipo_amostragem, unidade_esforco,
                       nome_cientifico, contagem, biomassa,
                       origem, ordem, familia, genero
                FROM biota_analise_consolidada
                WHERE codigo_interno_opyta = :code
                  AND grupo_biologico ILIKE :group_like
                  AND nome_cientifico IS NOT NULL
                """
            ),
            engine,
            params={"code": PROJECT_CODE, "group_like": "%Ictio%"},
        )
        registry = pd.read_sql(
            text(
                """
                SELECT nome_cientifico, nome_popular, origem, ordem, familia, genero,
                       status_ameaca_nacional, status_ameaca_global, status_estadual
                FROM especies
                WHERE grupo_biologico ILIKE :group_like
                """
            ),
            engine,
            params={"group_like": "%Ictio%"},
        )
    finally:
        engine.dispose()
    return points, efforts, results, registry


def build_crosswalk(points: pd.DataFrame) -> pd.DataFrame:
    campaigns = points[["id_campanha", "nome_campanha"]].drop_duplicates().copy()
    rows: list[dict[str, Any]] = []
    for _, row in campaigns.iterrows():
        seq, month_num, month_label, year = campaign_parts(row["nome_campanha"])
        season = season_from_month(month_num)
        temporal_start, temporal_end, cycle = temporal_cycle_from_year_month(year, month_num)
        rows.append(
            {
                "id_campanha": int(row["id_campanha"]),
                "nome_campanha_atual": _clean_text(row["nome_campanha"]),
                "campanha_ordem": seq,
                "ano_calendario": year,
                "mes": month_num,
                "mes_rotulo": month_label,
                "periodo_hidrologico": season,
                "ano_temporal_inicio": temporal_start,
                "ano_temporal_fim": temporal_end,
                "ciclo_temporal": cycle,
                "nome_campanha_padrao": f"C{seq:03d}-{year}-{month_num:02d}-{season}",
                "rotulo_curto": f"C{seq:03d}",
                "rotulo_relatorio": f"{month_label}/{str(year)[2:]}",
            }
        )
    return pd.DataFrame(rows).sort_values("campanha_ordem").reset_index(drop=True)


def apply_sampling_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    """Remove ponto-campanha definido como nao amostrado da camada analitica."""
    if df.empty or "nome_ponto" not in df.columns or "campanha_ordem" not in df.columns:
        return df
    out = df.copy()
    remove = pd.Series(False, index=out.index)
    seq = pd.to_numeric(out["campanha_ordem"], errors="coerce")
    for point_name, ranges in NOT_SAMPLED_CAMPAIGN_RANGES.items():
        for first_seq, last_seq in ranges:
            in_range = seq >= first_seq
            if last_seq is not None:
                in_range &= seq <= last_seq
            remove |= (out["nome_ponto"] == point_name) & in_range
    return out.loc[~remove].copy()


def apply_coordinate_overrides(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "nome_ponto" not in df.columns or "campanha_ordem" not in df.columns:
        return df
    out = df.copy()
    out["Fonte_Coordenada_Ajuste"] = ""
    out["Observacao_Coordenada"] = ""
    seq = pd.to_numeric(out["campanha_ordem"], errors="coerce")
    for point_name, payload in COORDINATE_OVERRIDES.items():
        mask = (out["nome_ponto"] == point_name) & (seq >= int(payload["first_campaign_seq"]))
        out.loc[mask, "Latitude"] = float(payload["latitude"])
        out.loc[mask, "Longitude"] = float(payload["longitude"])
        out.loc[mask, "Fonte_Coordenada_Ajuste"] = str(payload["source"])
        out.loc[mask, "Observacao_Coordenada"] = str(payload["note"])
    return out


def load_standard_coordinates(kml_standard: Path, point_order: list[str]) -> pd.DataFrame:
    coords = read_kml_point_coordinates(kml_standard)
    if coords.empty:
        raise ValueError(f"KML padrao sem pontos reconhecidos: {kml_standard}")
    coords["Ponto"] = coords["Ponto"].map(_normalize_point)
    coords = coords.rename(columns={"Latitude_ref": "Latitude", "Longitude_ref": "Longitude"})
    coords = coords[["Ponto", "Latitude", "Longitude", "nome_original", "fonte_coordenada"]].copy()
    coords["ordem_ponto"] = coords["Ponto"].map({point: idx for idx, point in enumerate(point_order)})
    coords = coords.sort_values(["ordem_ponto", "Ponto"], na_position="last").drop(columns="ordem_ponto")
    return coords.reset_index(drop=True)


def build_source_tables(
    points: pd.DataFrame,
    efforts: pd.DataFrame,
    results: pd.DataFrame,
    registry: pd.DataFrame,
    crosswalk: pd.DataFrame,
    coords: pd.DataFrame,
    point_order: list[str],
    area_by_point: dict[str, str],
    overrides: dict[str, str],
    field_overrides: dict[str, dict[str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    point_order_map = {point: idx for idx, point in enumerate(point_order)}
    campaign_cols = [
        "nome_campanha_atual",
        "nome_campanha_padrao",
        "campanha_ordem",
        "ano_calendario",
        "mes",
        "periodo_hidrologico",
        "ano_temporal_inicio",
        "ano_temporal_fim",
        "ciclo_temporal",
        "rotulo_relatorio",
    ]
    cw = crosswalk[campaign_cols].copy()

    pts = points.copy()
    pts["nome_ponto"] = pts["nome_ponto"].map(_normalize_point)
    pts = pts.merge(cw, left_on="nome_campanha", right_on="nome_campanha_atual", how="left")
    pts = apply_sampling_adjustments(pts)
    pts = pts.merge(coords, left_on="nome_ponto", right_on="Ponto", how="left", suffixes=("", "_kml"))
    pts = apply_coordinate_overrides(pts)
    pts["Area_Controle"] = pts["nome_ponto"].map(area_by_point)
    pts["Data"] = pd.to_datetime(
        dict(year=pts["ano_calendario"], month=pts["mes"], day=np.ones(len(pts), dtype=int)),
        errors="coerce",
    )
    pontos_source = pd.DataFrame(
        {
            "Campanha": pts["nome_campanha_padrao"],
            "Campanha_Original": pts["nome_campanha"],
            "Ponto": pts["nome_ponto"],
            "Data": pts["Data"],
            "Latitude": pts["Latitude"],
            "Longitude": pts["Longitude"],
            "Area_Controle": pts["Area_Controle"],
            "Ano_Temporal": pts["ano_temporal_fim"],
            "Ano_Calendario": pts["ano_calendario"],
            "Mes": pts["mes"],
            "Periodo_Hidrologico": pts["periodo_hidrologico"],
            "Ciclo_Temporal": pts["ciclo_temporal"],
            "Rotulo_Relatorio": pts["rotulo_relatorio"],
            "Curso_d_Agua": pts["curso_d_agua"],
            "Bacia_Hidrografica": pts["bacia_hidrografica"],
            "Fonte_Coordenada": str(KML_STANDARD),
            "Fonte_Coordenada_Ajuste": pts["Fonte_Coordenada_Ajuste"],
            "Observacao_Coordenada": pts["Observacao_Coordenada"],
        }
    )
    pontos_source["ordem_campanha"] = pts["campanha_ordem"]
    pontos_source["ordem_ponto"] = pontos_source["Ponto"].map(point_order_map)
    pontos_source = pontos_source.sort_values(["ordem_campanha", "ordem_ponto"]).drop(
        columns=["ordem_campanha", "ordem_ponto"]
    )

    eff = efforts.copy()
    eff["nome_ponto"] = eff["nome_ponto"].map(_normalize_point)
    eff = eff.merge(cw, left_on="nome_campanha", right_on="nome_campanha_atual", how="left")
    eff = apply_sampling_adjustments(eff)
    eff["Area_Controle"] = eff["nome_ponto"].map(area_by_point)
    esforcos_source = pd.DataFrame(
        {
            "Campanha": eff["nome_campanha_padrao"],
            "Campanha_Original": eff["nome_campanha"],
            "Ponto": eff["nome_ponto"],
            "Metodo_de_Captura": eff["metodo_de_captura"].fillna("Arrasto e peneira"),
            "Unidade_Esforco": eff["unidade_esforco"].fillna("m2/100"),
            "Tipo_de_Amostragem": eff["tipo_amostragem"].fillna("Quantitativa"),
            "Esforco": pd.to_numeric(eff["esforco"], errors="coerce"),
            "Area_Controle": eff["Area_Controle"],
            "Ano_Temporal": eff["ano_temporal_fim"],
            "Periodo_Hidrologico": eff["periodo_hidrologico"],
            "Ciclo_Temporal": eff["ciclo_temporal"],
        }
    )
    esforcos_source["ordem_campanha"] = eff["campanha_ordem"]
    esforcos_source["ordem_ponto"] = esforcos_source["Ponto"].map(point_order_map)
    esforcos_source = esforcos_source.sort_values(["ordem_campanha", "ordem_ponto"]).drop(
        columns=["ordem_campanha", "ordem_ponto"]
    )

    res = results.copy()
    res["nome_ponto"] = res["nome_ponto"].map(_normalize_point)
    res = res.merge(cw, left_on="nome_campanha", right_on="nome_campanha_atual", how="left")
    res = apply_sampling_adjustments(res)
    tax_cols = ["origem", "ordem", "familia", "genero"]
    tax_registry = registry[["nome_cientifico", *tax_cols]].drop_duplicates("nome_cientifico").rename(
        columns={col: f"{col}_cadastro" for col in tax_cols}
    )
    res = res.merge(tax_registry, on="nome_cientifico", how="left")
    for col in tax_cols:
        res[col] = res[f"{col}_cadastro"].combine_first(res[col])
    res["Area_Controle"] = res["nome_ponto"].map(area_by_point)
    res["nome_cientifico_relatorio"] = res["nome_cientifico"].map(lambda value: display_name(value, overrides))
    resultados_source = pd.DataFrame(
        {
            "Campanha": res["nome_campanha_padrao"],
            "Campanha_Original": res["nome_campanha"],
            "Ponto": res["nome_ponto"],
            "Metodo_de_Captura": res["metodo_de_captura"].fillna("Arrasto e peneira"),
            "Tipo_de_Amostragem": res["tipo_amostragem"].fillna("Quantitativa"),
            "Unidade_Esforco": res["unidade_esforco"].fillna("m2/100"),
            "Nome_Cientifico": res["nome_cientifico_relatorio"],
            "Nome_Cientifico_Banco": res["nome_cientifico"],
            "Numero_de_Individuos": pd.to_numeric(res["contagem"], errors="coerce").fillna(0),
            "Biomassa": pd.to_numeric(res["biomassa"], errors="coerce").fillna(0),
            "Origem": res["origem"],
            "Ordem": res["ordem"],
            "Familia": res["familia"],
            "Genero": res["genero"],
            "Area_Controle": res["Area_Controle"],
            "Ano_Temporal": res["ano_temporal_fim"],
            "Periodo_Hidrologico": res["periodo_hidrologico"],
            "Ciclo_Temporal": res["ciclo_temporal"],
        }
    )
    resultados_source = apply_taxonomy_field_overrides(resultados_source, field_overrides)
    resultados_source["ordem_campanha"] = res["campanha_ordem"]
    resultados_source["ordem_ponto"] = resultados_source["Ponto"].map(point_order_map)
    resultados_source = resultados_source.sort_values(["ordem_campanha", "ordem_ponto", "Nome_Cientifico"]).drop(
        columns=["ordem_campanha", "ordem_ponto"]
    )

    pontos_controle = pd.DataFrame(
        {
            "Ponto": point_order,
            "Area_Controle": [area_by_point.get(point) for point in point_order],
            "ordem_ponto": list(range(1, len(point_order) + 1)),
        }
    )
    return pontos_source, esforcos_source, resultados_source, pontos_controle


def build_traits(review_path: Path, overrides: dict[str, str]) -> pd.DataFrame:
    if not review_path.exists():
        raise FileNotFoundError(f"Matriz de traits aprovada nao encontrada: {review_path}")
    review = pd.read_excel(review_path, sheet_name="traits_funcionais")
    out = pd.DataFrame()
    out["Nome Cientifico"] = review["nome_cientifico"].map(lambda value: display_name(value, overrides))
    out["Nome Cientifico Banco"] = review["nome_cientifico"]
    for field in TRAIT_FIELDS:
        out[field] = review[field]
    out["Aplicar_no_teste"] = "sim"
    for col in ["Confianca_classificacao", "Fonte_classificacao", "Observacoes_funcionais"]:
        if col in review.columns:
            out[col] = review[col]
    return out.drop_duplicates("Nome Cientifico").sort_values("Nome Cientifico").reset_index(drop=True)


def build_composition(
    results_source: pd.DataFrame,
    registry: pd.DataFrame,
    overrides: dict[str, str],
    field_overrides: dict[str, dict[str, str]],
) -> pd.DataFrame:
    reg = registry.copy()
    reg["Nome_Cientifico_Banco"] = reg["nome_cientifico"].map(_clean_text)
    reg["Nome Cientifico"] = reg["nome_cientifico"].map(lambda value: display_name(value, overrides))
    used = results_source[["Nome_Cientifico_Banco"]].drop_duplicates()
    comp = used.merge(reg, on="Nome_Cientifico_Banco", how="left")
    comp["Nome Cientifico"] = comp["Nome Cientifico"].fillna(comp["Nome_Cientifico_Banco"].map(lambda value: display_name(value, overrides)))
    out = (
        comp.rename(
            columns={
                "Nome_Cientifico_Banco": "Nome Cientifico Banco",
                "nome_popular": "Nome Popular",
                "origem": "Origem",
                "ordem": "Ordem",
                "familia": "Familia",
                "genero": "Genero",
                "status_ameaca_nacional": "Status Ameaca Nacional",
                "status_ameaca_global": "Status Ameaca Global",
                "status_estadual": "Status Estadual",
            }
        )[
            [
                "Nome Cientifico",
                "Nome Cientifico Banco",
                "Nome Popular",
                "Origem",
                "Ordem",
                "Familia",
                "Genero",
                "Status Ameaca Nacional",
                "Status Ameaca Global",
                "Status Estadual",
            ]
        ]
        .drop_duplicates("Nome Cientifico")
        .sort_values("Nome Cientifico")
        .reset_index(drop=True)
    )
    return apply_taxonomy_field_overrides(out, field_overrides)


def write_combined_area_kml(output_path: Path, layers: list[tuple[str, Path]]) -> Path:
    placemarks: list[str] = []
    for label, layer in layers:
        if not layer.exists():
            continue
        data = read_kml_polygon_coordinates(layer)
        if data.empty:
            continue
        outer = data[data["ring_type"] == "outer"].copy()
        for (_polygon_id, ring_id), ring in outer.groupby(["polygon_id", "ring_id"], sort=False):
            ring = ring.sort_values("vertex_order")
            coords = " ".join(f"{row.Longitude:.8f},{row.Latitude:.8f},0" for row in ring.itertuples(index=False))
            if not coords:
                continue
            placemarks.append(
                "\n".join(
                    [
                        "    <Placemark>",
                        f"      <name>{label}</name>",
                        "      <Polygon>",
                        "        <outerBoundaryIs>",
                        "          <LinearRing>",
                        f"            <coordinates>{coords}</coordinates>",
                        "          </LinearRing>",
                        "        </outerBoundaryIs>",
                        "      </Polygon>",
                        "    </Placemark>",
                    ]
                )
            )
    kml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            "  <Document>",
            "    <name>BRAAVG002 areas de controle combinadas</name>",
            *placemarks,
            "  </Document>",
            "</kml>",
            "",
        ]
    )
    output_path.write_text(kml, encoding="utf-8")
    return output_path


def write_outputs(
    output_dir: Path,
    source: pd.DataFrame,
    efforts: pd.DataFrame,
    results: pd.DataFrame,
    traits: pd.DataFrame,
    composition: pd.DataFrame,
    crosswalk: pd.DataFrame,
    points_control: pd.DataFrame,
    combined_area_kml: Path,
    coords: pd.DataFrame,
) -> dict[str, str]:
    source_path = output_dir / "braavg002_geoarc001_source_ictiofauna.xlsx"
    traits_path = output_dir / "braavg002_geoarc001_traits_funcionais_ictiofauna.xlsx"
    composition_path = output_dir / "braavg002_geoarc001_composicao_ictiofauna.xlsx"
    with pd.ExcelWriter(source_path, engine="openpyxl") as writer:
        source.to_excel(writer, sheet_name="Pontos_e_Campanhas", index=False)
        efforts.to_excel(writer, sheet_name="Metadados_Esforco", index=False)
        results.to_excel(writer, sheet_name="Resultados_Ictiofauna", index=False)
        crosswalk.to_excel(writer, sheet_name="Campanhas_Crosswalk", index=False)
        points_control.to_excel(writer, sheet_name="Pontos_Area_Controle", index=False)
        coords.to_excel(writer, sheet_name="Coordenadas_KML_Padrao", index=False)
    with pd.ExcelWriter(traits_path, engine="openpyxl") as writer:
        traits.to_excel(writer, sheet_name="atributos_funcionais", index=False)
    with pd.ExcelWriter(composition_path, engine="openpyxl") as writer:
        composition.to_excel(writer, sheet_name="composicao", index=False)
    return {
        "source_workbook": str(source_path),
        "traits_workbook": str(traits_path),
        "composition_workbook": str(composition_path),
        "combined_area_kml": str(combined_area_kml),
    }


def build(output_dir: Path, recipe_path: Path, kml_standard: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    recipe = load_recipe(recipe_path)
    point_order, area_by_point = point_layout(recipe)
    overrides = taxonomy_overrides(recipe)
    field_overrides = taxonomy_field_overrides(recipe)
    points, efforts, results, registry = load_database()
    crosswalk = build_crosswalk(points)
    coords = load_standard_coordinates(kml_standard, point_order)
    pontos_source, esforcos_source, resultados_source, points_control = build_source_tables(
        points,
        efforts,
        results,
        registry,
        crosswalk,
        coords,
        point_order,
        area_by_point,
        overrides,
        field_overrides,
    )
    traits = build_traits(TRAITS_REVIEW, overrides)
    composition = build_composition(resultados_source, registry, overrides, field_overrides)
    area_kml = write_combined_area_kml(output_dir / "braavg002_areas_controle_01_02.kml", AREA_CONTROL_LAYERS)
    outputs = write_outputs(
        output_dir,
        pontos_source,
        esforcos_source,
        resultados_source,
        traits,
        composition,
        crosswalk,
        points_control,
        area_kml,
        coords,
    )
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "output_dir": str(output_dir),
        "coordinate_decision": "kml_padrao_provisorio_com_ajustes_usuario",
        "coordinate_reference": str(kml_standard),
        "coordinate_note": (
            "Usuario aprovou assumir o KML padrao neste momento; foram aplicados ajustes analiticos para "
            "PIC-11 e para a realocacao do PIC-02 a partir de fevereiro/2026. KML Atual permanece como ajuste futuro."
        ),
        "sampling_adjustments": NOT_SAMPLED_CAMPAIGN_RANGES,
        "coordinate_overrides": COORDINATE_OVERRIDES,
        "campaigns": int(crosswalk["nome_campanha_atual"].nunique()),
        "temporal_cycles": crosswalk.groupby("ciclo_temporal", as_index=False).agg(
            campanhas=("nome_campanha_atual", "nunique"),
            primeira=("nome_campanha_atual", "first"),
            ultima=("nome_campanha_atual", "last"),
        ).to_dict("records"),
        "points": int(pontos_source["Ponto"].nunique()),
        "point_campaign_rows": int(len(pontos_source)),
        "effort_rows": int(len(esforcos_source)),
        "result_rows": int(len(resultados_source)),
        "species": int(resultados_source["Nome_Cientifico"].nunique()),
        "area_control_groups": points_control.to_dict("records"),
        "taxonomy_display_overrides": overrides,
        "taxonomy_field_overrides": field_overrides,
        "outputs": outputs,
    }
    manifest = output_dir / "manifesto_braavg002_geoarc001_source_ictiofauna.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary["manifest"] = str(manifest)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monta fonte AVG Ictiofauna compativel com os scripts GEOARC001.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--recipe", default=str(CONFIG_PATH))
    parser.add_argument("--kml-standard", default=str(KML_STANDARD))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build(Path(args.output_dir), Path(args.recipe), Path(args.kml_standard))
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
