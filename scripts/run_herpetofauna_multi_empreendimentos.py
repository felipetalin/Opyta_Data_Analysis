from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run
import opyta_analysis.pipelines.diagnostico.herpetofauna as herp_mod


def main() -> int:
    base_out = Path(
        r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\28_campanha-Abril_26\Herpetofauna"
    )
    base_out.mkdir(parents=True, exist_ok=True)

    targets = [
        ("Jacaré", "Jacaré"),
        ("Dores de Guanhães", "Dores de Guanhães"),
        ("Fortuna II", "Fortuna II"),
        ("Senhora do Porto", "Senhora do Porto"),
    ]

    for pch_name, folder_name in targets:
        out_dir = base_out / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        herp_mod.TARGET_PCH_NAME = pch_name
        herp_mod.TARGET_CONTROL_NAME = "Área Controle"

        params = RunParams(
            project_id=165,
            group="Herpetofauna",
            pipeline="herpetofauna",
            client="fersam001",
            output_dir=out_dir,
            env_file=r"G:\Meu Drive\Opyta\Opyta_Data\.env",
            block="all",
        )

        result = run(params=params, config_root=ROOT / "configs")
        status = result.get("status", "unknown")
        generated = len(result.get("details", {}).get("generated_files", []))
        print(f"[{status}] {pch_name} -> {out_dir} | arquivos: {generated}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
