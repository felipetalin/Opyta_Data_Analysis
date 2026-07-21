# BRAAVG002 - Zoobentos - Consolidado 2026

Data de preparacao: 2026-07-20

## Escopo

- Projeto: `BRAAVG002`
- Grupo biologico: `Zoobentos`
- Recorte esperado: campanhas 01 a 47
- Saida final: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados bentos/Consolidado_2026`
- Configuracao: `configs/projects/braavg002_zoobentos_2026.json`

## Produtos Planejados

1. Composicao taxonomica.
2. Riqueza por ponto, campanha e ano temporal.
3. Abundancia e densidade.
4. Indices de diversidade.
5. Bioindicadores BMWP, CHOL e EPT.
6. Mini-mapas anuais com BMWP, CHOL e EPT.
7. PCoA Bray-Curtis, somente se a matriz apresentar densidade e leitura visual suficientes.

Fora do escopo atual: boxplots temporais/espaciais, NMDS e PERMANOVA.

## Checklist Pos-Migracao

Antes de gerar produtos finais, validar:

- `public.biota_analise_consolidada` contem `BRAAVG002`/`Zoobentos` para 47 campanhas.
- As campanhas estao na sequencia 01-47 e podem ser cruzadas com o padrao analitico `C001` a `C047`.
- A regra de ano temporal esta aplicada como agosto a julho.
- A regra sazonal esta aplicada como `CH = outubro a marco` e `SC = abril a setembro`.
- Pontos esperados por campanha conferidos contra a malha aprovada.
- Vigencia dos pontos aplicada: PIC-01, PIC-03 e PIC-11 descontinuados conforme regra AVG; PIC-03 com excecao em fevereiro/2026; PIC-02 realocado a partir de fevereiro/2026.
- Coordenadas analiticas conferidas para PIC-02 realocado e PIC-11.
- Esforcos de Zoobentos presentes para os pontos-campanhas efetivamente amostrados.
- Separar captura zero de ponto nao monitorado.
- Taxons sem `id_especie` ou sem correspondencia no cadastro central.
- Taxons sem ordem, familia ou menor nivel taxonomico interpretavel.
- Taxons sem `BMWP_Score`.
- Total de abundancia/densidade comparado entre tabela fonte, tabelas base e consolidada.
- CHOL e EPT conferidos por grupo taxonomico antes dos graficos.
- Tabelas de apoio salvas junto com cada figura.

## Regras Dos Bioindicadores

### CHOL

Definicao operacional:

- Chironomidae + Oligochaeta/Oligoqueta.

Saidas recomendadas:

- abundancia absoluta;
- abundancia relativa sobre o total de organismos por ponto-campanha;
- sintese por ano temporal e ponto.

Cuidados:

- CHOL nao deve ser interpretado isoladamente como indice de impacto.
- CHOL e EPT nao sao grupos complementares; os demais taxons tambem compoem a comunidade.

### EPT

Definicao operacional:

- Ephemeroptera + Plecoptera + Trichoptera.

Saidas recomendadas:

- abundancia absoluta;
- abundancia relativa sobre o total de organismos por ponto-campanha;
- riqueza de taxons EPT quando a resolucao taxonomica permitir.

Cuidados:

- Evitar comparacao percentual quando a abundancia total por ponto-campanha for muito baixa.
- Registrar filtro minimo caso seja adotado, por exemplo `N >= 10`.

### BMWP

Definicao operacional:

- Soma dos escores BMWP dos taxons/familias registrados na unidade amostral, conforme cadastro taxonomico disponivel.

Saidas recomendadas:

- escore BMWP por ponto-campanha;
- classe BMWP, se a escala de classificacao estiver definida;
- sintese por ano temporal e ponto.

Cuidados:

- Taxons sem familia ou sem `BMWP_Score` devem ser auditados antes do calculo final.
- Nao atribuir escore por inferencia sem registro na matriz de decisao.
- Se a identificacao estiver acima de familia, registrar como nao pontuado ate decisao tecnica.

## Decisoes Visuais Iniciais

- Usar o padrao visual AVG ja aplicado na ictiofauna.
- Para mini-mapas, priorizar painel anual e legibilidade de rótulos.
- Delimitar areas de controle 01 e 02 quando houver mapa.
- Usar escala comum dentro de cada indicador para comparacao temporal.
- Evitar boxplots neste consolidado.
- PCoA deve ser exploratoria e so entra no pacote final se separar grupos de forma interpretavel.

## Pendencias Para Amanha

- Receber/confirmar a base migrada de 47 campanhas.
- Rodar auditoria pos-migracao.
- Decidir escala/classificacao BMWP a ser usada no relatorio.
- Confirmar se EPT e CHOL entram como absoluto, relativo ou ambos nos produtos finais.
- Validar se a PCoA tem suporte analitico suficiente.
