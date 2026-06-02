# Porto Estrela - referencia de layout grafico baseada na Ducal

Registro criado em 2026-06-02 para orientar os produtos graficos de
ictiofauna de Porto Estrela a partir do padrao visual aplicado na Ducal.

## Fontes avaliadas

- Configuracao ativa da Ducal: `configs/clients/ducgeo001.json`.
- Tema base: `configs/theme_default.json`.
- Padrao institucional: `docs/PADRAO_GOLD_APROVADO.md`.
- Saidas reais Ducal:
  - `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Ducal\Produtos\Resultados\Campanha 05\Ictiofauna`
  - `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Ducal\Produtos\Resultados\Campanha 05\Zoobentos`
- Reprodutores:
  - `outputs/_project_scripts/ducal/ictiofauna/_run_this_analysis.py`
  - `outputs/_project_scripts/ducal/zoobentos/_run_this_analysis.py`

## Tema efetivamente usado na Ducal

O tema ativo e o resultado de `theme_default.json` com override do cliente
`ducgeo001`.

Valores principais:

- Familia tipografica: `Arial`.
- Fonte base: `17`.
- Fonte de rotulos dos eixos: `12`.
- Fonte de anotacoes: `12`.
- Fonte de legenda: `17`.
- Cor primaria: `#002060`.
- Cor secundaria: `#5B9BD5`.
- Cor de destaque: `#1F4E79`.
- Paleta/gradiente: de `#002060` ate `#DBE5F1`.
- Tamanho padrao de figura: `16 x 10` polegadas.
- DPI: `600`.
- Fundo: branco.
- Grade: apenas eixo Y.
- Cor da grade: `#D9D9D9`.
- Transparencia da grade: `0.25`.
- Bordas dos eixos: pretas, com largura `1.2`.
- Borda das barras: preta.
- Legenda: superior centralizada, sem moldura.
- Numero maximo de colunas da legenda: `5`.

Observacao: o documento Gold historico cita fonte base menor, mas a Ducal foi
avaliada pelo tema efetivamente aplicado e pelos PNGs gerados. Para Porto
Estrela, usar a referencia efetiva Ducal.

## Padrao visual observado nos PNGs

Caracteristicas consistentes:

- Graficos horizontais amplos.
- Sem titulo no corpo do grafico; titulo/identificacao fica no arquivo e no
  relatorio.
- Legenda grande no topo.
- Azul escuro como cor principal.
- Gradiente azul para multiplas campanhas.
- Barras com contorno preto.
- Valores anotados sobre as barras quando a leitura direta e importante.
- Rotulos do eixo X inclinados quando ha muitos pontos/campanhas.
- Grade horizontal leve, suficiente para leitura sem poluir o grafico.
- Fundo branco, pronto para insercao em relatorio tecnico.

Dimensoes observadas em PNGs de Ictiofauna Ducal:

- `02_grafico_riqueza_por_ponto_ictiofauna.png`: `9414 x 5566` px, `600 dpi`.
- `06_grafico_cpuen_por_ponto_ictiofauna.png`: `9414 x 5566` px, `600 dpi`.
- `10_grafico_diversidade_alfa_ictiofauna.png`: `9414 x 5206` px, `600 dpi`.
- `12_curva_suficiencia_amostral_ictiofauna.png`: `9414 x 5326` px, `600 dpi`.

## Regra de saida Excel + grafico

Toda saida grafica deve ter uma base tabular correspondente em Excel, salvo
casos muito especificos em que o grafico e apenas ilustrativo.

Padrao observado:

- Composicao/distribuicao: apenas tabela `.xlsx` quando nao ha grafico.
- Riqueza por ponto: `*_df_*.xlsx` + `*_grafico_*.png`.
- Abundancia por ponto: `*_df_*.xlsx` + `*_grafico_*.png`.
- CPUE por ponto: `*_df_*.xlsx` + graficos separados de `CPUEn` e `CPUEb`.
- CPUE por especie: tabelas separadas de `CPUEn` e `CPUEb` + graficos
  correspondentes.
- Diversidade: tabela `.xlsx` + grafico `.png`.
- Similaridade: matriz/complementos `.xlsx` + dendrograma `.png`.
- Curva de suficiencia: dados da curva `.xlsx` + curva `.png`.

Para Porto Estrela, cada produto final deve registrar:

- tabela usada para o grafico;
- grafico em PNG;
- nome de arquivo com prefixo numerico do bloco/resultado;
- mesmo recorte analitico entre Excel e PNG.

## Regras recomendadas para Porto Estrela

- Criar um cliente/configuracao Porto Estrela usando Ducal como referencia
  visual.
- Manter a paleta azul Ducal para os graficos principais.
- Usar `CPUEn` como metrica central de abundancia padronizada nos graficos
  estatisticos e temporais.
- Usar `CPUEb` em produtos pareados quando a pergunta envolver biomassa.
- Evitar titulos internos nos graficos; o relatorio deve titular a figura.
- Exportar PNGs em `600 dpi`.
- Validar estilo com `validate_axes_style` quando o grafico usar o pipeline
  central.
- Em graficos com muitas campanhas de Porto Estrela, avaliar:
  - reduzir rotulos por facet/ano hidrologico;
  - usar linhas temporais em vez de barras agrupadas;
  - usar paleta azul sequencial apenas quando a quantidade de series for
    visualmente legivel.

## Pontos de atencao para Porto Estrela

Porto Estrela tem 90 campanhas, muito mais do que a Ducal. Portanto, nao e
prudente replicar diretamente graficos de barras agrupadas por campanha quando
houver muitas series. O padrao visual deve ser o mesmo, mas a estrutura grafica
precisa respeitar legibilidade:

- series temporais para campanhas/anos hidrologicos;
- barras agrupadas apenas para poucos grupos;
- heatmaps ou matrizes quando houver muitos pontos/campanhas/especies;
- facetas por ano hidrologico ou por trecho quando necessario.

O criterio e manter identidade visual Ducal/Opyta, sem sacrificar leitura.
