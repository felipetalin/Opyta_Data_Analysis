from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Import ONLY primatas, skip full runner to avoid matplotlib slowdown
import opyta_analysis.pipelines.diagnostico.primatas as primatas_mod


def main() -> int:
    base_out = Path(
        r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\28_campanha-Abril_26\Primatas"
    )
    base_out.mkdir(parents=True, exist_ok=True)

    # Load theme once
    config_path = ROOT / "configs" / "theme_default.json"
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    env_file = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")

    targets = [
        ("Dores de Guanhães", "PCH Dores de Guanhães"),
        ("Fortuna II", "Fortuna II"),
        ("Jacaré", "Jacaré"),
        ("Senhora do Porto", "Senhora do Porto"),
    ]

    for pch_name, folder_name in targets:
        out_dir = base_out / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Set TARGET variables before run
        primatas_mod.TARGET_PCH_NAME = pch_name
        primatas_mod.TARGET_CONTROL_NAME = "Área Controle"

        print(f"\n[RUN] {pch_name} -> {folder_name}")
        try:
            result = primatas_mod.run_primatas_pipeline(
                project_id=165,
                group="primatas",
                theme=theme,
                output_dir=out_dir,
                env_file=env_file,
                block="all",
            )
            files = result.get("generated_files", [])
            print(f"✓ Gerou {len(files)} arquivos:")
            for f in files:
                print(f"  - {Path(f).name}")
        except Exception as e:
            print(f"✗ Erro: {e}")
            return 1

    print("\n✓ Primatas pipeline executado para todos os 4 PCHs!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
