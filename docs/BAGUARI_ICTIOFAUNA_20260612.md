# Baguari Ictiofauna 2026-04

Data do registro: 2026-06-12

## Escopo

Projeto Micra/Baguari:

- `project_id`: 188
- `codigo_interno_opyta`: `MICGAG001`
- grupo: `Ictiofauna`
- cliente: `Micra`
- projeto: `Monitoramento da ictiofauna da UHE Baguari`
- bacia: Rio Doce

Planilha revisada pelo cliente:

`G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Micra\Baguari\Campanhas\2026\4. Abril\5. Planilhas\BD_UHE_Baguari_MIGRACAO_AJUSTADA_20260612 REV01.xlsx`

Planilha usada para carga:

`G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Micra\Baguari\Campanhas\2026\4. Abril\5. Planilhas\BD_UHE_Baguari_MIGRACAO_AJUSTADA_20260612 REV01_MIGRACAO_VALIDADA.xlsx`

## Preparacao da Planilha

A planilha REV01 original foi preservada. Foi criada uma copia tecnica para
migracao com ajustes apenas em marcadores que entrariam em campos numericos:

- `Metadados_Esforco.Esforco`: 136 valores `N.A.` convertidos para vazio/NULL.
- `Especies.BMWP_Score`: 15 valores `N.A.` convertidos para vazio/NULL.

Regra fixada: em ictiofauna, esforco qualitativo pode ficar sem valor numerico.
O migrador deve converter valores vazios/`N.A.` para `NULL`, nunca tentar gravar
texto em campo numerico.

## Validacao

Validador oficial de `Opyta_Data` sobre a copia validada:

- campanhas: 65
- pontos: 393
- registros brutos: 4954
- linhas de cadastro de especies: 15
- especies novas no banco: 1
- especies ja existentes: 14
- bloqueios: 0
- aviso esperado antes da carga: projeto ainda nao existia no banco

Auditoria complementar:

- duplicatas exatas em resultados: 886 linhas.
- grupos com multiplas linhas para agregacao: 820.
- grupos esperados apos agregacao do migrador: 1901.
- especies dos resultados: 60.
- taxa sem correspondencia antes do cadastro: `Pseudoplatystoma sp.`
- apos cadastro, todas as 60 especies tiveram correspondencia exata.

O bloqueio complementar `SPECIES_UPSERT_CAN_OVERWRITE_EXISTING_DATA` foi tratado
como conservador para este caso, pois nao havia especies em risco alto. As
diferencas eram principalmente preenchimento de campos antes vazios.

## Cadastro e Migracao

Sequencia executada em `Opyta_Data`:

```powershell
python scripts\validar_importacao.py "<PLANILHA_VALIDADA>" Ictiofauna
python scripts\cadastrar_especies.py "<PLANILHA_VALIDADA>"
python scripts\migrar_ictiofauna.py "<PLANILHA_VALIDADA>"
python scripts\processar_dados.py
```

Resultado da migracao:

- cliente/projeto criado ou verificado no banco.
- 400 linhas de esforco processadas.
- 395 esforcos efetivos no banco, por chave unica `Campanha + Ponto + Metodo`.
- 1901 resultados inseridos/atualizados.
- soma de individuos: 141194.
- especies nos resultados: 60.

Chaves duplicadas de esforco equivalentes na planilha:

- `BG_STP_C18_202601 | BG-09 | Rede`
- `BG_STP_C19_202602 | BG-09 | Rede`
- `BG_STP_C23_202411 | STP | Arrasto`
- `BG_STP_C24_202411 | STP | Arrasto`
- `BG_STP_C31_202503 | STP | Arrasto`

## Consolidacao

`scripts/processar_dados.py` consolidou 24085 registros totais em
`biota_analise_consolidada`.

Conferencia para `MICGAG001` / Ictiofauna:

- linhas consolidadas: 1901
- campanhas com resultados: 64
- pontos unicos: 19
- especies: 60
- soma de individuos: 141194
- grupos faltantes na comparacao planilha agrupada x banco: 0
- grupos extras: 0
- diferencas de individuos por grupo: 0

Observacao: `BG_STP_C37_202601` possui pontos/esforcos, mas nao possui registros
em `Resultados_Ictiofauna`; por isso aparece na base operacional de pontos e
nao aparece na consolidada de resultados.

## Ajustes Incorporados em Codigo

Em `Opyta_Data/scripts/migrar_ictiofauna.py`:

- `Esforco` passa por coercao numerica antes da carga.
- valores `NaN` em esforco, unidade, tipo, abundancia e biometria sao enviados
  como `NULL`.

Em `Opyta_Data/scripts/processar_dados.py`:

- `id_projeto` foi incluido na tabela consolidada para permitir recorte seguro
  por projeto em produtos e relatorios.

Em `Opyta_Data_Analysis/scripts/validar_migracao_ictiofauna.py`:

- formato de campanha Baguari `BG_BAG_C##_AAAAMM` e `BG_STP_C##_AAAAMM` foi
  reconhecido na checagem data/campanha.
- esforco qualitativo sem valor numerico deixou de ser bloqueio.
- especies podem ser validadas contra cadastro incremental ou banco.
- duplicatas exatas de resultados viraram aviso, pois podem representar
  individuos/lotes antes da agregacao.

## Relatorio HTML Executivo

Gerador:

`outputs/_project_scripts/baguari_ictiofauna/generate_baguari_html_report.py`

Saida gerada:

`G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Micra\Baguari\Campanhas\2026\4. Abril\5. Planilhas\relatorio_resultados_baguari_ictiofauna_20260612.html`

Conteudo:

- resumo executivo.
- mapa interativo Leaflet/OpenStreetMap.
- mapa esquematico numerado, com legenda dos 19 pontos.
- infograficos de origem, estrategia reprodutiva e valor economico.
- graficos de especies dominantes, familias, metodos, pontos e serie temporal.
- tabelas de especies ameacadas, nao nativas, migradoras, top especies e pontos.

Aprendizado visual: para Baguari, pontos como `BG-02`, `BG-09` e `STP` sao muito
proximos. Evitar rotulos grandes diretamente no mapa. Usar numeracao,
deslocamento de rotulos, linhas-guia e legenda lateral.

## Checklist para Repetir

1. Preservar planilha original do cliente e criar copia de carga validada.
2. Converter marcadores `N.A.` de campos numericos para vazio/NULL.
3. Rodar validador oficial.
4. Rodar auditoria complementar para duplicatas/agregacoes.
5. Cadastrar especies antes de migrar.
6. Conferir correspondencia exata de todos os taxa dos resultados.
7. Migrar ictiofauna.
8. Consolidar `biota_analise_consolidada`.
9. Conferir planilha agrupada x banco:
   - grupos faltantes;
   - grupos extras;
   - soma de individuos por grupo;
   - riqueza total;
   - pontos e campanhas.
10. Gerar produto executivo apenas depois da carga bater.
