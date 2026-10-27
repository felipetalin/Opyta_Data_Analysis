# Registro de decisões

## MOD-001 — Memória persistente da modernização
Data: 2026-10-27
Status: aprovado pelo responsável do projeto.
Decisão: registrar a modernização em `docs/modernizacao/`, com estado atual, decisões, evidências e próximos passos. Não duplicar nem substituir a memória operacional do sistema.
Motivo: continuidade entre ChatGPT, Codex e outros agentes sem dependência de contexto de conversa.

## MOD-002 — Auditoria antes de reorganização
Data: 2026-10-27
Status: substituída quanto à premissa de arquivos locais por MOD-004; preservada a auditoria antes de reorganização.
Decisão original: começar por `Opyta_Data_Analysis`, comparar depois com arquivos locais e com `Opyta_Data` histórico; não alterar funcionalidades antes do diagnóstico.
Motivo: o workspace local pode estar à frente do GitHub e scripts antigos podem ter dependentes.

## MOD-003 — Tecnologias ainda em avaliação
Data: 2026-10-27
Status: decisão pendente.
Contexto: Excel permanece como entrada nesta fase; Supabase/PostgreSQL, Python, Streamlit e arquitetura híbrida serão avaliados, não substituídos por antecipação.

## Convenção
Cada nova decisão deve registrar data, status (proposta/aprovada/rejeitada/substituída), evidências, alternativas e consequências.

## MOD-004 — Investigar Drive × GitHub antes de reconciliar
Data: 2026-10-27
Status: aprovado pelo responsável nesta conversa.
Evidência: responsável informou “tudo está lá” no Drive e “Não tenho nada na máquina”; concordou com a investigação e autorizou seguir.
Decisão: tratar o Drive como origem dos arquivos de trabalho a investigar e comparar com GitHub. Não exigir cópia independente na máquina. Preservar o princípio de auditoria anterior à reorganização de MOD-002.
Alternativas: confiar só no GitHub; presumir o Drive inteiro canônico; comparar por conteúdo e evidências.
Escolhida: comparação por conteúdo e evidências.
Consequências: versões recentes no Drive não são automaticamente aprovadas; divergências ficam registradas antes de eventual sincronização.

## MOD-005 — Início oficial e regra de ouro de continuidade
Data: 2026-10-27
Status: aprovado pelo responsável nesta conversa.
Evidência: pedido explícito para registrar “como regra de ouro o passo a passo do que a gente tá fazendo, o que a gente já fez” e declaração de que a modernização já começou.
Decisão: oficializar o início em 2026-10-27 e utilizar desde agora os registros versionados desta branch como memória da modernização.
Protocolo: ler estado/decisões ao iniciar; ao encerrar cada etapa registrar ações, evidências, resultados, autorizações, pendências e próxima ação; verificar a gravação.
Alternativas: depender da conversa; instalar memória automática imediatamente; começar com documentação versionada existente.
Escolhida: usar imediatamente documentação versionada existente; automação permanece proposta em avaliação.
Consequências: atualizar README, ESTADO_ATUAL, HISTORICO e instrução de entrada no AGENTS. Cada registro distingue decisão aprovada, proposta e fato verificado.
Escopo autorizado: registros da modernização nesta branch. Não autoriza alterações em produção, código operacional ou instalação do ai-memory.
