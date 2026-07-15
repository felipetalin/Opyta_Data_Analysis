# BRAAVG002 - Ictiofauna - Preparacao da geracao de resultados 2026

## Controle

- projeto: `BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`
- grupo: Ictiofauna
- operacao: organizacao da matriz de geracao antes de executar novos produtos
- estado atual: `generated_pending_review`
- aberta em: 2026-07-13
- atualizada em: 2026-07-15
- proxima acao: aprovar a regra revisada de malha amostral antes de regenerar graficos; produtos tradicionais e espaciais ainda nao foram reemitidos com o ajuste de 2026-07-15

## Caminhos

- dados: banco consolidado `public.biota_analise_consolidada`, projeto `id_projeto=9`, grupo `Ictiofauna`
- cadastro de especies: banco `public.especies`; sem novo cadastro nesta preparacao
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026`
- dossie:
  `docs/AVG_ICTIOFAUNA_2026.md`
- recipe:
  `configs/projects/braavg002_ictiofauna_2026.json`
- tema:
  `configs/clients/braavg002.json`
- runner:
  `scripts/projects/avg/run_ictio_avg_2026_por_campanha.py`
- lastro:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg`

## Contexto Consultado

- Central de Controle: `docs/control_center/README.md`
- Politica LLM: `docs/control_center/LLM_CONTEXT_POLICY.md`
- Workflow oficial: `docs/control_center/WORKFLOW.md`
- Operacoes ativas: `docs/control_center/ACTIVE_OPERATIONS.md`
- Operacao concluida de origem: `docs/control_center/operations/BRAAVG002_ICTIOFAUNA_JUNHO_2026.md`
- Registry filtrado: `docs/registry/project_registry.json`
- Dossie AVG Ictiofauna: `docs/AVG_ICTIOFAUNA_2026.md`
- Tema/recipe cliente: `configs/clients/braavg002.json`
- Runner AVG: `scripts/projects/avg/run_ictio_avg_abril_maio.py`
- Wrapper de geracao: `scripts/projects/avg/run_ictio_avg_2026_por_campanha.py`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Projeto BRAAVG002/Ictiofauna identificado; codigo `AVG0002` tratado como referencia operacional a `BRAAVG002`. |
| Validacao | herdada | Dados ate `47a-Jun-26` foram validados na operacao `BRAAVG002_ICTIOFAUNA_JUNHO_2026`; nova campanha exige reabrir validacao. |
| Gate A - dados | herdado aprovado | Gate A aprovado em 2026-06-30 para a copia `GATEA_R01`; nao ha nova base nesta preparacao. |
| Cadastro de especies | herdado | As 13 especies da rodada ate junho ja existiam no banco. |
| Auditoria de atributos | herdada com ressalvas | Atributos ecologicos/ameaca vazios foram aceitos como ressalva no Gate B anterior. |
| Gate B - especies | herdado aprovado | Gate B aprovado em 2026-06-30; nova especie ou novo dado reabre Gate B. |
| Migracao | herdada | Migracao ate `47a-Jun-26` concluida e auditada sem divergencias. |
| Consolidacao | herdada | Consolidacao da fatia BRAAVG002/Ictiofauna concluida com 519 linhas. |
| Configuracao das analises | concluida | Recipe, fonte analitica AVG/GEOARC001, ano temporal ago-jul, traits aprovados e KML padrao provisorio registrados. |
| Gate C - analises | aprovado provisoriamente | Usuario autorizou assumir KML padrao para gerar os resultados; crosswalk e traits usados como camada analitica sem alterar banco. |
| Geracao dos produtos | aguardando regeneracao pontual | Analises tradicionais C001-C047 ja tinham sido regeneradas em `Consolidado_2026/icitiofauna`; nova regra de malha amostral recebida em 2026-07-15 foi aplicada apenas no codigo/registro, sem gerar novos graficos por orientacao do usuario. |
| Revisao tecnica | pendente | Validacao automatica OK; falta revisao tecnica/conteudo pelo usuario. |
| Revisao de layout | parcial | Minigraficos e sintese visualmente conferidos; legenda do mapa de balanco ajustada para fora dos pontos. |
| Fechamento | pendente | Encerrar apos aprovacao, geracao e revisao da rodada alvo. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved_inherited` | Herdado da operacao concluida `BRAAVG002_ICTIOFAUNA_JUNHO_2026`; reabrir se entrar nova base/campanha nao migrada. |
| B - especies | `approved_inherited` | Herdado da operacao concluida; reabrir se houver taxon novo ou ajuste taxonomico. |
| C - analises | `approved_provisional_generated` | Aprovacao operacional do usuario em 2026-07-13 para usar KML padrao provisoriamente e gerar resultados; banco e coordenadas mestre nao alterados. |

## Configuracao Das Analises

- numero de campanhas cadastradas no recipe: 3.
- campanhas cadastradas:
  - `abril` -> `45a-Abr-26` -> pasta `abril`;
  - `maio` -> `46a-Mai-26` -> pasta `maio`;
  - `junho` -> `47a-Jun-26` -> pasta `junho`.
- template: `scripts/projects/avg/run_ictio_avg_2026_por_campanha.py`, chamando o runner historico `scripts/projects/avg/run_ictio_avg_abril_maio.py`.
- paleta: `configs/clients/braavg002.json`, tema `gold_avg_green_2026`.
- pasta raiz de saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026`
- produtos esperados por campanha: 31 arquivos oficiais, sendo 15 PNG e 16 XLSX.
- comandos seguros antes da geracao:
  - listar alvos: `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --list-campaigns`;
  - preflight: `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --preflight --campaign junho`.
- comando de geracao, somente apos Gate C:
  `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --campaign {campanha}`.
- regra para nova campanha: adicionar alvo no recipe apenas depois de validacao, Gate A/B quando aplicavel, migracao e consolidacao auditadas.

## Avaliacao De Estudo Longo E Modelo GEOARC001

- auditor criado:
  `scripts/projects/avg/audit_ictio_avg_long_study_readiness.py`
- saida da auditoria:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/readiness_ictio_long_study_20260713`
- arquivos:
  - `readiness_ictio_avg_long_study.json`;
  - `readiness_ictio_avg_long_study.xlsx`;
  - `readiness_ictio_avg_long_study.md`.
- campanhas no banco: 47, de `1a-Ago-22` a `47a-Jun-26`.
- anos cobertos: 2022 a 2026.
- campanhas por ano: 2022 = 5; 2023 = 12; 2024 = 12; 2025 = 12; 2026 = 6.
- pontos: 13.
- grade ponto-campanha apos regra revisada: 585 amostragens efetivas; 26 combinacoes removidas por nao-amostragem/realocacao.
- consolidado: 519 linhas, 13 especies, 1.486 individuos.
- avaliacao inicial:
  - serie longa: pronta;
  - beta/LCBD taxonomico: gerado e validado;
  - funcional: gerado e validado com os 13 traits aprovados;
  - mini mapas/sintese espacial funcional: gerados com KML padrao provisorio, hidrografia AVG e delimitacao AC01/AC02.

### Coordenadas Para Minigraficos

- `pontos_coleta` possui 0 coordenadas ausentes.
- os 13 pontos possuem coordenada estavel ao longo das 47 campanhas.
- comparacao com `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Geo/Ponto amostral - AVG.kml`:
  - 13/13 pontos OK;
  - distancia maxima: 0,07 m.
- comparacao com `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Geo/KML Atual/Ponto amostral - AVG.kml`:
  - 6/13 pontos OK;
  - 7 pontos divergentes;
  - distancia maxima: 1.610,2 m.
- divergencias contra KML Atual:
  - `PIC-03`: 182,0 m;
  - `PIC-06`: 384,1 m;
  - `PIC-07`: 546,2 m;
  - `PIC-08`: 324,7 m;
  - `PIC-09`: 286,6 m;
  - `PIC-11`: 1.610,2 m;
  - `PIC-12`: 238,6 m.
- decisao registrada em 2026-07-13:
  - usar o KML da raiz `Geo` como fonte operacional provisoria para gerar os resultados agora;
  - se o `KML Atual` for adotado posteriormente, Gate A deve ser reaberto para correcao dos 7 pontos divergentes antes de regenerar produtos espaciais finais.
- ajuste recebido em 2026-07-15:
  - `PIC-01`: vigente de `C001` a `C039`; descontinuado de `C040` em diante por restricao de acesso;
  - `PIC-02` original: vigente de `C001` a `C039`; sem amostragem em `C040-C042`;
  - `PIC-02` realocado a partir de fevereiro/2026 (`C043-2026-02-CH`) para `-19.800376/-43.710610`;
  - `PIC-03`: vigente de `C001` a `C039`, sem `C040-C042`, amostrado excepcionalmente em `C043`, e descontinuado de `C044` em diante;
  - `PIC-11` definido em `-19.801526/-43.700959`;
  - `PIC-11`: vigente de `C001` a `C039`; descontinuado de `C040` em diante por restricao de acesso;
  - ajustes aplicados na camada analitica, sem alterar banco mestre.
- delimitacao para minigraficos:
  - usar `area_controle` como campo analitico derivado de `point_layout.control_groups`;
  - `Area de controle 01`: `PIC-01`, `PIC-02`, `PIC-03`, `PIC-04`, `PIC-05`, `PIC-06`, `PIC-07`, `PIC-08`, `PIC-09`, `PIC-11`;
  - `Area de controle 02`: `PIC-10`, `PIC-12`, `PIC-13`;
  - preservar a ordem AC01 + AC02 tambem nos minigraficos espaciais.

### Traits Funcionais

- modelo de referencia: `scripts/projects/geoarc001/generate_functional_exploratory_analysis.py`.
- campos funcionais exigidos:
  - `Habitat_funcional`;
  - `Preferencia_correnteza`;
  - `Guilda_trofica`;
  - `Porte_corporal`;
  - `Sensibilidade_funcional`.
- especies com traits completos reaproveitaveis do piloto GEOARC001: 6.
- especies que precisam completar traits: 7:
  - `Characidium fasciatum`;
  - `Geophagus brasiliensis`;
  - `Neoplecostomus franciscoensis`;
  - `Pareiorhaphis mutuca`;
  - `Parotocinclus robustus`;
  - `Poecilia mexicana`;
  - `Trichomycterus novalimensis`.
- observacao: o cadastro `public.especies` ainda possui lacunas ecologicas/ameaca para as 13 especies; para a analise funcional, a pendencia executavel imediata e completar a tabela de traits do projeto.

#### Matriz De Revisao Criada Em 2026-07-13

- script:
  `scripts/projects/avg/build_ictio_avg_species_traits_review.py`
- saida:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/species_traits_review_20260713`
- workbook:
  `braavg002_ictiofauna_traits_funcionais_revisao.xlsx`
- JSON:
  `braavg002_ictiofauna_traits_funcionais_revisao.json`
- markdown:
  `braavg002_ictiofauna_traits_funcionais_revisao.md`
- status: `approved_for_analysis`.
- aprovacao: usuario disse "aprovado" em 2026-07-13.
- escopo da aprovacao: uso como matriz analitica do projeto; nenhuma alteracao aplicada em `public.especies`.
- especies avaliadas: 13.
- traits reaproveitados do piloto GEOARC001: 6.
- traits novos propostos para revisao: 7.
- especies com traits novos propostos:
  - `Characidium fasciatum`: bentonico, reofilico, insetivoro, pequeno, intermediaria;
  - `Geophagus brasiliensis`: bentopelagico, generalista, onivoro, medio, tolerante;
  - `Neoplecostomus franciscoensis`: bentonico, reofilico, perifitivoro, medio, sensivel;
  - `Pareiorhaphis mutuca`: bentonico, reofilico, perifitivoro, medio, sensivel;
  - `Parotocinclus robustus`: bentonico, intermediario, perifitivoro, pequeno, intermediaria;
  - `Poecilia mexicana`: nectonico, limnofilico, onivoro, pequeno, tolerante;
  - `Trichomycterus novalimensis`: bentonico, reofilico, insetivoro, pequeno, sensivel.
- aplicacao no banco: nao executada. Se a decisao futura for gravar estes campos em `public.especies`, reabrir/aprovar Gate B antes do apply.
- ajuste taxonomico de apresentacao em 2026-07-13:
  - `Poecilia mexicana` deve aparecer nos produtos como `Poecilia cf. mexicana`;
  - motivo: usuario informou duvida na identificacao;
  - escopo: override analitico/de relatorio, preservando `Poecilia mexicana` como chave de banco/juncao;
  - banco `public.especies`: nao alterado.

### Analises GEOARC001 Candidatas

- beta/LCBD taxonomico:
  `scripts/projects/geoarc001/generate_exploratory_assembly_analysis.py`
  - status: gerado e validado;
  - adaptacao AVG: ano temporal agosto-julho e periodo hidrologico CH/SC via fonte analitica.
- composicao funcional:
  `scripts/projects/geoarc001/generate_functional_exploratory_analysis.py`
  - status: gerado e validado com os 13 traits aprovados.
- mini mapas funcionais:
  `scripts/projects/geoarc001/generate_functional_spatial_mini_maps.py`
  - status: gerado e validado com KML padrao provisorio;
  - requisito AVG: incluir delimitacao `area_controle` para separar `Area de controle 01` e `Area de controle 02`.
- sintese espacial funcional:
  `scripts/projects/geoarc001/generate_functional_spatial_synthesis.py`
  - status: gerada e validada com KML padrao provisorio;
  - requisito AVG: preservar delimitacao `area_controle` nos mapas/sinteses.

### Crosswalk De Campanhas E Nomenclatura

- script:
  `scripts/projects/avg/build_avg_campaign_crosswalk.py`
- saida:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/campaign_crosswalk_20260713`
- arquivos:
  - `braavg002_campaign_crosswalk.xlsx`;
  - `braavg002_campaign_crosswalk.json`;
  - `braavg002_campaign_crosswalk.md`;
  - `braavg002_campaign_rename_dry_run.sql`.
- regra proposta:
  - `CH`: outubro a marco;
  - `SC`: abril a setembro.
- ano temporal:
  - ciclo de agosto a julho;
  - meses agosto-dezembro pertencem ao ano de inicio;
  - meses janeiro-julho pertencem ao ano iniciado no ano anterior.
- ciclos validados:
  - `2022/2023`: 12 campanhas, `1a-Ago-22` a `12a-Jul-23`;
  - `2023/2024`: 12 campanhas, `13a-Ago-23` a `24a-Jul-24`;
  - `2024/2025`: 12 campanhas, `25a-Ago-24` a `36a-Jul-25`;
  - `2025/2026`: 11 campanhas, `37a-Ago-25` a `47a-Jun-26`; ciclo parcial, falta julho/2026.
- padrao proposto:
  - `1a-Ago-22` -> `C001-2022-08-SC`;
  - `47a-Jun-26` -> `C047-2026-06-SC`.
- estrategia recomendada no momento: `crosswalk_analitico_primeiro`.
- apply no banco: `not_approved`.
- impacto estimado se renomear no banco:
  - `public.campanhas`: 47 linhas globais por `id_campanha`;
  - `public.biota_analise_consolidada` Ictiofauna: 519 linhas;
  - `public.biota_analise_consolidada` Zoobentos: 3.937 linhas;
  - `public.fisico_analise_consolidada`: 0 linhas.
- avaliacao tecnica:
  - nao e dificil do ponto de vista de SQL;
  - e operacionalmente sensivel, porque `campanhas` e tabela global e a renomeacao afeta Zoobentos alem de Ictiofauna;
  - se aplicado no banco, exige backup, revalidacao de totais e revisao/regeneracao de produtos que usam `nome_campanha`.
- decisao necessaria:
  - aprovar crosswalk apenas como camada analitica; ou
  - abrir fluxo formal de mudanca de dado mestre/revisao `data/R3` para renomeacao no banco.

### Preflight Registrado Em 2026-07-13

- comando:
  `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --preflight --campaign junho`
- resultado: `ready=true`.
- campanha: `47a-Jun-26`.
- pasta: existe.
- arquivos existentes na pasta de junho: 31.
- registros observados no consolidado para junho: 6.
- pontos esperados com esforco: 13.
- pontos com captura em junho: `PIC-05`, `PIC-06`, `PIC-07`, `PIC-09`, `PIC-12`.
- pontos com esforco e captura zero: `PIC-01`, `PIC-02`, `PIC-03`, `PIC-04`, `PIC-08`, `PIC-11`, `PIC-10`, `PIC-13`.
- abundancia total: 45 individuos.
- biomassa total: 5,8.

### Preflight Geral Do Recipe Em 2026-07-13

- comando:
  `python scripts/projects/avg/run_ictio_avg_2026_por_campanha.py --preflight`
- resultado: `ready=true` para `abril`, `maio` e `junho`.
- arquivos existentes antes de qualquer nova geracao:
  - `abril`: 28 arquivos;
  - `maio`: 27 arquivos;
  - `junho`: 31 arquivos.
- abundancia total por campanha no consolidado:
  - `45a-Abr-26`: 9 individuos;
  - `46a-Mai-26`: 23 individuos;
  - `47a-Jun-26`: 45 individuos.
- observacao: a contagem de arquivos existentes e informativa; uma nova geracao aprovada pelo Gate C limpa a pasta alvo e reconstroi os produtos.

### Geracao Do Estudo Longo GEOARC001 Em 2026-07-13

- fonte analitica criada:
  `scripts/projects/avg/build_ictio_avg_geoarc001_source.py`
- lastro da fonte:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/geoarc001_long_study_source_20260713`
- saida dos produtos:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/2026/estudo_longo_geoarc001_20260713`
- copia consolidada solicitada pelo usuario:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/Consolidado_2026/icitiofauna`
- manifesto do pacote:
  `manifesto_braavg002_estudo_longo_geoarc001_ictiofauna.json`
- escopo gerado:
  - beta/LCBD taxonomico: produtos 15 a 18;
  - ecologia funcional: produtos 19 a 23;
  - minigraficos funcionais: produto 24;
  - sintese espacial funcional: produtos 34 a 36.
- base analitica:
  - 47 campanhas;
  - 13 pontos;
  - 585 linhas ponto-campanha esperadas apos remover nao-amostragens;
  - 343 amostras com captura quantitativa;
  - 13 especies;
  - 13 especies com traits funcionais.
- regra temporal aplicada:
  - ano temporal agosto-julho;
  - anos nos produtos representam o ano de inicio do ciclo (`2022`, `2023`, `2024`, `2025`).
- regra espacial aplicada:
  - coordenadas: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Geo/Ponto amostral - AVG.kml`;
  - status: KML padrao usado provisoriamente por aprovacao do usuario, com overrides analiticos para `PIC-02` e `PIC-11`;
  - hidrografia: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Geo/Hidrografia.kmz`;
  - delimitacao: KML combinado das areas de controle 01/02 criado no lastro da fonte.
- validacao automatica:
  - 13 PNG abriram via PIL;
  - 12 XLSX abriram via openpyxl;
  - na pasta original: 5 JSON e 2 README/MD presentes;
  - na copia consolidada: 13 PNG, 12 XLSX, 5 JSON e 2 README/MD abriram/foram conferidos;
  - erros: 0.
- ajustes executados:
  - `Poecilia mexicana` saiu como `Poecilia cf. mexicana` na fonte e nos produtos;
  - scripts GEOARC001 passaram a aceitar `Ano_Temporal` opcional na fonte analitica;
  - rotulos espaciais `PIC-XX` foram preservados nos mapas;
  - legenda do mapa de balanco funcional movida para fora da area dos pontos.

### Geracao Das Analises Tradicionais Em 2026-07-13

- runner criado:
  `scripts/projects/avg/run_ictio_avg_tradicional_consolidado_2026.py`
- saida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/AVG/Produtos/Planilha Consolidada/Resultados e planilhas/Resultados ictio/Consolidado_2026/icitiofauna`
- manifesto:
  `manifesto_braavg002_tradicional_ictiofauna_2026.json`
- escopo:
  - base historica completa `C001` a `C047`;
  - primeira campanha: `1a-Ago-22` -> `C001-2022-08-SC`;
  - ultima campanha: `47a-Jun-26` -> `C047-2026-06-SC`;
  - planilhas tradicionais mantidas com as 47 campanhas;
  - graficos por ponto exportados em pranchas A4 paisagem com C001-C047, um ponto por linha e eixo C01-C47 apenas no painel inferior;
  - `04B` mantido como heatmaps por ano temporal agosto-julho.
- anos temporais demarcados nas figuras:
  - `2023`: `C001` a `C012`;
  - `2024`: `C013` a `C024`;
  - `2025`: `C025` a `C036`;
  - `2026`: `C037` a `C047`, ainda sem julho/2026.
- produtos tradicionais gerados:
  - composicao, distribuicao e sintese de ocorrencia;
  - riqueza e abundancia por ponto;
  - riqueza por ordem/familia;
  - CPUEn/CPUEb por ponto;
  - CPUEn/CPUEb por especie e por especie-ponto;
  - diversidade alfa;
  - similaridade Bray-Curtis;
  - suficiencia amostral;
  - DarwinCore IEF.
- base:
  - 519 registros observados;
  - 761 linhas analiticas esperadas com placeholders de captura zero para metricas por ponto;
  - 585 ponto-campanhas amostrados esperados nas tabelas 02, 03 e 06;
  - 26 combinacoes removidas por nao-amostragem/realocacao;
  - graficos nao regenerados ainda por orientacao do usuario em 2026-07-15;
  - 13 pontos;
  - 13 especies.
- ajustes aplicados:
  - campanha padronizada em camada analitica `Cnnn-AAAA-MM-CH/SC`;
  - graficos `02`, `03`, `06`, `07`, `10A` e `10B` substituidos por 30 pranchas A4 C001-C047;
  - grafico `04B` mantido em 4 heatmaps por ano temporal;
  - `Poecilia mexicana` apresentada como `Poecilia cf. mexicana`;
  - produtos `15+`, `24` e `34-36` previamente gerados foram preservados na mesma pasta.
- validacao da pasta consolidada apos tradicionais + GEOARC001:
  - 58 PNG abriram via PIL;
  - 29 XLSX abriram via openpyxl;
  - 6 JSON e 3 README/MD presentes;
  - 30 pranchas A4 C001-C047 geradas para `02`, `03`, `06`, `07`, `10A` e `10B`;
  - 4 heatmaps `04B` por ano temporal gerados;
  - validacao em memoria da regra revisada: `PIC-01` e `PIC-11` = 0 linhas apos `C039`; `PIC-02` = 0 linhas em `C040-C042` e 5 linhas em `C043-C047`; `PIC-03` = 0 linhas em `C040-C042`, 1 linha em `C043` e 0 linhas em `C044-C047`;
  - `01_tabela_composicao_ictiofauna.xlsx` contem `Poecilia cf. mexicana` e nao contem `Poecilia mexicana` como nome de relatorio;
  - `04_df_riqueza_por_ordem_ictiofauna.xlsx` e `04_df_riqueza_por_familia_ictiofauna.xlsx` nao contem `Nao informado`;
  - erros: 0.

### Boxplots Exploratorios De Riqueza

- decisao: usuario aprovou testar boxplots temporais e espaciais de riqueza em 2026-07-15.
- script:
  `scripts/projects/avg/build_ictio_avg_richness_boxplots_exploratory.py`.
- saida:
  `outputs/_project_scripts/BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg/richness_boxplots_exploratory_20260715`.
- base: 585 ponto-campanhas amostrados; nao-amostragem como ausencia, nao zero.
- produtos:
  - `EXP_BOX_01_riqueza_por_ano_temporal_ictiofauna.png`;
  - `EXP_BOX_02_riqueza_area_controle_por_ano_temporal_ictiofauna.png`;
  - `EXP_BOX_03_riqueza_por_ponto_ictiofauna.png`;
  - `EXP_BOX_df_riqueza_ponto_campanha_ictiofauna.xlsx`;
  - `EXP_BOX_resumo_riqueza_ictiofauna.xlsx`.
- validacao: 3 PNG abriram via PIL, 2 XLSX abriram via openpyxl, 0 erros.

## Pendencias

- Traits funcionais aprovados para uso analitico do projeto em 2026-07-13.
- Decidir futuramente se os traits aprovados tambem serao gravados em `public.especies`; se sim, reabrir Gate B antes do apply.
- Revisar e aprovar o pacote consolidado em `Consolidado_2026/icitiofauna`.
- Crosswalk analitico de campanhas `Cnnn-AAAA-MM-CH/SC` usado nos produtos; apply no banco continua nao aprovado.
- Renomeacao no banco esta bloqueada ate aprovacao explicita de mudanca de dado mestre, com backup e plano de revalidacao.
- Produtos espaciais GEOARC001 devem ser regenerados com a fonte atualizada antes do fechamento dos minigraficos/mapas.
- KML padrao foi usado provisoriamente com overrides analiticos; revisar `KML Atual` antes de fechamento espacial definitivo.
- Se `KML Atual` for oficial, reabrir Gate A e corrigir pontos antes de regenerar os produtos espaciais finais.
- Se a proxima campanha ainda nao estiver migrada/consolidada, reabrir fluxo desde validacao e nao usar este registro como atalho.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| R01 - abril/2026 | `analysis` | `R2` | `review_completed` | [BRAAVG002_ICTIOFAUNA_ABRIL_2026_REV_R01.md](../reviews/BRAAVG002_ICTIOFAUNA_ABRIL_2026_REV_R01.md) |

## Fechamento E Aprendizados

- validadores: usar `--preflight` antes da geracao; usar `audit_ictio_avg_long_study_readiness.py` antes dos blocos GEOARC001; validar abertura real de PNG/XLSX depois da geracao.
- manifesto: pacote `estudo_longo_geoarc001_20260713` registrado e validado.
- patterns: recipe criado para evitar campanha/pasta hardcoded sem registro.
- portfolio: dossie AVG Ictiofauna deve ser atualizado apos a proxima rodada aprovada.
- backlog: promover o runner para nome generico apos estabilizar pelo menos uma nova rodada com recipe.
