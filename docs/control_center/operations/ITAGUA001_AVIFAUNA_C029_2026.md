# ITAGUA001 â€” Avifauna â€” C029 Julho/2026

## Controle

- projeto: `ITAGUA001__monitoramento_da_fauna` / `id_projeto=165`
- grupo: Avifauna
- operacao: migracao, consolidacao e geracao dos resultados da campanha `C029-2026-07-SC`
- estado atual: `reviewing`
- aberta em: 2026-08-03
- atualizada em: 2026-08-03
- proxima acao: revisar produtos gerados e fechar Gate R.

## Caminhos

- dados:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/GuanhÃ£es Energia/Campanhas de campo/29_campanha-Julho_26/Avifauna/Dados/wetransfer_dados-brutos-fotos-e-planilhas-darwin-core_2026-07-25_2010/ITA-GUA-Dados_Avifauna_brutos-Campanha_29.xlsx`
  - versao corrigida Gate A R01: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/GuanhÃ£es Energia/Resultados e anÃ¡lises/29_campanha_Jul_26/Planilha_de_Campo/ITA-GUA-Dados_Avifauna_brutos-Campanha_29_C029_corrigida_GateA_R01.xlsx`
- cadastro de especies:
  - aba `Cadastro_Especies` no workbook fonte.
  - tabela mestre Supabase `public.especies`.
- saida:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhaes Energia/Resultados e analises/29_campanha_Jul_26/Avifauna`.
- dossie:
  - nao ha dossie especifico de `ITAGUA001`; registry aponta `docs/PIPELINE_ICTIO_165.md` como referencia historica de ictiofauna.
- recipe:
  - nao ha recipe especifica no registry para esta operacao.
- lastro:
  - `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna`.
  - nao aberto nesta etapa, por politica de contexto minimo.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Operacao criada para `ITAGUA001 / Avifauna / C029`. |
| Validacao | concluida | Dry-run com filtro C029 validou 90 pontos, 94 esforcos, 907 resultados, 1.545 individuos, 170 taxons, 0 pontos/esforcos/especies faltantes. |
| Gate A — dados | aprovado | Usuario aprovou em 2026-08-03 apos dry-run limpo; coordenadas da R01 aceitas para prosseguir. |
| Cadastro de especies | concluida | Usuario autorizou cadastro; 40 taxons ausentes foram cadastrados em `public.especies`; verificacao pos-cadastro com 0 ausentes. |
| Auditoria de atributos | concluida | Campos taxonomicos/ecologicos principais dos 40 taxons preenchidos; `N.A.`/vazios aceitos no Gate B. |
| Gate B — especies | aprovado | Usuario aprovou em 2026-08-03; campos `N.A.`/vazios aceitos como padrao operacional do grupo. |
| Migracao | concluida | C029 migrada com filtro: 90 pontos, 94 esforcos, 904 resultados agregados, 1.545 individuos, 170 taxons. |
| Consolidacao | concluida | Consolidado global reconstruido com 24.311 linhas; C029 Avifauna possui 904 linhas, 1.545 individuos e 170 taxons. |
| Configuracao das analises | concluida | Runner C029 por empreendimento, filtro `C029-2026-07-SC`, pasta `Resultados e analises/29_campanha_Jul_26/Avifauna`. |
| Gate C — analises | aprovado | Usuario aprovou prosseguimento em 2026-08-03; produtos gerados por quatro empreendimentos. |
| Geracao dos produtos | concluida | Quatro pastas geradas com 20 arquivos cada: Dores de Guanhaes, Fortuna II, Jacare, Senhora do Porto. |
| Revisao tecnica | pendente | |
| Revisao de layout | concluida | R01 aprovada no teste 02 e promovida para a pasta final `Avifauna`. |
| Revisao Venn PT-BR | concluida | Diagrama de Venn regenerado com acentos em portugues brasileiro (`Área`, `Espécies`, `Espécie`, `ESPÉCIES`). |
| Fechamento | pendente | Pacote final limpo; falta fechamento formal da operacao. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved` | Usuario aprovou em 2026-08-03 apos dry-run limpo. |
| B — especies | `approved` | Usuario aprovou em 2026-08-03; cadastro concluido e `N.A.`/vazios aceitos. |
| C — analises | `approved` | Produtos C029 por empreendimento gerados apos aprovacao de prosseguimento. |

## Validacao Dos Dados

- bloqueios:
  - A fonte contem duas campanhas (`C028-2026-04-SC` e `C029-2026-07-SC`); migracao deve usar somente `C029-2026-07-SC`.
  - O migrador deve ser executado com `--campaign C029-2026-07-SC`; sem filtro, a planilha completa tambem contem C028.
  - Nenhuma chave resultado->esforco faltante na C029 apos correcao R01 validada em 2026-08-03.
- dry-run:
  - executado em 2026-08-03 com `scripts/migrar_avifauna.py "<R01>" Avifauna --campaign C029-2026-07-SC --dry-run`.
  - filtro aplicado: `Pontos_e_Campanhas` 174 -> 90; `Metadados_Esforco` 178 -> 94; `Resultados_Avifauna` 1652 -> 907.
  - resultado: 0 pontos faltantes, 0 esforcos faltantes, 0 especies ausentes no banco; nenhuma gravacao executada.
- avisos:
  - A fonte corrigida R01 ainda contem duas campanhas: `Pontos_e_Campanhas` C029=90/C028=84; `Metadados_Esforco` C029=94; `Resultados_Avifauna` C029=907/C028=745.
  - A C029 possui 907 linhas de resultado, 1.545 individuos, 193 valores distintos brutos em `Nome_Cientifico` e 170 nomes normalizados por `strip`.
  - A C028 ja existe no consolidado de Avifauna do banco com 744 linhas, 72 pontos, 153 taxons e 1.315 individuos; nao deve ser reprocessada nesta operacao.
- coordenadas:
  - fonte espacial oficial: a definir.
  - CRS/sistema: pendente.
  - pontos sem coordenada: 0 na C029 da fonte corrigida R01.
  - coordenadas fora da faixa esperada: nenhuma faixa grosseira detectada; latitude C029 entre -19.078351 e -18.888745, longitude entre -42.947242 e -42.663101.
  - variacao por ponto/campanha: pendente.
  - comparacao com KMZ/KML/shapefile/planilha oficial: pendente.
  - estrategia aprovada no Gate A: pendente.
- ajustes aplicados:
  - Usuario gerou a versao corrigida Gate A R01; chaves `JCLD1-AV`, `JCLD2-AV`, `FOLD1-AV` e `FOLD2-AV` foram resolvidas.
- arquivos corrigidos:
  - `ITA-GUA-Dados_Avifauna_brutos-Campanha_29_C029_corrigida_GateA_R01.xlsx`.

## Cadastro E Auditoria De Especies

- especies novas:
  - 40 taxons do recorte C029 estavam ausentes na tabela mestre `public.especies` como Avifauna.
  - cadastro autorizado pelo usuario em 2026-08-03 e aplicado no banco.
  - verificacao pos-cadastro: 0 taxons ausentes no banco para o recorte C029.
- atributos obrigatorios:
  - auditoria dos 40 novos taxons: `nome_popular`, `ordem`, `familia`, `genero`, `guilda_alimentar` e `sensibilidade_ambiental` preenchidos em 40/40.
  - `dependencia_florestal` preenchida em 39/40.
  - campos de listas/status com preenchimento quando aplicavel: IUCN 1/40, MMA 1/40, COPAM 2/40, CITES 9/40, endemismo 1/40, migratorio 2/40; demais permanecem `N.A.`/vazios na fonte.
- campos incertos:
  - `raridade` sem preenchimento nos 40 novos taxons.
- ajustes manuais:
  - cadastro aplicado a partir da aba `Cadastro_Especies` da fonte corrigida R01.

## Migracao E Consolidacao

- IDs:
  - projeto Supabase: `id_projeto=165`.
  - campanha alvo: `C029-2026-07-SC`.
- totais da fonte:
  - `Pontos_e_Campanhas` C029: 90 pontos.
  - `Metadados_Esforco` C029: 94 esforcos na fonte corrigida R01.
  - `Resultados_Avifauna` C029: 907 linhas; 1.545 individuos.
- totais no banco:
  - antes da migracao, `biota_analise_consolidada` possui Avifauna apenas para `C028-2026-04-SC`: 744 linhas.
- coordenadas no banco/consolidado:
  - C029 consolidada em `biota_analise_consolidada`; 78 pontos com resultado, 90 pontos/esforcos cadastrados.
- divergencias:
  - sem divergencias bloqueantes pos-migracao/consolidacao.
- backup:
  - `biota_analise_consolidada_bkp_itagua001_avifauna_c029_20260803_1130`, criado antes da consolidacao com 23.407 linhas.
- totais consolidados:
  - global: 24.311 linhas em `biota_analise_consolidada`.
  - ITAGUA001/Avifauna/C029: 904 linhas, 1.545 individuos, 170 taxons, 78 pontos com resultado.

## Configuracao Das Analises

- numero de campanhas:
  - 1 campanha alvo: `C029-2026-07-SC`.
- template:
  - runner C029 de Avifauna por empreendimento.
- paleta:
  - tema `fersam001` via runner padrao.
- pasta de saida:
  - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhaes Energia/Resultados e analises/29_campanha_Jul_26/Avifauna`.
- produtos:
  - 4 conjuntos por empreendimento, 20 arquivos cada.

## Pendencias

- Revisar tecnicamente os produtos gerados e registrar Gate R.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| R01 | layout | R1 | review_completed | [ITAGUA001_AVIFAUNA_C029_LAYOUT_REV_R01.md](../reviews/ITAGUA001_AVIFAUNA_C029_LAYOUT_REV_R01.md) |

## Fechamento E Aprendizados

- validadores: pendente.
- manifesto: pendente.
- patterns: considerar extrair wrapper de migracao por campanha para Avifauna.
- portfolio: pendente.
- backlog:
  - migrador de Avifauna deve aceitar filtro de campanha, dry-run e manifestos de validacao antes de apply.
