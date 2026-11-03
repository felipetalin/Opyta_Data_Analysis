# Roteiro do piloto local — WSL2 sem Docker

Data: 2026-11-03 (America/Sao_Paulo).
Status: roteiro técnico preparado após diagnóstico; etapas locais ainda não executadas.
Direção aprovada: ai-memory para modernização, piloto local e cópias no Drive (MOD-006–008).
Versão candidata do ai-memory consultada: v3.3.2, publicada em 2026-11-03.
Revisar versão e integridade novamente antes de baixar; templates v3.2.8 são históricos/inativos.

## Rota recomendada e justificativa
Windows → WSL2 com Ubuntu → ai-memory Linux → Codex no mesmo ambiente Linux.
Docker não é necessário para essa rota. Não instalar Rust para compilar o projeto;
usaremos o binário oficial compatível com a arquitetura detectada no Ubuntu.
A matriz do release v3.3.2 marca Linux/WSL2 suportados e Windows nativo experimental.
O binário nativo foi analisado como alternativa com menos pré-requisitos, mas não é a
rota recomendada para este primeiro piloto, dada a preocupação do responsável com estabilidade.
Essa é uma recomendação técnica explicitada, não instalação já realizada.

## Diagnóstico recebido
Windows reportou 10.0.26300.0. Git 2.52.0.windows.1 encontrado. WSL declarou não estar
instalado. Docker e Codex não encontrados no PATH; isso não prova ausência de extensão
Codex no VS Code. A tentativa anterior de wsl --version ofereceu instalação e foi cancelada.
Nunca mais chamar esse comando de apenas consulta nesse estado.

## Etapas, efeitos e critérios para avançar
| Etapa | Ação | Mudanças no computador | Verificação |
| --- | --- | --- | --- |
| 1 | Instalar Ubuntu/WSL pelo comando oficial Microsoft | Instala componentes WSL, habilita recursos necessários e instala uma distribuição Linux; requer administrador e pode exigir reinicialização | Ubuntu abre; conta Linux criada pelo usuário; WSL2 confirmado após instalação |
| 2 | Conferir arquitetura/recursos dentro do Ubuntu | Consulta; sem instalar ai-memory | Escolha do pacote correto e recursos disponíveis |
| 3 | Baixar binário oficial fixado e checksum para inspeção | Downloads em pasta temporária do Linux | Conferir SHA-256 contra arquivo publicado pelo projeto antes de extrair/executar |
| 4 | Extrair em diretório do usuário Linux e consultar versão/help | Arquivos locais do ai-memory; sem serviço/integração ainda | Versão igual ao release fixado |
| 5 | Inicializar e executar servidor local em primeiro plano | Cria config, credencial e dados próprios; abre porta somente loopback | health/status; autenticação conferida; Ctrl+C encerra o serviço de primeiro plano |
| 6 | Configurar Codex no mesmo WSL e integração ai-memory | Configuração do cliente, MCP e um único mecanismo de hooks | Ferramentas acessíveis; hooks conhecidos e confiados pelo cliente; sem instalação duplicada |
| 7 | Carregar acervo inicial revisado | Novas páginas na memória exclusiva da modernização | Fontes/status corretos; operação ambiental não capturada nesse escopo |
| 8 | Testar retomada e backup | Sessões sintéticas e arquivo de backup consistente | Nova sessão recupera objetivo/decisão/próxima ação; backup conferido |

Dar comandos das etapas posteriores somente após verificar o resultado da etapa anterior.
Não executar scripts remotos diretamente por pipe. Não iniciar setup global que detecte
e altere todos os agentes automaticamente. Servidor permanente/início automático fica
para depois da validação do piloto.

## Primeira etapa — instalação de fato
Fechar/salvar o trabalho antes de eventual reinicialização.
Abrir PowerShell como administrador e executar:

```powershell
wsl --install -d Ubuntu
```

Este comando instala WSL/Ubuntu: não é uma checagem. A Microsoft documenta habilitação
dos recursos e instalação da distribuição, além da necessidade de reiniciar quando indicado.
Seguir somente a saída real. Se falhar ou solicitar algo inesperado, copiar a mensagem;
não mudar BIOS, antivírus, políticas ou executar reparos especulativos.
Depois de reiniciar se solicitado, abrir Ubuntu pelo menu Iniciar e criar usuário/senha
Linux localmente, se solicitado. Não enviar senha à conversa.
Quando o Ubuntu estiver funcionando, verificar a distribuição/versão e prosseguir.

## Armazenamento e funcionamento
- Dados ativos: diretório próprio no sistema de arquivos Linux do WSL; caminho exato
  será fixado e registrado antes da inicialização. Não usar /mnt/g/Meu Drive para o banco ativo.
- Acervo compartilhável já criado: https://drive.google.com/drive/folders/14_1jmc3vqdRYDWAUMZ5KwLw8yx7DmqEx .
- Drive recebe cópias/exportações/backups consistentes, não o SQLite ativo.
- Serviço local só está acessível enquanto notebook, WSL e processo estiverem funcionando.
- Não configurar acesso pela internet nem abrir roteador neste piloto.
- Sem provedor LLM pago no início. Memória/modelos locais consomem disco/RAM e podem
  exigir downloads; medir uso antes de manter o processo ativo durante outras análises.
- Credenciais em armazenamento local apropriado, fora do Git e do Drive compartilhado.

## Reversão planejada
- Servidor em primeiro plano: encerrar pelo terminal; não presume apagar memória.
- Antes de integrar cliente, preservar configuração anterior; desinstalação oficial do
  ai-memory deve ter plano inspecionado e preservar dados, sem opção purge-data.
- Remover binário/integração não significa apagar wiki/backup. Conferir caminhos e manter cópia.
- Ubuntu/WSL podem ser desinstalados depois; remover uma distribuição elimina seu ambiente
  e dados. Fazer exportação/backup antes e fornecer comandos destrutivos somente se isso for solicitado.
- Não fornecer wsl --unregister como comando de rotina nem remover diretórios genericamente.

## Critério de conclusão
Outra sessão de um cliente integrado recupera a decisão de adoção, justificativas,
prioridade atual, limites e próxima ação. Captura é comprovada por observação armazenada,
não só pela existência de um arquivo de configuração. Verificar backup e retorno após reinício.
Somente depois atualizar estado como ativo e retomar auditoria.
Acesso automático deste ChatGPT continua uma integração separada não demonstrada.

## Fontes
- Microsoft: https://learn.microsoft.com/pt-br/windows/wsl/install
- Release: https://github.com/akitaonrails/ai-memory/releases/tag/v3.3.2
- Matriz: https://github.com/akitaonrails/ai-memory/blob/v3.3.2/README.md
- Instalação: https://github.com/akitaonrails/ai-memory/blob/v3.3.2/docs/install.md
- Windows: https://github.com/akitaonrails/ai-memory/blob/v3.3.2/docs/windows.md
- Operações e reversão: https://github.com/akitaonrails/ai-memory/blob/v3.3.2/docs/lifecycle-ops.md
