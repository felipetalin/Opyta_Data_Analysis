# WSPKIN001 — Biota aquática — Taxonomia — Revisão R01

## Controle

- projeto: WSPKIN001 / Kinross Bandeirinhas (`id_projeto=211`)
- operacao de origem: migração inicial de Fitoplâncton e Zooplâncton
- revisao: `R01`
- estado atual: `review_completed`
- solicitada em: 2026-09-04
- atualizada em: 2026-09-04
- proxima acao: revisão encerrada; configurar no Gate C as paletas e os demais produtos por grupo.

## Escopo

- solicitacao do usuario: verificar as divergências entre as planilhas validadas por fontes externas e o banco de dados.
- tipo principal: `taxonomy`
- tipos secundarios: `package`
- impacto: `R3`
- produtos alvo: tabelas de composição de Fitoplâncton e Zooplâncton, cadastro `public.especies`, resultados migrados e consolidado de WSPKIN001.
- fora do escopo: alteração no banco sem aprovação explícita de Gate B; figuras, paleta e demais resultados.

## Linha De Base

- fitoplancton: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Controle_Taxonomico_R01\Planilhas_Validadas\01_tabela_composicao_fitoplancton_ALGAEBASE_GBIF_validada.xlsx`
- zooplancton: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Controle_Taxonomico_R01\Planilhas_Validadas\01_tabela_composicao_zooplancton_COL_WoRMS_validada.xlsx`
- banco consultado: `public.especies` e resultados do projeto 211, sem escrita.

## Triagem

| Grupo | Banco | Planilha validada | Divergência confirmada | Situação |
| --- | ---: | ---: | --- | --- |
| Fitoplâncton | 77 táxons | 77 táxons | 48 campos em 35 táxons: 34 reino, 13 autoria, 1 ordem | Aplicável com base no consenso AlgaeBase × GBIF. |
| Zooplâncton | 53 táxons | 53 linhas | 14 campos documentados: 3 nomes, 1 gênero, 10 autorias | Aplicável em parte; há conflitos de duplicidade. |

## Lote Seguro Aplicado

- aprovação: mensagem `siga` do usuário em 2026-09-04, após apresentação explícita do lote seguro e das três pendências.
- aplicado: 59 campos em 45 cadastros globais, sendo 48 campos de Fitoplâncton e 11 campos não conflitantes de Zooplâncton.
- excluído automaticamente: 3 campos associados a `Cyphoderia ampula` e `Trichocerca pussilla`.
- backups: `public.backup_especies_wspkin001_taxonomia_r01_20260904t140332` e `public.backup_biota_wspkin001_taxonomia_r01_20260904t140332`.
- log: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Controle_Taxonomico_R01\Auditoria\20260904t140332_apply_lote_seguro_wspkin001.json`.
- validação: Fitoplâncton passou a coincidir integralmente com a planilha validada; totais permaneceram 124 resultados de Fitoplâncton e 244 de Zooplâncton, iguais no consolidado.
- regeneração: as duas tabelas oficiais de composição foram regeneradas; versões anteriores preservadas em `Controle_Taxonomico_R01\Auditoria\baseline_pre_r01`.

## Pendências Que Exigem Decisão Taxonômica

1. `Cyphoderia ampula` foi fundida em `Cyphoderia ampulla`, conforme decisão do usuário e WoRMS AphiaID 136874: `Chromista / Cercozoa / Imbricatea / Euglyphida / Cyphoderiidae / Cyphoderia`.
2. `Trichocerca pussilla` foi fundida em `T. pusilla` após aprovação do usuário; seis resultados de quatro projetos e seis linhas consolidadas foram redirecionados sem colisão.
3. `Colurella miníma` foi fundida em `Colurella minima`, sem acento e com gênero `Colurella`, conforme decisão do usuário.
4. `Platyias patulus` → `Plationus patulus` foi aplicado no lote seguro, conforme validação CoL × WoRMS.

## Fusão Trichocerca

- aprovação: mensagem `siga` do usuário em 2026-09-04 após recomendação explícita de fundir somente `Trichocerca`.
- origem removida após zerar referências: `Trichocerca pussilla`, `id_especie=100`.
- destino canônico: `Trichocerca pusilla`, `id_especie=4046`, autoria `(Jennings, 1903)`.
- resultados redirecionados: 6, distribuídos por BRAVAL004, GEOHER003 e WSPKIN001; nenhuma colisão por esforço.
- backups: `public.backup_especies_trichocerca_r01_20260904t140721`, `public.backup_resultados_zoo_trichocerca_r01_20260904t140721` e `public.backup_biota_trichocerca_r01_20260904t140721`.
- log: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Controle_Taxonomico_R01\Auditoria\20260904t140721_apply_merge_trichocerca.json`.
- validação: zero referências ao cadastro removido em `especies`, `resultados_zooplancton` e `biota_analise_consolidada`; WSPKIN001 preservou 244 resultados e 244 linhas consolidadas.

## Fusões Cyphoderia E Colurella

- aprovação: decisão taxonômica explícita do usuário em 2026-09-04 e mensagem subsequente `siga`.
- `Cyphoderia ampula` (`id_especie=4010`) fundida em `Cyphoderia ampulla` (`id_especie=82`); 10 resultados redirecionados globalmente.
- `Colurella miníma` (`id_especie=90`) fundida em `Colurella minima` (`id_especie=131`); 10 resultados redirecionados globalmente.
- colisões por esforço: zero para ambas as fusões.
- backups: `public.backup_especies_wspkin001_worms_r01_20260904t141901`, `public.backup_resultados_zoo_wspkin001_worms_r01_20260904t141901` e `public.backup_biota_wspkin001_worms_r01_20260904t141901`.
- log: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Controle_Taxonomico_R01\Auditoria\20260904t141901_apply_merge_cyphoderia_colurella.json`.
- validação: cadastros incorretos e referências residuais zerados; tabela de Zooplâncton regenerada com 51 táxons, mantendo 244 resultados e 244 linhas consolidadas.

## Dependencias E Retorno

- Gate A reaberto: não
- Gate B reaberto: sim
- Gate C reaberto: somente para regenerar as tabelas após a correção aprovada
- banco afetado: sim, cadastro global de espécies e resultados/consolidado dependentes
- coordenadas afetadas: não
- produtos dependentes: ambas as tabelas de composição; produtos analíticos futuros devem usar o cadastro corrigido.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Duas planilhas validadas preservadas. |
| Triagem de tipo e impacto | concluida | Taxonomia/R3; comparação banco × planilha concluída sem escrita. |
| Aprovacao de escopo, se necessaria | concluida | Lote seguro e três fusões aprovados pelo usuário. |
| Correcao | concluida | 59 campos aplicados; Trichocerca, Cyphoderia e Colurella fundidas. |
| Regeneracao de dependencias | concluida no escopo | Duas tabelas de composição regeneradas; demais produtos permanecem fora do Gate C parcial. |
| Validacao da revisao | concluida | Cadastros e referências residuais auditados; totais WSPKIN001 preservados. |
| Gate R — aprovacao final | concluida | Usuário definiu as composições como versões definitivas em 2026-09-04. |
| Promocao e fechamento | concluida | Versões finais organizadas por grupo e material de controle separado. |

## Gate R

- status: `approved`
- apresentado em: 2026-09-04
- aprovado em: 2026-09-04
- registro da aprovacao: usuário solicitou identificar e organizar estas composições como versões definitivas para gerar os demais resultados.

## Aprendizados E Pendencias

- O cadastro de espécies é global: correções de nomes já usados por outros projetos devem ser aplicadas por fusão controlada, com backup e reconciliação de todas as chaves dependentes.
