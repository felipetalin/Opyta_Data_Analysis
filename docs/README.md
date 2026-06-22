# Opyta Analysis — Central De Controle E Memoria Tecnica

Esta pasta e a entrada principal para a memoria tecnica da Opyta Analysis.

Para iniciar ou retomar uma operacao, use `center_control` e abra:

1. [Central de Controle](control_center/README.md)
2. [Fluxo operacional](control_center/WORKFLOW.md)
3. [Operacoes ativas](control_center/ACTIVE_OPERATIONS.md)

O nome fisico da pasta continua sendo `docs` porque ela tambem guarda dossies,
registries, patterns, templates e referencias tecnicas.

## Documento Mestre

- [Padrao Mestre de Redacao Tecnica Opyta](PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md):
  policy editorial evolutiva que governa a geracao automatica e assistida dos
  relatorios tecnicos apos a conclusao das analises.

## Central De Controle

- [Central de Controle](control_center/README.md): entrada operacional oficial.
- [Fluxo operacional](control_center/WORKFLOW.md): validacao, gates, migracao,
  consolidacao, configuracao, geracao e fechamento.
- [Operacoes ativas](control_center/ACTIVE_OPERATIONS.md): estado atual e proxima acao.
- [Inicio de analise](inicio_analise/README.md): modulo de abertura e decisao
  analitica usado dentro do fluxo oficial.
- [Modelo operacional](control_center/OPERATING_MODEL.md): como um projeto nasce,
  aprende e vira referencia.
- [Padrao de nomes](control_center/NAMING_STANDARD.md): regra `SIGLA__nome_supabase`.
- [Projetos](control_center/PROJECTS.md): projetos, status, recipes, scripts e lastro.
- [Portfolio](control_center/PORTFOLIO.md): modelos aprovados por tipo de estudo.
- [Sistema de aprendizado](control_center/LEARNING_SYSTEM.md): como capturar decisoes.
- [Registros historicos](control_center/LEGACY_REGISTERS.md): docs antigos preservados.
- [Backlog](control_center/BACKLOG.md): proximas rodadas de organizacao.
- [Portfolio de analises](portfolio_analises/README.md): matriz de decisao para escolher modulos e graficos.

## Registros

- [Project registry](registry/project_registry.json)
- [Pattern registry](registry/pattern_registry.json)
- [Portfolio registry](registry/portfolio_registry.json)

## Templates

- [Registro de operacao](templates/operation_record_template.md)
- [Dossie de projeto](templates/project_dossier_template.md)
- [Card de padrao](templates/pattern_card_template.md)
- [Registro de decisao](templates/decision_record_template.md)
- [Caso de portfolio](templates/portfolio_case_template.md)

## Comandos De Controle

```powershell
python scripts\validation\check_repo_organization.py
python scripts\validation\audit_supabase_project_coverage.py
python scripts\validation\build_knowledge_inventory.py --output outputs\_runs\knowledge_inventory_latest.json
```

## Regra Pratica

Todo projeto novo deve:

- comecar por [Inicio de analise](inicio_analise/README.md);
- usar a identidade oficial do Supabase;
- ter `canonical_key` no formato `SIGLA__nome_supabase_slug`;
- registrar entendimento tecnico e aprendizados;
- apontar para recipe, scripts, outputs e lastro;
- atualizar portfolio/patterns quando gerar algo reaproveitavel.
