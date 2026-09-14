# BRAAEG001 - Ictiofauna - Layout Biota - Revisao R02

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- operacao de origem: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- revisao: `R02`
- estado atual: `validating_revision`
- solicitada em: 2026-08-07
- atualizada em: 2026-08-07
- proxima acao: revisao visual/metodologica do usuario sobre as figuras e planilhas de CPUE por especie corrigidas.

## Escopo

- solicitacao do usuario: avaliar e corrigir Ictiofauna por estar fora do layout dos demais temas, sem alterar dados.
- tipo principal: `analysis`
- tipo secundario: `layout`
- impacto: `R2` restrito aos produtos derivados de CPUE por especie; sem alteracao de banco.
- produtos alvo: figuras `02`, `03`, `06`, `07`, `08`, `09`, `08B`, `09B` e `10`, com planilhas `08`, `09`, `08B` e `09B` em `resultados/migracao_biota/ictiofauna`.
- fora do escopo: banco, migracao, consolidacao, taxonomia, coordenadas, similaridade, curva de suficiencia e manifesto.

## Linha De Base

- pasta: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota/ictiofauna`
- linha de base visual: pacote Ictiofauna R01 em A4 paisagem, com barras sobrepostas por campanha em um unico eixo.
- referencia de layout: pacotes finais de Fitoplancton, Zooplancton e Zoobentos, com A4 paisagem e subpaineis por campanha/estacao.

## Alteracoes Executadas

| Produto | Antes | Depois |
| --- | --- | --- |
| `02_grafico_riqueza_por_ponto_ictiofauna.png` | Campanhas sobrepostas no mesmo eixo | Dois subpaineis: `C01-Chuva` e `C02-Seca` |
| `03_grafico_abundancia_por_ponto_ictiofauna.png` | Campanhas sobrepostas no mesmo eixo | Dois subpaineis por campanha |
| `06_grafico_cpuen_por_ponto_ictiofauna.png` | Campanhas sobrepostas no mesmo eixo | Dois subpaineis por campanha |
| `07_grafico_cpueb_por_ponto_ictiofauna.png` | Campanhas sobrepostas no mesmo eixo | Dois subpaineis por campanha |
| `08_df_cpuen_por_especie_ictiofauna.xlsx` e PNG | Barras horizontais sobrepostas por campanha; valores inflados por soma de CPUEs pontuais | CPUEn por especie/campanha recalculada como individuos da especie / esforco total da campanha x 100; dois subpaineis por campanha |
| `09_df_cpueb_por_especie_ictiofauna.xlsx` e PNG | Barras horizontais sobrepostas por campanha; valores inflados por soma de CPUEs pontuais | CPUEb por especie/campanha recalculada como biomassa da especie / esforco total da campanha x 100; dois subpaineis por campanha |
| `08B_df_cpuen_por_especie_ponto_ictiofauna.xlsx` e PNG | Matriz por ponto baseada em denominador inconsistente | CPUEn por especie/ponto recalculada com esforco total do ponto, incluindo esforcos quantitativos sem captura |
| `09B_df_cpueb_por_especie_ponto_ictiofauna.xlsx` e PNG | Matriz por ponto baseada em denominador inconsistente | CPUEb por especie/ponto recalculada com esforco total do ponto, incluindo esforcos quantitativos sem captura |
| `10_grafico_diversidade_alfa_ictiofauna.png` | Um painel com separador vertical e linhas gerais por campanha | Dois subpaineis ponto x campanha, sem misturar linhas `Geral` no eixo de pontos |

## Execucao

- script reprodutor: `scripts/projects/braaeg001/regerar_layout_ictiofauna_biota_r02.py`
- fonte usada: planilha linha-a-linha validada `lastros_migracao/Resultados_Migracao _Ictio.xlsx`.
- arquivos de dados alterados: `08_df_cpuen_por_especie_ictiofauna.xlsx`, `09_df_cpueb_por_especie_ictiofauna.xlsx`, `08B_df_cpuen_por_especie_ponto_ictiofauna.xlsx` e `09B_df_cpueb_por_especie_ponto_ictiofauna.xlsx`.
- banco alterado: nao.

## Validacao

- execucao do script: concluida sem erro.
- dimensao dos PNGs regenerados: `7014 x 4962 px`.
- tamanho de pagina: A4 paisagem, 600 dpi.
- validacao numerica:
  - esforco total por campanha: `1227 m2/100` em C01 e `1227 m2/100` em C02;
  - exemplo CPUEn corrigida: `Phalloceros uai` em C01 = `34 / 1227 * 100 = 2,77`, substituindo o valor inflado `170`;
  - exemplo CPUEb corrigida: `Psalidodon rivularis` em C02 = `6 / 1227 * 100 = 0,49`, substituindo o valor inflado `600`.
- validacao visual executada:
  - `02`: subpaineis por campanha, rotulos inteiros e sem sobreposicao;
  - `08`: especies em italico, eixo `Espécie` legivel e nomes completos;
  - `10`: diversidade em ponto x campanha, sem agregados `Geral` no eixo.

## Gate R

- status: `awaiting_revision_approval`
- pendencia: aprovacao visual/metodologica do usuario sobre a R02 corrigida.
