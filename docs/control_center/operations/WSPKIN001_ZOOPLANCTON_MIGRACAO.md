# WSPKIN001 — Zooplâncton — Migração inicial

## Controle

- projeto: WSPKIN001 / Kinross
- grupo: Zooplâncton
- operacao: Migração inicial
- estado atual: `registering_species`
- aberta em: 2026-09-02
- atualizada em: 2026-09-02
- proxima acao: Aguardar o preenchimento da planilha de cinco táxons novos, revalidar e aplicar o cadastro antes do Gate B.

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração_zooPLAN.xlsx`
- cadastro de especies: pendente de auditoria após Gate A.
- saida: pendente de definição no Gate C.
- dossie: pendente.
- recipe: pendente.
- lastro: pendente.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | WSPKIN001 confirmado no Supabase como `id_projeto=211`. |
| Validacao | concluida | 244 registros, 61 táxons e 20 chaves espaciais; relatório de pré-migração criado. |
| Gate A — dados | concluido | Ausências confirmadas pelo usuário em 2026-09-02. |
| Cadastro de especies | em andamento | Consulta Supabase: 56/61 táxons já cadastrados após normalização de espaços; planilha de cinco novos táxons criada. |
| Auditoria de atributos | concluida | Nenhum registro existente com atributo obrigatório incompleto. |
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
| A — dados | `approved_with_notes` | Ausências confirmadas; regra quali/quanti e ressalva espacial já aprovadas. |
| B — especies | `pending` | |
| C — analises | `pending` | |

## Validacao Dos Dados

- bloqueios: nenhum no Gate A.
- avisos: a aba de resultados conserva campos herdados de ictiofauna.
- coordenadas: 20/20 válidas, uma coordenada por ponto; seguir sem referência espacial externa, conforme ressalva aprovada para WSPKIN001.
- regra de transformação: `X` é ocorrência qualitativa; valores numéricos são abundância quantitativa em `org/amostra`.
- campos descartados no mapeamento: `Malha_ou_Anzol`, `CT_cm`, `CP_cm`, `PC_g`, `Sexo`, `EMG` e `Observacao_Individuo_Lote` quando contiverem `N.A.`.
- ajustes aplicados: regra de mapeamento registrada; fonte original preservada.
- arquivos corrigidos: nenhum.

## Cadastro E Auditoria De Especies

- especies novas: 5; planilha criada em `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Cadastro_Especies_WSPKIN001_Zooplancton.xlsx`.
- atributos obrigatorios: 56 táxons cadastrados após normalização de espaços; nenhum incompleto.
- campos incertos: classificação e autoria dos cinco táxons novos aguardam preenchimento e revalidação.
- ajustes manuais: nenhum.

## Pendencias

- Ausências confirmadas: PT_09 em C001-2026-03-CH, PT_09 em C002-2026-07-SC e PT_10 em C002-2026-07-SC.
- Gate B: aguarda o preenchimento da planilha de pendências taxonômicas.

## Fechamento E Aprendizados

- validadores: pendente.
- manifesto: pendente.
- patterns: pendente.
- portfolio: pendente.
- backlog: pendente.
