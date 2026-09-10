# BRAAEG001 - Fitoplâncton - Physolinum e Scytonemataceae - REV R04

## Controle

- projeto: BRAAEG001 / A&G Mineração
- grupo: Fitoplâncton
- operação relacionada: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- revisão: R04
- tipo principal: `taxonomia`
- tipos secundários: `dados`, `analise`
- impacto: `R3`
- estado: `approved`
- aberta em: 2026-07-28
- atualizada em: 2026-07-28

## Solicitação

- avaliar `Physolinum sp.`, que permanece como registro de maior atenção por classificação incompleta e uso pouco frequente do gênero.
- avaliar `Scytonemataceae N.I.`, removendo `None`/`N.I.` quando possível e tratando como família se tecnicamente adequado.

## Decisões Aplicadas

- `Physolinum sp.`:
  - nome do laudo preservado;
  - classificação complementada para `Chlorophyta > Ulvophyceae > Trentepohliales > Trentepohliaceae > Physolinum`;
  - observação no cadastro registra que o gênero é raro e atualmente tratado em AlgaeBase como sinônimo associado a `Trentepohlia`.
- `Scytonemataceae N.I.`:
  - renomeado para `Scytonemataceae`;
  - tratado no nível de família;
  - gênero mantido vazio.

## Aplicação No Banco

- script: `scripts/projects/braaeg001/fix_taxonomia_fitoplancton_r04_physolinum_scytonemataceae.py`.
- dry-run: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Fito/20260728T134928_fix_taxonomia_fitoplancton_r04_braaeg001.xlsx`.
- apply: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Fito/20260728T134939_fix_taxonomia_fitoplancton_r04_braaeg001.xlsx`.
- backups:
  - `public.backup_especies_braaeg001_fitoplancton_taxonomia_r04_20260728t134939`;
  - `public.backup_biota_braaeg001_fitoplancton_taxonomia_r04_20260728t134939`.
- consolidação reconstruída: 144 linhas em `public.biota_analise_consolidada`.
- riqueza taxonômica consolidada: 65 táxons.

## Produtos

- pasta oficial regenerada: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/fitoplancton`.
- auditoria oficial de geração: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T135325_geracao_resultados_fitoplancton_a4_paisagem.json`.
- prancha visual oficial: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T135325_contact_sheet_figuras_fitoplancton_a4_paisagem.png`.
- validação: `OK`, 12/12 figuras válidas, 33 arquivos finais e 0 erros.
- limpeza: pastas de trabalho intermediárias `fitoplancton_R03_taxonomia` e `fitoplancton_R04_taxonomia` removidas em 2026-07-28; mantida apenas a pasta oficial `fitoplancton`.

## Gate R

- estado: aprovado pelo usuário em 2026-07-28.
- decisão: pacote oficial R04 aceito para Fitoplâncton.
