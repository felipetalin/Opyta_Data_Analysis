# Changelog

All notable changes to Opyta Ecological Analysis Pipelines will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Avifauna species and general status outputs now use the approved two-row
  table model for Itatiaia/Guanhaes, including DAF, sensitivity, endemism,
  conservation-list years, and trophic guild codes.
- AVG Ictiofauna April/May 2026 outputs now run through a dedicated runner that
  cleans final folders, applies AC01/AC02 point ordering, keeps zero-capture
  points in point/CPUE charts, and prevents zero placeholders from entering
  taxonomic charts.
- Ictiofauna consolidated-view loading now fails closed when `id_projeto` is
  absent and no explicit project fallback is registered, preventing accidental
  cross-project result generation.
- Ducal Zoobentos 06B/06C stacked taxonomic charts now aggregate by order and
  use a high-contrast categorical palette with selected blues instead of the
  sequential project gradient.

### Added
- AVG Ictiofauna 2026 operational note in `docs/AVG_ICTIOFAUNA_2026.md`,
  including control-area point groups, zero-capture placeholder rules, and
  minimum validation checks.
- Ducal Ictiofauna scope fallback (`project_id=183` -> `DUCGEO001`) and
  project-scope safety note in `docs/PROJECT_SCOPE_SAFETY.md`.
- BRACAR001 client config (`configs/clients/bracar001.json`) with audit slug
  `BRACAR001__projeto_carangola` and the new biomass reconstruction flag.

- Ictiofauna report-layout figures for BRACAR001 (`ictio_report_layout`):
  CPUEn/CPUEb per point and per campaign, relative richness per river section,
  species-by-point occurrence table, and Shannon/Pielou per year. Sections and
  phases are declared in the client config and drawn as labelled boxes under the
  x axis. Approved Gold exception documented in `docs/PADRAO_GOLD_APROVADO.md`.
- Ictiofauna occurrence-by-campaign table for report layouts
  (`05_tabela_ocorrencia_por_campanha_*.xlsx`, Quadro 8 of the consolidated
  report): species-by-campaign presence matrix with OC, CO (%) and per-species
  N, plus abundance and richness footer rows, and a `Resumo_campanha` sheet
  mapping each ordinal to its campaign code, year and season. Built over every
  capture method, which is the basis the report uses. Validated against the
  client model for BRACAR001: 34 species, 1122 presence cells and the abundance
  and richness rows of all 33 reported campaigns match with zero differences
  (total 4976). The generated table additionally carries campaign 34
  (Jul/2026, 67 specimens), which postdates the report.
- `spine_sides` theme key so a product can open the axes frame (report layouts),
  enforced symmetrically by `validate_axes_style`. Omitting it keeps the closed
  four-sided frame the Gold standard requires.

### Fixed
- `apply_theme` no longer re-enables the y grid when `grid_y` is false. Passing
  line properties alongside `visible=False` makes matplotlib turn the grid back
  on, so `grid_y: false` had never worked.
- Ictiofauna yearly CPUE panels no longer drop campaigns: the grid was fixed at
  2x2 while `zip` stopped at the shorter sequence, silently discarding the fifth
  campaign of any year (BRACAR001 lost `C014-2009-12`). The grid now grows.
- Ictiofauna CPUEb can now reconstruct total line biomass as
  `contagem * biomassa` when a project sets `ictio_biomass_from_mean_weight`.
  The consolidated `biomassa` column stores `pc_g` (mean weight per individual
  of the lot), so summing it directly underestimates CPUEb whenever
  `contagem > 1`. Confirmed on BRACAR001: species-level comparison of `pc_g`
  for single-specimen rows versus lots gives a ratio around 1.0 (0.73-1.43)
  instead of scaling with lot size, and the project total moves from
  131,287 g to 518,017 g (about 3.95x). Enabled only for BRACAR001 for now;
  every other project keeps the previous behaviour by default.

## [0.1.0] - 2026-05-07

### Status
Minimum Viable Product (MVP) - Initial release with 3 biological groups implemented and validated.

### Added
- **Zoobentos Pipeline** (Complete)
  - Blocks 3-12: Full analytical suite (composition, occurrence, richness, abundance, diversity, clustering, sampling sufficiency, indices)
  - Gold visual standard compliance
  - Project-scoped data filtering with fallback for consolidated views
  - 1125 specimens validated from SAM Metais project

- **Fitoplancton Pipeline** (Complete)
  - Blocks 3-7, 10-13: Core analytical blocks (composition, occurrence, richness per point, phylum-level analysis, diversity, dendrogram, sufficiency, DarwinCore export)
  - Gold visual standard compliance with client-specific palette override
  - Project-scoped data filtering
  - 591 specimens validated from SAM Metais project

- **Zooplancton Pipeline** (Complete)
  - Blocks 3-13: Full analytical suite mirroring Fitoplancton/Zoobentos patterns
  - Gold visual standard compliance
  - Project-scoped data filtering with consolidated-view fallback
  - 852 specimens validated from SAM Metais project

- **Central Dispatcher & Runner**
  - Unified CLI entry point supporting all biological groups
  - Block-level execution with granular control
  - Automatic project script backup generation (reproducibility)
  - Execution metadata JSON for audit trail

- **Gold Visual Standard** (Approved & Frozen)
  - Figure size: 15×10 inches (A4 landscape)
  - Base font: 14 pt Arial, legend: 13 pt
  - Layout: horizontal legend on top, no title in chart body, Y-grid only
  - Export: DPI 600, bbox_inches="tight"
  - Documented exceptions for phylum composition (multicolor) and categorical density (high-contrast palette)

- **Automatic Audit Trail**
  - Execution metadata JSON captures timestamp, parameters, data scope
  - Reproducer scripts (`_run_this_analysis.py`) generated per project/group
  - Historical timestamped backups in `outputs/_project_scripts/<project>/<group>/`

- **Documentation**
  - `README.md`: Quick start, folder structure, output policy, block inventory
  - `docs/PADRAO_GOLD_APROVADO.md`: Full Gold standard specification
  - `logs/PROJECT_JOURNAL.md`: Phase-by-phase work log and learnings
  - Memory registry: `padrao_ouro_graficos.md` (permanent operational rules)

### Infrastructure
- Central theme engine (`theme.py`) for style consistency
- Validators (`validators.py`) for style enforcement before file save
- Supabase integration with pagination and project scoping
- Environment-based credential management (`.env` pattern)
- Modular pipeline architecture per biological group

### Testing & Validation
- Full pipeline execution tested for all 3 groups
- Visual style validated against approved Gold baseline
- Project scope fallback tested for consolidated data views
- Reproducibility validated: scripts and metadata automatically captured

### Known Limitations
- ICTIO group not yet implemented (planned for v0.2)
- No web UI integration (Streamlit planned for future)
- Limited to local execution (no CI/CD pipeline runners yet)
- Consolidated Supabase view lacks direct `id_projeto` column (fallback implemented)

### Technical Details
- Python 3.11+
- Dependencies: pandas, matplotlib, seaborn, scipy, plotly, openpyxl, supabase
- Modular structure: one pipeline function per biological group
- Strict project scoping: `project_id=62` (SAM Metais) with fallback filters
- Sample unit definition: `campanha + ponto` for sufficiency curves (fixed rule)

## [Unreleased]

### Planned for v0.2
- [ ] ICTIO biological group migration
- [ ] Block selector documentation per group
- [ ] Additional biological groups as needed
- [ ] Python test suite with pytest
- [ ] GitHub Actions CI/CD for validation

### Planned for Future
- [ ] Streamlit web UI
- [ ] Docker containerization
- [ ] Batch pipeline execution
- [ ] Advanced filtering UI
- [ ] Real-time result export
