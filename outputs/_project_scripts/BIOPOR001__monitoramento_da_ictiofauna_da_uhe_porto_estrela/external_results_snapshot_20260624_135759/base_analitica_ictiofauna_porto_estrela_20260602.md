# Base analitica ictiofauna - Porto Estrela

Gerado em 2026-06-02 14:05.

## Fontes

- Workbook validado: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Migração\Opyta-Bios-Porto_Estrela-Ictio-2026_MIGRACAO_VALIDADA_260602.xlsx`
- Caracterizacao aprovada: `caracterizacao_especies_porto_estrela_20260602.xlsx`

## Premissas aplicadas

- Corte temporal: ate dezembro de 2025 (`AAAAMM <= 202512`).
- Campanhas no corte: 90.
- Pontos: 9.
- Especies: 61.
- `PC_g` tratado como peso individual.
- `Biomassa_g_linha = Numero_de_Individuos * PC_g`.
- `CPUEn_linha = Numero_de_Individuos / Esforco * 100`.
- `CPUEb_linha = Biomassa_g_linha / Esforco * 100`.
- CPUE calculada apenas para amostragem quantitativa.
- `CPUEn` e a metrica central de abundancia padronizada e deve orientar
  estatistica, diversidade quantitativa, similaridade e series temporais de
  abundancia.
- Reproducao: `Sexo` + `EMG` padronizados conforme Bazzoli (2003).
- Evidencia reprodutiva forte: `F3`, `M3`, `F4` e `M4`.

## Amostragem

| Tipo_Amostragem_Base   |   Linhas |   Campanhas |   Pontos |   Especies |   Abundancia_Total |   Biomassa_Total_g |
|:-----------------------|---------:|------------:|---------:|-----------:|-------------------:|-------------------:|
| Qualitativa            |     9062 |          85 |        9 |         51 |              21151 |   416470           |
| Quantitativa           |    16007 |          90 |        9 |         52 |              17214 |        1.81068e+06 |

## CPUE por trecho

| Trecho   |   Campanhas |   Pontos |   Esforcos_Quantitativos |   Abundancia_Total |   Biomassa_Total_g |   CPUEn_Total |   CPUEb_Total |
|:---------|------------:|---------:|-------------------------:|-------------------:|-------------------:|--------------:|--------------:|
| Jusante  |          90 |        5 |                      260 |               6390 |        1.10322e+06 |       464.867 |       85081   |
| Montante |          90 |        4 |                      326 |              10824 |   707459           |       508.561 |       32597.7 |

## Reproducao - especies migradoras e/ou ameacadas

| Nome_Cientifico             | Migradora_Nao_Migradora   | Ameacada_Extincao   | Grupo_Reprodutivo_Principal   |   Linhas_EMG |   Abundancia_Total_EMG |   Abundancia_Evidencia_Forte |   Campanhas |   Pontos |   Perc_Evidencia_Forte |
|:----------------------------|:--------------------------|:--------------------|:------------------------------|-------------:|-----------------------:|-----------------------------:|------------:|---------:|-----------------------:|
| Pimelodus maculatus         | Migradora                 | N?o                 | True                          |         2142 |                   2191 |                          590 |          83 |        9 |               26.9283  |
| Prochilodus costatus        | Migradora                 | N?o                 | True                          |          282 |                    282 |                           75 |          58 |        7 |               26.5957  |
| Megaleporinus conirostris   | Migradora                 | N?o                 | True                          |          392 |                    414 |                           64 |          72 |        7 |               15.4589  |
| Salminus brasiliensis       | Migradora                 | N?o                 | True                          |          111 |                    119 |                           37 |          44 |        5 |               31.0924  |
| Prochilodus vimboides       | Migradora                 | Sim                 | True                          |          152 |                    152 |                           36 |          37 |        7 |               23.6842  |
| Lophiosilurus alexandri     | N?o migradora             | Sim                 | True                          |           50 |                     50 |                           23 |          30 |        6 |               46       |
| Hypomasticus copelandii     | Migradora                 | N?o                 | True                          |          201 |                    204 |                           12 |          62 |        6 |                5.88235 |
| Henochilus wheatlandii      | N?o migradora             | Sim                 | True                          |           47 |                     48 |                            4 |          25 |        6 |                8.33333 |
| Brycon dulcis               | Migradora                 | Sim                 | True                          |            7 |                      7 |                            2 |           3 |        5 |               28.5714  |
| Pseudoplatystoma sp. 1      | Migradora                 | N?o                 | True                          |            7 |                      7 |                            2 |           6 |        2 |               28.5714  |
| Brycon cf. falcatus         | Migradora                 | N?o                 | True                          |            3 |                      3 |                            2 |           3 |        2 |               66.6667  |
| Piaractus mesopotamicus     | Migradora                 | N?o                 | True                          |            8 |                      8 |                            1 |           5 |        4 |               12.5     |
| Megaleporinus macrocephalus | Migradora                 | N?o                 | True                          |            3 |                      3 |                            1 |           2 |        2 |               33.3333  |

## Validacoes

| Item                                            | Valor         | Observacao                               |
|:------------------------------------------------|:--------------|:-----------------------------------------|
| Projeto                                         | Porto Estrela | BIOPOR001                                |
| Corte temporal                                  | <= 202512     | Banco confirmado ate PE090_AH2526_202512 |
| Linhas de resultado apos corte                  | 25069         |                                          |
| Campanhas apos corte                            | 90            | Esperado: 90                             |
| Pontos apos corte                               | 9             | Esperado: 9                              |
| Especies apos corte                             | 61            | Esperado: 61                             |
| Linhas quantitativas                            | 16007         |                                          |
| Linhas qualitativas                             | 9062          |                                          |
| Esforcos quantitativos                          | 586           |                                          |
| Esforcos qualitativos                           | 522           |                                          |
| Resultados sem trecho espacial                  | 0             |                                          |
| Resultados sem classe de especie                | 0             |                                          |
| Quantitativas com esforco ausente/zero          | 0             |                                          |
| Quantitativas sem PC_g para CPUEb               | 0             |                                          |
| Linhas com mais de um individuo                 | 1823          | PC_g tratado como peso individual        |
| Divergencia esforco resultado vs metadata       | 0             |                                          |
| Esforcos quantitativos com captura zero         | 0             |                                          |
| Linhas com EMG informado                        | 12333         |                                          |
| Abundancia com EMG informado                    | 13392         |                                          |
| Linhas com evidencia reprodutiva forte          | 4751          | F3/M3 + F4/M4                            |
| Abundancia evidencia reprodutiva forte          | 4928          | F3/M3 + F4/M4                            |
| Abundancia evidencia forte migradoras/ameacadas | 849           | Recorte principal da analise reprodutiva |

## Saidas

- `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\base_analitica_ictiofauna_porto_estrela_20260602.xlsx`
- `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\de_para_pontos_trechos_porto_estrela_20260602.xlsx`
