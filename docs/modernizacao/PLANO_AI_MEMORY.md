# Implantação do ai-memory para a modernização

Data: 2026-10-27 (America/Sao_Paulo).
Direção aprovada: priorizar memória da modernização; auditoria funcional pausada.
Versão técnica consultada: akitaonrails/ai-memory v3.2.8 (release consultado nesta data).
Estado: preparação documental e templates; serviço ainda não implantado.

## Resultado esperado
Uma sessão de outro agente deve recuperar objetivo, decisões e justificativas,
tentativas descartadas, fontes, estado e próxima ação sem Felipe reconstruir a história.
O registro é o raciocínio explicitado em evidências e decisões; não o raciocínio
interno do modelo. A modernização será transitória, mas o acervo continuará útil na manutenção.

## Organização proposta
- Um servidor persistente do ai-memory sob controle da Opyta, com um único processo escritor.
- Workspace proposto: opyta. Projeto proposto: opyta-modernizacao.
- O código/dados ambientais existentes permanecem em suas fontes; a wiki guarda contexto,
  referências e conhecimento relevante da modernização.
- Memória operacional da futura plataforma exige arquitetura e avaliação de acesso próprias.
- Depois da modernização, preservar o acervo como histórico técnico consultável; decidir então
  entre continuar o mesmo projeto de memória para manutenção ou abrir um novo com referências.

## Hospedagem — informação necessária
Proposta preferencial: máquina Linux/servidor da Opyta já existente ou VPS sempre ligada,
com armazenamento persistente, Docker, acesso administrativo e conectividade autorizada.
Alternativa de piloto: Windows com WSL2, disponível apenas enquanto o computador e o serviço
estiverem funcionando. Windows nativo tem status experimental na matriz consultada.
Não escolher fornecedor, contratar infraestrutura ou assumir orçamento sem identificar o host.

O Google Drive pode receber backups; não executa o serviço. Não colocar o SQLite ativo
nem a wiki sob escrita simultânea de vários servidores em pasta de sincronização do Drive.
O workspace temporário desta conversa não é um host persistente de produção.

## Templates preparados
- ai-memory/compose.yaml.example: um servidor v3.2.8, porta só em loopback, volume nomeado persistente e token obrigatório por ambiente.
- ai-memory/project.ai-memory.toml.example: exemplo de escopo e briefing inicial.
São exemplos inativos. Não foram instalados, não criam recursos e não constituem pacote
completo para acesso remoto. Depois de definido o host, ajustar endereço/perfis, autenticação,
HTTPS ou túnel e conexão dos clientes.

Não usar indiscriminadamente o marcador no root de Opyta_Data_Analysis para capturar
operações ambientais como modernização. Usar um checkout/pasta dedicada a esse trabalho,
ou roteamento explícito verificado, antes de ativar captura.

## Sequência de implantação
1. Identificar host, responsável, SO, acesso administrativo e existência de Docker.
2. Conferir disponibilidade do artefato da versão fixada e instalar servidor com volume persistente.
3. Gerar credencial no host; guardá-la fora do Git e das conversas. Preparar acesso autenticado.
4. Verificar resposta do serviço e acesso negado sem credencial nos endpoints protegidos.
5. Para acesso remoto, configurar HTTPS ou túnel adequado; não publicar a porta HTTP bruta.
6. Conectar Codex: MCP para consulta/escrita e um único mecanismo de hooks para captura.
   Conferir confiança dos hooks no cliente e evitar instalação duplicada por plugin e config.
7. Criar escopo opyta/opyta-modernizacao e verificar isolamento da memória operacional.
8. Importar apenas o acervo revisado abaixo, atribuindo origem e data. Deduplicar e conferir páginas.
9. Validar gravação, consulta, encerramento e retomada por uma sessão nova/outro agente.
10. Criar backup consistente pelo comando oficial e demonstrar restauração em ambiente isolado.
11. Somente após evidência desses passos registrar estado como “ativo”.

## Clientes e limites
| Cliente | Caminho de integração | Estado |
| --- | --- | --- |
| Codex em ambiente sob controle da Opyta | MCP + hooks ou plugin oficial, com executável local e acesso ao servidor | Documentado pelo projeto; ainda não configurado aqui |
| Outro agente compatível | MCP e, quando disponíveis, hooks de captura | Verificar por cliente e versão |
| ChatGPT desta conversa | Conexão MCP suportada pelo ambiente/conta ou consulta ao acervo por fonte acessível | Integração direta não demonstrada; não prometer captura automática |

Login/subscrição do modelo não conecta automaticamente o cliente ao servidor.
Usar outro modelo dentro do mesmo cliente e trocar de cliente são situações diferentes.
Sem integração de captura, uma sessão de chat exige registro/exportação explícita.
Disponibilidade de conexão customizada do ChatGPT deverá ser conferida no momento da configuração.

## Conteúdo inicial a carregar
1. README: objetivo, escopo e regra de ouro.
2. DECISOES: decisões atuais com status e decisões substituídas identificadas.
3. ESTADO_ATUAL: prioridade ai-memory; auditoria pausada.
4. HISTORICO: trabalho já feito, correções de rumo e pendências.
5. INVENTARIO e ANALISE_DIFERENCAS: achados confirmados e limites da análise.
6. Fontes revisadas sobre ai-memory/livro e documentos do Drive, por referências.

Nada disso foi importado no ai-memory até agora. Não carregar o Drive inteiro,
credenciais, dados ambientais de clientes ou transcrições indiscriminadas.
Captura automática posterior não recupera retroativamente esta conversa por si só.

## Configuração inicial proposta
- Usar caminho sem provedor LLM externo; consolidar inicialmente pelo caminho local documentado.
- Embeddings locais conforme padrão da versão, com download inicial do modelo se necessário.
- Captura de resposta final do assistente desligada inicialmente.
- Revisar exclusões de captura e validar o que ficou em spool/wiki.
- Reescrita/aprendizado por LLM, se posteriormente habilitado, precisa de configuração de revisão.
- Uma configuração por projeto; consultas globais não habilitadas no template.

## Critérios de aceitação
- Uma decisão com referência e status é gravada e recuperada pelo escopo correto.
- Outra sessão identifica a prioridade ai-memory e que a auditoria está pausada.
- Outro agente explica por que copiar apenas o runner seria incompatível, com fonte.
- A sessão nova recupera a próxima ação correta e não promove uma hipótese a aprovação.
- Encerramento gera a continuidade prevista pelo cliente; restart do servidor mantém o acervo.
- Backup restaurado permite recuperar a mesma decisão.
- Diferenciar claramente testes do servidor, do Codex e do ChatGPT; sucesso em um não prova o outro.

## Fontes técnicas consultadas no release v3.2.8
- https://github.com/akitaonrails/ai-memory/releases/tag/v3.2.8
- https://github.com/akitaonrails/ai-memory/blob/v3.2.8/docs/deploy.md
- https://github.com/akitaonrails/ai-memory/blob/v3.2.8/docs/marker-file.md
- https://github.com/akitaonrails/ai-memory/blob/v3.2.8/docs/mcp-install.md
- https://akitaonrails.com/2026/09/02/ai-memory-2-0-melhor-sistema-memoria-agentes-e-times/

## Próximo passo bloqueante
Identificar com o responsável se existe servidor/NAS/VPS da Opyta disponível ou se
é necessário começar num Windows com WSL2. Essa informação determina os comandos
reais de instalação e o caminho de acesso dos clientes. Não pedir senhas ou tokens no chat.
