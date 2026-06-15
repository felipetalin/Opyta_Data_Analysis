# Minigraficos Temporais Por Ponto

## Quando usar

Usar quando o estudo tem muitas campanhas e poucos pontos amostrais. O grafico
substitui barras agrupadas densas por pequenos paineis, um para cada ponto.

## Estrutura visual

- Eixo X: campanhas abreviadas (`C21`, `C22`, etc.).
- Eixo Y: metrica analisada.
- Uma linha cinza conecta a serie temporal do ponto.
- Marcadores diferenciam `CH` e `SC`.
- Linha tracejada indica a media geral do estudo.
- Separadores verticais discretos marcam a mudanca de ano.

## Usos aprovados

- GEOHER001/Herculano:
  - Ictiofauna: graficos 02, 03 e 10.
  - Zoobentos: graficos 02, 03 e 10.

## Implementacao

- Ictiofauna:
  - `src/opyta_analysis/pipelines/diagnostico/ictio.py`
  - funcoes `_small_multiple_metric` e `_small_multiple_diversity`
- Zoobentos:
  - `src/opyta_analysis/pipelines/diagnostico/zoobentos.py`
  - funcoes `_small_multiple_metric` e `_small_multiple_diversity`

## Observacoes

Para diversidade alfa, usar duas linhas por painel: Shannon e Pielou. As medias
gerais tambem devem ser separadas por indice.
