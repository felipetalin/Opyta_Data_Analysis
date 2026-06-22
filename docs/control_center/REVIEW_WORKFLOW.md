# Fluxo De Revisao Da Central De Controle

Este protocolo e usado para revisar uma operacao, analise ou entrega existente
sem reiniciar automaticamente todo o fluxo principal.

## Como Acionar

Gatilhos reconhecidos:

- `center_control revisao`
- `center_control revisão`
- `revisar projeto <codigo>`
- `revisar operacao <nome>`
- `revisar relatorio`, `revisar graficos` ou `revisar dados`
- `ajustes de layout`, `ajustes de texto` ou `corrigir resultados`

Ao reconhecer um pedido de revisao:

1. abrir este protocolo;
2. localizar o projeto e a operacao original;
3. identificar o produto ou conjunto que sera a linha de base;
4. classificar o tipo e o impacto da revisao;
5. criar um registro em [reviews](reviews/README.md) quando o escopo estiver
   definido;
6. reabrir apenas as etapas e gates afetados;
7. validar todos os produtos dependentes;
8. apresentar o pacote revisado no Gate R.

## Primeira Resposta Esperada

A primeira devolutiva deve informar:

- projeto e operacao identificados;
- linha de base que sera preservada;
- tipo preliminar de revisao;
- etapas potencialmente afetadas;
- se algum gate anterior precisara ser reaberto;
- proxima acao.

Se o pedido ja for preciso, como "reduza a fonte da legenda do grafico 4", a
propria solicitacao aprova o escopo. Se houver mais de uma interpretacao
razoavel ou risco de alterar banco, metodologia ou muitos produtos, usar o
estado `awaiting_review_scope_approval`.

## Tipos De Revisao

| Tipo | Exemplos | Retorno minimo |
| --- | --- | --- |
| `data` | valor, ponto, campanha, esforco, contagem ou coordenada incorreta | Validacao e Gate A |
| `taxonomy` | nome cientifico, `cf.`, origem, endemismo, ameaca ou atributo de especie | Auditoria taxonomica e Gate B |
| `analysis` | formula, filtro, agrupamento, CPUE, indice ou metodo | Configuracao analitica; Gate C se mudar decisao aprovada |
| `text` | redacao, legenda, interpretacao, nomenclatura ou conclusao | Evidencias, validacao textual e produtos textuais |
| `layout` | paleta, fonte, tamanho, posicao, espacamento ou paginacao | Figuras/HTML/DOCX afetados e validacao visual |
| `package` | arquivo ausente, nome, pasta, manifesto, hash ou formato | Pacote de entrega e manifesto |
| `full` | revisao geral de uma entrega | Auditoria completa, inicialmente sem alteracao |

Uma revisao pode ter mais de um tipo. O registro deve indicar um tipo principal
e os tipos secundarios.

## Niveis De Impacto

| Nivel | Alcance | Regra |
| --- | --- | --- |
| `R0` | Sem alteracao de conteudo: nome de arquivo, empacotamento ou manifesto | Nao reabre Gates A, B ou C |
| `R1` | Apresentacao: texto ou layout sem mudar numeros/metodo | Regenerar apenas produtos dependentes |
| `R2` | Resultado derivado: formula, filtro, tabela ou metrica | Regenerar base analitica e todos os produtos dependentes |
| `R3` | Fonte, taxonomia, migracao ou consolidacao | Voltar ao gate afetado e repetir toda a cadeia posterior |

O impacto deve ser definido pela dependencia real, nao pelo tamanho visual da
mudanca. Uma unica letra em um nome cientifico pode ser `R3`; mudar a cor de
vinte graficos continua sendo `R1`.

## Matriz De Retorno

| O que mudou | Gate reaberto | Etapas que devem ser repetidas |
| --- | --- | --- |
| Dados de entrada | Gate A | validacao, migracao, consolidacao, analises e entrega |
| Cadastro ou atributo de especie | Gate B | cadastro; migracao/consolidacao quando afetadas; analises e entrega |
| Metodo, template, paleta ou produtos acordados | Gate C | configuracao, geracao e revisao |
| Formula ou filtro sem alterar o banco | Gate C quando a decisao metodologica mudar | base analitica e produtos dependentes |
| Texto sem mudanca de resultado | nenhum gate anterior | texto, evidencias, validacao textual e manifesto |
| Layout sem mudanca de conteudo | Gate C apenas se trocar identidade/template aprovado | figuras/relatorio afetados e manifesto |
| Pacote ou nome de arquivo | nenhum gate anterior | pacote, links, manifesto e hashes |

## Fluxo Da Revisao

```text
PEDIDO DE REVISAO
  |
  v
IDENTIFICAR LINHA DE BASE
  |
  v
TRIAGEM: TIPO + IMPACTO + DEPENDENCIAS
  |
  +--> escopo claro -----------------------------+
  |                                              |
  +--> escopo ambiguo/alto impacto                |
          |                                       |
          v                                       |
   APROVACAO DO ESCOPO                            |
          |                                       |
          +---------------------------------------+
  |
  v
REABRIR GATE A, B OU C SOMENTE SE NECESSARIO
  |
  v
EXECUTAR CORRECOES E REGENERAR DEPENDENCIAS
  |
  v
VALIDAR REVISAO E COMPARAR COM A LINHA DE BASE
  |
  v
GATE R — APROVACAO FINAL DA REVISAO
  |
  v
PROMOVER PACOTE REVISADO + ATUALIZAR LASTRO
```

## Linha De Base E Versionamento

Antes de alterar produtos:

- registrar os arquivos alvo, data e hashes quando disponiveis;
- preservar a versao anterior;
- identificar a revisao como `R01`, `R02` e assim por diante;
- evitar sobrescrever silenciosamente uma entrega ja enviada.

Antes da entrega final, a revisao pode regenerar os nomes oficiais depois de
criar snapshot ou manifesto da versao anterior. Depois de uma entrega enviada,
o pacote revisado deve ser gerado em pasta/versionamento separado ate o Gate R.

Nome recomendado do registro:

```text
<CODIGO>_<GRUPO>_<OPERACAO>_REV_R01.md
```

## Gate R — Aprovacao Final

Toda revisao termina com uma apresentacao objetiva:

- o que foi solicitado;
- o que foi alterado;
- o que foi regenerado por dependencia;
- comparacao antes/depois;
- validadores executados;
- pendencias remanescentes.

Depois da aprovacao do usuario:

- promover a versao revisada para a pasta final, quando necessario;
- atualizar manifesto, hashes e lastro;
- atualizar operacao, dossie, recipe ou pattern afetado;
- marcar o registro como `review_completed`.

## Estados De Revisao

| Estado | Significado |
| --- | --- |
| `review_planned` | Revisao futura registrada, ainda sem escopo executavel. |
| `review_scoping` | Linha de base, tipo e impacto em definicao. |
| `awaiting_review_scope_approval` | Escopo/impacto aguardando confirmacao. |
| `revising_data` | Dados e cadeia posterior em correcao. |
| `revising_taxonomy` | Cadastro taxonomico e dependencias em correcao. |
| `revising_analysis` | Metodo, calculo ou produtos analiticos em correcao. |
| `revising_text` | Narrativa, legendas ou evidencias em correcao. |
| `revising_layout` | Apresentacao visual em correcao. |
| `revising_package` | Pacote, nomes, links ou manifesto em correcao. |
| `validating_revision` | Revisao concluida tecnicamente e em auditoria. |
| `awaiting_revision_approval` | Gate R aguardando usuario. |
| `review_completed` | Revisao aprovada, promovida e documentada. |

## Revisao Completa

Quando o usuario pedir "revisao completa":

1. executar primeiro uma auditoria sem alterar arquivos;
2. classificar achados por tipo, impacto e severidade;
3. separar erro confirmado de hipotese de revisao;
4. apresentar o plano de correcao;
5. executar depois da confirmacao quando houver mudanca de alto impacto.

Para DOCX e relatorios consolidados, o protocolo especializado
[PROTOCOLO_REVISAO_RELATORIOS.md](../PROTOCOLO_REVISAO_RELATORIOS.md) pode ser
usado como ferramenta dentro desta etapa.

## Exemplos Rapidos

### Ajuste de layout

Pedido: "No VIRITA001, aumente os titulos e ajuste a legenda."

- tipo: `layout`;
- impacto: `R1`;
- Gates A e B permanecem validos;
- Gate C so reabre se houver troca de template ou paleta;
- regenerar figuras e HTML afetados;
- atualizar manifesto;
- apresentar antes/depois no Gate R.

### Correcao taxonomica

Pedido: "A especie estava identificada com `cf.` e deve ficar sem o
qualificador."

- tipo: `taxonomy`;
- impacto: `R3`;
- reabrir Gate B;
- verificar se a alteracao afeta resultados migrados e consolidado;
- regenerar tabelas, graficos, Darwin Core, texto e manifesto dependentes;
- apresentar os novos totais e produtos no Gate R.

### Divergencia numerica

Pedido: "A abundancia do ponto P03 parece incorreta."

- iniciar como revisao `full` do item, sem alterar dados;
- comparar planilha, banco, consolidado e base analitica;
- se o erro estiver na fonte/banco: `data/R3` e Gate A;
- se o erro estiver apenas no calculo: `analysis/R2`;
- regenerar toda a cadeia dependente;
- apresentar causa, antes/depois e validadores no Gate R.
