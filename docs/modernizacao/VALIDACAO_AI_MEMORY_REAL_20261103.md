# Validação real do ai-memory — 2026-11-03

Resultado técnico: **PASSOU** no Codex CLI Linux, ai-memory 3.3.2, escopo opyta/modernizacao-opyta-data. Auditoria permanece pausada nesta etapa; não foi executada retomada funcional.

## Objetivo, autorização e estado inicial
Responsável solicitou concluir a validação e registrar na branch modernizacao/memoria-e-auditoria-inicial; confirmou autorização dos hooks após abrir codex --no-daemon. Login verificado: Logged in using ChatGPT. Doctor agora não apresenta alerta de hooks untrusted/modified. Plugin oficial 3.3.2 habilitado; servidor 3.3.2 em http://127.0.0.1:49374, auth bearer token. Nenhuma credencial publicada.

## Correção necessária do CLI
A instalação anterior continha somente codex-x86_64-unknown-linux-musl. A sessão A confirmou a mensagem, mas o CLI avisou ausência de codex-code-mode-host. Primeira tentativa B com host desabilitado não pôde consultar MCP e foi considerada falha, não aceite (sessão 01a1a2a8-7bda-7cc0-8527-cb1fe69f3390).
Baixado pacote completo oficial da MESMA versão 0.166.0:
https://github.com/openai/codex/releases/download/rust-v0.166.0/codex-package-x86_64-unknown-linux-musl.tar.gz
SHA-256 conferido com digest da API do release: 1d44b28bc4ac9937d7d3532264baa68a507ce364956a0d4ebb856f331cdee254.
Extraído em /home/felipe/.local/lib/codex-package-0.166.0. Link ~/.local/bin/codex ajustado atomicamente para bin/codex desse pacote; destino anterior preservado em ~/opyta-modernizacao-evidence/codex-link-before.json e binário anterior mantido. Configurações, login e confiança nos hooks preservados. Reversão: restaurar apenas o destino do link conforme esse JSON; não remover dados do Codex/ai-memory.
Sessão B final executada com pacote completo, sem desabilitar code-mode host. As sessões de teste usaram --no-daemon; abertura interativa com daemon após a correção não foi testada.

## Captura e recuperação reais
- Sessão A: 01a1a2a8-3a1c-7aa2-ac32-b5326a8c5f94; iniciada 15:24:57 e encerrada 15:24:59 (America/Sao_Paulo).
- Observação user-prompt: 01a1a2a8-459f-7b43-89f5-aa7cc7bff970.
- Marcador exclusivo: OPYTA-REAL-e7a0752d-0f64-4453-a348-fddaf56eb050.
- Sessão B independente final: 01a1a2a9-48dc-7960-b203-c435f0a3d968; iniciada 15:26:07 e encerrada 15:26:27 (America/Sao_Paulo).
- Ambas confirmadas por memory_read_session_observations no mesmo cwd. Não houve fork/resume, inserção sintética nem gravação manual de wiki para produzir o marcador.
- B chamou MCP memory_read_session_observations e memory_read_page (cinco chamadas concluídas, nenhum erro); não executou shell nem leitura local como ferramenta.
- Comparação programática: marcador da A idêntico ao da resposta B; marcador ausente do prompt B.
- Decisão recuperada: MOD-007, prioridade da implantação/verificação do ai-memory antes da auditoria, com justificativa de continuidade; fonte sources/decisoes.md, page_id 01a1a26b-2b02-7f61-9d99-6b02062d37d0.
- Próxima ação recuperada: autenticar Codex WSL, confiar nos hooks e comprovar captura/recuperação em nova sessão; fonte sources/estado_atual.md, page_id 01a1a26d-5374-7aa2-b466-d41dddcf7746. B identificou explicitamente que não havia aceite atualizado nas evidências consultadas.

## Prompt cego exato
> Teste cego autorizado de continuidade. Usando somente as ferramentas MCP ai-memory do projeto atual, recupere a observação exclusiva do teste real mais recente de outra sessão, uma decisão aprovada da modernização com justificativa e a próxima ação concreta. Cite páginas e IDs reais. Não leia arquivos locais, histórico do Codex nem arquivos de evidências como fonte das respostas. Não altere arquivos nem grave wiki ou handoff. Não execute shell. Use memory_query, memory_read_page ou memory_read_session_observations; busque no projeto identificado pelo marcador. Se faltar evidência, diga explicitamente. Responda concisamente.

Não contém marcador, MOD-007, conteúdo da decisão ou próxima ação esperada. O marcador foi armazenado fora do workspace; esse arquivo não foi fornecido à sessão B. Contexto injetado pelos hooks do próprio ai-memory é parte da integração, não resposta adicionada manualmente ao prompt.

## Resposta final B
Recuperado via MCP ai-memory em `opyta / modernizacao-opyta-data`:

- **Observação exclusiva:** `OPYTA-REAL-e7a0752d-0f64-4453-a348-fddaf56eb050`, capturada em 03/11/2026 às 18:24:59Z. Observação ID `01a1a2a8-459f-7b43-89f5-aa7cc7bff970`; página `sessions/01a1a2a8-3a1c-7aa2-ac32-b5326a8c5f94.md`.
- **Decisão aprovada MOD-007:** priorizar implantação e validação inicial do ai-memory, mantendo a auditoria pausada, para preservar decisões e continuidade entre agentes. Aprovação registrada: “Siga nesse sentido. Depois retomamos a auditoria”. Fonte: `sources/decisoes.md`, página ID `01a1a26b-2b02-7f61-9d99-6b02062d37d0`.
- **Próxima ação registrada:** autenticar Codex no VS Code WSL, confiar nos hooks em `/hooks` e comprovar captura e recuperação em nova sessão real. Fonte: `sources/estado_atual.md`, página ID `01a1a26d-5374-7aa2-b466-d41dddcf7746`.

A observação recuperada comprova captura real posterior ao snapshot; **não encontrei nas evidências consultadas um aceite completo atualizado**.

## Evidências e backup
Resumo estruturado versionado: [EVIDENCIAS_AI_MEMORY_REAL_20261103.json](EVIDENCIAS_AI_MEMORY_REAL_20261103.json).
Arquivos completos no Linux: /home/felipe/opyta-modernizacao-evidence/.
Hashes SHA-256:
- real-session-a.jsonl: 6d1e3af981c8d69cefd6c02836fef3421ab250539c545371b5f9d0e40fe1948e
- real-session-b-retry.jsonl: 57e68f9779921d6b8b4a1f91718c913625865efbb2354d208f187ee7cc065714
- real-session-a-prompt.txt: 1ca824eec71a62a7ce75d13e6e1b13b44d8f3986eb8b2987bb54632c46546f4c
- real-session-b-prompt.txt: 94436a0cd19eb354e3ee82826225df25a6b74302f65a8fa91192c6b490b840cb
- ai-memory-real-validation-20261103.tar.gz: eea39e1f24bb192295781f544c8f1e024bc690ea8dede9334ef8f1427c02d305
Backup online criado pelo ai-memory após o teste; SQLite extraído conferido com PRAGMA integrity_check = ok. Backup não é migração completa: exclui credenciais e outros componentes auxiliares por contrato do comando. Não enviado ao Drive.
Doctor final: codex 4 sessões locais, 6 capturadas (inclui piloto sintético); nenhum backlog informado nem alerta de confiança. Copilot-cli continua 1 local / 0 capturada e não integra este aceite.

## Resultado, limites e próxima ação
Captura automática e recuperação em nova sessão Codex CLI comprovadas. Snapshot histórico da próxima ação foi recuperado corretamente e reconhecido como anterior ao teste: isso não demonstra sincronização automática GitHub–wiki nem atualização automática do acervo.
Nenhum novo desenho arquitetural ou aceite do responsável foi presumido. Registros atuais desta branch prevalecem sobre snapshots históricos importados. Próxima ação concreta: revisar este resultado e definir a retomada da auditoria a partir dos achados preservados; não ampliar a auditoria nesta etapa. Segundo agente e uso via painel VS Code ficam fora do teste concluído. Serviço continua local e depende do processo/WSL ligado.
