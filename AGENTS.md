# Instrucoes Operacionais Do Repositorio

## Regra De Economia De Contexto

Custo de tokens e requisito operacional. Em pedidos pontuais de revisao ou
correcao de um produto especifico, o Codex deve aplicar primeiro o modo
economico de micro-revisao.

Micro-revisao se aplica quando o usuario aponta um arquivo, grafico, tabela,
texto ou erro isolado e nao pede explicitamente `center_control` nem revisao
completa. Nesse modo:

1. abrir somente o artefato alvo, a planilha/base irma quando existir e o
   trecho minimo do script gerador;
2. usar buscas filtradas por projeto, nome do produto ou bloco tecnico;
3. nao abrir `README`, `WORKFLOW`, `ACTIVE_OPERATIONS`, registry, dossie,
   todos os reviews ou lastros historicos, salvo dependencia real;
4. nao criar registro operacional antes do diagnostico minimo;
5. executar a correcao e validar apenas os arquivos afetados;
6. responder de forma curta: causa, arquivo corrigido, validacao e pendencia.

Expandir para o fluxo completo somente se houver risco real de banco,
migracao, consolidacao, taxonomia, coordenadas, mudanca metodologica ampla,
varios produtos dependentes ou se o usuario pedir explicitamente a Central de
Controle.

## Gatilho Da Central De Controle

Quando o usuario mencionar `center_control`, `center_cotrol`, `control_center`,
`central de controle` ou pedir para seguir o fluxo operacional, o Codex deve:

1. abrir `docs/control_center/README.md`;
2. abrir `docs/control_center/LLM_CONTEXT_POLICY.md` e limitar o contexto a
   operacao alvo;
3. seguir `docs/control_center/WORKFLOW.md` na ordem definida;
4. consultar `docs/control_center/ACTIVE_OPERATIONS.md`;
5. localizar ou criar o registro da operacao em
   `docs/control_center/operations/`;
6. consultar o registry, o dossie, a recipe e os lastros do projeto de forma
   filtrada e somente quando aplicaveis;
7. atualizar o estado da operacao conforme o trabalho avanca;
8. parar nos portoes que exigem aprovacao explicita do usuario.

Nao abrir por padrao `outputs/`, `logs/`, ambientes virtuais, snapshots,
planilhas, imagens, HTMLs, PDFs, todos os registros de operacao ou todos os
reviews. Esses arquivos so entram no contexto quando houver dependencia tecnica
registrada na operacao.

Nao e permitido pular diretamente para migracao, consolidacao ou geracao de
produtos quando um gate anterior ainda estiver pendente. Uma aprovacao pode ser
aproveitada da propria solicitacao do usuario quando estiver expressa de forma
clara e registrada no documento da operacao.

O fluxo oficial e:

`validacao -> aprovacao dos dados -> cadastro e auditoria de especies ->
aprovacao taxonomica -> migracao -> consolidacao -> configuracao das analises ->
aprovacao de template/paleta/saida -> geracao -> revisao -> fechamento`

## Gatilho De Revisao

Quando o usuario pedir `center_control revisao`, "revisar", "ajustes de
layout", "ajustes de texto", "corrigir resultados" ou equivalente:

0. se for correcao pontual de um unico artefato, aplicar primeiro a
   micro-revisao da Regra De Economia De Contexto;
1. abrir `docs/control_center/REVIEW_WORKFLOW.md`;
2. localizar a operacao e preservar a linha de base;
3. classificar a revisao como dados, taxonomia, analise, texto, layout, pacote
   ou completa;
4. definir o impacto `R0`, `R1`, `R2` ou `R3`;
5. reabrir Gate A, B ou C apenas quando a mudanca afetar aquele gate;
6. criar registro em `docs/control_center/reviews/` quando houver escopo
   executavel;
7. finalizar no Gate R, com comparacao antes/depois e aprovacao do usuario.

Uma revisao visual ou textual nao deve refazer migracao/consolidacao sem
dependencia tecnica. Uma revisao de dados ou taxonomia deve regenerar toda a
cadeia posterior afetada.
