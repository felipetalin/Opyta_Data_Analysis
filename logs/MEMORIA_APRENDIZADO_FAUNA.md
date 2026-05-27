# Memoria de aprendizado - Fauna

Data: 2026-05-25

## Diagnostico

Os pipelines de fauna ja tinham boa base operacional: blocos por grupo,
padrao visual centralizado, scripts reprodutores e metadados por execucao.
O ponto fraco era o lastro: algumas memorias antigas registravam zero arquivos
gerados mesmo quando havia entregaveis no Drive, e nao havia contexto git nem
hashes dos artefatos.

## Ajustes incorporados

- Runner atualizado para registrar branch, commit, dirty status e hashes dos
  arquivos gerados.
- `zoobentos` passou a devolver `rows_loaded`, mantendo `records` por
  compatibilidade.
- Criado nucleo de auditoria em `opyta_analysis.fauna.audit`.
- Criado script `scripts/validar_fauna_outputs.py`.
- Criada documentacao operacional em `docs/README_FAUNA_AUDITORIA.md`.
- Auditoria passou a reconhecer aliases de pastas antigas/operacionais, como
  `Fitoplancton -> Fito` e `Zoobentos -> Bentos`, registrando o alias usado
  sem alterar a memoria original.
- O cliente `fersam001` passou a declarar `audit_project_slug="sam_metais"`,
  garantindo que novas memorias de fauna caiam no mesmo lastro oficial do
  projeto.
- O contexto git separa sujeira de codigo/configuracao dos arquivos gerados em
  `outputs/_project_scripts`, para que a propria auditoria nao contamine novas
  execucoes.

## Regra operacional

Para fauna, nenhuma entrega deve ser considerada fechada apenas pela existencia
dos `.xlsx` ou `.png` no Drive. O fechamento exige um manifesto de auditoria
com status conhecido:

- `OK`: memoria e arquivos coerentes;
- `OK_WITH_WARNINGS`: revisar memoria antiga ou incompleta;
- `ERROR`: corrigir antes de entregar.

## Proximo refinamento recomendado

Centralizar metricas ecologicas comuns em um modulo compartilhado de fauna
antes de ampliar novas migracoes. Prioridade: riqueza, abundancia, Shannon,
Pielou, Bray-Curtis/Jaccard, curva de suficiencia e exportacao DarwinCore.

## Ajuste ICTIO - CPUE

Data: 2026-05-26

O calculo de CPUEn/CPUEb da ictio foi revisado para evitar superestimativa em
pontos com mais de um metodo de captura ou esforco repetido por especie.

Regra aprovada:

- somar a abundancia/biomassa por campanha e ponto;
- somar todo o esforco usado no ponto, contando cada metodo/unidade/esforco uma
  unica vez;
- calcular `CPUEn = abundancia_total / esforco_total_ponto * 100`;
- calcular `CPUEb = biomassa_total / esforco_total_ponto * 100`;
- para CPUE por especie, calcular a especie dentro de cada ponto com o mesmo
  denominador de esforco total do ponto e depois agregar por campanha/especie.

## Ajuste ICTIO - diversidade, similaridade e produtos taxonomicos

Data: 2026-05-27

Depois da revisao de CPUEn/CPUEb, os blocos derivados de abundancia quantitativa
tambem foram alinhados:

- diversidade/equitabilidade passam a usar matriz de CPUEn;
- similaridade de Bray-Curtis passa a usar matriz de CPUEn;
- ICTIO passa a gerar tabela de distribuicao por campanha/ponto;
- ICTIO passa a gerar riqueza por ordem e por familia, com tabelas, barras e
  graficos de rosca.

## Auditoria Itatiaia/Guanhaes - campanha 28

Data: 2026-05-26

### Conhecimento incorporado

- A entrega de ictiofauna parcial da campanha `C028-2026-05-SC` deve ser lida
  como analise descritiva de campanha unica, nao como analise temporal de
  estabilidade.
- O bloco 6.4 usa somente pontos quantitativos RP. Portanto, a figura de
  similaridade nao deve trazer legenda de `Tributario (TR)`.
- Cores dos ramos em dendrograma representam agrupamentos hierarquicos, nao
  ambientes. A legenda aprovada para ictio parcial e:
  `Rio Principal (RP) - dados quantitativos | cores = agrupamentos`.
- Dendrogramas exibidos em similaridade, mas calculados a partir de distancia,
  precisam de margem visual alem de 100%. Sem isso, pares identicos
  (`Jaccard = 1`) ficam colados na borda e parecem desconectados.
- Quando nao houver registros TR, o Jaccard RP x TR do bloco 6.5 deve ser
  interpretado como ausencia de dados TR, nao como dissimilaridade ecologica
  testada.
- A regra de `Exotica` deve reconhecer `Nativo/Nativa` como nao exotico e
  `Nao Nativa/Nao Nativo`, `exotico`, `alocotone`, `introduzido` ou `invasor`
  como exotico.
- Para ictiofauna, a classificacao de uso economico/cinegetico da tabela 6.6-6.8
  deve usar `valor_economico` do cadastro de especies. O campo `cinegetica`
  pode ficar vazio para peixes e nao deve ser substituido por habito alimentar.
- `audit_project_slug` precisa poder ser definido por execucao. Um mesmo
  cliente/config pode atender mais de um projeto operacional, como `sam_metais`
  e `project_165`.

### Risco arquitetural identificado

Os scripts multiempreendimento atuais funcionam, mas ainda dependem de campanha,
caminho, lista de empreendimentos e variaveis globais hardcoded. Para novas
campanhas, o proximo ganho operacional e criar uma configuracao por
projeto/campanha e um runner de lote generico.

### Proxima frente

Antes da migracao da Avifauna, criar a arquitetura alvo registrada em
`docs/FAUNA_ARQUITETURA_MULTIUSO_AUDITORIA.md`, ou pelo menos usar esse desenho
como criterio para nao repetir scripts especificos e duplicados.
