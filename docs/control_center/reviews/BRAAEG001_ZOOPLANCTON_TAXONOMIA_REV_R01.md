# BRAAEG001 - Zooplâncton - Revisão R01 Taxonomia

## Escopo

- Revisão taxonômica pontual de Zooplâncton a partir da lista de correções enviada pelo usuário em 2026-07-29.
- Impacto: `R3`, pois altera cadastro/consolidado e afeta produtos derivados.
- Estado: `approved_regenerated`.

## Correções Aplicadas

- `Ceriodaphinia sp.` corrigido para `Ceriodaphnia sp.`.
- `Cyphoderia ampula` reapontado para o cadastro válido existente `Cyphoderia ampulla`.
- `Trichocerca pussila` corrigido para `Trichocerca pusilla`.
- `Difflugia lithophila` corrigido para `Difflugia litophila`.
- `Lecane arculla` corrigido para `Lecane arcula`, pois a fonte operacional trazia `arculla`, o cadastro válido `Lecane arcula` já existia, e a alteração mínima é remover o `l` duplicado.
- Famílias padronizadas: `Bosminidae`, `Chydoridae`, `Sididae`, `Cyclopidae`, `Synchaetidae`, `Lesquereusiidae` e `Phryganellidae`.
- `Conochilus natans` e `Conochilus coenobasis`: ordem corrigida para `Flosculariida`, mantendo `Conochilidae` como família.
- `Bdelloida`: ordem atualizada para `Bdelloida`; família e gênero como `N.A.`.
- Náuplios e copepoditos de Copepoda mantidos sem atribuição segura de família/gênero (`N.A.`).
- `Ciliado NI` corrigido para `Ciliophora`, removendo a classificação incompatível associada a `Arcella` e removendo `NI` por se tratar de identificação em alta hierarquia.

## Auditoria

- Script: `scripts/projects/braaeg001/fix_taxonomia_zooplancton_r01.py`.
- Dry-run: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo/20260729T090148_fix_taxonomia_zooplancton_r01_braaeg001.xlsx`.
- Apply: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo/20260729T090503_fix_taxonomia_zooplancton_r01_braaeg001.xlsx`.
- Apply complementar com `Difflugia litophila`: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo/20260729T091843_fix_taxonomia_zooplancton_r01_braaeg001.xlsx`.
- Apply complementar com `Lecane arcula`: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo/20260729T092421_fix_taxonomia_zooplancton_r01_braaeg001.xlsx`.
- Apply complementar com `Ciliophora`: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo/20260729T092840_fix_taxonomia_zooplancton_r01_braaeg001.xlsx`.
- Consolidado de Zooplâncton recriado com 423 linhas.
- Verificação pós-aplicação: nomes antigos ausentes no consolidado; termos antigos de família/ordem ausentes.
- Verificação complementar: `Difflugia lithophila` ausente; `Difflugia litophila` presente com 5 ocorrências no consolidado.
- Verificação complementar: `Lecane arculla` ausente; `Lecane arcula` presente com 4 ocorrências no consolidado.
- Verificação complementar: `Ciliophora NI` ausente; `Ciliophora` presente com 14 ocorrências no consolidado.

## Validação Do Usuário

- Aprovação da composição taxonômica recebida em 2026-07-29.
- Tabela isolada para validação:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo/20260729T092920_validacao_tabela_composicao_zooplancton_R01.xlsx`.
- Conteúdo: 57 táxons, com campos `Táxon`, `Filo`, `Classe`, `Ordem`, `Família`, `Gênero`, `Origem`, `Ocorrências`, `Campanhas`, `Tipos de amostragem` e `Densidade quantitativa total`.
- Pacote oficial regenerado após aprovação:
  - saída: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/zooplancton`;
  - auditoria JSON: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/zooplancton/20260729T093103_geracao_resultados_zooplancton_a4_paisagem.json`;
  - auditoria XLSX: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/zooplancton/20260729T093103_geracao_resultados_zooplancton_a4_paisagem.xlsx`;
  - prancha visual: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/zooplancton/20260729T093103_contact_sheet_figuras_zooplancton_a4_paisagem.png`.
- Validação final:
  - `validacao_entrega_zooplancton_braaeg001.json` com status `OK`;
  - 35 arquivos não-manifesto verificados;
  - 14/14 figuras em A4 paisagem, não vazias e com dimensões esperadas;
  - varredura dos produtos finais sem ocorrência dos nomes antigos;
  - figuras 08 e 09 revisadas visualmente, sem cortes críticos de táxons e sem sobreposição da barra de densidade.

## Produto Cartográfico Complementar

- Solicitação em 2026-07-29: gerar minimapa para a inserção de táxons associados à bioindicação ambiental, seguindo as premissas do minimapa de Fitoplâncton.
- Figura: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/zooplancton/13_mini_mapa_taxons_bioindicadores_zooplancton.png`.
- Planilha de apoio: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/zooplancton/13_df_mini_mapa_taxons_bioindicadores_zooplancton.xlsx`.
- Script: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/zooplancton/generate_minimapa_indicadores_zooplancton.py`.
- Auditoria do minimapa: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/zooplancton/20260729T120202_mini_mapa_taxons_bioindicadores_zooplancton.json`.
- Layout final: A4 paisagem, 600 dpi, sem título geral, 6 painéis, com associações ecológicas nas colunas e `C01-Chuva`/`C02-Seca` nas linhas.
- Ajuste visual final: nomes científicos e gêneros acompanhados de `sp.`/`spp.` em itálico nos rótulos inferiores dos painéis.
- Premissa interpretativa: círculos em tamanho fixo; cor representa classe de riqueza por ponto/campanha; o mapa não representa diagnóstico isolado de qualidade ambiental.
- Validação final do pacote após inclusão da figura 13: `validacao_entrega_zooplancton_braaeg001.json` status `OK`, 14/14 figuras.

## Observação Operacional

- A rotina completa de Zooplâncton foi disparada antes da solicitação posterior de gerar somente a tabela.
- Composição aprovada posteriormente; pacote oficial regenerado em 2026-07-29.
