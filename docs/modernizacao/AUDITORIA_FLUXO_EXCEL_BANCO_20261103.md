# Auditoria do fluxo Excel → banco — 2026-11-03

## Objetivo, autorização e método
Registro da auditoria somente leitura já concluída nesta conversa. O responsável autorizou a retomada para investigação e, em rodada posterior, autorizou exclusivamente documentação nesta branch e páginas correspondentes no ai-memory. Esta rodada não acrescenta investigação técnica, consulta ao banco, importação, migração ou correção de código. Excel permanece como padrão de entrada.

O MCP ai-memory respondeu no painel. Foi lida sources/estado_atual.md (page_id 01a1a2b4-e0f0-7dd0-b389-92b00b0d28d6), baseada no commit de0dfcc34312147bd1f103ecd9782067002e535a; ESTADO_ATUAL.md na base b7a77e23b892c601a920ecb99e69e39e86be7bae manteve blob 8a8bd767ce6bfd1f559cab842dff2edb96aafdd2. O resumo técnico anterior não havia sido gravado como página explícita; foi usado o contexto visível da conversa.

Verificação: leitura estática de código/documentos em commits fixados; leitura autenticada dos arquivos do Drive em memória, sem executar código da aplicação. Comparação textual limitada a normalização de BOM/CRLF. Metadados e presença no Drive não comprovam uso atual.

## Mapa identificado
1. Excel do projeto → Opyta_Data/app/pages/01_Importacao.py: upload .xlsx, cópia em runtime/importacao, normalização textual e clean_*.xlsx.
2. validators/registry.py verifica abas; validators/importacao/{reader,pipeline,checkers,advanced_checks,report}.py valida conteúdo e referências; can_proceed significa ausência de achados block.
3. Cadastro mestre paralelo: validators/especies/{pipeline,normalizer,rules,db_checker}.py → scripts/cadastrar_especies.py → especies e tabelas auxiliares.
4. runners/registry.py seleciona scripts/migrar_*.py; runners/script_runner.py executa subprocesso. Registro ampliado cobre ictiofauna, bentos, fito, zoo, meio físico, avifauna, herpetofauna e mastofauna. Leitura detalhada de migradores: ictiofauna e meio físico; não foi auditado integralmente cada grupo.
5. Migradores → clientes/projetos/campanhas/pontos_coleta; biota segue por esforcos_amostragem e resultados por grupo. Meio físico usa parametros_analise e resultados_analise.
6. scripts/processar_dados.py faz UNION ALL/JOIN e reconstrói biota_analise_consolidada globalmente na versão geral lida.
7. Opyta_Data_Analysis/scripts/run_pipeline.py ou scripts/run/run_project_recipe.py → RunParams → src/opyta_analysis/runner.py → análises/produtos. É runner analítico, não prova da execução de migração.
8. Rotas adicionais no Analysis: geradores SQL de ictio/herpetofauna, migrador específico AVG bentos e REST físico com staging. Não foi demonstrada aprovação comum obrigatória a todos esses caminhos.

## Onde estão as validações e seus limites
| Tema | Evidência de código | Limite |
| --- | --- | --- |
| Escrita/texto | Interface normaliza Unicode/espaços/hífens; normalizer de espécies trata capitalização e sp./cf./aff. | Limpeza textual não comprova taxonomia nem categoria semanticamente correta. |
| Coordenadas | check_pontos verifica faixas; check_pontos_conflitantes_no_banco compara projeto/campanha/ponto, tolerância 1e-6 grau. | Falha da consulta espacial vira warning; não há referência oficial geográfica obrigatória demonstrada nesse pipeline geral. |
| KML/KMZ | Analysis/scripts/validation/validar_migracao_ictiofauna.py oferece comparação geográfica. | Referência opcional; cobertura universal não demonstrada. |
| Espécies | Estrutura, campos, formato, gênero, duplicatas, presença/completude no cadastro; interface usa strict_unknown_species=True. | GENUS_MISMATCH é warning geral e bloqueio no validador específico ictio. |
| Taxonomia externa | No Drive: scripts/validation/species/validar_cadastro_especies.py e perfis do validador de pacote. | Rota adicional; não comprovada como etapa obrigatória de toda importação. APIs externas não consultadas pela auditoria. |
| Categorias | Obrigatoriedade, aliases de grupos, referências de método/tipo e comparações com cadastro. | Não encontrado domínio semântico único obrigatório para ameaça, origem, hábito e estratégia nos módulos lidos. |
| Escrita no banco | Interface libera por can_proceed; cadastro revalida; ictio Drive tem verificações próprias. | Execução direta do migrador não demonstra passagem pelo pipeline completo da interface. |

## Arquivos e versões consultados
| Fonte fixada | Recorte consultado |
| --- | --- |
| Analysis, modernizacao/memoria-e-auditoria-inicial, b7a77e23b892c601a920ecb99e69e39e86be7bae | Registros de modernização; runner.py, config.py, supabase_client.py, validators.py; scripts/run_pipeline.py, run/run_project_recipe.py; validation/validar_migracao_ictiofauna.py; migrations/ictiofauna/ictio_gen_sql.py; migrations/herpetofauna/herp_gen_sql.py; projects/avg/migrar_bentos_avg_2026.py; migrations/meio_fisico/migrar_meio_fisico_rest.py; READMEs de migração/validação. |
| Opyta_Data main, 24241161d1654ef3eb537d73c810c60041c33236 | app/pages/01_Importacao.py, runners/{registry,script_runner}.py, validators/registry.py e scripts/migrar_ictiofauna.py. |
| Opyta_Data deploy-cloud, 7fe41dd577b085837d32e8a5dbb53ed23502dc24 | Interface; importacao/{pipeline,checkers,advanced_checks}; especies/{rules,normalizer}; registry/runner; migrador ictio e consolidador. |
| Drive Opyta_Data | Contrapartes acima; importacao/{reader,report}; especies/{pipeline,db_checker}; common_checks.py; scripts/{validar_importacao,cadastrar_especies,migrar_meio_fisico}.py. |
| Drive Analysis | Runner; validar_pacote_migracao.py; validador taxonômico; perfis ictio/zooplâncton; documentação e registros de execução. |

## Evidências e hipóteses separadas
Comprovado por comparação: 8 de 10 módulos Drive × deploy-cloud coincidem após BOM/CRLF. Divergem:
- validators/especies/rules.py: Drive exige cadastro mais completo; lista de valores obrigatórios em deploy-cloud limita-se a nome científico/grupo.
- scripts/migrar_ictiofauna.py: Drive preserva Σ(N×PC) via média ponderada e valida consistência; deploy-cloud usa média simples de PC_g. Impacto em uma carga histórica não pode ser deduzido só dessa diferença.

Identificação do migrador Drive consultado: SHA-256 d32c332182326f997a99338c427cd0f791d341d6e392f760c97e4128661e7a61. Blob GitHub deploy-cloud: febd6b09df21e4722e7129c088f8915565a7b3a3. SHA-256 e blob Git não são grandezas diretamente comparáveis.

Evidência histórica de uso: manifesto 20260812T015704.787936_validacao_6b3fbca2.json registra deploy-cloud, commit 439d907, dirty=true, hash do Excel e validação OK; não comprova versão em produção hoje. Registro BRAAEG001/zooplâncton de 27/07/2026 documenta aplicação/backups/423 resultados; não foi tratado como carga ictio.

Hipótese a testar: reconhecimento do upload por nome/tamanho/grupo e booleano de sessão pode não invalidar uma aprovação para conteúdos diferentes com os mesmos atributos. Não reproduzida em execução.

Não disponíveis à comprovação: build efetivamente servido no Streamlit, ambiente dos operadores, banco atual/constraints/RLS/triggers. Não acessados nesta auditoria; não classificados como inexistentes. Fetch textual vazio de .py/JSON foi contornado por leitura bruta em memória.
No recorte GitHub do Analysis não constavam os caminhos validar_pacote_migracao.py e scripts/validation/species/validar_cadastro_especies.py encontrados no Drive. Isso não prova ausência em outras branches.

## Primeira prioridade proposta, não aprovada para implementação
Definir contrato único de aprovação do Excel antes da escrita, compartilhado por interface/CLI/migradores, com regras por grupo versionadas e aprovação ligada ao hash do arquivo realmente carregado. Fundamentação: caminhos/versões aplicam regras diferentes; limpeza textual e ausência de bloqueios não asseguram equivalência da carga. Não substituir Excel nem sincronizar pastas como primeiro passo.

## Fontes
- [Interface deploy-cloud](https://github.com/felipetalin/Opyta_Data/blob/7fe41dd577b085837d32e8a5dbb53ed23502dc24/app/pages/01_Importacao.py)
- [Checkers](https://github.com/felipetalin/Opyta_Data/blob/7fe41dd577b085837d32e8a5dbb53ed23502dc24/validators/importacao/checkers.py)
- [Migrador GitHub](https://github.com/felipetalin/Opyta_Data/blob/7fe41dd577b085837d32e8a5dbb53ed23502dc24/scripts/migrar_ictiofauna.py)
- [Migrador Drive](https://drive.google.com/file/d/1kwesjff7j3ZHwPUrVy2iiTpeMc7n2RZE/view)
- [Manifesto histórico de validação](https://drive.google.com/file/d/1FIH46jb24u9rhdWDOL5B1eBZt-kLT7NU/view)
- [Lastro de deploy histórico](https://drive.google.com/file/d/1sf_8q508wwuCkEdkSqM-uk24lUG87L7B/view)
- [Caso WSPKIN001, registrado separadamente](AUDITORIA_WSPKIN001_ICTIOFAUNA_20261103.md)

## Próxima ação
Localizar o Excel pelos hashes históricos, o log da migração e a evidência pós-carga por chave, começando pelo caso WSPKIN001. Esta rodada executa somente o registro. Nenhuma correção de código ou política foi aprovada.
