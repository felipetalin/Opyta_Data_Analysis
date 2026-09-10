# WSPKIN001 — Zooplâncton — Migração inicial

## Controle

- projeto: WSPKIN001 / Kinross
- grupo: Zooplâncton
- operacao: Migração inicial
- estado atual: `reviewing_outputs`
- aberta em: 2026-09-02
- atualizada em: 2026-09-04
- proxima acao: Revisar o pacote gerado; planilha integrada adicional fica por ultimo.

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração_zooPLAN.xlsx`
- cadastro de especies: pendente de auditoria após Gate A.
- saida-piloto: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados`.
- dossie: pendente.
- recipe: pendente.
- lastro: pendente.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | WSPKIN001 confirmado no Supabase como `id_projeto=211`. |
| Validacao | concluida | 244 registros, 61 táxons e 20 chaves espaciais; relatório de pré-migração criado. |
| Gate A — dados | concluido | Ausências confirmadas pelo usuário em 2026-09-02. |
| Cadastro de especies | concluida | Planilha de cinco táxons novos preenchida; três nomes aceitos indicados para o mapeamento. |
| Auditoria de atributos | concluida | Campos preenchidos; `Ciliado NI` preservado como identificação parcial. |
| Gate B — especies | concluido | Usuário aprovou; cadastros aplicados no Supabase. |
| Migracao | concluida | 244 resultados carregados com reconciliação fonte × banco. |
| Consolidacao | concluida | 244 registros consolidados; backup criado antes da carga. |
| Configuracao das analises | concluida parcialmente | Tabela Excel neutra de composição taxonômica; sem paleta ou gráficos. |
| Gate C — analises | aprovado parcial | Usuário autorizou em 2026-09-04 somente a tabela-piloto. |
| Geracao dos produtos | concluida parcialmente | `01_tabela_composicao_zooplancton.xlsx` gerada. |
| Revisao tecnica | pendente | |
| Revisao de layout | pendente | |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved_with_notes` | Ausências confirmadas; regra quali/quanti e ressalva espacial já aprovadas. |
| B — especies | `approved` | Cadastro aplicado em 2026-09-02. |
| C — analises | `pending` | |

## Validacao Dos Dados

- bloqueios: nenhum no Gate A.
- avisos: a aba de resultados conserva campos herdados de ictiofauna.
- coordenadas: 20/20 válidas, uma coordenada por ponto; seguir sem referência espacial externa, conforme ressalva aprovada para WSPKIN001.
- regra de transformação: `X` é ocorrência qualitativa; valores numéricos são abundância quantitativa em `org/amostra`.
- campos descartados no mapeamento: `Malha_ou_Anzol`, `CT_cm`, `CP_cm`, `PC_g`, `Sexo`, `EMG` e `Observacao_Individuo_Lote` quando contiverem `N.A.`.
- ajustes aplicados: regra de mapeamento registrada; fonte original preservada.
- arquivos corrigidos: nenhum.

## Cadastro E Auditoria De Especies

- especies novas: 5; planilha criada em `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Cadastro_Especies_WSPKIN001_Zooplancton.xlsx`.
- atributos obrigatorios: 56 táxons cadastrados após normalização de espaços; nenhum incompleto.
- campos incertos: `Ciliado NI` sem classificação inferior; gravar `N.A.` nos campos não aplicáveis.
- ajustes manuais: nenhum.

## Pendencias

- Ausências confirmadas: PT_09 em C001-2026-03-CH, PT_09 em C002-2026-07-SC e PT_10 em C002-2026-07-SC.
- Gate B: aguarda o preenchimento da planilha de pendências taxonômicas.
- Dependência de análises: aguardar ictiofauna e zoobentos.

## Fechamento E Aprendizados

## Gate C Parcial — Tabela de Composição Taxonômica

- decisão do usuário em 2026-09-04: gerar somente a tabela de composição para confirmação taxonômica; paletas serão definidas em etapa posterior.
- aprovação parcial: template Excel neutro, sem gráfico; pasta `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados`.
- produto final gerado: `Zooplancton\01_tabela_composicao_zooplancton.xlsx`, com 51 táxons canônicos e 244 linhas de resultados de duas campanhas.
- validação: planilha contém `Composicao_Taxonomica`, `Metadados` e `Conferencia`; total de táxons conferido contra o banco consolidado.
- próximo passo: usuário revisar a taxonomia na aba `Conferencia`; os demais produtos e qualquer paleta continuam fora deste Gate C parcial.

- validadores: pendente.
- manifesto: pendente.
- patterns: pendente.
- portfolio: pendente.
- backlog: pendente.

## Preflight Gate C Completo - 2026-09-04

- solicitacao: espelhar integralmente os pacotes de `BRACED001 / Fonseca` e `BRAAEG001`, incluindo paineis por campanha, minimapas, relatorio HTML, Darwin Core, sintese, manifestos e validacao; nenhuma geracao executada neste preflight.
- base apta: 244 registros consolidados, 51 taxons canonicos definitivos, duas campanhas e 10 esforcos/pontos por campanha; taxon, filo, campanha, ponto e coordenadas sem nulos.
- desenho amostral: C001 possui 11 registros qualitativos e 115 quantitativos em nove pontos; C002 possui 118 quantitativos em oito pontos. Os esforcos sem resultado correspondem as ausencias aprovadas no Gate A e devem entrar como zero amostral, nao como dado faltante.
- produtos propostos: base consolidada; composicao e ocorrencia; riqueza por ponto e por filo; densidade total, absoluta e relativa por filo; densidade por taxon; matriz/heatmap taxon x ponto; diversidade alfa; matrizes, Bray-Curtis e dendrogramas por amostra e por ponto; suficiencia amostral; minimapa de grupos associados a bioindicacao; sintese; Darwin Core; relatorio HTML; manifesto e validacao.
- minimapa viavel: os grupos de ampla tolerancia, materia organica e gradientes troficos possuem registros nas duas campanhas; ha camada espacial local em `Geo`. O produto sera apresentado como associacao ecologica, sem diagnostico isolado de qualidade ambiental.
- formato visual proposto: A4 paisagem, 600 dpi, paineis separados para C001-Chuva e C002-Seca, top 20 apenas nas figuras 08/09 e tabelas completas.
- saida confirmada: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Zooplancton`.
- planilha adicional avaliada: um arquivo integrado do projeto com abas de dados/resultados e graficos Excel editaveis quando nativos; heatmap, dendrogramas e minimapa devem ser inseridos como imagens de alta resolucao com respectivas abas-fonte para preservar fidelidade.
- paleta definida pelo usuario em 2026-09-04: mesma identidade verde de BRACED001/Fonseca e BRAAEG001 (`#11420C`, `#19FF00`, `#6A8F63` e cores auxiliares dos referenciais).
- revisao espacial R02 aplicada antes da geracao: 20 pontos-campanha e 244 linhas consolidadas de Zooplancton sincronizados com as novas coordenadas; auditoria geral das 368 linhas WSP com zero divergencia.
- Gate C completo: integrado adicional aprovado para execucao por ultimo, somente com graficos nativos e editaveis do Excel; produtos incompatíveis entram apenas como abas de dados.

## Revisão Taxonômica GBIF R03 — 2026-09-04

- GBIF aplicado a todo o zooplâncton com prévia, transação e backups.
- 36 de 51 táxons alterados; 244 resultados e abundância total 26,52 preservados, sem duplicações.
- pacote completo regenerado: 14/14 figuras válidas; composição definitiva com `Decisoes_Taxonomicas`.
- validação final `OK`: 35 arquivos verificados e zero erros.
- Gate R aguarda aprovação do usuário; planilha integrada adicional continua por último.
