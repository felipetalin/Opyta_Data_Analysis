# Politica De Tipos De Amostragem Em Biota Aquatica

Esta politica e obrigatoria quando uma base combina amostragem qualitativa e
quantitativa. O objetivo e impedir que presenca qualitativa seja convertida em
abundancia ou que um tipo explicito seja sobrescrito durante a migracao.

## Regra De Origem

- Preservar o tipo de amostragem explicitamente informado na fonte.
- Inferir o tipo somente quando o campo nao existir, com regra documentada e
  aprovada no Gate A.
- Valor numerico em registro qualitativo representa presenca; nao deve compor
  abundancia, densidade, diversidade quantitativa ou similar.
- Resultado e esforco devem concordar em projeto, campanha, ponto, metodo e
  tipo de amostragem.

## Gate A — Reconciliacao Obrigatoria

Apresentar, por grupo, campanha, metodo e tipo:

- linhas na fonte;
- linhas preparadas para migracao;
- total da medida quantitativa ou numero de presencas qualitativas;
- registros sem tipo, com tipo invalido ou incompativeis com o esforco.

O Gate A fica bloqueado se dois ou mais tipos presentes na fonte forem
colapsados em um unico tipo na preparacao.

## Migracao E Consolidacao

A carga deve falhar fechada quando ocorrer qualquer uma destas condicoes:

- tipo explicito alterado ou sobrescrito;
- tipo ausente ou fora do vocabulario aprovado;
- incompatibilidade entre resultado e esforco;
- divergencia dos totais por tipo entre fonte, preparacao, banco e consolidado;
- inclusao de presenca qualitativa em total quantitativo.

O plano de migracao deve registrar a reconciliacao por tipo antes da escrita.

## Gate C — Matriz Produto Por Tipo

O Gate C deve aprovar uma matriz que diga quais tipos alimentam cada produto.
Na ausencia de decisao especifica, usar:

| Produto | Qualitativo | Quantitativo | Regra |
| --- | --- | --- | --- |
| Composicao e ocorrencia | sim | sim | presenca por unidade amostral |
| Riqueza observada | sim | sim | informar que agrega os dois tipos |
| Abundancia e abundancia relativa | nao | sim | usar somente medida quantitativa |
| Diversidade e similaridade quantitativas | nao | sim | usar somente unidades quantitativas |
| Suficiencia amostral quantitativa | nao | sim | excluir unidades apenas qualitativas |
| Indices bioticos por presenca | conforme metodo | conforme metodo | decisao explicita no Gate C |
| Indicadores percentuais de abundancia | nao | sim | denominador exclusivamente quantitativo |
| Darwin Core/base de ocorrencia | sim | sim | preservar o tipo em campo rastreavel |

Qualquer excecao deve ser registrada na operacao e aprovada pelo usuario.

## Gate R — Validacao Bloqueante

O manifesto ou validador final deve informar e reconciliar:

- linhas qualitativas e quantitativas;
- presencas qualitativas;
- total quantitativo;
- tipos efetivamente usados por produto;
- fonte, banco, consolidado e pacote final.

Uma divergencia nesses controles bloqueia a entrega e reabre o gate afetado.
