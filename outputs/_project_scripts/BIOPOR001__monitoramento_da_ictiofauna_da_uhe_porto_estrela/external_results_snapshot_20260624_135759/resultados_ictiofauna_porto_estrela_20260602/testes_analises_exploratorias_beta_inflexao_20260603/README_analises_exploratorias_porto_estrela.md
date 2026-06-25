# Porto Estrela - testes exploratórios beta e inflexão

Bancada separada do escopo oficial, criada para avaliar melhorias analíticas.

## Referências metodológicas incorporadas

- Ferreira et al. (2026, Hydrobiologia): diversidade beta taxonômica temporal, matriz sítios x espécies, transformação de Hellinger, interpretação de diferenciação/homogeneização biótica e LCBD.
- Baselga (2010): decomposição de beta diversidade presença-ausência em turnover e nestedness.
- Aimorés 2026: uso prático de Bray-Curtis, PCoA, SIMPER/riqueza e leitura temporal de similaridade.

## Leituras rápidas dos dados gerados

- Anos hidrológicos avaliados: 23.
- Bray-Curtis CPUEn Montante x Jusante: mediana 0.592, mínimo 0.196, máximo 0.833.
- β-Sørensen Montante x Jusante: mediana 0.250.
- Inflexões com melhora forte de BIC: 16 séries.

## Arquivos principais

- `exploratoria_01_beta_montante_jusante.png`
- `exploratoria_02_beta_temporal_consecutiva_trechos.png`
- `exploratoria_03_lcbd_beta_espacial_trechos.png`
- `exploratoria_04_pcoa_ah_trecho_bray_curtis.png`
- `exploratoria_05_inflexao_cpuen_migracao_origem.png`
- `exploratoria_06_inflexao_cpueb_migracao_origem.png`
- `exploratoria_06_inflexao_cpueb_migracao_origem_v2_regressao_fracionada_azul.png`
- `exploratoria_06_inflexao_cpueb_migracao_origem_v3_sem_tendencia_azul.png`
- `exploratoria_07_inflexao_ameacadas_cpuen_cpueb.png`
- `exploratoria_08_delta_especies_pre_pos_inflexao.png`
- `exploratoria_09_fig13_cpue_total_com_inflexoes.png`
- `exploratoria_10_beta_pa_componentes_trechos_comparativo_azul.png`
- `exploratoria_11_beta_pa_componentes_por_area_azul.png`

## Cautelas

- As análises são exploratórias e ainda não fazem parte do escopo oficial.
- A análise funcional do artigo não foi replicada porque o cadastro atual não possui matriz funcional/ecomorfológica completa.
- Pontos de inflexão são triagem visual/estatística simples por regressão segmentada contínua e BIC; precisam de validação ecológica antes de entrar em relatório.
