# BRAAVG002 - Crosswalk de campanhas

- campanhas: 47
- regra sazonal: CH = outubro a marco; SC = abril a setembro
- ano temporal: ano temporal = agosto a julho; meses ago-dez pertencem ao ano de inicio, jan-jul ao ano anterior
- estrategia recomendada: `crosswalk_analitico_primeiro`
- apply no banco: `not_approved`

## Impacto Estimado Se Renomear No Banco

- `public.campanhas`: 47 linhas globais por `id_campanha`
- `public.biota_analise_consolidada` Ictiofauna: 519 linhas
- `public.biota_analise_consolidada` Zoobentos: 3937 linhas
- `public.fisico_analise_consolidada`: 0 linhas

## Primeiros Exemplos

- `1ª-Ago-22` -> `C001-2022-08-SC`
- `2ª-Set-22` -> `C002-2022-09-SC`
- `3ª-Out-22` -> `C003-2022-10-CH`
- `4ª-Nov-22` -> `C004-2022-11-CH`
- `5ª-Dez-22` -> `C005-2022-12-CH`
- `6ª-Jan-23` -> `C006-2023-01-CH`
- `7ª-Fev-23` -> `C007-2023-02-CH`
- `8ª-Mar-23` -> `C008-2023-03-CH`

## Arquivos

- Excel: `G:\Meu Drive\Opyta\Opyta_Data_Analysis\outputs\_project_scripts\BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg\campaign_crosswalk_20260713\braavg002_campaign_crosswalk.xlsx`
- SQL dry-run: `G:\Meu Drive\Opyta\Opyta_Data_Analysis\outputs\_project_scripts\BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg\campaign_crosswalk_20260713\braavg002_campaign_rename_dry_run.sql`

## Ciclos Temporais

- `2022/2023`: 12 campanhas (1ª-Ago-22 a 12ª-Jul-23)
- `2023/2024`: 12 campanhas (13ª-Ago-23 a 24ª-Jul-24)
- `2024/2025`: 12 campanhas (25ª-Ago-24 a 36ª-Jul-25)
- `2025/2026`: 11 campanhas (37ª-Ago-25 a 47ª-Jun-26)
