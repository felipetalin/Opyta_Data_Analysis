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
[operacoes ativas](ACTIVE_OPERATIONS.md) e respeitar os tres portoes de
aprovacao do usuario.

## Status Atual

| Area | Estado | Onde acessar |
| --- | --- | --- |
| Fluxo operacional | Oficial | [WORKFLOW.md](WORKFLOW.md) |
| Operacoes ativas | Ativo | [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md) |
| Registros por execucao | Ativo | [operations](operations/README.md) |
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

## Portoes Obrigatorios

| Gate | Confirmacao do usuario |
| --- | --- |
| A | Dados validados e ajustes aceitos. |
| B | Cadastro e atributos das especies aceitos. |
| C | Template, paleta, pasta de saida e produtos aceitos. |

O trabalho pode avancar automaticamente dentro de uma etapa, mas deve parar
quando chegar a um gate ainda nao aprovado.

## Ordem De Consulta

1. [WORKFLOW.md](WORKFLOW.md)
2. [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md)
3. registro da operacao em [operations](operations/README.md)
4. [PROJECTS.md](PROJECTS.md) e registry
5. dossie, recipe e lastro
6. portfolio e patterns aplicaveis
7. validadores e fechamento

## Comandos

```powershell
python scripts\validation\check_repo_organization.py
python scripts\validation\audit_supabase_project_coverage.py
python scripts\validation\build_knowledge_inventory.py --output outputs\_runs\knowledge_inventory_latest.json
```
