# BRAAVG002 - Ictiofauna - Migracao ate junho/2026

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- grupo: Ictiofauna
- operacao: Migracao da serie AVG ate a campanha `47a-Jun-26`
- estado atual: `completed`
- aberta em: 2026-06-30
- atualizada em: 2026-07-01
- proxima acao: operacao encerrada; ajustes futuros devem seguir fluxo de revisao quando solicitados

## Caminhos

- dados originais:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Migracao de dados/2026/Ictiofauna/projeto_ictio_real - AVG 260625.xlsx`
- dados corrigidos para Gate A:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Migracao de dados/2026/Ictiofauna/projeto_ictio_real - AVG 260625_GATEA_R01.xlsx`
- cadastro de especies: banco `public.especies`; cadastro separado nao informado
- saida informada:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/junho`
- dossie:
  `docs/AVG_ICTIOFAUNA_2026.md`
- recipe:
  `configs/clients/braavg002.json`; sem recipe em `configs/projects/` no registry
- lastro:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- validacoes:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026`

## Identidade De Abertura

- codigo informado pelo usuario: AVG / BRAAVG002
- nome na aba `Capa_Projeto`: Monitoramento de ictio e bentos - Brumado - AVG
- cliente na aba `Capa_Projeto`: Brandt Meio Ambiente Ltda.
- CNPJ na aba `Capa_Projeto`: `71061162/0001-88`
- responsavel tecnico na aba `Capa_Projeto`: Felipe Talin Normando
- data de inicio na aba `Capa_Projeto`: 2025-07-01
- data final prevista na aba `Capa_Projeto`: 2026-07-01
- status no registry local: `reference`
- id Supabase: `9`

## Contexto Consultado

- Central de Controle: `docs/control_center/README.md`
- Workflow oficial: `docs/control_center/WORKFLOW.md`
- Operacoes ativas: `docs/control_center/ACTIVE_OPERATIONS.md`
- Registry: `docs/registry/project_registry.json`
- Projetos: `docs/control_center/PROJECTS.md`
- Dossie AVG Ictiofauna: `docs/AVG_ICTIOFAUNA_2026.md`
- Tema/recipe cliente: `configs/clients/braavg002.json`
- Scripts AVG: `scripts/projects/avg`
- Migrador oficial: `G:/Meu Drive/Opyta/Opyta_Data/scripts/migrar_ictiofauna.py`
- Consolidador oficial: `G:/Meu Drive/Opyta/Opyta_Data/scripts/processar_dados.py`

## Inventario De Entrada

| Item | Resultado |
| --- | --- |
| Pasta de entrada | Existe |
| Arquivos encontrados | 1 XLSX principal |
| Planilha principal | `projeto_ictio_real - AVG 260625.xlsx` |
| Tamanho | 144.878 bytes |
| Ultima modificacao | 2026-06-30 17:15 |
| Abas | `Capa_Projeto`, `Pontos_e_Campanhas`, `Resultados_Ictiofauna`, `Metadados_Esforco` |
| Linhas em `Pontos_e_Campanhas` | 611 dados + cabecalho |
| Linhas em `Metadados_Esforco` | 611 dados + cabecalho |
| Linhas em `Resultados_Ictiofauna` | 1.360 dados + cabecalho |
| Campanhas | 47, de `1a-Ago-22` a `47a-Jun-26` |
| Pontos unicos | 13 |
| Especies em resultados | 13 |
| Pasta de saida | Existe; sem arquivos visiveis no momento da abertura |

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto, grupo, entrada e saida informados pelo usuario; registry/dossie/scripts consultados. |
| Validacao | concluida sem bloqueios na copia Gate A R01 | Revalidacao `20260630_gatea_r01`: 0 bloqueios, 3 avisos e `pode_prosseguir=true`. |
| Gate A - dados | aprovado | Usuario disse "aprovado siga" em 2026-06-30; aprovada a copia `GATEA_R01`, uso de `Metadados_Esforco` como fonte de esforco e manutencao das duplicatas como individuos/lotes. |
| Cadastro de especies | concluido sem novas especies | As 13 especies dos resultados ja existem em `public.especies`; nenhum cadastro novo necessario. |
| Auditoria de atributos | concluida com ressalvas | 0 bloqueios de ID/taxonomia basica; 13 especies com atributos ecologicos/ameaca vazios. |
| Gate B - especies | aprovado | Usuario disse "aprovado" em 2026-06-30; aceitas as ressalvas de atributos ecologicos/ameaca vazios. |
| Migracao | concluida | Migrador oficial executado; fonte e banco conferem em pontos, esforcos, resultados agregados, especies e individuos. |
| Consolidacao | concluida | Backup da fatia antiga criado; 519 linhas consolidadas e auditadas sem divergencias. |
| Configuracao das analises | preparada | Runner parcial de Ictiofauna AVG ajustado para `47a-Jun-26`; tema `braavg002` conferido com fontes grandes e preview tipografico em `outputs/_checks/braavg002_ictio_font_preview`. |
| Gate C - analises | aprovado | Usuario disse "Aprovado" em 2026-07-01 para campanha `47a-Jun-26`, template parcial AVG, tema `braavg002`, perfil tipografico e saida de junho. |
| Geracao dos produtos | concluida com correcao | 31 arquivos oficiais gerados em `Resultados ictio/2026/junho`: 15 PNG e 16 XLSX. Uma falha intermediaria truncou `03_grafico_abundancia_por_ponto_ictiofauna.png`; o salvamento foi reforcado via arquivo temporario local e os produtos por ponto foram regenerados. |
| Revisao tecnica | concluida | Todos os PNGs abriram via PIL, todos os XLSX abriram via openpyxl, nenhum PNG pequeno/corrompido permaneceu; planilhas por ponto somam 45 individuos, 13 pontos e campanha unica `47a-Jun-26`. |
| Revisao de layout | aprovada | Amostras visuais revisadas: abundancia por ponto, CPUEn por ponto e riqueza por ordem; fontes grandes e sem sobreposicao relevante. Usuario aprovou os produtos em 2026-07-01. |
| Fechamento | concluido | Usuario disse "aprovado... se surgir alguma coisa de ajuste ajustando na sequencia" em 2026-07-01; operacao encerrada e ajustes futuros devem seguir fluxo de revisao. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario disse "aprovado siga" em 2026-06-30 apos apresentacao da validacao `20260630_gatea_r01` e dos tres criterios de avanco. |
| B - especies | `approved` | Usuario disse "aprovado" em 2026-06-30; auditoria `20260630_gateb` com 13 especies existentes, 0 bloqueios de taxonomia basica/ID e 13 especies com atributos ecologicos/ameaca vazios aceitos como ressalva. |
| C - analises | `approved` | Usuario disse "Aprovado" em 2026-07-01 para campanha `47a-Jun-26`, template parcial AVG, tema `braavg002`, perfil tipografico e saida de junho. |

## Validacao Dos Dados

- bloqueios iniciais: 1 falso positivo de formato de campanha ordinal no wrapper complementar; datas conferidas manualmente e validador atualizado para reconhecer `1a-Ago-22`/`47a-Jun-26`.
- ajuste aplicado em copia: `45a-Abri-26` corrigido para `45a-Abr-26` em 13 linhas de `Pontos_e_Campanhas`; original preservado.
- bloqueios na revalidacao `20260630_gatea_r01`: 0.
- avisos na revalidacao `20260630_gatea_r01`: 3.
- relatorio:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026/validacao_braavg002_ictiofauna_junho_2026_ictiofauna_20260630_gatea_r01.md`
- Excel detalhado:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026/validacao_braavg002_ictiofauna_junho_2026_ictiofauna_20260630_gatea_r01.xlsx`
- JSON:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026/validacao_braavg002_ictiofauna_junho_2026_ictiofauna_20260630_gatea_r01.json`
- veredito: Gate A aprovado; migracao e consolidacao executadas apos Gate B.

### Achados Do Gate A

- 47 campanhas, 13 pontos, 611 linhas de pontos/esforcos, 1.360 linhas de resultados e 13 especies.
- As campanhas coincidem exatamente entre as abas na copia `GATEA_R01`.
- Cliente e projeto ja existem no banco.
- Aviso: 207 resultados possuem `Esforco_Amostral` diferente de `Metadados_Esforco.Esforco`; banco historico de AVG usa os valores de `Metadados_Esforco`.
- Aviso: 921 resultados sao duplicatas exatas; podem representar individuos/lotes distintos.
- Aviso: 254 grupos campanha+ponto+metodo+tipo+especie serao agregados pelo migrador, com abundancia por soma e biometria por media.

## Cadastro E Auditoria De Especies

- especies nos resultados: 13.
- especies novas: 0.
- especies ausentes no banco: 0.
- especies existentes no banco: 13.
- bloqueios de ID/taxonomia basica: 0.
- atributos obrigatorios/ecologicos: 13 especies possuem campos vazios em atributos de ameaca/ecologia, como status de ameaca, CITES, endemismo, habito/guilda alimentar, migratorio, sensibilidade, raridade e distribuicao.
- campos incertos: atributos ecologicos vazios aceitos como ressalva no Gate B.
- ajustes manuais: nenhum aplicado.
- auditoria:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026/auditoria_especies_braavg002_ictiofauna_20260630_gateb.md`
- Excel detalhado:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026/auditoria_especies_braavg002_ictiofauna_20260630_gateb.xlsx`
- JSON:
  `outputs/validacoes/braavg002_ictiofauna_junho_2026/auditoria_especies_braavg002_ictiofauna_20260630_gateb.json`

### Achados Do Gate B

- Todas as especies possuem ID no banco e taxonomia basica preenchida.
- Nenhuma especie nova precisa ser cadastrada antes da migracao.
- As lacunas de atributos nao bloqueiam a carga bruta/migracao, mas precisam ser aceitas como ressalva se a rodada seguir sem completar o cadastro ecologico.

## Migracao E Consolidacao

- IDs: projeto Supabase `id_projeto=9`; demais IDs pendentes.
- totais da fonte: 611 pontos/esforcos, 1.360 linhas de resultados, 13 especies.
- totais no banco apos migracao:
  - pontos: 611
  - esforcos: 611
  - resultados agregados: 519
  - individuos: 1.486
  - especies: 13
- divergencias da migracao: nenhuma nos checks de pontos, esforcos, resultados agregados, abundancia e especies.
- auditoria da migracao:
  `outputs/_migration/braavg002_ictiofauna_junho_2026/migration_audit.md`
- JSON da migracao:
  `outputs/_migration/braavg002_ictiofauna_junho_2026/migration_audit.json`
- backup antes da consolidacao:
  `public.backup_biota_consolidada_braavg002_ictio_20260630t203650z`
- linhas preservadas no backup: 513
- consolidacao executada por fatia, sem truncate global, recarregando apenas `BRAAVG002`/`Ictiofauna` em `public.biota_analise_consolidada`
- linhas removidas da fatia antiga: 513
- linhas inseridas na fatia nova: 519
- totais consolidados:
  - linhas: 519
  - campanhas: 47
  - pontos: 13
  - especies: 13
  - individuos: 1.486
- divergencias da consolidacao: nenhuma nos checks de linhas, abundancia, campanhas, pontos e especies.
- auditoria da consolidacao:
  `outputs/_migration/braavg002_ictiofauna_junho_2026/consolidation_audit.md`
- JSON da consolidacao:
  `outputs/_migration/braavg002_ictiofauna_junho_2026/consolidation_audit.json`

## Configuracao Das Analises

- numero de campanhas: 47.
- campanha alvo: `47a-Jun-26`, pasta `junho`.
- template: runner parcial AVG Ictiofauna em `scripts/projects/avg/run_ictio_avg_abril_maio.py`.
- paleta: `configs/clients/braavg002.json`.
- perfil tipografico validado em teste:
  - `font_size_base=21`
  - `label_size=20`
  - `legend_size=18`
  - `title_size=22`
  - `campaign_label_size=18`
  - `point_label_size=21`
  - `control_area_label_size=22`
  - `figsize_standard=[16, 10]`
  - `dpi=600`
- checagens:
  - `python -m py_compile scripts/projects/avg/run_ictio_avg_abril_maio.py`
  - preview visual de layout em `outputs/_checks/braavg002_ictio_font_preview/preview_riqueza_por_ponto_tema_braavg002.png`
- pasta de saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/junho`
- produtos previstos: planilhas e graficos parciais gerados pelo pipeline de Ictiofauna AVG, incluindo riqueza, abundancia, CPUE, diversidade, similaridade e suficiencia amostral.

## Geracao Dos Produtos

- Gate C aprovado pelo usuario em 2026-07-01 com a mensagem "Aprovado".
- comando principal:
  `python scripts/projects/avg/run_ictio_avg_abril_maio.py --campaign junho`
- saida oficial:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/junho`
- arquivos oficiais gerados: 31, sendo 15 PNG e 16 XLSX.
- conteudo conferido:
  - `02_df_riqueza_por_ponto_ictiofauna.xlsx`: 13 pontos; soma de riqueza por ponto = 6.
  - `03_df_abundancia_por_ponto_ictiofauna.xlsx`: 13 pontos; abundancia total = 45 individuos.
  - `06_df_cpue_por_ponto_ictiofauna.xlsx`: 13 pontos; abundancia total = 45 individuos; biomassa total = 5,8.
  - campanha unica nas planilhas por ponto: `47a-Jun-26`.
- revisao de integridade:
  - 15 PNGs verificados com abertura real via PIL.
  - 16 XLSX verificados com abertura real via openpyxl.
  - nenhum PNG pequeno/corrompido apos a regeneracao.
- correcao operacional aplicada:
  - runner passou a aceitar `--campaign junho`, evitando reprocessar abril/maio.
  - Matplotlib passou a usar backend `Agg`.
  - PNGs finais por ponto passaram a ser salvos primeiro em diretorio temporario local e depois copiados para o Google Drive.
  - produtos por ponto passaram a ser recalculados diretamente do dataframe consolidado em memoria, evitando depender de planilhas de saida ja sobrescritas.

## Pendencias

- Gate A aprovado: usar a copia `GATEA_R01`, aceitar `Metadados_Esforco` como fonte de esforco para a migracao e manter as duplicatas como individuos/lotes a serem agregados pelo migrador.
- Nenhuma pendencia executavel nesta operacao. Ajustes futuros devem abrir revisao pontual preservando a linha de base de junho.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| R01 - abril/2026 | `analysis` | `R2` | `review_completed` | [BRAAVG002_ICTIOFAUNA_ABRIL_2026_REV_R01.md](../reviews/BRAAVG002_ICTIOFAUNA_ABRIL_2026_REV_R01.md) |

## Fechamento E Aprendizados

- validadores: `scripts/validation/validar_migracao_ictiofauna.py` atualizado para campanhas ordinais e conferencia de campanhas entre abas.
- produtos: aprovados pelo usuario em 2026-07-01.
- manifesto/inventario: registro desta operacao funciona como inventario da rodada; saida oficial contem 31 arquivos conferidos.
- patterns: registrar como padrao operacional local que PNGs grandes no Google Drive devem ser salvos primeiro em diretorio temporario local e depois copiados para a pasta final.
- portfolio: dossie `docs/AVG_ICTIOFAUNA_2026.md` atualizado com junho/2026 e validacoes minimas.
- backlog: avaliar criacao de recipe `configs/projects` para AVG Ictiofauna 2026 e considerar promover o runner parcial para nome mais generico.
