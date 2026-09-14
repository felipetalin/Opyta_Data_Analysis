# BRACED001 - Fitoplancton - ajustes de produtos R02

## Controle

- projeto: BRACED001 / Fonseca-Biota Aquatica
- grupo: Fitoplancton
- revisao: analise e layout
- impacto: `R1`
- estado atual: `review_completed`
- aberta em: 2026-08-19
- Gate afetado: C
- Gates A e B: preservados

## Escopo Aprovado

- fixar a unidade de densidade como `org/amostra`.
- corrigir a legenda do minimapa para contemplar riquezas superiores a dois taxons.
- afastar as nomenclaturas dos pontos no minimapa.
- adicionar similaridade geral por ponto, sem separar campanhas, conforme o produto 11B de Zooplancton.

## Linha De Base

- entrega R01: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Fitoplancton`
- politica de entrega: substituir sempre a pasta oficial e manter somente `Fitoplancton` em `Produtos/Resultados`.
- banco e taxonomia: sem alteracao nesta revisao.

## Gate R

- pacote: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/reviews/R02_produtos`
- auditoria: `R02_produtos/_auditoria/20260819T194812_geracao_resultados_fitoplancton_a4_paisagem.json`
- contato visual: `R02_produtos/_auditoria/20260819T194812_contact_sheet_figuras_fitoplancton_a4_paisagem.png`
- validacao automatica: `OK`, zero erros e 14/14 figuras validas.
- unidade: `org/amostra` no manifesto e relatorio; nenhuma ocorrencia de `litros` no HTML.
- minimapa: legenda `Riqueza >= 2 taxons`; 18 rotulos organizados em duas colunas internas, sem sobreposicao.
- similaridade geral: matriz e distancias Bray-Curtis 15 x 15; figura 11B revisada visualmente.
- aprovacao: Gate R aprovado pelo usuario em 2026-08-19.
- promocao: 38 arquivos copiados para a pasta oficial, com hashes 38/38 conferidos.
- limpeza: pasta temporaria e backup anterior removidos; somente uma pasta `Fitoplancton` permanece em `Produtos/Resultados`.
- estado: `review_completed`
- criterios: unidade uniforme, minimapa legivel, figura 11B e planilhas coerentes, validacao automatica e revisao visual.
