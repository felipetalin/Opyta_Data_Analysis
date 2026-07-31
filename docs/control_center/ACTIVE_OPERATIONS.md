# Operacoes Da Central De Controle

Este painel acompanha execucoes. O estado tecnico permanente dos projetos
continua em [PROJECTS.md](PROJECTS.md).

## Em Andamento Ou Revisao

| Operacao | Projeto | Grupo | Estado atual | Proxima acao | Registro |
| --- | --- | --- | --- | --- | --- |
| Migracao inicial - meio fisico | BRAAEG001 / A&G Mineracao | Meio fisico | `superficial_minimaps_generated_pending_review` | Pacote final de Agua Superficial gerado em pasta unica; minimapas Chuva/Seca de violacoes por ponto, IQA e IET gerados para revisao | [BRAAEG001_MEIO_FISICO_MIGRACAO.md](operations/BRAAEG001_MEIO_FISICO_MIGRACAO.md) |
| Migração inicial - biota aquática | BRAAEG001 / A&G Mineração | Fitoplâncton, Zooplâncton, Zoobentos e Ictiofauna | `reviewing_outputs` | Fitoplâncton R04 aprovado; Zooplâncton R01 aprovado e regenerado com validação OK; revisar pacote final de Zoobentos R01 | [BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md](operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md) |
| Revisão R01 - figuras A4 retrato | BRAAEG001 / A&G Mineração | Ictiofauna | `regenerated_pending_review` | Conferir pacote R01: 16 figuras finais A4 paisagem, relatório HTML e rótulos pt-BR revisados, auditoria 16/16 OK e manifesto atualizado | [BRAAEG001_ICTIOFAUNA_FIGURAS_A4_RETRATO_REV_R01.md](reviews/BRAAEG001_ICTIOFAUNA_FIGURAS_A4_RETRATO_REV_R01.md) |
| Revisão R01 - indicadores e rótulos | BRAAEG001 / A&G Mineração | Zoobentos | `awaiting_revision_approval` | Aprovar pacote R01 em `migracao_biota/bentos`: Oligochaeta como classe, 08/09 com itálico seletivo, 11B por ponto, BMWP por classe e EPT/CHOL em painéis separados; validação 15/15 OK | [BRAAEG001_ZOOBENTOS_AJUSTES_INDICADORES_REV_R01.md](reviews/BRAAEG001_ZOOBENTOS_AJUSTES_INDICADORES_REV_R01.md) |
| Migracao inicial - meio fisico | FERSAM001 / Sam Metais Diagnostico | Meio fisico | `awaiting_data_approval` | Aprovar Gate A dos dados validados antes da migracao | [FERSAM001_MEIO_FISICO_MIGRACAO.md](operations/FERSAM001_MEIO_FISICO_MIGRACAO.md) |
| Migracao inicial - 18 campanhas | GEOARC001 / Monitoramento Arcelor | Ictiofauna | `configuring_analysis` | Configurar template multicampanha, paleta, pasta final e produtos para Gate C | [GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md](operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md) |
| Revisao R03 - figura 10 | GEOARC001 / Monitoramento Arcelor | Ictiofauna | `awaiting_revision_approval` | Aprovar figura 10 revisada no Gate R | [GEOARC001_ICTIOFAUNA_18_CAMPANHAS_REV_R03.md](reviews/GEOARC001_ICTIOFAUNA_18_CAMPANHAS_REV_R03.md) |
| Revisao R04 - Harttia ameacadas | GEOARC001 / Monitoramento Arcelor | Ictiofauna | `awaiting_revision_approval` | Aprovar figura 14 e planilha de apoio no Gate R | [GEOARC001_ICTIOFAUNA_18_CAMPANHAS_REV_R04.md](reviews/GEOARC001_ICTIOFAUNA_18_CAMPANHAS_REV_R04.md) |
| Revisao R05 - coordenadas Geoambiental | GEOARC001 / Monitoramento Arcelor | Ictiofauna | `awaiting_revision_approval` | Aprovar comparacao antes/depois no Gate R; limpar cache/reexecutar o app Streamlit | [GEOARC001_ICTIOFAUNA_COORDENADAS_GEOAMBIENTAL_REV_R05.md](reviews/GEOARC001_ICTIOFAUNA_COORDENADAS_GEOAMBIENTAL_REV_R05.md) |
| Revisao R01 - coordenadas | DUCGEO001 / Monitoramento Ducal | Ictiofauna e Zoobentos | `awaiting_revision_approval` | Aprovar comparacao antes/depois no Gate R; limpar cache/reexecutar o app Streamlit | [DUCGEO001_BIOTA_AQUATICA_COORDENADAS_REV_R01.md](reviews/DUCGEO001_BIOTA_AQUATICA_COORDENADAS_REV_R01.md) |
| Campanha 1 | VIRITA001 / Itabrita | Ictiofauna | `awaiting_revision_approval` | Aprovar revisoes R01 e R02 no Gate R | [VIRITA001_ICTIOFAUNA_CAMPANHA_1.md](operations/VIRITA001_ICTIOFAUNA_CAMPANHA_1.md) |
| Revisao R01 — 44ª-Mar-26 | BRAAVG002 / Brumado AVG | Zoobentos | `awaiting_revision_approval` | Aprovar Excel e figura EPT/CHOL revisados no Gate R | [BRAAVG002_ZOOBENTOS_MARCO_2026_REV_R01.md](reviews/BRAAVG002_ZOOBENTOS_MARCO_2026_REV_R01.md) |
| Consolidado 2026 - migracao 47 campanhas | BRAAVG002 / Brumado AVG | Zoobentos | `generated_after_approval` | Conferir pacote final regenerado em `Resultados bentos/Consolidado_2026`; produtos, Excel e Darwin Core atualizados | [BRAAVG002_ZOOBENTOS_CONSOLIDADO_2026.md](operations/BRAAVG002_ZOOBENTOS_CONSOLIDADO_2026.md) |
| Preparacao de geracao - resultados 2026 | BRAAVG002 / Brumado AVG | Ictiofauna | `generated_pending_review` | Revisar pacote consolidado `Consolidado_2026/icitiofauna` com tradicionais C001-C047 em pranchas A4 aprovadas + GEOARC001; KML padrao usado provisoriamente e KML Atual fica como ajuste futuro | [BRAAVG002_ICTIOFAUNA_GERACAO_RESULTADOS_2026.md](operations/BRAAVG002_ICTIOFAUNA_GERACAO_RESULTADOS_2026.md) |

## Como Atualizar

1. Criar um registro a partir de
   [operation_record_template.md](../templates/operation_record_template.md).
2. Incluir a operacao neste painel.
3. Atualizar o estado depois de cada etapa ou gate.
4. Ao concluir, mover a linha para "Concluidas" sem apagar o registro.

Para revisoes, seguir [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md) e criar o
registro em [reviews](reviews/README.md) quando houver escopo executavel.

## Concluidas

| Operacao | Projeto | Grupo | Estado final | Concluida em | Registro |
| --- | --- | --- | --- | --- | --- |
| Contencao de contexto LLM | Sistema Opyta / Central de Controle | Governanca operacional | `completed` | 2026-07-07 | [SISTEMA_CONTEXT_GUARDRAILS_LLM.md](operations/SISTEMA_CONTEXT_GUARDRAILS_LLM.md) |
| Migracao ate junho/2026 | BRAAVG002 / Brumado AVG | Ictiofauna | `completed` | 2026-07-01 | [BRAAVG002_ICTIOFAUNA_JUNHO_2026.md](operations/BRAAVG002_ICTIOFAUNA_JUNHO_2026.md) |
| Revisao R01 - 45a-Abr-26 | BRAAVG002 / Brumado AVG | Ictiofauna | `review_completed` | 2026-07-07 | [BRAAVG002_ICTIOFAUNA_ABRIL_2026_REV_R01.md](reviews/BRAAVG002_ICTIOFAUNA_ABRIL_2026_REV_R01.md) |
| Revisao R02 — 42ª-Jan-26 | BRAAVG002 / Brumado AVG | Zoobentos | `review_completed` | 2026-06-22 | [BRAAVG002_ZOOBENTOS_JANEIRO_2026_REV_R02.md](reviews/BRAAVG002_ZOOBENTOS_JANEIRO_2026_REV_R02.md) |

