# BRAAEG001 - Fitoplâncton - Revisão R02 - Painéis Por Estação

## Controle

- projeto: BRAAEG001 / A&G Mineração
- grupo: Fitoplâncton
- operação original: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- tipo principal: `layout`
- tipo secundário: `analysis`
- impacto: `R2` sem alteração de banco, migração ou taxonomia
- estado: `awaiting_revision_approval`
- aberta em: 2026-07-28
- atualizada em: 2026-07-28
- próxima ação: revisar pacote final regenerado e registrar aprovação no Gate R

## Solicitação

Usuário aprovou a separação por estação/campanha nos gráficos de Fitoplâncton após avaliação técnica:

- aplicar painéis por estação/campanha nos gráficos de riqueza, densidade total, densidade por táxon e mapa de calor táxon x ponto;
- ajustar Shannon para ponto + campanha/estação;
- manter similaridade agrupada, sem separar por estação.

## Linha De Base

- pacote original: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/fitoplancton`
- backup pré-revisão: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T095638_backup_pre_R02_layout_estacoes_fitoplancton`
- auditoria da versão anterior: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T093352_geracao_resultados_fitoplancton_a4_paisagem.json`

## Alterações Executadas

- script revisado: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/generate_fitoplancton_results_a4_landscape.py`
- gráficos alterados:
  - `02_grafico_riqueza_por_ponto_fitoplancton.png`: painéis `C01-Chuva` e `C02-Seca`;
  - `03_grafico_densidade_total_por_ponto_fitoplancton.png`: painéis `C01-Chuva` e `C02-Seca`;
  - `08_grafico_densidade_por_taxon_fitoplancton.png`: painéis por estação, mesma escala de densidade;
  - `09_grafico_densidade_taxon_ponto_fitoplancton.png`: mapa de calor em dois painéis, mesma escala de cor;
  - `10_grafico_diversidade_alfa_fitoplancton.png`: Shannon por ponto e campanha/estação, com Pielou como marcador auxiliar.
- similaridade preservada:
  - `11_dendrograma_similaridade_fitoplancton.png` permaneceu agrupado, sem separação por estação.

## Validação

- compilação: `python -m py_compile outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/generate_fitoplancton_results_a4_landscape.py`
- geração final: `20260728T095935`
- auditoria JSON: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T095935_geracao_resultados_fitoplancton_a4_paisagem.json`
- auditoria XLSX: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T095935_geracao_resultados_fitoplancton_a4_paisagem.xlsx`
- prancha visual: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/fitoplancton/20260728T095935_contact_sheet_figuras_fitoplancton_a4_paisagem.png`
- validação de entrega: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/fitoplancton/validacao_entrega_fitoplancton_braaeg001.json`
- resultado:
  - status `OK`;
  - 33 arquivos finais;
  - 12 figuras PNG;
  - 17 planilhas XLSX;
  - 12/12 figuras em A4 paisagem, 7014 x 4962 px, 600 dpi;
  - 0 arquivos com tamanho zero;
  - 0 figuras em branco;
  - 0 erros.

## Comparação Antes/Depois

- antes: gráficos 02, 03 e 08 usavam comparação lado a lado em eixo único; gráfico 09 usava 24 colunas no mesmo mapa; gráfico 10 mostrava Shannon agregado por campanha.
- depois: gráficos 02, 03, 08, 09 e 10 usam leitura por estação/campanha; o gráfico 10 passou a refletir ponto + estação, conforme solicitação do usuário.
- dados, migração, taxonomia, Darwin Core e planilhas consolidadas não foram alterados por esta revisão.

## Gate R

- estado: `awaiting_revision_approval`
- pendência: aprovação final do usuário sobre o pacote revisado.
