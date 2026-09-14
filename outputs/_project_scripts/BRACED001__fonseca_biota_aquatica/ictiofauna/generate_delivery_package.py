from __future__ import annotations

import os
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
os.environ["OPYTA_DELIVERY_PROJECT_CODE"] = "BRACED001"
os.environ["OPYTA_DELIVERY_PROJECT_ID"] = "133"
os.environ["OPYTA_DELIVERY_PACKAGE_SLUG"] = "braced001"
os.environ["OPYTA_DELIVERY_REPORT_TITLE"] = "BRACED001 - Diagnóstico da ictiofauna de Fonseca"
os.environ["OPYTA_DELIVERY_AUDIT_DIR"] = str(Path(__file__).resolve().parent)
os.environ["OPYTA_DELIVERY_OUTPUT_DIR"] = str(
    Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Resultados\Fonseca")
)

runpy.run_path(
    str(ROOT / "outputs" / "_project_scripts" / "BRAAEG001__a_g_mineracao_biota_aquatica" / "ictiofauna" / "generate_delivery_package.py"),
    run_name="__main__",
)
