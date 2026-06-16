# Checklist De Nova Analise

Use este checklist no inicio de qualquer projeto ou nova rodada analitica.

## 1. Identidade Do Projeto

- [ ] Consultar Supabase.
- [ ] Confirmar `id_projeto`.
- [ ] Confirmar `codigo_interno_opyta`.
- [ ] Confirmar `nome_projeto`.
- [ ] Definir `canonical_key` no formato `SIGLA__nome_supabase_slug`.
- [ ] Verificar se o projeto ja existe em `docs/registry/project_registry.json`.

## 2. Entendimento Tecnico

- [ ] Objetivo da analise.
- [ ] Grupo biologico, matriz ou tema.
- [ ] Recorte temporal.
- [ ] Recorte espacial.
- [ ] Dados de entrada.
- [ ] Pontos/campanhas removidos ou mantidos.
- [ ] Riscos conhecidos de dados, nomenclatura ou esforco amostral.

## 3. Reuso Antes De Criar

- [ ] Consultar `docs/registry/portfolio_registry.json`.
- [ ] Consultar `docs/registry/pattern_registry.json`.
- [ ] Consultar dossies similares em `docs/projects/`.
- [ ] Conferir lastros em `outputs/_project_scripts/`.
- [ ] Decidir se o caso e `approved`, `reference`, `prototype` ou `needs_review`.

## 4. Preparacao Operacional

- [ ] Abrir `docs/portfolio_analises`.
- [ ] Classificar numero de campanhas e pontos.
- [ ] Definir objetivo tecnico principal.
- [ ] Selecionar modulos analiticos.
- [ ] Registrar modulos descartados e justificativa.
- [ ] Criar/revisar dossie em `docs/projects/`.
- [ ] Criar/revisar recipe em `configs/projects/`.
- [ ] Definir `audit_project_slug` com a `canonical_key`.
- [ ] Definir pasta de entrega final no Drive do cliente.
- [ ] Definir pasta de lastro em `outputs/_project_scripts/<canonical_key>`.
- [ ] Definir scripts/pipelines que serao usados.

## 5. Alinhamento Antes De Rodar

- [ ] Listar produtos finais esperados.
- [ ] Listar graficos/tabelas que serao gerados.
- [ ] Confirmar que os graficos escolhidos cabem no volume de campanhas/pontos.
- [ ] Indicar quais padroes visuais serao reutilizados.
- [ ] Indicar quais pontos precisam de validacao do usuario.
- [ ] Confirmar que ainda nao ha analises a gerar ou que o usuario autorizou a execucao.
