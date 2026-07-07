# AVG Ictiofauna 2026

Data do registro: 2026-06-01

## Escopo

Projeto AVG/Brandt:

- `project_id`: 9
- `codigo_interno_opyta`: `BRAAVG002`
- grupo: `Ictiofauna`
- runner definitivo: `scripts/projects/avg/run_ictio_avg_abril_maio.py`
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

Depois de executar o runner em `scripts/projects/avg/run_ictio_avg_abril_maio.py`, conferir:

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
  `python scripts/projects/avg/run_ictio_avg_abril_maio.py --campaign junho`;
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/junho`;
- produtos oficiais: 31 arquivos, sendo 15 PNG e 16 XLSX;
- conferencias finais: 15 PNGs abriram via PIL, 16 XLSX abriram via openpyxl, abundancia total por ponto = 45 individuos, biomassa total = 5,8;
- aprovacao final do usuario registrada em `docs/control_center/operations/BRAAVG002_ICTIOFAUNA_JUNHO_2026.md`.

Aprendizado operacional: para PNGs grandes em pasta do Google Drive, salvar
primeiro em diretorio temporario local e depois copiar para a pasta final.

## Observacao Sobre Ordinais

Nas campanhas AVG, padronizar nomes com ordinal feminino `ª`, por exemplo
`45ª-Abr-26` e `46ª-Mai-26`. O runner canoniza nomes de campanha para reduzir
risco de divergencia entre `a` e `ª`.
