# EPT/CHOL

## Definicao

- EPT = Ephemeroptera + Plecoptera + Trichoptera.
- CHOL = Chironomidae + Oligochaeta/Oligoqueta.

## Convencao visual

- EPT em azul, pois simboliza melhor qualidade ambiental.
- CHOL em vermelho, pois simboliza maior pressao/degradacao organica.

## Usos aprovados

- GEOHER001/Herculano, Zoobentos grafico 12.

## Implementacao

- `src/opyta_analysis/pipelines/diagnostico/zoobentos.py`
- bloco `_run_block_12`

## Observacoes

O calculo deve manter colunas separadas na planilha de saida:

- `ept`
- `chironomidae`
- `oligochaeta`
- `chol`
- `pct_ept`
- `pct_chol`

Isso permite auditoria rapida de CHOL sem reconsultar o banco.
