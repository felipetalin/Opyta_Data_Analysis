# BRAAVG002 — Zoobentos — Marco de 2026 — Revisao R01

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- operacao de origem: resultados de Zoobentos da campanha `44ª-Mar-26`
- revisao: `R01`
- estado atual: `awaiting_revision_approval`
- solicitada em: 2026-06-22
- atualizada em: 2026-06-22
- proxima acao: obter aprovacao final da figura e da planilha revisadas no Gate R

## Escopo

- solicitacao do usuario: avaliar o erro tecnico no grafico EPT/CHOL, pois CHOL
  deve considerar `Chironomidae + Oligochaeta/Oligoqueta`;
- tipo principal: `analysis`;
- tipos secundarios: `package`;
- impacto: `R2`;
- produtos alvo:
  - `12_df_ept_chol_zoobentos.xlsx`;
  - `12_grafico_ept_chol_zoobentos.png`;
- fora do escopo:
  - alteracao dos dados no Supabase;
  - migracao ou consolidacao;
  - alteracao dos demais indicadores da campanha.

## Linha De Base

- pasta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/marco-26`;
- versao/data: produtos gerados em 2026-06-09;
- manifesto: `metadata_resultados_zoobentos.json`;
- hashes:
  - PNG: `6b6a925dd899ebe6cfc22e7535ca54697058aaef8e59001bd45ff3c8889c65c3`;
  - XLSX: `071f1064d9218bbd127e3945e31d59470129957b5f1fe687c5762015b837dc7c`;
- snapshot/backup:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/marco-26/_revisoes/R01_linha_base_20260622`.

## Dependencias E Retorno

- Gate A reaberto: nao;
- Gate B reaberto: nao;
- Gate C reaberto: nao; a definicao correta de CHOL ja e um pattern aprovado;
- banco afetado: nao;
- produtos dependentes:
  - planilha EPT/CHOL;
  - figura EPT/CHOL;
  - metadata/manifesto da pasta.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Arquivos, data e hashes registrados. |
| Triagem de tipo e impacto | concluida | Erro classificado como `analysis/R2`. |
| Aprovacao de escopo | concluida | Usuario autorizou a regeneracao em 2026-06-22. |
| Correcao | concluida | Regra atual `CHOL = Chironomidae + Oligochaeta/Oligoqueta` aplicada. |
| Regeneracao de dependencias | concluida | XLSX, PNG e metadata atualizados. |
| Validacao da revisao | concluida | Totais, percentuais, colunas, hashes e figura conferidos. |
| Gate R — aprovacao final | pendente | Figura revisada apresentada ao usuario. |
| Promocao e fechamento | pendente | Atualizar lastro depois da aprovacao. |

## Diagnostico Tecnico

A figura e a planilha foram geradas em 2026-06-09 com a implementacao antiga,
na qual `CHOL` era equivalente somente a `Chironomidae`. A correcao
`CHOL = Chironomidae + Oligochaeta/Oligoqueta` entrou no pipeline em
2026-06-15.

Na campanha `44ª-Mar-26`, `Oligochaeta` ocorreu somente no `PIC-13`, com tres
organismos. Nesse ponto:

| Metrica | Produto atual | Regra correta |
| --- | ---: | ---: |
| Total de organismos | 10 | 10 |
| Chironomidae | 1 | 1 |
| Oligochaeta | nao incorporado | 3 |
| CHOL | 1 | 4 |
| %CHOL | 10,00% | 40,00% |

No conjunto da campanha:

| Metrica | Produto atual | Regra correta |
| --- | ---: | ---: |
| Abundancia total | 154 | 154 |
| EPT | 22 | 22 |
| Chironomidae | 6 | 6 |
| Oligochaeta | nao incorporado | 3 |
| CHOL | 6 | 9 |
| %CHOL ponderado | 3,90% | 5,84% |

A legenda `%Chironomidae` no PNG confirma visualmente que o produto representa
a regra antiga. O Excel atual tambem nao possui as colunas separadas
`chironomidae` e `oligochaeta`, exigidas pelo pattern aprovado.

## Alteracoes Previstas

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Definicao de CHOL | Apenas Chironomidae | Chironomidae + Oligochaeta/Oligoqueta | Corrigir o indicador biologico. |
| PIC-13 | 10% CHOL | 40% CHOL | Incorporar tres Oligochaeta. |
| Legenda | `%Chironomidae` | `%CHOL` | Nomear corretamente o indicador composto. |
| Planilha | Sem colunas de componentes | Colunas `chironomidae`, `oligochaeta` e `chol` | Garantir rastreabilidade. |

## Arquivos Regenerados

| Arquivo | SHA-256 anterior | SHA-256 revisado |
| --- | --- | --- |
| `12_df_ept_chol_zoobentos.xlsx` | `071f1064d9218bbd127e3945e31d59470129957b5f1fe687c5762015b837dc7c` | `7247a6f7536c5c3d6f51392e6213b910f56dac8817db0efaee70b5e12a5ee32c` |
| `12_grafico_ept_chol_zoobentos.png` | `6b6a925dd899ebe6cfc22e7535ca54697058aaef8e59001bd45ff3c8889c65c3` | `d497b63f0ed8559171af3afc46ccc7109c597148a1bc711455e605d60bb93932` |
| `metadata_resultados_zoobentos.json` | preservado no snapshot | atualizado com o historico da R01 |

## Validadores

- comparacao com `11_df_matriz_comunidade_zoobentos.xlsx`;
- comparacao com `06B_df_abundancia_ordem_44_Mar_26_zoobentos.xlsx`;
- conferencia da implementacao atual em
  `src/opyta_analysis/pipelines/diagnostico/zoobentos.py`;
- validacao visual da figura original e da figura revisada;
- confirmacao das colunas `chironomidae`, `oligochaeta` e `chol`;
- confirmacao de 154 organismos, 22 EPT, 6 Chironomidae, 3 Oligochaeta e
  9 CHOL;
- confirmacao de 40% CHOL no `PIC-13`;
- nenhum dado do banco foi alterado.

## Gate R

- status: `awaiting_revision_approval`
- apresentado em: 2026-06-22
- aprovado em:
- registro da aprovacao:

## Aprendizados E Pendencias

- produtos AVG gerados antes de 2026-06-15 podem manter a regra antiga de CHOL;
- apos corrigir marco, avaliar se fevereiro de 2026 e outros produtos legados
  tambem precisam de auditoria do indicador;
- o pacote revisado aguarda aprovacao final no Gate R.
