# Análise das diferenças — runner e cliente Supabase

Data: 2026-10-27 (America/Sao_Paulo).
GitHub fixado: 3ba41794a495cce57905a78841a4a2bb18800a29.
Escopo: comparação estática dos dois módulos e leitura das dependências diretas
necessárias. Nenhum pipeline foi executado; nenhum acesso ao banco foi realizado.
Os fatos abaixo não equivalem a teste funcional do ambiente do responsável.

## Resumo de achados
| ID | Fato observado | Consequência / avaliação |
| --- | --- | --- |
| DIF-001 | Runner do Drive repassa point_filter para ictio e campaign_filter para quatro grupos de diagnóstico; runner do GitHub não repassa esses argumentos nesses caminhos. | São alterações de seleção dos dados, relevantes ao resultado científico. Não são apenas ajustes visuais ou de organização. |
| DIF-002 | RunParams e assinaturas dos pipelines também diferem entre Drive e GitHub. | Copiar apenas runner é incompatível com o conjunto GitHub observado. Reconciliar uma unidade coerente de dependências. |
| DIF-003 | Gerador de script reprodutor do Drive preserva campaigns, mas não points. | Uma execução restrita por pontos pode ser reproduzida sem aquele recorte. Lacuna identificada por leitura estática; efeito não testado em execução. |
| DIF-004 | Cliente Supabase do Drive usa page_size=250 e timeout=180; GitHub usa 1000 e 60. | Muda tamanho/frequência das requisições e tempo de espera. Não há medição que comprove desempenho ou confiabilidade superior. |

## DIF-001 e DIF-002 — filtros e dependências

No [runner do Drive](https://drive.google.com/file/d/1ZopxoQLl8pa-YgAohfskY41uXRhdvNwn/view), a chamada
para ictio passa point_filter=params.points (linha 242 na versão lida).
As chamadas de mastofauna, primatas, herpetofauna e avifauna passam
campaign_filter=params.campaigns (aproximadamente linhas 301–333).
No runner GitHub fixado essas cinco linhas não existem.

### Conferência dos contratos
| Arquivo / função | Drive observado | GitHub fixado |
| --- | --- | --- |
| [config.py / RunParams](https://drive.google.com/file/d/1TZt82Xc6Ij3EkjEqA8nFKHB3vb9MFBA4/view) | points: list[str] ou None | Campo points ausente |
| [ictio.py / run_ictio_pipeline](https://drive.google.com/file/d/1UHynmIEBvPhOaYbpYHWddefnBh4MIg7l/view) | Aceita campaign_filter, point_filter e sampling_filter; aplica os filtros nas linhas 2902–2904 | Assinatura aceita campaign_filter, sem point_filter ou sampling_filter |
| [mastofauna.py / run_mastofauna_pipeline](https://drive.google.com/file/d/1kgQPaQUpkYhs5jhEc73_VySlpOxygqDu/view) | campaign_filter na assinatura (linha 1168); filtra df_raw (1179) e unidades amostrais | Argumento campaign_filter ausente da assinatura (linha 995) |
| [primatas.py / run_primatas_pipeline](https://drive.google.com/file/d/1AYl2UMTox2nU_JRavuuLSVAuJ8YFGi4W/view) | campaign_filter na assinatura (686); filtra via helper da mastofauna (705) | Argumento ausente (684) |
| [herpetofauna.py / run_herpetofauna_pipeline](https://drive.google.com/file/d/19DwyoMD_biNPTTtOuRU2JdeDP1xoxxNe/view) | campaign_filter na assinatura (588); filtra dados (604) e unidades amostrais | Argumento ausente (211) |
| [avifauna.py / run_avifauna_pipeline](https://drive.google.com/file/d/16631d_sZM2oOlQf3PCo441mfTcNCOkCm/view) | campaign_filter na assinatura (620); filtra dados (643) e unidades amostrais | Argumento ausente (593) |

**Inferência de compatibilidade:** colocar o runner do Drive sobre o restante do
GitHub pode resultar em AttributeError para params.points e, mesmo levando config,
em TypeError para point_filter em ictio ou campaign_filter nos quatro outros grupos.
Essa inferência decorre das assinaturas observadas; não se executou uma montagem mista.

**Implicação do GitHub anterior:** o filtro informado em params.campaigns não é
repassado por aquelas quatro rotas, embora o runner registre campaign_filter em
metadados. Isso pode fazer a intenção registrada divergir do recorte efetivo.
Ainda não se verificaram todos os entry points/recipes nem eventuais filtros internos independentes.

**Proposta, não execução:** preparar futuramente um conjunto coerente incluindo
runner, RunParams, contratos dos pipelines e entry points/recipes que fornecem os
filtros. As dependências adicionais dos pipelines ainda precisam ser percorridas.
Não basta considerar estes sete arquivos como pacote completo já aprovado.

## DIF-003 — script reprodutor não preserva pontos

No mesmo runner do Drive:
- _generate_execution_metadata (linha 62) registra campaign_filter e os points retornados no resultado, mas não o pedido original params.points como filtro separado.
- _generate_reproducer_script (linha 115) serializa params.campaigns.
- O parser do script gerado expõe --campaigns; não há opção --points.
- A instanciação de RunParams gerada passa campaigns, sem points.
- No config do Drive, points tem valor padrão None.

**Consequência inferida:** em uma análise ictio que use subset de pontos, o script
reprodutor gerado não restaura esse subset. Se o mesmo conjunto-base estiver disponível,
a nova execução pode incluir pontos adicionais. A lista de pontos nos metadados ajuda a
investigar, mas não é aplicada automaticamente pelo script observado.

**Proposta:** quando houver autorização de implementação, preservar filtro solicitado,
filtro efetivamente aplicado e abrangência obtida; transportar points no reprodutor.
Verificar com um caso de subset e uma reconstrução da seleção antes de gerar produtos.
Nenhuma correção nem geração foi feita nesta investigação.

## DIF-004 — paginação e espera de rede

[Cliente do Drive](https://drive.google.com/file/d/1_gwvujRVGvcFqEub6NbmNiTC8aRklQ_a/view):
- paginate, linha 40: page_size padrão de 250, frente a 1000 no GitHub.
- urlopen: timeout de 180 segundos, frente a 60 no GitHub.

A função continua acumulando as páginas e encerrando quando retorna menos linhas
que o tamanho solicitado; portanto a alteração não limita deliberadamente o total
retornado a 250 linhas. Para volumes grandes, páginas menores exigem mais requisições;
o timeout maior permite aguardar mais em cada uma. Redução de falhas por timeout é
uma hipótese de motivação, não fato comprovado nem medição de ganho.

A rotina lida não acrescenta retry/backoff nem ordenação explícita à URL da consulta.
Essas propriedades não foram introduzidas pela mudança observada. Comportamento do
servidor, limites e consistência sob alterações simultâneas permanecem não verificados.
Não escolher automaticamente o valor mais recente como melhor configuração.

## Identificação dos conteúdos

runner e cliente têm os hashes normalizados registrados no INVENTARIO.
Para dependências lidas nesta etapa, SHA-256 normalizado (UTF-8 sem BOM, CRLF→LF):

| Arquivo | Drive SHA-256 normalizado | GitHub blob |
| --- | --- | --- |
| config.py | b1e17465c37d3dd6d7e3feecab4afbe9f7531bb2a9526053b1fd187e57e12529 | bb89656354e58f99202ac27627a8761bd8d99bc8 |
| pipelines/diagnostico/ictio.py | ef92d347eddc30550a130c5eaa690230bd2d4a8426bb437a63eb45a22c6b8801 | e994ba7599eddfcc0c1982f9c8b3af752fb3af07 |
| pipelines/diagnostico/mastofauna.py | acbb653ba597b9468735481c9fc317e3b8fc530bc8f0eea362bd555c0ef6877d | efee20475752a103b846933b8f510b40e65971b9 |
| pipelines/diagnostico/primatas.py | 25db73f5df2091a90d1b3eb9128a23f4f1e1c461e20f0aa902e98ca6a7799923 | bad98be304f66f67c63d0c6bdadf2ef9fab8be67 |
| pipelines/diagnostico/herpetofauna.py | e4c71ea2ddb0b2022d370f820fc6fdb6707264b2d8bfa036d158e48218d32027 | 2eea66dcdbf411ea1ef7aff60be2aac541e69cc1 |
| pipelines/diagnostico/avifauna.py | 67dab97fa079b016a6683d97aaa630770a63add4e9bad83729dbd79fbecdd4f4 | 254202403120bf28c29fc0a2bf38eaac62648706 |

SHA-256 e blob GitHub são identificadores de naturezas diferentes; não comparar
suas cadeias entre si para afirmar igualdade. As diferenças de contrato acima foram
confirmadas por leitura do código. AST foi usada somente para inspecionar assinaturas;
nenhum módulo da aplicação foi importado ou executado.

## Aprendizado para a memória da modernização
Ao registrar uma mudança, incluir suas dependências e quais parâmetros precisam
sobreviver à execução/reprodução. Uma nota isolada como “runner mais novo no Drive”
não é suficiente para orientar uma reconciliação segura.

## Próxima ação
Mapear CLI, recipes e demais callers de RunParams/pipelines para verificar por onde
campaigns/points chegam ao runner e quais caminhos ainda ignoram o recorte.
Depois analisar o restante das diferenças dos pipelines antes de propor um pacote
coerente de atualização. Não há sincronização operacional autorizada nesta etapa.
