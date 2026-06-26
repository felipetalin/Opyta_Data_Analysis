# VIRITA001 - Diagnóstico da ictiofauna do Projeto Itabrita

Status: `campaign_1_R01_R02_revised_awaiting_gate_r`

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
- estado operacional: `awaiting_revision_approval`
- registro:
  `docs/control_center/operations/VIRITA001_ICTIOFAUNA_CAMPANHA_1.md`
- proxima acao: aprovar as revisoes R01 e R02 no Gate R
- Gate A — dados: aprovado
- Gate B — especies: aprovado
- Gate C — analises: aprovado
- Gate R — revisao: aguardando aprovacao da R01 de dados e da R02 de
  biometria/pacote

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
- campanha: `C001-2026-06-SC`
- período amostral: 17 e 18 de junho de 2026
- pontos: `Ictio_01` a `Ictio_07`
- linhas de esforço: 7
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

- Seis grupos possuem mais de uma linha para a mesma combinação de campanha,
  ponto, método, tipo e espécie.
- Não há duplicidades exatas.
- As linhas aparentam representar indivíduos ou lotes distintos.
- O migrador agregou as 31 linhas em 19 combinações únicas de campanha, ponto,
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

Revisão R01 concluída tecnicamente em 2026-06-25:

- campanha corrigida: `C001-2026-06-SC`;
- planilha revisada validada sem bloqueios e com 1 aviso de agregação esperada;
- fatia antiga `ITA001_AH2526_202606` removida de forma escopada para
  `id_projeto=189`;
- pontos: 7;
- esforços de Ictiofauna: 7;
- resultados agregados: 19;
- indivíduos: 132;
- espécies: 15;
- linhas consolidadas do projeto: 19.

Backups R01:

- snapshot local da entrega anterior:
  `outputs/_snapshots/VIRITA001_R01_before_20260625/Campanha_1`;
- `public.backup_virita001_r01_pontos_20260625t175139z` (7 linhas);
- `public.backup_virita001_r01_esforcos_20260625t175139z` (9 linhas);
- `public.backup_virita001_r01_resictio_20260625t175139z` (20 linhas);
- `public.backup_virita001_r01_consol_20260625t175139z` (20 linhas);
- `public.backup_biota_before_vr01_20260625t175139z` (22.474 linhas).

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
- abundância quantitativa: 57 indivíduos em `Ictio_07` e 55 em `Ictio_05`;
- CPUEn máxima: 50,00 ind/100 m² em `Ictio_05`;
- CPUEb máxima: 3.854,17 g/100 m² em `Ictio_07`;
- maior CPUEn e CPUEb por espécie: `Acestrorhynchus lacustris`;
- tabela biometrica: 15 especies; maior biomassa em
  `Acestrorhynchus lacustris` (2.212,0 g); `Astyanax lacustris` calculada da
  fonte validada com N=9, CP medio 10,22 cm e biomassa 413,0 g;
- maior similaridade de Bray-Curtis: 21,05% entre `Ictio_02` e `Ictio_03`;
- riqueza observada final: 15;
- Jackknife 1: 25,29.

Pasta final:

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Resultados/Ictiofauna/Campanha_1`

Produtos finais:

- 17 planilhas XLSX;
- 15 figuras PNG;
- 1 HTML técnico autônomo;
- 2 JSONs de evidência/validação;
- 1 manifesto de entrega com hashes.

Produto R02:

- `13_tabela_biometria_biomassa_ictiofauna.xlsx`, com aba de entrega e aba
  `Dados` para rastreabilidade plana.

HTML:

`relatorio_tecnico_ictiofauna_campanha_1.html`

Validações:

- auditoria oficial de fauna: `OK`;
- erros: 0;
- avisos: 0;
- validação textual: `OK`;
- erros textuais: 0;
- avisos textuais: 0.
- revisao R01: validacao de planilha sem bloqueios; auditoria oficial de
  produtos `OK`.
- revisao R02: tabela biometrica adicionada; validacao textual `OK`; auditoria
  oficial `OK`; manifesto revisado com 35 itens declarados.

## Lastro

- recipe:
  `configs/projects/virita001_itabrita_ictiofauna.json`
- cliente:
  `configs/clients/virita001.json`
- gerador HTML:
  `scripts/projects/virita001/generate_ictio_html_report.py`
- auditoria:
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`
- execucao R01:
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita/ictiofauna/20260625T181107Z_execution_metadata.json`
- execucao R02:
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita/ictiofauna/20260626T122432Z_execution_metadata.json`

## Próximas Etapas

1. Aprovar as revisoes R01 e R02 no Gate R.
2. Migrar a segunda campanha quando estiver disponível.
3. Incluir a nova campanha na recipe.
4. Regenerar a bateria completa para comparação direta entre campanhas.
