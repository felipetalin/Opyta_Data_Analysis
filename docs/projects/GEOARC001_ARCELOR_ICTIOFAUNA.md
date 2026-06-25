# GEOARC001 - Monitoramento Arcelor - Ictiofauna

Status: `migrated_consolidated_configuring_analysis`

## Identidade Supabase

- `id_projeto`: `190`
- `id_cliente`: `31`
- `codigo_interno_opyta`: `GEOARC001`
- nome: `Monitoramento Arcelor`
- cliente: `Geomil Servicos de Mineracao Ltda.`
- CNPJ: `25.184.466/0001-15`
- `canonical_key`:
  `GEOARC001__monitoramento_arcelor`
- cadastrado no Supabase em: `2026-06-23`
- data de inicio: `2024-01-01`
- data final prevista: `2027-07-01`

## Central De Controle

- operacao: Migracao inicial - 18 campanhas
- estado operacional: `configuring_analysis`
- registro:
  `docs/control_center/operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md`
- proxima acao: configurar template multicampanha/serie longa, paleta, pasta final e produtos para Gate C
- Gate A - dados: aprovado
- Gate B - especies: aprovado
- Gate C - analises: pendente

## Dados De Entrada

- planilha original:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx.xlsx`
- planilha corrigida para Gate B:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx`
- cadastro de especies original:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326.xlsx`
- cadastro de especies corrigido:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326_CORRIGIDA_GATE_B_R02.xlsx`
- grupo: Ictiofauna
- campanhas: 18
- pontos cadastrados: 11
- pontos com resultados: 9
- linhas de pontos: 198
- linhas de esforco: 198
- linhas de resultados: 301
- especies nos resultados: 23

## Pasta Final

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Resultados`

## Validacao

Validador:

`scripts/validation/validar_migracao_ictiofauna.py`

Validacao pos-cadastro:

`outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_post_cadastro.xlsx`

Resultado:

- bloqueios: 0;
- avisos: 2;
- veredito: `pode_prosseguir=true`.

Avisos remanescentes:

- 154 resultados sao duplicatas exatas;
- 51 grupos campanha+ponto+metodo+tipo+especie possuem multiplas linhas e serao agregaveis pelo migrador.

## Decisoes Confirmadas

### Unidade Taxonomica

- `Australoheros oblongus` foi tratado como `Australoheros facetus`.
- `Crenicihla lepidota` foi corrigida para `Crenicichla lepidota`.
- `Hyphessobrycon santae` permanece sem `cf.`, distinto de `Hyphessobrycon cf. santae`.
- `Piabina argentea` foi tratada como especie nova.

### Especies Novas Cadastradas

- `Hyphessobrycon santae` - `id_especie=5452`
- `Crenicichla lepidota` - `id_especie=5453`
- `Australoheros facetus` - `id_especie=5454`
- `Piabina argentea` - `id_especie=5455`

### Cadastro Complementar

A copia corrigida removeu `N.A.` de `bmwp_score`, corrigiu o genero
`Crenicichla` e removeu espacos invisiveis em `Ordem` e `Familia`.

## Lastros

- projeto no banco:
  `outputs/validacoes/geoarc001_arcelor/cadastro_banco_geoarc001_projeto_20260623_gateb.json`
- especies no banco:
  `outputs/validacoes/geoarc001_arcelor/cadastro_banco_geoarc001_especies_20260623_gateb.json`
- validacao pos-cadastro:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_post_cadastro.md`

## Migracao E Consolidacao

- migracao: concluida em 2026-06-23
- consolidacao: concluida em 2026-06-23
- script de migracao:
  `G:/Meu Drive/Opyta/Opyta_Data/scripts/migrar_ictiofauna.py`
- script de consolidacao:
  `G:/Meu Drive/Opyta/Opyta_Data/scripts/processar_dados.py`
- pontos campanha+ponto: 198
- esforcos Ictiofauna: 198
- resultados no Excel: 301
- resultados agregados no banco: 150
- individuos: 707
- especies: 23
- backup completo antes da consolidacao:
  `public.backup_biota_consolidada_before_geoarc001_20260623t191207z`
- linhas globais consolidadas: 22.324 antes, 22.474 depois
- linhas consolidadas `GEOARC001`/`Ictiofauna`: 150
- auditoria da migracao:
  `outputs/_migration/geoarc001_ictiofauna/migration_audit.md`
- auditoria da consolidacao:
  `outputs/_migration/geoarc001_ictiofauna/consolidation_audit.md`

Observacao: o script oficial de consolidacao usa `PC_g` como campo `biomassa`
em ictiofauna. Para CPUEb exata, manter a planilha validada como fonte
linha-a-linha nas analises.

## Analises E Produtos

Como ha 18 campanhas, a configuracao analitica deve priorizar template de serie
longa/multicampanha. Gate C ainda precisa aprovar template, paleta, pasta final
e produtos.
