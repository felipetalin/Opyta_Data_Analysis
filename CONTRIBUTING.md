# Contributing

This project is currently in MVP phase (v0.1.0) with 3 stable biological pipelines:
- Zoobentos
- Fitoplancton
- Zooplancton

## Branch Strategy
Use one branch per work item:
- `feature/<short-name>` for new functionality
- `fix/<short-name>` for bug fixes
- `docs/<short-name>` for documentation-only updates

## Pull Request Rules
1. Keep changes focused and small.
2. Explain impact by biological group and block.
3. Include validation evidence (commands and generated artifacts).
4. Update `CHANGELOG.md` for user-visible changes.
5. Never commit secrets (`.env`, keys, credentials).

## Quality Gates
A PR should pass all checks below:
- Gold visual standard preserved (`docs/PADRAO_GOLD_APROVADO.md`)
- Project scoping correct (`project_id` and fallback filters)
- Reproducibility artifacts generated (`execution_metadata.json`, `_run_this_analysis.py`)
- Documentation updated when behavior changes

## Commit Messages
Prefer clear messages like:
- `feat(zooplancton): add block 6 density chart`
- `fix(zoobentos): correct project scope fallback`
- `docs: update roadmap for v0.2`

## Reporting Bugs
Use the bug report template and include:
- exact command used
- traceback or failing output
- metadata and reproducer script paths

## Suggesting Features
Use the feature request template and define acceptance criteria.
