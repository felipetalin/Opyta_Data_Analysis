# Instrucoes Operacionais Do Repositorio

## Gatilho Da Central De Controle

Quando o usuario mencionar `center_control`, `center_cotrol`, `control_center`,
`central de controle` ou pedir para seguir o fluxo operacional, o Codex deve:

1. abrir `docs/control_center/README.md`;
2. seguir `docs/control_center/WORKFLOW.md` na ordem definida;
3. consultar `docs/control_center/ACTIVE_OPERATIONS.md`;
4. localizar ou criar o registro da operacao em
   `docs/control_center/operations/`;
5. consultar o registry, o dossie, a recipe e os lastros do projeto;
6. atualizar o estado da operacao conforme o trabalho avanca;
7. parar nos portoes que exigem aprovacao explicita do usuario.

Nao e permitido pular diretamente para migracao, consolidacao ou geracao de
produtos quando um gate anterior ainda estiver pendente. Uma aprovacao pode ser
aproveitada da propria solicitacao do usuario quando estiver expressa de forma
clara e registrada no documento da operacao.

O fluxo oficial e:

`validacao -> aprovacao dos dados -> cadastro e auditoria de especies ->
aprovacao taxonomica -> migracao -> consolidacao -> configuracao das analises ->
aprovacao de template/paleta/saida -> geracao -> revisao -> fechamento`
