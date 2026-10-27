# Histórico da modernização e passagem de contexto

Este arquivo é a trilha cronológica. ESTADO_ATUAL contém a retomada curta.
Entradas antigas não devem ser reescritas para apagar decisões substituídas.

## MOD-20261027-01 — Investigação inicial e descoberta do Drive
Data: 2026-10-27 (America/Sao_Paulo).

### Objetivo e ações realizadas
1. Confirmados branch e cinco documentos iniciais no GitHub; base observada b2fcf2a9ce383188f96c4429b768f82bc62fda5c.
2. Consultados materiais públicos sobre agentes/memória no livro de Fabio Akita, documentação do ai-memory, Codex e alternativas. Produzida avaliação inicial; nenhum servidor instalado ou teste de execução no Windows realizado.
3. Responsável corrigiu a premissa de armazenamento: arquivos de trabalho no Drive, sem cópia independente na máquina.
4. Localizadas pastas principais no Drive e lidos documentos selecionados de governança, contexto e aprendizado.
5. Comparados AGENTS e README da Central com GitHub; divergências concretas verificadas. Política de contexto e auditoria de agosto não encontradas nos caminhos equivalentes da branch.

### Resultado e limites
O GitHub examinado não representa integralmente a documentação encontrada no Drive.
A existência de registros de julho/agosto não prova que suas propostas foram implementadas.
Recomendação de memória em camadas é proposta técnica, não escolha aprovada de ferramenta.

### Decisões e continuidade
MOD-004 registra a correção de fonte; MOD-005 registra início oficial e continuidade.
Próximo passo: comparar código e configurações por conteúdo, sem sincronização.

## MOD-20261027-02 — Regra de ouro e primeiro recorte de código
Data: 2026-10-27 (America/Sao_Paulo).
Autorização: responsável pediu seguir e registrar oficialmente passo a passo, trabalho feito e continuidade.

### Ações realizadas
1. Relidos os documentos atuais da branch antes de editar.
2. Definida regra de ouro no README e entrada de leitura no AGENTS.
3. Atualizados estado, decisões e plano para usar Drive × GitHub.
4. Criado inventário parcial com links das fontes e limites das conclusões.
5. Listado src/opyta_analysis no Drive. Busca filtrada omitiu arquivos .py, mas leitura direta da pasta os mostrou; não confundir busca vazia com ausência.
6. Fetch textual de dois módulos devolveu conteúdo vazio; tamanho e download autenticado comprovaram arquivos existentes. Comparação feita a partir do conteúdo completo baixado.
7. Confirmadas diferenças em runner.py e supabase_client.py após normalizar BOM/CRLF; registrados hashes. A análise semântica dos diffs fica pendente.

### Verificação e restrições
Este conjunto documental é preparado para um único commit na branch de modernização.
Após gravar, a leitura do HEAD e dos arquivos deve confirmar a persistência.
Nenhum módulo operacional, arquivo do Drive ou dado de produção foi modificado nesta etapa.

### Próxima ação concreta
Inspecionar os diffs dos dois módulos já comparados e registrar impacto; depois seguir
os entry points/imports necessários para comparar os pipelines e validadores atuais.

## Modelo para próximas entradas
- Identificador e data local.
- Objetivo/escopo autorizado.
- Ações realmente concluídas.
- Fontes e versões observadas.
- Resultado e forma de verificação.
- Decisões aprovadas e propostas pendentes.
- Pendências/bloqueios e próxima ação concreta.

## MOD-20261027-03 — Impacto funcional do primeiro recorte de código
Data: 2026-10-27 (America/Sao_Paulo).
Autorização: responsável confirmou “Ok siga”, dando continuidade à investigação e aos registros.
Base GitHub: 3ba41794a495cce57905a78841a4a2bb18800a29.

### Ações e verificação
1. Relidos estado/decisões e recuperados os registros anteriores antes de avançar.
2. Obtidos novamente conteúdos completos do runner e cliente no Drive; inspecionados diffs contra GitHub fixado.
3. Lidos config e assinaturas/aplicação dos filtros de ictio, mastofauna, primatas, herpetofauna e avifauna no Drive e contratos no GitHub.
4. Confirmado conjunto de dependências: runner do Drive não é compatível isoladamente com config/assinaturas antigas do GitHub.
5. Identificada omissão de points no script reprodutor gerado pelo runner do Drive.
6. Classificadas alterações de paginação/timeout sem presumir ganho medido.
7. Fontes e consequências registradas em ANALISE_DIFERENCAS_20261027.md, com atualização do estado e inventário.

### Resultado e limites
Diferenças alteram o recorte dos dados e a reprodutibilidade; não são só organização.
Consequências de execução são inferidas do código e explicitamente identificadas.
Usados diff textual e inspeção de AST; nenhum pipeline importado/executado ou banco acessado.
Nenhuma alteração de código operacional ou instalação realizada. Propostas não viraram decisões aprovadas.

### Próxima ação concreta
Mapear CLI/recipes/callers de RunParams e pipelines para conferir transporte dos
filtros. Percorrer demais dependências antes de propor qualquer atualização conjunta.

## MOD-20261027-04 — Correção de prioridade: ai-memory primeiro
Data: 2026-10-27 (America/Sao_Paulo).
Responsável reiterou a importância do ai-memory e apontou o artigo da versão 2.0.
O assistente reconheceu que deslocou o foco para auditoria do código e releu o artigo.

Resultado: MOD-006 registra a direção explícita de priorizar o planejamento da adoção
do ai-memory para agentes da modernização. A auditoria funcional não é pré-requisito
para esse planejamento e fica pausada no ponto já documentado.
Acervo existente será insumo inicial; captura, busca e passagem de contexto precisam
ser implementadas e verificadas nos clientes compatíveis.

Próxima ação: definir servidor persistente, integração Codex/ChatGPT e plano de piloto.
Nenhum servidor foi instalado, nenhuma captura automática foi ativada e nenhuma
compatibilidade com o ChatGPT desta conversa foi demonstrada.
