# Padrao De Redacao Tecnica Rastreavel Opyta v1

## Status

- status: prototype
- criado em: 2026-06-21
- validado em: GEOHER001 (piloto Zoobentos)
- substitui: nenhuma diretriz formal consolidada
- substituido por:

## Objetivo

Definir a regua editorial da Opyta para textos tecnicos gerados com apoio do
pipeline analitico e do HTML rastreavel. Este documento separa:

- o que o sistema pode estruturar automaticamente;
- o que depende de decisao editorial humana;
- quais limites de inferencia nao podem ser ultrapassados.

O uso pretendido e duplo:

1. orientar a escrita humana assistida;
2. servir de base para futura automacao do gerador HTML apos validacao editorial.

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

## Abordagem Analitica

- Nao fazer inferencias que nao sejam sustentadas pelos dados apresentados.
- Nao especular.
- Nao atribuir causalidade sem evidencia.
- Quando solicitado, descrever apenas os resultados observados.
- Diferenciar claramente descricao, interpretacao e conclusao.

## Resultados

Ao descrever dados ambientais:

- Apresentar primeiro os fatos observados.
- Destacar maiores e menores valores quando pertinente.
- Destacar padroes espaciais e temporais observados.
- Nao utilizar termos como "significativo", "importante", "preocupante", "relevante"
  ou similares sem respaldo estatistico ou tecnico explicito.
- Nao extrapolar os resultados.

## Tonalidade

A escrita deve transmitir:

- Objetividade;
- Credibilidade tecnica;
- Conhecimento pratico de campo;
- Experiencia em gestao ambiental;
- Foco em tomada de decisao.

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

## O Que O Sistema Pode Automatizar

- ordenar os modulos;
- recuperar metricas, figuras e fontes;
- montar a estrutura basica do texto;
- anexar evidencias por paragrafo;
- validar consistencia numerica e rastreabilidade.

## O Que Continua Sob Curadoria Humana

- calibracao do tom da Opyta;
- decisao sobre intensidade interpretativa;
- escolha final das recomendacoes;
- casos-limite de linguagem ecologica e regulatoria;
- aprovacao para uso automatico em producao.

## Regra De Entrada No Pipeline

Este padrao so deve virar etapa automatica do pipeline quando:

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
- futuro pipeline: fechamento analitico -> geracao de HTML rastreavel -> revisao humana

## Proxima Revisao Recomendada

Ao validar um segundo grupo biologico, revisar:

- se a intensidade interpretativa esta adequada;
- se os modulos estao longos demais;
- se as recomendacoes estao especificas o suficiente;
- se a voz da Opyta esta realmente reconhecivel.