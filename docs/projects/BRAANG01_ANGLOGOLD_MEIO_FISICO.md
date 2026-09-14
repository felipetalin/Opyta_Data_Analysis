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

## Atualizacoes De Revisao

### 2026-07-09 - Periodicidade De Efluente

O usuario informou que sera necessario mudar a periodicidade dos pontos
`MCB907E` e `MCB907S`. Antes da mudanca, foi registrado o estado atual:

- matriz de resultados de `Efluente`: 54 campanhas por ponto, de `jan-2021` a
  `jun-2025`;
- campanhas atuais na matriz: todos os meses de 2021, 2022, 2023 e 2024, mais
  `jan-2025`, `fev-2025`, `mar-2025`, `abr-2025`, `mai-2025` e `jun-2025`;
- fonte original: 58 datas unicas por ponto, incluindo tambem
  `2020-09-15`, `2020-10-07`, `2020-11-12` e `2020-12-10`;
- a coluna `Frequencia` na fonte permanece `Mensal` para todos os registros
  desses pontos.

Esta atualizacao substitui a decisao operacional de manter os graficos como
mensais apenas quando houver nova configuracao de periodicidade aprovada e
executada.

### 2026-07-09 - Agua Subterranea, Uso De Dessedentacao

O usuario solicitou revisao dos graficos de `Agua Subterranea` para manter
somente o uso de `dessedentacao animal` nas linhas de VMP, eliminando os demais
usos exibidos no grafico e preservando o layout aprovado.

Registro de revisao:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_AGUA_SUBTERRANEA_REV_R01.md`

Pasta de revisao criada:

- `Resultados/_revisoes/R01_agua_subterranea_dessedentacao_20260709`

### 2026-07-09 - Efluente MCB907, Periodicidade Grafica

O usuario aprovou a opcao 01 para revisar os graficos de efluente dos pontos
`MCB907E` e `MCB907S` com corte a partir de 2021.

Registro de revisao:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_EFLUENTE_MCB907_REV_R02.md`

Pasta de revisao criada:

- `Resultados/_revisoes/R02_efluente_mcb907_periodicidade_20260709`

Escopo aprovado:

- 13 parametros com campanhas selecionadas de `jan-2021` a `jun-2025`;
- DBO mantida como serie mensal em grafico separado;
- graficos revisados restritos a `MCB907E` e `MCB907S`.

Observacao operacional:

- as campanhas de 2020 existem na planilha-fonte, mas nao entram nesta revisao
  porque o usuario aprovou o corte a partir de 2021.

### 2026-07-09 - Agua Superficial, Padrao Visual R04

O usuario solicitou aplicar o padrao visual da revisao R04 a todos os
parametros de `Agua Superficial`, preservando os VMPs nos graficos.

Registro de revisao:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_AGUA_SUPERFICIAL_REV_R04.md`

Pasta de revisao:

- `Resultados/_revisoes/R04_agua_superficial_20260709`

Lastro tecnico:

- `outputs/_project_scripts/BRAANG01__anglogold_meio_fisico/meio_fisico`

Resultado:

- 34 graficos temporais gerados no padrao R04;
- VMPs corrigidos para usar `vmp_357_cl2_min`, `vmp_357_cl2_max` e
  `vmp_amonia_dinamico`, quando preenchidos no consolidado;
- parametros sem VMP preenchido no consolidado permanecem sem linha de VMP.

### 2026-07-10 - Agua Subterranea, VMPs Em Dissolvidos R05

O usuario identificou erro tecnico na interpretacao dos VMPs de parametros
dissolvidos/soluveis em Agua Subterranea. Foi aberta a revisao R05 para gerar
somente os parametros necessarios, preservando o layout aprovado da R01.

Registro de revisao:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_AGUA_SUBTERRANEA_REV_R05.md`

Pasta de revisao:

- `Resultados/_revisoes/R05_agua_subterranea_vmp_dissolvidos_20260710`

Lastro tecnico:

- `outputs/_project_scripts/BRAANG01_ANGLO_MEIO_FISICO`

Resultado:

- 18 graficos temporais gerados;
- limite legal da Resolucao CONAMA 396/2008 aplicado por equivalencia do
  analito para
  `Arsenio Dissolvido`, `Cobalto Dissolvido`, `Cobre Dissolvido`,
  `Cromo Dissolvido` e `Zinco Dissolvido`;
- `Arsenio Total` e `Sulfato` mantiveram limite legal do consolidado;
- `Solidos Dissolvidos Totais` foi gerado sem linha de limite, pois o limite
  existente e de consumo humano, nao de dessedentacao;
- `pH` foi gerado sem linha de limite, por ausencia de limite legal
  identificado na CONAMA 396/consolidado.

### 2026-07-10 - Efluente, DBO Separada Por Grupo R06

O usuario solicitou regerar a DBO em efluentes separando `MCB907E/MCB907S`
juntos e `MCB1005` em figura separada.

Registro de revisao:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_EFLUENTE_DBO_REV_R06.md`

Pasta de revisao:

- `Resultados/_revisoes/R06_efluente_dbo_pontos_20260710`

Resultado:

- 2 graficos temporais mensais gerados;
- `MCB907E` e `MCB907S` agrupados em uma figura com 19 campanhas
  trimestrais/selecionadas;
- `MCB1005` gerado em figura separada com serie mensal;
- VMP confirmado em `60 mg/L` para os tres pontos via `vmp_430_padrao`.

### 2026-07-10 - Agua Subterranea, Cenario R05 Todos Os VMPs

Foi gerado um pacote demonstrativo da R05 de Agua Subterranea com todos os usos
da Resolucao CONAMA 396/2008, para apresentacao ao cliente.

Registro:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_AGUA_SUBTERRANEA_R05_TODOS_VMPS.md`

Pasta:

- `Resultados/_revisoes/R05_todos_os_vmps_20260710`

Resultado:

- 18 graficos temporais gerados;
- figura-tabela dos VMPs por uso gerada em
  `Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.png`;
- figura-tabela de resultados violados gerada em
  `Tabela_Violacoes_VMPs_CONAMA396_Agua_Subterranea_R05.png`;
- figura-tabela de valores reais por ponto gerada em
  `Tabela_Valores_Reais_VMP_Agua_Subterranea_R05.png`;
- linhas de VMP por uso quando existentes: consumo humano, dessedentacao,
  irrigacao e recreacao;
- `Solidos Dissolvidos Totais` com apenas consumo humano;
- `pH` sem linhas de VMP.

### 2026-07-13 - Efluente, Eficiencia De Remocao De DBO R07

Foi gerado o pacote R07 para validar a eficiencia da ETE pelo par
`MCB907E`/`MCB907S`, usando `MCB907E` como entrada e `MCB907S` como saida.

Registro:

- `docs/control_center/reviews/BRAANG01_MEIO_FISICO_EFICIENCIA_DBO_ETE_REV_R07.md`

Pasta:

- `Resultados/_revisoes/R07_eficiencia_dbo_ete_20260713`

Produtos:

- grafico de eficiencia de remocao de DBO;
- planilha Excel com abas `eficiencia_por_campanha`, `nao_atende` e `resumo`;
- CSV equivalente;
- manifesto SHA256 e metadado de geracao.

Resultado:

- criterio aplicado: remocao minima de `60%`;
- campanhas avaliadas: `19`;
- campanhas conformes: `16`;
- campanhas abaixo de 60%: `jun-2023`, `jun-2024` e `nov-2024`;
- eficiencia media simples: `80,5%`;
- eficiencia ponderada por carga de entrada: `92,7%`.

## Metodologia E Reuso

- pipeline/documentacao relacionados: `docs/README_MEIO_FISICO.md`
- notebook legado localizado:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/Migração e resultados/Resultados/ANGLO-Meio-Físico.ipynb`
- saidas existentes:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/Migração e resultados/Resultados`
- lastro tecnico de revisoes:
  `outputs/_project_scripts/BRAANG01__anglogold_meio_fisico/meio_fisico`

## Limitacoes

- A pasta de resultados existente foi gerada por notebook legado, nao por
  execucao auditada do pipeline atual.
- A revisao R04 possui metadado especifico de geracao em
  `outputs/_project_scripts/BRAANG01__anglogold_meio_fisico/meio_fisico`,
  mas nao substitui o notebook legado como pipeline historico completo.
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
- scripts: `outputs/_project_scripts/BRAANG01__anglogold_meio_fisico/meio_fisico`.
- outputs finais: graficos revisados em
  `Resultados/_revisoes/R04_agua_superficial_20260709`.
- audit: manifesto e metadado R04 registrados no lastro tecnico.
- commits: pendente.
