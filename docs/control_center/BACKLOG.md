# Backlog Do Sistema Vivo

## Alta Prioridade

- Especificar e criar camada `opyta_ops` para usar o OPYTA DATA como frontend
  e o `Opyta_Data_Analysis` como motor/governanca, sem expor scripts e banco
  diretamente a colaboradores.
- Integrar o OPYTA DATA ao fluxo da Central de Controle: operacoes, estados,
  Gates A/B/C/R, aprovacoes explicitas e registro de lastro.
- Substituir a consolidacao global/destrutiva do OPYTA DATA por consolidacao
  controlada por escopo, com dry-run, backup, reversao e auditoria.
- Persistir a auditoria do OPYTA DATA em Supabase, mantendo arquivo local apenas
  como fallback.
- Implementar perfis de permissao para colaboradores: leitor, preparador,
  analista, revisor e administrador.
- Auditar proximos relatorios de consumo do Codex apos a inclusao de
  `.codexignore` e `LLM_CONTEXT_POLICY.md`.
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
- Conectar a pagina de analises do OPYTA DATA ao runner por recipe em
  `scripts/run/run_project_recipe.py`.
- Criar preview HTML simples do Control Center.
- Reduzir wrappers temporarios na raiz de `scripts`.
- Avaliar se `TESTE001` deve ser removido tambem do Supabase.

## Baixa Prioridade

- Criar screenshots ou thumbnails para portfolio visual.
- Padronizar status em todos os patterns antigos.
- Automatizar leitura de projetos do Supabase para atualizar registry.
