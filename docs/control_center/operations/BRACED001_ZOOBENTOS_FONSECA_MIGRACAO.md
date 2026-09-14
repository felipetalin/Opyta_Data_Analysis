# BRACED001 - Zoobentos - migracao inicial Fonseca

## Controle

- projeto: BRACED001 / Fonseca-Biota Aquatica
- grupo: Zoobentos
- operacao: validacao, auditoria taxonomica, migracao, consolidacao e analises
- estado atual: `awaiting_revision_approval`
- aberta em: 2026-08-18
- atualizada em: 2026-08-18
- proxima acao: revisar e aprovar o pacote gerado no Gate R

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/Resultados_Migracao_Zoobentos.xlsx`
- cadastro de especies: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/Cadastro_especies_opyta_fonseca-bentos-260818.xlsx`
- referencia espacial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/geo/Geo_Fonseca/Anteriores/pontos_geo.kml`
- saida final: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Bentos`
- script de validacao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/validar_gate_a_bentos.py`
- validacao atual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/validation/20260818T163434_validacao_gate_a_zoobentos_braced001.xlsx`
- log de validacao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/validation/20260818T163434_validacao_gate_a_zoobentos_braced001.json`
- validacao inicial bloqueada: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/validation/20260818T162920_validacao_gate_a_zoobentos_braced001.xlsx`
- script de auditoria Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/auditar_gate_b_especies.py`
- auditoria Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/gate_b/gate_b_especies_zoobentos_braced001_20260818T165203.xlsx`
- log Gate B: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/gate_b/gate_b_especies_zoobentos_braced001_20260818T165203.json`
- dry-run migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/migration/20260818T170109_dry_run_migracao_biota_aquatica_braced001.xlsx`
- aplicacao migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/migration/20260818T170125_apply_migracao_biota_aquatica_braced001.xlsx`
- auditoria pos-migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/migration/20260818T170256_auditoria_pos_migracao_zoobentos_braced001.xlsx`
- configuracao Gate C: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/config_analises_zoobentos_braced001.json`
- auditoria de geracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/20260818T172514_geracao_resultados_zoobentos_a4_paisagem.xlsx`
- contato visual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos/20260818T172514_contact_sheet_figuras_zoobentos_a4_paisagem.png`
- recipe: perfil de referencia `BRAAEG001__a_g_mineracao_biota_aquatica`
- lastro: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/bentos`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Fontes indicadas pelo usuario e operacao isolada dos demais grupos. |
| Validacao | concluida | Revalidacao `PASS`: 0 bloqueios, 0 avisos e coordenadas reconciliadas. |
| Gate A - dados | aprovado | Usuario aprovou em 2026-08-18 apos revalidacao `PASS`. |
| Cadastro de especies | auditado | Os 31 taxons ja existem no banco; a duplicacao identica de `Oligochaeta` foi consolidada somente na leitura. |
| Auditoria de atributos | concluida para decisao | BMWP 31/31 identico; 120 diferencas da hierarquia deslocada na fonte serao preservadas no banco. |
| Gate B - especies | aprovado | Usuario aprovou em 2026-08-18; os 31 registros existentes serao reutilizados sem escrita em `public.especies`. |
| Migracao | concluida | Dry-run limpo e aplicacao controlada: 36 esforcos e 134 resultados de Zoobentos. |
| Consolidacao | concluida | 134 linhas consolidadas; auditoria fonte/base/consolidado com 0 divergencias. |
| Configuracao das analises | concluida para decisao | Perfil operacional R01 da pasta A&G replicado para BRACED001. |
| Gate C - analises | aprovado | Usuario aprovou a geracao em 2026-08-18. |
| Geracao dos produtos | concluida | 16 figuras, 21 planilhas, HTML, Darwin Core, manifesto e validacao. |
| Revisao | aguardando aprovacao | Validacao automatica `OK` e revisao visual concluida; aguarda Gate R. |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario aprovou em 2026-08-18. |
| B - especies | `approved` | Usuario aprovou em 2026-08-18; decisao sem escrita no cadastro mestre. |
| C - analises | `approved` | Usuario aprovou a geracao em 2026-08-18. |

## Fontes Preservadas

- resultados SHA256 atual: `7B2AFD211CB9F8AB0F556D415740DFC30C0A03D7518117C6B2BA9E5E38A28016`
- resultados SHA256 inicial: `A8E0A9296BD32708D06AEA48DD39A65F4788FC275CB75531D1F3CCBAFFB3FB40`
- cadastro SHA256: `DBFCCA6FA4BD71D834B3780D7867C250E235F597D702DB1036A94464E9B3C9C3`
- resultados: 2 campanhas, 18 pontos, 36 linhas ponto-campanha, 36 esforcos e 134 resultados
- cobertura taxonomica: 31 taxons nos resultados e 31 taxons distintos no cadastro, sem ausencias
- cadastro: 32 linhas; 1 duplicacao identica de `Oligochaeta` consolidada em 31 taxons na auditoria

## Pendencias

- executar dry-run e reconciliar fonte, banco e consolidado

## Auditoria Do Gate B

- modo: `audit_only`; registros aplicados no banco: 0
- cobertura: 31 taxons nos resultados e 31 no cadastro, sem ausencias ou excedentes
- cadastro mestre: 31/31 taxons ja existentes; taxons novos: 0
- BMWP: 31/31 valores identicos entre fonte e banco
- estrategia proposta: preservar integralmente os registros existentes; campos nulos a preencher: 0
- diferencas preservadas: 120, todas explicadas pelo deslocamento da hierarquia taxonomica na planilha de origem
- estrutura correta no banco: `Animalia > Arthropoda > Insecta > ordem > familia` para 29 familias; `Hirudinea` e `Oligochaeta` mantidos em seus niveis taxonomicos reais
- observacoes da fonte: aba `Notas_e_Fontes` foi copiada da ictiofauna e nao sera usada
- pendencias obrigatorias apos a decisao proposta: 0
- decisao solicitada: aprovar o Gate B sem escrita em `public.especies`

## Aprovacao Do Gate B

- aprovado pelo usuario em 2026-08-18
- aplicacao taxonomica: no-op; nenhuma escrita em `public.especies`
- estrategia confirmada: reutilizar os 31 registros existentes e preservar integralmente seus atributos

## Migracao E Consolidacao

- dry-run: 2 campanhas, 36 pontos-campanha, 36 esforcos, 134 resultados e 31 taxons
- aplicacao: 134 resultados em `public.resultados_zoobentos` e 134 linhas em `public.biota_analise_consolidada`
- totais por campanha: C001 com 54 linhas e abundancia 159; C002 com 80 linhas e abundancia 328
- backup: prefixo `public.backup_biota_braced001_20260818t170125`
- auditoria pos-migracao: `PASS`
- divergencias fonte/base: 0
- divergencias fonte/consolidado: 0
- divergencias de esforcos: 0
- divergencias de pontos, datas ou coordenadas: 0

## Configuracao Do Gate C

- referencia literal: pasta operacional R01 de Zoobentos da A&G Mineracao
- layout: A4 paisagem, 600 dpi e paineis separados por `C01-Chuva` e `C02-Seca`
- paleta: verde A&G para composicao e cores originais de classe para BMWP
- escopo: 16 figuras, 21 planilhas, relatorio HTML, Darwin Core, manifesto e validacao
- analises: riqueza, abundancia, ordens, taxons, diversidade alfa, Bray-Curtis, suficiencia Jackknife 1, BMWP, EPT, CHOL, sintese e minimapa
- regras R01 preservadas: top 20 apenas nas figuras 08/09, todos os taxons nas tabelas; `Oligochaeta (Classe)`; italico apenas para `Genero sp.`; EPT/CHOL em paineis separados
- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Bentos`
- decisao solicitada: aprovar o Gate C para gerar e validar o pacote completo

## Geracao E Revisao

- perfil: A&G R01 em A4 paisagem, com paineis independentes para `C01-Chuva` e `C02-Seca`
- regras preservadas: Top 20 apenas nas figuras 08/09, tabelas completas, `Oligochaeta (Classe)`, italico seletivo, 11B por ponto e EPT/CHOL separados
- minimapa: BMWP, EPT e CHOL por campanha; rotulos dos trios distribuidos em triangulo com linhas-guia
- entrega: 16 PNG, 21 XLSX, relatorio HTML, Darwin Core, manifesto e validacao
- validacao: `OK`, 16/16 figuras, 0 erros, sem imagens vazias ou dimensoes incorretas
- integridade: 21/21 XLSX validos, sem erros de formula e sem referencias residuais ao projeto A&G
- estado: aguardando aprovacao do Gate R

## Revalidacao Do Gate A

- resultado: `PASS`
- bloqueios: 0
- avisos: 0
- correcao confirmada: `MA-06-06` eliminado e tres resultados associados a `MA-06-16`
- cobertura: 2 campanhas, 18 pontos, 36 linhas ponto-campanha, 36 esforcos unicos, 134 resultados positivos e 31 taxons
- coordenadas: 36/36 linhas conferem com o KML, distancia maxima `0 m`, tolerancia `50 m`
- validacao do relatorio: 13 abas e 0 erros de formula

## Validacao Inicial Do Gate A

- resultado: `BLOCKED`
- bloqueios oficiais: `INVALID_POINT_REFERENCE` e `INVALID_EFFORT_REFERENCE`
- causa unica: 3 resultados da C002 usam `MA-06-06`; o ponto correto existente em pontos, esforcos e KML e `MA-06-16`
- linhas afetadas: 122, 125 e 133 da aba `Resultados_Zoobentos`
- taxons afetados: `Chironomidae`, `Ceratopogonidae` e `Elmidae`
- estrutura valida: 2 campanhas, 18 pontos, 36 linhas ponto-campanha, 36 esforcos unicos, 134 resultados positivos e 31 taxons
- coordenadas: 36/36 linhas ponto-campanha conferem com o KML, distancia maxima `0 m`, tolerancia `50 m`
- avisos: 0
- ajustes aplicados nas fontes: nenhum
