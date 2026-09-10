# WSPKIN001 — Zoobentos — Tipo de amostragem REV R01

- projeto: WSPKIN001
- operacao de origem: `docs/control_center/operations/WSPKIN001_ZOOBENTOS_MIGRACAO.md`
- estado atual: `awaiting_revision_approval`
- tipo: `data` e `analysis`
- impacto: `R3`
- estado: `awaiting_revision_approval`
- linha de base: pacote `Resultados\Zoobentos`, auditoria `20260909T111841_geracao_resultados_zoobentos_a4_paisagem.json`

## Linha De Base

- pacote oficial anterior em `Resultados\Zoobentos`;
- auditoria `20260909T111841_geracao_resultados_zoobentos_a4_paisagem.json`.

## Diagnóstico

- fonte: 89 registros quantitativos e 63 qualitativos.
- chuva: 25 quantitativos (total 52) e 35 qualitativos (35 presenças).
- seca: 64 quantitativos (total 234) e 28 qualitativos (28 presenças).
- causa: o migrador inferiu o tipo pelo valor de indivíduos e sobrescreveu o campo explícito; todas as 152 linhas foram gravadas como quantitativas.
- impacto: banco, consolidado, análises, Darwin Core, HTML e pacote completo.
- pacote atual: bloqueado para uso.

## Escopo proposto

1. preservar o `Tipo_de_Amostragem` explícito, com backup e remigração;
2. ambos os tipos em composição, ocorrência e riqueza observada;
3. somente quantitativos em abundância, relativa, diversidade e Bray-Curtis;
4. ambos em BMWP por presença de famílias; somente quantitativos nos percentuais EPT/CHOL;
5. somente unidades quantitativas na suficiência amostral;
6. regenerar tudo em versão revisada, validar e submeter ao Gate R.

## Progresso

- diagnostico: concluido;
- correcao de dados e migrador: concluida;
- regeneracao e validacao: concluidas;
- aprovacao final: pendente no Gate R.

## Resultado

- escopo aprovado pelo usuário em 2026-09-09.
- remigração: 152 linhas preservadas; 89 quantitativas e 63 qualitativas.
- abundância quantitativa: 286; valores qualitativos preservados como presença.
- pacote oficial substituído por autorização explícita do usuário.
- validação: 16/16 figuras válidas, zero erros; manifesto confirma 89/63 e abundância 286.
- composição: 41 táxons, BMWP completo e tipos `Qualitativa`, `Quantitativa` ou ambos.

## Prevencao De Recorrencia

- migrador preserva o tipo explicito, valida resultado x esforco e inclui
  reconciliacao por campanha/tipo no plano de carga;
- dry-run confirmou 152/152 linhas, 89 quantitativas, 63 qualitativas e totais
  quantitativos 52 (chuva) + 234 (seca);
- Gates A, C e R foram reforcados pela politica
  `AQUATIC_SAMPLING_TYPE_POLICY.md`.

## Gate R

Status: aguardando aprovação do usuário.
