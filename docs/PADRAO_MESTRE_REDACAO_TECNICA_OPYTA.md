# Padrao Mestre De Redacao Tecnica Opyta

## Status

- papel: documento mestre evolutivo
- status editorial: ativo
- criado em: 2026-06-21
- ultima calibracao: 2026-06-21
- validado em: GEOHER001 (piloto Zoobentos)
- autoridade: referencia principal para redacao automatica e assistida de
  relatorios tecnicos
- substitui: diretrizes textuais dispersas quando houver conflito editorial

## Objetivo

Definir a regua editorial da Opyta para textos tecnicos gerados com apoio do
pipeline analitico e do HTML rastreavel. Este e o documento mestre de referencia
para a geracao automatica dos relatorios tecnicos apos a conclusao das analises.

O documento separa:

- o que o sistema pode estruturar automaticamente;
- o que depende de decisao editorial humana;
- quais limites de inferencia nao podem ser ultrapassados.

O uso pretendido e triplo:

1. orientar a escrita humana assistida;
2. governar a geracao automatica de narrativas apos o fechamento analitico;
3. registrar calibracoes produzidas pela evolucao dos projetos e das rotinas.

## Natureza Evolutiva E Governanca

Este padrao nao representa uma versao textual congelada. Ele permanece passivel
de ajustes e calibracoes continuas conforme novos projetos revelem necessidades
editoriais, tecnicas, regulatorias ou analiticas.

As calibracoes devem:

1. partir de um caso aplicado e rastreavel;
2. preservar regras anteriores que continuem validas;
3. registrar a data, o projeto de origem e a justificativa da mudanca;
4. distinguir melhoria geral de excecao especifica de um projeto;
5. ser refletidas na policy consumida pelo motor textual;
6. ser verificadas em um relatorio piloto antes da promocao ao fluxo automatico.

Em caso de conflito, aplicar a seguinte hierarquia:

1. este documento mestre;
2. patterns tecnicos aprovados em `docs/patterns`;
3. calibracao documentada no dossie do projeto;
4. configuracao particular do gerador ou renderer.

O HTML gerado deve identificar a revisao da policy utilizada, permitindo
reproduzir qual conjunto de regras orientou cada relatorio.

## Quando Usar

- relatorios tecnicos com texto modular por tema ecologico;
- HTMLs de apoio a redacao final;
- sinteses tecnicas produzidas a partir de evidencias versionadas;
- textos em que cada afirmacao precisa apontar a uma ou mais fontes.

## Quando Nao Usar

- comunicacao comercial ou institucional;
- parecer causal quando o desenho amostral nao sustenta causalidade;
- texto de divulgacao simplificada para publico leigo;
- blocos em que a equipe ainda nao definiu a metrica, a pergunta ou a limitacao.

## Estilo Geral

- Escrever de forma objetiva, tecnica e profissional.
- Priorizar clareza e precisao em detrimento de linguagem academica excessivamente rebuscada.
- Evitar floreios, adjetivacoes desnecessarias e opinioes subjetivas.
- Utilizar linguagem compativel com relatorios ambientais, pareceres tecnicos, estudos
  ambientais, programas de monitoramento e respostas a informacoes complementares.
- Produzir textos que transmitam seguranca tecnica sem parecerem excessivamente formais.

O texto final deve parecer ter sido elaborado por um coordenador tecnico senior da area
ambiental, habituado a elaboracao de EIAs, RIMAs, monitoramentos ambientais, programas
de fauna, ictiofauna, bentos, qualidade da agua e respostas tecnicas para orgaos ambientais.

### Naturalidade Da Narrativa

O rigor e a rastreabilidade devem permanecer no sistema, mas nao precisam ser
expostos repetidamente no corpo do relatorio. A narrativa principal deve
apresentar os resultados de forma direta, fluida e tecnicamente segura.

Evitar metalinguagem que explique a funcao do proprio texto, da metrica ou do
grafico, como:

- "a distribuicao descreve";
- "a frequencia resume";
- "a similaridade representa";
- "este resultado deve ser lido";
- "o indicador permite observar".

Quando a limitacao for indispensavel para evitar uma conclusao incorreta,
apresenta-la de forma breve. Limitacoes gerais ou recorrentes devem permanecer
na matriz de evidencias, em nota tecnica ou em secao metodologica propria.

## Estrutura Obrigatoria Do Texto

Sempre que possivel organizar os textos na seguinte sequencia logica:

1. Contextualizacao breve;
2. Apresentacao dos resultados;
3. Observacoes relevantes;
4. Encaminhamentos ou conclusoes.

## Escrita

- Utilizar frases relativamente curtas e diretas.
- Evitar periodos excessivamente longos.
- Preferir voz ativa, mas utilizar voz passiva quando for padrao tecnico.
- Manter boa fluidez entre os paragrafos.
- Evitar repeticoes de palavras e conceitos.
- Variar conectivos, aberturas de frase e estruturas narrativas.
- Evitar que todos os blocos reproduzam a mesma formula sintatica.

Para contextualizacao temporal, alternar de acordo com o caso:

- durante o monitoramento;
- entre os anos ou campanhas avaliados;
- considerando as campanhas realizadas;
- na serie historica;
- na avaliacao consolidada;
- no periodo analisado.

O uso de "ao longo do periodo" e aceitavel, mas nao deve funcionar como abertura
padrao de todos os paragrafos.

## Abordagem Analitica

- Nao fazer inferencias que nao sejam sustentadas pelos dados apresentados.
- Nao especular.
- Nao atribuir causalidade sem evidencia.
- Quando solicitado, descrever apenas os resultados observados.
- Diferenciar claramente descricao, interpretacao e conclusao.

Em paragrafos descritivos, registrar apenas fatos observados, valores, extremos,
distribuicoes e padroes diretamente sustentados pelos dados. Expressoes como
"concentrado", "predominante", "recorrente" ou "restrito" somente pertencem ao
bloco descritivo quando estiverem acompanhadas pela base numerica que as define.

### Regra Do Bloco Interpretativo

No HTML rastreavel e em textos modulares de monitoramento, o bloco dito
interpretativo nao deve, necessariamente, ampliar a inferencia.

Quando o bloco descritivo ja apresentar campanhas, pontos, maximos e minimos,
o bloco interpretativo pode assumir a funcao de panorama geral do periodo,
agrupando as metricas no tempo e no espaco sem extrapolar os dados.

Aplicar assim:

1. o descritivo mostra fatos observados, extremos e localizacao dos eventos;
2. o interpretativo organiza a leitura geral do periodo;
3. esse panorama nao deve especular mecanismo, causa ou efeito sem suporte;
4. se nao houver necessidade real de interpretar, o bloco pode funcionar como
  sintese descritiva de fechamento.

O bloco interpretativo nao deve repetir a metodologia, explicar a funcao da
metrica ou acumular frases defensivas. Sua funcao e integrar os achados e
traduzir seu significado tecnico na escala permitida pelas evidencias.

## Resultados

Ao descrever dados ambientais:

- Apresentar primeiro os fatos observados.
- Destacar maiores e menores valores quando pertinente.
- Destacar padroes espaciais e temporais observados.
- Nao utilizar termos como "significativo", "importante", "preocupante", "relevante"
  ou similares sem respaldo estatistico ou tecnico explicito.
- Nao extrapolar os resultados.

### Regra Do Continuo Dos Dados

Como regra geral, o texto deve percorrer o continuo dos dados, e nao apenas
registrar um valor medio ou um resumo isolado.

Aplicacao pratica:

1. apresentar o comportamento geral da metrica;
2. destacar os valores maximos e minimos mais representativos;
3. quando houver camada temporal, explicitar em quais campanhas, periodos ou
   recortes os extremos ocorreram;
4. fechar o bloco com uma leitura geral do conjunto.

Nao e obrigatorio citar sempre exatamente tres maximos e tres minimos, mas o
texto deve revelar os extremos principais quando eles ajudarem a entender o
comportamento espacial ou temporal dos dados.

Quando houver serie temporal ou comparacao entre campanhas, evitar resumo
excessivamente agregado. O texto deve mostrar onde o dado aumentou, reduziu,
atingiu maximos ou registrou minimos antes do fechamento interpretativo.

### Regra Das Series Temporais

Nas series temporais, o texto deve mencionar os maximos e minimos da variavel,
preferencialmente identificando ponto e campanha quando essa informacao estiver
visivel no output.

O redator pode optar por:

- falar diretamente dos pontos e campanhas em que ocorreram os extremos; ou
- agrupar os eventos e depois fazer um fechamento geral do periodo.

O fechamento deve resumir o comportamento da serie, sem substituir a leitura
dos extremos por medias ou generalidades vagas.

### Contextualizacao Espacial

Sempre que as bases do projeto permitirem, substituir ou complementar codigos
de pontos por informacoes que deem sentido ambiental a sua localizacao:

- corpo hidrico;
- trecho de montante, intermediario ou jusante;
- setor ou unidade da area de estudo;
- margem, tributario ou canal principal;
- relacao com estruturas, drenagens ou ambientes relevantes.

O codigo do ponto deve ser preservado para rastreabilidade, mas nao precisa ser
a unica referencia espacial. A contextualizacao somente pode ser utilizada
quando estiver cadastrada em fonte oficial do projeto.

### Restricao De Fonte Visual

Nao incluir no texto resultados que nao estejam efetivamente sustentados pela
figura, planilha-fonte ou output utilizado naquele bloco.

Se a figura nao mostra media, mediana ou outro resumo derivado, esses valores
nao devem ser inseridos no texto apenas porque existem na base numerica.

Em caso de duvida, priorizar:

1. o que esta visivel no output principal;
2. os extremos e padroes diretamente confirmaveis;
3. a descricao mais conservadora.

### Similaridade E Agrupamentos

Em blocos de similaridade, priorizar a descricao dos agrupamentos principais,
em vez de focar apenas no par mais proximo ou mais distante.

Como regra pratica, descrever de 1 a 4 agrupamentos principais quando essa
estrutura estiver visivel no dendrograma ou na matriz agregada.

Pares extremos podem ser citados como apoio, mas nao devem substituir a leitura
dos grupos formados.

### Sinteses Tecnicas

A sintese nao deve funcionar como copia abreviada dos paragrafos anteriores.
Ela deve conectar os principais achados espaciais, temporais e ecologicos,
selecionando somente o que altera a compreensao geral do diagnostico.

Uma boa sintese deve:

1. identificar os padroes dominantes;
2. relacionar resultados complementares;
3. registrar contrastes ou mudancas relevantes;
4. apresentar a implicacao tecnica permitida;
5. indicar encaminhamentos quando forem necessarios.

Evitar enumerar novamente todos os maximos, minimos e percentuais ja descritos.

### Vocabulário Preferencial De Escala

Evitar, quando desnecessario, expressoes como:

- "no conjunto";
- "nas unidades".

Essas expressoes podem ser utilizadas quando forem as mais naturais, mas nao
devem substituir a escala real da analise. Preferir formulacoes concretas e
variadas, como:

- "ao longo do periodo";
- "durante o monitoramento";
- "entre 2022 e 2025";
- "considerando as campanhas avaliadas";
- "nas campanhas e pontos avaliados";
- "na serie temporal";
- "na serie historica";
- "na avaliacao consolidada";
- "na matriz agregada";
- "nos pontos com maiores valores".

## Tonalidade

A escrita deve transmitir:

- Objetividade;
- Credibilidade tecnica;
- Conhecimento pratico de campo;
- Experiencia em gestao ambiental;
- Foco em tomada de decisao.

A linguagem deve se aproximar de relatorios de consultoria ambiental. Em vez
de comandos genericos como "os indicadores devem ser lidos de forma integrada",
preferir formulacoes que indiquem quais informacoes precisam ser consideradas,
por exemplo: composicao, riqueza, abundancia, condicoes de habitat e dados
ambientais disponiveis.

O texto deve transmitir seguranca tecnica sem assumir tom mecanico, academico
em excesso ou permanentemente defensivo.

### Uso Proporcional De Ressalvas

Frases como "nao permite inferir causalidade", "nao define isoladamente a
condicao ambiental" ou "deve ser interpretado com cautela" devem aparecer
somente quando evitarem uma leitura incorreta concreta.

Quando a mesma ressalva se aplicar a varios resultados:

1. registra-la uma vez na secao mais adequada;
2. mante-la associada a evidencia para auditoria;
3. evitar repeti-la em todos os paragrafos da narrativa.

## Regras Principais (Hierarquia De Decisao)

Quando houver duvida entre escrever de forma academica ou de forma tecnica-operacional:
priorizar sempre a forma tecnica-operacional.

Quando houver duvida entre interpretar ou apenas descrever:
priorizar sempre a descricao dos dados.

Quando houver duvida entre escrever muito ou escrever pouco:
ser conciso, desde que a informacao essencial seja preservada.

## Regras Numericas E De Rastreabilidade

1. Todo percentual deve vir acompanhado de denominador ou universo implicito claro.
2. Toda comparacao deve indicar a base comparada (campanhas, pontos, areas, periodos).
3. Toda mencao a diferenca visual deve distinguir observacao grafica de significancia estatistica.
4. Ausencia de registro nao equivale automaticamente a ausencia ecologica.
5. Diferenciar zero por ausencia de captura de zero por dado faltante.
6. Toda afirmacao numerica deve apontar um arquivo-fonte, metrica ou output rastreavel.
7. Nomes cientificos devem ser apresentados em italico no produto final.
8. Quando a identificacao nao alcancar especie, preferir o nivel taxonomico efetivo.
9. A rastreabilidade completa pode permanecer em camada tecnica sem interromper
   a fluidez da narrativa principal.
10. Toda contextualizacao espacial deve possuir fonte oficial do projeto.

## O Que O Sistema Pode Automatizar

- ordenar os modulos;
- recuperar metricas, figuras e fontes;
- montar a estrutura basica do texto;
- anexar evidencias por paragrafo;
- validar consistencia numerica e rastreabilidade.

## Arquitetura Do Sistema Textual

O sistema textual deve ser organizado em tres nucleos explicitos:

### Policy

Representa as regras editoriais da Opyta definidas neste documento: voz,
estrutura, vocabulario, limites de inferencia, tratamento de numeros,
rastreabilidade e criterios de recomendacao.

### Evidence

Representa os fatos produzidos pelas analises: metricas, fontes, denominadores,
recortes espaciais e temporais, figuras, limitacoes e nivel de inferencia
permitido.

As evidencias tambem devem armazenar descritores espaciais oficiais dos pontos
e as ressalvas aplicaveis, mesmo quando esses elementos nao forem exibidos em
todos os paragrafos.

### Renderer

Transforma as evidencias em texto e HTML obedecendo a policy vigente, sem
inventar fatos, ultrapassar o nivel de inferencia autorizado ou perder os
vinculos com as fontes.

O renderer deve separar duas camadas:

1. narrativa tecnica limpa, destinada a leitura do relatorio;
2. lastro de auditoria, com evidencias, fontes, limitacoes e validacoes.

A segunda camada nao deve impor metalinguagem ou ressalvas repetitivas a
primeira.

Fluxo esperado:

`analises concluidas -> evidence -> policy -> renderer -> HTML rastreavel -> revisao humana`

Scripts de projeto devem atuar como adaptadores das bases analiticas para o
nucleo de evidencias. Regras editoriais gerais nao devem permanecer duplicadas
nos scripts particulares.

## O Que Continua Sob Curadoria Humana

- calibracao do tom da Opyta;
- decisao sobre intensidade interpretativa;
- escolha final das recomendacoes;
- casos-limite de linguagem ecologica e regulatoria;
- aprovacao para uso automatico em producao.

## Regra De Entrada No Pipeline

Este documento deve ser consultado em toda geracao textual posterior ao
fechamento das analises. O motor somente deve ser promovido a uma etapa
automatica de producao quando:

1. houver validacao editorial humana em pelo menos dois projetos;
2. a equipe confirmar que a voz representa a linguagem desejada pela Opyta;
3. o gerador conseguir separar claramente resultado, interpretacao e limitacao;
4. o output HTML for tratado como apoio a redacao, nao como texto final irrevogavel.

## Projetos De Origem

- GEOHER001__monitoramento_de_ictio_e_bentos_herculano

## Relacao Com Outros Artefatos

- pattern-base: `docs/patterns/linguagem_tecnica_rastreavel.md`
- piloto: `outputs/_scratch/textual_pilot_geoher001/`
- gerador piloto: `scripts/projects/geoher001/generate_bentos_textual_pilot.py`
- implementacao atual: `src/opyta_analysis/textual/`
- futuro pipeline: fechamento analitico -> geracao de HTML rastreavel -> revisao humana

## Ciclo De Calibracao Continua

A cada novo projeto ou grupo biologico, revisar:

- se a intensidade interpretativa esta adequada;
- se os modulos estao longos demais;
- se as recomendacoes estao especificas o suficiente;
- se a voz da Opyta esta realmente reconhecivel.

### Historico De Calibracoes

| Data | Projeto | Calibracao |
| --- | --- | --- |
| 2026-06-21 | GEOHER001 / Zoobentos | Criacao da regua mestre; continuo dos dados, extremos temporais e espaciais, agrupamentos de similaridade e restricao de fonte visual. |
| 2026-06-21 | GEOHER001 / Zoobentos | Reducao de metalinguagem e frases defensivas; separacao mais estrita entre descricao e interpretacao; variacao textual; contextualizacao espacial; sinteses integradas e linguagem de consultoria ambiental. |
