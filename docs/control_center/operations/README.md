# Registros De Operacao

Cada arquivo desta pasta acompanha uma rodada concreta de trabalho, por exemplo
uma campanha, migracao, consolidacao ou regeneracao analitica.

O registro de operacao nao substitui:

- o dossie tecnico em `docs/projects/`;
- a recipe em `configs/projects/`;
- o cadastro em `docs/registry/project_registry.json`;
- o lastro automatico em `outputs/_project_scripts/`.

Ele conecta esses elementos e guarda:

- estado atual;
- entradas e saidas;
- resultado de cada etapa;
- gates e aprovacoes do usuario;
- backups e auditorias;
- pendencias e proxima acao.

Use o modelo
[operation_record_template.md](../../templates/operation_record_template.md).
