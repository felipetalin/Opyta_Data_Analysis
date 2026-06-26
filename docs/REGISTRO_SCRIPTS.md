# Registro de script inserido no sistema

> Registro historico. O indice operacional atual fica em
> `scripts/SCRIPT_CATALOG.md`. Novos scripts devem ser registrados primeiro no
> catalogo e, quando forem padroes reutilizaveis, tambem em `docs/patterns/`.

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

- Script: scripts/migrar_bentos_avg_2026.py
- Descricao: Valida e migra a planilha revisada de Zoobentos AVG 2026 para as tabelas base, integrando o validador oficial do Opyta Data, normalizacao de campanhas e auditoria da carga.
- Data de registro: 2026-06-08
- Responsavel: Codex/Felipe
- Observacoes: Usado na migracao da planilha `projeto_bentos_real - AVG- 260608 - Rev.xlsx`; resolve campanhas por chave canonica/id e registra auditoria em `outputs/_migration/avg_bentos_2026/`.

- Script: scripts/consolidar_bentos_avg_2026.py
- Descricao: Consolida a fatia AVG/Zoobentos das tabelas base para `biota_analise_consolidada`, com backup da fatia anterior e resumo comparativo fonte/destino.
- Data de registro: 2026-06-08
- Responsavel: Codex/Felipe
- Observacoes: Substitui somente `codigo_interno_opyta = BRAAVG002` e `grupo_biologico = Zoobentos`; backup preservado em tabela `bkp_biota_avg_zoobentos_20260608_112425`.

- Script: scripts/run_bentos_avg_2026_por_campanha.py
- Descricao: Gera os resultados de Zoobentos AVG 2026 separadamente para fevereiro e marco, filtrando as campanhas finais antes da execucao dos blocos do pipeline.
- Data de registro: 2026-06-08
- Responsavel: Codex/Felipe
- Observacoes: Saidas finais em `Resultados bentos/2026/Fevereir-26` e `Resultados bentos/2026/marco-26`; usado apos ajustes de paleta verde, rosca e remocao de `Nao informado`.

- Script: outputs/_project_scripts/ducal/ictiofauna/_run_this_analysis.py
- Descricao: Reprodutor oficial dos outputs de Ictiofauna Ducal Campanha 05, apontando para `pipeline=ictio`, `client=ducgeo001`, `project_id=183` e `--block all`.
- Data de registro: 2026-06-09
- Responsavel: Codex/Felipe
- Observacoes: Snapshot completo em `outputs/_project_scripts/ducal/ictiofauna/20260609T144110Z_run_this_analysis.py`; metadados em `20260609T144110Z_execution_metadata.json`; 27 arquivos gerados, 69 linhas carregadas e sem warnings.

- Script: outputs/_project_scripts/ducal/zoobentos/_run_this_analysis.py
- Descricao: Reprodutor oficial dos outputs de Zoobentos Ducal Campanha 05, apontando para `pipeline=zoobentos`, `client=ducgeo001`, `project_id=183` e `--block all`.
- Data de registro: 2026-06-09
- Responsavel: Codex/Felipe
- Observacoes: Snapshot completo em `outputs/_project_scripts/ducal/zoobentos/20260609T163939Z_run_this_analysis.py`; metadados em `20260609T163939Z_execution_metadata.json`; 41 arquivos gerados, 145 linhas carregadas e sem warnings. Os graficos `06B`/`06C` usam paleta azul Ducal alternada para contraste; BMWP preserva cores tecnicas por categoria.

- Script: scripts/projects/geoarc001/generate_exploratory_assembly_analysis.py
- Descricao: Gera pacote exploratorio taxonomico da assembleia de ictiofauna do GEOARC001, incluindo LCBD, NMDS/PERMANOVA, painel temporal de indicadores e beta diversidade particionada.
- Data de registro: 2026-06-26
- Responsavel: Codex/Felipe
- Observacoes: Produto exploratorio para avaliacao interna. Saidas na pasta `Exploratorio_assembleia_ictiofauna`, com PNG, XLSX, JSON e README de apoio.

- Script: scripts/projects/geoarc001/generate_functional_exploratory_analysis.py
- Descricao: Gera pacote exploratorio funcional da ictiofauna do GEOARC001 a partir da tabela especie x atributos, com composicao funcional, LCBD funcional, NMDS/PERMANOVA funcional, painel de indicadores e heatmap de grupos sentinelas.
- Data de registro: 2026-06-26
- Responsavel: Codex/Felipe
- Observacoes: Base do padrao `docs/patterns/grupos_funcionais_sentinelas_ictio.md`. Os grupos funcionais sentinelas sao independentes e podem compartilhar especies.

- Script: scripts/projects/geoarc001/generate_functional_spatial_mini_maps.py
- Descricao: Gera mini mapas anuais dos grupos funcionais sentinelas, com ponto amostral no espaco, ano em colunas, grupo em linhas, tamanho de bolha por CPUEn medio anual e cor por participacao no CPUEn total.
- Data de registro: 2026-06-26
- Responsavel: Codex/Felipe
- Observacoes: Usa KMZ/KML oficial como referencia de coordenadas quando informado. O produto aprovado no piloto foi `26_grafico_mini_mapas_funcoes_ecologicas_ano_ictiofauna.png`.

- Script: scripts/projects/geoarc001/generate_functional_species_signature.py
- Descricao: Gera painel de assinatura das especies por grupos funcionais sentinelas, com nomes cientificos em italico, barras de CPUEn total e marcadores AME/EXO.
- Data de registro: 2026-06-26
- Responsavel: Codex/Felipe
- Observacoes: Complementa o mapa funcional mostrando quais especies compoem cada grupo. O produto aprovado no piloto foi `27_grafico_assinatura_especies_grupos_funcionais_ictiofauna.png`.

- Script: scripts/maintenance/geoarc001/update_geoarc001_coordinates_from_kmz.py
- Descricao: Auditoria e correcao controlada das coordenadas do GEOARC001 no Supabase usando KMZ oficial.
- Data de registro: 2026-06-26
- Responsavel: Codex/Felipe
- Observacoes: Executado com `--apply` para `id_projeto=190`: 198 linhas avaliadas, 154 linhas corrigidas, 198/198 linhas conferindo apos correcao. Auditoria em `outputs/audits/geoarc001_coordinates/`.
