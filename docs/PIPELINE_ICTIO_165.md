# Pipeline Ictiofauna — Projeto 165 (ITAGUA001 — Guanhães Energia)

## Resumo
Pipeline ecológico para 4 PCHs da Guanhães Energia (Jacaré, Senhora do Porto,
Dores de Guanhães, Fortuna II) avaliando estabilização da ictiofauna após
formação dos reservatórios (corte Pré/Pós = 2017-07-01).

## Scripts
| Script | Função |
|--------|--------|
| `scripts/run_ictio_pipeline_165.py` | Pipeline analítico completo (blocos 0–7 + cascata + conclusão). |
| `scripts/gerar_relatorio_ictio_165.py` | Gera relatório HTML consolidado portável (imagens base64). |

## Hidrografia (CRÍTICO)
- **Rio Guanhães (cascata, montante → jusante):** Jacaré (1) → Senhora do Porto (2) → Dores de Guanhães (3).
- **Rio Corrente Grande (isolado, referência regional):** Fortuna II.
- Constante: `BACIA_EMP = {emp: {"rio", "posicao", "em_cascata"}}` em [run_ictio_pipeline_165.py](../scripts/run_ictio_pipeline_165.py).

## Arquitetura de blocos
| Bloco | Função no script | Saída |
|-------|------------------|-------|
| 0 | `bloco_0_suficiencia` | Mao Tau + Chao2 (unidade = campanha × ponto). |
| 1 | `bloco_1_alfa` | S, H', Simpson, Pielou, CPUEn, CPUEb. |
| 2 | `bloco_2_tendencia` | Regressão linear ano-a-ano + comparação Pré×Pós. |
| 3 | `bloco_3_estrutura` | Bray-Curtis + PCoA + dendrograma + heatmap. |
| 4 | `bloco_4_anosim_permanova` | ANOSIM + PERMANOVA (999 perms, manual). |
| 5 | `bloco_5_beta_temporal` | β-Sorensen + decomposição Baselga (turnover + nestedness). |
| 5b | `bloco_5b_legendre_its` | β-Legendre (Hellinger) por campanha + LCBD + ITS (a+b·t+δ·I+τ·t·I). |
| 6 | `bloco_6_sintese` | Síntese textual. |
| 7 | `bloco_7_estabilidade` | Score objetivo 0–6 (C1–C6). |
| ⋆ | `painel_comparativo` | Painel 2×3 entre empreendimentos. |
| ⋆ | `analise_cascata` | Ganassin et al. 2021 — gradiente + nestedness assimétrico. |
| ⋆ | `conclusao_estabilidade` | Tabela consolidada + parecer técnico. |

## Score de estabilidade (critérios C1–C6, 0–6)
1. **C1** — Suficiência amostral Pós (Chao2) ≥ 0,85.
2. **C2** — Sem tendência direcional dos alfa-índices na Pós (p > 0,05).
3. **C3** — CV temporal Pós ≤ CV Pré.
4. **C4** — Turnover (β-sim) > Nestedness (β-nes) na Pós.
5. **C5** — β-Sorensen mediana Pós ≤ 0,40.
6. **C6** — ITS sobre β-Legendre: b+τ não positivo significativo na Pós (sem diferenciação biótica em curso).

**Classes:** ≥6 = Altamente estável | 5 = Estável c/ ressalvas | 3–4 = Estabilidade parcial | ≤2 = Instável.

## Referências teóricas
- Agostinho et al. (2016) — trophic upsurge → equilíbrio dinâmico.
- Legendre & De Cáceres (2013, *Ecol. Lett.*) — β como variância + LCBD.
- Baselga (2010, *Glob. Ecol. Biogeogr.*) — decomposição turnover + nestedness.
- Ferreira et al. (2026, *Hydrobiologia* 853:3019-3033) — ITS aplicado a Serra da Mesa (15 anos) + redundância funcional.
- Ganassin et al. (2021, *Sci. Total Environ.*, DOI 10.1016/j.scitotenv.2021.146246) — cascatas neotropicais: S↓, β-Sorensen↑, nestedness jusante ⊆ montante.

## Outputs (estrutura)
```
<OUTPUT_BASE>/
├── _dados/df_ictio_quantitativa.xlsx
├── <Empreendimento>/
│   ├── 00_suficiencia_amostral/
│   ├── 01_diversidade_alfa/
│   ├── 02_tendencia_temporal/
│   ├── 03_estrutura_comunidade/
│   ├── 04_diferenca_periodos/
│   ├── 05_beta_temporal/    (inclui 05b β-Legendre/LCBD/ITS)
│   ├── 06_sintese/
│   └── 07_estabilidade/
├── _painel_comparativo/
├── _analise_cascata/        (Ganassin 2021)
├── _conclusao_estabilidade/
└── _relatorio_consolidado/relatorio_ictio_165.html
```

## Achados (run 2026-05-19)
| Empreendimento | Score | Classe | Bacia |
|----------------|------:|--------|-------|
| Jacaré | 3/6 | Estabilidade parcial | Guanhães (1) |
| Senhora do Porto | 3/6 | Estabilidade parcial | Guanhães (2) |
| Dores de Guanhães | 2/6 | Instável / em reorganização | Guanhães (3) |
| Fortuna II | 2/6 | Instável / em reorganização | Corrente Grande (isolado) |

**Cascata Guanhães:** nestedness jusante⊆montante = 93–100%; S e CPUEn declinam ao longo da cascata (slope negativo; ρ Spearman = –0,50; n=3 → indicativo, não teste).

## Limitações declaradas
- Análise apenas **taxonômica** — sem traits ecomorfológicos para testar redundância funcional (Ferreira et al. 2026).
- Cascata Guanhães com n=3 (Ganassin et al. usaram 7–9). Gradiente reportado como **indicativo**, não teste de hipótese.
- Fortuna II não compõe a cascata (Rio Corrente Grande) — entra como referência fora-cascata.
- ANOSIM/PERMANOVA são sensíveis a heterogeneidade de dispersão.

## Como reproduzir
```powershell
& "g:\Meu Drive\Opyta\Opyta_Data_Analysis\.venv\Scripts\python.exe" -u `
  "g:\Meu Drive\Opyta\Opyta_Data_Analysis\scripts\run_ictio_pipeline_165.py" `
  2>&1 | Tee-Object -FilePath "g:\Meu Drive\Opyta\Opyta_Data_Analysis\logs\ictio_pipeline_165.log"

& "g:\Meu Drive\Opyta\Opyta_Data_Analysis\.venv\Scripts\python.exe" `
  "g:\Meu Drive\Opyta\Opyta_Data_Analysis\scripts\gerar_relatorio_ictio_165.py"
```

## Histórico
- **2026-05-18** — pipeline inicial blocos 0–7 + painel + conclusão.
- **2026-05-19** — adicionado bloco 5b (β-Legendre + LCBD + ITS, Ferreira et al. 2026), C6 no score (0–6), `analise_cascata` (Ganassin et al. 2021), correção da topologia hidrográfica (FOR isolada em Corrente Grande), gerador de relatório HTML consolidado.
