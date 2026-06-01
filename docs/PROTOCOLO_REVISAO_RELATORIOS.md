# Protocolo de Revisao de Relatorios Tecnicos

Status: piloto em desenvolvimento

## Objetivo

Criar uma central de revisao reproduzivel para relatorios tecnicos em DOCX,
combinando verificacoes deterministicas, inventario de resultados e, em etapa
posterior, revisao semantica assistida por IA.

## Arquitetura

```text
src/opyta_analysis/revisao/
  docx_audit.py        # extrai estrutura, texto, estilos, legendas, referencias, tabelas e comentarios
  html_report.py       # gera uma revisao visual em HTML com filtros, cards e contexto destacado
  resultados_audit.py  # inventaria PNG/XLSX gerados e valida imagens/planilhas
  numeric_audit.py     # extrai metricas numericas das planilhas e procura mencoes no texto
  rules.py             # regras deterministicas iniciais e severidade dos achados

scripts/
  revisar_biota_aquatica_sam.py  # piloto SAM Metais - Biota Aquatica
```

## Camadas de revisao

1. Integridade do DOCX
   - comentarios internos;
   - controle de alteracoes;
   - tabelas, figuras e midias embutidas;
   - estrutura de titulos.

2. Revisao formal
   - grafias inconsistentes;
   - erros em titulos;
   - padronizacao de nomes de projeto, cliente, grupos e campanhas.

3. Figuras, quadros e tabelas
   - legendas duplicadas;
   - referencias textuais sem legenda equivalente;
   - legendas sem chamada textual;
   - verificacao futura de figuras incorporadas vs arquivos gerados.

4. Resultados externos
   - inventario das pastas de outputs;
   - PNGs em branco ou pequenos;
   - dimensoes das planilhas XLSX;
   - duplicidades de arquivos e versoes antigas.

5. Revisao numerica futura
   - cruzar numeros do texto contra tabelas de riqueza, abundancia, diversidade,
     similaridade, suficiencia e indicadores.
   - registrar metricas detectadas, contexto textual, ausencia de mencao numerica
     e alertas de conferencia no arquivo central `03_inconsistencias.xlsx`.
   - gerar candidatos de divergencia numerica quando o texto discute a mesma
     metrica, mas apresenta numeros diferentes do resultado calculado.

6. Revisao tecnica futura
   - coerencia de interpretacao;
   - conclusoes proporcionais aos dados;
   - consistencia entre metodologia, resultados e discussao.

## Pacote de saida do piloto

O runner gera uma pasta `_revisao_qualidade/piloto_biota_aquatica` ao lado do DOCX:

- `01_relatorio_revisao.md`
- `01_estrutura_documento.xlsx`
- `02_inventario_resultados.xlsx`
- `03_inconsistencias.xlsx`
- `04_texto_extraido.md`
- `05_metricas_numericas.xlsx`
- `06_divergencias_numericas_candidatas.xlsx`
- `07_revisao_visual.html`
- `00_documento_extraido.json`
- `00_resultados_inventario.json`

## Severidade

- `CRITICA`: impede entrega ou indica risco alto de erro tecnico/documental.
- `ALTA`: deve ser resolvida antes da entrega final.
- `MEDIA`: requer verificacao tecnica ou editorial.
- `BAIXA`: padronizacao, estilo ou alerta de completude.

## Registro de erros e alertas

O arquivo mais amigavel para leitura e `07_revisao_visual.html`. Ele apresenta
os achados em cards, com filtros por severidade, categoria e grupo, alem de
contexto textual destacado para facilitar a conferencia.

O arquivo mestre auditavel continua sendo `03_inconsistencias.xlsx`. A aba
`checklist` deve conter apenas achados documentais mais rastreaveis. Alertas
numericos e divergencias candidatas ficam separados na aba `triagem_numerica`,
pois sao apoio de investigacao, nao erro confirmado.
As colunas `procede?`, `acao`, `responsavel`, `status` e
`observacao_revisor` foram reservadas para transformar a saida em checklist
operacional de revisao. A aba `dicionario_revisao` descreve os valores
esperados para `tipo_achado` e `status`.

O arquivo `05_metricas_numericas.xlsx` e uma camada auxiliar: guarda todas as
metricas extraidas, as mencoes encontradas no texto e a classificacao de cada
metrica. Quando uma metrica-chave nao e localizada na narrativa do respectivo
grupo, ela tambem e registrada como `Numeros/conferencia` em
`03_inconsistencias.xlsx`.

O arquivo `06_divergencias_numericas_candidatas.xlsx` guarda, em modo
laboratorio, os casos em que a automacao encontrou paragrafo relevante para uma
metrica e numeros diferentes do valor de referencia. Essa camada ainda nao deve
ser usada como checklist visual padrao, porque pode confundir contexto biologico
com divergencia real.

Regra de confianca: a automacao nunca deve misturar hipotese numerica com erro
confirmado. O HTML pode mostrar a hipotese como triagem, mas o revisor precisa
validar contexto, tabela de origem e regra biologica antes de qualquer ajuste.

## Aprendizados do piloto

- Riqueza total de composicao nao deve ser calculada por quantidade de linhas
  da aba quando a planilha contem mais de uma tabela ou blocos auxiliares.
- A regra padrao e identificar a coluna taxonomica principal (`Nome Cientifico`,
  `Taxon`, `Taxa` ou equivalente), isolar o primeiro bloco de composicao e
  contar taxons unicos.
- No piloto de Ictio, `01_tabela_composicao_ictiofauna.xlsx` tinha 55 linhas
  totais, mas apenas 25 especies no bloco principal de composicao. As demais
  linhas pertenciam a outra tabela de atributos/status na mesma aba.
- A busca textual de numeros precisa evitar falsos positivos em codigos de
  ponto, como `SAM_25`, para nao confundir codigo amostral com riqueza,
  abundancia ou outro resultado numerico.
- Divergencias numericas candidatas devem ser tratadas como triagem. Elas so
  viram erro confirmado depois da leitura do contexto pelo revisor.

## Regra do piloto SAM Metais

O piloto foi executado sobre o relatorio consolidado de Biota Aquatica e as pastas:

- `Resultados/Bentos`
- `Resultados/Fito`
- `Resultados/Zooplancton`
- `Resultados/Ictio`

Esta primeira etapa nao altera o DOCX original. Ela apenas extrai, inventaria e
gera uma lista rastreavel de achados.
