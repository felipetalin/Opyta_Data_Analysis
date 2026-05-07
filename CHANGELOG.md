# Changelog

All notable changes to Opyta Ecological Analysis Pipelines will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
