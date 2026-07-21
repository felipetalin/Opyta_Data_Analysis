# BRAANG01 - Meio Fisico - Efluente MCB907 - REV R02

Data de abertura: 2026-07-09

## Status

- estado: `awaiting_revision_approval`
- tipo principal: `analysis`
- tipos secundarios: `layout`
- impacto: `R2`
- gates reabertos: Gate C somente para nova configuracao de graficos.

## Pedido

O usuario solicitou revisar os graficos de efluente dos pontos `MCB907E` e
`MCB907S`, porque as figuras mensais estavam visualmente muito densas.

Decisao aprovada pelo usuario em 2026-07-09:

- usar a opcao 01;
- aplicar o recorte a partir de 2021;
- manter DBO mensal em grafico separado.

## Linha De Base

Pasta original preservada:

- `Resultados/Efluente`

Pasta de revisao criada:

- `Resultados/_revisoes/R02_efluente_mcb907_periodicidade_20260709`

Conteudo criado:

- `linha_base/Efluente`: copia da saida atual de Efluente;
- `revisado/Efluente_MCB907`: destino dos graficos revisados;
- `scripts/ANGLO-Meio-Fisico_linha_base.ipynb`: copia do notebook original;
- `scripts/revisar_braang01_efluente_mcb907_periodicidade.py`: script
  reprodutivel da revisao;
- `manifest_linha_base_sha256.csv`;
- `manifest_revisado_sha256.csv`.

Linha de base copiada em 2026-07-09:

- 34 arquivos uteis de Efluente, excluindo `desktop.ini` e temporarios `~$`.

## Escopo Aprovado

Pontos:

- `MCB907E`;
- `MCB907S`.

Campanhas selecionadas a partir de 2021:

- `jan-2021`;
- `mar-2021`;
- `jul-2021`;
- `set-2021`;
- `dez-2021`;
- `mar-2022`;
- `jun-2022`;
- `set-2022`;
- `dez-2022`;
- `mar-2023`;
- `jun-2023`;
- `set-2023`;
- `nov-2023`;
- `mar-2024`;
- `jun-2024`;
- `set-2024`;
- `nov-2024`;
- `mar-2025`;
- `jun-2025`.

Parametros com campanhas selecionadas:

- `Coliformes Totais`;
- `Demanda Quimica de Oxigenio`;
- `E. Coli`;
- `Ferro Dissolvido`;
- `Fosforo Total`;
- `Nitrogenio Total`;
- `Sulfeto`;
- `Temperatura da Agua`;
- `Oxigenio Dissolvido (OD)`;
- `Solidos Sedimentaveis`;
- `Solidos Dissolvidos Totais`;
- `Solidos Totais Suspensos`;
- `pH`.

Parametro mensal separado:

- `Demanda Bioquimica de Oxigenio`.

## Diagnostico

A planilha-fonte `Dados_brutos` contem as campanhas de 2020 para os dois pontos,
mas o consolidado usado pelos graficos atuais contem apenas o recorte de 2021 a
2025. O usuario aprovou explicitamente que o corte seja a partir de 2021.

Com isso, a revisao nao altera fonte, banco, migracao ou consolidacao. O ajuste
e uma configuracao de saida grafica baseada no consolidado existente.

## Execucao

Executado em 2026-07-09.

Saida revisada:

- `Resultados/_revisoes/R02_efluente_mcb907_periodicidade_20260709/revisado/Efluente_MCB907`

Produtos gerados:

- 13 graficos `ST_*_MCB907_campanhas_selecionadas.png`;
- 1 grafico `ST_Demanda_Bioquimica_de_Oxigenio_MCB907_mensal.png`;
- 1 `revision_generation_metadata.json`;
- manifesto SHA256 revisado com 15 linhas.

Regras aplicadas:

- os 13 parametros aprovados usam 19 campanhas selecionadas;
- DBO mantem 54 campanhas mensais por ponto;
- DBO usa rotulos reduzidos no eixo X para leitura, preservando todos os pontos
  mensais;
- todos os graficos mostram apenas `MCB907E` e `MCB907S`;
- `MCB1005` nao entra nos graficos revisados desta R02.

## Validacao

- contagem da pasta revisada: 14 PNGs e 1 JSON;
- validacao de dimensoes/pixels por Pillow em amostra de PNGs;
- inspecao visual de `ST_pH_MCB907_campanhas_selecionadas.png`;
- inspecao visual de
  `ST_Demanda_Bioquimica_de_Oxigenio_MCB907_mensal.png`;
- manifesto `manifest_revisado_sha256.csv` atualizado.

Gate R:

- aguardando aprovacao do usuario para promover ou ajustar a versao revisada.
