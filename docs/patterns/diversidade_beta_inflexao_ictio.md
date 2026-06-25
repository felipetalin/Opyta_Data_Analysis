# Diversidade Beta E Pontos De Inflexao Em Ictiofauna

## Status

Metodo extraido do lastro BIOPOR001/Porto Estrela. Usar como referencia
metodologica e tecnica antes de aplicar em novos projetos. Ainda nao e um
padrao promovido para o pipeline central.

## Fontes

- `docs/PORTO_ESTRELA_ANALISES_EXPLORATORIAS_BETA_INFLEXAO_20260603.md`
- `scripts/projects/porto_estrela/gerar_exploratorias_porto_estrela_ictio.py`
- `scripts/projects/porto_estrela/gerar_resultados_porto_estrela_ictio.py`
- `scripts/projects/porto_estrela/gerar_relatorio_html_porto_estrela_ictio.py`
- `outputs/_project_scripts/BIOPOR001__monitoramento_da_ictiofauna_da_uhe_porto_estrela`

## Quando Usar

Usar em monitoramentos de ictiofauna com serie temporal longa, pontos
amostrais recorrentes e pergunta ecologica ligada a diferenciacao,
homogeneizacao, substituicao de especies ou mudanca de tendencia temporal.

Casos naturais:

- comparar composicao entre trechos, como montante e jusante, por ano
  hidrologico;
- avaliar mudanca composicional entre anos hidrologicos consecutivos;
- identificar pontos ou trechos com maior contribuicao para a beta diversidade;
- triar pontos de inflexao em series de CPUEn ou CPUEb;
- apoiar interpretacao de efeitos de barramento, reservatorio ou alteracao
  ambiental, sem tratar a analise como prova causal isolada.

Evitar quando a serie temporal e curta. Para regressao segmentada, o lastro
Porto Estrela usou minimo de 5 anos por segmento; na pratica, isso exige pelo
menos 11 observacoes temporais validas para testar um ponto de quebra.

## Dados Minimos

A base analitica precisa estar taxonomicamente harmonizada e conter, idealmente:

- `ano_hidrologico`;
- `Rotulo_AH` ou rotulo equivalente;
- `Ordem_AH`, com ordem temporal numerica;
- `Trecho`, por exemplo Montante/Jusante;
- `Ponto`;
- `Nome_Cientifico`;
- `Numero_de_Individuos`;
- `Tipo_Amostragem_Base`;
- `Captura_Real`, quando existir;
- `CPUEn_linha`;
- `CPUEb_linha`.

As matrizes devem ser preenchidas com zero para especies ausentes em uma
unidade amostral, mantendo a mesma lista de especies entre comparacoes.

## Diversidade Beta Quantitativa

### Matriz

Base usada no Porto Estrela:

- somente amostragem quantitativa;
- linhas agregadas por soma de `CPUEn_linha`;
- matriz `ano_hidrologico x Trecho x especie` para comparacao Montante x
  Jusante;
- matriz `ano_hidrologico x Ponto x especie` para LCBD.

### Bray-Curtis

Usado sobre abundancia padronizada (`CPUEn_linha`).

Formula operacional:

`BrayCurtis = soma(abs(x - y)) / soma(x + y)`

Tambem foi registrada a similaridade complementar:

`Similaridade_BrayCurtis = 1 - BrayCurtis`

Leitura: valores altos de Bray-Curtis indicam maior diferenca quantitativa na
composicao ou dominancia das especies entre unidades comparadas.

### Hellinger

Cada linha da matriz quantitativa e transformada por:

`Hellinger_i = sqrt(valor_i / soma_da_linha)`

A distancia entre duas linhas transformadas foi normalizada:

`Distancia_Hellinger_0_1 = norma(hx - hy) / sqrt(2)`

Leitura: reduz o peso de abundancias extremas e ajuda a interpretar diferenca
composicional em matrizes com muitos zeros.

## Diversidade Beta Presenca-Ausencia

### Matriz

Base usada:

- capturas reais qualitativas e quantitativas;
- presenca registrada quando a especie tem captura real ou individuos
  observados;
- matriz binaria `unidade x especie`.

Para duas unidades comparadas:

- `a`: especies compartilhadas;
- `b`: especies exclusivas da unidade x;
- `c`: especies exclusivas da unidade y.

### Componentes

Beta-Sorensen:

`beta_sor = (b + c) / (2a + b + c)`

Turnover, ou substituicao:

`beta_sim = min(b, c) / (a + min(b, c))`

Nestedness, ou aninhamento:

`beta_nes = beta_sor - beta_sim`

No script consolidado, `beta_nes` e limitado a zero quando a diferenca
numerica gera valor negativo residual.

Leitura:

- `beta_sor`: dissimilaridade total de presenca-ausencia;
- `beta_sim`: substituicao de especies entre unidades;
- `beta_nes`: diferenca associada a perda, ganho ou subconjunto de riqueza.

## Comparacoes Beta Recomendadas

### Montante x Jusante Por Ano Hidrologico

Para cada ano hidrologico:

1. montar matriz quantitativa por trecho e especie;
2. calcular Bray-Curtis e Hellinger sobre `CPUEn_linha`;
3. montar matriz presenca-ausencia por trecho e especie;
4. calcular beta-Sorensen, turnover e nestedness;
5. registrar riqueza de cada trecho e especies compartilhadas/exclusivas.

Essa leitura separa diferenca de abundancia padronizada de diferenca na lista
de especies.

### Anos Consecutivos Por Trecho

Para cada trecho:

1. ordenar os anos por `Ordem_AH`;
2. comparar cada ano com o ano anterior;
3. calcular Bray-Curtis, Hellinger e componentes presenca-ausencia;
4. interpretar picos como momentos de maior mudanca composicional.

Essa leitura e util para relatorios temporais porque mostra quando a comunidade
mudou mais, sem misturar montante e jusante.

## LCBD E Beta Espacial

LCBD foi usado como contribuicao local para beta diversidade.

Base:

- amostragem quantitativa;
- matriz `Ponto x especie` dentro de cada ano hidrologico;
- valores de `CPUEn_linha` agregados por soma;
- transformacao de Hellinger por linha.

Procedimento:

1. para cada ano hidrologico, montar a matriz ponto x especie;
2. exigir pelo menos 3 pontos no ano;
3. transformar por Hellinger;
4. calcular o centroide da matriz transformada;
5. calcular a soma de quadrados de cada ponto em relacao ao centroide;
6. calcular `SS_total`;
7. calcular `LCBD = SS_ponto / SS_total`;
8. calcular `Beta_Total_Hellinger = SS_total / (numero_de_pontos - 1)`;
9. agregar `LCBD_Medio` e `LCBD_Total` por trecho quando necessario.

Leitura:

- LCBD alto indica ponto mais singular na composicao daquele ano;
- beta total alta indica maior heterogeneidade espacial da comunidade naquele
  ano;
- LCBD deve ser interpretado junto com riqueza, abundancia e qualidade do
  esforco amostral.

## PCoA Como Apoio

O Porto Estrela tambem usou ordenacao PCoA exploratoria com Bray-Curtis sobre
`CPUEn_linha` em matriz `ano_hidrologico x trecho`.

Uso recomendado:

- apoiar leitura visual de trajetorias temporais;
- mostrar aproximacao ou afastamento entre trechos;
- nao substituir os indices beta e suas tabelas.

## Pontos De Inflexao

Ha duas camadas no lastro Porto Estrela: uma exploratoria por BIC e uma mais
robusta com teste por permutacao, intervalo por bootstrap e correcao
Benjamini-Hochberg.

### Camada 1: Triagem Exploratoria Por BIC

Usar para explorar muitas series rapidamente.

Series avaliadas:

- `CPUEn` e `CPUEb`;
- total por trecho;
- categorias ecologicas, como migracao x origem;
- ameacadas e nao ameacadas, quando houver classificacao.

Modelo nulo:

`y = b0 + b1*x`

Modelo segmentado com termo hinge:

`y = b0 + b1*x + b2*max(0, x - bp)`

Onde:

- `x` e a ordem temporal (`Ordem_AH`);
- `y` e a metrica avaliada (`CPUEn` ou `CPUEb`);
- `bp` e o ponto candidato de quebra;
- `b1` e a inclinacao antes da quebra;
- `b1 + b2` e a inclinacao apos a quebra.

Regras operacionais:

- remover valores ausentes;
- exigir serie nao constante;
- exigir minimo de 5 anos por segmento;
- testar candidatos excluindo os 5 primeiros e os 5 ultimos anos;
- escolher o ponto com menor BIC do modelo segmentado;
- calcular `Delta_BIC = BIC_linear - BIC_segmentado`;
- marcar `Melhora_Forte = True` quando `Delta_BIC > 2`;
- traduzir o ponto numerico para o ano hidrologico mais proximo.

Saidas recomendadas:

- ponto de quebra em `Ordem_AH`;
- ano hidrologico correspondente;
- SSE linear e segmentado;
- BIC linear e segmentado;
- `Delta_BIC`;
- inclinacao antes e depois da quebra;
- indicador de melhora forte.

Limite: esta camada e triagem. Ela nao deve entrar sozinha como conclusao
oficial sem validacao ecologica e estatistica.

### Camada 2: Teste Segmentado Com Permutacao E BH

Usar quando a inflexao for candidata a entrar em relatorio ou decisao tecnica.

Modelo nulo:

`CPUE ~ Ordem_AH`

Modelo alternativo:

`CPUE ~ Ordem_AH + max(0, Ordem_AH - bp)`

Escolha do ponto:

- testar os pontos candidatos respeitando minimo de 5 anos por segmento;
- escolher o ponto de quebra que minimiza o SSE do modelo segmentado.

Estatistica:

- calcular `F_sup` comparando reducao de SSE do modelo linear para o
  segmentado;
- usar o maior suporte entre os pontos candidatos.

Teste:

- permutar residuos do modelo linear nulo;
- reconstruir series sob a hipotese nula;
- recalcular a melhor segmentacao em cada permutacao;
- calcular `p_perm` pela proporcao de permutacoes com estatistica igual ou
  maior que a observada.

Parametros usados no Porto Estrela:

- `n_perm = 999`;
- `n_boot = 499`;
- `min_size = 5`;
- semente `20260603`.

Intervalo do ponto de quebra:

- usar bootstrap dos residuos do modelo segmentado;
- recalcular o melhor ponto de quebra;
- registrar percentis 2,5% e 97,5%.

Multiplicidade:

- ajustar `p_perm` por Benjamini-Hochberg entre as series testadas;
- exibir a linha vertical de inflexao apenas quando `p_BH <= 0,05`.

Saidas recomendadas:

- `Breakpoint_Ordem_AH`;
- intervalo 95% do breakpoint em ordem temporal;
- ano hidrologico mais proximo;
- `F_sup`;
- `p_perm`;
- `p_BH`;
- `Delta_BIC`;
- `SSE_Linear` e `SSE_Segmentado`;
- `R2_Linear` e `R2_Segmentado`;
- `Slope_Linear`;
- `Slope_Pre`;
- `Slope_Post`;
- `Delta_Slope`;
- numero de permutacoes e bootstraps validos.

## Interpretacao Tecnica

Inflexao nao e causalidade. Ela indica que uma serie temporal foi melhor
representada por duas tendencias conectadas do que por uma tendencia linear
simples, dentro das regras de teste adotadas.

Boa pratica:

- interpretar junto com evento ambiental, hidrologia, operacao do reservatorio
  ou mudanca de esforco;
- verificar se a mudanca e coerente em `CPUEn`, `CPUEb`, riqueza e composicao;
- diferenciar mudanca de abundancia de mudanca taxonomica;
- reportar a incerteza do ponto quando houver bootstrap;
- evitar destaque visual de pontos sem suporte estatistico.

## Cautelas

- Padronizacao de esforco e essencial.
- Revisao taxonomica deve estar fechada antes de calcular matrizes.
- Especies raras podem afetar presenca-ausencia e nestedness.
- Ausencia de captura nao e necessariamente ausencia ecologica.
- Mudancas de metodologia, pontos amostrais ou periodicidade devem ser
  documentadas antes da analise.
- Analise funcional nao foi replicada no Porto Estrela porque faltava matriz
  funcional/ecomorfologica completa.
- Resultados exploratorios precisam de aprovacao antes de entrar em produto
  oficial.

## Produtos Recomendados

Para cada analise, gerar tabela e figura pareadas.

Tabelas:

- `Beta_Montante_Jusante_AH`;
- `Beta_Consecutiva_Trechos`;
- `LCBD_Pontos`;
- `LCBD_Trechos_AH`;
- `PCoA_AH_Trecho`, quando usado;
- `Inflexoes_BIC_Exploratorio`, quando usado;
- `Teste_Inflexao`, quando usado no modo inferencial;
- aba `Metodo`, descrevendo parametros.

Figuras:

- beta quantitativa e presenca-ausencia Montante x Jusante por ano;
- beta temporal consecutiva por trecho;
- LCBD medio por trecho e beta total por ano;
- PCoA de ano hidrologico x trecho, quando fizer sentido;
- series temporais com ponto de inflexao apenas quando sustentado pelo criterio
  escolhido.

## Checklist Para Reuso

Antes de aplicar em outro projeto:

1. confirmar que ha serie temporal suficiente;
2. fechar taxonomia e sinonimias;
3. validar campos de esforco, CPUEn e CPUEb;
4. decidir se a analise sera exploratoria ou inferencial;
5. registrar grupos de comparacao, como trecho, ponto, campanha ou ano;
6. gerar tabelas de apoio antes dos graficos;
7. revisar picos ou quebras com interpretacao ecologica;
8. aprovar metodologia antes de incluir em relatorio final.

## Proxima Promocao Tecnica

Para virar padrao central do repositorio, este metodo ainda precisa:

- ser implementado em `src/opyta_analysis` com funcoes reutilizaveis;
- receber testes unitarios para Bray-Curtis, Hellinger, beta-Sorensen,
  turnover, nestedness, LCBD e ajuste BH;
- receber parametrizacao por cliente/projeto;
- gerar manifestos com parametros e versoes;
- ser aprovado em pelo menos um novo projeto alem do BIOPOR001.
