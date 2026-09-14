# BIOCOL001 - Colider - Ictiofauna

## Identidade

- codigo Opyta: `BIOCOL001`
- id Supabase: `206`
- canonical key: `BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider`
- nome Supabase: `Monitoramento e Resgate da Ictiofauna no rio Teles Pires, na Area de Influencia da Usina Hidreletrica Colider - MT`
- grupo: Ictiofauna
- cliente/origem operacional: Bios / Colider

## Estado Operacional

- operacao ativa:
  `docs/control_center/operations/BIOCOL001_ICTIOFAUNA_COLIDER_MIGRACAO.md`
- lastro:
  `outputs/_project_scripts/BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider`
- estado atual: `generated_pending_review`
- proxima decisao: revisar pacote R02 de produtos maduros no template BIOPOR001

## Dados E Cadastro

- planilha de dados validada/corrigida:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Planilha/Migracao/Opyta-Bios-Ictio-2026_MIGRACAO_DE DADOS -version 4.xlsx`
- cadastro de especies validado:
  `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Planilha/Migracao/Cadastro_especies_opyta_colider-ictio-2600812.xlsx`

## Totais De Referencia

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

## Observacoes Tecnicas

- A contagem operacional correta de campanhas usa o codigo `C###`; os 86 rotulos historicos originais foram padronizados para 69 campanhas no banco.
- A planilha v3 tem 18 pontos de programacao; para analises gerais, o universo padrao fica com 16 pontos de malha regular.
- O banco/consolidado tem 19 rotulos de ponto porque preserva `ICTIO13A - Marcação`.
- `ICTIO13A - Marcação` pertence a programacao de marcacao e deve ficar fora por padrao das analises gerais.
- `ICTIO13C` e `ICTIO13D` pertencem ao sistema de transposicao de peixes; usar como camada condicional, declarando inclusao/exclusao em cada produto.
- O consolidado contem BIOCOL001 por `id_projeto=206` e `codigo_interno_opyta='BIOCOL001'`; a coluna `codigo_opyta` esta nula para este projeto.
- Endemismo foi reconhecido como tema a resolver depois, sem bloquear a migracao autorizada.
- A correcao de campanhas foi aplicada em 2026-08-12 com backup `public.bkp_biocol001_cfix_20260812113032_*`.
- A correcao de abundancia/biometria da v4 foi aplicada ao banco em 2026-08-12 com backup `public.bkp_biocol001_v4fix_20260812133027_*`; BIOCOL001 ficou com 108.355 individuos no banco e na consolidada.
- A tabela `public.resultados_ictiofauna_detalhe` foi carregada em 2026-08-12 a partir da v4 para preservar biometria, sexo e EMG linha-a-linha; a auditoria fechou 13.798/13.798 agregados vinculados e diferenca zero contra `resultados_ictiofauna`.
- O pacote R02 de produtos maduros foi gerado em `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Bios/Colider/Resultados/2026/Junho-2026/BIOCOL001_ictiofauna_produtos_maduros_R02_BIOPOR001_template`, alinhado ao template BIOPOR001/Porto Estrela, com 5 bases finais, produtos oficiais em Excel, workbook tecnico e 7 figuras PNG.
- Ictioplancton/ovos e larvas e marcacao T-TAG ficam com status `Aguardar` ate recebimento das bases especificas.
- STP deve ser tratado pelo recorte proprio dos pontos `PT-13C` e `PT-13D`/camada operacional `ICTIO13C` e `ICTIO13D`.
- Recrutamento deve ser aplicado somente para especies migradoras de curta distancia (`MCD`) e migradoras de longa distancia (`MLD`); criterio preliminar documentado: jovens por especie = individuos com `CP_cm` inferior ao menor `CP_cm` observado em femeas `F2/F3/F4`; resultados devem ser acompanhados de bandeira de cautela para amostra pequena ou limite influenciado por registro isolado.
- Marcos temporais do reservatorio: pre-enchimento ate `C020`; pos-enchimento de `C021` em diante; rebaixamento parcial entre `2025-08` e `2026-02`; reenchimento em `2026-03`. A camada temporal oficial esta em `inventory/camada_temporal_reservatorio_biocol001.csv`.
