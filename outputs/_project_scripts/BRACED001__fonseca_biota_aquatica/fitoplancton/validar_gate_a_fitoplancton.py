from __future__ import annotations

import runpy
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "zooplancton" / "validar_gate_a_zooplancton.py"
DEFAULTS = [
    "--group",
    "Fitoplancton",
    "--output-prefix",
    "validacao_gate_a_fitoplancton_braced001",
]


if __name__ == "__main__":
    sys.argv = [str(TARGET), *sys.argv[1:], *DEFAULTS]
    runpy.run_path(str(TARGET), run_name="__main__")
