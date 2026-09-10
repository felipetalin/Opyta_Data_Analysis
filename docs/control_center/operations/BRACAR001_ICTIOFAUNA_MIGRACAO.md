# BRACAR001 - Ictiofauna - Migracao inicial

## Controle

- projeto: BRACAR001
- grupo: Ictiofauna
- operacao: Migracao inicial
- estado atual: `configuring_analysis`
- aberta em: 2026-08-31
- atualizada em: 2026-09-01
- proxima acao: propor template, paleta, pasta de saida e produtos de analise para o Gate C

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brasil PCH\Projeto Carangola\Resultados\Migracao\PCH_Brasil_Carangola_Ictiofauna_MIGRACAO_UNIFICADA_20260901.xlsx`
- cadastro de especies: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brasil PCH\Projeto Carangola\Resultados\Migracao\Cadastro\_especies\_opyta\_carangola-ictio-260901\_atualizado.xlsx` (a ser preparado pelo usuario)
- saida: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brasil PCH\Projeto Carangola\Resultados`
- lastro do projeto: `outputs/_project_scripts/BRACAR001__projeto_carangola`
- dossie: pendente
- recipe: pendente
- lastro: `outputs/_project_scripts/BRACAR001__projeto_carangola`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto `BRACAR001` confirmado como `Brasil PCH / Projeto Carangola`; planilha unificada de ictiofauna localizada em 2026-09-01; registry/config ainda inexistentes para o codigo. |
| Validacao | concluida | Validacao local da planilha unificada em 2026-09-01: 34 campanhas, 7 pontos, 238 registros ponto-campanha, 282 esforcos, 4.458 registros biologicos, 34 especies e 5.043 individuos; estrutura, chaves e campos nucleares conferidos. |
| Gate A - dados | concluido | Aprovado pelo usuario em 2026-09-01: `BRACAR001` como codigo definitivo; WGS84 e estrategia `sem_referencia_externa_aprovada` aceitos como ressalva. Planilha revalidada apos trocar `A_DEFINIR` por `BRACAR001`. |
| Cadastro de especies | validado estruturalmente | Cadastro atualizado recebido em 2026-09-01: 15 linhas correspondem exatamente aos 15 taxons antes ausentes; os demais 19 ja existem no cadastro. Cobertura dos 34 taxons completa, sujeita a aprovacao taxonomica. |
| Auditoria de atributos | auditada com pendencias | Os 15 novos registros possuem os 23 campos da planilha preenchidos; em 18 dos 19 taxons existentes ha ao menos um atributo de ameaca nacional/global, origem ou endemismo ausente. Nao houve preenchimento inferido. |
| Gate B - especies | concluido | Aprovado pelo usuario em 2026-09-01, com os qualificadores taxonomicos preservados conforme cadastro atualizado. |
| Migracao | concluida com revisao R01 | Cliente `Brasil PCH S.A.` e projeto `BRACAR001` (id `208`) cadastrados; 15 especies cadastradas. Fonte x banco: 34 campanhas, 238 pontos, 282 esforcos, 1.052 registros agregados, 34 especies e 5.043 individuos, sem divergencias. Revisão R01 preservou 4.458 detalhes individuais, incluindo EMG, PG e IGS. |
| Consolidacao | concluida | Backup `public.bkp_biota_analise_consolidada_pre_bracar001_20260901` criado com 39.529 linhas; consolidado global reconstruido com sucesso (40.581 linhas) e fatia BRACAR001 conferida. |
| Configuracao das analises | em andamento | Definir template, paleta, pasta de saida e produtos para o Gate C. |
| Gate C - analises | pendente | Aguardara aprovacao de template, paleta, saida e produtos. |
| Geracao dos produtos | pendente | Fora do escopo ate Gate C. |
| Revisao tecnica | pendente | |
| Revisao de layout | pendente | |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Aprovado pelo usuario em 2026-09-01: codigo definitivo `BRACAR001`, CRS WGS84 e estrategia `sem_referencia_externa_aprovada`. |
| B - especies | `approved` | Aprovado pelo usuario em 2026-09-01; usar o cadastro atualizado e preservar os qualificadores ainda nao confirmados. |
| C - analises | `pending` | Sem configuracao analitica aprovada. |

## Validacao Dos Dados

- bloqueios:
  - nenhum bloqueio de Gate A; a ressalva espacial foi aprovada pelo usuario.
  - cliente informado: `Brasil PCH S.A.`, CNPJ `07.314.233/0001-08`; nao existia na consulta ao banco. O cliente interno do Data_Analysis usa chave anonima somente para leitura e recusou escrita (HTTP 401). O fluxo correto de carga esta em `G:\Meu Drive\Opyta\Opyta_Data\scripts\cadastrar_especies.py` seguido de `migrar_ictiofauna.py`, ambos dependentes do `core.engine`; a conexao deste ambiente ao PostgreSQL expirou. Nenhuma alteracao foi aplicada ao banco.
- avisos:
  - a solicitacao informa que o escopo sera somente ictiofauna.
  - slug tecnico provisoriamente reservado em `outputs/_project_scripts/BRACAR001__projeto_carangola` ate confirmacao do nome canonico/registry.
- coordenadas:
  - fonte espacial oficial: nao fornecida
  - CRS/sistema: coordenadas geograficas decimais aparentes; confirmar como WGS84 ou fornecer fonte oficial
  - pontos sem coordenada: 0/238
  - coordenadas fora da faixa esperada: 0/238 (latitude: -20.7064563 a -20.6956792; longitude: -42.0789439 a -42.0373305)
  - variacao por ponto/campanha: nenhuma; os 7 pontos mantem uma unica latitude e longitude nas 34 campanhas
  - comparacao com KMZ/KML/shapefile/planilha oficial: nao executada por ausencia de fonte
  - estrategia aprovada no Gate A: pendente; propor `sem_referencia_externa_aprovada` como ressalva
- ajustes aplicados: `Capa_Projeto!Codigo_Opyta` atualizado de `A_DEFINIR` para `BRACAR001`, com revalidacao local concluida.
- arquivos corrigidos: nenhum

## Cadastro E Auditoria De Especies

- especies novas: 15 antes ausentes, agora apresentadas no cadastro atualizado: `Astyanax gr. lacustris`, `Astyanax sp. 1`, `Characidium sp.`, `Coptodon sp.`, `Deuterodon parahybae`, `Harttia loricariformis`, `Hasemania sp.`, `Hyphessobrycon sp.`, `Oligosarcus hepsetus`, `Neoplecostomus sp.`, `Phalloceros sp.`, `Pimelodella cf. lateristriga`, `Poecilia vivipara`, `Prochilodus lineatus` e `Psalidodon parahybae`.
- atributos obrigatorios: 18 dos 19 taxons localizados tem pelo menos um campo ausente entre ameaca nacional, ameaca global, origem e endemismo. O preenchimento requer fonte taxonomica aprovada, sem inferencia automatica.
- campos incertos: dez registros permanecem apenas no nivel de genero na verificacao nomenclatural: `Astyanax gr. lacustris`, `Astyanax sp.`, `Astyanax sp. 1`, `Characidium sp.`, `Coptodon sp.`, `Hasemania sp.`, `Hyphessobrycon sp.`, `Neoplecostomus sp.`, `Phalloceros sp.` e `Trichomycterus sp.`. Os qualificadores de `Knodus cf. moenkhausii` e `Pimelodella cf. lateristriga` devem ser preservados ate validacao do responsavel tecnico, embora o nome-base possua correspondencia.
- regra aprovada para o cadastro: preservar `gr.`, `sp.` e `cf.` quando a identificacao ainda depender de confirmacao; nao promover automaticamente esses registros. Quando o nome ja tiver classificacao definitiva no cadastro, manter a classificacao confirmada, como `Astyanax lacustris`.
- evidencia da consulta: cadastro remoto de especies consultado em 2026-09-01; 19 correspondencias exatas, 15 ausencias. `BRACAR001` tambem nao possui cadastro em `projetos`. Verificacao nomenclatural complementar no GBIF: 24 correspondencias exatas, 23 aceitas e uma sinonimia para `Hypomasticus copelandii`; os dez registros acima tiveram apenas correspondencia de genero. Planilha editavel de validacao entregue em `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brasil PCH\Projeto Carangola\Resultados\Migracao\BRACAR001_AUDITORIA_TAXONOMICA_GATE_B.xlsx`. Cadastro atualizado validado estruturalmente em `Cadastro_especies_opyta_carangola-ictio-260901_ESTRUTURA_VALIDADA.xlsx`, com manifesto `Cadastro_especies_opyta_carangola-ictio-260901_validacao_estrutura.json`: 15/15 linhas, sem pendencias estruturais e sem especie fora dos resultados.
- ajustes manuais: pendente

## Migracao E Consolidacao

- IDs: `id_projeto=208`; cliente `Brasil PCH S.A.` criado pelo fluxo padrao.
- totais da fonte: 34 campanhas; 238 pontos; 282 esforcos; 4.458 linhas brutas, agregadas em 1.052 registros; 34 especies; 5.043 individuos.
- totais no banco: 34 campanhas; 238 pontos; 282 esforcos; 1.052 registros; 34 especies; 5.043 individuos.
- coordenadas no banco/consolidado: pendente
- divergencias: nenhuma na comparacao fonte x banco em 2026-09-01.
- lastro de erro e solucao (R01, 2026-09-02): a migracao agregava os 4.458 registros em 1.052 linhas e descartava campos individuais (`Sexo`, `EMG`, `PG_g`, `IGS`). Solucao aplicada: `G:\Meu Drive\Opyta\Opyta_Data\scripts\migrar_detalhes_reprodutivos_ictio.py`, chamado pelo migrador oficial, grava a fonte individual em `public.resultados_ictiofauna_detalhe`. Resultado: 4.458 detalhes, 2.499 EMG preenchidos, 2.417 EMG numericos, 714 PG e 4.324 IGS; ver revisao `BRACAR001_ICTIOFAUNA_MIGRACAO_REPRODUCAO_REV_R01.md`.
- backup: `public.bkp_biota_analise_consolidada_pre_bracar001_20260901` (39.529 linhas antes da reconstrucao)
- totais consolidados: BRACAR001 com 1.052 registros, 34 campanhas, 7 pontos, 34 especies e 5.043 individuos; consolidado global com 40.581 linhas apos a reconstrucao.

## Configuracao Das Analises

- numero de campanhas: pendente
- template: pendente
- paleta: pendente
- pasta de saida: pendente
- produtos: pendente

## Pendencias

- Aprovar a fonte taxonomica e o tratamento dos 15 taxons ausentes, em especial os dez registros mantidos no nivel de genero e os dois qualificadores `cf.`.
- Receber e validar o cadastro atualizado informado pelo usuario antes de aplicar inclusoes ou atualizacoes no banco.
- Autorizar o preenchimento dos atributos obrigatorios a partir da fonte aprovada e revisar qualquer incerteza que permanecer.
- Cadastrar `BRACAR001` em `projetos` e no registry/canonical_key antes da carga controlada.
- Quando o runtime Opyta_Data estiver com conectividade ao banco, executar a cadeia ja padronizada: `cadastrar_especies.py`, depois `migrar_ictiofauna.py`; ela cria o cliente `Brasil PCH S.A.` (CNPJ `07.314.233/0001-08`), o projeto `BRACAR001` e carrega os dados aprovados de ictiofauna.
- Definir consolidacao: preferir carga incremental escopada a `BRACAR001`, com backup da fatia; a reconstrucao global por `processar_dados.py` so pode rodar com autorizacao expressa, pois executa `TRUNCATE` no consolidado de todos os projetos.
- Registrar o canonical_key definitivo no registry/config antes da etapa de consolidacao analitica, se o nome Supabase divergir do slug provisoriamente reservado em `outputs/_project_scripts`.

## Regras De Avanco Desta Operacao

- Nao avancar para migracao sem validacao concluida e Gate A aprovado.
- Nao avancar para migracao sem auditoria de especies concluida e Gate B aprovado ou marcado como `nao aplicavel`.
- Nao assumir template/paleta/saida sem Gate C explicito quando a operacao chegar na fase analitica.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| R01 — preservacao reprodutiva | dados/migracao | R3 | `awaiting_revision_approval` | [BRACAR001_ICTIOFAUNA_MIGRACAO_REPRODUCAO_REV_R01.md](../reviews/BRACAR001_ICTIOFAUNA_MIGRACAO_REPRODUCAO_REV_R01.md) |

## Fechamento E Aprendizados

- validadores: pendente
- manifesto: pendente
- patterns: pendente
- portfolio: pendente
- backlog: pendente
