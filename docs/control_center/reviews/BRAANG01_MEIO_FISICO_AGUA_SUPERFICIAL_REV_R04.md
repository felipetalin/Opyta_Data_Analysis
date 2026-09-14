# BRAANG01 - Meio Fisico - Agua Superficial - REV R04

Data de abertura: 2026-07-09

## Status

- estado: `awaiting_revision_approval`
- tipo principal: `layout`
- tipos secundarios: `analysis`
- impacto: `R1`
- gates reabertos: nenhum gate anterior; revisao restrita a saida grafica.

## Pedido

O usuario solicitou aplicar a todos os parametros de `Agua Superficial` o mesmo
padrao visual da pasta:

- `Resultados/_revisoes/R04_agua_superficial_20260709/revisado/Agua_Superficial`

O padrao inclui tamanho de letra, espacamento, dois paineis empilhados,
legendas, linhas de VMP e layout geral.

## Linha De Base

Pasta original preservada:

- `Resultados/Agua_Superficial`

Pasta de revisao:

- `Resultados/_revisoes/R04_agua_superficial_20260709`

Conteudo criado:

- `linha_base/Agua_Superficial`: copia da saida original;
- `revisado/Agua_Superficial`: graficos revisados;
- `scripts/gerar_braang01_agua_superficial.py`: script reprodutivel;
- `outputs/_project_scripts/BRAANG01__anglogold_meio_fisico/meio_fisico/`:
  lastro tecnico com script, metadado e manifesto da revisao R04;
- `manifest_linha_base_sha256.csv`;
- `manifest_revisado_sha256.csv`.

Linha de base copiada em 2026-07-09:

- 36 arquivos uteis de `Agua Superficial`.

## Execucao

Executado em 2026-07-09.

Produtos revisados:

- 34 graficos temporais `ST_*.png`;
- 1 `generation_metadata.json`, incluindo auditoria `vmp_visible` por ponto;
- manifesto SHA256 revisado com 35 linhas.

O script foi corrigido durante a revisao para usar VMPs de `Agua Superficial`
corretamente:

- `vmp_357_cl2_max` para limites maximos;
- `vmp_357_cl2_min` para limites minimos;
- `vmp_amonia_dinamico` quando houver limite dinamico;
- `vmp_430_padrao` nao e usado para `Agua Superficial`.

## Auditoria De VMP

No consolidado de `BRAANG01`, matriz `Agua Superficial`, pontos `MCB1010` e
`MCB1011`:

- 34 parametros avaliados;
- 24 parametros possuem VMP preenchido e foram gerados com linha/legenda de
  VMP;
- 10 parametros nao possuem VMP preenchido no consolidado e foram gerados sem
  linha de VMP.

Parametros com VMP preenchido:

- `Arsenio Total`;
- `Cianeto Livre`;
- `Cobalto Total`;
- `Cor Verdadeira`;
- `Cromo Total`;
- `Demanda Bioquimica de Oxigenio`;
- `Fenois Totais`;
- `Ferro Dissolvido`;
- `Manganes Dissolvido`;
- `Manganes Total`;
- `Mercurio Total`;
- `Niquel Total`;
- `Nitrato`;
- `Oleos e Graxas`;
- `Oxigenio Dissolvido (OD)`;
- `pH`;
- `Selenio Total`;
- `Solidos Dissolvidos Totais`;
- `Solidos Sedimentaveis`;
- `Solidos Totais Suspensos`;
- `Sulfato`;
- `Surfactantes (LAS)`;
- `Turbidez`;
- `Zinco Total`.

Parametros sem VMP preenchido:

- `Arsenio Dissolvido`;
- `Cianeto Total`;
- `Cianeto WAD`;
- `Cobre Total`;
- `Condutividade Eletrica`;
- `Demanda Quimica de Oxigenio`;
- `Ferro Total`;
- `Itrio (Metais Totais)`;
- `Temperatura da Agua`;
- `Temperatura do Ar`.

## Validacao

Validacoes executadas:

- contagem da pasta revisada: 34 PNGs e 1 JSON;
- manifesto revisado recriado;
- auditoria cruzada banco x `generation_metadata.json`: 24 parametros com VMP,
  0 ausencias de VMP visivel e 0 VMP extra indevido;
- inspecao visual de `ST_Demanda_Bioquimica_de_Oxigenio_P1.png`, confirmando
  `VMP - maximo: 5`;
- inspecao visual de `ST_Oxigenio_Dissolvido_(OD)_P1.png`, confirmando
  `VMP - minimo: 5`;
- inspecao visual de `ST_pH_P1.png`, confirmando `VMP - maximo: 9` e
  `VMP - minimo: 6`.

Gate R:

- aguardando aprovacao do usuario para promover ou ajustar a versao revisada.
