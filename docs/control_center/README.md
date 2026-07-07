# Central De Controle

Painel principal da operacao tecnica Opyta Analysis.

Esta pasta e chamada de **Central de Controle**. O caminho fisico permanece
`docs/control_center` para preservar links, scripts e compatibilidade com o
repositorio.

## Como Acionar

Os seguintes termos acionam o protocolo completo:

- `center_control`
- `center_cotrol`
- `control_center`
- `central de controle`

Quando acionada, a execucao deve comecar pelo
[fluxo operacional](WORKFLOW.md), consultar as
[operacoes ativas](ACTIVE_OPERATIONS.md) e respeitar os gates aplicaveis de
aprovacao do usuario.

## Status Atual

| Area | Estado | Onde acessar |
| --- | --- | --- |
| Fluxo operacional | Oficial | [WORKFLOW.md](WORKFLOW.md) |
| Politica de contexto LLM | Oficial | [LLM_CONTEXT_POLICY.md](LLM_CONTEXT_POLICY.md) |
| Riscos de custo de tokens | Ativo | [TOKEN_COST_RISK_REGISTER.md](TOKEN_COST_RISK_REGISTER.md) |
| Fluxo de meio fisico | Ativo | [MEIO_FISICO_WORKFLOW.md](MEIO_FISICO_WORKFLOW.md) |
| Fluxo de revisao | Oficial | [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md) |
| Operacoes ativas | Ativo | [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md) |
| Registros por execucao | Ativo | [operations](operations/README.md) |
| Registros de revisao | Ativo | [reviews](reviews/README.md) |
| Inicio de analise | Ativo | [../inicio_analise](../inicio_analise) |
| Projetos | Em consolidacao | [PROJECTS.md](PROJECTS.md) |
| Portfolio | Primeira curadoria criada | [PORTFOLIO.md](PORTFOLIO.md) |
| Portfolio de analises | Ativo | [../portfolio_analises](../portfolio_analises) |
| Patterns | Ativos + legado Gold preservado | [../patterns](../patterns) |
| Registries | JSON versionados | [../registry](../registry) |
| Templates | Base inicial criada | [../templates](../templates) |
| Policy textual | Documento mestre evolutivo | [../PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md](../PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md) |
| Lastro | Mantido em docs e outputs tecnicos | [LEGACY_REGISTERS.md](LEGACY_REGISTERS.md) |
| Controle automatico | Ativo | `scripts/validation` |

## Acessos

| Ambiente | Local |
| --- | --- |
| Workspace local | `g:/Meu Drive/Opyta/Opyta_Data_Analysis` |
| GitHub | `https://github.com/felipetalin/Opyta_Data_Analysis` |
| Lastro tecnico local | `outputs/_project_scripts` |
| Inventarios locais | `outputs/_runs` |

## Navegacao SaaS

Pense nesta pasta como a tela inicial de um produto interno:

- **Operacoes**: etapa atual, gates, evidencias, pendencias e proxima acao.
- **Projetos**: identidade Supabase, status, recipes, scripts e outputs.
- **Portfolio**: modelos aprovados por tipo de entrega ou estudo.
- **Patterns**: componentes tecnicos reutilizaveis.
- **Learning**: decisoes, erros, limitacoes e melhorias.
- **Backlog**: o que precisa virar pipeline, template ou deprecated.

## Fluxo Oficial

`validacao -> aprovacao dos dados -> cadastro e auditoria de especies ->
aprovacao taxonomica -> migracao -> consolidacao -> configuracao das analises ->
aprovacao de template/paleta/saida -> geracao -> revisao -> fechamento`

Os detalhes, estados e evidencias obrigatorias estao em
[WORKFLOW.md](WORKFLOW.md).

## Regra De Contexto Para LLM

Ao usar Codex ou outra LLM, a Central de Controle deve ser carregada em modo de
contexto minimo.

Sempre consultar [LLM_CONTEXT_POLICY.md](LLM_CONTEXT_POLICY.md) antes de abrir
dossies, reviews, lastros, outputs ou arquivos historicos. A operacao alvo deve
guiar quais arquivos adicionais entram no contexto.

Por padrao, nao abrir `outputs/`, `logs/`, todos os registros de operacao,
todos os reviews, planilhas, imagens, HTMLs, PDFs ou snapshots. Esses itens so
entram quando houver dependencia tecnica registrada.

## Portoes Obrigatorios

| Gate | Confirmacao do usuario |
| --- | --- |
| A | Dados validados, coordenadas auditadas e ajustes aceitos. |
| B | Cadastro e atributos das especies aceitos. |
| C | Template, paleta, pasta de saida e produtos aceitos. |
| R | Pacote revisado aceito depois da comparacao antes/depois. |

O trabalho pode avancar automaticamente dentro de uma etapa, mas deve parar
quando chegar a um gate ainda nao aprovado.

## Quando For Revisao

Use [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md). A revisao comeca pela linha de
base e por uma triagem de impacto:

- texto/layout sem alterar resultados: revisar apenas produtos dependentes;
- metodo/calculo: regenerar a cadeia analitica afetada;
- dados/coordenadas/taxonomia: reabrir Gate A ou B e repetir as etapas posteriores;
- toda revisao termina no Gate R.

## Ordem De Consulta

1. [WORKFLOW.md](WORKFLOW.md)
2. [LLM_CONTEXT_POLICY.md](LLM_CONTEXT_POLICY.md), quando houver LLM/Codex
3. [MEIO_FISICO_WORKFLOW.md](MEIO_FISICO_WORKFLOW.md), quando for meio fisico
4. [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md), quando for revisao
5. [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md)
6. registro da operacao em [operations](operations/README.md)
7. registro da revisao em [reviews](reviews/README.md), quando aplicavel
8. [PROJECTS.md](PROJECTS.md) e registry filtrado pelo projeto
9. dossie, recipe e lastro somente quando aplicaveis a operacao
10. portfolio e patterns aplicaveis
11. validadores e fechamento

## Comandos

```powershell
python scripts\validation\check_repo_organization.py
python scripts\validation\audit_supabase_project_coverage.py
python scripts\validation\build_knowledge_inventory.py --output outputs\_runs\knowledge_inventory_latest.json
```
