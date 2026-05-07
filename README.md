# Opyta Data Analysis Core

**Status**: MVP (Minimum Viable Product) | **Version**: 0.1.0 | **License**: MIT

Central project for ecological analysis pipelines with a single Python environment,
shared Supabase access, and a global plotting standard.

**Stable Pipelines**: Zoobentos ✓ | Fitoplancton ✓ | Zooplancton ✓  
**In Development**: ICTIO (planned for v0.2)

## Goals
- Reuse one environment for all clients/projects.
- Keep analysis blocks modular by biological group.
- Enforce one visual standard across all charts.
- Make client style changes configurable (colors/fonts) without code rewrite.

## Folder Structure
- src/opyta_analysis/: core package
- src/opyta_analysis/pipelines/: modular analysis blocks
- configs/: global and client configs
- scripts/: command line entry points
- outputs/: local technical area for reproducibility backups (`_project_scripts`) only
- logs/: execution logs and learning journal

## Quick Start
1. Create one conda env (recommended):
   - conda create -n opyta-eco python=3.11 -y
   - conda activate opyta-eco
2. Install dependencies once:
   - pip install -r requirements.txt
3. Create .env from .env.example and fill Supabase credentials.
4. Run pipeline:
   - python scripts/run_pipeline.py --project-id 62 --group Zoobentos --pipeline zoobentos --client fersam001 --output-dir "g:/Meu Drive/Opyta/Clientes/.../Resultados/Bentos" --env-file "g:/Meu Drive/Opyta/Opyta_Data/.env" --block 6

## Output Policy (Gold Operational Rule)
- `--output-dir` must always point to the final client/project delivery folder for business artifacts (`.xlsx`, `.png`, etc.).
- Local workspace `outputs/` must not accumulate validation-by-block folders or temporary delivery copies.
- Technical backup for reproducibility is written automatically to `outputs/_project_scripts/<project_name>/<group_name>/`.
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
   - `outputs/_project_scripts/sam_metais/fitoplancton`
   - `outputs/_project_scripts/sam_metais/zooplancton`
   - `outputs/_project_scripts/sam_metais/zoobentos`

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
