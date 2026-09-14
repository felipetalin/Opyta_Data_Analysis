#!/usr/bin/env python
"""One-command validation for results and species registration workbooks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill


REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
PROFILE_ROOT = Path(__file__).resolve().parent / "profiles"
DEFAULT_OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
OUTPUT_FOLDER_NAME = "VALIDACAO_FINAL"
FINAL_RESULTS_NAME = "Resultados_FINAL.xlsx"
FINAL_SPECIES_NAME = "Cadastro_Especies_FINAL.xlsx"
SUMMARY_NAME = "RESUMO_VALIDACAO.xlsx"
MANIFEST_NAME = "manifesto_validacao.json"
SPECIES_FIELDS = (
    "Nome_Cientifico",
    "Nome_Popular",
    "Grupo_Biologico",
    "Reino",
    "Filo",
    "Classe",
    "Ordem",
    "Familia",
    "Genero",
    "bmwp_score",
    "Autor_e_Ano",
    "Status_Ameaca_Estadual",
    "Status_Ameaca_Nacional",
    "Status_Ameaca_Global",
    "Origem",
    "Habito_Alimentar",
    "Estrategia_Reprodutiva",
    "Valor_Economico",
    "Observacoes",
    "Cinegetica",
    "Xerimbabo",
)
SPECIES_IDENTITY_FIELDS = {"Nome_Cientifico", "Grupo_Biologico"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a migration folder and produce a simple final package."
    )
    parser.add_argument("--pasta", required=True, type=Path, help="Folder containing migration workbooks.")
    parser.add_argument("--grupo", required=True, help="Validation profile, e.g. zooplancton or ictiofauna.")
    parser.add_argument("--resultados", type=Path, default=None, help="Optional explicit results workbook.")
    parser.add_argument("--especies", type=Path, default=None, help="Optional explicit species workbook.")
    parser.add_argument("--saida", type=Path, default=None, help="Output folder. Default: <pasta>/VALIDACAO_FINAL.")
    parser.add_argument("--opyta-data-root", type=Path, default=DEFAULT_OPYTA_DATA_ROOT)
    parser.add_argument("--skip-db", action="store_true", help="Skip database checks.")
    return parser.parse_args()


def normalize(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.casefold().split())


def load_profile(group: str) -> dict[str, Any]:
    profile_path = PROFILE_ROOT / f"{normalize(group).replace(' ', '_')}.json"
    if not profile_path.exists():
        available = ", ".join(path.stem for path in sorted(PROFILE_ROOT.glob("*.json")))
        raise ValueError(f"Perfil nao encontrado: {group}. Disponiveis: {available}")
    return json.loads(profile_path.read_text(encoding="utf-8"))


def workbook_sheets(path: Path) -> list[str]:
    try:
        return pd.ExcelFile(path).sheet_names
    except Exception:
        return []


def species_matches_profile(path: Path, profile: dict[str, Any]) -> bool:
    if profile["species_sheet"] not in workbook_sheets(path):
        return False
    try:
        frame = pd.read_excel(path, sheet_name=profile["species_sheet"], usecols=["Grupo_Biologico"])
    except Exception:
        return True
    expected = {normalize(value) for value in profile.get("species_group_aliases", [])}
    values = {normalize(value) for value in frame["Grupo_Biologico"].dropna().unique()}
    return not values or bool(values & expected)


def discover_results(folder: Path, profile: dict[str, Any], explicit: Path | None) -> Path:
    if explicit:
        path = explicit.resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    candidates = [
        path for path in folder.glob("*.xlsx")
        if profile["result_sheet"] in workbook_sheets(path)
    ]
    if len(candidates) != 1:
        names = ", ".join(path.name for path in candidates) or "nenhum"
        raise ValueError(f"Esperado um arquivo de resultados para {profile['label']}; encontrados: {names}")
    return candidates[0]


def species_score(path: Path) -> tuple[int, float]:
    name = normalize(path.stem)
    if "final conferencia" in name:
        score = 3
    elif "final" in name:
        score = 2
    else:
        score = 1
    return score, path.stat().st_mtime


def discover_species(folder: Path, profile: dict[str, Any], explicit: Path | None) -> Path:
    if explicit:
        path = explicit.resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    candidates = [
        path for path in folder.glob("*.xlsx")
        if species_matches_profile(path, profile)
    ]
    if not candidates:
        raise ValueError(f"Nenhum cadastro de especies encontrado para {profile['label']}")
    return sorted(candidates, key=species_score, reverse=True)[0]


def run_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def prepare_missing_species_values(
    source: Path,
    output: Path,
    species_sheet: str,
    missing_value: str,
) -> int:
    shutil.copy2(source, output)
    workbook = load_workbook(output)
    if species_sheet not in workbook.sheetnames:
        raise ValueError(f"Aba ausente no cadastro: {species_sheet}")
    worksheet = workbook[species_sheet]
    headers = {
        str(cell.value).strip(): cell.column
        for cell in worksheet[1]
        if cell.value is not None
    }
    filled = 0
    for field in SPECIES_FIELDS:
        if field in SPECIES_IDENTITY_FIELDS or field not in headers:
            continue
        column = headers[field]
        for row_number in range(2, worksheet.max_row + 1):
            cell = worksheet.cell(row_number, column)
            if cell.value is None or not str(cell.value).strip():
                cell.value = missing_value
                filled += 1
    workbook.save(output)
    return filled


def prepare_species(
    source: Path,
    output: Path,
    lastro_dir: Path,
    profile: dict[str, Any],
    opyta_data_root: Path,
) -> list[str]:
    sheets = workbook_sheets(source)
    if "O_QUE_MUDOU" in sheets:
        shutil.copy2(source, output)
        return ["cadastro final existente reutilizado"]

    if profile["taxonomy_profile"] not in {"zooplankton", "fitoplankton"}:
        if str(opyta_data_root) not in sys.path:
            sys.path.insert(0, str(opyta_data_root))
        from validators.especies import validate_especies_file

        validation_source = source
        missing_filled = 0
        missing_value = profile.get("rules", {}).get("missing_value")
        if missing_value:
            validation_source = lastro_dir / "cadastro_preparado_com_na.xlsx"
            missing_filled = prepare_missing_species_values(
                source,
                validation_source,
                profile["species_sheet"],
                str(missing_value),
            )

        report = validate_especies_file(validation_source, engine=None)
        if not report.can_proceed or report.cleaned_df is None:
            shutil.copy2(source, output)
            return ["cadastro profissional preservado; normalizacao oficial bloqueada"]

        workbook = Workbook()
        species_sheet = workbook.active
        species_sheet.title = profile["species_sheet"]
        cleaned = report.cleaned_df.copy()
        species_sheet.append([str(column) for column in cleaned.columns])
        for values in cleaned.itertuples(index=False, name=None):
            species_sheet.append(list(values))
        style_table(species_sheet, "245B78")

        changed = workbook.create_sheet("O_QUE_MUDOU")
        changed.append(["Nome informado", "Nome final", "Regra aplicada", "Detalhe"])
        name_corrections = 0
        for correction in report.corrections:
            changed.append(
                [
                    str(correction.original),
                    str(correction.corrected),
                    "NORMALIZACAO_OFICIAL",
                    f"linha {correction.row}; coluna {correction.column}; {correction.reason}",
                ]
            )
            if str(correction.column) == "Nome_Cientifico":
                name_corrections += 1
        if not report.corrections:
            changed.append(["-", "-", "SEM_ALTERACOES", "Nenhuma normalizacao necessaria."])
        style_table(changed, "2F6B4F")
        workbook.save(output)
        return [
            "cadastro normalizado pelo validador oficial",
            f"campos vazios registrados como {missing_value}: {missing_filled}",
            f"correcoes de nome cientifico registradas: {name_corrections}",
            "taxonomia especializada externa ainda nao conectada para este perfil",
        ]

    validated = lastro_dir / "cadastro_taxonomico_detalhado.xlsx"
    manifest = lastro_dir / "cadastro_taxonomico_manifesto.json"
    validator = REPO_ROOT / "scripts" / "validation" / "species" / "validar_cadastro_especies.py"
    professional_rules = REPO_ROOT / "scripts" / "validation" / "species" / (
        "aplicar_regras_fitoplancton.py"
        if profile["taxonomy_profile"] == "fitoplankton" else
        "aplicar_regras_profissionais.py"
    )
    run_command(
        [
            sys.executable,
            str(validator),
            "--input",
            str(source),
            "--sheet",
            profile["species_sheet"],
            "--profile",
            profile["taxonomy_profile"],
            "--delay",
            "0",
            "--output",
            str(validated),
            "--manifest",
            str(manifest),
        ]
    )
    run_command(
        [
            sys.executable,
            str(professional_rules),
            "--input",
            str(validated),
            "--output",
            str(output),
        ]
    )
    return [
        "cadastro consultado em tres bases e regras profissionais aplicadas",
        f"fontes: {' | '.join(profile.get('taxonomy_sources', []))}",
        "campos preenchidos somente com consenso; conflitos preservam o valor profissional",
    ]


def apply_species_overrides(
    species_file: Path,
    overrides_file: Path,
    species_sheet: str,
) -> list[str]:
    if not overrides_file.exists():
        return []
    payload = json.loads(overrides_file.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not records:
        return []

    workbook = load_workbook(species_file)
    worksheet = workbook[species_sheet]
    headers = {
        str(cell.value).strip(): cell.column
        for cell in worksheet[1]
        if cell.value is not None
    }
    name_column = headers["Nome_Cientifico"]
    changed_sheet = workbook["O_QUE_MUDOU"]
    for row_number in range(changed_sheet.max_row, 1, -1):
        if str(changed_sheet.cell(row_number, 3).value or "") == "INFORMACAO_PROFISSIONAL_FORNECIDA":
            changed_sheet.delete_rows(row_number)

    overridden_names: set[str] = set()
    updated_rows = 0
    source_label = str(payload.get("source", "informado pelo profissional"))
    for record in records:
        scientific_name = str(record.get("Nome_Cientifico", "")).strip()
        if not scientific_name:
            continue
        name_key = normalize(scientific_name)
        overridden_names.add(name_key)
        applied_fields = [
            field for field in SPECIES_FIELDS
            if field != "Nome_Cientifico" and field in record and field in headers
        ]
        for row_number in range(2, worksheet.max_row + 1):
            current_name = worksheet.cell(row_number, name_column).value
            if normalize(current_name) != name_key:
                continue
            for field in applied_fields:
                worksheet.cell(row_number, headers[field]).value = record[field]
            updated_rows += 1
        changed_sheet.append(
            [
                scientific_name,
                scientific_name,
                "INFORMACAO_PROFISSIONAL_FORNECIDA",
                f"campos confirmados: {', '.join(applied_fields)}; fonte: {source_label}",
            ]
        )

    if "PENDENCIAS_TAXONOMICAS" in workbook.sheetnames:
        pending = workbook["PENDENCIAS_TAXONOMICAS"]
        pending_headers = {
            str(cell.value).strip(): cell.column
            for cell in pending[1]
            if cell.value is not None
        }
        pending_name_column = pending_headers.get("Nome informado")
        if pending_name_column:
            for row_number in range(pending.max_row, 1, -1):
                if normalize(pending.cell(row_number, pending_name_column).value) in overridden_names:
                    pending.delete_rows(row_number)
            if pending.max_row == 1:
                pending.append(["-", "APROVADO", "N.A.", "Pendencias resolvidas pelo profissional."])

    style_table(changed_sheet, "2F6B4F")
    workbook.save(species_file)
    return [
        f"ajustes profissionais reaplicados: {len(overridden_names)} especies",
        f"linhas de cadastro atualizadas: {updated_rows}",
    ]


def read_name_mapping(species_file: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    sheets = workbook_sheets(species_file)
    if "O_QUE_MUDOU" not in sheets:
        return {}, []
    changes = pd.read_excel(species_file, sheet_name="O_QUE_MUDOU", keep_default_na=False)
    mapping: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    for _, row in changes.iterrows():
        original = str(row.get("Nome informado", ""))
        final = str(row.get("Nome final", ""))
        rule = str(row.get("Regra aplicada", "")).strip()
        detail = str(row.get("Detalhe", "")).strip()
        is_name_change = rule != "NORMALIZACAO_OFICIAL" or "coluna Nome_Cientifico" in detail
        if original and final and original != final and is_name_change:
            mapping[normalize(original)] = final.strip()
        if is_name_change:
            rows.append(
                {
                    "tipo": "cadastro_especies",
                    "original": original.strip(),
                    "final": final.strip(),
                    "regra": rule,
                    "detalhe": detail,
                }
            )
    return mapping, rows


def prepare_results(
    source: Path,
    output: Path,
    result_sheet: str,
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    shutil.copy2(source, output)
    workbook = load_workbook(output)
    if result_sheet not in workbook.sheetnames:
        raise ValueError(f"Aba ausente em resultados: {result_sheet}")
    worksheet = workbook[result_sheet]
    headers = {str(cell.value).strip(): cell.column for cell in worksheet[1] if cell.value is not None}
    name_column = headers.get("Nome_Cientifico")
    if not name_column:
        raise ValueError(f"Coluna Nome_Cientifico ausente em {result_sheet}")

    counts: Counter[tuple[str, str]] = Counter()
    for row_number in range(2, worksheet.max_row + 1):
        cell = worksheet.cell(row_number, name_column)
        original = "" if cell.value is None else str(cell.value)
        final = mapping.get(normalize(original))
        if final and original != final:
            cell.value = final
            counts[(original, final)] += 1
    workbook.save(output)
    return [
        {"original": original, "final": final, "linhas_alteradas": count}
        for (original, final), count in sorted(counts.items())
    ]


def normalize_explicit_effort(output: Path, result_sheet: str) -> list[dict[str, Any]]:
    """Split explicit values such as '100 litros' without inferring missing data."""
    workbook = load_workbook(output)
    targets = (
        ("Metadados_Esforco", "Esforco", "Unidade_Esforco"),
        (result_sheet, "Esforco_Amostral", "Unidade_Esforco"),
    )
    pattern = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s+([^\d]+?)\s*$")
    changes: Counter[tuple[str, str, str]] = Counter()

    for sheet_name, effort_field, unit_field in targets:
        if sheet_name not in workbook.sheetnames:
            continue
        worksheet = workbook[sheet_name]
        headers = {
            str(cell.value).strip(): cell.column
            for cell in worksheet[1]
            if cell.value is not None
        }
        effort_column = headers.get(effort_field)
        unit_column = headers.get(unit_field)
        if not effort_column or not unit_column:
            continue

        for row_number in range(2, worksheet.max_row + 1):
            effort_cell = worksheet.cell(row_number, effort_column)
            original = "" if effort_cell.value is None else str(effort_cell.value).strip()
            match = pattern.fullmatch(original)
            if not match:
                continue
            numeric_text, unit = match.groups()
            numeric_value = float(numeric_text.replace(",", "."))
            if numeric_value.is_integer():
                numeric_value = int(numeric_value)
            effort_cell.value = numeric_value
            worksheet.cell(row_number, unit_column).value = unit.strip().lower()
            changes[(sheet_name, original, unit.strip().lower())] += 1

    workbook.save(output)
    return [
        {
            "aba": sheet_name,
            "original": original,
            "unidade_final": unit,
            "linhas_alteradas": count,
        }
        for (sheet_name, original, unit), count in sorted(changes.items())
    ]


def reconcile_database(
    species_file: Path,
    lastro_dir: Path,
    opyta_data_root: Path,
    skip_db: bool,
) -> dict[str, Any]:
    if skip_db or "FONTES_CONSULTADAS" not in workbook_sheets(species_file):
        return {}
    output_json = lastro_dir / "conciliacao_banco.json"
    script = REPO_ROOT / "scripts" / "validation" / "species" / "conciliar_cadastro_banco.py"
    run_command(
        [
            sys.executable,
            str(script),
            "--input",
            str(species_file),
            "--output-json",
            str(output_json),
            "--opyta-data-root",
            str(opyta_data_root),
        ]
    )
    return json.loads(output_json.read_text(encoding="utf-8"))


def append_reconciliation_summary(output: Path, reconciliation: dict[str, Any]) -> None:
    if not reconciliation:
        return
    workbook = load_workbook(output)
    worksheet = workbook["RESUMO"]
    counts = reconciliation.get("counts", {})
    worksheet.append(
        [
            "Conciliação com banco",
            " | ".join(f"{key}: {value}" for key, value in sorted(counts.items())),
        ]
    )
    worksheet.append(["Conflitos com banco", reconciliation.get("not_ready", 0)])
    style_table(worksheet, "245B78")
    workbook.save(output)


def load_external_validators(opyta_data_root: Path, skip_db: bool) -> tuple[Any, Any, Any, str]:
    if str(opyta_data_root) not in sys.path:
        sys.path.insert(0, str(opyta_data_root))
    from validators.especies import validate_especies_file
    from validators.importacao import validate_importacao_file

    engine = None
    db_status = "pulado por --skip-db"
    if not skip_db:
        try:
            from core.engine import get_engine

            engine = get_engine()
            db_status = "conectado"
        except Exception as exc:
            db_status = f"indisponivel: {exc}"
    return validate_importacao_file, validate_especies_file, engine, db_status


def issue_dict(issue: Any, source: str) -> dict[str, Any]:
    lines = getattr(issue, "lines", None)
    row = getattr(issue, "row", None)
    if not lines and row is not None:
        lines = [row]
    return {
        "fonte": source,
        "severidade": str(getattr(issue, "severity", "warning")),
        "codigo": str(getattr(issue, "code", "")),
        "aba": str(getattr(issue, "sheet", "") or ""),
        "linhas": ", ".join(str(value) for value in (lines or [])),
        "mensagem": str(getattr(issue, "message", "")),
    }


def species_names(path: Path, sheet: str) -> set[str]:
    frame = pd.read_excel(path, sheet_name=sheet, usecols=["Nome_Cientifico"])
    return {
        normalize(value) for value in frame["Nome_Cientifico"].dropna()
        if normalize(value) not in {"", "n.a.", "na"}
    }


def result_names(path: Path, sheet: str) -> set[str]:
    frame = pd.read_excel(path, sheet_name=sheet, usecols=["Nome_Cientifico"])
    return {
        normalize(value) for value in frame["Nome_Cientifico"].dropna()
        if normalize(value) not in {"", "n.a.", "na"}
    }


def validate_package(
    results_file: Path,
    species_file: Path,
    profile: dict[str, Any],
    opyta_data_root: Path,
    skip_db: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    validate_results, validate_species, engine, db_status = load_external_validators(
        opyta_data_root, skip_db
    )
    species_report = validate_species(species_file, engine=engine)
    allowed_species = {
        str(value).strip()
        for value in pd.read_excel(
            species_file,
            sheet_name=profile["species_sheet"],
            usecols=["Nome_Cientifico"],
        )["Nome_Cientifico"].dropna()
        if str(value).strip()
    }
    results_report = validate_results(
        results_file,
        group=profile["label"],
        engine=engine,
        allowed_species=allowed_species,
        strict_unknown_species=True,
    )

    issues = [issue_dict(issue, "resultados") for issue in results_report.issues]
    issues.extend(issue_dict(issue, "cadastro_especies") for issue in species_report.issues)
    severity_overrides = profile.get("severity_overrides", {})
    for issue in issues:
        if issue["codigo"] in severity_overrides:
            issue["severidade"] = severity_overrides[issue["codigo"]]

    result_set = result_names(results_file, profile["result_sheet"])
    species_set = species_names(species_file, profile["species_sheet"])
    missing = sorted(result_set - species_set)
    if missing:
        issues.append(
            {
                "fonte": "reconciliacao",
                "severidade": "block",
                "codigo": "RESULTADO_SEM_CADASTRO",
                "aba": profile["result_sheet"],
                "linhas": "",
                "mensagem": "Nomes presentes nos resultados e ausentes no cadastro final: " + ", ".join(missing),
            }
        )

    metrics = {
        "campanhas": int(getattr(results_report, "total_campanhas", 0)),
        "pontos": int(getattr(results_report, "total_pontos", 0)),
        "registros": int(getattr(results_report, "total_registros", 0)),
        "especies_resultados": len(result_set),
        "especies_cadastro": len(species_set),
        "especies_sem_cadastro": len(missing),
        "cadastro_linhas": int(getattr(species_report, "total_rows", 0)),
        "cadastro_validas": int(getattr(species_report, "total_valid", 0)),
    }
    return issues, metrics, db_status


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def style_table(worksheet: Any, header_color: str) -> None:
    fill = PatternFill("solid", fgColor=header_color)
    for cell in worksheet[1]:
        cell.fill = fill
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.row_dimensions[1].height = 30
    for column in worksheet.columns:
        letter = column[0].column_letter
        width = min(max(len(str(cell.value or "")) for cell in column) + 2, 70)
        worksheet.column_dimensions[letter].width = max(width, 14)
    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)


def write_summary(
    output: Path,
    status: str,
    profile: dict[str, Any],
    source_results: Path,
    source_species: Path,
    metrics: dict[str, Any],
    issues: list[dict[str, Any]],
    species_changes: list[dict[str, str]],
    result_changes: list[dict[str, Any]],
    db_status: str,
) -> None:
    blocks = [issue for issue in issues if issue["severidade"] == "block"]
    warnings = [issue for issue in issues if issue["severidade"] == "warning"]
    next_step = (
        "Corrigir apenas a aba PENDENCIAS e executar novamente."
        if blocks else
        "Pacote pronto para aprovacao antes da migracao."
    )

    workbook = Workbook()
    summary = workbook.active
    summary.title = "RESUMO"
    summary.append(["Item", "Resultado"])
    rows = [
        ("STATUS", status),
        ("Grupo", profile["label"]),
        ("Resultados de entrada", source_results.name),
        ("Cadastro de entrada", source_species.name),
        ("Registros", metrics["registros"]),
        ("Campanhas", metrics["campanhas"]),
        ("Pontos", metrics["pontos"]),
        ("Especies nos resultados", metrics["especies_resultados"]),
        ("Especies no cadastro", metrics["especies_cadastro"]),
        ("Nomes corrigidos nos resultados", sum(change["linhas_alteradas"] for change in result_changes)),
        ("Bloqueios", len(blocks)),
        ("Avisos tecnicos", len(warnings)),
        ("Banco de dados", db_status),
        ("Fontes taxonomicas", ", ".join(profile.get("taxonomy_sources", []))),
        ("Proximo passo", next_step),
    ]
    for row in rows:
        summary.append(row)
    style_table(summary, "245B78")
    summary.column_dimensions["A"].width = 34
    summary.column_dimensions["B"].width = 80
    status_fill = "C6EFCE" if not blocks else "FFC7CE"
    summary["B2"].fill = PatternFill("solid", fgColor=status_fill)
    summary["B2"].font = Font(bold=True)

    pending = workbook.create_sheet("PENDENCIAS")
    pending.append(["Fonte", "Codigo", "Aba", "Linhas", "Mensagem"])
    if blocks:
        for issue in blocks:
            pending.append(
                [issue["fonte"], issue["codigo"], issue["aba"], issue["linhas"], issue["mensagem"]]
            )
    else:
        pending.append(["-", "SEM_PENDENCIAS", "-", "-", "Nenhuma pendencia bloqueante."])
    style_table(pending, "A33A3A" if blocks else "2F6B4F")

    changed = workbook.create_sheet("O_QUE_MUDOU")
    changed.append(["Tipo", "Original", "Final", "Regra", "Detalhe/Quantidade"])
    for row in species_changes:
        changed.append([row["tipo"], row["original"], row["final"], row["regra"], row["detalhe"]])
    for row in result_changes:
        changed.append(
            ["resultados", row["original"], row["final"], "nome sincronizado com cadastro", row["linhas_alteradas"]]
        )
    if len(species_changes) + len(result_changes) == 0:
        changed.append(["-", "-", "-", "SEM_ALTERACOES", "Nenhuma alteracao automatica."])
    style_table(changed, "2F6B4F")
    workbook.save(output)


def main() -> int:
    args = parse_args()
    folder = args.pasta.resolve()
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    profile = load_profile(args.grupo)
    source_results = discover_results(folder, profile, args.resultados)
    source_species = discover_species(folder, profile, args.especies)

    output_dir = (args.saida or (folder / OUTPUT_FOLDER_NAME / profile["id"])).resolve()
    lastro_dir = output_dir / "_lastro"
    output_dir.mkdir(parents=True, exist_ok=True)
    lastro_dir.mkdir(parents=True, exist_ok=True)
    final_results = output_dir / FINAL_RESULTS_NAME
    final_species = output_dir / FINAL_SPECIES_NAME
    summary_file = output_dir / SUMMARY_NAME
    manifest_file = lastro_dir / MANIFEST_NAME

    preparation_notes = prepare_species(
        source_species,
        final_species,
        lastro_dir,
        profile,
        args.opyta_data_root,
    )
    preparation_notes.extend(
        apply_species_overrides(
            final_species,
            lastro_dir / "ajustes_profissionais.json",
            profile["species_sheet"],
        )
    )
    mapping, species_changes = read_name_mapping(final_species)
    result_changes = prepare_results(source_results, final_results, profile["result_sheet"], mapping)
    effort_changes = normalize_explicit_effort(final_results, profile["result_sheet"])
    reconciliation = reconcile_database(
        final_species,
        lastro_dir,
        args.opyta_data_root,
        args.skip_db,
    )
    issues, metrics, db_status = validate_package(
        final_results,
        final_species,
        profile,
        args.opyta_data_root,
        args.skip_db,
    )
    blocks = [issue for issue in issues if issue["severidade"] == "block"]
    reconciliation_pending = int(reconciliation.get("not_ready", 0))
    if blocks or reconciliation_pending:
        status = "REVISAO_NECESSARIA"
    elif species_changes or result_changes:
        status = "PRONTO_COM_AJUSTES_AUTOMATICOS"
    else:
        status = "PRONTO"

    write_summary(
        summary_file,
        status,
        profile,
        source_results,
        source_species,
        metrics,
        issues,
        species_changes,
        result_changes,
        db_status,
    )
    append_reconciliation_summary(summary_file, reconciliation)

    manifest = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "profile": profile,
        "inputs": {
            "resultados": str(source_results),
            "cadastro_especies": str(source_species),
            "sha256_resultados": sha256(source_results),
            "sha256_cadastro_especies": sha256(source_species),
        },
        "outputs": {
            "resultados_final": str(final_results),
            "cadastro_especies_final": str(final_species),
            "resumo": str(summary_file),
            "sha256_resultados_final": sha256(final_results),
            "sha256_cadastro_especies_final": sha256(final_species),
        },
        "database_status": db_status,
        "preparation_notes": preparation_notes,
        "metrics": metrics,
        "result_name_changes": result_changes,
        "result_effort_changes": effort_changes,
        "database_reconciliation": reconciliation,
        "issues": issues,
    }
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    result = {
        "status": status,
        "pasta": str(output_dir),
        "resumo": str(summary_file),
        "resultados_final": str(final_results),
        "cadastro_especies_final": str(final_species),
        "bloqueios": len(blocks),
        "avisos": sum(1 for issue in issues if issue["severidade"] == "warning"),
        "conflitos_banco": reconciliation_pending,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if blocks else 0


if __name__ == "__main__":
    raise SystemExit(main())
