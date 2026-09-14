# BRAAEG001 - Fitoplâncton - taxonomia - REV R03

## Controle

- projeto: BRAAEG001 / A&G Mineração
- grupo: Fitoplâncton
- operação relacionada: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- revisão: R03
- tipo principal: `taxonomia`
- tipos secundários: `dados`, `analise`
- impacto: `R3`
- estado: `awaiting_revision_approval`
- aberta em: 2026-07-28
- atualizada em: 2026-07-28

## Solicitação

- corrigir a classificação taxonômica de `Encyonema silesiacum`, `Pinnularia divergens`, `Eunotia veneris`, `Gomphonema sp.`, `Pinnularia boyeriformis` e `Phormidium tergestinum`.
- verificar a sinonímia de `Surirella splendida` e decidir se permanece em `Surirella` ou passa para `Iconella`.

## Decisões Aplicadas

- `Encyonema silesiacum`: família atualizada para `Encyonemataceae`.
- `Pinnularia divergens`: gênero `Pinnularia`, família `Pinnulariaceae`, ordem `Naviculales`.
- `Eunotia veneris`: `Bacillariophyta > Bacillariophyceae > Eunotiales > Eunotiaceae > Eunotia`.
- `Gomphonema sp.`: `Bacillariophyta > Bacillariophyceae > Cymbellales > Gomphonemataceae > Gomphonema`.
- `Pinnularia boyeriformis`: `Bacillariophyta > Bacillariophyceae > Naviculales > Pinnulariaceae > Pinnularia`.
- `Phormidium tergestinum`: `Cyanobacteria > Cyanophyceae > Oscillatoriales > Oscillatoriaceae > Phormidium`.
- `Surirella splendida`: atualizada para `Iconella splendida`, pois AlgaeBase registra `Surirella splendida` como sinônimo de `Iconella splendida`.

## Aplicação No Banco

- script: `scripts/projects/braaeg001/fix_taxonomia_fitoplancton_r03.py`.
- dry-run: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Fito/20260728T114816_fix_taxonomia_fitoplancton_r03_braaeg001.xlsx`.
- apply: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Fito/20260728T114827_fix_taxonomia_fitoplancton_r03_braaeg001.xlsx`.
- backups:
  - `public.backup_especies_braaeg001_fitoplancton_taxonomia_r03_20260728t114827`;
  - `public.backup_resultados_fitoplancton_braaeg001_taxonomia_r03_20260728t114827`;
  - `public.backup_biota_braaeg001_fitoplancton_taxonomia_r03_20260728t114827`.
- consolidação reconstruída: 144 linhas em `public.biota_analise_consolidada`.
- riqueza taxonômica consolidada: 65 táxons após a união de `Surirella splendida` em `Iconella splendida`.

## Produtos

- pasta oficial regenerada: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/fitoplancton`.
- pasta de contingência removida em 2026-07-28 por decisão do usuário para manter somente a pasta final oficial de trabalho.
- auditoria oficial de geração: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T115548_geracao_resultados_fitoplancton_a4_paisagem.json`.
- prancha visual oficial: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T115548_contact_sheet_figuras_fitoplancton_a4_paisagem.png`.
- auditoria e prancha da pasta de contingência R03 removidas junto com a pasta de trabalho intermediária.
- validação: `OK`, 12/12 figuras válidas, 33 arquivos finais e 0 erros.

## Gate R

- estado: aguardando aprovação do usuário.
