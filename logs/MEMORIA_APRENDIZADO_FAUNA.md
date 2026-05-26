# Memoria de aprendizado - Fauna

Data: 2026-05-25

## Diagnostico

Os pipelines de fauna ja tinham boa base operacional: blocos por grupo,
padrao visual centralizado, scripts reprodutores e metadados por execucao.
O ponto fraco era o lastro: algumas memorias antigas registravam zero arquivos
gerados mesmo quando havia entregaveis no Drive, e nao havia contexto git nem
hashes dos artefatos.

## Ajustes incorporados

- Runner atualizado para registrar branch, commit, dirty status e hashes dos
  arquivos gerados.
- `zoobentos` passou a devolver `rows_loaded`, mantendo `records` por
  compatibilidade.
- Criado nucleo de auditoria em `opyta_analysis.fauna.audit`.
- Criado script `scripts/validar_fauna_outputs.py`.
- Criada documentacao operacional em `docs/README_FAUNA_AUDITORIA.md`.
- Auditoria passou a reconhecer aliases de pastas antigas/operacionais, como
  `Fitoplancton -> Fito` e `Zoobentos -> Bentos`, registrando o alias usado
  sem alterar a memoria original.
- O cliente `fersam001` passou a declarar `audit_project_slug="sam_metais"`,
  garantindo que novas memorias de fauna caiam no mesmo lastro oficial do
  projeto.
- O contexto git separa sujeira de codigo/configuracao dos arquivos gerados em
  `outputs/_project_scripts`, para que a propria auditoria nao contamine novas
  execucoes.

## Regra operacional

Para fauna, nenhuma entrega deve ser considerada fechada apenas pela existencia
dos `.xlsx` ou `.png` no Drive. O fechamento exige um manifesto de auditoria
com status conhecido:

- `OK`: memoria e arquivos coerentes;
- `OK_WITH_WARNINGS`: revisar memoria antiga ou incompleta;
- `ERROR`: corrigir antes de entregar.

## Proximo refinamento recomendado

Centralizar metricas ecologicas comuns em um modulo compartilhado de fauna
antes de ampliar novas migracoes. Prioridade: riqueza, abundancia, Shannon,
Pielou, Bray-Curtis/Jaccard, curva de suficiencia e exportacao DarwinCore.
