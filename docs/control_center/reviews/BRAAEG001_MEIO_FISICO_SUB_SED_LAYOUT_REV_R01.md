# BRAAEG001 - Meio fisico - Subterranea/Sedimentos - Revisao R01

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- grupo: Meio fisico
- operacao original: `docs/control_center/operations/BRAAEG001_MEIO_FISICO_MIGRACAO.md`
- tipo: `layout`
- impacto: `R1`
- estado: `regenerated_pending_review`
- aberta em: 2026-08-05
- atualizada em: 2026-08-05

## Linha De Base

- Agua Subterranea: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados/subterranea`
- Sedimentos: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/resultados/sedimentos`
- script: `scripts/projects/braaeg001/gerar_resultados_subterranea_sedimentos_meio_fisico.py`

## Pedido

- seguir os modelos finais de Agua Superficial;
- remover linhas entre pontos, mantendo somente spots;
- usar cores diferentes para os diferentes VMPs;
- iniciar o preenchimento vermelho no menor VMP aplicavel, tanto em Sedimentos quanto em Agua Subterranea.

## Alteracoes

- `ax.plot` substituido por `ax.scatter` nos paines por parametro;
- VMPs recebem cores distintas por coluna normativa;
- faixa vermelha de violacao inicia no menor VMP disponivel para o parametro;
- auditoria dos produtos atualizada com a nova premissa de layout.
- ajuste adicional: funcao grafica alinhada ao `plot_campaign_panel` de Agua Superficial, com `figsize=(14, 9)`, `dpi=600`, legenda superior, cores oficiais de campanha e sem sobrecamada vermelha nos spots em violacao.
- ajuste metodologico-grafico para Sedimentos: adotado Nivel 1 como limite conservador de violacao nos paineis de violacoes; nos paineis por parametro, preenchimento amarelo entre Nivel 1 e Nivel 2 e preenchimento vermelho acima do Nivel 2.

## Validacao

- produtos regenerados em 2026-08-05;
- Agua Subterranea: 258 registros, 43 parametros, 42 paineis, 19 violacoes;
- Sedimentos: 312 registros, 13 parametros, 13 paineis, 33 violacoes;
- inspecao visual realizada em `sedimentos/03_painel_cadmio.png` e `subterranea/03_painel_nitrato_n.png`.
- validacao adicional: `03_painel_Coliformes_Termotolerantes.png`, `sedimentos/03_painel_arsenio.png` e `subterranea/03_painel_nitrato_n.png` conferidos com dimensao identica `8400 x 5400`; gerador sem `ax.plot` nos paineis por parametro.
- validacao sedimentar: `sedimentos/03_painel_cadmio.png` conferido com faixa amarela N1-N2 e vermelha acima de N2; `sedimentos/04_painel_violacoes_chuva_seca.png` conferido no padrao Agua Superficial, contando `> Nivel 1` como violacao.
- minimapa sedimentar: gerado `sedimentos/05_minimapa_violacoes_por_ponto_chuva_seca.png` no padrao de Agua Superficial, com hidrografia, escala, norte, barra de cores e numero absoluto de violacoes por ponto. Planilha de apoio `sedimentos/05_Dados_Minimapas_Sedimentos.xlsx` registra totais por ponto/campanha, separando `Entre Nivel 1 e Nivel 2` e `Acima do Nivel 2`.
- validacao minimapa: dimensao identica ao minimapa de Agua Superficial (`4962 x 2481`); totais fechados em 29 violacoes conservadoras por campanha, 58 no total (`> Nivel 1`), sendo 25 entre N1-N2 e 33 acima de N2.
- ajuste Agua Subterranea: `01_Conformidade_Agua_Subterranea.xlsx` atualizado com preenchimento vermelho nas celulas de pontos que excedem o menor VMP disponivel por parametro; painel `04_painel_violacoes_chuva_seca.png` regenerado por parametro/campanha no padrao Agua Superficial e Sedimentos.
- validacao Agua Subterranea: Excel conferido com 12 celulas destacadas em `Campanha-01-Chuva` e 7 em `Campanha-02-Seca`; painel de violacoes totaliza 19 violacoes pelo menor VMP.
- correcao VMP Agua Subterranea R02: base `fisico_analise_consolidada` corrigida em 2026-08-06 conforme revisao do usuario, com backup `backup_fisico_braaeg001_vmp_subterranea_20260806t192437z`; cadastro mestre `parametros_analise` atualizado quando houve correspondencia, com backup `backup_parametros_analise_braaeg001_vmp_subterranea_20260806t192437z`.
- consolidado pos-correcao: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/consolidacao_pos_c02/20260806T192458Z_consolidado_meio_fisico_braaeg001_pos_c02.xlsx`; auditoria de correcao: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/Meio_fisico/migracao/revisoes_vmp_subterranea/20260806T192437Z_auditoria_correcao_vmp_subterranea_braaeg001.xlsx`.
- produtos Subterranea regenerados parcialmente apos R02: `02_Dados_por_Parametro_Agua_Subterranea.xlsx`, 42 paineis por parametro e `04_painel_violacoes_chuva_seca.png`; `01_Conformidade_Agua_Subterranea.xlsx` permaneceu bloqueado para escrita, provavelmente aberto no Excel, e precisa ser regenerado/destacado apos fechamento.

## Gate R

- status: `awaiting_user_approval`
- pendencia: aprovacao visual do usuario sobre a revisao R01.
