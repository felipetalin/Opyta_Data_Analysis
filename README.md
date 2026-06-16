# Opyta Data Analysis Core

**Status**: MVP (Minimum Viable Product) | **Version**: 0.1.0 | **License**: MIT

Central project for ecological analysis pipelines with a single Python environment,
shared Supabase access, and a global plotting standard.

**Stable Pipelines**: Zoobentos ✓ | Fitoplancton ✓ | Zooplancton ✓  
**In Development**: ICTIO (block 3 migrated, incremental rollout)

## Goals
- Reuse one environment for all clients/projects.
- Keep analysis blocks modular by biological group.
- Enforce one visual standard across all charts.
- Make client style changes configurable (colors/fonts) without code rewrite.

## Folder Structure
- src/opyta_analysis/: core package
- src/opyta_analysis/pipelines/: modular analysis blocks
- configs/: global, client and project recipes
- configs/projects/: reproducible project recipes (campaigns, outputs, visual decisions)
- scripts/: operational commands; see `scripts/README.md` and `scripts/SCRIPT_CATALOG.md`
- docs/patterns/: reusable visual/methodological patterns
- docs/projects/: project-level technical notes
- outputs/: local technical area for reproducibility backups and run manifests
- logs/: execution logs and learning journal

See `docs/README.md` for the Knowledge Hub and `docs/ORGANIZACAO_REPOSITORIO.md`
for the current organization policy.
Use `docs/CHECKLIST_PROJETO.md` at project opening/closing and run
`python scripts/validation/check_repo_organization.py` to audit the structure.

## Quick Start
1. Create one conda env (recommended):
   - conda create -n opyta-eco python=3.11 -y
   - conda activate opyta-eco
2. Install dependencies once:
   - pip install -r requirements.txt
3. Create .env from .env.example and fill Supabase credentials.
4. Run pipeline:
   - python scripts/run_pipeline.py --project-id 62 --group Zoobentos --pipeline zoobentos --client fersam001 --output-dir "g:/Meu Drive/Opyta/Clientes/.../Resultados/Bentos" --env-file "g:/Meu Drive/Opyta/Opyta_Data/.env" --block 6
5. Run a registered project recipe:
   - python scripts/run/run_project_recipe.py geoher001_herculano_2022_2025 --env-file .env --dry-run
6. Check repository organization before closing a project:
   - python scripts/validation/check_repo_organization.py
7. Build the knowledge inventory:
   - python scripts/validation/build_knowledge_inventory.py --output outputs/_runs/knowledge_inventory_latest.json

## Output Policy (Gold Operational Rule)
- `--output-dir` must always point to the final client/project delivery folder for business artifacts (`.xlsx`, `.png`, etc.).
- Local workspace `outputs/` must not accumulate validation-by-block folders or temporary delivery copies.
- Technical backup for reproducibility is written automatically to `outputs/_project_scripts/<project_name>/<group_name>/`.
- New run-level manifests and scratch artifacts should use `outputs/_runs/` and `outputs/_scratch/`.
- Each group backup folder must keep only:
   - `execution_metadata.json`
   - `_run_this_analysis.py`
   - one timestamped metadata file (`*_execution_metadata.json`)
   - one timestamped reproducer script (`*_run_this_analysis.py`)
- Optional project-level inventory file:
   - `outputs/_project_scripts/<project_name>/MANIFEST.json`

Example for SAM Metais:
- deliverables:
   - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Resultados/Fitoplancton`
   - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Resultados/Zooplancton`
   - `G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Resultados/Zoobentos`
- technical backups:
   - `outputs/_project_scripts/FERSAM001__sam_metais_diagnostico/fitoplancton`
   - `outputs/_project_scripts/FERSAM001__sam_metais_diagnostico/zooplancton`
   - `outputs/_project_scripts/FERSAM001__sam_metais_diagnostico/zoobentos`

Supported `--block` values for Zoobentos core currently:
- `3` (Tabela de Composição Taxonômica)
- `4` (Tabela de Ocorrência por Campanha)
- `5` (Riqueza por Ponto)
- `6` (Riqueza + Abundancia por Classe)
- `7` (Riqueza por Ordem - barras + rosca)
- `8` (Diversidade Alfa - Shannon + Pielou)
- `9` (Dendrograma Bray-Curtis)
- `10` (Curva de Suficiencia Amostral)
- `11` (BMWP)
- `12` (EPT/CHOL)
- `all` (runs 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12)

Supported `--block` values for Fitoplancton core currently:
- `3` (Tabela de Composição Taxonômica)
- `4` (Tabela de Ocorrencia por Campanha e Ponto, regra quanti/quali)
- `5` (Riqueza Taxonomica por Ponto e Campanha)
- `6` (06A/06B/06C - densidade por filo)
- `7` (Riqueza por Filo - barras + rosca)
- `10` (Diversidade Alfa - Shannon + Pielou)
- `11` (Dendrograma Bray-Curtis)
- `12` (Curva de Suficiencia Amostral)
- `13` (DarwinCore)
- `all` (runs migrated FITO set)

Supported `--block` values for Zooplancton core currently:
- `3` (Tabela de Composição Taxonômica)
- `4.5` (Tabela de Ocorrencia por Campanha e Ponto, regra quanti/quali)
- `5` (Riqueza Taxonomica por Ponto e Campanha)
- `6` (06A/06B/06C - densidade por filo)
- `7` (Riqueza por Filo - barras + rosca)
- `10` (Diversidade Alfa - Shannon + Pielou)
- `11` (Dendrograma Bray-Curtis)
- `12` (Curva de Suficiencia Amostral)
- `13` (DarwinCore)
- `all` (runs migrated ZOO set)

Supported `--block` values for ICTIO core currently:
- `3` (Tabela de Composição Taxonômica)
- `4` (Tabela de Distribuição/Ocorrência por Campanha e Ponto)
- `5` (Riqueza Taxonômica por Ponto e Campanha)
- `6` (Abundância Total por Ponto e Campanha)
- `7` (Riqueza por Ordem e Família - tabelas + gráficos)
- `8` (CPUE por Ponto: CPUEn e CPUEb)
- `9` (CPUE por Espécie: CPUEn e CPUEb)
- `10` (Diversidade Alfa: Shannon e Pielou sobre matriz CPUEn)
- `11` (Dendrograma de Similaridade - Bray-Curtis sobre matriz CPUEn)
- `12` (Curva de Suficiência Amostral - Jackknife 1)
- `13` (Exportação DarwinCore)
- `all` (currently runs blocks 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13)

## Rules
- Do not run pip install inside notebooks.
- Do not hardcode style in analysis blocks.
- Always apply theme through theme engine.
- Always validate chart style before saving.
- If style validation fails, treat as pipeline error and fix in central theme/validator.
- Block-level style exception is allowed only with explicit approval and mandatory documentation in Gold spec + project journal.

## Gold Standard (Approved)
- Approved baseline config: `configs/theme_gold_approved.json`
- Detailed specification: `docs/PADRAO_GOLD_APROVADO.md`
- Current default theme is aligned with approved Gold baseline.
- Latest approved analytical criterion included: block 10 counts sampling unit as `campaign + point`.

## Meio Fisico Documentation
- Technical README: `docs/README_MEIO_FISICO.md`
- Learning memory and operational lessons: `logs/MEMORIA_APRENDIZADO_MEIO_FISICO.md`

## Fauna Audit Documentation
- Technical README: `docs/README_FAUNA_AUDITORIA.md`
- Learning memory and operational lessons: `logs/MEMORIA_APRENDIZADO_FAUNA.md`
- Audit command: `python scripts/validation/validar_fauna_outputs.py --project FERSAM001__sam_metais_diagnostico`

## Next Steps
- Start modular migration for next biological groups not yet delivered.
- Reuse the approved Gold standard with no block-local style exceptions.
- Keep `outputs/` clean and reserve it for `_project_scripts` only.
- Integrate runner into Streamlit app after group migrations stabilize.

## Roadmap

### v0.2.0 (Planned)
- [ ] ICTIO biological group migration
- [ ] Block selector reference documentation
- [ ] Python test suite (pytest)

### v0.3.0 and Beyond
- [ ] Streamlit web UI integration
- [ ] Docker containerization
- [ ] GitHub Actions CI/CD pipeline
- [ ] Additional biological groups
- [ ] Batch execution mode

## Contributing

Development branches: `feature/<group>-migration` or `fix/<issue-name>`.

All PRs require:
- Gold standard visual compliance (see [docs/PADRAO_GOLD_APROVADO.md](docs/PADRAO_GOLD_APROVADO.md))
- Project scope validation (`project_id=62` with fallback)
- Full pipeline test (`--block all`)
- CHANGELOG.md update

See [logs/PROJECT_JOURNAL.md](logs/PROJECT_JOURNAL.md) for detailed project history and learnings.
