# GEOARC001 - Ictiofauna - 18 campanhas

## Controle

- projeto: `GEOARC001__monitoramento_arcelor`
- grupo: Ictiofauna
- operacao: Migracao inicial de 18 campanhas
- estado atual: `configuring_analysis`
- aberta em: 2026-06-23
- atualizada em: 2026-06-23
- proxima acao: configurar template multicampanha/serie longa, paleta, pasta final e produtos para Gate C

## Caminhos

- dados:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx.xlsx`
- dados com taxonomia Gate B:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx`
- cadastro de especies informado:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326.xlsx`
- cadastro de especies corrigido para Gate B:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326_CORRIGIDA_GATE_B_R02.xlsx`
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Resultados`
- dossie: `docs/projects/GEOARC001_ARCELOR_ICTIOFAUNA.md`
- recipe: `configs/projects/geoarc001_arcelor_ictiofauna.json`
- lastro: `outputs/_project_scripts/GEOARC001__monitoramento_arcelor`

## Identidade De Abertura

- codigo informado pelo usuario: `GEOARC001`
- nome na aba `Capa_Projeto`: Monitoramento Arcelor
- cliente na aba `Capa_Projeto`: Geomil Servicos de Mineracao Ltda.
- CNPJ na aba `Capa_Projeto`: `25.184.466/0001-15`
- responsavel tecnico na aba `Capa_Projeto`: Felipe Talin Normando
- data de inicio na aba `Capa_Projeto`: 2024-01-01
- data final prevista na aba `Capa_Projeto`: 2027-07-01
- status no registry local: cadastrado como `active` em `docs/registry/project_registry.json`
- id Supabase: `190`
- dossie local: `docs/projects/GEOARC001_ARCELOR_ICTIOFAUNA.md`
- recipe local: `configs/projects/geoarc001_arcelor_ictiofauna.json`
- lastro local: nao encontrado

## Contexto Consultado

- Central de Controle: `docs/control_center/README.md`
- Workflow oficial: `docs/control_center/WORKFLOW.md`
- Operacoes ativas: `docs/control_center/ACTIVE_OPERATIONS.md`
- Registry: `docs/registry/project_registry.json`
- Projetos: `docs/control_center/PROJECTS.md`
- Dossie/recipe/lastro: nao existentes localmente para `GEOARC001` no momento da abertura

## Inventario De Entrada

| Item | Resultado |
| --- | --- |
| Pasta de entrada | Existe |
| Arquivos encontrados | 1 XLSX |
| Planilha principal | `Projeto_GEOARC001_ictio_260326xlsx.xlsx` |
| Tamanho | 54.295 bytes |
| Ultima modificacao | 2026-06-23 14:40:24 |
| Abas | `Capa_Projeto`, `Pontos_e_Campanhas`, `Metadados_Esforco`, `Resultados_Ictiofauna` |
| Linhas em `Pontos_e_Campanhas` | 198 dados + cabecalho |
| Linhas em `Metadados_Esforco` | 198 dados + cabecalho |
| Linhas em `Resultados_Ictiofauna` | 301 dados + cabecalho |
| Pasta de saida | Existe; contem apenas `desktop.ini` oculto no momento da abertura |

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Usuario informou codigo, grupo, 18 campanhas, planilha de entrada e pasta de saida. Planilha inventariada. |
| Validacao | concluida sem bloqueios | Revalidacao `20260623_r03`: 0 bloqueios, 4 avisos e `pode_prosseguir=true`. |
| Gate A - dados | aprovado | Usuario aprovou seguir em 2026-06-23 apos validacao `20260623_r03` sem bloqueios. |
| Cadastro de especies | concluido | Cadastro complementar recebido, corrigido em copia e usado para cadastrar 4 especies novas no banco. |
| Auditoria de atributos | concluida e aceita no Gate B | Todas as 19 especies ja existentes possuem campos obrigatorios/ecologicos vazios segundo auditoria local; criterio aceito com aprovacao do usuario. |
| Gate B - especies | aprovado | Usuario disse "aprovado" em 2026-06-23; projeto `id_projeto=190` e 4 especies novas cadastrados; validacao pos-cadastro sem bloqueios. |
| Migracao | concluida | Migrador oficial executado; 198 pontos, 198 esforcos, 150 resultados agregados, 707 individuos e 23 especies. |
| Consolidacao | concluida | Backup completo criado; script oficial `processar_dados.py` executado; 150 linhas consolidadas para GEOARC001/Ictiofauna. |
| Configuracao das analises | em andamento | Definir template multicampanha/serie longa, paleta, pasta final e produtos para Gate C. |
| Gate C - analises | pendente | Confirmar template, paleta, pasta de saida e produtos. |
| Geracao dos produtos | pendente | Depende do Gate C. |
| Revisao tecnica | pendente | Depende da geracao. |
| Revisao de layout | pendente | Depende da revisao tecnica. |
| Fechamento | pendente | Depende dos gates, auditorias, produtos e atualizacao do dossie. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario disse "siga" em 2026-06-23 apos apresentacao da validacao `20260623_r03` sem bloqueios. |
| B - especies | `approved` | Usuario disse "aprovado" em 2026-06-23; projeto e especies cadastrados; validacao pos-cadastro `20260623_gateb_post_cadastro` com 0 bloqueios e 2 avisos. |
| C - analises | `pending` | Aguardando configuracao e aprovacao do pacote analitico. |

## Validacao Dos Dados

- bloqueios: 0 na revalidacao `20260623_r03`; eram 2 na rodada inicial, 1 na `20260623_r01` e 0 na `20260623_r02`
- avisos: 4
- ajustes aplicados: nenhum; original preservado
- arquivos corrigidos: nenhum
- relatorio:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_r02.md`
- Excel detalhado:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_r02.xlsx`
- JSON:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_r02.json`
- veredito: dados sem bloqueios; pode seguir para etapas posteriores somente apos Gate B

### Achados Do Gate A

- Campanhas: quantidade esperada conferida, 18 campanhas.
- Melhora da revalidacao: campos obrigatorios ausentes foram resolvidos; nao ha mais linhas com `Campanha` vazia.
- Bloqueio restante: nenhum na `20260623_r03`.
- Aviso de divergencia de esforco: resolvido na `20260623_r03`.
- Aviso: 154 resultados sao duplicatas exatas.
- Aviso: 51 grupos campanha+ponto+metodo+tipo+especie possuem multiplas linhas e seriam agregados pelo migrador.
- Aviso: validadores oficiais e banco foram pulados nesta rodada com `--skip-db`; a rodada final deve executar a validacao completa.

### Revalidacao 20260623_r01

- planilha reavaliada: modificada em 2026-06-23 15:02:20, tamanho 57.686 bytes;
- relatorio inicial: 2 bloqueios, 5 avisos, nao prosseguir;
- relatorio revalidado: 1 bloqueio, 5 avisos, nao prosseguir;
- linhas sem `Campanha`: resolvidas;
- linhas sem esforco correspondente: reduziram de 148 para 48;
- linhas com divergencia de esforco: aumentaram de 5 para 14;
- duplicatas exatas: reduziram de 167 para 152;
- grupos que serao agregados: reduziram de 64 para 51.

Resumo do bloqueio restante por campanha/ponto:

| Campanha | Ponto | Linhas |
| --- | --- | ---: |
| `C009-2023-12-CH` | `IC-ARC-06` | 3 |
| `C012-2024-12-SC` | `IC-ARC-05` | 1 |
| `C012-2024-12-SC` | `IC-ARC-06` | 5 |
| `C012-2024-12-SC` | `IC-ARC-10` | 1 |
| `C012-2024-12-SC` | `IC-ARC-14` | 6 |
| `C013-2025-03-SC` | `IC-ARC-05` | 1 |
| `C013-2025-03-SC` | `IC-ARC-06` | 3 |
| `C013-2025-03-SC` | `IC-ARC-07` | 1 |
| `C013-2025-03-SC` | `IC-ARC-08` | 1 |
| `C013-2025-03-SC` | `IC-ARC-10` | 1 |
| `C013-2025-03-SC` | `IC-ARC-14` | 8 |
| `C016-2025-12-SC` | `IC-ARC-05` | 1 |
| `C016-2025-12-SC` | `IC-ARC-06` | 2 |
| `C016-2025-12-SC` | `IC-ARC-10` | 1 |
| `C017-2026-04-SC` | `IC-ARC-05` | 3 |
| `C017-2026-04-SC` | `IC-ARC-06` | 4 |
| `C017-2026-04-SC` | `IC-ARC-07` | 1 |
| `C017-2026-04-SC` | `IC-ARC-08` | 4 |
| `C017-2026-04-SC` | `IC-ARC-10` | 1 |

### Revalidacao 20260623_r02

- planilha reavaliada: modificada em 2026-06-23 15:18:36, tamanho 57.706 bytes;
- relatorio revalidado: 0 bloqueios, 5 avisos, `pode_prosseguir=true`;
- linhas sem esforco correspondente: reduziram de 48 para 0;
- linhas com divergencia de esforco: aumentaram de 14 para 20;
- duplicatas exatas: mantidas em 152;
- grupos que serao agregados: mantidos em 51.

### Revalidacao 20260623_r03

- planilha reavaliada: modificada em 2026-06-23 15:25:12, tamanho 57.818 bytes;
- relatorio revalidado: 0 bloqueios, 4 avisos, `pode_prosseguir=true`;
- linhas sem esforco correspondente: 0;
- linhas com divergencia de esforco: reduziram de 20 para 0;
- duplicatas exatas: passaram de 152 para 154;
- grupos que serao agregados: mantidos em 51.

### Revalidacao 20260623_gateb

- planilha revalidada:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B.xlsx`;
- relatorio revalidado: 0 bloqueios, 4 avisos, `pode_prosseguir=true`;
- de/para aplicado:
  `outputs/validacoes/geoarc001_arcelor/de_para_taxonomico_geoarc001_ictiofauna_20260623.xlsx`;
- linhas alteradas:
  `outputs/validacoes/geoarc001_arcelor/ajustes_taxonomicos_geoarc001_ictiofauna_20260623.xlsx`;
- original preservado.

### Revalidacao 20260623_gateb_r02

- planilha revalidada:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx`;
- relatorio revalidado: 0 bloqueios, 4 avisos, `pode_prosseguir=true`;
- correcao adicional: `Crenicihla lepidota` foi corrigida para `Crenicichla lepidota`;
- de/para aplicado:
  `outputs/validacoes/geoarc001_arcelor/de_para_taxonomico_geoarc001_ictiofauna_20260623_r02.xlsx`;
- linhas alteradas:
  `outputs/validacoes/geoarc001_arcelor/ajustes_taxonomicos_geoarc001_ictiofauna_20260623_r02.xlsx`;
- original preservado.

### Revalidacao 20260623_gateb_species_r02

- planilha de resultados:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx`;
- cadastro de especies corrigido:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326_CORRIGIDA_GATE_B_R02.xlsx`;
- relatorio integrado: 0 bloqueios, 4 avisos, `pode_prosseguir=true`;
- especies no cadastro complementar: 4 linhas, 4 validas, 4 novas no banco;
- avisos restantes: projeto `GEOARC001` ainda nao existe no banco, 154 duplicatas exatas, 51 grupos agregaveis e status de projeto ausente no banco;
- relatorio:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_species_r02.md`;
- Excel detalhado:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_species_r02.xlsx`;
- JSON:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_species_r02.json`;
- ajustes do cadastro:
  `outputs/validacoes/geoarc001_arcelor/ajustes_cadastro_especies_geoarc001_ictiofauna_20260623_gateb_r02.json`;
- original preservado.

### Revalidacao 20260623_gateb_post_cadastro

- projeto cadastrado no banco: `id_projeto=190`;
- especies novas cadastradas no banco:
  `Hyphessobrycon santae` (`id_especie=5452`),
  `Crenicichla lepidota` (`id_especie=5453`),
  `Australoheros facetus` (`id_especie=5454`) e
  `Piabina argentea` (`id_especie=5455`);
- relatorio integrado pos-cadastro: 0 bloqueios, 2 avisos, `pode_prosseguir=true`;
- avisos restantes: 154 duplicatas exatas e 51 grupos campanha+ponto+metodo+tipo+especie agregaveis pelo migrador;
- relatorio:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_post_cadastro.md`;
- Excel detalhado:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_post_cadastro.xlsx`;
- JSON:
  `outputs/validacoes/geoarc001_arcelor/validacao_geoarc001_arcelor_ictiofauna_20260623_gateb_post_cadastro.json`;
- lastro do cadastro do projeto:
  `outputs/validacoes/geoarc001_arcelor/cadastro_banco_geoarc001_projeto_20260623_gateb.json`;
- lastro do cadastro das especies:
  `outputs/validacoes/geoarc001_arcelor/cadastro_banco_geoarc001_especies_20260623_gateb.json`.

## Cadastro E Auditoria De Especies

- especies nos resultados: 23
- especies existentes no banco antes do cadastro: 19
- especies novas no banco apos de/para: 4
- especies existentes no banco apos cadastro: 23
- especies novas:
  - `Australoheros facetus`
  - `Crenicichla lepidota`
  - `Hyphessobrycon santae`
  - `Piabina argentea`
- cadastro complementar informado pelo usuario:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326.xlsx`
- cadastro complementar corrigido:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_Cadastro_especie_GEOARC001_ictio_260326_CORRIGIDA_GATE_B_R02.xlsx`
- validacao integrada do cadastro corrigido:
  0 bloqueios, 4 avisos, `pode_prosseguir=true`; as 4 especies novas estao presentes e validas na planilha de cadastro.
- atributos obrigatorios: 19 especies existentes possuem ao menos um campo vazio na auditoria local
- decisoes taxonomicas do usuario:
  - `Australoheros oblongus` deve ser tratado como `Australoheros facetus`;
  - `Crenicihla lepidota` deve ser corrigida para `Crenicichla lepidota`;
  - `Hyphessobrycon santae` e similar a `Hyphessobrycon cf. santae`, mas deve permanecer sem `cf.`;
  - `Piabina argentea` e nova.
- campos incertos: resolvidos quanto a unidade taxonomica pelo usuario; criterios de campos vazios/avisos remanescentes aceitos no Gate B
- ajustes no cadastro complementar: `Crenicihla lepidota` corrigida para `Crenicichla lepidota`; `Genero` corrigido para `Crenicichla`; `bmwp_score` com `N.A.` removido; espacos invisiveis removidos em `Ordem` e `Familia`.
- ajustes no banco: projeto `GEOARC001` cadastrado como `id_projeto=190`; 4 especies novas cadastradas em `public.especies`
- observacao: a planilha de cadastro complementar foi validada e processada somente para as 4 especies novas
- auditoria:
  `outputs/validacoes/geoarc001_arcelor/auditoria_especies_geoarc001_ictiofauna_20260623_gateb_r02.md`
- Excel detalhado:
  `outputs/validacoes/geoarc001_arcelor/auditoria_especies_geoarc001_ictiofauna_20260623_gateb_r02.xlsx`
- JSON:
  `outputs/validacoes/geoarc001_arcelor/auditoria_especies_geoarc001_ictiofauna_20260623_gateb_r02.json`

### Achados Do Gate B

- `GEOARC001` foi cadastrado em `public.projetos` como `id_projeto=190`.
- 4 especies novas foram cadastradas antes da migracao: `Australoheros facetus`, `Crenicichla lepidota`, `Hyphessobrycon santae` e `Piabina argentea`.
- A planilha complementar corrigida foi validada sem bloqueios e processada no cadastro mestre.
- Todas as 19 especies ja existentes possuem campos vazios em atributos como ameaca, endemismo, migratorio, sensibilidade, raridade, distribuicao e/ou atributos ecologicos; o criterio foi aceito no Gate B.
- Gate B aprovado pelo usuario em 2026-06-23 com a mensagem "aprovado".
- Nenhuma migracao foi executada.

## Migracao E Consolidacao

- migracao executada com:
  `G:/Meu Drive/Opyta/Opyta_Data/scripts/migrar_ictiofauna.py`
- planilha migrada:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Planilhas de migracao/Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx`
- IDs principais:
  - projeto: `id_projeto=190`
  - especies novas: `Hyphessobrycon santae` (`5452`), `Crenicichla lepidota` (`5453`), `Australoheros facetus` (`5454`), `Piabina argentea` (`5455`)
- totais da fonte:
  - pontos campanha+ponto: 198
  - esforcos Ictiofauna: 198
  - linhas de resultados no Excel: 301
  - resultados agregados esperados: 150
  - individuos: 707
  - especies: 23
- totais no banco apos migracao:
  - pontos campanha+ponto: 198
  - esforcos Ictiofauna: 198
  - resultados agregados: 150
  - individuos: 707
  - especies: 23
- divergencias da migracao: nenhuma nos checks de pontos, esforcos, resultados agregados, abundancia e especies
- auditoria da migracao:
  `outputs/_migration/geoarc001_ictiofauna/migration_audit.md`
- JSON da migracao:
  `outputs/_migration/geoarc001_ictiofauna/migration_audit.json`
- backup antes da consolidacao oficial:
  `public.backup_biota_consolidada_before_geoarc001_20260623t191207z`
- linhas no backup completo: 22.324
- consolidacao executada com:
  `G:/Meu Drive/Opyta/Opyta_Data/scripts/processar_dados.py`
- totais globais consolidados: 22.324 antes, 22.474 depois
- totais consolidados para `GEOARC001`/`Ictiofauna`:
  - linhas: 150
  - campanhas: 18
  - pontos com resultado: 9
  - especies: 23
  - individuos: 707
- divergencias da consolidacao: nenhuma nos checks de linhas, abundancia, campanhas, pontos com resultado, especies e delta global
- auditoria da consolidacao:
  `outputs/_migration/geoarc001_ictiofauna/consolidation_audit.md`
- JSON da consolidacao:
  `outputs/_migration/geoarc001_ictiofauna/consolidation_audit.json`
- observacao tecnica: o script oficial usa `PC_g` como campo `biomassa` em ictiofauna; para CPUEb exata, manter a planilha validada como fonte linha-a-linha nas analises.

## Configuracao Das Analises

- numero de campanhas: 18 informado pelo usuario; confirmar na validacao
- template: a definir apos consolidacao; referencia provavel: padrao multicampanha/series longas
- paleta: a definir no Gate C
- pasta de saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Resultados`
- produtos: a confirmar no Gate C

## Pendencias

- confirmar se as 154 duplicatas exatas representam individuos/lotes distintos ou se devem ser deduplicadas;
- configurar template multicampanha/serie longa;
- aprovar Gate C antes da geracao de produtos.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| R05 - coordenadas Geoambiental | data | R3 | awaiting_revision_approval | docs/control_center/reviews/GEOARC001_ICTIOFAUNA_COORDENADAS_GEOAMBIENTAL_REV_R05.md |

## Fechamento E Aprendizados

- validadores: pendente
- manifesto: pendente
- patterns: pendente
- portfolio: pendente
- backlog: pendente
