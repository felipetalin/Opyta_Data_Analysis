# WSPKIN001 — Zoobentos — Migração inicial

## Controle

- projeto: WSPKIN001 / Kinross
- grupo: Zoobentos
- operacao: validação, cadastro taxonômico, migração, consolidação e análises
- estado atual: `awaiting_revision_approval`
- aberta em: 2026-09-09
- atualizada em: 2026-09-09
- proxima acao: aprovar o pacote corrigido no Gate R

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração_Zoobentos-WSP.xlsx`
- cadastro de especies: pendente após Gate A
- saida: pendente de Gate C
- dossie: não localizado
- recipe: não localizado
- lastro: `outputs/validacoes/wspkin001_zoobentos_20260909`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto confirmado no Supabase: `id_projeto=211`, `WSPKIN001`, Kinross. |
| Validacao | concluida com bloqueios | 152 resultados, 41 táxons, 20 pontos-campanha e 40 esforços; divergência de campanha e coordenadas. |
| Gate A — dados | aprovado | Usuário confirmou campanha corrigida, coordenadas oficiais e três ausências em 2026-09-09. |
| Cadastro de especies | concluido | 41/41 táxons cadastrados; `Pleidae` inserida como família, BMWP 3, conforme usuário. |
| Auditoria de atributos | concluida com ressalva | `Dryopidae` está repetida indevidamente no campo gênero; classificações históricas ainda serão confirmadas. |
| Gate B — especies | aprovado | Pleidae cadastrada; Dryopidae somente até família; ordens históricas preservadas conforme usuário. |
| Migracao | concluida | 152 resultados inseridos com backups, sem divergências. |
| Consolidacao | concluida | 152 linhas, 41 táxons e contagem total 349; coordenadas oficiais sem divergências. |
| Configuracao das analises | concluida | Proposta baseada em BRACED001/Fonseca e BRAAEG001, adaptada a duas campanhas. |
| Gate C — analises | aprovado parcial | Usuário autorizou somente a tabela taxonômica com BMWP para conferência. |
| Geracao dos produtos | concluida | Pacote completo R01 promovido na saída oficial após correção dos tipos de amostragem. |
| Revisao tecnica | concluida | 89 quantitativos, 63 qualitativos, abundância quantitativa 286; 16/16 figuras e validação OK. |
| Revisao tecnica | pendente | |
| Revisao de layout | pendente | |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved` | Usuário aprovou correções e confirmou ausências em 2026-09-09. |
| B — especies | `approved` | Usuário confirmou as decisões manuais em 2026-09-09. |
| C — analises | `partial` | Somente composição taxonômica com BMWP autorizada; pacote completo aguarda confirmação. |

## Validacao Dos Dados

- bloqueios:
  - `Metadados_Esforco` usa `C002-2026-06-SC`, enquanto pontos e resultados usam `C002-2026-07-SC`; corrigir os 20 esforços para julho.
  - 7 de 10 pontos divergem da malha definitiva: PT_01, PT_03, PT_04, PT_05, PT_07, PT_08 e PT_09.
- avisos:
  - três ponto-campanha sem resultados: PT_09/chuva, PT_09/seca e PT_10/seca; padrão igual ao observado nos grupos já processados, mas deve constar no Gate A.
  - `Pleidae` será tratada no Gate B, após a aprovação dos dados.
- coordenadas:
  - fonte espacial oficial: `Geo\2026\Projeto_WSPKIN001.kmz` e `Coordenadas_malha_definitiva_WSPKIN001.xlsx`.
  - CRS/sistema: SIRGAS 2000; UTM 23S na planilha oficial.
  - pontos sem coordenada: zero.
  - coordenadas fora da faixa esperada: zero; porém sete posições são antigas.
  - variacao por ponto/campanha: nenhuma dentro da fonte.
  - comparacao: PT_02, PT_06 e PT_10 coincidem; sete pontos divergem.
  - estrategia proposta no Gate A: substituir as 20 linhas ponto-campanha pela malha definitiva já aprovada no projeto.
- ajustes aplicados: campanha seca corrigida pelo usuário; coordenadas oficiais autorizadas para normalização controlada durante a carga.
- arquivos corrigidos: nenhum.

## Totais Validados

- 20 linhas de pontos, duas campanhas e 10 pontos por campanha.
- 152 resultados, 41 táxons e abundância numérica total 349.
- chuva: 60 resultados, 9 pontos com ocorrência e 29 táxons.
- seca: 92 resultados, 8 pontos com ocorrência e 35 táxons.
- 89 resultados quantitativos (`Rede D`, esforço 3) e 63 qualitativos (`Suber`, esforço 1).
- campos essenciais sem nulos; resultados positivos e numéricos; nenhuma duplicação táxon–método–ponto–campanha.

## Pendencias

- Gate A: concluído.
- Gate B: concluído; `Pleidae` cadastrada com BMWP 3, `Dryopidae` corrigida para identificação em família e classificações históricas mantidas.

## Migracao E Consolidacao

- IDs: projeto 211; campanhas 969 e 1013; Pleidae 6940.
- totais da fonte e banco: 20 pontos-campanha, 40 esforços, 152 resultados, 41 táxons e total 349.
- coordenadas: malha oficial, zero divergências nos dez pontos.
- outros grupos preservados: Fitoplâncton 124 linhas; Zooplâncton 244 linhas.
- backups: prefixo `public.backup_biota_wspkin001_20260909t105914_`; Dryopidae em `public.backup_especies_dryopidae_wspkin001_20260909t135827z`.
- consolidado: 152 linhas; chuva 60/87 e seca 92/262.

## Configuracao Das Analises

- numero de campanhas: duas — C001 chuva e C002 seca.
- template: A4 paisagem, painéis separados por campanha, espelhando BRACED001/Fonseca e BRAAEG001.
- paleta: identidade verde WSP (`#11420C`, `#19FF00`, `#6A8F63` e auxiliares).
- pasta de saida: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Zoobentos`.
- produtos: base consolidada; composição e ocorrência; riqueza e abundância; filos; diversidade alfa; Bray-Curtis e dendrogramas por amostra/ponto; suficiência; BMWP, EPT e CHOL; minimapas; táxons associados à fauna exótica; síntese; Darwin Core; HTML; manifesto e validação.
- planilha integrada adicional: por último, conforme decisão anterior.

## Gate C Parcial — Composição Taxonômica

- arquivo: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\01_tabela_composicao_taxonomica_zoobentos.xlsx`.
- conteúdo: 41 táxons, 152 registros de origem e coluna BMWP completa.
- abas: `Composicao_Taxonomica`, `Metadados` e `Conferencia`.
- validação: 42 linhas incluindo cabeçalho, 13 colunas, nenhum BMWP vazio e estrutura XLSX íntegra.
- pendência: aprovação do usuário antes da geração dos demais produtos.

## Revisão R01 — Tipo de amostragem

- erro confirmado: o migrador sobrescreveu o tipo explícito e registrou as 152 linhas como quantitativas.
- fonte correta: 89 quantitativas e 63 qualitativas.
- impacto: `data/analysis R3`; Gate A reaberto e pacote atual bloqueado para uso.
- registro: `docs/control_center/reviews/WSPKIN001_ZOOBENTOS_TIPO_AMOSTRAGEM_REV_R01.md`.
- correção aprovada e executada: remigração/reconsolidação com backup e pacote oficial substituído.
- Gate C concluído; pacote aguarda somente Gate R.
- prevencao aplicada: migrador com falha fechada para alteracao do tipo
  explicito ou incompatibilidade resultado x esforco; o plano de carga passou
  a registrar totais por campanha/tipo;
- Central de Controle reforcada nos Gates A, C e R pela politica de tipos de
  amostragem aquatica; dry-run preventivo aprovado em 2026-09-09.
