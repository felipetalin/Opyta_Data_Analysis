# BRAANG01 - Meio Fisico - Agua Subterranea - REV R05

Data de abertura: 2026-07-10

## Status

- estado: `awaiting_revision_approval`
- tipo principal: `analysis`
- tipos secundarios: `layout`, `package`
- impacto: `R1`
- gates reabertos: nenhum gate anterior; revisao restrita aos graficos
  temporais afetados e aos VMPs exibidos.

## Pedido

O usuario identificou erro tecnico na interpretacao dos VMPs para parametros
dissolvidos/soluveis em Agua Subterranea. A revisao deve gerar somente os
parametros necessarios:

- Arsenio;
- Cobre;
- Cobalto;
- Cromo;
- Solidos totais dissolvidos;
- Sulfato;
- Zinco;
- pH.

## Linha De Base

Linha de base preservada a partir da revisao R01:

- `Resultados/_revisoes/R01_agua_subterranea_dessedentacao_20260709/revisado/Agua_Subterranea`

Pasta de revisao:

- `Resultados/_revisoes/R05_agua_subterranea_vmp_dissolvidos_20260710`

Conteudo criado:

- `linha_base/Agua_Subterranea`: somente os PNGs afetados da R01;
- `revisado/Agua_Subterranea`: figuras revisadas;
- `scripts/revisar_braang01_agua_subterranea_vmp_dissolvidos_r05.py`;
- `manifest_linha_base_sha256.csv`;
- `manifest_revisado_sha256.csv`;
- lastro tecnico em `outputs/_project_scripts/BRAANG01_ANGLO_MEIO_FISICO`.

## Execucao

Gerados 18 graficos temporais, correspondentes a 9 parametros existentes na
base:

- `Arsenio Dissolvido`;
- `Arsenio Total`;
- `Cobalto Dissolvido`;
- `Cobre Dissolvido`;
- `Cromo Dissolvido`;
- `Solidos Dissolvidos Totais`;
- `Sulfato`;
- `Zinco Dissolvido`;
- `pH`.

## Limite Legal

Base adotada para todos os graficos revisados de Agua Subterranea:

- `Limite legal - Resolucao CONAMA 396/2008`.

A legenda visual dos graficos foi mantida como no layout aprovado, sem alterar
o texto grafico para nao descaracterizar o padrao da entrega.

Coluna do consolidado usada quando preenchida:

- `vmp_396_dessedentacao_animal`.

Limites aplicados por equivalencia do analito para especies dissolvidas:

- `Arsenio Dissolvido`: 0,2 mg/L;
- `Cobalto Dissolvido`: 1,0 mg/L;
- `Cobre Dissolvido`: 0,5 mg/L;
- `Cromo Dissolvido`: 1,0 mg/L;
- `Zinco Dissolvido`: 24,0 mg/L.

Limites mantidos do consolidado:

- `Arsenio Total`: 0,2 mg/L;
- `Sulfato`: 1000 mg/L, limite legal para dessedentacao.

Parametro sem limite desenhado:

- `Solidos Dissolvidos Totais`: sem limite legal para dessedentacao na CONAMA
  396/2008; ha limite para consumo humano, mas nao sera usado nesta revisao;
- `pH`: sem limite legal identificado na CONAMA 396/consolidado.

Fonte normativa:

- Resolucao CONAMA 396/2008, Anexo I.

## Validacao

Validacoes executadas:

- contagem da pasta revisada: 18 PNGs e 1 JSON;
- manifestos SHA256 de linha de base e revisado recriados;
- metadado `revision_generation_metadata.json` registra `vmp_visible` por
  ponto;
- inspecao visual de `ST_Cobre_Dissolvido_P1.png`, confirmando
  `VMP - Dessedentacao: 0.5`;
- inspecao visual de `ST_Solidos_Dissolvidos_Totais_P2.png`, confirmando
  ausencia de linha de limite;
- inspecao visual de `ST_Sulfato_P2.png`, confirmando limite de dessedentacao;
- inspecao visual de `ST_pH_P1.png`, confirmando ausencia de linha de VMP.

Gate R:

- aguardando aprovacao do usuario para promover ou ajustar a versao revisada.
