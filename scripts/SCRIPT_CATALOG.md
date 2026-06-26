# Script Catalog

Catalogo operacional dos scripts do repositorio. O objetivo e preservar
rastreabilidade sem depender de memoria ou de busca manual em pastas de cliente.

## Regras

- Prototipos ficam em `scripts/prototypes/`.
- Correcoes pontuais e auditorias ficam em `scripts/maintenance/<projeto>/`.
- Scripts especificos de clientes ficam em `scripts/projects/<cliente_ou_projeto>/`.
- Migracoes ficam em `scripts/migrations/<grupo_ou_tema>/`.
- Validadores ficam em `scripts/validation/`.
- Toda rotina reutilizavel deve ser promovida para `src/opyta_analysis`.
- Wrappers na raiz existem apenas para compatibilidade temporaria.

## Entry Points Estaveis

| Script | Status | Uso |
| --- | --- | --- |
| `scripts/run_pipeline.py` | producao | Runner central para pipelines de diagnostico. |
| `scripts/run/run_project_recipe.py` | producao | Runner por receita em `configs/projects/*.json`. |
| `scripts/run/meio_fisico/run_meio_fisico_pipeline.py` | producao | Runner especifico de meio fisico a partir de planilha. |
| `scripts/run/fauna/run_avifauna_multi_empreendimentos.py` | producao | Execucao multiempreendimento de avifauna. |
| `scripts/run/fauna/run_herpetofauna_multi_empreendimentos.py` | producao | Execucao multiempreendimento de herpetofauna. |
| `scripts/run/fauna/run_ictio_partial_multi_empreendimentos.py` | producao | Execucao parcial multiempreendimento de ictiofauna. |
| `scripts/run/fauna/run_mastofauna_multi_empreendimentos.py` | producao | Execucao multiempreendimento de mastofauna. |
| `scripts/run/fauna/run_primatas_multi_empreendimentos.py` | producao | Execucao multiempreendimento de primatas. |

## Projetos

| Projeto | Pasta | Uso |
| --- | --- | --- |
| Porto Estrela | `scripts/projects/porto_estrela/` | Ictiofauna: bases analiticas, exploratorias, graficos, HTML e resultados. |
| AVG | `scripts/projects/avg/` | Bentos/ictio 2026: migracao, consolidacao e geracao por campanha. |
| ITAGUA001 / Monitoramento da Fauna | `scripts/projects/project_165/` | Pipeline historico de ictiofauna documentado em `docs/PIPELINE_ICTIO_165.md`. |
| FERSAM001 / Sam Metais Diagnostico | `scripts/projects/sam_metais/` | Meio fisico, conformidade e revisao de biota aquatica. |
| VIRITA001 / Itabrita | `scripts/projects/virita001/` | Ictiofauna: relatorio tecnico HTML e evidencias da Campanha 1, seguindo o padrao analitico FERSAM001 para duas campanhas. |
| GEOARC001 / Arcelor | `scripts/projects/geoarc001/` | Ictiofauna: analises exploratorias taxonomicas e funcionais, mapas de grupos sentinelas e assinatura de especies por grupo funcional. |

## Geradores De Meio Fisico

Mantidos na raiz porque `src/opyta_analysis/pipelines/diagnostico/meio_fisico_xlsx.py`
os referencia por nome.

| Bloco | Script |
| --- | --- |
| B2 | `scripts/gerar_conformidade_sam_etapa2.py` |
| B3 | `scripts/gerar_b3_grafico_por_parametro.py` |
| B4 | `scripts/gerar_b4_pct_violacao.py` |
| B5 | `scripts/gerar_b5_iqa_cetesb.py` |
| B6 | `scripts/gerar_b6_iet_lamparelli.py` |
| B7 | `scripts/gerar_b7_iqasb_parcial.py` |
| B8 | `scripts/gerar_b8_mpelq.py` |
| B9 | `scripts/gerar_b9_sazonal.py` |
| B11 | `scripts/gerar_b11_sintese.py` |
| Piloto | `scripts/gerar_piloto_coliformes_etapa3.py` |
| Resumo | `scripts/gerar_resumo_tecnico.py` |

## Migracoes

| Tema | Pasta | Conteudo |
| --- | --- | --- |
| Herpetofauna | `scripts/migrations/herpetofauna/` | SQLs limpos, gerador SQL e inspecao. |
| Ictiofauna | `scripts/migrations/ictiofauna/` | Gerador SQL e migration SQL. |
| Meio fisico | `scripts/migrations/meio_fisico/` | Carga REST e insercao validada. |

## Validacao

| Script | Uso |
| --- | --- |
| `scripts/validation/audit_supabase_project_coverage.py` | Compara `public.projetos` do Supabase com `project_registry.json`. |
| `scripts/validation/build_knowledge_inventory.py` | Gera inventario da base tecnica, registries, docs e lastros. |
| `scripts/validation/check_repo_organization.py` | Auditoria da organizacao do repositorio, scripts e recipes. |
| `scripts/validation/validar_fauna_outputs.py` | Auditoria pos-run dos outputs de fauna. |
| `scripts/validation/validar_meio_fisico_outputs.py` | Auditoria pos-run dos outputs de meio fisico. |
| `scripts/validation/validar_migracao_ictiofauna.py` | Validacao pre-migracao de planilhas de ictiofauna. |

Observacao: `validar_migracao_ictiofauna.py` aceita `--coordinate-reference`
para validar coordenadas de pontos contra KMZ/KML antes da migracao.

## Prototipos

| Script | Origem | Status |
| --- | --- | --- |
| `scripts/prototypes/prototipar_geoher001_bentos_layouts.py` | GEOHER001/Herculano | Aprovado parcialmente; logica de minigraficos e 06 anual promovida para `src/opyta_analysis/pipelines/diagnostico/`. |
| `scripts/prototypes/prototipos_design_porto_estrela.py` | Porto Estrela | Referencia visual historica. |

## Relatorios Textuais

| Script | Projeto | Status |
| --- | --- | --- |
| `scripts/projects/geoher001/generate_bentos_textual_pilot.py` | GEOHER001/Herculano | Narrativa tecnica calibrada pela policy mestre Opyta, com HTML, matriz de evidencias e validacao sincronizados. |

## Manutencao

| Script | Projeto | Status |
| --- | --- | --- |
| `scripts/maintenance/geoher001/fix_geoher001_campaigns_supabase.py` | GEOHER001 | Correcao de nomenclatura de campanhas no Supabase. |
| `scripts/maintenance/geoher001/merge_geoher001_bentos_c37_nov_into_c36.py` | GEOHER001 | Script historico de investigacao/correcao. |
| `scripts/maintenance/geoher001/normalize_geoher001_bentos_taxonomy.py` | GEOHER001 | Auditoria e normalizacao transacional da taxonomia de Zoobentos, com dry-run, backup e verificacao pos-aplicacao. |
| `scripts/maintenance/geoher001/resolve_geoher001_bentos_pending_taxa.py` | GEOHER001 | Resolucao de taxons pendentes e consolidacao controlada de registros duplicados. |
| `scripts/maintenance/geoher001/restore_geoher001_bentos_c37_feb.py` | GEOHER001 | Restauracao da campanha C37 fevereiro/2026. |
| `scripts/maintenance/geoarc001/update_geoarc001_coordinates_from_kmz.py` | GEOARC001 | Auditoria dry-run/apply para corrigir `pontos_coleta` no Supabase usando KMZ oficial, com Excel/JSON antes e depois. |

## Wrappers Temporarios Na Raiz

Arquivos como `scripts/gerar_resultados_porto_estrela_ictio.py` ou
`scripts/validar_fauna_outputs.py` permanecem na raiz apenas como wrappers de
compatibilidade. Eles chamam o caminho organizado por meio de `scripts/_compat.py`.

Novos comandos, READMEs e documentos devem usar os caminhos organizados.
