# ITAGUA001 - Herpetofauna - Historico C009-C027

## Controle

- projeto: ITAGUA001 / Monitoramento da Fauna
- grupo: Herpetofauna
- operacao: migracao historica das campanhas C009 a C027
- estado atual: `awaiting_data_approval`
- aberta em: 2026-08-07
- atualizada em: 2026-08-10
- proxima acao: aprovar ou ajustar ressalvas da validacao final GOLDv7 antes da migracao

## Caminhos

- dados: `C:\Users\felip\OneDrive\Área de Trabalho\BD_GNE_Herpeto_GOLDv7.xlsx`
- cadastro de especies: aba `Cadastro_Especies`
- migrador: `G:\Meu Drive\Opyta\Opyta_Data\scripts\migrar_herpetofauna.py`
- registry: `docs/registry/project_registry.json` consultado por `ITAGUA001`
- dossie: nao aberto nesta etapa
- lastro: nao aberto nesta etapa

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Planilha GOLDv7 localizada; projeto ITAGUA001 confirmado no registry filtrado. |
| Validacao | reaberta | GOLDv7 validada; dry-run tecnico OK, mas auditoria criteriosa encontrou datas fora do mes/ano codificado pela campanha. |
| Gate A - dados | aguardando aprovacao | Sem datas ausentes e sem coordenadas ausentes; requer aprovacao explicita das datas que cruzam mes/ano da campanha ou novo ajuste. |
| Cadastro de especies | concluido | Todos os 97 taxons dos resultados constam na aba `Cadastro_Especies`. |
| Auditoria de atributos | reaberta | Campos principais preenchidos; GOLDv7 nao possui colunas `Origem` e `Distribuicao`. |
| Gate B - especies | aguardando aprovacao | Sem taxon ausente; `Origem` e `Distribuicao` exigem aprovacao para preenchimento padrao como `Nativa` ou reinclusao na planilha. |
| Migracao | pendente | Dry-run tecnico OK em 2026-08-10, sem gravacao; migracao real aguardando Gates A e B. |
| Consolidacao | pendente | |
| Configuracao das analises | pendente | |
| Gate C - analises | pendente | |
| Geracao dos produtos | pendente | |
| Revisao tecnica | pendente | |
| Fechamento | pendente | |

## Validacao Dos Dados

- campanhas na fonte: C009-2021-07-SC a C027-2026-01-CH
- campanhas ausentes na fonte: C028 e C029
- pontos: 618
- esforcos: 646
- resultados brutos: 9.770
- resultados agregados esperados pelo migrador: 2.376
- individuos: 18.336
- taxons: 97
- pontos faltantes nos resultados: 0
- esforcos faltantes nos resultados: 0
- especies sem cadastro: 0
- coordenadas ausentes: 0
- coordenadas fora da faixa global: 0
- datas ausentes/invalidas em pontos: 0
- datas de pontos fora do mes/ano codificado pela campanha: 28
- datas de resultados fora do mes/ano codificado pela campanha: 850 linhas
- duplicidade de chave ponto/campanha: 0
- duplicidade de chave esforco: 0

## Ressalvas De Data

Datas de pontos fora do mes/ano indicado no codigo da campanha:

| Campanha | Mes/ano esperado pelo codigo | Mes/ano das datas | Pontos |
| --- | --- | --- | --- |
| C015-2023-01-CH | 2023-01 | 2023-02 | 4 |
| C016-2023-04-SC | 2023-04 | 2023-05 | 4 |
| C019-2024-01-CH | 2024-01 | 2024-02 | 19 |
| C026-2025-10-CH | 2025-10 | 2025-09 | 1 |

Essas divergencias podem ser aceitaveis se a campanha de campo cruzou meses,
mas precisam de aprovacao explicita antes da migracao.

## Cadastro E Auditoria De Especies

- taxons usados: 97
- taxons no cadastro: 97
- taxons ausentes do cadastro: 0
- preenchidos em 97/97: `Nome_Cientifico`, `Grupo_Biologico`, `Reino`, `Filo`, `Classe`, `Ordem`, `Familia`, `Genero`, `Status_IUCN`, `Status_MMA`, `Status_COPAM`, `CITES`
- colunas ausentes na GOLDv7: `Origem`, `Distribuicao`
- identificacoes abertas preservadas conforme fonte

## Evento De Controle - 2026-08-07

- A migracao real foi tentada apos dry-run inicial aprovado, mas o banco bloqueou `data_hora_coleta` nula em `pontos_coleta`; a transacao foi revertida sem persistir dados.
- O migrador foi ajustado para interpretar datas ISO (`AAAA-MM-DD`) e intervalos contendo data ISO sem inverter mes/dia.
- O dry-run passou a validar datas de `Pontos_e_Campanhas` antes de qualquer gravacao.
- Novo dry-run bloqueou corretamente 2 pontos sem data na GOLDv2: `C014-2022-10-CH` / `DG2` e `C020-2024-04-SC` / `JAC1`.

## Evento De Controle - 2026-08-10

- GOLDv7 localizada em `C:\Users\felip\OneDrive\Área de Trabalho\BD_GNE_Herpeto_GOLDv7.xlsx`, modificada em 2026-08-10.
- Dry-run tecnico do migrador: OK, sem gravacao.
- Estrutura: abas obrigatorias presentes; 618 pontos, 646 esforcos, 9.770 resultados, 97 taxons, 18.336 individuos.
- Chaves: 0 pontos dos resultados sem cadastro, 0 esforcos dos resultados sem metadado, 0 duplicidades de ponto/campanha, 0 duplicidades de esforco.
- Coordenadas: 0 ausentes, 0 fora da faixa global, sinais coerentes para MG.
- Datas: 0 ausentes/invalidas em pontos, mas 28 pontos fora do mes/ano codificado pela campanha; resultados com 850 linhas na mesma condicao.
- Especies: 97 taxons usados e 97 cadastrados; nenhum taxon ausente. GOLDv7 nao possui colunas `Origem` e `Distribuicao`.

## Pendencias

- Aprovar explicitamente ou ajustar as datas que cruzam o mes/ano codificado pela campanha.
- Aprovar preenchimento padrao de `Origem` e `Distribuicao` como `Nativa` ou reincluir essas colunas na GOLDv7.
- Executar migracao somente apos Gates A e B liberados.
- Criar backup e consolidar.
- Auditar recorte historico no banco.

## Fechamento E Aprendizados

- pendente
