# BRACED001 - Ictiofauna - paineis por campanha - revisao R01

## Controle

- projeto: BRACED001 / Fonseca-Biota Aquatica
- grupo: Ictiofauna
- revisao: corrigir figuras para o layout final da pasta A&G indicada pelo usuario
- tipo principal: `layout`
- tipo secundario: `package`
- impacto: `R1`
- estado: `awaiting_revision_approval`
- aberta em: 2026-08-13

## Linha De Base

- referencia visual: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna`
- pacote Fonseca anterior: figuras geradas em 2026-08-13 pelo pipeline com campanhas agrupadas no mesmo painel
- backup: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/ictiofauna/reviews/R01_backup_pre_paineis`

## Diagnostico

- a pasta A&G final usa paineis separados `C01-Chuva` e `C02-Seca`;
- a primeira geracao Fonseca usou barras agrupadas ou matriz combinada em um unico painel;
- causa: o perfil generico do pipeline foi usado como autoridade, quando a pasta final A&G deveria ter sido a referencia visual direta.

## Escopo Aprovado

- regenerar 02, 03, 06, 07, 08, 09, 08B, 09B e 10 com o reprodutor final A&G;
- atualizar tabelas 08, 09, 08B e 09B pela mesma rotina aprovada de CPUE;
- atualizar relatorio, manifesto e validacao por dependencia;
- nao reabrir Gates A ou B; dados, taxonomia, migracao e consolidacao permanecem inalterados.

## Gate R

- status: aguardando aprovacao do usuario
- antes: 02, 03, 06, 07 e 10 com campanhas agrupadas; 08 e 09 sem separacao em paineis
- depois: figuras temporais com paineis independentes `C01-Chuva` e `C02-Seca`, reproduzindo a referencia final A&G
- 08B e 09B: mantidos como heatmaps agregados, conforme a referencia A&G
- contato visual: `outputs/_project_scripts/BRACED001__fonseca_biota_aquatica/ictiofauna/reviews/20260813T1300_R01_paineis_contact_sheet_figuras_ictio_a4_paisagem_R01.png`
- validacao: 41 arquivos; 20 XLSX; 17 PNG; 1 HTML; 2 JSON; 1 MD
- planilhas: 0 erros de abertura e 0 erros de formula
- imagens: 0 arquivos vazios, em baixa resolucao ou sem variacao visual
- reconciliacao: 14 taxons e 192 individuos
- produtos genericos da referencia A&G ausentes: 0
- relatorio e manifesto atualizados apos a regeneracao

## Refinamento Do Produto 15

- especies definidas pelo usuario:
  - `Brycon opalinus`, por estar ameacada;
  - `Pareiorhaphis scutula`, bentonica;
  - `Trichomycterus brasiliensis`, bentonica;
- prancha ampliada para A3 paisagem, com 2 linhas de campanha x 3 colunas de especies;
- rotulos dos pontos proximos distribuidos em triangulos e diagonais, com linhas-guia ate a coordenada real;
- arquivo final: `15_mini_mapa_especies_indicadoras_cpuen_ictiofauna.png`;
- tabela final: `15_df_mini_mapa_especies_indicadoras_cpuen_ictiofauna.xlsx`;
- validacao: 108 combinacoes especie-campanha-ponto, 0 erros de formula, imagem 9924 x 7014 px e nao vazia;
- produto antigo de cambevas removido da pasta final e preservado no backup `R01_backup_minimapa_pre_especies`;
- manifesto atualizado sem referencias ao produto antigo.
