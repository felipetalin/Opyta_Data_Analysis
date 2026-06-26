# VIRITA001 - Ictiofauna - Campanha 1 - Revisao R02

## Controle

- projeto: `VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`
- operacao de origem: `docs/control_center/operations/VIRITA001_ICTIOFAUNA_CAMPANHA_1.md`
- revisao: `R02`
- estado atual: `awaiting_revision_approval`
- solicitada em: 2026-06-26
- atualizada em: 2026-06-26
- proxima acao: aprovar a inclusao da tabela biometrica no Gate R

## Escopo

- solicitacao do usuario: gerar um resultado de exemplo no formato de tabela
  com especie, N, comprimento padrao, peso corporal e biomassa.
- tipo principal: `analysis`
- tipos secundarios: `package`, `text`
- impacto: `R2`
- produtos alvo: tabela biometrica XLSX, HTML tecnico, evidencias,
  validacao textual, manifesto e lastro.
- fora do escopo: alterar banco, remigrar dados, alterar cadastro taxonomico ou
  substituir valores oficiais por valores digitados como exemplo.

## Linha De Base

- pasta/arquivo:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1`
- versao/data: pacote revisado R01 gerado tecnicamente em 2026-06-25.
- manifesto:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1/manifesto_entrega_ictiofauna_campanha_1.json`
- hashes: lastro R01 em
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita/ictiofauna/20260625T181107Z_execution_metadata.json`
- snapshot/backup: nao houve alteracao de banco; snapshot R01 permanece em
  `outputs/_snapshots/VIRITA001_R01_before_20260625/Campanha_1`.

## Dependencias E Retorno

- Gate A reaberto: nao
- Gate B reaberto: nao
- Gate C reaberto: nao, pois nao houve troca de template, paleta ou metodo
  aprovado; apenas inclusao de produto derivado da fonte validada.
- banco afetado: nao
- produtos dependentes: tabela biometrica, HTML, evidencias, manifesto, lastro
  e auditoria de pacote.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Pacote R01 em Gate R identificado como base. |
| Triagem de tipo e impacto | concluida | Inclusao de tabela/metrica derivada classificada como `analysis/package`, impacto `R2`. |
| Aprovacao de escopo | concluida | Pedido do usuario foi especifico e executavel em 2026-06-26. |
| Correcao | concluida | Novo bloco `biometria` adicionado ao pipeline de ictiofauna. |
| Regeneracao de dependencias | concluida | Tabela 13, HTML, evidencias, validacao textual, manifesto e lastro atualizados. |
| Validacao da revisao | concluida | Validacao textual `OK`; auditoria oficial de fauna `OK`. |
| Gate R - aprovacao final | aguardando usuario | Pacote revisado apresentado para aprovacao. |
| Promocao e fechamento | pendente | |

## Alteracoes

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Tabela biometrica | Ausente no pacote VIRITA001 | `13_tabela_biometria_biomassa_ictiofauna.xlsx` criada | Incluir resultado de exemplo/apoio com N, CP, PC e biomassa. |
| Valores de exemplo | Linha informada para `Astyanax lacustris`: N=7, CP 2,5/3,66/6, PC 0,71/8, biomassa 14,4 | Produto oficial usa a planilha corrigida: N=9, CP 10,0/10,22/10,5, PC 45/47, biomassa 413,0 | Manter rastreabilidade com a fonte validada. |
| HTML tecnico | Sem secao de biometria | Secao "Biometria e biomassa" adicionada | Tornar o produto visivel no relatorio. |
| Manifesto | 34 itens declarados | 35 itens declarados, excluindo o proprio manifesto | Incluir a nova planilha de entrega. |

## Arquivos Regenerados

- `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1/13_tabela_biometria_biomassa_ictiofauna.xlsx`
- `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1/relatorio_tecnico_ictiofauna_campanha_1.html`
- `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1/evidencias_relatorio_ictiofauna_campanha_1.json`
- `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1/validacao_textual_ictiofauna_campanha_1.json`
- `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/Sao Goncalo/Resultados/Ictiofauna/Campanha_1/manifesto_entrega_ictiofauna_campanha_1.json`
- `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita/ictiofauna/20260626T122432Z_execution_metadata.json`

## Validadores

- `python -B -c ... ast.parse(...)`: `syntax_ok`.
- `python scripts/run_pipeline.py ... --block biometria ...`: `OK`.
- `python scripts/projects/virita001/generate_ictio_html_report.py`: validacao textual `OK`, 0 erros, 0 avisos.
- `python scripts/validation/validar_fauna_outputs.py --project VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`: `OK`, 0 erros, 0 avisos.

## Gate R

- status: `awaiting_revision_approval`
- apresentado em: 2026-06-26
- aprovado em:
- registro da aprovacao:

## Aprendizados E Pendencias

- A tabela biometrica deve usar a planilha validada linha a linha, pois o banco
  consolidado pode conter biometria agregada.
- Arquivos abertos no Excel podem bloquear a regeneracao completa do pacote; a
  revisao foi executada pelo bloco dirigido `biometria`.
- Falta aprovacao do usuario no Gate R para marcar `review_completed`.
