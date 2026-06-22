# Fluxo Operacional Da Central De Controle

Este e o caminho oficial para validacao, cadastro, migracao, consolidacao,
analises e entrega. Ele deve ser percorrido sempre que a Central de Controle for
acionada.

## Gatilhos Reconhecidos

- `center_control`
- `center_cotrol`
- `control_center`
- `central de controle`
- "seguir o fluxo operacional"

Ao reconhecer um gatilho, abrir nesta ordem:

1. [README.md](README.md)
2. [ACTIVE_OPERATIONS.md](ACTIVE_OPERATIONS.md)
3. registro da operacao em [operations](operations/README.md)
4. [project_registry.json](../registry/project_registry.json)
5. dossie em `docs/projects/`
6. recipe em `configs/projects/`
7. portfolio, patterns e lastros aplicaveis

## Fluxo Canonico

```text
ABERTURA
  |
  v
VALIDACAO DOS DADOS
  |
  v
GATE A — AJUSTE E APROVACAO DOS DADOS
  |
  v
CADASTRO E AUDITORIA DE ESPECIES
  |
  v
GATE B — AJUSTE E APROVACAO TAXONOMICA
  |
  v
MIGRACAO
  |
  v
CONSOLIDACAO
  |
  v
CONFIGURACAO DAS ANALISES
  |
  v
GATE C — TEMPLATE + PALETA + PASTA DE SAIDA
  |
  v
GERACAO DOS PRODUTOS
  |
  v
REVISAO VISUAL E TECNICA
  |
  v
FECHAMENTO E APRENDIZADO
```

## Etapas E Evidencias

| Etapa | Acao obrigatoria | Evidencia minima | Proximo estado |
| --- | --- | --- | --- |
| 0. Abertura | Confirmar projeto, grupo, campanhas, entradas, saida e operacao | Registro da operacao criado | `validating` |
| 1. Validacao | Validar estrutura, chaves, esforco, resultados, taxonomia e totais | Relatorio de validacao e lista de ajustes | `awaiting_data_approval` |
| Gate A | Aplicar ajustes permitidos e apresentar o pacote corrigido | Aprovacao explicita do usuario | `registering_species` |
| 2. Especies | Identificar especies novas, cadastrar e auditar todos os atributos exigidos | Relatorio de completude taxonomica | `awaiting_species_approval` |
| Gate B | Resolver campos incertos, endemismo, origem, ameaca e demais atributos | Aprovacao explicita do usuario ou registro `nao aplicavel` | `ready_to_migrate` |
| 3. Migracao | Executar carga controlada e comparar fonte com banco | Totais Excel x banco, IDs e divergencias | `consolidating` |
| 4. Consolidacao | Criar backup, consolidar e auditar a fatia do projeto | Nome do backup e comparacao base x consolidado | `configuring_analysis` |
| 5. Configuracao | Propor template pelo numero de campanhas, paleta, pasta de saida e produtos | Mapa de decisao analitica | `awaiting_analysis_approval` |
| Gate C | Confirmar template, paleta e pasta de saida | Aprovacao explicita do usuario | `generating_products` |
| 6. Geracao | Gerar bases, tabelas, graficos, HTML e manifesto | Produtos e lastro reprodutivel | `reviewing_outputs` |
| 7. Revisao | Conferir numeros, texto, layout e integridade | Validadores, hashes e pendencias visuais | `completed` ou `reviewing_layout` |
| 8. Fechamento | Atualizar dossie, registries, patterns, portfolio e backlog | Registro da operacao encerrado | `completed` |

## Portoes De Aprovacao

### Gate A — Dados

Antes de cadastrar especies ou migrar:

- apresentar erros, avisos e correcoes realizadas;
- preservar os arquivos originais;
- identificar qualquer ajuste que dependa de criterio tecnico do usuario;
- registrar a mensagem ou decisao que autorizou o avanco.

### Gate B — Especies

Antes de migrar:

- confirmar que todas as especies usadas nos resultados existem no cadastro;
- verificar se os atributos obrigatorios foram preenchidos;
- destacar taxons novos, `cf.`, `aff.`, `sp.`, endemismo, origem, ameaca e
  qualquer campo incerto;
- permitir ajustes manuais do usuario;
- registrar a aprovacao taxonomica.

Se nao houver especies novas, o gate continua existindo e deve ser registrado
como `nao aplicavel — cadastro ja completo`, com a auditoria correspondente.

### Gate C — Analises

Antes da geracao em lote, confirmar conjuntamente:

1. template adequado ao numero de campanhas;
2. paleta ou identidade visual;
3. pasta final de saida;
4. produtos esperados e formato do relatorio.

O pipeline pode propor defaults a partir do portfolio, mas nao deve assumir a
aprovacao quando houver mais de uma escolha razoavel.

## Estados Operacionais

| Estado | Significado |
| --- | --- |
| `intake` | Operacao aberta, contexto ainda incompleto. |
| `validating` | Dados em validacao. |
| `awaiting_data_approval` | Gate A aguardando usuario. |
| `registering_species` | Cadastro e auditoria taxonomica em andamento. |
| `awaiting_species_approval` | Gate B aguardando usuario. |
| `ready_to_migrate` | Gates A e B concluídos. |
| `migrating` | Migracao em andamento. |
| `consolidating` | Consolidacao e auditoria em andamento. |
| `configuring_analysis` | Template, paleta, saida e produtos em definicao. |
| `awaiting_analysis_approval` | Gate C aguardando usuario. |
| `generating_products` | Bases, tabelas, figuras e relatorio em geracao. |
| `reviewing_outputs` | Auditoria numerica, textual e de arquivos. |
| `reviewing_layout` | Produtos corretos, com ajustes visuais pendentes. |
| `completed` | Operacao concluida e documentada. |
| `blocked` | Existe impedimento objetivo registrado. |

Esses estados descrevem a execucao. Eles nao substituem os estados de
maturidade `prototype`, `approved`, `reference` e `deprecated` usados por
patterns e portfolio.

## Regras De Avanco

- Apenas uma etapa fica marcada como atual no registro da operacao.
- Nenhum gate e considerado aprovado por silencio.
- A solicitacao explicita "siga com a migracao" vale como aprovacao dos gates
  anteriores somente quando os ajustes e pendencias ja tiverem sido
  apresentados ao usuario.
- Toda mudanca manual do usuario deve ser revalidada antes da migracao.
- Migracao deve falhar fechada se a validacao ou a auditoria taxonomica tiver
  bloqueios.
- Consolidacao deve ter backup ou estrategia de reversao registrada.
- Geracao final deve produzir manifesto ou inventario equivalente.
- Ajustes apenas de layout podem manter a operacao em `reviewing_layout` sem
  invalidar os resultados numericos ja auditados.

## Encerramento

Uma operacao so fica `completed` quando:

- os tres gates estiverem registrados;
- migracao e consolidacao tiverem auditoria, quando aplicaveis;
- produtos e validadores estiverem conferidos;
- dossie e registro da operacao estiverem atualizados;
- aprendizados reutilizaveis tiverem destino definido.
