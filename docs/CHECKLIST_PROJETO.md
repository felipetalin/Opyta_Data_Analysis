# Checklist De Projeto

Use este checklist no inicio e no fechamento de cada projeto. A ideia e evitar
script solto, output perdido e padrao grafico esquecido.

## Abertura

- [ ] Registro criado em `docs/control_center/operations/`.
- [ ] Operacao incluida em `docs/control_center/ACTIVE_OPERATIONS.md`.
- [ ] Codigo do projeto definido.
- [ ] Cliente definido em `configs/clients/` quando houver paleta/tema proprio.
- [ ] Recipe criada em `configs/projects/` para execucoes reproduziveis.
- [ ] Nota tecnica criada em `docs/projects/`.
- [ ] Pasta de destino final do cliente definida.
- [ ] Grupos biologicos ou matrizes definidos.
- [ ] Recorte temporal e espacial registrado.
- [ ] Padrao visual escolhido em `docs/patterns/`.
- [ ] Scripts novos criados na subpasta correta de `scripts/`.

## Durante O Desenvolvimento

- [ ] Gates A, B e C registrados conforme `docs/control_center/WORKFLOW.md`.
- [ ] Estado e proxima acao da operacao atualizados.
- [ ] Prototipos ficam em `scripts/prototypes/`.
- [ ] Scripts especificos ficam em `scripts/projects/<projeto>/`.
- [ ] Migracoes ficam em `scripts/migrations/<tema>/`.
- [ ] Validadores ficam em `scripts/validation/`.
- [ ] Funcoes reutilizadas por mais de um projeto migram para `src/opyta_analysis/`.
- [ ] Outputs temporarios ficam em `outputs/_scratch/`.
- [ ] Backups tecnicos ficam em `outputs/_project_scripts/`.

## Fechamento

- [ ] Registro da operacao atualizado para `completed` ou pendencia explicita.
- [ ] Linha da operacao movida para "Concluidas" no painel.
- [ ] Produtos finais gerados na pasta do cliente.
- [ ] Manifests/auditorias conferidos.
- [ ] `scripts/SCRIPT_CATALOG.md` atualizado.
- [ ] Padroes novos documentados em `docs/patterns/`.
- [ ] Decisoes do projeto atualizadas em `docs/projects/`.
- [ ] Rodar:

```powershell
python scripts\validation\check_repo_organization.py
```

- [ ] Corrigir avisos relevantes antes de considerar o projeto encerrado.

## Quando Algo Sair Do Padrao

Se o validador apontar um aviso, escolher uma das opcoes:

- mover o arquivo para a pasta correta;
- transformar o script em wrapper temporario;
- registrar a excecao no catalogo;
- promover a logica para `src/opyta_analysis/`.
