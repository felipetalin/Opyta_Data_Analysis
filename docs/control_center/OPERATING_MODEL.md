# Modelo Operacional

O repositorio passa a operar como uma base viva de produto tecnico, nao como uma
pasta de scripts.

O fluxo de execucao de cada trabalho e definido em
[WORKFLOW.md](WORKFLOW.md). Este documento descreve o ciclo de vida do sistema,
dos projetos e dos componentes reutilizaveis.

## Principios

- Supabase e a fonte de verdade para identidade de projeto.
- GitHub guarda codigo, templates, registries e lastro tecnico versionavel.
- Google Drive do cliente guarda produto final entregue.
- `outputs/_project_scripts` guarda reproducibilidade tecnica.
- Toda analise deve consultar aprendizados antes de gerar novo padrao.
- Nenhum padrao e eterno: tudo pode ser aprovado, substituido ou depreciado.

## Ciclo De Vida Do Conhecimento

1. **Intake**: localizar projeto no Supabase e definir `canonical_key`.
2. **Entendimento**: registrar recorte, pergunta tecnica, dados e riscos.
3. **Reuse first**: consultar portfolio e patterns antes de prototipar.
4. **Prototipo**: criar experimento em `scripts/prototypes` ou pasta do projeto.
5. **Aprovacao**: registrar decisao visual/metodologica.
6. **Produto**: gerar outputs finais e lastro reprodutivel.
7. **Aprendizado**: atualizar dossie, portfolio, patterns e backlog.
8. **Fechamento**: rodar validadores, commit e push.

## Estados De Maturidade

| Estado | Uso |
| --- | --- |
| `draft` | Ideia registrada, ainda nao validada. |
| `prototype` | Testado em um projeto, mas ainda nao e padrao. |
| `approved` | Validado e recomendado para reuso. |
| `reference` | Bom exemplo historico, mesmo que nao seja padrao atual. |
| `deprecated` | Nao usar em novos projetos sem justificativa. |
| `needs_review` | Requer curadoria antes de reuso. |

Esses estados classificam patterns, referencias e componentes. O andamento de
uma execucao usa estados proprios, como `validating`,
`awaiting_data_approval`, `migrating`, `reviewing_layout` e `completed`,
documentados em [WORKFLOW.md](WORKFLOW.md).

Revisoes usam uma extensao desse ciclo, documentada em
[REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md). O principio e retornar apenas ao
ultimo ponto que deixou de ser confiavel, preservando as etapas anteriores que
continuam validas.

## Operacao De Projetos

Cada campanha ou rodada de trabalho deve ter um registro em
`docs/control_center/operations/`. O registro liga:

- identidade do projeto;
- dados e cadastro de especies;
- gates aprovados;
- migracao e consolidacao;
- configuracao das analises;
- produtos, validadores e pendencias.

O painel [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md) mostra somente o estado
operacional atual. O painel [PROJECTS.md](PROJECTS.md) continua mostrando a
identidade e o estado permanente do projeto.

## O Que Substitui O "Gold"

O antigo "Gold" vira uma familia de referencias:

- `approved`: o que esta pronto para reuso.
- `reference`: o que ensina algo, mesmo que nao seja o melhor atual.
- `deprecated`: o que foi superado.
- `portfolio`: exemplos finais por tipo de estudo.

Assim a engenharia continua viva sem perder memoria.
