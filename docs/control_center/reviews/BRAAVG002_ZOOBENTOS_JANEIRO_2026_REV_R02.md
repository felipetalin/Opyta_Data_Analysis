# BRAAVG002 — Zoobentos — Janeiro de 2026 — Revisao R02

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- operacao de origem: resultados de Zoobentos da campanha `42ª-Jan-26`
- revisao: `R02`
- estado atual: `review_completed`
- solicitada em: 2026-06-22
- atualizada em: 2026-06-22
- proxima acao: nenhuma; revisao aprovada, promovida e encerrada

## Escopo

- solicitacao do usuario: preservar os resultados antigos de janeiro e gerar
  os dados com os scripts e o layout atuais em uma pasta de revisao;
- tipo principal: `analysis`;
- tipos secundarios: `layout`, `package`;
- impacto: `R2`;
- produtos alvo: pacote completo de Zoobentos da campanha `42ª-Jan-26`;
- pasta da linha de base:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/janeiro-26`;
- pasta da revisao:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/janeiro-26/_revisoes/R02_novo_padrao_20260622`;
- fora do escopo:
  - alteracao dos dados no Supabase;
  - migracao ou consolidacao;
  - sobrescrita dos arquivos antigos;
  - alteracao de fevereiro ou marco.

## Linha De Base

- pacote antigo criado em 2026-04-16 e 2026-04-17;
- arquivos: 12 PNGs e `Resultados_Consolidados_Zoobentos.xlsx`;
- campanha: `42ª-Jan-26`;
- registros: 43;
- pontos com resultado: 9;
- pontos sem resultado: `PIC-01`, `PIC-02`, `PIC-03` e `PIC-11`;
- taxons: 22;
- abundancia total: 118 organismos;
- manifesto de hashes: gerado junto ao pacote revisado.

## Dependencias E Retorno

- Gate A reaberto: nao;
- Gate B reaberto: nao;
- Gate C reaberto: nao; o usuario solicitou explicitamente o padrao atual;
- banco afetado: nao;
- produtos dependentes: todos os produtos analiticos, graficos, Darwin Core e
  metadata da campanha de janeiro.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Pasta antiga inventariada. |
| Triagem de tipo e impacto | concluida | Revisao classificada como `analysis/layout/R2`. |
| Aprovacao de escopo | concluida | Usuario solicitou geracao no novo padrao em pasta de revisao. |
| Correcao/adequacao | concluida | Pipeline atual aplicado; graficos de ate duas campanhas ajustados para comparacao por ponto. |
| Regeneracao de dependencias | concluida | 14 XLSX, 12 PNGs e 2 JSONs gerados na pasta R02. |
| Validacao da revisao | concluida | Totais, planilhas, imagens, EPT/CHOL e hashes conferidos. |
| Gate R — aprovacao final | concluida | Usuario aprovou o pacote em 2026-06-22. |
| Promocao e fechamento | concluida | 28 arquivos promovidos para a pasta oficial; 13 arquivos legados preservados. |

## Diagnostico Tecnico

O workbook antigo e a consulta atual ao consolidado coincidem nos principais
totais:

| Metrica | Linha de base | Consolidado atual |
| --- | ---: | ---: |
| Registros | 43 | 43 |
| Taxons | 22 | 22 |
| Abundancia | 118 | 118 |
| Pontos com resultado | 9 | 9 |

Assim, a revisao pode usar os dados consolidados sem alterar a fonte. O pacote
novo deve aplicar:

- identidade visual AVG atual;
- ordem oficial dos 13 pontos, incluindo zeros;
- areas de controle 01 e 02;
- CHOL como `Chironomidae + Oligochaeta/Oligoqueta`;
- tabelas analiticas individuais;
- Darwin Core;
- metadata e manifesto de hashes.

## Alteracoes Previstas

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Estrutura | Workbook unico + 12 PNGs | Tabelas XLSX por bloco + PNGs + Darwin Core + metadata | Padrao atual do pipeline. |
| Pontos sem captura | Ausentes de parte dos graficos | Mantidos com valor zero | Preservar desenho amostral. |
| Identidade visual | Layout legado | Tema AVG atual | Padronizacao. |
| EPT/CHOL | Produto legado | Regra e rastreabilidade atuais | Coerencia tecnica. |
| Lastro | Sem metadata de revisao | Manifesto, hashes e registro R02 | Reprodutibilidade. |

## Arquivos Regenerados

Pasta:

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/janeiro-26/_revisoes/R02_novo_padrao_20260622`

Conteudo controlado:

- 14 planilhas XLSX;
- 12 figuras PNG;
- `metadata_resultados_zoobentos.json`;
- `manifesto_revisao_R02.json`.

Os 26 produtos analiticos abrangem os blocos 3 a 13, incluindo composicao,
ocorrencia, riqueza, abundancia, diversidade, similaridade, suficiencia
amostral, BMWP, EPT/CHOL e Darwin Core.

Durante a inspecao visual, os graficos de riqueza, abundancia e diversidade
foram regenerados. O pipeline agora usa:

- barras comparativas por ponto quando houver uma ou duas campanhas;
- paineis temporais para series com mais de duas campanhas;
- marcador generico para campanhas sem classificacao sazonal CH/SC.

Depois da aprovacao, os 28 arquivos controlados foram copiados para a pasta
oficial de janeiro. A pasta R02 foi mantida como snapshot auditavel e os 13
arquivos do layout antigo permaneceram intactos.

## Validadores

- comparacao com `Resultados_Consolidados_Zoobentos.xlsx`;
- comparacao com o consolidado do projeto;
- auditoria dos totais de registros, taxons e abundancia;
- validacao dos arquivos XLSX e PNG;
- inspecao visual dos graficos principais;
- conferencia do EPT/CHOL.

Resultados da validacao:

| Verificacao | Resultado |
| --- | --- |
| Planilhas abertas sem erro | 14 de 14 |
| Figuras validas e nao vazias | 12 de 12 |
| Integridade dos hashes | sem divergencias |
| Registros | 43 |
| Taxons | 22 |
| Abundancia | 118 |
| Pontos representados | 13, incluindo 4 zeros |
| EPT | 14 individuos |
| Chironomidae | 11 individuos |
| Oligochaeta | 0 individuos |
| CHOL | 11 individuos |

## Gate R

- status: `approved`
- apresentado em: 2026-06-22
- aprovado em: 2026-06-22
- registro da aprovacao: usuario confirmou que o pacote ficou perfeito e que
  a geracao funcionou corretamente

## Aprendizados E Pendencias

- a versao R02 permanece em `_revisoes` para auditoria;
- os produtos no novo padrao estao tambem na pasta oficial de janeiro;
- os arquivos legados foram preservados para comparacao e rastreabilidade.
