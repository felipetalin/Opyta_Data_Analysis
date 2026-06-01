from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.revisao.docx_audit import extract_docx_audit, render_extracted_markdown
from opyta_analysis.revisao.html_report import render_visual_review_html
from opyta_analysis.revisao.numeric_audit import (
    audit_metric_mentions,
    build_numeric_divergence_issues,
    build_numeric_issues,
    classify_metric_mentions,
    detect_numeric_divergence_candidates,
    extract_numeric_metrics,
)
from opyta_analysis.revisao.resultados_audit import inventory_results_dirs
from opyta_analysis.revisao.rules import (
    build_initial_issues,
    prepare_issues_checklist,
    review_status_dictionary,
)


DEFAULT_PRODUCTS_ROOT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Ferreira Rocha\SAM Metais\Produtos"
)
DOCX_PATTERN = "SAM-DIAG-AQUA-BIOTA-BHZ-RT-001-26-R00-260527*.docx"


def _resolve_docx(products_root: Path, explicit_docx: str | None) -> Path:
    if explicit_docx:
        path = Path(explicit_docx)
        if path.exists():
            return path
        matches = list(products_root.rglob(Path(explicit_docx).name))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"DOCX nao encontrado: {explicit_docx}")

    matches = list(products_root.rglob(DOCX_PATTERN))
    if not matches:
        raise FileNotFoundError(f"Nenhum DOCX encontrado com padrao {DOCX_PATTERN}")
    if len(matches) > 1:
        newest = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        return newest
    return matches[0]


def _default_result_dirs(products_root: Path) -> dict[str, Path]:
    base = products_root / "Resultados"
    return {
        "Bentos": base / "Bentos",
        "Fito": base / "Fito",
        "Zooplancton": base / "Zooplancton",
        "Ictio": base / "Ictio",
    }


def _write_excel(path: Path, sheets: dict[str, list[dict[str, Any]]]) -> Path:
    actual_path = path
    try:
        writer = pd.ExcelWriter(path, engine="openpyxl")
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        fallback = path.with_name(f"{path.stem}_{stamp}{path.suffix}")
        print(f"[revisao] Arquivo bloqueado, gravando copia: {fallback.name}")
        actual_path = fallback
        writer = pd.ExcelWriter(fallback, engine="openpyxl")

    with writer:
        for sheet_name, rows in sheets.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return actual_path


def _render_review_report(
    doc: dict[str, Any],
    results: dict[str, Any],
    metric_mentions: list[dict[str, Any]],
    metric_review: list[dict[str, Any]],
    divergence_candidates: list[dict[str, Any]],
    issues: list[dict[str, str]],
    numeric_triage_issues: list[dict[str, str]],
    output_dir: Path,
    metrics_path: Path,
    divergences_path: Path,
) -> str:
    captions_body = [c for c in doc.get("captions", []) if not c.get("is_toc")]
    captions_toc = [c for c in doc.get("captions", []) if c.get("is_toc")]
    severity_counts = pd.Series([i["severidade"] for i in issues]).value_counts().to_dict() if issues else {}
    likely_divergences = [
        i for i in numeric_triage_issues
        if i.get("categoria") == "Numeros/divergencia_candidata"
    ]

    lines = [
        "# Revisao piloto - Biota aquatica SAM Metais",
        "",
        "## Escopo",
        "",
        f"- Documento: `{doc.get('file_name')}`",
        f"- Pasta do pacote: `{output_dir}`",
        "- Grupos cruzados: Bentos, Fito, Zooplancton e Ictio.",
        "",
        "## Diagnostico do DOCX",
        "",
        f"- Palavras estimadas: {doc.get('words_count_estimate')}",
        f"- Paragrafos nao vazios: {doc.get('paragraphs_count')}",
        f"- Tabelas Word: {doc.get('tables_count')}",
        f"- Objetos inline Word: {doc.get('inline_shapes_count')}",
        f"- Arquivos de midia internos: {doc.get('zip_metadata', {}).get('media_files_count')}",
        f"- Headings detectados: {len(doc.get('headings', []))}",
        f"- Legendas no corpo: {len(captions_body)}",
        f"- Entradas de lista de figuras/quadros/sumario: {len(captions_toc)}",
        f"- Referencias textuais detectadas: {len(doc.get('references', []))}",
        f"- Comentarios Word: {len(doc.get('comments', []))}",
        "",
        "## Inventario de resultados",
        "",
    ]

    for row in results.get("summary", []):
        lines.append(
            f"- {row.get('grupo')}: {row.get('arquivos')} arquivos, "
            f"{row.get('png')} PNG, {row.get('xlsx')} XLSX, "
            f"duplicados por nome: {row.get('duplicated_file_names')}"
        )

    lines.extend(
        [
            "",
            "## Camada numerica inicial",
            "",
            "- A camada numerica e triagem assistida. Ela nao deve ser tratada como erro confirmado sem leitura humana.",
            f"- Metricas extraidas das planilhas: {len(metric_mentions)}",
            f"- Metricas com mencao numerica no texto do respectivo grupo: {sum(1 for item in metric_mentions if item.get('mencionado_no_texto_do_grupo'))}",
            f"- Metricas sem mencao numerica detectada no texto do respectivo grupo: {sum(1 for item in metric_mentions if not item.get('mencionado_no_texto_do_grupo'))}",
            f"- Itens de triagem numerica separados do checklist principal: {len(numeric_triage_issues)}",
            f"- Divergencias numericas candidatas avaliaveis: {len(likely_divergences)}",
            f"- Detalhe completo em `{metrics_path.name}`.",
            f"- Planilha especifica em `{divergences_path.name}`.",
            "",
            "## Checklist principal",
            "",
            f"- Total de achados documentais no checklist: {len(issues)}",
            f"- Por severidade: {severity_counts}",
            "",
        ]
    )

    if issues:
        for issue in issues:
            lines.extend(
                [
                    f"### {issue['severidade']} - {issue['categoria']}",
                    "",
                    issue["problema"],
                    "",
                    f"**Evidencia:** {issue.get('evidencia') or '-'}",
                    "",
                    f"**Sugestao:** {issue.get('sugestao') or '-'}",
                    "",
                ]
            )
    else:
        lines.append("Nenhum alerta inicial detectado nas regras deterministicas.")

    lines.extend(
        [
            "",
            "## Proximas camadas recomendadas",
            "",
            "1. Revisar primeiro o checklist principal; ele contem os achados mais rastreaveis.",
            "2. Usar a triagem numerica apenas como apoio visual, confirmando manualmente cada caso antes de corrigir.",
            "3. Mapear quais PNG/XLSX foram efetivamente incorporados ao DOCX.",
            "4. Revisar semanticamente as secoes de conclusao e indicadores por grupo.",
            "5. Evoluir para DOCX com comentarios automáticos somente depois de validar a planilha de inconsistencias.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Revisao piloto do relatorio de Biota Aquatica SAM Metais.")
    parser.add_argument("--products-root", type=Path, default=DEFAULT_PRODUCTS_ROOT)
    parser.add_argument("--docx", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    products_root = args.products_root
    docx_path = _resolve_docx(products_root, args.docx)
    output_dir = args.output_dir or (docx_path.parent / "_revisao_qualidade" / "piloto_biota_aquatica")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[revisao] DOCX: {docx_path}")
    print(f"[revisao] Saida: {output_dir}")

    doc = extract_docx_audit(docx_path)
    result_dirs = _default_result_dirs(products_root)
    results = inventory_results_dirs(result_dirs)
    numeric_metrics = extract_numeric_metrics(result_dirs)
    metric_mentions = audit_metric_mentions(numeric_metrics, doc)
    metric_review = classify_metric_mentions(metric_mentions)
    numeric_issues = build_numeric_issues(metric_review)
    divergence_candidates = detect_numeric_divergence_candidates(metric_review, doc)
    divergence_issues = build_numeric_divergence_issues(divergence_candidates)
    numeric_triage_issues = numeric_issues
    issues = build_initial_issues(doc, results)
    checklist_issues = prepare_issues_checklist(issues)
    numeric_triage_checklist = prepare_issues_checklist(numeric_triage_issues)

    (output_dir / "00_documento_extraido.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "04_texto_extraido.md").write_text(
        render_extracted_markdown(doc),
        encoding="utf-8",
    )
    (output_dir / "00_resultados_inventario.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _write_excel(
        output_dir / "01_estrutura_documento.xlsx",
        {
            "headings": doc.get("headings", []),
            "captions": doc.get("captions", []),
            "references": doc.get("references", []),
            "comments": doc.get("comments", []),
            "tables": doc.get("tables", []),
            "styles": [{"style": k, "count": v} for k, v in doc.get("styles_count", {}).items()],
        },
    )
    _write_excel(
        output_dir / "02_inventario_resultados.xlsx",
        {
            "summary": results.get("summary", []),
            "files": results.get("files", []),
            "xlsx_sheets": results.get("xlsx_sheets", []),
            "png_checks": results.get("png_checks", []),
        },
    )
    _write_excel(
        output_dir / "03_inconsistencias.xlsx",
        {
            "checklist": checklist_issues,
            "triagem_numerica": numeric_triage_checklist,
            "dicionario_revisao": review_status_dictionary(),
        },
    )
    metrics_path = _write_excel(
        output_dir / "05_metricas_numericas.xlsx",
        {
            "metricas": numeric_metrics,
            "mencoes_no_texto": metric_mentions,
            "revisao_metricas": metric_review,
            "alertas_metricas": numeric_issues,
            "divergencias_candidatas": divergence_candidates,
        },
    )
    divergences_path = _write_excel(
        output_dir / "06_divergencias_numericas_candidatas.xlsx",
        {
            "candidatas": divergence_candidates,
            "alertas_no_checklist": divergence_issues,
        },
    )
    (output_dir / "01_relatorio_revisao.md").write_text(
        _render_review_report(
            doc,
            results,
            metric_mentions,
            metric_review,
            divergence_candidates,
            issues,
            numeric_triage_issues,
            output_dir,
            metrics_path,
            divergences_path,
        ),
        encoding="utf-8",
    )
    (output_dir / "07_revisao_visual.html").write_text(
        render_visual_review_html(
            doc=doc,
            results=results,
            checklist_issues=checklist_issues,
            numeric_triage_issues=numeric_triage_checklist,
            metric_review=metric_review,
            divergence_candidates=[],
            output_dir=output_dir,
            metrics_path=metrics_path,
            divergences_path=divergences_path,
        ),
        encoding="utf-8",
    )

    print(f"[revisao] Issues documentais: {len(issues)}")
    print(f"[revisao] Triagem numerica: {len(numeric_triage_issues)}")
    print(f"[revisao] Metricas numericas: {len(metric_mentions)}")
    for issue in issues[:10]:
        print(f"  [{issue['severidade']}] {issue['categoria']}: {issue['problema']}")
    print(f"[revisao] HTML visual: {output_dir / '07_revisao_visual.html'}")
    print("[revisao] Pacote gerado com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
