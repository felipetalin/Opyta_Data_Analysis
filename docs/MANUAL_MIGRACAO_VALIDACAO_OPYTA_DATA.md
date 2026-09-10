Status: draft — auditoria de conhecimento, não altera código
Ultima atualizacao: 2026-08-17

Este documento cobre as ETAPAS 3, 4 e 5 do pedido de auditoria: o Manual de
Migração e Validação, a comparação regra-a-regra com o código atual do
Opyta_Data, e o backlog priorizado. O inventário (Etapa 1) e a classificação
(Etapa 2) estão em
[docs/AUDITORIA_CONHECIMENTO_MIGRACAO_VALIDACAO.md](AUDITORIA_CONHECIMENTO_MIGRACAO_VALIDACAO.md).

Convenção de proveniência: **[E]** regra comprovadamente existente (cito
arquivo) · **[I]** regra inferida do código/casos, sem declaração explícita ·
**[R]** recomendação nova desta auditoria.

Objetivo declarado pelo usuário — repetido aqui para não se perder no meio do
documento: **um colaborador precisa conseguir pegar uma planilha bruta, subir,
entender sozinho o erro, corrigir e migrar com segurança**, sem depender do
dono do processo. Nenhuma regra abaixo assume conhecimento tácito do usuário.

---

# ETAPA 3 — Manual de Migração e Validação do Opyta Data

## A. Estrutura da planilha (preparação)

### R01 — Abas obrigatórias por grupo biológico
- **Regra:** cada planilha de importação deve conter `Capa_Projeto`,
  `Pontos_e_Campanhas`, `Metadados_Esforco` (exceto Meio Físico) e
  `Resultados_<Grupo>`.
- **Etapa:** upload / leitura estrutural.
- **Por que existe:** sem essas abas o pipeline não consegue montar
  projeto→ponto→esforço→resultado.
- **Como validar:** conferir nomes de aba exatos (case-sensitive) contra
  `REQUIRED_SHEETS_BY_GROUP`.
- **Caracteriza erro quando:** aba ausente, vazia, ou nome diferente do
  esperado.
- **Bloqueante:** sim (`MISSING_SHEETS`, `EMPTY_CAPA/PONTOS/RESULTADOS`).
- **Exemplo incorreto:** aba chamada `Resultados Ictio` (espaço, sem underline).
- **Exemplo correto:** `Resultados_Ictiofauna`.
- **Mensagem ao usuário (já existe):** *"Aba obrigatória ausente: {nome}. Abas
  disponíveis: {lista}."*
- **Orientação de correção:** baixar o modelo oficial do grupo e copiar os
  dados para dentro dele, sem renomear abas.
- **Origem/evidência [E]:** `Opyta_Data/validators/importacao/reader.py`.
- **Exceções:** Meio Físico não usa `Metadados_Esforco` **[E]**
  `docs/control_center/MEIO_FISICO_WORKFLOW.md`.

### R02 — Nome da aba de cadastro de espécies é inconsistente entre grupos
- **Regra:** a aba de cadastro de espécies embutida na planilha de importação
  deve ter um nome único e previsível.
- **Etapa:** upload.
- **Por que existe:** hoje Ictiofauna espera `Especies`, Herpetofauna espera
  `Cadastro_Especies`, e há aliases (`Cadastro_Ictiofauna`) em scripts
  paralelos — isso é fonte de erro silencioso (usuário usa o nome errado e a
  aba simplesmente não é lida).
- **Como validar:** aceitar todos os aliases conhecidos e avisar qual foi
  usado.
- **Caracteriza erro quando:** usuário usa nome de aba que não está na lista
  de aliases do grupo específico.
- **Bloqueante:** hoje é bloqueante por omissão (aba não encontrada vira
  `MISSING_SHEETS`), mas a causa raiz (inconsistência de nome esperado por
  grupo) não é comunicada.
- **Exemplo incorreto:** usar `Especies` em uma planilha de Herpetofauna.
- **Exemplo correto:** usar `Cadastro_Especies` em Herpetofauna, `Especies` em
  Ictiofauna (por ora).
- **Mensagem sugerida:** *"Este grupo espera a aba '{nome_esperado}' para
  cadastro de espécies. Encontramos '{nome_usado}', que não é reconhecida
  para este grupo."*
- **Orientação de correção:** renomear a aba conforme o modelo oficial do
  grupo; melhor ainda, padronizar um único nome em todos os modelos (ver
  backlog P1).
- **Origem/evidência [E, tácito]:** `Opyta_Data/scripts/migrar_herpetofauna.py`
  vs `migrar_ictiofauna.py`; citado como risco em
  `PLANO_MELHORIAS_STREAMLIT.md` ("alinhar colunas... verificar exatidão").
- **Exceções:** nenhuma — é justamente a falta de padrão que é o problema.

### R03 — Cadastro mestre de espécies deve ter as 16 colunas completas
- **Regra:** `Nome_Cientifico, Grupo_Biologico, Reino, Filo, Classe, Ordem,
  Familia, Genero, Status_Ameaca_Nacional, Status_Ameaca_Global, Origem,
  Habito_Alimentar, Estrategia_Reprodutiva, Valor_Economico, Cinegetica,
  Xerimbabo` não podem ter célula vazia.
- **Etapa:** Base Mestre (antes de qualquer importação de resultados).
- **Por que existe:** cadastro incompleto propaga "buraco" para toda análise
  futura que dependa de taxonomia/atributo de conservação.
- **Como validar:** checagem célula a célula das 16 colunas.
- **Caracteriza erro quando:** qualquer uma vazia/nula.
- **Bloqueante:** sim (`MISSING_REQUIRED_VALUE`).
- **Exemplo incorreto:** linha com `Origem` vazio.
- **Exemplo correto:** `Origem = "Nativa"`.
- **Mensagem (já existe):** *"Coluna '{col}' sem valor na linha {linha}."*
- **Orientação de correção:** preencher a célula; se o valor é
  desconhecido, usar marcador explícito combinado com a equipe (`N/I`), nunca
  deixar vazio.
- **Origem/evidência [E]:** `Opyta_Data/validators/especies/rules.py`.
- **Exceções:** nenhuma exceção de grupo para esta regra estrutural (as
  exceções são só para *formato do nome*, ver R05).

## B. Campanhas

### R04 — Nomenclatura padrão de campanha
- **Regra:** toda campanha deve seguir `C{NNN}-{YYYY}-{MM}-{SC|CH}` (ex.:
  `C028-2026-04-SC`).
- **Etapa:** preparação da planilha / migração.
- **Por que existe:** rótulos livres como `28a-abr-26-SC` e `28ª-abr-26-SC`
  geram duas campanhas diferentes no banco para o mesmo evento de campo,
  porque `a` (ASCII) e `ª` (ordinal Unicode) não são a mesma string.
- **Como validar:** regex `^C\d{3}-\d{4}-\d{2}-(SC|CH)$`; se não bater, tentar
  normalizar a partir do rótulo livre + data real de coleta.
- **Caracteriza erro quando:** campanha fora do padrão E sem correspondência
  seguro com uma campanha já existente.
- **Bloqueante:** deveria ser alerta bloqueante só quando há ambiguidade real
  (duas campanhas candidatas); caso contrário, normalizar automaticamente e
  avisar (info).
- **Exemplo incorreto:** `10ª-Mai-23`, `10a-mai-23` (duas grafias do mesmo
  evento).
- **Exemplo correto:** `C010-2023-05-SC`.
- **Mensagem sugerida:** *"A campanha '{rotulo}' não segue o padrão
  C{{NNN}}-{{AAAA}}-{{MM}}-{{SC|CH}}. Convertemos automaticamente para
  '{padrao}'. Confirme se está correto antes de migrar."*
- **Orientação de correção:** usar o padrão desde a criação da planilha;
  se a campanha já existe no banco com nome diferente, usar exatamente o
  mesmo nome já cadastrado (consultar antes de criar).
- **Origem/evidência [E]:** `Opyta_Data/core/campanha.py` (função existe, mas
  **[I] não está plugada nos migradores** — ver Etapa 4);
  `scripts/maintenance/geoher001/fix_geoher001_campaigns_supabase.py` (lógica
  mais completa, nunca portada);
  `/memories/repo/arquitetura_dual_track.md` (motivação original).
- **Exceções:** dados legados de Meio Físico ainda usam `mes-ano`; o parser
  precisa aceitar os dois formatos **[E]**
  `logs/MEMORIA_APRENDIZADO_MEIO_FISICO.md`.

### R05 — Consistência do código operacional C### entre abas
- **Regra:** o código `C###` extraído do rótulo de campanha deve ser igual em
  `Pontos_e_Campanhas`, `Metadados_Esforco` e `Resultados_*`.
- **Etapa:** validação.
- **Por que existe:** se as abas usam rótulos diferentes para a "mesma"
  campanha (por erro de digitação ou cópia), o join campanha↔ponto↔resultado
  quebra silenciosamente.
- **Como validar:** comparar conjuntos de `C###` entre as três abas.
- **Caracteriza erro quando:** há `C###` em uma aba que não existe em
  `Pontos_e_Campanhas`.
- **Bloqueante:** sim (`CAMPAIGN_CODE_MISMATCH`, `CAMPAIGN_LABEL_NOT_IN_POINTS`).
- **Exemplo incorreto:** `Pontos_e_Campanhas` tem `C008-2013-08`, mas
  `Resultados_Ictiofauna` tem `C008-2013-09`.
- **Exemplo correto:** mesmo texto exato nas duas abas.
- **Mensagem (já existe):** *"{aba}: campanhas C### divergentes de
  Pontos_e_Campanhas. Extras: {extra}; ausentes: {faltando}."*
- **Orientação de correção:** copiar o rótulo exato de `Pontos_e_Campanhas`
  para as demais abas (não redigitar).
- **Origem/evidência [E]:** `Opyta_Data/validators/importacao/checkers.py`
  (`check_campaign_consistency`).
- **Exceções:** nenhuma.

### R06 — Data real da coleta deve prevalecer sobre a data do rótulo
- **Regra:** ao gerar/normalizar o nome canônico de uma campanha, usar
  `MIN(data_hora_coleta)` real dos pontos, não o mês/ano escrito no rótulo
  original.
- **Etapa:** migração / normalização.
- **Por que existe:** o rótulo de campo às vezes é preenchido errado (mês
  digitado errado), mas a data de coleta real dos registros é mais confiável.
- **Como validar:** comparar mês/ano do rótulo vs mês/ano de
  `data_hora_coleta`; se divergirem, sinalizar para decisão humana (não
  sobrescrever silenciosamente).
- **Caracteriza erro quando:** divergência entre rótulo e dado real sem
  explicação registrada.
- **Bloqueante:** alerta (exige decisão humana, não é auto-corrigível com
  segurança).
- **Exemplo incorreto:** rótulo diz "Maio/2023", mas todas as coletas têm
  `data_hora_coleta` em Abril/2023.
- **Exemplo correto:** rótulo e data real de coleta no mesmo mês/ano.
- **Mensagem sugerida:** *"A campanha '{rotulo}' tem data de coleta real em
  {mes_real}, mas o rótulo indica {mes_rotulo}. Confirme qual data está
  correta antes de migrar."*
- **Orientação de correção:** confirmar com quem fez campo qual data é
  verdadeira; corrigir o rótulo, não o dado de coleta (a menos que o erro
  esteja na digitação da data).
- **Origem/evidência [E, tácito]:**
  `scripts/maintenance/geoher001/fix_geoher001_campaigns_supabase.py`
  (`standard_name(name, data_min)`).
- **Exceções:** nenhuma conhecida.

### R07 — Deduplicação de campanhas equivalentes
- **Regra:** quando duas linhas de campanha no banco representam o mesmo
  evento de campo (variação de grafia), escolher uma como "principal" por
  critério objetivo e mesclar/apagar a outra.
- **Etapa:** migração (correção pós-fato) / idealmente prevenção na validação.
- **Por que existe:** campanhas duplicadas inflam contagem de esforço e
  fragmentam resultados do mesmo evento em dois registros.
- **Como validar:** agrupar campanhas por código canônico `C###`; se houver
  mais de uma linha física para o mesmo código, é duplicata.
- **Caracteriza erro quando:** `COUNT(DISTINCT id_campanha)` para um mesmo
  `C###` normalizado é maior que 1.
- **Bloqueante:** sim — migrar sobre campanha duplicada é uma decisão de alto
  risco (R3 conforme `REVIEW_WORKFLOW.md`); deve travar até decisão humana.
- **Exemplo incorreto:** banco com `id_campanha=36 ("28a-abr-26-SC")` e
  `id_campanha=41 ("28ª-abr-26-SC")` para o mesmo evento.
- **Exemplo correto:** uma única linha `C028-2026-04-SC`.
- **Mensagem sugerida:** *"Encontramos {n} campanhas equivalentes a
  '{codigo}' no banco: {lista}. Não migramos automaticamente — escolha qual
  deve ser mantida."*
- **Orientação de correção:** usar o critério de desempate documentado
  (maior `result_count` > maior diversidade de grupos > rótulo sem ordinal >
  menor id) e então mesclar esforços/resultados preservando dados, com
  backup prévio.
- **Origem/evidência [E, tácito]:**
  `fix_geoher001_campaigns_supabase.py::choose_keeper`,
  `merge_effort`, `merge_result_table` (não portados ao app).
- **Exceções:** casos de merge acidental exigem rollback específico (ver
  `restore_geoher001_bentos_c37_feb.py`) — procedimento de emergência, não
  regra preventiva.

## C. Pontos e coordenadas

### R08 — Coordenadas devem estar em faixa geográfica válida
- **Regra:** latitude ∈ [-90, 90], longitude ∈ [-180, 180], aceitando vírgula
  como separador decimal.
- **Etapa:** validação estrutural.
- **Por que existe:** valores fora da faixa indicam erro de digitação ou
  coluna trocada (lat↔lon).
- **Como validar:** parse numérico + checagem de intervalo.
- **Caracteriza erro quando:** valor fora do intervalo ou não numérico.
- **Bloqueante:** hoje é **apenas aviso** (`INVALID_COORDINATES`, warning) —
  ver discrepância na Etapa 4, pois coordenada errada não deveria nunca ser
  aviso.
- **Exemplo incorreto:** latitude `-243,50` (típico de lat/lon trocadas ou
  grau/minuto/segundo não convertido).
- **Exemplo correto:** `-20,1632590877`.
- **Mensagem (já existe):** *"Coordenadas inválidas nas linhas: {linhas}.
  Latitude deve estar em [-90,90] e longitude em [-180,180]."*
- **Orientação de correção:** verificar se as colunas lat/lon foram trocadas;
  confirmar formato decimal (não GMS) e datum (WGS84).
- **Origem/evidência [E]:** `Opyta_Data/validators/importacao/checkers.py`
  (`check_pontos`).
- **Exceções:** nenhuma.

### R09 — Coordenada de ponto já existente no banco não pode divergir sem revisão
- **Regra:** se (campanha, ponto) já existe no banco, a nova coordenada deve
  ser igual à já cadastrada (tolerância ε=1e-6°).
- **Etapa:** validação (com engine/banco).
- **Por que existe:** evita sobrescrever um ponto histórico com coordenada
  errada digitada na nova planilha.
- **Como validar:** comparar contra `pontos_coleta` existente por
  (`campanha`, `nome_ponto`).
- **Caracteriza erro quando:** mesma dupla (campanha, ponto) com coordenada
  diferente da já registrada.
- **Bloqueante:** sim (`POINT_COORDINATE_DIVERGENCE`).
- **Exemplo incorreto:** ponto `MICT1` já tem `(-20.16,-43.41)`, nova planilha
  traz `(-20.20,-43.35)` para o mesmo nome+campanha.
- **Exemplo correto:** coordenada idêntica, ou nome de ponto novo com sufixo
  (`MICT1-C02-01`) se for de fato um ponto diferente.
- **Mensagem (já existe):** *"{n} ponto(s) com mesmo nome/campanha já existem
  no banco com coordenadas diferentes. Crie novo nome de ponto (ex.: sufixo
  -CXX-01) ou ajuste a planilha."*
- **Orientação de correção:** confirmar com quem fez campo qual coordenada é
  a correta; nunca sobrescrever silenciosamente um ponto histórico.
- **Origem/evidência [E]:** `checkers.py::check_pontos_conflitantes_no_banco`.
- **Exceções:** nenhuma.

### R10 — Auditoria de coordenadas contra referência espacial oficial (KMZ/KML)
- **Regra:** antes de aprovar Gate A, toda coordenada deve ser comparada com
  arquivo de referência oficial do cliente (KMZ/KML/shapefile), quando
  existir; divergência acima de um limiar deve ser sinalizada.
- **Etapa:** validação / Gate A.
- **Por que existe:** já ocorreram deslocamentos reais de **3,6 a 14 km** em
  campanhas de DUCGEO001 e variações >5m em 14 pontos de GEOARC001/DUCGEO001 —
  suficiente para invalidar mapas, análises espaciais e Darwin Core.
- **Como validar:** distância Haversine entre coordenada da planilha e
  coordenada de referência por `nome_ponto` (não por posição sequencial).
- **Caracteriza erro quando:** distância acima do limiar aceito para o
  projeto.
- **Bloqueante:** sim quando há referência oficial disponível; se não houver
  referência, a ausência deve ser **registrada como ressalva aprovada**, não
  silenciada.
- **Exemplo incorreto:** ponto associado por *ordem da linha* na planilha em
  vez de por nome, causando troca de coordenadas entre pontos.
- **Exemplo correto:** join estrito por `nome_ponto` normalizado.
- **Mensagem sugerida:** *"O ponto '{ponto}' está a {distancia} do local
  oficial registrado no KMZ do cliente. Confirme antes de migrar — divergências
  de coordenada afetam mapas e banco de forma difícil de reverter depois
  (classificação R3)."*
- **Orientação de correção:** substituir pela coordenada do KMZ oficial
  quando ela existir e for a fonte de verdade acordada; documentar a
  estratégia escolhida (`referencia_kmz` / `primeira_coordenada_valida` /
  `coordenada_por_campanha` / `sem_referencia_externa_aprovada`).
- **Origem/evidência [E]:** `docs/control_center/WORKFLOW.md` (auditoria de
  coordenadas obrigatória em Gate A);
  `logs/revisao_ducgeo001_coordenadas/*.json`;
  `logs/revisao_geoambiental_coordenadas/*.json`;
  `scripts/maintenance/fix_geoambiental_coordinates.py` (Haversine,
  threshold 250m).
- **Exceções/particularidade a resolver:** o repositório usa **dois limiares
  diferentes** (5m no caso DUCGEO/GEOARC, 250m no script de manutenção
  genérico) sem explicação documentada de por que diferem — **[I]** precisa
  de decisão explícita de qual limiar vale por padrão e quais projetos têm
  exceção.

### R11 — Toda referência (campanha, ponto) em resultados deve existir em Pontos_e_Campanhas
- **Regra:** cada linha de `Resultados_*` deve corresponder a um par
  (campanha, ponto) cadastrado em `Pontos_e_Campanhas`.
- **Etapa:** validação.
- **Por que existe:** resultado "órfão" não pode ser georreferenciado nem
  associado a esforço.
- **Como validar:** chave normalizada (campanha, ponto) contra o conjunto de
  `Pontos_e_Campanhas`.
- **Caracteriza erro quando:** par ausente.
- **Bloqueante:** sim (`INVALID_POINT_REFERENCE`).
- **Exemplo incorreto:** resultado cita ponto `MICT12`, mas
  `Pontos_e_Campanhas` só vai até `MICT11`.
- **Exemplo correto:** todo ponto citado em resultados está listado antes.
- **Mensagem (já existe):** *"{n} registro(s) de resultados referenciam
  campanha+ponto ausente em Pontos_e_Campanhas."*
- **Orientação de correção:** adicionar a linha faltante em
  `Pontos_e_Campanhas` ou corrigir o nome do ponto no resultado (erro de
  digitação é a causa mais comum).
- **Origem/evidência [E]:** `checkers.py::check_referencias_cruzadas`.
- **Exceções:** nenhuma.

## D. Esforço amostral

### R12 — Metadados_Esforco obrigatório e esforço deve corresponder a cada resultado
- **Regra:** todo resultado precisa de um esforço correspondente pela chave
  composta (campanha, ponto, método de captura, tipo de amostragem).
- **Etapa:** validação.
- **Por que existe:** sem esforço, o resultado não pode ser normalizado
  (CPUE, densidade, etc. dependem do esforço empregado).
- **Como validar:** join estrito pela chave composta.
- **Caracteriza erro quando:** resultado sem esforço correspondente.
- **Bloqueante:** sim (`INVALID_EFFORT_REFERENCE`, `EMPTY_EFFORT_SHEET`).
- **Exemplo incorreto:** resultado com `tipo_de_amostragem="Ativa"`, mas
  `Metadados_Esforco` só tem `tipo_de_amostragem="Passiva"` para aquele
  ponto/campanha.
- **Exemplo correto:** chave composta idêntica nas duas abas.
- **Mensagem (já existe):** *"Grupo '{grupo}': {n} registro(s) de resultados
  sem esforço válido nos metadados (campanha+ponto+método+tipo)."*
- **Orientação de correção:** conferir se o método de captura e o tipo de
  amostragem foram digitados de forma idêntica nas duas abas (inclusive
  maiúsculas/acentos).
- **Origem/evidência [E]:** `checkers.py::check_resultados_vs_esforco`.
- **Exceções:** Mastofauna rebaixa esta checagem quando filtrando por
  `--campaign`, porque sua chave operacional real é campanha+ponto+método
  (não tipo_amostragem) **[E]** `migrar_mastofauna.py::rebaixar_validacao_tipo_esforco_mastofauna`.

### R13 — Colunas de esforço não podem estar trocadas
- **Regra:** `Tipo_de_Amostragem` (categoria, ex. "Quantitativa") e
  `Unidade_Esforco` (unidade, ex. "m²/100") não podem ter seus valores
  invertidos entre si.
- **Etapa:** validação.
- **Por que existe:** já ocorreu de verdade em BRAAEG001 — 52 esforços de
  Ictiofauna com as duas colunas trocadas, bloqueando Gate A.
- **Como validar:** checar se o valor de `Tipo_de_Amostragem` "parece" uma
  unidade (contém `/`, número, símbolo) e vice-versa.
- **Caracteriza erro quando:** padrão de conteúdo incompatível com o nome da
  coluna.
- **Bloqueante:** sim, deveria ser (hoje **não existe checagem específica**
  no validador do app — ver Etapa 4).
- **Exemplo incorreto:** `Tipo_de_Amostragem = "m²/100"`,
  `Unidade_Esforco = "Quantitativa"`.
- **Exemplo correto:** `Tipo_de_Amostragem = "Quantitativa"`,
  `Unidade_Esforco = "m²/100"`.
- **Mensagem sugerida:** *"A coluna 'Tipo_de_Amostragem' contém um valor que
  parece uma unidade de medida ('{valor}'). Verifique se as colunas
  Tipo_de_Amostragem e Unidade_Esforco não foram trocadas."*
- **Orientação de correção:** inverter os valores das duas colunas na
  planilha de origem.
- **Origem/evidência [E]:**
  `logs/migracao_biota_braaeg001/20260703T111200_validacao_nova_base_biota_aquatica_braaeg001.json`
  (códigos `EFFORT_INVALID_SAMPLE_TYPE`,
  `EFFORT_UNIT_LOOKS_LIKE_SAMPLE_TYPE` — nomenclatura já existe em algum
  validador auxiliar do Analysis, mas **não no Opyta_Data**).
- **Exceções:** nenhuma conhecida.

## E. Espécies e taxonomia

### R14 — Toda espécie usada em resultados deve estar no cadastro mestre ou na planilha atual
- **Regra:** espécie citada em `Resultados_*` precisa existir em
  `public.especies` OU estar na aba `Especies`/`Cadastro_Especies` da mesma
  planilha (cadastro aditivo).
- **Etapa:** validação.
- **Por que existe:** é o gate que impede resultado "órfão" de taxonomia —
  mas o aprendizado operacional documentado é que **bloquear toda espécie
  desconhecida sem essa exceção trava o fluxo desnecessariamente**.
- **Como validar:** LEFT JOIN resultados × (banco ∪ cadastro da planilha).
- **Caracteriza erro quando:** espécie não está em nenhuma das duas fontes.
- **Bloqueante:** modo estrito = bloqueia; modo padrão (lenient) = informa e
  segue (cadastro futuro).
- **Exemplo incorreto:** `Eunotia meridiana` citada em resultados, ausente do
  banco e ausente da aba de cadastro da planilha.
- **Exemplo correto:** mesma espécie presente na aba `Cadastro_Especies` da
  planilha atual, mesmo sendo nova no projeto.
- **Mensagem (já existe, modo lenient):** *"Serão cadastradas automaticamente
  ou necessitarão revisão."* — **fraca**, não diz *quais* espécies (ver
  Etapa 4/backlog).
- **Orientação de correção:** adicionar a espécie à aba de cadastro com os
  16 campos completos, ou confirmar que é erro de digitação do nome
  científico.
- **Origem/evidência [E]:** `checkers.py::check_especies_no_banco`;
  regra explícita em `META_PROXIMAS_ETAPAS.txt` ("bloquear espécies
  desconhecidas SALVO quando presentes na aba Especies da mesma planilha").
- **Exceções:** Zooplâncton e Zoobentos aceitam nomes de nível taxonômico
  superior (não espécie completa) **[E]** `validators/especies/rules.py`.

### R15 — BMWP_Score obrigatório e correto para famílias/ordens sensíveis (Zoobentos)
- **Regra:** táxons de Ephemeroptera, Plecoptera e Trichoptera (EPT) devem
  ter `bmwp_score` preenchido; se supra-específico (nível família), buscar
  score tabelado em literatura, nunca deixar nulo.
- **Etapa:** validação de espécies / Gate B.
- **Por que existe:** BMWP nulo em táxon EPT já causou índice de qualidade de
  água subestimado em análises reais (caso `Oligoneuriidae`).
- **Como validar:** para toda espécie/família com `ordem` ∈
  {Ephemeroptera, Plecoptera, Trichoptera}, exigir `bmwp_score` não nulo.
- **Caracteriza erro quando:** EPT com `bmwp_score IS NULL`.
- **Bloqueante:** deveria ser bloqueante (hoje só existe checagem genérica de
  "é numérico se preenchido" — ver Etapa 4).
- **Exemplo incorreto:** `Oligoneuriidae` com `bmwp_score = NULL`.
- **Exemplo correto:** `Oligoneuriidae` com `bmwp_score = 10`.
- **Mensagem sugerida:** *"'{taxon}' é um táxon de Ephemeroptera/Plecoptera/
  Trichoptera sem BMWP_Score cadastrado. Este score é usado para cálculo de
  qualidade de água — pesquise o valor em literatura BMWP antes de
  prosseguir."*
- **Orientação de correção:** consultar literatura BMWP oficial (protocolo
  já usado: BMWP-ASPT adaptado) e preencher o score antes de aprovar Gate B.
- **Origem/evidência [E]:**
  `logs/migracao_biota_braaeg001/20260727T134522_bmwp_oligoneuriidae_zoobentos_braaeg001.json`.
- **Exceções:** nenhuma — regra "tolerância zero" já foi proposta pela
  própria auditoria de logs do repositório.

### R16 — Normalização taxonômica hierárquica (Filo/Classe/Ordem/Gênero)
- **Regra:** (a) grafia de filo deve ser padronizada (`Arthropoda`, não
  `Artropoda`); (b) `Insecta` é sempre `classe`, nunca `ordem` — as ordens
  (Coleoptera, Diptera, Ephemeroptera, Hemiptera, Lepidoptera, Megaloptera,
  Odonata, Plecoptera, Trichoptera) ficam no campo `ordem`; (c) `familia`
  nunca pode ser igual a `genero`; (d) `genero` não deve carregar sufixo
  `sp.` (isso é atributo do nome científico, não do gênero).
- **Etapa:** validação de espécies / cadastro mestre.
- **Por que existe:** essas quatro inconsistências já ocorreram de verdade em
  42 táxons de Zoobentos de um único projeto (GEOHER001) e distorcem
  qualquer agregação por nível taxonômico.
- **Como validar:** comparar `filo` contra lista canônica; comparar `classe`
  contra lista de ordens de inseto; comparar `familia` normalizado com
  `genero` normalizado; regex de sufixo `sp\.?$` em `genero`.
- **Caracteriza erro quando:** qualquer uma das quatro condições acima falha.
- **Bloqueante:** deveria ser alerta bloqueante em Gate B (hoje **não existe
  no validador do app** — ver Etapa 4).
- **Exemplo incorreto:** `filo="Artropoda"`, `classe="Coleoptera"`,
  `ordem="Insecta"`; `familia="Staphylinidae", genero="Staphylinidae"`;
  `genero="Atopsyche sp."`.
- **Exemplo correto:** `filo="Arthropoda"`, `classe="Insecta"`,
  `ordem="Coleoptera"`; `familia="Staphylinidae", genero=NULL` (se não
  identificado); `genero="Atopsyche"`.
- **Mensagem sugerida:** *"'{genero}' aparece como gênero mas é igual à
  família cadastrada — provavelmente não há identificação em nível de
  gênero. Deixe o campo Gênero vazio nesse caso, em vez de repetir a
  família."*
- **Orientação de correção:** aplicar as quatro normalizações antes de
  cadastrar; se em dúvida, usar apenas os níveis taxonômicos efetivamente
  identificados e deixar os demais em branco (não repetir o nível anterior).
- **Origem/evidência [E, tácito]:**
  `scripts/maintenance/geoher001/normalize_geoher001_bentos_taxonomy.py`.
- **Exceções:** Zoobentos aceita identificação em qualquer nível taxonômico
  (não precisa chegar a espécie) — mas os níveis preenchidos precisam
  respeitar a hierarquia correta.

### R17 — Duplicata de espécie por variação de escrita
- **Regra:** duas entradas que representam o mesmo táxon com grafia
  diferente (ex. `Atopsyche` vs `Atopsyche sp.`) devem ser reconciliadas em
  uma única espécie antes ou durante a migração.
- **Etapa:** validação de espécies.
- **Por que existe:** duplicata de espécie fragmenta contagem de abundância
  e riqueza da mesma unidade taxonômica real.
- **Como validar:** comparar chave normalizada (remover `sp.`, `cf.`, `aff.`,
  case-insensitive) contra outras entradas já cadastradas.
- **Caracteriza erro quando:** duas linhas normalizam para a mesma chave mas
  têm registros de resultado associados a `id_especie` diferentes.
- **Bloqueante:** hoje é aviso (`INTRA_SHEET_DUPLICATE`) só para duplicata
  *dentro da mesma planilha*; duplicata *contra o banco* não é checada da
  mesma forma (ver Etapa 4).
- **Exemplo incorreto:** `Atopsyche` (id=101) e `Atopsyche sp.` (id=205) como
  espécies separadas no banco.
- **Exemplo correto:** uma única espécie canônica, com os resultados
  migrados para o mesmo `id_especie`.
- **Mensagem sugerida:** *"'{nome_a}' e '{nome_b}' parecem ser o mesmo táxon
  com grafia diferente. Confirme se devem ser consolidados em um único
  registro antes de migrar."*
- **Orientação de correção:** escolher a grafia canônica (geralmente a mais
  completa) e mover todos os resultados para ela.
- **Origem/evidência [E, tácito]:**
  `scripts/maintenance/geoher001/resolve_geoher001_bentos_pending_taxa.py`.
- **Exceções:** nenhuma.

## F. Meio Físico / parâmetros analíticos

### R18 — Parâmetro deve estar no cadastro master (matriz + parâmetro) ou virar cadastro aditivo revisado
- **Regra:** toda combinação (matriz, parâmetro) de `Resultados_Meio_Fisico`
  deve casar com `parametros_analise`; se não casar, classificar como
  `synonym_review`, `unit_review`, `vmp_review` ou `new_parameter` e revisar
  antes de migrar.
- **Etapa:** validação / Gate B específico de Meio Físico.
- **Por que existe:** laboratórios diferentes nomeiam o mesmo parâmetro de
  forma diferente (`Sulfato` vs `Sulfatos`, `DQO` vs `Demanda Química de
  Oxigênio`) e usam unidades distintas (`mg/L` vs `µg/L`) — já geraram 45
  problemas de Gate B em um único projeto (BRAAEG001).
- **Como validar:** comparação exata + fuzzy contra o cadastro master,
  reportando as 5 categorias acima.
- **Caracteriza erro quando:** parâmetro sem cadastro master E sem decisão
  registrada.
- **Bloqueante:** sim — geração de conformidade/IQA fica bloqueada até
  resolução do cadastro **[E]** `docs/control_center/MEIO_FISICO_WORKFLOW.md`.
- **Exemplo incorreto:** planilha traz `"Sulfato"`, master só tem
  `"Sulfatos"` cadastrado — sistema hoje trataria como parâmetro novo em vez
  de reconhecer sinônimo.
- **Exemplo correto:** nome do parâmetro na planilha bate exatamente com o
  master, ou existe decisão registrada de mapeamento.
- **Mensagem sugerida:** *"O parâmetro '{param}' ({matriz}) não foi
  encontrado no cadastro master. Pode ser sinônimo de '{sugestao}' já
  cadastrado, ou um parâmetro realmente novo. Confirme antes de migrar."*
- **Orientação de correção:** decidir explicitamente entre aceitar como
  sinônimo, cadastrar como novo (com ou sem VMP) ou corrigir a unidade;
  nunca deixar a decisão implícita.
- **Origem/evidência [E]:**
  `logs/validacao_meio_fisico/20260702T184353Z_auditoria_parametros_braaeg001.json`,
  `20260702T185714Z_gate_b_problemas_parametros_braaeg001.json`.
- **Exceções:** parâmetros cadastrados no master mas não usados na planilha
  atual são apenas informativos, não erro **[E]** mesmo relatório (caso SAM
  Metais, 24 parâmetros).

### R19 — Sinal de limite de detecção deve ser extraído antes de qualquer cálculo
- **Regra:** valores como `"<0,05"` ou `">1600"` devem ser separados em
  `sinal_limite` (`<`/`>`) e `valor_medido` (numérico) antes de qualquer
  agregação, e nunca tratados como texto opaco ou descartados.
- **Etapa:** migração.
- **Por que existe:** 1.104 valores com `<` foram encontrados em um único
  projeto (SAM Metais); se não tratados, cálculos como percentual de
  violação e IQA ficam incorretos ou quebram.
- **Como validar:** regex `r"([<>])?\s*([0-9.,]+)"` aplicado a todo campo
  `Resultado` antes de conversão para `float`.
- **Caracteriza erro quando:** campo `Resultado` não casa com o padrão
  numérico (com ou sem sinal) — indica erro de digitação (texto livre,
  "ND" não padronizado, etc.).
- **Bloqueante:** deveria ser bloqueante quando o parse falha (hoje o
  comportamento em falha não está claramente coberto por um código de erro
  dedicado no validador do app — ver Etapa 4).
- **Exemplo incorreto:** `Resultado = "não detectado"` (texto livre sem
  padrão).
- **Exemplo correto:** `Resultado = "<0,0500"` ou `Resultado = "ND"` (se
  "ND" for convenção acordada e documentada).
- **Mensagem sugerida:** *"O valor '{valor}' na linha {linha} não pôde ser
  interpretado como resultado numérico (com ou sem sinal de limite de
  detecção). Use o formato '<0,05', '>100' ou o valor numérico puro."*
- **Orientação de correção:** padronizar a planilha de laboratório para usar
  apenas os sinais `<`/`>` ou o marcador acordado, nunca texto livre.
- **Origem/evidência [E]:** `scripts/migrar_meio_fisico.py::extrair_sinal_e_valor`;
  `/memories/repo/arquitetura_dual_track.md` ("sinal_limite='<' → usar
  val/2"); `logs/MEMORIA_APRENDIZADO_MEIO_FISICO.md`.
- **Exceções:** regra de substituição por `valor/2` é usada só em **análise**
  posterior, não na migração — a migração deve preservar sinal + valor bruto
  separadamente **[I]**, não decidir a substituição.

## G. Integridade de dados / migração / escopo de projeto

### R20 — Migração deve falhar fechada se validação tiver bloqueios
- **Regra:** nenhum script de migração deve rodar (fora de `--dry-run`) se o
  relatório de validação tiver qualquer item bloqueante pendente.
- **Etapa:** transição validação→migração.
- **Por que existe:** é o gate central de segurança de todo o fluxo — sem
  ele, qualquer um dos outros 19 problemas documentados chega ao banco.
- **Como validar:** checar `report.can_proceed is True` antes de habilitar o
  botão/comando de migração.
- **Caracteriza erro quando:** migração é executada com `can_proceed=False`.
- **Bloqueante:** sim, por definição.
- **Exemplo incorreto:** usuário roda `python migrar_ictiofauna.py
  arquivo.xlsx` diretamente por linha de comando, ignorando o relatório de
  validação da UI.
- **Exemplo correto:** migração só é disparada pelo botão da UI, que já
  checou `can_proceed`.
- **Mensagem (já existe na UI):** botão de migração não aparece / fica
  desabilitado quando há bloqueio.
- **Orientação de correção:** corrigir todos os itens listados como bloqueio
  no relatório e reenviar a planilha.
- **Origem/evidência [E]:** `docs/control_center/WORKFLOW.md` ("Migracao
  deve falhar fechada se a validacao ou auditoria taxonomica tiver
  bloqueios"); `app/pages/01_Importacao.py` (UI já implementa isso para o
  fluxo normal).
- **Exceções:** scripts de migração podem ser chamados diretamente via CLI
  (fora da UI) para casos avançados — **isso contorna o gate** e é um risco
  real (ver backlog P0).

### R21 — Isolamento de projeto obrigatório em qualquer leitura/consolidação
- **Regra:** nenhuma consulta ou pipeline pode filtrar apenas por
  `grupo_biologico`; deve sempre isolar por `id_projeto` (ou fallback
  `codigo_interno_opyta` / `nome_empresa`+`nome_projeto`, com validação final
  de unicidade).
- **Etapa:** migração / consolidação / qualquer leitura da view consolidada.
- **Por que existe:** já ocorreu mistura real de dados entre projetos porque
  `biota_analise_consolidada` não expõe `id_projeto` de forma confiável em
  todos os pontos de acesso.
- **Como validar:** todo pipeline que lê a consolidada deve declarar
  explicitamente o filtro de escopo e validar que o resultado pertence a um
  único projeto antes de prosseguir.
- **Caracteriza erro quando:** pipeline retorna registros de mais de um
  projeto quando deveria retornar de um só.
- **Bloqueante:** sim — deve **falhar fechado** (interromper e pedir
  cadastro do escopo) em vez de retornar dado sem filtro.
- **Exemplo incorreto:** filtrar só por `grupo_biologico = 'Zoobentos'` e
  assumir que o resultado é de um projeto só.
- **Exemplo correto:** filtrar por `id_projeto = 183` (ou fallback
  documentado) e validar que só um projeto aparece no resultado.
- **Mensagem sugerida:** *"Não foi possível isolar este resultado a um único
  projeto. Cadastre o project_id ou o código interno antes de continuar —
  não geramos dado sem esse filtro para evitar mistura entre clientes."*
- **Orientação de correção:** cadastrar/confirmar `id_projeto` e
  `codigo_interno_opyta` antes de qualquer consolidação ou análise.
- **Origem/evidência [E]:** `docs/PROJECT_SCOPE_SAFETY.md` (caso real
  DUCGEO001).
- **Exceções:** nenhuma — é uma regra de segurança de dados entre clientes,
  não deveria ter exceção.

### R22 — Duplicidade de cadastro de projeto (registry vs Supabase)
- **Regra:** o código interno do projeto (`codigo_interno_opyta`) deve ser
  único no Supabase; duplicatas por espaço invisível, acento ou caixa
  diferente devem ser detectadas e bloqueadas antes de qualquer nova
  migração usar o código ambíguo.
- **Etapa:** preparação / migração.
- **Por que existe:** já existe um caso real — `id_projeto=95` tem
  `codigo_interno_opyta=" GEOHER003"` (espaço não-quebrável à esquerda),
  duplicando `id_projeto=31`.
- **Como validar:** normalizar código (remover `\xa0`, NFKD, uppercase,
  remover espaços) e comparar contra todos os códigos existentes no banco.
- **Caracteriza erro quando:** dois `id_projeto` normalizam para o mesmo
  código.
- **Bloqueante:** sim para novas migrações que apontem para um código
  ambíguo; a duplicata já existente deve ser sinalizada mas não corrigida
  automaticamente sem decisão humana.
- **Exemplo incorreto:** cadastrar novo projeto com código `"GEOHER003"`
  quando já existe `" GEOHER003"` (com espaço) no banco.
- **Exemplo correto:** reaproveitar o `id_projeto` já existente, corrigido.
- **Mensagem sugerida:** *"Já existe um projeto com código equivalente a
  '{codigo}' no banco (id={id}, grafado como '{codigo_banco}'). Confirme se
  é o mesmo projeto antes de continuar."*
- **Orientação de correção:** usar sempre `docs/registry/project_registry.json`
  como fonte de verdade formatada antes de criar/usar um código de projeto.
- **Origem/evidência [E]:** `docs/registry/project_registry.json`,
  `docs/control_center/PROJECTS.md`;
  `scripts/validation/audit_supabase_project_coverage.py::normalize_code`.
- **Exceções:** nenhuma.

### R23 — Consolidação exige simulação + backup + confirmação explícita
- **Regra:** a consolidação (`biota_analise_consolidada`) deve sempre rodar
  em modo simulação primeiro, criar backup lógico automático, e só gravar de
  fato após confirmação explícita do usuário; se a simulação falhar, a
  consolidação real é bloqueada.
- **Etapa:** consolidação.
- **Por que existe:** consolidação é uma operação "definitiva" (conforme o
  próprio aviso da UI) sobre uma tabela compartilhada entre todos os
  projetos — erro aqui afeta múltiplos clientes ao mesmo tempo.
- **Como validar:** checar se existe rotina de simulação e se o backup foi
  de fato criado antes do `INSERT`/`TRUNCATE` real.
- **Caracteriza erro quando:** consolidação real roda sem backup prévio
  identificável ou sem confirmação registrada.
- **Bloqueante:** sim.
- **Exemplo incorreto:** rodar script de consolidação direto por linha de
  comando sem passar pela simulação da UI.
- **Exemplo correto:** usar o botão "Rodar Consolidação Agora" da UI, que já
  simula e cria backup antes de gravar.
- **Mensagem (já existe):** *"⚠️ A Consolidação é obrigatória para que seus
  dados fiquem disponíveis para análise. Este processo é definitivo — não há
  volta atrás."* — **poderia ser mais clara sobre o que o backup permite
  reverter** (ver backlog P2).
- **Orientação de correção:** sempre confirmar visualmente o resumo da
  simulação antes de clicar em confirmar.
- **Origem/evidência [E]:** `SEGURANCA_STATUS_2026-04-09.md`
  (`app/pages/02_Consolidacao.py`).
- **Exceções:** scripts de consolidação históricos (`consolidar_bentos_avg_2026.py`)
  já seguem este padrão fora da UI, mas com escopo restrito a
  `codigo_interno_opyta` específico — **[E]** bom padrão a generalizar.

### R24 — Limpeza pré-migração deve ser cirúrgica (grupo + campanha), nunca ampla
- **Regra:** ao reprocessar uma campanha, o script de migração deve apagar
  apenas os resultados/esforços daquele grupo biológico e daquelas campanhas
  específicas — nunca os pontos de coleta (compartilhados entre grupos) nem
  dados de outras campanhas/grupos.
- **Etapa:** migração.
- **Por que existe:** pontos de coleta são infraestrutura compartilhada
  entre Ictiofauna, Zoobentos etc. no mesmo projeto; apagar de forma ampla
  destruiria dados de outros grupos sem necessidade.
- **Como validar:** revisar a cláusula `WHERE` do `DELETE` — deve conter
  `grupo_biologico` E a lista específica de campanhas encontradas na
  planilha atual, nunca um `DELETE` sem essas duas condições.
- **Caracteriza erro quando:** um `DELETE`/`TRUNCATE` afeta linhas fora do
  grupo+campanha da planilha atual.
- **Bloqueante:** sim — é proteção estrutural do script, deve ter teste
  automatizado (ver backlog).
- **Exemplo incorreto:** `TRUNCATE biota_analise_consolidada` sem filtro (já
  citado como prática histórica de risco em
  `docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md`).
- **Exemplo correto:** `DELETE FROM resultados_zoobentos WHERE id_esforco IN
  (SELECT ... WHERE grupo_biologico='Zoobentos' AND id_campanha IN (...))`.
- **Mensagem sugerida (para log de auditoria):** *"Limpeza cirúrgica:
  removidas {n} linhas de {grupo} nas campanhas {lista}. Nenhum outro grupo
  ou campanha foi afetado."*
- **Orientação de correção:** revisar o script antes de rodar em produção se
  a proteção de escopo não estiver clara nos logs.
- **Origem/evidência [E]:** `scripts/migrar_*.py::limpar_dados_do_grupo_e_campanha`;
  **[E, risco identificado]**
  `docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md` ("Scripts
  históricos fazem TRUNCATE em biota_analise_consolidada antes de
  recarregar").
- **Exceções:** nenhuma — quando a lista de campanhas encontradas está
  vazia, o script deve pular a limpeza (proteção já existente) em vez de
  assumir "limpar tudo".

### R25 — Toda operação de validação/migração/consolidação deve gerar trilha de auditoria
- **Regra:** cada operação relevante deve registrar timestamp, usuário,
  projeto, grupo, status (ok/bloqueado/erro), métricas e contexto git.
- **Etapa:** todas.
- **Por que existe:** é o que permite a um colaborador (e ao dono do
  processo) saber depois o que foi feito, quando, e por quem — pré-requisito
  para "colaborador migra sem depender de mim".
- **Como validar:** checar se `runtime/audit/*.json` (ou tabela persistida)
  tem entrada correspondente a cada operação feita.
- **Caracteriza erro quando:** operação crítica sem entrada de auditoria
  correspondente.
- **Bloqueante:** deveria ser não-bloqueante para a operação em si (não travar
  o fluxo por falha de auditoria), mas **bloqueante para considerar a
  operação "fechada"**.
- **Exemplo incorreto:** migração rodada e nenhum registro em
  `runtime/audit/` ou `import_logs`.
- **Exemplo correto:** entrada JSON com `operation="migracao"`,
  `status="ok"`, `metrics.total_registros=450`.
- **Mensagem sugerida:** já existe via página "Qualidade & Auditoria"; falta
  alertar quando uma operação recente **não tem** log correspondente.
- **Orientação de correção:** garantir que `record_operation()` seja chamado
  em todos os pontos de entrada, inclusive scripts rodados fora da UI.
- **Origem/evidência [E]:** `core/audit/manifest.py`,
  `LASTRO_ATIVIDADES_2026-06-20.txt` (P1/P2 pendentes: persistência em
  Supabase e cobertura ponta-a-ponta).
- **Exceções:** hoje é *best-effort* (try/except) por design — aceitável,
  desde que a ausência de log vire alerta visível, não silêncio.

## H. Segurança operacional (deploy e acesso)

### R26 — Deploy exige push imediato após commit
- **Regra:** `git commit` não publica nada sozinho; todo commit relevante
  deve ser seguido imediatamente de `git push origin deploy-cloud`.
- **Etapa:** fora do fluxo de dados, mas crítico porque **qualquer correção
  de validador só vale em produção depois do push**.
- **Por que existe:** já ocorreu divergência real entre o que o editor
  mostrava e o que estava de fato publicado em `app/pages/01_Importacao.py`.
- **Como validar:** comparar `git log --oneline -3` local vs
  `origin/deploy-cloud`.
- **Caracteriza erro quando:** commit local mais recente que o remoto.
- **Bloqueante:** sim, para qualquer alteração em validador/migrador.
- **Exemplo incorreto:** commitar a correção de uma regra de validação e
  esquecer o push.
- **Exemplo correto:** commit seguido imediatamente de push, com
  confirmação via `git log origin/deploy-cloud`.
- **Mensagem/checklist (já existe):** `DEPLOYMENT_CHECKLIST.md` (7 itens).
- **Orientação de correção:** seguir o checklist de deploy antes de
  considerar qualquer melhoria de validador "em produção".
- **Origem/evidência [E]:** `NORTE.md`, `DEPLOYMENT_CHECKLIST.md`.
- **Exceções:** nenhuma.

### R27 — Paginação obrigatória em leituras via Supabase REST (anon key)
- **Regra:** toda leitura via REST com chave anônima deve paginar em blocos
  de até 1000 linhas (`Range` header), nunca assumir que uma única chamada
  traz todos os dados.
- **Etapa:** qualquer leitura de validação/comparação contra o banco.
- **Por que existe:** a API REST do Supabase com `anon_key` limita o retorno
  por padrão; sem paginação, comparações "espécie existe no banco?" podem
  dar falso negativo silencioso.
- **Como validar:** revisar se toda função de leitura usa laço de paginação
  até que `len(rows) < page_size`.
- **Caracteriza erro quando:** função de leitura para após a primeira página
  sem verificar se havia mais dados.
- **Bloqueante:** é uma regra de implementação (já corretamente aplicada no
  módulo compartilhado), não um erro de dado do usuário.
- **Exemplo incorreto:** `sb.table("especies").select("*").execute()` sem
  paginação em uma tabela com mais de 1000 linhas.
- **Exemplo correto:** uso de `paginate()` com laço de `Range`.
- **Mensagem:** não aplicável ao usuário final — é regra de engenharia.
- **Origem/evidência [E]:** `src/opyta_analysis/supabase_client.py::paginate`;
  memória de usuário (`opyta_supabase_estrutura.md`).
- **Exceções:** nenhuma.

---

# ETAPA 4 — Comparação com o validador atual do Opyta_Data

## 4.1 Classificação por regra

| # | Regra | Classificação |
|---|---|---|
| R01 | Abas obrigatórias por grupo | **Implementada corretamente** |
| R02 | Nome de aba de espécies inconsistente | **Não implementada** (comportamento existe, mas não há aviso da causa raiz nem padronização) |
| R03 | Cadastro mestre 16 colunas completas | **Implementada corretamente** |
| R04 | Nomenclatura padrão de campanha | **Implementada parcialmente** — `core/campanha.py::normalizar_nome_campanha()` existe mas **[I] não está conectada aos migradores/validador de importação** (confirmado em `/memories/repo/opyta_data_portabilidade.md`: "Utilidade pura, NÃO ligada aos migradores ainda") |
| R05 | Consistência C### entre abas | **Implementada corretamente** |
| R06 | Data real vs data do rótulo | **Não implementada** no app (existe só no script ad-hoc do Analysis) |
| R07 | Deduplicação de campanhas equivalentes | **Não implementada** no app (existe só como script ad-hoc `fix_geoher001_campaigns_supabase.py`) — **exige decisão humana**, não deveria ser 100% automática mesmo depois de portada |
| R08 | Faixa válida de coordenadas | **Implementada, mas precisa ser revisada** — hoje é `warning`, deveria bloquear |
| R09 | Coordenada divergente vs banco | **Implementada corretamente** |
| R10 | Auditoria contra KMZ/KML oficial | **Não implementada no fluxo de upload do Opyta_Data** — existe apenas como script avulso no Analysis (`fix_geoambiental_coordinates.py`, `geo_reference.py`) rodado manualmente pelo dono do processo |
| R11 | Referência (campanha, ponto) em resultados | **Implementada corretamente** |
| R12 | Esforço obrigatório por chave composta | **Implementada corretamente** |
| R13 | Colunas de esforço trocadas | **Não implementada** |
| R14 | Espécie no banco ou na planilha atual | **Implementada corretamente** (inclusive a exceção documentada) |
| R15 | BMWP obrigatório para EPT | **Não implementada** (só existe checagem genérica "é numérico se preenchido") |
| R16 | Normalização taxonômica hierárquica | **Não implementada** |
| R17 | Duplicata de espécie entre grafias (banco) | **Implementada parcialmente** — só cobre duplicata *dentro da mesma planilha*, não contra o banco |
| R18 | Parâmetro Meio Físico no master / cadastro aditivo | **Não implementada** — confirmado como gap explícito pelo próprio código (nenhuma validação de Meio Físico em `checkers.py`) |
| R19 | Sinal de limite de detecção | **Implementada no script de migração, não no validador prévio** — o parse ocorre em `migrar_meio_fisico.py`, mas não há checagem antes disso que avise o usuário sobre valor não-parseável |
| R20 | Migração falha fechada se validação bloqueada | **Implementada corretamente na UI**, mas **exige decisão humana** quanto ao uso de scripts fora da UI (CLI direta contorna o gate) |
| R21 | Isolamento de projeto obrigatório | **Não deve ser automatizada sozinha** no sentido de "resolver"; a *detecção* de ausência de escopo deveria ser implementada e hoje **não está** no Opyta_Data (só documentada como lição no Analysis) |
| R22 | Duplicidade de código de projeto | **Não implementada no fluxo de upload** — existe só como script de auditoria avulso (`audit_supabase_project_coverage.py`) no Analysis |
| R23 | Consolidação segura (simulação+backup+confirmação) | **Implementada corretamente** |
| R24 | Limpeza cirúrgica grupo+campanha | **Implementada corretamente**, mas **precisa ser revisada** — há evidência documentada de scripts *históricos* que faziam `TRUNCATE` amplo; confirmar que nenhum caminho de código atual ainda permite isso |
| R25 | Trilha de auditoria obrigatória | **Implementada parcialmente** — captura em JSON local, sem persistência em Supabase (P1 do próprio time), e sem cobertura de todos os `scripts/migrar_*.py` |
| R26 | Deploy = push imediato | **Exige decisão humana / processo, não código** — é checklist manual, risco de esquecimento permanece |
| R27 | Paginação obrigatória Supabase | **Implementada corretamente** |

## 4.2 Onde dado inadequado passa hoje pela validação (achados críticos)

1. **Coordenada fora de faixa é apenas aviso (R08).** Uma planilha com
   latitude/longitude trocadas passa a validação normalmente porque
   `INVALID_COORDINATES` é `warning`, não `block`. Isso é inconsistente com a
   gravidade real do problema (coordenada errada já causou deslocamentos de
   até 14 km em produção).
2. **Nenhuma auditoria contra KMZ/KML no fluxo do colaborador (R10).** A
   única auditoria espacial rigorosa hoje depende de o dono do processo
   rodar manualmente um script fora do Opyta_Data. Um colaborador comum não
   tem como saber que essa checagem deveria acontecer.
3. **Taxonomia hierárquica não é validada (R16) nem BMWP obrigatório para
   EPT (R15).** Um cadastro com `filo="Artropoda"` ou `Insecta` como ordem
   passa sem nenhum aviso — mesmos erros reais já documentados em produção.
4. **Meio Físico não tem validação de parâmetros/VMP no validador do app
   (R18).** O `checkers.py` audita apenas a estrutura de biota; toda a
   inteligência de sinônimo/unidade/VMP existe apenas em `logs/` como
   trabalho manual do dono do processo.
5. **Colunas de esforço trocadas não são detectadas (R13).** Um erro que já
   bloqueou 52 esforços em produção via checagem manual não tem
   equivalente automático no validador atual.
6. **Deduplicação de campanha e de código de projeto não existe no app
   (R07, R22).** Um colaborador pode criar uma campanha ou usar um código
   de projeto "quase igual" a um já existente sem qualquer aviso — só será
   descoberto depois, em auditoria manual.
7. **Scripts de migração podem ser chamados fora da UI (R20).** Isso
   contorna o gate `can_proceed`; hoje nada impede tecnicamente essa
   execução direta por linha de comando.
8. **`core/campanha.py` existe mas não está conectado (R04).** É o exemplo
   mais claro de conhecimento já formalizado em código que **ainda não
   protege ninguém**, porque não foi plugado no pipeline de validação/migração.

---

# ETAPA 5 — Backlog priorizado de melhorias

## P0 — Crítico (risco de migrar dado incorreto ou comprometer o banco)

| # | Problema | Regra | Situação atual | Alteração proposta | Arquivos/funções envolvidos | Prioridade |
|---|---|---|---|---|---|---|
| P0-1 | Coordenada fora de faixa só gera aviso, não bloqueio | R08 | `INVALID_COORDINATES` = warning | Mudar severidade para `block`; manter mensagem já existente | `validators/importacao/checkers.py::check_pontos` | P0 |
| P0-2 | Sem auditoria de coordenadas contra KMZ/KML no fluxo do colaborador | R10 | Só existe como script manual no Analysis | Portar `geo_reference.py`/`fix_geoambiental_coordinates.py` para um checker opcional em `validators/importacao/`, ativado quando existir referência oficial cadastrada para o projeto | `Opyta_Data/validators/importacao/checkers.py` (novo `check_coordenadas_kmz`), `src/opyta_analysis/geo_reference.py` (fonte a portar) | P0 |
| P0-3 | Campanha duplicada (grafia diferente) não é detectada no app | R04, R07 | `core/campanha.py` existe mas não é chamado por validador/migrador | Plugar `normalizar_nome_campanha()` em `validators/importacao/checkers.py::check_campaign_consistency`; alertar (não decidir sozinho) quando encontrar campanha equivalente já existente no banco | `core/campanha.py`, `validators/importacao/checkers.py` | P0 |
| P0-4 | Código de projeto duplicado (espaço/acento/caixa) não é checado no upload | R22 | Só existe script de auditoria avulso no Analysis | Adicionar checagem de normalização de `Codigo_Opyta` contra `projetos` antes de liberar upload | `Opyta_Data/validators/importacao/checkers.py`, portar `normalize_code()` de `scripts/validation/audit_supabase_project_coverage.py` | P0 |
| P0-5 | Scripts de migração podem rodar fora da UI, contornando o gate `can_proceed` | R20 | Nenhuma trava técnica impede execução direta por CLI | Exigir relatório de validação (arquivo/hash) como argumento obrigatório dos scripts `migrar_*.py`, ou restringir execução a partir da UI/orquestrador | `scripts/migrar_*.py`, `runners/script_runner.py` | P0 |
| P0-6 | Limpeza pré-migração sem teste automatizado de escopo (grupo+campanha) | R24 | Lógica correta hoje, mas sem teste que garanta que nunca vira `DELETE`/`TRUNCATE` amplo | Criar teste automatizado que falha se a cláusula de limpeza não contiver `grupo_biologico` E lista de campanhas | `scripts/migrar_*.py::limpar_dados_do_grupo_e_campanha` | P0 |
| P0-7 | Isolamento de projeto não é validado no fluxo de consolidação/leitura | R21 | Documentado como lição, mas não codificado como checagem ativa no Opyta_Data | Adicionar checagem: toda consulta à consolidada deve confirmar 1 único `id_projeto`/`codigo_interno_opyta` no resultado antes de prosseguir | `Opyta_Data/scripts/processar_dados.py`, `core/engine.py` | P0 |

## P1 — Importante (problema frequente que hoje exige intervenção do dono do processo)

| # | Problema | Regra | Situação atual | Alteração proposta | Arquivos/funções envolvidos | Prioridade |
|---|---|---|---|---|---|---|
| P1-1 | Colunas de esforço trocadas (Tipo_de_Amostragem ↔ Unidade_Esforco) não detectadas | R13 | Já bloqueou 52 esforços em produção, mas via checagem manual/externa | Adicionar heurística: se `Tipo_de_Amostragem` casar com padrão de unidade (contém `/`, dígito+símbolo) ou vice-versa, gerar bloqueio | `validators/importacao/checkers.py::check_esforco` | P1 |
| P1-2 | BMWP obrigatório para EPT não é checado | R15 | Só checagem genérica "numérico se preenchido" | Adicionar checagem: se `ordem` ∈ {Ephemeroptera, Plecoptera, Trichoptera} então `bmwp_score` não pode ser nulo | `validators/especies/rules.py::_check_bmwp_score` | P1 |
| P1-3 | Normalização taxonômica hierárquica ausente (Arthropoda/Insecta/Família≠Gênero/sp.) | R16 | Só existe como script de manutenção ad-hoc para 1 projeto | Portar as 4 checagens de `normalize_geoher001_bentos_taxonomy.py` como regras genéricas em `validators/especies/rules.py` | `validators/especies/rules.py`, script fonte citado | P1 |
| P1-4 | Duplicata de espécie contra o banco (não só dentro da planilha) | R17 | Só checa duplicata intra-planilha | Estender `db_checker.py` para comparar chave normalizada da planilha contra todas as espécies já cadastradas, não só contra nome exato | `validators/especies/db_checker.py` | P1 |
| P1-5 | Meio Físico sem validação de parâmetros/VMP no app | R18 | Gap confirmado pelo próprio código; toda inteligência está em `logs/` manual | Criar `validators/meio_fisico/` (reader+checkers+pipeline) com as 5 categorias já usadas manualmente (`matched/synonym_review/unit_review/vmp_review/new_parameter`) | Novo módulo `Opyta_Data/validators/meio_fisico/`; fonte de regra: `docs/control_center/MEIO_FISICO_WORKFLOW.md` |P1 |
| P1-6 | Sinal de limite de detecção não é validado antes da migração (só no script de migração) | R19 | Parse ocorre tarde demais (dentro do migrador, não do validador) | Mover `extrair_sinal_e_valor` (ou equivalente) para um checker de pré-validação que reporte linhas não-parseáveis antes de migrar | `scripts/migrar_meio_fisico.py::extrair_sinal_e_valor` → novo checker |P1 |
| P1-7 | Auditoria não cobre todos os scripts de migração nem persiste em Supabase | R25 | JSON local, best-effort, cobertura parcial (P1/P2 já planejados pelo próprio time em `LASTRO_ATIVIDADES_2026-06-20.txt`) | Tabela `audit_log` em Supabase + `record_operation()` chamado em todos os `migrar_*.py` | `core/audit/manifest.py`, todos `scripts/migrar_*.py` | P1 |
| P1-8 | Nome de aba de cadastro de espécies inconsistente entre grupos (Especies vs Cadastro_Especies) | R02 | Cada script tem seu próprio alias, sem padrão único | Padronizar um único nome de aba (ou lista de aliases idêntica) em todos os modelos oficiais e no validador | `core/modelos_oficiais.py`, `validators/importacao/reader.py`, `validators/especies/reader.py` | P1 |

## P2 — Experiência do usuário (mensagens ruins, orientação insuficiente, fluxo confuso)

| # | Problema | Regra | Situação atual | Alteração proposta | Arquivos/funções envolvidos | Prioridade |
|---|---|---|---|---|---|---|
| P2-1 | Mensagem de espécie desconhecida não lista quais espécies faltam | R14 | Mensagem genérica "serão cadastradas automaticamente ou necessitarão revisão" | Listar nome exato de cada espécie desconhecida (já existe a lista `especies_desconhecidas`, só falta exibi-la de forma clara) | `validators/importacao/checkers.py::check_especies_no_banco`, `render.py` | P2 |
| P2-2 | Mensagem de consolidação não explica o que o backup permite reverter | R23 | Aviso genérico "processo definitivo, não há volta atrás" | Explicar: "um backup foi criado automaticamente; é possível reverter via {onde/como}" ou, se não for possível reverter facilmente, dizer isso explicitamente | `app/pages/02_Consolidacao.py` | P2 |
| P2-3 | Falta de orientação objetiva de correção nas mensagens de erro de coordenada/campanha | R04, R08 | Mensagem diz "o que" está errado, não sempre "como corrigir" | Padronizar todas as mensagens de erro com um campo fixo "Como corrigir:" seguindo o padrão já bom de `POINT_COORDINATE_DIVERGENCE` | `validators/*/checkers.py`, `render.py` | P2 |
| P2-4 | Colaborador não sabe quando uma checagem exige decisão humana vs correção objetiva | Todas | Severidades hoje são só `block`/`warning`/`info` | Adicionar rótulo visível "requer decisão humana" para os casos como campanha equivalente, sinônimo de parâmetro, espécie nova — sem tentar decidir automaticamente | `validators/findings.py` (já tem `StatusRevisao`, subaproveitado na UI de importação) | P2 |
| P2-5 | Nenhum painel único mostra "o que falta para este projeto poder migrar com segurança" | Várias | `00_Pipeline_Status.py` existe mas é genérico | Adicionar por projeto: checklist de pré-requisitos (Base Mestre ok? parâmetros ok? Gate A/B pendente?) | `app/pages/00_Pipeline_Status.py` | P2 |

## P3 — Evolução futura (não necessária agora para colocar o processo nas mãos da equipe)

| # | Problema | Regra | Situação atual | Alteração proposta | Arquivos/funções envolvidos | Prioridade |
|---|---|---|---|---|---|---|
| P3-1 | Sem RBAC por perfil (leitura/operação/administração) | — | Senha única compartilhada | Implementar perfis de acesso | `app/main.py`, `core/sidebar.py` | P3 |
| P3-2 | Backend orquestrador (`opyta_ops`) para impor gates centralizadamente | — | Decisão registrada, não iniciada | Especificar e construir conforme `docs/decisions/2026-07-06_opyta_data_backend_orquestrador.md` | Novo repositório | P3 |
| P3-3 | Consulta a taxonomia externa (GBIF/WoRMS) e detecção de sinonímia automática | R16, R17 | Não implementado, não crítico para operação atual | Avaliar depois que as regras P0-P1 estiverem estáveis | `validators/especies/` | P3 |
| P3-4 | Versionamento de modelos oficiais (v1.0, v1.1...) | R02 | Modelos existem, sem histórico de versão visível | Adicionar versionamento com changelog no app | `core/modelos_oficiais.py` | P3 |
| P3-5 | Chat/assistente de IA para orientar o colaborador durante a correção | — | Fora do escopo atual por decisão explícita do usuário | Não iniciar agora | — | P3 (explicitamente adiado) |

---

## Observação final sobre proveniência

Este documento evitou inventar regra nova sem marcar `[R]`. A imensa maioria
das entradas é `[E]` (comprovada em arquivo real) ou `[E, tácito]`/`[I]`
(código existe e implica a regra, mas ninguém a escreveu como frase explícita
em lugar nenhum). As poucas recomendações genuinamente novas desta auditoria
estão concentradas na Etapa 5 (ex.: "rótulo de decisão humana" em P2-4,
"teste automatizado de escopo de limpeza" em P0-6) — nenhuma delas foi
apresentada como se já existisse no projeto.
