"""Camada reutilizável para narrativa técnica rastreável."""

from .html import render_technical_report
from .models import (
    Evidence,
    FigureReference,
    NarrativeParagraph,
    NarrativeSection,
    TechnicalReport,
)
from .validation import ValidationIssue, validate_technical_report

__all__ = [
    "Evidence",
    "FigureReference",
    "NarrativeParagraph",
    "NarrativeSection",
    "TechnicalReport",
    "ValidationIssue",
    "render_technical_report",
    "validate_technical_report",
]
