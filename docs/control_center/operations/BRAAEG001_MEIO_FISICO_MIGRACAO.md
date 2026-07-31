# BRAAEG001 - Meio fisico - Migracao

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- grupo: Meio fisico
- operacao: migracao inicial dos dados fisicoquimicos
- estado atual: `superficial_minimaps_generated_pending_review`
- aberta em: 2026-07-02
- atualizada em: 2026-07-29
- proxima acao: revisar visualmente o pacote final de Agua Superficial; antes de produtos integrados, replicar os nomes de cursos d'agua da nova base da biota nos pontos compartilhados

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/Resultados_Meio_Fisico.xlsx`
- cadastro de especies: nao aplicavel; meio fisico usa cadastro de parametros/VMP
- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados`
- dossie: pendente; projeto ainda nao registrado em `docs/projects/`
- recipe: pendente; projeto ainda nao possui `configs/clients/braaeg001.json`
- lastro: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/0_Resultados_SGS/Resultados_SGS_consolidado_1AEGM002_20260702.xlsx`
- fluxo meio fisico: `docs/control_center/MEIO_FISICO_WORKFLOW.md`
- dados C02 Agua Superficial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/Campanha-02/Resultados-Agua_superficial`
- staging C02 Agua Superficial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/campanha_02_superficial/20260729T151930_staging_resultados_meio_fisico_c02_agua_superficial.xlsx`
- auditoria C02 x C01: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/campanha_02_superficial/20260729T151930_auditoria_c02_vs_c01_agua_superficial.xlsx`
- dry-run incremental C02: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/campanha_02_superficial/20260729T182456Z_dry_run_incremental_c02_agua_superficial_braaeg001.xlsx`
- SQL apply incremental C02: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/campanha_02_superficial/20260729T182456Z_apply_incremental_c02_agua_superficial_braaeg001.sql`
- SQL rollback incremental C02: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/campanha_02_superficial/20260729T182456Z_rollback_incremental_c02_agua_superficial_braaeg001.sql`
- log apply incremental C02: `logs/validacao_meio_fisico/20260729T183205Z_aplicacao_incremental_c02_agua_superficial_braaeg001.json`
- auditoria pos-incremental C02: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/campanha_02_superficial/20260729T183205Z_auditoria_pos_incremental_c02_agua_superficial_braaeg001.xlsx`
- consolidado pos-C02: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/consolidacao_pos_c02/20260729T183622Z_consolidado_meio_fisico_braaeg001_pos_c02.xlsx`
- auditoria de consolidacao pos-C02: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/consolidacao_pos_c02/20260729T183622Z_auditoria_consolidacao_meio_fisico_braaeg001_pos_c02.xlsx`
- saida Agua Superficial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados/superficial`
- teste de layout Agua Superficial: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados/superficial/_teste_layout`

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
| Validacao C02 - Agua Superficial | concluida | 12 XLS/PDF SGS extraidos para staging; 588 registros, 12 pontos, 49 parametros; sem parametro novo, sem unidade divergente e sem duplicidade. |
| Gate A/C02 - dados | aprovado | Aprovado pelo usuario em 2026-07-29. Pendencias informativas aceitas para staging: laudos informam projeto `1AEGM002`; datas XLS x PDF divergem em 11 laudos, usando XLS como fonte primaria e PDF como complemento quando XLS vazio. |
| Dry-run incremental C02 | concluido | 588 inserts planejados; 0 problemas de mapeamento; 0 duplicidades com o banco; banco antes 873 registros, esperado apos apply 1461. |
| Gate apply C02 | aprovado | Aprovado pelo usuario em 2026-07-29. |
| Migracao incremental C02 | concluida | Apply transacional executado; backup `backup_fisico_braaeg001_before_c02_20260729t183205z` com 873 linhas; 588 registros C02 inseridos. |
| Consolidacao C02 | concluida | Auditoria pos-incremental confirmou 1461 registros totais: Agua Superficial C01=588, Agua Superficial C02=588, Sedimento C01=156, Agua Subterranea C01=129. |
| Consolidacao analitica pos-C02 | concluida | Pasta de trabalho consolidada gerada a partir de `fisico_analise_consolidada`; 1461 registros, 2 campanhas, 3 matrizes, 15 pontos, 70 parametros, 0 duplicidades; cobertura Agua Superficial C01+C02 completa em 588 pares ponto-parametro. |
| Configuracao preliminar Agua Superficial | aprovada | Usuario restringiu analises ao momento para Agua Superficial. Referencia oficial corrigida para FERSAM Superficial (`SAM Metais/Produtos/Resultados/Meio_fisico/Superficial`). Prototipos de pH, Oxigenio Dissolvido e Ferro Dissolvido regenerados no padrao FERSAM: grafico unico por parametro, pontos no eixo X, duas campanhas em tons de verde, VMP vermelho continuo e faixa vermelha de violacao. Legenda dos limites simplificada para `VMP - Classe 2` com os respectivos valores, sem citar legislacao. Template aprovado pelo usuario em 2026-07-29. |
| Revisao de metadados de pontos | pendente | Validacao da nova base da biota em 2026-07-03 apontou divergencia de `Curso_d_Agua` em 12 pontos compartilhados. |
| Geracao dos produtos | concluida | Produtos de Agua Superficial gerados em `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados/superficial`: 1176 registros, 12 pontos, 2 campanhas, 49 parametros, 34 violacoes, 48 paineis por campanha, IQA e IET com 24 amostras cada. Auditoria `12_Auditoria_Execucao.json` com status `OK`. Em 2026-07-30, saida reorganizada em pasta unica, com paineis assumidos como layout final, sem PNGs individuais e sem planilhas `_dados.xlsx`. `01_Conformidade_Agua_Superficial.xlsx` reorganizada em abas por campanha (`Campanha-01-Chuva` e `Campanha-02-Seca`), com parametros em linhas, unidade, VMP CONAMA 357 Classe 2, VMP COPAM 8 Classe 2 e pontos amostrais em colunas. Criado `02_Dados_por_Parametro_Agua_Superficial.xlsx`, com 49 abas de parametros + aba `Indice`, reunindo os dados das duas campanhas em cada aba. Criado painel executivo unico de violacoes `04_painel_violacoes_chuva_seca.png` (subpaineis Chuva/Seca; 13 parametros, 34 violacoes), com um unico verde do layout e apoio em `04_Painel_Violacoes_por_Campanha.xlsx`; modelos separados por campanha removidos. Gerados minimapas A4 paisagem em painel Chuva/Seca para violacoes por ponto (`07_minimapa_violacoes_por_ponto_chuva_seca.png`), IQA (`08_minimapa_iqa_chuva_seca.png`) e IET (`09_minimapa_iet_chuva_seca.png`), com hidrografia do KMZ `Geo/1AEMG002/Hidrografia.kmz`, escala grafica, norte, legendas e planilha de apoio `07_Dados_Minimapas_Agua_Superficial.xlsx`. Versao detalhada preservada como `01_Conformidade_Agua_Superficial_detalhada.xlsx`. Observacao operacional: pasta antiga `03_parametros_vmp` aparece como item travado/inconsistente do Google Drive e bloqueou remocao por permissao, embora os arquivos finais estejam gravados na raiz da pasta `superficial`. |
| Revisao tecnica | preliminar concluida | Auditoria tabular validou 34 violacoes apos correcoes legais: Manganes Dissolvido e Amonia sem VMP direto; Nitrogenio Amoniacal em `mg N/L`; Escherichia coli com observacao na coluna CONAMA e 1000 NMP/100 mL na COPAM; SST com VMP apenas na COPAM; OD como `≥5`; Cloro Residual Livre sem comparacao direta. IQA: 16 amostras Otima e 8 Boa; IET recalculado com conversao de Fosforo Total em `mg P/L` para `ug/L`, resultando em 22 Mesotrofico e 2 Eutrofico. |
| Revisao de layout | pendente | Amostras visuais conferidas para pH, Ferro Dissolvido, percentual de violacao, IQA, IET e minimapas; aguardando revisao do usuario sobre o pacote final. |
| Fechamento | pendente | Depende dos validadores, manifesto e atualizacao de registro/lastro. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario aprovou em 2026-07-02 apos apresentacao da validacao `PASS_WITH_WARNINGS`. |
| B - parametros | `approved_with_adjustments` | Usuario devolveu `20260702T190158Z_gate_b_problemas_parametros_braaeg001_rev.xlsx`; decisoes normalizadas em `20260702T192427Z_gate_b_decisoes_normalizadas_braaeg001.xlsx`. |
| C - analises | `deferred` | Usuario decidiu aguardar a segunda campanha antes da geracao; proposta pronta permanece registrada em `20260702T200115Z_gate_c_proposta_analises_braaeg001.xlsx`. Antes de abrir Gate C novamente, revisar `Curso_d_Agua` dos pontos compartilhados com a biota. |
| A/C02 - dados | `approved` | Usuario aprovou em 2026-07-29; staging e auditoria C02 Agua Superficial aceitas para dry-run incremental. |
| Apply C02 | `approved_applied` | Usuario aprovou em 2026-07-29; carga incremental aplicada e auditada com 588 registros C02. |
| Consolidacao pos-C02 | `completed` | Consolidado analitico pronto para configuracao das analises; pendencia de `Curso_d_Agua` permanece apenas para produtos integrados/espaciais. |
| C/Superficial - layout e analises | `approved` | Tres graficos-teste gerados em `_teste_layout` e `_teste_layout_paineis_campanha` no padrao FERSAM Superficial. Em 2026-07-29, legenda dos VMPs revisada para `VMP - Classe 2`, pH validado sem quebra horizontal e sinais `<` removidos das figuras, mantendo a informacao nas planilhas de dados. Template aprovado pelo usuario em 2026-07-29. |

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

- Reabrir configuracao das analises para base consolidada com Agua Superficial C01+C02.
- Manter Gate C suspenso ate nova decisao do usuario sobre produtos.
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
