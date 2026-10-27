# Estado atual da modernização

Atualizado em: 2026-10-27 (America/Sao_Paulo).
Prioridade: implantação do ai-memory para a memória da modernização (MOD-006/MOD-007).
Auditoria funcional Drive × GitHub: pausada; achados preservados no inventário e relatório.

## Feito nesta etapa
- Reconfirmado release v3.2.8 do ai-memory e consultadas referências desse release para servidor, escopo e MCP.
- Preparados PLANO_AI_MEMORY.md e dois templates inativos: servidor Docker e marcador de projeto.
- Definidos proposta de organização, acervo inicial, sequência de implantação e critérios de retomada entre sessões/agentes.
- Registrada MOD-007: memória da modernização primeiro; auditoria será retomada depois.

## Estado real da integração
- Servidor ai-memory: não implantado.
- Host persistente: ainda não identificado.
- Captura automática, MCP e importação: não ativados.
- Codex e ChatGPT: nenhum acesso ao ai-memory demonstrado nesta investigação.
- Documentação versionada continua sendo o acervo de transição; não confundir com serviço ativo.

## Próxima ação concreta
Identificar servidor/NAS/VPS existente na Opyta e acesso de instalação, ou confirmar
piloto Windows/WSL2. A partir desse ambiente, finalizar comandos de instalação,
autenticação e conectividade conforme PLANO_AI_MEMORY.md.

## Retomada
Ler README, DECISOES/MOD-006–007, PLANO_AI_MEMORY e HISTORICO/MOD-20261027-05.
Não ampliar a auditoria de código enquanto esta prioridade estiver em vigor.
Para recuperar achados: ANALISE_DIFERENCAS_20261027.md e INVENTARIO_DRIVE_GITHUB.md.

## Acervo já apurado
- Drive contém instruções/documentos que divergem do GitHub examinado.
- Runner/config/pipelines têm contratos diferentes; copiar apenas runner é incompatível.
- Script reprodutor observado omite o filtro de pontos; impacto inferido estaticamente.
- Paginação/timeout diferem; benefício não medido.
- Nenhum pipeline executado nem dado de produção alterado nesta investigação.

## Infraestrutura informada pelo responsável
Em 2026-10-27, o responsável informou disponibilidade de GitHub, Google Drive,
computadores e Supabase. Servidor dedicado/NAS/VPS não foi identificado.
Ainda não estão confirmados: qual computador pode executar o piloto, disponibilidade
para permanecer ligado, acesso administrativo, WSL2/Docker e conectividade dos agentes.
Próximo passo: identificar esse computador e preparar instalação conforme seu ambiente.
Proposta inicial: piloto em computador existente, antes de contratar infraestrutura.
