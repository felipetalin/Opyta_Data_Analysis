# Decision Record - OPYTA DATA Como Frontend E Backend Orquestrador

## Contexto

Em 2026-07-06 foi avaliada a possibilidade de usar o OPYTA DATA para permitir
que mais pessoas da OPYTA gerem analises sem depender exclusivamente do Felipe.

O sistema atual esta dividido em duas bases principais:

- `G:/Meu Drive/Opyta/Opyta_Data`: frontend Streamlit, fluxo de importacao,
  validadores, consolidacao, analises simples, exportacao, qualidade e
  geoprocessamento.
- `G:/Meu Drive/Opyta/Opyta_Data_Analysis`: motor analitico atual, recipes,
  Central de Controle, registros de operacao, workflow, scripts de projeto,
  pipelines e lastro reprodutivel.

O OPYTA DATA ja entrega uma interface funcional, mas a execucao ainda chama
scripts diretamente, conecta no banco com bastante poder e nao aplica
formalmente os gates da Central de Controle. O motor de analises mais atual e
a governanca operacional estao no `Opyta_Data_Analysis`.

## Decisao

Nao descartar o OPYTA DATA.

Usar o OPYTA DATA como frontend interno e casca operacional, mas nao tratar o
backend atual dele como base final para colaboracao multiusuario.

Criar uma camada incremental de backend/orquestracao, chamada provisoriamente
de `opyta_ops`, responsavel por:

- impor o workflow da Central de Controle;
- controlar estados e gates de cada operacao;
- separar permissao por perfil;
- registrar auditoria persistente;
- executar validacao, migracao, consolidacao e geracao por jobs controlados;
- chamar o motor atual em `Opyta_Data_Analysis` por recipes/pipelines;
- servir como ponto seguro para uma futura LLM operacional.

Arquitetura alvo:

```text
Colaborador / LLM
  -> OPYTA DATA (frontend Streamlit, inicialmente)
  -> opyta_ops (backend/orquestrador)
  -> Opyta_Data_Analysis (motor, recipes, validadores, produtos)
  -> Supabase / Google Drive / outputs de lastro
```

## Alternativas Consideradas

1. Manter apenas o OPYTA DATA atual.

   Rejeitado como caminho final porque a UI chama scripts diretamente, nao tem
   RBAC completo, nao persiste toda auditoria em banco e ainda nao aplica os
   gates oficiais da Central de Controle.

2. Reescrever tudo em um novo backend/frontend.

   Rejeitado no curto prazo por alto custo e risco de regressao. O frontend
   existente ja tem valor e pode ser reaproveitado.

3. Expor o sistema diretamente a uma LLM.

   Rejeitado como primeira etapa. A LLM deve operar por cima de uma camada com
   permissao, logs, gates e acoes permitidas, nao diretamente sobre scripts ou
   banco.

4. Reaproveitar OPYTA DATA com backend/orquestrador incremental.

   Escolhido como melhor equilibrio entre velocidade, seguranca e evolucao.

## Evidencias Da Avaliacao

- O OPYTA DATA e um app Streamlit, sem FastAPI/Flask ou API separada.
- A pagina `app/pages/01_Importacao.py` tem validadores uteis e reaproveitaveis.
- A pagina `app/pages/02_Consolidacao.py` chama `scripts/processar_dados.py`.
- `scripts/processar_dados.py` faz `TRUNCATE` em `biota_analise_consolidada`
  antes de recarregar a base analitica.
- A auditoria do OPYTA DATA existe em `core/audit/`, mas o lastro atual e local
  em `runtime/audit/` e precisa de persistencia em Supabase.
- O workflow oficial com gates esta em
  `docs/control_center/WORKFLOW.md` no `Opyta_Data_Analysis`.

## Consequencias

Consequencias positivas:

- aproveita o investimento ja feito no OPYTA DATA;
- reduz retrabalho de interface;
- permite evolucao gradual;
- preserva o motor novo e a Central de Controle como fonte de verdade;
- cria base segura para colaborar com humanos e depois com LLM.

Riscos se a decisao nao for seguida:

- colaboradores podem executar acoes destrutivas sem gate;
- consolidacoes podem afetar mais escopo do que o esperado;
- o sistema pode ficar dependente de memoria operacional do Felipe;
- a LLM pode ganhar poder antes de haver controles suficientes.

## Proximas Acoes

1. Criar especificacao inicial de `opyta_ops`.
2. Mapear acoes criticas do OPYTA DATA:
   - cadastro;
   - validacao;
   - migracao;
   - consolidacao;
   - geracao;
   - revisao;
   - fechamento.
3. Definir perfis de permissao:
   - leitor;
   - preparador;
   - analista;
   - revisor;
   - administrador.
4. Persistir auditoria operacional em Supabase.
5. Substituir a consolidacao global por consolidacao controlada por escopo ou
   job com backup/reversao.
6. Conectar a pagina de analises do OPYTA DATA ao runner/recipe atual do
   `Opyta_Data_Analysis`.
7. Criar ponte futura para LLM apenas depois dos gates e permissoes existirem.

## Projetos Afetados

- OPYTA DATA
- Opyta Data Analysis Core
- Central de Controle
- Supabase OPYTA
- Futuros colaboradores internos da OPYTA

## Status

- registered
- decisao estrategica registrada em 2026-07-06
- pendente de especificacao tecnica e operacao propria
