from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path

import pandas as pd


DEFAULT_OUTPUT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\Exploratorio_assembleia_ictiofauna"
)

FIGURES = {
    "signature": "27_grafico_assinatura_especies_grupos_funcionais_ictiofauna.png",
    "annual": "33_grafico_mini_mapas_funcoes_ecologicas_ano_ictiofauna.png",
    "persistence": "34_grafico_mapa_permanencia_funcional_ictiofauna.png",
    "balance": "35_grafico_mapa_balanco_funcional_ictiofauna.png",
    "trajectory": "36_grafico_mapa_trajetoria_funcional_ictiofauna.png",
}
DATA_FILES = {
    "signature": "27_df_assinatura_especies_grupos_funcionais_ictiofauna.xlsx",
    "annual": "33_df_mini_mapas_funcoes_ecologicas_ictiofauna.xlsx",
    "synthesis": "34_36_df_sintese_espacial_funcional_ictiofauna.xlsx",
    "manifest": "34_36_manifesto_sintese_espacial_funcional_ictiofauna.json",
}


def _fmt(value: object, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number - round(number)) < 1e-9:
        return str(int(round(number)))
    return f"{number:.{digits}f}".replace(".", ",")


def _pct(value: object) -> str:
    return f"{_fmt(value, 1)}%"


def _safe(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    head = "".join(f"<th>{_safe(label)}</th>" for _key, label in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{_safe(row.get(key, ''))}</td>" for key, _label in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _image_src(path: Path, embed_images: bool) -> str:
    if not embed_images:
        return path.name
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def load_context(output_dir: Path, *, embed_images: bool = False) -> dict[str, object]:
    signature_xlsx = output_dir / DATA_FILES["signature"]
    synthesis_xlsx = output_dir / DATA_FILES["synthesis"]
    manifest_path = output_dir / DATA_FILES["manifest"]
    missing = [name for name in [*FIGURES.values(), *DATA_FILES.values()] if not (output_dir / name).exists()]
    if missing:
        raise FileNotFoundError("Arquivos ausentes: " + ", ".join(missing))
    figure_sources = {
        key: _image_src(output_dir / filename, embed_images)
        for key, filename in FIGURES.items()
    }

    group_summary = pd.read_excel(signature_xlsx, sheet_name="resumo_grupos")
    balance = pd.read_excel(synthesis_xlsx, sheet_name="balanco_funcional")
    trajectory = pd.read_excel(synthesis_xlsx, sheet_name="trajetoria_funcional")
    persistence = pd.read_excel(synthesis_xlsx, sheet_name="permanencia_funcional")
    criteria_balance = pd.read_excel(synthesis_xlsx, sheet_name="criterios_balanco")
    criteria_trajectory = pd.read_excel(synthesis_xlsx, sheet_name="criterios_trajetoria")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    total_points = int(balance["nome_ponto"].nunique())
    years = manifest.get("years", [])
    group_rows = []
    for _, row in group_summary.sort_values("ordem_grupo").iterrows():
        group_rows.append(
            {
                "Grupo": row["grupo_rotulo"],
                "Espécies": _fmt(row["especies"]),
                "CPUEn total": _fmt(row["CPUEn_total"], 1),
                "Ameaçadas": _fmt(row["ameacadas"]),
                "Exóticas": _fmt(row["exoticas"]),
            }
        )

    balance_counts = balance["categoria_balanco"].value_counts().reindex(
        ["Refúgio funcional", "Área de transição", "Perfil funcional generalista", "Sem sinal funcional consistente"],
        fill_value=0,
    )
    trajectory_counts = trajectory["trajetoria_funcional"].value_counts().reindex(
        [
            "Ganho funcional",
            "Estabilidade funcional",
            "Oscilação funcional",
            "Enfraquecimento funcional",
            "Perfil funcional generalista",
            "Sem sinal funcional consistente",
        ],
        fill_value=0,
    )

    balance_rows = []
    for _, row in balance.sort_values("nome_ponto").iterrows():
        balance_rows.append(
            {
                "Ponto": row["nome_ponto"],
                "Categoria": row["categoria_balanco"],
                "Anos sensíveis": _fmt(row["anos_funcoes_sensiveis"]),
                "Anos generalistas": _fmt(row["anos_generalistas"]),
                "% sensível": _pct(row["perc_CPUEn_funcoes_sensiveis"]),
                "% generalista": _pct(row["perc_CPUEn_generalistas"]),
            }
        )

    trajectory_rows = []
    for _, row in trajectory.sort_values("nome_ponto").iterrows():
        trajectory_rows.append(
            {
                "Ponto": row["nome_ponto"],
                "Trajetória": row["trajetoria_funcional"],
                "Anos sensíveis": _fmt(row["anos_funcoes_sensiveis"]),
                "Pico sensível": _fmt(row["CPUEn_sensivel_pico"], 1),
                "Média recente": _fmt(row["CPUEn_sensivel_media_recente"], 1),
                "Leitura": row["justificativa"],
            }
        )

    top_persistence = (
        persistence[persistence["anos_com_registro"] > 0]
        .sort_values(["anos_com_registro", "CPUEn_soma_periodo"], ascending=[False, False])
        .head(8)
    )
    persistence_rows = []
    for _, row in top_persistence.iterrows():
        persistence_rows.append(
            {
                "Ponto": row["nome_ponto"],
                "Grupo": row["grupo_rotulo"],
                "Anos": _fmt(row["anos_com_registro"]),
                "CPUEn total": _fmt(row["CPUEn_soma_periodo"], 1),
            }
        )

    return {
        "years": years,
        "total_points": total_points,
        "group_rows": group_rows,
        "balance_counts": balance_counts.to_dict(),
        "trajectory_counts": trajectory_counts.to_dict(),
        "balance_rows": balance_rows,
        "trajectory_rows": trajectory_rows,
        "persistence_rows": persistence_rows,
        "criteria_balance": criteria_balance.to_dict("records"),
        "criteria_trajectory": criteria_trajectory.to_dict("records"),
        "figures": figure_sources,
        "embedded_images": embed_images,
    }


def build_html(context: dict[str, object]) -> str:
    years = context["years"]
    figures = context["figures"]
    period = f"{min(years)}-{max(years)}" if years else "2022-2026"
    group_table = _table(
        context["group_rows"],
        [("Grupo", "Grupo sentinela"), ("Espécies", "Espécies"), ("CPUEn total", "CPUEn total"), ("Ameaçadas", "Ameaçadas"), ("Exóticas", "Exóticas")],
    )
    balance_table = _table(
        context["balance_rows"],
        [("Ponto", "Ponto"), ("Categoria", "Balanço funcional"), ("Anos sensíveis", "Anos sensíveis"), ("Anos generalistas", "Anos generalistas"), ("% sensível", "% sensível"), ("% generalista", "% generalista")],
    )
    trajectory_table = _table(
        context["trajectory_rows"],
        [("Ponto", "Ponto"), ("Trajetória", "Trajetória"), ("Anos sensíveis", "Anos sensíveis"), ("Pico sensível", "Pico sensível"), ("Média recente", "Média recente"), ("Leitura", "Leitura técnica")],
    )
    persistence_table = _table(
        context["persistence_rows"],
        [("Ponto", "Ponto"), ("Grupo", "Grupo"), ("Anos", "Anos"), ("CPUEn total", "CPUEn total")],
    )
    balance_counts = context["balance_counts"]
    trajectory_counts = context["trajectory_counts"]

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GEOARC001 - Apresentação Técnica Funcional</title>
  <style>
    :root {{
      --ink: #18212b;
      --muted: #5d6875;
      --line: #d8dee6;
      --paper: #f5f7f8;
      --panel: #ffffff;
      --green: #2f7d4a;
      --gold: #d9a441;
      --clay: #c46a3a;
      --red: #b65b5a;
      --blue: #8ac9e8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: "Segoe UI", Arial, sans-serif;
      line-height: 1.55;
    }}
    header {{
      background: linear-gradient(110deg, #102532 0%, #284a3a 64%, #4d6a4a 100%);
      color: #fff;
      padding: 42px min(6vw, 72px) 34px;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 30px min(4vw, 44px) 60px; }}
    h1 {{ margin: 0 0 12px; font-size: clamp(2.0rem, 4vw, 3.4rem); line-height: 1.05; letter-spacing: 0; }}
    h2 {{ margin: 0 0 18px; font-size: 1.55rem; letter-spacing: 0; }}
    h3 {{ margin: 0 0 10px; font-size: 1.05rem; letter-spacing: 0; }}
    p {{ margin: 0 0 14px; }}
    .subtitle {{ max-width: 850px; color: #d9e5e4; font-size: 1.05rem; }}
    .eyebrow {{ font-weight: 700; letter-spacing: 0; text-transform: uppercase; color: #b9d7ca; font-size: 0.78rem; margin-bottom: 12px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }}
    .pill {{
      display: inline-flex; align-items: center; gap: 6px;
      border: 1px solid rgba(255,255,255,0.28); color: #f5fbfb;
      padding: 6px 10px; border-radius: 999px; font-size: 0.86rem;
      background: rgba(255,255,255,0.08);
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 22px 0;
      padding: 24px;
      box-shadow: 0 12px 26px rgba(24,33,43,0.06);
    }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }}
    .grid.two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      background: #fbfcfd;
    }}
    .stat strong {{ display: block; font-size: 1.55rem; line-height: 1.1; }}
    .stat span {{ color: var(--muted); font-size: 0.9rem; }}
    .callout {{
      border-left: 4px solid var(--green);
      background: #eef6f1;
      padding: 14px 16px;
      border-radius: 6px;
      margin: 16px 0;
    }}
    figure {{
      margin: 18px 0 6px;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }}
    figure img {{ display: block; width: 100%; height: auto; }}
    figcaption {{
      padding: 10px 13px;
      color: var(--muted);
      background: #f8fafb;
      border-top: 1px solid var(--line);
      font-size: 0.9rem;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; margin: 12px 0 0; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 8px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #f2f5f6; font-weight: 700; }}
    .note {{ color: var(--muted); font-size: 0.92rem; }}
    .tagline {{ color: var(--muted); margin-top: -8px; }}
    .legend-list {{ display: grid; gap: 8px; margin: 12px 0 0; }}
    .legend-item {{ display: flex; gap: 9px; align-items: flex-start; }}
    .dot {{ width: 12px; height: 12px; border-radius: 50%; margin-top: 6px; flex: 0 0 auto; border: 1px solid rgba(0,0,0,0.25); }}
    .green {{ background: var(--green); }}
    .gold {{ background: var(--gold); }}
    .clay {{ background: var(--clay); }}
    .red {{ background: var(--red); }}
    .gray {{ background: #d5d9de; }}
    .blue-line {{ border-top: 3px solid var(--blue); padding-top: 8px; }}
    .footer {{ color: var(--muted); font-size: 0.85rem; text-align: center; padding: 20px; }}
    @media (max-width: 840px) {{
      .grid, .grid.two {{ grid-template-columns: 1fr; }}
      section {{ padding: 18px; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      header {{ break-after: avoid; }}
      section {{ box-shadow: none; break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">GEOARC001 · Ictiofauna · Análise funcional exploratória</div>
    <h1>Avaliação Integrada Da Composição Funcional</h1>
    <p class="subtitle">Síntese técnica para discussão interna com a equipe: grupos funcionais sentinelas, permanência espacial, balanço funcional e trajetória temporal das funções sensíveis.</p>
    <div class="meta">
      <span class="pill">Período: {period}</span>
      <span class="pill">Pontos: {context["total_points"]}</span>
      <span class="pill">Base: CPUEn</span>
      <span class="pill">Produto exploratório</span>
    </div>
  </header>
  <main>
    <section>
      <h2>1. Contexto Técnico</h2>
      <p>A análise funcional foi desenvolvida para complementar a leitura taxonômica da ictiofauna. Enquanto riqueza, CPUEn, biomassa, diversidade e composição taxonômica indicam se a comunidade mudou, a composição funcional ajuda a interpretar quais funções ecológicas foram mantidas, perdidas, substituídas ou concentradas espacialmente.</p>
      <p>O foco não é propor um novo índice. A proposta é organizar evidências ecológicas rastreáveis, baseadas em atributos simples e auditáveis das espécies, permitindo discutir estabilidade, alteração e simplificação funcional da assembleia.</p>
      <div class="grid">
        <div class="stat"><strong>{len(context["group_rows"])}</strong><span>grupos funcionais avaliados na assinatura</span></div>
        <div class="stat"><strong>{sum(1 for k, v in balance_counts.items() if v > 0)}</strong><span>categorias observadas no balanço funcional</span></div>
        <div class="stat"><strong>{sum(1 for k, v in trajectory_counts.items() if v > 0)}</strong><span>trajetórias funcionais observadas</span></div>
      </div>
    </section>

    <section>
      <h2>2. Metodologia</h2>
      <p>As espécies foram classificadas em grupos funcionais sentinelas a partir de atributos ecológicos como preferência por correnteza, sensibilidade ambiental, habitat e guilda trófica. Os grupos são independentes e não mutuamente exclusivos: uma mesma espécie pode compor mais de um grupo quando responde a perguntas ecológicas distintas.</p>
      <div class="callout"><strong>Premissa central:</strong> os grupos funcionais não somam 100% da fauna. Eles funcionam como sentinelas ecológicas para acompanhar funções sensíveis, especializadas ou generalistas ao longo do monitoramento.</div>
      <figure>
        <img src="{figures["signature"]}" alt="Assinatura das espécies por grupos funcionais">
        <figcaption>Figura 27. Assinatura das espécies por grupo funcional sentinela. A figura explicita quais espécies sustentam cada grupo e por isso foi usada como base metodológica da análise.</figcaption>
      </figure>
      <h3>Grupos avaliados</h3>
      {group_table}
      <p class="note">Predadores foram avaliados na assinatura, mas removidos das figuras de síntese espacial por apresentarem sinal muito baixo no conjunto analisado.</p>
    </section>

    <section>
      <h2>3. Estratégia Analítica</h2>
      <div class="grid">
        <div class="stat blue-line"><strong>Mapa anual</strong><span>Distribui os grupos por ponto e ano, usando bolhas proporcionais ao CPUEn médio.</span></div>
        <div class="stat blue-line"><strong>Permanência</strong><span>Conta em quantos anos cada função ocorreu em cada ponto.</span></div>
        <div class="stat blue-line"><strong>Balanço</strong><span>Integra recorrência e participação acumulada para classificar o perfil funcional do ponto.</span></div>
      </div>
      <div class="callout"><strong>Pulo metodológico:</strong> a permanência indica frequência, mas não informa direção da mudança. Por isso foi incluído o mapa de trajetória funcional, que avalia ganho, oscilação ou enfraquecimento das funções sensíveis ao longo dos anos.</div>
    </section>

    <section>
      <h2>4. Resultado 1 · Mini Mapas Anuais</h2>
      <p>A figura anual permite observar quando e onde os grupos funcionais sentinelas ocorreram. A versão final usa hidrografia em azul claro, ADA em vermelho translúcido e bolhas verdes para o dado biológico, reduzindo competição visual entre camadas cartográficas e ecológicas.</p>
      <figure>
        <img src="{figures["annual"]}" alt="Mini mapas anuais dos grupos funcionais sentinelas">
        <figcaption>Figura 33. Mini mapas anuais dos grupos funcionais sentinelas. Linhas representam grupos funcionais e colunas representam anos.</figcaption>
      </figure>
    </section>

    <section>
      <h2>5. Resultado 2 · Permanência Funcional</h2>
      <p>O mapa de permanência resume a frequência temporal das funções em cada ponto. O número dentro da bolha corresponde ao total de anos com registro do grupo funcional.</p>
      <figure>
        <img src="{figures["persistence"]}" alt="Mapa de permanência funcional">
        <figcaption>Figura 34. Mapa de permanência funcional. A permanência evidencia pontos com recorrência de funções sensíveis ou generalistas.</figcaption>
      </figure>
      <h3>Maiores sinais de permanência</h3>
      {persistence_table}
    </section>

    <section>
      <h2>6. Resultado 3 · Balanço Funcional</h2>
      <p>O balanço funcional integra a recorrência das funções e sua participação acumulada em CPUEn. A nomenclatura adotada é propositalmente neutra: pontos com recorrência de generalistas são descritos como <strong>perfil funcional generalista</strong>, e não como dominância ou impacto.</p>
      <div class="grid">
        <div class="stat"><strong>{balance_counts.get("Refúgio funcional", 0)}</strong><span>pontos classificados como refúgio funcional</span></div>
        <div class="stat"><strong>{balance_counts.get("Área de transição", 0)}</strong><span>pontos em área de transição</span></div>
        <div class="stat"><strong>{balance_counts.get("Perfil funcional generalista", 0)}</strong><span>pontos com perfil funcional generalista</span></div>
      </div>
      <figure>
        <img src="{figures["balance"]}" alt="Mapa de balanço funcional">
        <figcaption>Figura 35. Mapa de balanço funcional. A classificação é exploratória e deve ser interpretada junto às séries temporais e à composição taxonômica.</figcaption>
      </figure>
      {balance_table}
    </section>

    <section>
      <h2>7. Resultado 4 · Trajetória Funcional</h2>
      <p>O mapa de trajetória funcional avalia direção temporal. Ele diferencia pontos onde funções sensíveis ganharam expressão, enfraqueceram, oscilaram ou permaneceram ausentes em favor de um perfil generalista.</p>
      <div class="legend-list">
        <div class="legend-item"><span class="dot green"></span><span><strong>Ganho funcional:</strong> funções sensíveis ausentes ou baixas no início e presentes de forma recorrente nos anos posteriores.</span></div>
        <div class="legend-item"><span class="dot red"></span><span><strong>Enfraquecimento funcional:</strong> funções sensíveis já ocorreram, mas caíram fortemente ou zeraram no período recente.</span></div>
        <div class="legend-item"><span class="dot gold"></span><span><strong>Oscilação funcional:</strong> ocorrência intermitente, sem direção temporal robusta.</span></div>
        <div class="legend-item"><span class="dot clay"></span><span><strong>Perfil funcional generalista:</strong> funções sensíveis ausentes e generalistas recorrentes.</span></div>
      </div>
      <figure>
        <img src="{figures["trajectory"]}" alt="Mapa de trajetória funcional">
        <figcaption>Figura 36. Mapa de trajetória funcional. A classificação utiliza a série anual de CPUEn das funções sensíveis. O ano de 2026 é parcial.</figcaption>
      </figure>
      {trajectory_table}
    </section>

    <section>
      <h2>8. Interpretação Integrada</h2>
      <div class="grid two">
        <div>
          <h3>Mensagens Principais</h3>
          <p>Os pontos IC-ARC-06 e IC-ARC-14 mantêm sinal de funções sensíveis em parte relevante do monitoramento, mas com trajetórias distintas: IC-ARC-06 indica ganho funcional, enquanto IC-ARC-14 indica enfraquecimento recente das funções sensíveis.</p>
          <p>IC-ARC-05 apresenta perfil funcional generalista, enquanto IC-ARC-08 apresenta oscilação funcional associada à intermitência de funções sensíveis.</p>
        </div>
        <div>
          <h3>Cuidados De Uso</h3>
          <p>As classificações são exploratórias e devem ser lidas junto com riqueza, CPUEn total, espécies dominantes, LCBD, NMDS/PERMANOVA, sazonalidade e histórico de campo.</p>
          <p>Como 2026 ainda é parcial, sua contribuição para trajetórias recentes deve ser interpretada com cautela.</p>
        </div>
      </div>
    </section>

    <section>
      <h2>9. Arquivos De Apoio</h2>
      <p>Os dados de apoio e critérios de classificação estão disponíveis nas planilhas e manifestos gerados junto às figuras.</p>
      <ul>
        <li><code>{DATA_FILES["signature"]}</code></li>
        <li><code>{DATA_FILES["annual"]}</code></li>
        <li><code>{DATA_FILES["synthesis"]}</code></li>
        <li><code>{DATA_FILES["manifest"]}</code></li>
      </ul>
    </section>
    <div class="footer">GEOARC001 · Apresentação técnica exploratória · Gerado para discussão interna da equipe técnica</div>
  </main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera HTML tecnico da analise funcional GEOARC001.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Pasta com figuras e planilhas exploratorias.")
    parser.add_argument("--html-name", default="37_apresentacao_tecnica_analise_funcional_ictiofauna.html", help="Nome do HTML de saida.")
    parser.add_argument("--embed-images", action="store_true", help="Embute as imagens em base64 para compartilhar um unico HTML.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    context = load_context(output_dir, embed_images=args.embed_images)
    html_text = build_html(context)
    out_html = output_dir / args.html_name
    out_html.write_text(html_text, encoding="utf-8")
    print(json.dumps({"html": str(out_html), "bytes": out_html.stat().st_size}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
