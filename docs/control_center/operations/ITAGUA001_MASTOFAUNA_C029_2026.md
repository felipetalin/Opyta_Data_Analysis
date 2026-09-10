# ITAGUA001 - Mastofauna - C029/2026

## Controle

- projeto: ITAGUA001 / Monitoramento da Fauna
- grupo: Mastofauna
- operacao: migracao e resultados da campanha C029-2026-07-SC
- estado atual: `reviewing_outputs`
- aberta em: 2026-08-03
- atualizada em: 2026-08-03
- proxima acao: revisar pacote final C029/Mastofauna

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhăes Energia\Resultados e análises\29_campanha_Jul_26\Planilha_de_Campo\ITA-GNE-Dados_brutos-Mastofauna-Campanha_29.xlsx`
- cadastro de especies: aba `Especies` da planilha
- saida: a definir no Gate C
- dossie: nao aberto nesta etapa
- recipe: nao identificado no registry filtrado
- lastro: nao aberto nesta etapa

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto 165 / ITAGUA001 confirmado no registry filtrado; planilha localizada na pasta Planilha_de_Campo. |
| Validacao | concluida | Dry-run C029 OK apos correcao de ponto em resultados: `SPT2 / Busca ativa` ajustado para `SP2 / Busca ativa`. |
| Gate A - dados | aprovado | Usuario aprovou em 2026-08-03 apos dry-run C029 OK. |
| Cadastro de especies | concluido | Todos os 19 taxons usados na C029 existem na aba `Especies`; 10 ainda serao cadastrados/atualizados no banco. |
| Auditoria de atributos | concluida | `Akodon sp.` aceito como taxon aberto; `Callicebus personatus` e `Sapajus nigritus` atualizados com CITES II. |
| Gate B - especies | aprovado | Usuario aprovou `Akodon sp.` e atualizou CITES dos primatas em 2026-08-03. |
| Migracao | concluida | Carga C029 executada com filtro; 38 resultados agregados, 99 individuos, 19 taxons; 102 chaves unicas de esforco. |
| Consolidacao | concluida | Backup criado e consolidado reprocessado; recorte C029/Mastofauna auditado. |
| Configuracao das analises | concluida | Gate C aprovado pelo usuario em 2026-08-03. |
| Gate C - analises | aprovado | Usar pasta de saida C029/Mastofauna e padrao visual aprovado no ciclo. |
| Geracao dos produtos | concluida | Pacote C029 regenerado apos revisao da tabela 6.6/6.8; filtro de campanha efetivo; auxiliares removidos. |
| Revisao tecnica | concluida | 4 pastas validadas com 8 PNG + 10 XLSX; tabela 6.6/6.8 por empreendimento + area controle, sem vazios e sem primatas. |
| Revisao de layout | em andamento | Amostra 6.1 revisada sem mojibake e com folga para legenda. |
| Revisao tabela status | concluida | Causa identificada: migrador nao mapeava `Distribuicao`, `Cinegetica` e `Xerimbado`; banco atualizado a partir da aba `Especies`; gerador 6.6/6.8 ajustado para Mastofauna sem primatas e campos completos. |
| Revisao Venn PT-BR | concluida | Diagrama de Venn regenerado com acentos em portugues brasileiro (`Área`, `Espécies`, `Espécie`, `ESPÉCIES`). |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario: "aprovado" em 2026-08-03 |
| B - especies | `approved` | Usuario aprovou avanco em 2026-08-03; `Akodon` correto como taxon sem definicao; CITES II atualizado para `Callicebus personatus` e `Sapajus nigritus`. |
| C - analises | `approved` | Usuario aprovou em 2026-08-03. |

## Validacao Dos Dados

- bloqueios: nenhum no dry-run C029
- avisos:
  - planilha possui tambem dados C028; migrador foi ajustado para filtrar a campanha antes da limpeza
  - divergencia `DGN2 / Camera trap` x `DGN2 / Câmera trap` resolvida tecnicamente por normalizacao de acento nas chaves do migrador
  - pendencia anterior `SPT2 / Busca ativa` era nomenclatura incorreta em resultados; planilha atual usa `SP2 / Busca ativa`, coerente com `Metadados_Esforco`
- coordenadas:
  - fonte espacial oficial: pendente
  - CRS/sistema: pendente
  - pontos sem coordenada: 0 na C029
  - coordenadas fora da faixa esperada: 0 na faixa global; faixa C029 lat -19.0798141 a -18.8873047, lon -42.9577909 a -42.6369445
  - variacao por ponto/campanha: pendente
  - comparacao com KMZ/KML/shapefile/planilha oficial: pendente
  - estrategia aprovada no Gate A: pendente
- ajustes aplicados: resultado `SPT2 / Busca ativa` corrigido pelo usuario para `SP2 / Busca ativa`
- arquivos corrigidos: `G:\Meu Drive\Opyta\Opyta_Data\scripts\migrar_mastofauna.py` preparado com `--campaign` e `--dry-run`

## Cadastro E Auditoria De Especies

- especies novas: 10 taxons dos resultados ainda nao constam no banco, mas estao na aba `Especies` e podem ser cadastrados pelo migrador apos Gate B: `Akodon sp.`, `Cerradomys subflavus`, `Didelphis albiventris`, `Guerlinguetus brasiliensis`, `Monodelphis (Microdelphys) americana`, `Oligoryzomys nigripes`, `Philander quica`, `Procyon cancrivorus`, `Sapajus nigritus`, `Trinomys setosus`
- atributos obrigatorios: preenchidos para os campos principais; CITES II confirmado em `Callicebus personatus` e `Sapajus nigritus`
- campos incertos: `Akodon sp.` aceito como taxon ainda sem definicao especifica
- ajustes manuais: CITES dos primatas atualizado pelo usuario na planilha

## Migracao E Consolidacao

- IDs: projeto 165 / ITAGUA001
- totais da fonte: C029 = 83 pontos, 103 esforcos, 71 linhas de resultados, 99 individuos, 19 taxons nos resultados
- totais no banco: 102 esforcos unicos, 38 resultados agregados, 99 individuos, 19 taxons; sem chave de esforco faltante
- coordenadas no banco/consolidado: pendente
- divergencias: Excel possui 103 linhas de esforco, mas 102 chaves unicas por duplicidade `PMPRIJAC1 / Playback e transecto`; banco gravou 102 chaves unicas
- backup: `biota_analise_consolidada_bkp_itagua001_mastofauna_c029_20260803_1343` com 24.320 linhas
- totais consolidados: global 24.358 linhas; C029/Mastofauna = 38 linhas, 99 individuos, 19 taxons, 24 pontos com resultado

## Configuracao Das Analises

- numero de campanhas: C029 isolada para esta operacao; base historica preservada no banco para analises quando aprovadas
- template: diagnostico Mastofauna por empreendimento, C029
- paleta: padrao aprovado no ciclo ITAGUA001
- pasta de saida: sugerida `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhăes Energia\Resultados e análises\29_campanha_Jul_26\Mastofauna`
- produtos: por empreendimento, 8 PNG e 10 XLSX; arquivos `.txt` e `desktop.ini` removidos do pacote final

## Pendencias

- Fechamento operacional apos aprovacao final do usuario.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: pendente
- manifesto: pendente
- patterns: pendente
- portfolio: pendente
- backlog: registrar que, em Mastofauna, primatas permanecem no banco por origem dos dados, mas devem ser excluidos dos produtos finais de Mastofauna e tratados no programa/pipeline Primatas; tabela 6.6/6.8 deve usar a base filtrada sem primatas.
