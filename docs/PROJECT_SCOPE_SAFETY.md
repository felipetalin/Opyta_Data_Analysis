# Seguranca de escopo por projeto

Data: 2026-06-01

## Aprendizado registrado

A view `biota_analise_consolidada` pode nao expor a coluna `id_projeto`.
Quando isso acontece, um pipeline que filtra apenas por `grupo_biologico`
pode carregar registros de todos os projetos daquele grupo.

O caso que motivou a regra foi o projeto Ducal:

- codigo interno Opyta: `DUCGEO001`
- id no banco: `183`
- projeto: `Monitoramento Ducal`
- grupo: `Ictiofauna`

Ao executar resultados de ictiofauna, o carregamento deve confirmar que os
dados retornados pertencem somente ao projeto esperado. Para Ducal, a
conferencia minima esperada e:

- `codigo_interno_opyta`: somente `DUCGEO001`
- campanhas: 5
- pontos: 5
- especies: 11
- registros consolidados: 69
- individuos: 404

## Regra operacional

Pipelines que usam views consolidadas sem `id_projeto` devem falhar fechado.
Ou seja: se nao existir fallback de escopo cadastrado para o `project_id`,
o pipeline deve interromper a execucao e pedir cadastro do identificador do
projeto, em vez de retornar dados sem filtro.

Fallbacks aceitos, em ordem de preferencia:

1. `codigo_interno_opyta` exato.
2. Combinacao de `nome_empresa` e `nome_projeto` normalizados.
3. Validacao final de unicidade do escopo retornado.

## Implementacao atual

No pipeline de `ictio`, `project_id=183` esta amarrado a
`codigo_interno_opyta=DUCGEO001`, e o carregamento valida o escopo antes de
gerar qualquer arquivo.

Novos projetos sem `id_projeto` na view devem ser cadastrados explicitamente
em `PROJECT_FALLBACK_HINTS` e, se houver codigo interno, em `PROJECT_CODE_BY_ID`
no carregador do pipeline correspondente.
