# BRACED001 - Zooplancton - migracao inicial Fonseca

## Controle

- projeto: BRACED001 / Fonseca-Biota Aquatica
- grupo: Zooplancton
- operacao: validacao, auditoria taxonomica, migracao, consolidacao e analises
- estado atual: `completed`
- aberta em: 2026-08-18
- atualizada em: 2026-08-18
- proxima acao: nenhuma; operacao concluida

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/Resultados_Migracao_zoo.xlsx`
- cadastro de especies: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Migracao/Fonseca/Cadastro_especies_fonseca_zoo_FINAL_CONFERENCIA.xlsx`
- referencia espacial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/geo/Geo_Fonseca/Anteriores/pontos_geo.kml`
- saida final: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Zooplancton`
- script de validacao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/validar_gate_a_zooplancton.py`
- validacao atual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/validation/20260818T180817_validacao_gate_a_zooplancton_braced001.xlsx`
- log de validacao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/validation/20260818T180817_validacao_gate_a_zooplancton_braced001.json`
- validacao inicial bloqueada: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/validation/20260818T114112_validacao_gate_a_zooplancton_braced001.xlsx`
- auditoria Gate B aplicada: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/gate_b/gate_b_especies_zooplancton_braced001_20260818T181529.xlsx`
- decisoes taxonomicas: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/gate_b/taxon_overrides_approved_20260818.json`
- migracao aplicada: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/migration/20260818T181243_apply_migracao_biota_aquatica_braced001.xlsx`
- auditoria pos-migracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/migration/20260818T181537_auditoria_pos_migracao_zooplancton_braced001.xlsx`
- auditoria de geracao: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/20260818T181722_geracao_resultados_zooplancton_a4_paisagem.xlsx`
- contato visual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/20260818T181722_contact_sheet_figuras_zooplancton_a4_paisagem.png`
- dossie: pendente
- recipe: perfil de referencia `BRAAEG001__a_g_mineracao_biota_aquatica`
- lastro: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Fontes informadas pelo usuario e operacao isolada da migracao de Ictiofauna. |
| Validacao | concluida com aviso | Revalidacao: 0 bloqueios, 1 aviso; 72/72 esforcos unicos, 624 resultados validos e 36/36 coordenadas conferidas. |
| Gate A - dados | aprovado | Usuario aprovou em 2026-08-18, incluindo o aviso nao bloqueante sobre `Esforco = 100 litros`. |
| Cadastro de especies | auditado com pendencias | 58 taxons na fonte; 1 divergencia resultados/cadastro e 1 duplicata potencial por capitalizacao. |
| Auditoria de atributos | bloqueada | Corrigir hierarquia deslocada de `Filinia terminalis`; 209 diferencas dos taxons existentes serao preservadas. |
| Gate B - especies | aprovado e aplicado | 58/58 taxons, 3 novos, normalizacoes aprovadas e 0 pendencias obrigatorias. |
| Migracao | concluida | 36 esforcos mistos e 624 resultados migrados com backup. |
| Consolidacao | concluida | 624 linhas; auditoria pos-migracao `PASS` sem divergencias. |
| Configuracao das analises | concluida | Perfil final da A&G com paineis por campanha e Top 20 nas figuras densas. |
| Gate C - analises | aprovado | Autorizacao de geracao registrada pelo usuario em 2026-08-18. |
| Geracao dos produtos | concluida | 14 figuras, 20 planilhas, HTML, Darwin Core, manifesto e validacao. |
| Revisao | aprovada | Gate R da revisao taxonomica R01 aprovado em 2026-08-19. |
| Fechamento | concluido | Pacote R01 promovido para a pasta oficial, com hashes 38/38 conferidos. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario aprovou em 2026-08-18 a revalidacao e o aviso sobre `100 litros`. |
| B - especies | `approved_applied` | Decisoes aprovadas pelo usuario e aplicadas em 2026-08-18; 0 pendencias. |
| C - analises | `approved` | Geracao aprovada pelo usuario em 2026-08-18. |

Autorizacao de geracao recebida do usuario em 2026-08-18 e executada apos a aprovacao e aplicacao do Gate B.

## Fontes Preservadas

- resultados SHA256 atual: `A6C525D6D491D90ED85892B669D58C065CBF826D7C0711CB53863D9E2731E9B7`
- resultados SHA256 inicial: `C111DD7A28A3F7EF8A197236C68E70E4FC8E9F8F97752A954339ABC533AE1C57`
- cadastro SHA256: `6CF07D496F03D7CB834B491D0638B756265297E7DA4AD8A80A0775A1F103DC8A`
- resultados: 2 campanhas, 18 pontos, 36 linhas ponto-campanha, 72 linhas de esforco e 624 linhas de resultados
- cadastro: 58 linhas de taxons na aba `Cadastro_Especies`; auditoria taxonomica ainda nao iniciada

## Revalidacao Do Gate A

- resultado: `PASS_WITH_WARNINGS`
- bloqueios: 0
- correcoes confirmadas: `MA-04-012` eliminado e esforcos de `MA-01-01` corretamente distribuidos entre C001 e C002
- reconciliacao: 72 linhas de esforco, 72 chaves unicas e 624/624 resultados com referencia valida de ponto e esforco
- aviso para aceite: as 72 linhas de esforco usam o texto `100 litros`; o validador oficial espera valor numerico, mas o mesmo formato foi aceito operacionalmente no perfil A&G
- coordenadas: 36/36 linhas ponto-campanha conferem com os 18 pontos do KML, distancia maxima `0 m`, tolerancia `50 m`
- estrutura valida: codigo `BRACED001`, 4 abas obrigatorias, 2 campanhas, 18 pontos, 624 resultados positivos e 58 taxons distintos
- ajustes aplicados nas fontes: realizados pelo usuario antes da revalidacao
- validacao do relatorio: 13 abas e 0 erros de formula

## Pendencias Resolvidas

Todas as pendencias abaixo foram resolvidas por ajustes do usuario ou normalizacoes aprovadas e registradas no Gate B.

- em `Resultados_Zooplancton`, substituir `Difflugia lithophila` por `Difflugia litophila` nas 6 ocorrencias; o segundo nome existe no cadastro, no banco e no perfil A&G
- em resultados e cadastro, substituir `Ciliado NI` por `Ciliado ni`; reutilizar `public.especies.id_especie = 4008` em vez de criar duplicata por capitalizacao
- corrigir `Filinia terminalis` no cadastro para `Animalia > Rotifera > Eurotatoria > Flosculariaceae > Trochosphaeridae > Filinia`, autor `(Plate, 1886)`
- repetir a auditoria; a expectativa apos os ajustes e de 3 taxons novos: `Filinia terminalis`, `Platyias quadricornis` e `Colurella uncinata`
- manter a estrategia incremental: preencher apenas campos nulos nos existentes e preservar valores nao nulos do banco
- aguardar aprovacao explicita do Gate B antes de qualquer escrita em `public.especies`

## Auditoria Inicial Do Gate B

- modo: `audit_only`; registros aplicados no banco: 0
- cobertura: 58 taxons nos resultados e 58 no cadastro; 1 ausente e 1 excedente por divergencia ortografica
- comparacao inicial: 4 taxons classificados como novos, 54 existentes, 571 campos potencialmente preenchiveis e 209 diferencas preservadas
- apos normalizar `Ciliado NI`, a expectativa e de 3 taxons novos e 55 existentes
- conflitos de grupo biologico entre fonte e banco: 0
- pendencias obrigatorias simuladas apos as acoes: 0, condicionadas as correcoes acima
- planilha de auditoria: 6 abas e 0 erros de formula

## Reabertura Em 2026-08-18

- motivo: a planilha de resultados apresentou novo SHA256 durante a checagem previa a geracao
- Gate A repetido: `PASS_WITH_WARNINGS`, 0 bloqueios e o mesmo aviso ja aceito sobre `100 litros`
- Gate B repetido em modo somente leitura: ainda ha 1 taxon dos resultados sem cadastro e 1 taxon do cadastro sem resultados
- pendencias confirmadas: `Difflugia lithophila`, `Ciliado NI` e hierarquia de `Filinia terminalis`
- escritas no cadastro mestre: 0
- migracao e geracao: nao executadas

## Fechamento Tecnico Da Rodada

- decisoes: `Difflugia litophila` confirmada; `Ciliado NI` normalizado para `Ciliado ni`; `Filinia terminalis` aplicada como `Animalia > Rotifera > Eurotatoria > Flosculariaceae > Trochosphaeridae > Filinia`, autor `(Plate, 1886)`
- Gate B: 58 taxons reconciliados, 3 novos inseridos, preenchimento apenas de nulos e 200 diferencas nao nulas preservadas
- migracao: 624 resultados e 36 esforcos mistos; backup `public.backup_biota_braced001_20260818t181243_*`
- auditoria: 0 divergencias entre fonte, base e consolidado; pontos, datas e coordenadas sem divergencias
- entrega: 14 PNG, 20 XLSX, relatorio HTML, Darwin Core, manifesto e validacao `OK`
- layout: paineis separados por `C01-Chuva` e `C02-Seca`, Top 20 nas figuras 08/09 e minimapa com rotulos triangulares
- estado: aguardando aprovacao do Gate R

## Revisao Taxonomica R01 - 2026-08-19

- Gate B reaberto e aprovado pela solicitacao direta do usuario.
- correcoes: `Cyclopidae`, `Difflugiidae`, `Cyphoderiidae`, `Colurella minima` e campos `N.A.` de `Ciliado ni`.
- backups: `public.bk_esp_braced001_zoo_r01_20260819t205722` e `public.bk_cons_braced001_zoo_r01_20260819t205722`.
- integridade: 58 taxons e 624 resultados preservados; 0 pendencias no cadastro e consolidado.
- pacote R01: 38 arquivos, 14/14 figuras validas, zero erros e zero ocorrencias dos valores antigos nas planilhas.
- promocao: 38 arquivos substituidos na pasta oficial, hashes 38/38, 14/14 figuras e validador `OK`.
- estado: Gate R aprovado e operacao concluida em 2026-08-19.
