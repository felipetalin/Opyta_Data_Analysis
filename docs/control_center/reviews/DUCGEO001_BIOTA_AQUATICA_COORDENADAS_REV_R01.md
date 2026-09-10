# DUCGEO001 - Biota aquatica - Revisao R01 coordenadas

## Controle

- projeto: DUCGEO001 / Monitoramento Ducal
- grupo: Ictiofauna e Zoobentos
- revisao: R01 - auditoria e correcao potencial de coordenadas
- estado atual: `awaiting_revision_approval`
- aberta em: 2026-07-03
- solicitacao: usuario indicou que as coordenadas do projeto Ducal pareciam incorretas e pediu avaliacao.
- tipo principal: `data`
- impacto: `R3`
- gate afetado se houver apply: Gate A, pois altera dados de ponto migrados e consolidado.
- proxima acao: usuario aprovar comparacao antes/depois no Gate R.

## Linha De Base

- projeto Supabase: `id_projeto=183`, `codigo_interno_opyta=DUCGEO001`.
- operacao original localizada: nao ha registro dedicado em `docs/control_center/operations/`.
- outputs de referencia existentes:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Ducal/Produtos/Resultados/Campanha 05/Ictiofauna`;
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Ducal/Produtos/Resultados/Campanha 05/Zoobentos`.
- metadados de execucao:
  - `outputs/_project_scripts/DUCGEO001__monitoramento_ducal/ictiofauna/execution_metadata.json`;
  - `outputs/_project_scripts/DUCGEO001__monitoramento_ducal/zoobentos/execution_metadata.json`.

## Evidencias

- referencia espacial principal: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Ducal/Geo/Ducal-Ponto_Trilhas-abr-26.kmz`.
- auditoria gerada:
  - JSON: `logs/revisao_ducgeo001_coordenadas/20260703T120538_auditoria_coordenadas_ducgeo001.json`;
  - Excel: `logs/revisao_ducgeo001_coordenadas/20260703T120538_auditoria_coordenadas_ducgeo001.xlsx`.
- auditoria geral da pagina Geoambiental:
  - JSON: `logs/revisao_geoambiental_coordenadas/20260703T132328_auditoria_geoambiental_coordenadas.json`;
  - Excel: `logs/revisao_geoambiental_coordenadas/20260703T132328_auditoria_geoambiental_coordenadas.xlsx`.
- auditoria complementar Biota/Fisico da pagina Geoambiental:
  - JSON: `logs/revisao_geoambiental_coordenadas/20260703T132604_auditoria_geoambiental_coordenadas_biota_fisico.json`;
  - Excel: `logs/revisao_geoambiental_coordenadas/20260703T132604_auditoria_geoambiental_coordenadas_biota_fisico.xlsx`.
- correcao controlada:
  - dry-run: `logs/revisao_geoambiental_coordenadas/20260703T134531Z_dry_run_fix_geoambiental_coordinates.xlsx`;
  - apply: `logs/revisao_geoambiental_coordenadas/20260703T134600Z_apply_fix_geoambiental_coordinates.xlsx`;
  - validacao pos-apply: `logs/revisao_geoambiental_coordenadas/20260703T134637Z_dry_run_fix_geoambiental_coordinates.xlsx`.

## Diagnostico

- total auditado em `public.pontos_coleta`: 25 ponto-campanha.
- pontos OK: 5, todos da campanha `C001-2024-04-SC`.
- pontos a corrigir: 20, correspondentes a `C002-2024-10-CH`, `C003-2025-04-SC`, `C004-2025-10-CH` e `C005-2026-04-SC`.
- causa provavel: a planilha de migracao contem a primeira campanha com coordenadas corretas, mas as campanhas seguintes ficaram com uma sequencia artificial de deslocamento. Em C002-C005 os pontos aparecem em diagonal regular, com incremento constante entre pontos.
- validacao externa: o KMZ mais recente possui `Ictio01` a `Ictio05` e coincide com a coordenada correta por ponto usada em C001.

## Coordenadas De Referencia

| Ponto | Latitude correta | Longitude correta | Fonte |
| --- | ---: | ---: | --- |
| ICTIO01 | -20.1632590877 | -43.4136118424 | `Ducal-Ponto_Trilhas-abr-26.kmz` |
| ICTIO02 | -20.1955096526 | -43.4003222630 | `Ducal-Ponto_Trilhas-abr-26.kmz` |
| ICTIO03 | -20.1926698287 | -43.3569295261 | `Ducal-Ponto_Trilhas-abr-26.kmz` |
| ICTIO04 | -20.1792346941 | -43.3914422400 | `Ducal-Ponto_Trilhas-abr-26.kmz` |
| ICTIO05 | -20.1893337084 | -43.3577074087 | `Ducal-Ponto_Trilhas-abr-26.kmz` |

## Impacto Tecnico

- tabelas afetadas se aprovado:
  - `public.pontos_coleta`: atualizar latitude/longitude por `id_ponto_coleta`;
  - `public.biota_analise_consolidada`: atualizar latitude/longitude por `codigo_interno_opyta`, `nome_campanha` e `nome_ponto`.
- resultados numericos biologicos nao mudam: abundancia, riqueza, CPUE, diversidade e composicao permanecem iguais.
- produtos dependentes que devem ser regenerados se houver coordenadas em saida:
  - pagina Geoambiental do Opyta_Data, que le coordenadas de
    `public.biota_analise_consolidada`;
  - Darwin Core de Ictiofauna;
  - Darwin Core de Zoobentos;
  - qualquer mapa, tabela espacial ou arquivo que exponha latitude/longitude.

## Proposta De Escopo

1. Criar backup transacional da fatia DUCGEO001 em `pontos_coleta` e `biota_analise_consolidada`.
2. Atualizar os 20 ponto-campanha de C002 a C005 para as coordenadas do KMZ por `nome_ponto`.
3. Validar antes/depois no banco, confirmando 25 pontos e 0 divergencias contra KMZ.
4. Regenerar somente produtos que carregam coordenadas, se forem parte da entrega ativa.
5. Apresentar comparacao antes/depois no Gate R.

## Acao Executada

- script usado:
  `scripts/maintenance/fix_geoambiental_coordinates.py --apply`.
- backups criados:
  - `public.backup_pc_ducgeo001_coords_20260703t134600`;
  - `public.backup_bac_ducgeo001_coords_20260703t134600`.
- `public.pontos_coleta`:
  - linhas avaliadas: 25;
  - linhas atualizadas: 20;
  - status antes: 20 `corrigir`, 5 `ok`;
  - status depois: 25 `ok`.
- `public.biota_analise_consolidada`:
  - linhas avaliadas: 214;
  - linhas atualizadas: 149;
  - status antes: 149 `corrigir`, 65 `ok`;
  - status depois: 214 `ok`.
- pontos com variacao de coordenada acima de 5 m antes: 5.
- pontos com variacao de coordenada acima de 5 m depois: 0.
- resultados biologicos nao foram alterados.

## Gate R

- status: awaiting_user_approval.
- comparacao antes/depois:
  - antes: 20 ponto-campanha e 149 linhas consolidadas divergiam da
    referencia espacial aprovada.
  - depois: 25/25 registros em `pontos_coleta` e 214/214 linhas consolidadas
    estao `ok` contra a referencia.
- pendencia operacional: limpar cache/reexecutar o app Streamlit para refletir
  imediatamente a base corrigida.
