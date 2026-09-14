from __future__ import annotations

import runpy
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "ictiofauna" / "auditar_gate_b_especies.py"
DEFAULTS = [
    "--group",
    "Fitoplancton",
    "--results-sheet",
    "Resultados_Fitoplancton",
    "--output-prefix",
    "gate_b_especies_fitoplancton_braced001",
    "--required-fields",
    "grupo_biologico",
    "reino",
    "filo",
    "classe",
    "ordem",
    "familia",
    "genero",
    "status_estadual",
    "status_ameaca_nacional",
    "status_ameaca_global",
    "origem",
    "habito_alimentar",
    "estrategia_reprodutiva",
    "valor_economico",
]


if __name__ == "__main__":
    sys.argv = [str(TARGET), *sys.argv[1:], *DEFAULTS]
    runpy.run_path(str(TARGET), run_name="__main__")
