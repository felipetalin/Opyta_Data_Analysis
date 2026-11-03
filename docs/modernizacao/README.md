# Modernização do Opyta Data

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
