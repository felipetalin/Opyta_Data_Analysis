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
from opyta_analysis.geo_reference import read_kml_point_coordinates  # noqa: E402


PROJECT_CODE = "BRAAVG002"
PROJECT_ID = 9
GROUP = "Zoobentos"
CONFIG_PATH = ROOT / "configs" / "projects" / "braavg002_zoobentos_2026.json"
ICTIO_CONFIG_PATH = ROOT / "configs" / "projects" / "braavg002_ictiofauna_2026.json"
AUDIT_ROOT = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
DEFAULT_OUTPUT_DIR = AUDIT_ROOT / "zoobentos_consolidated_analytic_base_20260721"
KML_STANDARD = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Geo\Ponto amostral - AVG.kml")

MONTHS = {
    "jan": (1, "Jan"),
    "janeiro": (1, "Jan"),
    "fev": (2, "Fev"),
    "fevereiro": (2, "Fev"),
    "mar": (3, "Mar"),
    "marco": (3, "Mar"),
    "abr": (4, "Abr"),
    "abril": (4, "Abr"),
    "mai": (5, "Mai"),
    "maio": (5, "Mai"),
    "jun": (6, "Jun"),
    "junho": (6, "Jun"),
    "jul": (7, "Jul"),
    "julho": (7, "Jul"),
    "ago": (8, "Ago"),
    "agosto": (8, "Ago"),
    "set": (9, "Set"),
    "setembro": (9, "Set"),
    "out": (10, "Out"),
    "outubro": (10, "Out"),
    "nov": (11, "Nov"),
    "novembro": (11, "Nov"),
    "dez": (12, "Dez"),
    "dezembro": (12, "Dez"),
}

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


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def _normalize_text(value: object) -> str:
    text_value = _clean_text(value).lower()
    text_value = unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii")
    text_value = re.sub(r"[^a-z0-9]+", " ", text_value)
    return re.sub(r"\s+", " ", text_value).strip()


def _normalize_point(value: object) -> str:
    text_value = _clean_text(value).upper()
    text_value = unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii")
    match = re.search(r"PIC\s*-?\s*(\d+)", text_value)
    if match:
        return f"PIC-{int(match.group(1)):02d}"
    return re.sub(r"\s+", " ", text_value)


def campaign_parts(value: object) -> tuple[int, int, str, int]:
    raw = _clean_text(value)
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
    start = year if month >= 8 else year - 1
    end = start + 1
    return start, end, f"{start}/{end}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def point_layout() -> tuple[list[str], dict[str, str]]:
    recipe = load_json(ICTIO_CONFIG_PATH)
    layout = recipe["point_layout"]
    point_order = [_normalize_point(point) for point in layout["point_order"]]
    area_by_point: dict[str, str] = {}
    for group in layout["control_groups"]:
        for point in group["points"]:
            area_by_point[_normalize_point(point)] = group["label"].replace("Ã", "Á")
    return point_order, area_by_point


def load_standard_coordinates(kml_standard: Path, point_order: list[str]) -> pd.DataFrame:
    coords = read_kml_point_coordinates(kml_standard)
    if "Ponto" in coords.columns:
        coords["Ponto"] = coords["Ponto"].map(_normalize_point)
    else:
        coords["Ponto"] = coords["name"].map(_normalize_point)
    if "Latitude" not in coords.columns and "Latitude_ref" in coords.columns:
        coords = coords.rename(columns={"Latitude_ref": "Latitude", "Longitude_ref": "Longitude"})
    coords = coords[coords["Ponto"].isin(point_order)].copy()
    coords = coords.rename(columns={"latitude": "Latitude", "longitude": "Longitude"})
    coords = coords[["Ponto", "Latitude", "Longitude"]].drop_duplicates("Ponto")
    return coords.reset_index(drop=True)


def build_campaign_crosswalk(campaigns: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for campaign in sorted(campaigns.dropna().unique(), key=lambda value: campaign_parts(value)[0]):
        seq, month_num, month_label, year = campaign_parts(campaign)
        season = season_from_month(month_num)
        temporal_start, temporal_end, cycle = temporal_cycle_from_year_month(year, month_num)
        rows.append(
            {
                "Campanha_Original": _clean_text(campaign),
                "campanha_ordem": seq,
                "Ano_Calendario": year,
                "Mes": month_num,
                "Mes_Rotulo": month_label,
                "Periodo_Hidrologico": season,
                "Ano_Temporal_Inicio": temporal_start,
                "Ano_Temporal": temporal_end,
                "Ciclo_Temporal": cycle,
                "Campanha": f"C{seq:03d}-{year}-{month_num:02d}-{season}",
                "Campanha_Curta": f"C{seq:03d}",
                "Rotulo_Relatorio": f"{month_label}/{str(year)[2:]}",
            }
        )
    return pd.DataFrame(rows)


def is_not_monitored(point: str, seq: int) -> bool:
    for first_seq, last_seq in NOT_SAMPLED_CAMPAIGN_RANGES.get(point, []):
        in_range = seq >= first_seq
        if last_seq is not None:
            in_range = in_range and seq <= last_seq
        if in_range:
            return True
    return False


def apply_coordinate_overrides(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Fonte_Coordenada_Ajuste"] = "KML padrão provisório"
    out["Observacao_Coordenada"] = ""
    for point_name, payload in COORDINATE_OVERRIDES.items():
        mask = (out["Ponto"] == point_name) & (out["campanha_ordem"] >= int(payload["first_campaign_seq"]))
        out.loc[mask, "Latitude"] = float(payload["latitude"])
        out.loc[mask, "Longitude"] = float(payload["longitude"])
        out.loc[mask, "Fonte_Coordenada_Ajuste"] = str(payload["source"])
        out.loc[mask, "Observacao_Coordenada"] = str(payload["note"])
    return out


def load_consolidated() -> pd.DataFrame:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql(
                text(
                    """
                    SELECT nome_campanha, nome_ponto, latitude, longitude,
                           data_hora_coleta, bacia_hidrografica,
                           metodo_de_captura, esforco, unidade_esforco, tipo_amostragem,
                           nome_cientifico, contagem, biomassa, bmwp_score,
                           reino, filo, classe, ordem, familia, genero, origem
                    FROM public.biota_analise_consolidada
                    WHERE codigo_interno_opyta = :code
                      AND grupo_biologico = :group
                    """
                ),
                conn,
                params={"code": PROJECT_CODE, "group": GROUP},
            )
    finally:
        engine.dispose()


def load_efforts() -> pd.DataFrame:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql(
                text(
                    """
                    SELECT c.nome_campanha, p.nome_ponto,
                           p.data_hora_coleta, p.bacia_hidrografica,
                           e.metodo_de_captura, e.esforco, e.unidade_esforco,
                           COALESCE(e.tipo_amostragem, e.tipo_de_amostragem) AS tipo_amostragem
                    FROM public.esforcos_amostragem e
                    JOIN public.pontos_coleta p
                      ON p.id_ponto_coleta = e.id_ponto_coleta
                    JOIN public.campanhas c
                      ON c.id_campanha = p.id_campanha
                    WHERE p.id_projeto = :project_id
                      AND e.grupo_biologico = :group
                    """
                ),
                conn,
                params={"project_id": PROJECT_ID, "group": GROUP},
            )
    finally:
        engine.dispose()


def build(output_dir: Path, kml_standard: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    point_order, area_by_point = point_layout()
    point_order_map = {point: idx + 1 for idx, point in enumerate(point_order)}
    coords = load_standard_coordinates(kml_standard, point_order)
    raw = load_consolidated()
    efforts = load_efforts()
    raw["Ponto"] = raw["nome_ponto"].map(_normalize_point)
    crosswalk = build_campaign_crosswalk(raw["nome_campanha"])
    df = raw.merge(crosswalk, left_on="nome_campanha", right_on="Campanha_Original", how="left")
    df["Area_Controle"] = df["Ponto"].map(area_by_point)
    df = df.merge(coords, on="Ponto", how="left", suffixes=("_Banco", ""))
    df = apply_coordinate_overrides(df)
    df["Status_Monitoramento"] = np.where(
        [is_not_monitored(point, int(seq)) for point, seq in zip(df["Ponto"], df["campanha_ordem"])],
        "Não monitorado",
        "Monitorado",
    )
    df["Grupo_EPT"] = df["ordem"].isin(["Ephemeroptera", "Plecoptera", "Trichoptera"])
    df["Grupo_CHOL"] = df["familia"].eq("Chironomidae") | df["nome_cientifico"].isin(["Oligochaeta", "Oligoqueta"])
    df["Densidade"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0) / pd.to_numeric(
        df["esforco"], errors="coerce"
    ).replace(0, np.nan)

    analytic = pd.DataFrame(
        {
            "Campanha": df["Campanha"],
            "Campanha_Curta": df["Campanha_Curta"],
            "Campanha_Original": df["nome_campanha"],
            "Ponto": df["Ponto"],
            "Area_Controle": df["Area_Controle"],
            "Status_Monitoramento": df["Status_Monitoramento"],
            "Ano_Temporal": df["Ano_Temporal"],
            "Ciclo_Temporal": df["Ciclo_Temporal"],
            "Periodo_Hidrologico": df["Periodo_Hidrologico"],
            "Ano_Calendario": df["Ano_Calendario"],
            "Mes": df["Mes"],
            "Data": df["data_hora_coleta"],
            "Latitude": df["Latitude"],
            "Longitude": df["Longitude"],
            "Fonte_Coordenada_Ajuste": df["Fonte_Coordenada_Ajuste"],
            "Observacao_Coordenada": df["Observacao_Coordenada"],
            "Metodo_de_Captura": df["metodo_de_captura"],
            "Esforco": df["esforco"],
            "Unidade_Esforco": df["unidade_esforco"],
            "Tipo_de_Amostragem": df["tipo_amostragem"],
            "Nome_Cientifico": df["nome_cientifico"],
            "Numero_de_Individuos": pd.to_numeric(df["contagem"], errors="coerce").fillna(0),
            "Densidade": df["Densidade"],
            "Biomassa": pd.to_numeric(df["biomassa"], errors="coerce").fillna(0),
            "BMWP_Score": pd.to_numeric(df["bmwp_score"], errors="coerce"),
            "Reino": df["reino"],
            "Filo": df["filo"],
            "Classe": df["classe"],
            "Ordem": df["ordem"],
            "Familia": df["familia"],
            "Genero": df["genero"],
            "Origem": df["origem"],
            "EPT": df["Grupo_EPT"],
            "CHOL": df["Grupo_CHOL"],
        }
    )
    analytic["_ordem_campanha"] = df["campanha_ordem"]
    analytic["_ordem_ponto"] = analytic["Ponto"].map(point_order_map)
    analytic = analytic.sort_values(["_ordem_campanha", "_ordem_ponto", "Nome_Cientifico"]).drop(
        columns=["_ordem_campanha", "_ordem_ponto"]
    )

    analytic["EPT_Abundancia"] = np.where(analytic["EPT"], analytic["Numero_de_Individuos"], 0)
    analytic["CHOL_Abundancia"] = np.where(analytic["CHOL"], analytic["Numero_de_Individuos"], 0)
    metric_keys = ["Campanha", "Campanha_Curta", "Campanha_Original", "Ponto", "Area_Controle"]
    abundance_metrics = (
        analytic.groupby(metric_keys, as_index=False)
        .agg(
            riqueza=("Nome_Cientifico", "nunique"),
            abundancia=("Numero_de_Individuos", "sum"),
            densidade_total=("Densidade", "sum"),
            ept_abundancia=("EPT_Abundancia", "sum"),
            chol_abundancia=("CHOL_Abundancia", "sum"),
        )
    )
    bmwp_source = analytic.copy()
    bmwp_source["BMWP_Key"] = bmwp_source["Familia"].fillna("").replace("", np.nan).fillna(bmwp_source["Nome_Cientifico"])
    bmwp_by_family = (
        bmwp_source.groupby([*metric_keys, "BMWP_Key"], dropna=False, as_index=False)
        .agg(BMWP_Score=("BMWP_Score", "max"))
    )
    bmwp_metrics = (
        bmwp_by_family.groupby(metric_keys, as_index=False)
        .agg(bmwp_score=("BMWP_Score", "sum"), bmwp_familias=("BMWP_Key", "nunique"))
    )
    point_metrics = abundance_metrics.merge(bmwp_metrics, on=metric_keys, how="left")

    eff = efforts.copy()
    eff["Ponto"] = eff["nome_ponto"].map(_normalize_point)
    eff = eff.merge(crosswalk, left_on="nome_campanha", right_on="Campanha_Original", how="left")
    eff["Area_Controle"] = eff["Ponto"].map(area_by_point)
    eff = eff.merge(coords, on="Ponto", how="left")
    eff = apply_coordinate_overrides(eff)
    eff["Status_Monitoramento"] = np.where(
        [is_not_monitored(point, int(seq)) for point, seq in zip(eff["Ponto"], eff["campanha_ordem"])],
        "Não monitorado",
        "Monitorado",
    )
    point_campaign = pd.DataFrame(
        {
            "Campanha": eff["Campanha"],
            "Campanha_Curta": eff["Campanha_Curta"],
            "Campanha_Original": eff["nome_campanha"],
            "Ponto": eff["Ponto"],
            "Area_Controle": eff["Area_Controle"],
            "Status_Monitoramento": eff["Status_Monitoramento"],
            "Ano_Temporal": eff["Ano_Temporal"],
            "Ciclo_Temporal": eff["Ciclo_Temporal"],
            "Periodo_Hidrologico": eff["Periodo_Hidrologico"],
            "Data": eff["data_hora_coleta"],
            "Latitude": eff["Latitude"],
            "Longitude": eff["Longitude"],
            "Metodo_de_Captura": eff["metodo_de_captura"],
            "Esforco": eff["esforco"],
            "Unidade_Esforco": eff["unidade_esforco"],
            "Tipo_de_Amostragem": eff["tipo_amostragem"],
        }
    ).merge(point_metrics, on=["Campanha", "Campanha_Curta", "Campanha_Original", "Ponto", "Area_Controle"], how="left")
    for col in ["riqueza", "abundancia", "densidade_total", "ept_abundancia", "chol_abundancia", "bmwp_score", "bmwp_familias"]:
        point_campaign[col] = pd.to_numeric(point_campaign[col], errors="coerce").fillna(0)
    point_campaign["ept_percentual"] = np.where(
        point_campaign["abundancia"] > 0,
        100 * point_campaign["ept_abundancia"] / point_campaign["abundancia"],
        0,
    )
    point_campaign["chol_percentual"] = np.where(
        point_campaign["abundancia"] > 0,
        100 * point_campaign["chol_abundancia"] / point_campaign["abundancia"],
        0,
    )

    taxon_audit = (
        analytic.groupby(["Nome_Cientifico", "Ordem", "Familia", "Genero", "BMWP_Score"], dropna=False, as_index=False)
        .agg(linhas=("Nome_Cientifico", "size"), abundancia=("Numero_de_Individuos", "sum"))
        .sort_values("abundancia", ascending=False)
    )
    gap_summary = {
        "linhas": int(len(analytic)),
        "ponto_campanhas_com_esforco": int(len(point_campaign)),
        "ponto_campanhas_com_captura_zero": int((point_campaign["abundancia"] == 0).sum()),
        "ponto_campanhas_nao_monitorados_regra": int(point_campaign["Status_Monitoramento"].eq("Não monitorado").sum()),
        "campanhas": int(analytic["Campanha"].nunique()),
        "pontos": int(analytic["Ponto"].nunique()),
        "taxons": int(analytic["Nome_Cientifico"].nunique()),
        "abundancia_total": float(analytic["Numero_de_Individuos"].sum()),
        "bmwp_nulo": int(analytic["BMWP_Score"].isna().sum()),
        "familia_vazia": int(analytic["Familia"].fillna("").eq("").sum()),
        "ordem_vazia": int(analytic["Ordem"].fillna("").eq("").sum()),
        "campanhas_esperadas": 47,
        "pontos_esperados": 13,
        "status": "ok" if analytic["Campanha"].nunique() == 47 and analytic["BMWP_Score"].isna().sum() == 0 else "review",
    }

    xlsx = output_dir / "base_analitica_consolidada_zoobentos_20260721.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        analytic.to_excel(writer, sheet_name="base_analitica", index=False)
        point_campaign.to_excel(writer, sheet_name="ponto_campanha", index=False)
        taxon_audit.to_excel(writer, sheet_name="auditoria_taxons", index=False)
        crosswalk.to_excel(writer, sheet_name="campanhas", index=False)
        pd.DataFrame([gap_summary]).to_excel(writer, sheet_name="resumo_validacao", index=False)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": GROUP,
        "output_dir": output_dir,
        "source": "public.biota_analise_consolidada",
        "coordinate_reference": kml_standard,
        "coordinate_overrides": COORDINATE_OVERRIDES,
        "sampling_adjustments": NOT_SAMPLED_CAMPAIGN_RANGES,
        "summary": gap_summary,
        "outputs": {"analytic_workbook": xlsx},
    }
    manifest_path = output_dir / "manifesto_base_analitica_consolidada_zoobentos_20260721.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Monta base analitica consolidada AVG Zoobentos 01-47.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--kml-standard", type=Path, default=KML_STANDARD)
    args = parser.parse_args()
    manifest = build(args.output_dir, args.kml_standard)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
