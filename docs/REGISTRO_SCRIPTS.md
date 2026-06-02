# Registro de script inserido no sistema

- Script: scripts/validar_migracao_ictiofauna.py
- Descricao: Validador CLI reutilizavel para pre-migracao de workbooks de Ictiofauna, integrando validadores oficiais de `Opyta_Data`, checagens complementares de pontos, esforcos, resultados, especies e premissas de contagem.
- Data de registro: 2026-06-02
- Responsavel: Codex/Felipe
- Observacoes: Criado durante a organizacao da migracao Porto Estrela e validado com Ducal e Porto Estrela. O script gera relatorios em Markdown, Excel e JSON em `outputs/validacoes/<project-slug>`.

- Script: scripts/inserir_meio_fisico_rest.py
- Descrição: Validação, harmonização e inserção de dados de Meio Físico no Supabase via REST, com validação robusta e tratamento de valores laboratoriais (ex: <0.0500, >1600, ND, etc).
- Data de registro: 2026-05-18
- Responsável: [Seu nome ou responsável pelo commit]
- Observações: Script validado e executado com sucesso. Pronto para uso em produção e versionamento.
