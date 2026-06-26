# VIRITA001 — Ictiofauna — Campanha 1

## Controle

- projeto: `VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`
- grupo: Ictiofauna
- operacao: Campanha 1
- estado atual: `awaiting_revision_approval`
- aberta em: 2026-06-22
- atualizada em: 2026-06-26
- proxima acao: aprovar as revisoes R01 e R02 no Gate R

## Caminhos

- dados e especies:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Campanha/Junho 26/Planilha`
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Virtual/São Gonçalo/Resultados/Ictiofauna/Campanha_1`
- dossie:
  `docs/projects/VIRITA001_ITABRITA_ICTIOFAUNA.md`
- recipe:
  `configs/projects/virita001_itabrita_ictiofauna.json`
- lastro:
  `outputs/_project_scripts/VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto, grupo, origem e saida definidos. |
| Validacao | concluida | Pacote corrigido sem bloqueios. |
| Gate A — dados | aprovado | Usuario autorizou seguir com migracao apos os ajustes apresentados. |
| Cadastro de especies | concluido | Sete especies novas cadastradas. |
| Auditoria de atributos | concluida | Ajustes de `Rhamdiopsis microcephala`, `Hypostomus francisci` e `Cichlasoma sanctifranciscense` aplicados. |
| Gate B — especies | aprovado | Usuario definiu as correcoes taxonomicas/ecologicas e autorizou a migracao. |
| Migracao | concluida | 132 individuos, 15 especies e 20 registros agregados. |
| Consolidacao | concluida | Backup criado e 20 linhas do projeto auditadas no consolidado. |
| Configuracao das analises | concluida | Template FERSAM001 para ate duas campanhas; paleta verde; pasta de saida confirmada. |
| Gate C — analises | aprovado | Usuario definiu referencia, numero de campanhas e destino. |
| Geracao dos produtos | concluida | 30 produtos declarados no manifesto. |
| Revisao tecnica | concluida | Zero arquivos ausentes e zero divergencias de hash. |
| Revisao R01 de dados | concluida tecnicamente | Campanha corrigida para `C001-2026-06-SC`; 7 esforcos, 19 resultados agregados, 132 individuos; pacote revisado validado. |
| Revisao R02 de biometria | concluida tecnicamente | Tabela 13 de biometria e biomassa adicionada; HTML e manifesto atualizados; auditoria oficial `OK`. |
| Revisao de layout | pendente | Usuario aprovou o conjunto e registrou ajustes pontuais para uma rodada futura. |
| Fechamento | pendente | Encerrar depois da revisao visual final. |

## Revisoes

| Revisao | Tipo previsto | Impacto previsto | Estado | Registro |
| --- | --- | --- | --- | --- |
| R01 | `data` | `R3` | `awaiting_revision_approval` | [VIRITA001_ICTIOFAUNA_CAMPANHA_1_REV_R01.md](../reviews/VIRITA001_ICTIOFAUNA_CAMPANHA_1_REV_R01.md) |
| R02 | `analysis/package` | `R2` | `awaiting_revision_approval` | [VIRITA001_ICTIOFAUNA_CAMPANHA_1_REV_R02.md](../reviews/VIRITA001_ICTIOFAUNA_CAMPANHA_1_REV_R02.md) |
| R03 | `layout` | `R1` | `review_planned` | Criar quando houver lista executavel de ajustes visuais. |

Regra para R01:

- preservar a entrega de 2026-06-22 como linha de base;
- reabrir Gate A porque a revisao altera fonte, esforco, tipo de amostragem e
  nomenclatura de campanha;
- nao reabrir Gate B se nenhuma especie ou atributo taxonomico for alterado;
- nao executar upsert do cadastro incremental de especies, pois as sete
  especies ja existem no banco;
- apos aprovacao do escopo, corrigir a planilha fonte, validar, remigrar,
  consolidar e regenerar todos os produtos dependentes;
- apresentar comparacao antes/depois no Gate R.

Regra para R02:

- preservar o pacote R01 como linha de base;
- nao reabrir Gate A ou B;
- nao reabrir Gate C porque a tabela biometrica segue o metodo ja aprovado e
  usa a planilha validada linha a linha;
- regenerar tabela derivada, HTML, manifesto e lastro;
- apresentar comparacao antes/depois no Gate R.

Regra para R03:

- preservar o manifesto e os produtos atuais como linha de base;
- nao reabrir Gate A ou B;
- reabrir Gate C somente se houver troca de paleta, template ou conjunto de
  produtos previamente aprovado;
- regenerar apenas figuras, HTML e manifesto dependentes dos ajustes;
- apresentar comparacao antes/depois no Gate R.

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A — dados | `approved` | Aprovacao para seguir com migracao em 2026-06-22. |
| B — especies | `approved` | Correcoes informadas e aprovacao para migrar em 2026-06-22. |
| C — analises | `approved` | Padrao FERSAM001 para duas campanhas e pasta de saida confirmados em 2026-06-22. |

## Pendencias

- aprovar as revisoes R01 e R02 no Gate R;
- ajustes pontuais de layout no HTML e/ou figuras;
- registrar a segunda campanha quando os dados forem recebidos;
- apos a segunda campanha, regenerar os produtos comparativos no mesmo template.
