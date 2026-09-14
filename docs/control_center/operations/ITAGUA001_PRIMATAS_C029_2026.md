# ITAGUA001 - Primatas - C029/2026

## Controle

- projeto: ITAGUA001 / Monitoramento da Fauna
- grupo: Primatas
- operacao: resultados da campanha C029/Julho-2026 a partir do subconjunto de Mastofauna
- estado atual: `reviewing_outputs`
- aberta em: 2026-08-04
- atualizada em: 2026-08-04
- proxima acao: revisar pacote final C029/Primatas

## Caminhos

- dados origem: base migrada de Mastofauna C029 (`resultados_mastofauna`)
- saida: `G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\29_campanha_Jul_26\Primatas`
- runner: `scripts/run/fauna/run_primatas_multi_empreendimentos_c029.py`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Primatas tratados como programa/produto proprio a partir dos registros de Mastofauna. |
| Validacao | concluida | Filtro C029 aplicado no pipeline; recorte com 12 registros, 40 individuos e 3 taxons. |
| Gate A - dados | aprovado | Dados de Mastofauna C029 ja aprovados; primatas preservados no banco para programa proprio. |
| Cadastro de especies | concluido | `Callicebus personatus`, `Callithrix geoffroyi` e `Sapajus nigritus` constam no cadastro. |
| Auditoria de atributos | concluida | Tabela 6.3 validada sem vazios usando `Distribuicao` no lugar de `Origem`. |
| Gate B - especies | aprovado | CITES II de `Callicebus personatus` e `Sapajus nigritus` havia sido aprovado na Mastofauna. |
| Configuracao das analises | concluida | Runner C029 criado; output em `29_campanha_Jul_26\Primatas`; layout C029 aplicado. |
| Geracao dos produtos | concluida | 4 pastas geradas; cada uma com 2 PNG + 2 XLSX; auxiliares removidos. |
| Revisao tecnica | concluida | Figura 17 e Venn revisados visualmente; planilhas de composicao/status validadas. |
| Fechamento | pendente | Aguardando aprovacao final do usuario. |

## Totais C029

- registros primatas brutos/preparados: 12 / 12
- individuos: 40
- taxons: 3
- especies:
  - `Callicebus personatus`: 36 individuos
  - `Callithrix geoffroyi`: 3 individuos
  - `Sapajus nigritus`: 1 individuo
- distribuicao por empreendimento:
  - Fortuna II: 4 individuos
  - Jacare: 9 individuos
  - Senhora do Porto: 27 individuos
  - Dores de Guanhaes: 0 individuos
  - Area Controle: 0 individuos

## Produtos

- por pasta de empreendimento:
  - `fig17_abundancia_registros_primatas_campanha.png`
  - `fig17_tabela_composicao_primatas.xlsx`
  - `6_2_prim_diagrama_venn_pch_vs_controle.png`
  - `6_3_tabela_status_ecologico_primatas.xlsx`

## Pendencias

- Revisao/aprovacao final do usuario.

## Fechamento E Aprendizados

- Primatas devem ser mantidos no banco dentro da origem Mastofauna, mas excluidos dos produtos de Mastofauna e tratados no pipeline/produto Primatas.
- O pipeline de Primatas deve sempre receber filtro de campanha para evitar mistura C028/C029.
- Rótulos e tabelas devem usar português brasileiro com acentos.
