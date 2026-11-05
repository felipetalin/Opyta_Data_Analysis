# Auditoria histórica WSPKIN001/Ictiofauna — 2026-11-03

## Objetivo, escopo e escolha do caso
Registro da investigação somente leitura concluída nesta conversa sobre a carga documentada de 11/09/2026, WSPKIN001/Ictiofauna, projeto 211. Selecionada entre os casos examinados pela combinação de manifesto com hashes, validação, carga/consolidação e produto histórico identificável. Migração concluída não equivale à aprovação final da entrega. Este resultado não se estende às demais cargas.
Nesta rodada: somente documentação e memória autorizadas; nenhuma nova consulta ao banco, importação, migração, correção ou investigação executada.

## Excel: identidade histórica e atual
Caminho declarado pela operação:
`G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração_Ictio_FINAL.xlsx`.
Saída da validação: `VALIDACAO_FINAL\ictiofauna\Resultados_FINAL.xlsx`, sob a mesma pasta.

| Arquivo | SHA-256 registrado na validação de 11/09/2026 | SHA-256 calculado na auditoria em 03/11/2026 |
| --- | --- | --- |
| Entrada FINAL | 319e04e62ffdc37178434792e5c96dc00af42d810193a84cb80f8b5115bf13f2 | 7c776d6fa774cf4858cfa1b6ed046f1fca0c58301fde7fd57d4c09df94da8b6a |
| Saída Resultados_FINAL | 301abd6dba79c3681da2e142f47a4497e57e0231d310e622fdf4304337008f3d | c2fb3a0c7aaa1980858e56ed8a95c620aa772f3abd75516dcd59253c349eb213 |

O manifesto de 11/09/2026 14:04:00Z vincula os caminhos aos hashes históricos: comprovado documentalmente. Esses hashes foram registrados na validação, não comprovados no processo de migração.
As duas cópias atuais possuem conteúdo celular lido equivalente, 76 resultados e 354 indivíduos, mas seus bytes não coincidem com os históricos. O histórico do Drive mostra revisão de entrada em 11/09 e atualização posterior em 14/09; a saída também teve revisões posteriores ao manifesto.
Download das revisões históricas de ambos os arquivos retornou HTTP 403. Não foi determinado se as alterações foram só de empacotamento/formatação ou de valores.

## Trilha por vínculo
| Vínculo | Classificação | Evidência e limite |
| --- | --- | --- |
| Caminhos → hashes na validação | Comprovado documentalmente | manifesto_validacao.json, PRONTO_COM_AJUSTES_AUTOMATICOS, banco conectado, 76 registros, 20 ponto/campanha, 21 táxons, zero espécies sem cadastro; só achado informativo de alias de aba. |
| Relatórios anteriores → aprovação final | Não aplicável | Relatórios anteriores, inclusive official, têm bloqueios sobre versão anterior; não foram promovidos a aceite do FINAL. |
| Arquivo aprovado → bytes efetivamente migrados | Pendente | Não localizado manifesto de execução da carga que fixe o hash consumido; revisões históricas inacessíveis (403). |
| Carga → migrador oficial | Comprovado como declaração documental | Operação declara scripts/migrar_ictiofauna.py; sem stdout/comando/hash do executável daquela carga. |
| Carga → runners/script_runner.py | Pendente | Caminho existe no código; execução direta versus runner não comprovada para esse caso. |
| Carga → commit/build/hash do migrador | Pendente | Registro encontrado de commit pertence à análise posterior, não à migração. |
| Pós-carga → contagens | Comprovado nos registros existentes | Consolidação: 57 resultados, 354 indivíduos, 21 táxons e 76 detalhes de linhas-fonte. Sem soma de peso suficiente para identificar fórmula gravada. |
| Produto histórico → arquivo atual de biometria | Comprovado por SHA-256 | Hash atual da Tabela 13 coincide com execution_metadata.json e manifesto histórico de entrega. |
| Peso efetivamente gravado no banco naquela carga | Pendente | Não consultado banco nesta auditoria; falta exportação/auditoria pós-carga de N e PC por chave. |

## Runner analítico versus migrador
execution_metadata.json: projeto 211, pipeline ictio, runner 1.2, execução 11/09/2026 14:21:17Z, commit f4ec217, branch agent/braavg002-ictiofauna-resultados-2026, dirty=true. Isso comprova registro do runner analítico, não versão do migrador.
Código disponível na auditoria:
- GitHub Opyta_Data/deploy-cloud: commit 7fe41dd577b085837d32e8a5dbb53ed23502dc24, blob do migrador febd6b09df21e4722e7129c088f8915565a7b3a3; média simples de PC_g.
- Drive migrador: SHA-256 d32c332182326f997a99338c427cd0f791d341d6e392f760c97e4128661e7a61, metadado de modificação 08/10/2026; média ponderada e verificações prévias.
Nenhuma dessas identificações foi atribuída à carga de setembro ou ao build operacional atualmente em uso.

## Peso: o que foi reconciliado
Produto: 13_tabela_biometria_biomassa_ictiofauna.xlsx.
SHA-256 calculado em 03/11/2026 e idêntico ao hash histórico de execução/entrega:
`5d83e0b6efec9ff90981c43af52c1b1e85144f2159e26de510df088ebd17feda`.
Soma no produto histórico: 2.610,3 g. Conteúdo reconciliado com a cópia atual por 21 táxons: zero divergências de abundância e biomassa.

Cálculo independente, em memória, sem executar/importar migrador, sobre a cópia atual:
chave = Campanha + Ponto + Metodo_de_Captura + Nome_Cientifico + Tipo_de_Amostragem.

| Método | Resultado |
| --- | --- |
| 76 linhas / 354 indivíduos / 57 grupos | Conferidos |
| Soma linha a linha Σ(Nᵢ × PCᵢ) | 2.610,3000 g |
| Média simples por grupo, depois Σ(N_grupo × média(PC)) | 2.491,1667 g |
| Média ponderada Σ(Nᵢ×PCᵢ)/ΣNᵢ, depois recomposição | 2.610,3000 g |
| Diferença da média simples | -119,1333 g (-4,564%) |
| Grupos com diferença | 7 de 57 |

Exemplo C002/PT_06/Matapi/Psalidodon fasciatus: lotes 42×10, 10×6, 10×5 e 5×4 → 550 g. Média simples dos quatro pesos × 67 indivíduos → 418,75 g.
Valores calculados sobre cópia atual não substituem o Excel histórico por identidade criptográfica.

Conclusão: reconciliação do produto histórico confirmada, mas versão executada do migrador e peso gravado naquela carga continuam sem comprovação. Não foi demonstrado erro nem correção no banco dessa carga. Peso médio (PC_g) e biomassa total não são equivalentes; o cálculo não é SUM(pc_g).

## Lacunas e próxima ação concreta
1. Localizar o Excel pelos hashes históricos acima e o registro que identifique qual arquivo foi passado à carga.
2. Localizar log de migração com comando, caminho/hash do Excel, versão/hash do migrador, stdout/stderr e código de retorno; commit isolado é insuficiente se a árvore estava suja.
3. Localizar exportação/auditoria pós-carga por chave com numero_de_individuos e pc_g. Uma consulta atual, em rodada autorizada, só comprovaria o estado atual, não por si o de setembro.
4. Separar a identificação do build operacional atual da reconstrução da execução histórica.
Nesta rodada, nenhuma dessas buscas adicionais foi executada.

## Fontes primárias examinadas na investigação anterior
- [Operação WSPKIN001](https://drive.google.com/file/d/1pcNjcJLpCiB2McixF13b9OhNMTP7Opx_/view)
- [Manifesto de validação com hashes históricos](https://drive.google.com/file/d/1LruE-T5ZprkgfP723yHWWuTWePe6BYqf/view)
- [Entrada FINAL atual](https://drive.google.com/file/d/12TyGDaUXVrqhLJbHwEYuDJstS4WlvxLn/view)
- [Saída validada atual](https://drive.google.com/file/d/1Iqwa3LTYRLw4W8X9LDO6tHdGdxXBuDBU/view)
- [Relatório anterior com bloqueios](https://drive.google.com/file/d/1FsBNh2j8Aq6GfFm6uv8iyUvMLfwsfIYx/view)
- [Consolidação segura](https://drive.google.com/file/d/1hLwYW_O4VqvXXlVJS1_NKRXzEt52Y78U/view)
- [Metadados da execução analítica](https://drive.google.com/file/d/17sng1SDnnkJef8E8NHE4Srk2J6QqGT2-/view)
- [Tabela 13 histórica](https://drive.google.com/file/d/110ffwV6nSn119iQ96GSkCCmznMcqFecE/view)
- [Manifesto de entrega histórico](https://drive.google.com/file/d/1rlriT_GWcZoYWT-gTON5PGGjtbUmuBym/view)

## Resultado e decisões
Nenhuma proposta de modernização foi promovida a decisão de implementação. Excel continua como entrada. A autorização desta rodada é exclusivamente para registrar estes resultados na documentação e no ai-memory.

## Complemento registrado em 2026-11-05 — hipótese N/PC e retomada adiada

Objetivo: registrar a etapa somente leitura já concluída nesta conversa, por autorização “Registre e seguiremos depois com isso”. Data de registro: 05/11/2026; leituras e hashes da investigação anterior referem-se a 03/11/2026, não foram recalculados nesta rodada. Nenhuma carga, consulta ao banco, correção ou nova busca operacional realizada no registro. Investigação adiada a pedido do responsável, com pendências preservadas.

### Definições: comprovado, compatível e pendente

- Excel WSP disponível: Numero_de_Individuos e PC_g, quatro abas (Capa_Projeto, Pontos_e_Campanhas, Resultados_Ictiofauna e Metadados_Esforco), sem aba de instruções/dicionário nem comentários no arquivo inspecionado. N como quantidade representada é compatível com a estrutura; PC não tem definição documental suficiente de média individual, exemplar representativo ou peso do lote.
- Gerador core/modelos_oficiais.py no GitHub Opyta_Data, commit 7fe41dd577b085837d32e8a5dbb53ed23502dc24, blob 6bdecd1a141fe542f506661051ee6583d2344e97: modelo de ictiofauna usa Quantidade, Biomassa, Comprimento e orientação genérica; não define PC_g. Cópia Drive SHA-256 13a36786ee70cc5f401ef47973cd8e540d41cb1750a815bb0d6d32215369bf10. Não comprovado uso desse modelo no preenchimento histórico WSP.
- Migrador Drive SHA-256 d32c332182326f997a99338c427cd0f791d341d6e392f760c97e4128661e7a61: comprovado no código o cálculo de N×PC por linha, soma N e PC agregado = Σ(N×PC)/ΣN, mapeado para resultados_ictiofauna.pc_g. Trata o destino como peso médio por indivíduo do grupo.
- Migrador GitHub no commit acima, blob febd6b09df21e4722e7129c088f8915565a7b3a3: soma N e usa média simples de PC antes de gravar pc_g.
- scripts/processar_dados.py no mesmo commit: pc_g AS medida_2 e res.medida_2 AS biomassa, sem multiplicação por N nesse trecho. Divergência de nomenclatura; o alias não comprova biomassa total.
- Não localizado nas fontes examinadas um dicionário formal do destino que defina pc_g. Disponibilidade das versões no Drive/GitHub não comprova qual foi executada em setembro ou qual está implantada hoje.

Hipótese de Felipe: compatível com a interpretação operacional ponderada, mas definição histórica de PC no WSP permanece PENDENTE. Peso de exemplar individual × N é uma extrapolação; peso médio dos N indivíduos × N recompõe o total do lote; se PC já for total do lote, a biomassa é ΣPC. Não comprovado se todos os indivíduos foram pesados nem como se obteve PC para N>1. Documentação de outros projetos não fecha a definição deste caso.

### Exemplo real e cálculo independente

Excel disponível, Resultados_Ictiofauna, linhas 51–54:
C002-2026-07-SC / PT_06 / Matapi / Psalidodon fasciatus / Quantitativa.

| Linha | N | PC (g) | N×PC (g) |
| --- | ---: | ---: | ---: |
| 51 | 42 | 10 | 420 |
| 52 | 10 | 6 | 60 |
| 53 | 10 | 5 | 50 |
| 54 | 5 | 4 | 20 |
| Total | 67 | 25 (soma dos PC) | 550 |

Média simples: 6,25 g; ponderada por N: 550/67 = 8,208955 g/indivíduo.
Se PC é média individual por linha, biomassa = 550 g; recomposição com média simples = 418,75 g, diferença 131,25 g.
Se PC é peso total do lote, biomassa = 25 g e peso médio = 25/67 = 0,373134 g/indivíduo.
A média simples é a média das quatro linhas; não a dos 67 indivíduos representados.

No conjunto, Σ(N×PC) = 2.610,3 g; recomposição com médias simples = 2.491,1667 g; diferença de 119,1333 g (4,564%), sete grupos. A Tabela 13 histórica reconcilia com 2.610,3 g e tem identidade SHA-256 histórica comprovada. Essa reconciliação é numérica, condicionada à interpretação de PC; não certifica a pesagem nem o pc_g gravado na carga.

### Continuação da busca e elos ainda pendentes

Cópias alternativas examinadas na investigação anterior também não correspondem aos hashes históricos:
- Resultados_Migração_Ictio_1.xlsx, 20539 bytes, SHA-256 84584e17e859961df25ed1dc381ea520965333204a3754337200a1cb259c65ea.
- Resultados_Migração_Ictio_validada.xlsx, 15579 bytes, SHA-256 36d397a21cdf00138e7ca69e57ac02e25d132e9aa032a7bb547476e0a24cae3f.
_staging WSP só continha cadastro de espécies. Verificados diretórios de migracoes, snapshots, runs e resultados históricos acessíveis; não encontrado elo que fixe o Excel consumido ou o hash do migrador. Revisões antigas seguem sem evidência acessível (tentativas anteriores: HTTP 403); não confundir arquivos de produto com exportação pós-carga por chave.

Consolidação existente registra 57 resultados, 354 indivíduos e 21 táxons, sem N/pc_g por chave; cita public.backup_biota_wspkin001_ictiofauna_consolidado_20260911t111241, não inspecionado. Não foi demonstrado que esse backup contenha o estado posterior à carga.

Próxima ação, quando o responsável retomar: localizar os Excel pelos dois hashes históricos já registrados, o log da migração com comando/caminho/hash do Excel e versão/hash do script, e evidência histórica pós-carga com numero_de_individuos e pc_g por chave; obter a instrução original de pesagem/preenchimento WSP. Uma consulta atual comprova apenas o estado atual sem lastro temporal adicional. Sem aprovação de correção ou decisão de definição de PC nesta etapa.

Fontes adicionais:
- [Gerador do modelo e instruções genéricas](https://github.com/felipetalin/Opyta_Data/blob/7fe41dd577b085837d32e8a5dbb53ed23502dc24/core/modelos_oficiais.py).
- [Migrador GitHub](https://github.com/felipetalin/Opyta_Data/blob/7fe41dd577b085837d32e8a5dbb53ed23502dc24/scripts/migrar_ictiofauna.py).
- [Migrador Drive](https://drive.google.com/file/d/1kwesjff7j3ZHwPUrVy2iiTpeMc7n2RZE/view).
- [Consolidador GitHub](https://github.com/felipetalin/Opyta_Data/blob/7fe41dd577b085837d32e8a5dbb53ed23502dc24/scripts/processar_dados.py).
- [Modelo no Drive](https://drive.google.com/file/d/1FqZyTVpgDiLxghN_8-9UwiEjy4O_xc6T/view).
- [Entrada alternativa _1](https://drive.google.com/file/d/1md4ANt8m2S85ulf4P1uvQ9J2XoKywq57/view).
- [Entrada alternativa validada](https://drive.google.com/file/d/1n5hKWeU9NxfUCCtl6OgLzxjuNq0uaKrP/view).
