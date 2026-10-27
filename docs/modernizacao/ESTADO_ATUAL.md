# Estado atual da modernização

Atualizado em: 2026-10-27 (America/Sao_Paulo).
Fase: inventário e reconciliação Drive × GitHub, em andamento.
Última base GitHub comparada: 3ba41794a495cce57905a78841a4a2bb18800a29.
Esse SHA é a base anterior a esta atualização documental, não o HEAD resultante dela.

## Objetivo atual
Identificar diferenças entre os arquivos no Drive e GitHub, mantendo memória
persistente da investigação e evitando reconstruir contexto em toda sessão.

## Concluído
- Confirmados no GitHub os cinco documentos iniciais e a branch de modernização.
- Inspeção documental do livro (incluindo o apêndice de memória), documentação e estrutura do ai-memory e alternativas; recomendação inicial apresentada como proposta, sem validação de execução no Windows.
- Responsável esclareceu que os arquivos atuais estão no Drive; premissa de comparação com cópia independente na máquina foi corrigida.
- Localizadas as pastas Opyta_Data, Opyta_Data_Analysis e Opyta_Data_Analysis.worktrees.
- Lidos AGENTS, README da Central, política de contexto, sistema de aprendizado, auditoria de conhecimento de agosto e decisão arquitetural de julho no Drive.
- Confirmadas divergências de conteúdo em AGENTS e README da Central; política de contexto e auditoria não encontradas nos caminhos equivalentes da branch examinada.
- Comparados os conteúdos completos de runner.py e supabase_client.py por download autenticado do Drive e leitura no SHA GitHub acima: ambos diferentes, inclusive após normalizar CRLF e BOM. Análise funcional inicial documentada em ANALISE_DIFERENCAS_20261027.md.
- Início oficial e regra de ouro de continuidade registrados por solicitação explícita do responsável.

## Em andamento / não concluído
- Inventário é parcial; não representa comparação recursiva de toda a plataforma.
- Ampliar análise aos callers/entry points e às demais diferenças dos pipelines; primeiro recorte funcional concluído por inspeção estática.
- Comparação dos pipelines, validadores, recipes e dependências efetivamente usados.
- Verificação no código das conclusões da auditoria de agosto e da decisão de julho.
- Identificação de versões em worktrees e eventuais alterações ainda não publicadas.
- Avaliação de arquitetura, banco, interface e memória automática; nenhuma tecnologia escolhida por antecipação.

## Achados funcionais desta etapa
- Runner do Drive repassa filtros de pontos/campanhas; config e cinco pipelines também mudaram seus contratos. Copiar só runner cria incompatibilidades com o GitHub observado.
- Script reprodutor gerado pelo runner do Drive não preserva params.points: lacuna de reprodutibilidade identificada estaticamente, sem teste de execução.
- Paginação mudou de 1000 para 250 e timeout de 60 para 180 segundos; benefício de desempenho/confiabilidade não medido.
- Fontes, linhas, hashes, consequências e propostas em ANALISE_DIFERENCAS_20261027.md.

## Próxima ação concreta
Mapear CLI, recipes e callers de RunParams/pipelines para verificar o transporte de
campaigns/points até a execução. Em seguida percorrer as dependências adicionais e
diferenças dos pipelines para preparar uma proposta coerente de reconciliação.

## Retomada por outro agente
Ler README e DECISOES; consultar HISTORICO/MOD-20261027-03, ANALISE_DIFERENCAS_20261027 e INVENTARIO.
Usar listagem direta de pasta para código: a busca do conector omitiu .py em um caso.
Fetch textual de .py devolveu vazio mesmo com tamanho não zero; usar download raw.
Não interpretar limitação da ferramenta como ausência ou arquivo vazio.

## Escopo autorizado
Investigação e manutenção da documentação da modernização nesta branch.
Código operacional, dados, main, instalação do ai-memory e sincronização em massa
permanecem fora desta rodada. Mudanças de documentação não equivalem a adoção da
arquitetura proposta nem a confirmação de funcionamento da plataforma.
