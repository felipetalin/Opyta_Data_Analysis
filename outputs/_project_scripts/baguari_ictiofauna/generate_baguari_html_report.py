from __future__ import annotations

import json
import math
import sys
from html import escape
from pathlib import Path

import pandas as pd
from sqlalchemy import text

OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from core.engine import get_engine


OUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Micra\Baguari\Campanhas\2026\4. Abril\5. Planilhas"
)
XLSX = OUT_DIR / "BD_UHE_Baguari_MIGRACAO_AJUSTADA_20260612 REV01_MIGRACAO_VALIDADA.xlsx"
OUT_HTML = OUT_DIR / "relatorio_resultados_baguari_ictiofauna_20260612.html"
PROJECT_ID = 188
CODIGO = "MICGAG001"
REPORT_DATE = "12/06/2026"

GREEN = "#1f7a4d"
GREEN_DARK = "#0f3d2e"
MINT = "#7bc6a4"
BLUE = "#2f6f8f"
AMBER = "#d69a2d"
RED = "#b14d42"
INK = "#18312a"
MUTED = "#66766f"
GRID = "#d9e5de"
BG = "#f4f8f5"


def clean_value(value, default="Não informado"):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    text_value = str(value).strip()
    if not text_value or text_value.lower() in {"nan", "none", "null"}:
        return default
    replacements = {
        "N?o informado": "Não informado",
        "Nao informado": "Não informado",
        "NÃ£o informado": "Não informado",
        "N?o Nativo": "Não nativo",
        "Nao Nativo": "Não nativo",
        "Não Nativo": "Não nativo",
        "nao nativo": "Não nativo",
        "S.I": "S.I.",
        "s.i.": "S.I.",
        "Cr": "CR",
        "Vu": "VU",
        "En": "EN",
    }
    return replacements.get(text_value, text_value)


def fmt_int(value):
    return f"{int(round(float(value))):,}".replace(",", ".")


def fmt_float(value, digits=2):
    return f"{float(value):.{digits}f}".replace(".", ",")


def pct(value, total, digits=1):
    if not total:
        return "0%"
    return f"{100 * float(value) / float(total):.{digits}f}%".replace(".", ",")


def h(value):
    return escape(str(value), quote=True)


def shannon(counts):
    total = sum(counts)
    return -sum((c / total) * math.log(c / total) for c in counts if c > 0) if total else 0.0


def simpson(counts):
    total = sum(counts)
    return 1 - sum((c / total) ** 2 for c in counts if c > 0) if total else 0.0


def svg_horizontal_bars(rows, label_key, value_key, width=760, row_h=34, left=245, right=95, title=None, color=GREEN):
    rows = list(rows)
    height = 34 + row_h * len(rows) + (34 if title else 10)
    top = 36 if title else 16
    max_value = max([float(r[value_key]) for r in rows] or [1])
    chart_w = width - left - right
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img">']
    if title:
        parts.append(f'<text x="0" y="20" class="svg-title">{h(title)}</text>')
    for i, row in enumerate(rows):
        y = top + i * row_h
        value = float(row[value_key])
        bar_w = 0 if max_value == 0 else max(2, chart_w * value / max_value)
        parts.append(f'<text x="0" y="{y + 19}" class="svg-label">{h(row[label_key])}</text>')
        parts.append(f'<rect x="{left}" y="{y + 5}" width="{chart_w}" height="16" rx="4" fill="#e5eee8" />')
        parts.append(f'<rect x="{left}" y="{y + 5}" width="{bar_w:.2f}" height="16" rx="4" fill="{color}" />')
        parts.append(f'<text x="{left + bar_w + 8}" y="{y + 19}" class="svg-value">{fmt_int(value)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_donut(counts, title, width=430, height=270):
    items = [(clean_value(k), float(v)) for k, v in counts.items() if float(v) > 0]
    total = sum(v for _, v in items) or 1
    colors = [GREEN, BLUE, AMBER, MINT, "#8ba99a", RED, "#97b9d0"]
    cx, cy, r = 112, 136, 74
    circumference = 2 * math.pi * r
    offset = 0
    parts = [f'<svg class="chart donut" viewBox="0 0 {width} {height}" role="img">']
    parts.append(f'<text x="0" y="22" class="svg-title">{h(title)}</text>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e5eee8" stroke-width="28"/>')
    for idx, (label, value) in enumerate(items):
        dash = circumference * value / total
        color = colors[idx % len(colors)]
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="28" '
            f'stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})" />'
        )
        offset += dash
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="white"/>')
    parts.append(f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" class="donut-number">{fmt_int(total)}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 18}" text-anchor="middle" class="donut-caption">espécies</text>')
    legend_x = 225
    for idx, (label, value) in enumerate(items):
        y = 78 + idx * 29
        color = colors[idx % len(colors)]
        parts.append(f'<rect x="{legend_x}" y="{y - 12}" width="13" height="13" rx="3" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 22}" y="{y}" class="svg-label">{h(label)}</text>')
        parts.append(f'<text x="{width - 6}" y="{y}" text-anchor="end" class="svg-value">{fmt_int(value)} · {pct(value, total)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_point_map(point_rows, width=760, height=520):
    pts = list(point_rows)
    if not pts:
        return ""
    min_lon = min(p["longitude"] for p in pts)
    max_lon = max(p["longitude"] for p in pts)
    min_lat = min(p["latitude"] for p in pts)
    max_lat = max(p["latitude"] for p in pts)
    pad = 58
    plot_w = width - 2 * pad
    plot_h = height - 2 * pad
    max_ab = max([p["abundancia"] for p in pts] or [1])
    max_rich = max([p["riqueza"] for p in pts] or [1])

    def x(lon):
        return pad + (lon - min_lon) / (max_lon - min_lon or 1) * plot_w

    def y(lat):
        return pad + (max_lat - lat) / (max_lat - min_lat or 1) * plot_h

    offsets = [
        (0, 0),
        (28, -22),
        (-28, -22),
        (28, 22),
        (-28, 22),
        (0, -38),
        (0, 38),
        (48, 0),
        (-48, 0),
        (52, -34),
        (-52, -34),
        (52, 34),
        (-52, 34),
        (76, -12),
        (-76, -12),
        (76, 12),
        (-76, 12),
    ]
    placed = []
    label_positions = []
    for p in sorted(pts, key=lambda item: item["abundancia"], reverse=True):
        anchor_x = x(p["longitude"])
        anchor_y = y(p["latitude"])
        radius = 10 + 6 * math.sqrt((p["abundancia"] or 0) / (max_ab or 1))
        best = None
        best_score = float("inf")
        for dx, dy in offsets:
            lx = min(max(anchor_x + dx, pad + radius + 2), width - pad - radius - 2)
            ly = min(max(anchor_y + dy, pad + radius + 2), height - pad - radius - 2)
            overlap = 0
            for px, py, pr in placed:
                dist = math.hypot(lx - px, ly - py)
                overlap += max(0, (radius + pr + 8) - dist)
            score = overlap * 1000 + abs(dx) + abs(dy)
            if score < best_score:
                best = (lx, ly, radius)
                best_score = score
        placed.append(best)
        label_positions.append({"point": p, "anchor_x": anchor_x, "anchor_y": anchor_y, "label_x": best[0], "label_y": best[1], "radius": best[2]})

    parts = [f'<svg class="spatial-svg" viewBox="0 0 {width} {height}" role="img">']
    parts.append('<defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#173b2d" flood-opacity="0.18"/></filter></defs>')
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#eef6f0"/>')
    for i in range(6):
        xx = pad + i * plot_w / 5
        yy = pad + i * plot_h / 5
        parts.append(f'<line x1="{xx:.1f}" y1="{pad}" x2="{xx:.1f}" y2="{height - pad}" stroke="#d7e6dc" stroke-width="1"/>')
        parts.append(f'<line x1="{pad}" y1="{yy:.1f}" x2="{width - pad}" y2="{yy:.1f}" stroke="#d7e6dc" stroke-width="1"/>')
    parts.append(f'<rect x="{pad}" y="{pad}" width="{plot_w}" height="{plot_h}" rx="8" fill="none" stroke="#bdd5c7" stroke-width="1.5"/>')
    for item in label_positions:
        p = item["point"]
        parts.append(f'<circle cx="{item["anchor_x"]:.1f}" cy="{item["anchor_y"]:.1f}" r="3" fill="{GREEN_DARK}" opacity="0.48"/>')
        if math.hypot(item["label_x"] - item["anchor_x"], item["label_y"] - item["anchor_y"]) > 5:
            parts.append(f'<line x1="{item["anchor_x"]:.1f}" y1="{item["anchor_y"]:.1f}" x2="{item["label_x"]:.1f}" y2="{item["label_y"]:.1f}" stroke="#9dbdab" stroke-width="1.2"/>')
    for item in label_positions:
        p = item["point"]
        intensity = (p["riqueza"] or 0) / (max_rich or 1)
        color = BLUE if intensity > 0.66 else GREEN if intensity > 0.33 else AMBER
        parts.append(f'<circle cx="{item["label_x"]:.1f}" cy="{item["label_y"]:.1f}" r="{item["radius"]:.1f}" fill="{color}" fill-opacity="0.88" stroke="white" stroke-width="2" filter="url(#shadow)"/>')
        parts.append(f'<text x="{item["label_x"]:.1f}" y="{item["label_y"] + 4:.1f}" text-anchor="middle" class="map-number">{h(p.get("idx", ""))}</text>')
    parts.append(f'<text x="{pad}" y="{height - 20}" class="map-axis">Longitude {min_lon:.3f} a {max_lon:.3f}</text>')
    parts.append(f'<text x="{width - pad}" y="{height - 20}" text-anchor="end" class="map-axis">Latitude {min_lat:.3f} a {max_lat:.3f}</text>')
    parts.append(f'<path d="M {width - 72} {pad + 44} L {width - 72} {pad + 12} M {width - 82} {pad + 24} L {width - 72} {pad + 12} L {width - 62} {pad + 24}" stroke="{GREEN_DARK}" stroke-width="2" fill="none"/>')
    parts.append(f'<text x="{width - 72}" y="{pad + 60}" text-anchor="middle" class="map-axis">N</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_time_series(rows, width=940, height=320):
    rows = list(rows)
    if not rows:
        return ""
    left, right, top, bottom = 54, 34, 28, 42
    plot_w, plot_h = width - left - right, height - top - bottom
    max_ab = max(r["abundancia"] for r in rows) or 1
    max_rich = max(r["riqueza"] for r in rows) or 1
    n = len(rows)

    def x(i):
        return left + (i / max(n - 1, 1)) * plot_w

    def y_ab(v):
        return top + plot_h - math.sqrt(v / max_ab) * plot_h

    def y_r(v):
        return top + plot_h - (v / max_rich) * plot_h

    parts = [f'<svg class="chart timeline" viewBox="0 0 {width} {height}" role="img">']
    parts.append('<text x="0" y="18" class="svg-title">Série temporal por campanha</text>')
    for i in range(5):
        yy = top + i * plot_h / 4
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width - right}" y2="{yy:.1f}" stroke="{GRID}"/>')
    bar_w = max(3, plot_w / max(n, 1) * 0.62)
    for i, row in enumerate(rows):
        xx = x(i) - bar_w / 2
        yy = y_ab(row["abundancia"])
        parts.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{bar_w:.1f}" height="{top + plot_h - yy:.1f}" rx="2" fill="#b9dbc7" opacity="0.8"/>')
    points = " ".join(f'{x(i):.1f},{y_r(row["riqueza"]):.1f}' for i, row in enumerate(rows))
    parts.append(f'<polyline points="{points}" fill="none" stroke="{GREEN_DARK}" stroke-width="3"/>')
    for i, row in enumerate(rows):
        if i % max(1, n // 12) == 0 or i == n - 1:
            parts.append(f'<circle cx="{x(i):.1f}" cy="{y_r(row["riqueza"]):.1f}" r="3.5" fill="{GREEN_DARK}"/>')
    seen = set()
    for i, row in enumerate(rows):
        year = str(row["ano"])
        if year not in seen:
            seen.add(year)
            parts.append(f'<text x="{x(i):.1f}" y="{height - 14}" text-anchor="middle" class="svg-label small">{year}</text>')
            parts.append(f'<line x1="{x(i):.1f}" y1="{height - bottom}" x2="{x(i):.1f}" y2="{height - bottom + 6}" stroke="{MUTED}"/>')
    parts.append(f'<text x="{left}" y="{height - 14}" class="legend-item"><tspan fill="#89b99b">■</tspan> abundância (escala raiz)</text>')
    parts.append(f'<text x="{left + 230}" y="{height - 14}" class="legend-item"><tspan fill="{GREEN_DARK}">●</tspan> riqueza</text>')
    parts.append("</svg>")
    return "".join(parts)


def badge(text):
    return f'<span class="badge">{h(text)}</span>'


def load_data():
    engine = get_engine()
    with engine.connect() as con:
        project = pd.read_sql(
            text(
                """
                SELECT p.id_projeto, p.codigo_interno_opyta, p.nome_projeto, c.nome_empresa
                FROM projetos p
                JOIN clientes c ON c.id_cliente = p.id_cliente
                WHERE p.id_projeto = :id_projeto
                """
            ),
            con,
            params={"id_projeto": PROJECT_ID},
        )
        points = pd.read_sql(
            text(
                """
                SELECT ca.nome_campanha, pc.nome_ponto, pc.latitude, pc.longitude,
                       pc.data_hora_coleta, pc.bacia_hidrografica
                FROM pontos_coleta pc
                JOIN campanhas ca ON ca.id_campanha = pc.id_campanha
                WHERE pc.id_projeto = :id_projeto
                """
            ),
            con,
            params={"id_projeto": PROJECT_ID},
        )
        data = pd.read_sql(
            text(
                """
                SELECT ca.nome_campanha, pc.nome_ponto, pc.latitude, pc.longitude,
                       pc.data_hora_coleta, pc.bacia_hidrografica,
                       e.metodo_de_captura, e.tipo_amostragem, e.esforco, e.unidade_esforco,
                       sp.nome_cientifico, sp.nome_popular, sp.ordem, sp.familia, sp.genero, sp.origem,
                       sp.status_ameaca_nacional, sp.status_ameaca_global, sp.status_estadual,
                       sp.status_copam, sp.cites, sp.habito_alimentar, sp.guilda_alimentar,
                       sp.estrategia_reprodutiva, sp.valor_economico, sp.migratorio, sp.raridade,
                       ri.numero_de_individuos, ri.ct_cm, ri.pc_g
                FROM resultados_ictiofauna ri
                JOIN esforcos_amostragem e ON e.id_esforco = ri.id_esforco
                JOIN pontos_coleta pc ON pc.id_ponto_coleta = e.id_ponto_coleta
                JOIN campanhas ca ON ca.id_campanha = pc.id_campanha
                JOIN especies sp ON sp.id_especie = ri.id_especie
                WHERE pc.id_projeto = :id_projeto AND e.grupo_biologico = 'Ictiofauna'
                """
            ),
            con,
            params={"id_projeto": PROJECT_ID},
        )
    if project.empty or data.empty:
        raise RuntimeError("Projeto ou dados consolidados nao encontrados.")
    return project, points, data


def build_report():
    project, points, data = load_data()

    raw_result_rows = raw_effort_rows = None
    if XLSX.exists():
        raw_result_rows = len(pd.read_excel(XLSX, sheet_name="Resultados_Ictiofauna").dropna(how="all"))
        raw_effort_rows = len(pd.read_excel(XLSX, sheet_name="Metadados_Esforco").dropna(how="all"))

    for col in ["numero_de_individuos", "ct_cm", "pc_g", "esforco", "latitude", "longitude"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    for col in ["latitude", "longitude"]:
        points[col] = pd.to_numeric(points[col], errors="coerce")
    points["data_hora_coleta"] = pd.to_datetime(points["data_hora_coleta"], errors="coerce")
    data["data_hora_coleta"] = pd.to_datetime(data["data_hora_coleta"], errors="coerce")

    species = data.drop_duplicates("nome_cientifico").copy()
    category_cols = [
        "origem",
        "habito_alimentar",
        "guilda_alimentar",
        "estrategia_reprodutiva",
        "valor_economico",
        "migratorio",
        "raridade",
        "status_ameaca_nacional",
        "status_ameaca_global",
        "status_estadual",
        "status_copam",
        "familia",
        "ordem",
    ]
    for col in category_cols:
        species[col] = species[col].map(clean_value)
        data[col] = data[col].map(clean_value)

    abundance_by_species = (
        data.groupby("nome_cientifico", dropna=False)
        .agg(
            abundancia=("numero_de_individuos", "sum"),
            registros=("nome_cientifico", "size"),
            pontos=("nome_ponto", "nunique"),
            campanhas=("nome_campanha", "nunique"),
            familia=("familia", "first"),
            ordem=("ordem", "first"),
            origem=("origem", "first"),
            status_nacional=("status_ameaca_nacional", "first"),
            status_global=("status_ameaca_global", "first"),
            status_estadual=("status_estadual", "first"),
            estrategia=("estrategia_reprodutiva", "first"),
            valor_economico=("valor_economico", "first"),
        )
        .reset_index()
        .sort_values("abundancia", ascending=False)
    )
    counts = abundance_by_species["abundancia"].fillna(0).tolist()
    richness_total = int(data["nome_cientifico"].nunique())
    total_individuals = float(data["numero_de_individuos"].sum())
    h_index = shannon(counts)
    j_index = h_index / math.log(richness_total) if richness_total > 1 else 0
    simpson_index = simpson(counts)
    top5_ab = float(abundance_by_species.head(5)["abundancia"].sum())

    point_stats = (
        data.groupby("nome_ponto")
        .agg(
            abundancia=("numero_de_individuos", "sum"),
            riqueza=("nome_cientifico", "nunique"),
            registros=("nome_cientifico", "size"),
            campanhas_com_resultado=("nome_campanha", "nunique"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .reset_index()
    )
    point_campaigns = (
        points.groupby("nome_ponto")
        .agg(campanhas=("nome_campanha", "nunique"), latitude_p=("latitude", "mean"), longitude_p=("longitude", "mean"))
        .reset_index()
    )
    point_stats = point_campaigns.merge(point_stats, on="nome_ponto", how="left")
    point_stats["abundancia"] = point_stats["abundancia"].fillna(0)
    point_stats["riqueza"] = point_stats["riqueza"].fillna(0).astype(int)
    point_stats["registros"] = point_stats["registros"].fillna(0).astype(int)
    point_stats["campanhas_com_resultado"] = point_stats["campanhas_com_resultado"].fillna(0).astype(int)
    point_stats["latitude"] = point_stats["latitude"].fillna(point_stats["latitude_p"])
    point_stats["longitude"] = point_stats["longitude"].fillna(point_stats["longitude_p"])

    point_rows = [
        {
            "ponto": row.nome_ponto,
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "abundancia": int(round(row.abundancia)),
            "riqueza": int(row.riqueza),
            "campanhas": int(row.campanhas),
            "registros": int(row.registros),
        }
        for row in point_stats.dropna(subset=["latitude", "longitude"]).sort_values("nome_ponto").itertuples()
    ]
    for idx, point in enumerate(point_rows, start=1):
        point["idx"] = idx

    method_stats = (
        data.groupby(["metodo_de_captura", "tipo_amostragem"], dropna=False)
        .agg(abundancia=("numero_de_individuos", "sum"), riqueza=("nome_cientifico", "nunique"), registros=("nome_cientifico", "size"))
        .reset_index()
        .sort_values("abundancia", ascending=False)
    )
    method_stats["metodo_tipo"] = method_stats["metodo_de_captura"].map(clean_value) + " · " + method_stats["tipo_amostragem"].map(clean_value)

    temporal = (
        data.groupby("nome_campanha")
        .agg(data=("data_hora_coleta", "min"), abundancia=("numero_de_individuos", "sum"), riqueza=("nome_cientifico", "nunique"), pontos=("nome_ponto", "nunique"))
        .reset_index()
        .dropna(subset=["data"])
        .sort_values("data")
    )
    temporal["ano"] = temporal["data"].dt.year

    families = species["familia"].map(clean_value).value_counts().reset_index()
    families.columns = ["familia", "riqueza"]

    def category_counts(column):
        return species[column].map(clean_value).value_counts().to_dict()

    non_native = abundance_by_species[
        abundance_by_species["origem"].map(lambda v: "não nativo" in clean_value(v).lower() or "nao nativo" in clean_value(v).lower())
    ]
    migratory = abundance_by_species[abundance_by_species["estrategia"].map(lambda v: "migrador" in clean_value(v).lower())]

    threat_codes = {"VU", "EN", "CR", "CRITICAMENTE EM PERIGO", "EM PERIGO", "VULNERÁVEL", "VULNERAVEL", "AMEAÇADA", "AMEACADA"}

    def is_threat(value):
        normalized = clean_value(value, "").upper().strip()
        if normalized in {"", "LC", "NT", "DD", "NE", "NÃO", "NAO", "NÃO CONSTA", "NAO CONSTA", "NÃO INFORMADO", "S.I."}:
            return False
        return any(code in normalized for code in threat_codes)

    threatened_rows = []
    for _, row in abundance_by_species.iterrows():
        statuses = []
        for label, col in [("Nacional", "status_nacional"), ("Global", "status_global"), ("Estadual", "status_estadual")]:
            value = clean_value(row[col], "")
            if is_threat(value):
                statuses.append(f"{label}: {value}")
        if statuses:
            threatened_rows.append(
                {
                    "nome": row["nome_cientifico"],
                    "familia": clean_value(row["familia"]),
                    "abundancia": int(round(row["abundancia"])),
                    "pontos": int(row["pontos"]),
                    "status": "; ".join(statuses),
                }
            )

    period_start = points["data_hora_coleta"].min()
    period_end = points["data_hora_coleta"].max()
    period_label = f"{period_start:%d/%m/%Y} a {period_end:%d/%m/%Y}"
    project_row = project.iloc[0].to_dict()

    top_species_svg = svg_horizontal_bars(
        abundance_by_species.head(12).assign(nome=lambda frame: frame["nome_cientifico"]).to_dict("records"),
        "nome",
        "abundancia",
        title="Espécies mais abundantes",
        color=GREEN,
    )
    point_ab_svg = svg_horizontal_bars(
        point_stats.sort_values("abundancia", ascending=False).head(10).rename(columns={"nome_ponto": "ponto"}).to_dict("records"),
        "ponto",
        "abundancia",
        title="Pontos com maior abundância",
        color=BLUE,
    )
    point_rich_svg = svg_horizontal_bars(
        point_stats.sort_values("riqueza", ascending=False).head(10).rename(columns={"nome_ponto": "ponto"}).to_dict("records"),
        "ponto",
        "riqueza",
        title="Pontos com maior riqueza",
        color=GREEN_DARK,
    )
    method_svg = svg_horizontal_bars(method_stats.to_dict("records"), "metodo_tipo", "abundancia", title="Abundância por método de captura", color=AMBER)
    origin_svg = svg_donut(category_counts("origem"), "Origem das espécies")
    strategy_svg = svg_donut(category_counts("estrategia_reprodutiva"), "Estratégia reprodutiva")
    economic_svg = svg_donut(category_counts("valor_economico"), "Valor econômico")
    family_svg = svg_horizontal_bars(families.head(10).to_dict("records"), "familia", "riqueza", width=620, left=210, right=70, title="Famílias mais ricas", color=GREEN)
    time_svg = svg_time_series(temporal.to_dict("records"))
    static_map_svg = svg_point_map(point_rows)
    map_data = json.dumps(point_rows, ensure_ascii=False)
    map_legend_html = "".join(
        f"<div class='point-legend-item'><span>{point['idx']}</span><strong>{h(point['ponto'])}</strong><small>{fmt_int(point['riqueza'])} esp. · {fmt_int(point['abundancia'])} ind.</small></div>"
        for point in point_rows
    )

    cards = [
        ("Campanhas", points["nome_campanha"].nunique(), "série 2022-2026"),
        ("Pontos", point_stats["nome_ponto"].nunique(), "rede espacial"),
        ("Registros consolidados", len(data), "após agregação"),
        ("Indivíduos", total_individuals, "abundância total"),
        ("Espécies", richness_total, "riqueza observada"),
        ("Famílias", species["familia"].nunique(), "estrutura taxonômica"),
    ]
    cards_html = "".join(
        f"<article class='metric-card'><span>{h(label)}</span><strong>{fmt_int(value)}</strong><small>{h(detail)}</small></article>"
        for label, value, detail in cards
    )
    summary_items = [
        ("Diversidade alfa", f"H' = {fmt_float(h_index)} · 1-D = {fmt_float(simpson_index)}", "Riqueza expressiva para a série, com dominância perceptível de poucos táxons."),
        ("Equitabilidade", f"J' = {fmt_float(j_index)}", "A distribuição de abundância exige interpretar riqueza junto com dominância."),
        ("Dominância", f"Top 5 = {pct(top5_ab, total_individuals)}", "As cinco espécies mais abundantes concentram parte relevante dos indivíduos."),
        ("Espécies não nativas", f"{fmt_int(len(non_native))} espécies", "Componente alóctone relevante para acompanhar pressão ecológica e alteração de habitat."),
    ]
    summary_html = "".join(f"<article class='insight'><span>{h(label)}</span><strong>{h(value)}</strong><p>{h(desc)}</p></article>" for label, value, desc in summary_items)

    species_table_rows = "".join(
        f"<tr><td><em>{h(row['nome_cientifico'])}</em></td><td>{h(clean_value(row['familia']))}</td><td>{h(clean_value(row['origem']))}</td><td class='num'>{fmt_int(row['abundancia'])}</td><td class='num'>{fmt_int(row['pontos'])}</td><td class='num'>{pct(row['abundancia'], total_individuals)}</td></tr>"
        for _, row in abundance_by_species.head(15).iterrows()
    )
    threat_table = "".join(
        f"<tr><td><em>{h(row['nome'])}</em></td><td>{h(row['familia'])}</td><td>{h(row['status'])}</td><td class='num'>{fmt_int(row['abundancia'])}</td><td class='num'>{fmt_int(row['pontos'])}</td></tr>"
        for row in threatened_rows
    ) or "<tr><td colspan='5'>Nenhuma espécie com categoria de ameaça destacada nas colunas avaliadas.</td></tr>"
    non_native_rows = "".join(
        f"<tr><td><em>{h(row['nome_cientifico'])}</em></td><td>{h(clean_value(row['familia']))}</td><td class='num'>{fmt_int(row['abundancia'])}</td><td class='num'>{fmt_int(row['pontos'])}</td></tr>"
        for _, row in non_native.head(10).iterrows()
    ) or "<tr><td colspan='4'>Sem espécies não nativas registradas no cadastro usado.</td></tr>"
    migratory_table = "".join(
        f"<tr><td><em>{h(row['nome_cientifico'])}</em></td><td>{h(clean_value(row['familia']))}</td><td>{h(clean_value(row['estrategia']))}</td><td class='num'>{fmt_int(row['abundancia'])}</td><td class='num'>{fmt_int(row['pontos'])}</td></tr>"
        for _, row in migratory.sort_values("abundancia", ascending=False).head(12).iterrows()
    ) or "<tr><td colspan='5'>Nenhuma espécie migradora destacada na coluna de estratégia reprodutiva.</td></tr>"
    point_table = "".join(
        f"<tr><td>{h(row.nome_ponto)}</td><td class='num'>{fmt_int(row.campanhas)}</td><td class='num'>{fmt_int(row.riqueza)}</td><td class='num'>{fmt_int(row.abundancia)}</td><td class='num'>{fmt_float(row.latitude, 5)}</td><td class='num'>{fmt_float(row.longitude, 5)}</td></tr>"
        for row in point_stats.sort_values(["abundancia", "riqueza"], ascending=False).itertuples()
    )

    raw_rows_label = fmt_int(raw_result_rows) if raw_result_rows is not None else "-"
    raw_efforts_label = fmt_int(raw_effort_rows) if raw_effort_rows is not None else "-"

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Resultados Ictiofauna - UHE Baguari</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIINfQPDwpZpoomOFCD5lGMvgtLLmYeYhY=" crossorigin="" />
  <style>
    :root {{ --green:{GREEN}; --green-dark:{GREEN_DARK}; --mint:{MINT}; --blue:{BLUE}; --amber:{AMBER}; --red:{RED}; --ink:{INK}; --muted:{MUTED}; --grid:{GRID}; --bg:{BG}; --paper:#fff; --line:#d8e4dd; }}
    * {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.45; letter-spacing:0; }}
    .hero {{ min-height:78vh; display:grid; align-items:end; background:linear-gradient(180deg,rgba(13,53,38,.18),rgba(13,53,38,.84)),radial-gradient(circle at 18% 24%,rgba(123,198,164,.36),transparent 28%),linear-gradient(135deg,#164733 0%,#1f7a4d 46%,#2f6f8f 100%); color:white; position:relative; overflow:hidden; }}
    .hero:after {{ content:""; position:absolute; inset:auto 0 0 0; height:120px; background:linear-gradient(180deg,transparent,var(--bg)); pointer-events:none; }}
    .hero-inner {{ width:min(1180px,calc(100% - 40px)); margin:0 auto; padding:86px 0 82px; position:relative; z-index:1; }}
    .eyebrow {{ display:inline-flex; gap:10px; align-items:center; font-weight:800; font-size:13px; text-transform:uppercase; color:#d8f2e4; margin-bottom:18px; }}
    h1 {{ max-width:880px; font-size:clamp(42px,7vw,82px); line-height:.96; margin:0; letter-spacing:0; }}
    .hero-copy {{ max-width:790px; margin:22px 0 0; font-size:clamp(17px,2vw,22px); color:#edf8f0; }}
    .hero-meta {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:28px; }}
    .badge {{ display:inline-flex; align-items:center; min-height:32px; padding:6px 11px; border-radius:999px; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.28); color:inherit; font-weight:800; font-size:13px; }}
    main {{ width:min(1180px,calc(100% - 34px)); margin:-46px auto 72px; position:relative; z-index:2; }}
    section {{ margin:28px 0; }}
    .metric-grid {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:12px; }}
    .metric-card,.panel,.insight,.callout {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; box-shadow:0 10px 30px rgba(24,49,42,.06); }}
    .metric-card {{ padding:18px 16px; min-height:126px; }}
    .metric-card span,.insight span,.section-kicker {{ display:block; color:var(--muted); font-size:12px; font-weight:900; text-transform:uppercase; }}
    .metric-card strong {{ display:block; font-size:clamp(26px,3vw,38px); margin:8px 0 3px; color:var(--green-dark); }}
    .metric-card small {{ color:var(--muted); font-weight:700; }}
    .section-head {{ display:flex; justify-content:space-between; align-items:end; gap:22px; margin:34px 0 14px; }}
    .section-head h2 {{ margin:0; font-size:clamp(25px,3vw,38px); line-height:1.08; }}
    .section-head p {{ margin:0; color:var(--muted); max-width:560px; }}
    .panel {{ padding:22px; overflow:hidden; }} .panel h3 {{ margin:0 0 14px; font-size:18px; }}
    .two-col {{ display:grid; grid-template-columns:minmax(0,1.35fr) minmax(330px,.65fr); gap:16px; }}
    .balanced {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .three-col {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
    .insight {{ padding:18px; }} .insight strong {{ display:block; margin:8px 0 6px; font-size:24px; color:var(--green-dark); }} .insight p {{ margin:0; color:var(--muted); }}
    .map-layout {{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr); gap:16px; align-items:stretch; }}
    #map {{ height:540px; min-height:420px; border-radius:8px; border:1px solid var(--line); background:#e7efe9; }}
    .map-note {{ padding:18px; background:#f7faf7; border:1px solid var(--line); border-radius:8px; color:var(--muted); }}
    .chart {{ width:100%; height:auto; display:block; }} .svg-title {{ font:800 18px system-ui,sans-serif; fill:var(--ink); }} .svg-label {{ font:600 13px system-ui,sans-serif; fill:var(--ink); }} .svg-label.small {{ font-size:11px; fill:var(--muted); }} .svg-value {{ font:800 12px system-ui,sans-serif; fill:var(--green-dark); }} .donut-number {{ font:900 28px system-ui,sans-serif; fill:var(--green-dark); }} .donut-caption,.legend-item,.map-axis {{ font:700 12px system-ui,sans-serif; fill:var(--muted); }} .map-label {{ font:900 12px system-ui,sans-serif; fill:var(--green-dark); paint-order:stroke; stroke:white; stroke-width:4px; }} .map-number {{ font:900 12px system-ui,sans-serif; fill:white; }}
    .point-legend {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin:14px 0 0; }}
    .point-legend-item {{ display:grid; grid-template-columns:24px minmax(0,1fr); grid-template-rows:auto auto; column-gap:8px; align-items:center; padding:8px; border:1px solid var(--line); border-radius:8px; background:#fbfdfb; }}
    .point-legend-item span {{ grid-row:1 / span 2; display:grid; place-items:center; width:24px; height:24px; border-radius:50%; background:var(--green-dark); color:white; font-size:12px; font-weight:900; }}
    .point-legend-item strong {{ font-size:13px; line-height:1.05; }} .point-legend-item small {{ color:var(--muted); font-size:11px; font-weight:700; }}
    .leaflet-div-icon.point-icon {{ width:24px; height:24px; margin-left:-12px; margin-top:-12px; border:0; background:transparent; }}
    .leaflet-div-icon.point-icon span {{ display:grid; place-items:center; width:24px; height:24px; border-radius:50%; background:rgba(15,61,46,.92); color:white; font:900 12px system-ui,sans-serif; border:2px solid white; box-shadow:0 2px 8px rgba(0,0,0,.25); }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }} th,td {{ padding:11px 10px; border-bottom:1px solid var(--line); vertical-align:top; }} th {{ text-align:left; color:var(--muted); font-size:12px; text-transform:uppercase; }} td.num,th.num {{ text-align:right; font-variant-numeric:tabular-nums; }} tr:last-child td {{ border-bottom:0; }} .scroll-table {{ overflow-x:auto; }}
    .callout {{ padding:20px 22px; border-left:5px solid var(--green); }} .callout p {{ margin:0; color:var(--muted); }} .callout strong {{ color:var(--green-dark); }}
    .foot {{ color:var(--muted); font-size:12px; margin-top:26px; }}
    @media (max-width:980px) {{ .metric-grid {{ grid-template-columns:repeat(3,minmax(0,1fr)); }} .two-col,.map-layout,.balanced,.three-col {{ grid-template-columns:1fr; }} main {{ width:min(100% - 24px,760px); }} .section-head {{ display:block; }} .section-head p {{ margin-top:8px; }} }}
    @media (max-width:620px) {{ .metric-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .hero-inner {{ width:calc(100% - 26px); padding-bottom:68px; }} .panel {{ padding:16px; }} #map {{ height:430px; }} th,td {{ padding:9px 8px; }} }}
    @media print {{ .hero {{ min-height:auto; }} main {{ margin-top:20px; }} #map {{ break-inside:avoid; }} .panel,.metric-card,.insight {{ box-shadow:none; }} }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <div class="eyebrow">Opyta Data Analysis · Ictiofauna</div>
      <h1>Monitoramento da ictiofauna da UHE Baguari</h1>
      <p class="hero-copy">Síntese ecológica dos dados consolidados para o projeto {h(project_row['codigo_interno_opyta'])}, com leitura espacial, temporal e taxonômica da comunidade amostrada na bacia do Rio Doce.</p>
      <div class="hero-meta">{badge('Cliente: ' + project_row['nome_empresa'])}{badge('Período: ' + period_label)}{badge('Base consolidada: ' + REPORT_DATE)}{badge('Código: ' + CODIGO)}</div>
    </div>
  </header>
  <main>
    <section class="metric-grid" aria-label="Resumo geral">{cards_html}</section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Resumo executivo</span><h2>Comunidade diversa, com sinais úteis para gestão ecológica</h2></div><p>Os resultados integram {fmt_int(raw_result_rows) if raw_result_rows is not None else '-'} linhas brutas de resultados e {fmt_int(raw_effort_rows) if raw_effort_rows is not None else '-'} linhas de esforço, consolidadas em {fmt_int(len(data))} registros analíticos.</p></div>
      <div class="three-col">{summary_html}</div>
    </section>
    <section class="callout"><p><strong>Leitura ecológica.</strong> A ictiofauna registrada combina espécies nativas, espécies de interesse econômico, táxons migradores e um componente não nativo relevante. A interpretação mais robusta considera simultaneamente riqueza, abundância, origem, dominância e distribuição espacial, evitando conclusões baseadas apenas na contagem total de indivíduos.</p></section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Mapa dos pontos</span><h2>Distribuição espacial da amostragem e dos registros</h2></div><p>O tamanho dos marcadores representa abundância e a cor indica faixas de riqueza. Clique nos pontos para ver os indicadores locais.</p></div>
      <div class="map-layout"><div id="map" aria-label="Mapa interativo dos pontos de ictiofauna"></div><div class="panel"><h3>Mapa esquemático numerado</h3>{static_map_svg}<div class="map-note">As bolhas numeradas representam a posição dos pontos. O tamanho sintetiza abundância e a cor indica faixas de riqueza; linhas-guia reduzem sobreposição em áreas com pontos muito próximos.</div><div class="point-legend">{map_legend_html}</div></div></div>
    </section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Estrutura da comunidade</span><h2>Dominância, riqueza e composição taxonômica</h2></div><p>As espécies dominantes ajudam a interpretar resposta ambiental, conectividade e pressão por alterações de habitat.</p></div>
      <div class="two-col balanced"><div class="panel">{top_species_svg}</div><div class="panel">{family_svg}</div></div>
    </section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Categorias ecológicas</span><h2>Origem, estratégia reprodutiva e uso humano</h2></div><p>Essas categorias apoiam priorização de manejo, atenção a invasões biológicas e comunicação de espécies de interesse socioeconômico.</p></div>
      <div class="three-col"><div class="panel">{origin_svg}</div><div class="panel">{strategy_svg}</div><div class="panel">{economic_svg}</div></div>
    </section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Espaço e esforço</span><h2>Pontos e métodos que mais estruturam os resultados</h2></div><p>Comparar abundância e riqueza por ponto ajuda a separar locais muito produtivos de locais ecologicamente mais diversos.</p></div>
      <div class="two-col balanced"><div class="panel">{point_ab_svg}</div><div class="panel">{point_rich_svg}</div></div><div class="panel" style="margin-top:16px">{method_svg}</div>
    </section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Série temporal</span><h2>Variação de abundância e riqueza ao longo das campanhas</h2></div><p>A série temporal mostra mudanças na intensidade dos registros e na riqueza por campanha, útil para acompanhar tendências e eventos de campo.</p></div>
      <div class="panel">{time_svg}</div>
    </section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Espécies de atenção</span><h2>Conservação, origem e conectividade</h2></div><p>As tabelas abaixo destacam grupos que costumam orientar decisões de manejo e comunicação com órgãos ambientais.</p></div>
      <div class="two-col balanced">
        <div class="panel scroll-table"><h3>Espécies com status de ameaça destacado</h3><table><thead><tr><th>Espécie</th><th>Família</th><th>Status</th><th class="num">Ind.</th><th class="num">Pontos</th></tr></thead><tbody>{threat_table}</tbody></table></div>
        <div class="panel scroll-table"><h3>Não nativas mais abundantes</h3><table><thead><tr><th>Espécie</th><th>Família</th><th class="num">Ind.</th><th class="num">Pontos</th></tr></thead><tbody>{non_native_rows}</tbody></table></div>
      </div>
      <div class="panel scroll-table" style="margin-top:16px"><h3>Espécies migradoras registradas no cadastro</h3><table><thead><tr><th>Espécie</th><th>Família</th><th>Estratégia</th><th class="num">Ind.</th><th class="num">Pontos</th></tr></thead><tbody>{migratory_table}</tbody></table></div>
    </section>
    <section>
      <div class="section-head"><div><span class="section-kicker">Tabelas de apoio</span><h2>Principais espécies e pontos amostrais</h2></div></div>
      <div class="panel scroll-table"><h3>Top 15 espécies por abundância</h3><table><thead><tr><th>Espécie</th><th>Família</th><th>Origem</th><th class="num">Indivíduos</th><th class="num">Pontos</th><th class="num">% total</th></tr></thead><tbody>{species_table_rows}</tbody></table></div>
      <div class="panel scroll-table" style="margin-top:16px"><h3>Resumo por ponto</h3><table><thead><tr><th>Ponto</th><th class="num">Campanhas</th><th class="num">Riqueza</th><th class="num">Indivíduos</th><th class="num">Latitude</th><th class="num">Longitude</th></tr></thead><tbody>{point_table}</tbody></table></div>
    </section>
    <section class="callout"><p><strong>Nota técnica.</strong> Os indicadores foram calculados a partir da base migrada e consolidada em banco. Linhas brutas com múltiplos indivíduos/lotes foram agregadas por campanha, ponto, método, tipo de amostragem e espécie, preservando a soma de indivíduos. Esforços qualitativos marcados como N.A. foram tratados como ausência de valor numérico.</p></section>
    <p class="foot">Relatório HTML gerado em {REPORT_DATE}. Fonte: banco Opyta/Data, projeto {CODIGO}; planilha de carga: {h(XLSX.name)}.</p>
  </main>
  <script>window.BAGUARI_POINTS = {map_data};</script>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    (function () {{
      const points = window.BAGUARI_POINTS || [];
      const el = document.getElementById('map');
      if (!el || !points.length || typeof L === 'undefined') {{
        if (el) el.innerHTML = '<div style="padding:24px;color:#66766f">Mapa interativo indisponível. Use o mapa esquemático ao lado.</div>';
        return;
      }}
      const map = L.map(el, {{ scrollWheelZoom: false }});
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 18, attribution: '&copy; OpenStreetMap' }}).addTo(map);
      const maxAb = Math.max(...points.map(p => p.abundancia || 0), 1);
      const maxRich = Math.max(...points.map(p => p.riqueza || 0), 1);
      const bounds = [];
      points.forEach(p => {{
        const richnessRatio = (p.riqueza || 0) / maxRich;
        const color = richnessRatio > .66 ? '#2f6f8f' : richnessRatio > .33 ? '#1f7a4d' : '#d69a2d';
        const radius = 5 + 11 * Math.sqrt((p.abundancia || 0) / maxAb);
        const marker = L.circleMarker([p.latitude, p.longitude], {{ radius, color: '#ffffff', weight: 2, fillColor: color, fillOpacity: .58 }}).addTo(map);
        marker.bindPopup(`<strong>${{p.ponto}}</strong><br>Campanhas: ${{p.campanhas}}<br>Riqueza: ${{p.riqueza}} espécies<br>Indivíduos: ${{Number(p.abundancia).toLocaleString('pt-BR')}}<br>Registros: ${{p.registros}}`);
        marker.bindTooltip(`${{p.idx}} · ${{p.ponto}}`, {{ sticky: true, direction: 'top' }});
        L.marker([p.latitude, p.longitude], {{
          interactive: false,
          icon: L.divIcon({{ className: 'point-icon', html: `<span>${{p.idx}}</span>`, iconSize: [24, 24], iconAnchor: [12, 12] }})
        }}).addTo(map);
        bounds.push([p.latitude, p.longitude]);
      }});
      map.fitBounds(bounds, {{ padding: [42, 42], maxZoom: 11 }});
    }})();
  </script>
</body>
</html>
"""

    OUT_HTML.write_text(html, encoding="utf-8")
    return {
        "html": str(OUT_HTML),
        "bytes": OUT_HTML.stat().st_size,
        "records": len(data),
        "species": richness_total,
        "individuals": int(total_individuals),
        "points": len(point_rows),
        "campaigns": int(points["nome_campanha"].nunique()),
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
