# BRAAEG001 - Zoobentos - ajustes de indicadores e rotulos - REV R01

## Controle

- projeto: BRAAEG001 / A&G Mineração
- grupo: Zoobentos
- operação relacionada: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- revisão: R01
- tipo principal: `layout`
- tipos secundários: `analysis`, `text`
- impacto: `R2`
- estado: `awaiting_revision_approval`
- aberta em: 2026-07-28
- atualizada em: 2026-07-28

## Linha De Base

- pacote final anterior: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/bentos`
- pacote final R01 operacional: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/bentos`
- backup pré-R01: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/20260728T103351_backup_pre_R01_ajustes_bentos`
- auditoria anterior de geração: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/20260728T101311_geracao_resultados_zoobentos_a4_paisagem.json`

## Solicitação

- substituir `Ordem não informada` por classificação taxonômica válida com nível entre parênteses.
- aproveitar melhor o espaço lateral das figuras 08 e 09.
- aplicar itálico somente em táxons do tipo `Gênero sp.`.
- adicionar uma similaridade somente por ponto, sem distinguir campanha.
- aplicar cores originais do indicador BMWP e legenda específica.
- separar EPT e CHOL em painéis por indicador.

## Alterações Aplicadas

- figuras 04, 05, 06, 07 e 15: `Oligochaeta` passou a ser exibido como `Oligochaeta (Classe)`.
- figuras 08 e 09: margem esquerda reduzida e itálico aplicado somente a `Sphaerium sp.`.
- figura 11B adicionada: dendrograma de Bray-Curtis por ponto, com campanhas agregadas por ponto.
- figura 13: BMWP exibido por classe do indicador, com legenda `Muito boa`, `Boa`, `Regular`, `Ruim` e `Péssima`.
- figura 14: EPT e CHOL separados em painéis por indicador, com EPT em azul e CHOL em vermelho.
- figura 16 adicionada: minimapa conjunto de BMWP, EPT e CHOL, com indicadores nas colunas e `C01-Chuva`/`C02-Seca` nas linhas.
- relatório HTML, manifesto e validação regenerados.

## Validação Pós-R01

- geração final: `20260729T140450`
- auditoria JSON: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/20260729T140450_geracao_resultados_zoobentos_a4_paisagem.json`
- auditoria XLSX: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/20260729T140450_geracao_resultados_zoobentos_a4_paisagem.xlsx`
- prancha visual: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/20260729T140450_contact_sheet_figuras_zoobentos_a4_paisagem.png`
- validação de entrega: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/bentos/validacao_entrega_zoobentos_braaeg001.json`
- status: `OK`
- figuras checadas: 16/16
- arquivos no manifesto: 38
- erros: 0

## Produto Cartográfico Complementar

- figura: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/bentos/16_mini_mapa_bmwp_ept_chol_zoobentos.png`.
- planilha de apoio: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/bentos/16_df_mini_mapa_bmwp_ept_chol_zoobentos.xlsx`.
- script: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/generate_minimapa_bmwp_ept_chol_zoobentos.py`.
- auditoria do minimapa: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/20260729T141536_mini_mapa_bmwp_ept_chol_zoobentos.json`.
- premissas: A4 paisagem, 600 dpi, hidrografia, rótulos deslocados para pontos próximos, BMWP com cores originais de classe, EPT e CHOL em percentual de abundância.
- ajuste final solicitado: números removidos dos círculos; EPT e CHOL representados por barras de escala percentual; texto auxiliar de valores nos círculos removido.

## Gate R

- estado: aguardando aprovação do usuário.

