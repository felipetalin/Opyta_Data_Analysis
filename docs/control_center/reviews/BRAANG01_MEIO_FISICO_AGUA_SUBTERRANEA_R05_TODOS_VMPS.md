# BRAANG01 - Meio Fisico - Agua Subterranea - R05 Todos Os VMPs

Data: 2026-07-10

## Status

- estado: `scenario_generated`
- tipo principal: `analysis`
- impacto: `R1`
- objetivo: cenario demonstrativo para cliente, sem substituir a R05 principal.

## Pedido

Gerar, a partir da R05 de Agua Subterranea, um pacote com os VMPs de todos os
usos da Resolucao CONAMA 396/2008 para visualizacao do cenario completo.

Pasta criada:

- `Resultados/_revisoes/R05_todos_os_vmps_20260710`

## Escopo

Parametros gerados:

- `Arsenio Dissolvido`;
- `Arsenio Total`;
- `Cobalto Dissolvido`;
- `Cobre Dissolvido`;
- `Cromo Dissolvido`;
- `Solidos Dissolvidos Totais`;
- `Sulfato`;
- `Zinco Dissolvido`;
- `pH`.

## Resultado

- 18 graficos temporais `ST_*.png`;
- 1 figura-tabela `Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.png`;
- 1 figura-tabela de resultados violados
  `Tabela_Violacoes_VMPs_CONAMA396_Agua_Subterranea_R05.png`;
- 1 CSV de apoio `Tabela_Violacoes_VMPs_CONAMA396_Agua_Subterranea_R05.csv`;
- 1 figura-tabela de valores reais por ponto
  `Tabela_Valores_Reais_VMP_Agua_Subterranea_R05.png`;
- 1 CSV de apoio `Tabela_Valores_Reais_VMP_Agua_Subterranea_R05.csv`;
- 1 `revision_generation_metadata.json`;
- manifestos SHA256 de linha de base e revisado;
- script reprodutivel em `scripts/revisar_braang01_agua_subterranea_todos_vmps_r05.py`;
- lastro tecnico em `outputs/_project_scripts/BRAANG01_ANGLO_MEIO_FISICO`.

## Observacoes

- Este pacote e somente comparativo/demonstrativo.
- A R05 principal de Agua Subterranea permanece como versao de referencia para
  o recorte solicitado anteriormente.
- `Solidos Dissolvidos Totais` aparece apenas com `Consumo Humano`, pois nao ha
  limite de dessedentacao para esse parametro.
- `pH` foi gerado sem linhas de VMP.

## Validacao

- contagem da pasta revisada: 18 PNGs e 1 JSON;
- inspecao visual de `ST_Sulfato_P2.png`, confirmando quatro usos;
- inspecao visual de `ST_Solidos_Dissolvidos_Totais_P2.png`, confirmando
  somente `Consumo Humano`.
- inspecao visual da figura-tabela, confirmando legibilidade para apresentacao.
- inspecao visual da tabela de violacoes, confirmando exibicao de parametro,
  ponto, usos violados e maximo medido.
- inspecao visual da tabela de valores reais, confirmando colunas de parametro,
  VMP e pontos monitorados.
