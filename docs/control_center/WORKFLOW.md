# Fluxo Operacional Da Central De Controle

Este e o caminho oficial para validacao, cadastro, migracao, consolidacao,
analises e entrega. Ele deve ser percorrido sempre que a Central de Controle for
acionada.

## Gatilhos Reconhecidos

- `center_control`
- `center_cotrol`
- `control_center`
- `central de controle`
- "seguir o fluxo operacional"

Ao reconhecer um gatilho, abrir nesta ordem:

1. [README.md](README.md)
2. [LLM_CONTEXT_POLICY.md](LLM_CONTEXT_POLICY.md), quando o executor for
   Codex/LLM
3. [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md)
4. registro da operacao alvo em [operations](operations/README.md)
5. [project_registry.json](../registry/project_registry.json), filtrado pelo
   projeto/codigo/canonical_key
6. dossie em `docs/projects/`, somente do projeto alvo
7. recipe em `configs/projects/`, somente quando existir para a operacao
8. portfolio, patterns e lastros aplicaveis, sem abrir historico inteiro

## Politica De Contexto Para LLM

Quando a Central for usada por Codex ou outra LLM, aplicar
[LLM_CONTEXT_POLICY.md](LLM_CONTEXT_POLICY.md).

Regras obrigatorias:

- usar a operacao alvo como limite de contexto;
- nao abrir `outputs/`, `logs/`, snapshots, planilhas, imagens, HTMLs ou PDFs
  sem dependencia tecnica registrada;
- nao carregar todos os registros de operacao ou revisao;
- consultar registry, dossie, recipe e lastro de forma filtrada;
- registrar no documento da operacao qualquer abertura de lastro pesado;
- se o consumo de contexto parecer anormal, parar expansao de contexto e voltar
  para a operacao e etapa atuais.

## Fluxo Canonico

```text
ABERTURA
  |
  v
VALIDACAO DOS DADOS
  |
  v
GATE A — AJUSTE E APROVACAO DOS DADOS
  |
  v
CADASTRO E AUDITORIA DE ESPECIES
  |
  v
GATE B — AJUSTE E APROVACAO TAXONOMICA
  |
  v
MIGRACAO
  |
  v
CONSOLIDACAO
  |
  v
CONFIGURACAO DAS ANALISES
  |
  v
GATE C — TEMPLATE + PALETA + PASTA DE SAIDA
  |
  v
GERACAO DOS PRODUTOS
  |
  v
REVISAO VISUAL E TECNICA
  |
  v
FECHAMENTO E APRENDIZADO
```

## Etapas E Evidencias

| Etapa | Acao obrigatoria | Evidencia minima | Proximo estado |
| --- | --- | --- | --- |
| 0. Abertura | Confirmar projeto, grupo, campanhas, entradas, saida e operacao; consultar Supabase e registrar `codigo_interno_opyta`, `canonical_key` e `id_projeto` | Registro da operacao criado e identidade Supabase consultada | `validating` |
| 1. Validacao | Validar estrutura, chaves, pontos, coordenadas, esforco, resultados, taxonomia, tipos de amostragem e totais | Relatorio de validacao, auditoria de coordenadas, reconciliacao por tipo de amostragem e lista de ajustes | `awaiting_data_approval` |
| Gate A | Aplicar ajustes permitidos e apresentar o pacote corrigido, incluindo decisao sobre coordenadas | Aprovacao explicita do usuario | `registering_species` |
| 2. Especies | Identificar especies novas, cadastrar e auditar todos os atributos exigidos | Relatorio de completude taxonomica | `awaiting_species_approval` |
| Gate B | Resolver campos incertos, endemismo, origem, ameaca e demais atributos | Aprovacao explicita do usuario ou registro `nao aplicavel` | `ready_to_migrate` |
| 3. Migracao | Reconfirmar identidade Supabase no preflight, executar carga controlada e comparar fonte com banco | Totais Excel x banco por tipo de amostragem, `id_projeto` reconfirmado e divergencias | `consolidating` |
| 4. Consolidacao | Criar backup, consolidar e auditar a fatia do projeto | Nome do backup e comparacao base x consolidado | `configuring_analysis` |
| 5. Configuracao | Propor template pelo numero de campanhas, paleta, pasta de saida e produtos | Mapa de decisao analitica | `awaiting_analysis_approval` |
| Gate C | Confirmar template, paleta, pasta de saida e matriz produto x tipo de dado/amostragem | Aprovacao explicita do usuario | `generating_products` |
| 6. Geracao | Gerar bases, tabelas, graficos, HTML e manifesto | Produtos e lastro reprodutivel | `reviewing_outputs` |
| 7. Revisao | Conferir numeros, texto, layout e integridade | Validadores, hashes e pendencias visuais | `completed`, `review_planned` ou fluxo de revisao |
| 8. Fechamento | Atualizar dossie, registries, patterns, portfolio e backlog | Registro da operacao encerrado | `completed` |

Quando houver pedido de correcao ou nova rodada de revisao, seguir
[REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md). O protocolo de revisao decide se a
operacao volta ao Gate A, B ou C ou se segue diretamente para texto, layout ou
empacotamento.

## Portoes De Aprovacao

### Gate A — Dados

Antes de cadastrar especies ou migrar:

- apresentar erros, avisos e correcoes realizadas;
- auditar coordenadas de todos os pontos antes da aprovacao: presenca,
  faixa valida, sistema de referencia/CRS, sinais de latitude/longitude
  invertidas, variacao entre campanhas e comparacao com KMZ/KML, shapefile,
  planilha oficial ou outra fonte espacial aprovada;
- registrar a estrategia de coordenadas quando houver conflito, por exemplo
  `referencia_kmz`, `primeira_coordenada_valida_planilha`,
  `coordenada_por_campanha` ou `sem_referencia_externa_aprovada`;
- tratar divergencia de coordenada como pendencia de Gate A. Se a coordenada
  afetar banco, consolidado, Darwin Core, mapa, tabela espacial ou qualquer
  produto com latitude/longitude, classificar a revisao como `data/R3`;
- preservar os arquivos originais;
- identificar qualquer ajuste que dependa de criterio tecnico do usuario;
- registrar a mensagem ou decisao que autorizou o avanco.
- quando houver amostragem qualitativa e quantitativa, preservar o tipo
  explicito da fonte e reconciliar, por grupo/campanha/metodo/tipo, linhas da
  fonte, linhas preparadas e medida ou presencas;
- conferir a compatibilidade entre o tipo do resultado e o tipo do esforco;
- bloquear o gate se tipos distintos da fonte forem colapsados ou se valor
  qualitativo for interpretado como abundancia, conforme
  [AQUATIC_SAMPLING_TYPE_POLICY.md](AQUATIC_SAMPLING_TYPE_POLICY.md).

### Gate B — Especies

Antes de migrar:

- confirmar que todas as especies usadas nos resultados existem no cadastro;
- verificar se os atributos obrigatorios foram preenchidos;
- destacar taxons novos, `cf.`, `aff.`, `sp.`, endemismo, origem, ameaca e
  qualquer campo incerto;
- permitir ajustes manuais do usuario;
- registrar a aprovacao taxonomica.

Quando a auditoria identificar táxons não cadastrados, gerar automaticamente a
planilha de pendências na raiz de migração, conforme
[TAXON_REGISTRATION_INTAKE_POLICY.md](TAXON_REGISTRATION_INTAKE_POLICY.md).

Se nao houver especies novas, o gate continua existindo e deve ser registrado
como `nao aplicavel — cadastro ja completo`, com a auditoria correspondente.

### Identidade Supabase

`id_projeto` não é pendência de Gate A nem de Gate B, pois a identidade Supabase deve ser consultada na abertura. Antes da carga, o preflight apenas reconfirma essa identidade, segundo [SUPABASE_IDENTITY_POLICY.md](SUPABASE_IDENTITY_POLICY.md).

### Gate C — Analises

Antes da geracao em lote, confirmar conjuntamente:

1. template adequado ao numero de campanhas;
2. paleta ou identidade visual;
3. pasta final de saida;
4. produtos esperados e formato do relatorio.
5. para bases mistas, matriz produto x tipo de amostragem, incluindo o
   tratamento de composicao, riqueza, abundancia, diversidade, similaridade,
   suficiencia e indices bioticos.

O pipeline pode propor defaults a partir do portfolio, mas nao deve assumir a
aprovacao quando houver mais de uma escolha razoavel.

## Estados Operacionais

| Estado | Significado |
| --- | --- |
| `intake` | Operacao aberta, contexto ainda incompleto. |
| `validating` | Dados em validacao. |
| `awaiting_data_approval` | Gate A aguardando usuario. |
| `registering_species` | Cadastro e auditoria taxonomica em andamento. |
| `awaiting_species_approval` | Gate B aguardando usuario. |
| `ready_to_migrate` | Gates A e B concluídos. |
| `migrating` | Migracao em andamento. |
| `consolidating` | Consolidacao e auditoria em andamento. |
| `configuring_analysis` | Template, paleta, saida e produtos em definicao. |
| `awaiting_analysis_approval` | Gate C aguardando usuario. |
| `generating_products` | Bases, tabelas, figuras e relatorio em geracao. |
| `reviewing_outputs` | Auditoria numerica, textual e de arquivos. |
| `reviewing_layout` | Produtos corretos, com ajustes visuais pendentes. |
| `review_planned` | Revisao futura registrada, ainda sem escopo executavel. |
| `review_scoping` | Tipo, impacto e linha de base da revisao em definicao. |
| `awaiting_review_scope_approval` | Escopo de revisao aguardando usuario. |
| `revising_data` | Revisao de dados e dependencias em andamento. |
| `revising_taxonomy` | Revisao taxonomica e dependencias em andamento. |
| `revising_analysis` | Revisao metodologica ou numerica em andamento. |
| `revising_text` | Revisao textual em andamento. |
| `revising_layout` | Revisao visual em andamento. |
| `revising_package` | Revisao de pacote, nomes ou manifesto em andamento. |
| `validating_revision` | Produtos revisados em auditoria. |
| `awaiting_revision_approval` | Gate R aguardando usuario. |
| `review_completed` | Revisao aprovada e documentada. |
| `completed` | Operacao concluida e documentada. |
| `blocked` | Existe impedimento objetivo registrado. |

Esses estados descrevem a execucao. Eles nao substituem os estados de
maturidade `prototype`, `approved`, `reference` e `deprecated` usados por
patterns e portfolio.

## Regras De Avanco

- Apenas uma etapa fica marcada como atual no registro da operacao.
- Nenhum gate e considerado aprovado por silencio.
- A solicitacao explicita "siga com a migracao" vale como aprovacao dos gates
  anteriores somente quando os ajustes e pendencias ja tiverem sido
  apresentados ao usuario.
- Toda mudanca manual do usuario deve ser revalidada antes da migracao.
- Coordenadas sem auditoria registrada nao podem passar como Gate A limpo.
  Quando nao houver referencia espacial externa, essa ausencia deve ser
  explicitada e aprovada pelo usuario como ressalva antes da migracao.
- Migracao deve falhar fechada se a validacao ou a auditoria taxonomica tiver
  bloqueios.
- Em biota aquatica mista, a migracao tambem deve falhar fechada se o tipo
  explicito for alterado, divergir do esforco ou nao reconciliar entre fonte,
  preparacao, banco e consolidado.
- Consolidacao deve ter backup ou estrategia de reversao registrada.
- Geracao final deve produzir manifesto ou inventario equivalente.
- O Gate R deve bloquear o pacote quando linhas por tipo, presencas
  qualitativas ou total quantitativo divergirem do lastro aprovado, ou quando
  um produto usar tipo de amostragem diferente da matriz aprovada no Gate C.
- Ajustes apenas de layout podem manter a operacao em `reviewing_layout` sem
  invalidar os resultados numericos ja auditados.
- Execucoes por LLM devem obedecer a politica de contexto minimo antes de
  consultar historico, outputs ou lastros pesados.

## Encerramento

Uma operacao so fica `completed` quando:

- os tres gates estiverem registrados;
- migracao e consolidacao tiverem auditoria, quando aplicaveis;
- produtos e validadores estiverem conferidos;
- dossie e registro da operacao estiverem atualizados;
- aprendizados reutilizaveis tiverem destino definido.
