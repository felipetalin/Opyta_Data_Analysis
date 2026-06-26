# VIRITA001 - Ictiofauna - Campanha 1 - Revisao R01

## Controle

- projeto: `VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`
- operacao de origem: `docs/control_center/operations/VIRITA001_ICTIOFAUNA_CAMPANHA_1.md`
- revisao: `R01`
- estado atual: `awaiting_revision_approval`
- solicitada em: 2026-06-25
- atualizada em: 2026-06-25
- proxima acao: aprovar a revisao de dados no Gate R

## Escopo

- solicitacao do usuario: avaliar a planilha alterada
  `Opyta-Virtual-Itabrita-Ictio-2026_260621_MIGRACAO_CORRIGIDA.xlsx`,
  com mudancas de esforco, tipo de esforco e nomenclatura da campanha.
- tipo principal: `data`
- tipos secundarios: `analysis`, `text`, `package`
- impacto: `R3`
- produtos alvo: banco migrado, consolidado, recipe, lastro, planilhas, figuras,
  HTML tecnico, evidencias, validacao textual e manifesto da Campanha 1.
- fora do escopo: cadastro ou alteracao taxonomica de especies, troca de
  template/paleta e ajustes visuais previamente planejados.

## Linha De Base

- pasta/arquivo:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Resultados/Ictiofauna/Campanha_1`
- versao/data: produtos gerados em 2026-06-22.
- manifesto:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Resultados/Ictiofauna/Campanha_1/manifesto_entrega_ictiofauna_campanha_1.json`
- hashes: `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita/ictiofauna/execution_metadata.json`
  registra 27 arquivos principais com `sha256`.
- snapshot/backup:
  - `outputs/_snapshots/VIRITA001_R01_before_20260625/Campanha_1`
  - `public.backup_virita001_r01_pontos_20260625t175139z`
  - `public.backup_virita001_r01_esforcos_20260625t175139z`
  - `public.backup_virita001_r01_resictio_20260625t175139z`
  - `public.backup_virita001_r01_consol_20260625t175139z`
  - `public.backup_biota_before_vr01_20260625t175139z`

## Dependencias E Retorno

- Gate A reaberto: sim
- Gate B reaberto: nao, salvo se houver nova alteracao taxonomica.
- Gate C reaberto: nao, salvo se houver troca de template, paleta ou conjunto
  de produtos.
- banco afetado: sim
- produtos dependentes: validacao, migracao, consolidacao, analises, HTML,
  evidencias, manifesto e lastro.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Lastro 20260622T115015Z e pasta final da Campanha 1 identificados. |
| Triagem de tipo e impacto | concluida | Mudanca de fonte/campanha/esforco classificada como `data/R3`. |
| Validacao preliminar | concluida | Validadores executados em 2026-06-25. |
| Aprovacao de escopo | concluida | Usuario informou que ajustou manualmente a planilha e autorizou seguir em 2026-06-25. |
| Correcao | concluida | Planilha revalidada; divergencias de esforco resolvidas. |
| Regeneracao de dependencias | concluida | Remigracao, consolidacao, recipe, produtos, HTML, evidencias e manifesto atualizados. |
| Validacao da revisao | concluida | Auditoria oficial de fauna `OK`, validacao textual `OK`, banco x planilha sem divergencias. |
| Gate R - aprovacao final | aguardando usuario | Pacote revisado apresentado para aprovacao. |
| Promocao e fechamento | pendente | |

## Alteracoes Avaliadas

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Campanha | `ITA001_AH2526_202606` no banco/config/produtos | `C001-2026-06-SC` na planilha alterada | Padronizacao da nomenclatura da campanha. |
| Linhas de esforco | 9 linhas registradas no dossie original | 7 linhas na planilha alterada, uma por ponto | Revisao de esforco amostral. |
| Matriz quantitativa | Produtos atuais de abundancia/CPUE usam `Ictio_06` e `Ictio_07` | Planilha alterada marca capturas quantitativas tambem em `Ictio_02`, `Ictio_03` e `Ictio_05` | Mudanca de tipo de esforco/amostragem. |
| Esforco nos resultados | Divergente em 5 linhas | Precisa ser sincronizado com `Metadados_Esforco` ou confirmado como intencional | Aviso dos validadores. |
| Cadastro de especies | Sete especies incrementais ja cadastradas | Nao usar cadastro incremental nesta revisao | Evitar upsert em especies existentes. |
| Resultados agregados | 20 linhas em `ITA001_AH2526_202606` | 19 linhas em `C001-2026-06-SC` | Mudanca de campanha/esforco/tipo de amostragem. |
| Consolidado | 20 linhas para a campanha antiga | 19 linhas para a campanha corrigida | Cadeia posterior regenerada. |

## Previa Numerica

Usando `Metadados_Esforco` como fonte de esforco na planilha alterada:

| Ponto | Abundancia | Biomassa g | Esforco | CPUEn | CPUEb |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Ictio_02` | 4 | 82.0 | 30 | 13.33 | 273.33 |
| `Ictio_03` | 11 | 132.0 | 60 | 18.33 | 220.00 |
| `Ictio_05` | 55 | 121.5 | 110 | 50.00 | 110.45 |
| `Ictio_06` | 5 | 1166.0 | 120 | 4.17 | 971.67 |
| `Ictio_07` | 57 | 4625.0 | 120 | 47.50 | 3854.17 |

Totais: 132 individuos, 15 especies, 5 pontos quantitativos com captura.

## Avisos Resolvidos Ou Aceitos

- `RESULT_EFFORT_VALUE_DIFFERS_FROM_METADATA`: resolvido na planilha ajustada.
- `RESULT_GROUPS_WILL_BE_AGGREGATED`: 6 grupos de resultado possuem multiplas
  linhas e foram agregados por campanha+ponto+metodo+tipo+especie.

## Arquivos Regenerados

- Banco base: campanha antiga removida de forma escopada; campanha
  `C001-2026-06-SC` migrada com 7 pontos, 7 esforcos e 19 resultados.
- Consolidado: `biota_analise_consolidada` regenerada com 22.473 registros
  totais; fatia VIRITA001/Ictiofauna com 19 linhas.
- Recipe: `configs/projects/virita001_itabrita_ictiofauna.json`.
- Gerador HTML: `scripts/projects/virita001/generate_ictio_html_report.py`.
- Produtos finais: 16 planilhas XLSX, 15 figuras PNG, 1 HTML tecnico, 2 JSONs
  e 1 manifesto.
- Lastro:
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita/ictiofauna/20260625T181107Z_execution_metadata.json`.
- Relatorios de validacao criados em:
  - `outputs/validacoes/virita001_itabrita_revisao_dados/`
  - `outputs/validacoes/virita001_itabrita_revisao_dados_oficial/`
  - `outputs/validacoes/virita001_itabrita_revisao_dados_oficial_sem_species/`

## Validadores

- `python scripts/validation/validar_migracao_ictiofauna.py --skip-db`:
  0 bloqueios, 4 avisos, `pode_prosseguir=true`.
- Validacao oficial com cadastro incremental:
  1 bloqueio, 9 avisos, `pode_prosseguir=false`; bloqueio por especies ja
  existentes no banco, portanto fora do escopo desta revisao de dados.
- Validacao oficial sem cadastro incremental:
  0 bloqueios, 2 avisos, `pode_prosseguir=true`.
- Validacao oficial pos-ajuste sem cadastro incremental:
  0 bloqueios, 1 aviso de agregacao esperada, `pode_prosseguir=true`.
- Comparacao planilha agrupada x banco:
  19 grupos esperados, 19 grupos no banco, 0 divergencias, 132 individuos.
- Auditoria oficial de fauna:
  `OK`, 0 erros, 0 avisos.
- Validacao textual:
  `OK`, 0 erros, 0 avisos.

## Gate R

- status: `awaiting_revision_approval`
- apresentado em: 2026-06-25
- aprovado em:
- registro da aprovacao:

## Aprendizados E Pendencias

- A revisao deve tratar apenas dados/campanha/esforco; especies ja estao no
  banco e nao devem ser reupsertadas.
- Arquivos temporarios `~$` do Excel devem ser ignorados em manifestos e
  auditorias de entrega.
- A revisao esta tecnicamente concluida; falta aprovacao do usuario no Gate R
  para marcar `review_completed`.
