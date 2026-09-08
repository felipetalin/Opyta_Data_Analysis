# Diario Do Piloto - ITAGUA001 / Ictiofauna / C029

Piloto colaborativo. Operadora: Ismayllen. Dados migrados e consolidados pelo
Felipe. Escopo: somente Gate C.

Registro em `docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029.md`.

## 2026-09-08 - Sessao 1

### O que foi feito

- Leitura minima exigida pela Central de Controle: `AGENTS.md`, `README.md`,
  `WORKFLOW.md`, `ACTIVE_OPERATIONS.md`, `NAMING_STANDARD.md`,
  `operation_record_template.md` e `project_registry.json`.
- Identidade confirmada: `ITAGUA001__monitoramento_da_fauna`, `id_projeto=165`.
- Recorte da C029 conferido no Supabase por consultas somente leitura.
- Geradores mapeados em `src/opyta_analysis`.
- Registro da operacao criado e proposta do Gate C montada.
- Nenhuma escrita no banco, nenhum produto gerado, nenhum commit.

### Dificuldades

1. **A branch nao e a do briefing.** O terminal foi aberto em
   `itagua001-ictiofauna-c029`, nao em `pilot/ismayllen-itagua001-ictio-c029`.
   O `git pull` do roteiro tambem nao aparece no historico local. Nao troquei de
   branch por conta propria.
2. **Nao existe convencao de "diario do piloto".** A Central de Controle nao
   preve esse artefato. Criei este arquivo ao lado do registro da operacao,
   seguindo o padrao de nomes das operacoes. Se a convencao for outra, o
   arquivo deve ser movido.
3. **ITAGUA001 nao tem dossie nem recipe.** `docs/projects/` e
   `configs/projects/` nao possuem entrada para o projeto, embora o
   `NAMING_STANDARD.md` exija ambos. Hoje o projeto so aparece no registry como
   `reference` e no lastro em `outputs/_project_scripts/`.
4. **Divergencia no rotulo da campanha.** O briefing diz `C029-2026-07-SC`. No
   banco, Ictiofauna esta em `C029-2026-08-SC`; Avifauna e Mastofauna em
   `C029-2026-07-SC`; Herpetofauna em `29ª-jul-26-SC`. Sem um rotulo unico, o
   filtro de campanha tem que ser diferente por grupo.
5. **A C029 nao existe no repositorio.** Nenhuma pasta, config ou script
   menciona a campanha 29. A unica mencao e prospectiva, em
   `docs/FAUNA_ARQUITETURA_MULTIUSO_AUDITORIA.md`, que recomenda um
   `scripts/run_fauna_batch.py` ainda inexistente.
6. **O gerador da ictiofauna do 165 tem alvo fixo no codigo.** Em
   `src/opyta_analysis/pipelines/diagnostico/ictio_partial.py` existem
   `TARGET_PCH_NAME = "Senhora do Porto"` e `TARGET_CAMPANHA = "C028-2026-05-SC"`
   no nivel do modulo, sobrescritos por um runner externo
   (`scripts/run/fauna/run_ictio_partial_multi_empreendimentos.py`). Rodar a
   C029 exige alterar esse alvo, e nao ha parametro de campanha na assinatura do
   `run_ictio_partial_pipeline` (o `campaign_filter` do `RunParams` nao chega ate ele).
7. **O client usado na C028 nao e do projeto.** As execucoes da C028 usaram
   `client="fersam001"`, cujo `audit_project_slug` aponta para
   `FERSAM001__sam_metais_diagnostico`. O lastro so caiu na pasta certa porque o
   runner recebeu `--audit-project-slug` explicito. E fragil.
8. **Pipeline historico de estabilidade fica de fora.** `docs/PIPELINE_ICTIO_165.md`
   e `scripts/run_ictio_pipeline_165.py` foram lidos apenas para delimitar o que
   nao seria reutilizado. Esse pipeline nao usa `RunParams` nem as recipes, tem
   caminhos embutidos, e opera sobre a serie historica com corte Pre/Pos em
   2017-07-01 — incompativel com um recorte de campanha unica.

### Adaptacoes necessarias (nao executadas)

- Criar `configs/projects/itagua001_guanhaes_ictiofauna.json` no padrao das
  recipes existentes, com `campaigns: ["C029-2026-08-SC"]` e um item em `groups`
  por empreendimento (ou um item unico, se o gerador escolhido for o `ictio`).
- Criar `configs/clients/itagua001_guanhaes.json` com o `theme_override` verde
  atual e `audit_project_slug: "ITAGUA001__monitoramento_da_fauna"`.
- Criar `docs/projects/ITAGUA001_GUANHAES_FAUNA.md` declarando a `canonical_key`.
- Parametrizar a campanha no `ictio_partial` (ou passar por runner, como hoje).
- Decidir o tratamento dos blocos 6.4 e 6.5 diante dos pontos `TR*` sem captura.

### Observacoes sobre os dados (nao corrigidas)

- Recorte integro nos campos criticos: 0 linhas sem contagem, biomassa,
  coordenada ou esforco.
- Campo `origem` com vocabulario inconsistente: `Nativo`, `Nativa`,
  `Nao Nativo` e uma frase longa em `Cichla kelberi`.
- 32 pontos cadastrados na campanha, 20 com captura; os `TR*` concentram os
  pontos zerados.
- Data de coleta unica para todas as linhas: 2026-08-01.

### Proxima acao

Aguardar a aprovacao explicita do Felipe no Gate C, com resposta as sete
pendencias do registro da operacao.

## 2026-09-08 - Sessao 2 (Gate C aprovado com 10 condicoes)

Felipe aprovou o Gate C com 10 condicoes (rotulo real da campanha, pasta
contratual mantida, gerador `ictio_partial`, eliminar globais fixos do
modulo, recipe/client proprios do projeto, dossie minimo autorizado,
preservar os 32 pontos incluindo os 12 com captura zero, normalizar origem
so nos produtos, manter status `prototype`, registrar tudo no diario).
Pediu preflight de isolamento dos filtros, depois amostra de 1 empreendimento
apenas, sem gerar o pacote completo, sem alterar o Supabase e sem push.

### Mudancas de codigo

1. **`src/opyta_analysis/pipelines/diagnostico/ictio_partial.py`**
   - Removidos `TARGET_PCH_NAME`/`TARGET_CAMPANHA` (variaveis globais do
     modulo). `run_ictio_partial_pipeline` agora exige `campanha_alvo` e
     `pch_alvo` como parametros; levanta `ValueError` se ausentes.
   - Adicionadas duas validacoes de isolamento dentro do proprio pipeline:
     apos carregar os dados, confirma que so a campanha pedida esta presente,
     e apos filtrar o empreendimento, confirma que so ele esta presente.
     Levanta `RuntimeError` em caso de vazamento (nao apenas um aviso).
   - `_load_ictio_partial_df` deixou de descartar silenciosamente esforcos
     de ictiofauna sem nenhuma linha em `resultados_ictiofauna`. Esses
     esforcos agora entram como linhas de "captura zero"
     (`amostragem_zero_captura=True`), com `contagem=0`/`biomassa_g=0` e
     campos de especie nulos. Sem isso, pontos efetivamente amostrados mas
     sem captura eram tratados como se nao tivessem sido amostrados,
     distorcendo riqueza por ponto, suficiencia amostral e a base de pontos
     de 6.4/6.5 (exatamente o risco que a condicao 7 do Felipe apontava).
   - Adicionada `_normalize_origem()` para classificar o campo `origem` do
     cadastro de especies em `Nativa`/`Nao nativa`/`Nao informado`, usada
     apenas na tabela de especies (6.1) e antes de `masto._save_general_status_tables`
     (6.6-6.8). Nao toca o Supabase.
   - `_save_block_6_1`/`_save_block_6_2`/`_save_descriptive_report` passaram
     a receber `pch_alvo`/`campanha_alvo` como parametro em vez de ler os
     globais removidos.
   - Calculo de "pontos com captura" vs "pontos com captura zero" corrigido
     para usar diferenca de conjuntos (um ponto pode ter mais de um esforco,
     ex.: rede de emalhar + peneira e arrasto; conta como "com captura" se
     qualquer um dos esforcos capturou algo). A primeira versao usava uma
     contagem por linha que classificava incorretamente pontos com esforco
     misto como "zero captura" mesmo quando um dos metodos tinha capturado —
     bug encontrado e corrigido antes de gerar a amostra (ver "Dificuldades").

2. **`src/opyta_analysis/config.py`** — `RunParams` ganhou o campo `pch_target`.

3. **`src/opyta_analysis/runner.py`**
   - Dispatch de `ictio_partial` agora valida que `RunParams.campaigns` tem
     exatamente uma campanha e que `RunParams.pch_target` foi informado,
     antes de repassar para o pipeline.
   - `_generate_reproducer_script` (gera o `_run_this_analysis.py` do lastro)
     nao incluia `pch_target` no script reproduzido — corrigido, senao o
     reprodutor automatico quebraria para este pipeline.

4. **`scripts/run/run_project_recipe.py`** — grupos de uma recipe podem
   informar `pch_target` (e opcionalmente `campaigns` proprio, com fallback
   para o da recipe).

5. **`scripts/run/fauna/run_ictio_partial_multi_empreendimentos.py`**
   (script historico da C028) — adaptado para passar `campaigns`/`pch_target`
   via `RunParams` em vez de setar atributos no modulo (que deixaram de
   existir). Comportamento e client (`fersam001`) mantidos identicos ao
   uso historico; nao foi reexecutado.

### Arquivos novos

- `configs/clients/itagua001_guanhaes.json` — client/paleta proprios do
  projeto (mesma paleta verde da C028), `status` documentado como `prototype`.
- `configs/projects/itagua001_guanhaes_ictiofauna.json` — recipe com
  `status: "prototype"`, `campaigns: ["C029-2026-08-SC"]`, um grupo por
  empreendimento com `pch_target`.
- `docs/projects/ITAGUA001_GUANHAES_FAUNA.md` — dossie minimo autorizado
  pela condicao 6.
- `scripts/run/fauna/preflight_itagua001_c029_ictio.py` — preflight somente
  leitura de isolamento de filtros.
- `scripts/run/fauna/run_ictio_partial_c029_itagua001.py` — runner da C029
  que le a recipe e exige `--pch "<nome>"` ou `--all` explicito (nao roda
  nada por omissao, para nao gerar o pacote completo sem querer).
- `docs/registry/project_registry.json` atualizado: `recipes` e `docs` do
  ITAGUA001 passam a apontar para os arquivos novos; nota de aprendizado
  registrando que a recipe e `prototype`.

### Preflight (somente leitura)

`python scripts/run/fauna/preflight_itagua001_c029_ictio.py` —
`preflight_ok: true`. Testes: controle negativo com o rotulo
`C029-2026-07-SC` (retornou 0 linhas, confirmando que o pipeline nao cai
silenciosamente em outra campanha); isolamento de campanha (so
`C029-2026-08-SC` no dataset); 32/32 pontos presentes; isolamento por
empreendimento sem vazamento; sem colisao de pontos entre empreendimentos.
Pontos com captura por empreendimento: Jacaré 5/9, Senhora do Porto 5/8,
Dores de Guanhães 5/7, Fortuna II 5/8 (total 20/32).

### Amostra gerada (Senhora do Porto, 1 de 4 empreendimentos)

Rodada via `RunParams`/`runner.run` com `client="itagua001_guanhaes"`,
`campaigns=["C029-2026-08-SC"]`, `pch_target="Senhora do Porto"`, destino
local de staging (ver "Dificuldades" — pasta do Drive nao acessivel aqui).
13 produtos gerados, todos existentes em disco;
`execution_metadata.json` sem avisos. Confirmado manualmente:
`Cichla kelberi` (origem composta "exotica na bacia do rio Doce; nativa da
bacia Amazonica") passou a ser classificada como `Nao nativa` e
`Exotica=Sim` na tabela 6.6-6.8 — antes da normalizacao essa especie
escaparia da flag de exotica por conter a palavra "nativa" no texto.

### Dificuldades

1. **Bug real encontrado durante o teste da amostra, nao antes.** Com pontos
   de captura zero agora presentes, `df_quali` (linhas de tipo Qualitativa)
   deixou de ficar vazio mesmo quando nenhuma especie foi capturada
   qualitativamente. `_save_block_6_1` registrava o arquivo
   `6_1_figura_ocorrencia_qualitativa_*.png` no manifesto de auditoria sem
   o arquivo existir de fato — o proprio `execution_metadata.json` acusou
   `generated_files_missing_count: 1`. Corrigido fazendo
   `_save_abundance_figure` retornar `None` quando nao ha especie a plotar,
   e o chamador so registra o arquivo quando ele e de fato salvo. Sem essa
   correcao, o pacote final teria um manifesto mentiroso.
2. **Bug proprio (introduzido e corrigido na mesma sessao) na contagem de
   pontos com/sem captura.** A primeira versao do calculo tratava
   "com captura" e "com captura zero" como mutuamente exclusivos por linha,
   mas um ponto pode ter dois esforcos (ex.: rede de emalhar + peneira e
   arrasto). Isso fez o primeiro preflight reportar 0 pontos com captura em
   Jacaré e Senhora do Porto, quando na verdade 5 pontos em cada tinham
   captura real. Corrigido usando diferenca de conjuntos por ponto antes de
   gerar qualquer produto.
3. **A pasta contratual do Google Drive nao esta acessivel nesta maquina.**
   `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhães Energia/...`
   nao existe localmente; a arvore do Drive montada aqui so tem `Geomil` sob
   `Clientes/Clientes/Clientes`. A amostra foi gerada em
   `outputs/_staging_review/ITAGUA001_C029_ictiofauna/Senhora do Porto/`.
   Felipe precisa reexecutar em uma maquina com essa pasta sincronizada para
   os produtos ficarem no destino contratual (`29_campanha-Julho_26`).
4. **Script historico da C028 nao foi reexecutado**, apenas adaptado para
   nao quebrar com a remocao dos globais do modulo. Nao ha como confirmar
   que ele ainda reproduz os mesmos 13 arquivos sem rodar de fato (nao feito
   nesta sessao, fora do escopo pedido).
5. **Risco sistemico encontrado: a geracao da amostra apagou o lastro
   historico da C028.** `_get_project_audit_dir` (runner.py) agrupa a trilha
   de auditoria por projeto+grupo apenas (`outputs/_project_scripts/
   ITAGUA001__monitoramento_da_fauna/ictiofauna/`), sem distinguir campanha
   nem empreendimento. Ao rodar a amostra de Senhora do Porto para a C029,
   `_prune_timestamped_audit_artifacts` apagou os 8 arquivos timestampados
   (`execution_metadata.json` + `_run_this_analysis.py`) que eram o lastro
   dos 4 runs da C028 (Jacaré, Senhora do Porto, Dores de Guanhães,
   Fortuna II, 2026-05-20/26), e sobrescreveu os ponteiros "latest"
   (`execution_metadata.json`/`_run_this_analysis.py` sem timestamp) com os
   dados da C029. Isso foi percebido no `git status` logo em seguida — os 8
   arquivos apareceram como deletados (`D`) e os dois "latest" como
   modificados (`M`). Restaurados com `git checkout --
   outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/ictiofauna/`
   antes de qualquer commit, entao nada foi perdido, mas o problema e
   estrutural: qualquer nova campanha ou empreendimento do MESMO grupo do
   MESMO projeto vai continuar apagando o lastro anterior enquanto o runner
   nao distinguir campanha/empreendimento no caminho de auditoria. Nao
   corrigi isso porque afeta o comportamento do `runner.py` para todos os
   projetos, nao so o ITAGUA001/C029, e esta fora do escopo autorizado neste
   piloto. Reportando para o Felipe decidir se e quando isso deve ser
   corrigido de forma geral.

### Proxima acao

Aguardar revisao da amostra de Senhora do Porto pelo Felipe e autorizacao
explicita para gerar os 3 empreendimentos restantes — e definir onde rodar
para alcancar a pasta contratual do Google Drive.

## 2026-09-08 - Sessao 3 (correcao do risco de sobrescrita do lastro)

Felipe aprovou a configuracao da C029 mas classificou o risco de sobrescrever
o lastro da C028 como bloqueante, e pediu correcao restrita no `runner.py`
antes de gerar os 3 empreendimentos restantes. Nao gerar mais nada; nao
publicar na pasta contratual; preparar commit local sem push.

### 1. Impacto sistemico (registrado antes de qualquer alteracao)

**Causa raiz:** `_get_project_audit_dir()` em `src/opyta_analysis/runner.py`
identifica o diretorio de auditoria de uma execucao usando apenas
`(projeto, grupo)`:

```
outputs/_project_scripts/<project_slug>/<group_slug>/
```

Ela NAO inclui campanha, empreendimento (PCH) nem qualquer identificador de
execucao alem de um timestamp que so sobrevive ate a proxima rodada. Depois
que `run()` grava a metadata, `_prune_timestamped_audit_artifacts()` apaga
(`Path.unlink()`) todo arquivo timestampado dentro desse diretorio que nao
pertenca ao `run_id` da execucao atual, mantendo so 1 par
(`execution_metadata.json`/`_run_this_analysis.py` com timestamp) por
diretorio — ou seja, por `(projeto, grupo)`, nunca por campanha nem por
empreendimento.

**Quem e afetado (nao so ITAGUA001):** todo projeto/grupo que seja executado
mais de uma vez ao longo do tempo cai no mesmo diretorio e sofre poda mutua.
Isso inclui:
- ITAGUA001 (o caso que gerou o incidente): `ictio_partial` roda 1x por
  empreendimento por campanha; `avifauna`/`herpetofauna`/`mastofauna`/`primatas`
  tambem rodam 1x por empreendimento por campanha (via scripts
  `run_<grupo>_multi_empreendimentos.py`), todos sem passar campanha nem PCH
  no `RunParams` — o alvo fica em variavel global dentro de cada modulo de
  pipeline (`TARGET_PCH_NAME` em `mastofauna.py`, `avifauna.py`,
  `herpetofauna.py`, `primatas.py`; fora do escopo deste piloto, nao alterado).
- Qualquer projeto que reexecute o mesmo grupo depois de uma correcao ou
  revisao (ex.: GEOARC001, VIRITA001, BIOPOR001, DUCGEO001) tambem sofreria
  o mesmo problema se rodasse novamente o mesmo grupo — o caso do ITAGUA001
  so apareceu primeiro porque e o unico projeto com varias campanhas
  discretas do MESMO grupo já executadas separadamente (C028 e agora C029).

**Exatamente quais caminhos podem ser apagados/sobrescritos hoje (antes da
correcao):**
- Apagados (`Path.unlink()` em `_prune_timestamped_audit_artifacts`):
  `outputs/_project_scripts/<project_slug>/<group_slug>/<qualquer_timestamp_antigo>_execution_metadata.json`
  e `..._run_this_analysis.py`, exceto o par do `run_id` da execucao atual.
  Foi isso que apagou os 8 arquivos da C028 quando rodei a amostra da C029
  (restaurados via `git checkout` antes de qualquer commit).
- Sobrescritos (`open(..., "w")`, sem apagar, mas perdendo o conteudo
  anterior sem registro): `outputs/_project_scripts/<project_slug>/<group_slug>/execution_metadata.json`
  e `..._run_this_analysis.py` (os ponteiros "latest", sem timestamp) — isso
  ja acontecia mesmo antes do bug de poda, e e esperado de um ponteiro
  "ultimo estado"; o problema e que, ate agora, esse ponteiro era a UNICA
  fonte relativamente estavel por `(projeto, grupo)`, entao sobrescreve-lo
  apaga a unica evidencia legivel de qual foi a ultima execucao de OUTRA
  campanha/empreendimento sem deixar rastro.

**O que NAO e afetado:** os produtos finais (Excel/PNG/relatorio) na pasta
de saida real (`output_dir`, ex.: a pasta do Google Drive) nao sao tocados
por esse bug — só a trilha de auditoria/reproducibilidade em
`outputs/_project_scripts/` fica sujeita a poda cruzada.

**Ferramenta que depende do layout atual (limite da correcao):**
`src/opyta_analysis/fauna/audit.py::audit_project()` descobre metadados com
`project_dir.glob("*/execution_metadata.json")` — um unico nivel de
subdiretorio a partir do projeto (ou seja, exatamente
`<project_dir>/<group_slug>/execution_metadata.json`). Qualquer correcao
**precisa manter esse arquivo exatamente nesse caminho** para nao quebrar
`fauna_audit_manifest.json` de todos os projetos silenciosamente.

### 2. Correcao aplicada (restrita a `runner.py`)

Ver diff apresentado ao Felipe junto com este registro. Resumo da mudanca:

- Identidade de execucao passa a incluir projeto, grupo, campanha(s),
  empreendimento (quando disponivel) e um `run_id` (timestamp UTC) unico.
- O historico completo de cada execucao (metadata + reprodutor) passa a
  morar em um subdiretorio IMUTAVEL por execucao:
  `outputs/_project_scripts/<project_slug>/<group_slug>/runs/<identidade>/<run_id>/`,
  onde `<identidade>` = slug da(s) campanha(s) + slug do empreendimento (ou
  `sem_pch_alvo` quando o pipeline nao informa `pch_target`, caso das 4
  fauna legadas que ainda usam globais no modulo).
- Nenhum arquivo dentro de `runs/` e apagado ou sobrescrito por outra
  execucao: cada `run_id` e um diretorio novo. A antiga
  `_prune_timestamped_audit_artifacts()` (que fazia `Path.unlink()`) foi
  removida; nao ha exclusao de arquivos em lugar nenhum do fluxo.
- Os ponteiros de conveniencia `<project_dir>/<group_slug>/execution_metadata.json`
  e `..._run_this_analysis.py` continuam sendo escritos exatamente no mesmo
  caminho de sempre (sobrescritos a cada run, como sempre foram), preservando
  o contrato de `fauna/audit.py::audit_project()` para todos os projetos
  existentes sem qualquer mudanca de comportamento observavel por essa
  ferramenta.
- Nao foi usada nenhuma exclusao recursiva (`shutil.rmtree` ou equivalente)
  em nenhum ponto da correcao.

### 2.1 Resultado dos testes (executados antes de gerar novamente)

**Testes automatizados novos:** `tests/test_runner_audit_isolation.py` (5
testes, `pytest`), chamando diretamente as funcoes internas de trilha de
auditoria do runner (sem tocar o Supabase):

```
tests/test_runner_audit_isolation.py::test_c028_and_c029_coexist_without_deleting_each_other PASSED
tests/test_runner_audit_isolation.py::test_two_consecutive_c029_runs_preserve_previous_run PASSED
tests/test_runner_audit_isolation.py::test_group_dir_latest_pointer_keeps_audit_project_contract PASSED
tests/test_runner_audit_isolation.py::test_different_pch_same_campaign_do_not_collide PASSED
tests/test_runner_audit_isolation.py::test_no_recursive_delete_helpers_in_runner_module PASSED
5 passed in 2.83s
```

**Teste real (nao simulado), com o pipeline de verdade contra o Supabase
(somente leitura) e a correcao ja aplicada:**

1. Checksum MD5 de todos os 10 pares timestampados da C028
   (`20260520T*`/`20260526T*`, 20 arquivos) antes de qualquer nova execucao.
2. Rodei a amostra de Senhora do Porto (C029) DUAS VEZES consecutivas,
   apontando para a mesma pasta de staging.
3. Resultado: os dois `run_id` (`20260908T175719Z` e `20260908T175735Z`)
   geraram diretorios `runs/C029_2026_08_SC__Senhora_do_Porto/<run_id>/`
   distintos, ambos preservados.
4. Checksum MD5 dos 20 arquivos da C028 reconferido depois das duas rodadas:
   **identico, byte a byte**, ao checksum anterior. Nenhum arquivo da C028
   foi tocado.
5. `opyta_analysis.fauna.audit.audit_project()` rodado sobre
   `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/` continua
   descobrindo os 5 grupos (Avifauna, Herpetofauna, Ictiofauna, Mastofauna,
   Primatas) pelo caminho de sempre; os unicos erros reportados sao
   `output_dir_missing`/`missing_generated_files` relativos a pasta do
   Google Drive nao acessivel nesta maquina (limitacao ja conhecida, nao
   relacionada a esta correcao).

Removidos, apos os testes, 2 arquivos de teste que eu mesma tinha gerado
antes desta correcao no formato antigo (`20260908T173822Z_*`, criados durante
a Sessao 2 antes de existir `runs/`) — nao eram lastro de producao, so
resíduo do meu proprio teste anterior.

### 2.2 Push e pacote de revisao

Felipe aprovou a correcao de isolamento "para compartilhamento e revisao"
(nao para merge na main) e autorizou: push da branch, informar branch/hash,
disponibilizar os 13 produtos de Senhora do Porto em pacote de revisao sem
versionar binarios no Git, e manter registrados os resultados dos testes e
o checksum da C028 (feito na secao 2.1 acima).

- Commit local: `git commit` unico contendo a correcao do runner + toda a
  configuracao da C029 (recipe, client, dossie, scripts, teste de regressao).
  Hash: `500a297d79a63b85db8512c7e189089e24dbd3b9`.
- Push: `git push -u origin itagua001-ictiofauna-c029` — sucesso,
  `1addfb2..500a297 itagua001-ictiofauna-c029 -> itagua001-ictiofauna-c029`.
  Nenhum merge na main foi feito nem tentado.
- Pacote de revisao: os 13 produtos de "Senhora do Porto" foram compactados
  com `Compress-Archive` (PowerShell) em
  `outputs/_staging_review/_pacotes_revisao/ITAGUA001_C029_Ictiofauna_SenhoraDoPorto_revisao_20260908.zip`
  (2.156.566 bytes). Verificado com `Expand-Archive` para um diretorio
  temporario: 13 arquivos, igual ao numero gerado. O caminho esta sob
  `outputs/_staging_review/`, coberto pela regra `outputs/*` do `.gitignore`
  (confirmado com `git check-ignore -v`) — no ficou fora do Git.
- Entrega: enviado a Ismayllen via `SendUserFile` (nao ha canal direto para
  enviar arquivos a Felipe nesta sessao); ela repassa manualmente.
- Registrado como backlog de alta prioridade em
  [BACKLOG.md](../BACKLOG.md): os diretorios imutaveis de execucao
  (`runs/<identidade>/<run_id>/`) crescem indefinidamente e precisam de uma
  politica explicita de retencao/arquivamento, decidida separadamente e
  **sem** introduzir qualquer exclusao automatica no fluxo de geracao
  (`runner.py` continua sem apagar nada).

### 3. Limitacao reconhecida

Para os grupos que ainda usam `TARGET_PCH_NAME` como variavel global dentro
do proprio modulo de pipeline (avifauna, herpetofauna, mastofauna, primatas —
fora do escopo deste piloto), `RunParams.pch_target` continua vazio, entao a
identidade cai em `..._sem_pch_alvo` e os 4 empreendimentos dessas fauna
compartilham o mesmo balde de identidade dentro de `runs/`. Isso NAO causa
mais perda de dados (cada execucao ainda ganha seu proprio `run_id`
imutavel), mas o rotulo do diretorio fica menos descritivo para esses 4
grupos ate que eles tambem sejam migrados para receber `pch_target` via
`RunParams` — mudanca fora do escopo autorizado aqui.

## 2026-09-08 - Sessao 4 (caminho contratual confirmado e primeira publicacao)

A usuaria informou o caminho real da pasta contratual (um atalho de drive
compartilhado, diferente do "Meu Drive" tentado nas sessoes anteriores) e
perguntou se poderia subir os resultados. Ao inspecionar essa pasta:

- Confirmado acesso: `G:\.shortcut-targets-by-id\1dfa3mDLQkCZuEErnRrnLm1tKG19ZAIjZ\...`
  existe e esta acessivel nesta maquina — a limitacao das sessoes anteriores
  era so sobre o caminho errado ("Meu Drive"), nao sobre o Drive em si.
- Nome real da pasta da campanha: `29_campanha_Jul_26` (com underscore),
  diferente do `29_campanha-Julho_26` que eu tinha suposto por analogia com
  a C028. Corrigido na recipe e no dossie.
- `Ictiofauna\` dentro dessa pasta so continha uma subpasta vazia `Análise
  consolidada`, enquanto os outros 4 grupos da C029 (Avifauna, Mastofauna,
  Herpetofauna, Primatas) ja tinham subpastas por empreendimento com
  produtos gerados. Reportei essa divergencia e perguntei qual estrutura
  usar antes de publicar qualquer coisa.
- A usuaria confirmou o caminho e autorizou salvar nele
  ("Está autorizado salvar nesta pasta"), sem se pronunciar explicitamente
  sobre qual das duas estruturas usar.

**Decisao tomada (registrada, nao consultada com o Felipe ainda):** publiquei
Senhora do Porto espelhando o padrao ja existente nos outros 4 grupos
(subpasta por empreendimento), por ser a estrutura mais consistente com o
que ja estava la. A subpasta `Análise consolidada` continua vazia, intacta;
nao sei se era o destino pretendido para Ictiofauna. Isso precisa de
confirmacao do Felipe antes de gerar os outros 3 empreendimentos.

**Acao:**
1. Corrigi `configs/projects/itagua001_guanhaes_ictiofauna.json`
   (`output_root`) para o caminho real, com nota explicando o erro anterior.
2. Rodei `scripts/run/fauna/run_ictio_partial_c029_itagua001.py --pch
   "Senhora do Porto" --dry-run` primeiro para conferir o plano.
3. Rodei sem `--dry-run`: `[ok] Senhora do Porto -> ...\29_campanha_Jul_26\Ictiofauna\Senhora do Porto | arquivos: 13`.
4. Verifiquei os 13 arquivos na pasta real via `Get-ChildItem` (nomes e
   tamanhos conferem com a amostra revisada).
5. Conferi o `execution_metadata.json` (ponteiro "latest"): `output_dir`
   aponta para o caminho real, `warnings: []`,
   `generated_files_missing_count: 0`, `run_id=20260908T182849Z`.
6. Reconferi o checksum MD5 dos arquivos da C028 (mesmos 8 pares
   timestampados de sempre) — identico ao de antes desta publicacao. A unica
   diferenca no diff foram os 2 arquivos de teste que eu mesma tinha
   removido na Sessao 3 (residuo do formato antigo, ja tratado, nao e lastro
   real).
7. Rodar diretamente para o destino real (em vez de copiar os arquivos da
   amostra ja revisada) foi deliberado: assim o `execution_metadata.json` do
   lastro registra o `output_dir` verdadeiro, e nao um caminho de staging
   obsoleto. O conteudo gerado e deterministico e identico ao da amostra
   revisada (mesma campanha, mesmo empreendimento, mesmo codigo).

**Nao feito:** os 3 empreendimentos restantes nao foram gerados; nada foi
commitado ainda nesta sessao (arquivos gerados sao binarios/dados de cliente,
fora do Git); a pasta `Análise consolidada` nao foi tocada.

## 2026-09-08 - Sessao 5 (amostra aprovada; 3 ajustes pos-aprovacao)

A usuaria aprovou a amostra de Senhora do Porto quanto a campanha, aos
resultados e a metodologia, e pediu 3 ajustes antes de liberar os outros
empreendimentos: manifesto de rastreabilidade, reposicionamento do texto no
diagrama de Venn (sem cruzar a borda da caixa, reduzindo o espaco vazio) e
padronizacao textual (acentuacao, "Não nativa", capitalizacao de nomes
populares, UTF-8). Lista explicita do que NAO poderia mudar: rotulo/pasta da
campanha, o Jaccard dos 5 pontos com captura, os calculos/resultados
numericos, a ausencia de Shannon/Pielou/Simpson nos dados qualitativos, e
banco/consolidado/cadastro/runs anteriores.

### 1. Manifesto de rastreabilidade

Implementado em `src/opyta_analysis/runner.py`
(`_write_deliverable_manifest`), chamado ao final de `run()` para QUALQUER
pipeline (nao so ictio_partial) — escreve
`MANIFESTO_RASTREABILIDADE.json` dentro do proprio `output_dir` (a pasta do
cliente, ao lado dos produtos), nao so na trilha de auditoria interna.
Campos: projeto (`project_id`/`audit_project_slug`), grupo, campanha(s),
empreendimento, responsavel (`RunParams.operator` — novo campo opcional —
ou `git config user.name` como default via nova `audit_utils.git_user_name`),
`git` (branch/commit/dirty, reaproveitando `git_context` ja existente),
`run_id`, fonte (`Supabase` + `env_file` + `pipeline`), parametros
utilizados e a lista de produtos com SHA-256 (reaproveitando
`audit_utils.build_file_manifest`, que ja calculava sha256 para a trilha
interna — nao precisei escrever hashing novo). `RUNNER_VERSION` (constante
nova, antes hardcoded como `"1.2"` dentro da funcao de metadata) subiu para
`"1.3"`.

Testado com 3 casos novos em `tests/test_runner_audit_isolation.py`:
manifesto tem todos os campos pedidos e SHA-256 de 64 caracteres por
produto; `RunParams.operator` explicito e respeitado (nao usa git quando
informado); o manifesto de uma execucao nao e tocado por outra (mesmo
teste de nao-destrutividade aplicado ao manifesto).

### 2. Diagrama de Venn — bug real encontrado (pre-existente, nao introduzido por mim)

Ao tentar apenas mover o texto "Sem registros TR nesta campanha" para
dentro da caixa, notei que a imagem tinha uma area em branco enorme (quase
metade da altura) sem nenhuma explicacao aparente pela geometria que eu
tinha calculado. Investiguei com um script de reproducao isolado
(matplotlib puro, fora do pipeline) e descobri: `ax.set_xticks([0.0, 0.5,
1.0])`/`set_yticks(...)` eram chamados DEPOIS de `ax.set_xlim`/`set_ylim`
no codigo original. O matplotlib expande automaticamente os limites do
eixo para incluir qualquer tick definido — como os ticks ficavam em 0.0 e
1.0 (fora do intervalo de dados real, ali so para depois receber rotulos
vazios), o `ylim` pretendido (`~0.29` a `~0.89`) era silenciosamente
sobrescrito para `(0.0, 1.0)` assim que os ticks eram aplicados,
inflando a figura com espaco vazio. Confirmado empiricamente: reproduzi o
mesmo bloco de codigo em um script minimo, imprimi `ax.get_ylim()` antes e
depois, e vi o valor mudar de `(0.294, 0.89)` para `(0.0, 1.0)` exatamente
na chamada dos ticks. Esse bug ja existia no codigo ANTES da minha primeira
edicao desta sessao (mesma ordem de chamadas) — nao foi algo que eu
introduzi ao mexer no texto, so nunca tinha sido notado porque o efeito
(espaco vazio) parecia "so" uma escolha de layout, nao um bug de logica.

Corrigido invertendo a ordem: ticks + labels de tick primeiro, `set_xlim`/
`set_ylim` por ultimo (unica mudanca necessaria). Resultado visualmente
conferido (ver imagens antes/depois): espaco vazio eliminado, composicao
mais equilibrada, nota "Sem registros TR nesta campanha" agora inteiramente
dentro da caixa, sem cruzar nenhuma borda.

A caixa em si tambem foi redesenhada para ter uma unica logica de margem
(`0.028` do limite do eixo) tanto no caso com nota (2 linhas) quanto sem
nota (1 linha), fazendo o topo da caixa ficar na mesma posicao relativa nos
dois cenarios — antes a nota "extra" so existia como um `ax.text()` solto
fora da caixa.

### 3. Padronizacao textual

Apliquei acentuacao correta em TODO texto de exibicao gerado por
`ictio_partial.py` (cabecalhos de tabela, rotulos/legendas de grafico,
texto do relatorio `.txt`), com cuidado explicito para NAO tocar:
nomes de tabela/coluna do Supabase (`especies`, `tipo_amostragem`,
`esforcos_amostragem` etc. permanecem exatamente como o schema do banco),
nomes de arquivo (mantidos sem acento, como sempre foram — renomear
arquivos nao foi pedido e quebraria comparabilidade entre campanhas) e
identificadores internos usados por outras partes do codigo.

Um caso exigiu cuidado extra: a tabela de status do bloco 6.6-6.8 e gerada
por `masto._save_general_status_tables()`, uma funcao COMPARTILHADA que
Avifauna, Herpetofauna, Mastofauna e Primatas tambem usam (e cujos produtos
da C029 ja estao publicados na pasta contratual). Editar os cabecalhos
dentro de `mastofauna.py` alteraria o comportamento futuro desses outros 4
grupos — fora do escopo autorizado neste piloto (que e sobre Ictiofauna).
Em vez disso, criei `_fix_status_table_header_accents()` em
`ictio_partial.py`, que reabre o `.xlsx` logo apos `masto._save_general_status_tables()`
escreve-lo e acentua so os 4 cabecalhos problematicos ("Ameaçada",
"Endêmica", "Exótica", "Cinegética") diretamente na planilha — um
pos-processamento local, sem tocar o modulo compartilhado.

Tambem criei `_title_case_popular_name()` para padronizar a capitalizacao
do "Nome popular" (ex.: "Piau-vermelho" em vez de qualquer grafia
inconsistente do cadastro), aplicada so na tabela de exibicao, sem alterar
o cadastro no Supabase — mesmo padrao ja usado para `_normalize_origem()`.

### Verificacao antes de republicar

- Comparei valores numericos linha a linha entre a amostra ja aprovada e a
  republicada (matriz de Jaccard 5x5, tabela RP x TR, indices de
  diversidade, contagem de especies): identicos.
- Reconferido o checksum MD5 dos 20 arquivos do lastro da C028 apos as
  duas republicacoes desta sessao (uma para manifesto+acentuacao, outra
  para o ajuste final do Venn): identico nas duas vezes.
- Cada republicacao criou um novo diretorio imutavel em `runs/`
  (`20260908T192337Z`, depois `20260908T192825Z`), sem sobrescrever a
  publicacao original (`20260908T182849Z`) nem nenhuma execucao da C028.
- Rodei a suite de testes completa (5 testes anteriores + 3 novos do
  manifesto) apos as mudancas: 8/8 passando.
- Confirmei visualmente as duas imagens do Venn (antes/depois) lado a
  lado antes de aceitar a correcao como resolvida.

### Proxima acao

Aguardar revisao dos 3 ajustes pela usuaria/Felipe antes de gerar os 3
empreendimentos restantes. Preparar commit local (sem push automatico,
aguardando nova autorizacao explicita).

## 2026-09-08 - Sessao 6 (geracao dos 3 empreendimentos restantes)

A usuaria autorizou explicitamente: "Pode gerar os três que ainda faltam:
Jacaré, Dores de Guanhães, Fortuna II". Gerados com o mesmo comando/recipe
ja usado para Senhora do Porto, sem alterar campanha nem pasta contratual.

### Acao

1. Snapshot antes: checksum MD5 dos 20 arquivos do lastro da C028 e lista
   completa de arquivos em `runs/` (28 arquivos, incluindo as 5 execucoes
   ja feitas de Senhora do Porto).
2. `python scripts/run/fauna/run_ictio_partial_c029_itagua001.py --pch
   "Jacaré" --pch "Dores de Guanhães" --pch "Fortuna II" --dry-run` primeiro,
   para conferir o plano (3 `RunParams`, cada um com seu `pch_target` e
   mesmo `output_root`/`campaigns`).
3. Rodado sem `--dry-run`: os 3 completaram `[ok]`. Jacaré gerou 13
   produtos (igual a Senhora do Porto); Dores de Guanhães e Fortuna II
   geraram 14 cada (a figura extra `6_1_figura_ocorrencia_qualitativa_*`
   aparece porque esses dois empreendimentos tem pelo menos um ponto TR
   com captura real — `TRDGN2` e `TRFOR2`/`TRFOR3`, ja identificados no
   preflight desta operacao).
4. Verificado: cada um dos 3 ganhou sua PROPRIA pasta de identidade em
   `runs/` (`C029_2026_08_SC__Jacaré`, `..._Dores_de_Guanhães`,
   `..._Fortuna_II`), cada uma com um `run_id` novo e unico
   (`20260908T194249Z`, `20260908T194307Z`, `20260908T194325Z`).
5. Checksum MD5 da C028 reconferido: identico ao snapshot antes da geracao.
6. Lista de arquivos em `runs/` comparada antes/depois: nenhuma linha
   removida (as 5 execucoes anteriores de Senhora do Porto continuam
   intactas), so linhas adicionadas para os 3 novos empreendimentos.
7. `MANIFESTO_RASTREABILIDADE.json` confirmado presente nas 3 pastas reais
   do cliente (`Jacaré/`, `Dores de Guanhães/`, `Fortuna II/`).
8. `execution_metadata.json` (ponteiro "latest", reflete Fortuna II, a
   ultima execucao): `warnings: []`, `generated_files_missing_count: 0`.
9. Suite de testes completa reexecutada: 8/8 passando.

### O que NAO foi feito nesta sessao

- Nao fiz revisao numerica linha a linha dos 3 novos empreendimentos (como
  fiz para Senhora do Porto antes da aprovacao). Eles usam o MESMO codigo
  ja revisado e aprovado, mas os numeros especificos de cada um (riqueza,
  Jaccard, diversidade, especies por ponto) ainda nao foram conferidos
  individualmente. Registrado como pendencia explicita no registro da
  operacao para o Felipe conferir.
- Nao decidi sobre a subpasta `Análise consolidada` (ainda vazia, proposito
  nao confirmado).
- Nao fiz push dos commits desta e da sessao anterior (`845385e`, `27dc3fe`
  e o novo commit desta sessao) — aguardando autorizacao explicita, como
  da vez anterior.
- Nao fiz merge na main.

### Proxima acao

Aguardar o Felipe revisar os 4 empreendimentos publicados (numeros de
Jacaré/Dores de Guanhães/Fortuna II ainda nao conferidos individualmente) e
decidir sobre fechamento da operacao e a duvida da subpasta `Análise
consolidada`.
