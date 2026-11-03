# Piloto ai-memory — 2026-11-03

Estado: servidor local validado; integração completa com Codex pendente de autenticação e confiança nos hooks. Auditoria permanece pausada.

## Autorização e escopo
Pedido explícito do responsável: concluir instalação Linux no WSL2, serviço local, preparar Codex com preservação das configurações, importar registros revisados, testar e registrar. Escolha posterior: autenticar pelo VS Code no WSL.

## Resultados verificados
- Windows local com acesso ao Ubuntu WSL2; usuário felipe; x86_64; Ubuntu 26.04.1 LTS.
- ai-memory 3.3.2 já estava extraído em ~/.local/lib/ai-memory, com link em ~/.local/bin. Não reinstalado. Binário comparado byte a byte ao pacote.
- SHA-256 do pacote: bb967293da4f977141089a6afeb888d65dc0d12a3a65db9b0c46524324d145a6; igual ao digest oficial do release v3.3.2.
- Dados ativos: /home/felipe/.local/share/ai-memory. Configuração e credencial ficam no Linux; token com permissão 0600, sem impressão ou cópia ao Drive/Git.
- Processo piloto HTTP em 127.0.0.1:49374; /healthz retorna ok; /mcp sem credencial retorna 401; ss confirmou somente loopback para essa porta.
- Sem serviço permanente/início automático, conforme roteiro. WSL e processo precisam permanecer ligados.
- Codex CLI Linux 0.166.0 instalado pelo artefato oficial verificado: SHA-256 a0bf572d2f93f056c6712a6da348e96078dc84f3885fd7be67807ef389cb3978.
- Plugin oficial ai-memory@ai-memory 3.3.2 instalado e habilitado. Arquivos de hooks/launcher/MCP iguais à fonte do tag. Não existe ~/.codex/hooks.json paralelo; nenhum MCP manual duplicado.
- Antes da integração não existiam config.toml/hooks.json no Codex Linux; ausência registrada. Configuração inicial do ai-memory preservada em ~/opyta-modernizacao-evidence/config.initial.toml. Configurações Windows não alteradas.
- Captura em allowlist, marcador exclusivo em /home/felipe/projects/opyta-modernizacao/.ai-memory.toml; workspace opyta, projeto modernizacao-opyta-data. Backfill histórico desativado; perfil entre projetos desativado no marcador. LLM e embeddings desativados.
- Importados seis registros da branch, cada um com URL e SHA do blob: AGENTS.md, README, ESTADO_ATUAL, DECISOES, HISTORICO e ROTEIRO_INSTALACAO_AI_MEMORY. Snapshots identificados como históricos; estado verificado do piloto tem precedência.
- Captura sintética pelo launcher oficial: duas sessões e seis observações persistidas; handoff com prioridade, limites e próxima ação entregue à segunda sessão sintética.
- Bridge MCP oficial iniciou e expôs 25 ferramentas; memory_query recuperou MOD-007. Consulta posterior ao reinício confirmou a página do piloto. Isso não comprova execução por um Codex autenticado.
- Backup online ~/opyta-modernizacao-evidence/ai-memory-pilot-20261103.tar.gz: 165759 bytes; SHA-256 e99974c6ef3e6c798435ba74ad363dd910a451af9ab8f18244f5f1eab604b200. Arquivo aberto e SQLite extraído conferido com PRAGMA integrity_check = ok; sem auth-tokens no pacote. Backup não inclui credenciais, modelos nem todos os dados auxiliares: não é migração completa.
- VS Code Remote WSL instalado e janela solicitada para o workspace Linux. Codex Linux ainda retorna Not logged in.
- doctor confirmou sete hooks do plugin como untrusted; captura automática em sessão real ainda não validada.

## Pendências e próxima ação
1. Responsável entra no Codex pela janela do VS Code conectada ao Ubuntu e confia nos hooks oficiais em /hooks.
2. Agente verifica autenticação e confiança via doctor; cria observação em sessão real; abre outra sessão e recupera decisão, justificativa, prioridade, limites e próxima ação, sem fornecer a resposta no prompt.
3. Confirmar backup após o teste real. Só então avaliar aceite da memória e retomada da auditoria. Segunda ferramenta compatível fica para depois do primeiro marco.
4. Publicação/sincronização do backup com a pasta compartilhada do Drive não realizada; backup consistente permanece no Linux. Não há sincronização automática.
5. Serviço automático e integração com este ChatGPT não configurados/demonstrados.

## Continuidade local
Workspace documental: /home/felipe/projects/opyta-modernizacao (não é checkout operacional).
Evidências locais: /home/felipe/opyta-modernizacao-evidence (logs, manifest de fontes, doctor, consultas, eventos sintéticos, PID e backup).
Nenhum Supabase, dado ambiental, pipeline operacional, branch main ou checkout operacional foi modificado. Nenhuma proteção foi desativada.

## Fontes oficiais
- https://github.com/akitaonrails/ai-memory/releases/tag/v3.3.2
- https://github.com/akitaonrails/ai-memory/blob/v3.3.2/docs/install.md
- https://github.com/akitaonrails/ai-memory/blob/v3.3.2/docs/lifecycle-ops.md
- https://github.com/akitaonrails/ai-memory/tree/v3.3.2/plugins/codex
- https://github.com/openai/codex/releases/tag/rust-v0.166.0
- https://developers.openai.com/learn/docs-mcp
