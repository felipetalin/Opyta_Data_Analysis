#!/usr/bin/env python
"""Validate species registration spreadsheets before database import."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import pandas as pd

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)

GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
GBIF_USAGE_URL = "https://api.gbif.org/v1/species/{usage_key}"
GBIF_VERNACULAR_URL = "https://api.gbif.org/v1/species/{usage_key}/vernacularNames"
WORMS_NAME_URL = "https://www.marinespecies.org/rest/AphiaRecordsByName/{name}"
DIATOMBASE_NAME_URL = (
    "https://www.diatombase.org/aphia.php?p=rest&__route__/"
    "AphiaRecordsByName/{name}?like=false&marine_only=false"
)
COL_DATASET_KEY = 315834
COL_SEARCH_URL = f"https://api.checklistbank.org/dataset/{COL_DATASET_KEY}/nameusage/search"
CTFB_TAXON_URL = "https://fauna.jbrj.gov.br/rest/v_taxon_data"
CTFB_HIERARCHY_URL = "https://fauna.jbrj.gov.br/rest/v_taxonomia_hierarquia"
USER_AGENT = "Opyta species registration validator"
NA_VALUE = "N.A."

CADASTRO_COLUMNS = [
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
]

NAME_CANDIDATES = [
    "scientific_name",
    "nome_cientifico",
    "nome científico",
    "taxon",
    "táxon",
    "species",
    "especie",
    "espécie",
]
FAMILY_CANDIDATES = ["family", "familia", "família"]
KINGDOM_CANDIDATES = ["kingdom", "reino"]


@dataclass(frozen=True)
class ColumnMap:
    name: str
    family: str | None
    kingdom: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a species registration spreadsheet against taxonomic sources."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input .xlsx, .xls or .csv file.")
    parser.add_argument("--sheet", default=0, help="Excel sheet name or index. Default: first sheet.")
    parser.add_argument("--output", type=Path, default=None, help="Validated output path.")
    parser.add_argument("--manifest", type=Path, default=None, help="JSON trace manifest path.")
    parser.add_argument("--name-column", default=None, help="Column containing the scientific name.")
    parser.add_argument("--family-column", default=None, help="Optional original family column.")
    parser.add_argument("--kingdom-column", default=None, help="Optional kingdom column.")
    parser.add_argument("--min-confidence", type=int, default=92, help="Minimum GBIF confidence for approval.")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between online API calls, in seconds.")
    parser.add_argument(
        "--vernacular-language",
        default="por",
        help="GBIF vernacular language code used for Nome_Popular. Default: por.",
    )
    parser.add_argument("--offline", action="store_true", help="Only check spreadsheet structure.")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for tests.")
    parser.add_argument("--strict-review", action="store_true", help="Return exit code 1 when review rows exist.")
    parser.add_argument(
        "--profile",
        choices=["gbif", "zooplankton", "fitoplankton"],
        default="gbif",
        help=(
            "Validation profile. zooplankton uses WoRMS, CTFB and GBIF; "
            "fitoplankton uses GBIF, Catalogue of Life and DiatomBase."
        ),
    )
    return parser.parse_args()


def _clean_header(value: str) -> str:
    return str(value).strip().lower()


def _find_column(columns: list[str], explicit: str | None, candidates: list[str]) -> str | None:
    if explicit:
        if explicit not in columns:
            raise ValueError(f"Column not found: {explicit}")
        return explicit
    lowered = {_clean_header(col): col for col in columns}
    for candidate in candidates:
        found = lowered.get(_clean_header(candidate))
        if found:
            return found
    return None


def detect_columns(df: pd.DataFrame, args: argparse.Namespace) -> ColumnMap:
    columns = [str(col) for col in df.columns]
    name = _find_column(columns, args.name_column, NAME_CANDIDATES)
    if not name:
        raise ValueError(
            "Scientific name column not detected. Use --name-column. "
            f"Candidates: {', '.join(NAME_CANDIDATES)}"
        )
    return ColumnMap(
        name=name,
        family=_find_column(columns, args.family_column, FAMILY_CANDIDATES),
        kingdom=_find_column(columns, args.kingdom_column, KINGDOM_CANDIDATES),
    )


def read_table(path: Path, sheet: str | int) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        parsed_sheet: str | int = int(sheet) if str(sheet).isdigit() else sheet
        return pd.read_excel(path, sheet_name=parsed_sheet)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {suffix}")


def write_table(
    df: pd.DataFrame,
    path: Path,
    input_path: Path | None = None,
    input_sheet: str | int = 0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        if input_path and input_path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
            workbook = pd.ExcelFile(input_path)
            parsed_sheet = int(input_sheet) if str(input_sheet).isdigit() else input_sheet
            target_name = workbook.sheet_names[parsed_sheet] if isinstance(parsed_sheet, int) else str(parsed_sheet)
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                for sheet_name in workbook.sheet_names:
                    sheet_df = df if sheet_name == target_name else pd.read_excel(input_path, sheet_name=sheet_name)
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            df.to_excel(path, index=False)
        return
    if suffix == ".csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return
    raise ValueError(f"Unsupported output format: {suffix}")


def _text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _gbif_match(name: str, kingdom: str | None) -> dict[str, Any]:
    params = {"name": name, "verbose": "true"}
    if kingdom:
        params["kingdom"] = kingdom
    url = f"{GBIF_MATCH_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _gbif_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _json_request(url: str) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
        return json.loads(body.decode("utf-8")) if body else []


def _gbif_usage(usage_key: Any) -> dict[str, Any]:
    if not usage_key:
        return {}
    return _gbif_json(GBIF_USAGE_URL.format(usage_key=usage_key))


def _gbif_vernacular_name(usage_key: Any, language: str) -> str:
    if not usage_key:
        return NA_VALUE
    data = _gbif_json(GBIF_VERNACULAR_URL.format(usage_key=usage_key))
    results = data.get("results") or []
    language = language.strip().lower()
    for item in results:
        if _text(item.get("language")).lower() == language and _text(item.get("vernacularName")):
            return _text(item.get("vernacularName"))
    return NA_VALUE


def _same_text(left: str, right: str) -> bool:
    return _clean_header(left) == _clean_header(right)


def _normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _text(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.casefold().split())


def _source_result(source: str, **values: Any) -> dict[str, Any]:
    result = {
        "source": source,
        "found": False,
        "accepted": False,
        "accepted_name": "",
        "matched_name": "",
        "status": "not_found",
        "id": "",
        "rank": "",
        "kingdom": "",
        "phylum": "",
        "class": "",
        "order": "",
        "family": "",
        "genus": "",
        "authorship": "",
        "confidence": "",
        "url": "",
        "notes": "",
    }
    if "class_" in values:
        values["class"] = values.pop("class_")
    result.update(values)
    return result


def _canonical_from_full_name(full_name: Any, authorship: Any) -> str:
    full = _text(full_name)
    author = _text(authorship)
    if author and full.endswith(author):
        return full[: -len(author)].strip()
    return full


def _ctfb_kingdom(higher_classification: Any) -> str:
    hierarchy = _text(higher_classification)
    return hierarchy.split(";", 1)[0].strip() if hierarchy else ""


def query_gbif(name: str, kingdom: str, min_confidence: int) -> dict[str, Any]:
    result = _gbif_match(name, kingdom or None)
    if _text(result.get("matchType")).upper() == "NONE":
        return _source_result("gbif", notes="nome nao encontrado")
    status = _text(result.get("status")).upper()
    confidence = int(result.get("confidence") or 0)
    usage_key = result.get("acceptedUsageKey") or result.get("usageKey")
    usage = _gbif_usage(usage_key)
    accepted_name = _text(result.get("acceptedUsage"))
    if not accepted_name:
        accepted_name = _text(result.get("species")) or _text(result.get("canonicalName"))
    accepted = status == "ACCEPTED" and confidence >= min_confidence
    return _source_result(
        "gbif",
        found=True,
        accepted=accepted,
        accepted_name=accepted_name,
        matched_name=_text(result.get("canonicalName")) or _text(result.get("scientificName")),
        status=status.lower(),
        id=usage_key or "",
        rank=_text(result.get("rank")),
        kingdom=_text(result.get("kingdom")),
        phylum=_text(result.get("phylum")),
        class_=_text(result.get("class")),
        order=_text(result.get("order")),
        family=_text(result.get("family")),
        genus=_text(result.get("genus")),
        authorship=_text(usage.get("authorship")),
        confidence=confidence,
        url=f"https://www.gbif.org/species/{usage_key}" if usage_key else "",
        notes="" if accepted else "status ou confianca exige revisao",
    )


def query_worms(
    name: str,
    expected_kingdom: str = "",
    expected_rank: str = "",
) -> dict[str, Any]:
    url = WORMS_NAME_URL.format(name=quote(name, safe=""))
    data = _json_request(f"{url}?like=false&marine_only=false")
    if not data:
        return _source_result("worms", notes="nome nao encontrado")
    exact = [item for item in data if _normalized(item.get("scientificname")) == _normalized(name)]
    if expected_kingdom:
        contextual = [
            item for item in exact
            if _normalized(item.get("kingdom")) == _normalized(expected_kingdom)
        ]
        if contextual:
            exact = contextual
    if expected_rank:
        contextual = [
            item for item in exact
            if _normalized(item.get("rank")) == _normalized(expected_rank)
        ]
        if contextual:
            exact = contextual
    accepted_exact = [item for item in exact if _normalized(item.get("status")) == "accepted"]
    if accepted_exact:
        exact = accepted_exact
    record = exact[0] if exact else data[0]
    status = _text(record.get("status")).lower()
    accepted_name = _text(record.get("valid_name")) or _text(record.get("scientificname"))
    return _source_result(
        "worms",
        found=True,
        accepted=status == "accepted" and bool(exact),
        accepted_name=accepted_name,
        matched_name=_text(record.get("scientificname")),
        status=status,
        id=record.get("valid_AphiaID") or record.get("AphiaID") or "",
        rank=_text(record.get("rank")),
        kingdom=_text(record.get("kingdom")),
        phylum=_text(record.get("phylum")),
        class_=_text(record.get("class")),
        order=_text(record.get("order")),
        family=_text(record.get("family")),
        genus=_text(record.get("genus")),
        authorship=_text(record.get("valid_authority")) or _text(record.get("authority")),
        url=_text(record.get("url")),
        notes="" if exact else "resultado nao exato",
    )


def query_diatombase(
    name: str,
    expected_kingdom: str = "",
    expected_rank: str = "",
) -> dict[str, Any]:
    url = DIATOMBASE_NAME_URL.format(name=quote(name, safe=""))
    try:
        data = _json_request(url)
    except HTTPError as exc:
        if exc.code == 404:
            return _source_result("diatombase", notes="nome nao encontrado")
        raise
    if not data:
        return _source_result("diatombase", notes="nome nao encontrado")
    exact = [item for item in data if _normalized(item.get("scientificname")) == _normalized(name)]
    if expected_kingdom:
        contextual = [
            item for item in exact
            if _normalized(item.get("kingdom")) == _normalized(expected_kingdom)
        ]
        if contextual:
            exact = contextual
    if expected_rank:
        contextual = [
            item for item in exact
            if _normalized(item.get("rank")) == _normalized(expected_rank)
        ]
        if contextual:
            exact = contextual
    if not exact:
        return _source_result("diatombase", notes="resultado nao exato")
    exact.sort(
        key=lambda item: (
            _normalized(item.get("valid_name")) != _normalized(name),
            _normalized(item.get("status")) not in {"accepted", "unassessed"},
            not bool(item.get("isFreshwater")),
        )
    )
    record = exact[0]
    status = _text(record.get("status")).lower()
    accepted_name = _text(record.get("valid_name")) or _text(record.get("scientificname"))
    accepted = bool(accepted_name) and status not in {"unaccepted", "quarantined", "deleted"}
    return _source_result(
        "diatombase",
        found=True,
        accepted=accepted,
        accepted_name=accepted_name,
        matched_name=_text(record.get("scientificname")),
        status=status,
        id=record.get("valid_AphiaID") or record.get("AphiaID") or "",
        rank=_text(record.get("rank")),
        kingdom=_text(record.get("kingdom")),
        phylum=_text(record.get("phylum")),
        class_=_text(record.get("class")),
        order=_text(record.get("order")),
        family=_text(record.get("family")),
        genus=_text(record.get("genus")),
        authorship=_text(record.get("valid_authority")) or _text(record.get("authority")),
        url=_text(record.get("url")),
        notes="" if accepted else "status exige revisao",
    )


def _classification_by_rank(classification: Any) -> dict[str, str]:
    if not isinstance(classification, list):
        return {}
    return {
        _normalized(item.get("rank")): _text(item.get("name"))
        for item in classification
        if isinstance(item, dict) and _text(item.get("rank")) and _text(item.get("name"))
    }


def query_catalogue_of_life(
    name: str,
    expected_kingdom: str = "",
    expected_rank: str = "",
) -> dict[str, Any]:
    url = f"{COL_SEARCH_URL}?{urlencode({'q': name, 'limit': 50})}"
    data = _json_request(url)
    rows = data.get("result", []) if isinstance(data, dict) else []
    exact = [
        item for item in rows
        if _normalized((item.get("usage") or {}).get("name", {}).get("scientificName"))
        == _normalized(name)
    ]
    if expected_rank:
        contextual = [
            item for item in exact
            if _normalized((item.get("usage") or {}).get("name", {}).get("rank"))
            == _normalized(expected_rank)
        ]
        if contextual:
            exact = contextual
    if expected_kingdom:
        contextual = [
            item for item in exact
            if _normalized(_classification_by_rank(item.get("classification")).get("kingdom"))
            == _normalized(expected_kingdom)
        ]
        if contextual:
            exact = contextual
    if not exact:
        return _source_result("col", notes="nome nao encontrado")
    exact.sort(
        key=lambda item: (
            _normalized((item.get("usage") or {}).get("status")) != "accepted",
            _normalized(item.get("group")) not in {"algae", "prokaryotes"},
        )
    )
    item = exact[0]
    usage = item.get("usage") or {}
    usage_name = usage.get("name") or {}
    accepted_usage = usage.get("accepted") or {}
    accepted_name_data = accepted_usage.get("name") or {}
    status = _text(usage.get("status")).lower()
    accepted_name = _text(accepted_name_data.get("scientificName"))
    if not accepted_name:
        accepted_name = _text(usage_name.get("scientificName"))
    classification = _classification_by_rank(item.get("classification"))
    taxon_id = accepted_usage.get("id") or usage.get("id") or item.get("id") or ""
    return _source_result(
        "col",
        found=True,
        accepted=status == "accepted" or bool(accepted_usage),
        accepted_name=accepted_name,
        matched_name=_text(usage_name.get("scientificName")),
        status=status,
        id=taxon_id,
        rank=_text(accepted_name_data.get("rank")) or _text(usage_name.get("rank")),
        kingdom=classification.get("kingdom", ""),
        phylum=classification.get("phylum", ""),
        class_=classification.get("class", ""),
        order=classification.get("order", ""),
        family=classification.get("family", ""),
        genus=classification.get("genus", ""),
        authorship=_text(accepted_name_data.get("authorship")) or _text(usage_name.get("authorship")),
        url=f"https://www.checklistbank.org/dataset/{COL_DATASET_KEY}/taxon/{taxon_id}",
        notes="" if status == "accepted" else "nome resolvido para uso aceito",
    )


def query_ctfb(name: str) -> dict[str, Any]:
    taxon_url = f"{CTFB_TAXON_URL}?{urlencode({'nome': f'ilike.{name}'})}"
    taxa = _json_request(taxon_url)
    exact = [item for item in taxa if _normalized(item.get("nome")) == _normalized(name)]
    if not exact:
        return _source_result("ctfb", notes="nome nao encontrado")
    record = sorted(exact, key=lambda item: (bool(item.get("sinonimo")), not bool(item.get("lista"))))[0]
    full_name = _text(record.get("nome_completo"))
    hierarchy_url = f"{CTFB_HIERARCHY_URL}?{urlencode({'scientificName': f'eq.{full_name}'})}"
    hierarchy_rows = _json_request(hierarchy_url) if full_name else []
    hierarchy = hierarchy_rows[0] if hierarchy_rows else {}
    is_synonym = bool(record.get("sinonimo"))
    taxonomic_status = _text(hierarchy.get("taxonomicStatus")).lower()
    accepted_name = _text(hierarchy.get("acceptedNameUsage"))
    if not accepted_name and not is_synonym:
        accepted_name = _text(record.get("nome"))
    authorship = _text(hierarchy.get("scientificNameAuthorship")) or _text(record.get("autor"))
    accepted_name = _canonical_from_full_name(accepted_name, authorship)
    accepted = not is_synonym and taxonomic_status in {"", "accepted"} and bool(hierarchy)
    taxon_id = hierarchy.get("taxonID") or record.get("id_dados_lista_brasil") or record.get("id_taxon")
    return _source_result(
        "ctfb",
        found=True,
        accepted=accepted,
        accepted_name=accepted_name,
        matched_name=_text(record.get("nome")),
        status=taxonomic_status or ("synonym" if is_synonym else "accepted"),
        id=taxon_id or "",
        rank=_text(hierarchy.get("taxonRank")) or _text(record.get("rank")),
        kingdom=_ctfb_kingdom(hierarchy.get("higherClassification")),
        phylum=_text(hierarchy.get("phylum")),
        class_=_text(hierarchy.get("class")),
        order=_text(hierarchy.get("order")),
        family=_text(hierarchy.get("family")),
        genus=_text(hierarchy.get("genus")),
        authorship=authorship,
        url=_text(hierarchy.get("references")) or f"https://fauna.jbrj.gov.br/fauna/faunadobrasil/{taxon_id}",
        notes="" if accepted else "registro sinonimo ou hierarquia indisponivel",
    )


def _approval_status(result: dict[str, Any], family: str, min_confidence: int) -> tuple[str, str]:
    notes: list[str] = []
    match_type = str(result.get("matchType", "NONE"))
    status = str(result.get("status", "UNKNOWN"))
    confidence = int(result.get("confidence") or 0)

    if match_type == "NONE":
        return "review", "nome nao encontrado na base"
    if confidence < min_confidence:
        notes.append(f"confianca abaixo do minimo ({confidence} < {min_confidence})")
    if status and status not in {"ACCEPTED"}:
        notes.append(f"status taxonomico exige revisao: {status.lower()}")

    returned_family = _text(result.get("family"))
    if family and returned_family and not _same_text(family, returned_family):
        notes.append(f"familia divergente: planilha={family}; base={returned_family}")

    if notes:
        return "review", "; ".join(notes)
    return "approved", "match aceito com alta confianca"


def _na_if_blank(value: Any) -> str:
    text = _text(value)
    return text if text else NA_VALUE


def _cadastro_from_gbif(
    result: dict[str, Any],
    usage: dict[str, Any],
    vernacular_name: str,
) -> dict[str, Any]:
    status = _text(result.get("status")).upper()
    accepted_name = _text(result.get("acceptedUsage"))
    if not accepted_name and status == "SYNONYM":
        accepted_name = _text(result.get("species")) or _text(result.get("genus"))
    if not accepted_name:
        accepted_name = _text(result.get("canonicalName")) or _text(result.get("scientificName"))

    return {
        "Nome_Cientifico": _na_if_blank(accepted_name),
        "Nome_Popular": _na_if_blank(vernacular_name),
        "Grupo_Biologico": NA_VALUE,
        "Reino": _na_if_blank(result.get("kingdom")),
        "Filo": _na_if_blank(result.get("phylum")),
        "Classe": _na_if_blank(result.get("class")),
        "Ordem": _na_if_blank(result.get("order")),
        "Familia": _na_if_blank(result.get("family")),
        "Genero": _na_if_blank(result.get("genus")),
        "bmwp_score": NA_VALUE,
        "Autor_e_Ano": _na_if_blank(usage.get("authorship")),
        "Status_Ameaca_Estadual": NA_VALUE,
        "Status_Ameaca_Nacional": NA_VALUE,
        "Status_Ameaca_Global": NA_VALUE,
        "Origem": NA_VALUE,
        "Habito_Alimentar": NA_VALUE,
        "Estrategia_Reprodutiva": NA_VALUE,
        "Valor_Economico": NA_VALUE,
        "Observacoes": NA_VALUE,
        "Cinegetica": NA_VALUE,
        "Xerimbabo": NA_VALUE,
    }


def _empty_cadastro() -> dict[str, str]:
    return {column: NA_VALUE for column in CADASTRO_COLUMNS}


CONSENSUS_FIELDS = {
    "Nome_Cientifico": "accepted_name",
    "Reino": "kingdom",
    "Filo": "phylum",
    "Classe": "class",
    "Ordem": "order",
    "Familia": "family",
    "Genero": "genus",
    "Autor_e_Ano": "authorship",
}


def _professional_cadastro(row: pd.Series) -> dict[str, str]:
    return {
        column: _na_if_blank(row.get(column)) if column in row.index else NA_VALUE
        for column in CADASTRO_COLUMNS
    }


def _source_trace(result: dict[str, Any]) -> dict[str, Any]:
    prefix = f"opyta_{result['source']}"
    return {
        f"{prefix}_found": result["found"],
        f"{prefix}_accepted": result["accepted"],
        f"{prefix}_accepted_name": result["accepted_name"],
        f"{prefix}_matched_name": result["matched_name"],
        f"{prefix}_status": result["status"],
        f"{prefix}_id": result["id"],
        f"{prefix}_rank": result["rank"],
        f"{prefix}_kingdom": result["kingdom"],
        f"{prefix}_phylum": result["phylum"],
        f"{prefix}_class": result["class"],
        f"{prefix}_order": result["order"],
        f"{prefix}_family": result["family"],
        f"{prefix}_genus": result["genus"],
        f"{prefix}_authorship": result["authorship"],
        f"{prefix}_confidence": result["confidence"],
        f"{prefix}_url": result["url"],
        f"{prefix}_notes": result["notes"],
    }


def validate_row_consensus(
    row: pd.Series,
    columns: ColumnMap,
    min_confidence: int,
    offline: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    name = _text(row.get(columns.name))
    kingdom = _text(row.get(columns.kingdom)) if columns.kingdom else ""
    base: dict[str, Any] = {
        **_professional_cadastro(row),
        "opyta_input_name": name,
        "opyta_validation_status": "review",
        "opyta_consensus_name": "",
        "opyta_consensus_fields": "",
        "opyta_conflict_fields": "",
        "opyta_source": "WoRMS | CTFB | GBIF",
        "opyta_validated_at": now,
        "opyta_validation_notes": "",
    }
    if not name:
        base["opyta_validation_notes"] = "nome cientifico vazio"
        return base
    if offline:
        base["opyta_validation_status"] = "unchecked"
        base["opyta_source"] = "offline_structure_check"
        base["opyta_validation_notes"] = "validacao online nao executada"
        return base

    queries = (
        ("worms", lambda: query_worms(name)),
        ("ctfb", lambda: query_ctfb(name)),
        ("gbif", lambda: query_gbif(name, "", min_confidence)),
    )
    results: list[dict[str, Any]] = []
    for source, query in queries:
        try:
            results.append(query())
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            results.append(_source_result(source, status="error", notes=f"erro de consulta: {exc}"))
    for result in results:
        base.update(_source_trace(result))

    accepted_results = [result for result in results if result["accepted"]]
    name_values = [_normalized(result["accepted_name"]) for result in accepted_results]
    all_accepted = len(accepted_results) == 3
    name_consensus = all_accepted and len(set(name_values)) == 1 and bool(name_values[0])

    agreed_fields: dict[str, str] = {}
    conflict_fields: list[str] = []
    for output_field, source_field in CONSENSUS_FIELDS.items():
        values = [_text(result[source_field]) for result in results]
        available = [value for value in values if value]
        if len(available) == 3:
            if len({_normalized(value) for value in available}) == 1:
                agreed_fields[output_field] = available[0]
            else:
                conflict_fields.append(output_field)

    if name_consensus and not conflict_fields:
        base.update(agreed_fields)
        base["opyta_validation_status"] = "approved_consensus"
        base["opyta_consensus_name"] = accepted_results[0]["accepted_name"]
        base["opyta_consensus_fields"] = ";".join(agreed_fields)
        base["opyta_validation_notes"] = "tres bases concordam; campos sem consenso mantidos conforme profissional"
    elif all_accepted:
        base["opyta_validation_status"] = "review_conflict"
        base["opyta_conflict_fields"] = ";".join(conflict_fields or ["Nome_Cientifico"])
        base["opyta_validation_notes"] = "conflito entre bases; cadastro profissional preservado"
    elif accepted_results:
        base["opyta_validation_status"] = "review_partial"
        base["opyta_validation_notes"] = (
            f"somente {len(accepted_results)} de 3 bases aceitaram o registro; cadastro profissional preservado"
        )
    else:
        base["opyta_validation_status"] = "not_found"
        base["opyta_validation_notes"] = "nenhuma das tres bases aceitou o registro; cadastro profissional preservado"
    return base


_FITOPLANKTON_QUERY_CACHE: dict[tuple[str, str, str, int], list[dict[str, Any]]] = {}


def _fitoplankton_lookup(name: str, row: pd.Series | None = None) -> tuple[str, str, bool]:
    sp_match = re.fullmatch(r"\s*([A-Za-z][A-Za-z-]+)\s+sp\.\s*", name, flags=re.IGNORECASE)
    if sp_match:
        return sp_match.group(1), "genus", True
    unidentified = re.fullmatch(
        r"\s*([A-Za-z][A-Za-z-]+)\s+n\.?i\.?\s*",
        name,
        flags=re.IGNORECASE,
    )
    if unidentified:
        taxon = unidentified.group(1)
        suffix_ranks = (
            ("aceae", "family"),
            ("ales", "order"),
            ("phyceae", "class"),
            ("phyta", "phylum"),
        )
        rank = next(
            (candidate for suffix, candidate in suffix_ranks if taxon.casefold().endswith(suffix)),
            "",
        )
        if not rank and row is not None:
            for column, candidate_rank in (
                ("Genero", "genus"),
                ("Familia", "family"),
                ("Ordem", "order"),
                ("Classe", "class"),
                ("Filo", "phylum"),
                ("Reino", "kingdom"),
            ):
                value = _text(row.get(column))
                if value and _normalized(value) not in {"n.a.", "na"}:
                    return value, candidate_rank, True
        return taxon, rank, True
    return name, "", False


def _fitoplankton_queries(
    name: str,
    kingdom: str,
    expected_rank: str,
    min_confidence: int,
) -> list[dict[str, Any]]:
    cache_key = (_normalized(name), _normalized(kingdom), _normalized(expected_rank), min_confidence)
    if cache_key in _FITOPLANKTON_QUERY_CACHE:
        return [dict(result) for result in _FITOPLANKTON_QUERY_CACHE[cache_key]]

    queries = (
        (
            "gbif",
            lambda: query_gbif(name, kingdom, min_confidence),
        ),
        (
            "col",
            lambda: query_catalogue_of_life(name, kingdom, expected_rank),
        ),
        (
            "diatombase",
            lambda: query_diatombase(name, kingdom, expected_rank),
        ),
    )
    results: list[dict[str, Any]] = []
    for source, query in queries:
        try:
            result = query()
            if source == "gbif":
                confidence = int(result.get("confidence") or 0)
                if (
                    result.get("found")
                    and result.get("accepted_name")
                    and _normalized(result.get("status")) in {"accepted", "synonym"}
                    and confidence >= min_confidence
                ):
                    result["accepted"] = True
                if expected_rank and _normalized(result.get("rank")) != _normalized(expected_rank):
                    result["accepted"] = False
                    result["notes"] = "categoria taxonomica divergente"
            results.append(result)
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            results.append(_source_result(source, status="error", notes=f"erro de consulta: {exc}"))
    _FITOPLANKTON_QUERY_CACHE[cache_key] = [dict(result) for result in results]
    return results


def validate_row_fitoplankton(
    row: pd.Series,
    columns: ColumnMap,
    min_confidence: int,
    offline: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    name = _text(row.get(columns.name))
    kingdom = _text(row.get(columns.kingdom)) if columns.kingdom else ""
    base: dict[str, Any] = {
        **_professional_cadastro(row),
        "opyta_input_name": name,
        "opyta_validation_status": "review",
        "opyta_consensus_name": "",
        "opyta_consensus_fields": "",
        "opyta_conflict_fields": "",
        "opyta_source": "GBIF | Catalogue of Life | DiatomBase",
        "opyta_validated_at": now,
        "opyta_validation_notes": "",
    }
    if not name:
        base["opyta_validation_notes"] = "nome cientifico vazio"
        return base
    if offline:
        base["opyta_validation_status"] = "unchecked"
        base["opyta_source"] = "offline_structure_check"
        base["opyta_validation_notes"] = "validacao online nao executada"
        return base

    lookup_name, expected_rank, partial = _fitoplankton_lookup(name, row)
    results = _fitoplankton_queries(lookup_name, kingdom, expected_rank, min_confidence)
    for result in results:
        base.update(_source_trace(result))

    accepted_results = [result for result in results if result["accepted"]]
    agreed_fields: list[str] = []
    conflict_fields: list[str] = []
    for output_field, source_field in CONSENSUS_FIELDS.items():
        if partial and output_field == "Nome_Cientifico":
            continue
        values = [_text(result[source_field]) for result in accepted_results]
        available = [value for value in values if value]
        distinct = {_normalized(value) for value in available}
        if len(available) >= 2 and len(distinct) == 1:
            agreed_fields.append(output_field)
        elif len(available) >= 2 and len(distinct) > 1:
            conflict_fields.append(output_field)

    accepted_names = [_normalized(result["accepted_name"]) for result in accepted_results]
    name_consensus = (
        not partial
        and len(accepted_results) == 3
        and len(set(accepted_names)) == 1
        and bool(accepted_names[0])
    )
    base["opyta_consensus_fields"] = ";".join(agreed_fields)
    base["opyta_conflict_fields"] = ";".join(conflict_fields)

    if partial and agreed_fields:
        base["opyta_validation_status"] = "approved_classification"
        base["opyta_validation_notes"] = (
            "identificacao parcial preservada; classificacao confirmada por pelo menos duas bases"
        )
    elif name_consensus and not conflict_fields:
        base["opyta_validation_status"] = "approved_consensus"
        base["opyta_consensus_name"] = accepted_results[0]["accepted_name"]
        base["opyta_validation_notes"] = "tres bases concordam com o nome; classificacao sem conflito"
    elif len(accepted_results) == 3:
        base["opyta_validation_status"] = "review_conflict"
        base["opyta_validation_notes"] = "conflito entre bases; cadastro profissional preservado"
    elif accepted_results:
        base["opyta_validation_status"] = "review_partial"
        base["opyta_validation_notes"] = (
            f"somente {len(accepted_results)} de 3 bases aceitaram o registro; cadastro profissional preservado"
        )
    else:
        base["opyta_validation_status"] = "not_found"
        base["opyta_validation_notes"] = "nenhuma das tres bases aceitou o registro"
    return base


def validate_row(
    row: pd.Series,
    columns: ColumnMap,
    min_confidence: int,
    offline: bool,
    vernacular_language: str,
    profile: str = "gbif",
) -> dict[str, Any]:
    if profile == "zooplankton":
        return validate_row_consensus(row, columns, min_confidence, offline)
    if profile == "fitoplankton":
        return validate_row_fitoplankton(row, columns, min_confidence, offline)
    now = datetime.now(timezone.utc).isoformat()
    name = _text(row.get(columns.name))
    family = _text(row.get(columns.family)) if columns.family else ""
    kingdom = _text(row.get(columns.kingdom)) if columns.kingdom else ""

    base = {
        **_empty_cadastro(),
        "opyta_input_name": name,
        "opyta_validation_status": "review",
        "opyta_taxonomic_status": "",
        "opyta_matched_name": "",
        "opyta_accepted_name": "",
        "opyta_usage_key": "",
        "opyta_accepted_usage_key": "",
        "opyta_confidence": "",
        "opyta_match_type": "",
        "opyta_rank": "",
        "opyta_kingdom": "",
        "opyta_phylum": "",
        "opyta_class": "",
        "opyta_order": "",
        "opyta_family": "",
        "opyta_genus": "",
        "opyta_family_check": "",
        "opyta_source": "GBIF Backbone Taxonomy" if not offline else "offline_structure_check",
        "opyta_validated_at": now,
        "opyta_validation_notes": "",
    }

    if not name:
        base["opyta_validation_notes"] = "nome cientifico vazio"
        return base
    if offline:
        base["opyta_validation_status"] = "unchecked"
        base["opyta_validation_notes"] = "validacao online nao executada"
        return base

    try:
        result = _gbif_match(name, kingdom or None)
    except (HTTPError, URLError, TimeoutError) as exc:
        base["opyta_validation_status"] = "review"
        base["opyta_validation_notes"] = f"erro na consulta GBIF: {exc}"
        return base

    accepted_usage_key = result.get("acceptedUsageKey", "") or result.get("usageKey", "")
    try:
        usage = _gbif_usage(accepted_usage_key)
        vernacular_name = _gbif_vernacular_name(accepted_usage_key, vernacular_language)
    except (HTTPError, URLError, TimeoutError) as exc:
        usage = {}
        vernacular_name = NA_VALUE
        base["opyta_validation_notes"] = f"consulta complementar GBIF incompleta: {exc}"

    validation_status, notes = _approval_status(result, family, min_confidence)
    cadastro_values = _cadastro_from_gbif(result, usage, vernacular_name)
    returned_family = _text(result.get("family"))
    if not family:
        family_check = "not_provided"
    elif returned_family and _same_text(family, returned_family):
        family_check = "match"
    elif returned_family:
        family_check = "mismatch"
    else:
        family_check = "not_returned"

    status = _text(result.get("status")).upper()
    accepted_name = _text(result.get("acceptedUsage"))
    if not accepted_name and status == "SYNONYM":
        accepted_name = _text(result.get("species")) or _text(result.get("genus"))
    if not accepted_name:
        accepted_name = _text(result.get("scientificName"))
    if base["opyta_validation_notes"] and notes:
        notes = f"{notes}; {base['opyta_validation_notes']}"
    elif base["opyta_validation_notes"]:
        notes = base["opyta_validation_notes"]

    base.update(
        {
            **cadastro_values,
            "opyta_validation_status": validation_status,
            "opyta_taxonomic_status": status.lower() or "unknown",
            "opyta_matched_name": _text(result.get("scientificName")),
            "opyta_accepted_name": accepted_name,
            "opyta_usage_key": result.get("usageKey", ""),
            "opyta_accepted_usage_key": result.get("acceptedUsageKey", "") or result.get("usageKey", ""),
            "opyta_confidence": result.get("confidence", ""),
            "opyta_match_type": _text(result.get("matchType")),
            "opyta_rank": _text(result.get("rank")),
            "opyta_kingdom": _text(result.get("kingdom")),
            "opyta_phylum": _text(result.get("phylum")),
            "opyta_class": _text(result.get("class")),
            "opyta_order": _text(result.get("order")),
            "opyta_family": returned_family,
            "opyta_genus": _text(result.get("genus")),
            "opyta_family_check": family_check,
            "opyta_validation_notes": notes,
        }
    )
    return base


def default_output_path(input_path: Path) -> Path:
    return REPO_ROOT / "species_validation" / "outputs" / f"{input_path.stem}_validated{input_path.suffix}"


def default_manifest_path(input_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "species_validation" / "traces" / f"{input_path.stem}_{stamp}.json"


def build_manifest(
    args: argparse.Namespace,
    output: Path,
    columns: ColumnMap,
    df: pd.DataFrame,
) -> dict[str, Any]:
    counts = df["opyta_validation_status"].value_counts(dropna=False).to_dict()
    return {
        "validator": "species_registration_validator",
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "output": str(output),
        "source": (
            "offline" if args.offline else
            "WoRMS | CTFB | GBIF" if args.profile == "zooplankton" else
            "GBIF | Catalogue of Life | DiatomBase" if args.profile == "fitoplankton" else
            "GBIF Backbone Taxonomy"
        ),
        "columns": {
            "name": columns.name,
            "family": columns.family,
            "kingdom": columns.kingdom,
        },
        "parameters": {
            "min_confidence": args.min_confidence,
            "offline": bool(args.offline),
            "limit": args.limit,
            "vernacular_language": args.vernacular_language,
            "profile": args.profile,
        },
        "summary": {
            "rows": int(len(df)),
            "status_counts": {str(key): int(value) for key, value in counts.items()},
        },
    }


def main() -> int:
    args = parse_args()
    df = read_table(args.input, args.sheet)
    if args.limit:
        df = df.head(args.limit).copy()
    columns = detect_columns(df, args)

    results: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        results.append(
            validate_row(
                row,
                columns,
                args.min_confidence,
                args.offline,
                args.vernacular_language,
                args.profile,
            )
        )
        if not args.offline and index < len(df) - 1 and args.delay > 0:
            time.sleep(args.delay)

    original_df = df.reset_index(drop=True).copy()
    collisions = {column: f"input_{column}" for column in CADASTRO_COLUMNS if column in original_df.columns}
    if collisions:
        original_df = original_df.rename(columns=collisions)
    result_df = pd.concat([original_df, pd.DataFrame(results)], axis=1)
    output = args.output or default_output_path(args.input)
    manifest_path = args.manifest or default_manifest_path(args.input)

    write_table(result_df, output, args.input, args.sheet)
    manifest = build_manifest(args, output, columns, result_df)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    counts = manifest["summary"]["status_counts"]
    print(f"[species-validation] output -> {output}")
    print(f"[species-validation] manifest -> {manifest_path}")
    print(f"[species-validation] rows={len(result_df)} status={counts}")

    review_count = sum(int(value) for key, value in counts.items() if str(key).startswith("review"))
    if args.strict_review and review_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
