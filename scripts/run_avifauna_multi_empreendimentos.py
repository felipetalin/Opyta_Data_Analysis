from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run
import opyta_analysis.pipelines.diagnostico.avifauna as avi_mod


def main() -> int:
    base_out = Path(
        "G:\\Meu Drive\\Opyta\\Clientes\\Clientes\\Clientes\\Itatiaia\\"
        "Guanh\u00e3es Energia\\Resultados e an\u00e1lises\\28_campanha-Abril_26\\Avifauna"
    )
    base_out.mkdir(parents=True, exist_ok=True)

    targets = [
        ("Dores de Guanh\u00e3es", "Dores de Guanh\u00e3es"),
        ("Fortuna II", "Fortuna II"),
        ("Jacar\u00e9", "Jacar\u00e9"),
        ("Senhora do Porto", "Senhora do Porto"),
    ]

    premises = {
        "grupo": "Avifauna",
        "campanha": "C028-2026-04-SC",
        "controle": "\u00c1rea Controle",
        "regra_empreendimento": {
            "CO": "\u00c1rea Controle",
            "DG/RNDG": "Dores de Guanh\u00e3es",
            "FO/RNFO": "Fortuna II",
            "JC/RNJC": "Jacar\u00e9",
            "SP/RNSP": "Senhora do Porto",
        },
        "observacao": (
            "Pontos de Avifauna com id_empreendimento vazio sao classificados "
            "por prefixo do nome do ponto para permitir analises por empreendimento."
        ),
    }
    (base_out / "00_premissas_avifauna_empreendimentos.json").write_text(
        json.dumps(premises, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for pch_name, folder_name in targets:
        out_dir = base_out / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        avi_mod.TARGET_PCH_NAME = pch_name
        avi_mod.TARGET_CONTROL_NAME = "\u00c1rea Controle"

        params = RunParams(
            project_id=165,
            group="Avifauna",
            pipeline="avifauna",
            client="fersam001",
            output_dir=out_dir,
            env_file="G:\\Meu Drive\\Opyta\\Opyta_Data\\.env",
            block="all",
            audit_project_slug="project_165",
        )

        result = run(params=params, config_root=ROOT / "configs")
        status = result.get("status", "unknown")
        generated = len(result.get("details", {}).get("generated_files", []))
        print(f"[{status}] {pch_name} -> {out_dir} | arquivos: {generated}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
