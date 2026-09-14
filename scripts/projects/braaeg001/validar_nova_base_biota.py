from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text


PROJECT_CODE = "BRAAEG001"
EXPECTED_CODE = "BRAAEG001"
SHEET_TO_GROUP = {
    "Resultados_Fitoplancton": ("Fitoplancton", "Fitopl\u00e2ncton"),
    "Resultados_Zooplancton": ("Zooplancton", "Zoopl\u00e2ncton"),
    "Resultados_Zoobentos": ("Zoobentos", "Bentos"),
    "Resultados_Ictiofauna": ("Ictiofauna", "Ictiofauna"),
}
CANONICAL_GROUPS = ["Fitoplancton", "Zooplancton", "Zoobentos", "Ictiofauna"]
QUAL_TYPES = {"quantitativa", "qualitativa"}
BIO_OUT_DIR = Path("logs/validacao_biota_braaeg001")


@dataclass
class GroupWorkbook:
    group: str
    validator_group: str
    path: Path
    result_sheet: str
    sheets: dict[str, pd.DataFrame]
    sha256: str


@dataclass
class Issue:
    gate: str
    group: str
    severity: str
    code: str
    message: str
    detail: str = ""
    row_count: int = 0


@dataclass
class ValidationBundle:
    generated_at: str
    input_dir: str
    meio_fisico_file: str | None
    campaign_coverage_decision: str | None
    status_gate_a: str
    status_gate_b: str
    summary: list[dict[str, Any]] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    official_issues: list[dict[str, Any]] = field(default_factory=list)
    point_course_rows: list[dict[str, Any]] = field(default_factory=list)
    course_comparison: list[dict[str, Any]] = field(default_factory=list)
    effort_rows: list[dict[str, Any]] = field(default_factory=list)
    effort_mismatches: list[dict[str, Any]] = field(default_factory=list)
    taxa_summary: list[dict[str, Any]] = field(default_factory=list)
    taxa_audit: list[dict[str, Any]] = field(default_factory=list)
    db_summary: list[dict[str, Any]] = field(default_factory=list)


def norm_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text_value = str(value).replace("\u00a0", " ")
    text_value = unicodedata.normalize("NFKC", text_value)
    text_value = re.sub(r"\s+", " ", text_value).strip().lower()
    return text_value


def norm_key(value: object) -> str:
    text_value = norm_text(value)
    text_value = unicodedata.normalize("NFKD", text_value)
    return "".join(ch for ch in text_value if not unicodedata.combining(ch))


def safe_value(value: object) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_workbooks(input_dir: Path) -> list[GroupWorkbook]:
    workbooks: list[GroupWorkbook] = []
    for path in sorted(input_dir.glob("*.xlsx")):
        if path.name.startswith("~$") or path.name.startswith("2026") or "__backup_" in path.name:
            continue
        try:
            xls = pd.ExcelFile(path)
        except Exception:
            continue
        sheet_set = set(xls.sheet_names)
        for result_sheet, (group, validator_group) in SHEET_TO_GROUP.items():
            if result_sheet in sheet_set:
                sheets = {
                    sheet_name: pd.read_excel(xls, sheet_name=sheet_name, dtype=object).dropna(how="all")
                    for sheet_name in xls.sheet_names
                }
                workbooks.append(
                    GroupWorkbook(
                        group=group,
                        validator_group=validator_group,
                        path=path,
                        result_sheet=result_sheet,
                        sheets=sheets,
                        sha256=sha256_file(path),
                    )
                )
                break
    return workbooks


def parse_positive(value: object) -> tuple[bool, bool]:
    if pd.isna(value):
        return False, False
    txt = str(value).strip()
    if not txt:
        return False, False
    if norm_key(txt) in {"x", "presente", "sim"}:
        return True, True
    try:
        number = float(txt.replace(",", "."))
    except ValueError:
        return False, False
    return number > 0, False


def cell(row: pd.Series, name: str) -> Any:
    return safe_value(row[name]) if name in row.index else None


def point_key(row: pd.Series) -> tuple[str, str]:
    return (norm_key(row.get("Ponto")), norm_key(row.get("Campanha")))


def effort_key(row: pd.Series) -> tuple[str, str, str, str]:
    return (
        norm_key(row.get("Ponto")),
        norm_key(row.get("Campanha")),
        norm_key(row.get("Metodo_de_Captura")),
        norm_key(row.get("Tipo_de_Amostragem")),
    )


def summarize_group(wb: GroupWorkbook, issues: list[Issue], effort_rows: list[dict[str, Any]], effort_mismatches: list[dict[str, Any]]) -> dict[str, Any]:
    capa = wb.sheets.get("Capa_Projeto", pd.DataFrame())
    pontos = wb.sheets.get("Pontos_e_Campanhas", pd.DataFrame())
    esforco = wb.sheets.get("Metadados_Esforco", pd.DataFrame())
    resultados = wb.sheets.get(wb.result_sheet, pd.DataFrame())

    project_code = str(capa.iloc[0].get("Codigo_Opyta", "")).strip() if not capa.empty else ""
    if project_code != EXPECTED_CODE:
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="block",
                code="PROJECT_CODE_MISMATCH",
                message=f"Codigo_Opyta esperado {EXPECTED_CODE}, encontrado {project_code or '(vazio)'}.",
            )
        )

    point_keys = [point_key(row) for _, row in pontos.iterrows()]
    point_key_counts = Counter(point_keys)
    duplicate_point_keys = [key for key, count in point_key_counts.items() if all(key) and count > 1]
    if duplicate_point_keys:
        examples = [
            f"{key[0]} | {key[1]} ({point_key_counts[key]} linhas)"
            for key in duplicate_point_keys[:8]
        ]
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="warning",
                code="DUPLICATE_POINT_CAMPAIGN",
                message="Ha ponto+campanha repetido em Pontos_e_Campanhas.",
                detail="; ".join(examples),
                row_count=len(duplicate_point_keys),
            )
        )

    result_point_keys = [point_key(row) for _, row in resultados.iterrows()]
    missing_result_points = sorted({key for key in result_point_keys if all(key) and key not in point_key_counts})
    if missing_result_points:
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="block",
                code="RESULT_POINT_CAMPAIGN_NOT_IN_POINTS",
                message="Ha resultados com ponto+campanha ausente em Pontos_e_Campanhas.",
                detail="; ".join(f"{p} | {c}" for p, c in missing_result_points[:15]),
                row_count=len(missing_result_points),
            )
        )

    effort_keys = [effort_key(row) for _, row in esforco.iterrows()]
    effort_key_counts = Counter(effort_keys)
    duplicate_effort_keys = [key for key, count in effort_key_counts.items() if all(key) and count > 1]
    if duplicate_effort_keys:
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="warning",
                code="DUPLICATE_EFFORT_KEY",
                message="Ha chave de esforco repetida em Metadados_Esforco.",
                detail="; ".join(f"{p} | {c} | {m} | {t}" for p, c, m, t in duplicate_effort_keys[:10]),
                row_count=len(duplicate_effort_keys),
            )
        )

    invalid_sample_type_rows: list[str] = []
    unit_as_type_rows: list[str] = []
    non_numeric_effort_rows: list[str] = []
    for idx, row in esforco.iterrows():
        tipo = norm_key(row.get("Tipo_de_Amostragem"))
        unidade = norm_key(row.get("Unidade_Esforco"))
        effort_value = row.get("Esforco")
        effort_rows.append(
            {
                "grupo": wb.group,
                "linha_excel": idx + 2,
                "ponto": cell(row, "Ponto"),
                "campanha": cell(row, "Campanha"),
                "metodo": cell(row, "Metodo_de_Captura"),
                "tipo_amostragem": cell(row, "Tipo_de_Amostragem"),
                "esforco": cell(row, "Esforco"),
                "unidade_esforco": cell(row, "Unidade_Esforco"),
            }
        )
        if tipo and tipo not in QUAL_TYPES:
            invalid_sample_type_rows.append(f"linha {idx + 2}: {row.get('Tipo_de_Amostragem')}")
        if unidade in QUAL_TYPES:
            unit_as_type_rows.append(f"linha {idx + 2}: {row.get('Unidade_Esforco')}")
        if effort_value is not None and str(effort_value).strip():
            try:
                float(str(effort_value).strip().replace(",", "."))
            except ValueError:
                non_numeric_effort_rows.append(f"linha {idx + 2}: {effort_value}")

    if invalid_sample_type_rows:
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="block",
                code="EFFORT_INVALID_SAMPLE_TYPE",
                message="Tipo_de_Amostragem em Metadados_Esforco deve ser Quantitativa ou Qualitativa.",
                detail="; ".join(invalid_sample_type_rows[:12]),
                row_count=len(invalid_sample_type_rows),
            )
        )
    if unit_as_type_rows:
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="block",
                code="EFFORT_UNIT_LOOKS_LIKE_SAMPLE_TYPE",
                message="Unidade_Esforco em Metadados_Esforco parece conter tipo de amostragem.",
                detail="; ".join(unit_as_type_rows[:12]),
                row_count=len(unit_as_type_rows),
            )
        )
    if non_numeric_effort_rows:
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="warning",
                code="EFFORT_NON_NUMERIC",
                message="Esforco em Metadados_Esforco contem texto/unidade junto do valor.",
                detail="; ".join(non_numeric_effort_rows[:12]),
                row_count=len(non_numeric_effort_rows),
            )
        )

    effort_index: dict[tuple[str, str, str, str], list[pd.Series]] = defaultdict(list)
    for _, row in esforco.iterrows():
        key = effort_key(row)
        if all(key):
            effort_index[key].append(row)

    invalid_result_effort = []
    effort_value_mismatches = []
    for idx, row in resultados.iterrows():
        key = effort_key(row)
        if not all(key) or key not in effort_index:
            invalid_result_effort.append((idx + 2, row))
            continue
        candidates = effort_index[key]
        result_effort = norm_key(row.get("Esforco_Amostral"))
        result_unit = norm_key(row.get("Unidade_Esforco"))
        if result_effort or result_unit:
            matched = False
            for eff in candidates:
                if (
                    (not result_effort or norm_key(eff.get("Esforco")) == result_effort)
                    and (not result_unit or norm_key(eff.get("Unidade_Esforco")) == result_unit)
                ):
                    matched = True
                    break
            if not matched:
                effort_value_mismatches.append((idx + 2, row, candidates[0]))

    if invalid_result_effort:
        examples = []
        for line, row in invalid_result_effort[:8]:
            examples.append(
                f"linha {line}: {row.get('Ponto')} | {row.get('Campanha')} | "
                f"{row.get('Metodo_de_Captura')} | {row.get('Tipo_de_Amostragem')}"
            )
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="block",
                code="RESULT_WITHOUT_VALID_EFFORT",
                message="Resultados sem metadado de esforco correspondente por ponto+campanha+metodo+tipo.",
                detail="; ".join(examples),
                row_count=len(invalid_result_effort),
            )
        )

    if effort_value_mismatches:
        for line, row, effort in effort_value_mismatches[:100]:
            effort_mismatches.append(
                {
                    "grupo": wb.group,
                    "linha_excel": line,
                    "ponto": row.get("Ponto"),
                    "campanha": row.get("Campanha"),
                    "metodo": row.get("Metodo_de_Captura"),
                    "tipo": row.get("Tipo_de_Amostragem"),
                    "resultado_esforco": row.get("Esforco_Amostral"),
                    "resultado_unidade": row.get("Unidade_Esforco"),
                    "metadata_esforco": effort.get("Esforco"),
                    "metadata_unidade": effort.get("Unidade_Esforco"),
                }
            )
        issues.append(
            Issue(
                gate="Gate A",
                group=wb.group,
                severity="warning",
                code="RESULT_EFFORT_VALUE_OR_UNIT_MISMATCH",
                message="Ha resultados cujo valor/unidade de esforco diverge do Metadados_Esforco.",
                detail="Ver aba effort_mismatches.",
                row_count=len(effort_value_mismatches),
            )
        )

    positives = 0
    qualitative_hits = 0
    zeros = 0
    if "Numero_de_Individuos" in resultados.columns:
        for value in resultados["Numero_de_Individuos"]:
            positive, qualitative = parse_positive(value)
            positives += int(positive)
            qualitative_hits += int(qualitative)
            if not positive:
                zeros += 1

    return {
        "grupo": wb.group,
        "arquivo": str(wb.path),
        "sha256": wb.sha256,
        "codigo_opyta": project_code,
        "abas": ", ".join(wb.sheets.keys()),
        "campanhas": ", ".join(sorted({str(value).strip() for value in pontos.get("Campanha", pd.Series(dtype=object)).dropna()})),
        "pontos_linhas": int(len(pontos)),
        "pontos_nomes_distintos": int(pontos["Ponto"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique())
        if "Ponto" in pontos.columns
        else 0,
        "pontos_distintos": int(len({k for k in point_keys if all(k)})),
        "ponto_campanha_duplicados": int(len(duplicate_point_keys)),
        "esforcos_linhas": int(len(esforco)),
        "esforcos_chaves_distintas": int(len({k for k in effort_keys if all(k)})),
        "resultados_linhas": int(len(resultados)),
        "resultados_ocorrencias_positivas": int(positives),
        "resultados_zeros_ou_ausencias": int(zeros),
        "resultados_qualitativos_x": int(qualitative_hits),
        "taxons_distintos": int(resultados["Nome_Cientifico"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique())
        if "Nome_Cientifico" in resultados.columns
        else 0,
    }


def collect_point_courses(workbooks: list[GroupWorkbook], issues: list[Issue]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for wb in workbooks:
        pontos = wb.sheets.get("Pontos_e_Campanhas", pd.DataFrame())
        for idx, row in pontos.iterrows():
            rec = {
                "grupo": wb.group,
                "linha_excel": idx + 2,
                "ponto": cell(row, "Ponto"),
                "campanha": cell(row, "Campanha"),
                "data": safe_value(row.get("Data")),
                "latitude": cell(row, "Latitude"),
                "longitude": cell(row, "Longitude"),
                "curso_d_agua": cell(row, "Curso_d_Agua"),
                "bacia_hidrografica": cell(row, "Bacia_Hidrografica"),
                "municipio": cell(row, "Municipio"),
            }
            rows.append(rec)
            key = (norm_key(row.get("Ponto")), norm_key(row.get("Campanha")))
            if all(key):
                by_key[key].append(rec)

    for key, recs in by_key.items():
        courses = {norm_key(rec.get("curso_d_agua")) for rec in recs if norm_key(rec.get("curso_d_agua"))}
        coords = {(norm_key(rec.get("latitude")), norm_key(rec.get("longitude"))) for rec in recs if rec.get("latitude") is not None or rec.get("longitude") is not None}
        if len(courses) > 1:
            issues.append(
                Issue(
                    gate="Gate A",
                    group="Bioaquatica",
                    severity="block",
                    code="COURSE_NAME_CONFLICT_BETWEEN_GROUPS",
                    message="Mesmo ponto+campanha tem Curso_d_Agua diferente entre grupos biologicos.",
                    detail=f"{key[0]} | {key[1]}",
                    row_count=len(recs),
                )
            )
        if len(coords) > 1:
            issues.append(
                Issue(
                    gate="Gate A",
                    group="Bioaquatica",
                    severity="warning",
                    code="COORDINATE_CONFLICT_BETWEEN_GROUPS",
                    message="Mesmo ponto+campanha tem coordenadas diferentes entre grupos biologicos.",
                    detail=f"{key[0]} | {key[1]}",
                    row_count=len(recs),
                )
            )
    return rows


def compare_courses_with_meio_fisico(meio_fisico_file: Path | None, point_course_rows: list[dict[str, Any]], issues: list[Issue]) -> list[dict[str, Any]]:
    if meio_fisico_file is None or not meio_fisico_file.exists():
        return []

    try:
        mf = pd.read_excel(meio_fisico_file, sheet_name="Pontos_e_Campanhas", dtype=object).dropna(how="all")
    except Exception as exc:
        issues.append(
            Issue(
                gate="Gate A",
                group="Meio fisico",
                severity="warning",
                code="MEIO_FISICO_POINTS_READ_ERROR",
                message=f"Nao foi possivel ler Pontos_e_Campanhas do meio fisico: {exc}",
            )
        )
        return []

    bio_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in point_course_rows:
        key = (norm_key(rec.get("ponto")), norm_key(rec.get("campanha")))
        if all(key) and key not in bio_by_key:
            bio_by_key[key] = rec

    mf_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for _, row in mf.iterrows():
        key = (norm_key(row.get("Ponto")), norm_key(row.get("Campanha")))
        if all(key) and key not in mf_by_key:
            mf_by_key[key] = {
                "ponto": cell(row, "Ponto"),
                "campanha": cell(row, "Campanha"),
                "curso_d_agua": cell(row, "Curso_d_Agua"),
                "bacia_hidrografica": cell(row, "Bacia_Hidrografica"),
                "municipio": cell(row, "Municipio"),
            }

    rows: list[dict[str, Any]] = []
    all_keys = sorted(set(bio_by_key) | set(mf_by_key))
    diff_count = 0
    for key in all_keys:
        bio = bio_by_key.get(key)
        mf_rec = mf_by_key.get(key)
        if bio is None:
            status = "missing_in_biota"
        elif mf_rec is None:
            status = "missing_in_meio_fisico"
        elif norm_key(bio.get("curso_d_agua")) == norm_key(mf_rec.get("curso_d_agua")):
            status = "same"
        else:
            status = "different_course_name"
            diff_count += 1
        rows.append(
            {
                "ponto": bio.get("ponto") if bio else mf_rec.get("ponto"),
                "campanha": bio.get("campanha") if bio else mf_rec.get("campanha"),
                "status": status,
                "curso_biota": bio.get("curso_d_agua") if bio else None,
                "curso_meio_fisico": mf_rec.get("curso_d_agua") if mf_rec else None,
                "bacia_biota": bio.get("bacia_hidrografica") if bio else None,
                "bacia_meio_fisico": mf_rec.get("bacia_hidrografica") if mf_rec else None,
            }
        )
    if diff_count:
        issues.append(
            Issue(
                gate="Gate A",
                group="Meio fisico",
                severity="warning",
                code="COURSE_NAME_DIFFERS_FROM_BIOTA",
                message="Curso_d_Agua do meio fisico diverge da nova base da biota em pontos compartilhados.",
                detail="Replicar atualizacao dos nomes no meio fisico antes de reprocessar produtos.",
                row_count=diff_count,
            )
        )
    return rows


def connect_engine(opyta_data_root: Path):
    sys.path.insert(0, str(opyta_data_root))
    from core.engine import get_engine  # noqa: PLC0415

    return get_engine()


def run_official_validators(workbooks: list[GroupWorkbook], engine: Any | None) -> list[dict[str, Any]]:
    sys.path.insert(0, str(Path.cwd().parent / "Opyta_Data"))
    from validators.importacao.pipeline import validate_importacao_file  # noqa: PLC0415

    records: list[dict[str, Any]] = []
    for wb in workbooks:
        report = validate_importacao_file(
            wb.path,
            group=wb.validator_group,
            engine=engine,
            strict_unknown_species=False,
        )
        records.append(
            {
                "grupo": wb.group,
                "arquivo": str(wb.path),
                "status": "PASS" if report.can_proceed else "BLOCKED",
                "total_campanhas": report.total_campanhas,
                "total_pontos": report.total_pontos,
                "total_resultados": report.total_registros,
                "total_esforco_dias": report.total_esforco_dias,
                "total_especies_desconhecidas": report.total_especies_desconhecidas,
                "issue_code": "SUMMARY",
                "severity": "summary",
                "message": f"{len(report.blocks)} bloqueio(s), {len(report.warnings)} aviso(s), {len(report.infos)} info(s).",
                "lines": "",
            }
        )
        for issue in report.issues:
            records.append(
                {
                    "grupo": wb.group,
                    "arquivo": str(wb.path),
                    "status": "PASS" if report.can_proceed else "BLOCKED",
                    "total_campanhas": report.total_campanhas,
                    "total_pontos": report.total_pontos,
                    "total_resultados": report.total_registros,
                    "total_esforco_dias": report.total_esforco_dias,
                    "total_especies_desconhecidas": report.total_especies_desconhecidas,
                    "issue_code": issue.code,
                    "severity": issue.severity,
                    "message": issue.message,
                    "lines": ", ".join(str(x) for x in issue.lines),
                }
            )
    return records


def compatible_group(input_group: str, db_group: str | None) -> bool:
    input_norm = norm_key(input_group)
    db_norm = norm_key(db_group)
    if input_norm == "zoobentos":
        return db_norm in {"zoobentos", "bentos", "macroinvertebrados bentonicos"}
    return input_norm == db_norm


def audit_taxa(workbooks: list[GroupWorkbook], engine: Any | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    occurrences: dict[tuple[str, str], dict[str, Any]] = {}
    for wb in workbooks:
        resultados = wb.sheets.get(wb.result_sheet, pd.DataFrame())
        if "Nome_Cientifico" not in resultados.columns:
            continue
        for idx, row in resultados.iterrows():
            name = str(row.get("Nome_Cientifico", "")).strip()
            if not name or name.lower() == "nan":
                continue
            key = (wb.group, norm_key(name))
            rec = occurrences.setdefault(
                key,
                {
                    "grupo": wb.group,
                    "nome_cientifico": name,
                    "ocorrencias": 0,
                    "pontos": set(),
                    "campanhas": set(),
                    "primeira_linha": idx + 2,
                    "status_cadastro": "not_checked",
                    "grupo_banco": None,
                    "id_especie": None,
                },
            )
            rec["ocorrencias"] += 1
            rec["pontos"].add(str(row.get("Ponto", "")).strip())
            rec["campanhas"].add(str(row.get("Campanha", "")).strip())

    db_index: dict[str, dict[str, Any]] = {}
    if engine is not None:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id_especie, nome_cientifico, grupo_biologico FROM public.especies")).mappings().all()
        for row in rows:
            db_index[norm_key(row["nome_cientifico"])] = dict(row)

    audit: list[dict[str, Any]] = []
    for rec in occurrences.values():
        db_row = db_index.get(norm_key(rec["nome_cientifico"]))
        if db_row is None:
            status = "missing"
        elif compatible_group(rec["grupo"], db_row.get("grupo_biologico")):
            status = "existing"
        else:
            status = "group_conflict"
        audit.append(
            {
                "grupo": rec["grupo"],
                "nome_cientifico": rec["nome_cientifico"],
                "status_cadastro": status,
                "id_especie": db_row.get("id_especie") if db_row else None,
                "grupo_banco": db_row.get("grupo_biologico") if db_row else None,
                "ocorrencias": rec["ocorrencias"],
                "pontos": ", ".join(sorted(p for p in rec["pontos"] if p)),
                "campanhas": ", ".join(sorted(c for c in rec["campanhas"] if c)),
                "primeira_linha": rec["primeira_linha"],
            }
        )

    summary: list[dict[str, Any]] = []
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in audit:
        by_group[rec["grupo"]].append(rec)
    for group in CANONICAL_GROUPS:
        records = by_group.get(group, [])
        status_counts = Counter(rec["status_cadastro"] for rec in records)
        summary.append(
            {
                "grupo": group,
                "taxons_distintos": len(records),
                "existentes": status_counts.get("existing", 0),
                "ausentes": status_counts.get("missing", 0),
                "conflito_grupo": status_counts.get("group_conflict", 0),
            }
        )
    return summary, sorted(audit, key=lambda r: (r["grupo"], r["status_cadastro"], r["nome_cientifico"]))


def collect_db_summary(engine: Any | None) -> list[dict[str, Any]]:
    if engine is None:
        return [{"item": "db", "valor": "nao consultado"}]
    records: list[dict[str, Any]] = []
    with engine.connect() as conn:
        project = conn.execute(
            text(
                """
                SELECT id_projeto, codigo_interno_opyta, nome_projeto
                FROM public.projetos
                WHERE codigo_interno_opyta = :code
                """
            ),
            {"code": PROJECT_CODE},
        ).mappings().first()
        if project:
            records.extend(
                [
                    {"item": "id_projeto", "valor": project["id_projeto"]},
                    {"item": "codigo_interno_opyta", "valor": project["codigo_interno_opyta"]},
                    {"item": "nome_projeto", "valor": project["nome_projeto"]},
                ]
            )
            id_projeto = project["id_projeto"]
            points_count = conn.execute(
                text("SELECT count(*) FROM public.pontos_coleta WHERE id_projeto = :id"),
                {"id": id_projeto},
            ).scalar()
            records.append({"item": "pontos_coleta_projeto", "valor": points_count})
        else:
            records.append({"item": "projeto", "valor": "nao encontrado"})
        consolidated_count = conn.execute(
            text("SELECT count(*) FROM public.biota_analise_consolidada WHERE codigo_interno_opyta = :code"),
            {"code": PROJECT_CODE},
        ).scalar()
        records.append({"item": "biota_analise_consolidada_BRAAEG001", "valor": consolidated_count})
    return records


def build_report(
    input_dir: Path,
    meio_fisico_file: Path | None,
    opyta_data_root: Path,
    no_db: bool,
    allow_uneven_campaigns: bool,
    campaign_coverage_note: str | None,
) -> ValidationBundle:
    workbooks = load_workbooks(input_dir)
    issues: list[Issue] = []
    effort_rows: list[dict[str, Any]] = []
    effort_mismatches: list[dict[str, Any]] = []

    found_groups = {wb.group for wb in workbooks}
    missing_groups = [group for group in CANONICAL_GROUPS if group not in found_groups]
    for group in missing_groups:
        issues.append(
            Issue(
                gate="Gate A",
                group=group,
                severity="block",
                code="MISSING_GROUP_WORKBOOK",
                message="Planilha do grupo biologico nao encontrada na pasta de entrada.",
            )
        )

    summary = [summarize_group(wb, issues, effort_rows, effort_mismatches) for wb in workbooks]
    campaign_sets: dict[str, set[str]] = {}
    for wb in workbooks:
        pontos = wb.sheets.get("Pontos_e_Campanhas", pd.DataFrame())
        resultados = wb.sheets.get(wb.result_sheet, pd.DataFrame())
        campaigns = {
            str(value).strip()
            for value in pd.concat(
                [
                    pontos.get("Campanha", pd.Series(dtype=object)),
                    resultados.get("Campanha", pd.Series(dtype=object)),
                ],
                ignore_index=True,
            ).dropna()
            if str(value).strip()
        }
        campaign_sets[wb.group] = campaigns
    if campaign_sets and len({tuple(sorted(values)) for values in campaign_sets.values()}) > 1:
        detail = "; ".join(f"{group}: {', '.join(sorted(values))}" for group, values in sorted(campaign_sets.items()))
        issues.append(
            Issue(
                gate="Gate A",
                group="Bioaquatica",
                severity="warning" if allow_uneven_campaigns else "block",
                code="CAMPAIGN_COVERAGE_DIFFERS_BY_GROUP_APPROVED" if allow_uneven_campaigns else "CAMPAIGN_COVERAGE_DIFFERS_BY_GROUP",
                message=(
                    "A cobertura de campanhas difere entre os grupos biologicos, mas foi aceita como escopo operacional."
                    if allow_uneven_campaigns
                    else "A cobertura de campanhas difere entre os grupos biologicos; definir o recorte antes da migracao."
                ),
                detail=f"{detail}. Decisao: {campaign_coverage_note or 'nao informada'}",
                row_count=len(campaign_sets),
            )
        )
    point_course_rows = collect_point_courses(workbooks, issues)
    course_comparison = compare_courses_with_meio_fisico(meio_fisico_file, point_course_rows, issues)

    engine = None
    if not no_db:
        try:
            engine = connect_engine(opyta_data_root)
        except Exception as exc:
            issues.append(
                Issue(
                    gate="Gate B",
                    group="Bioaquatica",
                    severity="warning",
                    code="DB_CONNECTION_ERROR",
                    message=f"Nao foi possivel consultar o banco: {exc}",
                )
            )

    official_issues = run_official_validators(workbooks, engine)
    taxa_summary, taxa_audit = audit_taxa(workbooks, engine)
    db_summary = collect_db_summary(engine)

    for row in taxa_audit:
        if row["status_cadastro"] == "missing":
            issues.append(
                Issue(
                    gate="Gate B",
                    group=row["grupo"],
                    severity="block",
                    code="TAXON_MISSING_IN_MASTER_CATALOG",
                    message=f"Taxon ausente no cadastro mestre: {row['nome_cientifico']}",
                    detail=f"{row['ocorrencias']} ocorrencia(s); pontos: {row['pontos']}",
                    row_count=1,
                )
            )
        elif row["status_cadastro"] == "group_conflict":
            issues.append(
                Issue(
                    gate="Gate B",
                    group=row["grupo"],
                    severity="warning",
                    code="TAXON_GROUP_CONFLICT",
                    message=f"Taxon existe no banco, mas com grupo biologico diferente: {row['nome_cientifico']}",
                    detail=f"grupo banco: {row['grupo_banco']}",
                    row_count=1,
                )
            )

    gate_a_blocks = [issue for issue in issues if issue.gate == "Gate A" and issue.severity == "block"]
    gate_b_blocks = [issue for issue in issues if issue.gate == "Gate B" and issue.severity == "block"]
    status_gate_a = "BLOCKED" if gate_a_blocks else "PASS_WITH_WARNINGS" if any(issue.gate == "Gate A" for issue in issues) else "PASS"
    status_gate_b = "BLOCKED" if gate_b_blocks else "PASS_WITH_WARNINGS" if any(issue.gate == "Gate B" for issue in issues) else "PASS"

    return ValidationBundle(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        input_dir=str(input_dir),
        meio_fisico_file=str(meio_fisico_file) if meio_fisico_file else None,
        campaign_coverage_decision=campaign_coverage_note if allow_uneven_campaigns else None,
        status_gate_a=status_gate_a,
        status_gate_b=status_gate_b,
        summary=summary,
        issues=issues,
        official_issues=official_issues,
        point_course_rows=point_course_rows,
        course_comparison=course_comparison,
        effort_rows=effort_rows,
        effort_mismatches=effort_mismatches,
        taxa_summary=taxa_summary,
        taxa_audit=taxa_audit,
        db_summary=db_summary,
    )


def df_from_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def write_outputs(bundle: ValidationBundle, output_dir: Path, client_output_dir: Path | None) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if client_output_dir:
        client_output_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    base_name = f"{stamp}_validacao_nova_base_biota_aquatica_braaeg001"
    json_path = output_dir / f"{base_name}.json"
    xlsx_path = output_dir / f"{base_name}.xlsx"

    serializable = asdict(bundle)
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(serializable, fh, ensure_ascii=False, indent=2, default=str)

    issues_df = pd.DataFrame([asdict(issue) for issue in bundle.issues])
    taxa_missing_df = df_from_records([row for row in bundle.taxa_audit if row["status_cadastro"] != "existing"])
    course_diff_df = df_from_records([row for row in bundle.course_comparison if row.get("status") != "same"])
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {"item": "generated_at", "valor": bundle.generated_at},
                {"item": "input_dir", "valor": bundle.input_dir},
                {"item": "meio_fisico_file", "valor": bundle.meio_fisico_file},
                {"item": "campaign_coverage_decision", "valor": bundle.campaign_coverage_decision},
                {"item": "status_gate_a", "valor": bundle.status_gate_a},
                {"item": "status_gate_b", "valor": bundle.status_gate_b},
            ]
        ).to_excel(writer, sheet_name="00_resumo_gate", index=False)
        df_from_records(bundle.summary).to_excel(writer, sheet_name="01_resumo_grupos", index=False)
        issues_df.to_excel(writer, sheet_name="02_achados", index=False)
        df_from_records(bundle.official_issues).to_excel(writer, sheet_name="03_validador_oficial", index=False)
        df_from_records(bundle.point_course_rows).to_excel(writer, sheet_name="04_pontos_cursos_biota", index=False)
        df_from_records(bundle.course_comparison).to_excel(writer, sheet_name="05_cursos_vs_meio_fisico", index=False)
        course_diff_df.to_excel(writer, sheet_name="06_diferencas_cursos", index=False)
        df_from_records(bundle.effort_rows).to_excel(writer, sheet_name="07_esforcos", index=False)
        df_from_records(bundle.effort_mismatches).to_excel(writer, sheet_name="08_divergencias_esforco", index=False)
        df_from_records(bundle.taxa_summary).to_excel(writer, sheet_name="09_resumo_taxons", index=False)
        df_from_records(bundle.taxa_audit).to_excel(writer, sheet_name="10_auditoria_taxons", index=False)
        taxa_missing_df.to_excel(writer, sheet_name="11_taxons_problemas", index=False)
        df_from_records(bundle.db_summary).to_excel(writer, sheet_name="12_banco", index=False)

    if client_output_dir:
        client_json = client_output_dir / json_path.name
        client_xlsx = client_output_dir / xlsx_path.name
        client_json.write_bytes(json_path.read_bytes())
        client_xlsx.write_bytes(xlsx_path.read_bytes())

    return json_path, xlsx_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BRAAEG001 new bioaquatic base.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--meio-fisico-file", type=Path)
    parser.add_argument("--client-output-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=BIO_OUT_DIR)
    parser.add_argument("--opyta-data-root", type=Path, default=Path.cwd().parent / "Opyta_Data")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--allow-uneven-campaigns", action="store_true")
    parser.add_argument("--campaign-coverage-note")
    args = parser.parse_args()

    bundle = build_report(
        input_dir=args.input_dir,
        meio_fisico_file=args.meio_fisico_file,
        opyta_data_root=args.opyta_data_root,
        no_db=args.no_db,
        allow_uneven_campaigns=args.allow_uneven_campaigns,
        campaign_coverage_note=args.campaign_coverage_note,
    )
    json_path, xlsx_path = write_outputs(bundle, args.output_dir, args.client_output_dir)
    print(json.dumps(
        {
            "status_gate_a": bundle.status_gate_a,
            "status_gate_b": bundle.status_gate_b,
            "issues": len(bundle.issues),
            "json": str(json_path),
            "xlsx": str(xlsx_path),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
