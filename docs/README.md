# Opyta Analysis Knowledge Hub

Esta pasta e a entrada principal para a memoria tecnica da Opyta Analysis.

## Control Center

- [Inicio de analise](inicio_analise/README.md): protocolo obrigatorio para abrir
  uma nova analise sem depender de memoria do chat.
- [Control Center](control_center/README.md): painel geral em formato SaaS.
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
