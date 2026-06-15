# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
import base64
from html import escape
import mimetypes
from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd


RUN_DATE = date(2026, 6, 4)
RESULTADOS_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados"
    r"\resultados_ictiofauna_porto_estrela_producao_20260603"
)
REFERENCE_DOCX = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Relatório Consolidado"
    r"\Relatório Consolidado - UHE Porto Estrela - 2004 a 2026 - 260603.docx"
)
OUTPUT_HTML = RESULTADOS_DIR / "relatorio_tecnico_ictiofauna_porto_estrela_20260604.html"
OUTPUT_HTML_EMBEDDED = (
    RESULTADOS_DIR / "relatorio_tecnico_ictiofauna_porto_estrela_20260604_autonomo_celular.html"
)
EMBED_ASSETS = False

RECENT_AH = ["AH2324", "AH2425", "AH2526"]
BLOCK_FILES = {
    "6.6.1 - todas as espécies": "secao_661_cpue_todas_especies_dados.xlsx",
    "6.6.2 - nativas e não nativas": "secao_662_cpue_nativas_nao_nativas_dados.xlsx",
    "6.6.3 - migradoras": "secao_663_cpue_migradoras_nativas_nao_nativas_dados.xlsx",
    "6.6.4 - ameaçadas": "secao_664_cpue_ameacadas_dados.xlsx",
}


def _norm(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().strip().split())


def _col(df: pd.DataFrame, name: str) -> str:
    target = _norm(name)
    for column in df.columns:
        if _norm(column) == target:
            return column
    raise KeyError(f"Coluna nao encontrada: {name}")


def _fmt_int(value: object) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}".replace(",", ".")


def _fmt_num(value: object, decimals: int = 2) -> str:
    if pd.isna(value):
        return "-"
    text = f"{float(value):,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: object, decimals: int = 1) -> str:
    return f"{_fmt_num(value, decimals)}%"


def _read_xlsx(filename: str, sheet_name: str | int = 0, **kwargs) -> pd.DataFrame:
    return pd.read_excel(RESULTADOS_DIR / filename, sheet_name=sheet_name, **kwargs)


def _exists(filename: str) -> bool:
    return (RESULTADOS_DIR / filename).exists()


def _link(filename: str, label: str | None = None) -> str:
    if not _exists(filename):
        return f"<span class='missing'>{escape(filename)} não encontrado</span>"
    label = filename if label is None else label
    return f"<a href='{escape(filename)}'>{escape(label)}</a>"


def _asset_src(filename: str) -> str:
    if not EMBED_ASSETS:
        return filename
    path = RESULTADOS_DIR / filename
    if not path.exists():
        return filename
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _table(headers: list[str], rows: list[list[object]], css_class: str = "") -> str:
    cls = f" class='{css_class}'" if css_class else ""
    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>")
    return f"<table{cls}><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _figure(filename: str, caption: str, excel: str | None = None) -> str:
    if not _exists(filename):
        return f"<div class='callout warn'>Figura não encontrada: {escape(filename)}</div>"
    links = [_link(filename, "PNG")]
    if excel:
        links.append(_link(excel, "Excel"))
    src = _asset_src(filename)
    return f"""
    <figure>
      <img src="{escape(src)}" alt="{escape(caption)}">
      <figcaption>{escape(caption)} <span class="file-links">{" · ".join(links)}</span></figcaption>
    </figure>
    """


def _figure_grid(items: list[tuple[str, str, str | None]], columns: int = 2) -> str:
    cls = "fig-grid two" if columns == 2 else "fig-grid"
    return f"<div class='{cls}'>" + "".join(_figure(*item) for item in items) + "</div>"


def _significant_mask(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "sim", "yes"]) | (series == True)


def _load_inflections() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for block, filename in BLOCK_FILES.items():
        path = RESULTADOS_DIR / filename
        if not path.exists():
            continue
        for metric in ["CPUEn", "CPUEb"]:
            df = pd.read_excel(path, sheet_name=f"Ponto_Inflexao_{metric}")
            sig_col = _col(df, "Significativo_BH_0_05")
            sig = df[_significant_mask(df[sig_col])].copy()
            for _, row in sig.iterrows():
                rows.append(
                    {
                        "Bloco": block,
                        "Métrica": metric,
                        "Categoria": row.get("Categoria", "-"),
                        "Trecho": row.get("Trecho", "-"),
                        "Ponto de inflexão": row.get("Breakpoint_AH", "-"),
                        "p_BH": row.get("p_BH", np.nan),
                        "R2 linear": row.get("R2_Linear", np.nan),
                        "R2 segmentado": row.get("R2_Segmentado", np.nan),
                    }
                )
    return pd.DataFrame(rows)


def _summaries() -> dict[str, object]:
    t5 = _read_xlsx("tabela_05_composicao_especies.xlsx", "Tabela 5")
    t6 = _read_xlsx("tabela_06_caracteristicas_biologicas.xlsx", "Tabela 6")
    t7 = _read_xlsx("tabela_07_ocorrencia_fa_fr.xlsx", "Tabela 7")
    t8_raw = _read_xlsx("tabela_08_biometria_biomassa.xlsx", "Tabela 8")
    t8 = t8_raw[t8_raw["Espécie"].notna()].copy()

    comp = {
        "species": len(t5),
        "orders": t5["Ordem"].nunique(),
        "families": t5["Família"].nunique(),
        "top_orders": t5["Ordem"].value_counts().head(5),
        "top_families": t5["Família"].value_counts().head(8),
    }

    mig = t6[_col(t6, "Migração")].astype(str).str.strip()
    dist = t6[_col(t6, "Distribuição")].astype(str).str.strip()
    threat = t6[_col(t6, "Ameaçada de extinção")].astype(str).str.strip()
    commercial = t6[_col(t6, "Interesse Comercial")].astype(str).str.strip()
    jus = t6[_col(t6, "Jusante")].astype(str).str.strip()
    mon = t6[_col(t6, "Montante")].astype(str).str.strip()
    bio = {
        "migradoras": int((mig == "Migradora").sum()),
        "nao_migradoras": int((mig == "Não migradora").sum()),
        "nativas": int((dist == "Nativa").sum()),
        "nao_nativas": int((dist == "Não nativa").sum()),
        "ameacadas_cadastro": int((threat == "Sim").sum()),
        "interesse_comercial": int((commercial == "Sim").sum()),
        "presenca_ambos": int(((jus == "Presença") & (mon == "Presença")).sum()),
        "somente_jusante": int(((jus == "Presença") & (mon != "Presença")).sum()),
        "somente_montante": int(((mon == "Presença") & (jus != "Presença")).sum()),
    }

    occ = {
        "fa9": int((t7["FA"] == 9).sum()),
        "fa8mais": int((t7["FA"] >= 8).sum()),
        "mais_amplas": t7.sort_values(["FA", "FR (%)", "Espécie"], ascending=[False, False, True]).head(10),
    }

    t8 = t8.rename(
        columns={
            "B": "Biomassa_g",
            "CT (cm)": "CT_min",
            "Unnamed: 4": "CT_med",
            "Unnamed: 5": "CT_max",
            "PC (g)": "PC_min",
            "Unnamed: 7": "PC_med",
            "Unnamed: 8": "PC_max",
        }
    )
    for colname in ["N", "Biomassa_g", "CT_min", "CT_med", "CT_max", "PC_min", "PC_med", "PC_max"]:
        t8[colname] = pd.to_numeric(t8[colname], errors="coerce")
    biom = {
        "total_n": t8["N"].sum(),
        "total_b": t8["Biomassa_g"].sum(),
        "top_n": t8.sort_values("N", ascending=False).head(10),
        "top_b": t8.sort_values("Biomassa_g", ascending=False).head(10),
    }

    curva = _read_xlsx("figura_10_curva_coletor_dados.xlsx", "Curva")
    final_curve = curva.sort_values("Unidade_Amostral").iloc[-1]
    collector = {
        "units": int(final_curve["Unidade_Amostral"]),
        "obs": float(final_curve["Riqueza_Observada_Media"]),
        "obs_dp": float(final_curve["Riqueza_Observada_DP"]),
        "jack": float(final_curve["Jackknife1_Medio"]),
        "jack_dp": float(final_curve["Jackknife1_DP"]),
        "coverage": float(final_curve["Riqueza_Observada_Media"] / final_curve["Jackknife1_Medio"] * 100),
        "permutations": int(final_curve["Permutacoes"]),
    }

    richness = _read_xlsx("figura_12_riqueza_temporal_dados.xlsx", "Riqueza")
    max_rich = richness.loc[richness["Riqueza_Total"].idxmax()]
    min_rich = richness.loc[richness["Riqueza_Total"].idxmin()]
    recent_rich = richness[richness["Ano_Hidrologico"].isin(RECENT_AH)].copy()

    reg = _read_xlsx("figura_13_cpue_regressao_dados.xlsx", "Regressoes")

    diversity = _read_xlsx("figura_30_diversidade_equitabilidade_dados.xlsx", "Diversidade")
    div_ranges = (
        diversity.groupby("Trecho")
        .agg(
            Shannon_min=("Shannon", "min"),
            Shannon_max=("Shannon", "max"),
            Pielou_min=("Pielou", "min"),
            Pielou_max=("Pielou", "max"),
        )
        .reset_index()
    )
    recent_div = diversity[diversity["Ano_Hidrologico"].isin(RECENT_AH)].copy()

    beta = _read_xlsx("figura_31_beta_temporal_pa_dados.xlsx", "Beta_temporal_PA")
    beta_stats = (
        beta.groupby("Trecho")
        .agg(
            Sor_med=("Beta_Sorensen", "median"),
            Sor_max=("Beta_Sorensen", "max"),
            Turn_med=("Turnover_BetaSim", "median"),
            Turn_max=("Turnover_BetaSim", "max"),
            Nes_med=("Nestedness_BetaNes", "median"),
            Nes_max=("Nestedness_BetaNes", "max"),
        )
        .reset_index()
    )

    repro = _read_xlsx("figuras_32_33_reproducao_femeas_migradoras_dados.xlsx", "Todas")
    repro_totals = (
        repro.groupby(["Origem_Modelo", "Trecho", "EMG_Codigo"], as_index=False)["Abundancia"]
        .sum()
        .sort_values(["Origem_Modelo", "Trecho", "EMG_Codigo"])
    )

    inflections = _load_inflections()

    return {
        "t5": t5,
        "t6": t6,
        "t7": t7,
        "t8": t8,
        "comp": comp,
        "bio": bio,
        "occ": occ,
        "biom": biom,
        "collector": collector,
        "richness": richness,
        "max_rich": max_rich,
        "min_rich": min_rich,
        "recent_rich": recent_rich,
        "reg": reg,
        "diversity": diversity,
        "div_ranges": div_ranges,
        "recent_div": recent_div,
        "beta_stats": beta_stats,
        "repro_totals": repro_totals,
        "inflections": inflections,
    }


def _top_series_table(series: pd.Series, value_label: str) -> str:
    rows = [[idx, _fmt_int(value)] for idx, value in series.items()]
    return _table(["Grupo", value_label], rows, "compact")


def _df_table(df: pd.DataFrame, columns: list[str], headers: list[str] | None = None, limit: int | None = None) -> str:
    view = df.copy()
    if limit is not None:
        view = view.head(limit)
    rows: list[list[object]] = []
    for _, row in view.iterrows():
        rendered = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                rendered.append(_fmt_num(value, 3 if abs(value) < 1 else 2))
            else:
                rendered.append(value)
        rows.append(rendered)
    return _table(headers or columns, rows, "compact")


def _build_html(data: dict[str, object]) -> str:
    comp = data["comp"]
    bio = data["bio"]
    occ = data["occ"]
    biom = data["biom"]
    collector = data["collector"]
    max_rich = data["max_rich"]
    min_rich = data["min_rich"]
    recent_rich = data["recent_rich"]
    reg = data["reg"]
    div_ranges = data["div_ranges"]
    recent_div = data["recent_div"]
    beta_stats = data["beta_stats"]
    repro_totals = data["repro_totals"]
    inflections = data["inflections"]

    kpi_rows = [
        ["Espécies registradas", _fmt_int(comp["species"])],
        ["Ordens / famílias", f"{_fmt_int(comp['orders'])} / {_fmt_int(comp['families'])}"],
        ["Migradoras / não migradoras", f"{_fmt_int(bio['migradoras'])} / {_fmt_int(bio['nao_migradoras'])}"],
        ["Nativas / não nativas", f"{_fmt_int(bio['nativas'])} / {_fmt_int(bio['nao_nativas'])}"],
        ["Ameaçadas no cadastro / análise oficial", f"{_fmt_int(bio['ameacadas_cadastro'])} / 3"],
        ["Com interesse comercial", _fmt_int(bio["interesse_comercial"])],
        ["Campanhas consolidadas", "90"],
        ["Período analisado", "jan/2004 a dez/2025"],
    ]

    reg_rows = []
    for _, row in reg.iterrows():
        reg_rows.append(
            [
                row["Trecho"],
                row["Metrica"],
                _fmt_num(row["Coeficiente_b"], 3),
                _fmt_num(row["R2"], 3),
            ]
        )

    inflection_rows: list[list[object]] = []
    if not inflections.empty:
        for _, row in inflections.sort_values(["Bloco", "Métrica", "Trecho", "Categoria"]).iterrows():
            inflection_rows.append(
                [
                    row["Bloco"],
                    row["Métrica"],
                    row["Categoria"],
                    row["Trecho"],
                    row["Ponto de inflexão"],
                    _fmt_num(row["p_BH"], 3),
                    _fmt_num(row["R2 linear"], 3),
                    _fmt_num(row["R2 segmentado"], 3),
                ]
            )

    recent_rich_rows = [
        [
            row["Ano_Hidrologico"],
            row["Rotulo"],
            _fmt_int(row["Riqueza_Total"]),
            _fmt_int(row["Riqueza_Nativa"]),
            _fmt_int(row["Riqueza_Nao_Nativa"]),
        ]
        for _, row in recent_rich.iterrows()
    ]

    diversity_rows = [
        [
            row["Trecho"],
            f"{_fmt_num(row['Shannon_min'], 2)} - {_fmt_num(row['Shannon_max'], 2)}",
            f"{_fmt_num(row['Pielou_min'], 2)} - {_fmt_num(row['Pielou_max'], 2)}",
        ]
        for _, row in div_ranges.iterrows()
    ]
    recent_div_rows = [
        [
            row["Trecho"],
            row["Ano_Hidrologico"],
            row["Rotulo"],
            _fmt_int(row["Riqueza"]),
            _fmt_num(row["Shannon"], 2),
            _fmt_num(row["Pielou"], 2),
        ]
        for _, row in recent_div.sort_values(["Trecho", "Ordem_AH"]).iterrows()
    ]

    beta_rows = [
        [
            row["Trecho"],
            _fmt_num(row["Sor_med"], 3),
            _fmt_num(row["Sor_max"], 3),
            _fmt_num(row["Turn_med"], 3),
            _fmt_num(row["Turn_max"], 3),
            _fmt_num(row["Nes_med"], 3),
            _fmt_num(row["Nes_max"], 3),
        ]
        for _, row in beta_stats.iterrows()
    ]

    repro_rows = []
    for _, row in repro_totals.iterrows():
        repro_rows.append([row["Origem_Modelo"], row["Trecho"], row["EMG_Codigo"], _fmt_int(row["Abundancia"])])

    top_n_rows = [
        [row["Espécie"], _fmt_int(row["N"])]
        for _, row in biom["top_n"].iterrows()
    ]
    top_b_rows = [
        [row["Espécie"], _fmt_num(row["Biomassa_g"], 1)]
        for _, row in biom["top_b"].iterrows()
    ]

    css = """
    :root {
      --blue: #002060;
      --blue-2: #1f4e79;
      --blue-3: #5b9bd5;
      --light: #eef4fb;
      --line: #d8e2ee;
      --text: #1d2733;
      --muted: #5f6c7b;
      --accent: #d4672a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--text);
      background: #f7f9fc;
      line-height: 1.55;
      font-size: 16px;
    }
    main {
      width: min(1180px, calc(100% - 40px));
      margin: 0 auto 64px;
      background: white;
      box-shadow: 0 18px 60px rgba(0, 32, 96, .12);
    }
    header {
      padding: 52px 64px 42px;
      color: white;
      background: linear-gradient(135deg, var(--blue), var(--blue-2));
    }
    header p { margin: 8px 0 0; color: #dfeaf6; font-size: 18px; }
    h1 { margin: 0; font-size: 36px; line-height: 1.15; font-weight: 750; }
    h2 {
      margin: 42px 0 14px;
      padding-bottom: 8px;
      border-bottom: 2px solid var(--line);
      color: var(--blue);
      font-size: 25px;
    }
    h3 { margin: 28px 0 10px; color: var(--blue-2); font-size: 20px; }
    section { padding: 0 64px 20px; }
    .lead { font-size: 18px; color: #26384d; }
    .meta {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 24px 0 6px;
    }
    .kpi {
      background: var(--light);
      border: 1px solid var(--line);
      padding: 12px 14px;
      border-radius: 8px;
    }
    .kpi strong { display: block; color: var(--blue); font-size: 21px; }
    .kpi span { color: var(--muted); font-size: 13px; }
    .callout {
      margin: 18px 0;
      padding: 16px 18px;
      border-left: 5px solid var(--blue-3);
      background: #f3f8fd;
    }
    .warn { border-color: var(--accent); background: #fff5ef; }
    .toc {
      columns: 2;
      padding-left: 18px;
    }
    .toc li { break-inside: avoid; margin: 4px 0; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0 22px;
      font-size: 14px;
    }
    th {
      background: var(--blue);
      color: white;
      text-align: left;
      padding: 8px 10px;
      font-weight: 650;
    }
    td {
      border-bottom: 1px solid var(--line);
      padding: 7px 10px;
      vertical-align: top;
    }
    tr:nth-child(even) td { background: #fafcff; }
    table.compact { font-size: 13.5px; }
    figure {
      margin: 22px 0 28px;
      padding: 12px;
      border: 1px solid var(--line);
      background: white;
    }
    figure img {
      display: block;
      width: 100%;
      max-width: 100%;
      height: auto;
    }
    figcaption {
      margin-top: 8px;
      color: #334155;
      font-size: 13.5px;
    }
    .file-links { color: var(--muted); white-space: nowrap; }
    a { color: var(--blue-2); text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; }
    .fig-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      align-items: start;
    }
    .fig-grid figure { margin: 8px 0 16px; }
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }
    .note { color: var(--muted); font-size: 14px; }
    .missing { color: #b42318; font-weight: 700; }
    .page-break { break-before: page; }
    @media print {
      body { background: white; }
      main { width: 100%; margin: 0; box-shadow: none; }
      section, header { padding-left: 28px; padding-right: 28px; }
      figure { break-inside: avoid; }
      h2 { break-after: avoid; }
      a { color: inherit; }
    }
    @media (max-width: 900px) {
      main { width: 100%; }
      header, section { padding-left: 24px; padding-right: 24px; }
      .meta, .fig-grid, .two-col { grid-template-columns: 1fr; }
      .toc { columns: 1; }
    }
    """

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Relatório técnico - Ictiofauna UHE Porto Estrela</title>
  <style>{css}</style>
</head>
<body>
<main>
  <header>
    <h1>Monitoramento da ictiofauna da UHE Porto Estrela</h1>
    <p>Análise técnica consolidada e texto-base para relatório · janeiro de 2004 a dezembro de 2025</p>
    <p class="note">Gerado em {RUN_DATE.strftime('%d/%m/%Y')} a partir dos produtos oficiais da pasta de produção.</p>
  </header>

  <section>
    <h2>Resumo Executivo</h2>
    <p class="lead">
      O conjunto de dados consolidado para a UHE Porto Estrela reúne 90 campanhas de monitoramento da ictiofauna
      realizadas no rio Santo Antônio, município de Joanésia/MG, com avaliação integrada de composição, ocorrência,
      CPUE em número e biomassa, diversidade, diversidade beta temporal e atividade reprodutiva de fêmeas de espécies
      migradoras. A interpretação abaixo foi estruturada para servir como texto-base de relatório técnico, mantendo
      separados os produtos oficiais em Excel e PNG.
    </p>
    <div class="meta">
      {"".join(f"<div class='kpi'><strong>{escape(v)}</strong><span>{escape(k)}</span></div>" for k, v in kpi_rows)}
    </div>
    <div class="callout">
      A base aprovada considera 61 espécies registradas. Para o bloco de espécies ameaçadas, a análise oficial trata
      três espécies, excluindo <em>Lophiosilurus alexandri</em> desse recorte por se tratar de espécie exótica na bacia,
      embora a espécie permaneça nos demais produtos de composição, biometria e CPUE geral.
    </div>
    <h3>Produtos utilizados</h3>
    <ul class="toc">
      <li>Tabela 5 - composição de espécies.</li>
      <li>Tabela 6 - características biológicas e ocorrência espacial.</li>
      <li>Tabela 7 - frequência absoluta e relativa de ocorrência.</li>
      <li>Tabela 8 - abundância, biomassa e biometria.</li>
      <li>Figuras 10 a 16 - composição, suficiência amostral, riqueza e CPUE.</li>
      <li>Blocos 6.6.1 a 6.6.4 - séries temporais, tornado e mapas de CPUE.</li>
      <li>Figuras 30 e 31 - diversidade/equitabilidade e diversidade beta temporal.</li>
      <li>Figuras 32 a 34 - estádios reprodutivos de fêmeas migradoras.</li>
    </ul>
  </section>

  <section>
    <h2>Base Analítica e Premissas</h2>
    <p>
      As amostragens qualitativas foram utilizadas para compor as análises de composição, ocorrência e suficiência
      amostral. As amostragens quantitativas constituem a base principal das análises temporais, especialmente para
      CPUEn, CPUEb, diversidade, equitabilidade e modelos de tendência. A estrutura espacial foi mantida por ponto
      amostral e por trecho, evitando alterar a nomenclatura original dos pontos e garantindo reuso dos scripts em
      outros empreendimentos.
    </p>
    <p>
      O trecho de montante é formado por P4, P5, P2 e P1, em ordem geográfica de montante para jusante. O trecho de
      jusante é formado por P3, P6, P7, P8 e P9. A coordenada oficial corrigida para P1 é latitude -19,108602 e
      longitude -42,662967. Os anos hidrológicos recentes destacados graficamente correspondem a AH2324, AH2425 e
      AH2526; este último representa o corte atual da base, encerrado em dezembro de 2025.
    </p>
    <h3>CPUE e biomassa</h3>
    <p>
      A CPUEn foi calculada como abundância dividida pelo esforço e multiplicada por 100. Para CPUEb, o campo PC_g foi
      tratado como peso individual; portanto, quando uma linha contém mais de um indivíduo, a biomassa da linha foi
      obtida por N × PC_g antes da divisão pelo esforço. Assim, a CPUEb expressa a biomassa padronizada em g/100 m².
    </p>
    <h3>Pontos de inflexão</h3>
    <p>
      As séries temporais de CPUE foram avaliadas por regressão segmentada. O modelo linear simples foi utilizado como
      hipótese nula, enquanto o modelo alternativo incluiu um termo de quebra. O ponto de inflexão foi definido pelo
      menor erro quadrático do modelo segmentado, respeitando mínimo de cinco anos hidrológicos por segmento. A
      significância global foi avaliada por permutação dos resíduos do modelo nulo e os valores de p foram corrigidos
      por Benjamini-Hochberg. Nos gráficos, a linha vertical de inflexão é exibida apenas quando p_BH ≤ 0,05.
    </p>
  </section>

  <section>
    <h2>Composição da Ictiofauna</h2>
    <p>
      A ictiofauna registrada na área de influência da UHE Porto Estrela totalizou {comp['species']} espécies,
      distribuídas em {comp['families']} famílias e {comp['orders']} ordens. O conjunto reflete uma comunidade com
      participação expressiva de espécies nativas, mas também com presença importante de espécies não nativas,
      condição relevante para a interpretação das séries temporais e para a definição dos grupos ecológicos do relatório.
    </p>
    <div class="two-col">
      <div>
        <h3>Ordens mais representativas</h3>
        {_top_series_table(comp['top_orders'], 'Nº de espécies')}
      </div>
      <div>
        <h3>Famílias mais representativas</h3>
        {_top_series_table(comp['top_families'], 'Nº de espécies')}
      </div>
    </div>
    {_figure_grid([
        ('figura_11a_percentual_ordem.png', 'Figura 11a. Percentual de espécies por ordem.', 'figura_11_ordem_familia_dados.xlsx'),
        ('figura_11b_percentual_familia.png', 'Figura 11b. Percentual de espécies por família.', 'figura_11_ordem_familia_dados.xlsx'),
    ])}
    <h3>Caracterização biológica</h3>
    <p>
      A Tabela 6 organiza os atributos ecológicos utilizados nos blocos analíticos: migração, distribuição, ameaça de
      extinção, interesse comercial e ocorrência espacial. Foram registradas {bio['migradoras']} espécies migradoras e
      {bio['nao_migradoras']} não migradoras; quanto à distribuição, {bio['nativas']} espécies foram classificadas como
      nativas e {bio['nao_nativas']} como não nativas. A ocorrência simultânea em montante e jusante foi observada em
      {bio['presenca_ambos']} espécies, enquanto {bio['somente_jusante']} ocorreram apenas a jusante e
      {bio['somente_montante']} apenas a montante.
    </p>
    {_table(
        ['Indicador', 'Resultado'],
        [
            ['Migradoras', _fmt_int(bio['migradoras'])],
            ['Não migradoras', _fmt_int(bio['nao_migradoras'])],
            ['Nativas', _fmt_int(bio['nativas'])],
            ['Não nativas', _fmt_int(bio['nao_nativas'])],
            ['Ameaçadas no cadastro', _fmt_int(bio['ameacadas_cadastro'])],
            ['Com interesse comercial', _fmt_int(bio['interesse_comercial'])],
            ['Presença em ambos os trechos', _fmt_int(bio['presenca_ambos'])],
        ],
        'compact',
    )}
    <p class="note">Arquivos: {_link('tabela_05_composicao_especies.xlsx', 'Tabela 5 em Excel')} · {_link('tabela_06_caracteristicas_biologicas.xlsx', 'Tabela 6 em Excel')}</p>
  </section>

  <section class="page-break">
    <h2>Suficiência Amostral</h2>
    <p>
      A curva do coletor foi construída com unidades amostrais do tipo campanha × ponto, utilizando
      {collector['permutations']} permutações. Ao final de {collector['units']} unidades amostrais, a riqueza observada
      foi de {_fmt_num(collector['obs'], 1)} espécies, enquanto o estimador Jackknife 1 indicou
      {_fmt_num(collector['jack'], 1)} espécies. A cobertura amostral aproximada foi de {_fmt_pct(collector['coverage'], 1)},
      indicando elevada suficiência para caracterizar a composição regional registrada no monitoramento.
    </p>
    <p>
      A diferença remanescente entre riqueza observada e estimada sugere que espécies raras ou de ocorrência ocasional
      ainda podem ser adicionadas com a continuidade do programa, mas a estabilização da curva demonstra que o esforço
      acumulado é robusto para sustentar as análises de composição, ocorrência e agrupamentos ecológicos.
    </p>
    {_figure(
        'figura_10_curva_coletor_observada_jackknife1.png',
        'Figura 10. Curva do coletor da riqueza ictiofaunística com riqueza observada e Jackknife 1.',
        'figura_10_curva_coletor_dados.xlsx',
    )}
  </section>

  <section>
    <h2>Riqueza, Ocorrência e Biometria</h2>
    <p>
      A riqueza total variou ao longo da série, com maior valor no ano hidrológico {max_rich['Ano_Hidrologico']}
      ({max_rich['Rotulo']}), quando foram registradas {_fmt_int(max_rich['Riqueza_Total'])} espécies. O menor valor
      ocorreu em {min_rich['Ano_Hidrologico']} ({min_rich['Rotulo']}), com {_fmt_int(min_rich['Riqueza_Total'])}
      espécies, devendo ser interpretado considerando que AH2526 corresponde ao corte atual da base até dezembro de
      2025. Nos anos recentes, a riqueza total foi:
    </p>
    {_table(['Ano hidrológico', 'Rótulo', 'Total', 'Nativas', 'Não nativas'], recent_rich_rows, 'compact')}
    {_figure(
        'figura_12_riqueza_temporal_ano_hidrologico.png',
        'Figura 12. Variação temporal da riqueza total, nativa e não nativa por ano hidrológico.',
        'figura_12_riqueza_temporal_dados.xlsx',
    )}
    <h3>Ocorrência espacial</h3>
    <p>
      A frequência de ocorrência foi calculada nos nove pontos amostrais, na ordem P9, P8, P7, P6, P3, P1, P2, P5 e
      P4. Foram registradas {occ['fa9']} espécies com ocorrência em todos os pontos e {occ['fa8mais']} espécies com
      ocorrência em pelo menos oito pontos, indicando um núcleo de espécies amplamente distribuídas na área de
      influência.
    </p>
    {_df_table(
        occ['mais_amplas'],
        ['Espécie', 'Distribuição', 'FA', 'FR (%)'],
        ['Espécie', 'Distribuição', 'FA', 'FR (%)'],
        limit=10,
    )}
    <p class="note">Arquivo: {_link('tabela_07_ocorrencia_fa_fr.xlsx', 'Tabela 7 em Excel')}</p>
    <h3>Abundância, biomassa e medidas biométricas</h3>
    <p>
      A Tabela 8 consolida número de indivíduos, biomassa total e estatísticas de comprimento e peso por espécie. No
      conjunto quantitativo, foram contabilizados {_fmt_int(biom['total_n'])} indivíduos e biomassa acumulada de
      {_fmt_num(biom['total_b'], 1)} g. As espécies mais abundantes e com maior biomassa acumulada nem sempre
      coincidem, evidenciando a influência do porte corporal na interpretação da CPUEb.
    </p>
    <div class="two-col">
      <div>
        <h3>Maiores abundâncias</h3>
        {_table(['Espécie', 'N'], top_n_rows, 'compact')}
      </div>
      <div>
        <h3>Maiores biomassas</h3>
        {_table(['Espécie', 'B (g)'], top_b_rows, 'compact')}
      </div>
    </div>
    <p class="note">Arquivo: {_link('tabela_08_biometria_biomassa.xlsx', 'Tabela 8 em Excel')}</p>
  </section>

  <section class="page-break">
    <h2>CPUE e Séries Temporais</h2>
    <p>
      As séries de CPUEn e CPUEb evidenciam variação temporal marcada entre anos hidrológicos e entre os trechos de
      montante e jusante. A regressão linear simples foi mantida como descrição geral de tendência, enquanto a regressão
      segmentada foi utilizada para identificar mudanças estatisticamente sustentadas no comportamento temporal dos
      grupos ecológicos.
    </p>
    {_table(['Trecho', 'Métrica', 'Coeficiente b', 'R²'], reg_rows, 'compact')}
    <p>
      Os coeficientes negativos observados para CPUEn e CPUEb nos dois trechos indicam tendência geral de redução dos
      valores padronizados ao longo do período monitorado. A interpretação, entretanto, deve considerar a heterogeneidade
      entre grupos biológicos, a presença de espécies não nativas e a influência de anos específicos com oscilações
      abruptas de biomassa.
    </p>
    {_figure(
        'figura_13_painel_cpue_regressao.png',
        'Figura 13. CPUEn e CPUEb a montante e jusante com regressão linear simples.',
        'figura_13_cpue_regressao_dados.xlsx',
    )}
    {_figure_grid([
        ('figura_13a_cpuen_montante_ano_hidrologico.png', 'Figura 13a. CPUEn a montante por ano hidrológico.', 'figura_13_cpue_regressao_dados.xlsx'),
        ('figura_13b_cpueb_montante_ano_hidrologico.png', 'Figura 13b. CPUEb a montante por ano hidrológico.', 'figura_13_cpue_regressao_dados.xlsx'),
        ('figura_13c_cpuen_jusante_ano_hidrologico.png', 'Figura 13c. CPUEn a jusante por ano hidrológico.', 'figura_13_cpue_regressao_dados.xlsx'),
        ('figura_13d_cpueb_jusante_ano_hidrologico.png', 'Figura 13d. CPUEb a jusante por ano hidrológico.', 'figura_13_cpue_regressao_dados.xlsx'),
    ])}
    {_figure(
        'figura_14_cpue_percentual_migracao_origem.png',
        'Figura 14. Participação relativa de CPUEn e CPUEb por grupos de migração e origem.',
        'figura_14_cpue_percentual_grupos_dados.xlsx',
    )}
    <h3>Espécies nativas: período completo e condição atual</h3>
    <p>
      A avaliação específica das espécies nativas foi organizada em dois recortes complementares. O primeiro sintetiza
      o período completo de monitoramento, enquanto o segundo destaca AH2324, AH2425 e AH2526 para apoiar a leitura da
      condição atual. Esse recorte recente é útil para separar tendências históricas de respostas mais próximas do
      cenário contemporâneo do empreendimento.
    </p>
    {_figure_grid([
        ('figura_15_especies_nativas_periodo_completo.png', 'Figura 15. CPUEn e CPUEb das espécies nativas no período completo.', 'figura_15_especies_nativas_periodo_completo_dados.xlsx'),
        ('figura_16_especies_nativas_recorte_atual.png', 'Figura 16. CPUEn e CPUEb das espécies nativas no recorte AH2324-AH2526.', 'figura_16_especies_nativas_recorte_atual_dados.xlsx'),
    ])}
    <h3>Pontos de inflexão estatisticamente significativos</h3>
    <p>
      As linhas verticais de ponto de inflexão foram exibidas apenas quando o teste segmentado apresentou p_BH ≤ 0,05.
      Os resultados significativos identificados nos blocos oficiais estão resumidos abaixo.
    </p>
    {(_table(['Bloco', 'Métrica', 'Categoria', 'Trecho', 'Ponto de inflexão', 'p_BH', 'R² linear', 'R² segmentado'], inflection_rows, 'compact') if inflection_rows else "<div class='callout'>Nenhum ponto de inflexão significativo foi identificado após correção BH.</div>")}

    <h3>6.6.1 - Variação temporal e composição dos CPUEs de todas as espécies</h3>
    <p>
      O bloco de todas as espécies permite avaliar a composição geral da CPUE, separando migradoras nativas, migradoras
      não nativas, não migradoras nativas e não migradoras não nativas. Essa leitura é a referência mais ampla para
      interpretar mudanças temporais na estrutura da comunidade.
    </p>
    {_figure_grid([
        ('secao_661_cpue_todas_especies_temporal_cpuen.png', 'CPUEn temporal por grupo biológico - todas as espécies.', 'secao_661_cpue_todas_especies_dados.xlsx'),
        ('secao_661_cpue_todas_especies_temporal_cpueb.png', 'CPUEb temporal por grupo biológico - todas as espécies.', 'secao_661_cpue_todas_especies_dados.xlsx'),
        ('secao_661_cpue_todas_especies_tornado_especies.png', 'Gráfico tornado de CPUEn e CPUEb - todas as espécies.', 'secao_661_cpue_todas_especies_dados.xlsx'),
        ('secao_661_cpue_todas_especies_mapa_pizzas_cpuen.png', 'Mapa de pizzas da composição espacial de CPUEn e CPUEb - todas as espécies.', 'secao_661_cpue_todas_especies_dados.xlsx'),
    ])}

    <h3>6.6.2 - Nativas e não nativas</h3>
    <p>
      A separação por origem evidencia a contribuição relativa das espécies nativas e não nativas nos dois trechos. Esse
      recorte é central para avaliar o grau de conservação da comunidade nativa e a influência das introduções na série.
    </p>
    {_figure_grid([
        ('secao_662_cpue_nativas_nao_nativas_temporal_cpuen.png', 'CPUEn temporal - espécies nativas e não nativas.', 'secao_662_cpue_nativas_nao_nativas_dados.xlsx'),
        ('secao_662_cpue_nativas_nao_nativas_temporal_cpueb.png', 'CPUEb temporal - espécies nativas e não nativas.', 'secao_662_cpue_nativas_nao_nativas_dados.xlsx'),
        ('secao_662_cpue_nativas_nao_nativas_tornado_especies.png', 'Gráfico tornado por espécie - nativas e não nativas.', 'secao_662_cpue_nativas_nao_nativas_dados.xlsx'),
        ('secao_662_cpue_nativas_nao_nativas_mapa_pizzas_cpuen.png', 'Mapa de pizzas de CPUEn e CPUEb - nativas e não nativas.', 'secao_662_cpue_nativas_nao_nativas_dados.xlsx'),
    ])}

    <h3>6.6.3 - Migradoras nativas e não nativas</h3>
    <p>
      O recorte de espécies migradoras é particularmente importante no contexto de barramentos, por refletir grupos
      sensíveis à conectividade longitudinal, à disponibilidade de áreas de reprodução e aos históricos de transposição.
      A distinção entre migradoras nativas e não nativas evita que a resposta de espécies introduzidas seja interpretada
      como recuperação funcional da ictiofauna nativa.
    </p>
    {_figure_grid([
        ('secao_663_cpue_migradoras_nativas_nao_nativas_temporal_cpuen.png', 'CPUEn temporal - migradoras nativas e não nativas.', 'secao_663_cpue_migradoras_nativas_nao_nativas_dados.xlsx'),
        ('secao_663_cpue_migradoras_nativas_nao_nativas_temporal_cpueb.png', 'CPUEb temporal - migradoras nativas e não nativas.', 'secao_663_cpue_migradoras_nativas_nao_nativas_dados.xlsx'),
        ('secao_663_cpue_migradoras_nativas_nao_nativas_tornado_especies.png', 'Gráfico tornado por espécie - migradoras.', 'secao_663_cpue_migradoras_nativas_nao_nativas_dados.xlsx'),
        ('secao_663_cpue_migradoras_nativas_nao_nativas_mapa_pizzas_cpuen.png', 'Mapa de pizzas de CPUEn e CPUEb - migradoras.', 'secao_663_cpue_migradoras_nativas_nao_nativas_dados.xlsx'),
    ])}

    <h3>6.6.4 - Espécies ameaçadas de extinção</h3>
    <p>
      O bloco de ameaçadas foi tratado por espécie, sem categoria "outras", porque o objetivo é avaliar diretamente a
      resposta das três espécies válidas para este recorte. A ausência de ponto de inflexão significativo neste bloco
      indica que, nas séries testadas, as oscilações observadas não superaram o critério estatístico aprovado após
      correção por múltiplos testes.
    </p>
    {_figure_grid([
        ('secao_664_cpue_ameacadas_temporal_cpuen.png', 'CPUEn temporal - espécies ameaçadas.', 'secao_664_cpue_ameacadas_dados.xlsx'),
        ('secao_664_cpue_ameacadas_temporal_cpueb.png', 'CPUEb temporal - espécies ameaçadas.', 'secao_664_cpue_ameacadas_dados.xlsx'),
        ('secao_664_cpue_ameacadas_tornado_especies.png', 'Gráfico tornado por espécie - ameaçadas.', 'secao_664_cpue_ameacadas_dados.xlsx'),
        ('secao_664_cpue_ameacadas_mapa_pizzas_cpuen.png', 'Mapa de pizzas de CPUEn e CPUEb - ameaçadas.', 'secao_664_cpue_ameacadas_dados.xlsx'),
    ])}
  </section>

  <section class="page-break">
    <h2>Diversidade, Equitabilidade e Beta Temporal</h2>
    <p>
      Os índices de Shannon e Pielou foram calculados a partir da matriz quantitativa padronizada, permitindo avaliar
      mudanças no equilíbrio entre riqueza e dominância das espécies ao longo do tempo. A diversidade beta temporal foi
      calculada entre anos hidrológicos consecutivos, separadamente para montante e jusante, com decomposição em
      turnover (β-sim) e nestedness (β-nes).
    </p>
    {_table(['Trecho', 'Shannon H’', 'Pielou J’'], diversity_rows, 'compact')}
    <h3>Anos hidrológicos recentes</h3>
    {_table(['Trecho', 'Ano hidrológico', 'Rótulo', 'Riqueza', 'Shannon', 'Pielou'], recent_div_rows, 'compact')}
    {_figure(
        'figura_30_diversidade_equitabilidade.png',
        'Figura 30. Índices de diversidade e equitabilidade a montante e jusante.',
        'figura_30_diversidade_equitabilidade_dados.xlsx',
    )}
    <h3>Diversidade beta temporal</h3>
    <p>
      Valores de β-sor representam a dissimilaridade total entre anos consecutivos. O componente β-sim indica
      substituição de espécies, enquanto β-nes indica diferenças de riqueza em padrão de aninhamento. No contexto do
      monitoramento, picos de nestedness em anos recentes podem refletir perda ou redução temporária de registros,
      enquanto picos de turnover apontam para substituição mais direta na composição.
    </p>
    {_table(['Trecho', 'β-sor med.', 'β-sor máx.', 'β-sim med.', 'β-sim máx.', 'β-nes med.', 'β-nes máx.'], beta_rows, 'compact')}
    {_figure(
        'figura_31_beta_temporal_componentes_por_area.png',
        'Figura 31. Diversidade beta temporal por trecho, com β-sor, β-sim e β-nes.',
        'figura_31_beta_temporal_pa_dados.xlsx',
    )}
  </section>

  <section class="page-break">
    <h2>Atividade Reprodutiva</h2>
    <p>
      A caracterização reprodutiva foi realizada a partir dos estádios macroscópicos de maturação gonadal registrados
      nas colunas Sexo e EMG. Para fêmeas, F1 representa repouso, F2 maturação inicial, F3 maturação avançada/maduro e
      F4 desovado/esgotado. Para interpretação ecológica, F3 e F4 indicam maior evidência de atividade reprodutiva
      recente ou potencialmente associada ao ciclo reprodutivo.
    </p>
    {_table(['Origem', 'Trecho', 'EMG', 'Abundância'], repro_rows, 'compact')}
    <p>
      As figuras 32 e 33 separam fêmeas migradoras nativas e não nativas, mantendo leitura individualizada por trecho.
      A figura 34 sintetiza espacialmente a distribuição dos estádios nos pontos amostrais, utilizando o mesmo padrão de
      legenda das figuras de abundância relativa.
    </p>
    {_figure(
        'figura_32_emg_femeas_migradoras_nativas.png',
        'Figura 32. Estádios reprodutivos de fêmeas de espécies migradoras nativas.',
        'figuras_32_33_reproducao_femeas_migradoras_dados.xlsx',
    )}
    {_figure(
        'figura_33_emg_femeas_migradoras_nao_nativas.png',
        'Figura 33. Estádios reprodutivos de fêmeas de espécies migradoras não nativas.',
        'figuras_32_33_reproducao_femeas_migradoras_dados.xlsx',
    )}
    {_figure(
        'figura_34_mapa_pizzas_emg_femeas_migradoras.png',
        'Figura 34. Distribuição espacial dos estádios reprodutivos de fêmeas migradoras.',
        'figuras_32_33_reproducao_femeas_migradoras_dados.xlsx',
    )}
  </section>

  <section>
    <h2>Síntese Técnica para Discussão</h2>
    <p>
      Os resultados consolidados indicam que a área de influência da UHE Porto Estrela mantém uma ictiofauna diversa,
      com predomínio numérico de espécies nativas no cadastro, mas com contribuição relevante de espécies não nativas
      em determinados grupos de CPUE, especialmente quando avaliada a biomassa. Esse padrão reforça a necessidade de
      interpretar CPUEn e CPUEb de forma complementar: a primeira é mais sensível à abundância de espécies de pequeno
      porte, enquanto a segunda destaca a influência de espécies de maior massa corporal.
    </p>
    <p>
      A separação entre montante e jusante permanece essencial para avaliar os efeitos espaciais do barramento e da
      dinâmica longitudinal do rio Santo Antônio. O padrão temporal mostra oscilações interanuais importantes, mas os
      pontos de inflexão só foram incorporados quando sustentados por teste estatístico, evitando interpretação baseada
      apenas em mudanças visuais. O sombreamento dos anos AH2324, AH2425 e AH2526 foi mantido para destacar a condição
      atual da série, especialmente porque o último ano hidrológico representa o corte em dezembro de 2025.
    </p>
    <p>
      Para o relatório final, recomenda-se manter a leitura em blocos: composição e suficiência amostral; riqueza e
      ocorrência; CPUE geral; CPUE por origem; CPUE de migradoras; CPUE de ameaçadas; diversidade/equitabilidade;
      diversidade beta temporal; e reprodução. Essa organização facilita ajustes pontuais sem comprometer a coerência
      estatística e gráfica dos resultados.
    </p>
    <div class="callout">
      Este HTML é um produto de apoio à redação. As tabelas e figuras vinculadas permanecem como produtos oficiais, e
      qualquer alteração futura deve ser feita nos scripts/blocos analíticos correspondentes antes de atualizar o texto.
    </div>
  </section>

  <section>
    <h2>Arquivos e Reprodutibilidade</h2>
    <p>
      O relatório foi gerado a partir da pasta de produção
      <code>{escape(str(RESULTADOS_DIR))}</code>. O documento de referência consultado para alinhamento de estilo e teor
      técnico foi <code>{escape(str(REFERENCE_DOCX))}</code>.
    </p>
    <p>
      Manifesto oficial: {_link('manifesto_resultados_ictiofauna_porto_estrela.xlsx', 'Excel')} ·
      {_link('manifesto_resultados_ictiofauna_porto_estrela.md', 'Markdown')}.
    </p>
    <p class="note">
      Referências metodológicas a manter na bibliografia final, conforme revisão técnica do relatório: Bazzoli (2003)
      para estádios gonadais, Magurran e Pielou para diversidade/equitabilidade, Jackknife 1 para riqueza estimada e
      Baselga (2010) para decomposição da diversidade beta temporal.
    </p>
  </section>
</main>
</body>
</html>
"""
    return html


def main() -> None:
    global EMBED_ASSETS
    if not RESULTADOS_DIR.exists():
        raise FileNotFoundError(RESULTADOS_DIR)
    data = _summaries()
    EMBED_ASSETS = False
    html = _build_html(data)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Relatorio HTML gerado: {OUTPUT_HTML}")
    EMBED_ASSETS = True
    html_embedded = _build_html(data)
    OUTPUT_HTML_EMBEDDED.write_text(html_embedded, encoding="utf-8")
    print(f"Relatorio HTML autonomo gerado: {OUTPUT_HTML_EMBEDDED}")


if __name__ == "__main__":
    main()
