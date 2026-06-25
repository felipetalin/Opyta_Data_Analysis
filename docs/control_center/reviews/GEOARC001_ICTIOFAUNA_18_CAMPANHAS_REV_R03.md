# GEOARC001 - Ictiofauna - 18 campanhas - Revisao R03

## Controle

- projeto: GEOARC001__monitoramento_arcelor
- operacao de origem: docs/control_center/operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md
- revisao: R03
- estado atual: awaiting_revision_approval
- solicitada em: 2026-06-24
- atualizada em: 2026-06-24
- proxima acao: usuario aprovar a figura 10 revisada no Gate R

## Escopo

- solicitacao do usuario: ajustar `10_grafico_diversidade_alfa_ictiofauna.png`
  seguindo o padrao de `02_grafico_riqueza_por_ponto_ictiofauna.png`, com letra
  10 no eixo X.
- tipo principal: layout
- tipos secundarios: nenhum
- impacto: R1
- justificativa do impacto: alteracao apenas visual, restrita ao tamanho dos
  rotulos de campanha no eixo X da figura 10.
- produtos alvo:
  - `10_grafico_diversidade_alfa_ictiofauna.png`
  - `10_df_diversidade_alfa_ictiofauna.xlsx`, regenerado por dependencia do
    bloco 10 sem alteracao metodologica.
- fora do escopo: dados brutos, consolidacao, migracao, taxonomia, formulas de
  diversidade, HTML e demais figuras.

## Linha De Base

- pasta/arquivo: pasta final GEOARC001/Ictiofauna indicada pelo usuario.
- baseline preservado em:
  - `outputs/_reviews/geoarc001_ictiofauna_R03/baseline/02_grafico_riqueza_por_ponto_ictiofauna.png`
  - `outputs/_reviews/geoarc001_ictiofauna_R03/baseline/10_grafico_diversidade_alfa_ictiofauna.png`
- hash baseline figura 02: `EC496C9A0DAA9946DD0DBDFA2BA8E2638A3F2AE8109B28A1B4123A79AC73877B`
- hash baseline figura 10: `8324CB903DE0684BC1544E2071715E023A28895A7220BD11D37865E4016F7C61`

## Dependencias E Retorno

- Gate A reaberto: nao
- Gate B reaberto: nao
- Gate C reaberto: nao
- banco afetado: nao
- migracao/consolidacao afetadas: nao
- produtos dependentes: figura 10 e planilha do bloco 10; o HTML aponta para o
  mesmo nome de PNG e nao precisou ser refeito.

## Acao Executada

- `src/opyta_analysis/pipelines/diagnostico/ictio.py`
  - `_small_multiple_diversity` passou a respeitar a chave
    `diversity_campaign_label_size` para os rotulos do eixo X.
- `configs/clients/geoarc001_arcelor.json`
  - adicionada a chave `"diversity_campaign_label_size": 10`.
- bloco 10 executado com o reprodutor do lastro:
  - `python outputs/_project_scripts/GEOARC001__monitoramento_arcelor/ictiofauna/_run_this_analysis.py --block 10`

## Arquivos Regenerados

- `10_df_diversidade_alfa_ictiofauna.xlsx`
- `10_grafico_diversidade_alfa_ictiofauna.png`
- lastro de execucao:
  - `outputs/_project_scripts/GEOARC001__monitoramento_arcelor/ictiofauna/20260624T191103Z_execution_metadata.json`
  - `outputs/_project_scripts/GEOARC001__monitoramento_arcelor/ictiofauna/20260624T191103Z_run_this_analysis.py`

## Validacao Pos-Revisao

- sintaxe Python validada por parse em memoria: `PY_SYNTAX_OK`.
- configuracao JSON validada: `JSON_OK`.
- bloco 10 executado com status `OK`.
- figura revisada preservada em:
  - `outputs/_reviews/geoarc001_ictiofauna_R03/final/10_grafico_diversidade_alfa_ictiofauna.png`
- hash final figura 10: `E8636CCB0849FA2AFB062F1E011CE3B5EFF74C044CD56D996BFA453F7338AD15`
- tamanho baseline: 769166 bytes.
- tamanho final: 807120 bytes.

## Gate R

- status: awaiting_user_approval
- comparacao antes/depois:
  - antes: eixo X da figura 10 tinha rotulos C01-C18 muito pequenos em relacao
    a figura 02.
  - depois: eixo X da figura 10 foi regenerado com rotulos perpendiculares em
    10 pt, mantendo o mesmo padrao de leitura solicitado.

## Pendencias

- aguardar aprovacao do usuario para marcar a R03 como `review_completed`.
