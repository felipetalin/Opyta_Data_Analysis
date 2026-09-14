# FERSAM001 - Meio fisico - Migracao

## Controle

- projeto: FERSAM001 / Sam Metais Diagnostico
- grupo: Meio fisico
- operacao: migracao inicial dos dados fisicoquimicos
- estado atual: `awaiting_data_approval`
- aberta em: 2026-07-02
- atualizada em: 2026-07-02
- proxima acao: Gate A - aprovar dados validados e ressalvas informativas antes da migracao

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Migração/Físico/Resultados_Meio_Fisico.xlsx`
- cadastro de especies: nao aplicavel; meio fisico usa cadastro de parametros em `cadastro_parametros_opyta.xlsx`
- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Resultados/Meio_físico`
- dossie: `docs/README_MEIO_FISICO.md`; `docs/MEIO_FISICO_MEMORIA_GOLD.md`
- recipe: `configs/clients/fersam001.json`
- lastro: `outputs/_project_scripts/FERSAM001__sam_metais_diagnostico/meio_fisico`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto, grupo, entradas, saida, dossies, recipe e lastro localizados. |
| Validacao | concluida | `logs/validacao_meio_fisico/20260702T145546Z_validacao_meio_fisico_sam.json` com `status: PASS`. |
| Gate A - dados | aguardando usuario | Validacao apresentada; migracao bloqueada ate aprovacao explicita. |
| Cadastro de especies | nao aplicavel | Meio fisico nao possui cadastro taxonomico; ver cadastro de parametros. |
| Auditoria de atributos | pendente | Registrar Gate B como nao aplicavel apos confirmacao do escopo pelo usuario. |
| Gate B - especies | pendente | Nao aplicavel tecnicamente, mas ainda precisa ficar registrado antes de migrar. |
| Migracao | pendente | Nao executar antes dos Gates A/B. |
| Consolidacao | pendente | Depende da carga controlada e comparacao fonte x banco. |
| Configuracao das analises | pendente | Depende da consolidacao. |
| Gate C - analises | pendente | Template, paleta, saida e produtos serao confirmados apos consolidacao. |
| Geracao dos produtos | pendente | Depende do Gate C. |
| Revisao tecnica | pendente | Depende dos produtos gerados. |
| Revisao de layout | pendente | Depende dos produtos gerados. |
| Fechamento | pendente | Depende dos validadores, manifesto e atualizacao do lastro. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `pending` | Aguardando aprovacao dos 2.408 registros validados e dos achados informativos. |
| B - especies | `pending` | Meio fisico sem especies; registrar como nao aplicavel apos confirmacao. |
| C - analises | `pending` | Aguardara consolidacao e proposta de template/paleta/saida. |

## Validacao Dos Dados

- bloqueios: nenhum bloqueio; validacao retornou `PASS`.
- avisos: nenhum `WARN`; achados apenas `INFO`.
- ajustes aplicados: nenhum ajuste novo aplicado nesta rodada; validacao apenas leu as planilhas.
- arquivos corrigidos: nenhum.
- evidencia: `logs/validacao_meio_fisico/20260702T145546Z_validacao_meio_fisico_sam.json`.
- resumo:
  - resultados: 2.408 registros;
  - pontos na base: 34;
  - pontos com resultados: 33;
  - cadastro de parametros: 62 parametros;
  - parametros nos resultados: 45;
  - matrizes: Agua Subterranea, Agua Superficial, Sedimento;
  - campanhas: Campanha-01-Seca, Campanha-02-Chuva;
  - laboratorio: LABLAAE;
  - erros de parse: 0;
  - sinais: `<` = 1.104; `>` = 10; `<=` = 0; `>=` = 0.
- achados informativos:
  - `SAM_22` ausente nos resultados, permitido como ponto seco;
  - `Dureza Total` e `Materia Organica` sem cadastro formal, permitidos pelo validador;
  - 24 parametros do cadastro sem uso nesta base, documentados no JSON.

## Cadastro E Auditoria De Especies

- especies novas: nao aplicavel.
- atributos obrigatorios: nao aplicavel.
- campos incertos: nao aplicavel.
- ajustes manuais: nao aplicavel.
- observacao operacional: para meio fisico, a etapa equivalente e o cadastro de parametros/VMP; a validacao pre-migracao conferiu cobertura e apontou apenas itens informativos.

## Migracao E Consolidacao

- IDs: Supabase `id_projeto` 62; `codigo_interno_opyta` FERSAM001.
- totais da fonte: 2.408 registros em `Resultados_Meio_Fisico.xlsx`.
- totais no banco: pendente; leitura em 2026-07-02 encontrou `FISICO_DB_URL`, mas a conexao ao banco expirou antes de retornar contagem.
- divergencias: pendente.
- backup: pendente; definir antes de inserir/truncar registros.
- totais consolidados: pendente.
- script previsto: `scripts/projects/sam_metais/migrar_meio_fisico_sam.py`.
- validador previsto: `scripts/projects/sam_metais/validar_meio_fisico_sam.py`.

## Configuracao Das Analises

- numero de campanhas: 2.
- template: pipeline Gold XLSX de meio fisico.
- paleta: `configs/clients/fersam001.json` com tema verde SAM.
- pasta de saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Resultados/Meio_físico`.
- produtos: blocos `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `b8`, `b9`, `b11`, `resumo`, `audit`.

## Pendencias

- Obter aprovacao explicita do usuario para Gate A.
- Registrar Gate B como nao aplicavel para meio fisico antes da migracao.
- Confirmar estrategia de migracao: dry-run, insercao incremental ou `--truncate`.
- Confirmar backup/estrategia de reversao antes de tocar no banco.
- Repetir leitura dos totais existentes no banco quando a conexao estiver disponivel.
- Depois da carga, comparar totais fonte x banco e registrar divergencias.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: pre-migracao `PASS`; pos-migracao pendente.
- manifesto: `12_Auditoria_Execucao.json` sera exigido na geracao dos produtos.
- patterns: usar regras compartilhadas em `src/opyta_analysis/meio_fisico/rules.py`.
- portfolio: FERSAM001 continua como referencia Gold de meio fisico.
- backlog: avaliar recipe dedicada de projeto se a operacao evoluir para pipeline recorrente.
