"""Core rules for Meio Fisico XLSX processing.

This module keeps business rules that must stay identical across blocks:
result parsing, VMP parsing/filtering, unit conversion and violation logic.
Keep it dependency-light so standalone scripts can import it safely.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable, Literal

import pandas as pd

LimitMode = Literal["min", "max"]

MISSING_TOKENS = {"", "-", "--", "\u2014", "NA", "N/A", "ND", "N/D", "NI", "N/I"}

UNIT_FACTORS_TO_BASE = {
    "mg/l": 1.0,
    "\u00b5g/l": 1e-3,
    "\u03bcg/l": 1e-3,
    "ug/l": 1e-3,
    "ng/l": 1e-6,
    "g/l": 1e3,
    "mg/kg": 1.0,
    "\u00b5g/kg": 1e-3,
    "\u03bcg/kg": 1e-3,
    "ug/kg": 1e-3,
}


def normalize_text(value: object) -> str:
    """Return lowercase ASCII-ish text for matching parameters and units."""
    text = "" if value is None else str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().upper() in MISSING_TOKENS


def _number_text(value: object) -> str:
    text = str(value).strip().replace("\u00a0", " ")
    text = text.replace("\u2264", "<=").replace("\u2265", ">=")
    text = text.replace("%", "").strip()
    return text


def parse_resultado(value: object) -> tuple[float | None, str]:
    """Parse result text into numeric value and qualifier sign.

    Examples:
        "< 0,5" -> (0.5, "<")
        ">= 10" -> (10.0, ">=")
        "12.3" -> (12.3, "")
    """
    if _is_missing(value):
        return None, ""

    text = _number_text(value)
    sign = ""
    for prefix in ("<=", ">=", "<", ">"):
        if text.startswith(prefix):
            sign = prefix
            text = text[len(prefix):].strip()
            break

    text = re.sub(r"(?i)\b(nd|n/d|na|n\.a\.|ni|n/i)\b", "", text).strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    text = text.replace(" ", "")
    if not text:
        return None, sign

    try:
        return float(text), sign
    except ValueError:
        return None, sign


def parse_vmp(value: object) -> float | None:
    """Parse VMP text into float, without applying business filtering."""
    if _is_missing(value):
        return None
    text = _number_text(value)
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    text = text.replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return None


def unit_norm(value: object) -> str:
    text = "" if value is None else str(value).strip().lower()
    text = text.replace(" ", "")
    text = text.replace("\u03bc", "\u00b5")
    return text


def conversion_factor(from_unit: object, to_unit: object) -> float | None:
    """Return factor to convert a value from from_unit to to_unit."""
    source = UNIT_FACTORS_TO_BASE.get(unit_norm(from_unit))
    target = UNIT_FACTORS_TO_BASE.get(unit_norm(to_unit))
    if source is None or target is None:
        return None
    return source / target


def is_zero_vmp_valid(parameter: object) -> bool:
    """True when VMP=0 means absence, not a placeholder."""
    p = normalize_text(parameter)
    return "coliform" in p or "escherichia" in p or "e coli" in p


def filter_vmp_value(value: object, parameter: object) -> float | None:
    """Parse and apply shared VMP validity rules."""
    parsed = parse_vmp(value)
    if parsed is None or parsed < 0:
        return None
    if parsed == 0 and not is_zero_vmp_valid(parameter):
        return None
    return parsed


def violates_limit(value: float | None, sign: str, limit: float | None, mode: LimitMode) -> bool:
    """Evaluate one limit against one result.

    Results reported below quantification ("<" or "<=") are not violations.
    """
    if value is None or limit is None:
        return False
    if sign in ("<", "<="):
        return False
    if mode == "min":
        return value < limit
    if mode == "max":
        return value > limit
    return False


def summarize_limits(limits: Iterable[tuple[LimitMode, float | None]]) -> tuple[float | None, float | None, float | None, str]:
    """Summarize min/max rules for reporting in B4/B11 outputs."""
    limits = list(limits)
    mins = [v for mode, v in limits if mode == "min" and v is not None]
    maxs = [v for mode, v in limits if mode == "max" and v is not None]
    limit_min = max(mins) if mins else None
    limit_max = min(maxs) if maxs else None
    if limit_min is not None and limit_max is not None:
        return limit_min, limit_max, limit_max, "faixa"
    if limit_min is not None:
        return limit_min, None, limit_min, "min"
    if limit_max is not None:
        return None, limit_max, limit_max, "max"
    return None, None, None, ""


def latest_generated(path: Path) -> Path:
    """Return the newest official/_NEW path for a generated file."""
    alt = path.with_name(path.stem + "_NEW" + path.suffix)
    existing = [p for p in (path, alt) if p.exists()]
    if not existing:
        return path
    return max(existing, key=lambda p: p.stat().st_mtime)
