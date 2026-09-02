# WSPKIN001 — Fitoplâncton — Migração inicial

## Controle

- projeto: WSPKIN001 / WSP Kinross Bandeirinhas
- grupo: Fitoplâncton
- operacao: Migração inicial
- estado atual: `registering_species`
- aberta em: 2026-09-02
- atualizada em: 2026-09-02
- proxima acao: Aguardar o preenchimento da planilha de pendências taxonômicas pelo usuário e revalidar antes do Gate B.

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração _Fito_wsp.xlsx`
- cadastro de especies: pendente.
- saida: pendente de definição no Gate C.
- dossie: não localizado no registry filtrado em 2026-09-02.
- recipe: não localizada no registry filtrado em 2026-09-02.
- lastro: pendente.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Operação criada; fonte identificada; registry ainda sem entrada WSPKIN001. |
| Validacao | concluida | Relatório em `outputs/validacoes/wspkin001_fitoplancton_20260902/`; estrutura e coordenadas internas OK, com cinco pendências. |
| Gate A — dados | concluido | Decisões do usuário registradas em 2026-09-02. |
| Cadastro de especies | em andamento | Consulta Supabase: 67/77 táxons já cadastrados; 10 novos pendentes. |
| Auditoria de atributos | em andamento | Dois registros existentes com classificação incompleta; relatório de auditoria Supabase criado. |
| Gate B — especies | pendente | |
| Migracao | pendente | |
| Consolidacao | pendente | |
| Configuracao das analises | pendente | |
| Gate C — analises | pendente | |
| Geracao dos produtos | pendente | |
| Revisao tecnica | pendente | |
| Revisao de layout | pendente | |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved_with_notes` | Ausências confirmadas; regra qualitativa/quantitativa e descarte de campos aprovados; ressalva espacial aceita. |
| B — especies | `pending` | Cadastro/auditoria taxonômica ainda não executados. |
| C — analises | `pending` | |

## Validacao Dos Dados

- bloqueios: nenhum no Gate A.
- avisos: nenhuma referência espacial externa disponível; ressalva aprovada pelo usuário.
- coordenadas: 20/20 válidas, uma coordenada por ponto; seguir sem comparação externa, aprovado em 2026-09-02.
- regra de transformação aprovada: `X` representa ocorrência de amostragem qualitativa; valor numérico representa abundância de amostragem quantitativa em `org/amostra`.
- campos descartados no mapeamento: `Malha_ou_Anzol`, `CT_cm`, `CP_cm`, `PC_g`, `Sexo`, `EMG` e `Observacao_Individuo_Lote` quando contiverem `N.A.`.
- ausências confirmadas: PT_03, PT_04, PT_06 e PT_09 em C001-2026-03-CH; PT_07, PT_09 e PT_10 em C002-2026-07-SC.
- ajustes aplicados: nenhum.
- arquivos corrigidos: nenhum.

## Cadastro E Auditoria De Especies

- especies novas: 10, listadas em `outputs/validacoes/wspkin001_fitoplancton_20260902/auditoria_cadastro_supabase_wspkin001_fitoplancton_20260902.md`; planilha criada em `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Cadastro_Especies_WSPKIN001_Fitoplancton.xlsx`.
- atributos obrigatorios: 67/77 táxons encontrados; `Euastrum sp.` e `Phacus orbicularis` sem classe, ordem e família.
- campos incertos: classificação e autoria dos 10 táxons novos aguardam auditoria.
- ajustes manuais: nenhum.

## Migracao E Consolidacao

- IDs: pendente.
- totais da fonte: pendente.
- totais no banco: pendente.
- coordenadas no banco/consolidado: pendente.
- divergencias: pendente.
- backup: pendente.
- totais consolidados: pendente.

## Configuracao Das Analises

- numero de campanhas: pendente.
- template: pendente.
- paleta: pendente.
- pasta de saida: pendente.
- produtos: pendente.

## Pendencias

- Identidade Supabase confirmada na abertura: cliente WSP `id_cliente=216`; WSPKIN001 `id_projeto=211`. O preflight da migração somente reconfirmará esses IDs.

## Fechamento E Aprendizados

- validadores: pendente.
- manifesto: pendente.
- patterns: pendente.
- portfolio: pendente.
- backlog: pendente.
