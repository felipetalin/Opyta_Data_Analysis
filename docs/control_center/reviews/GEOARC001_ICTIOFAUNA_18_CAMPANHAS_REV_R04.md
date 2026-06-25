# GEOARC001 - Ictiofauna - 18 campanhas - Revisao R04

## Controle

- projeto: GEOARC001__monitoramento_arcelor
- operacao de origem: docs/control_center/operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md
- revisao: R04
- estado atual: awaiting_revision_approval
- solicitada em: 2026-06-24
- atualizada em: 2026-06-24
- proxima acao: usuario aprovar a figura tecnica de especies ameacadas no Gate R

## Escopo

- solicitacao do usuario: criar figura tecnica em Python, usando pandas e
  matplotlib, para heatmap espacial-temporal de especies ameacadas da
  ictiofauna, destacando registros exclusivamente no ponto `IC-ARC-14`.
- especies alvo:
  - `Harttia torrenticola`
  - `Harttia leiopleura`
- tipo principal: analysis
- tipos secundarios: layout, package
- impacto: R2
- justificativa do impacto: novo produto derivado de CPUEn por especie,
  campanha e ponto, sem alteracao de dados de origem, taxonomia, migracao ou
  consolidacao.
- produtos alvo:
  - `14_df_heatmap_especies_ameacadas_harttia_ictiofauna.xlsx`
  - `14_grafico_heatmap_especies_ameacadas_harttia_ictiofauna.png`
- fora do escopo: alterar figuras existentes, HTML final, manifesto de entrega,
  banco, dados brutos ou formulas ja aprovadas de CPUEn.

## Linha De Base

- baseline: nao existia figura anterior equivalente.
- fonte tecnica: base consolidada carregada pelo pipeline `ictio` para
  `project_id=190`, grupo `Ictiofauna`, com filtro das 18 campanhas do
  GEOARC001.
- lastro visual final:
  - `outputs/_reviews/geoarc001_ictiofauna_R04/final/14_grafico_heatmap_especies_ameacadas_harttia_ictiofauna.png`
  - `outputs/_reviews/geoarc001_ictiofauna_R04/final/14_df_heatmap_especies_ameacadas_harttia_ictiofauna.xlsx`

## Dependencias E Retorno

- Gate A reaberto: nao
- Gate B reaberto: nao
- Gate C reaberto: sim, apenas para configuracao do novo produto tecnico
- banco afetado: nao
- migracao/consolidacao afetadas: nao
- produtos dependentes: nenhum produto existente foi alterado.

## Acao Executada

- criado o script:
  - `scripts/projects/geoarc001/generate_harttia_threatened_heatmap.py`
- o script:
  - aceita planilha/CSV com `nome_campanha`, `nome_ponto`, `especie` e `CPUEn`;
  - quando sem `--input`, carrega a base consolidada do pipeline do GEOARC001;
  - calcula CPUEn por especie, campanha e ponto;
  - mantem todos os pontos e todas as campanhas;
  - gera dois paineis verticais, um por especie;
  - destaca visualmente `IC-ARC-14`;
  - anota valores positivos nas celulas;
  - inclui barra de cores `CPUEn (ind./100 m²)`.

## Arquivos Gerados

- pasta final:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Resultados/Ictiofauna/14_df_heatmap_especies_ameacadas_harttia_ictiofauna.xlsx`
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Arcellor/Arcellor Monitoramento/Produtos/Resultados/Resultados/Ictiofauna/14_grafico_heatmap_especies_ameacadas_harttia_ictiofauna.png`
- dimensoes do PNG: `7093 x 4622` px.
- tamanho do PNG: `705053` bytes.
- tamanho do XLSX: `12257` bytes.

## Validacao Pos-Revisao

- sintaxe Python validada por parse em memoria: `PY_SYNTAX_OK`.
- script executado com sucesso.
- planilha escrita com `xlsx_written=true`.
- tabela final:
  - linhas: `396` (`2 especies x 18 campanhas x 11 pontos`);
  - especies: `Harttia leiopleura`, `Harttia torrenticola`;
  - campanhas: `18`;
  - pontos: `11`;
  - celulas positivas: `9`;
  - pontos positivos: somente `IC-ARC-14`.
- hash final PNG:
  - `E4C6F595EA4005183405E17CC683D2B44A0CC04FB517DAF08D7327948C0BCD20`
- hash final XLSX:
  - `C8F2D9DDBCCAEC62A1FBAE8574B0D23743E0189518ADA149EB1D1D6AEE1095C8`

## Registros Positivos

| Especie | Campanha | Ponto | CPUEn |
| --- | --- | --- | ---: |
| Harttia leiopleura | C007-2023-09-SC | IC-ARC-14 | 2.857143 |
| Harttia leiopleura | C010-2024-06-SC | IC-ARC-14 | 4.285714 |
| Harttia torrenticola | C007-2023-09-SC | IC-ARC-14 | 4.285714 |
| Harttia torrenticola | C008-2023-12-CH | IC-ARC-14 | 2.857143 |
| Harttia torrenticola | C009-2024-03-CH | IC-ARC-14 | 2.857143 |
| Harttia torrenticola | C011-2024-09-SC | IC-ARC-14 | 2.857143 |
| Harttia torrenticola | C012-2024-12-CH | IC-ARC-14 | 1.428571 |
| Harttia torrenticola | C014-2025-06-SC | IC-ARC-14 | 4.285714 |
| Harttia torrenticola | C015-2025-09-SC | IC-ARC-14 | 1.428571 |

## Gate R

- status: awaiting_user_approval
- comparacao antes/depois:
  - antes: nao havia figura especifica para demonstrar a restricao espacial dos
    registros das duas especies ameacadas.
  - depois: figura 14 mostra as duas especies em paineis verticais, todas as
    campanhas, todos os pontos e registros positivos exclusivamente em
    `IC-ARC-14`.

## Pendencias

- aguardar aprovacao do usuario para marcar a R04 como `review_completed`.
