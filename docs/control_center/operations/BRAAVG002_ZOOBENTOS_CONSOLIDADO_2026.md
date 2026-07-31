# BRAAVG002 — Zoobentos — Consolidado 2026

## Controle

- projeto: BRAAVG002 / Monitoramento de ictio e bentos - Brumado - AVG
- grupo: Zoobentos
- operacao: migracao, consolidacao e organizacao das analises do consolidado 01-47
- estado atual: `generated_pending_review`
- aberta em: 2026-07-21
- atualizada em: 2026-07-21
- proxima acao: revisar os produtos selecionados gerados para o consolidado 01-47

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Migração de dados/2026/Bentos/projeto_bentos_real - AVG- 260721.xlsx`
- cadastro de especies: `public.especies`
- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/Consolidado_2026`
- dossie: `docs/projects/BRAAVG002_ZOOBENTOS_CONSOLIDADO_2026.md`
- recipe: `configs/projects/braavg002_zoobentos_2026.json`
- lastro: `outputs/_migration/avg_bentos_2026`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Operacao aberta com planilha 260721, projeto 9/BRAAVG002 e grupo Zoobentos. |
| Validacao | concluida | Dry-run aprovado apos de/para `Atopsyche` -> `Atopsyche sp.`; sem bloqueios, avisos ou especies desconhecidas. |
| Gate A — dados | aprovado | Usuario aprovou em 2026-07-21; planilha validada com 47 campanhas, 611 pontos-campanha, 611 esforcos e 4.126 resultados. |
| Cadastro de especies | concluido | 117 taxons preparados apos agregacao e de/para; especies desconhecidas = 0. |
| Auditoria de atributos | concluida | BMWP revisado conforme adaptacao Rio das Velhas; nao ha mais `bmwp_score` nulo no consolidado. |
| Gate B — especies | aprovado | Usuario aprovou em 2026-07-21; de/para `Atopsyche` -> `Atopsyche sp.` aplicado no script. |
| Migracao | concluida | `migration_applied.json`: 4.106 resultados agregados, 117 taxons e abundancia total 13.680. |
| Consolidacao | concluida | Backup `bkp_biota_avg_zoobentos_20260721_141031`; 3.937 linhas antigas substituidas por 4.106 linhas consolidadas. |
| Configuracao das analises | em andamento | Base analitica consolidada gerada e validada; falta aprovar padrao visual/produtos no Gate C. |
| Gate C — analises | aprovado | Escopo selecionado pelo usuario: composicao, riqueza, abundancia/densidade, Shannon/Pielou, minimapas BMWP/EPT/CHOL, PCoA, tabelas bioindicadoras e Darwin Core. |
| Geracao dos produtos | concluida parcial | Produtos selecionados gerados em `Resultados bentos/Consolidado_2026`, com Excel por produto e Darwin Core. |
| Revisao tecnica | pendente | |
| Revisao de layout | pendente | |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved` | Aprovado pelo usuario em 2026-07-21. |
| B — especies | `approved` | Aprovado pelo usuario em 2026-07-21. |
| C — analises | `approved` | Escopo e regras visuais aprovados pelo usuario em 2026-07-21; produtos selecionados gerados para revisao. |

## Validacao Dos Dados

- bloqueios: nenhum no dry-run apos de/para
- avisos: nenhum
- coordenadas:
  - fonte espacial oficial: KML padrao AVG provisorio, com ajustes analiticos ja definidos para PIC-02 realocado e PIC-11
  - CRS/sistema: WGS84 presumido, a confirmar na auditoria
  - pontos sem coordenada: em apuracao
  - coordenadas fora da faixa esperada: em apuracao
  - variacao por ponto/campanha: em apuracao
  - comparacao com KMZ/KML/shapefile/planilha oficial: em apuracao
  - estrategia aprovada no Gate A: pendente
- ajustes aplicados: de/para taxonomico `Atopsyche` -> `Atopsyche sp.` antes da copia limpa de validacao
- arquivos corrigidos: `scripts/projects/avg/migrar_bentos_avg_2026.py`

## Cadastro E Auditoria De Especies

- especies novas: nenhuma confirmada; ha nome nao padronizado `Atopsyche`
- atributos obrigatorios: auditoria gerada em `outputs/_migration/avg_bentos_2026/auditoria_taxonomia_bmwp_zoobentos_20260721.xlsx`
- campos incertos: 6 taxons sem BMWP requerem decisao tecnica/manual; `Oligochaeta` e `Hirudinea` estao sem ordem/familia, mas nao afetam EPT e `Oligochaeta` continua classificavel para CHOL pelo nome
- ajustes manuais: `Atopsyche` padronizado para `Atopsyche sp.`

## Migracao E Consolidacao

- IDs: projeto 9; grupo Zoobentos
- totais da fonte: 47 campanhas, 13 pontos, 611 pontos-campanha, 611 esforcos, 4.126 resultados, 118 taxons informados na planilha, abundancia total 13.680
- totais preparados: 611 pontos, 611 esforcos, 4.106 resultados agregados, 117 taxons, abundancia total 13.680
- totais no banco: apos migracao, 4.106 linhas em `resultados_zoobentos`, 562 esforcos com resultado, 117 taxons e abundancia total 13.680
- coordenadas no banco/consolidado: em apuracao
- divergencias: nenhuma nos totais globais fonte x consolidado
- backup: `public.bkp_biota_avg_zoobentos_20260721_141031`, com 3.937 linhas; reconsolidacoes apos BMWP geraram `public.bkp_biota_avg_zoobentos_20260721_142319` e `public.bkp_biota_avg_zoobentos_20260721_142813`, ambas com 4.106 linhas
- totais consolidados: 4.106 linhas, 47 campanhas, 13 pontos, 117 taxons, abundancia total 13.680, periodo 2022-08-01 a 2026-06-01

## Configuracao Das Analises

- numero de campanhas: esperado 47
- template: consolidado multicampanha, com paineis temporais e minimapas anuais
- paleta: padrao AVG
- pasta de saida: `Resultados bentos/Consolidado_2026`
- produtos: composicao taxonomica; riqueza por ponto/campanha/ano temporal; abundancia/densidade; diversidade; BMWP/CHOL/EPT; minimapas anuais BMWP/CHOL/EPT; PCoA Bray-Curtis se fizer sentido
- base analitica: `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/zoobentos_consolidated_analytic_base_20260721/base_analitica_consolidada_zoobentos_20260721.xlsx`
- validacao da base: 4.106 registros, 611 ponto-campanhas com esforco, 49 capturas zero, 26 ponto-campanhas nao monitorados pela regra de vigencia, 47 campanhas, 13 pontos, 117 taxons, BMWP nulo = 0
- figura exploratoria substituida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/Consolidado_2026/APROVACAO_06_mini_mapas_anuais_bmwp_chol_ept_zoobentos.png`
- Excel da figura exploratoria: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/Consolidado_2026/APROVACAO_06_df_mini_mapas_anuais_bmwp_chol_ept_zoobentos.xlsx`
- minimapas espelhados Ictiofauna validos para aprovacao: `APROVACAO_06B_mini_mapas_anuais_bmwp_zoobentos.png`, `APROVACAO_06C_mini_mapas_anuais_ept_zoobentos.png`, `APROVACAO_06D_mini_mapas_anuais_chol_zoobentos.png`
- Excel dos minimapas espelhados: `APROVACAO_06BCD_df_mini_mapas_anuais_bmwp_ept_chol_zoobentos.xlsx`
- ajuste visual em 2026-07-21: removido `Nao monitorado` das legendas de BMWP e EPT; CHOL alterado para gradiente verde-vermelho com maiores valores em vermelho.
- resultados selecionados gerados em 2026-07-21:
  - composicao taxonomica por ordem e tabela completa por filo/classe/ordem/familia/taxon
  - riqueza taxonomica, abundancia, densidade, Shannon e Pielou em paineis A4 por grupos de pontos no padrao da Ictiofauna
  - sintese 08C de abundancia por taxon, temporal e espacial; figura com top 30 taxons e Excel com todos os taxons
  - tabelas de grupos bioindicadores BMWP/EPT/CHOL
  - PCoA Bray-Curtis por ano temporal
  - Darwin Core
- manifesto dos resultados selecionados: `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/zoobentos_selected_results_20260721/manifesto_resultados_selecionados_zoobentos_20260721.json`
- revisao taxonomica aplicada em 2026-07-21:
  - `Oligochaeta`: removida ordem `Hemiptera`; ordem mantida em branco
  - `Artropoda` -> `Arthropoda`
  - `Scirtodae` -> `Scirtidae`
  - `Dolychopodidae` mesclado em `Dolichopodidae` (`2` resultados remapeados; taxon duplicado removido)
  - `Turbelaria` -> `Turbellaria`
  - `Melanoides sp.` corrigido para `Mollusca / Gastropoda / Mesogastropoda / Thiaridae`
  - `Acarina` -> `Acari` no nome taxonomico e ordem `Acari`
  - `Sphaeriida` -> `Veneroida`
- lastro da revisao taxonomica: `outputs/_migration/avg_bentos_2026/taxonomia_bentos_avg_revisao_20260721.xlsx` e `outputs/_migration/avg_bentos_2026/taxonomia_bentos_avg_revisao_20260721_aplicada.json`
- reconsolidacao apos revisao taxonomica: backup `bkp_biota_avg_zoobentos_20260721_152855`; consolidado final com 4.106 linhas, 116 taxons e abundancia total 13.680
- validacao pos-revisao: 0 ocorrencias de `Artropoda`, `Scirtodae`, `Dolychopodidae`, `Turbelaria`, `Oligochaeta/Hemiptera` e `Melanoides sp.` fora de `Mollusca` no consolidado e na base analitica
- validacao incremental: `Oligochaeta` permanece como `Annelida / Oligochaeta / <ordem em branco>`; `Acarina` nao aparece mais no consolidado/base, substituido por `Acari`.
- correcao incremental adicional: registro falso `Hemiptera` classificado como `Annelida / Oligochaeta / Hemiptera` mesclado em `Oligochaeta`; 1 resultado remapeado, taxon falso removido.
- validacao incremental adicional: `Annelida / Oligochaeta` possui apenas `Nome_Cientifico = Oligochaeta`, ordem vazia, familia vazia; erro alvo = 0.
- listas pre-geracao em 2026-07-21: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/Consolidado_2026/LISTAS_APROVACAO_composicao_pcoa_amostragem_zoobentos.xlsx`
- decisao aprovada: composicao por ordem em grafico de rosca no modelo da Ictiofauna, com oito ordens principais e agrupamento `Outras ordens`.
- ajuste tecnico aplicado: pontos/campanhas `Nao monitorado` tratados como lacunas nos paineis temporais, nao como zeros.
- PCoA auditada: Bray-Curtis por ano temporal com corte 0,80 forma grupo unico em 2023, 2024 e 2025; em 2026 separa `PIC-01/PIC-03/PIC-11` dos demais pontos.
- geracao final apos aprovacao em 2026-07-21 16:00: resultados tradicionais, rosca de composicao, 08C, PCoA, Excel de apoio, Darwin Core e minimapas BMWP/EPT/CHOL regenerados em `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/Consolidado_2026`.
- validacao pos-geracao final: 32 PNG, 12 XLSX, 115 taxons; erro `Annelida / Oligochaeta / Hemiptera` = 0; `Oligochaeta` permanece com ordem e familia vazias.
- revisao pontual do PCoA em 2026-07-21: figura `07_grafico_pcoa_bray_curtis_por_ano_temporal_zoobentos.png` passou a usar grupos Bray-Curtis 0,80 na legenda de todos os anos, hull para grupos de 2026 e vetores dos taxons mais correlacionados aos eixos; Excel `07_df_pcoa_bray_curtis_zoobentos.xlsx` inclui abas `grupos_bray_080` e `taxons_vetores_pcoa`.
- taxons vetoriais principais em 2026: `Simuliidae`, `Cloeodes sp.`, `Baetidae` e `Elmidae`.
- produto 12 incluido em 2026-07-22: curva de suficiencia amostral de Zoobentos no padrao da Ictiofauna, com 585 unidades amostrais monitoradas, 115 taxons observados, Jackknife 1 final = 126,98 e cobertura observada/estimada = 90,6%; arquivos `12_curva_suficiencia_amostral_zoobentos.png` e `12_df_curva_suficiencia_zoobentos.xlsx`.
- revisao metodologica BMWP aprovada e aplicada em 2026-07-22: `bmwp_score` por campanha/ponto passa a somar familias unicas presentes na amostra, usando `Familia` como chave e `Nome_Cientifico` apenas quando a familia estiver vazia (ex.: `Oligochaeta`).
- minimapas BMWP mantidos como `bmwp_medio` anual das campanhas monitoradas, conforme produto principal conservador; Excel dos minimapas inclui `comparativo_BMWP_anual` com `bmwp_acumulado_anual_familias`, `familias_bmwp_acumuladas` e diferenca acumulado-menos-medio.
- tabela `05_df_grupos_bioindicadores_bmwp_ept_chol_zoobentos.xlsx` atualizada com `bmwp_familias` por campanha/ponto e aba `comparativo_BMWP_anual`.
- efeito da correcao BMWP: maximo por campanha/ponto corrigido para 147 (antes havia valor inflado ate 228 por soma repetida de taxons da mesma familia); media campanha/ponto = 34,34; mediana = 32; 611 ponto-campanhas avaliados.
- produto 13 incluido em 2026-07-22: painel A3 de minimapas anuais dos taxons associados a fauna exotica (`Melanoides sp.`, `Corbicula sp.`, `Physa sp.`), com legenda apenas por taxon e escala de abundancia anual; arquivos `13_mini_mapas_anuais_taxons_associados_fauna_exotica_zoobentos.png` e `13_df_mini_mapas_anuais_taxons_associados_fauna_exotica_zoobentos.xlsx`.
- revisao visual do produto 13: paleta alterada para gradiente amarelo-vermelho e generos em italico na legenda; restante do layout mantido.

## Pendencias

- BMWP de 20 taxons preenchido em `public.especies` por escore unico da familia; auditoria em `outputs/_migration/avg_bentos_2026/bmwp_update_20_taxons_20260721_142311.json`.
- BMWP dos 6 taxons remanescentes preenchido conforme adaptacao Rio das Velhas: `Marilia sp.` = 10, `Odontoceridae` = 10, `Culicidae` = 2, `Dolichopodidae` = 4, `Corbicula sp.` = 1, `Scirtodae` = 0 por nao constar na adaptacao original.
- Auditoria em `outputs/_migration/avg_bentos_2026/bmwp_update_6_taxons_rio_das_velhas_20260721_142802.json`.
- Revisar os produtos selecionados gerados; o painel 08C deve ser tratado como candidato a ajuste visual por ter 117 taxons na base e top 30 na figura.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: pendente
- manifesto: pendente
- patterns: pendente
- portfolio: pendente
- backlog: pendente
