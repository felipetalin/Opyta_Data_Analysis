# Linguagem Técnica Rastreável

## Status

- status: aprovado
- criado em: 2026-06-20
- aprovado em: 2026-06-20
- projeto piloto: `GEOHER001__monitoramento_de_ictio_e_bentos_herculano`
- grupo piloto: Zoobentos
- referência editorial: relatório consolidado de Bentos entregue ao cliente

## Problema

Geradores HTML anteriores misturam conteúdo, números, interpretação e layout em
um único script. Isso dificulta atualizar os valores, revisar a proporcionalidade
das conclusões e identificar qual planilha sustenta cada afirmação.

## Estrutura Obrigatória

Cada tema deve ser estruturado pelo sistema em cinco camadas:

1. resultado observado;
2. comparação espacial, temporal ou entre grupos;
3. interpretação tecnicamente compatível;
4. limitação da evidência;
5. implicação ou recomendação para o monitoramento.

Nem todas as camadas precisam aparecer como parágrafos separados. Evidências e
limitações podem permanecer na camada técnica de auditoria, enquanto o corpo do
relatório apresenta uma narrativa direta. Resultado e interpretação não devem
ser apresentados como se fossem a mesma coisa.

## Níveis De Inferência

| Nível | Verbos preferenciais | Uso |
| --- | --- | --- |
| Descritivo | registrou, apresentou, variou, ocorreu | observação direta |
| Comparativo | foi superior, foi menor, concentrou | comparação sem teste causal |
| Interpretativo | é compatível, sugere, pode estar associado | significado ecológico proporcional |
| Recomendação | recomenda-se, merece acompanhamento | implicação de gestão |
| Causal | causou, provocou, decorreu de | somente com desenho causal explícito |

## Regras

- Toda afirmação numérica deve ter arquivo-fonte.
- Todo parágrafo deve apontar uma ou mais evidências.
- Interpretações devem registrar limitações na evidência, sem necessidade de
  repeti-las em todos os parágrafos visíveis.
- Percentuais devem ser lidos com seus denominadores.
- Ausência de registro não equivale automaticamente à ausência ecológica.
- Diferença visual não equivale à diferença estatisticamente significativa.
- Indicadores biológicos não devem ser interpretados isoladamente como prova de
  causa ou impacto.
- O nível taxonômico deve ser respeitado; usar “táxon” quando a identificação não
  alcançar espécie.
- Nomes científicos devem ser apresentados em itálico.
- A narrativa principal deve evitar metalinguagem e frases defensivas
  recorrentes.
- O lastro de auditoria não deve tornar o texto mecânico ou interromper sua
  fluidez.

## Arquitetura

- modelos: `src/opyta_analysis/textual/models.py`
- validação: `src/opyta_analysis/textual/validation.py`
- HTML: `src/opyta_analysis/textual/html.py`
- piloto:
  `scripts/projects/geoher001/generate_bentos_textual_pilot.py`

## Saídas Do Piloto

Em `outputs/_scratch/textual_pilot_geoher001`:

- `relatorio_piloto_geoher001_bentos.html`;
- `evidencias_geoher001_bentos.json`;
- `validacao_textual_geoher001_bentos.json`;
- `calibracao_relatorio_referencia.md`.

## Aprovação

O piloto foi aprovado após revisão humana do HTML e confirmação de que o tom,
a organização e a legibilidade representam a linguagem técnica desejada pela
Opyta. A validação final registrou zero erros e zero avisos.

A aplicação em um segundo grupo biológico permanece como etapa de ampliação da
base de validação, sem impedir o uso do padrão aprovado em novos relatórios.

## Desdobramento Editorial

Em 2026-06-21 foi criado o documento
`docs/PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md` para formalizar a regua evolutiva
de redacao da Opyta e governar a geracao automatica posterior ao fechamento
analitico. Este pattern registra a abordagem tecnica rastreavel; o documento
mestre concentra a policy de voz, inferencia, limitacao e recomendacao.
