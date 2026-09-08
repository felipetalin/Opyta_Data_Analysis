# ITAGUA001 - Ictiofauna - Campanha 29

## Controle

- projeto: `ITAGUA001__monitoramento_da_fauna`
- grupo: Ictiofauna
- operacao: Configuracao das analises da Campanha 29 (piloto colaborativo)
- estado atual: `reviewing_outputs` (4 de 4 empreendimentos gerados e publicados na pasta contratual: Senhora do Porto revisado/aprovado com 3 ajustes; Jacaré, Dores de Guanhães e Fortuna II gerados em 2026-09-08 mediante autorizacao explicita, ainda sem revisao formal)
- aberta em: 2026-09-08
- atualizada em: 2026-09-08
- operador: Ismayllen
- responsavel pelos dados: Felipe (migracao e consolidacao ja executadas)
- Gate C: aprovado por Felipe em 2026-09-08; configuracao da C029 aprovada;
  correcao de isolamento do runner aprovada para compartilhamento/revisao
- branch: `itagua001-ictiofauna-c029`
- commit enviado (push): `500a297d79a63b85db8512c7e189089e24dbd3b9`
  ("fix(runner): stop cross-campaign audit trail deletion; configure ITAGUA001 C029")
- push feito para `origin/itagua001-ictiofauna-c029` em 2026-09-08; **sem merge
  na main** (nao autorizado)
- pacote de revisao (fora do Git): `outputs/_staging_review/_pacotes_revisao/ITAGUA001_C029_Ictiofauna_SenhoraDoPorto_revisao_20260908.zip`
  (2,1 MB, 13 arquivos, enviado a Ismayllen para repasse ao Felipe)
- pasta contratual **confirmada pela usuaria** em 2026-09-08 (caminho real,
  atalho de drive compartilhado — diferente do "Meu Drive" tentado antes):
  `G:/.shortcut-targets-by-id/1dfa3mDLQkCZuEErnRrnLm1tKG19ZAIjZ/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhães Energia/Resultados e análises/29_campanha_Jul_26/Ictiofauna`
  (nome real usa `_Jul_` com underscore; o `29_campanha-Julho_26` anterior
  era suposicao errada). Recipe corrigida.
- **Senhora do Porto publicado na pasta contratual**, autorizado
  explicitamente pela usuaria em 2026-09-08: 13 arquivos, sem avisos no
  manifesto (`generated_files_missing_count: 0`), `run_id=20260908T182849Z`.
  Estrutura por subpasta de empreendimento escolhida por espelhar o padrao
  ja existente nos outros 4 grupos da mesma pasta contratual (ver "Duvida
  De Estrutura Nao Resolvida" abaixo).
- amostra de Senhora do Porto **revisada e aprovada** pela usuaria em
  2026-09-08 quanto a campanha, aos resultados e a metodologia; 3 ajustes
  pos-aprovacao pedidos (manifesto de rastreabilidade, diagrama de Venn,
  padronizacao textual) — todos aplicados e republicados na pasta
  contratual (ver "Ajustes Pos-Aprovacao Da Amostra" abaixo)
- os 3 empreendimentos restantes (Jacaré, Dores de Guanhães, Fortuna II)
  foram gerados e publicados na pasta contratual em 2026-09-08, mediante
  autorizacao explicita da usuaria ("Pode gerar os três que ainda faltam")
  (ver "Geracao Dos 3 Empreendimentos Restantes" abaixo)
- proxima acao: Felipe revisar os 4 empreendimentos publicados (Senhora do
  Porto ja aprovado; Jacaré/Dores de Guanhães/Fortuna II ainda sem revisao
  formal); confirmar se a subpasta `Análise consolidada` (vazia, ja
  existente em `Ictiofauna/`) tinha outro proposito; decidir sobre
  fechamento da operacao.

## Duvida De Estrutura Nao Resolvida

Ao inspecionar a pasta real, `Ictiofauna/` continha apenas uma subpasta
vazia `Análise consolidada`, enquanto os outros 4 grupos da C029 (Avifauna,
Mastofauna, Herpetofauna, Primatas) ja tinham subpastas por empreendimento
(`Jacaré/`, `Senhora do Porto/`, `Dores de Guanhães/`, `Fortuna II/`) com
produtos gerados. Publiquei Senhora do Porto espelhando o padrao dos outros
4 grupos (decisao mais consistente com o que ja existia), mas **nao
confirmei com o Felipe** se `Análise consolidada` era o destino pretendido
para Ictiofauna (por exemplo, um pacote unico cruzando os 4 empreendimentos,
em vez de 4 pastas separadas). A pasta `Análise consolidada` continua vazia;
nada foi movido para ou apagado dela.

## Escopo Autorizado

- Trabalhar somente na etapa 5 (configuracao das analises) e apresentar o Gate C.
- Nao validar planilhas, nao cadastrar especies, nao migrar, nao consolidar.
- Nao alterar o Supabase; apenas consultas somente leitura.
- Nao executar nem reutilizar automaticamente o pipeline historico de
  estabilidade da ictiofauna (`scripts/run_ictio_pipeline_165.py`).
- Nao gerar produtos antes da aprovacao explicita do Felipe.

## Caminhos

- dados: Supabase `public.biota_analise_consolidada` (projeto 165, grupo Ictiofauna)
- cadastro de especies: `public.especies` (nao alterado nesta operacao)
- saida proposta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhães Energia/Resultados e análises/29_campanha-Julho_26/Ictiofauna/<Empreendimento>`
- dossie: nao existe (`docs/projects/` nao tem ITAGUA001) — proposto criar
- recipe: nao existe (`configs/projects/` nao tem ITAGUA001) — proposto criar
- lastro: `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/ictiofauna`
- diario do piloto: `ITAGUA001_ICTIOFAUNA_C029_DIARIO_PILOTO.md`

## Identidade

- codigo interno: `ITAGUA001`
- nome no Supabase: `Monitoramento da Fauna`
- `id_projeto`: 165
- canonical key no registry: `ITAGUA001__monitoramento_da_fauna`
- status no registry: `reference` (nao `active`)
- cliente/empreendedor: Guanhães Energia (pasta Itatiaia)
- empreendimentos: Jacaré, Senhora do Porto, Dores de Guanhães, Fortuna II

## Contexto Consultado

- `AGENTS.md`
- `docs/control_center/README.md`
- `docs/control_center/WORKFLOW.md`
- `docs/control_center/ACTIVE_OPERATIONS.md`
- `docs/control_center/NAMING_STANDARD.md`
- `docs/registry/project_registry.json`
- `docs/templates/operation_record_template.md`
- `docs/control_center/operations/GEOARC001_ICTIOFAUNA_18_CAMPANHAS.md` (referencia de forma)
- `configs/projects/geoarc001_arcelor_ictiofauna.json`, `configs/projects/virita001_itabrita_ictiofauna.json`
- `configs/clients/fersam001.json`, `configs/theme_default.json`
- `src/opyta_analysis/runner.py`, `src/opyta_analysis/pipelines/diagnostico/ictio.py`,
  `src/opyta_analysis/pipelines/diagnostico/ictio_partial.py`
- `docs/PIPELINE_ICTIO_165.md` (lido apenas para delimitar o que NAO sera reutilizado)
- `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/*/execution_metadata.json`

## Conferencia Do Recorte No Supabase (somente leitura)

Consultas em `public.biota_analise_consolidada`, `pontos_coleta`, `empreendimentos`,
`esforcos_amostragem` e `resultados_ictiofauna`. Nenhuma escrita executada.

### Nome da campanha de ictiofauna

| Grupo | Nome da campanha 29 no banco |
| --- | --- |
| Ictiofauna | `C029-2026-08-SC` |
| Avifauna | `C029-2026-07-SC` |
| Mastofauna | `C029-2026-07-SC` |
| Herpetofauna | `29ª-jul-26-SC` |

O briefing do piloto informa `C029-2026-07-SC`. Para Ictiofauna esse rotulo nao
existe no banco; o recorte real e `C029-2026-08-SC`. **Pendencia de confirmacao.**

### Totais do recorte `ITAGUA001` / Ictiofauna / `C029-2026-08-SC`

| Item | Valor |
| --- | ---: |
| Linhas consolidadas | 66 |
| Especies | 14 |
| Pontos com resultado | 20 |
| Pontos cadastrados na campanha | 32 |
| Individuos | 235 |
| Biomassa total (g) | 36.647,35 |
| Metodos de captura | 2 |
| Bacias | 1 |
| Data de coleta registrada | 2026-08-01 (unica) |
| Linhas sem contagem / biomassa / coordenada / esforco | 0 / 0 / 0 / 0 |

### Por metodo

| Metodo | Unidade de esforco | Pontos | Linhas | Individuos | Especies |
| --- | --- | ---: | ---: | ---: | ---: |
| Rede de emalhar | m²/100 | 17 | 61 | 212 | 12 |
| Peneira e arrasto | m²/100 | 5 | 5 | 23 | 2 |

### Por empreendimento (linhas de resultado)

| Empreendimento | Pontos cadastrados | Pontos com resultado | Linhas |
| --- | ---: | ---: | ---: |
| Jacaré | 9 | 5 | 20 |
| Senhora do Porto | 8 | 5 | 16 |
| Dores de Guanhães | 7 | 5 | 16 |
| Fortuna II | 8 | 5 | 14 |

Todos os pontos `TR*` (tributarios) estao sem captura, exceto `TRDGN2`,
`TRFOR2` e `TRFOR3`, com 1 linha cada.

### Composicao (14 taxons)

Astyanax lacustris (64), Hypostomus affinis (50), Geophagus brasiliensis (37),
Hypomasticus copelandii (20), Knodus moenkhausii (15), Hoplias intermedius (14),
Deuterodon taeniatus (10), Phalloceros uai (8), Hoplias malabaricus (6),
Rhamdia quelen (4), Cichla kelberi (3), Oreochromis niloticus (2),
Hypomasticus thayeri (1), Delturus carinotus (1).

Nao nativas presentes: `Cichla kelberi` e `Oreochromis niloticus`.

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Briefing do piloto; identidade confirmada no registry e no Supabase (`id_projeto=165`). |
| Validacao | fora do escopo | Executada pelo Felipe antes do piloto. |
| Gate A - dados | fora do escopo | Registrado pelo Felipe. |
| Cadastro de especies | fora do escopo | Executado pelo Felipe. |
| Auditoria de atributos | fora do escopo | Executada pelo Felipe. |
| Gate B - especies | fora do escopo | Registrado pelo Felipe. |
| Migracao | concluida pelo Felipe | Backups `bkp_itagua001_ictio_c029_20260908t162046z_*` presentes no banco. |
| Consolidacao | concluida pelo Felipe | 66 linhas em `biota_analise_consolidada` para o recorte. |
| Configuracao das analises | concluida | Template, paleta, pasta e produtos abaixo; recipe e client criados. |
| Gate C - analises | aprovado com condicoes | Felipe aprovou em 2026-09-08 com 10 condicoes; ver secao dedicada. |
| Geracao dos produtos | concluida | 4 de 4 empreendimentos gerados e publicados na pasta contratual em 2026-09-08. |
| Revisao tecnica | parcial | Senhora do Porto revisado e aprovado (campanha, resultados, metodologia) com 3 ajustes aplicados. Jacaré, Dores de Guanhães e Fortuna II ainda sem revisao numerica individual. |
| Revisao de layout | parcial | Layout do Venn corrigido (aplica-se aos 4 empreendimentos, mesmo codigo); demais produtos ainda nao revisados individualmente para os 3 novos. |
| Fechamento | pendente | Depende da revisao dos 3 empreendimentos restantes e da decisao sobre `Análise consolidada`. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `out_of_scope` | Conduzido pelo Felipe fora deste piloto. |
| B - especies | `out_of_scope` | Conduzido pelo Felipe fora deste piloto. |
| C - analises | `approved_with_conditions` | Felipe aprovou em 2026-09-08 com 10 condicoes (ver "Condicoes Do Gate C" abaixo). |

## Condicoes Do Gate C (Felipe, 2026-09-08)

1. Usar exclusivamente `C029-2026-08-SC` (rotulo real do banco para Ictiofauna) — **atendida**.
2. Manter `29_campanha-Julho_26` como pasta contratual e registrar no manifesto que a coleta ocorreu em 2026-08-01 — **atendida** (nota na recipe e no dossie; pendente confirmar no manifesto quando a pasta real do Google Drive estiver acessivel, ver "Limitacao De Ambiente").
3. Usar `ictio_partial` e preservar os 13 produtos comparaveis a C028 — **atendida** (13 produtos gerados na amostra; um 14o produto, `6_1_figura_ocorrencia_qualitativa`, so aparece quando ha captura qualitativa real, o que nao ocorreu na C028).
4. Eliminar `TARGET_PCH_NAME`/`TARGET_CAMPANHA` fixos do modulo antes de gerar — **atendida** (globais removidos; `campanha_alvo`/`pch_alvo` agora obrigatorios).
5. Criar recipe e client proprios do ITAGUA001; proibido `client="fersam001"` ou `audit_project_slug` de outro projeto — **atendida**.
6. Autorizada a criacao de um dossie minimo do ITAGUA001 — **atendida**.
7. Preservar os 32 pontos cadastrados, inclusive os 12 com captura zero, e confirmar que representam esforco valido antes de gerar — **atendida** (confirmado no Supabase; loader corrigido para nao descartar esses pontos; ver "Correcoes Aplicadas").
8. Normalizar o vocabulario de origem apenas nos produtos, sem alterar o Supabase — **atendida**.
9. Manter status `prototype`; nao promover para `reference` antes do Gate R — **atendida** (recipe e registry marcados `prototype`).
10. Registrar no diario todas as mudancas e dificuldades — **atendida**, ver diario do piloto.

## Configuracao Das Analises (proposta do Gate C)

- numero de campanhas no recorte: 1 (`C029-2026-08-SC`)
- template proposto: **campanha unica / poucas campanhas**, o mesmo perfil usado
  na Campanha 28 e o mesmo perfil de referencia do VIRITA001. Em
  `src/opyta_analysis/pipelines/diagnostico/ictio.py` o ramo de poucas campanhas
  e acionado por `len(campaigns) <= 2` (barras agrupadas, sem small multiples
  nem paineis por ano). Nenhuma serie longa e nenhuma comparacao Pre/Pos.
- gerador proposto: `ictio_partial` (`run_ictio_partial_pipeline`), blocos
  `6.1` a `6.8`, executado uma vez por empreendimento, como na Campanha 28.
  Alternativa possivel: `ictio` (blocos 3 a 13). Ver "Decisao pendente 1".
- paleta proposta: verde FERSAM001/Guanhães ja usada na Campanha 28
  (`configs/clients/fersam001.json`: `primary_hex #11420C`,
  `secondary_hex #6A8F63`, `highlight_hex #3F5F3B`) sobre `configs/theme_default.json`.
  Proposta de melhoria: criar `configs/clients/itagua001_guanhaes.json` com o
  mesmo `theme_override` e com `audit_project_slug` correto. Ver "Decisao pendente 2".
- pasta de saida proposta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhães Energia/Resultados e análises/29_campanha-Julho_26/Ictiofauna/<Empreendimento>`
  espelhando `28_campanha-Abril_26/Ictiofauna/<Empreendimento>`.
- produtos esperados (por empreendimento, padrao da Campanha 28):
  1. `6_1_tabela_especies_<emp>.xlsx`
  2. `6_1_figura_abundancia_cpue_n_<emp>.png`
  3. `6_2_tabela_estimadores_<emp>.xlsx`
  4. `6_2_curva_coletor_dados_<emp>.xlsx`
  5. `6_2_curva_coletor_<emp>.png`
  6. `6_3_indices_diversidade.xlsx`
  7. `6_3_indices_diversidade.png`
  8. `6_4_matriz_similaridade_jaccard_por_pontos.xlsx`
  9. `6_4_dendrograma_jaccard_por_pontos.png`
  10. `6_5_tabela_jaccard_rp_vs_tr.xlsx`
  11. `6_5_diagrama_venn_rp_vs_tr.png`
  12. `6_6_6_8_tabela_geral_status.xlsx`
  13. `6_relatorio_descritivo_ictio_parcial.txt`
- lastro automatico: `execution_metadata.json` + `_run_this_analysis.py` em
  `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/ictiofauna`
  (gerado pelo `runner.py`, com manifesto de arquivos e contexto git).

## Correcoes Aplicadas Antes Da Geracao

- **Isolamento de filtros:** `run_ictio_partial_pipeline` agora exige
  `campanha_alvo` e `pch_alvo` explicitos (`ValueError` se ausentes) e valida
  internamente que o dataframe carregado contem apenas a campanha e o
  empreendimento pedidos, abortando com `RuntimeError` em caso de vazamento.
  Testado no preflight (ver abaixo) com controle negativo usando o rotulo
  divergente do briefing (`C029-2026-07-SC`), que corretamente retorna 0 linhas
  para Ictiofauna.
- **Pontos com captura zero:** o loader (`_load_ictio_partial_df`) deixou de
  descartar esforcos sem nenhuma linha em `resultados_ictiofauna`. Esses
  esforcos agora entram como unidades amostrais de captura zero
  (`amostragem_zero_captura=True`), afetando corretamente riqueza por ponto,
  suficiencia amostral (6.2, `n_unidades_amostrais`) e a base de pontos usada
  em 6.4/6.5. Confirmado no Supabase (somente leitura) que os 32 pontos
  cadastrados na campanha, incluindo os 12 sem captura, tem `esforco_amostragem`
  valido (100 ou 120, metodo e tipo de amostragem preenchidos).
- **Bug encontrado e corrigido durante o teste da amostra:** com pontos de
  captura zero agora presentes, `df_quali` deixou de ficar vazio mesmo sem
  nenhuma especie real, e `_save_block_6_1` registrava
  `6_1_figura_ocorrencia_qualitativa_*.png` no manifesto sem o arquivo
  existir de fato (`generated_files_missing_count: 1` no
  `execution_metadata.json`). Corrigido: `_save_abundance_figure` agora
  retorna `None` quando nao ha especie a plotar, e o chamador so registra o
  arquivo no manifesto quando ele e realmente salvo.
- **Vocabulario de origem:** `_normalize_origem` classifica em
  `Nativa`/`Nao nativa`/`Nao informado` a partir do texto do Supabase, sem
  alterar o banco. Aplicado na tabela de especies (6.1) e antes da chamada a
  `masto._save_general_status_tables` (6.6-6.8). Confirmado na amostra:
  `Cichla kelberi` (frase composta "exotica na bacia do rio Doce; nativa da
  bacia Amazonica") passou a ser corretamente classificada como `Nao nativa`
  e marcada `Exotica=Sim`, o que antes nao ocorria.
- **Client/recipe proprios:** criados `configs/clients/itagua001_guanhaes.json`
  e `configs/projects/itagua001_guanhaes_ictiofauna.json` (status `prototype`).
  `RunParams` ganhou o campo `pch_target`; `runner.py` valida que `ictio_partial`
  recebe exatamente uma campanha e um `pch_target`, e o script reprodutor
  gerado automaticamente (`_run_this_analysis.py`) foi corrigido para incluir
  `pch_target` (nao incluia antes desta mudanca).

## Preflight (Somente Leitura)

Script: `scripts/run/fauna/preflight_itagua001_c029_ictio.py`.
Resultado: `preflight_ok: true` para os 4 empreendimentos —
isolamento de campanha e de empreendimento sem vazamento, controle negativo
do rotulo divergente sem dados, 32/32 pontos presentes, sem colisao de pontos
entre empreendimentos. Pontos com captura por empreendimento: Jacaré 5/9,
Senhora do Porto 5/8, Dores de Guanhães 5/7, Fortuna II 5/8 (total 20/32,
confere com a consulta inicial ao Supabase).

## Amostra Gerada Para Revisao

- empreendimento: Senhora do Porto (1 de 4; os outros 3 nao foram gerados)
- destino: `outputs/_staging_review/ITAGUA001_C029_ictiofauna/Senhora do Porto/`
  (pasta local de staging, **nao** a pasta contratual — ver "Limitacao De Ambiente")
- 13 produtos gerados, todos existentes em disco;
  `execution_metadata.json` sem avisos (`warnings: []`, `generated_files_missing_count: 0`)
- lastro: `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/ictiofauna/`

## Ajustes Pos-Aprovacao Da Amostra (2026-09-08)

A usuaria aprovou a amostra de Senhora do Porto quanto a campanha, aos
resultados e a metodologia, e pediu 3 ajustes antes de liberar os outros
empreendimentos, com uma lista explicita do que NAO poderia mudar
(`C029-2026-08-SC`/pasta `29_campanha_Jul_26`, o Jaccard dos 5 pontos com
captura, os calculos/resultados numericos, a ausencia de Shannon/Pielou/
Simpson nos dados qualitativos, banco/consolidado/cadastro taxonomico/runs
anteriores).

1. **Manifesto de rastreabilidade** — `runner.py` ganhou
   `_write_deliverable_manifest()`, chamada ao final de `run()` para
   qualquer pipeline (nao so ictio_partial). Grava
   `MANIFESTO_RASTREABILIDADE.json` DENTRO do proprio pacote de entrega
   (`output_dir`, ao lado dos produtos — nao so na trilha de auditoria
   interna), com projeto, campanha, empreendimento, grupo, responsavel
   (`RunParams.operator` ou `git config user.name` como default), branch,
   commit, `run_id`, fonte/base (Supabase + pipeline), parametros
   utilizados e SHA-256 de cada produto. `RunParams` ganhou o campo
   `operator`. Versao do runner subiu para `1.3`.
2. **Diagrama de Venn (`_save_block_6_5`)**:
   - Causa raiz do espaco vazio excessivo: `ax.set_xticks([0.0, 0.5, 1.0])`/
     `set_yticks(...)` eram chamados DEPOIS de `ax.set_xlim`/`set_ylim`. O
     matplotlib expande automaticamente os limites do eixo para incluir
     qualquer tick definido, entao a chamada de ticks sobrescrevia
     silenciosamente os limites pretendidos (ylim virava `(0.0, 1.0)` em vez
     de `(0.294, 0.89)`), deixando quase metade da imagem em branco. Esse
     bug ja existia ANTES desta correcao (mesma ordem de chamadas no codigo
     original) — nao foi introduzido pela mudanca, so descoberto ao
     investigar o pedido de "reduzir espaco vazio". Corrigido invertendo a
     ordem: ticks antes de `set_xlim`/`set_ylim`.
   - A nota "Sem registros TR nesta campanha" cruzava a borda inferior da
     caixa (texto flutuando fora, quase colado no limite do eixo). Movida
     para DENTRO da caixa, como segunda linha, com margem simetrica de
     `0.028` em relacao ao limite do eixo nos dois cenarios (com/sem nota),
     e a altura/posicao da caixa passou a ser calculada para manter o topo
     da caixa na mesma posicao relativa em ambos os casos.
   - Nenhum valor foi alterado: `only_rp`, `only_tr`, `both`, `jacc` e a
     logica de calculo permanecem identicos (conferido — ver verificacao
     abaixo).
3. **Padronizacao textual** — aplicada SOMENTE em texto de exibicao
   (cabecalhos de tabela, rotulos de grafico, texto do relatorio `.txt`),
   nunca em nomes de tabela/coluna do Supabase, nomes de arquivo ou
   identificadores internos:
   - `_normalize_origem()` passou a retornar "Não nativa"/"Não informado"
     (com acento) em vez de "Nao nativa"/"Nao informado".
   - Cabecalhos da tabela de especies (`_build_species_list_ictio`):
     "Espécie", "Família", "Migratório".
   - Nova funcao `_title_case_popular_name()` padroniza a capitalizacao do
     "Nome popular" apenas para exibicao (ex.: "Piau-vermelho",
     "Lambari-do-rabo-amarelo"), sem alterar o cadastro no Supabase.
   - Relatorio descritivo (`.txt`) reescrito com acentuacao correta
     ("Relatório", "espécies", "suficiência", "Índices", "abundância" etc.).
   - Tabela de status (bloco 6.6-6.8): como essa tabela e gerada por
     `masto._save_general_status_tables` (funcao COMPARTILHADA com
     Avifauna/Herpetofauna/Mastofauna/Primatas), os cabecalhos nao foram
     corrigidos ali para nao alterar o comportamento dessas outras 4 fauna.
     Em vez disso, `_fix_status_table_header_accents()` (nova, local a
     `ictio_partial.py`) reabre o `.xlsx` recem-gerado e acentua apenas os
     cabecalhos ("Ameaçada", "Endêmica", "Exótica", "Cinegética") como
     pos-processamento restrito a este produto.
   - Garantido UTF-8 explicito em toda escrita de texto (ja era o padrao do
     arquivo antes desta mudanca).

### Verificacao Antes De Republicar

- Valores numericos comparados linha a linha entre a amostra anterior e a
  republicada: matriz de Jaccard (5x5), tabela RP x TR (Spp_A=9, Spp_B=0,
  Jaccard=0), indices de diversidade (Shannon 1.8784, Pielou 0.8549, Simpson
  0.8093 para Quantitativa; Shannon/Pielou/Simpson ausentes — `NaN` — para
  Qualitativa e Geral, como antes) e contagem de especies (9) — **identicos**
  antes e depois dos 3 ajustes.
- Checksum MD5 dos 20 arquivos do lastro da C028 reconferido apos as duas
  republicacoes desta sessao: identico.
- Cada republicacao gerou um novo diretorio imutavel em `runs/` (nunca
  sobrescreveu execucoes anteriores da propria C029): `20260908T182849Z`
  (primeira publicacao), `20260908T192337Z` (manifesto + acentuacao),
  `20260908T192825Z` (ajuste final do Venn).
- `execution_metadata.json` da execucao final: `warnings: []`,
  `generated_files_missing_count: 0`.
- 5 testes de regressao existentes + 3 novos testes para o manifesto
  (`tests/test_runner_audit_isolation.py`) — todos passando (8/8).
- Campanha `C029-2026-08-SC` e pasta `29_campanha_Jul_26` **nao foram
  alteradas**.

## Geracao Dos 3 Empreendimentos Restantes (2026-09-08)

Autorizado pela usuaria apos a revisao/aprovacao de Senhora do Porto e a
aplicacao dos 3 ajustes pos-aprovacao. Gerados com o mesmo comando/recipe
(`configs/projects/itagua001_guanhaes_ictiofauna.json`), campanha
`C029-2026-08-SC` e pasta `29_campanha_Jul_26` inalteradas:

```
python scripts/run/fauna/run_ictio_partial_c029_itagua001.py --pch "Jacaré" --pch "Dores de Guanhães" --pch "Fortuna II"
```

| Empreendimento | Produtos + manifesto | `run_id` |
| --- | --- | --- |
| Jacaré | 13 produtos + `MANIFESTO_RASTREABILIDADE.json` (14 arquivos) | `20260908T194249Z` |
| Dores de Guanhães | 14 produtos + manifesto (15 arquivos) | `20260908T194307Z` |
| Fortuna II | 14 produtos + manifesto (15 arquivos) | `20260908T194325Z` |

Jacaré tem 13 produtos (como Senhora do Porto) porque nao houve captura
qualitativa (TR) real; Dores de Guanhães e Fortuna II tem 14 porque cada um
teve ao menos um ponto TR com captura real (confirmado no preflight desta
operacao: `TRDGN2` e `TRFOR2`/`TRFOR3`), gerando tambem a figura
`6_1_figura_ocorrencia_qualitativa_*`.

**Verificacoes antes e depois da geracao:**

- Checksum MD5 dos 20 arquivos do lastro da C028: identico antes e depois.
- Nenhum arquivo das 5 execucoes anteriores de Senhora do Porto (`runs/
  C029_2026_08_SC__Senhora_do_Porto/`) foi removido ou alterado — cada
  empreendimento novo criou sua PRÓPRIA pasta de identidade em `runs/`
  (`C029_2026_08_SC__Jacaré`, `..._Dores_de_Guanhães`, `..._Fortuna_II`),
  cada uma com um unico `run_id` novo.
- `execution_metadata.json` (ponteiro "latest", reflete a ultima execucao —
  Fortuna II): `warnings: []`, `generated_files_missing_count: 0`.
- `MANIFESTO_RASTREABILIDADE.json` confirmado presente dentro de cada uma
  das 3 pastas reais (`Jacaré/`, `Dores de Guanhães/`, `Fortuna II/`).
- Suite de testes completa (8 testes) reexecutada apos a geracao: 8/8
  passando.
- Nenhuma revisao numerica/textual detalhada foi feita ainda para estes 3
  empreendimentos (diferente de Senhora do Porto, que foi revisado
  linha a linha antes desta geracao); eles usam o MESMO codigo ja revisado
  e aprovado para Senhora do Porto (mesmos blocos, mesma normalizacao de
  origem, mesmo layout de Venn corrigido, mesma acentuacao), mas os
  NUMEROS especificos de cada empreendimento ainda nao foram conferidos
  individualmente pelo Felipe.

## Limitacao De Ambiente (Resolvida)

O caminho `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhães
Energia/...` nao estava acessivel nesta maquina/sessao. A usuaria identificou
o caminho real como um atalho de drive compartilhado
(`G:/.shortcut-targets-by-id/1dfa3mDLQkCZuEErnRrnLm1tKG19ZAIjZ/...`), que
**esta** acessivel aqui. A recipe foi corrigida para esse caminho e Senhora
do Porto ja foi publicado nele (ver "Configuracao Das Analises" acima). Nao
ha mais limitacao de ambiente conhecida para publicar os empreendimentos
restantes desta maquina.

## Risco Sistemico Encontrado E Corrigido (Runner)

Gerar a amostra apagou temporariamente o lastro historico da C028: o
runner (`_get_project_audit_dir`) agrupava a trilha de auditoria so por
projeto+grupo, sem distinguir campanha/empreendimento, e
`_prune_timestamped_audit_artifacts` mantinha apenas o par mais recente. Os
8 arquivos timestampados da C028 foram restaurados com `git checkout` antes
de qualquer commit (nada foi perdido).

Felipe classificou o risco como bloqueante e pediu correcao restrita antes de
gerar novamente. Aplicada em `src/opyta_analysis/runner.py`:

- identidade de execucao agora inclui projeto, grupo, campanha(s),
  empreendimento (quando disponivel) e `run_id`;
- cada execucao grava em um diretorio IMUTAVEL:
  `outputs/_project_scripts/<projeto>/<grupo>/runs/<campanha>__<empreendimento>/<run_id>/`;
  nada e apagado (`_prune_timestamped_audit_artifacts` foi removida, sem
  substituicao por outra forma de exclusao);
  nenhuma exclusao recursiva foi usada em nenhum ponto;
- os ponteiros de conveniencia `<grupo>/execution_metadata.json` e
  `..._run_this_analysis.py` continuam no MESMO caminho de sempre, porque
  `opyta_analysis.fauna.audit.audit_project()` os descobre com um glob de
  profundidade fixa (`<projeto>/*/execution_metadata.json`); mudar esse
  caminho quebraria silenciosamente o audit manifest de todos os projetos.

**Testado** (detalhe completo no diario, sessao 3): 5 testes automatizados
novos em `tests/test_runner_audit_isolation.py` (coexistencia C028/C029,
duas execucoes consecutivas da C029, contrato do ponteiro "latest",
dois empreendimentos da mesma campanha, ausencia de exclusao recursiva no
modulo) — todos passando; e um teste real (nao simulado) rodando a amostra
da C029 duas vezes consecutivas contra o Supabase, com checksum MD5 dos 20
arquivos da C028 identico antes e depois, e `audit_project()` continuando a
descobrir os 5 grupos do projeto pelo caminho de sempre.

## Pendencias

1. Blocos 6.4 e 6.5 ficam descritivos quando os pontos `TR*` tem pouca ou
   nenhuma captura nesta campanha; tratado como limitacao documentada no
   relatorio descritivo e no dossie, nao como erro. Confirmar com Felipe se
   isso e aceitavel para o pacote final.
2. Jacaré, Dores de Guanhães e Fortuna II foram gerados e publicados em
   2026-09-08 mediante autorizacao explicita da usuaria. **Ainda nao
   passaram por revisao numerica individual** (diferente de Senhora do
   Porto, que foi conferido linha a linha). Recomendado que o Felipe
   confira os 3 antes do fechamento da operacao.
3. Confirmar com o Felipe o proposito da subpasta vazia `Análise
   consolidada` em `Ictiofauna/` (ver "Duvida De Estrutura Nao Resolvida").
4. Correcao do runner aplicada, testada, commitada (`500a297`) e enviada
   (push) para `origin/itagua001-ictiofauna-c029` em 2026-09-08. Merge na
   main **nao autorizado**. Commits subsequentes (`845385e`, `27dc3fe`)
   ainda nao enviados (push) — aguardando nova autorizacao explicita.
5. Politica de retencao/arquivamento dos diretorios imutaveis de execucao
   registrada como backlog de alta prioridade
   ([BACKLOG.md](../BACKLOG.md)) — nao implementada, sem exclusao automatica
   introduzida.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: pendente
- manifesto: pendente
- patterns: pendente
- portfolio: pendente
- backlog: pendente
