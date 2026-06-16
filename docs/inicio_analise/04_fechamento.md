# Fechamento Da Analise

Antes de considerar uma analise concluida, executar este fechamento.

## Lastro Tecnico

- [ ] Outputs finais gerados na pasta do cliente.
- [ ] `execution_metadata.json` ou registro equivalente salvo.
- [ ] Reprodutor ou recipe salvo.
- [ ] Scripts usados identificados.
- [ ] Inputs principais registrados.
- [ ] Decisoes metodologicas documentadas.

## Aprendizado

- [ ] Atualizar dossie em `docs/projects/`.
- [ ] Atualizar `project_registry.json` se houver novo lastro.
- [ ] Atualizar `pattern_registry.json` se houver padrao reutilizavel.
- [ ] Atualizar `portfolio_registry.json` se houver caso de referencia.
- [ ] Atualizar backlog se houver pendencia.

## Validadores

Rodar:

```powershell
python scripts\validation\check_repo_organization.py
python scripts\validation\audit_supabase_project_coverage.py --output outputs\_runs\supabase_project_coverage_latest.json
python scripts\validation\build_knowledge_inventory.py --output outputs\_runs\knowledge_inventory_latest.json
```

Quando houver codigo Python alterado, rodar tambem:

```powershell
python -m py_compile <arquivos_alterados.py>
```

## Git

- [ ] Revisar `git status`.
- [ ] Revisar escopo do diff.
- [ ] Commitar com mensagem clara.
- [ ] Fazer push.
