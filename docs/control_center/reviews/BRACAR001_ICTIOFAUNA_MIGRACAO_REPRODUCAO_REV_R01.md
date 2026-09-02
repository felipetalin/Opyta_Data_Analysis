# BRACAR001 — Ictiofauna — Migração inicial — Revisão R01

## Controle

- projeto: `BRACAR001`
- operacao de origem: Migração inicial
- revisao: `R01`
- estado atual: `awaiting_revision_approval`
- solicitada em: 2026-09-02
- atualizada em: 2026-09-02
- proxima acao: aprovar Gate R da correção de preservação dos dados reprodutivos

## Escopo

- solicitacao do usuario: verificar e corrigir a ausência aparente de números de EMG; deixar lastro no Gate de migração.
- tipo principal: `data`
- tipos secundarios: `analysis`
- impacto: `R3`
- produtos alvo: tabelas normalizadas e base individual para análises reprodutivas.
- fora do escopo: geração de resultados, template, paleta e produtos finais.

## Linha De Base

- fonte: `PCH_Brasil_Carangola_Ictiofauna_MIGRACAO_UNIFICADA_20260901.xlsx`, aba `Resultados_Ictiofauna`.
- banco antes: `resultados_ictiofauna` com 1.052 registros agregados e `EMG=0`; `biota_analise_consolidada` não expunha campos reprodutivos.
- backup do consolidado existente: `public.bkp_biota_analise_consolidada_pre_bracar001_20260901`.

## Dependencias E Retorno

- Gate A reaberto: nao
- Gate B reaberto: nao
- Gate C reaberto: nao
- banco afetado: sim
- coordenadas afetadas: nao
- produtos dependentes: futuras análises reprodutivas devem usar `public.resultados_ictiofauna_detalhe` filtrada por `codigo_opyta = 'BRACAR001'`.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | EMG existia na fonte, mas era perdido na agregação. |
| Triagem de tipo e impacto | concluida | `data/R3`: migração e base de análise afetadas. |
| Correcao | concluida | Criado sincronizador individual e integrado ao migrador oficial. |
| Regeneracao de dependencias | concluida | 4.458 linhas individuais inseridas em `resultados_ictiofauna_detalhe`. |
| Validacao da revisao | concluida | Totais EMG, PG e IGS conferem com a fonte. |
| Gate R — aprovacao final | aguardando aprovacao | |

## Alteracoes

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Migração agregada | EMG, sexo, PG e IGS não eram persistidos | O agregador permanece para abundância; detalhes individuais passam a ser preservados | atributos individuais não cabem no nível agregado |
| Detalhe individual | BRACAR001 sem registros | 4.458 linhas em `resultados_ictiofauna_detalhe` | permitir análise reprodutiva auditável |
| EMG | 0 no banco para BRACAR001 | 2.499 preenchidos; 2.417 numéricos | corrigir perda de dados |

## Validadores

- fonte: 4.458 linhas; EMG preenchido 2.499; EMG numérico 2.417; PG preenchido 714; IGS preenchido 4.324.
- banco após correção: 4.458 linhas de detalhe; EMG preenchido 2.499; EMG numérico 2.417; PG preenchido 714; IGS preenchido 4.324.
- distribuição EMG: classe 1 = 814; classe 2 = 552; classe 3 = 572; classe 4 = 479; `IMAT` = 42; `M` = 25; `F` = 15; vazio = 1.959.
- estádios derivados: repouso = 814; maturação inicial = 552; maturação avançada/maduro = 572; desovado/esgotado = 479.

## Gate R

- status: `pending`
- apresentado em: 2026-09-02
- aprovado em:
- registro da aprovacao:

## Aprendizados E Pendencias

- Para resultados de ictiofauna, manter `resultados_ictiofauna` como tabela agregada e `resultados_ictiofauna_detalhe` como fonte individual para reprodução.
- Valores `M`, `F` e `IMAT` em `EMG` foram preservados como texto bruto e não receberam estádio numérico; revisar apenas se houver decisão técnica específica.
