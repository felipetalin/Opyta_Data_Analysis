# Politica De Contexto Para LLM

Esta politica reduz o custo e o risco operacional quando Codex, outra LLM ou um
assistente automatizado usa a Central de Controle.

O objetivo e preservar governanca sem transformar o repositorio inteiro em
contexto ativo.

## Regra Principal

Contexto e um recurso operacional. Ao acionar a Central de Controle, carregar
apenas o necessario para a operacao atual.

A Central deve funcionar como indice e trilha de decisao, nao como convite para
abrir todos os dossies, reviews, outputs, logs e lastros historicos.

## Modo Economico Obrigatorio

Pedidos pontuais de correcao/revisao de um unico artefato devem comecar em
micro-revisao, nao no fluxo completo.

Exemplos: "corrigir este grafico", "a curva esta errada", "ajuste a legenda",
"trocar o texto desta figura", quando o usuario aponta arquivo ou produto
especifico.

Nesse modo, abrir inicialmente no maximo:

- o artefato alvo, se for necessario inspecionar;
- a planilha/base irma que alimenta o artefato;
- o trecho minimo do script gerador;
- uma configuracao visual, somente se o erro for layout.

Nao abrir por padrao `README`, `WORKFLOW`, `ACTIVE_OPERATIONS`, registry,
dossie, todos os registros, outputs historicos ou lastros. Tambem nao criar
registro de revisao antes do diagnostico minimo.

Escalar para o fluxo completo somente quando houver evidencia de impacto em
banco, migracao, consolidacao, taxonomia, coordenadas, metodo aprovado, cadeia
com muitos produtos dependentes ou quando o usuario pedir explicitamente
`center_control`/Central de Controle.

## Ordem Minima Obrigatoria

Quando `center_control`, `center_cotrol`, `control_center`, "central de
controle" ou "seguir o fluxo operacional" forem acionados:

1. abrir `docs/control_center/README.md`;
2. abrir este arquivo;
3. abrir `docs/control_center/WORKFLOW.md`;
4. abrir `docs/control_center/ACTIVE_OPERATIONS.md`;
5. localizar ou criar somente o registro da operacao alvo;
6. consultar o registry de forma filtrada pelo projeto/codigo/canonical_key;
7. abrir dossie, recipe, portfolio, pattern ou lastro somente quando forem
   aplicaveis ao projeto e a etapa atual.

Para revisoes completas ou de alto impacto, abrir tambem
`docs/control_center/REVIEW_WORKFLOW.md` e somente o registro de revisao alvo.
Para micro-revisoes, seguir o Modo Economico Obrigatorio acima.

## O Que Nao Abrir Por Padrao

Nao abrir por padrao:

- `outputs/`;
- `logs/`;
- `.venv/`;
- todos os registros em `docs/control_center/operations/`;
- todos os registros em `docs/control_center/reviews/`;
- todos os dossies em `docs/projects/`;
- snapshots, planilhas, imagens, HTMLs, PDFs ou artefatos binarios;
- resultados antigos que nao estejam ligados a operacao atual.

Esses itens so devem ser abertos quando houver uma pergunta explicita ou uma
dependencia tecnica registrada no documento da operacao.

## Consulta Ao Registry

O registry deve ser consultado como indice.

Preferir:

- localizar a entrada por `codigo_interno_opyta`;
- localizar por `canonical_key`;
- abrir apenas o trecho ou o arquivo que contem a entrada relevante;
- registrar no documento da operacao quais docs, recipes e lastros foram
  considerados aplicaveis.

Evitar carregar o registry inteiro em toda rodada quando o projeto alvo ja foi
identificado.

## Lastros E Outputs

Lastros em `outputs/_project_scripts` continuam sendo fonte tecnica de
reprodutibilidade, mas nao sao contexto inicial.

Abrir lastro somente se:

- a operacao estiver em revisao numerica;
- houver divergencia entre produto e metadado;
- o usuario pedir comparacao antes/depois;
- for necessario recuperar manifesto, reproducer script ou hash.

Quando abrir um lastro pesado, registrar no documento da operacao:

- caminho;
- motivo;
- informacao extraida;
- se houve impacto em gate ou revisao.

## Buscas E Comandos

Usar buscas filtradas.

Preferir:

```powershell
rg -n "BRAAVG002|canonical_key" docs/registry docs/control_center docs/projects configs
rg -n "estado atual|Gate C" docs/control_center/operations/NOME_DA_OPERACAO.md
rg --files docs/control_center docs/projects configs scripts src
```

Evitar:

```powershell
rg "termo" .
rg --files
Get-ChildItem -Recurse
```

Se uma busca ampla for inevitavel, excluir outputs, logs, ambientes virtuais,
artefatos binarios e snapshots.

## Checklist Antes De Gerar Resposta Ou Produto

Antes de executar, migrar, consolidar ou gerar produtos, confirmar:

- operacao alvo identificada;
- estado atual lido no registro da operacao;
- gates aplicaveis checados;
- arquivos abertos limitados ao escopo;
- nenhum output pesado foi usado como contexto sem motivo registrado;
- proxima acao registrada.

## Falha De Contexto

Se a sessao ficar pesada, confusa ou com consumo anormal:

1. parar expansao de contexto;
2. listar apenas os arquivos ja abertos que importam;
3. reduzir o escopo para uma operacao e uma etapa;
4. registrar a causa provavel no documento da operacao;
5. continuar somente com arquivos-alvo.

## Relacao Com `.codexignore`

O arquivo `.codexignore` na raiz do repositorio e a barreira pratica para
impedir que Codex carregue ambientes, outputs e artefatos pesados. Esta
politica e a regra operacional; `.codexignore` e o mecanismo de contencao.
