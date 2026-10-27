# Diagnóstico inicial — evidências documentais

Data: 2026-10-27.
Escopo: leitura de documentação no GitHub; **não** representa auditoria do código em execução.

## Evidências observadas
- `README.md`: descreve pipelines por grupos biológicos, configurações por projeto, saída reproduzível e padrões Gold.
- `AGENTS.md`: determina gates de aprovação e fluxos de revisão para a Central de Controle.
- `docs/ORGANIZACAO_REPOSITORIO.md`: define código reutilizável em `src/opyta_analysis/`, recipes em `configs/projects/` e scripts por finalidade.
- `docs/control_center/README.md`: documenta operações, revisões, registries, portfolio e aprendizado.
- `scripts/SCRIPT_CATALOG.md`: cataloga entry points e scripts específicos de projetos; registra wrappers de compatibilidade.

## Hipóteses a verificar
- Funções duplicadas entre scripts de projetos e código reutilizável.
- Dependências ainda ativas de wrappers legados.
- Desalinhamento entre documentação, código remoto e versão local.
- Cobertura de testes e qualidade da validação antes de migração.

## Não concluído
Nenhuma falha de código, duplicação concreta, desempenho de banco ou obsolescência tecnológica foi confirmada nesta rodada.
