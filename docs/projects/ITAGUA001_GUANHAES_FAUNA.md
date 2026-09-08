# ITAGUA001 - Monitoramento da Fauna (Guanhães Energia)

Status: `prototype` — dossie minimo criado durante o piloto Gate C da
Campanha 29 de Ictiofauna. Nao promover para `active`/`reference` antes do
Gate R (autorizacao explicita do Felipe em 2026-09-08, condicao 9).

## Identidade Supabase

- `id_projeto`: `165`
- `codigo_interno_opyta`: `ITAGUA001`
- nome: `Monitoramento da Fauna`
- cliente/empreendedor: Guanhães Energia
- `canonical_key`: `ITAGUA001__monitoramento_da_fauna`
- registry: `docs/registry/project_registry.json` (entrada existente, status
  `reference` no registro geral do projeto — refere-se ao historico do
  projeto, nao a esta recipe/prototipo)

## Empreendimentos

Quatro PCHs da Guanhães Energia, cadastrados como `empreendimentos` do
projeto 165:

- Jacaré
- Senhora do Porto
- Dores de Guanhães
- Fortuna II

Jacaré → Senhora do Porto → Dores de Guanhães formam uma cascata no rio
Guanhães (montante → jusante); Fortuna II e isolada, no rio Corrente Grande
(referencia regional). Essa topologia e usada pelo pipeline historico de
estabilidade ([docs/PIPELINE_ICTIO_165.md](../PIPELINE_ICTIO_165.md)), que
**nao e reutilizado** nesta operacao de campanha unica.

## Central De Controle

- operacao: Ictiofauna — Campanha 29 (piloto colaborativo)
- registro: `docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029.md`
- diario do piloto:
  `docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_DIARIO_PILOTO.md`
- Gate A/B: fora do escopo deste piloto (conduzidos pelo Felipe antes da
  abertura)
- Gate C: aprovado com condicoes em 2026-09-08

## Recipe E Gerador

- recipe: `configs/projects/itagua001_guanhaes_ictiofauna.json` (`status: prototype`)
- client/paleta: `configs/clients/itagua001_guanhaes.json` (verde
  `#11420C`/`#6A8F63`/`#3F5F3B`, mesma identidade da Campanha 28)
- gerador: `ictio_partial`
  (`src/opyta_analysis/pipelines/diagnostico/ictio_partial.py`), blocos
  6.1-6.8, um run por empreendimento
- campanha: `C029-2026-08-SC` (rotulo real no Supabase para Ictiofauna;
  diverge do `C029-2026-07-SC` usado por Avifauna/Mastofauna)
- pasta de saida (confirmada pela usuaria em 2026-09-08, atalho de drive
  compartilhado):
  `G:/.shortcut-targets-by-id/1dfa3mDLQkCZuEErnRrnLm1tKG19ZAIjZ/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhães Energia/Resultados e análises/29_campanha_Jul_26/Ictiofauna/<Empreendimento>`
  (o nome `29_campanha-Julho_26` usado antes era uma suposicao errada por
  analogia com a C028); coleta real em 2026-08-01, registrada no manifesto
  de cada execucao
- estrutura por empreendimento escolhida por espelhar o padrao ja existente
  dos outros 4 grupos da C029 (Avifauna, Mastofauna, Herpetofauna, Primatas)
  na mesma pasta contratual; havia uma subpasta vazia `Análise consolidada`
  dentro de `Ictiofauna/` cujo proposito nao foi confirmado com o Felipe —
  nao utilizada
- **4 de 4 empreendimentos publicados** na pasta contratual em 2026-09-08:
  Senhora do Porto (13 produtos, revisado/aprovado com 3 ajustes —
  manifesto de rastreabilidade, layout do Venn, acentuacao), Jacaré
  (13 produtos), Dores de Guanhães e Fortuna II (14 produtos cada, com
  figura extra de ocorrencia qualitativa por terem captura real em pontos
  TR). Jacaré/Dores de Guanhães/Fortuna II gerados com o mesmo codigo ja
  revisado, mas **ainda sem revisao numerica individual** pelo Felipe.
- Cada pasta de empreendimento agora tambem contem
  `MANIFESTO_RASTREABILIDADE.json` (projeto, campanha, empreendimento,
  responsavel, git, run_id, fonte e SHA-256 de cada produto).

## Limitacoes Conhecidas

- O projeto 165 (ictiofauna) nao possui pontos controle; as analises do
  relatorio parcial (6.1-6.8) sao internas a cada empreendimento.
- Blocos 6.4 (Jaccard entre pontos) e 6.5 (Venn RP x TR) ficam descritivos
  quando os pontos de tributario (`TR*`) tem poucas ou nenhuma captura —
  isso e esperado nesta campanha e esta registrado no relatorio descritivo
  de cada execucao, nao e tratado como erro.
- 12 dos 32 pontos cadastrados na campanha nao tiveram nenhuma captura, mas
  possuem esforco de amostragem valido (confirmado no Supabase). O pipeline
  mantem esses pontos como unidades amostrais de captura zero em vez de
  descarta-los.
- O vocabulario de `origem` no cadastro de especies e inconsistente
  (`Nativo`/`Nativa`/`Nao Nativo`/frase composta). Normalizado somente nos
  produtos gerados; o Supabase nao foi alterado.

## Historico Anterior (fora desta recipe)

- Campanha 28 (`C028-2026-05-SC`) foi executada com o mesmo gerador
  `ictio_partial`, porem usando `client="fersam001"` (config de outro
  projeto) e alvo fixo em variavel global do modulo. Lastro em
  `outputs/_project_scripts/ITAGUA001__monitoramento_da_fauna/ictiofauna/`.
  Essas duas praticas foram corrigidas nesta recipe (client proprio do
  projeto; filtros via `RunParams`/recipe, sem estado global no modulo).
