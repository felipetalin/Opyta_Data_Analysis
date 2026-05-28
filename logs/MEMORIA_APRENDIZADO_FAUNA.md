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

## Ajuste ICTIO - ocorrencia por campanha

Data: 2026-05-27

A tabela de distribuicao da ictio deve calcular `%OC` com o numero de pontos
com dados dentro de cada campanha, nao com a lista global de pontos do projeto.
No projeto SAM Metais, a regra validada foi:

- `1a Campanha (Seca)`: 18 pontos com dados;
- `2a Campanha (Chuva)`: 22 pontos com dados.

Assim, uma especie registrada em 13 pontos na seca fica com `13/18 = 72%`, e
uma especie registrada em 11 pontos na chuva fica com `11/22 = 50%`.

## Ajuste FITO - padronizacao de filo

Data: 2026-05-27

Fitoplancton deve consolidar `filo` sem diferenciar maiuscula/minuscula.
No projeto SAM Metais, o cadastro `especies` tinha variantes como
`BACILLARIOPHYTA` e `Bacillariophyta`, gerando categorias duplicadas nos
graficos de riqueza por filo.

Correcao aplicada:

- 106 registros de `especies` foram padronizados no banco;
- o pipeline de Fitoplancton tambem normaliza `filo` na carga e nos blocos
  taxonomicos, para evitar regressao em novas importacoes;
- a riqueza por filo passou de 14 categorias textuais para 8 filos reais.

Resultado validado no bloco 7:

- `Bacillariophyta`: 82 taxons;
- `Charophyta`: 40 taxons;
- `Euglenophyta`: 15 taxons;
- `Chlorophyta`: 14 taxons;
- `Cyanobacteria`: 12 taxons;
- `Dinophyta`: 3 taxons;
- `Ochrophyta`: 2 taxons;
- `Cryptophyta`: 1 taxon.

## Ajuste DarwinCore - modelo IEF

Data: 2026-05-27

O DarwinCore dos grupos aquaticos deve seguir o modelo IEF validado a partir de
`Ocorrencia_DWC_Mirai-330216.xlsx`, em workbook multi-abas:

- `Orientacoes`;
- `Sampling Events`;
- `Associated Occurrences`;
- `Fish Biometric data` somente para ictiofauna.

Regra aprovada:

- `county` e `municipality`: `Grao Mogol`;
- `geodeticDatum`: `WGS84`;
- `basisOfRecord`: `Especime vivo`;
- `taxonRank`: `Especie`;
- `recordedBy`: `Opyta`;
- `individualCount`: densidade/contagem para Fito, Zoo e Bentos; abundancia
  para Ictio;
- coordenadas no formato decimal com simbolo de grau;
- arquivos oficiais gerados como `DarwinCore_IEF_<grupo>_<projeto>.xlsx`.

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

## Ajuste AVIFAUNA - tabelas de especies e status

Data: 2026-05-28

A tabela `6_6_6_8_tabela_geral_status.xlsx` da Avifauna para
Itatiaia/Guanhaes deve seguir o modelo aprovado com duas linhas de cabecalho:

- linha 1: `Ordem`, `Familia`, `Taxon`, `Nome Comum`, `Status`, `DAF`,
  `Sens`, `Endemismo`, `IUCN`, `MMA`, `COPAM`, `CITES`, `Guilda`;
- linha 2: anos apenas sob as listas oficiais: `IUCN=-2025`,
  `MMA=-2022`, `COPAM=-2010`, `CITES=-2025`.

Regra de preenchimento aprovada:

- usar a tabela `especies` como fonte dos campos taxonomicos e de status;
- `Status`: usar `migratorio` quando houver valor, caso contrario `BR`;
- `DAF`: `Dependentes=DEP`, `Semidependente=SED`,
  `Independente=IND`; valor vazio fica `N.A.`;
- `Sens`: `Baixo=B`, `Medio=M`, `Alto=A`;
- `Endemismo`: manter o codigo em caixa alta, como `MA` e `CA`;
- `IUCN`: status global quando houver valor; vazio fica `LC`;
- `MMA` e `COPAM`: status quando houver valor; vazio fica `NA`;
- `CITES`: manter o codigo cadastrado em caixa alta;
- `Guilda`: converter `Onivoro=ON`, `Insetivoro=IN`, `Frugivoro=FG`,
  `Granivoro=GR`, `Carnivoro=CR`, `Nectarivoro=NE`, `Necrofago=NC`,
  preservando combinacoes como `GR, FG` e `IN, CR`.

Especies com `Dependencia_Florestal` vazia no banco, mas aprovadas no output
como `DAF=N.A.`:

- `Dysithamnus stictothorax`;
- `Cercomacra brasiliana`;
- `Jacamaralcyon tridactyla`.

O modelo foi validado e gerado para os quatro empreendimentos da campanha:
`Dores de Guanhaes`, `Fortuna II`, `Jacare` e `Senhora do Porto`.

O mesmo modelo aprovado deve ser usado nas tabelas de especies do bloco 6.1:

- `6_1_tabela_especies_<empreendimento>.xlsx`;
- `6_1_tabela_especies_area_controle.xlsx`.

Essas tabelas devem conter apenas as especies do subconjunto correspondente
(empreendimento ou Area Controle), mas preservar exatamente o mesmo cabecalho,
as mesmas conversoes e a mesma segunda linha de anos da tabela geral de status.
