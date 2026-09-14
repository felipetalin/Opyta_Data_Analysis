# ITAGUA001 — Avifauna C029 — Revisao Layout R01

## Controle

- projeto: `ITAGUA001__monitoramento_da_fauna` / `id_projeto=165`
- grupo: Avifauna
- operacao original: [ITAGUA001_AVIFAUNA_C029_2026.md](../operations/ITAGUA001_AVIFAUNA_C029_2026.md)
- tipo: `layout`
- impacto: `R1`
- estado: `review_completed`
- aberta em: 2026-08-03
- atualizada em: 2026-08-03

## Pedido

- Ajustar tamanho dos graficos pensando em pequena folga para inserir legenda no Word.

## Linha De Base

- pasta original: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/Guanhaes Energia/Resultados e analises/29_campanha_Jul_26/Avifauna`
- snapshot dos PNGs originais: `.../Avifauna/_layout_R00_before_word_margin_20260803`
- total preservado: 32 PNGs.

## Alteracoes

- Teste visual `teste_02_abundancia_intermediario` aprovado pelo usuario.
- Pacote final promovido para: `.../29_campanha_Jul_26/Avifauna`.
- Fonte base adotada para pacote C029: base 11, labels 10, legenda 10.
- Graficos de abundancia: dimensoes paisagem 8.6 x 6.8 com margem preservada.
- Curvas, indices, dendrogramas e Venn: salvamento ajustado para preservar margem externa em vez de cortar rente.
- Dendrograma por pontos: mantido em retrato, com largura/altura reduzidas e legenda superior limpa.
- Venn: textos normalizados para ASCII para evitar artefato de codificacao.

## Validacao

- `python -m py_compile` OK para:
  - `src/opyta_analysis/pipelines/diagnostico/avifauna.py`
  - `src/opyta_analysis/pipelines/diagnostico/mastofauna.py`
  - `scripts/run/fauna/run_avifauna_multi_empreendimentos_c029.py`
- `git diff --check` OK para `mastofauna.py` apos reparo de codificacao.
- runner C029 executado com sucesso para pacote temporario e PNGs promovidos para pasta final.
- pasta final `Avifauna`:
  - Dores de Guanhaes: 8 PNGs e 11 XLSX.
  - Fortuna II: 8 PNGs e 11 XLSX.
  - Jacare: 8 PNGs e 11 XLSX.
  - Senhora do Porto: 8 PNGs e 11 XLSX.
- amostras verificadas visualmente:
  - abundancia relativa;
  - dendrograma por pontos;
  - Venn PCH vs controle.

## Antes/Depois

- Antes: figuras grandes e salvas com `bbox_inches="tight"`, com pouca folga externa para legenda no Word.
- Depois: figuras em escala intermediaria aprovada no `teste_02`, fonte legivel no Word e margem externa preservada para insercao de legenda.

## Gate R

- status: `approved`
- aprovacao: usuario aprovou o `teste_02` e solicitou promocao para a pasta final em 2026-08-03.
- limpeza: pastas auxiliares `Avifauna_layout_TESTES`, `Avifauna_layout_R01_word_margin`, `Avifauna_tmp_promote_pngs_*` e snapshot interno `_layout_R00_before_word_margin_20260803` removidos.
