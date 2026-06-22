# VIRITA001 - Diagnóstico da ictiofauna do Projeto Itabrita

Status: `campaign_1_migrated_consolidated_analyzed`

## Identidade Supabase

- `id_projeto`: `189`
- `id_cliente`: `193`
- `codigo_interno_opyta`: `VIRITA001`
- nome: `Diagnóstico da ictiofauna do Projeto Itabrita`
- cliente: `Virtual Ambiental`
- local de referência: São Gonçalo do Pará, MG
- `canonical_key`:
  `VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`
- CNPJ: `00.750.399/0001-28`
- cadastrado no Supabase em: `2026-06-22`

## Central De Controle

- operacao: Ictiofauna — Campanha 1
- estado operacional: `review_planned`
- registro:
  `docs/control_center/operations/VIRITA001_ICTIOFAUNA_CAMPANHA_1.md`
- proxima acao: abrir a revisao R01 quando os ajustes de layout forem informados
- Gate A — dados: aprovado
- Gate B — especies: aprovado
- Gate C — analises: aprovado
- Gate R — revisao: pendente; R01 ainda sem escopo executavel

## Dados De Entrada

- planilha de importação:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Campanha/Junho 26/Planilha/Opyta-Virtual-Itabrita-Ictio-2026_260621.xlsx`
- cadastro de espécies:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Campanha/Junho 26/Planilha/Cadastro_especies_virtual_itabrita-ictio-260621.xlsx`
- planilha corrigida para migração:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Campanha/Junho 26/Planilha/Opyta-Virtual-Itabrita-Ictio-2026_260621_MIGRACAO_CORRIGIDA.xlsx`
- cadastro incremental corrigido:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Campanha/Junho 26/Planilha/Cadastro_especies_virtual_itabrita-ictio-260621_NOVAS_MIGRACAO_CORRIGIDA.xlsx`
- grupo: Ictiofauna
- campanha: `ITA001_AH2526_202606`
- período amostral: 17 e 18 de junho de 2026
- pontos: `Ictio_01` a `Ictio_07`
- linhas de esforço: 9
- linhas de resultados: 31
- espécies nos resultados: 15
- espécies no cadastro fornecido: 15

## Pasta Final

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Resultados/Ictiofauna/Campanha_1`

A pasta já existe. Em 2026-06-22 continha apenas `desktop.ini`.

## Validação Inicial

Validador:

`scripts/validation/validar_migracao_ictiofauna.py`

Relatório:

`outputs/validacoes/virita001_itabrita/validacao_virita001_itabrita_ictiofauna_20260622.xlsx`

Resultado inicial após reconhecer o padrão de campanha `*_AH####_AAAAMM`:

- bloqueios: 4;
- avisos: 19;
- campos obrigatórios ausentes: 0;
- valores numéricos inválidos: 0;
- relações de esforço ausentes: 0;
- divergências entre esforço dos resultados e metadados: 0;
- duplicidades exatas: 0.

Validação final do pacote corrigido:

- bloqueios: 0;
- avisos: 11;
- veredito: pode seguir para ensaio de migração.

Relatório final:

`outputs/validacoes/virita001_itabrita_corrigida/validacao_virita001_itabrita_corrigida_ictiofauna_20260622.xlsx`

## Decisões Confirmadas

### Unidade Taxonômica

O usuário confirmou `Rhamdiopsis microcephala` sem `cf.`. O pacote corrigido
usa esse nome nos resultados e no cadastro incremental.

### Espécies Novas No Banco

- `Salminus hilarii`
- `Hypostomus margaritifer`
- `Acestrorhynchus lacustris`
- `Hypostomus francisci`
- `Serrasalmus brandtii`
- `Pterygoplichthys etentaculatus`
- `Rhamdiopsis microcephala`

O cadastro incremental corrigido contém somente essas sete espécies.

### Espécies Já Existentes

- `Gymnotus carapo`
- `Knodus moenkhausii`
- `Hoplias malabaricus`
- `Pimelodus maculatus`
- `Hoplosternum littorale`
- `Astyanax lacustris`
- `Cichlasoma sanctifranciscense`
- `Rhamdia quelen`

Essas oito espécies foram removidas do cadastro incremental corrigido. Não
serão alteradas durante o cadastro das espécies novas.

### Endemismo

O usuário confirmou que as espécies abaixo não são endêmicas:

- `Hypostomus francisci`;
- `Cichlasoma sanctifranciscense`.

A aba `Endemismo_Especies` do cadastro incremental corrigido ficou sem
registros, preservando apenas o cabeçalho.

### BMWP

Os 15 registros usam `N.A.` em `bmwp_score`. Para Ictiofauna, o campo não é
aplicável; manter a decisão consciente e evitar tratá-la como erro ecológico.

## Observações De Migração

- Sete grupos possuem mais de uma linha para a mesma combinação de campanha,
  ponto, método, tipo e espécie.
- Não há duplicidades exatas.
- As linhas aparentam representar indivíduos ou lotes distintos.
- O migrador agregou as 31 linhas em 20 combinações únicas de campanha, ponto,
  método, tipo e espécie.
- A abundância foi preservada integralmente: 132 indivíduos no Excel e 132 no
  banco, sem divergências.
- O campo `PC_g` do migrador é consolidado por média. Para as análises de CPUEb,
  a biomassa foi reconstruída a partir da planilha validada pela fórmula
  `Numero_de_Individuos * PC_g` por linha, seguida de soma.

## Migração E Consolidação

Execução concluída em 2026-06-22:

- espécies novas cadastradas: 7;
- pontos: 7;
- esforços de Ictiofauna: 9;
- resultados agregados: 20;
- indivíduos: 132;
- espécies: 15;
- campanha: `ITA001_AH2526_202606`;
- linhas consolidadas do projeto: 20;
- `id_projeto`: 189.

Backup anterior à consolidação:

`public.backup_biota_consolidada_before_virita001_20260622t113408z`

O backup contém 22.318 linhas. A consolidação final contém 22.324 linhas.

## Análises E Produtos

Como o estudo terá somente duas campanhas, o usuário definiu `FERSAM001` como
referência analítica e visual.

Decisões:

- barras agrupadas por campanha para riqueza, abundância, CPUEn e CPUEb;
- painel único de Shannon e Pielou;
- paleta verde FERSAM001;
- layout Gold horizontal `15 x 10`, 600 dpi;
- tabela completa de distribuição suficiente para até duas campanhas;
- sínteses multicampanha adicionais ficam desativadas nesse recorte.

Resultados principais da Campanha 1:

- riqueza: 15 táxons, 4 ordens e 12 famílias;
- Siluriformes: 7 táxons (46,7%);
- Characiformes: 6 táxons (40,0%);
- riqueza máxima: 8 táxons em `Ictio_07`;
- abundância quantitativa: 57 indivíduos em `Ictio_07` e 5 em `Ictio_06`;
- CPUEn: 47,50 e 4,17 ind/100 m², respectivamente;
- CPUEb: 3.854,17 e 971,67 g/100 m², respectivamente;
- maior CPUEn e CPUEb por espécie: `Acestrorhynchus lacustris`;
- similaridade de Bray-Curtis entre os pontos quantitativos: 6,45%;
- riqueza observada final: 10;
- Jackknife 1: 14.

Pasta final:

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Resultados/Ictiofauna/Campanha_1`

Produtos finais:

- 14 planilhas XLSX;
- 13 figuras PNG;
- 1 HTML técnico autônomo;
- 2 JSONs de evidência/validação;
- 1 manifesto de entrega com hashes.

HTML:

`relatorio_tecnico_ictiofauna_campanha_1.html`

Validações:

- auditoria oficial de fauna: `OK`;
- erros: 0;
- avisos: 0;
- validação textual: `OK`;
- erros textuais: 0;
- avisos textuais: 0.

## Lastro

- recipe:
  `configs/projects/virita001_itabrita_ictiofauna.json`
- cliente:
  `configs/clients/virita001.json`
- gerador HTML:
  `scripts/projects/virita001/generate_ictio_html_report.py`
- auditoria:
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`

## Próximas Etapas

1. Migrar a segunda campanha quando estiver disponível.
2. Incluir a nova campanha na recipe.
3. Regenerar a bateria completa para comparação direta entre campanhas.
4. Atualizar o HTML técnico e a síntese temporal.
