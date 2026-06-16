# Sistema De Aprendizado

O objetivo e fazer cada analise melhorar as proximas.

## O Que Registrar

Cada projeto deve capturar:

- problemas encontrados nos dados;
- ajustes de nomenclatura;
- decisoes visuais;
- graficos rejeitados e motivo;
- graficos aprovados e contexto;
- calculos corrigidos;
- limitacoes do pipeline;
- scripts temporarios que precisam virar produto;
- perguntas que ficaram abertas.

## Tipos De Memoria

| Tipo | Onde fica | Exemplo |
| --- | --- | --- |
| Dossie de projeto | `docs/projects` | Recorte GEOHER001 2022-2025 |
| Pattern | `docs/patterns` | Minigraficos temporais |
| Portfolio | `docs/control_center/PORTFOLIO.md` | Series longas bentos/ictio |
| Decisao | `docs/projects` ou `docs/decisions` | Trocar heatmap por minigraficos |
| Lastro de execucao | `outputs/_project_scripts` | Metadata e reproducer |
| Codigo reutilizavel | `src/opyta_analysis` | Funcoes promovidas |

## Perguntas Obrigatorias Antes De Rodar Analise

1. Qual e a `canonical_key` do projeto?
2. Existe portfolio aplicavel?
3. Existe pattern aprovado?
4. Algum padrao antigo foi rejeitado para esse caso?
5. Qual sera o output final e qual sera o lastro tecnico?

## Perguntas Obrigatorias Depois De Rodar

1. O que foi aprovado?
2. O que foi rejeitado?
3. O que deve virar pattern?
4. O que deve virar backlog?
5. O que precisa ser lembrado em analises futuras?
