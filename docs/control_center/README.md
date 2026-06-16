# Control Center

Painel principal da base tecnica Opyta Analysis.

## Status Atual

| Area | Estado | Onde acessar |
| --- | --- | --- |
| Inicio de analise | Ativo | [../inicio_analise](../inicio_analise) |
| Projetos | Em consolidacao | [PROJECTS.md](PROJECTS.md) |
| Portfolio | Primeira curadoria criada | [PORTFOLIO.md](PORTFOLIO.md) |
| Portfolio de analises | Ativo | [../portfolio_analises](../portfolio_analises) |
| Patterns | Ativos + legado Gold preservado | [../patterns](../patterns) |
| Registries | JSON versionados | [../registry](../registry) |
| Templates | Base inicial criada | [../templates](../templates) |
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

- **Projetos**: identidade Supabase, status, recipes, scripts e outputs.
- **Portfolio**: modelos aprovados por tipo de entrega ou estudo.
- **Patterns**: componentes tecnicos reutilizaveis.
- **Learning**: decisoes, erros, limitacoes e melhorias.
- **Backlog**: o que precisa virar pipeline, template ou deprecated.

## Fluxo Diario

1. Abrir [Inicio de analise](../inicio_analise/README.md) quando o trabalho for novo.
2. Consultar o projeto em [PROJECTS.md](PROJECTS.md).
3. Decidir tipo de analise em [Portfolio de analises](../portfolio_analises/README.md).
4. Conferir portfolio/patterns antes de criar novo grafico.
5. Registrar decisao nova usando `docs/templates/decision_record_template.md`.
6. Se algo funcionou bem, promover para portfolio ou pattern.
7. Rodar os validadores antes de fechar.

## Comandos

```powershell
python scripts\validation\check_repo_organization.py
python scripts\validation\audit_supabase_project_coverage.py
python scripts\validation\build_knowledge_inventory.py --output outputs\_runs\knowledge_inventory_latest.json
```
