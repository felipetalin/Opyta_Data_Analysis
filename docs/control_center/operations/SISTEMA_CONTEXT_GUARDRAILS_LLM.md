# SISTEMA - GOVERNANCA LLM - CONTENCAO DE CONTEXTO

## Controle

- projeto: Sistema Opyta / Central de Controle
- grupo: Governanca operacional e LLM
- operacao: Ajuste da Central de Controle para reduzir consumo de contexto
- estado atual: `completed`
- aberta em: 2026-07-07
- atualizada em: 2026-07-07
- proxima acao: monitorar proximos relatorios de uso do Codex e ajustar a
  politica se o consumo continuar anormal.

## Caminhos

- dados: nao aplicavel
- cadastro de especies: nao aplicavel
- saida: documentacao operacional
- dossie: `docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md`
- recipe: nao aplicavel
- lastro:
  - `.codexignore`
  - `G:/Meu Drive/Opyta/Opyta_Data/.codexignore`
  - `docs/control_center/LLM_CONTEXT_POLICY.md`
  - `docs/control_center/TOKEN_COST_RISK_REGISTER.md`
  - `docs/control_center/README.md`
  - `docs/control_center/WORKFLOW.md`
  - `AGENTS.md`

## Motivacao

O usuario identificou consumo anormal no relatorio
`codex-daily-workspace-usage-counts-2026-07-02.json`, com mais de 172 milhoes
de tokens contabilizados no periodo avaliado e cerca de 90% em contexto
cacheado.

A avaliacao concluiu que o problema nao era o motor analitico da OPYTA rodando
analises, mas o uso de Codex/LLM com superficie de contexto grande demais:
documentacao operacional, registros, outputs, lastros e historico sendo
facilmente carregados em excesso.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Usuario autorizou seguir com ajustes no `center_control`. |
| Validacao | concluida | README, WORKFLOW, ACTIVE_OPERATIONS, registry e decision record foram consultados. |
| Gate A - dados | nao aplicavel | Nao ha base de dados ou migracao nesta operacao. |
| Cadastro de especies | nao aplicavel | Nao ha taxonomia nesta operacao. |
| Auditoria de atributos | nao aplicavel | Nao ha especies nesta operacao. |
| Gate B - especies | nao aplicavel | Nao ha aprovacao taxonomica nesta operacao. |
| Migracao | nao aplicavel | Nenhuma migracao executada. |
| Consolidacao | nao aplicavel | Nenhuma consolidacao executada. |
| Configuracao das analises | nao aplicavel | Nenhuma analise configurada. |
| Gate C - analises | nao aplicavel | Sem geracao de produtos analiticos. |
| Geracao dos produtos | concluida | Politica de contexto e ajustes documentais criados. |
| Revisao tecnica | concluida | Arquivos revisados apos edicao. |
| Revisao de layout | nao aplicavel | Sem produto visual. |
| Fechamento | concluida | Operacao registrada e painel atualizado. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `not_applicable` | Operacao de governanca sem dados externos. |
| B - especies | `not_applicable` | Operacao sem taxonomia. |
| C - analises | `not_applicable` | Operacao sem produtos analiticos. |

## Ajustes Aplicados

- Criado `.codexignore` na raiz do repositorio para excluir outputs, logs,
  ambientes virtuais, caches e artefatos pesados do contexto padrao do Codex.
- Criada `docs/control_center/LLM_CONTEXT_POLICY.md`.
- Atualizado `docs/control_center/README.md` para expor a politica de contexto.
- Atualizado `docs/control_center/WORKFLOW.md` para incluir a politica na ordem
  obrigatoria de consulta e limitar abertura de arquivos.
- Atualizado `AGENTS.md` para que futuras sessoes de Codex respeitem a politica.
- Atualizado `docs/control_center/ACTIVE_OPERATIONS.md` com esta operacao
  concluida.
- Criado `.codexignore` tambem no repositorio `G:/Meu Drive/Opyta/Opyta_Data`,
  que era uma fragilidade relevante por conter `runtime/`, `.venv/`,
  `analises_raw/` e scripts historicos de analise.
- Criado `docs/control_center/TOKEN_COST_RISK_REGISTER.md` para registrar riscos
  conhecidos de custo de tokens e mitigacoes.

## Pendencias

- Auditar proximos relatorios de consumo apos duas ou tres sessoes de trabalho.
- Criar, futuramente, validador automatico para detectar buscas amplas em
  `outputs/`, `logs/` e artefatos pesados.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: nao executados; alteracao documental e de contexto.
- manifesto: este registro operacional.
- patterns: politica de contexto para LLM criada.
- portfolio: nao aplicavel.
- backlog: monitorar consumo e evoluir `opyta_ops` antes de abrir a LLM para
  execucao operacional.
