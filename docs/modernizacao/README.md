# Modernização do Opyta Data

## Registro de 2026-11-05 — retomada adiada

Complemento N/PC do WSPKIN001 registrado na [auditoria do caso](AUDITORIA_WSPKIN001_ICTIOFAUNA_20261103.md). Definição histórica de PC, migrador executado e peso pós-carga continuam pendentes. O responsável pediu registrar e continuar depois. Orientação vigente: [ESTADO_ATUAL.md](ESTADO_ATUAL.md).


## Estado vigente e auditorias registradas — 2026-11-03

Auditoria retomada somente para leitura por autorização do responsável; esta rodada apenas registra o que foi concluído. Excel permanece como entrada. Consultar [ESTADO_ATUAL.md](ESTADO_ATUAL.md) para orientação vigente; os relatos anteriores abaixo são históricos.
- [Mapeamento Excel → banco](AUDITORIA_FLUXO_EXCEL_BANCO_20261103.md).
- [Trilha histórica WSPKIN001/Ictiofauna](AUDITORIA_WSPKIN001_ICTIOFAUNA_20261103.md).
Reconciliação do produto histórico confirmada; versão executada do migrador e peso gravado naquela carga não comprovados. Próxima ação: Localizar o Excel pelos hashes históricos, o log da migração e a evidência pós-carga por chave.


## Atualização da página de estado no ai-memory — 2026-11-03

Por pedido explícito do responsável, sources/estado_atual.md foi atualizada a partir de ESTADO_ATUAL.md no commit de0dfcc34312147bd1f103ecd9782067002e535a, blob 8a8bd767ce6bfd1f559cab842dff2edb96aafdd2. Versão anterior preservada integralmente e identificada como histórica. Nova sessão real 01a1a2b4-ffe0-7122-b8f2-47bff0d3f26c recuperou via MCP o estado vigente e reconheceu a orientação superada, sem respostas no prompt cego. Resultado: PASSOU. Evidência: [ATUALIZACAO_ESTADO_AI_MEMORY_20261103.md](ATUALIZACAO_ESTADO_AI_MEMORY_20261103.md).

Encontrada pendência residual em decisions/pilot-status-20261103.md ainda fixada com orientação antiga; não alterada neste escopo. Próxima ação: tratar essa página em escopo próprio e definir retomada da auditoria com o responsável. Auditoria permanece pausada; nenhuma nova aprovação presumida. ESTADO_ATUAL.md preservado como fonte exata do teste.

## Validação real concluída em 2026-11-03 — estado mais recente

Login ChatGPT confirmado; hooks oficiais reconhecidos pelo doctor. Teste em duas sessões reais Codex CLI passou: marcador exclusivo capturado na sessão A e recuperado por MCP na sessão B independente, junto à MOD-007, justificativa e próxima ação registrada, sem respostas no prompt cego. Corrigida instalação incompleta do CLI com pacote oficial completo da mesma versão 0.166.0, digest conferido; configurações e confiança preservadas. Backup online validado por integrity_check = ok.

Evidências, IDs, prompt, hashes, tentativa falha preservada e limites: [VALIDACAO_AI_MEMORY_REAL_20261103.md](VALIDACAO_AI_MEMORY_REAL_20261103.md). A próxima ação consultada no ai-memory ainda era um snapshot histórico; B reconheceu ausência de aceite atualizado. Não presumir sincronização automática do acervo. Auditoria permanece pausada nesta etapa. Próxima ação: revisar resultado e definir retomada da auditoria; nenhuma nova decisão aprovada.

## Validação real em 2026-11-03 — login confirmado; hooks pendentes

Objetivo autorizado: concluir a validação em duas sessões reais e registrar evidências na branch modernizacao/memoria-e-auditoria-inicial. Auditoria permanece pausada.

Ações e evidências desta sessão:
- Workspace inspecionado: /home/felipe/projects/opyta-modernizacao; não contém .git. Registros remotos consultados na branch de felipetalin/Opyta_Data_Analysis, base 7bf76af341eefc7e1c6cb069f80db6557371e745.
- `codex login status`: `Logged in using ChatGPT`, saída 0. Supera a pendência histórica de login do CLI; não é teste de captura.
- `ai-memory --version`: ai-memory 3.3.2.
- `ai-memory doctor`: servidor http://127.0.0.1:49374, server 3.3.2, auth bearer token, identidade anonymous (root); coordenada exata opyta/modernizacao-opyta-data, marcador válido; plugin Codex 3.3.2 habilitado.
- Alerta literal: “Codex skips 7 of the plugin's hooks (untrusted or modified). Open Codex, run /hooks, and trust them; until then Codex sessions are not captured.”
- Doctor indica codex: 1 local, 2 captured; esses números não comprovam captura atual. Também alerta copilot-cli: 1 local, 0 captured; sem instalação adicional nesta etapa.
- MCP memory_status respondeu sem erro com escopo explícito opyta/modernizacao-opyta-data: 9 páginas atuais, 12 versões, 2 sessões e 6 observações.
- MCP memory_read_session_observations retornou sessão b74cf2c5-f260-42d0-8913-1416e86a8070, encerrada em 2026-11-03T17:18:41.818638Z; corpo “reason: synthetic validation complete”. Portanto, a evidência recuperada é sintética e não satisfaz o teste solicitado.

Resultado: validação completa NÃO concluída. Não foi registrada observação real de teste nem iniciada sessão de recuperação, pois a confiança nos hooks está pendente. Nenhuma confiança, configuração ou credencial foi alterada. Não se substituiu captura real por inserção manual no servidor.

Próxima ação concreta do responsável: na janela do VS Code conectada ao Ubuntu/WSL, abrir o Codex neste workspace; executar /hooks no Codex (se o painel não oferecer o comando, abrir o terminal integrado WSL, executar `codex` nesta pasta e então /hooks). Revisar os sete hooks do plugin ai-memory@ai-memory e autorizá-los. Não é necessário repetir login enquanto o status continuar autenticado. Reexecutar doctor para confirmar ausência do alerta.

Depois da autorização: sessão A produz um marcador aleatório exclusivo e confirma sua persistência nas observações capturadas com ID real. Abrir sessão B independente no mesmo projeto. Prompt cego: “Usando somente o ai-memory deste projeto, recupere a observação do teste real mais recente, uma decisão aprovada da modernização com justificativa e a próxima ação. Cite páginas ou IDs de observações; informe se faltar evidência. Não leia arquivos locais como fonte das respostas.” Não fornecer marcador, decisão ou próxima ação no prompt. Registrar IDs distintos, prompt, chamadas MCP, respostas e comparação; só então avaliar aceite e backup.

Autorização mantida: investigação e registros; nenhuma nova decisão aprovada. Auditoria, código operacional, dados e main permanecem sem alteração.
Referência de confiança dos hooks: https://learn.chatgpt.com/docs/hooks


## Piloto executado em 2026-11-03 — estado que prevalece sobre os relatos históricos abaixo

Instalação ai-memory 3.3.2 verificada no Ubuntu/WSL2 do responsável. Servidor piloto autenticado em loopback; dados ativos no Linux fora do Drive. Plugin oficial Codex 3.3.2 instalado sem hooks duplicados. Importação de seis registros, captura/handoff sintéticos, consulta MCP, reinício e integridade do backup verificados.

**Aceite completo pendente:** Codex Linux ainda sem autenticação; sete hooks oficiais identificados como untrusted. Responsável escolheu autenticação pelo VS Code no WSL; janela do workspace foi aberta. Próximo passo: entrar no Codex nessa janela, confiar nos hooks em /hooks e comprovar captura e recuperação em nova sessão real. Auditoria permanece pausada. Não confundir testes sintéticos com continuidade de um Codex autenticado.

Evidências, caminhos, digests, limites e reversão: [PILOTO_AI_MEMORY_20261103.md](PILOTO_AI_MEMORY_20261103.md). Processo local sem início automático; não há integração demonstrada com este ChatGPT.


Status: oficialmente iniciada; investigação e reconciliação Drive × GitHub.
Início oficial confirmado pelo responsável: 2026-10-27 (America/Sao_Paulo).
Branch: `modernizacao/memoria-e-auditoria-inicial`.

## Objetivo
Modernizar a plataforma preservando resultados científicos, processos aprovados,
conhecimento acumulado e rastreabilidade. Primeiro identificar a implementação e
os documentos atuais, depois propor mudanças fundamentadas.

## Regra de ouro — continuidade obrigatória
1. Ao iniciar, ler este índice, ESTADO_ATUAL e DECISOES; conferir a fonte/versão relevante.
2. Recuperar apenas os trechos necessários do histórico e inventário; evitar releituras amplas.
3. Executar a etapa dentro do escopo autorizado, diferenciando observado, inferido e pendente.
4. Ao concluir ou interromper, registrar o que foi feito, como foi verificado, evidências,
   decisões e sua autorização, pendências e a próxima ação concreta.
5. Atualizar ESTADO_ATUAL e HISTORICO. Acrescentar DECISOES somente quando houver decisão.
6. Antes de dizer que algo foi registrado, confirmar a gravação e reler os arquivos modificados.

## Fontes e escopo
- O responsável informou: os arquivos estão no Drive da Opyta; não há cópia independente na máquina a comparar.
- Pastas verificadas: [Opyta_Data_Analysis](https://drive.google.com/drive/folders/1ZD4kzzrznP2bbPkcjTcjfHk7Nj_O9ttv) e [Opyta_Data](https://drive.google.com/drive/folders/15EUr3YuZYLWCuUhAFCZqup-g-VpcS5S2).
- Drive é a referência de descoberta da implementação atual. Isso não torna todo arquivo do Drive canônico ou correto.
- GitHub contém versões divergentes; determinar correspondência por conteúdo e evidências, nunca apenas por data.
- Não classificar Opyta_Data inteiro como histórico: o Drive contém registros sobre seu papel de interface e validação, a confirmar no código.
- Esta pasta registra a modernização. A memória operacional em docs/control_center conserva sua finalidade própria.
- Documentos aprovados e evidências versionadas sustentam continuidade. Memória de ChatGPT/Codex é auxílio, não confirmação automática de fatos.
- ai-memory e a arquitetura proposta continuam em avaliação; nenhuma instalação foi aprovada/executada nesta rodada.

## Ordem de trabalho
1. Mapear diferenças de documentos, código e configurações entre Drive e GitHub.
2. Classificar diferenças: iguais, diferentes, exclusivas da fonte, indisponíveis ou pendentes.
3. Propor reconciliação preservando versões; não executar sincronização em massa.
4. Consolidar a memória da modernização e avaliar automação por benefício demonstrado.

## Índice
- [Estado atual](ESTADO_ATUAL.md)
- [Decisões](DECISOES.md)
- [Histórico e passagem de contexto](HISTORICO.md)
- [Inventário Drive × GitHub](INVENTARIO_DRIVE_GITHUB.md)
- [Diagnóstico inicial — histórico da primeira leitura](DIAGNOSTICO_INICIAL.md)
- [Plano de auditoria](PLANO_AUDITORIA.md)

## Limites atuais
Autorizados: investigação e atualização dos registros da modernização nesta branch.
Mudanças operacionais, instalação de memória, sincronização, produção, Supabase e main
não estão incluídas nesta autorização documental.

## Prioridade em vigor — MOD-007
Implantar e verificar o uso inicial do ai-memory para a modernização; depois retomar
a auditoria funcional. Ver [Plano de implantação](PLANO_AI_MEMORY.md).
Os templates em ai-memory/ são exemplos inativos, não evidência de serviço instalado.
