# Linguagem Técnica Rastreável

## Status

- status: candidato
- criado em: 2026-06-20
- projeto piloto: `GEOHER001__monitoramento_de_ictio_e_bentos_herculano`
- grupo piloto: Zoobentos
- referência editorial: relatório consolidado de Bentos entregue ao cliente

## Problema

Geradores HTML anteriores misturam conteúdo, números, interpretação e layout em
um único script. Isso dificulta atualizar os valores, revisar a proporcionalidade
das conclusões e identificar qual planilha sustenta cada afirmação.

## Estrutura Obrigatória

Cada tema deve ser redigido em cinco camadas:

1. resultado observado;
2. comparação espacial, temporal ou entre grupos;
3. interpretação tecnicamente compatível;
4. limitação da evidência;
5. implicação ou recomendação para o monitoramento.

Nem todas as camadas precisam ocupar parágrafos separados, mas resultado e
interpretação não devem ser apresentados como se fossem a mesma coisa.

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
- Interpretações devem registrar limitações.
- Percentuais devem ser lidos com seus denominadores.
- Ausência de registro não equivale automaticamente à ausência ecológica.
- Diferença visual não equivale à diferença estatisticamente significativa.
- Indicadores biológicos não devem ser interpretados isoladamente como prova de
  causa ou impacto.
- O nível taxonômico deve ser respeitado; usar “táxon” quando a identificação não
  alcançar espécie.
- Nomes científicos devem ser apresentados em itálico.

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

## Critério Para Promoção

O padrão poderá passar para `approved` após:

1. revisão técnica do HTML piloto;
2. confirmação de que o tom representa a linguagem desejada pela Opyta;
3. validação de pelo menos um segundo grupo biológico;
4. incorporação das correções editoriais resultantes da revisão humana.

## Desdobramento Editorial

Em 2026-06-21 foi criado o documento
`padrao_redacao_tecnica_rastreavel_opyta_v1.md` para formalizar a regua de
redacao da Opyta antes da automacao plena no pipeline. Este pattern permanece
como guarda-chuva tecnico da abordagem; o documento v1 concentra a politica de
voz, inferencia, limitacao e recomendacao.
