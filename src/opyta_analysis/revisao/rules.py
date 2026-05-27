from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any


CHECKLIST_COLUMNS = {
    "tipo_achado": "alerta_para_conferencia",
    "procede?": "",
    "acao": "",
    "responsavel": "",
    "status": "pendente",
    "observacao_revisor": "",
}


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _norm_text(value: object) -> str:
    return _strip_accents(str(value or "")).lower()


def _issue(
    severity: str,
    category: str,
    message: str,
    evidence: str = "",
    suggestion: str = "",
    *,
    issue_type: str = "alerta_para_conferencia",
) -> dict[str, str]:
    return {
        "severidade": severity,
        "categoria": category,
        "problema": message,
        "evidencia": evidence,
        "sugestao": suggestion,
        "tipo_achado": issue_type,
    }


def prepare_issues_checklist(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, issue in enumerate(issues, start=1):
        row = {"id_revisao": f"REV-{index:04d}", **issue}
        for column, default in CHECKLIST_COLUMNS.items():
            row.setdefault(column, default)
        rows.append(row)
    return rows


def review_status_dictionary() -> list[dict[str, str]]:
    return [
        {
            "campo": "tipo_achado",
            "valor": "erro_confirmado",
            "uso": "Achado deterministico que deve ser corrigido antes da entrega.",
        },
        {
            "campo": "tipo_achado",
            "valor": "alerta_para_conferencia",
            "uso": "Achado plausivel que requer leitura do revisor.",
        },
        {
            "campo": "tipo_achado",
            "valor": "divergencia_candidata",
            "uso": "Possivel divergencia numerica detectada por contexto.",
        },
        {
            "campo": "status",
            "valor": "pendente",
            "uso": "Ainda nao avaliado pelo revisor.",
        },
        {
            "campo": "status",
            "valor": "confirmado",
            "uso": "O revisor confirmou que procede.",
        },
        {
            "campo": "status",
            "valor": "falso_positivo",
            "uso": "O revisor descartou o achado.",
        },
        {
            "campo": "status",
            "valor": "corrigido",
            "uso": "O problema foi corrigido no produto final.",
        },
        {
            "campo": "status",
            "valor": "nao_aplica",
            "uso": "O item nao se aplica ao escopo da entrega.",
        },
    ]


def _label_key(kind: object, number: object) -> tuple[str, str]:
    return (str(kind or "").strip().lower(), re.sub(r"\D+", "", str(number or "")))


def build_initial_issues(doc: dict[str, Any], results: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    comments = doc.get("comments", [])
    if comments:
        issues.append(
            _issue(
                "ALTA",
                "Word/comentarios",
                f"O documento ainda contem {len(comments)} comentario(s) interno(s).",
                "; ".join((c.get("text") or "")[:160] for c in comments[:3]),
                "Resolver/remover comentarios antes da entrega final.",
                issue_type="erro_confirmado",
            )
        )

    zip_meta = doc.get("zip_metadata", {})
    if zip_meta.get("track_changes_insertions") or zip_meta.get("track_changes_deletions"):
        issues.append(
            _issue(
                "CRITICA",
                "Word/controle_de_alteracoes",
                "O documento possui marcas de controle de alteracoes.",
                f"ins={zip_meta.get('track_changes_insertions')}; del={zip_meta.get('track_changes_deletions')}",
                "Aceitar/rejeitar alteracoes antes da entrega.",
                issue_type="erro_confirmado",
            )
        )

    headings_text = [str(h.get("text", "")) for h in doc.get("headings", [])]
    for text in headings_text:
        normalized = _norm_text(text)
        lowered = text.lower()
        if "metodologicos" in normalized and "metodológic" not in lowered:
            issues.append(
                _issue(
                    "MEDIA",
                    "Ortografia/titulo",
                    "Possivel erro em titulo: 'PROCEDIMENTOS METODOLOGICOS'.",
                    text,
                    "Padronizar para 'PROCEDIMENTOS METODOLOGICOS' com acento correto em '-LOGICOS'.",
                    issue_type="erro_confirmado",
                )
            )

    all_text = "\n".join(str(p.get("text", "")) for p in doc.get("paragraphs", []))
    sam_variants = re.findall(r"\bSam\s+metais\b|\bSAM\s+metais\b|\bSam\s+Metais\b", all_text)
    if sam_variants:
        issues.append(
            _issue(
                "BAIXA",
                "Padronizacao",
                "Foram encontradas grafias potencialmente inconsistentes de SAM Metais.",
                f"ocorrencias={len(sam_variants)}; exemplos={sorted(set(sam_variants))[:5]}",
                "Padronizar como 'SAM Metais', salvo quando for citacao literal.",
            )
        )

    captions_body = [c for c in doc.get("captions", []) if not c.get("is_toc")]
    labels = [_label_key(c.get("tipo", ""), c.get("numero", "")) for c in captions_body]
    raw_label_by_key = {
        _label_key(c.get("tipo", ""), c.get("numero", "")): (str(c.get("tipo", "")).lower(), str(c.get("numero", "")))
        for c in captions_body
    }
    duplicates = [label for label, count in Counter(labels).items() if count > 1 and label[1]]
    if duplicates:
        issues.append(
            _issue(
                "ALTA",
                "Figuras_tabelas/numeracao",
                "Ha legendas com numeracao repetida no corpo do documento.",
                ", ".join(f"{kind} {num}" for kind, num in duplicates[:12]),
                "Conferir campos de legenda e atualizar numeracao/listas automaticas.",
            )
        )

    refs = {_label_key(r.get("tipo", ""), r.get("numero", "")) for r in doc.get("references", [])}
    caption_set = set(labels)
    refs_without_caption = sorted(refs - caption_set)
    if refs_without_caption:
        issues.append(
            _issue(
                "MEDIA",
                "Figuras_tabelas/referencias",
                "Ha referencias no texto sem legenda equivalente detectada no corpo.",
                ", ".join(f"{kind} {num}" for kind, num in refs_without_caption[:20]),
                "Verificar se a legenda existe, se esta em campo automatico ou se ha erro de numeracao.",
            )
        )

    caption_without_refs = sorted(caption_set - refs)
    if caption_without_refs:
        issues.append(
            _issue(
                "BAIXA",
                "Figuras_tabelas/referencias",
                "Ha legendas sem citacao textual detectada.",
                ", ".join(
                    f"{raw_label_by_key.get((kind, num), (kind, num))[0]} {raw_label_by_key.get((kind, num), (kind, num))[1]}"
                    for kind, num in caption_without_refs[:20]
                ),
                "Confirmar se toda figura/quadro/tabela e chamada no texto.",
            )
        )

    for row in results.get("summary", []):
        if not row.get("exists"):
            issues.append(
                _issue(
                    "CRITICA",
                    "Resultados/pasta",
                    f"Pasta de resultados ausente para {row.get('grupo')}.",
                    str(row.get("pasta")),
                    "Corrigir caminho de entrada da revisao.",
                )
            )
        if row.get("duplicated_file_names"):
            issues.append(
                _issue(
                    "MEDIA",
                    "Resultados/duplicidade",
                    f"{row.get('grupo')} possui nomes de arquivos duplicados em subpastas.",
                    str(row.get("duplicated_names_sample")),
                    "Verificar se ha versoes antigas/duplicadas sendo consideradas na revisao.",
                )
            )

    bad_png = [
        item for item in results.get("png_checks", [])
        if item.get("blank") or item.get("small")
    ]
    if bad_png:
        issues.append(
            _issue(
                "ALTA",
                "Resultados/imagens",
                "Ha PNGs em branco ou com dimensoes muito pequenas.",
                "; ".join(f"{i.get('grupo')}/{i.get('relative_path')}" for i in bad_png[:10]),
                "Regenerar ou substituir imagens problemáticas.",
                issue_type="erro_confirmado",
            )
        )

    return issues
