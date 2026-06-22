# Registries

Registries sao cadastros versionados em JSON. Eles alimentam o Control Center e
servem como fonte local para busca rapida.

## Arquivos

- `project_registry.json`: identidade Supabase, aliases, docs, scripts e lastro.
- `pattern_registry.json`: padroes tecnicos, status e contexto de uso.
- `portfolio_registry.json`: casos aprovados ou de referencia.

O estado de uma rodada de trabalho nao deve ser gravado como status permanente
do projeto. Operacoes e gates ficam em
`docs/control_center/operations/` e aparecem no painel
`docs/control_center/ACTIVE_OPERATIONS.md`.

## Regra

Se algo deve ser encontrado no futuro, deve aparecer em algum registry.
