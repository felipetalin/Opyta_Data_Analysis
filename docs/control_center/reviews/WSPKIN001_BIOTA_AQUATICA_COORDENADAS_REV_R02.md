# WSPKIN001 - Biota aquatica - Coordenadas REV R02

## Controle

- projeto: WSPKIN001 / Kinross
- grupos afetados: Fitoplancton e Zooplancton
- tipo principal: `data`
- impacto: `R3`
- estado: `awaiting_revision_approval`
- aberta em: 2026-09-04
- linha de base: 20 registros ponto-campanha em `public.pontos_coleta` e 368 registros de `public.biota_analise_consolidada`.

## Solicitacao

- substituir as coordenadas dos pontos PT01 a PT10 pelas coordenadas geograficas e UTM 23S fornecidas pelo usuario antes da geracao dos resultados.
- manter suspensa a geracao enquanto banco e consolidado nao estiverem conferidos.

## Escopo E Dependencias

- Gate A reaberto somente para coordenadas.
- atualizar `public.pontos_coleta` nas duas campanhas.
- sincronizar latitude/longitude de `public.biota_analise_consolidada`.
- preservar backups transacionais antes da alteracao.
- regenerar posteriormente os produtos espaciais, Darwin Core, bases e manifestos; as tabelas de composicao taxonomica nao mudam em conteudo taxonomico.

## Validacao Previa

- latitude/longitude conferidas contra os pares UTM informados na zona 23S com elipsoide WGS84/SIRGAS 2000.
- diferenca maxima encontrada inferior a 0,01 m, compativel com arredondamento dos valores UTM a centimetros.

## Execucao E Gate R

- aplicado em: 2026-09-04 18:36:07 UTC.
- `public.pontos_coleta`: 20/20 linhas ponto-campanha atualizadas; 10 pares espaciais finais.
- `public.biota_analise_consolidada`: 368/368 linhas sincronizadas; divergencias espaciais pos-update: zero.
- totais preservados: Fitoplancton 124 registros e 77 taxons; Zooplancton 244 registros e 51 taxons canonicos.
- backups: `public.backup_pontos_wspkin001_coordenadas_r02_20260904t183607z` e `public.backup_biota_wspkin001_coordenadas_r02_20260904t183607z`.
- auditoria: `outputs/validacoes/wspkin001_coordenadas_r02_20260904/20260904t183607z_auditoria_coordenadas_wspkin001_r02.json`, status `OK`.
- Gate R: aguarda confirmacao do usuario; nenhuma geracao de resultados foi executada.
