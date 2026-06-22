# Inicio De Analise

Esta pasta e o modulo de abertura e configuracao analitica da
[Central de Controle](../control_center/README.md).

O fluxo completo, incluindo validacao, cadastro de especies, migracao e
consolidacao, esta em
[WORKFLOW.md](../control_center/WORKFLOW.md).

Quando o usuario mencionar `docs/inicio_analise`, `inicio_analise`,
`pasta de inicio de analise` ou equivalente, o procedimento esperado e:

1. Conferir primeiro a Central de Controle e a operacao ativa.
2. Ler esta pasta antes de criar scripts, graficos ou outputs.
3. Identificar o projeto pelo Supabase e pelo registry local.
4. Abrir ou criar o dossie tecnico do projeto.
5. Criar ou revisar a recipe da analise.
6. Consultar portfolio, patterns e aprendizados aprovados.
7. Definir produtos, recorte, destino final e lastro tecnico.
8. Registrar o Gate C antes da geracao.

## Arquivos

- [01_protocolo_codex.md](01_protocolo_codex.md): como o Codex deve agir quando esta pasta for citada.
- [02_checklist_nova_analise.md](02_checklist_nova_analise.md): checklist operacional.
- [03_briefing_minimo.md](03_briefing_minimo.md): informacoes minimas para abrir um projeto.
- [04_fechamento.md](04_fechamento.md): validacao, lastro, commit e aprendizados.
- [05_decisao_tipo_analise.md](05_decisao_tipo_analise.md): gate para escolher modulos e graficos antes da recipe final.

## Regra Curta

Nenhuma analise nova comeca por script solto. Dentro da Central de Controle, o
modulo analitico percorre:

`Supabase -> registry -> dossie -> portfolio de analises -> recipe -> execucao -> lastro -> aprendizado`
