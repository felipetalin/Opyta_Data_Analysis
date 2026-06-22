# BRAANG01 - AngloGold Meio Fisico

Data do registro: 2026-06-17

## Identidade Supabase

- `id_projeto`: 115
- `codigo_interno_opyta`: `BRAANG01`
- `nome_projeto`: `AngloGold`
- `canonical_key`: `BRAANG01__anglogold`
- empresa nos dados consolidados: `Brandt Meio Ambiente Ltda.`

## Entendimento Tecnico

- objetivo: registrar a decisao sobre a periodicidade dos efluentes `MCB907E` e
  `MCB907S`, para evitar alteracao indevida dos graficos existentes.
- pergunta tecnica: as campanhas de efluente dos pontos `MCB907E` e `MCB907S`
  deveriam ser trimestrais ou mensais?
- matriz: `Efluente`
- pontos avaliados: `MCB907E` e `MCB907S`
- recorte temporal no Supabase consolidado: `2021-01-12` a `2025-06-04`
- dados de origem:
  - `public.fisico_analise_consolidada`, filtrada por
    `codigo_interno_opyta = BRAANG01`
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/Monit_Geral_Efluente_Sanitario_Complexo_CB.xlsx`

## Evidencia De Periodicidade

Na planilha original de efluente, a coluna `Frequencia` registra `Mensal` para
todos os registros dos pontos `MCB907E` e `MCB907S`:

| Ponto | Registros na planilha original | Frequencia observada | Periodo na planilha original |
| --- | ---: | --- | --- |
| `MCB907E` | 894 | `Mensal` | 2020-09-15 a 2025-06-04 |
| `MCB907S` | 898 | `Mensal` | 2020-09-15 a 2025-06-04 |

No Supabase consolidado, os dois pontos aparecem na matriz `Efluente` com 54
datas/campanhas entre 2021 e 2025. Para `pH`, o recorte usado nos graficos
possui 52 campanhas para `MCB907E` e 53 campanhas para `MCB907S`, coerente com
avaliacao mensal e pequenas lacunas pontuais por parametro.

## Decisao

| Decisao | Motivo | Status |
| --- | --- | --- |
| Manter os graficos existentes de efluente como series mensais. | A fonte original e o Supabase indicam frequencia mensal para `MCB907E` e `MCB907S`. | Aprovada pelo usuario em 2026-06-17 |
| Nao criar `Resultados_revisados` neste momento. | A duvida era metodologica, nao estetica; confirmada a frequencia mensal, nao ha necessidade de refazer figuras. | Aprovada pelo usuario em 2026-06-17 |
| Preservar todos os pontos mensais no eixo temporal. | Remover meses transformaria dado mensal em serie trimestral sem respaldo na fonte. | Aprovada |

## Metodologia E Reuso

- pipeline/documentacao relacionados: `docs/README_MEIO_FISICO.md`
- notebook legado localizado:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/Migração e resultados/Resultados/ANGLO-Meio-Físico.ipynb`
- saidas existentes:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/Migração e resultados/Resultados`

## Limitacoes

- A pasta de resultados existente foi gerada por notebook legado, nao por
  execucao auditada do pipeline atual.
- Nao foi criado novo `execution_metadata.json`, porque nao houve nova geracao
  de analises ou graficos.
- A verificacao de periodicidade foi documental e de banco, suficiente para a
  decisao de manter os graficos.

## Aprendizados

- Para `BRAANG01`/AngloGold, nao inferir periodicidade trimestral pela aparencia
  do grafico ou pela densidade do eixo X. A planilha de origem explicita
  `Frequencia = Mensal` para `MCB907E` e `MCB907S`.
- Quando houver muitas campanhas mensais, a melhoria visual recomendada e
  reduzir a densidade dos rotulos do eixo X, nao filtrar campanhas sem decisao
  metodologica explicita.

## Lastro

- recipe: nao criada nesta etapa.
- scripts: nenhum script novo.
- outputs finais: graficos existentes mantidos.
- audit: verificacao manual registrada neste dossie.
- commits: pendente.
