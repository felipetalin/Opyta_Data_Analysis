# BRAANG01 - Meio Fisico - Eficiencia DBO ETE - REV R07

Data de abertura: 2026-07-13

## Status

- estado: `awaiting_revision_approval`
- tipo principal: `analise`
- tipos secundarios: `package`
- impacto: `R2`
- gates reabertos: Gate C/produto analitico; sem alteracao de banco,
  migracao ou consolidacao.

## Pedido

O usuario solicitou validar a eficiencia da ETE a partir de DBO para o par
`MCB907E`/`MCB907S`, usando criterio de remocao minima de `60%`, e gerar o
resultado tambem em Excel.

## Criterio Aplicado

- ponto de entrada: `MCB907E`;
- ponto de saida: `MCB907S`;
- parametro: `Demanda Bioquimica de Oxigenio`;
- campanhas: somente campanhas trimestrais/selecionadas ja aprovadas para
  `MCB907E/S`, a partir de 2021;
- formula:
  `Eficiencia (%) = ((DBO entrada - DBO saida) / DBO entrada) * 100`;
- criterio: atende quando a eficiencia e maior ou igual a `60%`;
- referencia normativa registrada: CONAMA 430/2011, complementar a CONAMA
  357/2005, com remocao minima de 60% de DBO.

## Saidas

Pasta de revisao:

- `Resultados/_revisoes/R07_eficiencia_dbo_ete_20260713`

Arquivos criados:

- `revisado/Eficiencia_DBO_ETE/Grafico_Eficiencia_DBO_ETE_MCB907E_MCB907S_R07.png`;
- `revisado/Eficiencia_DBO_ETE/Eficiencia_DBO_ETE_MCB907E_MCB907S_R07.xlsx`;
- `revisado/Eficiencia_DBO_ETE/Eficiencia_DBO_ETE_MCB907E_MCB907S_R07.csv`;
- `revisado/Eficiencia_DBO_ETE/revision_generation_metadata.json`;
- `manifest_revisado_sha256.csv`;
- `scripts/gerar_braang01_eficiencia_dbo_ete_r07.py`;
- lastro tecnico em `outputs/_project_scripts/BRAANG01_ANGLO_MEIO_FISICO`;
- lastro tecnico espelhado em
  `outputs/_project_scripts/BRAANG01__anglogold_meio_fisico/meio_fisico`.

## Resultado

- campanhas avaliadas: `19`;
- campanhas que atendem ao criterio: `16`;
- campanhas abaixo de 60%: `3`;
- eficiencia media simples: `80,5%`;
- eficiencia ponderada por carga de entrada: `92,7%`.

Campanhas abaixo de 60%:

- `jun-2023`: `38,9%`;
- `jun-2024`: `11,3%`;
- `nov-2024`: `42,2%`.

## Validacao

- Excel aberto e validado com 3 abas:
  `eficiencia_por_campanha`, `nao_atende`, `resumo`;
- aba `eficiencia_por_campanha`: 19 campanhas mais cabecalho;
- aba `nao_atende`: 3 campanhas mais cabecalho;
- aba `resumo`: indicadores principais;
- figura inspecionada visualmente apos ajuste de espacamento;
- manifesto SHA256 criado para os arquivos revisados;
- metadado confirma 19 campanhas, 16 atendimentos e 3 nao atendimentos.

Gate R:

- aguardando aprovacao do usuario para promover ou ajustar a versao revisada.
