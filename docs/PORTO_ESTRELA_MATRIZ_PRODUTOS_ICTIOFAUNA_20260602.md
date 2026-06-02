# Porto Estrela - matriz tecnica de produtos ictiofauna

Registro criado em 2026-06-02 a partir da lista de produtos solicitada para o
relatorio de monitoramento da ictiofauna da UHE Porto Estrela.

## Bases ja aprovadas

- Base analitica: `base_analitica_ictiofauna_porto_estrela_20260602.xlsx`.
- Caracterizacao de especies: `caracterizacao_especies_porto_estrela_20260602.xlsx`.
- De/para espacial: `de_para_pontos_trechos_porto_estrela_20260602.xlsx`.
- Corte temporal: janeiro de 2004 a dezembro de 2025.
- Campanhas no corte: 90.
- Pontos: 9.
- Especies: 61.
- Trecho Montante: `P4`, `P5`, `P2`, `P1`.
- Trecho Jusante: `P3`, `P6`, `P7`, `P8`, `P9`.
- `CPUEn` e a metrica central de abundancia padronizada.
- `CPUEb` usa `Biomassa_g_linha = Numero_de_Individuos * PC_g`.

## Regras gerais

- Todo grafico final deve ter uma planilha `.xlsx` correspondente.
- Graficos devem seguir a referencia visual Ducal/Opyta:
  `docs/PORTO_ESTRELA_LAYOUT_GRAFICOS_REFERENCIA_DUCAL_20260602.md`.
- Amostragem qualitativa: composicao, ocorrencia, curva do coletor e
  presenca/ausencia.
- Amostragem quantitativa: CPUE, diversidade quantitativa, similaridade e
  series temporais.
- Diversidade/equitabilidade devem usar matriz baseada em `CPUEn`.
- Regressao temporal: usar dados nao transformados, regressao linear simples e
  reportar parametros `a`, `b` e `R2`.

## Matriz de produtos

| Produto | Descricao | Base | Metrica | Agrupamento/recorte | Saida |
|---|---|---|---|---|---|
| Tabela 5 | Composicao de especies | Caracterizacao aprovada | Lista taxonomica | Ordem, familia, especie, autor, nome popular, nativa/nao nativa, ameaca estadual/federal/mundial | `.xlsx` |
| Figura 10 | Curva do coletor da riqueza ictiofaunistica | Presenca/ausencia, quali + quanti | Riqueza acumulada | Unidade amostral sugerida: `campanha + ponto`; periodo completo 2004-2025 | `.xlsx` + `.png` |
| Tabela 6 | Caracteristicas biologicas | Caracterizacao + ocorrencia espacial | Classes ecologicas e presenca por trecho | Especie, migracao, distribuicao, ameaca, interesse comercial, ocorrencia em Jusante/Montante | `.xlsx` |
| Figura 11a | Percentual de especies por ordem | Caracterizacao aprovada | Percentual de riqueza | Ordem | `.xlsx` + rosca `.png` |
| Figura 11b | Percentual de especies por familia | Caracterizacao aprovada | Percentual de riqueza | Familia | `.xlsx` + rosca `.png` |
| Figura 12 | Variacao temporal da riqueza | Presenca/ausencia, quali + quanti | Riqueza total, riqueza nativa, riqueza nao nativa | Campanha e/ou ano hidrologico | `.xlsx` + `.png` |
| Tabela 7 | Ocorrencia absoluta e relativa das especies | Presenca/ausencia, quali + quanti | Presenca por ponto, FA, FR | P9, P8, P7, P6, P3, P1, P2, P5, P4; Jusante/Montante | `.xlsx` |
| Tabela 8 | Biometria e biomassa por especie | Base de linhas | N, B, CT min/med/max, PC min/med/max | Especie | `.xlsx` |
| Figura 13a | CPUEn montante x anos hidrologicos | Quantitativa | CPUEn | Trecho Montante, serie temporal, regressao linear | `.xlsx` + `.png` |
| Figura 13b | CPUEb montante x anos hidrologicos | Quantitativa | CPUEb | Trecho Montante, serie temporal, regressao linear | `.xlsx` + `.png` |
| Figura 13c | CPUEn jusante x anos hidrologicos | Quantitativa | CPUEn | Trecho Jusante, serie temporal, regressao linear | `.xlsx` + `.png` |
| Figura 13d | CPUEb jusante x anos hidrologicos | Quantitativa | CPUEb | Trecho Jusante, serie temporal, regressao linear | `.xlsx` + `.png` |
| Figura 14 | CPUE percentual por migracao e origem | Quantitativa | CPUEn (%) e CPUEb (%) | Migradoras nativas, migradoras nao nativas, nao migradoras nativas, nao migradoras nao nativas; 4 graficos: montante CPUEn, montante CPUEb, jusante CPUEn, jusante CPUEb | `.xlsx` + 4 `.png` |
| Figura 15 | CPUE percentual das especies nativas | Quantitativa | CPUEn (%) e CPUEb (%) | Nativas; 4 graficos: montante CPUEn, montante CPUEb, jusante CPUEn, jusante CPUEb | `.xlsx` + 4 `.png` |
| Figura 16 | Recorte dos dois ultimos anos hidrologicos | Quantitativa | CPUEn (%) e CPUEb (%) | Mesmo recorte da Figura 15, somente anos hidrologicos finais | `.xlsx` + 4 `.png` |
| Secao 6.6.3 | Variacoes temporal e espacial das CPUEs das migradoras nativas e nao nativas | Quantitativa | CPUEn (%) e CPUEb (%) | Migradoras x origem x montante/jusante x ano hidrologico | `.xlsx` + graficos |
| Secao 6.6.4 | Variacao temporal e espacial das CPUEs das ameacadas | Quantitativa | CPUEn (%) e CPUEb (%) | Ameacadas x montante/jusante x ano hidrologico | `.xlsx` + graficos |
| Figura 30 | Diversidade e equitabilidade | Quantitativa | Shannon e Pielou sobre matriz CPUEn | Montante e Jusante ao longo do monitoramento | `.xlsx` + `.png` |
| Figura 32 | Estadios reprodutivos de femeas migradoras nativas | Linhas com Sexo/EMG | Abundancia por EMG | Femeas, migradoras nativas, F1-F4, periodo completo | `.xlsx` + `.png` |
| Figura 33 | Estadios reprodutivos de femeas migradoras nao nativas | Linhas com Sexo/EMG | Abundancia por EMG | Femeas, migradoras nao nativas, F1-F4, periodo completo | `.xlsx` + `.png` |

## Regras analiticas sugeridas

## Decisoes confirmadas em 2026-06-02

- `Interesse Comercial` da Tabela 6: derivar do campo `Valor_Economico` do
  cadastro definitivo, padronizando como `Sim`/`Nao`.
- Figura 10: incluir curva observada e estimador Jackknife 1. A linha
  observada representa a media das aleatorizacoes; o Jackknife 1 representa a
  estimativa media; as faixas sombreadas representam `+/- 1 DP`.
- Figura 15: produto geral para especies nativas no periodo completo.
- Figura 16: produto complementar para condicao atual, com recorte
  `AH2324`, `AH2425` e `AH2526`.
- Series temporais: testar modelos por `Ano_Hidrologico` e por campanha
  individual. A decisao final fica condicionada a legibilidade; a tendencia
  esperada e usar `Ano_Hidrologico` como eixo principal e campanha individual
  como tabela de apoio ou grafico complementar.

### Tabela 7 - FA e FR

Pelo layout solicitado, a ocorrencia deve ser espacial:

- `FA`: numero de pontos em que a especie ocorreu.
- `FR`: `FA / 9 * 100`.
- Colunas de ponto em ordem solicitada:
  `P9`, `P8`, `P7`, `P6`, `P3`, `P1`, `P2`, `P5`, `P4`.
- Subtitulos:
  - Jusante: `P9`, `P8`, `P7`, `P6`, `P3`.
  - Montante: `P1`, `P2`, `P5`, `P4`.

### Tabela 8 - biomassa

- `N`: soma de `Numero_de_Individuos`.
- `B`: soma de `Biomassa_g_linha`.
- `CT`: usar `CT_cm`.
- `PC`: usar `PC_g` como peso individual.
- `Min`, `Med`, `Max`: calculados sobre medidas individuais registradas na
  linha.

### Figuras de CPUE percentual

Quando o produto pedir `CPUEn (%)` ou `CPUEb (%)`, regra sugerida:

- Calcular CPUE absoluta por grupo/ano/trecho.
- Converter para percentual dentro de cada combinacao `Trecho + Ano
  hidrologico + metrica`.
- Formula: `CPUE_percentual_grupo = CPUE_grupo / soma_CPUE_dos_grupos * 100`.

### Regressao temporal

- Eixo X analitico: ordem numerica do ano hidrologico ou ano decimal da
  campanha.
- Eixo X visual: rotulo de ano hidrologico.
- Usar dados nao transformados.
- Reportar `a`, `b` e `R2` em tabela de apoio.

## Decisoes de layout apos revisao dos modelos

- Todos os graficos devem ser gerados em paisagem.
- A fonte deve ser aumentada ao maximo possivel sem perda de legibilidade.
- Referencia usada nos modelos revisados:
  - fonte base: `17`;
  - rotulos de eixo: `17`;
  - ticks: `13`;
  - legenda: `15`;
  - titulos internos/painel: `16`;
  - figura padrao: aproximadamente `18 x 10,2` ou `18 x 11,2` polegadas.
- O modelo por campanha individual foi reprovado como figura final.
- Campanhas individuais permanecem somente como tabela de apoio, salvo se uma
  discussao especifica exigir detalhe de pico/sazonalidade.
- Os heatmaps de especies nativas foram reprovados.
- Para especies nativas, usar graficos horizontais tipo lollipop/Top especies +
  `Outras`, inspirados nos modelos de Aimores.
- Para roscas de ordem/familia, usar cores alternadas fora da paleta azul para
  diferenciar melhor as categorias.
- Para reproducao, separar tambem Montante/Jusante.

## Modelos graficos gerados para avaliacao

Pasta:

- `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\modelos_graficos_porto_estrela_20260602`

Arquivos principais:

- `modelo_01_curva_coletor_observada_jackknife1.png`: curva do coletor com
  riqueza observada media, Jackknife 1 medio e faixas de DP para ambos, por
  permutacoes da unidade `campanha x ponto`.
- `modelo_02_riqueza_temporal_ano_hidrologico.png`: riqueza total, nativa e
  nao nativa por ano hidrologico. Modelo aprovado.
- `modelo_03_fig13_painel_cpue_absoluta_regressao_ano_hidrologico.png`: painel
  2 x 2 para `CPUEn`/`CPUEb` em Montante/Jusante, com regressao linear simples.
- `modelo_05_fig14_cpue_percentual_grupos_area_empilhada.png`: CPUE percentual
  por grupos migracao x origem, em quatro paineis.
- `modelo_06a_fig15_lollipop_especies_nativas_periodo_completo.png`: principais
  especies nativas + `Outras`, em paineis Montante/Jusante x `CPUEn`/`CPUEb`,
  no periodo completo.
- `modelo_06b_fig16_lollipop_especies_nativas_recorte_atual.png`: principais
  especies nativas + `Outras`, em paineis Montante/Jusante x `CPUEn`/`CPUEb`,
  no recorte `AH2324`, `AH2425`, `AH2526`.
- `modelo_07_fig11_rosca_ordem_familia.png`: roscas por ordem e familia, com
  cores alternadas fora da paleta azul.
- `modelo_08_fig30_diversidade_equitabilidade_ano_hidrologico.png`: Shannon e
  Pielou em dois paineis, Montante/Jusante.
- `modelo_09_fig32_33_reproducao_femeas_migradoras_emg.png`: abundancia de
  femeas migradoras por EMG, separando nativas/nao nativas e
  Montante/Jusante.

Recomendacao tecnica inicial:

- Usar `Ano_Hidrologico` como eixo principal das series temporais.
- Manter painel 2 x 2 para os pares Montante/Jusante x `CPUEn`/`CPUEb`.
- Para muitas especies, priorizar lollipop/Top especies + `Outras`, evitando
  grafico com dezenas de linhas.
- Para diversidade, manter Shannon e Pielou em paineis separados.
- Para reproducao, usar barras empilhadas por EMG e destacar `F3/F4` como
  evidencia reprodutiva forte.
- Scripts de Aimores avaliados como referencia visual/metodologica:
  `_simper_riqueza.py`, `_simper_barramento.py` e rotinas de Jackknife.
  A abordagem e util, mas nao exige novas bibliotecas alem de `pandas`,
  `numpy` e `matplotlib`.

## Resultados oficiais gerados

Pasta:

- `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_20260602`

Decisao operacional:

- Saida em pasta unica, sem subpastas numeradas, para facilitar visualizacao.
- Modularidade mantida no script `scripts/gerar_resultados_porto_estrela_ictio.py`.
- Para rerodar um bloco especifico, usar `--only`.
  Exemplo: `python scripts\gerar_resultados_porto_estrela_ictio.py --only 10,13,14`.
- Manifestos gerados:
  - `manifesto_resultados_ictiofauna_porto_estrela.xlsx`;
  - `manifesto_resultados_ictiofauna_porto_estrela.md`.
