from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


InferenceLevel = Literal[
    "descritivo",
    "comparativo",
    "interpretativo",
    "recomendacao",
    "causal",
]

ParagraphRole = Literal[
    "contexto",
    "resultado",
    "comparacao",
    "interpretacao",
    "limitacao",
    "sintese",
    "recomendacao",
]


@dataclass(frozen=True)
class Evidence:
    """Unidade auditável que sustenta uma ou mais afirmações textuais."""

    evidence_id: str
    title: str
    section: str
    observation: str
    sources: tuple[str, ...]
    inference_level: InferenceLevel = "descritivo"
    metrics: dict[str, Any] = field(default_factory=dict)
    interpretation: str = ""
    limitations: tuple[str, ...] = ()
    scope: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NarrativeParagraph:
    text: str
    evidence_ids: tuple[str, ...]
    role: ParagraphRole = "resultado"
    inference_level: InferenceLevel = "descritivo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FigureReference:
    filename: str
    caption: str
    source_workbook: str | None = None
    alt_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NarrativeSection:
    section_id: str
    title: str
    paragraphs: tuple[NarrativeParagraph, ...]
    figures: tuple[FigureReference, ...] = ()
    table_rows: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TechnicalReport:
    title: str
    subtitle: str
    project_code: str
    group: str
    period: str
    metadata: dict[str, str]
    sections: tuple[NarrativeSection, ...]
    evidence: tuple[Evidence, ...]
    editorial_profile: dict[str, Any] = field(default_factory=dict)
    report_status: str = "piloto"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
