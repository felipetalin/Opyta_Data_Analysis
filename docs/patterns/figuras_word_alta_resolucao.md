# Figuras Para Word Em Alta Resolucao

## Status

- status: aprovado
- criado em: 2026-06-19
- validado em: 2026-06-19
- substitui: uso de A4 paisagem com fontes pequenas no GEOHER001
- substituido por:

## Quando Usar

- Relatorios tecnicos montados no Microsoft Word.
- Figuras que ocupam uma pagina inteira ou uma secao em paisagem.
- Series temporais com muitos pontos ou campanhas.
- Paineis anuais, mapas de calor, dendrogramas, indices e curvas amostrais.
- Entregas que exigem boa leitura no Word e qualidade para impressao.

## Quando Nao Usar

- Miniaturas para portfolio ou interfaces web.
- Figuras simples que serao inseridas com largura muito pequena.
- Paginas obrigatoriamente em retrato quando o grafico possui muitos paineis.
- Graficos extremamente densos sem antes abreviar rotulos ou reorganizar o layout.

## Decisao Tecnica

- entrada: tabelas analiticas dos pipelines de fauna.
- processamento:
  - desenhar a figura considerando o tamanho final no Word;
  - manter resolucao de 600 dpi;
  - usar campanhas abreviadas (`C21`, `C22`, etc.) quando o codigo completo
    reduzir a area util;
  - evitar figuras muito mais largas que uma pagina A4;
  - mover identificadores de paineis para o cabecalho quando puderem colidir
    com barras ou anotacoes;
  - reorganizar paineis densos para aproveitar a pagina paisagem.
- saida: PNG em alta resolucao, pronto para insercao em pagina paisagem.
- layout:
  - tamanho-base: A4 paisagem, `11.69 x 8.27` polegadas;
  - resolucao: `600 dpi`;
  - fonte-base: `15 pt`;
  - titulos e identificadores de painel: `15-16 pt`;
  - rotulos de eixos: `16 pt`;
  - legendas: `13 pt`;
  - anotacoes: `12 pt`;
  - anotacoes internas de mapas de calor: `11 pt`;
  - marcas dos eixos em mapas de calor: `12 pt`.

## Regras Por Tipo De Figura

| Tipo | Orientacao | Regra |
| --- | --- | --- |
| Series temporais por ponto | Paisagem | Ate 4 paineis por linha; rotulos de campanha abreviados |
| CPUEn e CPUEb por ano | Paisagem | Grade 2 x 2; campanha no cabecalho do painel |
| CPUEn e CPUEb por especie | Paisagem | Mapa de calor com largura fixa de A4, sem largura proporcional ao numero de campanhas |
| Abundancia por ordem e ano | Paisagem | Grade 2 x 2 e legenda geral |
| BMWP | Paisagem | Mapa de calor com campanhas abreviadas |
| EPT e CHOL | Paisagem | Dois mapas de calor lado a lado |
| Dendrogramas e curvas amostrais | Paisagem | Uma figura por pagina |
| Composicao com poucas categorias | Compacta ou paisagem | Escolher pela extensao dos rotulos |

## Criterio De Aceite

- A figura deve permanecer legivel quando inserida na largura util de uma
  pagina A4 paisagem no Word.
- Rotulos, legendas e anotacoes nao podem depender de zoom para leitura.
- Nenhum elemento deve colidir com barras, eixos ou outros textos.
- A figura nao deve ser criada com largura excessiva para depois ser reduzida
  drasticamente pelo Word.

## Projetos De Origem

- `GEOHER001__monitoramento_de_ictio_e_bentos_herculano`
- Aprovado pelo usuario apos a regeneracao integral das 37 figuras em
  2026-06-19.

## Limitacoes

- A resolucao de 600 dpi aumenta o tamanho dos arquivos.
- Fontes maiores podem exigir abreviacao de categorias e mudanca de
  orientacao.
- Figuras com muitas categorias taxonomicas ainda podem precisar de divisao
  em partes.
- O Word deve estar configurado para nao compactar imagens quando a entrega
  exigir preservacao integral da resolucao.

## Codigo

- modulo: `src/opyta_analysis/theme.py`
- configuracao: `configs/clients/geoher001.json`
- pipelines:
  - `src/opyta_analysis/pipelines/diagnostico/ictio.py`
  - `src/opyta_analysis/pipelines/diagnostico/zoobentos.py`
- funcoes principais:
  - `_small_multiple_metric`
  - `_small_multiple_diversity`
  - `_plot_yearly_metric_panels`
  - `_plot_heatmap`
  - `_plot_06_year_panels`
  - `_run_block_11`
  - `_run_block_12`
