"""
Gera relatorio HTML consolidado da analise de Ictiofauna - Projeto 165.

Le os outputs em <OUTPUT_BASE> produzidos por run_ictio_pipeline_165.py e
produz UM unico arquivo HTML portavel (imagens embarcadas em base64),
pronto para apresentacao ao cliente.

Saida: <OUTPUT_BASE>/_relatorio_consolidado/relatorio_ictio_165.html
"""
from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd

OUTPUT_BASE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia"
    r"\Guanhães Energia\Resultados e análises\28_campanha-Abril_26"
    r"\Ictiofauna\Análise consolidada"
)

EMPREENDIMENTOS = ["Jacaré", "Senhora do Porto", "Dores de Guanhães", "Fortuna II"]

# ---------------------------------------------------------------------------
def _img(p: Path, alt: str = "") -> str:
    """PNG embarcado base64 em <img>."""
    if not p.exists():
        return f"<p style='color:#a00'><em>[imagem ausente: {html.escape(str(p))}]</em></p>"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return (f"<figure><img alt='{html.escape(alt)}' "
            f"src='data:image/png;base64,{b64}' />"
            f"<figcaption>{html.escape(alt)}</figcaption></figure>")


def _read_txt(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _df_to_html(df: pd.DataFrame, **kw) -> str:
    return df.to_html(index=False, classes="tbl", border=0,
                      float_format=lambda v: f"{v:.3f}", **kw)


def _section(emp: str) -> str:
    folder = OUTPUT_BASE / emp
    out = [f"<h2 id='emp-{emp}'>{html.escape(emp)}</h2>"]

    # score
    f_score = folder / "07_estabilidade" / "07_criterios_estabilidade.xlsx"
    if f_score.exists():
        df = pd.read_excel(f_score)
        out.append("<h3>Criterios de estabilidade (score 0-6)</h3>")
        out.append(_df_to_html(df))
    out.append(_img(folder / "07_estabilidade" / "07a_estabilidade_score.png",
                    f"{emp} - score de estabilidade"))

    # suficiencia
    out.append("<h3>Suficiência amostral</h3>")
    out.append(_img(folder / "00_suficiencia_amostral" / "00a_curva_suficiencia.png",
                    f"{emp} - curva de suficiência (Mao Tau + Chao2)"))

    # alfa + tendencia
    out.append("<h3>Diversidade alfa Pré/Pós e tendência temporal</h3>")
    out.append(_img(folder / "01_diversidade_alfa" / "01a_boxplot_alfa_pre_pos.png",
                    f"{emp} - alfa Pré/Pós"))
    out.append(_img(folder / "02_tendencia_temporal" / "02a_painel_temporal.png",
                    f"{emp} - painel temporal (regressão ano-a-ano)"))

    # estrutura
    out.append("<h3>Estrutura da comunidade</h3>")
    out.append(_img(folder / "03_estrutura_comunidade" / "03a_heatmap_similaridade.png",
                    f"{emp} - heatmap Bray-Curtis"))
    out.append(_img(folder / "03_estrutura_comunidade" / "03b_pcoa_campanhas.png",
                    f"{emp} - PCoA Pré/Pós"))
    out.append(_img(folder / "03_estrutura_comunidade" / "03c_dendrograma_temporal.png",
                    f"{emp} - dendrograma temporal"))

    # ANOSIM/PERMANOVA
    out.append("<h3>Diferença entre períodos (ANOSIM + PERMANOVA, 999 perms)</h3>")
    f_ap = folder / "04_diferenca_periodos" / "04_anosim_permanova.xlsx"
    if f_ap.exists():
        out.append(_df_to_html(pd.read_excel(f_ap)))
    out.append(_img(folder / "04_diferenca_periodos" / "04a_resumo_anosim_permanova.png",
                    f"{emp} - ANOSIM/PERMANOVA"))

    # beta temporal + Legendre + ITS
    out.append("<h3>β-diversidade temporal (Baselga) e β-Legendre/ITS</h3>")
    f_bres = folder / "05_beta_temporal" / "05_beta_resumo_por_fase.xlsx"
    if f_bres.exists():
        out.append(_df_to_html(pd.read_excel(f_bres)))
    out.append(_img(folder / "05_beta_temporal" / "05a_beta_temporal.png",
                    f"{emp} - β-Sorensen + Baselga (consecutivos)"))
    f_its = folder / "05_beta_temporal" / "05b_its_resumo.xlsx"
    if f_its.exists():
        out.append("<p><strong>ITS (Interrupted Time Series) sobre β-Legendre:</strong></p>")
        out.append(_df_to_html(pd.read_excel(f_its)))
    out.append(_img(folder / "05_beta_temporal" / "05b_beta_legendre_its.png",
                    f"{emp} - β-Legendre por campanha + ITS"))
    out.append(_img(folder / "05_beta_temporal" / "05c_lcbd_por_ponto.png",
                    f"{emp} - LCBD por ponto"))

    # sintese
    txt = _read_txt(folder / "06_sintese" / "06_sintese.txt")
    if txt:
        out.append("<h3>Síntese textual</h3>")
        out.append(f"<pre class='sintese'>{html.escape(txt)}</pre>")

    return "\n".join(out)


def _section_painel() -> str:
    base = OUTPUT_BASE / "_painel_comparativo"
    out = ["<h2 id='painel'>Painel comparativo entre empreendimentos</h2>"]
    out.append(_img(base / "painel_comparativo_metricas.png",
                    "Painel comparativo - S, H', CPUEn, β-Sor, β-Legendre, score"))
    out.append(_img(base / "painel_comparativo_estabilidade.png",
                    "Score de estabilidade comparado (0-6)"))
    return "\n".join(out)


def _section_cascata() -> str:
    base = OUTPUT_BASE / "_analise_cascata"
    out = ["<h2 id='cascata'>Análise de cascata (Ganassin et al. 2021)</h2>"]
    out.append("<p>Cascata do <strong>Rio Guanhães</strong> "
               "(montante → jusante): Jacaré (1) → Senhora do Porto (2) → "
               "Dores de Guanhães (3). <strong>Fortuna II</strong> está "
               "isolada no Rio Corrente Grande e entra como referência regional "
               "fora-cascata.</p>")

    f_grad = base / "01_gradiente_cascata.xlsx"
    if f_grad.exists():
        out.append("<h3>Gradiente alfa (medianas Pós)</h3>")
        out.append(_df_to_html(pd.read_excel(f_grad)))
    f_st = base / "02_gradiente_estatistica.xlsx"
    if f_st.exists():
        out.append("<h3>Estatística do gradiente (Spearman + linear; n=3, indicativo)</h3>")
        out.append(_df_to_html(pd.read_excel(f_st)))
    out.append(_img(base / "03_gradiente_cascata.png",
                    "Gradiente da cascata - S, H', CPUEn ao longo da posição"))

    f_pares = base / "04_pares_beta_baselga.xlsx"
    if f_pares.exists():
        out.append("<h3>β-diversidade pareada (Baselga)</h3>")
        out.append(_df_to_html(pd.read_excel(f_pares)))
    out.append(_img(base / "05_beta_vs_distancia_cascata.png",
                    "β-Sorensen + Baselga vs distância na cascata"))
    out.append(_img(base / "06_nestedness_assimetrico.png",
                    "Nestedness assimétrico - jusante ⊆ montante?"))

    txt = _read_txt(base / "00_sintese_cascata.txt")
    if txt:
        out.append("<h3>Síntese da cascata</h3>")
        out.append(f"<pre class='sintese'>{html.escape(txt)}</pre>")
    return "\n".join(out)


def _section_conclusao() -> str:
    base = OUTPUT_BASE / "_conclusao_estabilidade"
    out = ["<h2 id='conclusao'>Conclusão de estabilidade ecológica</h2>"]
    f_x = base / "conclusao_estabilidade.xlsx"
    if f_x.exists():
        df = pd.read_excel(f_x)
        out.append("<h3>Tabela consolidada</h3>")
        out.append(_df_to_html(df))
    txt = _read_txt(base / "conclusao_estabilidade.txt")
    if txt:
        out.append("<h3>Parecer técnico</h3>")
        out.append(f"<pre class='sintese'>{html.escape(txt)}</pre>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
def main() -> None:
    out_dir = OUTPUT_BASE / "_relatorio_consolidado"
    out_dir.mkdir(parents=True, exist_ok=True)

    css = """
    body { font-family: 'Segoe UI', Calibri, Arial, sans-serif;
           max-width: 1200px; margin: 24px auto; padding: 0 24px;
           color:#222; line-height:1.5; }
    h1 { border-bottom: 3px solid #1f4e79; padding-bottom: 6px; color:#1f4e79; }
    h2 { border-bottom: 2px solid #d0d7e2; padding-bottom: 4px;
         margin-top: 48px; color:#1f4e79; }
    h3 { color:#365f91; margin-top: 24px; }
    figure { margin: 12px 0 24px 0; text-align:center; }
    figure img { max-width: 100%; height: auto;
                 border:1px solid #d0d7e2; padding:4px; background:#fff; }
    figcaption { color:#555; font-size: 0.9em; margin-top: 4px; }
    pre.sintese { background:#f5f7fb; padding:12px 16px;
                  border-left: 4px solid #1f4e79; white-space: pre-wrap;
                  font-size: 0.9em; }
    table.tbl { border-collapse: collapse; width: 100%; margin: 12px 0;
                font-size: 0.92em; }
    table.tbl th, table.tbl td { border: 1px solid #d0d7e2;
                                  padding: 6px 10px; text-align:left; }
    table.tbl th { background:#e8eef7; color:#1f4e79; }
    nav.toc { background:#f5f7fb; padding: 12px 18px; border-radius: 6px;
              margin: 24px 0; }
    nav.toc a { color:#1f4e79; text-decoration:none; margin-right: 16px; }
    nav.toc a:hover { text-decoration:underline; }
    .meta { color:#666; font-size: 0.95em; }
    """

    toc = ["<nav class='toc'><strong>Conteúdo:</strong> "]
    toc.append("<a href='#sumario'>Sumário executivo</a>")
    toc.append("<a href='#painel'>Painel comparativo</a>")
    toc.append("<a href='#cascata'>Cascata (Ganassin)</a>")
    toc.append("<a href='#conclusao'>Conclusão</a>")
    for emp in EMPREENDIMENTOS:
        toc.append(f"<a href='#emp-{emp}'>{html.escape(emp)}</a>")
    toc.append("</nav>")

    sumario_exec = """
    <h2 id='sumario'>Sumário executivo</h2>
    <p>Esta análise consolida 38 campanhas de monitoramento da
       <strong>ictiofauna</strong> da Guanhães Energia (4 PCHs)
       e avalia a <strong>estabilização ecológica</strong> das assembleias
       de peixes em reservatórios neotropicais, integrando o framework
       de Agostinho et al. (2016), Legendre &amp; De Cáceres (2013),
       Baselga (2010), Ferreira et al. (2026, Hydrobiologia) e
       Ganassin et al. (2021, Sci. Total Environ.).</p>
    <p>Escopo: filtro <em>tipo_amostragem = Quantitativa</em>; corte
       Pré/Pós = <strong>2017-07-01</strong>; CPUE em ind ou g por 100 m².</p>
    <p>Score 0-6 (critérios objetivos C1-C6: suficiência amostral,
       tendência alfa, CV temporal, predomínio de turnover sobre
       nestedness, β-Sorensen mediana, ITS sobre β-Legendre).</p>
    <ul>
      <li><strong>Jacaré:</strong> 3/6 — Estabilidade parcial.</li>
      <li><strong>Senhora do Porto:</strong> 3/6 — Estabilidade parcial.</li>
      <li><strong>Dores de Guanhães:</strong> 2/6 — Instável / em reorganização.</li>
      <li><strong>Fortuna II:</strong> 2/6 — Instável / em reorganização.</li>
    </ul>
    <p><strong>Padrão de cascata (Guanhães):</strong> nestedness assimétrico
       jusante ⊆ montante = <strong>93-100%</strong>, com S e CPUEn
       declinando ao longo da cascata (compatível com Ganassin et al. 2021,
       embora com n=3 reservatórios o gradiente seja indicativo, não teste).</p>
    """

    body_parts = [toc[0] + " ".join(toc[1:]), sumario_exec,
                  _section_painel(), _section_cascata(),
                  _section_conclusao()]
    for emp in EMPREENDIMENTOS:
        body_parts.append(_section(emp))

    html_doc = (
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8' />"
        "<title>Relatório Ictiofauna - Guanhães Energia (ITAGUA001)</title>"
        f"<style>{css}</style></head><body>"
        "<h1>Análise consolidada de Ictiofauna - Guanhães Energia</h1>"
        "<p class='meta'>Projeto ITAGUA001 (165) | "
        "4 PCHs: Jacaré, Senhora do Porto, Dores de Guanhães, Fortuna II | "
        "Corte Pré/Pós: 2017-07-01 | "
        "Pipeline: <code>run_ictio_pipeline_165.py</code></p>"
        + "\n".join(body_parts)
        + "</body></html>"
    )

    out_file = out_dir / "relatorio_ictio_165.html"
    out_file.write_text(html_doc, encoding="utf-8")
    print(f"OK -> {out_file}  ({out_file.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
