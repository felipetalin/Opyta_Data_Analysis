# BRAANG01 - Meio Fisico - Efluente DBO - REV R06

Data de abertura: 2026-07-10

## Status

- estado: `awaiting_revision_approval`
- tipo principal: `layout`
- tipos secundarios: `package`
- impacto: `R1`
- gates reabertos: nenhum gate anterior; revisao restrita a separacao visual
  dos graficos de DBO.

## Pedido

O usuario solicitou regerar as figuras de DBO em efluentes separando:

- `MCB907E` e `MCB907S` juntos;
- `MCB1005` separado.

Posteriormente, o usuario reforcou que os dados de `MCB907E` e `MCB907S`
devem ficar somente nas campanhas trimestrais/selecionadas.

## Linha De Base

Linha de base preservada a partir das revisoes anteriores:

- R02: `Efluente_MCB907/ST_Demanda_Bioquimica_de_Oxigenio_MCB907_mensal.png`;
- R03: `Efluente_MCB1005/ST_Demanda_Bioquimica_de_Oxigenio_MCB1005.png`.

Pasta de revisao:

- `Resultados/_revisoes/R06_efluente_dbo_pontos_20260710`

Conteudo criado:

- `linha_base/Efluente_DBO`: copias das figuras anteriores;
- `revisado/Efluente_DBO`: figuras revisadas;
- `scripts/revisar_braang01_efluente_dbo_pontos_r06.py`;
- `manifest_linha_base_sha256.csv`;
- `manifest_revisado_sha256.csv`;
- lastro tecnico em `outputs/_project_scripts/BRAANG01_ANGLO_MEIO_FISICO`.

## Execucao

Produtos revisados:

- `ST_Demanda_Bioquimica_de_Oxigenio_MCB907E_MCB907S.png`;
- `ST_Demanda_Bioquimica_de_Oxigenio_MCB1005.png`.

Periodicidade aplicada:

- `MCB907E/MCB907S`: somente campanhas trimestrais/selecionadas, total de 19
  campanhas;
- `MCB1005`: serie mensal, total de 54 campanhas.

Todos os graficos mantem VMP de `60 mg/L` via `vmp_430_padrao`.

## Validacao

Validacoes executadas:

- contagem da pasta revisada: 2 PNGs e 1 JSON;
- manifesto revisado recriado;
- metadado confirma `vmp_visible = 60` para `MCB907E`, `MCB907S` e `MCB1005`;
- metadado confirma `MCB907E/MCB907S` com 19 campanhas selecionadas e
  `MCB1005` com 54 campanhas mensais;
- inspecao visual confirmou `MCB907E/MCB907S` juntos com campanhas
  selecionadas;
- inspecao visual confirmou `MCB1005` separado.

Gate R:

- aguardando aprovacao do usuario para promover ou ajustar a versao revisada.
