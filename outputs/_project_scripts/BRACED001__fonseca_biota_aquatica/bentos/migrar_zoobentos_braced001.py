from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.braaeg001 import migrar_biota_aquatica as migration


migration.PROJECT_CODE = "BRACED001"
migration.PROJECT_ID = 133
migration.PROJECT_SLUG = "braced001"
migration.OUTPUT_LOG_DIR = Path(__file__).resolve().parent / "migration"


if __name__ == "__main__":
    raise SystemExit(migration.main())
