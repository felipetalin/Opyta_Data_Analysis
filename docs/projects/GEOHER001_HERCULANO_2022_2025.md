# GEOHER001 Herculano 2022-2025

## Escopo

- Projeto Supabase: `30`
- Codigo: `GEOHER001`
- Cliente: Geomil
- Projeto: `Monitoramento de ictio e bentos - Herculano`
- Recorte temporal: C21 a C36, de 2022 a 2025
- Recorte espacial: todos os pontos amostrais

## Receita

Arquivo oficial:

`configs/projects/geoher001_herculano_2022_2025.json`

## Produtos

Destino final:

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Herculano - Informacoes Complementares Licenciamento Pilhas/Resultados`

Subpastas:

- `Ictiofauna`
- `Bentos`

## Decisoes graficas

- A4 paisagem.
- 600 dpi.
- Paleta azul Opyta.
- Perfil aprovado para Word:
  - fonte-base de 15 pt;
  - rotulos de eixos de 16 pt;
  - legendas de 13 pt;
  - anotacoes de 12 pt;
  - campanhas abreviadas quando necessario.
- Minigraficos temporais nos graficos 02, 03 e 10.
- Grafico 06 separado por ano.
- Mapas de calor de CPUEn e CPUEb limitados a largura de A4 paisagem.
- Zoobentos grafico 12 com EPT azul e CHOL vermelho, lado a lado.
- Codigos das campanhas anuais posicionados no cabecalho dos paineis.

O perfil foi aprovado pelo usuario em 2026-06-19 apos a regeneracao integral
das 37 figuras. O criterio principal foi a leitura confortavel no Word sem
necessidade de zoom.

## Geracao aprovada em 2026-06-19

- 66 produtos regenerados:
  - 37 figuras PNG;
  - 29 planilhas XLSX.
- Auditoria automatica concluida sem erros ou avisos.
- Backup anterior preservado em:
  `Resultados_backup_20260619_111003`.
- Bentos regenerado com 74 taxons e 2.596 organismos.

## Sintese De Ocorrencia Multicampanha

Em 2026-06-19 foi implementada uma nova forma de apresentar ocorrencia em 16
campanhas sem levar o quadro completo de aproximadamente 160 colunas para o
corpo do relatorio.

Produtos adicionados para Ictiofauna e Zoobentos:

- workbook `04A_tabela_sintese_ocorrencia_*`;
- mapa de calor `04B` com frequencia por campanha;
- mapa de calor `04C` com frequencia por ponto.

O workbook possui:

- `Resumo_Geral`;
- `Freq_Campanha`;
- `Freq_Ponto`;
- quadros anuais de 2022 a 2025;
- `Base_Longa`.

Ictiofauna cabe em uma figura por sintese. Zoobentos foi dividido
automaticamente em quatro partes por sintese para manter a legibilidade dos 74
taxons e preservar, quando possivel, os grupos taxonomicos na mesma pagina.

O quadro completo anterior foi preservado como lastro. O novo layout esta
registrado como pattern candidato, aguardando aprovacao visual final.

## Revisao taxonomica de Zoobentos em 2026-06-19

A auditoria completa identificou e corrigiu 42 taxons no catalogo central:

- 25 ocorrencias de `Artropoda` normalizadas para `Arthropoda`;
- cinco inversoes entre classe `Insecta` e ordem;
- uma inversao entre classe `Bivalvia` e ordem `Veneroida`;
- `Staphylinidae` e `Empididae` removidas do campo genero;
- `sp.` removido do campo genero em 15 taxons.

O campo genero passou a receber somente o nome do genero. Para identificacoes
em nivel de familia, o genero permanece vazio. A ordem artificial `Insecta`
deixou de aparecer nos resultados, a riqueza de Ephemeroptera passou de 8 para
10 taxons e o EPT consolidado passou de 1.001 para 1.024 organismos (39,45%).

O Darwin Core tambem passou a inferir o nivel taxonomico real: familia, genero,
ordem ou classe. Identificacoes como `Baetodes sp.` sao exportadas no nivel
genero com `identificationQualifier = sp.`.

Backup da migracao:
`public.backup_geoher001_bentos_taxonomy_20260619t173235z`.

Boas praticas aplicadas no fechamento:

- dry-run antes da escrita;
- backup transacional dos 42 registros;
- verificacao pos-aplicacao com zero pendencias;
- regeneracao integral dos 42 produtos de Bentos;
- manifesto reprodutivel com hashes na pasta canonica do projeto;
- auditoria oficial de fauna apos a geracao;
- retencao de apenas um par timestamped de metadata e reprodutor por grupo.

## Lastro Git

- Repositorio:
  [`felipetalin/Opyta_Data_Analysis`](https://github.com/felipetalin/Opyta_Data_Analysis)
- Branch publicada: `main`
- Commit de implementacao: `2bb06890fe92566586e1a789432871c18e6c1709`
- Link permanente:
  [`2bb0689 - Aprimora resultados e taxonomia GEOHER001`](https://github.com/felipetalin/Opyta_Data_Analysis/commit/2bb06890fe92566586e1a789432871c18e6c1709)
- Publicado em: `2026-06-20T08:49:20-03:00`
- Base anterior: `77c6240`

O commit registra conjuntamente:

- normalizacao taxonomica de Zoobentos;
- correcao do nivel taxonomico no Darwin Core;
- sintese de ocorrencia multicampanha;
- perfil de figuras em alta resolucao para Word;
- atualizacoes nos pipelines de Ictiofauna e Zoobentos;
- patterns, registries, catalogo de scripts e dossie do projeto;
- retencao controlada do lastro reprodutivel gerado pelo runner.

## Fechamento operacional em 2026-06-20

Apos a liberacao dos arquivos no Excel, o pipeline de Zoobentos foi executado
integralmente na pasta final do cliente.

- execucao: `block=all`;
- registros carregados: 725;
- campanhas: 16;
- pontos: 8;
- blocos executados: 3 a 13;
- produtos declarados: 42;
- produtos ausentes: 0;
- hashes SHA-256: presentes nos 42 produtos;
- avisos do runner: 0.

Lastro reprodutivel oficial:

- `outputs/_project_scripts/GEOHER001__monitoramento_de_ictio_e_bentos_herculano/zoobentos/execution_metadata.json`;
- `outputs/_project_scripts/GEOHER001__monitoramento_de_ictio_e_bentos_herculano/zoobentos/20260620T145722Z_execution_metadata.json`;
- `outputs/_project_scripts/GEOHER001__monitoramento_de_ictio_e_bentos_herculano/zoobentos/20260620T145722Z_run_this_analysis.py`;
- `outputs/_project_scripts/GEOHER001__monitoramento_de_ictio_e_bentos_herculano/fauna_inventory.json`.

Validacoes finais:

- auditoria oficial de fauna: `OK`;
- erros: 0;
- avisos: 0;
- auditoria taxonomica no banco: zero pendencias;
- ordem artificial `Insecta`: ausente;
- riqueza de Ephemeroptera: 10 taxons;
- EPT: 1.024 de 2.596 organismos, equivalente a 39,45%;
- Darwin Core: niveis taxonomicos distribuidos entre familia, genero, ordem e
  classe, sem ordem `Insecta` indevida;
- cobertura Supabase x registry: nenhum projeto ausente;
- alias tecnico `geoher001_recorte_2022_2025`: removido;
- retencao: um unico par timestamped de metadata e reprodutor por grupo.

## Observacoes de dados

- A campanha C37 de Bentos foi corrigida como fevereiro/2026 e ficou fora do
  recorte analitico 2022-2025.
- Para Ictiofauna, a campanha C21 possui esforco com captura zero. O pipeline
  preserva a campanha nas metricas temporais com registros internos de esforco
  zero, mas exclui esses registros dos produtos taxonomicos.

## Scripts de apoio

- `scripts/run_pipeline.py`
- `scripts/run/run_project_recipe.py geoher001_herculano_2022_2025 --env-file .env`
- `scripts/maintenance/geoher001/`
- `scripts/prototypes/prototipar_geoher001_bentos_layouts.py`

## Padroes relacionados

- `docs/patterns/minigraficos_temporais.md`
- `docs/patterns/cpue_por_ano.md`
- `docs/patterns/ept_chol.md`
- `docs/patterns/figuras_word_alta_resolucao.md`
- `docs/patterns/ocorrencia_multicampanha.md`
- `docs/patterns/paleta_azul_opyta.md`
