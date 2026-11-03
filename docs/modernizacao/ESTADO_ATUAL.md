# Estado atual da modernização

Atualizado em: 2026-11-03 (America/Sao_Paulo).
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

## Organização aprovada — MOD-008
Pasta do acervo: https://drive.google.com/drive/folders/14_1jmc3vqdRYDWAUMZ5KwLw8yx7DmqEx
Caminho: Opyta/Modernizacao_Opyta_Data/Memoria.
Acordado: Drive recebe acervo compartilhável; serviço e armazenamento ativo ficam fora da sincronização no notebook do piloto. O notebook não precisa ficar ligado 24 horas; consultas ao serviço dependem de ele estar funcionando.
Esta rodada disponibiliza cópias documentais identificadas por fonte/versão; não cria sincronização automática.
Próxima ação para instalação: identificar computador alvo e disponibilidade de Windows/WSL2/Docker; servidor/captura/importação no ai-memory permanecem não ativados.

## Retomada em 2026-11-03 — diagnóstico do computador
Memória documental recuperada do GitHub antes de avançar. Mantida MOD-008: piloto
local fora da pasta sincronizada e acervo compartilhável no Drive.
O terminal desta conversa retornou Linux; isso não identifica nem permite verificar
o Windows do responsável. Nenhuma instalação foi realizada no computador dele.
Próxima ação: receber diagnóstico somente leitura do PowerShell (versão do Windows,
WSL/distribuições, Docker e Codex). Com a saída, escolher os comandos de instalação
compatíveis. Não assumir Docker/WSL2 instalado nem executar instalação no host temporário.

## Atualização de 2026-11-03 — diagnóstico recebido e correção da orientação
O responsável executou os comandos no Windows e enviou a saída: Windows reportado
10.0.26300.0; Git 2.52.0.windows.1; WSL não instalado; Docker e Codex não encontrados
no PATH. Isso não prova ausência da extensão Codex no VS Code.
O comando wsl --version abriu oferta de instalação e exigência de elevação;
a saída informa cancelamento pelo usuário. Nenhuma instalação concluída foi demonstrada.
O assistente havia chamado o diagnóstico de somente consulta; essa garantia foi incorreta.
Evitar invocar wsl novamente nesta condição para mera detecção.
Decisões mantidas: ai-memory para modernização, piloto local fora do Drive,
acervo documental no Drive e auditoria pausada. WSL/Docker eram uma rota proposta,
não uma escolha técnica concluída nem pré-requisito já validado no computador.
Próxima ação: preparar roteiro único de instalação com versão revisada, componentes
necessários, efeitos no Windows, armazenamento, desinstalação e teste de continuidade.
Neste momento não há ai-memory instalado, captura ativa ou integração com este ChatGPT.

## Roteiro fechado em 2026-11-03
Ver ROTEIRO_INSTALACAO_AI_MEMORY.md: rota técnica recomendada para o piloto é Ubuntu
no WSL2 com binário Linux, sem Docker. Versão candidata conferida: v3.3.2.
Windows nativo tem artefato oficial, mas segue experimental na matriz consultada.
Primeira etapa entregue ao responsável: instalação oficial Microsoft de WSL/Ubuntu,
explicitamente identificada como mudança de sistema com elevação e possível reinício.
Etapa ainda não executada/confirmada. Etapas seguintes dependem da saída real.
O serviço permanece não instalado/não conectado. Acesso automático deste ChatGPT não demonstrado.

## Ambiente de trabalho aprovado — MOD-009 (2026-11-03)
- Execução técnica: Codex no VS Code.
- Discussão, prioridades e revisão: este ChatGPT.
- Memória entre agentes: ai-memory; decisões do chat precisam de registro explícito acessível ao agente.
- Primeiro marco: gravação de decisão e recuperação correta em nova sessão de Codex; depois outra ferramenta compatível.
- Instalação do WSL/Ubuntu e ai-memory ainda sem confirmação. Não marcar como instalado.
- Próxima ação: obter resultado da etapa WSL/Ubuntu documentada; só então prosseguir com pacote Linux e integração no mesmo ambiente.

## Ambiente Linux confirmado — 2026-11-03
Evidência enviada pelo responsável: criação do usuário felipe e “Installation successful!”.
Comandos executados no prompt Ubuntu retornaram x86_64, kernel
6.18.54.1-microsoft-standard-WSL2 e Ubuntu 26.04.1 LTS.
WSL2/Ubuntu confirmado por saída do usuário, não por execução remota do assistente.
Próxima etapa preparada: baixar pacote oficial Linux x86_64 v3.3.2 (~22,6 MB),
verificar SHA-256 publicado no GitHub e informar pasta do download. Sem extrair,
executar binário, configurar hooks ou iniciar serviço nessa etapa.
SHA-256 esperado do tar.gz: bb967293da4f977141089a6afeb888d65dc0d12a3a65db9b0c46524324d145a6.
Download/verificação ainda aguardam saída do responsável; ai-memory não marcado como instalado.

## Verificação do pacote recebida — 2026-11-03
Responsável enviou saída sha256sum: ai-memory-linux-x86_64.tar.gz: OK.
Pasta no Ubuntu: /home/felipe/ai-memory-download.jZQx44.
Pacote v3.3.2 conferido contra digest publicado. Lidos install.sh e workflow de
release desse tag: conteúdo do pacote fica na raiz, incluindo binário e hooks.
Próxima etapa fornecida: extrair o pacote completo em ~/.local/lib/ai-memory,
criar atalho em ~/.local/bin e executar somente --version. Recusar caminhos
existentes, sem sobrescrever instalação. Sem setup/serviço/hooks nesta etapa.
Instalação e execução da versão ainda aguardam resultado do responsável.
