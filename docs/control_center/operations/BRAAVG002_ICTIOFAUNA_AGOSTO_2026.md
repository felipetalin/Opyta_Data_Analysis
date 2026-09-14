# BRAAVG002 - Ictiofauna - Agosto/2026

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- grupo: Ictiofauna
- operacao: validacao, cadastro taxonomico, migracao, consolidacao e Darwin Core da campanha `49a-Ago-26`
- estado atual: `completed`
- aberta em: 2026-09-01
- atualizada em: 2026-09-01
- proxima acao: operacao encerrada; gerar outros produtos somente mediante novo Gate C

## Caminhos

- dados: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Migracao de dados/2026/Ictiofauna/projeto_ictio_real - AVG 260625_GATEA_R01-rev.xlsx`
- cadastro de especies: `public.especies`
- saida: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/agosto`
- dossie: `docs/AVG_ICTIOFAUNA_2026.md`
- recipe: `configs/projects/braavg002_ictiofauna_2026.json`
- validacao final: `outputs/validacoes/braavg002_ictiofauna_agosto_2026_gates_ab`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Campanha `49a-agosto-26` identificada na planilha revisada. |
| Validacao | concluida | Revalidacao final com 0 bloqueios, 3 avisos historicos e `pode_prosseguir=true`. |
| Gate A - dados | aprovado | Usuario aprovou; `Metadados_Esforco` e a fonte autoritativa e PIC-05/agosto = 80. |
| Cadastro de especies | concluido | `Xiphophorus hellerii` cadastrada como `id_especie=6926`. |
| Auditoria de atributos | concluida | Sete registros antigos tiveram apenas campos vazios completados. |
| Gate B - especies | aprovado | Usuario aprovou o novo cadastro e a regularizacao dos sete registros. |
| Migracao | concluida | 631 esforcos, 535 resultados, 49 campanhas e 1.544 individuos. |
| Consolidacao | concluida | Somente BRAAVG002/Ictiofauna foi substituida, com backup e reconciliacao. |
| Configuracao | concluida | Escopo reduzido a uma planilha Darwin Core de agosto. |
| Gate C - analises | aprovado | Usuario solicitou apenas Darwin Core na pasta `2026/agosto`. |
| Geracao | concluida | Um XLSX Darwin Core gerado; nenhum outro produto criado. |
| Revisao tecnica | concluida | 4 abas; 7 eventos, 7 ocorrencias e 7 registros biometricos; sem erro de formula. |
| Fechamento | concluido | Registro, painel, dossie, registry e recipe atualizados. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved` | Esforco herdado de `Metadados_Esforco`; PIC-05/agosto = 80. |
| B - especies | `approved` | `Xiphophorus hellerii` e sete registros antigos aprovados. |
| C - analises | `approved` | Produto unico: Darwin Core de agosto. |

## Validacao Dos Dados

- bloqueios finais: 0
- avisos finais: 3, historicos: divergencias de esforco, duplicatas exatas e grupos agregados
- campanha: 10 pontos previstos, 7 linhas, 30 individuos e 6 especies
- coordenadas: 10/10 preenchidas; 10/10 comparadas com julho; variacao maxima 0,0 m
- estrategia espacial: preservar coordenadas por campanha; agosto repete julho
- ajuste do usuario: normalizacao de cinco ocorrencias de `Xiphophorus hellerii`

## Cadastro E Auditoria De Especies

- especie nova: `Xiphophorus hellerii` Heckel, 1848, `id_especie=6926`
- registros regularizados: `Neoplecostomus franciscoensis`, `Parotocinclus robustus`, `Trichomycterus novalimensis`, `Pareiorhaphis mutuca`, `Characidium fasciatum`, `Gymnotus carapo` e `Poecilia reticulata`
- somente campos nulos foram completados; valores existentes foram preservados

## Migracao E Consolidacao

- projeto: `id_projeto=9`, `codigo_interno_opyta=BRAAVG002`
- antes: 48 campanhas, 621 esforcos, 528 resultados e 1.514 individuos
- depois: 49 campanhas, 631 esforcos, 535 resultados e 1.544 individuos
- agosto: 10 esforcos, 7 resultados, 6 especies e 30 individuos
- backup: `public.bkp_biota_braavg002_ictio_20260901_172512`, 528 linhas
- consolidacao: 528 linhas removidas e 535 inseridas somente em BRAAVG002/Ictiofauna
- divergencias: nenhuma nos totais reconciliados

## Configuracao Das Analises

- template: Darwin Core IEF oficial, igual a julho/2026
- paleta: nao aplicavel
- pasta: `Resultados ictio/2026/agosto`
- produto: `DarwinCore_IEF_Ictiofauna_Monitoramento_De_Ictio_E_Bentos_Brumado_Avg.xlsx`

## Pendencias

- Nenhuma no escopo. Outros produtos exigem novo Gate C.

## Fechamento E Aprendizados

- validador: XLSX abriu; abas e dimensoes conferidas; nenhum erro de formula
- inventario: pasta de agosto contem somente o Darwin Core aprovado
- pattern: Gate C pode limitar uma entrega mensal a um unico produto
- backlog: criar consolidador parametrizado por projeto/grupo para evitar `TRUNCATE` global
