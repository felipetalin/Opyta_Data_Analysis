# Validacao pre-importacao - Fonseca - Biota Aquática Ictiofauna

Data: 2026-08-13

## Arquivos avaliados
- Resultados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Migracao\Fonseca\Opyta_ictiofauna_banco_dados_mar-jul_26-260813.xlsx`
- Cadastro de especies: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Migracao\Fonseca\Cadastro_especies_opyta_fonseca-ictio-2600813.xlsx`

## Veredito

**Nao importar ainda.** Foram encontrados **2 bloqueios** e **2 avisos**.

## Resumo dos dados

- codigo_opyta: BRACED001
- nome_projeto: Fonseca - Biota Aquática
- cliente: Brandt Meio Ambiente
- campanhas_pontos: 2
- pontos_unicos: 18
- linhas_pontos: 36
- linhas_esforco: 42
- linhas_resultados: 55
- linhas_cadastro_especies: 14
- linhas_endemismo: 0
- especies_resultados: 14
- especies_cadastro: 14

## Bloqueios

- **INCOMPLETE_SPECIES_CATALOG** | linhas: 3, 16, 4, 5, 6, 7, 10, 11, 12, 13: 11 especie(s) usadas nos resultados existem no cadastro mestre, mas estao incompletas. Exemplos: Psalidodon rivularis (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar, estrategia_reprodutiva, valor_economico) ; Hasemania nana (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar) ; Oligosarcus argenteus (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar) ; Astyanax lacustris (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar) ; Geophagus brasiliensis (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar) ; Trichomycterus brasiliensis (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar, estrategia_reprodutiva, valor_economico) ; Pareiorhaphis scutula (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar) ; Phalloceros uai (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar) ; Parotocinclus sp. (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar, estrategia_reprodutiva, valor_economico) ; Knodus moenkhausii (faltando: status_ameaca_nacional, status_ameaca_global, habito_alimentar)
- **SPECIES_UPSERT_CAN_OVERWRITE_EXISTING_DATA** | aba: Especies: A planilha possui especies ja existentes no banco com diferencas. Especies com risco alto: ['Hoplias malabaricus', 'Parotocinclus sp.', 'Rhamdia quelen'].
  - Ajuste: Cadastrar apenas especies novas ou ajustar o upsert para nao atualizar campos nulos em especies existentes.

## Avisos

- **RESULT_GROUPS_WILL_BE_AGGREGATED**: 12 grupos campanha+ponto+metodo+tipo+especie possuem multiplas linhas. O script de migracao pode agregar Numero_de_Individuos por soma e biometria por media.
  - Ajuste: Confirmar se as multiplas linhas representam individuos/lotes distintos.
- **CLIENT_DB_STATUS**: Cliente 'Brandt Meio Ambiente' nao foi encontrado no banco.

## Cadastro de especies

- Total: 14; novas no banco: 1; ja existentes: 13.
- Novas: Brycon opalinus.
- Existentes: Astyanax lacustris, Geophagus brasiliensis, Hasemania nana, Hoplias intermedius, Hoplias malabaricus, Knodus moenkhausii, Oligosarcus argenteus, Pareiorhaphis scutula, Parotocinclus sp., Phalloceros uai, Psalidodon rivularis, Rhamdia quelen, Trichomycterus brasiliensis.
- Atencao: para especies existentes, preferir cadastro incremental para nao sobrescrever metadados do banco.

## Arquivos gerados
- Excel detalhado: `outputs\_project_scripts\BRACED001__fonseca_biota_aquatica\ictiofauna\validation\validacao_braced001_fonseca_ictiofauna_20260813R07.xlsx`
- JSON: `outputs\_project_scripts\BRACED001__fonseca_biota_aquatica\ictiofauna\validation\validacao_braced001_fonseca_ictiofauna_20260813R07.json`