# WSPKIN001 — Fitoplâncton — Migração inicial

## Controle

- projeto: WSPKIN001 / WSP Kinross Bandeirinhas
- grupo: Fitoplâncton
- operacao: Migração inicial
- estado atual: `reviewing_outputs`
- aberta em: 2026-09-02
- atualizada em: 2026-09-04
- proxima acao: Revisar a classificacao AlgaeBase R02 e o pacote regenerado; planilha integrada adicional fica por ultimo.

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração _Fito_wsp.xlsx`
- cadastro de especies: pendente.
- saida-piloto: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados`.
- dossie: não localizado no registry filtrado em 2026-09-02.
- recipe: não localizada no registry filtrado em 2026-09-02.
- lastro: pendente.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Operação criada; fonte identificada; registry ainda sem entrada WSPKIN001. |
| Validacao | concluida | Relatório em `outputs/validacoes/wspkin001_fitoplancton_20260902/`; estrutura e coordenadas internas OK, com cinco pendências. |
| Gate A — dados | concluido | Decisões do usuário registradas em 2026-09-02. |
| Cadastro de especies | concluida | Planilha de 10 táxons novos preenchida; nome aceito registrado para `Stephanocyclus meneghinianus`. |
| Auditoria de atributos | concluida | Dois registros existentes completados; fonte taxonômica informada. |
| Gate B — especies | concluido | Usuário aprovou; cadastros e complementos aplicados no Supabase. |
| Migracao | concluida | 124 resultados carregados com reconciliação fonte × banco. |
| Consolidacao | concluida | 124 registros consolidados; backup criado antes da carga. |
| Configuracao das analises | concluida parcialmente | Tabela Excel neutra de composição taxonômica; sem paleta ou gráficos. |
| Gate C — analises | aprovado parcial | Usuário autorizou em 2026-09-04 somente a tabela-piloto. |
| Geracao dos produtos | concluida parcialmente | `01_tabela_composicao_fitoplancton.xlsx` gerada. |
| Revisao tecnica | pendente | |
| Revisao de layout | pendente | |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved_with_notes` | Ausências confirmadas; regra qualitativa/quantitativa e descarte de campos aprovados; ressalva espacial aceita. |
| B — especies | `approved` | Cadastro aplicado em 2026-09-02. |
| C — analises | `pending` | |

## Validacao Dos Dados

- bloqueios: nenhum no Gate A.
- avisos: nenhuma referência espacial externa disponível; ressalva aprovada pelo usuário.
- coordenadas: 20/20 válidas, uma coordenada por ponto; seguir sem comparação externa, aprovado em 2026-09-02.
- regra de transformação aprovada: `X` representa ocorrência de amostragem qualitativa; valor numérico representa abundância de amostragem quantitativa em `org/amostra`.
- campos descartados no mapeamento: `Malha_ou_Anzol`, `CT_cm`, `CP_cm`, `PC_g`, `Sexo`, `EMG` e `Observacao_Individuo_Lote` quando contiverem `N.A.`.
- ausências confirmadas: PT_03, PT_04, PT_06 e PT_09 em C001-2026-03-CH; PT_07, PT_09 e PT_10 em C002-2026-07-SC.
- ajustes aplicados: nenhum.
- arquivos corrigidos: nenhum.

## Cadastro E Auditoria De Especies

- especies novas: 10, listadas em `outputs/validacoes/wspkin001_fitoplancton_20260902/auditoria_cadastro_supabase_wspkin001_fitoplancton_20260902.md`; planilha criada em `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Cadastro_Especies_WSPKIN001_Fitoplancton.xlsx`.
- atributos obrigatorios: 67/77 táxons encontrados; `Euastrum sp.` e `Phacus orbicularis` sem classe, ordem e família.
- campos incertos: classificação e autoria dos 10 táxons novos aguardam auditoria.
- ajustes manuais: nenhum.

## Migracao E Consolidacao

- IDs: `id_projeto=211`; campanhas C001=969 e C002=1013.
- totais da fonte: 124 resultados.
- totais no banco: 124 resultados de fitoplâncton.
- coordenadas no banco/consolidado: pendente.
- divergencias: pendente.
- backup: `public.backup_biota_wspkin001_20260902t154518_fitoplancton`.
- totais consolidados: 124.

## Configuracao Das Analises

- numero de campanhas: pendente.
- template: pendente.
- paleta: pendente.
- pasta de saida: pendente.
- produtos: pendente.

## Pendencias

- Identidade Supabase confirmada na abertura: cliente WSP `id_cliente=216`; WSPKIN001 `id_projeto=211`. O preflight da migração somente reconfirmará esses IDs.

## Fechamento E Aprendizados

## Gate C Parcial — Tabela de Composição Taxonômica

- decisão do usuário em 2026-09-04: gerar somente a tabela de composição para confirmação taxonômica; paletas serão definidas em etapa posterior.
- aprovação parcial: template Excel neutro, sem gráfico; pasta `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados`.
- produto final gerado: `Fitoplancton\01_tabela_composicao_fitoplancton.xlsx`, com 77 táxons e 124 linhas de resultados de duas campanhas.
- validação: planilha contém `Composicao_Taxonomica`, `Metadados` e `Conferencia`; total de táxons conferido contra o banco consolidado.
- próximo passo: usuário revisar a taxonomia na aba `Conferencia`; os demais produtos e qualquer paleta continuam fora deste Gate C parcial.

- validadores: pendente.
- manifesto: pendente.
- patterns: pendente.
- portfolio: pendente.
- backlog: pendente.

## Preflight Gate C Completo - 2026-09-04

- solicitacao: espelhar integralmente os pacotes de `BRACED001 / Fonseca` e `BRAAEG001`, incluindo paineis por campanha, minimapa, relatorio HTML, Darwin Core, sintese, manifestos e validacao; nenhuma geracao executada neste preflight.
- base apta: 124 registros consolidados, 77 taxons definitivos, duas campanhas e 10 esforcos/pontos por campanha; taxon, filo, campanha, ponto e coordenadas sem nulos.
- desenho amostral: C001 possui 20 registros qualitativos em cinco pontos e tres registros quantitativos em tres pontos; C002 possui 85 registros qualitativos em sete pontos e 16 quantitativos em seis pontos. Os esforcos sem resultado correspondem as ausencias aprovadas no Gate A e devem entrar como zero amostral, nao como dado faltante.
- produtos propostos: base consolidada; composicao e ocorrencia; riqueza por ponto e por filo; densidade total, absoluta e relativa por filo; densidade por taxon; matriz/heatmap taxon x ponto; diversidade alfa; matriz, Bray-Curtis e dendrograma; suficiencia amostral; minimapa de Cyanobacteria; sintese; Darwin Core; relatorio HTML; manifesto e validacao.
- minimapa viavel: cinco combinacoes campanha-ponto com Cyanobacteria e camada espacial local disponivel em `Geo`; adaptar rotulos e enquadramento aos 10 pontos WSP, sem reutilizar offsets fixos dos referenciais.
- formato visual proposto: A4 paisagem, 600 dpi, paineis separados para C001-Chuva e C002-Seca, top 20 apenas nas figuras 08/09 e tabelas completas.
- saida confirmada: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Fitoplancton`.
- planilha adicional avaliada: um arquivo integrado do projeto com abas de dados/resultados e graficos Excel editaveis quando nativos; heatmap, dendrograma e minimapa devem ser inseridos como imagens de alta resolucao com respectivas abas-fonte para preservar fidelidade.
- paleta definida pelo usuario em 2026-09-04: mesma identidade verde de BRACED001/Fonseca e BRAAEG001 (`#11420C`, `#19FF00`, `#6A8F63` e cores auxiliares dos referenciais).
- revisao espacial R02 aplicada antes da geracao: 20 pontos-campanha e 124 linhas consolidadas de Fitoplancton sincronizados com as novas coordenadas; auditoria geral das 368 linhas WSP com zero divergencia.
- Gate C completo: integrado adicional aprovado para execucao por ultimo, somente com graficos nativos e editaveis do Excel; produtos incompatíveis entram apenas como abas de dados.

## Revisao Taxonomica AlgaeBase R02 - 2026-09-04

- 46 de 77 taxons tiveram Reino e/ou Filo padronizados; 124 registros consolidados sincronizados.
- filos finais exclusivos: Bacillariophyta, Charophyta, Cyanobacteria, Euglenozoa, Chlorophyta, Ochrophyta, Rhodophyta e Cryptophyta.
- pacote completo regenerado e validado: 14/14 figuras validas, zero erros.
- composicao definitiva possui `Composicao_Taxonomica`, `Metadados`, `Conferencia` e `Decisoes_Taxonomicas`; manifesto e hash atualizados.
