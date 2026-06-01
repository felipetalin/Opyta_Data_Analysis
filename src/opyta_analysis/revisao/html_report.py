from __future__ import annotations

import re
from collections import Counter
from html import escape
from pathlib import Path
from typing import Any


SEVERITY_LABELS = {
    "CRITICA": "critica",
    "ALTA": "alta",
    "MEDIA": "media",
    "BAIXA": "baixa",
}


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _html(value: object) -> str:
    return escape(_text(value), quote=True)


def _class_token(value: object) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", _text(value).strip().lower())
    return token.strip("-") or "vazio"


def _short(value: object, limit: int = 260) -> str:
    text = " ".join(_text(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _parse_paragraph_id(evidence: object) -> str:
    match = re.search(r"paragrafo=([0-9]+)", _text(evidence))
    return match.group(1) if match else ""


def _split_candidate_numbers(value: object) -> list[str]:
    numbers = []
    for item in _text(value).split(","):
        item = item.strip()
        if item:
            numbers.append(item)
    return numbers


def _highlight_context(context: object, expected: object = "", candidates: object = "") -> str:
    rendered = _html(context)
    terms = []
    if _text(expected).strip():
        terms.append((_text(expected).strip(), "expected"))
    for candidate in _split_candidate_numbers(candidates):
        terms.append((candidate, "candidate"))

    for term, css_class in sorted(terms, key=lambda item: len(item[0]), reverse=True):
        escaped = re.escape(_html(term))
        rendered = re.sub(
            rf"(?<![\w.,-])({escaped})(?![\w.,-])",
            rf'<mark class="{css_class}">\1</mark>',
            rendered,
        )
    return rendered


def _candidate_lookup(candidates: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (
            _text(candidate.get("grupo")),
            _text(candidate.get("metrica")),
            _text(candidate.get("paragrafo")),
        )
        lookup.setdefault(key, candidate)
        loose_key = (_text(candidate.get("grupo")), _text(candidate.get("metrica")), "")
        lookup.setdefault(loose_key, candidate)
    return lookup


def _issue_candidate(issue: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    lookup = _candidate_lookup(candidates)
    paragraph = _parse_paragraph_id(issue.get("evidencia"))
    keys = [
        (_text(issue.get("grupo")), _text(issue.get("metrica")), paragraph),
        (_text(issue.get("grupo")), _text(issue.get("metrica")), ""),
    ]
    for key in keys:
        candidate = lookup.get(key)
        if candidate:
            return candidate
    return None


def _severity_counts(issues: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(_text(issue.get("severidade")) for issue in issues)
    return {key: counter.get(key, 0) for key in ["CRITICA", "ALTA", "MEDIA", "BAIXA"]}


def _stats_panel(doc: dict[str, Any], results: dict[str, Any], issues: list[dict[str, Any]], metrics: list[dict[str, Any]]) -> str:
    severity = _severity_counts(issues)
    result_files = sum(int(row.get("arquivos") or 0) for row in results.get("summary", []))
    png_files = sum(int(row.get("png") or 0) for row in results.get("summary", []))
    xlsx_files = sum(int(row.get("xlsx") or 0) for row in results.get("summary", []))
    stats = [
        ("Achados", len(issues), "Itens no checklist visual"),
        ("Alta/Critica", severity["CRITICA"] + severity["ALTA"], "Prioridade de entrega"),
        ("Metricas", len(metrics), "Valores extraidos dos resultados"),
        ("Resultados", result_files, f"{png_files} PNG / {xlsx_files} XLSX"),
        ("Comentarios Word", len(doc.get("comments", [])), "Comentarios internos detectados"),
    ]
    return "\n".join(
        f"""
        <section class="stat-card">
          <span>{_html(label)}</span>
          <strong>{_html(value)}</strong>
          <small>{_html(detail)}</small>
        </section>
        """
        for label, value, detail in stats
    )


def _artifact_links(metrics_path: Path, divergences_path: Path) -> str:
    artifacts = [
        ("Checklist Excel", "03_inconsistencias.xlsx"),
        ("Metricas", metrics_path.name),
        ("Divergencias", divergences_path.name),
        ("Texto extraido", "04_texto_extraido.md"),
    ]
    return "\n".join(
        f'<a class="artifact-link" href="{_html(file_name)}">{_html(label)}</a>'
        for label, file_name in artifacts
    )


def _issue_card(issue: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    severity = _text(issue.get("severidade"))
    category = _text(issue.get("categoria"))
    group = _text(issue.get("grupo")) or "Geral"
    issue_type = _text(issue.get("tipo_achado")) or "alerta"
    candidate = _issue_candidate(issue, candidates)
    details = ""
    if candidate:
        details = f"""
        <div class="trace-grid">
          <div>
            <h4>Dado de origem</h4>
            <dl>
              <dt>Grupo</dt><dd>{_html(candidate.get("grupo"))}</dd>
              <dt>Metrica</dt><dd>{_html(candidate.get("rotulo_metrica") or candidate.get("metrica"))}</dd>
              <dt>Valor esperado</dt><dd><mark class="expected">{_html(candidate.get("valor_resultado"))}</mark></dd>
              <dt>Arquivo</dt><dd>{_html(candidate.get("arquivo_origem"))}</dd>
              <dt>Evidencia</dt><dd>{_html(candidate.get("evidencia_resultado"))}</dd>
            </dl>
          </div>
          <div>
            <h4>Contexto no relatorio</h4>
            <p class="context">
              {_highlight_context(candidate.get("contexto"), candidate.get("valor_resultado"), candidate.get("valores_texto_candidatos"))}
            </p>
          </div>
        </div>
        """

    return f"""
    <article class="review-card issue-card sev-{_class_token(severity)}"
      data-severity="{_html(severity)}"
      data-category="{_html(category)}"
      data-group="{_html(group)}"
      data-type="{_html(issue_type)}"
      data-search="{_html(' '.join(_text(issue.get(k)) for k in ['id_revisao', 'categoria', 'problema', 'evidencia', 'sugestao', 'grupo', 'metrica']))}">
      <header>
        <div>
          <span class="review-id">{_html(issue.get("id_revisao"))}</span>
          <span class="pill severity">{_html(SEVERITY_LABELS.get(severity, severity.lower()))}</span>
          <span class="pill group">{_html(group)}</span>
          <span class="pill type">{_html(issue_type)}</span>
        </div>
        <span class="status">{_html(issue.get("status") or "pendente")}</span>
      </header>
      <h3>{_html(issue.get("problema"))}</h3>
      <dl class="compact">
        <dt>Categoria</dt><dd>{_html(category)}</dd>
        <dt>Evidencia</dt><dd>{_html(issue.get("evidencia") or "-")}</dd>
        <dt>Sugestao</dt><dd>{_html(issue.get("sugestao") or "-")}</dd>
      </dl>
      {details}
    </article>
    """


def _metric_rows(metric_review: list[dict[str, Any]]) -> str:
    ordered = sorted(
        metric_review,
        key=lambda row: (_text(row.get("grupo")), _text(row.get("status_revisao")), _text(row.get("metrica"))),
    )
    return "\n".join(
        f"""
        <tr>
          <td>{_html(row.get("grupo"))}</td>
          <td>{_html(row.get("rotulo_metrica") or row.get("metrica"))}</td>
          <td class="number">{_html(row.get("valor_texto"))}</td>
          <td>{_html(row.get("status_revisao"))}</td>
          <td>{_html(row.get("arquivo_origem"))}</td>
          <td>{_html(_short(row.get("melhor_contexto"), 180) or "-")}</td>
        </tr>
        """
        for row in ordered
    )


def _divergence_card(candidate: dict[str, Any]) -> str:
    has_expected = bool(candidate.get("valor_resultado_aparece_no_contexto"))
    state = "valor aparece no contexto" if has_expected else "valor esperado ausente no contexto"
    return f"""
    <article class="review-card divergence-card {'muted' if has_expected else ''}"
      data-severity="BAIXA"
      data-category="Numeros/divergencia_candidata"
      data-group="{_html(candidate.get("grupo"))}"
      data-type="{_html(candidate.get("status_candidato"))}"
      data-search="{_html(' '.join(_text(candidate.get(k)) for k in ['grupo', 'metrica', 'rotulo_metrica', 'valor_resultado', 'valores_texto_candidatos', 'contexto']))}">
      <header>
        <div>
          <span class="pill group">{_html(candidate.get("grupo"))}</span>
          <span class="pill type">{_html(candidate.get("status_candidato"))}</span>
        </div>
        <span class="status">{_html(state)}</span>
      </header>
      <h3>{_html(candidate.get("rotulo_metrica") or candidate.get("metrica"))}</h3>
      <div class="trace-grid">
        <div>
          <h4>Resultado calculado</h4>
          <dl>
            <dt>Valor</dt><dd><mark class="expected">{_html(candidate.get("valor_resultado"))}</mark></dd>
            <dt>Arquivo</dt><dd>{_html(candidate.get("arquivo_origem"))}</dd>
            <dt>Evidencia</dt><dd>{_html(candidate.get("evidencia_resultado"))}</dd>
            <dt>Paragrafo</dt><dd>{_html(candidate.get("paragrafo"))}</dd>
            <dt>Score</dt><dd>{_html(candidate.get("score_relevancia"))}</dd>
          </dl>
        </div>
        <div>
          <h4>Texto encontrado</h4>
          <p class="context">
            {_highlight_context(candidate.get("contexto"), candidate.get("valor_resultado"), candidate.get("valores_texto_candidatos"))}
          </p>
        </div>
      </div>
    </article>
    """


def _triage_issue_card(issue: dict[str, Any]) -> str:
    severity = _text(issue.get("severidade"))
    category = _text(issue.get("categoria"))
    group = _text(issue.get("grupo")) or "Geral"
    return f"""
    <article class="review-card triage-card sev-{_class_token(severity)}"
      data-severity="{_html(severity)}"
      data-category="{_html(category)}"
      data-group="{_html(group)}"
      data-type="{_html(issue.get("tipo_achado") or "triagem")}"
      data-search="{_html(' '.join(_text(issue.get(k)) for k in ['id_revisao', 'categoria', 'problema', 'evidencia', 'sugestao', 'grupo', 'metrica']))}">
      <header>
        <div>
          <span class="review-id">{_html(issue.get("id_revisao"))}</span>
          <span class="pill severity">{_html(SEVERITY_LABELS.get(severity, severity.lower()))}</span>
          <span class="pill group">{_html(group)}</span>
          <span class="pill type">triagem numerica</span>
        </div>
        <span class="status">nao e erro confirmado</span>
      </header>
      <h3>{_html(issue.get("problema"))}</h3>
      <dl class="compact">
        <dt>Categoria</dt><dd>{_html(category)}</dd>
        <dt>Evidencia</dt><dd>{_html(issue.get("evidencia") or "-")}</dd>
        <dt>Sugestao</dt><dd>{_html(issue.get("sugestao") or "-")}</dd>
      </dl>
    </article>
    """


def _visible_divergence_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    ordered = sorted(
        candidates,
        key=lambda row: (
            bool(row.get("valor_resultado_aparece_no_contexto")),
            -int(row.get("score_relevancia") or 0),
            int(row.get("paragrafo") or 0),
        ),
    )
    for candidate in ordered:
        if candidate.get("valor_resultado_aparece_no_contexto"):
            continue
        if int(candidate.get("score_relevancia") or 0) < 8:
            continue
        key = (_text(candidate.get("grupo")), _text(candidate.get("metrica")))
        if key in seen:
            continue
        seen.add(key)
        visible.append(candidate)
    return visible


def _results_table(results: dict[str, Any]) -> str:
    return "\n".join(
        f"""
        <tr>
          <td>{_html(row.get("grupo"))}</td>
          <td>{_html(row.get("arquivos"))}</td>
          <td>{_html(row.get("png"))}</td>
          <td>{_html(row.get("xlsx"))}</td>
          <td>{_html(row.get("duplicated_file_names"))}</td>
          <td>{_html(row.get("pasta"))}</td>
        </tr>
        """
        for row in results.get("summary", [])
    )


def _select_options(values: list[str], label: str) -> str:
    options = [f'<option value="">{_html(label)}</option>']
    options.extend(f'<option value="{_html(value)}">{_html(value)}</option>' for value in sorted(set(values)) if value)
    return "\n".join(options)


def render_visual_review_html(
    *,
    doc: dict[str, Any],
    results: dict[str, Any],
    checklist_issues: list[dict[str, Any]],
    numeric_triage_issues: list[dict[str, Any]],
    metric_review: list[dict[str, Any]],
    divergence_candidates: list[dict[str, Any]],
    output_dir: Path,
    metrics_path: Path,
    divergences_path: Path,
) -> str:
    visual_divergences = _visible_divergence_candidates(divergence_candidates)
    categories = [_text(issue.get("categoria")) for issue in checklist_issues + numeric_triage_issues]
    groups = [_text(issue.get("grupo") or "Geral") for issue in checklist_issues]
    groups.extend(_text(issue.get("grupo") or "Geral") for issue in numeric_triage_issues)
    groups.extend(_text(candidate.get("grupo")) for candidate in visual_divergences)
    severities = [_text(issue.get("severidade")) for issue in checklist_issues + numeric_triage_issues]

    issue_cards = "\n".join(_issue_card(issue, divergence_candidates) for issue in checklist_issues)
    triage_cards = "\n".join(_triage_issue_card(issue) for issue in numeric_triage_issues)
    divergence_cards = "\n".join(_divergence_card(candidate) for candidate in visual_divergences)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Revisao visual - {_html(doc.get("file_name"))}</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #667085;
      --line: #d9e0e7;
      --accent: #0f766e;
      --blue: #2563eb;
      --amber: #b45309;
      --red: #b42318;
      --green: #2f855a;
      --violet: #7c3aed;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.45;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100vh;
    }}
    aside {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      background: #102a43;
      color: #eff6ff;
      padding: 22px;
    }}
    main {{ padding: 22px 26px 48px; }}
    h1 {{ font-size: 22px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 18px; margin: 26px 0 12px; letter-spacing: 0; }}
    h3 {{ font-size: 17px; margin: 12px 0; letter-spacing: 0; }}
    h4 {{ font-size: 13px; margin: 0 0 8px; color: var(--muted); text-transform: uppercase; letter-spacing: 0; }}
    .doc-name {{ color: #bcccdc; font-size: 13px; word-break: break-word; }}
    .artifact-list {{ display: grid; gap: 8px; margin: 18px 0; }}
    .artifact-link {{
      color: #e0f2fe;
      text-decoration: none;
      border: 1px solid rgba(255,255,255,.22);
      border-radius: 8px;
      padding: 8px 10px;
      display: block;
    }}
    .tabs {{ display: grid; gap: 8px; margin-top: 22px; }}
    .tab-button {{
      width: 100%;
      border: 0;
      border-radius: 8px;
      padding: 10px 12px;
      text-align: left;
      color: #dbeafe;
      background: rgba(255,255,255,.08);
      cursor: pointer;
      font-weight: 700;
    }}
    .tab-button.active {{ background: #e0f2fe; color: #102a43; }}
    .topbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) 160px 220px 170px;
      gap: 10px;
      width: 100%;
      margin: 12px 0 18px;
    }}
    input, select {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 11px;
      background: #fff;
      color: var(--ink);
      font-size: 14px;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(130px, 1fr));
      gap: 10px;
      margin: 14px 0 18px;
    }}
    .stat-card, .review-card, .table-wrap {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
    }}
    .stat-card {{ padding: 14px; }}
    .stat-card span {{ display: block; color: var(--muted); font-size: 12px; }}
    .stat-card strong {{ display: block; font-size: 26px; margin: 2px 0; }}
    .stat-card small {{ color: var(--muted); }}
    .review-card {{
      padding: 16px;
      margin-bottom: 12px;
      border-left: 5px solid var(--line);
    }}
    .review-card header {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }}
    .sev-critica, .sev-alta {{ border-left-color: var(--red); }}
    .sev-media {{ border-left-color: var(--amber); }}
    .sev-baixa {{ border-left-color: var(--blue); }}
    .muted {{ opacity: .78; }}
    .pill, .status, .review-id {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      font-weight: 700;
      margin: 0 4px 4px 0;
      background: #eef2f6;
      color: #243b53;
    }}
    .severity {{ background: #fee2e2; color: var(--red); }}
    .group {{ background: #dcfce7; color: #166534; }}
    .type {{ background: #ede9fe; color: var(--violet); }}
    .status {{ background: #e0f2fe; color: #075985; white-space: nowrap; }}
    dl.compact {{
      display: grid;
      grid-template-columns: 120px minmax(0, 1fr);
      gap: 7px 12px;
      margin: 8px 0 0;
    }}
    dt {{ color: var(--muted); font-weight: 700; }}
    dd {{ margin: 0; word-break: break-word; }}
    .trace-grid {{
      display: grid;
      grid-template-columns: minmax(220px, 330px) minmax(0, 1fr);
      gap: 14px;
      border-top: 1px solid var(--line);
      margin-top: 14px;
      padding-top: 14px;
    }}
    .context {{
      margin: 0;
      padding: 12px;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 14px;
    }}
    mark {{
      border-radius: 4px;
      padding: 1px 4px;
      font-weight: 700;
    }}
    mark.expected {{ background: #bbf7d0; color: #14532d; }}
    mark.candidate {{ background: #fde68a; color: #78350f; }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .table-wrap {{ overflow: auto; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
      min-width: 860px;
    }}
    th, td {{
      padding: 10px 11px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #edf2f7; color: #243b53; }}
    td.number {{ font-weight: 700; white-space: nowrap; }}
    .empty-state {{
      background: #fff;
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 16px;
      color: var(--muted);
    }}
    .notice {{
      background: #fff7ed;
      border: 1px solid #fed7aa;
      color: #7c2d12;
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 12px;
      font-size: 14px;
    }}
    @media (max-width: 1040px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{ position: relative; height: auto; }}
      .filters, .stat-grid, .trace-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <h1>Revisao visual</h1>
      <div class="doc-name">{_html(doc.get("file_name"))}</div>
      <div class="artifact-list">{_artifact_links(metrics_path, divergences_path)}</div>
      <nav class="tabs">
        <button class="tab-button active" data-tab="checklist">Checklist</button>
        <button class="tab-button" data-tab="triagem">Triagem numerica</button>
        <button class="tab-button" data-tab="metricas">Metricas</button>
        <button class="tab-button" data-tab="inventario">Inventario</button>
      </nav>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <h2>Biota aquatica SAM Metais</h2>
          <div class="doc-name" style="color: var(--muted)">Pacote: {_html(output_dir)}</div>
        </div>
      </div>
      <section class="stat-grid">{_stats_panel(doc, results, checklist_issues, metric_review)}</section>
      <section class="filters">
        <input id="search" type="search" placeholder="Buscar por termo, grupo, arquivo ou paragrafo">
        <select id="severity">{_select_options(severities, "Severidade")}</select>
        <select id="category">{_select_options(categories, "Categoria")}</select>
        <select id="group">{_select_options(groups, "Grupo")}</select>
      </section>

      <section id="checklist" class="tab-panel active">
        {issue_cards or '<div class="empty-state">Nenhum achado no checklist.</div>'}
      </section>

      <section id="triagem" class="tab-panel">
        <div class="notice">
          Esta aba e apoio de investigacao. Os itens numericos abaixo nao sao erros confirmados; use apenas para orientar a leitura do relatorio e dos arquivos de origem.
        </div>
        {triage_cards or ''}
        {divergence_cards or '<div class="empty-state">Nenhuma divergencia candidata prioritaria.</div>'}
      </section>

      <section id="metricas" class="tab-panel">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Grupo</th><th>Metrica</th><th>Valor</th><th>Status</th><th>Arquivo</th><th>Contexto encontrado</th></tr>
            </thead>
            <tbody>{_metric_rows(metric_review)}</tbody>
          </table>
        </div>
      </section>

      <section id="inventario" class="tab-panel">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Grupo</th><th>Arquivos</th><th>PNG</th><th>XLSX</th><th>Nomes duplicados</th><th>Pasta</th></tr>
            </thead>
            <tbody>{_results_table(results)}</tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
  <script>
    const buttons = document.querySelectorAll('.tab-button');
    const panels = document.querySelectorAll('.tab-panel');
    const filters = ['search', 'severity', 'category', 'group'].map(id => document.getElementById(id));

    function setTab(name) {{
      buttons.forEach(button => button.classList.toggle('active', button.dataset.tab === name));
      panels.forEach(panel => panel.classList.toggle('active', panel.id === name));
      applyFilters();
    }}

    function matches(card, q, severity, category, group) {{
      const haystack = (card.dataset.search || '').toLowerCase();
      return (!q || haystack.includes(q))
        && (!severity || card.dataset.severity === severity)
        && (!category || card.dataset.category === category)
        && (!group || card.dataset.group === group);
    }}

    function applyFilters() {{
      const q = document.getElementById('search').value.trim().toLowerCase();
      const severity = document.getElementById('severity').value;
      const category = document.getElementById('category').value;
      const group = document.getElementById('group').value;
      document.querySelectorAll('.issue-card, .triage-card, .divergence-card').forEach(card => {{
        card.style.display = matches(card, q, severity, category, group) ? '' : 'none';
      }});
    }}

    buttons.forEach(button => button.addEventListener('click', () => setTab(button.dataset.tab)));
    filters.forEach(input => input.addEventListener('input', applyFilters));
  </script>
</body>
</html>
"""
