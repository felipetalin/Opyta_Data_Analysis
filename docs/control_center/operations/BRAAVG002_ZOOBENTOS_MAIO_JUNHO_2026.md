# BRAAVG002 — Zoobentos — Resultados mensais maio e junho/2026

## Controle

- projeto: BRAAVG002 / Monitoramento de ictio e bentos - Brumado - AVG
- grupo: Zoobentos
- operacao: geracao mensal dos resultados 46ª-Mai-26 e 47ª-Jun-26
- estado atual: `completed`
- aberta em: 2026-08-03
- atualizada em: 2026-08-03
- proxima acao: revisao visual pelo usuario, se necessario

## Caminhos

- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026`
- maio: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/maio-26`
- junho: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/junho-26`
- script mensal: `scripts/projects/avg/run_bentos_avg_2026_por_campanha.py`
- resumo: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/2026/metadata_resultados_zoobentos_maio_junho_2026.json`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Solicitada geracao mensal de maio e junho/2026, apos abril/2026. |
| Validacao | concluida | Base atual de Zoobentos confirmada com 47 campanhas, incluindo `46ª-Mai-26` e `47ª-Jun-26`. |
| Gate A — dados | reaproveitado | Dados ja migrados/consolidados na operacao BRAAVG002_ZOOBENTOS_CONSOLIDADO_2026. |
| Gate B — especies | reaproveitado | Taxonomia e BMWP ja aprovados/aplicados na operacao consolidada. |
| Gate C — analises | reaproveitado | Template mensal por campanha ja usado para Fev/Mar/Abr 2026. |
| Geracao dos produtos | concluida | Pastas `maio-26` e `junho-26` geradas em 2026-08-03. |
| Revisao tecnica | concluida | Metadados indicam 0 arquivos faltantes em Maio e Junho; regra de pontos nao monitorados aplicada. |
| Fechamento | concluido | Registro criado na Central de Controle. |

## Regra De Vigencia Amostral Aplicada

- Malha original: 13 pontos amostrais ate outubro/2025.
- A partir de novembro/2025 (`C040`), `PIC-01`, `PIC-03` e `PIC-11` deixaram de ser amostrados por restricoes de acesso; `PIC-02` tambem ficou pendente durante a tentativa de realocacao.
- Em fevereiro/2026 (`C043`), `PIC-02` e `PIC-03` foram amostrados de forma excepcional.
- A partir de marco/2026 (`C044`), apenas a realocacao de `PIC-02` foi consolidada.
- Portanto, de marco/2026 em diante a malha ativa das analises mensais passa a ter 10 pontos: `PIC-02`, `PIC-04`, `PIC-05`, `PIC-06`, `PIC-07`, `PIC-08`, `PIC-09`, `PIC-10`, `PIC-12` e `PIC-13`.
- `PIC-01`, `PIC-03` e `PIC-11` devem ser tratados como nao monitorados/lacuna, nunca como zero analitico, nas campanhas a partir de marco/2026.

## Validacao Da Geracao

- Maio/2026 (`46ª-Mai-26`):
  - pontos ativos: 10
  - pontos nao monitorados: `PIC-01`, `PIC-03`, `PIC-11`
  - registros monitorados: 91
  - taxons: 31
  - abundancia total: 482
  - arquivos listados no metadata: 28
  - arquivos faltantes: 0
  - pontos monitorados sem resultado: nenhum
- Junho/2026 (`47ª-Jun-26`):
  - pontos ativos: 10
  - pontos nao monitorados: `PIC-01`, `PIC-03`, `PIC-11`
  - registros monitorados: 78
  - taxons: 26
  - abundancia total: 391
  - arquivos listados no metadata: 26
  - arquivos faltantes: 0
  - pontos monitorados sem resultado: `PIC-06`
- Conferencia das planilhas `02_df_riqueza_por_ponto_zoobentos.xlsx`, `03_df_abundancia_por_ponto_zoobentos.xlsx` e `10_df_diversidade_alfa_zoobentos.xlsx`:
  - Maio/2026: `PIC-01`, `PIC-03` e `PIC-11` ausentes das analises por ponto.
  - Junho/2026: `PIC-01`, `PIC-03` e `PIC-11` ausentes das analises por ponto.

## Observacao Operacional

- O script mensal escreve por padrao o resumo `metadata_resultados_zoobentos_fev_mar_abr_2026.json`.
- Durante a execucao temporaria de Maio/Junho esse resumo foi sobrescrito pelo comportamento fixo do script.
- O resumo Fev/Mar/Abr foi restaurado a partir dos metadados individuais das pastas `Fevereir-26`, `marco-26` e `abril-26`.
- O resumo especifico Maio/Junho foi salvo em `metadata_resultados_zoobentos_maio_junho_2026.json`.
- Em 2026-08-03, o script mensal foi corrigido para reaproveitar a regra de vigencia do consolidado:
  - `PIC-01`: nao monitorado de `C040` em diante.
  - `PIC-02`: nao monitorado de `C040` a `C042`; realocado/monitorado a partir de `C043`.
  - `PIC-03`: nao monitorado de `C040` a `C042`, monitorado excepcionalmente em `C043`, e nao monitorado de `C044` em diante.
  - `PIC-11`: nao monitorado de `C040` em diante.
- As pastas `maio-26` e `junho-26` foram regeneradas apos essa correcao.

## Pendencias

- Revisao visual pelo usuario, se desejar.
