# Protocolo Codex

Este arquivo e uma instrucao operacional para futuras conversas.

## Gatilho

Se o usuario disser algo como:

- "center_control";
- "center_cotrol";
- "central de controle";
- "use a pasta inicio_analise";
- "vamos comecar uma analise";
- "seguir o fluxo de inicio de analise";
- "abra o protocolo de nova analise";
- "use o sistema de lastro";

o Codex deve abrir primeiro `docs/control_center/README.md`, seguir
`docs/control_center/WORKFLOW.md` e usar esta pasta na etapa de configuracao das
analises.

## Primeira Resposta Esperada

Confirmar que o fluxo sera seguido e iniciar a coleta de contexto local.

Exemplo:

```text
Vou seguir o fluxo de docs/inicio_analise: primeiro confiro identidade Supabase/registry,
dossie, recipe, portfolio e lastro existente; depois alinhamos produtos antes de gerar analises.
```

## Ordem De Trabalho

1. Conferir `docs/control_center/ACTIVE_OPERATIONS.md`.
2. Localizar ou criar o registro da operacao.
3. Consultar `docs/registry/project_registry.json`.
4. Conferir `docs/control_center/PROJECTS.md`.
5. Localizar ou criar dossie em `docs/projects/`.
6. Consultar `docs/portfolio_analises` para decidir o tipo de analise.
7. Localizar ou criar recipe em `configs/projects/`.
8. Consultar `docs/registry/pattern_registry.json` e `docs/registry/portfolio_registry.json`.
9. Conferir lastro em `outputs/_project_scripts/<canonical_key>`.
10. Propor template, paleta, outputs finais e pasta no Drive do cliente.
11. Registrar a aprovacao do Gate C.
12. So gerar analises depois do alinhamento metodologico.

## Regras De Cuidado

- Nao criar novo nome interno se o Supabase ja tiver codigo e nome oficial.
- Nao usar `project_165`, `project_62` ou aliases antigos como pasta nova de lastro.
- Nao tratar exemplo historico como padrao aprovado sem verificar o portfolio/patterns.
- Nao gerar graficos finais antes de definir recorte temporal, recorte espacial, grupo biologico e destino.
- Registrar todo aprendizado novo no dossie, portfolio, pattern ou backlog.

## Saida Minima Antes Da Execucao

Antes de rodar analises, deixar claro:

- projeto e `canonical_key`;
- dados de entrada;
- periodo e pontos considerados;
- grupos biologicos/matrizes;
- tipo de analise escolhido e justificativa;
- produtos esperados;
- padroes graficos reaproveitados;
- pasta final de entrega;
- pasta de lastro tecnico.
