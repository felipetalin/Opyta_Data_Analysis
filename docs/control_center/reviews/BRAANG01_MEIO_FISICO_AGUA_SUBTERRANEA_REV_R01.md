# BRAANG01 - Meio Fisico - Agua Subterranea - REV R01

Data de abertura: 2026-07-09

## Status

- estado: `awaiting_revision_approval`
- tipo principal: `analysis`
- tipos secundarios: `layout`
- impacto: `R2`
- gates reabertos: Gate C somente, se a revisao for executada como nova saida
  grafica.

## Pedido

O usuario solicitou registrar uma revisao para os graficos de `Agua
Subterranea` do projeto AngloGold/Brandt:

- manter o layout aprovado;
- deixar nos graficos somente o uso de `dessedentacao animal`;
- eliminar os outros usos atualmente desenhados como linhas de VMP na serie
  temporal.

## Linha De Base

Pasta original preservada:

- `Resultados/Agua_Subterranea`

Pasta de revisao criada:

- `Resultados/_revisoes/R01_agua_subterranea_dessedentacao_20260709`

Conteudo criado na pasta de revisao:

- `linha_base/Agua_Subterranea`: copia da saida atual de Agua Subterranea;
- `revisado/Agua_Subterranea`: destino vazio para a nova geracao;
- `scripts/ANGLO-Meio-Fisico_linha_base.ipynb`: copia do notebook original;
- `manifest_linha_base_sha256.csv`: manifesto SHA256 da linha de base.

Linha de base copiada em 2026-07-09:

- 38 arquivos de saida de Agua Subterranea;
- 37 graficos PNG;
- 1 matriz Excel.

## Diagnostico Tecnico

O notebook legado `ANGLO-Meio-Fisico.ipynb` desenha, para `Agua Subterranea`,
quatro categorias de VMP na funcao `gerar_serie_temporal_perfeita`:

- `vmp_396_consumo_humano`;
- `vmp_396_dessedentacao_animal`;
- `vmp_396_irrigacao`;
- `vmp_396_recreacao`.

A revisao solicitada deve alterar somente essa configuracao visual dos graficos
temporais, mantendo:

- dados de medicao;
- pontos;
- campanhas;
- layout aprovado;
- dimensoes, fonte, cor da serie, DPI e paginacao do grafico.

## Escopo Executavel Proposto

1. Usar a pasta `revisado/Agua_Subterranea` como destino da nova geracao.
2. Ajustar a configuracao subterranea dos graficos temporais para manter apenas
   `vmp_396_dessedentacao_animal`.
3. Preservar o label visual como `VMP - Dessedentacao`.
4. Nao alterar matriz Excel, IQASB ou regra de coloracao de violacao sem nova
   aprovacao explicita.
5. Comparar a linha de base com a revisao no Gate R.

## Execucao Da Revisao

Executado em 2026-07-09.

Script reprodutivel:

- `scripts/revisar_braang01_agua_subterranea_dessedentacao.py`
- copia arquivada em
  `Resultados/_revisoes/R01_agua_subterranea_dessedentacao_20260709/scripts/revisar_braang01_agua_subterranea_dessedentacao.py`

Saida revisada:

- `Resultados/_revisoes/R01_agua_subterranea_dessedentacao_20260709/revisado/Agua_Subterranea`

Arquivos gerados/copiedos:

- 36 graficos temporais `ST_*.png` regenerados;
- 1 grafico `02_Percentual_Violacao.png` copiado sem alteracao;
- 1 `revision_generation_metadata.json`;
- `manifest_revisado_sha256.csv` criado na raiz da revisao.

Configuracao aplicada nos graficos temporais:

- uso mantido: `vmp_396_dessedentacao_animal`;
- usos removidos da visualizacao: `vmp_396_consumo_humano`,
  `vmp_396_irrigacao`, `vmp_396_recreacao`;
- layout visual preservado a partir do notebook legado:
  paginacao por ate 3 pontos, serie verde, fonte grande, DPI 600 e legenda no
  canto superior direito quando ha VMP.

Validacao executada:

- contagem da pasta revisada: 37 PNGs e 1 JSON;
- manifesto SHA256 revisado: 38 linhas;
- validacao de dimensoes/pixels por Pillow em amostra de PNGs;
- inspecao visual de `ST_Manganes_Total_P1.png`, confirmando apenas a linha
  `VMP - Dessedentacao: 0.05`;
- parametros com VMP de dessedentacao preenchido no consolidado:
  `Arsenio Total`, `Manganes Total` e `Sulfato`.

Gate R:

- aguardando aprovacao do usuario para promover ou ajustar a versao revisada.

## Ajuste Pontual De Layout

Data: 2026-07-09

Arquivos ajustados:

- `revisado/Agua_Subterranea/ST_Solidos_Dissolvidos_Totais_P2.png`
- `revisado/Agua_Subterranea/ST_Zinco_Dissolvido_P2.png`

Causa:

- o titulo geral sobrepunha o titulo do primeiro painel nas paginas com poucos
  paineis:
  - `Solidos Dissolvidos Totais (Agua Subterranea)` sobre `Ponto MCB2003`;
  - `Zinco Dissolvido (Agua Subterranea)` sobre `Ponto MCB2012`.

Correcao:

- as figuras foram regeneradas com maior margem superior entre o titulo geral e os
  paineis;
- dados, pontos, campanhas, escala, serie temporal e criterio de VMP foram
  preservados.

Validacao:

- inspecao visual confirmou ausencia de sobreposicao;
- `manifest_revisado_sha256.csv` foi atualizado;
- o script reprodutivel aplica margem superior ampliada para paginas
  com 1 ou 2 paineis.

## Observacoes

- Esta revisao nao implica migracao nem consolidacao.
- A alteracao e metodologica/analitica da saida grafica, por isso foi
  classificada como `R2` mesmo sem alterar os dados brutos.
- A palavra operacional normalizada no registro e `dessedentacao animal`.
