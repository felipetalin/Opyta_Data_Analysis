# BIOCOL001 - Monitoramento e Resgate da Ictiofauna - UHE Colider

Lastro tecnico da operacao de validacao, cadastro, migracao e consolidacao de
Ictiofauna do projeto BIOCOL001.

## Identidade

- codigo Opyta: `BIOCOL001`
- projeto Supabase: `id_projeto=206`
- nome do projeto:
  `Monitoramento e Resgate da Ictiofauna no rio Teles Pires, na Area de Influencia da Usina Hidreletrica Colider - MT`
- cliente: `Bios Consultoria e Servicos Ambientais Ltda.`
- CNPJ: `05.344.781/0001-55`
- responsavel tecnico: `Felipe Talin Normando`
- licenca ambiental: `N/I`
- data de inicio: `2011-12-21`
- data fim prevista: `2028-06-20`

## Estado

- Gate A - dados: aprovado com ressalva
- Gate B - especies: aprovado com ressalva
- migracao: concluida
- consolidacao: concluida
- Gate C - analises: aprovado parcial para bateria madura
- produtos analiticos: R02 gerado para bateria madura no template BIOPOR001

## Totais De Controle

| Item | Total |
| --- | ---: |
| Campanhas operacionais | 69 |
| Rotulos historicos de campanha | 86 |
| Pontos/campanha-ponto no banco apos padronizacao | 1245 |
| Pontos unicos na planilha v3 | 18 |
| Pontos da malha geral padrao | 16 |
| Pontos condicionais do sistema de transposicao | 2 |
| Rotulos de ponto no banco/consolidado | 19 |
| Esforcos Ictiofauna | 1869 |
| Registros em `resultados_ictiofauna` | 13798 |
| Individuos | 108355 |
| Especies distintas | 327 |
| Registros consolidados | 13798 |
| Linhas em `resultados_ictiofauna_detalhe` | 74579 |
| Linhas com sexo F/M no detalhe | 13510 |
| Linhas com EMG no detalhe | 13439 |
| Linhas com evidencia reprodutiva forte | 2755 |
| Linhas no universo geral R01 | 71519 |
| Individuos no universo geral R01 | 100110 |
| Especies no universo geral R01 | 323 |

## Referencias

- operacao:
  `docs/control_center/operations/BIOCOL001_ICTIOFAUNA_COLIDER_MIGRACAO.md`
- dossie:
  `docs/projects/BIOCOL001_COLIDER_ICTIOFAUNA.md`
- recipe:
  `configs/projects/biocol001_colider_ictiofauna.json`
- dados:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Planilha/Migracao/Opyta-Bios-Ictio-2026_MIGRACAO_DE DADOS -version 4.xlsx`
- cadastro de especies:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Planilha/Migracao/Cadastro_especies_opyta_colider-ictio-2600812.xlsx`
- carga detalhe reproducao/biometria:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/ictiofauna/carregar_resultados_ictiofauna_detalhe_biocol001.py`
- auditoria DB detalhe x agregado:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/auditoria_db_resultados_ictiofauna_detalhe_biocol001_20260812134703.csv`
- camada temporal do reservatorio:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/camada_temporal_reservatorio_biocol001.csv`
- auditoria preliminar de recrutamento:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider/inventory/auditoria_recrutamento_mcd_mld_cp_f2_biocol001_20260812.csv`
- pacote R01 de produtos maduros:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_ictiofauna_produtos_maduros_R01`
- pacote R02 de produtos maduros no template BIOPOR001:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_ictiofauna_produtos_maduros_R02_BIOPOR001_template`

## Pendencias Antes De Gerar Produtos

- confirmar template multicampanha, paleta, pasta de saida e produtos no Gate C;
- declarar universo de pontos de cada produto conforme camada operacional em
  `inventory/camada_operacional_pontos_biocol001.csv`;
- registrar referencia espacial externa se mapas, Darwin Core ou outro produto geoespacial forem gerados;
- padronizar ou considerar nos scripts que BIOCOL001 esta em `codigo_interno_opyta` na consolidada, enquanto `codigo_opyta` esta nulo;
- resolver endemismo em rodada futura se o produto depender desse atributo.
- manter ictioplancton/ovos e larvas e marcacao T-TAG como `Aguardar` ate recebimento das bases especificas;
- tratar STP pelos pontos `PT-13C` e `PT-13D`/camada operacional `ICTIO13C` e `ICTIO13D`;
- revisar criterio preliminar de recrutamento por especie antes de produto final, somente para `MLD`: jovem = `CP_cm` menor que o menor `CP_cm` de femeas `F2/F3/F4`, com cautela para amostra pequena ou valor isolado.
- aplicar marcos temporais do reservatorio nas figuras temporais: pre-enchimento ate `C020`, pos-enchimento de `C021` em diante, rebaixamento parcial de `2025-08` a `2026-02` e reenchimento em `2026-03`.

## Backup Da Correcao De Campanhas

- `public.bkp_biocol001_cfix_20260812113032_pontos`
- `public.bkp_biocol001_cfix_20260812113032_esforcos`
- `public.bkp_biocol001_cfix_20260812113032_resictio`
- `public.bkp_biocol001_cfix_20260812113032_consol`

## Backup Da Correcao V4

- `public.bkp_biocol001_v4fix_20260812133027_resictio`
- `public.bkp_biocol001_v4fix_20260812133027_consol`

## Backup Da Carga Detalhe

- `public.bkp_biocol001_detail_20260812134703`
