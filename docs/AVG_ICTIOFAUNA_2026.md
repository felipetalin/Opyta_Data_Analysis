# AVG Ictiofauna 2026

Data do registro: 2026-06-01

## Escopo

Projeto AVG/Brandt:

- `project_id`: 9
- `codigo_interno_opyta`: `BRAAVG002`
- grupo: `Ictiofauna`
- recipe: `configs/projects/braavg002_ictiofauna_2026.json`
- runner por campanha: `scripts/projects/avg/run_ictio_avg_2026_por_campanha.py`
- runner historico: `scripts/projects/avg/run_ictio_avg_abril_maio.py`
- tema: `configs/clients/braavg002.json`
- raiz de saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026`

Campanhas executadas:

- abril: `45ª-Abr-26`
- maio: `46ª-Mai-26`

## Areas de Controle

Area de controle 01:

- `PIC-01`
- `PIC-02`
- `PIC-03`
- `PIC-04`
- `PIC-05`
- `PIC-06`
- `PIC-07`
- `PIC-08`
- `PIC-09`
- `PIC-11`

Area de controle 02:

- `PIC-10`
- `PIC-12`
- `PIC-13`

Nos graficos por ponto, a ordem final deve ser AC01 completa primeiro e AC02
depois:

`PIC-01`, `PIC-02`, `PIC-03`, `PIC-04`, `PIC-05`, `PIC-06`, `PIC-07`,
`PIC-08`, `PIC-09`, `PIC-11`, `PIC-10`, `PIC-12`, `PIC-13`.

Para os minigraficos espaciais e sinteses funcionais, criar a coluna analitica
`area_controle` com estes mesmos grupos. Essa delimitacao deve ser usada para
separar/identificar AC01 e AC02 nos produtos derivados do modelo GEOARC001.

## Ajustes De Pontos E Amostragem

Definicao revisada em 2026-07-15:

- `PIC-01`: vigente de agosto/2022 a outubro/2025 (`C001` a `C039`);
  descontinuado a partir de novembro/2025 por restricao de acesso.
- `PIC-02` original: vigente de agosto/2022 a outubro/2025 (`C001` a
  `C039`); substituido por novo ponto com caracteristicas ambientais
  semelhantes.
- `PIC-02` realocado: ativo de fevereiro/2026 a junho/2026 (`C043` a
  `C047`); usar `-19.800376/-43.710610` na camada analitica espacial.
- `PIC-03`: vigente de agosto/2022 a outubro/2025 (`C001` a `C039`), com
  amostragem excepcional em fevereiro/2026 (`C043`); sem amostragem em
  `C040-C042` e descontinuado definitivamente de `C044` em diante.
- `PIC-11` deve usar `-19.801526/-43.700959`.
- `PIC-11`: vigente de agosto/2022 a outubro/2025 (`C001` a `C039`);
  descontinuado a partir de novembro/2025 por restricao de acesso.

Esses ajustes foram aplicados na regra da camada analitica. Por orientacao do
usuario em 2026-07-15, os graficos ainda nao foram regenerados com esta revisao
pontual. O banco mestre nao foi alterado nesta rodada.

## Pontos com Captura Zero

Pontos com esforco quantitativo e captura zero devem aparecer nos graficos por
ponto ate CPUE:

- riqueza por ponto;
- abundancia por ponto;
- CPUEn por ponto;
- CPUEb por ponto.

Para isso, o runner cria linhas auxiliares com `contagem = 0` e `biomassa = 0`.
Essas linhas existem apenas para completar o eixo dos graficos por ponto.

Regra importante: essas linhas auxiliares nao podem entrar em blocos
taxonomicos ou comunitarios, porque nao representam especie real. Se entrarem
em riqueza por ordem/familia ou composicao, geram uma categoria falsa
`Nao informado`.

No runner AVG, usar:

- dados observados reais nos blocos de composicao, distribuicao, ordem,
  familia, CPUE por especie, diversidade, similaridade, suficiencia e
  DarwinCore;
- dados com placeholders de zero somente nos blocos 5, 6 e 8, isto e,
  riqueza/abundancia/CPUE por ponto.

## Saida Final

As pastas `abril` e `maio` devem conter somente a versao final dos arquivos.
Nao deixar subpastas paralelas como `corrigidos_word`, para evitar confusao na
montagem do Word.

## Validacoes Minimas Apos Rodar

Antes de gerar, rodar o preflight da campanha alvo:

`python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --preflight --campaign junho`

Depois de executar o runner em `scripts/projects/avg/run_ictio_avg_2026_por_campanha.py`, conferir:

- as pastas `abril` e `maio` nao possuem `corrigidos_word`;
- os arquivos `02_df_riqueza_por_ponto_ictiofauna.xlsx`,
  `03_df_abundancia_por_ponto_ictiofauna.xlsx` e
  `06_df_cpue_por_ponto_ictiofauna.xlsx` possuem 13 pontos;
- a ordem dos pontos segue AC01 + AC02;
- os quatro PNGs por ponto existem:
  - `02_grafico_riqueza_por_ponto_ictiofauna.png`;
  - `03_grafico_abundancia_por_ponto_ictiofauna.png`;
  - `06_grafico_cpuen_por_ponto_ictiofauna.png`;
  - `07_grafico_cpueb_por_ponto_ictiofauna.png`;
- `04_df_riqueza_por_ordem_ictiofauna.xlsx` e
  `04_df_riqueza_por_familia_ictiofauna.xlsx` nao contem `Nao informado`;
- `01_tabela_composicao_ictiofauna.xlsx` nao contem linha com taxon vazio.

## Junho/2026

Rodada parcial de Ictiofauna AVG encerrada em 2026-07-01.

- campanha: `47ª-Jun-26`;
- comando recomendado para campanha unica:
  `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --campaign junho`;
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/junho`;
- produtos oficiais: 31 arquivos, sendo 15 PNG e 16 XLSX;
- conferencias finais: 15 PNGs abriram via PIL, 16 XLSX abriram via openpyxl, abundancia total por ponto = 45 individuos, biomassa total = 5,8;
- aprovacao final do usuario registrada em `docs/control_center/operations/BRAAVG002_ICTIOFAUNA_JUNHO_2026.md`.

Aprendizado operacional: para PNGs grandes em pasta do Google Drive, salvar
primeiro em diretorio temporario local e depois copiar para a pasta final.

## Estudo Longo E Analises GEOARC001

Auditoria de prontidao criada em 2026-07-13:

- script:
  `scripts/projects/avg/audit_ictio_avg_long_study_readiness.py`;
- saida:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/readiness_ictio_long_study_20260713`;
- escopo atual apos regra revisada: 47 campanhas, 13 pontos, 585 ponto-campanhas amostrados e 13 especies;
- beta/LCBD taxonomico: gerado em 2026-07-13 com ano temporal agosto-julho;
- ecologia funcional: gerada em 2026-07-13 com 13 traits aprovados para uso analitico;
- minigraficos funcionais e sintese espacial: gerados em 2026-07-13 usando provisoriamente o KML padrao da raiz `Geo`; em 2026-07-15 a regra analitica foi atualizada para PIC-01/PIC-02/PIC-03/PIC-11. Os produtos espaciais derivados devem ser regenerados antes do fechamento desses mapas.
- requisito adicional para minigraficos/sinteses funcionais: preservar a delimitacao `area_controle` com `Area de controle 01` e `Area de controle 02`.

Pacote gerado:

- pasta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/estudo_longo_geoarc001_20260713`;
- copia consolidada:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/Consolidado_2026/icitiofauna`;
- fonte analitica:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/geoarc001_long_study_source_20260713`;
- produtos gerados anteriormente: 13 PNG, 12 XLSX, 5 JSON e 2 README/MD;
- validacao: PNGs abriram via PIL e XLSX abriram via openpyxl, sem erro;
- pendencia: regenerar produtos espaciais GEOARC001 com a fonte atualizada e revisar `KML Atual`; se for adotado como oficial, reabrir Gate A e regenerar produtos espaciais.

## Consolidado 2026

Analises tradicionais geradas em 2026-07-14 na pasta consolidada:

- pasta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/Consolidado_2026/icitiofauna`;
- runner:
  `scripts/projects/avg/run_ictio_avg_tradicional_consolidado_2026.py`;
- escopo: base historica completa `C001-2022-08-SC` a `C047-2026-06-SC`;
- base da regra revisada: 519 registros observados, 761 linhas analiticas esperadas com placeholders de captura zero, 585 ponto-campanhas amostrados, 13 pontos e 13 especies;
- figuras por ponto: modelo A4 paisagem aprovado para relatorio, com um ponto por linha, eixo C01-C47 somente no painel inferior, CH/SC em cores fortes e anos temporais demarcados;
- nao-amostragem revisada: `PIC-01` e `PIC-11` lacuna de `C040` em diante; `PIC-02` lacuna em `C040-C042` e ativo como realocado em `C043-C047`; `PIC-03` lacuna em `C040-C042`, ativo excepcionalmente em `C043`, e lacuna de `C044` em diante;
- ocorrencia por campanha (`04B`): mantida em heatmaps por ano temporal agosto-julho (`2023`: C001-C012; `2024`: C013-C024; `2025`: C025-C036; `2026`: C037-C047);
- ajuste taxonomico de saida: `Poecilia mexicana` apresentada como `Poecilia cf. mexicana`;
- validacao da pasta final apos tradicionais + GEOARC001: 58 PNG, 29 XLSX, 6 JSON e 3 MD; PNGs abriram via PIL e XLSX abriram via openpyxl, sem erro;
- conferencia da regra em memoria: 585 ponto-campanhas amostrados; `PIC-03` presente somente em `C043` apos outubro/2025; graficos/planilhas finais ainda pendentes de regeneracao apos a revisao de 2026-07-15;
- banco: sem alteracao de nomenclatura, traits, coordenadas ou taxonomia mestre.

## Boxplots Exploratorios De Riqueza

Boxplots de riqueza gerados em 2026-07-15 como produto exploratorio separado,
sem substituir ainda os graficos tradicionais do pacote consolidado:

- script:
  `scripts/projects/avg/build_ictio_avg_richness_boxplots_exploratory.py`;
- saida:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/richness_boxplots_exploratory_20260715`;
- base: 585 ponto-campanhas amostrados, com nao-amostragem tratada como
  ausencia e nao como zero;
- figuras:
  - `EXP_BOX_01_riqueza_por_ano_temporal_ictiofauna.png`;
  - `EXP_BOX_02_riqueza_area_controle_por_ano_temporal_ictiofauna.png`;
  - `EXP_BOX_03_riqueza_por_ponto_ictiofauna.png`;
- validacao: 3 PNG abriram via PIL e 2 XLSX abriram via openpyxl, sem erro.

## Observacao Sobre Ordinais

Nas campanhas AVG, padronizar nomes com ordinal feminino `ª`, por exemplo
`45ª-Abr-26` e `46ª-Mai-26`. O runner canoniza nomes de campanha para reduzir
risco de divergencia entre `a` e `ª`.
