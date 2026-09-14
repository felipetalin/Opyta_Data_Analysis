# Registro De Riscos De Custo De Tokens

Este registro lista fragilidades que podem tornar o uso de Codex/LLM caro ou
pesado nos reposititorios OPYTA.

## Principio

O custo de LLM deve ser controlado por escopo. A LLM deve operar sobre:

- operacao ativa;
- arquivos-alvo;
- trechos filtrados de registry/dossie/recipe;
- lastros apenas quando tecnicamente necessarios.

Nao deve operar sobre repositorio inteiro, outputs, logs, historicos completos
ou artefatos gerados.

## Riscos Atuais

| Risco | Impacto | Status | Mitigacao |
| --- | --- | --- | --- |
| Workspace `Opyta_Data_Analysis` com `outputs/`, `logs/`, snapshots e lastros tecnicos | Muito alto | mitigado inicialmente | `.codexignore` criado na raiz do repo. |
| Workspace `Opyta_Data` sem `.codexignore` | Alto | mitigado inicialmente | `.codexignore` criado em `G:/Meu Drive/Opyta/Opyta_Data`. |
| Central de Controle incentivava consulta ampla de registry, dossies, recipes e lastros | Alto | mitigado inicialmente | `LLM_CONTEXT_POLICY.md`, README, WORKFLOW e AGENTS atualizados. |
| Registros de operacao/revisao contem muitos caminhos para `outputs/` e `logs/` | Medio/alto | controlado por regra | Abrir outputs/logs apenas com dependencia registrada. |
| Scripts longos de projeto e pipelines grandes podem ser abertos inteiros sem necessidade | Medio | pendente | Preferir `rg`, `Select-String`, trechos e funcoes-alvo antes de abrir arquivo inteiro. |
| `docs/portfolio_analises/index.html` e artefatos visuais/documentais podem entrar como contexto | Medio | mitigado | `.codexignore` ignora `*.html`, imagens e binarios. |
| Historico de conversa longo com muitas saidas de ferramenta | Alto | operacional | Encerrar/retomar sessoes por operacao; resumir contexto antes de continuar. |
| Buscas amplas como `rg --files` ou `Get-ChildItem -Recurse` em todo o repo | Alto | controlado por regra | Politica exige buscas filtradas e exclusao de artefatos pesados. |
| Uso de dois repositorios no mesmo trabalho sem escopo claro | Alto | mitigado parcialmente | Ambos agora possuem `.codexignore`; ainda exige disciplina de workspace. |

## Regras Operacionais De Economia

1. Nao abrir repo inteiro para responder pergunta arquitetonica.
2. Nao usar `rg --files` sem pasta alvo.
3. Nao abrir `outputs/`, `logs/`, `runtime/` ou planilhas sem motivo registrado.
4. Ler registry como indice, nao como documento integral recorrente.
5. Abrir operacao, dossie e recipe somente do projeto alvo.
6. Para scripts grandes, localizar funcao/classe primeiro e abrir trechos.
7. Para revisoes, abrir somente linha de base, registro de revisao e produtos
   afetados.
8. Quando a sessao passar de uma operacao para outra, fechar contexto antigo no
   registro e recomecar pelo escopo minimo.

## Monitoramento

Depois de duas ou tres sessoes de trabalho com as novas regras, comparar novo
relatorio de uso com o relatorio de 2026-07-02.

Metricas esperadas:

- queda forte de tokens cacheados por turno;
- menos chamadas com contexto acima de centenas de milhares de tokens;
- proporcao maior de trabalho em arquivos-alvo;
- menos leitura de outputs/logs.

## Arquivos De Controle

- `.codexignore`
- `G:/Meu Drive/Opyta/Opyta_Data/.codexignore`
- `docs/control_center/LLM_CONTEXT_POLICY.md`
- `docs/control_center/operations/SISTEMA_CONTEXT_GUARDRAILS_LLM.md`
- `AGENTS.md`
