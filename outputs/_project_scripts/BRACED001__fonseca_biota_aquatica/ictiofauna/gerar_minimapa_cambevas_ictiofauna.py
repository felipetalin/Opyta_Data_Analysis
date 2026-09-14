from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.projects.braaeg001 import gerar_minimapa_cambevas_ictiofauna as base


SOURCE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Migracao\Fonseca\Opyta_ictiofauna_banco_dados_mar-jul_26-260813.xlsx"
)

base.PROJECT_CODE = "BRACED001"
base.PRODUCT_STEM = "mini_mapa_especies_indicadoras_cpuen_ictiofauna"
base.PRODUCT_CODE = "mini_mapa_especies_indicadoras_cpuen"
base.A4_LANDSCAPE = (16.54, 11.69)
base.SPECIES = [
    "Brycon opalinus",
    "Pareiorhaphis scutula",
    "Trichomycterus brasiliensis",
]
base.SPECIES_LABELS = {
    "Brycon opalinus": r"$\it{Brycon\ opalinus}$" + "\nAmeaçada",
    "Pareiorhaphis scutula": r"$\it{Pareiorhaphis\ scutula}$" + "\nBentônica",
    "Trichomycterus brasiliensis": r"$\it{Trichomycterus\ brasiliensis}$" + "\nBentônica",
}
base.CAMPAIGNS = ["C001-2026-03-CH", "C002-2026-06-SC"]
base.OUTPUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\Produtos\Resultados\Fonseca"
)
base.AUDIT_DIR = Path(__file__).resolve().parent
base.KMZ_PATH = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\Cedro Mineração\geo\Geo_Fonseca\Anteriores\Hidrografia - Fonseca.kmz"
)
base.LABEL_OFFSETS = {
    "MA-01-01": (-0.0060, -0.0028),
    "MA-01-02": (-0.0045, 0.0038),
    "MA-01-03": (0.0028, 0.0030),
    "MA-02-04": (0.0007, 0.0012),
    "MA-02-05": (0.0008, -0.0012),
    "MA-02-06": (-0.0030, 0.0009),
    "MA-03-07": (0.0030, 0.0025),
    "MA-03-08": (-0.0050, 0.0025),
    "MA-03-09": (0.0012, -0.0030),
    "MA-04-10": (0.0020, 0.0020),
    "MA-04-11": (-0.0050, 0.0020),
    "MA-04-12": (0.0020, -0.0027),
    "MA-05-13": (0.0008, 0.0011),
    "MA-05-14": (0.0020, 0.0020),
    "MA-05-15": (0.0020, -0.0020),
    "MA-06-16": (0.0010, -0.0010),
    "MA-06-17": (0.0020, 0.0020),
    "MA-06-18": (0.0020, -0.0020),
}
base.source_workbook = lambda: SOURCE


def campaign_label(campaign: str) -> str:
    if campaign == "C001-2026-03-CH":
        return "C01-Chuva"
    if campaign == "C002-2026-06-SC":
        return "C02-Seca"
    return campaign


base.campaign_label = campaign_label


if __name__ == "__main__":
    raise SystemExit(base.main())
