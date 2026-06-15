# GEOHER001 Herculano 2022-2025

## Escopo

- Projeto Supabase: `30`
- Codigo: `GEOHER001`
- Cliente: Geomil
- Projeto: `Monitoramento de ictio e bentos - Herculano`
- Recorte temporal: C21 a C36, de 2022 a 2025
- Recorte espacial: todos os pontos amostrais

## Receita

Arquivo oficial:

`configs/projects/geoher001_herculano_2022_2025.json`

## Produtos

Destino final:

`G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Geomil/Herculano - Informacoes Complementares Licenciamento Pilhas/Resultados`

Subpastas:

- `Ictiofauna`
- `Bentos`

## Decisoes graficas

- A4 paisagem.
- 600 dpi.
- Paleta azul Opyta.
- Minigraficos temporais nos graficos 02, 03 e 10.
- Grafico 06 separado por ano.
- Zoobentos grafico 12 com EPT azul e CHOL vermelho.

## Observacoes de dados

- A campanha C37 de Bentos foi corrigida como fevereiro/2026 e ficou fora do
  recorte analitico 2022-2025.
- Para Ictiofauna, a campanha C21 possui esforco com captura zero. O pipeline
  preserva a campanha nas metricas temporais com registros internos de esforco
  zero, mas exclui esses registros dos produtos taxonomicos.

## Scripts de apoio

- `scripts/run_pipeline.py`
- `scripts/run/run_project_recipe.py geoher001_herculano_2022_2025 --env-file .env`
- `scripts/maintenance/geoher001/`
- `scripts/prototypes/prototipar_geoher001_bentos_layouts.py`

## Padroes relacionados

- `docs/patterns/minigraficos_temporais.md`
- `docs/patterns/cpue_por_ano.md`
- `docs/patterns/ept_chol.md`
- `docs/patterns/paleta_azul_opyta.md`
