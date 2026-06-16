# Decisao Do Tipo De Analise

Esta etapa acontece antes da recipe final e antes de gerar graficos.

## Objetivo

Escolher quais analises fazem sentido para o projeto, considerando:

- numero de campanhas;
- numero de pontos;
- grupo biologico ou matriz;
- objetivo tecnico do produto;
- qualidade e completude dos dados;
- padroes aprovados no portfolio.

## Quando Decidir

A decisao deve acontecer depois de:

1. confirmar identidade Supabase;
2. localizar dados;
3. definir recorte temporal;
4. definir recorte espacial;
5. revisar lastros e referencias.

E antes de:

1. escrever scripts finais;
2. gerar figuras em lote;
3. montar relatorio;
4. aprovar pasta final de entrega.

## Classificacao Inicial

| Dimensao | Baixa complexidade | Media complexidade | Alta complexidade |
| --- | --- | --- | --- |
| Campanhas | 1 a 4 | 5 a 8 | 9 ou mais |
| Pontos | 1 a 5 | 6 a 12 | 13 ou mais |
| Grupos | 1 | 2 | 3 ou mais |
| Objetivo | descritivo | comparativo | diagnostico + tendencia + sintese |

## Regras De Decisao

| Situacao | Caminho recomendado |
| --- | --- |
| Poucas campanhas e poucos pontos | barras, pontos, tabelas sinteticas e mapas simples |
| Poucas campanhas e muitos pontos | rankings, mapas, barras horizontais e paineis por trecho |
| Muitas campanhas e poucos pontos | linhas, minigraficos temporais e medias gerais |
| Muitas campanhas e muitos pontos | minigraficos, paineis por ano, sinteses por classe/trecho e heatmaps apenas como apoio |
| Dados com esforco amostral variavel | CPUE, normalizacao por esforco e alertas metodologicos |
| Diagnostico ambiental | indicadores, categorias ecologicas, grupos sensiveis/tolerantes e sintese interpretativa |
| Produto executivo | poucos graficos fortes, tabelas decisivas e narrativa curta |
| Produto tecnico completo | conjunto modular: QA, composicao, riqueza, abundancia, diversidade, indicadores e sintese |

## Saida Esperada

Antes de rodar a analise, produzir um mapa de decisao com:

- modulos selecionados;
- modulos descartados;
- justificativa tecnica;
- padroes graficos usados;
- nivel de complexidade;
- riscos de layout;
- produtos finais esperados.

## Portfolio

Consultar:

- [Portfolio de Analises](../portfolio_analises/README.md)
- [Portfolio HTML](../portfolio_analises/index.html)
