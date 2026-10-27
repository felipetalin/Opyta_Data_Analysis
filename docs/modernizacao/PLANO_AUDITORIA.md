# Plano de auditoria — Drive × GitHub

Atualizado em: 2026-10-27. Referências: MOD-004 e MOD-005.
Investigação de código/dados é somente leitura; os registros da modernização
podem ser atualizados nesta branch conforme autorização do responsável.

1. **Fontes:** localizar pastas Opyta_Data, Opyta_Data_Analysis e worktrees no Drive; mapear para os repositórios GitHub. Não pressupor cópia independente na máquina.
2. **Documentos e instruções:** comparar AGENTS, políticas, decisões e auditorias existentes. Diferenciar registros históricos de fatos confirmados no código atual.
3. **Código e configurações:** listar pastas diretamente, identificar entry points, obter conteúdo completo e comparar com SHA GitHub fixado. Normalizar apenas BOM/CRLF para comparação textual; preservar hashes do original.
4. **Mapa funcional:** seguir validação → taxonomia → migração → consolidação → análises → geração, sem executar esses fluxos.
5. **Classificação:** igual, diferente, exclusivo confirmado, não encontrado naquele caminho ou indisponível. Busca vazia não prova ausência. Data/tamanho não provam equivalência.
6. **Riscos e mudanças:** descrever impacto das diferenças e propor plano de reconciliação reversível antes de sincronizar ou reorganizar.
7. **Arquitetura e memória:** avaliar alternativas considerando requisitos observados, inclusive custo de contexto e uso entre agentes; manter proposta separada de decisão aprovada.
8. **Continuidade:** registrar cada etapa no HISTORICO e atualizar ESTADO_ATUAL; novas decisões em DECISOES com origem da autorização.

## Critérios
- Diferenciar observado, inferido e não verificado.
- Registrar caminho/ID Drive, versão/horário observado quando disponível e SHA GitHub.
- Não tratar README ou auditoria histórica como prova de funcionamento atual.
- Não copiar segredos nem dados de clientes para registros públicos.
- Não ampliar contexto com outputs/logs sem dependência técnica.
- Confirmar a escrita e a leitura dos registros antes de afirmar persistência.
