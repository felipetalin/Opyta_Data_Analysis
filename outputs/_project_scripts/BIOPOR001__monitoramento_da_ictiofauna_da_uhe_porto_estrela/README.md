# BIOPOR001 - Monitoramento da ictiofauna da UHE Porto Estrela

Este diretorio centraliza o lastro reutilizavel do projeto Porto Estrela dentro
de `outputs/_project_scripts`. O pacote combina o snapshot dos resultados
externos com scripts, configuracao e documentos tecnicos que ja estavam no
repositorio.

## Origem externa

- Caminho original: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados`
- Snapshot local: `external_results_snapshot_20260624_135759`
- Tipo: resultados, bases analiticas, modelos graficos, prototipos e relatorio HTML.
- Grupo: ictiofauna.
- Periodo de geracao observado: 2026-06-02 a 2026-06-05.

## Inventario do snapshot externo

- Total de arquivos nao ocultos: 138.
- Planilhas `.xlsx`: 43.
- Figuras `.png`: 87.
- Documentos `.md`: 6.
- Relatorios `.html`: 2.
- Scripts `.py`: 0.
- Metadados `.json`: 0.

## Conteudo interno consolidado

- `scripts/projects/porto_estrela`: 6 scripts principais do projeto.
- `scripts/wrappers`: 7 wrappers/atalhos historicos, incluindo prototipo visual.
- `scripts/prototypes`: prototipo de design Porto Estrela.
- `configs/projects/biopor001_porto_estrela_ictiofauna.json`: configuracao do projeto.
- `docs`: 5 documentos tecnicos copiados do repositorio.
- `inventory/BIOPOR001_file_inventory_final_20260624_142726.csv`: inventario final do pacote.

## Documentos-chave

- `PORTO_ESTRELA_MIGRACAO_ICTIOFAUNA_20260602.md`: lastro da migracao e consolidacao inicial.
- `PORTO_ESTRELA_LAYOUT_GRAFICOS_REFERENCIA_DUCAL_20260602.md`: referencia visual baseada no padrao Ducal.
- `PORTO_ESTRELA_MATRIZ_PRODUTOS_ICTIOFAUNA_20260602.md`: matriz de produtos e entregaveis.
- `PORTO_ESTRELA_ANALISES_EXPLORATORIAS_BETA_INFLEXAO_20260603.md`: beta diversidade, LCBD, PCoA e pontos de inflexao.
- `biopor001_porto_estrela_ictiofauna.md`: dossie resumido do projeto.

## Pasta de producao principal

Dentro do snapshot externo, a pasta principal e:

`resultados_ictiofauna_porto_estrela_producao_20260603`

- Total: 56 arquivos.
- Planilhas: 20.
- Figuras: 33.
- Relatorios HTML: 2.
- Manifesto Markdown: 1.
- Ultima alteracao observada: 2026-06-05 14:49.

## Classificacao

Este e um lastro de produto/entrega enriquecido com o lastro tecnico interno.
A pasta externa original nao continha `execution_metadata.json`,
`run_this_analysis.py`, manifestos com hash ou snapshot dos scripts de execucao.

Quando o pipeline de Porto Estrela voltar a ser usado, a acao recomendada e
fazer retrofit do lastro tecnico no padrao novo: registrar runner, parametros,
hashes, scripts executados e manifestos por bloco.
