# Registros De Revisao

Esta pasta guarda rodadas de revisao vinculadas a uma operacao existente.

Cada registro deve indicar:

- projeto e operacao de origem;
- identificador da revisao (`R01`, `R02`, ...);
- linha de base preservada;
- tipo e nivel de impacto;
- gates reabertos;
- arquivos alterados e regenerados;
- validadores;
- aprovacao final no Gate R.

Use o modelo
[review_record_template.md](../../templates/review_record_template.md).

Uma observacao futura sem escopo definido permanece no registro da operacao
como `review_planned`. O arquivo de revisao deve ser criado quando houver alvo
ou pedido executavel.
