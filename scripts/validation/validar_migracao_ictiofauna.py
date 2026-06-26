#!/usr/bin/env python
"""Generic pre-migration validation for Ictiofauna workbooks.

This script extracts the reusable checks first consolidated during the Ducal
validation and keeps project-specific information in command-line arguments.
It can run with or without the external Opyta_Data validators/database access.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from opyta_analysis.geo_reference import haversine_km, read_kml_point_coordinates, standardize_point_name

DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "validacoes"
DEFAULT_OPTYA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
GROUP = "Ictiofauna"

IMPORT_SHEETS = [
    "Capa_Projeto",
    "Pontos_e_Campanhas",
    "Metadados_Esforco",
    "Resultados_Ictiofauna",
]
SPECIES_SHEETS = [
    "Especies",
    "Endemismo_Especies",
    "Bacias_Hidrograficas",
    "Biomas",
]


def norm(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).replace("\xa0", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def slugify(value: object) -> str:
    text = norm(value)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "projeto"


def to_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", ".")
    if text == "" or text.upper() in {"N.A.", "NA", "NAN", "NONE"}:
        return None
    try:
        return float(text)
    except Exception:
        return math.nan


def to_intish(value: object) -> int | None:
    parsed = to_float(value)
    if parsed is None or (isinstance(parsed, float) and math.isnan(parsed)):
        return None
    return int(parsed)


def issue(
    kind: str,
    severity: str,
    code: str,
    message: str,
    *,
    lines: list[int] | None = None,
    sheet: str = "",
    suggestion: str = "",
) -> dict[str, Any]:
    return {
        "tipo": kind,
        "severidade": severity,
        "codigo": code,
        "aba": sheet,
        "linhas": ", ".join(str(x) for x in (lines or [])),
        "mensagem": message,
        "sugestao": suggestion,
    }


def import_issues_df(report: object, label: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for severity, attr in [("BLOQUEIO", "blocks"), ("AVISO", "warnings"), ("INFO", "infos")]:
        for item in getattr(report, attr, []):
            rows.append(
                {
                    "validacao": label,
                    "severidade": severity,
                    "codigo": getattr(item, "code", ""),
                    "linhas": ", ".join(map(str, getattr(item, "lines", []))),
                    "mensagem": getattr(item, "message", ""),
                }
            )
    return pd.DataFrame(rows)


def species_issues_df(report: object) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for severity, attr in [("BLOQUEIO", "blocks"), ("AVISO", "warnings")]:
        for item in getattr(report, attr, []):
            rows.append(
                {
                    "severidade": severity,
                    "codigo": getattr(item, "code", ""),
                    "linha": getattr(item, "row", ""),
                    "coluna": getattr(item, "column", ""),
                    "mensagem": getattr(item, "message", ""),
                }
            )
    return pd.DataFrame(rows)


def pick_col(df: pd.DataFrame, names: list[str]) -> str | None:
    wanted = {norm(name) for name in names}
    for col in df.columns:
        if norm(col) in wanted:
            return str(col)
    return None


def col_values(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype=object)
    return df[col]


def key(row: pd.Series) -> tuple[str, str, str, str]:
    return (
        norm(row.get("Campanha")),
        norm(row.get("Ponto")),
        norm(row.get("Metodo_de_Captura")),
        norm(row.get("Tipo_de_Amostragem")),
    )


def key_exact(row: pd.Series) -> tuple[str, str, str, str]:
    return (
        clean(row.get("Campanha")),
        clean(row.get("Ponto")),
        clean(row.get("Metodo_de_Captura")),
        clean(row.get("Tipo_de_Amostragem")),
    )


def read_sheet(xls: pd.ExcelFile, sheet: str, findings: list[dict[str, Any]], *, required: bool) -> pd.DataFrame:
    if sheet not in xls.sheet_names:
        severity = "BLOQUEIO" if required else "INFO"
        findings.append(
            issue(
                "Leitura da planilha",
                severity,
                "SHEET_NOT_FOUND",
                f"Aba '{sheet}' nao encontrada em {xls.io}.",
                sheet=sheet,
            )
        )
        return pd.DataFrame()
    return pd.read_excel(xls, sheet_name=sheet, dtype=str).dropna(how="all")


def load_external_tools(opyta_data_root: Path, skip_db: bool) -> tuple[dict[str, Any], str | None]:
    if skip_db:
        return {}, "Validadores externos e banco foram pulados por --skip-db."
    if str(opyta_data_root) not in sys.path:
        sys.path.insert(0, str(opyta_data_root))
    try:
        from core.engine import get_engine  # type: ignore
        from sqlalchemy import text  # type: ignore
        from validators.especies.pipeline import validate_especies_file  # type: ignore
        from validators.importacao.pipeline import validate_importacao_file  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        return {}, f"Ferramentas externas indisponiveis: {exc}"
    return {
        "get_engine": get_engine,
        "text": text,
        "validate_especies_file": validate_especies_file,
        "validate_importacao_file": validate_importacao_file,
    }, None


def query_database(tools: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, pd.DataFrame]:
    empty = {
        "species": pd.DataFrame(),
        "bacias": pd.DataFrame(),
        "biomas": pd.DataFrame(),
        "clients": pd.DataFrame(),
        "projects": pd.DataFrame(),
    }
    if not tools:
        return empty
    engine = tools["get_engine"]()
    text = tools["text"]
    try:
        with engine.connect() as conn:
            return {
                "species": pd.DataFrame(conn.execute(text("SELECT * FROM especies")).mappings().all()),
                "bacias": pd.DataFrame(conn.execute(text("SELECT * FROM bacias_hidrograficas")).mappings().all()),
                "biomas": pd.DataFrame(conn.execute(text("SELECT * FROM biomas")).mappings().all()),
                "clients": pd.DataFrame(conn.execute(text("SELECT * FROM clientes")).mappings().all()),
                "projects": pd.DataFrame(conn.execute(text("SELECT * FROM projetos")).mappings().all()),
            }
    except Exception as exc:  # pragma: no cover - environment dependent
        findings.append(
            issue(
                "Banco de dados",
                "AVISO",
                "DB_QUERY_FAILED",
                f"Nao foi possivel consultar tabelas de apoio: {exc}",
            )
        )
        return empty
    finally:
        engine.dispose()


def run_official_validators(
    args: argparse.Namespace,
    tools: dict[str, Any],
    df_especies: pd.DataFrame,
    findings: list[dict[str, Any]],
) -> tuple[object | None, object | None, object | None]:
    if not tools:
        findings.append(
            issue(
                "Validador Opyta_Data",
                "AVISO",
                "OFFICIAL_VALIDATORS_NOT_RUN",
                "Validadores oficiais nao foram executados nesta rodada.",
                suggestion="Executar sem --skip-db e conferir --opyta-data-root quando for validar a versao final.",
            )
        )
        return None, None, None

    validate_importacao_file = tools["validate_importacao_file"]
    validate_especies_file = tools["validate_especies_file"]
    species_report = None
    import_report_isolated = None
    import_report_integrated = None
    engine = None

    try:
        engine = tools["get_engine"]()
        if args.species_file and not df_especies.empty:
            species_report = validate_especies_file(args.species_file, engine=engine)
            for item in getattr(species_report, "blocks", []):
                findings.append(
                    issue(
                        "Validador Opyta_Data especies",
                        "BLOQUEIO",
                        item.code,
                        item.message,
                        lines=[item.row] if getattr(item, "row", None) else [],
                        sheet=getattr(item, "column", "") or "",
                    )
                )
            for item in getattr(species_report, "warnings", []):
                severity = "BLOQUEIO" if item.code == "GENUS_MISMATCH" else "AVISO"
                suggestion = (
                    "Corrigir genero antes de cadastrar; cadastro de especies pode gravar valor errado."
                    if item.code == "GENUS_MISMATCH"
                    else "Revisar. Para ictiofauna, BMWP N.A. costuma ser aceitavel, mas precisa ser consciente."
                )
                findings.append(
                    issue(
                        "Validador Opyta_Data especies",
                        severity,
                        item.code,
                        item.message,
                        lines=[item.row] if getattr(item, "row", None) else [],
                        sheet=getattr(item, "column", "") or "",
                        suggestion=suggestion,
                    )
                )

            df_allowed = getattr(species_report, "cleaned_df", None)
            if df_allowed is not None and "Nome_Cientifico" in df_allowed.columns:
                allowed_species = set(df_allowed["Nome_Cientifico"].dropna().astype(str).str.strip())
            else:
                allowed_species = set(df_especies["Nome_Cientifico"].dropna().astype(str).str.strip())

            import_report_isolated = validate_importacao_file(
                args.import_file,
                group=GROUP,
                engine=engine,
                strict_unknown_species=True,
            )
            import_report_integrated = validate_importacao_file(
                args.import_file,
                group=GROUP,
                engine=engine,
                allowed_species=allowed_species,
                strict_unknown_species=True,
            )
            primary_report = import_report_integrated
            primary_label = "Validador Opyta_Data importacao integrada"
        else:
            primary_report = validate_importacao_file(
                args.import_file,
                group=GROUP,
                engine=engine,
                strict_unknown_species=True,
            )
            import_report_isolated = primary_report
            primary_label = "Validador Opyta_Data importacao"

        for item in getattr(primary_report, "blocks", []):
            findings.append(issue(primary_label, "BLOQUEIO", item.code, item.message, lines=item.lines))
        for item in getattr(primary_report, "warnings", []):
            findings.append(issue(primary_label, "AVISO", item.code, item.message, lines=item.lines))
        for item in getattr(primary_report, "infos", []):
            findings.append(issue(primary_label, "INFO", item.code, item.message, lines=item.lines))
        findings.append(
            issue(
                "Validador Opyta_Data",
                "INFO",
                "OFFICIAL_VALIDATORS_RUN",
                "Validadores oficiais de Opyta_Data executados como fonte primaria da pre-validacao.",
            )
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        findings.append(issue("Validador Opyta_Data", "AVISO", "OFFICIAL_VALIDATORS_FAILED", str(exc)))
    finally:
        if engine is not None:
            engine.dispose()

    if not args.species_file and df_especies.empty:
        findings.append(
            issue(
                "Validador Opyta_Data especies",
                "INFO",
                "SPECIES_FILE_NOT_PROVIDED",
                "Cadastro de especies nao informado; validacao integrada sera limitada.",
            )
        )
    elif not args.species_file:
        findings.append(
            issue(
                "Validador Opyta_Data especies",
                "INFO",
                "EMBEDDED_SPECIES_CATALOG_DETECTED",
                "Cadastro de especies detectado na planilha de importacao; validacao oficial embutida foi usada.",
            )
        )

    return species_report, import_report_isolated, import_report_integrated


def add_expected_count_checks(args: argparse.Namespace, summary: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    if args.expected_campaigns is not None and summary["campanhas_pontos"] != args.expected_campaigns:
        findings.append(
            issue(
                "Premissas do projeto",
                "AVISO",
                "EXPECTED_CAMPAIGN_COUNT_MISMATCH",
                f"Esperadas {args.expected_campaigns} campanhas, encontradas {summary['campanhas_pontos']}.",
            )
        )
    elif args.expected_campaigns is not None:
        findings.append(
            issue(
                "Premissas do projeto",
                "INFO",
                "EXPECTED_CAMPAIGN_COUNT_OK",
                f"Quantidade de campanhas confere: {summary['campanhas_pontos']}.",
            )
        )

    for field, expected, code_base, label in [
        ("linhas_resultados", args.expected_result_lines, "RESULT_LINE_COUNT", "linhas em Resultados_Ictiofauna"),
        ("especies_resultados", args.expected_species, "SPECIES_COUNT", "especies nos resultados"),
    ]:
        if expected is None:
            continue
        observed = int(summary[field])
        tolerance = max(int(round(expected * args.expected_tolerance_pct / 100.0)), 1)
        lo = expected - tolerance
        hi = expected + tolerance
        if observed < lo or observed > hi:
            findings.append(
                issue(
                    "Premissas do projeto",
                    "AVISO",
                    f"{code_base}_OUTSIDE_EXPECTED_RANGE",
                    f"Esperado aproximadamente {expected} {label} (+/- {tolerance}); encontrado {observed}.",
                )
            )
        else:
            findings.append(
                issue(
                    "Premissas do projeto",
                    "INFO",
                    f"{code_base}_WITHIN_EXPECTED_RANGE",
                    f"{label.capitalize()} dentro da faixa esperada: {observed}.",
            )
        )


def add_coordinate_reference_checks(
    args: argparse.Namespace,
    sheets: dict[str, pd.DataFrame],
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, pd.DataFrame]:
    if not args.coordinate_reference:
        summary["validacao_coordenadas_referencia"] = "nao_configurada"
        return {}

    reference_path = Path(args.coordinate_reference)
    if not reference_path.exists():
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "COORDINATE_REFERENCE_NOT_FOUND",
                f"Arquivo de referencia de coordenadas nao encontrado: {reference_path}",
                sheet="Pontos_e_Campanhas",
            )
        )
        summary["validacao_coordenadas_referencia"] = "arquivo_nao_encontrado"
        return {}

    df_pontos = sheets["Pontos_e_Campanhas"]
    required = {"Ponto", "Latitude", "Longitude"}
    missing = sorted(required - set(df_pontos.columns))
    if missing:
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "COORDINATE_REFERENCE_REQUIRED_COLUMNS_MISSING",
                f"Colunas ausentes para comparar coordenadas oficiais: {', '.join(missing)}.",
                sheet="Pontos_e_Campanhas",
            )
        )
        summary["validacao_coordenadas_referencia"] = "colunas_ausentes"
        return {}

    ref = read_kml_point_coordinates(reference_path)
    if ref.empty:
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "COORDINATE_REFERENCE_EMPTY",
                f"Nenhum ponto foi lido da referencia de coordenadas: {reference_path}",
                sheet="Pontos_e_Campanhas",
            )
        )
        summary["validacao_coordenadas_referencia"] = "referencia_vazia"
        return {}

    tolerance_m = float(args.coordinate_tolerance_m)
    comp = df_pontos.copy()
    comp["linha_excel"] = comp.index + 2
    comp["Ponto_padrao"] = comp["Ponto"].map(standardize_point_name)
    comp["Latitude_planilha"] = comp["Latitude"].map(to_float)
    comp["Longitude_planilha"] = comp["Longitude"].map(to_float)
    comp = comp.merge(ref, left_on="Ponto_padrao", right_on="Ponto", how="left", suffixes=("", "_ref_merge"))

    distances: list[float | None] = []
    statuses: list[str] = []
    for _, row in comp.iterrows():
        lat = row.get("Latitude_planilha")
        lon = row.get("Longitude_planilha")
        lat_ref = row.get("Latitude_ref")
        lon_ref = row.get("Longitude_ref")
        if pd.isna(row.get("Latitude_ref")) or pd.isna(row.get("Longitude_ref")):
            distances.append(None)
            statuses.append("ponto_sem_referencia")
        elif lat is None or lon is None or math.isnan(float(lat)) or math.isnan(float(lon)):
            distances.append(None)
            statuses.append("coordenada_planilha_invalida")
        else:
            distance_m = haversine_km(float(lat), float(lon), float(lat_ref), float(lon_ref)) * 1000
            distances.append(distance_m)
            statuses.append("ok" if distance_m <= tolerance_m else "divergente")
    comp["distancia_m"] = distances
    comp["status_coordenada"] = statuses

    observed_points = set(comp["Ponto_padrao"].dropna().astype(str))
    reference_points = set(ref["Ponto"].dropna().astype(str))
    missing_in_reference = sorted(observed_points - reference_points)
    missing_in_sheet = sorted(reference_points - observed_points)
    mismatches = comp[comp["status_coordenada"].isin(["divergente", "ponto_sem_referencia", "coordenada_planilha_invalida"])].copy()

    summary["arquivo_referencia_coordenadas"] = str(reference_path)
    summary["tolerancia_coordenadas_m"] = tolerance_m
    summary["linhas_coordenadas_divergentes"] = int(len(mismatches))
    summary["pontos_sem_referencia_coordenadas"] = int(len(missing_in_reference))
    summary["pontos_referencia_ausentes_planilha"] = int(len(missing_in_sheet))
    summary["validacao_coordenadas_referencia"] = "ok" if mismatches.empty and not missing_in_reference else "bloqueio"

    if missing_in_reference:
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "COORDINATE_REFERENCE_POINTS_MISSING",
                f"Pontos da planilha ausentes no KMZ/KML de referencia: {', '.join(missing_in_reference)}.",
                sheet="Pontos_e_Campanhas",
            )
        )
    if not mismatches.empty:
        max_dist = pd.to_numeric(mismatches["distancia_m"], errors="coerce").max()
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "COORDINATE_REFERENCE_MISMATCH",
                f"{len(mismatches)} linha(s) de coordenadas divergem da referencia oficial acima de {tolerance_m:g} m. Distancia maxima: {max_dist:.1f} m.",
                sheet="Pontos_e_Campanhas",
                suggestion="Corrigir Latitude/Longitude na planilha ou atualizar a fonte oficial antes de migrar.",
            )
        )
    if missing_in_sheet:
        findings.append(
            issue(
                "Validacao complementar",
                "AVISO",
                "COORDINATE_REFERENCE_EXTRA_POINTS",
                f"Pontos existentes no KMZ/KML, mas ausentes na planilha: {', '.join(missing_in_sheet)}.",
                sheet="Pontos_e_Campanhas",
            )
        )
    if mismatches.empty and not missing_in_reference:
        findings.append(
            issue(
                "Validacao complementar",
                "INFO",
                "COORDINATE_REFERENCE_OK",
                f"Todas as coordenadas conferem com a referencia oficial dentro de {tolerance_m:g} m.",
                sheet="Pontos_e_Campanhas",
            )
        )

    comparison_cols = [
        "linha_excel",
        "Campanha",
        "Ponto_padrao",
        "Latitude_planilha",
        "Longitude_planilha",
        "Latitude_ref",
        "Longitude_ref",
        "distancia_m",
        "status_coordenada",
        "fonte_coordenada",
    ]
    available_cols = [col for col in comparison_cols if col in comp.columns]
    return {
        "coordinate_ref_points": ref,
        "coordinate_ref_compare": comp[available_cols],
        "coordinate_ref_mismatches": mismatches[available_cols] if not mismatches.empty else pd.DataFrame(columns=available_cols),
    }


def add_complementary_checks(
    sheets: dict[str, pd.DataFrame],
    species_sheets: dict[str, pd.DataFrame],
    db: dict[str, pd.DataFrame],
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, pd.DataFrame]:
    df_pontos = sheets["Pontos_e_Campanhas"]
    df_esforco = sheets["Metadados_Esforco"]
    df_resultados = sheets["Resultados_Ictiofauna"]
    df_especies = species_sheets.get("Especies", pd.DataFrame())
    df_endemismo = species_sheets.get("Endemismo_Especies", pd.DataFrame())

    missing_required_rows: list[dict[str, Any]] = []
    required_checks = {
        "Capa_Projeto": (sheets["Capa_Projeto"], ["Codigo_Opyta", "Nome_do_Projeto", "Cliente"]),
        "Pontos_e_Campanhas": (
            df_pontos,
            ["Ponto", "Campanha", "Data", "Latitude", "Longitude", "Bacia_Hidrografica"],
        ),
        "Metadados_Esforco": (
            df_esforco,
            ["Ponto", "Campanha", "Grupo_Biologico", "Metodo_de_Captura", "Unidade_Esforco", "Tipo_de_Amostragem"],
        ),
        "Resultados_Ictiofauna": (
            df_resultados,
            ["Ponto", "Campanha", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico", "Numero_de_Individuos"],
        ),
    }
    if not df_especies.empty:
        required_checks["Especies"] = (
            df_especies,
            ["Nome_Cientifico", "Grupo_Biologico", "Reino", "Filo", "Classe", "Ordem", "Familia", "Genero"],
        )
    if not df_endemismo.empty:
        required_checks["Endemismo_Especies"] = (
            df_endemismo,
            ["Nome_Cientifico", "Tipo_de_Regiao", "Nome_da_Regiao"],
        )

    for sheet, (df, cols) in required_checks.items():
        for col in cols:
            if col not in df.columns:
                missing_required_rows.append({"aba": sheet, "coluna": col, "linhas": "todas", "n": len(df), "tipo": "COLUNA_AUSENTE"})
                continue
            mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
            if sheet == "Metadados_Esforco" and col in {"Unidade_Esforco"} and "Tipo_de_Amostragem" in df.columns:
                is_qualitative = df["Tipo_de_Amostragem"].astype(str).map(norm).str.contains("qualit", na=False)
                mask = mask & ~is_qualitative
            if mask.any():
                missing_required_rows.append(
                    {
                        "aba": sheet,
                        "coluna": col,
                        "linhas": ", ".join(str(int(i + 2)) for i in df[mask].index[:20]),
                        "n": int(mask.sum()),
                        "tipo": "VALOR_AUSENTE",
                    }
                )
    findings.append(
        issue(
            "Validacao complementar",
            "BLOQUEIO" if missing_required_rows else "INFO",
            "MISSING_REQUIRED_FIELDS" if missing_required_rows else "REQUIRED_FIELDS_OK",
            f"Campos obrigatorios ausentes: {len(missing_required_rows)} ocorrencia(s)."
            if missing_required_rows
            else "Nao foram encontrados campos obrigatorios ausentes nas colunas conferidas.",
        )
    )

    numeric_rows: list[dict[str, Any]] = []
    for sheet, df, cols in [
        ("Pontos_e_Campanhas", df_pontos, ["Latitude", "Longitude"]),
        ("Metadados_Esforco", df_esforco, ["Esforco"]),
        ("Resultados_Ictiofauna", df_resultados, ["Esforco_Amostral", "Numero_de_Individuos", "CT_cm", "CP_cm", "PC_g"]),
    ]:
        for col in cols:
            if col not in df.columns:
                continue
            for idx, value in df[col].items():
                if sheet == "Metadados_Esforco" and col == "Esforco" and "Tipo_de_Amostragem" in df.columns:
                    tipo = norm(df.at[idx, "Tipo_de_Amostragem"])
                    if "qualit" in tipo and clean(value) == "":
                        continue
                parsed = to_float(value)
                if isinstance(parsed, float) and math.isnan(parsed):
                    numeric_rows.append({"aba": sheet, "coluna": col, "linha_excel": int(idx + 2), "valor": value, "problema": "nao numerico"})
                elif parsed is not None and col not in {"Latitude", "Longitude"} and parsed < 0:
                    numeric_rows.append({"aba": sheet, "coluna": col, "linha_excel": int(idx + 2), "valor": value, "problema": "valor negativo"})
    findings.append(
        issue(
            "Validacao complementar",
            "BLOQUEIO" if numeric_rows else "INFO",
            "INVALID_NUMERIC_VALUES" if numeric_rows else "NUMERIC_VALUES_OK",
            f"Valores numericos invalidos/negativos: {len(numeric_rows)}." if numeric_rows else "Coordenadas, esforcos, abundancia, comprimentos e peso avaliados como numericos validos.",
        )
    )

    date_rows: list[dict[str, Any]] = []
    campaign_patterns = [
        (re.compile(r"^C(\d{3})-(\d{4})-(\d{2})-(SC|CH)$"), 2, 3),
        (re.compile(r"^BG_(?:BAG|STP)_C\d+_(\d{4})(\d{2})$", re.IGNORECASE), 1, 2),
        (
            re.compile(
                r"^[A-Z0-9]+_AH\d{4}_(\d{4})(\d{2})(?:_R\d+)?$",
                re.IGNORECASE,
            ),
            1,
            2,
        ),
    ]
    if not df_pontos.empty and {"Campanha", "Data"}.issubset(df_pontos.columns):
        for idx, row in df_pontos.iterrows():
            camp = clean(row.get("Campanha"))
            match_info = next(
                ((m, year_group, month_group) for pattern, year_group, month_group in campaign_patterns if (m := pattern.match(camp))),
                None,
            )
            parsed = pd.to_datetime(row.get("Data"), errors="coerce")
            problems: list[str] = []
            if not match_info:
                problems.append("formato do codigo")
            if pd.isna(parsed):
                problems.append("data invalida")
            elif match_info:
                match, year_group, month_group = match_info
                expected_year = int(match.group(year_group))
                expected_month = int(match.group(month_group))
                if parsed.year != expected_year or parsed.month != expected_month:
                    problems.append(f"data {parsed.date()} nao bate com {expected_year}-{expected_month:02d}")
            if problems:
                date_rows.append(
                    {
                        "linha_excel": int(idx + 2),
                        "Ponto": row.get("Ponto"),
                        "Campanha": camp,
                        "Data": row.get("Data"),
                        "problema": "; ".join(problems),
                    }
                )
    findings.append(
        issue(
            "Validacao complementar",
            "BLOQUEIO" if date_rows else "INFO",
            "CAMPAIGN_DATE_MISMATCH" if date_rows else "CAMPAIGN_DATE_OK",
            f"{len(date_rows)} ponto(s) com inconsistencia entre data e campanha." if date_rows else "Codigos de campanha e datas estao consistentes quanto a ano/mes e formato reconhecido.",
        )
    )

    point_ref_exact = set(col_values(df_pontos, "Ponto").dropna().astype(str).str.strip())
    point_ref_norm = {norm(x) for x in point_ref_exact}
    if "Ponto" in df_resultados.columns and point_ref_exact:
        case_lines = [
            int(idx + 2)
            for idx, value in df_resultados["Ponto"].dropna().astype(str).str.strip().items()
            if value not in point_ref_exact and norm(value) in point_ref_norm
        ]
        if case_lines:
            findings.append(
                issue(
                    "Validacao complementar",
                    "BLOQUEIO",
                    "POINT_CASE_MISMATCH_EXACT_IMPORT",
                    f"{len(case_lines)} resultado(s) usam ponto com grafia diferente de Pontos_e_Campanhas.",
                    lines=case_lines[:50],
                    sheet="Resultados_Ictiofauna",
                    suggestion="Padronizar Ponto de forma identica em Pontos_e_Campanhas, Metadados_Esforco e Resultados_Ictiofauna.",
                )
            )

    effort_keys_norm = {key(row) for _, row in df_esforco.iterrows() if all(key(row))}
    effort_keys_exact = {key_exact(row) for _, row in df_esforco.iterrows() if all(key_exact(row))}
    missing_effort_records: list[dict[str, Any]] = []
    exact_mismatch_records: list[dict[str, Any]] = []
    for idx, row in df_resultados.iterrows():
        if key(row) not in effort_keys_norm:
            missing_effort_records.append(
                {
                    "linha_excel": int(idx + 2),
                    "Campanha": row.get("Campanha"),
                    "Ponto": row.get("Ponto"),
                    "Metodo_de_Captura": row.get("Metodo_de_Captura"),
                    "Tipo_de_Amostragem": row.get("Tipo_de_Amostragem"),
                    "Nome_Cientifico": row.get("Nome_Cientifico"),
                }
            )
        elif key_exact(row) not in effort_keys_exact:
            exact_mismatch_records.append(
                {
                    "linha_excel": int(idx + 2),
                    "Campanha": row.get("Campanha"),
                    "Ponto": row.get("Ponto"),
                    "Metodo_de_Captura": row.get("Metodo_de_Captura"),
                    "Tipo_de_Amostragem": row.get("Tipo_de_Amostragem"),
                    "Nome_Cientifico": row.get("Nome_Cientifico"),
                }
            )
    if missing_effort_records:
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "MISSING_EFFORT_METADATA_NORMALIZED",
                f"{len(missing_effort_records)} resultado(s) nao possuem linha correspondente em Metadados_Esforco por campanha+ponto+metodo+tipo.",
                lines=[r["linha_excel"] for r in missing_effort_records[:50]],
                sheet="Resultados_Ictiofauna/Metadados_Esforco",
                suggestion="Adicionar esforco correspondente ou corrigir campanha/ponto/metodo/tipo.",
            )
        )
    elif exact_mismatch_records:
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "EFFORT_KEY_EXACT_IMPORT_MISMATCH",
                f"{len(exact_mismatch_records)} resultado(s) batem so apos normalizacao; o migrador pode exigir chave exata.",
                lines=[r["linha_excel"] for r in exact_mismatch_records[:50]],
                sheet="Resultados_Ictiofauna/Metadados_Esforco",
                suggestion="Padronizar maiusculas, acentos e espacos nas chaves.",
            )
        )

    effort_map = {key(row): clean(row.get("Esforco")) for _, row in df_esforco.iterrows()}
    effort_value_mismatch: list[dict[str, Any]] = []
    for idx, row in df_resultados.iterrows():
        meta_effort = effort_map.get(key(row))
        result_effort = clean(row.get("Esforco_Amostral"))
        if meta_effort is not None and result_effort and meta_effort != result_effort:
            effort_value_mismatch.append(
                {
                    "linha_excel": int(idx + 2),
                    "Campanha": row.get("Campanha"),
                    "Ponto": row.get("Ponto"),
                    "Metodo_de_Captura": row.get("Metodo_de_Captura"),
                    "Nome_Cientifico": row.get("Nome_Cientifico"),
                    "Esforco_Amostral_resultados": result_effort,
                    "Esforco_metadados": meta_effort,
                }
            )
    if effort_value_mismatch:
        findings.append(
            issue(
                "Validacao complementar",
                "AVISO",
                "RESULT_EFFORT_VALUE_DIFFERS_FROM_METADATA",
                f"{len(effort_value_mismatch)} resultado(s) possuem Esforco_Amostral diferente do Esforco em Metadados_Esforco.",
                lines=[r["linha_excel"] for r in effort_value_mismatch[:50]],
                sheet="Resultados_Ictiofauna/Metadados_Esforco",
                suggestion="Definir valor correto e padronizar nas duas abas.",
            )
        )

    species_results = {
        norm(v): clean(v)
        for v in col_values(df_resultados, "Nome_Cientifico").dropna()
        if clean(v) and clean(v).upper() != "N.A."
    }
    species_catalog = (
        {norm(v) for v in col_values(df_especies, "Nome_Cientifico").dropna() if clean(v)}
        if not df_especies.empty
        else set()
    )
    species_db = (
        {norm(v) for v in col_values(db["species"], "nome_cientifico").dropna() if clean(v)}
        if not db["species"].empty
        else set()
    )
    missing_in_catalog = (
        sorted(
            original
            for species_key, original in species_results.items()
            if species_key not in species_catalog and species_key not in species_db
        )
        if species_catalog
        else []
    )
    if species_catalog:
        reference_label = "cadastro fornecido ou banco" if species_db else "cadastro fornecido"
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO" if missing_in_catalog else "INFO",
                "RESULT_SPECIES_NOT_IN_CATALOG" if missing_in_catalog else "RESULT_SPECIES_CATALOG_MATCH",
                f"Especies dos resultados ausentes no {reference_label}: {missing_in_catalog}"
                if missing_in_catalog
                else f"Todas as {len(species_results)} especies dos resultados estao presentes no {reference_label}.",
            )
        )

    species_dups = pd.DataFrame()
    if not df_especies.empty and "Nome_Cientifico" in df_especies.columns:
        species_dups = df_especies[df_especies.duplicated(subset=["Nome_Cientifico"], keep=False)]
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO" if not species_dups.empty else "INFO",
                "SPECIES_CATALOG_DUPLICATES" if not species_dups.empty else "SPECIES_CATALOG_NO_DUPLICATES",
                f"{len(species_dups)} linhas duplicadas na aba Especies." if not species_dups.empty else "Nao ha duplicidades intra-planilha em Nome_Cientifico.",
                lines=[int(i + 2) for i in species_dups.index[:50]],
            )
        )

    exact_dups = df_resultados[df_resultados.duplicated(keep=False)] if not df_resultados.empty else pd.DataFrame()
    findings.append(
        issue(
            "Validacao complementar",
            "AVISO" if not exact_dups.empty else "INFO",
            "EXACT_RESULT_DUPLICATES" if not exact_dups.empty else "NO_EXACT_RESULT_DUPLICATES",
            f"{len(exact_dups)} resultados sao duplicatas exatas; revisar se representam individuos/lotes distintos antes de deduplicar." if not exact_dups.empty else "Nao ha linhas exatamente duplicadas na aba Resultados_Ictiofauna.",
        )
    )

    group_cols = ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]
    present_group_cols = [col for col in group_cols if col in df_resultados.columns]
    grouped_dupes = pd.DataFrame()
    if len(present_group_cols) == len(group_cols):
        grouped_results = df_resultados.groupby(group_cols, dropna=False).size().reset_index(name="n_linhas")
        grouped_dupes = grouped_results[grouped_results["n_linhas"] > 1].copy()
        if not grouped_dupes.empty:
            findings.append(
                issue(
                    "Validacao complementar",
                    "AVISO",
                    "RESULT_GROUPS_WILL_BE_AGGREGATED",
                    f"{len(grouped_dupes)} grupos campanha+ponto+metodo+tipo+especie possuem multiplas linhas. O script de migracao pode agregar Numero_de_Individuos por soma e biometria por media.",
                    suggestion="Confirmar se as multiplas linhas representam individuos/lotes distintos.",
                )
            )

    endemism_region_col = pick_col(
        df_endemismo,
        ["Nome_da_Regiao", "Nome da Regiao", "Bacia Hidrografica", "Bacia_Hidrografica"],
    )
    if not df_especies.empty and not df_endemismo.empty and "Origem" in df_especies.columns and "Nome_Cientifico" in df_endemismo.columns:
        endemic_catalog = set(
            df_especies.loc[
                df_especies["Origem"].astype(str).map(norm).str.contains("endem", na=False),
                "Nome_Cientifico",
            ]
            .dropna()
            .astype(str)
            .str.strip()
        )
        endemism_species = set(df_endemismo["Nome_Cientifico"].dropna().astype(str).str.strip())
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO" if endemic_catalog != endemism_species else "INFO",
                "ENDEMISM_SPECIES_SET_MISMATCH" if endemic_catalog != endemism_species else "ENDEMISM_SPECIES_SET_OK",
                f"Especies endemicas em Origem ({sorted(endemic_catalog)}) diferem da aba Endemismo ({sorted(endemism_species)})."
                if endemic_catalog != endemism_species
                else f"As {len(endemic_catalog)} especies marcadas como endemicas em Origem aparecem na aba Endemismo_Especies.",
            )
        )

    if not df_endemismo.empty and "Tipo_de_Regiao" in df_endemismo.columns:
        valid_types = {"Bacia Hidrografica", "Bioma"}
        type_norm_to_raw = {norm(v): v for v in valid_types}
        invalid_end_type = df_endemismo[~df_endemismo["Tipo_de_Regiao"].astype(str).map(norm).isin(type_norm_to_raw.keys())]
        if not invalid_end_type.empty:
            findings.append(
                issue(
                    "Validacao complementar",
                    "BLOQUEIO",
                    "INVALID_ENDEMISM_REGION_TYPE",
                    "Tipo_de_Regiao usa valor nao aceito pelo script de cadastro. Use 'Bacia Hidrografica' ou 'Bioma'.",
                    lines=[int(i + 2) for i in invalid_end_type.index[:50]],
                    sheet="Endemismo_Especies",
                )
            )
    if not df_endemismo.empty and endemism_region_col != "Nome_da_Regiao":
        findings.append(
            issue(
                "Validacao complementar",
                "BLOQUEIO",
                "INVALID_ENDEMISM_REGION_COLUMN",
                f"A coluna de regiao da aba Endemismo_Especies esta como '{endemism_region_col or 'ausente'}', mas o script de cadastro espera exatamente 'Nome_da_Regiao'.",
                sheet="Endemismo_Especies",
                suggestion="Renomear a coluna para Nome_da_Regiao.",
            )
        )

    if not df_endemismo.empty and endemism_region_col:
        end_regions = set(df_endemismo[endemism_region_col].dropna().astype(str).str.strip())
        db_bacia_names = set(db["bacias"].get("nome_bacia", pd.Series(dtype=str)).dropna().astype(str)) if not db["bacias"].empty else set()
        db_bioma_names = set(db["biomas"].get("nome_bioma", pd.Series(dtype=str)).dropna().astype(str)) if not db["biomas"].empty else set()
        if db_bacia_names or db_bioma_names:
            missing_regions = sorted([v for v in end_regions if v not in db_bacia_names and v not in db_bioma_names])
            findings.append(
                issue(
                    "Validacao complementar",
                    "AVISO" if missing_regions else "INFO",
                    "ENDEMISM_REGION_NOT_IN_DB" if missing_regions else "ENDEMISM_REGION_DB_OK",
                    f"Regioes de endemismo nao encontradas em bacias/biomas: {missing_regions}."
                    if missing_regions
                    else f"Regioes de endemismo existem no banco: {sorted(end_regions)}.",
                )
            )

    if not db["clients"].empty and "nome_empresa" in db["clients"].columns:
        client_exists = norm(summary.get("cliente")) in set(db["clients"]["nome_empresa"].map(norm))
        findings.append(
            issue(
                "Banco de dados",
                "INFO" if client_exists else "AVISO",
                "CLIENT_DB_STATUS",
                f"Cliente '{summary.get('cliente')}' {'ja existe' if client_exists else 'nao foi encontrado'} no banco.",
            )
        )
    if not db["projects"].empty and "codigo_interno_opyta" in db["projects"].columns:
        project_exists = norm(summary.get("codigo_opyta")) in set(db["projects"]["codigo_interno_opyta"].map(norm))
        findings.append(
            issue(
                "Banco de dados",
                "INFO" if project_exists else "AVISO",
                "PROJECT_DB_STATUS",
                f"Projeto Codigo_Opyta '{summary.get('codigo_opyta')}' {'ja existe' if project_exists else 'nao existe ainda'} no banco.",
            )
        )

    species_status_rows: list[dict[str, Any]] = []
    upsert_risk_rows: list[dict[str, Any]] = []
    if not df_especies.empty and not db["species"].empty and "nome_cientifico" in db["species"].columns:
        db_species = db["species"]
        db_index = {norm(row["nome_cientifico"]): row for _, row in db_species.iterrows() if pd.notna(row.get("nome_cientifico"))}
        mapping = {
            "Nome_Cientifico": "nome_cientifico",
            "Nome_Popular": "nome_popular",
            "Grupo_Biologico": "grupo_biologico",
            "Reino": "reino",
            "Filo": "filo",
            "Classe": "classe",
            "Ordem": "ordem",
            "Familia": "familia",
            "Genero": "genero",
            "Autor_e_Ano": "autor_e_ano",
            "Status_Ameaca_Nacional": "status_ameaca_nacional",
            "Status_Ameaca_Global": "status_ameaca_global",
            "Origem": "origem",
            "Habito_Alimentar": "habito_alimentar",
            "Estrategia_Reprodutiva": "estrategia_reprodutiva",
            "Valor_Economico": "valor_economico",
            "Observacoes": "observacoes",
            "BMWP_Score": "bmwp_score",
            "bmwp_score": "bmwp_score",
            "Status_Ameaca_Estadual": "status_estadual",
        }
        for idx, row in df_especies.iterrows():
            nc = clean(row.get("Nome_Cientifico"))
            dbrow = db_index.get(norm(nc))
            species_status_rows.append(
                {
                    "linha_excel": int(idx + 2),
                    "Nome_Cientifico": nc,
                    "status_banco": "existente" if dbrow is not None else "nova",
                    "id_especie": None if dbrow is None else dbrow.get("id_especie"),
                    "grupo_banco": None if dbrow is None else dbrow.get("grupo_biologico"),
                }
            )
            if dbrow is None:
                continue
            for xl_col, db_col in mapping.items():
                if xl_col not in df_especies.columns or db_col not in dbrow.index:
                    continue
                plan = row.get(xl_col)
                plan_norm = None if pd.isna(plan) or clean(plan).upper() in {"N.A.", "NA", ""} else clean(plan)
                dbval = dbrow.get(db_col)
                db_norm = None if pd.isna(dbval) or clean(dbval) == "" else clean(dbval)
                if db_norm != plan_norm:
                    risk = "RISCO_ALTO" if db_norm is not None and plan_norm is None else "DIFERENCA"
                    upsert_risk_rows.append(
                        {
                            "linha_excel": int(idx + 2),
                            "Nome_Cientifico": nc,
                            "campo_planilha": xl_col,
                            "campo_banco": db_col,
                            "valor_planilha_pos_NA": plan_norm,
                            "valor_banco_atual": db_norm,
                            "tipo": risk,
                        }
                    )
        if upsert_risk_rows:
            risky = sorted({r["Nome_Cientifico"] for r in upsert_risk_rows if r["tipo"] == "RISCO_ALTO"})
            findings.append(
                issue(
                    "Validacao complementar",
                    "BLOQUEIO",
                    "SPECIES_UPSERT_CAN_OVERWRITE_EXISTING_DATA",
                    f"A planilha possui especies ja existentes no banco com diferencas. Especies com risco alto: {risky}.",
                    sheet="Especies",
                    suggestion="Cadastrar apenas especies novas ou ajustar o upsert para nao atualizar campos nulos em especies existentes.",
                )
            )

    methods_eff = sorted(col_values(df_esforco, "Metodo_de_Captura").dropna().astype(str).unique())
    methods_res = sorted(col_values(df_resultados, "Metodo_de_Captura").dropna().astype(str).unique())
    if methods_eff or methods_res:
        severity = "AVISO" if methods_eff != methods_res else "INFO"
        findings.append(
            issue(
                "Validacao complementar",
                severity,
                "METHOD_NAMING_STANDARDIZATION",
                f"Metodos em Metadados_Esforco: {methods_eff}; em Resultados_Ictiofauna: {methods_res}.",
                suggestion="Se houver nomes equivalentes, padronizar de forma identica nas duas abas antes de migrar.",
            )
        )

    campaign_points = pd.DataFrame()
    effort_profile = pd.DataFrame()
    results_profile = pd.DataFrame()
    if {"Campanha", "Ponto"}.issubset(df_pontos.columns):
        campaign_points = df_pontos.groupby("Campanha").agg(
            pontos_n=("Ponto", "count"),
            pontos=("Ponto", lambda x: "; ".join(sorted(x.astype(str).unique()))),
            datas=("Data", lambda x: "; ".join(sorted(x.astype(str).unique())) if "Data" in df_pontos.columns else ""),
        ).reset_index()
    if {"Campanha", "Metodo_de_Captura", "Ponto", "Esforco"}.issubset(df_esforco.columns):
        effort_profile = df_esforco.groupby(["Campanha", "Metodo_de_Captura"]).agg(
            linhas=("Ponto", "count"),
            pontos=("Ponto", lambda x: "; ".join(sorted(x.astype(str).unique()))),
            esforcos=("Esforco", lambda x: "; ".join(sorted(x.astype(str).unique()))),
        ).reset_index()
    if {"Campanha", "Metodo_de_Captura", "Ponto", "Nome_Cientifico"}.issubset(df_resultados.columns):
        results_profile = df_resultados.groupby(["Campanha", "Metodo_de_Captura"]).agg(
            linhas=("Ponto", "count"),
            pontos=("Ponto", lambda x: "; ".join(sorted(x.astype(str).unique()))),
            especies=("Nome_Cientifico", lambda x: "; ".join(sorted(x.astype(str).unique()))),
        ).reset_index()

    return {
        "missing_required_rows": pd.DataFrame(missing_required_rows),
        "numeric_rows": pd.DataFrame(numeric_rows),
        "date_rows": pd.DataFrame(date_rows),
        "missing_effort_records": pd.DataFrame(missing_effort_records),
        "exact_mismatch_records": pd.DataFrame(exact_mismatch_records),
        "effort_value_mismatch": pd.DataFrame(effort_value_mismatch),
        "exact_dups": exact_dups,
        "grouped_dupes": grouped_dupes,
        "species_status_rows": pd.DataFrame(species_status_rows),
        "upsert_risk_rows": pd.DataFrame(upsert_risk_rows),
        "species_dups": species_dups,
        "campaign_points": campaign_points,
        "effort_profile": effort_profile,
        "results_profile": results_profile,
    }


def write_outputs(
    args: argparse.Namespace,
    output_dir: Path,
    stamp: str,
    sheets: dict[str, pd.DataFrame],
    species_sheets: dict[str, pd.DataFrame],
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
    tables: dict[str, pd.DataFrame],
    species_report: object | None,
    import_report_isolated: object | None,
    import_report_integrated: object | None,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = args.project_slug
    md_out = output_dir / f"validacao_{slug}_ictiofauna_{stamp}.md"
    xlsx_out = output_dir / f"validacao_{slug}_ictiofauna_{stamp}.xlsx"
    json_out = output_dir / f"validacao_{slug}_ictiofauna_{stamp}.json"

    findings_df = pd.DataFrame(findings)
    blockers = findings_df[findings_df["severidade"] == "BLOQUEIO"] if not findings_df.empty else pd.DataFrame()
    warnings = findings_df[findings_df["severidade"] == "AVISO"] if not findings_df.empty else pd.DataFrame()
    infos = findings_df[findings_df["severidade"] == "INFO"] if not findings_df.empty else pd.DataFrame()
    summary["bloqueios_relatorio_total"] = int(len(blockers))
    summary["avisos_relatorio_total"] = int(len(warnings))
    summary["infos_relatorio_total"] = int(len(infos))
    summary["validacao_pode_prosseguir"] = int(len(blockers)) == 0

    payload = {
        "summary": summary,
        "files": {"importacao": str(args.import_file), "cadastro_especies": str(args.species_file) if args.species_file else None},
        "findings": findings,
        "species_validation": None,
    }
    if species_report is not None:
        payload["species_validation"] = {
            "total_rows": getattr(species_report, "total_rows", None),
            "total_valid": getattr(species_report, "total_valid", None),
            "total_new": getattr(species_report, "total_new", None),
            "total_existing": getattr(species_report, "total_existing", None),
            "new_species": getattr(species_report, "new_species", []),
            "existing_species": getattr(species_report, "existing_species", []),
            "issues": species_issues_df(species_report).to_dict(orient="records"),
            "corrections": [asdict(c) for c in getattr(species_report, "corrections", [])],
        }
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="00_resumo", index=False)
        findings_df.to_excel(writer, sheet_name="01_achados", index=False)
        if import_report_isolated is not None:
            import_issues_df(import_report_isolated, "oficial_sem_cadastro_sep").to_excel(writer, sheet_name="02_validador_import", index=False)
        if import_report_integrated is not None:
            import_issues_df(import_report_integrated, "integrado_com_cadastro").to_excel(writer, sheet_name="03_validador_integr", index=False)
        if species_report is not None:
            species_issues_df(species_report).to_excel(writer, sheet_name="04_validador_especies", index=False)
            pd.DataFrame([asdict(c) for c in getattr(species_report, "corrections", [])]).to_excel(writer, sheet_name="05_correcoes_especies", index=False)
        for idx, (name, df) in enumerate(tables.items(), start=6):
            sheet_name = f"{idx:02d}_{name}"[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        for sheet, df in sheets.items():
            df.head(5000).to_excel(writer, sheet_name=f"raw_{sheet}"[:31], index=False)
        for sheet, df in species_sheets.items():
            df.head(5000).to_excel(writer, sheet_name=f"raw_{sheet}"[:31], index=False)

    title_project = summary.get("nome_projeto") or args.project_slug.replace("_", " ").title()
    verdict = (
        "**Nao importar ainda.**"
        if len(blockers)
        else "**Pode seguir para ensaio de migracao**, mantendo revisao dos avisos."
    )
    lines = [
        f"# Validacao pre-importacao - {title_project} Ictiofauna",
        "",
        f"Data: {date.today().isoformat()}",
        "",
        "## Arquivos avaliados",
        f"- Resultados: `{args.import_file}`",
        f"- Cadastro de especies: `{args.species_file}`" if args.species_file else "- Cadastro de especies: nao informado",
        "",
        "## Veredito",
        "",
        f"{verdict} Foram encontrados **{len(blockers)} bloqueios** e **{len(warnings)} avisos**.",
        "",
        "## Resumo dos dados",
        "",
    ]
    for field in [
        "codigo_opyta",
        "nome_projeto",
        "cliente",
        "campanhas_pontos",
        "pontos_unicos",
        "linhas_pontos",
        "linhas_esforco",
        "linhas_resultados",
        "linhas_cadastro_especies",
        "linhas_endemismo",
        "especies_resultados",
        "especies_cadastro",
    ]:
        lines.append(f"- {field}: {summary.get(field)}")

    lines.extend(["", "## Bloqueios", ""])
    if blockers.empty:
        lines.append("- Nenhum bloqueio encontrado.")
    else:
        for _, row in blockers.iterrows():
            loc = f" | linhas: {row['linhas']}" if str(row["linhas"]).strip() else ""
            sheet = f" | aba: {row['aba']}" if str(row["aba"]).strip() else ""
            lines.append(f"- **{row['codigo']}**{sheet}{loc}: {row['mensagem']}")
            if str(row["sugestao"]).strip():
                lines.append(f"  - Ajuste: {row['sugestao']}")

    lines.extend(["", "## Avisos", ""])
    if warnings.empty:
        lines.append("- Nenhum aviso encontrado.")
    else:
        for _, row in warnings.iterrows():
            loc = f" | linhas: {row['linhas']}" if str(row["linhas"]).strip() else ""
            sheet = f" | aba: {row['aba']}" if str(row["aba"]).strip() else ""
            lines.append(f"- **{row['codigo']}**{sheet}{loc}: {row['mensagem']}")
            if str(row["sugestao"]).strip():
                lines.append(f"  - Ajuste: {row['sugestao']}")

    lines.extend(["", "## Cadastro de especies", ""])
    if species_report is not None:
        lines.append(
            f"- Total: {getattr(species_report, 'total_rows', '-')}; novas no banco: {getattr(species_report, 'total_new', '-')}; ja existentes: {getattr(species_report, 'total_existing', '-')}."
        )
        new_species = getattr(species_report, "new_species", [])
        existing_species = getattr(species_report, "existing_species", [])
        lines.append(f"- Novas: {', '.join(new_species) if new_species else '-'}.")
        lines.append(f"- Existentes: {', '.join(existing_species) if existing_species else '-'}.")
        lines.append("- Atencao: para especies existentes, preferir cadastro incremental para nao sobrescrever metadados do banco.")
    elif summary.get("linhas_cadastro_especies", 0):
        lines.append(f"- Cadastro lido com {summary.get('linhas_cadastro_especies')} linhas.")
        lines.append("- Validador oficial de especies nao retornou relatorio nesta execucao.")
    else:
        lines.append("- Cadastro de especies ainda nao informado.")

    lines.extend(
        [
            "",
            "## Arquivos gerados",
            f"- Excel detalhado: `{xlsx_out}`",
            f"- JSON: `{json_out}`",
        ]
    )
    md_out.write_text("\n".join(lines), encoding="utf-8")

    return {"md": str(md_out), "xlsx": str(xlsx_out), "json": str(json_out)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an Ictiofauna migration workbook before import.")
    parser.add_argument("--import-file", type=Path, required=True, help="Migration workbook with Capa/Pontos/Esforco/Resultados sheets.")
    parser.add_argument("--species-file", type=Path, default=None, help="Optional species cadastro workbook.")
    parser.add_argument("--project-slug", type=str, default=None, help="Output slug, for example porto_estrela.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory. Defaults to outputs/validacoes/<project-slug>.")
    parser.add_argument("--opyta-data-root", type=Path, default=DEFAULT_OPTYA_DATA_ROOT, help="Path to Opyta_Data for official validators.")
    parser.add_argument("--skip-db", action="store_true", help="Skip official validators and DB checks.")
    parser.add_argument("--expected-campaigns", type=int, default=None, help="Expected campaign count.")
    parser.add_argument("--expected-result-lines", type=int, default=None, help="Approximate expected number of result rows.")
    parser.add_argument("--expected-species", type=int, default=None, help="Approximate expected number of species in results.")
    parser.add_argument("--expected-tolerance-pct", type=float, default=10.0, help="Tolerance for approximate counts, in percent.")
    parser.add_argument("--coordinate-reference", type=Path, default=None, help="Optional KMZ/KML reference used to validate point coordinates before migration.")
    parser.add_argument("--coordinate-tolerance-m", type=float, default=50.0, help="Maximum accepted distance from the coordinate reference, in meters.")
    parser.add_argument("--stamp", type=str, default=None, help="Date stamp for outputs, default YYYYMMDD.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.import_file.exists():
        raise FileNotFoundError(args.import_file)
    if args.species_file and not args.species_file.exists():
        raise FileNotFoundError(args.species_file)

    if args.project_slug is None:
        args.project_slug = slugify(args.import_file.stem)
    else:
        args.project_slug = slugify(args.project_slug)
    output_dir = args.output_dir or (DEFAULT_OUTPUT_ROOT / args.project_slug)
    stamp = args.stamp or datetime.now().strftime("%Y%m%d")

    findings: list[dict[str, Any]] = []
    import_xls = pd.ExcelFile(args.import_file)
    sheets = {sheet: read_sheet(import_xls, sheet, findings, required=True) for sheet in IMPORT_SHEETS}

    species_sheets: dict[str, pd.DataFrame] = {}
    if args.species_file:
        species_xls = pd.ExcelFile(args.species_file)
        species_sheets = {sheet: read_sheet(species_xls, sheet, findings, required=(sheet == "Especies")) for sheet in SPECIES_SHEETS}
    else:
        species_sheets = {
            sheet: read_sheet(import_xls, sheet, findings, required=False)
            for sheet in SPECIES_SHEETS
            if sheet in import_xls.sheet_names
        }

    df_capa = sheets["Capa_Projeto"]
    df_pontos = sheets["Pontos_e_Campanhas"]
    df_esforco = sheets["Metadados_Esforco"]
    df_resultados = sheets["Resultados_Ictiofauna"]
    df_especies = species_sheets.get("Especies", pd.DataFrame())
    df_endemismo = species_sheets.get("Endemismo_Especies", pd.DataFrame())

    capa0 = df_capa.iloc[0] if not df_capa.empty else pd.Series(dtype=object)
    summary = {
        "arquivo_resultados": str(args.import_file),
        "arquivo_cadastro_especies": str(args.species_file) if args.species_file else None,
        "codigo_opyta": clean(capa0.get("Codigo_Opyta")),
        "nome_projeto": clean(capa0.get("Nome_do_Projeto")),
        "cliente": clean(capa0.get("Cliente")),
        "campanhas_pontos": int(col_values(df_pontos, "Campanha").nunique()) if not df_pontos.empty else 0,
        "pontos_unicos": int(col_values(df_pontos, "Ponto").nunique()) if not df_pontos.empty else 0,
        "linhas_pontos": int(len(df_pontos)),
        "linhas_esforco": int(len(df_esforco)),
        "linhas_resultados": int(len(df_resultados)),
        "linhas_cadastro_especies": int(len(df_especies)),
        "linhas_endemismo": int(len(df_endemismo)),
        "especies_resultados": int(col_values(df_resultados, "Nome_Cientifico").dropna().astype(str).str.strip().replace({"N.A.": ""}).replace({"": pd.NA}).dropna().nunique())
        if not df_resultados.empty
        else 0,
        "especies_cadastro": int(col_values(df_especies, "Nome_Cientifico").nunique()) if not df_especies.empty else 0,
    }

    add_expected_count_checks(args, summary, findings)
    tools, tool_warning = load_external_tools(args.opyta_data_root, args.skip_db)
    if tool_warning:
        findings.append(issue("Ambiente", "AVISO", "EXTERNAL_TOOLS_STATUS", tool_warning))
    db = query_database(tools, findings)
    species_report, import_report_isolated, import_report_integrated = run_official_validators(args, tools, df_especies, findings)
    tables = add_complementary_checks(sheets, species_sheets, db, summary, findings)
    tables.update(add_coordinate_reference_checks(args, sheets, summary, findings))

    outputs = write_outputs(
        args,
        output_dir,
        stamp,
        sheets,
        species_sheets,
        summary,
        findings,
        tables,
        species_report,
        import_report_isolated,
        import_report_integrated,
    )
    result = {
        **outputs,
        "bloqueios": summary["bloqueios_relatorio_total"],
        "avisos": summary["avisos_relatorio_total"],
        "pode_prosseguir": summary["validacao_pode_prosseguir"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if summary["bloqueios_relatorio_total"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
