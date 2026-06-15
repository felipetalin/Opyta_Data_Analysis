"""Executa Ictiofauna parcial (campanha C028-2026-05-SC) para os 4 empreendimentos.

Padrao identico a run_herpetofauna_multi_empreendimentos.py e
run_mastofauna_multi_empreendimentos.py: usa RunParams + opyta_analysis.runner.run,
o que aciona tema padrao Gold e gera trilha de auditoria automaticamente.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run
import opyta_analysis.pipelines.diagnostico.ictio_partial as ictio_part_mod


CAMPANHA_ALVO = "C028-2026-05-SC"


def main() -> int:
    base_out = Path(
        r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia"
        r"\Resultados e análises\28_campanha-Abril_26\Ictiofauna"
    )
    base_out.mkdir(parents=True, exist_ok=True)

    targets = [
        ("Dores de Guanhães", "Dores de Guanhães"),
        ("Fortuna II", "Fortuna II"),
        ("Jacaré", "Jacaré"),
        ("Senhora do Porto", "Senhora do Porto"),
    ]

    for pch_name, folder_name in targets:
        out_dir = base_out / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Setar TARGET (PCH alvo + campanha) no modulo antes de cada execucao
        ictio_part_mod.TARGET_PCH_NAME = pch_name
        ictio_part_mod.TARGET_CAMPANHA = CAMPANHA_ALVO

        params = RunParams(
            project_id=165,
            group="Ictiofauna",
            pipeline="ictio_partial",
            client="fersam001",
            output_dir=out_dir,
            env_file=r"G:\Meu Drive\Opyta\Opyta_Data\.env",
            block="all",
            audit_project_slug="project_165",
        )

        result = run(params=params, config_root=ROOT / "configs")
        status = result.get("status", "unknown")
        details = result.get("details", {})
        generated = len(details.get("generated_files", []))
        warning = details.get("warning")
        extra = f" | {warning}" if warning else ""
        print(f"[{status}] {pch_name} -> {out_dir} | arquivos: {generated}{extra}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
