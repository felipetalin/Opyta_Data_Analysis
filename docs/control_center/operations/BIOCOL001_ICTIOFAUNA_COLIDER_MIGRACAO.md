# BIOCOL001 - Ictiofauna - Colider

## Controle

- projeto: `BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider`
- grupo: Ictiofauna
- operacao: Migracao, validacao e primeira versao analitica
- estado atual: `first_analytical_version_registered_pending_incremental_review`
- aberta em: 2026-08-11
- atualizada em: 2026-08-12
- proxima acao: revisar incrementalmente a V1 e fechar os gates espacial e hidrologico antes das analises exploratorias; 5.1, 5.14 e 5.18 permanecem em Aguardar

## Caminhos

- dados:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Planilha/Migracao/Opyta-Bios-Ictio-2026_MIGRACAO_DE DADOS -version 4.xlsx`
- cadastro de especies:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Planilha/Migracao/Cadastro_especies_opyta_colider-ictio-2600812.xlsx`
- runtime Opyta_Data:
  `G:/Meu Drive/Opyta/Opyta_Data/runtime/importacao/migrar_ictio/projeto_ictio_real.xlsx`
- dossie:
  `docs/projects/BIOCOL001_COLIDER_ICTIOFAUNA.md`
- recipe:
  `configs/projects/biocol001_colider_ictiofauna.json`
- lastro:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider`
- pasta unica de resultados para revisao:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02`
- pasta separada de analises exploratorias:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_ANALISES_EXPLORATORIAS_R01`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | concluida | Usuario definiu projeto novo `BIOCOL001`, grupo Ictiofauna e fonte Colider. |
| Validacao | concluida sem bloqueios | Planilha v3 aprovada pelo validador com 69 campanhas operacionais, 1551 pontos e 74589 linhas de resultados na fonte. |
| Gate A - dados | aprovado e corrigido no banco | Usuario aprovou a padronizacao de rotulos; BIOCOL001 ficou com 69 rotulos/campanhas no banco e na consolidada. |
| Cadastro de especies | concluido | Cadastro v2600812 processado com 327 especies; 38 novas e 289 existentes. |
| Auditoria de atributos | concluida | Cobertura dados x cadastro: 327/327; especies usadas sem buraco nos atributos obrigatorios do cadastro. Endemismo tratado como pendencia futura. |
| Gate B - especies | aprovado com ressalva | Usuario autorizou seguir mesmo com tema de endemismo para resolver depois. |
| Migracao | concluida e ajustada | Projeto `id_projeto=206`; apos padronizacao e correcao v4: 1245 pontos, 1869 esforcos e 13798 registros em `resultados_ictiofauna`, com 108355 individuos. |
| Consolidacao | concluida e reprocessada | 13798 registros de BIOCOL001 encontrados em `biota_analise_consolidada` por `id_projeto=206`/`codigo_interno_opyta`, com 69 campanhas e 108355 individuos. |
| Configuracao das analises | concluida para produtos maduros | Gate C aprovado para bateria inicial; 5.1, ictioplancton/ovos e larvas e T-TAG ficam em Aguardar. |
| Tabela detalhe reproducao/biometria | concluida | `resultados_ictiofauna_detalhe` carregada com 74579 linhas, 108355 individuos e diferenca zero contra a tabela agregada. |
| Gate C - analises | aprovado parcial | Bateria inicial aprovada pelo usuario; produtos maduros gerados em R01. |
| Geracao dos produtos | primeira versao analitica registrada | Pasta oficial plana com 14 workbooks tematicos, 5 bases, 4 auditorias e 21 figuras vigentes no manifesto. |
| Organizacao dos resultados | concluida | Pasta oficial plana e manifesto com fontes vigentes; planilha 5.5 antiga excluida apos fechamento do Excel. |
| Revisao tecnica | concluida para a V1 com notas | Nenhum erro de formula; totais tematicos reconciliados. Permanecem produtos aguardando bases e revisoes incrementais. |
| Revisao de layout | concluida para a V1 | Figuras a 300 dpi, sem titulo interno e com paleta/marcos aprovados. |
| Escalonamento tecnico | planejado | Plano exploratorio R01 separado, com nucleo multivariado enxuto e gates espacial/hidrologico. |
| Fechamento | pendente | A V1 esta registrada, mas o pacote final depende das bases aguardadas e das revisoes aprovadas item a item. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved_corrected` | Validacao final sem bloqueios; 69 campanhas operacionais; rotulos historicos padronizados no banco em 2026-08-12. |
| B - especies | `approved_with_note` | 327 especies cobertas no cadastro; atributos obrigatorios completos; endemismo fica como ajuste futuro. |
| C - analises | `approved_partial` | Template, paleta, universo e produtos maduros aprovados; 5.1, 5.14 e 5.18 aguardam bases especificas. |

## Validacao Dos Dados

- bloqueios: 0 na validacao final
- avisos/informativos:
  - antes da correcao, 86 rotulos de campanha equivaliam a 69 campanhas operacionais `C###`;
  - apos correcao no banco, BIOCOL001 possui 69 rotulos de campanha e 69 campanhas operacionais;
  - a contagem operacional correta e 69;
  - validacao passou com campanha+ponto em chaves cruzadas;
  - regra aprovada para padronizacao analitica: usar o maior `AAAA-MM` dentro
    de cada `C###`, exceto `C067`, que deve ser tratado como
    `C067-2026-02` por decisao do usuario.
- coordenadas:
  - fonte interna auditada: aba `Pontos_e_Campanhas` da planilha v4
  - 18 estacoes fisicas com 86 registros historicos por ponto
  - cada ponto possui um unico par de coordenadas em toda a serie; nulos/invalidos: 0
  - faixa: latitude -11,23510228 a -10,95489761; longitude -55,85100350 a -55,27281295
  - CRS/sistema oficial: ainda nao confirmado; o formato e compativel com coordenadas geograficas decimais, sem assumir datum
  - comparacao com KMZ/KML/shapefile/planilha oficial: pendente se houver produto espacial
  - estrategia aprovada no Gate A: usar coordenadas da planilha validada em diagnosticos internos; minimapas oficiais dependem de validacao do SRC e das camadas de rio, reservatorio e barragem
- ajustes aplicados:
  - `Codigo_Opyta` definido como `BIOCOL001`;
  - headers normalizados;
  - coordenadas convertidas para numerico;
  - campanhas corrigidas pelo usuario;
  - chaves campanha/ponto/esforco/resultados revalidadas;
  - campanhas padronizadas no banco por fusao de pontos, esforcos e resultados duplicados por `C###`.
- de/para analitico de campanhas:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/de_para_campanhas_biocol001_regra_aprovada.csv`

## Camada Operacional Dos Pontos

- camada registrada em:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/camada_operacional_pontos_biocol001.csv`
- entendimento aprovado:
  - planilha v3: 18 pontos de programacao;
  - universo padrao para analises gerais: 16 pontos de malha regular, excluindo `ICTIO13A - Marcação` e tratando `ICTIO13C`/`ICTIO13D` como camada condicional;
  - banco/consolidado: 19 rotulos de ponto quando `ICTIO13A - Marcação` e contado separadamente;
  - `ICTIO13A - Marcação` faz parte da programacao de marcacao; deve permanecer no banco, mas fica excluido por padrao das analises gerais;
  - `ICTIO13C` e `ICTIO13D` pertencem ao sistema de transposicao de peixes; ficam como pontos condicionais, podendo entrar ou sair conforme o objetivo da analise;
  - todo produto analitico deve declarar o universo de pontos usado: malha regular, malha regular sem transposicao, transposicao, marcacao, ou conjunto completo.

## Camada Temporal Do Reservatorio

- camada registrada em:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/camada_temporal_reservatorio_biocol001.csv`
- premissas aprovadas:
  - pre-enchimento: ate a campanha `C020`;
  - pos-enchimento: de `C021` em diante;
  - rebaixamento parcial do reservatorio: periodo `2025-08` a `2026-02`, sem rebaixamento total;
  - reenchimento: marco em `2026-03`;
  - figuras temporais devem usar esses marcos como apoio visual discreto, sem titulo interno na figura.

## Cadastro E Auditoria De Especies

- especies nos resultados: 327
- especies no cadastro complementar: 327
- especies ausentes no cadastro: 0
- especies extras no cadastro: 0
- especies novas processadas: 38
- especies existentes atualizadas/conferidas: 289
- atributos obrigatorios: completos para as especies usadas nos resultados
- campos incertos:
  - endemismo: coluna/tema existente, mas resolucao adiada por decisao do usuario
  - `cinegetica` e `xerimbabo`: tratados como colunas opcionais tri-state quando `N.A.` nao cabe no tipo booleano do banco
- auditoria taxonomica FishBase/rOpenSci v25.04 concluida em 2026-08-12:
  - fonte usada: snapshot FishBase `species`, `genera`, `families` e `synonyms`;
  - 9 nomes cientificos atualizados para nomes aceitos FishBase;
  - familias corrigidas por regra aprovada do usuario e por divergencias FishBase;
  - auditoria pre-correcao:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/auditoria_taxonomica_fishbase_biocol001.xlsx`;
  - auditoria pos-correcao:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/auditoria_taxonomica_fishbase_biocol001_pos_correcao.xlsx`;
  - validacao pos-correcao: 322 taxa na Tabela 05 operacional, 173 matches binomiais exatos, 147 matches por genero, 2 sem match direto e 0 divergencias de familia contra FishBase nos registros pareados.
  - banco atualizado em `public.especies` com backup
    `public.bkp_biocol001_taxon_fishbase_20260812_especies`:
    76 correcoes de familia e 8 atualizacoes de nome cientifico sem conflito;
  - merge controlado concluido em 2026-08-12:
    `Squaliforma emarginata` (`id_especie=6131`) foi fundido em
    `Aphanotorulus emarginatus` (`id_especie=5782`) para BIOCOL001;
  - backups do merge:
    `public.bkp_biocol001_squaliforma_merge_20260812_resictio`,
    `public.bkp_biocol001_squaliforma_merge_20260812_detail` e
    `public.bkp_biocol001_squaliforma_merge_20260812_consol`;
  - linhas atualizadas no merge:
    48 em `resultados_ictiofauna_detalhe`, 34 em
    `resultados_ictiofauna` e 34 em `biota_analise_consolidada`;
  - validacao pos-merge: residuo zero para `Squaliforma emarginata` em
    BIOCOL001; `Aphanotorulus emarginatus` totaliza 85 individuos no banco
    completo e 69 individuos na Tabela 05 do universo operacional geral.

## Migracao E Consolidacao

- IDs:
  - projeto: `id_projeto=206`
  - codigo: `BIOCOL001`
- totais da fonte:
  - campanhas operacionais: 69
  - rotulos de campanha originais: 86
  - pontos/campanha-ponto: 1551
  - linhas de resultados na planilha: 74589
  - especies: 327
- totais no banco:
  - pontos: 1245
  - campanhas: 69
  - esforcos Ictiofauna: 1869
  - registros em `resultados_ictiofauna`: 13798
  - individuos: 108355
  - especies distintas: 327
- tabela detalhe `resultados_ictiofauna_detalhe`:
  - linhas: 74579
  - individuos: 108355
  - registros agregados vinculados: 13798/13798
  - diferenca de abundancia contra `resultados_ictiofauna`: 0
  - linhas com `CP_cm`: 71201
  - linhas com `PC_g`: 74570
  - linhas com sexo `F/M`: 13510
  - linhas com EMG: 13439
  - linhas com evidencia reprodutiva forte: 2755
  - individuos com evidencia reprodutiva forte: 3070
- divergencias:
  - nenhuma divergencia bloqueante apos normalizacao de nomes cientificos
  - observacao tecnica: `biota_analise_consolidada.codigo_opyta` esta `NULL` para BIOCOL001; o codigo esta em `codigo_interno_opyta`
- backup:
  - `public.bkp_biocol001_cfix_20260812113032_pontos`
  - `public.bkp_biocol001_cfix_20260812113032_esforcos`
  - `public.bkp_biocol001_cfix_20260812113032_resictio`
  - `public.bkp_biocol001_cfix_20260812113032_consol`
  - `public.bkp_biocol001_v4fix_20260812133027_resictio`
  - `public.bkp_biocol001_v4fix_20260812133027_consol`
  - `public.bkp_biocol001_detail_20260812134703`
- totais consolidados:
  - registros: 13798
  - individuos: 108355
  - campanhas operacionais: 69
  - rotulos de campanha: 69
  - pontos com resultado: 19
  - especies: 327
  - grupo: Ictiofauna

## Configuracao Das Analises

- numero de campanhas: 69 operacionais
- planilha de aprovacao/planejamento:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/Planilha_aprovacao_analises/planejamento_analises_biocol001_CORRIGIDO_R01.xlsx`
- planilha objetiva por temas:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/Planilha_aprovacao_analises/planejamento_analises_biocol001_TEMAS_R02.xlsx`
- diagnostico tecnico Gate C:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/Planilha_aprovacao_analises/diagnostico_gate_c_biocol001_TEMAS_R03.xlsx`
- chave de automacao dos produtos: `ID_produto`, sequencial de `00` a `39`
- chave simplificada por temas: `ID`, sequencial de `00` a `19`
- universo padrao de pontos para analises gerais: 16 pontos de malha regular; excluir `ICTIO13A - Marcacao` por padrao; `ICTIO13C` e `ICTIO13D` devem ser tratados como camada condicional do sistema de transposicao quando a analise exigir esse recorte
- itens `5.13`, `5.16` e `5.17`: inexistentes no relatorio, confirmados pelo usuario
- bases/produtos de ictioplancton e marcacao T-TAG: manter como `Aguardar`, pois as bases serao fornecidas posteriormente
- STP: resultados correspondem aos pontos `PT-13C` e `PT-13D`/camada operacional `ICTIO13C` e `ICTIO13D`; tratar como recorte proprio do Sistema de Transposicao de Peixes
- recrutamento: aplicar somente para especies migradoras de longa distancia (`MLD`); criterio preliminar por especie baseado em `CP_cm` e maturacao gonadal; referencia = menor `CP_cm` observado em femeas `F2/F3/F4`; jovens = individuos da mesma especie com `CP_cm` inferior a esse limite, com bandeira de cautela para amostra pequena ou limite influenciado por registro isolado; o estadio 2 e exclusivo desta referencia de recrutamento
- diagnostico R03:
  - geraveis diretamente ou com regra simples: `5.2`, `5.2.1`, `5.3`, `5.5`, `5.6`, `5.8`, `5.9`, `5.10`;
  - geraveis com fonte original/correcao de migracao: `5.4` e `5.12`, pois `CP_cm`, `Sexo` e `EMG` estao fortes na planilha-fonte, mas nao chegaram completos ao banco/consolidado;
  - decisao tecnica para `5.12`: tema reprodutivo deve ficar no banco definitivo em tabela detalhe propria, pois `resultados_ictiofauna` e agregada por `id_esforco + id_especie` e ha grupos com multiplos sexos/EMG;
  - decisao do usuario: adotar para BIOCOL001 a estrategia analitica usada em BIOPOR001/Porto Estrela para reproducao, com base derivada da planilha validada e campos `Sexo_Padronizado`, `EMG_Codigo`, `EMG_Estadio`, `EMG_Ordem` e `Evidencia_Reprodutiva_Forte`;
  - base reprodutiva R01 gerada:
    `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/Planilha_aprovacao_analises/base_reproducao_biocol001_estrategia_porto_estrela_R01.xlsx`;
  - base reprodutiva/biometrica R02 gerada:
    `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/Planilha_aprovacao_analises/base_reproducao_biocol001_estrategia_porto_estrela_R02.xlsx`;
  - auditoria da correcao R02:
    `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/Planilha_aprovacao_analises/auditoria_correcao_biometria_abundancia_biocol001_R02.xlsx`;
  - script gerador:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/ictiofauna/gerar_base_reproducao_biocol001.py`;
  - validacao da base reprodutiva R01: 74.579 linhas com taxon, 327 especies, 69 campanhas canonicas, 19 pontos totais, 16 pontos no universo geral, 13.510 linhas com sexo F/M, 13.439 linhas com EMG, 2.755 linhas com evidencia reprodutiva forte; 60 linhas possuem `Numero_de_Individuos` decimal e devem ser revisadas antes dos produtos finais de abundancia;
  - validacao da base R02: rodada intermediaria superada pela v4 oficial; mantida apenas como historico da auditoria de correcao;
  - validacao vigente R03/v4: 74.579 linhas com taxon, 108.355 individuos, 327 especies, 69 campanhas canonicas, 19 pontos totais, 16 pontos no universo geral, 13.510 linhas com sexo F/M, 13.439 linhas com EMG, 2.755 linhas com evidencia reprodutiva forte; sem `Numero_de_Individuos` decimal remanescente;
  - decisao operacional atualizada: usar a planilha v4 e a tabela `resultados_ictiofauna_detalhe` para `5.4` e `5.12`; banco migrado/consolidado ja foi corrigido para a v4 e a tabela detalhe preserva sexo/EMG/biometria linha-a-linha;
  - carga detalhe no banco:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/ictiofauna/carregar_resultados_ictiofauna_detalhe_biocol001.py`;
  - staging da carga detalhe:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/staging_resultados_ictiofauna_detalhe_biocol001_20260812134703.csv`;
  - auditoria da carga detalhe:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/auditoria_resultados_ictiofauna_detalhe_biocol001_20260812134703.csv`;
  - auditoria DB detalhe x agregado:
    `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/auditoria_db_resultados_ictiofauna_detalhe_biocol001_20260812134703.csv`;
  - proposta documentada em `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/sql/README_REPRODUCAO_BIOMETRIA.md`;
  - rascunho SQL em `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/sql/proposta_resultados_ictiofauna_detalhe.sql`;
  - CPUE `5.7`: concluida para C001-C069, abrangendo a base atual ate junho/2026;
    - somente `Rede de Emalhar` quantitativa, 16 pontos regulares, excluidos marcacao e STP;
    - CPUEn = N / esforco x 100 (ind./100 m2); CPUEb = biomassa em kg / esforco x 100 (kg/100 m2);
    - medias e IC 95% calculados por unidade campanha x ponto, incluindo esforcos com captura zero;
    - 995 unidades de esforco, 69 campanhas, 53.479 individuos e 9.832,7526 kg; 4 unidades com captura zero;
    - figuras temporais em linha, com barras de erro do IC 95%, legenda horizontal e limites inferiores truncados em zero;
    - lastro visual obrigatorio: `05_06_riqueza_temporal_campanha.png` e a funcao `_shade_reservoir_events` de `gerar_bateria_produtos_maduros_biocol001.py`;
    - semantica visual aprovada: CPUEn/serie principal `#002060`; CPUEb/serie secundaria `#5B9BD5`; pre-enchimento `#F0F0F0`; rebaixamento parcial `#DBE5F1`; reenchimento `#D4672A` tracejado;
    - template aprovado: 18 x 10,2 pol, 300 dpi, Arial, fonte-base 17, moldura completa, grade suave, legenda superior horizontal e sem titulo interno;
    - ressalva auditada: 13 individuos sem `PC_g` nao contribuem para CPUEb;
    - Excel tematico: `05_07_captura_unidade_esforco.xlsx`, com premissas, auditoria, esforco, base e tabelas analiticas correspondentes;
    - figuras sem titulo interno: `05_07_1_cpuen_trecho.png` a `05_07_6_top20_cpueb_especies.png`;
    - script reprodutivel: `ictiofauna/gerar_5_7_cpue_biocol001.py`;
  - diversidade/equitabilidade geral por ponto `5.8`: concluida para os 16 pontos gerais, integrando C001-C069 sem separar campanhas;
    - matriz comunitaria: CPUEn media por especie e ponto, com ausencias incorporadas como zero;
    - 995 unidades de esforco quantitativo e 161 especies registradas em rede de emalhar;
    - Shannon H' e Pielou J' calculados sobre a mesma matriz; resultado incorporado ao workbook tematico `05_08_dados_diversidade_equitabilidade.xlsx`;
    - figura sem titulo interno: `05_08_diversidade_equitabilidade_pontos.png`;
  - similaridade geral por ponto `5.9`: concluida sobre a mesma matriz CPUEn de `5.8`;
    - Bray-Curtis para 120 pares entre os 16 pontos; dendrograma com agrupamento medio UPGMA;
    - matrizes de similaridade/distancia e tabela de pares incorporadas ao workbook tematico `05_09_dados_similaridade_bray_curtis.xlsx`;
    - figura sem titulo interno: `05_09_similaridade_bray_curtis_pontos.png`;
    - script reprodutivel conjunto: `ictiofauna/gerar_5_8_5_9_pontos_biocol001.py`;
  - processo reprodutivo `5.12`: concluido para machos e femeas no universo geral de 16 pontos;
    - tabela geral por especie: nome cientifico, nome popular, F1-F4, M1-M4 e totais por sexo;
    - categorias: 1 repouso, 2 maturacao inicial, 3 maturacao avancada/maduro, 4 desovado/esgotado;
    - 92 especies, 13.583 individuos com EMG valido e 49 campanhas com informacao reprodutiva; 60 individuos F/M sem EMG excluidos das categorias, sem imputacao;
    - tabelas espacial e temporal em abundancia absoluta e relativa; percentuais calculados separadamente dentro de femeas e machos;
    - workbook tematico: `05_12_processo_reprodutivo.xlsx`;
    - figuras sem titulo interno: `05_12_1_reproducao_espacial.png` e `05_12_2_reproducao_temporal.png`;
  - recrutamento `5.15`: produto atual concluido somente para juvenis MLD, conforme solicitacao mais recente;
    - criterio mantido: `CP_cm < menor CP_cm de femeas F2/F3/F4` da especie; especies sem referencia F2+ nao classificadas;
    - 487 registros juvenis, somando 528 individuos de 8 especies, em 50 campanhas e nos 16 pontos gerais; auditoria cobre 15 especies MLD;
    - base canonica exclusivamente MLD: `base_recrutamento_mld_biocol001.xlsx`, com 7.307 registros de biometria de 15 especies;
    - tabelas geral, espacial, temporal e registros consolidadas no workbook canonico `05_15_recrutamento_mld_auditoria.xlsx`, exclusivamente MLD;
    - figuras com a soma das especies juvenis MLD: `05_15_1_recrutamento_mld_espacial.png` por ponto, `05_15_2_recrutamento_mld_temporal.png` por campanha e `05_15_3_mapa_recrutamento_mld_espacial.png`;
    - script reprodutivel conjunto: `ictiofauna/gerar_5_12_reproducao_5_15_recrutamento_biocol001.py`;
  - estrutura trofica `5.11`: viavel parcial; `habito_alimentar` existe, `guilda_alimentar` esta vazia;
  - recrutamento `5.15`: base e produtos canonicos usam somente MLD, com criterio `CP_cm < menor CP F2+ por especie`; arquivos mistos MCD/MLD foram retirados do pacote oficial para manter uma unica fonte operacional e arquivados em `inventory/historico_recrutamento_preliminar` apenas como lastro da triagem;
  - ictioplancton `5.14`, `5.14.1`, `5.14.2`, `5.14.3`: status `Aguardar` ate recebimento da base de ovos e larvas;
  - marcacao T-TAG `5.18`: status `Aguardar` ate recebimento da base especifica;
  - STP `5.19`: concluido como recorte proprio do Sistema de Transposicao de Peixes;
    - universo exclusivo: `ICTIO13C` e `ICTIO13D`, equivalentes a `PT-13C` e `PT-13D`; camada `sistema_transposicao_condicional`;
    - todos os metodos quantitativos e qualitativos registrados no STP; nao misturar ao universo geral;
    - 2.804 linhas, 7.989 individuos, 1.646.518,2 g, 87 especies e 37 campanhas com registros STP;
    - classificacao geral sem lacunas ou divergencias em nome popular, ordem, familia, origem, classe migratoria, estrategia reprodutiva e categorias de ameaca;
    - tabelas espaciais por especie e nome popular para abundancia, biomassa e ocorrencia em `ICTIO13C/ICTIO13D`;
    - tabelas temporais por especie e nome popular para abundancia, biomassa e ocorrencia somente nas 37 campanhas com registros STP; campanhas nao amostradas nao recebem zero;
    - workbook tematico unico: `05_19_sistema_transposicao_peixes.xlsx`;
    - script reprodutivel: `ictiofauna/gerar_5_19_stp_biocol001.py`;
  - pendente de base externa/regra: `5.1`.
- template: aprovado, conforme lastro visual BIOCOL001/BIOPOR001 registrado abaixo
- paleta: aprovada, com semantica fixa por serie e evento do reservatorio
- pasta de saida: aprovada, pacote plano `BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02`
- produtos: R01 gerado para a bateria madura

## Primeira Versao Analitica V1

- pasta:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02`
- script:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/ictiofauna/gerar_bateria_produtos_maduros_biocol001.py`
- manifesto:
  `BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02/manifesto_bateria_produtos_maduros_biocol001_R02.json`
- validacao:
  `BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02/validacao_pacote_produtos_maduros_biocol001_R02.json`
- bases finais geradas: 5 arquivos `.xlsx`
- produtos oficiais/tabelas gerados: 14 arquivos `.xlsx`
- auditorias preservadas: 4 arquivos `.xlsx`
- fonte unica definida por tema: arquivos `.xlsx` separados; workbook consolidado multitematico descontinuado e removido
- figuras vigentes no manifesto: 21 arquivos `.png`
- premissa grafica: template BIOPOR001/Porto Estrela, paleta azul primaria `#002060`, secundaria `#5B9BD5`, figuras 18 x 10,2 pol ou equivalentes a 300 dpi, sem titulo interno na figura; figuras temporais devem trazer legenda explicativa dos marcos do reservatorio
- curva do coletor: riqueza observada media + Jackknife 1, ambos com faixa `±1 DP`, unidade campanha x ponto, 300 permutacoes
- totais da base completa: 74579 linhas, 108355 individuos, 327 especies, 69 campanhas, 19 pontos
- totais do universo geral: 71519 linhas, 100110 individuos, 322 especies, 69 campanhas, 16 pontos
- produtos contemplados diretamente:
  - `5.2` composicao da ictiofauna
  - `5.2.1` classificacao taxonomica
  - `5.3` especies ameacadas
  - `5.4` estrutura das populacoes
  - `5.5` distribuicao espacial
  - `5.6` distribuicao temporal
  - `5.8` diversidade/equitabilidade
  - `5.9` similaridade
  - `5.10` curva acumulativa de especies
  - `5.12` processo reprodutivo
  - `5.15` recrutamento de juvenis MLD
  - `5.19` Sistema de Transposicao de Peixes

- auditoria V1 em 2026-08-12:
  - nenhum erro de formula encontrado nos workbooks tematicos;
  - grades desativadas e estrutura tabular preservada;
  - figuras verificadas a 300 dpi, sem titulo interno e com semantica visual aprovada;
  - workbooks antigos possuem diferencas menores de congelamento de paineis e filtros; registrar para padronizacao futura sem reformatar produtos ja aprovados;
  - fonte unica de `5.5`: `05_05_distribuicao_espacial_riqueza_abundancia.xlsx`, que possui `nome_popular`;
  - `05_05_tabela_distribuicao_espacial.xlsx`, versao anterior sem `nome_popular`, foi excluida apos o fechamento do Excel;
  - `5.8` possui duas leituras complementares: temporal por campanha e geral por pontos, no mesmo Excel tematico;
  - `5.9` possui duas leituras complementares: dendrograma temporal por campanhas e dendrograma geral por pontos, no mesmo Excel tematico;
  - figuras temporais vigentes: `05_08_diversidade_equitabilidade.png` e `05_09_similaridade_bray_curtis_campanhas.png`;
  - script reprodutivel das quatro leituras: `ictiofauna/gerar_5_8_5_9_pontos_biocol001.py`.

## Revisao 5.3 - Especies Ameacadas (2026-08-12)

- `5.2` e `5.2.1` aprovados pelo responsavel tecnico;
- causa do 5.3 vazio corrigida: o filtro antigo nao reconhecia as siglas oficiais `VU`, `EN` e `CR`;
- fonte nacional vigente: Portaria GM/MMA no 1.667/2026, que revogou a Portaria MMA no 445/2014 para peixes e invertebrados aquaticos;
- fonte global: FishBase v25.04, campo IUCN por especie (`IUCN 2025-2` nas fichas consultadas);
- Mato Grosso nao possui lista estadual oficial vigente de fauna ameacada; o campo estadual recebe `Sem lista estadual oficial vigente (MT)`, sem vazio ou `N.A.`;
- categorias nao ameacadas permanecem informativas: `LC`, `NT`, `DD` e `NE`; somente `VU`, `EN`, `CR`, `EW`, `EX` e `RE` alimentam o produto 5.3;
- resultado do universo geral: quatro especies no 5.3:
  - `Colossoma macropomum`: nacional `VU`, global `NT`;
  - `Knodus dorsomaculatus`: nacional `EN`, global `EN`;
  - `Harttia dissidens`: nacional `Nao listada`, global `VU`;
  - `Scobinancistrus pariolispos`: nacional `Nao listada`, global `VU`;
- produto final: `BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02/05_03_tabela_especies_ameacadas.xlsx`;
- auditoria final: `BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02/auditoria_status_ameaca_biocol001.xlsx`;
- cadastro oficial, bases analiticas, workbook consolidado e tabela `public.especies` atualizados sem lacunas nos tres niveis;
- backup do banco: `public.bkp_biocol001_ameaca_20260812_especies`;
- backup do cadastro: `inventory/bkp_cadastro_especies_biocol001_pre_ameaca_20260812.xlsx`;
- regra permanente implementada em `ictiofauna/gerar_bateria_produtos_maduros_biocol001.py`.
- complemento espacial e temporal aprovado como parte do produto 5.3 e incorporado ao mesmo Excel:
  - aba `Variacao_espacial`: 16 pontos operacionais, abundancia e biomassa por especie, riqueza e totais;
  - aba `Variacao_temporal`: 69 campanhas canonicas, abundancia e biomassa por especie, riqueza, totais e marcos do reservatorio;
  - totais reconciliados entre as duas dimensoes e a tabela principal: 45 individuos e 31.944,6199 g;
- script reprodutivel: `ictiofauna/complementar_5_3_variacao_biocol001.py`.
- premissa de economia operacional: cada item do relatorio possui um unico Excel tematico, que pode conter abas auxiliares do proprio tema; nao manter nem regenerar `BIOCOL001_tabelas_produtos_maduros_R02.xlsx`.
- distribuicoes gerais exportadas como fontes tematicas unicas:
  - `05_05_distribuicao_espacial_riqueza_abundancia.xlsx`: resumo dos 16 pontos e matrizes especie x ponto de abundancia, biomassa e ocorrencia;
  - `05_06_riqueza_temporal_campanha.xlsx`: resumo das 69 campanhas e matrizes especie x campanha de abundancia, biomassa e ocorrencia, incluindo os marcos do reservatorio;
  - matrizes por especie devem apresentar `nome_cientifico` e `nome_popular` como primeiras colunas; cobertura atual de nome popular: 322/322;
  - quando tabela e figura forem produtos pareados, usar o mesmo nome-base e diferenciar somente pela extensao (`.xlsx`/`.png`);
  - universo reconciliado: 322 especies, 100.110 individuos e 10.399.857,7047 g;
  - `05_06_dados_riqueza_temporal.xlsx` removido por duplicar o resumo incorporado no produto 5.6;
  - script reprodutivel: `ictiofauna/gerar_5_5_5_6_distribuicoes_biocol001.py`.
  - figura `05_05_distribuicao_espacial_riqueza_abundancia.png` revisada em 2026-08-17 com legenda horizontal para `Riqueza acumulada (nº de especies)` e `Abundancia acumulada (nº de individuos)`;
  - os dois geradores do produto 5.5 foram corrigidos para preservar a legenda em atualizacoes futuras.
- composicao por estrategia reprodutiva incorporada ao tema 5.2:
  - universo: 322 especies do universo geral;
  - nao migradoras: 287 (89,1%);
  - migradoras de curta distancia: 20 (6,2%);
  - migradoras de longa distancia: 15 (4,7%);
  - figura sem titulo interno: `05_02_2_figura_estrategias_reprodutivas.png`;
  - dados incorporados na aba `Estrategias_reprodutivas` de `05_02_tabela_caracteristicas_biologicas.xlsx`;
  - porte derivado do comprimento maximo adulto: pequeno ate 15 cm, medio >15-30 cm, grande >30-60 cm e muito grande >60 cm;
  - fonte automatica: FishBase v25.04; para nomes abertos (`cf.`, `aff.`, `gr.` e `sp.`), usar a mediana do comprimento maximo das especies do mesmo genero;
  - excecao manual aprovada: `Pamphorichthys cf. scalpridens` classificada como pequeno porte;
  - resultado: 190 pequenas (59,0%), 73 medias (22,7%), 39 grandes (12,1%) e 20 muito grandes (6,2%); cobertura 322/322;
  - auditoria nas abas `Porte_especies`, `Criterio_porte` e `Resumo_porte` de `05_02_tabela_caracteristicas_biologicas.xlsx`;
  - figura sem titulo interno: `05_02_3_figura_porte_especies.png`;
  - script reprodutivel: `ictiofauna/gerar_5_2_estrategia_reprodutiva_biocol001.py`.
- revisao pontual das Figuras 11A/11B concluida em 2026-08-17:
  - fonte unica: abas `Ordem` e `Familia` de `05_02_1_dados_ordem_familia.xlsx`, reconciliadas linha a linha com a `Tabela_05`;
  - total taxonomico: 322 especies nas duas figuras;
  - ordem: 9 categorias, com `Siluriformes = 71`;
  - familia: 38 categorias, incluindo `Acestrorhamphidae = 71`, `Characidae = 18` e `Stevardiidae = 12`;
  - total `322 especies` inserido no centro das duas roscas;
  - arquivos oficiais sobrescritos sem versao paralela: `05_02_1_figura_11a_percentual_ordem.png` e `05_02_1_figura_11b_percentual_familia.png`;
  - gerador corrigido: `ictiofauna/gerar_bateria_produtos_maduros_biocol001.py`.
- comparacao da lista de especies com Ohara et al. (2017), incorporada ao tema 5.2 em 2026-08-17:
  - livro `Peixes do rio Teles Pires`: 342 especies, 191 generos, 42 familias e 11 ordens;
  - monitoramento UHE Colider: 322 especies apos 69 campanhas;
  - reconciliacao aritmetica usada na figura: 232 compartilhadas, 110 somente no livro e 90 somente na UHE Colider;
  - proporcao compartilhada: 232/322 = 72,05%, apresentada como aproximadamente 72%;
  - o valor narrativo `234 compartilhadas` e incompativel com `322 no total` e `90 somente na UHE Colider`, devendo ser substituido por `232` caso 90 seja confirmado;
  - a sobreposicao ainda e uma premissa quantitativa fornecida pelo responsavel tecnico, sem validacao nominal especie a especie contra a lista integral do livro;
  - `somente` significa exclusivo entre as duas listas comparadas, sem inferencia de endemismo ou novo registro de distribuicao;
  - figura oficial sem titulo interno: `05_02_4_figura_51_comparacao_ohara_colider.png`;
  - gerador reprodutivel: `ictiofauna/gerar_5_2_4_comparacao_ohara_colider.py`.
- status da identificacao taxonomica incorporado ao tema 5.2 em 2026-08-17:
  - universo: 322 especies;
  - identificacao definitiva em nivel especifico: 176 (54,7%);
  - identificacao especifica duvidosa, com `cf.`, `aff.` ou `gr.`: 74 (23,0%);
  - identificacao em nivel de genero ou morfotipo: 71 (22,0%);
  - potencialmente nova para a ciencia: 1 (0,3%);
  - os 10 juvenis com identificacao impossibilitada e os 13 taxons que demandam investigacao adicional sao subconjuntos complementares e nao constituem fatias adicionais da rosca;
  - figura oficial sem titulo interno: `05_02_5_figura_52_status_identificacao_taxonomica.png`;
  - gerador reprodutivel: `ictiofauna/gerar_5_2_5_status_identificacao_taxonomica.py`.

## Escalonamento Tecnico Exploratorio

- objetivo: compreender mudancas na comunidade, seu momento, especies/grupos
  condutores e sinais de resposta temporaria, persistente, recuperacao ou
  reorganizacao, sem produzir uma bateria estatistica sem pergunta ecologica;
- plano canonico:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_ANALISES_EXPLORATORIAS_R01/PLANO_ANALISES_EXPLORATORIAS_BIOCOL001_R01.md`;
- nucleo proposto:
  - NMDS Bray-Curtis sobre `CPUEn` transformada por campanha x ponto;
  - distancia temporal ao centroide do pre-enchimento;
  - dbRDA/particao de variacao entre fase e hidrologia, apos entrada das covariaveis;
  - especies e grupos ecologicos condutores, com filtros de robustez;
  - sinteses direcionadas de reproducao e recrutamento MLD;
  - ate quatro minimapas, somente apos Gate Espacial;
- figura espacial oficial aprovada:
  - lastro correto: `Porto Estrela/Planilha/Resultados/resultados_ictiofauna_porto_estrela_producao_20260603`;
  - arquivo: `BIOCOL001_ANALISES_EXPLORATORIAS_R01/TESTE_05_05_mapa_longitudinal_padrao_BIOPOR001.png`;
  - produto-base: `5.5 Distribuicao espacial`;
  - produto separado em duas figuras oficiais: riqueza e abundancia, cada uma
    com mapa unico, simbolos proporcionais e proporcao geografica preservada;
  - arquivos: `05_05_mapa_riqueza_espacial.png` e
    `05_05_mapa_abundancia_espacial.png`;
  - sem titulo interno, conforme o padrao grafico do relatorio;
  - legenda azul apresentada como `Reservatorio/montante`, mantendo `Montante`
    apenas como codigo interno da camada operacional;
  - legendas inferiores exibem apenas a variavel e a unidade; os tres simbolos
    trazem valores aproximados de referencia, sem os termos minimo, mediana e
    maximo e sem faixas, pois a escala das bolhas e continua;
  - valores zero nao geram bolha; legendas de temas com zeros usam apenas
    referencias positivas distintas;
  - rotulo `ICTIO13B` na diagonal superior esquerda do simbolo;
  - nao estirar os eixos para ocupar toda a largura, pois isso deforma a malha
    hidrica e descaracteriza o padrao cartografico tradicional;
  - dimensao do template cartografico oficial: 18 x 10,2 pol, 300 dpi;
  - preenchimento oficial das bolhas: azul-claro `#8CC4E8`;
  - escalas relativas independentes com legendas de minimo, mediana e maximo;
  - rotulo `ICTIO11` deslocado para baixo do simbolo; legendas de tamanho fora
    da area grafica, em faixa horizontal abaixo de cada painel;
  - borda azul = Montante; borda laranja = Jusante;
  - linhas artificiais entre pontos removidas apos avaliacao do mapa original,
    que confirma reservatorio e rede hidrografica ramificados;
  - KMZ de apoio incorporado em 2026-08-13:
    `Clientes/Clientes/Clientes/Bios/Colider/Geo/UHE_Colider_reservatorio_malha_hidrica.kmz`;
  - conteudo auditado: 1 poligono de reservatorio de nivel cheio, 184 trechos de
    hidrografia e 1 ponto de barragem em `-55,7661111; -10,9847222`;
  - encaixe espacial validado para os 16 pontos regulares;
  - enquadramento derivado: 4 Montante (`ICTIO01`-`ICTIO04`), 9 Reservatorio
    (`ICTIO05`-`ICTIO12` e `ICTIO13B`) e 3 Jusante (`ICTIO13A`, `ICTIO14`,
    `ICTIO15`), registrado em
    `inventory/enquadramento_cartografico_pontos_biocol001.csv`;
  - o enquadramento cartografico complementa, sem sobrescrever, a camada
    operacional Montante/Jusante usada nos produtos ja aprovados;
  - Gate Espacial fechado para cartografia analitica, com ressalva de uso como
    apoio e sem finalidade juridica/operacional;
  - bateria cartografica oficial gerada para riqueza, abundancia, biomassa,
    riqueza e abundancia de ameacadas, CPUEn, CPUEb, Shannon, Pielou, femeas e
    machos em atividade reprodutiva e recrutamento MLD;
  - similaridade mantida fora da bateria de bolhas porque representa relacoes
    entre pares de pontos;
  - Montante: `ICTIO01` a `ICTIO12` e `ICTIO13B`;
  - Jusante: `ICTIO13A`, `ICTIO14` e `ICTIO15`;
  - camada registrada em `inventory/camada_trechos_longitudinais_biocol001.csv`;
  - script: `ictiofauna/gerar_teste_5_5_mapa_longitudinal_biocol001.py`;
- referencia cartografica apresentada em 2026-08-12:
  - mapa original UHE Colider, marco de 2018, escala 1:150.000;
  - projecao UTM, datum SIRGAS 2000, fuso 21;
  - fontes declaradas no mapa: ANA, IBGE 2017 e imagem Landsat 8;
  - arquivo cartografico original/camadas vetoriais ainda nao registrados;
- restricoes:
  - nao ha desenho BACI; evitar atribuicao causal forte ao empreendimento;
  - PERMANOVA sera verificacao secundaria, com dispersao e permutacoes restritas;
  - nao duplicar analises para `CPUEn`, `CPUEb` e presenca/ausencia sem ganho interpretativo;
  - resultados exploratorios nao entram no relatorio antes de aprovacao tecnica.
- nova rodada exploratoria solicitada em 2026-08-13:
  - diversidade beta temporal geral, sem separacao por trecho, entre campanhas
    consecutivas, com `beta-sor`, turnover (`beta-sim`) e nestedness (`beta-nes`),
    seguindo o lastro BIOPOR001;
  - PCoA Bray-Curtis por quatro periodos operacionais, com CPUEn por especie,
    transformacao raiz quadrada, grupos UPGMA no corte `0,55` e vetores de
    especies filtrados por ocorrencia em pelo menos tres pontos, seguindo o
    lastro visual e metodologico AVG;
  - saidas mantidas em `BIOCOL001_ANALISES_EXPLORATORIAS_R01`, acompanhadas de
    Excel de auditoria e sem promocao automatica ao relatorio oficial;
  - script: `ictiofauna/gerar_beta_pcoa_exploratorias_biocol001.py`.
  - produtos gerados e verificados em 2026-08-13:
    - `EXP_01_diversidade_beta_temporal_componentes_geral.png/.xlsx`:
      69 campanhas, 68 comparacoes consecutivas, 16 pontos, 322 especies na
      matriz de incidencia e identidade `beta-sor = beta-sim + beta-nes` sem
      erro numerico;
    - `EXP_02_pcoa_biplot_bray_curtis_vetores_especies.png/.xlsx`:
      995 unidades de esforco, 16 pontos em todos os quatro periodos e 161
      especies na matriz quantitativa de rede de emalhar;
    - figuras em `5400 x 3060 px`, 300 dpi, sem titulo geral e com rotulos
      revisados;
    - status: exploratorio, aguardando aprovacao tecnica.
  - corte da PCoA revisado e aprovado em 2026-08-13:
    - sensibilidade avaliada entre Bray-Curtis `0,40` e `0,85`;
    - corte selecionado: `0,55` (55% de dissimilaridade);
    - a escolha aumenta a resolucao dos grupos sem alterar coordenadas da PCoA,
      matriz de Bray-Curtis ou vetores de especies.
  - PCoA temporal conjunta gerada em 2026-08-13 apos revisao da pergunta:
    - arquivo: `EXP_03_pcoa_temporal_conjunta_fases_vetores_especies.png/.xlsx`;
    - unidade: 69 campanhas na mesma ordenacao, com CPUEn media por especie e
      transformacao raiz quadrada;
    - resultado no corte `0,55`: todas as 41 campanhas pos-enchimento, as seis
      de rebaixamento e as duas de reenchimento no mesmo grupo; 14 das 20
      campanhas pre-enchimento em grupo proprio e seis campanhas pre isoladas;
    - leitura: separacao composicional principal entre pre e pos-enchimento,
      sem evidencia de nova separacao completa no rebaixamento/reenchimento;
    - PCoA por pontos e periodos mantida apenas como leitura espacial
      complementar.

## Correcao Dos Mapas Reprodutivos

- regra aprovada em 2026-08-13:
  - universo taxonomico dos mapas reprodutivos: somente especies migradoras `MLD`;
  - femeas reprodutivas: `F3 + F4`;
  - machos reprodutivos: `M3 + M4`;
  - `F2/M2` nao entra nos mapas reprodutivos; o estadio 2 permanece exclusivo
    do corte de referencia utilizado na analise de recrutamento;
- produtos sobrescritos:
  - `05_12_3_mapa_femeas_reprodutivas_espacial.png`;
  - `05_12_4_mapa_machos_reprodutivos_espacial.png`;
- lastro incorporado em `05_12_processo_reprodutivo.xlsx`:
  - `Migradoras_reprod_espacial`;
  - `Migradoras_reprod_especies`;
  - `Premissas_mapas_reprod`;
- auditoria: 9 especies `MLD`, 216 femeas `F3/F4` e 105 machos `M3/M4`
  nos 16 pontos gerais;
- scripts atualizados:
  - `ictiofauna/gerar_5_12_reproducao_5_15_recrutamento_biocol001.py`;
  - `ictiofauna/gerar_teste_5_5_mapa_longitudinal_biocol001.py`.

## Revisao 5.10 - Curva Do Coletor

- figura oficial revisada em 2026-08-17:
  `05_10_curva_coletor_observada_jackknife1.png`;
- valores finais exibidos junto as extremidades das curvas:
  - riqueza observada: `322` especies;
  - riqueza estimada por Jackknife 1: `384,9` especies;
- valores calculados apos `1.050` unidades amostrais de campanha x ponto e
  confirmados na aba `Curva` de `05_10_dados_curva_coletor.xlsx`;
- mantidos o padrao sem titulo interno, a legenda superior, as faixas de
  `±1 DP`, a paleta aprovada e a resolucao de 300 dpi;
- regra incorporada ao gerador
  `ictiofauna/gerar_bateria_produtos_maduros_biocol001.py`.

## Produto 5.11 - Guildas Troficas

- figura gerada em 2026-08-17 no padrao grafico oficial:
  `05_11_figura_guildas_troficas.png`;
- universo recalculado a partir dos dados brutos fornecidos pelo responsavel
  tecnico: `99` especies;
- composicao: Piscivoro `27`, Onivoro `26`, Detritivoro `17`, Herbivoro `16`,
  Insetivoro `10`, Nao determinada `2` e Bentivoro `1`;
- os dois registros sem determinacao correspondem a estomago vazio e/ou
  descricao da dieta nao localizada na literatura;
- figura sem titulo interno, com total no centro, paleta variada e legenda
  externa contendo contagem e percentual;
- esta entrega representa as `99` especies informadas e nao fecha a
  classificacao trofica das `322` especies do projeto;
- script: `ictiofauna/gerar_5_11_guildas_troficas_biocol001.py`.

## Revisao De Layout 5.12 - Reproducao

- figuras oficiais regeneradas em 2026-08-17:
  - `05_12_1_reproducao_espacial.png`;
  - `05_12_2_reproducao_temporal.png`;
- formato final: A4 paisagem real, `3507 x 2481 px`, 300 dpi;
- tipografia ampliada para leitura apos insercao no relatorio;
- figura espacial: legenda dos quatro estadios em duas linhas e rotulos dos
  16 pontos ampliados;
- figura temporal: legenda dos estadios e legenda dos eventos em linhas
  independentes; eixo temporal reduzido para 12 referencias uniformes, com
  campanha e data em duas linhas;
- mantidos o padrao sem titulo interno, a paleta aprovada, os marcos temporais
  e os dados das planilhas oficiais;
- revisao exclusivamente grafica, sem alteracao de valores ou criterios
  analiticos;
- gerador atualizado:
  `ictiofauna/gerar_5_12_reproducao_5_15_recrutamento_biocol001.py`.

## Pendencias

- registrar/confirmar referencia espacial externa se houver mapas, Darwin Core com coordenadas ou produto geoespacial;
- confirmar SRC, barragem, espelho do reservatorio e malha hidrica antes dos minimapas;
- incorporar chuva, vazao, nivel do rio/cota do reservatorio e calendario oficial dos eventos antes da separacao fase x hidrologia;
- corrigir ou padronizar o preenchimento de `codigo_opyta` na consolidada, pois BIOCOL001 aparece em `codigo_interno_opyta`;
- registrar estrategia de backup antes de eventual nova consolidacao;
- revisar a V1 item a item e registrar ajustes tecnicos/graficos antes da versao final;
- receber as bases de 5.1, 5.14 e 5.18; completar 5.11 quando houver guilda trofica;
- resolver endemismo em rodada futura, se o produto precisar desse atributo.

## Fechamento E Aprendizados

- validadores:
  - Gate A fortalecido no `Opyta_Data` para campanhas operacionais `C###`, chave campanha+ponto, cadastro mestre completo e especies sem buracos obrigatorios;
  - validador de especies passou a exigir classificacao/categorias centrais antes de migracao.
- manifesto: atualizado para registrar a primeira versao analitica V1
- patterns: avaliar pattern para validacao de campanhas historicas com rotulos colapsados
- portfolio: pendente apos produtos aprovados
- backlog:
  - persistir melhor logs de validacao/migracao executados por CLI;
  - padronizar `codigo_opyta` vs `codigo_interno_opyta` no consolidado.
