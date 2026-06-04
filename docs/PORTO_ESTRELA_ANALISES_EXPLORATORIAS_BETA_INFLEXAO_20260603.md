# Porto Estrela - analises exploratorias beta e inflexao

Registro criado para testar melhorias analiticas fora do escopo oficial inicial
do relatorio de ictiofauna.

## Pasta de teste

`G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\resultados_ictiofauna_porto_estrela_20260602\testes_analises_exploratorias_beta_inflexao_20260603`

## Referencias consultadas

- `c:\Users\felip\OneDrive\Area de Trabalho\s10750-026-06118-x.pdf`
  - Ferreira et al. (2026), Hydrobiologia.
  - Tema: efeito de barramento sobre diversidade beta taxonomica e funcional
    de peixes em reservatorio neotropical.
  - Aprendizado util: matriz sitios x especies por evento temporal,
    transformacao de Hellinger, diversidade beta espacial ao longo do tempo,
    LCBD como contribuicao local para beta diversidade e leitura ecologica de
    diferenciacao ou homogeneizacao biotica.
- `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Terrima\Aimores\relatorio consolidado\2026\Planilha\Planilha revisao monitoramento\relatorio_ictio_165.html`
  - Aprendizado util: uso operacional de Bray-Curtis, PCoA, SIMPER/riqueza,
    beta-Sorensen, turnover/nestedness e score de estabilizacao.

## Script

- `scripts/gerar_exploratorias_porto_estrela_ictio.py`

O script e independente dos resultados oficiais e grava tudo em pasta propria.

## Produtos gerados

- `exploratoria_01_beta_montante_jusante.png`
  - Beta quantitativa Montante x Jusante por ano hidrologico:
    Bray-Curtis sobre CPUEn e beta Hellinger sobre CPUEn.
  - Decomposicao presenca-ausencia: beta-Sorensen, turnover e nestedness.
- `exploratoria_02_beta_temporal_consecutiva_trechos.png`
  - Mudanca ano a ano dentro de cada trecho.
  - Mostra Bray-Curtis CPUEn e beta-Sorensen entre anos hidrologicos
    consecutivos.
- `exploratoria_03_lcbd_beta_espacial_trechos.png`
  - Beta espacial taxonomica por ano hidrologico em matriz ponto x especie,
    com transformacao de Hellinger.
  - LCBD medio por trecho como proxy de unicidade composicional.
- `exploratoria_04_pcoa_ah_trecho_bray_curtis.png`
  - Ordenacao exploratoria de ano hidrologico x trecho usando Bray-Curtis
    sobre CPUEn.
- `exploratoria_05_inflexao_cpuen_migracao_origem.png`
  - Pontos de inflexao exploratorios em CPUEn por categoria migracao x origem.
- `exploratoria_06_inflexao_cpueb_migracao_origem.png`
  - Pontos de inflexao exploratorios em CPUEb por categoria migracao x origem.
- `exploratoria_07_inflexao_ameacadas_cpuen_cpueb.png`
  - Pontos de inflexao para ameacadas e nao ameacadas por trecho e metrica.
- `exploratoria_08_delta_especies_pre_pos_inflexao.png`
  - Especies que mais mudam a CPUEn media antes/depois dos pontos
    exploratorios selecionados.
- `exploratoria_09_fig13_cpue_total_com_inflexoes.png`
  - Painel 2x2 inspirado na Figura 13 oficial, com CPUE total por trecho e
    pontos de inflexao quando a regressao segmentada melhora o BIC.
- `dados_exploratorios_beta_inflexao_porto_estrela.xlsx`
  - Workbook com as tabelas de apoio de todos os graficos.
- `README_analises_exploratorias_porto_estrela.md`
  - Resumo metodologico e cautelas dentro da propria pasta de teste.

## Criterios analiticos usados

- Beta quantitativa:
  - Base: amostragem quantitativa.
  - Matriz: ano hidrologico x trecho x especie.
  - Metrica: `CPUEn_linha` agregada por soma.
  - Indices: Bray-Curtis e distancia Hellinger normalizada.
- Beta presenca-ausencia:
  - Base: capturas reais qualitativas e quantitativas.
  - Decomposicao: beta-Sorensen, turnover beta-sim e nestedness beta-nes.
- LCBD:
  - Base: amostragem quantitativa.
  - Matriz: ponto x especie por ano hidrologico.
  - Transformacao: Hellinger.
  - LCBD: contribuicao relativa de cada ponto para a soma de quadrados total.
- Inflexao:
  - Regressao segmentada continua com um ponto de quebra.
  - Escolha do ponto por menor BIC.
  - Marcacao visual apenas quando `Delta_BIC > 2`.

## Leituras preliminares

- A diferenca Montante x Jusante e mais forte em abundancia padronizada do que
  apenas na lista de especies.
- Bray-Curtis CPUEn Montante x Jusante teve mediana aproximada de `0,59`.
- Beta-Sorensen Montante x Jusante teve mediana aproximada de `0,25`.
- Nos anos recentes (`AH2324`, `AH2425`, `AH2526`), a beta espacial permanece
  relativamente alta, sugerindo diferenca composicional relevante entre pontos.
- Pontos exploratorios de inflexao mais recorrentes apareceram em torno de
  `AH0809`, `AH1213` e, para algumas series de biomassa/montante, `AH2021`.

## Cautelas

- Estes produtos nao fazem parte do escopo oficial aprovado ate validacao do
  usuario.
- A analise funcional do artigo de Ferreira et al. (2026) nao foi replicada
  porque ainda nao ha matriz funcional/ecomorfologica completa no cadastro.
- Os pontos de inflexao sao triagem exploratoria e precisam de interpretacao
  ecologica antes de qualquer uso em relatorio.
