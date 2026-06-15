# Scripts

Esta pasta guarda comandos operacionais. Codigo reutilizavel deve migrar para
`src/opyta_analysis`; aqui ficam apenas orquestradores, migracoes, prototipos e
rotinas de manutencao.

## Subpastas

- `run/`: entrypoints estaveis e runners multiempreendimento.
- `projects/`: scripts especificos de projetos ou clientes que ainda nao viraram
  pipeline/recipe reutilizavel.
- `migrations/`: migracoes e cargas controladas.
- `maintenance/`: correcoes pontuais, auditorias e operacoes de banco.
- `validation/`: validadores e auditorias pos-processamento.
- `prototypes/`: experimentos visuais ou metodologicos que ainda nao viraram
  padrao de pipeline.
- `legacy/`: scripts antigos mantidos para consulta.

## Compatibilidade

Alguns scripts movidos mantem wrappers temporarios na raiz de `scripts/`.
Esses wrappers chamam o novo caminho via `scripts/_compat.py` e preservam
comandos/documentos antigos durante a transicao.

Novos documentos devem apontar sempre para o caminho organizado, nao para o
wrapper.

## Catalogo

Use `scripts/SCRIPT_CATALOG.md` como indice principal. Sempre que um script novo
for criado, registre:

- categoria;
- projeto ou cliente;
- status (`prototipo`, `producao`, `manutencao`, `legado`);
- output esperado;
- se a logica ja foi promovida para `src/opyta_analysis`.
