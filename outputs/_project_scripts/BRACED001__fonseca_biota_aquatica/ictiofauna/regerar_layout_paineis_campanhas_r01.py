from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.projects.braaeg001 import regerar_layout_ictiofauna_biota_r02 as base


base.OUTPUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Resultados\Fonseca"
)
base.SOURCE_WORKBOOK = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Migracao\Fonseca\Opyta_ictiofauna_banco_dados_mar-jul_26-260813.xlsx"
)
base.CAMPAIGNS = ["C001-2026-03-CH", "C002-2026-06-SC"]
base.CAMPAIGN_LABELS = {
    "C001-2026-03-CH": "C01-Chuva",
    "C002-2026-06-SC": "C02-Seca",
}
base.CAMPAIGN_COLORS = {
    "C001-2026-03-CH": "#0B4F12",
    "C002-2026-06-SC": "#10F20A",
}


if __name__ == "__main__":
    base.main()
