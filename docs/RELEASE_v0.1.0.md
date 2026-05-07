# Release v0.1.0 (MVP)

Date: 2026-05-07
Tag: v0.1.0

## Highlights
- MVP stabilized with 3 biological pipelines:
  - Zoobentos
  - Fitoplancton
  - Zooplancton
- Unified execution runner with block-level dispatch
- Approved Gold visual standard applied across outputs
- Automatic reproducibility backup generation per project and group
- Execution metadata and replay script generation after successful runs

## Included in This Release
- Pipeline modules and central runner
- Supabase integration and project-scope fallback logic
- Theme engine and validation layer
- Documentation baseline:
  - README
  - CONTRIBUTING
  - CHANGELOG
  - Gold standard documentation
- GitHub collaboration templates:
  - Issue templates (bug + feature)
  - Pull request template

## Reproducibility and Audit Trail
Each successful execution generates technical backup artifacts in:
- outputs/_project_scripts/<project>/<group>/

Artifacts include:
- execution_metadata.json (latest)
- _run_this_analysis.py (latest)
- timestamped metadata/script snapshots

## Known Limitations
- ICTIO pipeline not yet implemented (target: v0.2)
- No CI workflow yet
- No Streamlit UI yet

## Upgrade and Compatibility
- Python 3.11+
- Environment variables required:
  - SUPABASE_URL
  - SUPABASE_ANON_KEY
- Existing workflows remain CLI-first and backward compatible for current 3 groups

## Next Milestones
- v0.2: ICTIO migration + test suite growth
- v0.3: Streamlit integration + CI/CD + containerization
