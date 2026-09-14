Status: draft — auditoria de conhecimento, não altera código
Ultima atualizacao: 2026-08-17
Autor: auditoria assistida (GitHub Copilot), revisão humana pendente

Este documento cobre as ETAPAS 1 e 2 do pedido de auditoria: inventário do
conhecimento existente e sua classificação em grandes grupos. O Manual de
Migração e Validação (Etapa 3), a comparação com o validador atual (Etapa 4)
e o backlog priorizado (Etapa 5) estão em
[docs/MANUAL_MIGRACAO_VALIDACAO_OPYTA_DATA.md](MANUAL_MIGRACAO_VALIDACAO_OPYTA_DATA.md).

> Convenção de proveniência usada em todo o documento:
> **[E]** = regra comprovadamente existente (lida em arquivo/código real, com
> caminho citado) · **[I]** = regra inferida (dedução a partir de padrão de
> código ou de casos repetidos, sem declaração explícita) · **[R]** = recomendação
> nova da auditoria, ainda não existente em nenhum lugar do projeto.

---

## Escopo e método

Dois ambientes foram lidos:

- **Opyta_Data_Analysis** (`g:\Meu Drive\Opyta\Opyta_Data_Analysis`) — motor de
  análises do dia a dia, scripts ad-hoc, memória de aprendizado, Central de
  Controle (`docs/control_center`).
- **Opyta_Data** (`G:\Meu Drive\Opyta\Opyta_Data`) — app Streamlit de
  upload/validação/migração para Supabase (o alvo da melhoria pedida).

Não foi lido, por não ser o alvo da migração/validação hoje: `Opyta_Data_novo`
(cópia com estrutura mais enxuta, aparenta ser checkpoint antigo — **[I]**,
merece confirmação com o usuário antes de qualquer decisão que dependa dela).

---

## ETAPA 1 — Inventário do conhecimento

### 1.1 Opyta_Data (app Streamlit — raiz)

| Arquivo/local | Assunto | Tipo de conhecimento | Relevância | Aplicação possível |
|---|---|---|---|---|
| `NORTE.md` | Divergência editor×disco×commit×deploy | Regra operacional de deploy | Alta | Base do gate de deploy do manual |
| `README.md` | Mapa de pastas do app (app/core/runners/validators/scripts) | Documentação estrutural | Média | Onboarding de colaborador |
| `ARQUITETURA_ESTRATEGIA.md` | Decisão Streamlit vs Next.js, roadmap 3 fases | Decisão arquitetural | Média-alta | Justifica manter validação em Python/Streamlit |
| `PLANO_MELHORIAS_STREAMLIT.md` | 6 blocos de melhoria (UX, cache, status, plotly, auditoria, modelos oficiais) | Roadmap de produto | Muito alta | Backlog P1-P3 (Bloco 5 e 6 tocam validação direto) |
| `PRIORIDADE_MELHORIAS.md` | Matriz impacto×esforço dos blocos acima | Planejamento | Média | Cronograma de referência |
| `DEPLOYMENT_CHECKLIST.md` | Regra de ouro `commit != deploy`; checklist 4 passos | Regra operacional crítica | Crítica | Gate de deploy do manual |
| `SETUP_SUPABASE.txt` | Passo a passo de setup local + `.env` + teste de conexão | Guia operacional | Alta | Onboarding de colaborador |
| `LASTRO_ATIVIDADES_2026-06-20.txt` | Portabilidade de auditoria/lineage, normalização de campanha, página Qualidade | Histórico + regras | Crítica | Normalização de campanha, auditoria obrigatória |
| `META_PROXIMAS_ETAPAS.txt` | Visão estratégica + 3 aprendizados operacionais críticos (ordem espécies→migração, espécie desconhecida condicional, captura de observações) | Estratégia + regras de negócio | Crítica | Núcleo do Manual (Etapa 3) |
| `SEGURANCA_STATUS_2026-04-09.md` | Auth, RBAC pendente, consolidação segura (simulação+backup+confirmação) | Segurança | Alta | Regras de consolidação segura e RBAC |
| `REGISTRO_CONVERSA_PORTAL_CLIENTE_2026-04-15.txt` | Decisão: portal cliente Next.js é read-only, Streamlit mantém escrita | Decisão arquitetural | Média | Confirma que validação/migração ficam só no Streamlit |
| `validators/base.py` | Interfaces abstratas (stub, não usado) | Código (estrutura) | Baixa | — |
| `validators/registry.py` | Registro de validadores por grupo | Código | Média | Mapa grupo→validador |
| `validators/common_checks.py` | Checks reutilizáveis (colunas, nulos, duplicatas, negativos) | Código | Alta | Base para novas regras comuns |
| `validators/findings.py` | Modelo rico de achado (Severidade/TipoAchado/StatusRevisao) | Código (modelo de dados) | Alta | Padrão de mensagem ao usuário |
| `validators/gate_a_rules.py` | Documentação textual das regras de Gate A | Documentação + regra | Crítica | Espinha dorsal do Manual |
| `validators/especies/*.py` (reader, normalizer, rules, db_checker, pipeline, report, render) | Validação do cadastro mestre de espécies | Código completo | Crítica | Base de comparação Etapa 4 |
| `validators/importacao/*.py` (reader, checkers, pipeline, report, render) | Validação de planilhas de importação por grupo biológico | Código completo | Crítica | Base de comparação Etapa 4 |
| `core/engine.py` | Conexão Supabase/Postgres (`get_engine`) | Código de infraestrutura | Alta | Pré-requisito técnico |
| `core/audit/manifest.py` | `record_operation`, `load_audit_log`, git_context, sha256 | Código de auditoria | Alta | Trilha de migração/validação |
| `core/campanha.py` | `normalizar_nome_campanha()` → `C{NNN}-{YYYY}-{MM}-{SC|CH}` | Código (regra de negócio) | Crítica | Regra de campanha do Manual |
| `core/modelos_oficiais.py` | Especificação dos modelos oficiais de planilha | Código | Alta | Reduz erro na origem |
| `app/pages/00_Base_Mestre.py` | UI de cadastro de espécies/parâmetros (Gate A bloqueante) | Código de fluxo | Crítica | Etapa "preparação"/"validação" do fluxo |
| `app/pages/01_Importacao.py` | UI de upload + validação + disparo de migração | Código de fluxo | Crítica | Coração do fluxo upload→migração |
| `app/pages/02_Consolidacao.py` | UI de consolidação com simulação/backup/confirmação | Código de fluxo | Crítica | Regra de consolidação segura |
| `app/pages/05_Qualidade_Dados.py` | Painel de auditoria/lineage (KPIs, histórico) | Código de fluxo | Alta | Rastreabilidade para colaborador |
| `app/pages/00_Pipeline_Status.py` | Dashboard de status operacional | Código de fluxo | Média | Visibilidade de pendências |
| `runners/registry.py` | Mapa grupo biológico → script de migração → tabela destino | Código (registro central) | Crítica | Fonte de verdade do fluxo de migração |
| `runners/script_runner.py` | Execução de scripts via subprocess com streaming | Código de infraestrutura | Média | Mecanismo de execução |
| `scripts/validar_importacao.py` | CLI de validação de importação + `record_operation` best-effort | Código | Alta | Entry point testável fora da UI |
| `scripts/migrar_ictiofauna.py`, `migrar_bentos.py`, `migrar_fitoplancton.py`, `migrar_zooplancton.py`, `migrar_avifauna.py`, `migrar_herpetofauna.py`, `migrar_mastofauna.py`, `migrar_meio_fisico.py` | Migração por grupo biológico (limpeza cirúrgica, upsert, agregação) | Código | Crítica | Base de comparação Etapa 4 |
| `scripts/cadastrar_especies.py`, `cadastrar_parametros.py` | Migração da Base Mestre | Código | Alta | Pré-requisito de dados |
| `scripts/processar_dados.py` | Consolidação (UNION+JOIN) para `biota_analise_consolidada` | Código | Crítica | Regra de consolidação |
| `migrations/001_empreendimentos.sql`, `002_*.sql` (fauna terrestre) | Schema (índices parciais, colunas novas) | Código/schema | Alta | Estrutura e integridade dos dados |

### 1.2 Opyta_Data_Analysis — Central de Controle e documentação

| Arquivo/local | Assunto | Tipo de conhecimento | Relevância | Aplicação possível |
|---|---|---|---|---|
| `docs/control_center/README.md` | Entrada da Central de Controle; gates A/B/C/R; fluxo oficial | Regra explícita de processo | Alta | Framework de gates do Manual |
| `docs/control_center/WORKFLOW.md` | Fluxo detalhado por etapa (validação→espécies→migração→consolidação), auditoria de coordenadas, estados operacionais | Regra explícita | Alta | Núcleo do Manual (coordenadas, Gate A/B) |
| `docs/control_center/LLM_CONTEXT_POLICY.md` | Política de contexto mínimo para IA | Regra de processo (meta) | Média | Já aplicada nesta própria auditoria |
| `docs/control_center/ACTIVE_OPERATIONS.md` | Estado dinâmico das operações | Registro operacional | Média | Exemplo de rastreabilidade |
| `docs/control_center/OPERATING_MODEL.md` | Supabase como fonte de verdade; ciclo de vida do conhecimento | Regra explícita | Alta | Princípio "Supabase = fonte de verdade" |
| `docs/control_center/NAMING_STANDARD.md` | `canonical_key` = `SIGLA__slug_supabase` | Regra explícita | Alta | Nomenclatura/escopo de projeto |
| `docs/control_center/REVIEW_WORKFLOW.md` | Tipos/impacto de revisão (R0-R3); coordenada sempre R3 | Regra explícita | Alta | Regra de revisão pós-migração |
| `docs/control_center/MEIO_FISICO_WORKFLOW.md` | Fluxo específico para dados fisicoquímicos, auditoria de delta de parâmetros/VMP | Regra explícita | Alta | Regras de Meio Físico do Manual |
| `docs/control_center/PORTFOLIO.md` | Casos aprovados reutilizáveis | Referência | Baixa | Não é validação de dados |
| `docs/control_center/PROJECTS.md` | Estado permanente de 14 projetos, pendências (GEOHER003 duplicado, BRAANG01 frequência) | Registro + regra implícita | Alta | Casos reais de integridade de dados |
| `docs/control_center/operations/*.md` (18 arquivos) | Registro por operação | Registro operacional | Variável | Consultar caso a caso |
| `docs/control_center/reviews/*.md` (28 arquivos) | Registro por revisão | Registro operacional | Variável | Consultar caso a caso |
| `docs/PADRAO_GOLD_APROVADO.md` | Padrão visual de gráficos | Padrão pós-análise | Baixa p/ migração | Fora do escopo do Manual |
| `docs/PROJECT_SCOPE_SAFETY.md` | View consolidada sem `id_projeto`; regra "falhar fechado"; fallback `codigo_interno_opyta`→`nome_empresa+nome_projeto` | Regra explícita crítica | Alta | Regra de isolamento de projeto do Manual |
| `docs/ORGANIZACAO_REPOSITORIO.md` | Onde ficam validadores/scripts/config por camada | Documentação estrutural | Alta | Onboarding |
| `docs/REGISTRO_SCRIPTS.md` | Catálogo de scripts de validação/migração/consolidação já produzidos | Registro | Alta | Insumo de scripts reutilizáveis |
| `docs/CHECKLIST_PROJETO.md` | Checklist abertura/desenvolvimento/fechamento de projeto | Regra de processo | Alta | Checklist de operacionalização |
| `docs/README.md` | Entrada geral; regra de `canonical_key` | Documentação | Média | Onboarding |
| `docs/PROTOCOLO_REVISAO_RELATORIOS.md` | Auditoria de DOCX final | Regra de processo | Média (pós-migração) | Fora do escopo direto do Manual |
| `docs/GITHUB_PUBLISH_CHECKLIST.md` | Publicação do repositório | Processo | Baixa | Fora do escopo |
| `docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md` | Decisão: backend `opyta_ops` futuro para RBAC/gates/auditoria persistente | Decisão arquitetural crítica | Alta | Direciona backlog P3/P4 |
| `docs/patterns/linguagem_tecnica_rastreavel.md` | Padrão textual pós-análise | Padrão | Baixa p/ migração | Fora do escopo |
| `docs/registry/project_registry.json` | Registro JSON de projetos (fonte de verdade formatada), duplicatas conhecidas | Registro estruturado | Alta | Validação de escopo de projeto |

### 1.3 Opyta_Data_Analysis — logs de aprendizado e casos reais

| Arquivo/local | Assunto | Tipo de conhecimento | Relevância | Aplicação possível |
|---|---|---|---|---|
| `logs/MEMORIA_APRENDIZADO_FAUNA.md` | 10 lições (CPUE, %OC, filo case-sensitive, DarwinCore, cascata, nestedness, avifauna status, mastofauna hardcode, CPUEB, lastro incompleto) | Aprendizado + regra implícita | Alta (parcialmente análise, parcialmente dado) | Separar o que é validação de dado vs análise ecológica (ver Etapa 2) |
| `logs/MEMORIA_APRENDIZADO_MEIO_FISICO.md` | 5 lições (limite de detecção, campanha legada, VMP incompleto, `FISICO_DB_URL`, chave cliente vs projeto) | Aprendizado + regra | Alta | Regras de Meio Físico do Manual |
| `logs/PROJECT_JOURNAL.md` | Cronologia de eventos (ITAGUA001 cascata, ajustes CPUE/DarwinCore, paleta Ducal, SAM Metais cross-project) | Histórico | Média-alta | Evidência de recorrência de erro |
| `logs/migracao_biota_braaeg001/*.json` | Casos reais: esforço com campos trocados, taxonomia incompleta, BMWP nulo | Registro de erro real + resolução | Crítica | Casos-fonte do Manual (R15, R16, R20) |
| `logs/validacao_biota_braaeg001/*.json` | Retries de validação Gate A, cobertura desigual de pontos por grupo | Registro de erro real | Alta | Evidência de padrão de retrabalho |
| `logs/revisao_ducgeo001_coordenadas/*.json` | Deslocamento de coordenadas por campanha (3,6-14km) vs KMZ oficial | Registro de erro real crítico | Crítica | Regra de auditoria de coordenadas |
| `logs/revisao_geoambiental_coordenadas/*.json` | Coordenadas múltiplas para 1 ponto (GEOARC001, DUCGEO001), 14 pontos com Δ>5m | Registro de erro real crítico | Crítica | Regra de 1 coordenada por ponto |
| `logs/validacao_meio_fisico/*.json` | Parâmetros sem cadastro, sinônimos, unidades divergentes, VMP conflitante, `<`/`>` não tratado | Registro de erro real | Crítica | Regras de Meio Físico do Manual |

### 1.4 Opyta_Data_Analysis — scripts ad-hoc e módulos reutilizáveis (conhecimento tácito)

| Arquivo/local | Assunto | Tipo de conhecimento | Relevância | Aplicação possível |
|---|---|---|---|---|
| `scripts/maintenance/geoher001/fix_geoher001_campaigns_supabase.py` | Normalização/deduplicação de campanha por ranking; usa data real de coleta | Código (regra tácita, não formalizada no app) | Crítica | Regra de campanha do Manual (R04-R07) |
| `scripts/maintenance/geoher001/normalize_geoher001_bentos_taxonomy.py` | Artropoda→Arthropoda; Insecta=classe; Família≠Gênero; Gênero sem "sp." solto | Código (regra tácita) | Crítica | Regra de taxonomia do Manual (R21) |
| `scripts/maintenance/geoher001/resolve_geoher001_bentos_pending_taxa.py` | Deduplicação funcional de taxa (Atopsyche vs Atopsyche sp.) | Código (regra tácita) | Alta | Regra de duplicata de espécie |
| `scripts/maintenance/geoher001/restore_geoher001_bentos_c37_feb.py` | Rollback transacional de merge acidental de campanha | Código (procedimento de recuperação) | Alta | Procedimento de emergência (não validação preventiva) |
| `scripts/maintenance/fix_geoambiental_coordinates.py` | Haversine, threshold de deriva (250m), padronização de nome de ponto | Código (regra tácita) | Crítica | Regra de coordenadas do Manual |
| `src/opyta_analysis/geo_reference.py` | Leitura de KML/KMZ oficial para conferência de coordenadas | Código reutilizável | Alta | Ferramenta de auditoria de coordenadas |
| `src/opyta_analysis/supabase_client.py` | Paginação obrigatória (limite 1000, anon key) | Código reutilizável (já formalizado) | Média | Já coberto — replicar padrão em qualquer leitura |
| `scripts/validation/audit_supabase_project_coverage.py` | Normalização de código de projeto; comparação registry×Supabase; duplicatas | Código (regra tácita) | Crítica | Regra de integridade de projeto |
| `scripts/validation/validar_migracao_ictiofauna.py` | Checklist completo pré-migração de Ictiofauna, parsing robusto de campanha (inclusive encoding corrompido) | Código (regra tácita, mais completa que o validador do app) | Crítica | Comparação direta Etapa 4 |
| `scripts/validation/validar_fauna_outputs.py` | Manifesto de entregáveis pós-run | Código | Média | Fora do escopo direto de migração de dados |
| `src/opyta_analysis/audit_utils.py` | git_context, sha256, discover_deliverables (auditoria genérica) | Código reutilizável | Alta | Base do módulo de auditoria portado ao Opyta_Data |
| `scripts/_compat.py` | Wrapper de compatibilidade para scripts movidos | Código de infraestrutura | Baixa | Não é regra de dado |
| `scripts/consolidar_bentos_avg_2026.py`, `migrar_bentos_avg_2026.py`, `inserir_meio_fisico_rest.py` | Casos de migração/consolidação com backup e tratamento de valores laboratoriais (`<0.05`, `ND`) | Código (caso real) | Alta | Evidência de padrão reutilizável |

### 1.5 Memória de usuário (persistente, fora do repositório versionado)

| Local | Assunto | Tipo de conhecimento | Relevância |
|---|---|---|---|
| `/memories/repo/arquitetura_dual_track.md` | Convenção de campanha `C{NNN}-{YYYY}-{MM}-{SC\|CH}`, migração pendente FERSAM001, segurança RLS aplicada | Regra + histórico | Alta |
| `/memories/repo/opyta_data_portabilidade.md` | Portabilidade de auditoria/lineage do Analysis para o Data (2026-06-20), pendências (migradores ainda não instrumentados) | Histórico técnico | Alta |
| `/memories/repo/git_google_drive_desktop_ini.md` | `desktop.ini` do Google Drive corrompe `.git` | Armadilha técnica de ambiente | Média (não é dado, é infra) |
| Memória pessoal (`opyta_supabase_estrutura.md`, fora do repo) | Estrutura normalizada do banco, tabelas por grupo, paginação, campanhas duplicadas `a`/`ª`, RLS ativo | Regra + estrutura de banco | Alta |

---

## ETAPA 2 — Classificação em grandes grupos

A tabela abaixo aponta, para cada grupo temático pedido, **onde mora** o
conhecimento e se ele já está formalizado em código, só em documento, ou
apenas na cabeça do usuário (tácito).

### 1. Preparação das planilhas
- Abas obrigatórias por grupo, nomes de aba de espécies inconsistentes (`Especies` vs `Cadastro_Especies`) **[E]** `Opyta_Data/validators/importacao/reader.py`, `Opyta_Data/scripts/migrar_herpetofauna.py`.
- Modelos oficiais de planilha (Bloco 6) **[E]** `Opyta_Data/core/modelos_oficiais.py`, `META_PROXIMAS_ETAPAS.txt`.
- Status: **parcialmente formalizado no código, sem versionamento (v1.0/v1.1) ainda**.

### 2. Migração
- Limpeza cirúrgica por grupo+campanha, upsert, agregação por grupo biológico **[E]** `Opyta_Data/scripts/migrar_*.py`.
- Deduplicação/merge de campanhas, rollback de merge acidental **[E, tácito]** `scripts/maintenance/geoher001/*.py` (Opyta_Data_Analysis) — **não portado ao validador do app**.
- Migração deve "falhar fechada" se Gate A/B tiver bloqueio **[E]** `docs/control_center/WORKFLOW.md`.
- Status: **código de migração robusto por grupo, mas regras de deduplicação/merge só existem como script ad-hoc fora do app**.

### 3. Validação
- Gate A/B/C/R, estados operacionais **[E]** `docs/control_center/WORKFLOW.md`, `README.md`.
- Códigos de erro/bloqueio por grupo (`MISSING_REQUIRED_COLUMNS`, `INVALID_EFFORT_REFERENCE` etc.) **[E]** `Opyta_Data/validators/*`.
- Checklist completo de pré-migração Ictiofauna (mais rigoroso que o validador do app) **[E, tácito]** `scripts/validation/validar_migracao_ictiofauna.py`.
- Status: **bem formalizado para estrutura/referência cruzada; fraco para taxonomia fina, coordenadas geoespaciais e Meio Físico**.

### 4. Estrutura e integridade dos dados
- Índices parciais para pontos com/sem empreendimento **[E]** `Opyta_Data/migrations/001_empreendimentos.sql`.
- Isolamento de projeto obrigatório (`id_projeto`) em views consolidadas **[E]** `docs/PROJECT_SCOPE_SAFETY.md`.
- Duplicidade de projeto (`GEOHER003` id=31 vs id=95) **[E]** `docs/registry/project_registry.json`, `docs/control_center/PROJECTS.md`.
- Status: **regras conhecidas e documentadas na Central de Controle, mas sem constraint/trigger no banco que impeça reincidência**.

### 5. Supabase/banco de dados
- Paginação obrigatória com anon key **[E]** `src/opyta_analysis/supabase_client.py`.
- RLS ativo, uso de service key/MCP para leitura administrativa **[E]** memória de usuário.
- Auditoria só em JSON local (`runtime/audit/`), não persistida no Supabase **[E]** `LASTRO_ATIVIDADES_2026-06-20.txt` (P1 pendente).
- Status: **infraestrutura de acesso madura; auditoria/rastreabilidade ainda não persistente em produção**.

### 6. Análises ecológicas (fora do escopo do Manual de migração/validação)
- CPUE, Shannon/Pielou, cascata hidrográfica, nestedness, DarwinCore — **explicitamente excluído da Etapa 3** por instrução do usuário, mas registrado aqui para não se perder: `logs/MEMORIA_APRENDIZADO_FAUNA.md`.

### 7. Geração de resultados (fora do escopo do Manual)
- Padrão visual Gold, redação técnica rastreável — `docs/PADRAO_GOLD_APROVADO.md`, `docs/PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md`. Não é validação de dado de entrada.

### 8. Particularidades por grupo biológico
- Ictiofauna: agrega CT/PC por média, soma indivíduos **[E]**.
- Zoobentos: campo `abundancia` (não `numero_de_individuos`), BMWP obrigatório para EPT **[E, tácito]**.
- Fitoplâncton: `densidade_cel_ml`/`biovolume_mm3_L`, filo sensível a maiúsculas **[E]**.
- Meio Físico: sinal de limite de detecção, VMP por matriz+parâmetro **[E]**.
- Mastofauna/Herpetofauna/Avifauna: `--dry-run`/`--campaign`, aba de espécies com nome diferente, mastofauna rebaixa validação de tipo_esforco **[E]**.
- Status: **cada grupo tem particularidade real e documentada, mas dispersa em 8+ scripts diferentes — sem tabela única de referência**.

### 9. Particularidades por projeto
- GEOHER001: duplicidade de campanha, taxonomia zoobentos.
- DUCGEO001/GEOARC001: coordenadas divergentes entre campanhas.
- BRAAEG001: esforço com campos trocados, taxonomia fitoplâncton incompleta, parâmetros meio físico sem equivalência.
- SAM Metais (FERSAM001): cross-project data mixing, migração de meio físico pendente.
- Status: **bem documentado em `logs/` e `docs/control_center/`, mas como "caso resolvido", não como regra generalizada no validador**.

### 10. Erros conhecidos e soluções
- Ver tabela consolidada de 20 itens no relatório de logs (fonte primária desta seção do Manual, Etapa 3).

### 11. Regras ainda não formalizadas
- Nomenclatura de campanha por regex + deduplicação por ranking.
- Normalização taxonômica (Arthropoda/Insecta/gênero).
- Threshold de deriva de coordenadas (o projeto usa **dois valores diferentes**: 5m em `revisao_geoambiental_coordenadas` e 250m em `fix_geoambiental_coordinates.py` — **inconsistência a esclarecer, não regra única** — **[I]**).
- Normalização de código de projeto (NBSP, NFKD, uppercase).
- Encoding corrompido em rótulos de campanha (`Ã‚Âª`).
- Status: **conhecimento tácito real, comprovado em script, mas nunca portado para `Opyta_Data/validators/`**.

---

## Leitura consolidada: quanto está documentado vs no código vs só na cabeça do usuário

| Camada | Onde está | Cobertura |
|---|---|---|
| Documentado (Markdown/JSON) | `docs/control_center/*`, `META_PROXIMAS_ETAPAS.txt`, `logs/*` | Alta para *processo* (gates, estados); média para *regra técnica exata* |
| Codificado no validador do app (`Opyta_Data/validators`) | Estrutura de abas, colunas, referências cruzadas, coordenadas (range simples), espécie no banco | Boa para o "esqueleto"; fraca para taxonomia fina, campanha, Meio Físico, coordenadas geoespaciais reais |
| Codificado em scripts ad-hoc (`Opyta_Data_Analysis/scripts/maintenance`) | Deduplicação de campanha, normalização taxonômica, deriva de coordenadas, normalização de código de projeto | Boa, mas **nunca chega ao validador que os colaboradores vão usar** |
| Só na cabeça do usuário / memória pessoal | Exceções de campo por projeto, decisões de VMP caso a caso, "quando aceitar espécie desconhecida" | Risco alto — é exatamente o que a Etapa 5 (backlog) precisa mitigar |

Isso confirma o diagnóstico do próprio `docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md`:
o Opyta_Data_Analysis é o "motor" com regras mais maduras; o Opyta_Data (o que
os colaboradores realmente usam) ficou para trás nesse conjunto específico de
regras teciturnas de migração.
