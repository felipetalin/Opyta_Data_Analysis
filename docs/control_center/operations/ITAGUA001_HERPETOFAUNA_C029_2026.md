# ITAGUA001 - Herpetofauna - C029/2026

## Controle

- projeto: ITAGUA001 / Monitoramento da Fauna
- grupo: Herpetofauna
- operacao: validacao, migracao e resultados da campanha C029/Julho-2026
- estado atual: `reviewing_outputs`
- aberta em: 2026-08-03
- atualizada em: 2026-08-03
- proxima acao: revisar pacote final C029/Herpetofauna

## Caminhos

- dados: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\29_campanha_Jul_26\Planilha_de_Campo\1.ITA-GUA-Dados_brutos-Herpetofauna-Campanha_29.xlsx`
- cadastro de especies: aba `Cadastro_Especies`
- saida: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\29_campanha_Jul_26\Herpetofauna`
- dossie: nao aberto nesta etapa
- recipe: nao identificado no registry filtrado
- lastro: nao aberto nesta etapa

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Planilha localizada na pasta `Planilha_de_Campo`. |
| Validacao | concluida | Chaves C029 corrigidas; coordenadas com simbolo de grau convertidas para decimal; sem bloqueios. |
| Gate A - dados | aprovado | Usuario aprovou em 2026-08-03; dados C029 validados. |
| Cadastro de especies | concluido | Todos os 21 taxons dos resultados aparecem na aba `Cadastro_Especies`; 4 novos serao cadastrados/atualizados. |
| Auditoria de atributos | concluida | Campos obrigatorios sem vazio apos ajuste; `cf.` e `aff.` aceitos como identificacoes abertas. |
| Gate B - especies | aprovado | Usuario aprovou `Hylodes cf. uai` e `Scinax aff. perereca`; `Status_COPAM` ajustado. |
| Migracao | concluida | Carga C029 executada e auditada; 45 esforcos, 81 resultados, 279 individuos, 21 taxons. |
| Consolidacao | concluida | Backup criado e consolidado reprocessado; recorte C029/Herpetofauna auditado. |
| Configuracao das analises | concluida | Gate C aprovado pelo usuario em 2026-08-03. |
| Gate C - analises | aprovado | Usar pasta C029/Herpetofauna e padrao visual aprovado no ciclo. |
| Geracao dos produtos | concluida | Pacote C029 regenerado apos revisao da tabela 6.6/6.8; filtro de campanha robusto; auxiliares removidos. |
| Revisao tecnica | concluida | 4 pastas validadas com 8 PNG + 10 XLSX; tabela 6.6/6.8 por empreendimento + area controle e sem vazios. |
| Revisao de layout | em andamento | Amostra 6.1 revisada sem mojibake e com folga para legenda. |
| Revisao tabela status | concluida | `Cadastro_Especies` nao possui colunas `Origem`/`Distribuicao`; migrador ajustado para preencher Herpetofauna como `Nativa` quando ausente; banco reprocessado e tabela 6.6/6.8 temporaria validada sem vazios. |
| Revisao Venn PT-BR | concluida | Diagrama de Venn regenerado com acentos em portugues brasileiro (`Área`, `Espécies`, `Espécie`, `ESPÉCIES`). |
| Fechamento | pendente | |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Usuario: "Aprovado" em 2026-08-03. |
| B - especies | `approved` | Usuario aprovou identificacoes abertas e ajustou `Status_COPAM`. |
| C - analises | `approved` | Usuario aprovou em 2026-08-03. |

## Validacao Dos Dados

- bloqueios: nenhum apos leitura correta das coordenadas com simbolo de grau
- validado:
  - `Pontos_e_Campanhas`: 45 linhas em `29ª-jul-26-SC`
  - `Metadados_Esforco`: 45 linhas em `29ª-jul-26-SC`
  - `Resultados_Herpetofauna`: 81 linhas em `29ª-jul-26-SC`
- avisos:
  - arquivo corrigido agora indica `Campanha_29`
  - todos os 21 taxons dos resultados aparecem em `Cadastro_Especies`
  - chaves resultado -> ponto/esforco sem faltantes apos correcao; `CON2 / Pitfall` presente
  - coordenadas estao em decimal com simbolo de grau (`°`); migrador foi ajustado para converter para numero
- coordenadas:
  - fonte espacial oficial: pendente
  - CRS/sistema: pendente
  - pontos sem coordenada: 0 apos conversao do simbolo de grau
  - coordenadas fora da faixa esperada: 0 na faixa global; faixa C029 lat -19.0798141 a -18.875429, lon -42.957791 a -42.636944
  - variacao por ponto/campanha: pendente
  - comparacao com KMZ/KML/shapefile/planilha oficial: pendente
  - estrategia aprovada no Gate A: pendente
- ajustes aplicados: nenhum
- arquivos corrigidos: `G:\Meu Drive\Opyta\Opyta_Data\scripts\migrar_herpetofauna.py` preparado para converter coordenadas decimais com `°`

## Cadastro E Auditoria De Especies

- especies novas: 4 taxons dos resultados ainda nao constam no banco: `Boana crepitans`, `Bokermannohyla gr. circumdata`, `Leposternon microcephalus`, `Xenodon neuwiedii`
- atributos obrigatorios: sem campos vazios apos ajuste; `origem` e `distribuicao` preenchidos como `Nativa` para Herpetofauna quando ausentes da aba `Cadastro_Especies`
- campos incertos: `Hylodes cf. uai` e `Scinax aff. perereca` aceitos como identificacoes abertas
- ajustes manuais: `Status_COPAM` ajustado pelo usuario

## Migracao E Consolidacao

- IDs: projeto 165 / ITAGUA001
- totais da fonte: preliminar resultados C029 = 81 linhas, 279 individuos, 21 taxons; `Cadastro_Especies` = 32 linhas
- totais no banco: 45 pontos/esforcos, 81 resultados, 279 individuos, 21 taxons
- coordenadas no banco/consolidado: pendente
- divergencias: nenhuma na comparacao Excel agregado x banco
- backup: `biota_analise_consolidada_bkp_itagua001_herpetofauna_c029_20260803_1449` com 24.358 linhas
- totais consolidados: global 24.439 linhas; C029/Herpetofauna = 81 linhas, 279 individuos, 21 taxons, 33 pontos com resultado

## Configuracao Das Analises

- numero de campanhas: C029 isolada para esta operacao
- template: diagnostico Herpetofauna por empreendimento, C029
- paleta: padrao aprovado no ciclo ITAGUA001
- pasta de saida: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\29_campanha_Jul_26\Herpetofauna`
- produtos: por empreendimento, 8 PNG e 10 XLSX; arquivos `.txt` e `desktop.ini` removidos do pacote final

## Pendencias

- Fechamento operacional apos aprovacao final do usuario.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: pendente
- manifesto: pendente
- patterns: pendente
- portfolio: pendente
- backlog: registrar que `Cadastro_Especies` de Herpetofauna pode nao trazer `Origem`/`Distribuicao`; para este grupo, quando ausentes, o migrador preenche ambos como `Nativa` seguindo o padrao dos demais taxons do banco.
