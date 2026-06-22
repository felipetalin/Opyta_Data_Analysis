# Organizacao Do Repositorio

## Objetivo

Evitar perda de historico tecnico conforme o numero de projetos cresce. A
organizacao deve permitir localizar rapidamente:

- scripts de producao;
- prototipos aprovados ou rejeitados;
- paletas;
- templates graficos;
- receitas de projeto;
- outputs tecnicos e reprodutores.

## Camadas

### Codigo reutilizavel

`src/opyta_analysis/`

Toda funcao que se repete entre projetos deve viver aqui. Exemplos:

- minigraficos temporais;
- CPUE por ano;
- EPT/CHOL;
- validadores;
- exportadores;
- acesso ao Supabase.

### Configuracao

`configs/clients/` guarda estilo por cliente.

`configs/projects/` guarda receitas reprodutiveis por projeto, incluindo
campanhas, destino e decisoes visuais.

### Scripts operacionais

`scripts/` e dividido por finalidade. O catalogo oficial esta em
`scripts/SCRIPT_CATALOG.md`.

Scripts antigos movidos para subpastas podem manter wrappers temporarios na
raiz para nao quebrar documentos e comandos historicos.

### Memoria tecnica

`docs/README.md` e a entrada principal da base tecnica.

`docs/control_center/` e a Central de Controle: guarda o fluxo operacional,
operacoes ativas, gates de aprovacao, projetos, portfolio, aprendizados,
backlog e modelo operacional.

Quando `center_control`, `center_cotrol`, `control_center` ou "central de
controle" for mencionado, o caminho oficial e
`docs/control_center/README.md -> WORKFLOW.md -> ACTIVE_OPERATIONS.md ->
registro da operacao`.

`docs/registry/` guarda cadastros JSON versionados.

`docs/templates/` guarda modelos para novos dossies, patterns, decisoes e casos
de portfolio.

`docs/patterns/` guarda padroes reutilizaveis.

`docs/projects/` guarda decisoes e contexto por projeto.

### Outputs tecnicos

`outputs/_project_scripts/` continua sendo o backup automatico dos pipelines.

`outputs/_runs/` fica reservado para manifests consolidados de execucao.

`outputs/_scratch/` fica reservado para artefatos temporarios locais.

## Fluxo recomendado

1. Criar prototipo em `scripts/prototypes/`.
2. Aprovar visual/metodologia com um projeto real.
3. Promover a logica para `src/opyta_analysis/`.
4. Registrar o padrao em `docs/patterns/`.
5. Criar ou atualizar a receita em `configs/projects/`.
6. Gerar produtos finais no Drive do cliente.
7. Conferir auditoria em `outputs/_project_scripts/`.

## Proximas rodadas

1. Transformar scripts Porto Estrela/AVG/SAM em recipes ou pipelines.
2. Criar manifests consolidados em `outputs/_runs/`.
3. Reduzir gradualmente wrappers de raiz quando os documentos antigos forem atualizados.
4. Promover funcoes repetidas de scripts de projeto para `src/opyta_analysis/`.
5. Curar documentos historicos para `docs/projects`, `docs/patterns` ou portfolio.
