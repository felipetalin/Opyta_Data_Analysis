# BRAAVG002 - Ictiofauna - Abril de 2026 - Revisao R01

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- operacao de origem: resultados de Ictiofauna da campanha `45a-Abr-26`
- revisao: `R01`
- estado atual: `review_completed`
- solicitada em: 2026-07-07
- atualizada em: 2026-07-07
- proxima acao: revisao concluida; arquivos revisados promovidos para a pasta oficial

## Escopo

- solicitacao do usuario: corrigir a curva de especie do produto de Ictiofauna de abril/2026;
- tipo principal: `analysis`;
- tipos secundarios: `package`;
- impacto: `R2`;
- produtos alvo:
  - `12_df_curva_suficiencia_ictiofauna.xlsx`;
  - `12_curva_suficiencia_amostral_ictiofauna.png`;
- fora do escopo:
  - alteracao dos dados no Supabase;
  - migracao ou consolidacao;
  - alteracao de taxonomia;
  - alteracao dos demais indicadores da campanha, salvo dependencia direta.

## Linha De Base

- pasta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/abril`;
- versao/data: produtos gerados em 2026-06-01;
- manifesto: nao identificado nesta revisao pontual;
- hashes:
  - PNG: `6358E8004331CA24569DBECE4D9D37944856CCD2AC341BF31FFCF9C0C30EB5B4`;
  - XLSX: `59D9FF8425488E793DBAF46BD391537140E69F6B447E17C4CAD6830C49C0DF51`;
- snapshot/backup:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/abril/_revisoes/R01_linha_base_20260707`.

## Dependencias E Retorno

- Gate A reaberto: nao;
- Gate B reaberto: nao;
- Gate C reaberto: nao;
- banco afetado: nao;
- coordenadas afetadas: nao;
- fonte espacial de referencia: nao aplicavel;
- produtos com latitude/longitude: nao aplicavel;
- produtos dependentes:
  - planilha da curva de suficiencia;
  - figura da curva de suficiencia.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Arquivos, data e hashes registrados. |
| Triagem de tipo e impacto | concluida | Erro classificado como `analysis/R2`; nao ha indicio de erro de dados, coordenadas, taxonomia ou banco. |
| Aprovacao de escopo | concluida | Pedido do usuario foi pontual para a curva de especie de abril/2026. |
| Correcao | concluida | Runner AVG de ictio ajustado para passar pontos com captura zero ao bloco 12. |
| Regeneracao de dependencias | concluida | PNG e XLSX revisados gerados em `_revisoes/R01_curva_suficiencia_20260707`. |
| Validacao da revisao | concluida | Conferidos 13 unidades amostrais, riqueza observada final 4,0, Jackknife 1 final 7,69, PNG e XLSX abrindo corretamente. |
| Gate R - aprovacao final | concluida | Usuario aprovou a substituicao em 2026-07-07 com "ok substituir". |
| Promocao e fechamento | concluida | PNG e XLSX revisados substituidos na pasta oficial e conferidos. |

## Diagnostico Tecnico

A planilha de linha de base da curva possui somente 4 unidades amostrais
(`n_amostras = 1..4`). A campanha `45a-Abr-26` possui 13 pontos com esforco
quantitativo registrado, dos quais 9 tiveram captura zero.

O runner AVG ja montava `df_point_metrics` com os pontos de captura zero para
riqueza, abundancia e CPUE por ponto, mas o bloco 12 de suficiencia era chamado
com `df_observed`, contendo apenas pontos com captura. Assim, a curva de
suficiencia foi calculada sobre 4 pontos com ocorrencia, e nao sobre as 13
unidades amostrais da campanha.

## Alteracoes

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Base do bloco 12 | Apenas pontos com captura (`df_observed`) | Pontos com esforco, incluindo captura zero (`df_point_metrics`) | Corrigir o numero de unidades amostrais da curva. |
| `n_amostras` final | 4 | esperado: 13 | Representar os 13 pontos da campanha. |
| Banco/migracao | Sem alteracao | Sem alteracao | Erro restrito ao calculo do produto derivado. |

## Arquivos Regenerados

| Arquivo | SHA-256 anterior | SHA-256 revisado |
| --- | --- | --- |
| `12_df_curva_suficiencia_ictiofauna.xlsx` | `59D9FF8425488E793DBAF46BD391537140E69F6B447E17C4CAD6830C49C0DF51` | `4D2040AE358A24BB02D26DA74D5C205A27CE6EB4BE3E4015E98AB4AA06906254` |
| `12_curva_suficiencia_amostral_ictiofauna.png` | `6358E8004331CA24569DBECE4D9D37944856CCD2AC341BF31FFCF9C0C30EB5B4` | `E61C0540CFEA0DC089D129C68CCF3ACB4EEC01F7830AFE1FEE85B0B2933A412F` |

Pasta revisada:
`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/abril/_revisoes/R01_curva_suficiencia_20260707`

## Validadores

- leitura da planilha original `12_df_curva_suficiencia_ictiofauna.xlsx`;
- comparacao com planilhas por ponto (`02`, `03` e `06`), que possuem 13 pontos;
- inspecao do runner `scripts/projects/avg/run_ictio_avg_abril_maio.py`;
- validacao apos regeneracao:
  - `n_amostras` final = 13;
  - riqueza observada final = 4,0;
  - riqueza estimada Jackknife 1 final = 7,69;
  - PNG abre via PIL;
  - XLSX abre via openpyxl;
  - hashes revisados registrados.
- auditoria de coordenadas:
  - antes: nao aplicavel;
  - depois: nao aplicavel;
  - divergencias remanescentes: nao aplicavel.

## Gate R

- status: `approved`
- apresentado em: 2026-07-07
- aprovado em: 2026-07-07
- registro da aprovacao: usuario disse "ok substituir"; arquivos revisados foram promovidos para a pasta oficial.

## Aprendizados E Pendencias

- produtos de suficiencia amostral devem receber unidades amostrais com esforco
  e captura zero quando o produto representar campanha/pontos de monitoramento;
- avaliar, em revisao separada se solicitado, se maio e junho tambem precisam
  de reemissao da curva de suficiencia.
