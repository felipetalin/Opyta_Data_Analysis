from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.braaeg001 import migrar_biota_aquatica as migration


TAXON_MAP = {"Scytonemataceae n.i.": "Scytonemataceae"}


def load_workbooks_with_taxon_map(input_dir: Path, input_files: list[Path] | None = None):
    workbooks = ORIGINAL_LOADER(input_dir, input_files)
    for workbook in workbooks:
        if "Nome_Cientifico" in workbook.resultados.columns:
            workbook.resultados["Nome_Cientifico"] = workbook.resultados["Nome_Cientifico"].replace(TAXON_MAP)
    return workbooks


migration.PROJECT_CODE = "BRACED001"
migration.PROJECT_ID = 133
migration.PROJECT_SLUG = "braced001"
migration.OUTPUT_LOG_DIR = Path(__file__).resolve().parent / "migration"
ORIGINAL_LOADER = migration.load_workbooks
migration.load_workbooks = load_workbooks_with_taxon_map


if __name__ == "__main__":
    raise SystemExit(migration.main())
