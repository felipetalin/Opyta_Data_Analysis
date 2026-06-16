# Protocolo Codex

Este arquivo e uma instrucao operacional para futuras conversas.

## Gatilho

Se o usuario disser algo como:

- "use a pasta inicio_analise";
- "vamos comecar uma analise";
- "seguir o fluxo de inicio de analise";
- "abra o protocolo de nova analise";
- "use o sistema de lastro";

o Codex deve abrir esta pasta e seguir o checklist antes de implementar.

## Primeira Resposta Esperada

Confirmar que o fluxo sera seguido e iniciar a coleta de contexto local.

Exemplo:

```text
Vou seguir o fluxo de docs/inicio_analise: primeiro confiro identidade Supabase/registry,
dossie, recipe, portfolio e lastro existente; depois alinhamos produtos antes de gerar analises.
```

## Ordem De Trabalho

1. Consultar `docs/registry/project_registry.json`.
2. Conferir `docs/control_center/PROJECTS.md`.
3. Localizar ou criar dossie em `docs/projects/`.
4. Consultar `docs/portfolio_analises` para decidir o tipo de analise.
5. Localizar ou criar recipe em `configs/projects/`.
6. Consultar `docs/registry/pattern_registry.json` e `docs/registry/portfolio_registry.json`.
7. Conferir lastro em `outputs/_project_scripts/<canonical_key>`.
8. Definir outputs finais no Drive do cliente.
9. So gerar analises depois do alinhamento metodologico.

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
