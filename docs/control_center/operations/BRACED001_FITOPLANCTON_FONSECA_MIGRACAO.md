# BRACED001 - Fitoplancton - migracao inicial Fonseca

## Controle

- projeto: BRACED001 / Fonseca-Biota Aquatica
- grupo: Fitoplancton
- operacao: validacao, auditoria taxonomica, migracao, consolidacao e analises
- estado atual: `completed`
- aberta em: 2026-08-18
- atualizada em: 2026-08-19
- proxima acao: nenhuma; operacao encerrada apos revisao taxonomica R01

## Caminhos

- pasta de entrada: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/VALIDACAO_FINAL/fitoplancton`
- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/VALIDACAO_FINAL/fitoplancton/Resultados_FINAL.xlsx`
- cadastro de especies: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/VALIDACAO_FINAL/fitoplancton/Cadastro_Especies_FINAL.xlsx`
- referencia espacial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/geo/Geo_Fonseca/Anteriores/pontos_geo.kml`
- validacao previa dos resultados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/VALIDACAO_FINAL/fitoplancton/VALIDACAO_RESULTADOS.xlsx`
- resumo taxonomico previo: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/VALIDACAO_FINAL/fitoplancton/RESUMO_VALIDACAO.xlsx`
- saida final: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Fitoplancton`
- script de validacao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/validar_gate_a_fitoplancton.py`
- validacao atual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/validation/20260818T154122_validacao_gate_a_fitoplancton_braced001.xlsx`
- log de validacao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/validation/20260818T154122_validacao_gate_a_fitoplancton_braced001.json`
- auditoria inicial Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/gate_b/gate_b_especies_fitoplancton_braced001_20260818T160244.xlsx`
- pacote de decisao Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/gate_b/20260818T160626_gate_b_decisao_fitoplancton_braced001.xlsx`
- log Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/gate_b/20260818T160626_gate_b_decisao_fitoplancton_braced001.json`
- aplicacao Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/gate_b/20260818T161632_apply_gate_b_fitoplancton_braced001.xlsx`
- dry-run migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/migration/20260818T161728_dry_run_migracao_biota_aquatica_braced001.xlsx`
- aplicacao migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/migration/20260818T161743_apply_migracao_biota_aquatica_braced001.xlsx`
- auditoria pos-migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/migration/20260818T162000_auditoria_pos_migracao_fitoplancton_braced001.xlsx`
- auditoria de geracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/20260818T172022_geracao_resultados_fitoplancton_a4_paisagem.xlsx`
- contato visual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton/20260818T172022_contact_sheet_figuras_fitoplancton_a4_paisagem.png`
- recipe: perfil de referencia `BRAAEG001__a_g_mineracao_biota_aquatica`
- lastro: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/fitoplancton`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Operacao independente criada para os arquivos de `VALIDACAO_FINAL/fitoplancton`. |
| Validacao | concluida | Gate A `PASS`: 0 bloqueios, 0 avisos, esforcos e coordenadas reconciliados. |
| Gate A - dados | aprovado | Usuario aprovou em 2026-08-18 apos validacao `PASS` sem avisos. |
| Cadastro de especies | auditado | 198 taxons canonicos: 92 novos e 106 registros existentes reutilizados. |
| Auditoria de atributos | concluida para decisao | 1.076 nulos a preencher, 2 grupos com codificacao a corrigir e 194 diferencas nao nulas preservadas. |
| Gate B - especies | aprovado e aplicado | Usuario aprovou em 2026-08-18; 92 novos inseridos, 106 existentes processados e 198/198 verificados. |
| Migracao | concluida | Dry-run limpo e aplicacao controlada: 72 esforcos e 511 resultados de Fitoplancton. |
| Consolidacao | concluida | 511 linhas consolidadas; auditoria fonte/base/consolidado com 0 divergencias. |
| Configuracao das analises | concluida | Perfil final da A&G aplicado, com paineis separados por campanha e Top 20 apenas nas figuras densas. |
| Gate C - analises | aprovado | Usuario aprovou a geracao em 2026-08-18. |
| Geracao dos produtos | concluida | 13 figuras, 18 planilhas, HTML, Darwin Core, manifesto e validacao. |
| Revisao | concluida | Revisao taxonomica R01 validada e aprovada para substituicao em 2026-08-19. |
| Fechamento | concluido | Pacote R01 promovido com 35/35 hashes conferidos e backup preservado. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario aprovou em 2026-08-18. |
| B - especies | `approved_applied` | Aprovado pelo usuario e aplicado em 2026-08-18; pos-validacao `PASS`. |
| C - analises | `approved` | Usuario aprovou a geracao em 2026-08-18. |

## Fontes Preservadas

- resultados SHA256: `D4687C500BDC7CFCC560EC6546C98896358CDD4712E8922A7354323F64730C34`
- cadastro SHA256: `531D2CC23DCC4DEA2E635B37282AC68017B4C976D9FE2C9BE1D85C8D21D0253B`
- resultados: 2 campanhas, 18 pontos, 36 linhas ponto-campanha, 72 esforcos e 511 resultados
- cobertura taxonomica: 198 taxons nos resultados e 198 taxons distintos no cadastro, sem ausencias
- relatorio previo: 0 bloqueios nos resultados e 1 aviso de preenchimento complementar do cadastro mestre

## Validacao Do Gate A

- resultado: `PASS`
- validadores oficiais: 0 bloqueios, 0 avisos e 0 informativos
- estrutura: codigo `BRACED001` e 4 abas obrigatorias presentes
- cobertura: 2 campanhas, 18 pontos, 36 linhas ponto-campanha e 511 resultados positivos
- esforco: 72 linhas e 72 chaves unicas; valores numericos separados nas unidades `litro` e `litros`
- taxons nos resultados: 198; todos encontrados no cadastro fornecido
- coordenadas: 36/36 linhas conferem com os 18 pontos do KML, distancia maxima `0 m`, tolerancia `50 m`
- ajustes aplicados nas fontes: nenhum
- validacao do relatorio: 13 abas e 0 erros de formula

## Auditoria Do Gate B

- modo: `audit_only`; registros aplicados no banco: 0
- cobertura: 198 taxons nos resultados e 198 no cadastro canonico, sem ausencias
- cadastro de origem: 285 linhas; 87 duplicacoes consolidadas por `keep_last`, conforme `O_QUE_MUDOU` e `FONTES_CONSULTADAS`
- taxons novos: 92
- registros existentes reutilizados: 106
- estrategia incremental nos existentes: preencher somente 1.076 campos nulos e preservar 194 diferencas nao nulas
- correcao controlada: `Frustulia sp.` id 5466 e `Iconella delicatissima` id 5467, apenas `Fitopl?ncton` para `Fitoplâncton` no grupo biologico
- alias de migracao: `Scytonemataceae n.i.` para `Scytonemataceae`, id 5461, conforme padrao de BRAAEG001
- correspondencia exata: `Gomphonema lagenula`, id 225; reutilizar sem sobrescrever taxonomia nao nula
- pendencias obrigatorias simuladas apos as acoes: 0
- validacao do pacote: 8 abas, 0 erros de formula e 0 IDs ausentes entre os registros existentes

## Pendencias Do Gate B

- nenhuma; Gate B aprovado, aplicado e revalidado

## Aplicacao Do Gate B

- backup: `public.backup_especies_braced001_fitoplancton_gate_b_20260818t161632`
- taxons novos inseridos: 92
- registros existentes processados: 106
- registros verificados apos aplicacao: 198/198
- taxons ausentes apos aplicacao: 0
- grupos biologicos invalidos apos aplicacao: 0
- tentativa anterior: abortada e revertida integralmente antes de qualquer escrita persistente por incompatibilidade de `bmwp_score = N.A.`; campo excluido da carga aprovada
- status final: `PASS`

## Migracao E Consolidacao

- projeto confirmado no banco: `BRACED001`, `id_projeto = 133`
- campanhas: `C001-2026-03-CH` e `C002-2026-06-SC`
- dry-run: 36 pontos, 72 esforcos, 511 resultados migraveis e 198 taxons
- banco antes: 36 pontos existentes e 0 esforcos/resultados/consolidado de Fitoplancton
- backups: prefixo `public.backup_biota_braced001_20260818t161743_*`
- banco depois: 36 pontos, 72 esforcos, 511 resultados base e 511 consolidados
- por campanha: C001 = 214 linhas, 17 pontos e 123 taxons; C002 = 297 linhas, 18 pontos e 162 taxons
- de/para aplicado somente em memoria: `Scytonemataceae n.i.` para `Scytonemataceae`; fonte preservada
- auditoria pos-migracao: 0 divergencias de resultados base, consolidado, esforcos, datas ou coordenadas
- status: `PASS`

## Geracao E Revisao

- perfil: A4 paisagem e paleta da A&G, com `C01-Chuva` e `C02-Seca` em paineis independentes
- legibilidade: figuras 08 e 09 limitadas aos 20 taxons mais densos; planilhas preservam todos os taxons
- minimapa: rotulos distribuidos em triangulo para os trios de pontos
- entrega: 13 PNG, 18 XLSX, relatorio HTML, manifesto e validacao
- validacao: `OK`, 13/13 figuras, 0 erros, sem imagens vazias ou dimensoes incorretas
- integridade: 18/18 XLSX validos, sem erros de formula e sem referencias residuais ao projeto A&G
- revisao taxonomica R01: 198 taxons em nove filos; 13/13 figuras e validador `OK`
- promocao: 35 arquivos substituidos, hashes 35/35 conferidos
- revisao de produtos R02: 38 arquivos promovidos, 14/14 figuras, hashes 38/38 e validador `OK`
- revisao de layout R03: nomenclaturas do minimapa reposicionadas junto aos trios de pontos, sem sobreposicao; pacote regenerado e validador `OK`
- politica de entrega: substituir sempre `Produtos/Resultados/Fitoplancton`; nao manter pastas paralelas de versoes ou backups em `Produtos/Resultados`.
- estado: Gate R aprovado e operacao concluida em 2026-08-19
