from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text


ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from core.engine import get_engine  # noqa: E402
from opyta_analysis.geo_reference import read_kml_point_coordinates  # noqa: E402


PROJECT_ID = 9
PROJECT_CODE = "BRAAVG002"
GROUP = "Ictiofauna"
AUDIT_ROOT = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
DEFAULT_OUTPUT_DIR = AUDIT_ROOT / "readiness_ictio_long_study_20260713"
KML_BASE = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\Ponto amostral - AVG.kml")
KML_CURRENT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\KML Atual\Ponto amostral - AVG.kml"
)
GEOARC_TRAITS = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\Exploratorio_assembleia_ictiofauna\tabela_especie_atributos_funcionais_geoarc001_teste.xlsx"
)

FUNCTIONAL_FIELDS = [
    "Habitat_funcional",
    "Preferencia_correnteza",
    "Guilda_trofica",
    "Porte_corporal",
    "Sensibilidade_funcional",
]
SPECIES_FIELDS = [
    "origem",
    "status_ameaca_nacional",
    "status_ameaca_global",
    "status_copam",
    "status_estadual",
    "cites",
    "habito_alimentar",
    "guilda_alimentar",
    "estrategia_reprodutiva",
    "dependencia_florestal",
    "endemismo",
    "sensibilidade_ambiental",
    "migratorio",
    "raridade",
    "distribuicao",
    "valor_economico",
]
MONTHS = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
    "marco": 3,
    "abr": 4,
    "abri": 4,
    "abril": 4,
    "mai": 5,
    "maio": 5,
    "jun": 6,
    "junho": 6,
    "jul": 7,
    "julho": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "setembro": 9,
    "out": 10,
    "outubro": 10,
    "nov": 11,
    "novembro": 11,
    "dez": 12,
    "dezembro": 12,
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
    text = str(value or "").replace("\xa0", " ").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_point(value: object) -> str:
    text_value = str(value or "").strip().upper()
    text_value = unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii")
    match = re.search(r"PIC\s*-?\s*(\d+)", text_value)
    if match:
        return f"PIC-{int(match.group(1)):02d}"
    return re.sub(r"\s+", " ", text_value)


def _campaign_parts(value: object) -> tuple[int, int | None, int | None]:
    raw = str(value or "")
    text_value = _normalize_text(raw)
    seq_match = re.match(r"^\s*(\d+)", text_value)
    seq = int(seq_match.group(1)) if seq_match else 999999
    month = None
    year = None
    for token in text_value.split():
        if token in MONTHS:
            month = MONTHS[token]
        elif re.fullmatch(r"\d{2,4}", token):
            num = int(token)
            year = 2000 + num if num < 100 else num
    return seq, month, year


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return float(2 * radius * math.asin(math.sqrt(a)))


def _is_missing(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    normalized = _normalize_text(value)
    return normalized in {"", "nan", "none", "na", "n a", "nao informado", "sem classificacao"}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    engine = get_engine()
    try:
        points = pd.read_sql(
            text(
                """
                SELECT c.nome_campanha, p.nome_ponto, p.latitude, p.longitude,
                       p.curso_d_agua, p.bacia_hidrografica
                FROM pontos_coleta p
                JOIN campanhas c ON c.id_campanha = p.id_campanha
                WHERE p.id_projeto = :pid
                """
            ),
            engine,
            params={"pid": PROJECT_ID},
        )
        consolidated = pd.read_sql(
            text(
                """
                SELECT nome_campanha, nome_ponto, latitude, longitude, nome_cientifico,
                       contagem, biomassa, tipo_amostragem, esforco, ordem, familia,
                       genero, origem
                FROM biota_analise_consolidada
                WHERE codigo_interno_opyta = :code
                  AND grupo_biologico ILIKE :group
                """
            ),
            engine,
            params={"code": PROJECT_CODE, "group": "%Ictio%"},
        )
        species = pd.read_sql(
            text(
                """
                SELECT nome_cientifico, nome_popular, grupo_biologico, origem,
                       status_ameaca_nacional, status_ameaca_global, status_copam,
                       status_estadual, cites, habito_alimentar, guilda_alimentar,
                       estrategia_reprodutiva, dependencia_florestal, endemismo,
                       sensibilidade_ambiental, migratorio, raridade, distribuicao,
                       valor_economico
                FROM especies
                WHERE grupo_biologico ILIKE :group
                """
            ),
            engine,
            params={"group": "%Ictio%"},
        )
    finally:
        engine.dispose()
    return points, consolidated, species


def campaign_audit(points: pd.DataFrame, consolidated: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    point_campaign = points.copy()
    point_campaign["seq"], point_campaign["mes"], point_campaign["ano"] = zip(
        *point_campaign["nome_campanha"].map(_campaign_parts)
    )
    point_campaign["ponto_norm"] = point_campaign["nome_ponto"].map(_normalize_point)

    cons = consolidated.copy()
    cons["contagem"] = pd.to_numeric(cons["contagem"], errors="coerce").fillna(0)
    cons["biomassa"] = pd.to_numeric(cons["biomassa"], errors="coerce").fillna(0)
    cons["seq"], cons["mes"], cons["ano"] = zip(*cons["nome_campanha"].map(_campaign_parts))
    cons["ponto_norm"] = cons["nome_ponto"].map(_normalize_point)

    effort_summary = (
        point_campaign.groupby(["nome_campanha", "seq", "mes", "ano"], as_index=False)
        .agg(pontos_com_esforco=("ponto_norm", "nunique"), linhas_ponto_campanha=("ponto_norm", "size"))
    )
    result_summary = (
        cons.groupby(["nome_campanha"], as_index=False)
        .agg(
            registros_resultado=("nome_cientifico", "size"),
            pontos_com_captura=("ponto_norm", "nunique"),
            especies=("nome_cientifico", "nunique"),
            abundancia_total=("contagem", "sum"),
            biomassa_total=("biomassa", "sum"),
        )
    )
    summary = effort_summary.merge(result_summary, on="nome_campanha", how="left")
    for col in ["registros_resultado", "pontos_com_captura", "especies", "abundancia_total", "biomassa_total"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0)
    summary = summary.sort_values(["seq", "ano", "mes", "nome_campanha"]).reset_index(drop=True)

    meta = {
        "campaigns": int(point_campaign["nome_campanha"].nunique()),
        "points": int(point_campaign["ponto_norm"].nunique()),
        "point_campaign_rows": int(len(point_campaign)),
        "expected_point_campaign_rows": int(point_campaign["nome_campanha"].nunique() * point_campaign["ponto_norm"].nunique()),
        "first_campaign": str(summary.iloc[0]["nome_campanha"]) if not summary.empty else None,
        "last_campaign": str(summary.iloc[-1]["nome_campanha"]) if not summary.empty else None,
        "years": sorted(int(y) for y in point_campaign["ano"].dropna().unique().tolist()),
        "campaigns_by_year": {
            str(int(k)): int(v) for k, v in point_campaign.drop_duplicates("nome_campanha").groupby("ano").size().items()
        },
        "total_consolidated_rows": int(len(cons)),
        "total_abundance": float(cons["contagem"].sum()),
        "total_species": int(cons["nome_cientifico"].nunique()),
    }
    meta["complete_effort_grid"] = meta["point_campaign_rows"] == meta["expected_point_campaign_rows"]
    return summary, meta


def coordinate_variation(points: pd.DataFrame) -> pd.DataFrame:
    data = points.copy()
    data["ponto_norm"] = data["nome_ponto"].map(_normalize_point)
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    out = (
        data.groupby("ponto_norm", as_index=False)
        .agg(
            n_registros=("nome_campanha", "size"),
            n_campanhas=("nome_campanha", "nunique"),
            n_latitudes=("latitude", "nunique"),
            n_longitudes=("longitude", "nunique"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            lat_min=("latitude", "min"),
            lat_max=("latitude", "max"),
            lon_min=("longitude", "min"),
            lon_max=("longitude", "max"),
            cursos_dagua=("curso_d_agua", lambda s: "; ".join(sorted({str(x).strip() for x in s.dropna() if str(x).strip()}))),
        )
        .sort_values("ponto_norm")
        .reset_index(drop=True)
    )
    out["amplitude_lat"] = out["lat_max"] - out["lat_min"]
    out["amplitude_lon"] = out["lon_max"] - out["lon_min"]
    out["coordenada_estavel"] = (out["n_latitudes"] == 1) & (out["n_longitudes"] == 1)
    out["coordenada_presente"] = out["latitude"].notna() & out["longitude"].notna()
    return out


def compare_kml(points_unique: pd.DataFrame, reference: Path, label: str) -> pd.DataFrame:
    ref = read_kml_point_coordinates(reference)
    ref = ref.rename(columns={"Latitude_ref": "lat_ref", "Longitude_ref": "lon_ref"})
    ref["ponto_norm"] = ref["Ponto"].map(_normalize_point)
    ref = ref.sort_values("ponto_norm").drop_duplicates("ponto_norm", keep="first")
    comp = points_unique[["ponto_norm", "latitude", "longitude"]].merge(
        ref[["ponto_norm", "nome_original", "lat_ref", "lon_ref"]],
        on="ponto_norm",
        how="outer",
    )
    comp["referencia"] = label
    comp["arquivo_referencia"] = str(reference)
    comp["distancia_m"] = comp.apply(
        lambda row: _haversine_m(row["latitude"], row["longitude"], row["lat_ref"], row["lon_ref"])
        if pd.notna(row.get("latitude"))
        and pd.notna(row.get("longitude"))
        and pd.notna(row.get("lat_ref"))
        and pd.notna(row.get("lon_ref"))
        else np.nan,
        axis=1,
    )
    comp["status"] = np.where(
        comp["distancia_m"].notna() & (comp["distancia_m"] <= 5),
        "ok",
        np.where(comp["distancia_m"].isna(), "sem_comparacao", "divergente"),
    )
    return comp.sort_values(["referencia", "ponto_norm"]).reset_index(drop=True)


def species_audit(consolidated: pd.DataFrame, species_table: pd.DataFrame, traits_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    species = (
        consolidated[["nome_cientifico"]]
        .dropna()
        .drop_duplicates()
        .sort_values("nome_cientifico")
        .reset_index(drop=True)
    )
    species["species_key"] = species["nome_cientifico"].map(_normalize_text)
    cad = species_table.copy()
    cad["species_key"] = cad["nome_cientifico"].map(_normalize_text)
    joined = species.merge(cad, on="species_key", how="left", suffixes=("", "_cad"))

    if traits_path.exists():
        traits = pd.read_excel(traits_path)
        trait_name_col = "Nome Cientifico" if "Nome Cientifico" in traits.columns else "nome_cientifico"
        traits["species_key"] = traits[trait_name_col].map(_normalize_text)
        trait_cols = [trait_name_col, "species_key", *[col for col in FUNCTIONAL_FIELDS if col in traits.columns]]
        joined = joined.merge(traits[trait_cols], on="species_key", how="left", suffixes=("", "_trait"))
    else:
        trait_name_col = None

    rows = []
    for _, row in joined.iterrows():
        missing_cadastro = [field for field in SPECIES_FIELDS if _is_missing(row.get(field))]
        missing_traits = [field for field in FUNCTIONAL_FIELDS if _is_missing(row.get(field))]
        rows.append(
            {
                "nome_cientifico": row["nome_cientifico"],
                "cadastro_encontrado": not _is_missing(row.get("nome_cientifico_cad")),
                "campos_cadastro_faltantes_n": len(missing_cadastro),
                "campos_cadastro_faltantes": "; ".join(missing_cadastro),
                "tem_traits_geoarc": bool(trait_name_col and not _is_missing(row.get(trait_name_col))),
                "traits_funcionais_faltantes_n": len(missing_traits),
                "traits_funcionais_faltantes": "; ".join(missing_traits),
                "status_funcional": "ok_reutilizar_geoarc" if len(missing_traits) == 0 else "completar_traits",
            }
        )
    audit = pd.DataFrame(rows)
    meta = {
        "species": int(len(audit)),
        "species_with_complete_geoarc_traits": int((audit["traits_funcionais_faltantes_n"] == 0).sum()),
        "species_needing_functional_traits": int((audit["traits_funcionais_faltantes_n"] > 0).sum()),
        "species_needing_species_registry_completion": int((audit["campos_cadastro_faltantes_n"] > 0).sum()),
        "traits_source": str(traits_path),
        "traits_source_exists": traits_path.exists(),
    }
    return audit, meta


def write_report(
    output_dir: Path,
    campaign_summary: pd.DataFrame,
    campaign_meta: dict[str, Any],
    coords: pd.DataFrame,
    kml_compare: pd.DataFrame,
    species: pd.DataFrame,
    species_meta: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    kml_status = (
        kml_compare.groupby("referencia")
        .agg(
            pontos=("ponto_norm", "nunique"),
            ok=("status", lambda s: int((s == "ok").sum())),
            divergentes=("status", lambda s: int((s == "divergente").sum())),
            max_distancia_m=("distancia_m", "max"),
        )
        .reset_index()
    )
    readiness = {
        "long_series_ready": bool(campaign_meta["campaigns"] >= 12 and campaign_meta["complete_effort_grid"]),
        "beta_taxonomic_ready": bool(campaign_meta["campaigns"] >= 3 and campaign_meta["total_species"] > 1),
        "functional_ready": bool(species_meta["species_needing_functional_traits"] == 0),
        "coordinates_stable_in_database": bool(coords["coordenada_estavel"].all() and coords["coordenada_presente"].all()),
        "coordinates_match_base_kml": bool(
            (kml_compare[kml_compare["referencia"] == "geo_raiz"]["status"] == "ok").all()
        ),
        "coordinates_match_current_kml": bool(
            (kml_compare[kml_compare["referencia"] == "kml_atual"]["status"] == "ok").all()
        ),
    }
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": GROUP,
        "campaigns": campaign_meta,
        "species": species_meta,
        "coordinates": {
            "points": int(len(coords)),
            "missing_coordinates": int((~coords["coordenada_presente"]).sum()),
            "unstable_points": int((~coords["coordenada_estavel"]).sum()),
            "kml_status": kml_status.to_dict("records"),
        },
        "readiness": readiness,
    }
    json_path = output_dir / "readiness_ictio_avg_long_study.json"
    md_path = output_dir / "readiness_ictio_avg_long_study.md"
    xlsx_path = output_dir / "readiness_ictio_avg_long_study.xlsx"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        campaign_summary.to_excel(writer, sheet_name="campanhas", index=False)
        coords.to_excel(writer, sheet_name="coordenadas_banco", index=False)
        kml_compare.to_excel(writer, sheet_name="comparacao_kml", index=False)
        kml_status.to_excel(writer, sheet_name="resumo_kml", index=False)
        species.to_excel(writer, sheet_name="especies_traits", index=False)
    needs_traits = species[species["traits_funcionais_faltantes_n"] > 0]["nome_cientifico"].tolist()
    divergent_current = kml_compare[
        (kml_compare["referencia"] == "kml_atual") & (kml_compare["status"] == "divergente")
    ][["ponto_norm", "distancia_m"]]
    lines = [
        "# BRAAVG002 - Ictiofauna - readiness estudo longo",
        "",
        f"- campanhas: {campaign_meta['campaigns']} ({campaign_meta['first_campaign']} a {campaign_meta['last_campaign']})",
        f"- pontos: {campaign_meta['points']}; grade ponto-campanha completa: {campaign_meta['complete_effort_grid']}",
        f"- linhas consolidadas: {campaign_meta['total_consolidated_rows']}; especies: {campaign_meta['total_species']}; abundancia total: {campaign_meta['total_abundance']:.0f}",
        f"- coordenadas no banco: {int((~coords['coordenada_presente']).sum())} ausentes; {int((~coords['coordenada_estavel']).sum())} pontos instaveis",
        f"- comparacao KML raiz: {int((kml_compare[(kml_compare['referencia'] == 'geo_raiz')]['status'] == 'ok').sum())}/13 ok",
        f"- comparacao KML atual: {int((kml_compare[(kml_compare['referencia'] == 'kml_atual')]['status'] == 'ok').sum())}/13 ok",
        f"- especies com traits funcionais completos herdaveis do GEOARC001: {species_meta['species_with_complete_geoarc_traits']}",
        f"- especies que precisam completar traits funcionais: {species_meta['species_needing_functional_traits']}",
        "",
        "## Pontos divergentes contra KML atual",
        "",
    ]
    if divergent_current.empty:
        lines.append("- nenhum")
    else:
        for _, row in divergent_current.sort_values("ponto_norm").iterrows():
            lines.append(f"- {row['ponto_norm']}: {row['distancia_m']:.1f} m")
    lines.extend(["", "## Especies para completar traits funcionais", ""])
    if needs_traits:
        for name in needs_traits:
            lines.append(f"- {name}")
    else:
        lines.append("- nenhuma")
    lines.extend(
        [
            "",
            "## Arquivos",
            "",
            f"- JSON: `{json_path}`",
            f"- Excel: `{xlsx_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary["outputs"] = {"json": str(json_path), "xlsx": str(xlsx_path), "markdown": str(md_path)}
    return summary


def run(output_dir: Path, kml_base: Path, kml_current: Path, traits: Path) -> dict[str, Any]:
    points, consolidated, species_table = load_data()
    campaign_summary, campaign_meta = campaign_audit(points, consolidated)
    coords = coordinate_variation(points)
    kml_compare = pd.concat(
        [
            compare_kml(coords, kml_base, "geo_raiz"),
            compare_kml(coords, kml_current, "kml_atual"),
        ],
        ignore_index=True,
    )
    species, species_meta = species_audit(consolidated, species_table, traits)
    return write_report(output_dir, campaign_summary, campaign_meta, coords, kml_compare, species, species_meta)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audita prontidao do AVG Ictiofauna para estudo longo.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--kml-base", type=Path, default=KML_BASE)
    parser.add_argument("--kml-current", type=Path, default=KML_CURRENT)
    parser.add_argument("--traits", type=Path, default=GEOARC_TRAITS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run(args.output_dir, args.kml_base, args.kml_current, args.traits)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
