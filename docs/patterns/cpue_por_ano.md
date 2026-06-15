# CPUE Por Ano

## Quando usar

Usar quando a serie temporal tem muitas campanhas e graficos de barras por
campanha ficam ilegiveis.

## Estrutura visual

- Um arquivo por ano.
- Quatro paineis por figura, um para cada campanha do ano.
- Eixo X: pontos amostrais.
- Eixo Y: CPUE ou abundancia.
- Cores indicam estacao (`CH` e `SC`).

## Usos aprovados

- GEOHER001/Herculano:
  - Ictiofauna grafico 06: CPUEn por ano.
  - Ictiofauna grafico 07: CPUEb por ano.
  - Zoobentos grafico 06: abundancia por ordem agrupada por ano.

## Implementacao

- Ictiofauna:
  - `src/opyta_analysis/pipelines/diagnostico/ictio.py`
  - funcao `_plot_yearly_metric_panels`
- Zoobentos:
  - `src/opyta_analysis/pipelines/diagnostico/zoobentos.py`
  - funcao `_plot_06_year_panels`

## Observacoes

Para Zoobentos, manter a versao absoluta como leitura principal. A versao
relativa e util como apoio, mas pode supervalorizar campanhas com baixa
abundancia total.
