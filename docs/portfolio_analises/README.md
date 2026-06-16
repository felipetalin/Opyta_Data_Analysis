# Portfolio De Analises

Este portfolio e o ponto de decisao para escolher o tipo de analise antes de
gerar scripts ou outputs finais.

## Uso

1. Classificar o estudo por numero de campanhas e pontos.
2. Definir o objetivo tecnico principal.
3. Selecionar modulos analiticos.
4. Escolher representacoes graficas adequadas ao volume de dados.
5. Registrar a decisao no dossie do projeto e na recipe.

## Ponto De Decisao

O tipo de analise deve ser decidido no `inicio_analise`, depois do entendimento
dos dados e antes da execucao.

Fluxo:

`dados -> complexidade -> objetivo -> modulos -> graficos -> recipe -> execucao`

## Catalogo Inicial

| Modulo | Melhor uso | Graficos recomendados | Evitar quando |
| --- | --- | --- | --- |
| QA e completude | qualquer projeto | tabela de lacunas, matriz campanha x ponto | nunca |
| Composicao taxonomica | biota aquatica/fauna | barras horizontais, rosca com top N, tabela | ha excesso de categorias sem agrupamento |
| Riqueza temporal | series medias/longas | minigraficos, linhas por ponto, media geral | barras com muitas campanhas |
| Abundancia/CPUE | esforco variavel | barras por ano, linhas, pequenos multiplos | valores sem esforco padronizado |
| Diversidade alfa | comparacao ponto/campanha | minigraficos, boxplots, linhas | amostras muito incompletas |
| Diversidade beta/estrutura | comunidades | dendrograma, NMDS/PCoA, turnover | poucos pontos/campanhas |
| Indicadores ecologicos | diagnostico | EPT/CHOL, BMWP, grupos funcionais | classificacao taxonomica incerta |
| Espacial | muitos pontos/trechos | mapas, rankings por trecho, paineis | ausencia de coordenadas/conectividade |
| Sintese executiva | decisao tecnica | scorecards, quadros resumo, top achados | quando substitui evidencias essenciais |

## Cardapio De Exemplos Reais

O cardapio principal deve mostrar exemplos reais ja desenvolvidos pela Opyta.
Cada card deve funcionar como uma ficha de restaurante: imagem do produto,
contexto de uso, projeto de origem, especificacao tecnica e caminho do lastro.

Exemplos iniciais embarcados no HTML:

| Modelo | Exemplo real | Projeto | Thumbnail |
| --- | --- | --- | --- |
| M01 - Minigraficos temporais | Riqueza temporal por ponto em zoobentos | GEOHER001/Herculano | `assets/thumbs/m01_herculano_bentos_riqueza_temporal.png` |
| M02 - Barras por ano | CPUEn anual em ictiofauna | GEOHER001/Herculano | `assets/thumbs/m02_herculano_ictio_cpuen_ano.png` |
| M03 - Ranking horizontal | Tornado de CPUE por especie | BIOPOR001/Porto Estrela | `assets/thumbs/m03_porto_estrela_tornado_especies.png` |
| M04 - Indicadores ecologicos | EPT/CHOL em zoobentos | GEOHER001/Herculano | `assets/thumbs/m04_herculano_bentos_ept_chol.png` |
| M05 - Composicao taxonomica | Percentual por ordem | BIOPOR001/Porto Estrela | `assets/thumbs/m05_porto_estrela_composicao_ordem.png` |
| M06 - Sintese executiva | Painel editorial de diversidade | BIOPOR001/Porto Estrela | `assets/thumbs/m06_porto_estrela_dashboard_editorial.png` |

## Ficha Tecnica Dos Modelos

Cada modelo analitico deve ter uma ficha tecnica antes de ser usado em uma
recipe. A ficha minima e:

- objetivo do modelo;
- quando usar;
- quando evitar;
- dados necessarios;
- formato da figura;
- DPI;
- familia e tamanho de fonte;
- dimensao em polegadas/centimetros;
- saidas esperadas;
- referencias de projeto/padrao.

### Especificacao grafica base

| Uso | Tamanho | DPI | Fonte | Titulo | Eixos/rotulos | Legenda | Observacao |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| Relatorio tecnico A4 paisagem | 11.69 x 8.27 in | 600 | Arial/DejaVu Sans | 12-14 pt | 8-10 pt | 8-9 pt | padrao para muitas campanhas |
| Relatorio tecnico A4 retrato | 8.27 x 11.69 in | 600 | Arial/DejaVu Sans | 12-14 pt | 8-10 pt | 8-9 pt | tabelas, rankings e mapas verticais |
| Documento executivo | 10 x 5.6 in | 300-600 | Arial/DejaVu Sans | 13-15 pt | 9-10 pt | 9 pt | menos elementos e maior contraste |
| HTML interativo/consulta | responsivo | 144-300 | system sans-serif | 16-22 px | 12-14 px | 12-13 px | usar cards, filtros e tabelas |

### Modelos iniciais

| Modelo | Melhor para | Figura base | Saidas |
| --- | --- | --- | --- |
| Minigraficos temporais com media geral | series longas, muitos pontos | A4 paisagem, 600 DPI, fonte 8-12 pt | PNG + XLSX de dados |
| Barras por ano/periodo | CPUE, abundancia, classes com muitas campanhas | A4 paisagem, 600 DPI, fonte 8-12 pt | PNG + XLSX |
| Barras horizontais/ranking | muitos pontos ou especies | A4 retrato ou paisagem, 600 DPI, fonte 8-12 pt | PNG + XLSX |
| Indicadores ecologicos | EPT/CHOL, BMWP, grupos tolerantes/sensiveis | A4 paisagem, 600 DPI, fonte 8-12 pt | PNG + tabela interpretativa |
| Composicao taxonomica top N | muitas categorias taxonomicas | A4 paisagem, 600 DPI, fonte 8-12 pt | PNG + tabela completa |
| Sintese executiva | decisao e apresentacao curta | 10 x 5.6 in ou HTML, 300-600 DPI | PNG/HTML + tabela resumo |

## Regras Para Muitas Campanhas

Quando houver 9 ou mais campanhas:

- priorizar minigraficos temporais;
- agrupar barras por ano ou periodo hidrologico;
- usar medias gerais como linha/valor de referencia;
- reduzir rotulos no eixo e mover detalhes para tabela;
- evitar barras longas campanha x ponto;
- usar heatmap apenas quando a pergunta for matriz de intensidade/presenca.

## Regras Para Poucas Campanhas

Quando houver ate 4 campanhas:

- priorizar barras, pontos e comparacoes diretas;
- usar mapas e rankings quando houver muitos pontos;
- evitar modelos temporais ou tendencias fortes;
- deixar claro que a inferencia e descritiva.

## HTML

Abrir [index.html](index.html) no navegador para usar a matriz visual de decisao.
O HTML inclui thumbnails reais de graficos/prototipos ja desenvolvidos e,
abaixo, fichas tecnicas base para orientar specs de novos produtos.
