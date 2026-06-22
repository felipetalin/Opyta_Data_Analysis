from __future__ import annotations

import base64
import mimetypes
from html import escape
from pathlib import Path
from typing import Iterable

from .models import Evidence, FigureReference, TechnicalReport
from .validation import ValidationIssue


LEVEL_LABELS = {
    "descritivo": "Descritivo",
    "comparativo": "Comparativo",
    "interpretativo": "Interpretativo",
    "recomendacao": "Recomendação",
    "causal": "Causal",
}


def _asset_src(path: Path, embed_assets: bool) -> str:
    if not embed_assets:
        return path.as_uri()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def _source_link(source_dir: Path, filename: str) -> str:
    path = source_dir / filename
    return f"<a href='{escape(path.as_uri())}'>{escape(filename)}</a>"


def _render_figure(
    figure: FigureReference,
    *,
    source_dir: Path,
    embed_assets: bool,
) -> str:
    path = source_dir / figure.filename
    if not path.exists():
        return f"<div class='warning'>Figura não encontrada: {escape(figure.filename)}</div>"
    links = [f"<a href='{escape(path.as_uri())}'>PNG</a>"]
    if figure.source_workbook:
        workbook = source_dir / figure.source_workbook
        if workbook.exists():
            links.append(f"<a href='{escape(workbook.as_uri())}'>Planilha-fonte</a>")
    return f"""
    <figure>
      <img src="{escape(_asset_src(path, embed_assets))}" alt="{escape(figure.alt_text or figure.caption)}">
      <figcaption>
        {escape(figure.caption)}
        <span class="figure-links">{" · ".join(links)}</span>
      </figcaption>
    </figure>
    """


def _render_evidence_card(evidence: Evidence, source_dir: Path) -> str:
    sources = " · ".join(_source_link(source_dir, source) for source in evidence.sources)
    metrics = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
        for key, value in evidence.metrics.items()
    )
    limitations = "".join(f"<li>{escape(item)}</li>" for item in evidence.limitations)
    interpretation = (
        f"<p><strong>Interpretação permitida:</strong> {escape(evidence.interpretation)}</p>"
        if evidence.interpretation
        else ""
    )
    return f"""
    <article class="evidence-card" id="evidence-{escape(evidence.evidence_id)}">
      <div class="evidence-head">
        <strong>{escape(evidence.evidence_id)} · {escape(evidence.title)}</strong>
        <span class="level level-{escape(evidence.inference_level)}">
          {escape(LEVEL_LABELS[evidence.inference_level])}
        </span>
      </div>
      <p>{escape(evidence.observation)}</p>
      {interpretation}
      <p><strong>Escopo:</strong> {escape(evidence.scope or "não informado")}</p>
      <table class="metric-table"><tbody>{metrics}</tbody></table>
      <p><strong>Fontes:</strong> {sources}</p>
      {f"<div class='limitations'><strong>Limitações:</strong><ul>{limitations}</ul></div>" if limitations else ""}
    </article>
    """


def _render_validation(issues: Iterable[ValidationIssue]) -> str:
    issues = list(issues)
    errors = sum(issue.severity == "ERROR" for issue in issues)
    warnings = sum(issue.severity == "WARNING" for issue in issues)
    rows = "".join(
        f"<tr><td>{escape(issue.severity)}</td><td>{escape(issue.code)}</td>"
        f"<td>{escape(issue.location)}</td><td>{escape(issue.message)}</td></tr>"
        for issue in issues
    )
    if not rows:
        rows = "<tr><td colspan='4'>Nenhum erro ou aviso textual detectado.</td></tr>"
    return f"""
    <div class="validation-summary">
      <div><strong>{errors}</strong><span>erros</span></div>
      <div><strong>{warnings}</strong><span>avisos</span></div>
    </div>
    <table>
      <thead><tr><th>Severidade</th><th>Código</th><th>Local</th><th>Mensagem</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """


def render_technical_report(
    report: TechnicalReport,
    *,
    source_dir: Path,
    validation_issues: Iterable[ValidationIssue] = (),
    embed_assets: bool = True,
) -> str:
    toc = "".join(
        f"<li><a href='#{escape(section.section_id)}'>{escape(section.title)}</a></li>"
        for section in report.sections
    )
    metadata = "".join(
        f"<div class='meta-item'><span>{escape(str(key))}</span><strong>{escape(str(value))}</strong></div>"
        for key, value in report.metadata.items()
    )

    section_html: list[str] = []
    for section in report.sections:
        paragraphs = []
        for paragraph in section.paragraphs:
            refs = " ".join(
                f"<a href='#evidence-{escape(evidence_id)}'>{escape(evidence_id)}</a>"
                for evidence_id in paragraph.evidence_ids
            )
            paragraphs.append(
                f"""
                <div class="narrative narrative-{escape(paragraph.role)}">
                  <p>{paragraph.text}</p>
                  <details class="trace">
                    <summary>Rastreabilidade</summary>
                    <div>
                      <span>{escape(LEVEL_LABELS[paragraph.inference_level])}</span>
                      Evidências: {refs}
                    </div>
                  </details>
                </div>
                """
            )
        table = ""
        if section.table_rows:
            rows = "".join(
                f"<tr><th>{escape(label)}</th><td>{value}</td></tr>"
                for label, value in section.table_rows
            )
            table = f"<table class='summary-table'><tbody>{rows}</tbody></table>"
        figures = "".join(
            _render_figure(
                figure,
                source_dir=source_dir,
                embed_assets=embed_assets,
            )
            for figure in section.figures
        )
        section_html.append(
            f"""
            <section id="{escape(section.section_id)}">
              <h2>{escape(section.title)}</h2>
              {table}
              {"".join(paragraphs)}
              <div class="figure-grid">{figures}</div>
            </section>
            """
        )

    evidence_html = "".join(
        _render_evidence_card(evidence, source_dir)
        for evidence in report.evidence
    )
    editorial = "".join(
        f"<li><strong>{escape(str(key))}:</strong> {escape(str(value))}</li>"
        for key, value in report.editorial_profile.items()
    )

    css = """
    :root {
      --blue: #002060;
      --blue-2: #1f4e79;
      --blue-soft: #eaf1f8;
      --ink: #1d2733;
      --muted: #5b6775;
      --line: #d6dee8;
      --surface: #ffffff;
      --bg: #f4f7fb;
      --warn: #8b5a00;
      --error: #a32222;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.62;
    }
    main { max-width: 1160px; margin: 0 auto; background: var(--surface); min-height: 100vh; }
    header { padding: 54px 68px 38px; color: #fff; background: linear-gradient(135deg, var(--blue), var(--blue-2)); }
    header h1 { margin: 0 0 10px; font-size: 32px; line-height: 1.18; }
    header p { margin: 5px 0; max-width: 900px; }
    .pilot-badge { display: inline-block; margin-bottom: 16px; padding: 5px 10px; border: 1px solid rgba(255,255,255,.55); border-radius: 999px; font-weight: 700; font-size: 12px; }
    .meta-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; padding: 22px 68px; border-bottom: 1px solid var(--line); }
    .meta-item { padding: 12px; border: 1px solid var(--line); border-radius: 9px; background: #fbfcfe; }
    .meta-item span { display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
    .meta-item strong { display: block; margin-top: 3px; font-size: 15px; }
    nav, section { padding: 28px 68px; }
    nav { border-bottom: 1px solid var(--line); background: #fbfcfe; }
    nav ol { columns: 2; margin: 0; padding-left: 22px; }
    nav a { color: var(--blue-2); text-decoration: none; }
    section { border-bottom: 1px solid var(--line); scroll-margin-top: 20px; }
    h2 { margin: 0 0 18px; color: var(--blue); font-size: 24px; }
    h3 { color: var(--blue-2); }
    .narrative { margin: 15px 0; }
    .narrative p { margin: 0; text-align: justify; }
    .narrative-interpretacao, .narrative-limitacao, .narrative-recomendacao {
      padding: 14px 16px;
      border-left: 4px solid var(--blue-2);
      background: var(--blue-soft);
    }
    .narrative-limitacao { border-left-color: #b27600; background: #fff8e8; }
    .trace { margin-top: 6px; color: var(--muted); font-size: 12px; }
    .trace summary { width: max-content; cursor: pointer; color: var(--blue-2); font-weight: 700; }
    .trace > div { margin-top: 5px; }
    .trace span { display: inline-block; margin-right: 8px; padding: 1px 7px; border-radius: 999px; background: #e8edf3; color: #344457; font-weight: 700; }
    .trace a { color: var(--blue-2); font-weight: 700; text-decoration: none; }
    .summary-table, table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
    th { background: #f0f4f8; }
    .summary-table th { width: 35%; }
    .figure-grid { display: grid; grid-template-columns: 1fr; gap: 20px; margin-top: 22px; }
    figure { margin: 0; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: #fff; }
    figure img { width: 100%; height: auto; display: block; }
    figcaption { padding: 10px 13px; color: var(--muted); font-size: 13px; }
    .figure-links { float: right; }
    .figure-links a, .evidence-card a { color: var(--blue-2); }
    .evidence-card { border: 1px solid var(--line); border-radius: 10px; padding: 17px; margin: 14px 0; }
    .evidence-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
    .level { padding: 3px 9px; border-radius: 999px; background: #e8edf3; font-size: 12px; white-space: nowrap; }
    .level-interpretativo, .level-recomendacao { background: #dcebf8; color: var(--blue); }
    .metric-table th { width: 45%; }
    .limitations { padding: 10px 14px; background: #fff8e8; border-radius: 8px; }
    .validation-summary { display: flex; gap: 12px; }
    .validation-summary div { min-width: 120px; padding: 12px; border: 1px solid var(--line); border-radius: 8px; text-align: center; }
    .validation-summary strong { display: block; font-size: 24px; color: var(--blue); }
    .validation-summary span { color: var(--muted); }
    .warning { padding: 12px; color: var(--warn); background: #fff8e8; }
    .audit-link { margin: 14px 0 0; font-size: 13px; }
    .audit-section { background: #fbfcfe; }
    .audit-section > details > summary {
      cursor: pointer;
      color: var(--blue);
      font-size: 22px;
      font-weight: 700;
    }
    .audit-content { margin-top: 18px; }
    code { font-family: Consolas, monospace; font-size: 12px; }
    @media (max-width: 760px) {
      header, nav, section { padding-left: 22px; padding-right: 22px; }
      .meta-grid { grid-template-columns: 1fr 1fr; padding-left: 22px; padding-right: 22px; }
      nav ol { columns: 1; }
    }
    @media print {
      body { background: #fff; }
      main { max-width: none; }
      .trace, .audit-section, .audit-link { display: none; }
      section { break-inside: avoid-page; }
    }
    """

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(report.title)}</title>
  <style>{css}</style>
</head>
<body>
<main>
  <header>
    <span class="pilot-badge">{escape(report.report_status.upper())} · NARRATIVA RASTREÁVEL</span>
    <h1>{escape(report.title)}</h1>
    <p>{escape(report.subtitle)}</p>
    <p>{escape(report.project_code)} · {escape(report.group)} · {escape(report.period)}</p>
  </header>
  <div class="meta-grid">{metadata}</div>
  <nav>
    <h2>Sumário</h2>
    <ol>{toc}</ol>
    <p class="audit-link"><a href="#evidencias">Acessar lastro de auditoria</a></p>
  </nav>
  {"".join(section_html)}
  <section id="perfil-editorial" class="audit-section">
    <details>
      <summary>Policy e perfil editorial</summary>
      <div class="audit-content"><ul>{editorial}</ul></div>
    </details>
  </section>
  <section id="evidencias" class="audit-section">
    <details>
      <summary>Matriz de evidências</summary>
      <div class="audit-content">
        <p>As evidências abaixo sustentam a narrativa e preservam métricas, fontes e limitações sem interromper a leitura principal.</p>
        {evidence_html}
      </div>
    </details>
  </section>
  <section id="validacao" class="audit-section">
    <details>
      <summary>Validação textual automática</summary>
      <div class="audit-content">{_render_validation(validation_issues)}</div>
    </details>
  </section>
</main>
<script>
  function openAuditTarget() {{
    if (!window.location.hash) return;
    const target = document.getElementById(window.location.hash.slice(1));
    if (!target) return;
    const details = target.matches("details") ? target : target.closest("details") || target.querySelector("details");
    if (details) details.open = true;
  }}
  window.addEventListener("DOMContentLoaded", openAuditTarget);
  window.addEventListener("hashchange", openAuditTarget);
</script>
</body>
</html>
"""
