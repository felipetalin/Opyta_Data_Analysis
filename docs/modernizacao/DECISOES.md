# Registro de decisões

## MOD-001 — Memória persistente da modernização
Data: 2026-10-27
Status: aprovado pelo responsável do projeto.
Decisão: registrar a modernização em `docs/modernizacao/`, com estado atual, decisões, evidências e próximos passos. Não duplicar nem substituir a memória operacional do sistema.
Motivo: continuidade entre ChatGPT, Codex e outros agentes sem dependência de contexto de conversa.

## MOD-002 — Auditoria antes de reorganização
Data: 2026-10-27
Status: aprovado.
Decisão: começar por `Opyta_Data_Analysis`, comparar depois com arquivos locais e com `Opyta_Data` histórico; não alterar funcionalidades antes do diagnóstico.
Motivo: o workspace local pode estar à frente do GitHub e scripts antigos podem ter dependentes.

## MOD-003 — Tecnologias ainda em avaliação
Data: 2026-10-27
Status: decisão pendente.
Contexto: Excel permanece como entrada nesta fase; Supabase/PostgreSQL, Python, Streamlit e arquitetura híbrida serão avaliados, não substituídos por antecipação.

## Convenção
Cada nova decisão deve registrar data, status (proposta/aprovada/rejeitada/substituída), evidências, alternativas e consequências.
