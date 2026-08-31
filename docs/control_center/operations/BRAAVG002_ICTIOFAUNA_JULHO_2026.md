# BRAAVG002 - Ictiofauna - Julho/2026

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- grupo: Ictiofauna
- operacao: validacao, migracao, consolidacao e geracao parcial da campanha `48ª-Jul-26`
- estado atual: `reviewing_outputs`
- aberta em: 2026-08-03
- atualizada em: 2026-08-03
- proxima acao: revisao visual/tecnica pelo usuario dos produtos em `Resultados ictio/2026/julho`

## Caminhos

- dados:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Migração de dados/2026/Ictiofauna/projeto_ictio_real - AVG 260625_GATEA_R01.xlsx`
- cadastro de especies: banco `public.especies`
- saida prevista:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/julho`
- dossie:
  `docs/AVG_ICTIOFAUNA_2026.md`
- recipe:
  `configs/projects/braavg002_ictiofauna_2026.json`
- runner mensal:
  `scripts/projects/avg/run_ictio_avg_2026_por_campanha.py`
- validacoes:
  `outputs/validacoes/braavg002_ictiofauna_julho_2026`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Nova campanha parcial `48ª-Jul-26` identificada na planilha `GATEA_R01`. |
| Validacao | concluida sem bloqueios | Validador oficial retornou 0 bloqueios, 3 avisos e `pode_prosseguir=true`. |
| Gate A - dados | aprovado | Usuario disse "aprovado" em 2026-08-03 apos validacao com 0 bloqueios e 3 avisos. |
| Cadastro de especies | concluido sem novas especies | As 13 especies da planilha existem em `public.especies`. |
| Gate B - especies | aprovado | Usuario disse "aprovado" em 2026-08-03; 13 especies ja existentes e sem especies novas. |
| Migracao | concluida | Migrador oficial executado; 621 esforcos e 528 resultados agregados em Ictiofauna AVG. |
| Consolidacao | concluida | Consolidador oficial executado; fatia consolidada BRAAVG002/Ictiofauna auditada com 528 linhas, 48 campanhas, 13 especies e 1.514 individuos. |
| Configuracao das analises | concluida | Alvo `julho` adicionado ao recipe `configs/projects/braavg002_ictiofauna_2026.json`. |
| Gate C - analises | aprovado | Usuario pediu gerar o parcial de julho e disse "aprovado"; template parcial, paleta AVG e pasta `2026/julho` reaproveitados do fluxo abril/maio/junho. |
| Geracao dos produtos | concluida | 31 arquivos oficiais gerados em `Resultados ictio/2026/julho`, sendo 15 PNG e 16 XLSX. |
| Revisao tecnica | concluida | 15 PNG abriram via PIL; 16 XLSX abriram via openpyxl; planilhas por ponto com 10 pontos e sem `PIC-01`, `PIC-03`, `PIC-11`. |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario disse "aprovado" em 2026-08-03; 0 bloqueios, 3 avisos recorrentes aceitos. |
| B - especies | `approved` | Usuario disse "aprovado" em 2026-08-03; 13 especies existentes; sem especies novas. |
| C - analises | `approved` | Usuario pediu gerar parcial de julho e disse "aprovado"; template/paleta/saida herdados da rodada parcial AVG. |

## Validacao Dos Dados

- arquivo: `projeto_ictio_real - AVG 260625_GATEA_R01.xlsx`
- abas: `Capa_Projeto`, `Pontos_e_Campanhas`, `Resultados_Ictiofauna`, `Metadados_Esforco`
- linhas:
  - `Pontos_e_Campanhas`: 621
  - `Metadados_Esforco`: 621
  - `Resultados_Ictiofauna`: 1369
- campanhas: 48, de `1ª-Ago-22` a `48ª-Jul-26`
- julho/2026:
  - campanha: `48ª-Jul-26`
  - pontos previstos: 10 (`PIC-02`, `PIC-04`, `PIC-05`, `PIC-06`, `PIC-07`, `PIC-08`, `PIC-09`, `PIC-10`, `PIC-12`, `PIC-13`)
  - pontos com resultado: `PIC-04`, `PIC-05`, `PIC-06`, `PIC-07`, `PIC-09`, `PIC-10`, `PIC-12`
  - linhas de resultado: 9
  - individuos: 28
- consolidado apos migracao/consolidacao:
  - linhas: 528
  - campanhas: 48
  - pontos: 13
  - especies: 13
  - individuos: 1.514
  - julho/2026: 9 linhas e 28 individuos
- relatorio:
  `outputs/validacoes/braavg002_ictiofauna_julho_2026/validacao_braavg002_ictiofauna_julho_2026_ictiofauna_20260803_gatea_julho.md`
- Excel detalhado:
  `outputs/validacoes/braavg002_ictiofauna_julho_2026/validacao_braavg002_ictiofauna_julho_2026_ictiofauna_20260803_gatea_julho.xlsx`
- JSON:
  `outputs/validacoes/braavg002_ictiofauna_julho_2026/validacao_braavg002_ictiofauna_julho_2026_ictiofauna_20260803_gatea_julho.json`

### Avisos

- `RESULT_EFFORT_VALUE_DIFFERS_FROM_METADATA`: 209 resultados possuem `Esforco_Amostral` diferente de `Metadados_Esforco`.
- `EXACT_RESULT_DUPLICATES`: 921 resultados sao duplicatas exatas; historicamente aceitas como individuos/lotes.
- `RESULT_GROUPS_WILL_BE_AGGREGATED`: 254 grupos serao agregados pelo migrador, com abundancia por soma e biometria por media.

## Cadastro E Auditoria De Especies

- especies nos resultados: 13
- especies ausentes no banco: 0
- especies novas: 0
- observacao: seguem as mesmas ressalvas de atributos ecologicos/ameaca vazios aceitas na operacao ate junho/2026.

## Observacao Operacional

- Em 2026-08-03, durante tentativa de obter ajuda do consolidador oficial, `G:/Meu Drive/Opyta/Opyta_Data/scripts/processar_dados.py --help` executou a consolidacao global porque o script nao possui modo `--help`.
- O processo terminou com sucesso, mas foi fora da etapa planejada.
- Auditoria imediata da fatia `BRAAVG002`/`Ictiofauna` em `public.biota_analise_consolidada` indicou permanencia dos totais ate junho: 519 linhas, 47 campanhas, 13 pontos, 13 especies e 1.486 individuos.

## Pendencias

- Revisao visual/tecnica pelo usuario dos produtos gerados em `Resultados ictio/2026/julho`.

## Geracao Dos Produtos

- recipe atualizado: `configs/projects/braavg002_ictiofauna_2026.json`
- comando de preflight:
  `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --preflight --campaign julho`
- preflight: `ready=true`
- pontos esperados em julho: 10
- pontos nao monitorados: `PIC-01`, `PIC-03`, `PIC-11`
- pontos com captura zero e esforco: `PIC-02`, `PIC-08`, `PIC-13`
- comando de geracao:
  `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --campaign julho`
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/julho`
- arquivos oficiais: 31
  - PNG: 15
  - XLSX: 16
- validacao de integridade:
  - PNG: 15/15 abriram via PIL
  - XLSX: 16/16 abriram via openpyxl
  - erros: 0
- validacao de malha ativa:
  - `02_df_riqueza_por_ponto_ictiofauna.xlsx`: 10 pontos; `PIC-01`, `PIC-03`, `PIC-11` ausentes
  - `03_df_abundancia_por_ponto_ictiofauna.xlsx`: 10 pontos; `PIC-01`, `PIC-03`, `PIC-11` ausentes
  - `06_df_cpue_por_ponto_ictiofauna.xlsx`: 10 pontos; `PIC-01`, `PIC-03`, `PIC-11` ausentes
