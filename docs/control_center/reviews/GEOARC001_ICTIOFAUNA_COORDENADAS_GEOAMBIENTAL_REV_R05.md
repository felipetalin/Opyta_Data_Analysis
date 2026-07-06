# GEOARC001 - Ictiofauna - Revisao R05 coordenadas Geoambiental

## Controle

- projeto: GEOARC001__monitoramento_arcelor
- operacao de origem: docs/control_center/operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md
- revisao: R05
- estado atual: awaiting_revision_approval
- solicitada em: 2026-07-03
- atualizada em: 2026-07-03
- solicitacao: usuario indicou que a parte Geoambiental do Opyta_Data ainda
  exibe coordenadas incorretas.
- tipo principal: data
- impacto: R3
- gate afetado se houver apply: Gate A, pois altera coordenadas ja migradas e
  consolidadas, com reflexo em mapas/produtos espaciais.
- proxima acao: usuario aprovar comparacao antes/depois no Gate R.

## Linha De Base

- projeto Supabase: `id_projeto=190`, `codigo_interno_opyta=GEOARC001`.
- fonte oficial de coordenadas: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Geo/Arcelor_2026.kmz`.
- pagina afetada no app:
  - `G:/Meu Drive/Opyta/Opyta_Data/app/pages/6_Geoprocessamento.py`;
  - `G:/Meu Drive/Opyta/Opyta_Data/core/geoprocessamento/queries.py`;
  - `G:/Meu Drive/Opyta/Opyta_Data/core/geoprocessamento/services.py`.

## Evidencias

- auditoria de `pontos_coleta` contra KMZ oficial:
  - JSON: `outputs/audits/geoarc001_coordinates/geoarc001_coordinate_update_audit_20260703T132159.json`;
  - Excel: `outputs/audits/geoarc001_coordinates/geoarc001_coordinate_update_audit_20260703T132159.xlsx`.
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

- `pontos_coleta` esta consistente com o KMZ oficial:
  - linhas auditadas: 198;
  - status: 198 `ok`;
  - linhas a atualizar: 0;
  - distancia maxima contra KMZ: 0,052 m.
- `public.biota_analise_consolidada` ainda possui variacao indevida de
  coordenadas por ponto:
  - pontos afetados: 9;
  - distancia maxima entre coordenadas do mesmo ponto: 11.722,45 m.
- `public.fisico_analise_consolidada` nao apresentou variacao de coordenadas
  por ponto acima de 5 m na auditoria complementar.
- causa tecnica provavel: `pontos_coleta` foi corrigida ou auditada apos a
  consolidacao, mas `biota_analise_consolidada` manteve coordenadas antigas.
- causa visual na pagina: o Geoambiental de Biota consulta
  `public.biota_analise_consolidada` e agrupa os marcadores por
  `projeto`, `ponto`, `latitude`, `longitude` e `grupo_biologico`; assim,
  multiplas coordenadas para o mesmo ponto aparecem como marcadores separados.

## Impacto Tecnico

- tabela afetada se aprovado:
  - `public.biota_analise_consolidada`: atualizar latitude/longitude por
    `codigo_interno_opyta`, `nome_campanha` e `nome_ponto`, usando
    `public.pontos_coleta` como referencia ja auditada contra KMZ.
- `public.pontos_coleta` nao precisa de ajuste nesta revisao.
- resultados numericos biologicos nao mudam: abundancia, riqueza, CPUEn,
  diversidade e composicao permanecem iguais.
- produtos dependentes:
  - pagina Geoambiental do Opyta_Data;
  - mapas, tabelas ou exportacoes que carreguem latitude/longitude do
    consolidado.

## Proposta De Escopo

1. Criar backup transacional da fatia `GEOARC001` em
   `public.biota_analise_consolidada`.
2. Atualizar latitude/longitude no consolidado a partir de `public.pontos_coleta`
   por projeto, campanha e ponto.
3. Validar antes/depois, confirmando 0 ponto com multiplas coordenadas acima de
   5 m no consolidado.
4. Limpar cache/reexecutar o app Streamlit; a pagina usa cache de 3600 segundos.
5. Apresentar comparacao antes/depois no Gate R.

## Acao Executada

- script usado:
  `scripts/maintenance/fix_geoambiental_coordinates.py --apply`.
- backup criado:
  `public.backup_bac_geoarc001_coords_20260703t134600`.
- linhas avaliadas no consolidado: 150.
- linhas atualizadas no consolidado: 131.
- status antes: 131 `corrigir`, 19 `ok`.
- status depois: 150 `ok`.
- pontos com variacao de coordenada acima de 5 m antes: 9.
- pontos com variacao de coordenada acima de 5 m depois: 0.
- resultados biologicos nao foram alterados.

## Gate R

- status: awaiting_user_approval.
- comparacao antes/depois:
  - antes: a pagina Geoambiental podia exibir o mesmo ponto em coordenadas
    diferentes, gerando marcadores em diagonal.
  - depois: todas as 150 linhas consolidadas de `GEOARC001` ficaram coerentes
    com `pontos_coleta` auditado contra KMZ.
- pendencia operacional: limpar cache/reexecutar o app Streamlit para refletir
  imediatamente a base corrigida.
