# Backlog Do Sistema Vivo

## Alta Prioridade

- Definir politica explicita de retencao/arquivamento para os diretorios
  imutaveis de execucao criados por `runner.py`
  (`outputs/_project_scripts/<projeto>/<grupo>/runs/<campanha>__<empreendimento>/<run_id>/`,
  ver correcao de 2026-09-08 no piloto ITAGUA001/Ictiofauna/C029). A correcao
  atual garante que nenhuma execucao apaga ou reutiliza o diretorio de outra,
  mas isso tambem significa que o volume cresce indefinidamente (um diretorio
  por execucao, para sempre). Falta decidir, sem introduzir exclusao
  automatica durante a geracao: quando um `run_id` pode ser arquivado ou
  compactado, quem aprova o arquivamento, se ha um limite de retencao por
  projeto/grupo/campanha, e onde registrar a decisao (provavelmente um script
  de arquivamento manual/aprovado, separado do fluxo de geracao, nunca
  acionado automaticamente por `run()`).
- Automatizar a criacao e atualizacao dos registros em
  `docs/control_center/operations/`.
- Criar validador dos gates e transicoes do fluxo operacional.
- Confirmar/corrigir duplicidade `GEOHER003` no Supabase (`id_projeto=31` e `95`).
- Confirmar se todo o lastro `FERSAM001__sam_metais_diagnostico__historico_id_62` pertence a FERSAM001.
- Criar dossies para BRAAVG002, FERSAM001, DUCGEO001, ITAGUA001 e TOTVAL001.
- Criar dossies para BIOPOR001, MICGAG001, BRAVAL004, GEOHER003, BRAANG01 e BRACED001 quando entrarem no fluxo.
- Migrar gradualmente docs raiz para dossies, patterns ou portfolio.
- Promover geracao de HTML textual rastreavel ao pipeline apenas apos validar o
  `docs/PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md` em pelo menos dois projetos.

## Media Prioridade

- Criar `scripts/run/new_project.py` para abrir projeto, dossie, recipe e
  registro de operacao com templates.
- Criar gerador de decision record.
- Criar preview HTML simples do Control Center.
- Reduzir wrappers temporarios na raiz de `scripts`.
- Avaliar se `TESTE001` deve ser removido tambem do Supabase.

## Baixa Prioridade

- Criar screenshots ou thumbnails para portfolio visual.
- Padronizar status em todos os patterns antigos.
- Automatizar leitura de projetos do Supabase para atualizar registry.
