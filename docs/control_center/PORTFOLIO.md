# Portfolio Tecnico

Fonte principal: [portfolio_registry.json](../registry/portfolio_registry.json).

O portfolio nao e uma galeria bonita. Ele e uma biblioteca de respostas
aprovadas para problemas recorrentes.

## Casos De Referencia

| Caso | Quando usar | Status | Fonte |
| --- | --- | --- | --- |
| Series longas com minigraficos temporais | Muitas campanhas e necessidade de leitura por ponto | approved | GEOHER001/Herculano |
| CPUE por ano | Muitas campanhas em ictiofauna, barras ficam ilegíveis por campanha | approved | GEOHER001/Herculano |
| EPT/CHOL com semantica ambiental | Indicador bentonico com leitura "bom vs ruim" | approved | GEOHER001/Herculano |
| Paleta azul Opyta | Produtos Geomil/Ducal/Herculano com identidade azul | approved | Ducal/Porto Estrela/GEOHER001 |
| Figuras para Word em alta resolucao | Relatorios tecnicos com figuras de pagina inteira, paineis e mapas de calor | approved | GEOHER001/Herculano |
| Meio fisico conformidade | Produtos tabulares e graficos por matriz/parametro | reference | SAM Metais |
| Migracao ictiofauna Porto Estrela | Fluxo de validacao e geracao de base analitica | reference | BIOPOR001 |
| Project 165 fauna multi-grupo | Pipeline historico multi-grupo | reference | ITAGUA001 |

## Como Usar

Antes de criar grafico novo, responder:

- existe um caso parecido aqui?
- o padrao esta `approved`, `reference` ou `deprecated`?
- quais limitacoes foram registradas?
- precisa virar pattern reutilizavel em `src/opyta_analysis`?

## Como Promover Um Caso

Um caso entra no portfolio quando:

- resolveu um problema recorrente;
- foi aprovado visualmente ou metodologicamente;
- tem script/função rastreavel;
- tem exemplo ou projeto de origem;
- tem limitacoes conhecidas.
