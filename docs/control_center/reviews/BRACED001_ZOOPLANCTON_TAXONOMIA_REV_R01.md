# BRACED001 - Zooplancton - revisao taxonomica R01

## Controle

- projeto: BRACED001 / Fonseca-Biota Aquatica
- grupo: Zooplancton
- revisao: taxonomia
- impacto: `R3`
- estado atual: `review_completed`
- aberta em: 2026-08-19
- Gate reaberto: B
- Gates A e C: preservados

## Escopo Aprovado

- `Ciclopideos` para `Cyclopidae`.
- `Difflugidae` para `Difflugiidae`.
- `Cyphoderidae` para `Cyphoderiidae`.
- `Collurella minima` para `Colurella minima`, incluindo o genero `Colurella`.
- substituir campos taxonomicos nulos ou `None` por `N.A.` na fatia do projeto.
- remover `Ciliado NI` da coluna genero e preencher com `N.A.`.
- regenerar todos os produtos dependentes de Zooplancton.

## Linha De Base

- operacao: `BRACED001_ZOOPLANCTON_FONSECA_MIGRACAO.md`.
- entrega vigente: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Zooplancton`.
- base antes: 624 resultados e 58 taxons na fatia consolidada.
- resultados preservados: os IDs de especies e as contagens nao serao alterados.

## Gate B

- aprovacao: correcoes taxonomicas determinadas diretamente pelo usuario em 2026-08-19.
- cadastro mestre: 7 registros da fatia corrigidos; 58 taxons preservados e 0 pendencias.
- consolidado: 7 grupos taxonomicos corrigidos; 624/624 resultados preservados.
- backup do cadastro: `public.bk_esp_braced001_zoo_r01_20260819t205722`.
- backup do consolidado: `public.bk_cons_braced001_zoo_r01_20260819t205722`.
- auditoria: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/gate_b/20260819T205722_taxonomia_r01_zooplancton_braced001.xlsx`.
- estado: aprovado e aplicado.

## Gate R

- pacote: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/reviews/R01_taxonomia`.
- geracao: 38 arquivos, incluindo 14 PNG e 20 XLSX.
- validacao automatica: `OK`, zero erros e 14/14 figuras validas.
- auditoria taxonomica dos XLSX: zero ocorrencias de `Ciclopideos`, `Difflugidae`, `Cyphoderidae`, `Collurella`, `Ciliado NI` ou `None`.
- campos finais de `Ciliado ni`: classe, ordem, familia e genero = `N.A.`.
- integridade: 58 taxons, 624 resultados e nenhum erro de formula.
- contato visual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/zooplancton/20260819T205808_contact_sheet_figuras_zooplancton_a4_paisagem.png`.
- aprovacao: Gate R aprovado explicitamente pelo usuario em 2026-08-19.
- promocao: 38 arquivos substituidos na pasta oficial, com hashes 38/38 conferidos.
- destino: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Cedro Mineracao/Produtos/Resultados/Zooplancton`.
- estado: `review_completed`.
