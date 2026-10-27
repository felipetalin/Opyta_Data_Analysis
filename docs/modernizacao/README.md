# Modernização do Opyta Data

Status: diagnóstico inicial (não autoriza mudanças operacionais).
Início: 2026-10-27.
Branch de trabalho: `modernizacao/memoria-e-auditoria-inicial`.

## Objetivo
Avaliar e modernizar a plataforma multiuso Opyta Data, preservando resultados científicos, processos aprovados e rastreabilidade. A primeira prioridade é organizar o GitHub e compreender a implementação atual.

## Fonte de verdade e escopo
- Referência operacional inicial: `Opyta_Data_Analysis` (a confirmar frente ao workspace local).
- `Opyta_Data` original é fonte histórica; não presumir que seja a versão atual.
- Código local pode conter alterações não commitadas ou não enviadas.
- Esta pasta registra **a modernização**, não substitui a memória operacional em `docs/control_center/`.
- Documentação versionada é fonte persistente de decisões; separar fatos observados, hipóteses e decisões aprovadas.

## Ordem obrigatória para agentes
1. Ler este README, `ESTADO_ATUAL.md` e `DECISOES.md`.
2. Consultar `AGENTS.md`, `docs/ORGANIZACAO_REPOSITORIO.md` e `docs/control_center/README.md`.
3. Verificar estado real do Git e diferenças locais/remotas antes de propor alterações.
4. Trabalhar no escopo aprovado; registrar evidências com caminhos de arquivo.
5. Atualizar estado, decisões e aprendizados ao concluir cada atividade.
6. Não alterar dados de produção, Supabase, pipelines ou branch main sem aprovação específica.

## Índice
- [Estado atual](ESTADO_ATUAL.md)
- [Decisões](DECISOES.md)
- [Diagnóstico inicial](DIAGNOSTICO_INICIAL.md)
- [Plano de auditoria](PLANO_AUDITORIA.md)
