# Ocorrencia Em Series Com Muitas Campanhas

## Status

- status: candidato
- criado em: 2026-06-19
- validado tecnicamente em: 2026-06-19
- aprovacao visual: pendente
- substitui: quadro unico com todas as campanhas e pontos no corpo do relatorio
- substituido por:

## Quando Usar

- Estudos com muitas campanhas e varios pontos amostrais.
- Quadros de presenca/ausencia que ficariam excessivamente largos.
- Relatorios que precisam mostrar persistencia temporal e distribuicao espacial.
- Ictiofauna, zoobentos e outros grupos com dados de ocorrencia por campanha e ponto.

## Quando Nao Usar

- Estudos com uma ou duas campanhas, quando o quadro completo ainda e legivel.
- Dados sem uma grade amostral confiavel de campanha por ponto.
- Casos em que abundancia, e nao ocorrencia, seja a pergunta principal.

## Decisao Tecnica

- entrada:
  - taxon;
  - campanha;
  - ponto;
  - abundancia ou contagem;
  - unidades campanha-ponto efetivamente amostradas.
- processamento:
  - converter abundancia positiva em presenca;
  - calcular frequencia por campanha usando os pontos amostrados como denominador;
  - calcular frequencia por ponto usando as campanhas amostradas como denominador;
  - manter o quadro completo em Excel, organizado por ano;
  - gerar uma base longa completa para auditoria.
- saida:
  - workbook com resumo, matrizes sinteticas, quadros anuais e base longa;
  - mapa de calor de frequencia por campanha;
  - mapa de calor de frequencia por ponto.
- layout:
  - A4 paisagem;
  - 600 dpi;
  - sem titulo dentro da figura;
  - campanhas abreviadas (`C21`, `C22`, etc.);
  - nomes dos taxons em italico no eixo vertical;
  - valor percentual escrito apenas nas celulas com ocorrencia;
  - ausencia em branco;
  - nao amostrado em cinza no Excel;
  - grupos com muitos taxons divididos automaticamente em partes;
  - preservar ordens taxonomicas na mesma parte quando houver espaco.

## Formulas

Frequencia do taxon em uma campanha:

`pontos com presenca / pontos amostrados na campanha`

Frequencia do taxon em um ponto:

`campanhas com presenca / campanhas em que o ponto foi amostrado`

Frequencia global:

`unidades campanha-ponto com presenca / unidades campanha-ponto amostradas`

Ausencia e nao amostrado nao devem ser tratados como a mesma condicao.

## Estrutura Do Workbook

- `Resumo_Geral`
  - numero e percentual de campanhas com ocorrencia;
  - numero e percentual de pontos com ocorrencia;
  - frequencia global;
  - campanhas e pontos observados.
- `Freq_Campanha`
  - taxons nas linhas;
  - campanhas nas colunas;
  - percentual de pontos ocupados.
- `Freq_Ponto`
  - taxons nas linhas;
  - pontos nas colunas;
  - percentual de campanhas com presenca.
- `Ocorrencia_AAAA`
  - quadro anual com presenca por campanha e ponto;
  - `OC` e `%OC` por campanha.
- `Base_Longa`
  - uma linha para cada combinacao taxon, campanha e ponto;
  - abundancia e presenca.

## Projetos De Origem

- `GEOHER001__monitoramento_de_ictio_e_bentos_herculano`
- Recorte de 16 campanhas, oito pontos, oito especies de peixes e 74 taxons de
  zoobentos.

## Limitacoes

- O denominador depende de uma grade amostral correta.
- Para grupos muito ricos, o mapa completo precisa ser dividido em paginas.
- A frequencia nao substitui abundancia, biomassa, CPUE ou indices ecologicos.
- A aprovacao visual pelo usuario ainda deve ser registrada antes da promocao
  para `approved`.

## Codigo

- modulo: `src/opyta_analysis/pipelines/diagnostico/occurrence_summary.py`
- integracoes:
  - `src/opyta_analysis/pipelines/diagnostico/ictio.py`
  - `src/opyta_analysis/pipelines/diagnostico/zoobentos.py`
- funcao principal: `export_occurrence_summary`
