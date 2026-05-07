# Padrao Gold Aprovado

Data de aprovacao: 2026-05-06
Status: Aprovado para todos os proximos grupos biologicos
Referencia de configuracao: `configs/theme_gold_approved.json`

## Objetivo
Padronizar visualmente todos os graficos dos pipelines Opyta para garantir:
- consistencia entre grupos e projetos
- legibilidade em relatorio tecnico
- reproducibilidade no runner central

## Layout
- Tamanho padrao unico para todos os graficos: `15 x 10` (horizontal)
- Legenda horizontal no topo da figura (`upper center`)
- Sem titulo no corpo do grafico; identificacao via nome do arquivo
- Eixo X e anotacoes sem sobreposicao com legenda

## Tipografia
- Familia: `Arial`
- Fonte base: `14`
- Labels de eixo: `14`
- Anotacoes de valores: `14`
- Labels de campanha: `14`
- Legenda: `13`

## Regras visuais
- Fundo: branco
- Grade: apenas eixo Y (`grid_y=true`, `grid_x=false`)
- Bordas: pretas e visiveis em todos os lados (`spine_linewidth=1.2`)
- Direcao dos ticks: `out`
- Borda de barras: preta

## Qualidade tecnica
- Exportacao em `dpi=600`
- Validacao obrigatoria via `validate_axes_style`
- Falhas de estilo devem quebrar pipeline
- Ajustes de estilo apenas no core (nao em bloco isolado)

## Paletas
- Tema base Gold com cores tecnicas para indices quando aplicavel
- Override de cliente mantido para identidade visual quando definido

## Excecoes aprovadas (registradas)
- Bloco 7, Grafico 05 (rosca por ordem):
	- Paleta multicolor categorial para separar melhor grupos.
	- Rotulos externos com linhas-guia suaves.
	- Anticolisao de rotulos e ocultacao de percentuais internos para fatias pequenas.
- Bloco 6, Graficos 06B e 06C (abundancia por classe):
	- Quebra controlada da paleta verde para paleta categorial de alto contraste (tab10).
	- Motivo: melhorar detectabilidade visual entre classes.

## Criterio analitico atualizado
- Bloco 10 (curva de suficiencia amostral):
	- Unidade amostral contabilizada por `campanha + ponto`.
	- Exemplo: 25 amostras na campanha 1 e 26 na campanha 2 resultam em total 51.
	- Regra aplicada no identificador de amostra do bloco para evitar fusao indevida por ponto repetido entre campanhas.

## Aplicacao nos proximos grupos
Ao iniciar FITO, ZOO e ICTIO:
1. Reusar este mesmo tema como baseline.
2. Nao criar excecoes por bloco sem aprovacao explicita e registro no journal + documento Gold.
3. Ajustar apenas semantica de dados e calculos.
4. Manter validacao de estilo ativa em todos os graficos.
