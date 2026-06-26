# Grupos Funcionais Sentinelas Para Ictiofauna

Padrao exploratorio aprovado no projeto `GEOARC001` para complementar a leitura
taxonomica com interpretacao funcional da assembleia de ictiofauna.

## Objetivo

Usar atributos ecologicos simples para responder nao apenas quais especies
mudaram, mas quais funcoes ecologicas aparecem, desaparecem ou se concentram no
monitoramento.

O foco nao e criar um novo indice composto. O foco e traduzir a composicao
funcional em figuras rastreaveis, com dados de apoio e criterios claros.

## Grupos Sentinelas

Os grupos sao independentes e nao mutuamente exclusivos. Uma mesma especie pode
entrar em mais de um grupo quando atende a mais de uma pergunta ecologica.

Grupos usados no piloto:

- Especialistas loticos sensiveis:
  especies reofilicas e sensiveis.
- Raspadores/bentonicos reofilicos:
  especies perifitivoras/raspadoras, bentonicas e reofilicas.
- Generalistas tolerantes:
  especies onivoras e tolerantes.
- Predadores:
  especies piscivoras.

Exemplo de sobreposicao correta:

- `Harttia torrenticola` pode entrar em especialistas loticos sensiveis e em
  raspadores/bentonicos reofilicos.
- Isso nao e duplicidade taxonomica; e leitura funcional por perguntas
  ecologicas independentes.

Frase recomendada para relatorio:

> Os grupos funcionais sentinelas sao independentes e nao somam 100%; uma
> especie pode compor mais de um grupo quando atende a criterios ecologicos
> distintos.

## Produtos Visuais

### Mapa Funcional Ponto x Ano

Produto de referencia do piloto:

- `26_grafico_mini_mapas_funcoes_ecologicas_ano_ictiofauna.png`

Estrutura:

- linhas = grupos funcionais sentinelas;
- colunas = anos;
- ponto espacial = coordenada oficial do ponto amostral;
- tamanho da bolha = CPUEn medio anual absoluto do grupo;
- cor = participacao media do grupo no CPUEn total do ponto/ano;
- rodape explicando que e produto exploratorio.

Boas praticas de layout:

- usar coordenadas oficiais por KMZ/KML ou Supabase auditado;
- registrar pares de pontos proximos para risco de sobreposicao;
- nao usar legenda de tamanho quando ela competir visualmente com os paineis;
- manter a barra de cor como legenda principal;
- usar rotulos curtos de ponto (`IC-05`, `IC-14`).

### Assinatura De Especies Por Grupo

Produto de referencia do piloto:

- `27_grafico_assinatura_especies_grupos_funcionais_ictiofauna.png`

Estrutura:

- quatro paineis, um por grupo sentinela;
- nomes cientificos em italico;
- tamanho do nome e barra proporcionais ao CPUEn total acumulado da especie no
  grupo;
- `AME` para especies ameacadas/de interesse;
- `EXO` para especies exoticas;
- planilha de apoio com CPUEn, abundancia, frequencia de amostras, pontos,
  campanhas e fonte do marcador de ameaca.

Boas praticas de layout:

- separar claramente a coluna de nomes da coluna de barras;
- reduzir dinamicamente nomes longos para evitar sobreposicao;
- usar barras discretas como apoio, nao como grafico principal;
- manter a lista completa na planilha quando houver muitas especies.

## Coordenadas

O piloto GEOARC001 mostrou que coordenadas podem variar indevidamente por
campanha na planilha de migracao. Para produtos espaciais:

1. usar fonte oficial de coordenadas, preferencialmente KMZ/KML ou tabela mestre
   auditada no Supabase;
2. registrar diagnostico de variacao das coordenadas da planilha;
3. validar a planilha contra a referencia antes de migrar;
4. corrigir `pontos_coleta` com auditoria antes/depois quando necessario.

No GEOARC001, a referencia oficial foi:

- `Arcelor_2026.kmz`

Scripts associados:

- `scripts/projects/geoarc001/generate_functional_spatial_mini_maps.py`
- `scripts/projects/geoarc001/generate_functional_species_signature.py`
- `scripts/maintenance/geoarc001/update_geoarc001_coordinates_from_kmz.py`
- `src/opyta_analysis/geo_reference.py`

## Saidas Obrigatorias

Todo produto derivado deste padrao deve gerar:

- PNG da figura;
- XLSX com dados de apoio;
- JSON manifesto com fontes, criterios e parametros;
- diagnostico de coordenadas quando houver mapa;
- nota metodologica informando que a analise e exploratoria, salvo promocao
  formal para produto oficial.

## Quando Usar

Usar em monitoramentos de ictiofauna com:

- pontos fixos no tempo;
- esforco quantitativo comparavel;
- atributos funcionais minimamente revisados;
- necessidade de explicar estabilidade, substituicao ou simplificacao
  funcional da assembleia.

Evitar como unica evidencia conclusiva. Interpretar junto com riqueza, CPUEn,
biomassa, diversidade alfa, composicao taxonomica, LCBD, NMDS/PERMANOVA,
sazonalidade e historico de campo.

