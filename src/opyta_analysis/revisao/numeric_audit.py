from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


GROUP_KEYWORDS = {
    "Bentos": ["macroinvertebr", "bentonic", "zoobent", "bentos"],
    "Fito": ["fitoplanct"],
    "Zooplancton": ["zooplanct"],
    "Ictio": ["ictiofauna", "peixes", "ictio"],
}

METRIC_POLICIES = {
    "riqueza_total_composicao": {
        "rotulo": "riqueza total da composicao",
        "severidade": "MEDIA",
        "registrar_se_ausente": True,
        "termos": ["riqueza", "taxon", "taxons", "especie", "registr"],
    },
    "riqueza_max_por_ponto_campanha": {
        "rotulo": "maior riqueza por ponto/campanha",
        "severidade": "BAIXA",
        "registrar_se_ausente": True,
        "termos": ["riqueza", "ponto", "taxon", "taxons", "especie", "maior"],
        "usar_evidencia": True,
    },
    "riqueza_max_total_por_ponto": {
        "rotulo": "maior riqueza total por ponto",
        "severidade": "BAIXA",
        "registrar_se_ausente": True,
        "termos": ["riqueza", "ponto", "taxon", "taxons", "especie", "maior"],
        "usar_evidencia": True,
    },
    "abundancia_total_soma": {
        "rotulo": "abundancia total",
        "severidade": "MEDIA",
        "registrar_se_ausente": True,
        "termos": ["abundancia", "total", "individuo", "organismo"],
    },
    "abundancia_max_por_ponto_campanha": {
        "rotulo": "maior abundancia por ponto/campanha",
        "severidade": "BAIXA",
        "registrar_se_ausente": True,
        "termos": ["abundancia", "ponto", "individuo", "organismo", "maior"],
        "usar_evidencia": True,
    },
    "shannon_max": {
        "rotulo": "maior indice de Shannon",
        "severidade": "BAIXA",
        "registrar_se_ausente": False,
        "termos": ["shannon", "diversidade", "indice", "maior"],
    },
    "suficiencia_riqueza_obs_final": {
        "rotulo": "riqueza observada final na suficiencia amostral",
        "severidade": "BAIXA",
        "registrar_se_ausente": False,
        "termos": ["suficiencia", "riqueza", "observada", "amostral"],
    },
    "suficiencia_jackknife1_final": {
        "rotulo": "riqueza estimada final por Jackknife 1",
        "severidade": "BAIXA",
        "registrar_se_ausente": False,
        "termos": ["suficiencia", "jackknife", "riqueza", "estim"],
    },
    "bmwp_max": {
        "rotulo": "maior BMWP",
        "severidade": "MEDIA",
        "registrar_se_ausente": True,
        "termos": ["bmwp", "indice", "score", "maior"],
        "usar_evidencia": True,
    },
}


def _read_xlsx(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)


def _first_existing(base: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(path for path in base.glob(pattern) if path.is_file())
        if matches:
            return matches[0]
    return None


def _safe_num(value: object) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _norm_text(value: object) -> str:
    return _strip_accents(str(value or "")).lower()


def _heading_level(style: object) -> int:
    match = re.search(r"(\d+)", str(style or ""))
    if not match:
        return 9
    return int(match.group(1))


def _group_heading_match(text: object, group: str) -> bool:
    normalized = _norm_text(text)
    if group == "Bentos":
        return "macroinvertebr" in normalized or "zoobent" in normalized or "bentos" in normalized
    if group == "Fito":
        return "fitoplanct" in normalized
    if group == "Zooplancton":
        return "zooplanct" in normalized
    if group == "Ictio":
        return "ictiofauna" in normalized or normalized.strip() == "ictio"
    return group.lower() in normalized


def _heading_interval_end(headings: list[dict[str, Any]], idx: int) -> int:
    heading = headings[idx]
    level = _heading_level(heading.get("style"))
    for next_heading in headings[idx + 1:]:
        if _heading_level(next_heading.get("style")) <= level:
            return int(next_heading.get("paragraph_index", 0))
    return 10**12


def _inside_interval(value: int, intervals: list[tuple[int, int]]) -> bool:
    return any(start <= value < end for start, end in intervals)


def _fmt_number(value: float | int | None, decimals: int = 2) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isfinite(value) and abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.{decimals}f}".rstrip("0").rstrip(".")


def _metric_row(
    group: str,
    metric: str,
    value: object,
    source_file: Path | None,
    evidence: str = "",
    *,
    value_display: str | None = None,
) -> dict[str, Any]:
    return {
        "grupo": group,
        "metrica": metric,
        "valor": value,
        "valor_texto": value_display if value_display is not None else str(value),
        "arquivo_origem": source_file.name if source_file else "",
        "evidencia_resultado": evidence,
    }


def _clean_cell(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _is_blank_row(row: pd.Series) -> bool:
    return all(not _clean_cell(value) for value in row.tolist())


def _is_embedded_header_row(row: pd.Series) -> bool:
    values = [_norm_text(value).strip() for value in row.tolist() if _clean_cell(value)]
    if not values:
        return False
    header_terms = {
        "ordem",
        "filo",
        "classe",
        "familia",
        "familia",
        "genero",
        "taxon",
        "nome cientifico",
        "nome comum",
        "nome popular",
        "campanha",
        "status de ameaca",
    }
    matches = sum(1 for value in values if value in header_terms)
    return matches >= 2 or any(value.startswith("status de ameaca") for value in values)


def _composition_prefix(df: pd.DataFrame) -> pd.DataFrame:
    end = len(df)
    has_data = False
    for idx, row in df.iterrows():
        if _is_blank_row(row):
            if has_data:
                end = idx
                break
            continue
        if has_data and _is_embedded_header_row(row):
            end = idx
            break
        has_data = True
    return df.iloc[:end].copy()


def _taxon_column(df: pd.DataFrame) -> str | None:
    candidates = {
        "nome cientifico": 100,
        "taxon": 90,
        "taxa": 80,
        "especie": 70,
        "especies": 70,
    }
    best: tuple[int, str] | None = None
    for col in df.columns:
        normalized = _norm_text(col).strip()
        score = candidates.get(normalized)
        if score is None:
            continue
        if best is None or score > best[0]:
            best = (score, str(col))
    return best[1] if best else None


def _composition_richness_metric(group: str, composition: Path) -> dict[str, Any]:
    df = _read_xlsx(composition)
    prefix = _composition_prefix(df)
    taxon_col = _taxon_column(prefix)
    if taxon_col is None:
        value = int(len(prefix.dropna(how="all")))
        evidence = f"linhas nao vazias da tabela de composicao; linhas_consideradas={len(prefix)}; linhas_totais={len(df)}"
        return _metric_row(group, "riqueza_total_composicao", value, composition, evidence, value_display=_fmt_number(value))

    values = prefix[taxon_col].dropna().astype(str).str.strip()
    values = values[(values != "") & (values != "-")]
    value = int(values.nunique())
    evidence = (
        f"taxons unicos em {taxon_col}; "
        f"linhas_consideradas={len(prefix)}; linhas_totais={len(df)}"
    )
    return _metric_row(group, "riqueza_total_composicao", value, composition, evidence, value_display=_fmt_number(value))


def _extract_group_metrics(group: str, base: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    composition = _first_existing(base, ["01_tabela_composicao*.xlsx"])
    if composition:
        rows.append(_composition_richness_metric(group, composition))

    richness_point = _first_existing(base, ["02_df_riqueza_por_ponto*.xlsx"])
    if richness_point:
        df = _read_xlsx(richness_point)
        if "riqueza" in df.columns and not df.empty:
            idx = pd.to_numeric(df["riqueza"], errors="coerce").idxmax()
            max_value = _safe_num(df.loc[idx, "riqueza"])
            evidence = f"{df.loc[idx].get('nome_ponto', '')}; {df.loc[idx].get('nome_campanha', '')}"
            rows.append(_metric_row(group, "riqueza_max_por_ponto_campanha", max_value, richness_point, evidence, value_display=_fmt_number(max_value)))
            rows.append(_metric_row(group, "unidades_riqueza_por_ponto_campanha", int(len(df)), richness_point, "linhas da matriz ponto-campanha"))

    richness_total_point = _first_existing(base, ["06A_df_riqueza_total_por_ponto*.xlsx"])
    if richness_total_point:
        df = _read_xlsx(richness_total_point)
        col = "riqueza_taxons" if "riqueza_taxons" in df.columns else None
        if col and not df.empty:
            idx = pd.to_numeric(df[col], errors="coerce").idxmax()
            max_value = _safe_num(df.loc[idx, col])
            evidence = f"{df.loc[idx].get('nome_ponto', '')}"
            rows.append(_metric_row(group, "riqueza_max_total_por_ponto", max_value, richness_total_point, evidence, value_display=_fmt_number(max_value)))
            rows.append(_metric_row(group, "pontos_com_riqueza_total", int(len(df)), richness_total_point, "linhas da tabela por ponto"))

    abundance_point = _first_existing(base, ["03_df_abundancia_por_ponto*.xlsx"])
    if abundance_point:
        df = _read_xlsx(abundance_point)
        if "abundancia_total" in df.columns and not df.empty:
            vals = pd.to_numeric(df["abundancia_total"], errors="coerce")
            idx = vals.idxmax()
            max_value = _safe_num(df.loc[idx, "abundancia_total"])
            total = float(vals.sum())
            rows.append(_metric_row(group, "abundancia_total_soma", total, abundance_point, "soma da abundancia por ponto", value_display=_fmt_number(total)))
            evidence = f"{df.loc[idx].get('nome_ponto', '')}; {df.loc[idx].get('nome_campanha', '')}"
            rows.append(_metric_row(group, "abundancia_max_por_ponto_campanha", max_value, abundance_point, evidence, value_display=_fmt_number(max_value)))

    diversity = _first_existing(base, ["10_df_diversidade_alfa*.xlsx"])
    if diversity:
        df = _read_xlsx(diversity)
        for col, metric in [("Shannon_H", "shannon_max"), ("Pielou_J", "pielou_max")]:
            if col in df.columns and not df.empty:
                vals = pd.to_numeric(df[col], errors="coerce")
                idx = vals.idxmax()
                value = _safe_num(df.loc[idx, col])
                evidence = f"{df.loc[idx].get('nome_ponto', '')}; {df.loc[idx].get('nome_campanha', '')}"
                rows.append(_metric_row(group, metric, value, diversity, evidence, value_display=_fmt_number(value, 3)))

    curve = _first_existing(base, ["12_df_curva_suficiencia*.xlsx"])
    if curve:
        df = _read_xlsx(curve)
        if not df.empty:
            last = df.iloc[-1]
            for col, metric in [
                ("n_amostras", "suficiencia_n_amostras"),
                ("riqueza_obs_media", "suficiencia_riqueza_obs_final"),
                ("riqueza_est_jackknife1_media", "suficiencia_jackknife1_final"),
            ]:
                if col in df.columns:
                    value = _safe_num(last.get(col))
                    rows.append(_metric_row(group, metric, value, curve, "ultima linha da curva", value_display=_fmt_number(value, 2)))

    bmwp = _first_existing(base, ["11_df_bmwp*.xlsx"])
    if bmwp:
        df = _read_xlsx(bmwp)
        if "bmwp_score" in df.columns and not df.empty:
            vals = pd.to_numeric(df["bmwp_score"], errors="coerce")
            idx = vals.idxmax()
            value = _safe_num(df.loc[idx, "bmwp_score"])
            evidence = f"{df.loc[idx].get('nome_ponto', '')}; {df.loc[idx].get('nome_campanha', '')}; {df.loc[idx].get('classificacao', '')}"
            rows.append(_metric_row(group, "bmwp_max", value, bmwp, evidence, value_display=_fmt_number(value)))
        if "classificacao" in df.columns:
            counts = df["classificacao"].astype(str).value_counts().to_dict()
            for name, count in counts.items():
                rows.append(_metric_row(group, f"bmwp_classificacao_{name}", int(count), bmwp, "contagem de pontos/campanhas"))

    ept = _first_existing(base, ["12_df_ept_chol*.xlsx"])
    if ept:
        df = _read_xlsx(ept)
        for col, metric in [("pct_ept", "pct_ept_max"), ("pct_chol", "pct_chol_max")]:
            if col in df.columns and not df.empty:
                vals = pd.to_numeric(df[col], errors="coerce")
                idx = vals.idxmax()
                value = _safe_num(df.loc[idx, col])
                evidence = f"{df.loc[idx].get('nome_ponto', '')}; {df.loc[idx].get('nome_campanha', '')}"
                rows.append(_metric_row(group, metric, value, ept, evidence, value_display=_fmt_number(value, 1)))

    return rows


def extract_numeric_metrics(result_dirs: dict[str, str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group, raw_dir in result_dirs.items():
        base = Path(raw_dir)
        if not base.exists():
            continue
        rows.extend(_extract_group_metrics(group, base))
    return rows


def _group_paragraphs(doc: dict[str, Any], group: str) -> list[dict[str, Any]]:
    paragraphs = [
        p for p in doc.get("paragraphs", [])
        if not p.get("is_toc") and str(p.get("text", "")).strip()
    ]
    headings = [
        h for h in doc.get("headings", [])
        if h.get("paragraph_index") is not None
    ]
    headings = sorted(headings, key=lambda h: int(h.get("paragraph_index", 0)))

    intervals: list[tuple[int, int]] = []
    for idx, heading in enumerate(headings):
        if not _group_heading_match(heading.get("text", ""), group):
            continue
        start = int(heading.get("paragraph_index", 0))
        intervals.append((start, _heading_interval_end(headings, idx)))

    result_starts = [
        int(h.get("paragraph_index", 0))
        for h in headings
        if _norm_text(h.get("text", "")).strip() == "resultados"
    ]
    primary_intervals: list[tuple[int, int]] = []
    for idx, heading in enumerate(headings):
        text = _norm_text(heading.get("text", ""))
        start = int(heading.get("paragraph_index", 0))
        if "dados primarios" not in text:
            continue
        top_start = max(
            [
                int(h.get("paragraph_index", 0))
                for h in headings[:idx + 1]
                if _heading_level(h.get("style")) == 1
            ],
            default=0,
        )
        after_results = any(top_start < result_start < start for result_start in result_starts)
        if not after_results:
            continue
        if _group_heading_match(text, group) or _inside_interval(start, intervals):
            primary_intervals.append((start, _heading_interval_end(headings, idx)))

    if primary_intervals:
        scoped = [
            paragraph for paragraph in paragraphs
            if _inside_interval(int(paragraph.get("paragraph_index", 0)), primary_intervals)
        ]
        if scoped:
            return scoped

    if intervals:
        scoped = [
            paragraph for paragraph in paragraphs
            if _inside_interval(int(paragraph.get("paragraph_index", 0)), intervals)
        ]
        if scoped:
            return scoped

    keywords = GROUP_KEYWORDS.get(group, [group.lower()])
    return [
        paragraph for paragraph in paragraphs
        if any(re.search(keyword, str(paragraph.get("text", "")), flags=re.IGNORECASE) for keyword in keywords)
    ]


def _number_patterns(value_text: str, value: object = None) -> list[str]:
    if not value_text:
        return []
    raw_values = {str(value_text).strip()}

    numeric = _safe_num(value)
    if numeric is None:
        numeric = _safe_num(value_text)
    if numeric is not None and math.isfinite(numeric):
        if abs(numeric - round(numeric)) < 1e-9:
            raw_values.add(str(int(round(numeric))))
        else:
            for decimals in (1, 2, 3):
                raw_values.add(_fmt_number(numeric, decimals))

    patterns = set()
    for raw in raw_values:
        if not raw:
            continue
        variants = {raw}
        if "." in raw:
            variants.add(raw.replace(".", ","))
        if "," in raw:
            variants.add(raw.replace(",", "."))
        for variant in variants:
            patterns.add(re.escape(variant))
    return sorted(patterns, key=len, reverse=True)


def _contains_metric_number(text: str, value_text: str, value: object = None) -> bool:
    return any(
        re.search(rf"(?<![A-Za-z_0-9.,-]){pat}(?![A-Za-z_0-9.,-])", text)
        for pat in _number_patterns(value_text, value)
    )


def audit_metric_mentions(metrics: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for metric in metrics:
        group = str(metric.get("grupo", ""))
        paragraphs = _group_paragraphs(doc, group)
        value_text = str(metric.get("valor_texto", "")).strip()
        number_patterns = _number_patterns(value_text, metric.get("valor"))
        if not number_patterns:
            continue

        metric_name = str(metric.get("metrica", ""))
        metric_tokens = [tok for tok in re.split(r"[_\W]+", metric_name) if len(tok) >= 4]

        hits = []
        for paragraph in paragraphs:
            text = str(paragraph.get("text", ""))
            if metric_name in METRIC_POLICIES and not _metric_context_allowed(metric_name, text, metric):
                continue
            has_number = any(
                re.search(rf"(?<![A-Za-z_0-9.,-]){pat}(?![A-Za-z_0-9.,-])", text)
                for pat in number_patterns
            )
            if not has_number:
                continue
            token_score = sum(1 for token in metric_tokens if re.search(token, text, flags=re.IGNORECASE))
            hits.append((token_score, paragraph))

        hits = sorted(hits, key=lambda item: (-item[0], item[1].get("paragraph_index", 0)))
        best_context = str(hits[0][1].get("text", ""))[:500] if hits else ""
        rows.append(
            {
                **metric,
                "mencionado_no_texto_do_grupo": bool(hits),
                "ocorrencias_no_texto_do_grupo": len(hits),
                "melhor_contexto": best_context,
                "paragrafos_no_escopo_do_grupo": len(paragraphs),
            }
        )
    return rows


def _expected_values(value: object, value_text: str) -> list[float]:
    expected: list[float] = []
    for raw in [value, value_text, str(value_text).replace(",", ".")]:
        numeric = _safe_num(raw)
        if numeric is None or not math.isfinite(numeric):
            continue
        if not any(abs(numeric - previous) <= 1e-6 for previous in expected):
            expected.append(numeric)
    return expected


def _extract_evidence_tokens(evidence: object) -> list[str]:
    text = str(evidence or "")
    tokens = re.findall(r"SAM[_-]?\d+", text, flags=re.IGNORECASE)
    tokens.extend(re.findall(r"Campanha[-\s]*\d+[-\s]*[A-Za-zÀ-ÿ]+", text, flags=re.IGNORECASE))
    for part in text.split(";"):
        stripped = part.strip()
        if stripped and stripped.lower() not in {"ultima linha da curva", "linhas da tabela de composicao"}:
            tokens.append(stripped)
    seen: set[str] = set()
    unique: list[str] = []
    for token in tokens:
        normalized = _norm_text(token)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(token)
    return unique


def _has_expected_number(text: str, value_text: str, value: object) -> bool:
    return _contains_metric_number(text, value_text, value)


def _is_contextual_number(text: str, start: int, end: int) -> bool:
    previous = text[max(0, start - 20):start].lower()
    next_char = text[end:end + 1]
    previous_char = text[start - 1:start]
    if previous_char in {"_", "-", "/"} or next_char in {"_", "-", "/"}:
        return False
    if re.search(r"(sam[_-]?|campanha[-\s]*|quadro\s*|figura\s*|tabela\s*|grafico\s*|gráfico\s*)$", previous):
        return False
    return True


def _numbers_in_text(text: str) -> list[dict[str, Any]]:
    numbers: list[dict[str, Any]] = []
    for match in re.finditer(r"(?<![A-Za-z_0-9])\d+(?:[.,]\d+)?%?", text):
        raw = match.group(0)
        if not _is_contextual_number(text, match.start(), match.end()):
            continue
        numeric = _safe_num(raw.rstrip("%").replace(",", "."))
        if numeric is None or not math.isfinite(numeric):
            continue
        if 1900 <= numeric <= 2100 and "." not in raw and "," not in raw:
            continue
        if abs(numeric) > 100000:
            continue
        numbers.append({"texto": raw, "valor": numeric})
    return numbers


def _relevance_score(text: str, item: dict[str, Any], policy: dict[str, Any]) -> int:
    normalized = _norm_text(text)
    terms = [str(term) for term in policy.get("termos", [])]
    score = sum(1 for term in terms if _norm_text(term) in normalized)
    for token in _extract_evidence_tokens(item.get("evidencia_resultado")):
        if _norm_text(token) and _norm_text(token) in normalized:
            score += 3
    if re.search(r"\b(maior|maxim[ao]|superior|elevad[ao]|registrad[ao]s?)\b", normalized):
        score += 1
    return score


def _metric_context_allowed(metric: str, text: str, item: dict[str, Any]) -> bool:
    normalized = _norm_text(text)
    lowered = text.lower()
    if metric == "riqueza_total_composicao":
        return (
            "riqueza total" in normalized
            or re.search(r"riqueza\w*[^.]{0,120}\d+\s+(taxon|taxons|taxa|especie|especies)", normalized) is not None
            or re.search(r"registrad\w*\s+\d+\s+(taxon|taxons|taxa|especie|especies)", normalized) is not None
            or re.search(r"\d+\s+(taxon|taxons|taxa|especie|especies)\s+registrad\w*", normalized) is not None
            or re.search(r"total\s+de\s+\d+\s+(taxon|taxons|taxa|especie|especies)", normalized) is not None
            or re.search(r"pertencent\w*\s+a\s+\d+\s+(taxon|taxons|taxa|especie|especies)", normalized) is not None
            or re.search(r"compost\w*\s+por\s+\d+\s+(taxon|taxons|taxa|especie|especies)", normalized) is not None
        )
    if metric in {"riqueza_max_por_ponto_campanha", "riqueza_max_total_por_ponto"}:
        evidence_tokens = [_norm_text(token) for token in _extract_evidence_tokens(item.get("evidencia_resultado"))]
        evidence_hit = any(token and token in normalized for token in evidence_tokens)
        return "riqueza" in normalized and (
            evidence_hit
            or "maior riqueza" in normalized
            or "maiores valores de riqueza" in normalized
            or "maior riqueza taxonomica" in normalized
        )
    if metric in {"abundancia_total_soma", "abundancia_max_por_ponto_campanha"}:
        return (
            "abundancia" in normalized
            or "densidade" in normalized
            or re.search(r"capturad\w*\s+\d+\s+individu", normalized) is not None
            or re.search(r"total\s+de\s+\d+\s+individu", normalized) is not None
            or re.search(r"\d+\s+individu", normalized) is not None and "captur" in normalized
        )
    if metric == "shannon_max":
        return "shannon" in normalized or "h'" in lowered or "h’" in lowered
    if metric == "suficiencia_riqueza_obs_final":
        return "suficiencia" in normalized and ("riqueza" in normalized or "comunidade" in normalized)
    if metric == "suficiencia_jackknife1_final":
        return "jackknife" in normalized
    if metric == "bmwp_max":
        return "bmwp" in normalized
    return True


def detect_numeric_divergence_candidates(metric_review: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in metric_review:
        metric = str(item.get("metrica", ""))
        policy = METRIC_POLICIES.get(metric)
        if not policy:
            continue

        group = str(item.get("grupo", ""))
        value_text = str(item.get("valor_texto", "")).strip()
        expected = _expected_values(item.get("valor"), value_text)
        if not expected:
            continue

        paragraphs = _group_paragraphs(doc, group)
        metric_candidates: list[dict[str, Any]] = []
        for paragraph in paragraphs:
            text = str(paragraph.get("text", ""))
            if not _metric_context_allowed(metric, text, item):
                continue
            score = _relevance_score(text, item, policy)
            threshold = 5 if policy.get("usar_evidencia") else 3
            if score < threshold:
                continue

            numbers = _numbers_in_text(text)
            alternatives = [
                number for number in numbers
                if not any(abs(float(number["valor"]) - exp) <= 0.02 for exp in expected)
            ]
            if not alternatives:
                continue

            has_expected = _has_expected_number(text, value_text, item.get("valor"))
            if has_expected and score < threshold + 2:
                continue

            metric_candidates.append(
                {
                    "grupo": group,
                    "metrica": metric,
                    "rotulo_metrica": policy.get("rotulo", metric),
                    "valor_resultado": value_text,
                    "valores_texto_candidatos": ", ".join(dict.fromkeys(str(n["texto"]) for n in alternatives[:8])),
                    "arquivo_origem": item.get("arquivo_origem", ""),
                    "evidencia_resultado": item.get("evidencia_resultado", ""),
                    "paragrafo": paragraph.get("paragraph_index", ""),
                    "score_relevancia": score,
                    "valor_resultado_aparece_no_contexto": has_expected,
                    "contexto": text[:800],
                    "status_candidato": (
                        "possivel_divergencia" if not has_expected else "contexto_com_outros_numeros"
                    ),
                    "acao_recomendada": (
                        "Comparar o valor do texto com a planilha de origem antes de corrigir o relatorio."
                    ),
                }
            )

        metric_candidates = sorted(
            metric_candidates,
            key=lambda row: (
                not bool(row.get("valor_resultado_aparece_no_contexto")),
                int(row.get("score_relevancia") or 0),
                -int(row.get("paragrafo") or 0),
            ),
            reverse=True,
        )
        candidates.extend(metric_candidates[:3])
    return candidates


def classify_metric_mentions(metric_mentions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in metric_mentions:
        metric = str(item.get("metrica", ""))
        policy = METRIC_POLICIES.get(metric, {})
        mentioned = bool(item.get("mencionado_no_texto_do_grupo"))
        should_register = bool(policy.get("registrar_se_ausente"))
        if mentioned:
            status = "ok_mencionada"
            action = "Nenhuma acao automatica."
        elif should_register:
            status = "alerta_para_conferencia"
            action = "Conferir se a metrica deve constar no texto; se houver outro valor no relatorio, corrigir."
        else:
            status = "informativa_sem_mencao"
            action = "Metrica informativa mantida apenas no inventario numerico."

        rows.append(
            {
                **item,
                "status_revisao": status,
                "registrar_em_inconsistencias": status == "alerta_para_conferencia",
                "rotulo_metrica": policy.get("rotulo", metric),
                "severidade_sugerida": policy.get("severidade", "BAIXA"),
                "acao_recomendada": action,
            }
        )
    return rows


def build_numeric_issues(metric_review: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for item in metric_review:
        if not item.get("registrar_em_inconsistencias"):
            continue
        value_text = str(item.get("valor_texto", "")).strip()
        issues.append(
            {
                "severidade": str(item.get("severidade_sugerida") or "BAIXA"),
                "categoria": "Numeros/conferencia",
                "problema": (
                    f"Metrica-chave nao localizada no texto do grupo {item.get('grupo')}: "
                    f"{item.get('rotulo_metrica')} = {value_text}."
                ),
                "evidencia": (
                    f"arquivo={item.get('arquivo_origem')}; "
                    f"resultado={item.get('evidencia_resultado')}; "
                    f"metrica={item.get('metrica')}"
                ),
                "sugestao": (
                    "Conferir se o valor deve aparecer na narrativa. Se aparecer com outro numero, "
                    "tratar como divergencia numerica e corrigir o texto."
                ),
                "grupo": str(item.get("grupo", "")),
                "metrica": str(item.get("metrica", "")),
                "arquivo_origem": str(item.get("arquivo_origem", "")),
                "tipo_registro": "alerta_numerico",
                "tipo_achado": "alerta_para_conferencia",
            }
        )
    return issues


def build_numeric_divergence_issues(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in candidates:
        if item.get("valor_resultado_aparece_no_contexto"):
            continue
        metric = str(item.get("metrica", ""))
        policy = METRIC_POLICIES.get(metric, {})
        if int(item.get("score_relevancia") or 0) < 8:
            continue
        key = (str(item.get("grupo", "")), metric)
        if key in seen:
            continue
        seen.add(key)
        issues.append(
            {
                "severidade": str(policy.get("severidade", "BAIXA")),
                "categoria": "Numeros/divergencia_candidata",
                "problema": (
                    f"Possivel divergencia numerica em {item.get('grupo')}: "
                    f"{item.get('rotulo_metrica')} esperado {item.get('valor_resultado')}, "
                    f"mas o contexto traz {item.get('valores_texto_candidatos')}."
                ),
                "evidencia": (
                    f"paragrafo={item.get('paragrafo')}; arquivo={item.get('arquivo_origem')}; "
                    f"resultado={item.get('evidencia_resultado')}"
                ),
                "sugestao": str(item.get("acao_recomendada") or ""),
                "grupo": str(item.get("grupo", "")),
                "metrica": metric,
                "arquivo_origem": str(item.get("arquivo_origem", "")),
                "tipo_registro": "divergencia_numerica_candidata",
                "tipo_achado": "divergencia_candidata",
            }
        )
    return issues
