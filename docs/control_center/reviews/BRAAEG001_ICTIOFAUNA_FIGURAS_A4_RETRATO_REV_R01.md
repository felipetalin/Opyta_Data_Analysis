# BRAAEG001 - Ictiofauna - Figuras A4 Retrato - Revisao R01

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- operacao de origem: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- revisao: `R01`
- estado atual: `regenerated_pending_review`
- solicitada em: 2026-07-27
- atualizada em: 2026-07-28
- proxima acao: revisar as 16 figuras finais de ictiofauna regeneradas em A4 paisagem e aprovar o fechamento da R01.

## Escopo

- solicitacao do usuario: revisar as figuras de ictiofauna antes da geracao dos resultados, pois as letras parecem muito pequenas para A4 retrato.
- tipo principal: `layout`
- tipos secundarios: `package`
- impacto: `R1`
- produtos alvo: 16 figuras PNG de ictiofauna em `resultados/migracao_biota/ictiofauna` e produtos dependentes de apresentacao, como HTML/manifesto, se as figuras forem regeneradas.
- fora do escopo: dados, banco, migracao, consolidacao, taxonomia, coordenadas, formulas e metricas.

## Linha De Base

- pasta/arquivo: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna`
- versao/data: pacote de ictiofauna gerado em 2026-07-13.
- manifesto: `manifesto_entrega_ictiofauna_braaeg001.json`
- hashes: registrados no manifesto de entrega.
- snapshot/backup: criado antes da regeneracao final em `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260727T151940_backup_figuras_ictio_pre_R01`.

## Dependencias E Retorno

- Gate A reaberto: nao
- Gate B reaberto: nao
- Gate C reaberto: nao, salvo se o usuario decidir trocar template/paleta alem do ajuste de legibilidade.
- banco afetado: nao
- coordenadas afetadas: nao
- fonte espacial de referencia: nao aplicavel nesta revisao.
- produtos com latitude/longitude: nenhum produto de mapa de ictiofauna nesta entrega.
- produtos dependentes: figuras PNG, relatorio HTML, manifesto e validacao de entrega quando houver regeneracao.

## Progresso

| Etapa | Estado | Evidencia |
| --- | --- | --- |
| Identificacao da linha de base | concluida | Pasta final de ictiofauna e manifesto de 2026-07-13 localizados. |
| Triagem de tipo e impacto | concluida | Revisao `layout/R1`; sem impacto em dados, banco, taxonomia ou metodo. |
| Auditoria inicial de legibilidade | concluida | `20260727T142711_auditoria_figuras_ictio_a4_retrato_braaeg001.xlsx/json`; 16/16 figuras em risco alto para A4 retrato. |
| Aprovacao de escopo, se necessaria | parcial | Usuario autorizou gerar somente 1 figura para teste. |
| Correcao | teste gerado | `02_grafico_riqueza_por_ponto_ictiofauna_A4_retrato_teste_R01.png`, sem sobrescrever o PNG original. |
| Regeneracao de dependencias | concluida | 16 PNGs finais de ictiofauna regenerados em A4 paisagem; manifesto e validacao atualizados. |
| Validacao da revisao | concluida para teste | Figura teste aberta e conferida visualmente; rótulos legiveis e sem sobreposicao. |
| Teste A4 paisagem | concluido | `02_grafico_riqueza_por_ponto_ictiofauna_A4_paisagem_final_R01.png`, mantendo barras verticais e proporcao original em prancha A4 paisagem. |
| Teste A4 paisagem original/refinado | concluido | `02_grafico_riqueza_por_ponto_ictiofauna_A4_paisagem_original_refinado_R01.png`, mantendo layout-base original, legenda sazonal curta, grid horizontal por unidade, riqueza sem casas decimais e margem superior ampliada. |
| Gate R - aprovacao do padrao visual | aprovado | Usuario aprovou a figura teste A4 paisagem original/refinada em 2026-07-27 e autorizou regenerar as figuras de ictiofauna. |
| Regeneracao das figuras finais | concluida | 16 PNGs finais de ictiofauna sobrescritos em A4 paisagem; backup dos 16 PNGs originais criado antes da regeneracao. |
| Ajuste dos graficos 08 e 09 | concluido | Margem esquerda ampliada em `08_grafico_cpuen_por_especie_ictiofauna.png` e `09_grafico_cpueb_por_especie_ictiofauna.png` para exibir nomes cientificos completos. |
| Ajuste de acentuação `Espécie` | concluído | `08`, `09`, `08B` e `09B` regenerados com eixo `Espécie` no lugar de `Especie`. |
| Ajuste geral de acentuação pt-BR | concluído | 16 PNGs finais regenerados; rótulos visíveis revisados: `Riqueza taxonômica`, `Abundância total (nº de indivíduos)`, `Número de espécies`, `Família`, `Número de unidades amostrais`, `Síntese ecológica` e `Comportamento migratório`. |
| Ajuste de acentuação no relatório HTML | concluído | `relatorio_tecnico_ictiofauna_braaeg001.html` atualizado com termos visíveis em pt-BR; manifesto e validação regravados com novos hashes. |
| Promocao e fechamento | aguardando revisao final | Aguardando conferencia/aprovacao do usuario sobre o pacote completo regenerado. |

## Diagnostico

- A auditoria simulou encaixe em A4 retrato com largura util de 16,5 cm.
- As figuras atuais foram produzidas em formato largo/horizontal, com largura nativa aproximada entre 32,75 cm e 37,85 cm.
- Ao encaixar em A4 retrato, a escala cai para 0,436 a 0,504.
- Com essa escala, texto original de 10 pt vira aproximadamente 4,4 a 5,0 pt; por isso a legibilidade fica inadequada para relatorio em A4 retrato.
- Status da auditoria: `FAIL_A4_PORTRAIT_LEGIBILITY`.

## Alteracoes

| Item | Antes | Depois | Motivo |
| --- | --- | --- | --- |
| Figuras ictiofauna | Formato horizontal, largura nativa ~33-38 cm | Figuras finais regeneradas em A4 paisagem, 29,69 x 21,01 cm, 600 dpi | Texto efetivo em A4 retrato ficava ~4,4-5,0 pt. |
| `02_grafico_riqueza_por_ponto_ictiofauna.png` | Barras verticais em formato horizontal | Figura teste A4 retrato com barras horizontais agrupadas, fonte efetiva preservada e eixo de pontos legivel | Testar alternativa adequada para A4 retrato sem alterar o original. |
| `02_grafico_riqueza_por_ponto_ictiofauna.png` | Barras verticais em formato horizontal largo | Figura teste A4 paisagem em tamanho real de pagina, 29,7 x 21,0 cm, 600 dpi, mantendo barras verticais | Preservar a logica visual original e evitar conflitos causados pela inversao das barras. |
| `02_grafico_riqueza_por_ponto_ictiofauna.png` | Legenda `C01`/`C02`, eixo de riqueza decimal e grid original | Figura teste A4 paisagem original/refinada com legenda `C01-Chuva`/`C02-Seca`, eixo inteiro e grid horizontal tracejado nas unidades | Manter o layout original e melhorar leitura de sazonalidade e de riqueza absoluta. |
| 16 figuras finais de ictiofauna | PNGs horizontais largos, nativos ~33-38 cm | PNGs finais regenerados em A4 paisagem, 29,69 x 21,01 cm, 600 dpi | Aplicar o padrao aprovado pelo usuario ao pacote final. |
| Graficos 08 e 09 | Nomes cientificos cortados no lado esquerdo | Margem esquerda ampliada nos graficos horizontais por especie | Garantir exibicao completa dos nomes das especies. |
| Graficos 08, 09, 08B e 09B | Eixo `Especie` sem acento | Eixo corrigido para `Espécie` | Corrigir acentuação do rótulo em português. |
| Rótulos em português brasileiro | Termos visíveis sem acento, como `Abundancia`, `Numero`, `Sintese`, `ecologica`, `migratorio`, `Riqueza taxonomica` e `Familia` | Termos corrigidos para pt-BR com acentuação e unidades revisadas para `m²` | Evitar perda de qualidade linguística nas figuras finais. |
| Script reprodutor | Sem trava para rótulos pt-BR | `validate_ptbr_labels()` bloqueia rótulos visíveis sem acentuação pt-BR antes da regeneração | Prevenir regressão em futuras execuções. |
| Relatório HTML | Textos visíveis sem acento, como `diagnostico`, `individuos`, `familias`, `Sintese`, `abundancia`, `suficiencia` e unidades `m2` | Textos corrigidos para `diagnóstico`, `indivíduos`, `famílias`, `Síntese`, `abundância`, `suficiência` e `m²`; gerador com `validate_report_ptbr()` | Corrigir o produto visível dependente das figuras. |

## Arquivos Regenerados

- Figura teste gerada:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna/02_grafico_riqueza_por_ponto_ictiofauna_A4_retrato_teste_R01.png`
- Figura teste A4 paisagem gerada:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna/02_grafico_riqueza_por_ponto_ictiofauna_A4_paisagem_final_R01.png`
- Figura teste A4 paisagem original/refinada gerada:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna/02_grafico_riqueza_por_ponto_ictiofauna_A4_paisagem_original_refinado_R01.png`
- Figuras finais regeneradas:
  - 16 PNGs finais em `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna`
- Backup dos PNGs originais:
  - `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260727T151940_backup_figuras_ictio_pre_R01`
- Script reprodutor:
  - `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/regenerate_figures_a4_landscape_r01.py`
- Lastros de auditoria criados:
  - `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260727T142711_auditoria_figuras_ictio_a4_retrato_braaeg001.json`
  - `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260727T142711_auditoria_figuras_ictio_a4_retrato_braaeg001.xlsx`
  - `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260727T142711_preview_figuras_ictio_a4_retrato_braaeg001.pdf`

## Validadores

- auditoria de legibilidade A4 retrato:
  - status: `FAIL_A4_PORTRAIT_LEGIBILITY`
  - figuras avaliadas: 16
  - alto risco: 16
  - menor fonte efetiva estimada para texto 10 pt: 4,4 pt
- teste A4 paisagem original/refinado:
  - arquivo: `02_grafico_riqueza_por_ponto_ictiofauna_A4_paisagem_original_refinado_R01.png`
  - dimensao: 7014 x 4962 px
  - tamanho nativo: 29,69 x 21,01 cm
  - resolucao: 600 dpi
  - validacao visual: barras verticais, quadro completo, legenda sazonal acima do eixo com margem superior ampliada, rotulos inteiros e eixos legiveis em A4 paisagem.
- pacote final A4 paisagem:
  - auditoria final: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260728T090955_validacao_figuras_ictio_a4_paisagem_R01_pos_acentos_ptbr.json`
  - planilha de auditoria: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260728T090955_validacao_figuras_ictio_a4_paisagem_R01_pos_acentos_ptbr.xlsx`
  - prancha visual: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260728T090955_contact_sheet_figuras_ictio_a4_paisagem_R01.png`
  - figuras avaliadas: 16
  - status dimensional: 16/16 em 7014 x 4962 px, 29,69 x 21,01 cm, 600 dpi
  - status de imagem: 16/16 nao vazias
  - ajuste visual final: graficos 08 e 09 conferidos com nomes cientificos completos; graficos 08, 09, 08B e 09B corrigidos para o eixo `Espécie`; rótulos pt-BR conferidos em 02, 03, 04, 08, 09, 08B, 12 e 14.
  - validacao de entrega: `validacao_entrega_ictiofauna_braaeg001.json` com status `OK`, 36 arquivos checados, 0 erros
  - manifesto: `manifesto_entrega_ictiofauna_braaeg001.json/.xlsx/.md` atualizado com hashes pos-R01
- relatório HTML:
  - auditoria: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260728T091728_validacao_relatorio_html_ictio_R01_pos_acentos_ptbr.json`
  - planilha de auditoria: `outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/ictiofauna/20260728T091728_validacao_relatorio_html_ictio_R01_pos_acentos_ptbr.xlsx`
  - status: `OK`; termos visíveis sem acentuação pt-BR: 0
- auditoria de coordenadas:
  - antes: nao aplicavel
  - depois: nao aplicavel
  - divergencias remanescentes: nao aplicavel

## Gate R

- status: `applied_pending_final_package_approval`
- apresentado em: 2026-07-27
- aprovado em: 2026-07-27 para o padrao visual A4 paisagem da figura teste
- registro da aprovacao: usuario aprovou a figura teste e autorizou regenerar as figuras finais de ictiofauna.

## Aprendizados E Pendencias

- Para A4 retrato, a aprovacao visual anterior em layout horizontal nao deve ser reaproveitada sem nova simulacao de escala.
- Recomendacao tecnica atual: usar A4 paisagem para as figuras largas de ictiofauna, preservando o layout-base original e aplicando apenas ajustes pontuais de legibilidade aprovados.
- Legenda sazonal recomendada para campanhas curtas: `C01-Chuva` e `C02-Seca`, mantendo o codigo da campanha e explicitando `CH`/`SC` para o leitor.
