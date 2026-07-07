# BRAAEG001 - Meio fisico - Migracao

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- grupo: Meio fisico
- operacao: migracao inicial dos dados fisicoquimicos
- estado atual: `awaiting_analysis_approval`
- aberta em: 2026-07-02
- atualizada em: 2026-07-03
- proxima acao: aguardar segunda campanha antes da geracao; antes de produtos integrados, replicar os nomes de cursos d'agua da nova base da biota nos pontos compartilhados

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/Resultados_Meio_Fisico.xlsx`
- cadastro de especies: nao aplicavel; meio fisico usa cadastro de parametros/VMP
- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados`
- dossie: pendente; projeto ainda nao registrado em `docs/projects/`
- recipe: pendente; projeto ainda nao possui `configs/clients/braaeg001.json`
- lastro: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/0_Resultados_SGS/Resultados_SGS_consolidado_1AEGM002_20260702.xlsx`
- fluxo meio fisico: `docs/control_center/MEIO_FISICO_WORKFLOW.md`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Entrada, saida, projeto informado na capa e lastro SGS localizados. |
| Validacao | concluida com aviso | `logs/validacao_meio_fisico/20260702T172605Z_validacao_meio_fisico_braaeg001.json` com `PASS_WITH_WARNINGS`. |
| Gate A - dados | aprovado | Aprovado pelo usuario em 2026-07-02. Estrategia aprovada: cadastro mestre + delta de parametros novos/divergentes. |
| Cadastro de especies | nao aplicavel | Meio fisico nao possui cadastro taxonomico. |
| Auditoria de atributos | concluida com delta | Auditoria de parametros/VMP contra `parametros_analise` gerou delta para revisao. |
| Gate B - especies | aprovado com ajustes | Usuario devolveu planilha `_rev.xlsx`; 45/45 linhas decididas e normalizadas para execucao. |
| Migracao | concluida | Apply autorizado executado por SQL transacional via `core.engine`; 873 registros inseridos e projeto `id_projeto=195` criado. |
| Consolidacao | concluida | Carga gravada em `fisico_analise_consolidada`; auditoria pos-migracao `PASS` sem divergencia por matriz/campanha/ponto. |
| Configuracao das analises | concluida para Gate C | Proposta registrada em `20260702T200115Z_gate_c_proposta_analises_braaeg001.xlsx`. |
| Gate C - analises | adiado pelo usuario | Usuario decidiu nao gerar agora e aguardar a segunda campanha; somente balanco intermediario foi solicitado. |
| Revisao de metadados de pontos | pendente | Validacao da nova base da biota em 2026-07-03 apontou divergencia de `Curso_d_Agua` em 12 pontos compartilhados. |
| Geracao dos produtos | pendente | Depende do Gate C. |
| Revisao tecnica | pendente | Depende dos produtos gerados. |
| Revisao de layout | pendente | Depende dos produtos gerados. |
| Fechamento | pendente | Depende dos validadores, manifesto e atualizacao de registro/lastro. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario aprovou em 2026-07-02 apos apresentacao da validacao `PASS_WITH_WARNINGS`. |
| B - parametros | `approved_with_adjustments` | Usuario devolveu `20260702T190158Z_gate_b_problemas_parametros_braaeg001_rev.xlsx`; decisoes normalizadas em `20260702T192427Z_gate_b_decisoes_normalizadas_braaeg001.xlsx`. |
| C - analises | `deferred` | Usuario decidiu aguardar a segunda campanha antes da geracao; proposta pronta permanece registrada em `20260702T200115Z_gate_c_proposta_analises_braaeg001.xlsx`. Antes de abrir Gate C novamente, revisar `Curso_d_Agua` dos pontos compartilhados com a biota. |

## Validacao Dos Dados

- bloqueios: nenhum erro estrutural encontrado.
- avisos:
  - a aba `Resultados_Meio_Fisico` nao contem colunas VMP;
  - conformidade, percentual de violacao e sintese dependem de cadastro/lookup de VMP antes da geracao analitica.
- ajustes aplicados: nenhum ajuste novo aplicado nesta rodada; validacao apenas leu a planilha.
- arquivos corrigidos: nenhum.
- evidencia: `logs/validacao_meio_fisico/20260702T172605Z_validacao_meio_fisico_braaeg001.json`.
- hash SHA-256 da entrada: `8c32c8e47434f6df2c10f14c15b24476953a75d1089474f5cb65498d60de8bcf`.
- resumo:
  - codigo na capa: BRAAEG001;
  - projeto na capa: A&G Mineracao;
  - cliente: Brandt;
  - resultados: 873 registros;
  - pontos: 15 na base e 15 nos resultados;
  - campanha: `C001-2026-02-CH`;
  - matrizes: Agua Superficial, Sedimento, Agua Subterranea;
  - parametros distintos: 70;
  - laboratorio: Geosol;
  - erros de parse: 0;
  - sinais: `<` = 283; sem sinal = 590;
  - duplicidades no grao de migracao: 0;
  - pares `Ponto + Campanha` fora da base: 0.
- totais por matriz:
  - Agua Superficial: 588 registros, 12 pontos, 49 parametros;
  - Sedimento: 156 registros, 12 pontos, 13 parametros;
  - Agua Subterranea: 129 registros, 3 pontos, 43 parametros.
- atualizacao de cursos d'agua compartilhados:
  - a nova base de biota validada em `20260703T113813_validacao_nova_base_biota_aquatica_braaeg001.xlsx` registrou divergencia de `Curso_d_Agua` em 12 pontos `PT_01` a `PT_12`;
  - a tabela `fisico_analise_consolidada` nao possui coluna `curso_d_agua`, entao a migracao fisicoquimica ja executada nao muda os resultados analiticos;
  - a revisao deve ser feita no cadastro/planilha de pontos antes de produtos integrados ou nova consolidacao de metadados.

## Cadastro E Auditoria De Especies

- especies novas: nao aplicavel.
- atributos obrigatorios: nao aplicavel.
- campos incertos: nao aplicavel.
- ajustes manuais: nao aplicavel.
- substituicao operacional: auditar cadastro de parametros/VMP.
- regra proposta: reaproveitar o cadastro mestre de parametros/VMP e gerar apenas o delta de novos/divergentes, como na biota.
- fonte de confronto do laudo: workbook consolidado SGS `Resultados_SGS_consolidado_1AEGM002_20260702.xlsx`, que preserva `VMP_01`, `VMP_02`, `VMP_03` e legendas dos laudos.
- classes esperadas na auditoria: `matched`, `synonym_review`, `unit_review`, `vmp_review`, `new_parameter`, `not_applicable`.
- evidencia da auditoria: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T184519Z_auditoria_parametros_braaeg001.xlsx`.
- log da auditoria: `logs/validacao_meio_fisico/20260702T184519Z_auditoria_parametros_braaeg001.json`.
- recorte operacional dos problemas: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T190158Z_gate_b_problemas_parametros_braaeg001.xlsx`.
- log do recorte: `logs/validacao_meio_fisico/20260702T190158Z_gate_b_problemas_parametros_braaeg001.json`.
- aba de decisao do usuario: preencher somente `decisao_gate_b`, coluna `decisao_usuario`, com `APROVAR`, `ALTERAR`, `NAO_APROVAR` ou `NAO_APLICAVEL`.
- planilha revisada pelo usuario: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T190158Z_gate_b_problemas_parametros_braaeg001_rev.xlsx`.
- decisoes normalizadas: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T192427Z_gate_b_decisoes_normalizadas_braaeg001.xlsx`.
- log das decisoes normalizadas: `logs/validacao_meio_fisico/20260702T192427Z_gate_b_decisoes_normalizadas_braaeg001.json`.
- cadastro mestre consultado: `public.parametros_analise`, 236 linhas.
- cobertura:
  - combinacoes `Matriz + Parametro + Unidade` auditadas: 105;
  - `matched`: 60;
  - `new_parameter`: 1;
  - `synonym_review`: 18;
  - `unit_review`: 23;
  - `vmp_review`: 3.
- foco Gate B:
  - problemas revisaveis: 45 combinacoes;
  - aceite operacional de unidade: 16;
  - cadastro com VMP de fonte: 6;
  - cadastro sem VMP: 12;
  - cadastro/correcao simples: 2;
  - mapeamento de alias: 1;
  - revisao tecnica: 6;
  - revisao/preenchimento de VMP: 3.
- decisao do usuario:
  - linhas decididas: 45/45;
  - linhas sem decisao: 0;
  - aprovado conforme sugestao: 16;
  - aprovado com ajuste/instrucao do usuario: 29;
  - grupos de acao: 17 cadastros de parametro, 20 ajustes/aceites de unidade, 7 VMPs e 1 alias/nomenclatura.
- cadastros provaveis:
  - detalhe operacional na aba `cadastro_sugerido` do recorte Gate B;
  - Agua Subterranea / Alcalinidade de Bicarbonato / `mg CaCO3/L`;
  - Agua Subterranea: Boro Total, Fluoreto, Molibdenio Total e Vanadio Total com VMP de fonte;
  - parametros sem VMP de fonte para serie historica/apoio, separados como `cadastro_simples`.
- revisoes de VMP destacadas:
  - Agua Superficial / Cloreto: laudo indica `250`, cadastro mestre sem VMP ativo para a referencia usada;
  - Agua Subterranea / Cloreto Dissolvido: cadastro mestre traz VMP ativo `0,07`, marcado como suspeito para conferencia;
  - Agua Subterranea / Bario Total: laudo indica `0,7`, cadastro mestre sem VMP ativo para a referencia usada;
  - Agua Superficial / Bario Total: laudo indica `0,7`, cadastro mestre sem VMP ativo para a referencia usada;
  - Agua Superficial / Cobre Dissolvido: laudo `0,009`, cadastro mestre `0,013`.

## Migracao E Consolidacao

- IDs: codigo interno na planilha `BRAAEG001`; `id_projeto` Supabase `195`.
- registry local: projeto ainda nao encontrado em `docs/registry/project_registry.json`.
- consulta Supabase: REST em 2026-07-02 retornou vazio para `BRAAEG001` e `1AEGM002` em `public.projetos`.
- totais da fonte: 873 resultados.
- dry-run controlado: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T193527Z_dry_run_migracao_controlada_braaeg001.xlsx`.
- log do dry-run: `logs/validacao_meio_fisico/20260702T193527Z_dry_run_migracao_controlada_braaeg001.json`.
- SQL apply gerado: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T193527Z_braaeg001_gate_b_apply_dry_run.sql`.
- SQL rollback gerado: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/20260702T193527Z_braaeg001_gate_b_rollback.sql`.
- resultado do dry-run:
  - preview de migracao: 873 registros;
  - Agua Superficial: 588;
  - Agua Subterranea: 129;
  - Sedimento: 156;
  - parametros sem mapeamento: 0;
  - valores numericos nulos por ausencia/N.A.: 18;
  - inserts planejados em `parametros_analise`: 18;
  - updates planejados em `parametros_analise`: 5;
  - aliases locais de migracao: 5;
  - projeto existente no Supabase: 0;
  - registros existentes em `fisico_analise_consolidada` para `BRAAEG001`: 0.
- tentativa de apply REST: REST com `SUPABASE_ANON_KEY` em 2026-07-02 bloqueou no primeiro passo com HTTP 401; acesso corrigido para o padrao da biota via `core.engine.get_engine()`.
- log do bloqueio: `logs/validacao_meio_fisico/20260702T193740Z_aplicacao_bloqueada_401_braaeg001.json`.
- apply final: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G MineraÃ§Ã£o/resultados/Meio_fisico/migracao/20260702T195747Z_aplicacao_migracao_controlada_braaeg001.json`.
- modo de acesso final: `sqlalchemy_core_engine`, transacional.
- backup de parametros atualizados: `public.backup_parametros_analise_braaeg001_20260702t195615z`, 5 linhas.
- escrita parcial: nao ocorreu na tentativa REST; apply final concluido em transacao unica.
- totais no banco: 873 registros para `BRAAEG001` em `fisico_analise_consolidada`.
- auditoria pos-migracao: `logs/validacao_meio_fisico/20260702T195832Z_auditoria_pos_migracao_braaeg001.json`.
- planilha de auditoria pos-migracao: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G MineraÃ§Ã£o/resultados/Meio_fisico/migracao/20260702T195832Z_auditoria_pos_migracao_braaeg001.xlsx`.
- divergencias: nenhuma; fonte e banco batem em 873 linhas, 3 matrizes, 1 campanha, 15 pontos e 70 parametros.
- totais por matriz no banco: Sedimento 156; Agua Subterranea 129; Agua Superficial 588.
- valores numericos nulos mantidos: 18, conforme dry-run; sinais de limite no banco: 283.
- parametros no cadastro mestre apos apply: 254; foram inseridos 18 parametros e atualizados 5.
- totais consolidados: carga direta na tabela consolidada auditada com `PASS`.
- estrategia executada: carga controlada em `fisico_analise_consolidada`, com comparacao por matriz, campanha e ponto.

## Configuracao Das Analises

- numero de campanhas: 1.
- template proposto: pipeline principal `meio_fisico` via banco, blocos 1-7, baseado no portfolio `meio_fisico_conformidade_sam`.
- paleta proposta: tema Gold aprovado com cores tecnicas de meio fisico.
- pasta de saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados`.
- produtos propostos: conformidade, percentual de violacao, series por parametro com VMP, IQA/IET para Agua Superficial, IQASB para Agua Subterranea, mPELq para Sedimento e manifesto/auditoria final.
- proposta Gate C: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G MineraÃ§Ã£o/resultados/Meio_fisico/migracao/20260702T200115Z_gate_c_proposta_analises_braaeg001.xlsx`.
- log da proposta Gate C: `logs/validacao_meio_fisico/20260702T200115Z_gate_c_proposta_analises_braaeg001.json`.
- decisao do usuario em 2026-07-02: nao gerar produtos agora; aguardar a segunda campanha para economizar processamento/tokens.
- balanco intermediario: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G MineraÃ§Ã£o/resultados/Meio_fisico/migracao/20260702T201301Z_balanco_pontos_parametros_matrizes_braaeg001.xlsx`.
- log do balanco: `logs/validacao_meio_fisico/20260702T201301Z_balanco_pontos_parametros_matrizes_braaeg001.json`.
- resumo do balanco:
  - registros: 873;
  - campanhas: 1;
  - matrizes: 3;
  - pontos: 15;
  - parametros: 70;
  - Sedimento: 156 registros, 12 pontos, 13 parametros;
  - Agua Subterranea: 129 registros, 3 pontos, 43 parametros;
  - Agua Superficial: 588 registros, 12 pontos, 49 parametros.

## Pendencias

- Aguardar dados da segunda campanha de meio fisico para decidir geracao consolidada.
- Manter Gate C suspenso ate entrada da segunda campanha ou nova decisao do usuario.
- Replicar nomes de cursos d'agua da nova base da biota no Meio Fisico antes de abrir Gate C novamente.
- Migracao da biota deve aguardar Gate A limpo e Gate B taxonomico aprovado.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: pre-migracao `PASS_WITH_WARNINGS`; pos-migracao `PASS`.
- manifesto: pendente.
- patterns: usar fluxo `docs/control_center/MEIO_FISICO_WORKFLOW.md`.
- portfolio: pendente.
- backlog: criar recipe `configs/clients/braaeg001.json` se o projeto seguir para geracao recorrente.
