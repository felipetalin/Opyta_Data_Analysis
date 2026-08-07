# BRAAEG001 - Ictiofauna - Layout Biota - Revisao R02

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- operacao de origem: `docs/control_center/operations/BRAAEG001_BIOTA_AQUATICA_CAMPANHA_1.md`
- revisao: `R02`
- estado atual: `awaiting_revision_approval`
- solicitada em: 2026-08-07
- atualizada em: 2026-08-07
- proxima acao: revisao visual do usuario sobre as figuras de Ictiofauna ajustadas ao padrao dos demais temas de biota.

## Escopo

- solicitacao do usuario: avaliar e corrigir Ictiofauna por estar fora do layout dos demais temas, sem alterar dados.
- tipo principal: `layout`
- impacto: `R1`
- produtos alvo: figuras `02`, `03`, `06`, `07`, `08`, `09` e `10` em `resultados/migracao_biota/ictiofauna`.
- fora do escopo: dados, banco, migracao, consolidacao, taxonomia, coordenadas, metricas, similaridade, curva de suficiencia, tabelas e manifesto.

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
| `08_grafico_cpuen_por_especie_ictiofauna.png` | Barras horizontais sobrepostas por campanha | Dois subpaineis por campanha, especies em italico e nomes completos |
| `09_grafico_cpueb_por_especie_ictiofauna.png` | Barras horizontais sobrepostas por campanha | Dois subpaineis por campanha, especies em italico e nomes completos |
| `10_grafico_diversidade_alfa_ictiofauna.png` | Um painel com separador vertical e linhas gerais por campanha | Dois subpaineis ponto x campanha, sem misturar linhas `Geral` no eixo de pontos |

## Execucao

- script reprodutor: `scripts/projects/braaeg001/regerar_layout_ictiofauna_biota_r02.py`
- fonte usada: planilhas finais `.xlsx` ja existentes na pasta de Ictiofauna.
- arquivos de dados alterados: nenhum.
- banco alterado: nao.

## Validacao

- execucao do script: concluida sem erro.
- dimensao dos 7 PNGs regenerados: `7014 x 4962 px`.
- tamanho de pagina: A4 paisagem, 600 dpi.
- validacao visual executada:
  - `02`: subpaineis por campanha, rotulos inteiros e sem sobreposicao;
  - `08`: especies em italico, eixo `Especie`/`Espécie` legivel e nomes completos;
  - `10`: diversidade em ponto x campanha, sem agregados `Geral` no eixo.

## Gate R

- status: `awaiting_revision_approval`
- pendencia: aprovacao visual do usuario sobre a R02.
