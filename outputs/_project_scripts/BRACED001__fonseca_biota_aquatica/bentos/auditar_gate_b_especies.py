from __future__ import annotations

import runpy
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "ictiofauna" / "auditar_gate_b_especies.py"
DEFAULTS = [
    "--group",
    "Zoobentos",
    "--results-sheet",
    "Resultados_Zoobentos",
    "--output-prefix",
    "gate_b_especies_zoobentos_braced001",
    "--required-fields",
    "grupo_biologico",
    "reino",
    "filo",
    "classe",
    "bmwp_score",
]


if __name__ == "__main__":
    sys.argv = [str(TARGET), *sys.argv[1:], *DEFAULTS]
    runpy.run_path(str(TARGET), run_name="__main__")
