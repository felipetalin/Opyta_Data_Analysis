from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import TechnicalReport


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    location: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


CAUSAL_PATTERNS = (
    r"\bcaus(?:a|ou|aram|ado|ada)\b",
    r"\bprovoc(?:a|ou|aram|ado|ada)\b",
    r"\bdecorrente de\b",
    r"\bdevido a\b",
    r"\bem resposta direta\b",
    r"\bdemonstra impacto\b",
    r"\bevidencia impacto\b",
    r"\breflete a influência\b",
)

ABSOLUTE_PATTERNS = (
    r"\bcomprova\b",
    r"\bconfirma definitivamente\b",
    r"\bsem dúvida\b",
    r"\bexclusivamente\b",
)

METALANGUAGE_PATTERNS = (
    r"\ba distribui[cç][aã]o (?:descreve|resume|representa)\b",
    r"\ba frequ[eê]ncia (?:descreve|resume|representa)\b",
    r"\ba similaridade (?:descreve|resume|representa)\b",
    r"\beste resultado deve ser lido\b",
    r"\bo indicador permite observar\b",
)


def validate_technical_report(
    report: TechnicalReport,
    *,
    source_dir: Path,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    evidence_map = {item.evidence_id: item for item in report.evidence}

    if len(evidence_map) != len(report.evidence):
        issues.append(
            ValidationIssue(
                "ERROR",
                "duplicate_evidence_id",
                "Existem identificadores de evidência duplicados.",
            )
        )

    for evidence in report.evidence:
        if not evidence.sources:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    "evidence_without_source",
                    f"A evidência {evidence.evidence_id} não possui arquivo-fonte.",
                    evidence.evidence_id,
                )
            )
        for filename in evidence.sources:
            if not (source_dir / filename).exists():
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "source_not_found",
                        f"Arquivo-fonte não encontrado: {filename}.",
                        evidence.evidence_id,
                    )
                )
        if evidence.inference_level in {"interpretativo", "recomendacao"} and not evidence.limitations:
            issues.append(
                ValidationIssue(
                    "WARNING",
                    "interpretation_without_limitation",
                    "Evidência interpretativa sem limitação explícita.",
                    evidence.evidence_id,
                )
            )

    for section in report.sections:
        if not section.paragraphs:
            issues.append(
                ValidationIssue(
                    "WARNING",
                    "empty_section",
                    f"A seção '{section.title}' não possui parágrafos.",
                    section.section_id,
                )
            )
        for index, paragraph in enumerate(section.paragraphs, start=1):
            location = f"{section.section_id}.p{index}"
            if not paragraph.evidence_ids:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "paragraph_without_evidence",
                        "Parágrafo sem vínculo com evidência.",
                        location,
                    )
                )
            for evidence_id in paragraph.evidence_ids:
                if evidence_id not in evidence_map:
                    issues.append(
                        ValidationIssue(
                            "ERROR",
                            "unknown_evidence",
                            f"Parágrafo referencia evidência inexistente: {evidence_id}.",
                            location,
                        )
                    )

            normalized = paragraph.text.casefold()
            has_causal_term = any(
                re.search(pattern, normalized, flags=re.IGNORECASE)
                for pattern in CAUSAL_PATTERNS
            )
            if has_causal_term and paragraph.inference_level != "causal":
                issues.append(
                    ValidationIssue(
                        "WARNING",
                        "causal_language_without_causal_design",
                        "Linguagem causal detectada em parágrafo não classificado como causal.",
                        location,
                    )
                )

            if any(
                re.search(pattern, normalized, flags=re.IGNORECASE)
                for pattern in ABSOLUTE_PATTERNS
            ):
                issues.append(
                    ValidationIssue(
                        "WARNING",
                        "absolute_language",
                        "Afirmação absoluta detectada; revisar proporcionalidade da conclusão.",
                        location,
                    )
                )

            if any(
                re.search(pattern, normalized, flags=re.IGNORECASE)
                for pattern in METALANGUAGE_PATTERNS
            ):
                issues.append(
                    ValidationIssue(
                        "WARNING",
                        "editorial_metalanguage",
                        "Metalinguagem detectada; apresentar diretamente o resultado.",
                        location,
                    )
                )

            if paragraph.role == "interpretacao":
                linked = [
                    evidence_map[evidence_id]
                    for evidence_id in paragraph.evidence_ids
                    if evidence_id in evidence_map
                ]
                if linked and not any(item.limitations for item in linked):
                    issues.append(
                        ValidationIssue(
                            "WARNING",
                            "interpretive_paragraph_without_limitation",
                            "Parágrafo interpretativo sem limitação associada.",
                            location,
                        )
                    )

        for figure in section.figures:
            if not (source_dir / figure.filename).exists():
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "figure_not_found",
                        f"Figura não encontrada: {figure.filename}.",
                        section.section_id,
                    )
                )
            if figure.source_workbook and not (source_dir / figure.source_workbook).exists():
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "figure_source_not_found",
                        f"Planilha associada à figura não encontrada: {figure.source_workbook}.",
                        section.section_id,
                    )
                )

    return issues
