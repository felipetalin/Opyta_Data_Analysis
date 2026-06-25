# Caracterizacao de especies - Porto Estrela

Base aprovada para uso em 2026-06-02.

- Especies com resultados migrados: 61
- Especies no cadastro definitivo: 61
- Migradoras derivadas: 12
- Nao migradoras derivadas: 49
- Nativas: 40
- Nao nativas: 21
- Ameacadas de extincao: 4

Observacao: apos a correcao de `Brycon dulcis` e `Megaleporinus macrocephalus`,
o total correto e 12 migradoras e 49 nao migradoras, fechando 61 especies.

## Entendimento-guia do projeto

Este arquivo passa a ser o lastro analitico inicial do projeto Porto Estrela
para ictiofauna. A base de especies esta aprovada para uso e deve orientar os
scripts e validacoes seguintes.

Valores aprovados da base:

- Especies com resultados migrados: 61
- Especies no cadastro definitivo: 61
- Migradoras derivadas: 12
- Nao migradoras derivadas: 49
- Nativas: 40
- Nao nativas: 21
- Ameacadas de extincao: 4

## Separacao qualitativa e quantitativa

Existem dois tipos de amostragem que nao devem ser tratados como equivalentes
em todas as analises.

A amostragem qualitativa entra principalmente nas analises de composicao,
ocorrencia, curva do coletor, suficiencia amostral e outras leituras baseadas
em presenca/ausencia. Ela ajuda a representar a composicao da ictiofauna, mas
nao deve ser o motor das analises quantitativas ou estatisticas baseadas em
abundancia padronizada.

A amostragem quantitativa sera o eixo principal do relatorio analitico. As
quantidades observadas devem ser tratadas com padronizacao por esforco,
especialmente nas analises estatisticas, series temporais, diversidade baseada
em abundancia, similaridade e comparacoes entre campanhas, pontos, trechos e
anos hidrologicos.

## Regra oficial de CPUE para Porto Estrela

Para Porto Estrela, o esforco esta disponivel na linha analitica. Portanto, a
regra oficial sera calcular CPUE primeiro por linha quantitativa e depois
agregar conforme a pergunta da analise.

Formulas:

- `CPUEn_linha = Numero_de_Individuos / Esforco * 100`
- `CPUEb_linha = Biomassa_g / Esforco * 100`

Onde:

- `CPUEn` representa abundancia padronizada por esforco.
- `CPUEb` representa biomassa padronizada por esforco.
- `Esforco` e o valor da linha, vindo da aba/tabela de metadados de esforco.
- O fator `100` padroniza o resultado para a unidade comparavel do relatorio.

`CPUEn` e a metrica central de abundancia padronizada do projeto. Ela deve
orientar as analises estatisticas, diversidade quantitativa, similaridade e
series temporais de abundancia.

Apos o calculo por linha, as agregacoes devem ser feitas por soma de CPUE,
conforme o recorte:

- por campanha;
- por ano hidrologico;
- por ponto;
- por trecho montante/jusante;
- por especie;
- por grupo ecologico, como migradoras, nativas e ameacadas.

## Aprendizado acumulado dos scripts

O aprendizado dos scripts anteriores confirma tres cuidados importantes:

- Scripts de ictiofauna ja usam `CPUEn = contagem / esforco * 100` e
  `CPUEb = biomassa / esforco * 100` como memoria operacional.
- Para diversidade e similaridade quantitativas, a matriz-base deve ser
  construida com `CPUEn`, nao com dados qualitativos.
- Pontos quantitativos com captura zero podem entrar em graficos de riqueza,
  abundancia e CPUE por ponto, mas linhas auxiliares de zero nao devem entrar
  em composicao, taxonomia, curvas ou analises comunitarias como se fossem
  registros reais de especie.

Para Porto Estrela, sempre que houver conflito entre um script antigo que usa
esforco total por ponto e a regra deste guia, prevalece a regra por linha:
`valor / esforco da linha * 100`.

## Observacoes para validacao futura

- Confirmar se `Biomassa_g` esta representando biomassa total da linha. Caso
  represente peso individual ou peso medio, a `CPUEb` devera usar a biomassa
  total calculada antes da padronizacao.
- Manter `tipo_amostragem` explicito em todos os produtos intermediarios.
- Nao misturar qualitativo e quantitativo em estatisticas de abundancia.
- Para presenca/ausencia, usar ocorrencia real de especie, nao CPUE.

## Regra reprodutiva

A analise reprodutiva usa as colunas `Sexo` e `EMG`, com classificacao
macroscopica baseada em Bazzoli (2003):

- `F1`/`M1`: repouso.
- `F2`/`M2`: maturacao inicial.
- `F3`/`M3`: maturacao avancada/maduro.
- `F4`/`M4`: desovado/esgotado.

Para o relatorio, a evidencia reprodutiva forte fica definida como:
`F3`, `M3`, `F4` e `M4`.

A metrica principal sera a abundancia de individuos por EMG, com recortes por
especie, ponto, campanha, ano hidrologico, trecho e grupos ecologicos. O foco
principal sera em especies migradoras e/ou ameacadas, mantendo uma visao
complementar para todas as especies com EMG informado.
