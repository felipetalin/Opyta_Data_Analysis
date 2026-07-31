from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text


ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
for path in (ROOT / "src", OPYTA_DATA_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.engine import get_engine  # noqa: E402
from validators.importacao.pipeline import validate_importacao_file  # noqa: E402


PROJECT_CODE = "BRAAVG002"
PROJECT_ID = 9
GROUP = "Zoobentos"
RESULTS_TABLE = "resultados_zoobentos"
AUDIT_DIR = ROOT / "outputs" / "_migration" / "avg_bentos_2026"

TAXON_ALIASES = {
    "Atopsyche": "Atopsyche sp.",
}

MONTHS = {
    "jan": "Jan",
    "janeiro": "Jan",
    "fev": "Fev",
    "fevereiro": "Fev",
    "mar": "Mar",
    "marco": "Mar",
    "marco": "Mar",
    "abr": "Abr",
    "abril": "Abr",
    "mai": "Mai",
    "maio": "Mai",
    "jun": "Jun",
    "junho": "Jun",
    "jul": "Jul",
    "julho": "Jul",
    "ago": "Ago",
    "agosto": "Ago",
    "set": "Set",
    "setembro": "Set",
    "out": "Out",
    "outubro": "Out",
    "nov": "Nov",
    "novembro": "Nov",
    "dez": "Dez",
    "dezembro": "Dez",
}


@dataclass(frozen=True)
class CampaignRef:
    raw: str
    norm_key: str
    canonical: str
    id_campanha: int
    db_name: str


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text_value = str(value).replace("\xa0", " ").strip()
    return text_value == "" or text_value.lower() in {"nan", "none", "na", "n.a.", "n.a"}


def _clean_text(value: object) -> str | None:
    if _is_blank(value):
        return None
    return str(value).replace("\xa0", " ").strip()


def _norm_text(value: object) -> str:
    if _is_blank(value):
        return ""
    text_value = str(value).replace("\xa0", " ").strip().lower()
    text_value = (
        text_value.replace("Ã‚Âª", "a")
        .replace("Ã‚Âº", "o")
        .replace("Ã‚Â°", "o")
        .replace("ª", "a")
        .replace("º", "o")
        .replace("°", "o")
    )
    text_value = unicodedata.normalize("NFKD", text_value)
    text_value = "".join(ch for ch in text_value if not unicodedata.combining(ch))
    text_value = re.sub(r"[^a-z0-9]+", " ", text_value)
    return re.sub(r"\s+", " ", text_value).strip()


def _campaign_parts(value: object) -> tuple[int, str, int] | None:
    norm = _norm_text(value)
    match = re.match(r"^(\d+)\s*(?:a|o)?\s*(.*)$", norm)
    if not match:
        return None
    seq = int(match.group(1))
    tokens = [token for token in match.group(2).split() if token]
    month = None
    year2 = None
    for token in tokens:
        if token in MONTHS:
            month = MONTHS[token]
        elif re.fullmatch(r"\d{2,4}", token):
            year2 = int(token) % 100
    if month is None or year2 is None:
        return None
    return seq, month, year2


def campaign_norm_key(value: object) -> str:
    parts = _campaign_parts(value)
    if not parts:
        return _norm_text(value)
    seq, month, year2 = parts
    return f"{seq:02d}-{month.lower()}-{year2:02d}"


def campaign_canonical(value: object) -> str:
    parts = _campaign_parts(value)
    if not parts:
        text_value = _clean_text(value)
        if text_value is None:
            raise ValueError("Campanha vazia")
        return text_value
    seq, month, year2 = parts
    return f"{seq}ª-{month}-{year2:02d}"


def _to_float(value: object) -> float | None:
    if _is_blank(value):
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return int(round(numeric))


def _read_clean_workbook(xlsx: Path) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(xlsx)
    sheets = {
        "capa": pd.read_excel(xls, "Capa_Projeto").dropna(how="all"),
        "pontos": pd.read_excel(xls, "Pontos_e_Campanhas").dropna(how="all"),
        "esforco": pd.read_excel(xls, "Metadados_Esforco").dropna(how="all"),
        "resultados": pd.read_excel(xls, "Resultados_Zoobentos").dropna(how="all"),
    }

    key_cols = ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]
    resultados = sheets["resultados"].copy()
    has_key = resultados[key_cols].apply(lambda col: col.map(lambda value: not _is_blank(value))).any(axis=1)
    sheets["resultados"] = resultados.loc[has_key].copy()

    for name, df in sheets.items():
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].map(lambda value: None if _is_blank(value) else value)
        sheets[name] = df

    if "Nome_Cientifico" in sheets["resultados"].columns:
        sheets["resultados"]["Nome_Cientifico"] = sheets["resultados"]["Nome_Cientifico"].map(
            lambda value: TAXON_ALIASES.get(str(value).strip(), value) if value is not None else value
        )

    return sheets


def _write_clean_validation_copy(sheets: dict[str, pd.DataFrame], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        sheets["capa"].to_excel(writer, sheet_name="Capa_Projeto", index=False)
        sheets["pontos"].to_excel(writer, sheet_name="Pontos_e_Campanhas", index=False)
        sheets["esforco"].to_excel(writer, sheet_name="Metadados_Esforco", index=False)
        sheets["resultados"].to_excel(writer, sheet_name="Resultados_Zoobentos", index=False)


def _validate_clean_copy(clean_xlsx: Path, engine) -> dict[str, Any]:
    report = validate_importacao_file(
        clean_xlsx,
        group="Bentos",
        engine=engine,
        strict_unknown_species=True,
    )
    return {
        "can_proceed": bool(report.can_proceed),
        "blocks": [{"code": i.code, "message": i.message, "lines": i.lines} for i in report.blocks],
        "warnings": [{"code": i.code, "message": i.message, "lines": i.lines} for i in report.warnings],
        "infos": [{"code": i.code, "message": i.message} for i in report.infos],
        "totals": {
            "campanhas": int(report.total_campanhas),
            "pontos": int(report.total_pontos),
            "registros": int(report.total_registros),
            "especies_desconhecidas": int(report.total_especies_desconhecidas),
        },
    }


def _load_campaign_refs(conn, raw_campaigns: set[str], id_projeto: int) -> dict[str, CampaignRef]:
    db_campaigns = pd.read_sql(
        text(
            """
            SELECT DISTINCT c.id_campanha, c.nome_campanha
            FROM campanhas c
            JOIN pontos_coleta p ON p.id_campanha = c.id_campanha
            WHERE p.id_projeto = :id_projeto
            """
        ),
        conn,
        params={"id_projeto": id_projeto},
    )
    by_norm: dict[str, list[tuple[int, str]]] = {}
    for _, row in db_campaigns.iterrows():
        by_norm.setdefault(campaign_norm_key(row["nome_campanha"]), []).append(
            (int(row["id_campanha"]), str(row["nome_campanha"]))
        )

    refs: dict[str, CampaignRef] = {}
    missing: list[str] = []
    ambiguous: dict[str, list[tuple[int, str]]] = {}
    for raw in sorted(raw_campaigns, key=campaign_norm_key):
        norm_key = campaign_norm_key(raw)
        candidates = by_norm.get(norm_key, [])
        if not candidates:
            missing.append(raw)
            continue
        if len(candidates) > 1:
            ambiguous[raw] = candidates
            continue
        id_campanha, db_name = candidates[0]
        refs[raw] = CampaignRef(
            raw=raw,
            norm_key=norm_key,
            canonical=campaign_canonical(raw),
            id_campanha=id_campanha,
            db_name=db_name,
        )

    if missing or ambiguous:
        raise RuntimeError(
            "Falha ao resolver campanhas. "
            f"missing={missing}; ambiguous={ambiguous}"
        )
    return refs


def _project_id(conn, df_capa: pd.DataFrame) -> int:
    code = _clean_text(df_capa.iloc[0].get("Codigo_Opyta"))
    if code != PROJECT_CODE:
        raise RuntimeError(f"Codigo_Opyta esperado {PROJECT_CODE}, recebido {code}")
    id_projeto = conn.execute(
        text("SELECT id_projeto FROM projetos WHERE codigo_interno_opyta = :code"),
        {"code": code},
    ).scalar_one_or_none()
    if int(id_projeto or 0) != PROJECT_ID:
        raise RuntimeError(f"Projeto esperado {PROJECT_ID}, recebido {id_projeto}")
    return int(id_projeto)


def _prepare_pontos(df_pontos: pd.DataFrame, refs: dict[str, CampaignRef], id_projeto: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for _, row in df_pontos.iterrows():
        camp_raw = _clean_text(row.get("Campanha"))
        ponto = _clean_text(row.get("Ponto"))
        if not camp_raw or not ponto:
            continue
        ref = refs[camp_raw]
        data_value = pd.to_datetime(row.get("Data"), errors="coerce")
        records.append(
            {
                "id_projeto": id_projeto,
                "id_campanha": ref.id_campanha,
                "nome_ponto": ponto,
                "data_hora_coleta": None if pd.isna(data_value) else data_value.to_pydatetime(),
                "latitude": _to_float(row.get("Latitude")),
                "longitude": _to_float(row.get("Longitude")),
                "bacia_hidrografica": _clean_text(row.get("Bacia_Hidrografica")),
                "curso_d_agua": _clean_text(row.get("Curso_d_Agua")),
                "municipio": _clean_text(row.get("Municipio")),
                "observacoes": _clean_text(row.get("Observacoes_Coleta")),
            }
        )
    return records


def _species_map(conn) -> dict[str, int]:
    df = pd.read_sql(text("SELECT id_especie, nome_cientifico FROM especies"), conn)
    return {str(row["nome_cientifico"]).strip(): int(row["id_especie"]) for _, row in df.iterrows()}


def _pontos_map(conn, id_projeto: int) -> dict[tuple[int, str], int]:
    df = pd.read_sql(
        text(
            """
            SELECT id_ponto_coleta, id_campanha, nome_ponto
            FROM pontos_coleta
            WHERE id_projeto = :id_projeto
            """
        ),
        conn,
        params={"id_projeto": id_projeto},
    )
    return {(int(row["id_campanha"]), str(row["nome_ponto"]).strip()): int(row["id_ponto_coleta"]) for _, row in df.iterrows()}


def _prepare_efforts(df_esforco: pd.DataFrame, refs: dict[str, CampaignRef], point_map: dict[tuple[int, str], int]) -> list[dict[str, Any]]:
    records_by_key: dict[tuple[int, str, str], dict[str, Any]] = {}
    missing_points: list[str] = []
    for _, row in df_esforco.iterrows():
        group = _clean_text(row.get("Grupo_Biologico"))
        if group != GROUP:
            continue
        camp_raw = _clean_text(row.get("Campanha"))
        ponto = _clean_text(row.get("Ponto"))
        metodo = _clean_text(row.get("Metodo_de_Captura"))
        if not camp_raw or not ponto or not metodo:
            continue
        ref = refs[camp_raw]
        id_ponto = point_map.get((ref.id_campanha, ponto))
        if id_ponto is None:
            missing_points.append(f"{ref.db_name}/{ponto}")
            continue
        key = (id_ponto, GROUP, metodo)
        records_by_key[key] = {
            "id_ponto_coleta": id_ponto,
            "grupo_biologico": GROUP,
            "metodo_de_captura": metodo,
            "esforco": _to_float(row.get("Esforco")),
            "unidade_esforco": _clean_text(row.get("Unidade_Esforco")),
            "tipo_amostragem": _clean_text(row.get("Tipo_de_Amostragem")),
            "tipo_de_amostragem": _clean_text(row.get("Tipo_de_Amostragem")),
        }
    if missing_points:
        raise RuntimeError(f"Pontos de esforco ausentes no banco: {missing_points[:20]}")
    return list(records_by_key.values())


def _effort_map(conn, id_projeto: int, target_ids: list[int]) -> dict[tuple[int, str, str], int]:
    df = pd.read_sql(
        text(
            """
            SELECT e.id_esforco, p.id_campanha, p.nome_ponto, e.metodo_de_captura
            FROM esforcos_amostragem e
            JOIN pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id_projeto
              AND p.id_campanha = ANY(:target_ids)
              AND e.grupo_biologico = :grupo
            """
        ),
        conn,
        params={"id_projeto": id_projeto, "target_ids": target_ids, "grupo": GROUP},
    )
    return {
        (int(row["id_campanha"]), str(row["nome_ponto"]).strip(), str(row["metodo_de_captura"]).strip()): int(row["id_esforco"])
        for _, row in df.iterrows()
    }


def _prepare_results(
    df_resultados: pd.DataFrame,
    refs: dict[str, CampaignRef],
    efforts: dict[tuple[int, str, str], int],
    species: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    df = df_resultados.copy()
    for col in ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]:
        df[col] = df[col].map(_clean_text)
    df["Numero_de_Individuos"] = df["Numero_de_Individuos"].map(_to_float).fillna(0)

    grouped = (
        df.groupby(["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"], dropna=False)
        .agg(abundancia=("Numero_de_Individuos", "sum"))
        .reset_index()
    )

    records: list[dict[str, Any]] = []
    missing_species: set[str] = set()
    missing_efforts: set[str] = set()
    for _, row in grouped.iterrows():
        camp_raw = row["Campanha"]
        ponto = row["Ponto"]
        metodo = row["Metodo_de_Captura"]
        tipo = row["Tipo_de_Amostragem"]
        taxon = row["Nome_Cientifico"]
        if not camp_raw or not ponto or not metodo or not taxon:
            continue
        ref = refs[camp_raw]
        id_esforco = efforts.get((ref.id_campanha, ponto, metodo))
        if id_esforco is None:
            missing_efforts.add(f"{ref.db_name}/{ponto}/{metodo}")
            continue
        id_especie = species.get(taxon)
        if id_especie is None:
            missing_species.add(taxon)
            continue
        records.append(
            {
                "id_esforco": id_esforco,
                "id_especie": id_especie,
                "abundancia": _to_int(row["abundancia"]),
                "tipo_amostragem": tipo,
            }
        )
    if missing_species or missing_efforts:
        raise RuntimeError(
            "Falha ao preparar resultados. "
            f"missing_species={sorted(missing_species)[:30]}; "
            f"missing_efforts={sorted(missing_efforts)[:30]}"
        )
    summary = {
        "raw_valid_rows": int(len(df_resultados)),
        "aggregated_rows": int(len(grouped)),
        "abundancia_total": int(sum(r["abundancia"] or 0 for r in records)),
        "taxa": int(df["Nome_Cientifico"].dropna().nunique()),
    }
    return records, summary


def _preflight_results(
    df_resultados: pd.DataFrame,
    refs: dict[str, CampaignRef],
    effort_records: list[dict[str, Any]],
    point_map: dict[tuple[int, str], int],
    species: dict[str, int],
) -> tuple[int, dict[str, Any]]:
    effort_keys: set[tuple[int, str, str]] = set()
    id_point_to_key = {id_ponto: key for key, id_ponto in point_map.items()}
    for rec in effort_records:
        point_key = id_point_to_key.get(int(rec["id_ponto_coleta"]))
        if point_key is None:
            continue
        id_campanha, nome_ponto = point_key
        effort_keys.add((int(id_campanha), str(nome_ponto).strip(), str(rec["metodo_de_captura"]).strip()))

    df = df_resultados.copy()
    for col in ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]:
        df[col] = df[col].map(_clean_text)
    df["Numero_de_Individuos"] = df["Numero_de_Individuos"].map(_to_float).fillna(0)

    grouped = (
        df.groupby(["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"], dropna=False)
        .agg(abundancia=("Numero_de_Individuos", "sum"))
        .reset_index()
    )

    missing_species: set[str] = set()
    missing_efforts: set[str] = set()
    prepared = 0
    abundance_total = 0
    for _, row in grouped.iterrows():
        camp_raw = row["Campanha"]
        ponto = row["Ponto"]
        metodo = row["Metodo_de_Captura"]
        taxon = row["Nome_Cientifico"]
        if not camp_raw or not ponto or not metodo or not taxon:
            continue
        ref = refs[camp_raw]
        if (ref.id_campanha, ponto, metodo) not in effort_keys:
            missing_efforts.add(f"{ref.db_name}/{ponto}/{metodo}")
            continue
        if taxon not in species:
            missing_species.add(taxon)
            continue
        prepared += 1
        abundance_total += int(round(float(row["abundancia"] or 0)))

    if missing_species or missing_efforts:
        raise RuntimeError(
            "Falha no preflight de resultados. "
            f"missing_species={sorted(missing_species)[:30]}; "
            f"missing_efforts={sorted(missing_efforts)[:30]}"
        )

    return prepared, {
        "raw_valid_rows": int(len(df_resultados)),
        "aggregated_rows": int(len(grouped)),
        "abundancia_total": int(abundance_total),
        "taxa": int(df["Nome_Cientifico"].dropna().nunique()),
    }


def _db_counts(conn, id_projeto: int, target_ids: list[int]) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT
                count(*) AS linhas,
                count(distinct rz.id_esforco) AS esforcos_com_resultado,
                count(distinct rz.id_especie) AS taxa,
                coalesce(sum(rz.abundancia), 0) AS abundancia_total
            FROM resultados_zoobentos rz
            JOIN esforcos_amostragem e ON e.id_esforco = rz.id_esforco
            JOIN pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id_projeto
              AND p.id_campanha = ANY(:target_ids)
              AND e.grupo_biologico = :grupo
            """
        ),
        {"id_projeto": id_projeto, "target_ids": target_ids, "grupo": GROUP},
    ).mappings().one()
    return {key: int(value or 0) for key, value in dict(row).items()}


def run(xlsx: Path, apply: bool) -> dict[str, Any]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    sheets = _read_clean_workbook(xlsx)
    clean_xlsx = AUDIT_DIR / "projeto_bentos_real_AVG_260416_cleaned.xlsx"
    _write_clean_validation_copy(sheets, clean_xlsx)

    raw_campaigns = {
        str(value).strip()
        for df in (sheets["pontos"], sheets["esforco"], sheets["resultados"])
        for value in df.get("Campanha", pd.Series(dtype=object)).dropna().tolist()
        if str(value).strip()
    }

    engine = get_engine()
    try:
        with engine.begin() as conn:
            validation = _validate_clean_copy(clean_xlsx, engine)
            if not validation["can_proceed"]:
                raise RuntimeError(f"Validacao Opyta falhou na copia limpa: {validation['blocks']}")

            id_projeto = _project_id(conn, sheets["capa"])
            refs = _load_campaign_refs(conn, raw_campaigns, id_projeto)
            target_ids = sorted({ref.id_campanha for ref in refs.values()})
            before = _db_counts(conn, id_projeto, target_ids)

            pontos_records = _prepare_pontos(sheets["pontos"], refs, id_projeto)
            if apply and pontos_records:
                conn.execute(
                    text(
                        """
                        INSERT INTO pontos_coleta (
                            id_projeto, id_campanha, nome_ponto, data_hora_coleta,
                            latitude, longitude, bacia_hidrografica, curso_d_agua,
                            municipio, observacoes
                        )
                        VALUES (
                            :id_projeto, :id_campanha, :nome_ponto, :data_hora_coleta,
                            :latitude, :longitude, :bacia_hidrografica, :curso_d_agua,
                            :municipio, :observacoes
                        )
                        ON CONFLICT (id_projeto, id_campanha, nome_ponto)
                            WHERE id_empreendimento IS NULL
                        DO UPDATE SET
                            data_hora_coleta = EXCLUDED.data_hora_coleta,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            bacia_hidrografica = EXCLUDED.bacia_hidrografica,
                            curso_d_agua = EXCLUDED.curso_d_agua,
                            municipio = EXCLUDED.municipio,
                            observacoes = EXCLUDED.observacoes
                        """
                    ),
                    pontos_records,
                )

            point_map = _pontos_map(conn, id_projeto)
            effort_records = _prepare_efforts(sheets["esforco"], refs, point_map)
            result_records: list[dict[str, Any]] = []
            result_summary: dict[str, Any] = {}

            if apply:
                conn.execute(
                    text(
                        """
                        DELETE FROM resultados_zoobentos rz
                        USING esforcos_amostragem e, pontos_coleta p
                        WHERE rz.id_esforco = e.id_esforco
                          AND e.id_ponto_coleta = p.id_ponto_coleta
                          AND p.id_projeto = :id_projeto
                          AND p.id_campanha = ANY(:target_ids)
                          AND e.grupo_biologico = :grupo
                        """
                    ),
                    {"id_projeto": id_projeto, "target_ids": target_ids, "grupo": GROUP},
                )
                conn.execute(
                    text(
                        """
                        DELETE FROM esforcos_amostragem e
                        USING pontos_coleta p
                        WHERE e.id_ponto_coleta = p.id_ponto_coleta
                          AND p.id_projeto = :id_projeto
                          AND p.id_campanha = ANY(:target_ids)
                          AND e.grupo_biologico = :grupo
                        """
                    ),
                    {"id_projeto": id_projeto, "target_ids": target_ids, "grupo": GROUP},
                )
                if effort_records:
                    conn.execute(
                        text(
                            """
                            INSERT INTO esforcos_amostragem (
                                id_ponto_coleta, grupo_biologico, metodo_de_captura,
                                esforco, unidade_esforco, tipo_amostragem, tipo_de_amostragem
                            )
                            VALUES (
                                :id_ponto_coleta, :grupo_biologico, :metodo_de_captura,
                                :esforco, :unidade_esforco, :tipo_amostragem, :tipo_de_amostragem
                            )
                            ON CONFLICT (id_ponto_coleta, grupo_biologico, metodo_de_captura)
                            DO UPDATE SET
                                esforco = EXCLUDED.esforco,
                                unidade_esforco = EXCLUDED.unidade_esforco,
                                tipo_amostragem = EXCLUDED.tipo_amostragem,
                                tipo_de_amostragem = EXCLUDED.tipo_de_amostragem
                            """
                        ),
                        effort_records,
                    )
                efforts = _effort_map(conn, id_projeto, target_ids)
                species = _species_map(conn)
                result_records, result_summary = _prepare_results(sheets["resultados"], refs, efforts, species)
                if result_records:
                    conn.execute(
                        text(
                            """
                            INSERT INTO resultados_zoobentos (
                                id_esforco, id_especie, abundancia, tipo_amostragem
                            )
                            VALUES (
                                :id_esforco, :id_especie, :abundancia, :tipo_amostragem
                            )
                            ON CONFLICT (id_esforco, id_especie)
                            DO UPDATE SET
                                abundancia = EXCLUDED.abundancia,
                                tipo_amostragem = EXCLUDED.tipo_amostragem
                            """
                        ),
                        result_records,
                    )
                after = _db_counts(conn, id_projeto, target_ids)
            else:
                if not effort_records:
                    raise RuntimeError("Nenhum esforco preparado.")
                species = _species_map(conn)
                result_prepared, result_summary = _preflight_results(
                    sheets["resultados"],
                    refs,
                    effort_records,
                    point_map,
                    species,
                )
                result_records = [{} for _ in range(result_prepared)]
                after = before

            report = {
                "applied": apply,
                "xlsx": str(xlsx),
                "clean_xlsx": str(clean_xlsx),
                "validation": validation,
                "project_id": id_projeto,
                "target_campaigns": [
                    {
                        "raw": ref.raw,
                        "db_name": ref.db_name,
                        "id_campanha": ref.id_campanha,
                        "norm_key": ref.norm_key,
                    }
                    for ref in sorted(refs.values(), key=lambda ref: ref.norm_key)
                ],
                "counts": {
                    "source_pontos_rows": int(len(sheets["pontos"])),
                    "source_effort_rows": int(len(sheets["esforco"])),
                    "source_result_rows_clean": int(len(sheets["resultados"])),
                    "pontos_prepared": int(len(pontos_records)),
                    "efforts_prepared": int(len(effort_records)),
                    "results_prepared": int(len(result_records)),
                    "result_summary": result_summary,
                    "db_before": before,
                    "db_after": after,
                },
            }
            out_json = AUDIT_DIR / ("migration_applied.json" if apply else "migration_preflight.json")
            out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
            return report
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Migracao controlada AVG Bentos 2026")
    parser.add_argument("--xlsx", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Aplica a migracao no banco; sem isso, roda preflight.")
    args = parser.parse_args()

    report = run(xlsx=args.xlsx, apply=args.apply)
    print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    print(f"clean_xlsx={report['clean_xlsx']}")
    print(f"campaigns={len(report['target_campaigns'])}")
    print("APPLIED" if report["applied"] else "PREFLIGHT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
