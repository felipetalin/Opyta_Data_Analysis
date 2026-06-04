# Registro de script inserido no sistema

- Script: scripts/validar_migracao_ictiofauna.py
- Descricao: Validador CLI reutilizavel para pre-migracao de workbooks de Ictiofauna, integrando validadores oficiais de `Opyta_Data`, checagens complementares de pontos, esforcos, resultados, especies e premissas de contagem.
- Data de registro: 2026-06-02
- Responsavel: Codex/Felipe
- Observacoes: Criado durante a organizacao da migracao Porto Estrela e validado com Ducal e Porto Estrela. O script gera relatorios em Markdown, Excel e JSON em `outputs/validacoes/<project-slug>`.

- Script: scripts/gerar_base_analitica_porto_estrela_ictio.py
- Descricao: Gera a base analitica consolidada de ictiofauna da UHE Porto Estrela, com premissas aprovadas de ano hidrologico, trechos Montante/Jusante, biomassa por linha, CPUE N e CPUE B.
- Data de registro: 2026-06-04
- Responsavel: Codex/Felipe
- Observacoes: Base oficial usada pelos resultados de producao de Porto Estrela. Mantem P1 com coordenada corrigida e separacao espacial por tabela de relacionamento, nao por alteracao do nome do ponto.

- Script: scripts/gerar_resultados_porto_estrela_ictio.py
- Descricao: Pipeline modular oficial dos produtos de ictiofauna da UHE Porto Estrela, incluindo tabelas 5 a 8, figuras 10 a 16, blocos 6.6.1 a 6.6.4, diversidade, beta temporal e reproducao.
- Data de registro: 2026-06-04
- Responsavel: Codex/Felipe
- Observacoes: Fonte unica dos outputs finais aprovados. Cada figura possui Excel de apoio; os blocos 661 a 664 incluem abas de especies, tornado, temporal, ponto de inflexao e espacial. Use `--only` para ajustes pontuais.

- Script: scripts/gerar_relatorio_html_porto_estrela_ictio.py
- Descricao: Gera relatorio tecnico em HTML com texto-base para o relatorio consolidado da ictiofauna da UHE Porto Estrela, integrando os produtos oficiais em PNG e Excel.
- Data de registro: 2026-06-04
- Responsavel: Codex/Felipe
- Observacoes: Produto de apoio a redacao tecnica. O HTML fica na pasta de producao dos resultados e usa caminhos relativos para as figuras e planilhas oficiais.

- Script: scripts/gerar_exploratorias_porto_estrela_ictio.py
- Descricao: Gera analises exploratorias de diversidade beta, pontos de inflexao e padroes temporais para avaliacao tecnica antes de incorporacao ao pipeline oficial.
- Data de registro: 2026-06-04
- Responsavel: Codex/Felipe
- Observacoes: Mantido como laboratorio metodologico. Nao substitui o pipeline oficial de producao.

- Script: scripts/gerar_exploratorias_espaciais_porto_estrela_ictio.py
- Descricao: Gera analises exploratorias espaciais por mapas de bolhas, pizzas, colares, heatmaps e perfis longitudinais para ictiofauna da UHE Porto Estrela.
- Data de registro: 2026-06-04
- Responsavel: Codex/Felipe
- Observacoes: O modelo espacial de mapa de pizzas foi aprovado como referencia visual futura; fundo limpo, legenda superior e pontos por trechos Montante/Jusante.

- Script: scripts/inserir_meio_fisico_rest.py
- Descrição: Validação, harmonização e inserção de dados de Meio Físico no Supabase via REST, com validação robusta e tratamento de valores laboratoriais (ex: <0.0500, >1600, ND, etc).
- Data de registro: 2026-05-18
- Responsável: [Seu nome ou responsável pelo commit]
- Observações: Script validado e executado com sucesso. Pronto para uso em produção e versionamento.
