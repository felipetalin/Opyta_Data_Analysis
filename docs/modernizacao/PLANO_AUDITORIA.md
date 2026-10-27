# Plano de auditoria (somente leitura)

1. **Git remoto:** inventariar árvore, módulos, dependências, testes, scripts, documentação e caminhos de execução; registrar evidências.
2. **Máquina local:** verificar `git status`, branch, remotos, commits locais não enviados, alterações não commitadas e arquivos ignorados relevantes; nunca expor valores de segredos.
3. **Mapa funcional:** traçar validação → taxonomia → migração → consolidação → análises → geração, com pontos de aprovação.
4. **Riscos:** classificar duplicações confirmadas, dependências, scripts sem testes e documentação divergente.
5. **Tecnologia:** comparar manutenção do Supabase/PostgreSQL e opções de backend/UI conforme requisitos reais.
6. **Plano de mudanças:** apresentar sequência reversível e de baixo risco; aguardar aprovação antes de executar.

## Critérios de qualidade
- Distinguir observado, inferido e não verificado.
- Não tratar README como prova de funcionamento.
- Não copiar credenciais nem dados sensíveis para relatórios.
- Preservar regras científicas, compatibilidade e rastreabilidade.
- Atualizar `ESTADO_ATUAL.md` e `DECISOES.md` após cada etapa aprovada.
