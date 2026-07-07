# BRAAEG001 - Biota aquatica - nova base de referencia

## Controle

- projeto: BRAAEG001 / A&G Mineracao
- grupo: Biota aquatica
- operacao: validacao e migracao inicial de Fitoplancton, Zooplancton, Zoobentos e Ictiofauna
- estado atual: `configuring_analysis`
- aberta em: 2026-07-02
- atualizada em: 2026-07-03
- proxima acao: configurar recorte analitico, template, paleta, pasta de saida e produtos para abrir Gate C; nao gerar produtos antes da aprovacao

## Caminhos

- dados de referencia: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota`
- planilhas:
  - Fitoplancton: `Resultados_Migracao _Fito.xlsx`
  - Zooplancton: `Resultados_Migracao_zoo.xlsx`
  - Zoobentos: `Resultados_Migracao_Zoobentos.xlsx`
  - Ictiofauna: `Resultados_Migracao _Ictio.xlsx`
- cadastro de especies: `public.especies`
- saida operacional: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota`
- dossie: pendente; projeto ainda nao registrado em `docs/projects/`
- recipe: pendente; projeto ainda nao possui `configs/projects/` ou `configs/clients/braaeg001.json`
- lastro de validacao atual: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota/20260703T113813_validacao_nova_base_biota_aquatica_braaeg001.xlsx`
- log de validacao atual: `logs/validacao_biota_braaeg001/20260703T113813_validacao_nova_base_biota_aquatica_braaeg001.json`
- decisao taxonomica Gate B: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota/20260703T113754_gate_b_taxonomia_biota_braaeg001.xlsx`
- dry-run de migracao: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota/20260703T115152_dry_run_migracao_biota_aquatica_braaeg001.xlsx`
- apply de migracao: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota/20260703T115212_apply_migracao_biota_aquatica_braaeg001.xlsx`
- log de apply: `logs/migracao_biota_braaeg001/20260703T115212_apply_migracao_biota_aquatica_braaeg001.json`
- lastro superseded: `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineracao/resultados/migracao_biota/20260702T201844Z_escopo_migracao_biota_aquatica_braaeg001.xlsx`

## Progresso

| Etapa | Estado | Evidencia resumida |
| --- | --- | --- |
| Abertura | atualizada | Usuario definiu a pasta `migracao_biota` como nova base de referencia e informou inclusao de Ictiofauna, padronizacao de esforcos, correcao de `PX`/`PXX` e atualizacao de cursos d'agua. |
| Validacao | concluida com avisos | Relatorio `20260703T113813_validacao_nova_base_biota_aquatica_braaeg001.xlsx` gerado com Gate A `PASS_WITH_WARNINGS` e Gate B `PASS`. |
| Gate A - dados | aprovado com avisos | Usuario aprovou correcao de Ictiofauna e confirmou cobertura desigual de campanhas em 2026-07-03. |
| Cadastro de especies | concluido | 8 taxons cadastrados de forma aditiva em `public.especies`; `Sphaerium sp.` ja existia e foi usado como nome aprovado. |
| Auditoria de atributos | concluida para migracao | Validacao pos-cadastro encontrou 0 taxons ausentes e 0 conflitos de grupo. |
| Gate B - especies | aprovado | Taxonomia informada pelo usuario em 2026-07-03 e registrada em `20260703T113754_gate_b_taxonomia_biota_braaeg001.xlsx`. |
| Migracao | concluida | Dry-run `20260703T115152` sem divergencias bloqueantes; apply `20260703T115212` executado com backup por tabela. |
| Consolidacao | concluida | `biota_analise_consolidada` recebeu 404 linhas, equivalente aos resultados migraveis agregados. |
| Configuracao das analises | em andamento | Proxima etapa e definir recorte, template, paleta, pasta de saida e produtos para Gate C. |
| Gate C - analises | pendente | Deve ser aberto apenas com proposta explicita de template/paleta/saida/produtos. |
| Geracao dos produtos | pendente | Nao executar nesta etapa sem Gate C. |
| Revisao tecnica | pendente | Depende de produtos gerados. |
| Revisao de layout | pendente | Depende de produtos gerados. |
| Fechamento | pendente | Depende de Gate C, produtos/manifesto quando aplicavel e atualizacao de dossie/registry. |

## Gates

| Gate | Status | Registro |
| --- | --- | --- |
| A - dados | `approved_with_warnings` | Ictiofauna corrigida; cobertura desigual de campanhas aceita pelo usuario; permanecem avisos de esforco textual em Fito/Zoo e curso d'agua do meio fisico. |
| B - especies | `approved` | 8 novos taxons cadastrados e `Sphaerium spp.` normalizado para `Sphaerium sp.` conforme taxonomia informada. |
| C - analises | `pending` | Migracao/consolidacao concluidas; falta proposta de template, paleta, pasta de saida e produtos. |

## Validacao Dos Dados

- evidencia:
  - workbook: `20260703T113813_validacao_nova_base_biota_aquatica_braaeg001.xlsx`;
  - log: `logs/validacao_biota_braaeg001/20260703T113813_validacao_nova_base_biota_aquatica_braaeg001.json`;
  - script: `scripts/projects/braaeg001/validar_nova_base_biota.py`.
- status:
  - Gate A: `PASS_WITH_WARNINGS`;
  - Gate B: `PASS`.
- bloqueios Gate A: nenhum apos ajustes.
- avisos Gate A:
  - Fitoplancton e Zooplancton trazem `Esforco` como texto com unidade (`100 litros`, `1 litro`); o validador oficial marca aviso, nao bloqueio;
  - cobertura de campanhas difere por grupo, aceita como escopo operacional: Fito/Zoo/Zoobentos apenas `C001-2026-02-CH`; Ictiofauna com `C001-2026-02-CH` e `C002-2026-06-SC`;
  - nomes de cursos d'agua da nova base de biota divergem do Meio Fisico em 12 pontos compartilhados; replicar antes de reprocessar produtos de meio fisico.
- validacao oficial por grupo:
  - Fitoplancton: `PASS`, 12 pontos, 65 resultados, 39 taxons, 0 taxons ausentes;
  - Zooplancton: `PASS`, 12 pontos, 251 resultados, 53 taxons, 0 taxons ausentes;
  - Zoobentos: `PASS`, 12 pontos, 70 resultados, 26 taxons, 0 taxons ausentes;
  - Ictiofauna: `PASS`, 24 ponto-campanha, 23 resultados, 5 taxons, 0 taxons ausentes.
- banco antes da migracao:
  - `id_projeto`: `195`;
  - `pontos_coleta` para `BRAAEG001`: 0;
  - `biota_analise_consolidada` para `BRAAEG001`: 0.
- ajustes aplicados:
  - Ictiofauna: 52 linhas de `Metadados_Esforco` ajustadas para `Tipo_de_Amostragem = Quantitativa` e `Unidade_Esforco = m2/100`;
  - Zoobentos: 2 linhas de resultados alteradas de `Sphaerium spp.` para `Sphaerium sp.`;
  - backups criados antes dos ajustes em `Resultados_Migracao _Ictio__backup_pre_gate_ab_20260703T113754.xlsx` e `Resultados_Migracao_Zoobentos__backup_pre_gate_ab_20260703T113658.xlsx`.

## Cadastro E Auditoria De Especies

- especies/taxons ausentes no banco apos Gate B: 0.
- cadastrados em `public.especies`:
  - `Eunotia pectinalis` (`id_especie=5456`);
  - `Gyrosigma scalproides` (`id_especie=5457`);
  - `Humidophila contenta` (`id_especie=5458`);
  - `Pinnularia gibba` (`id_especie=5459`);
  - `Anagnostidinema sp.` (`id_especie=5460`);
  - `Scytonemataceae N.I.` (`id_especie=5461`);
  - `Physolinum sp.` (`id_especie=5462`);
  - `Oligoneuriidae` (`id_especie=5463`).
- `Sphaerium sp.` ja existia em `public.especies` (`id_especie=552`); resultados foram normalizados para esse nome.
- atributos obrigatorios: todos os taxons usados nos resultados existem no cadastro mestre; atributos ecologicos opcionais permanecem como lastro futuro.
- campos incertos: resolvidos pela taxonomia informada pelo usuario em 2026-07-03.
- ajustes manuais: aplicados e documentados em `20260703T113754_gate_b_taxonomia_biota_braaeg001.xlsx`.

## Migracao E Consolidacao

- IDs:
  - `codigo_interno_opyta`: `BRAAEG001`;
  - `id_projeto`: `195`.
- totais da fonte atual:
  - Fitoplancton: 65 resultados;
  - Zooplancton: 251 resultados;
  - Zoobentos: 70 resultados;
  - Ictiofauna: 23 resultados;
  - total bruto: 409 resultados.
- dry-run:
  - `20260703T115152_dry_run_migracao_biota_aquatica_braaeg001.xlsx`;
  - 24 ponto-campanha, 2 campanhas, 100 esforcos, 404 resultados migraveis;
  - banco antes do apply: 0 pontos, 0 esforcos, 0 resultados e 0 linhas consolidadas para a fatia biologica de `BRAAEG001`.
- apply:
  - `20260703T115212_apply_migracao_biota_aquatica_braaeg001.xlsx`;
  - campanhas cadastradas/resolvidas: `C001-2026-02-CH` (`id_campanha=678`) e `C002-2026-06-SC` (`id_campanha=679`);
  - resultados por tabela: Fitoplancton 65, Zooplancton 251, Zoobentos 70, Ictiofauna 18;
  - observacao: Ictiofauna tinha 23 linhas-fonte e foi agregada para 18 registros migraveis por esforco + especie, preservando 72 individuos.
- totais no banco apos apply:
  - pontos: 24;
  - esforcos: 100;
  - resultados base: 404;
  - consolidado: 404.
- auditoria consolidada por grupo/campanha:
  - Fitoplancton / `C001-2026-02-CH`: 65 linhas, 12 pontos, 39 taxons, contagem total 97,8484848485;
  - Zooplancton / `C001-2026-02-CH`: 251 linhas, 12 pontos, 53 taxons, contagem total 59,1;
  - Zoobentos / `C001-2026-02-CH`: 70 linhas, 12 pontos, 26 taxons, contagem total 116;
  - Ictiofauna / `C001-2026-02-CH`: 12 linhas, 8 pontos, 5 taxons, 55 individuos, biomassa 129,5;
  - Ictiofauna / `C002-2026-06-SC`: 6 linhas, 6 pontos, 4 taxons, 17 individuos, biomassa 74,4.
- coordenadas ausentes no consolidado: 0.
- backups criados antes do apply:
  - `public.backup_biota_braaeg001_20260703t115212_pontos`;
  - `public.backup_biota_braaeg001_20260703t115212_esforcos`;
  - `public.backup_biota_braaeg001_20260703t115212_fitoplancton`;
  - `public.backup_biota_braaeg001_20260703t115212_zooplancton`;
  - `public.backup_biota_braaeg001_20260703t115212_zoobentos`;
  - `public.backup_biota_braaeg001_20260703t115212_ictiofauna`;
  - `public.backup_biota_braaeg001_20260703t115212_consolidado`.

## Configuracao Das Analises

- numero de campanhas na base atual: `C001-2026-02-CH` para todos os grupos e `C002-2026-06-SC` apenas para Ictiofauna.
- template: pendente; depende do recorte de campanhas e da decisao do Gate C.
- paleta: pendente.
- pasta de saida: pendente.
- produtos: nao gerar antes do Gate C.

## Pendencias

- Configurar proposta de Gate C para analises e produtos, se/quando for a hora de gerar.
- Replicar nomes de cursos d'agua no Meio Fisico antes de qualquer produto integrado.

## Revisoes

| Revisao | Tipo | Impacto | Estado | Registro |
| --- | --- | --- | --- | --- |
| | | | | |

## Fechamento E Aprendizados

- validadores: nova validacao formal gerada e registrada em 2026-07-03.
- manifesto: pendente para produtos; migracao possui JSON/XLSX de dry-run e apply.
- patterns: seguir fluxo de biota com Gates A/B antes da migracao.
- portfolio: pendente.
- backlog: migrador biota deve aceitar recortes por grupo/campanha e registrar explicitamente quando a cobertura de campanhas for desigual.
