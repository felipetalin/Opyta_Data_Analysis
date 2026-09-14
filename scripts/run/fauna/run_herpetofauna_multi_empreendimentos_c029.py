from __future__ import annotations

import os
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
import opyta_analysis.runner as runner_mod
import opyta_analysis.pipelines.diagnostico.herpetofauna as herp_mod


CAMPAIGN = "jul-26"


def _install_c029_layout_theme() -> None:
    original_load_theme = runner_mod.load_theme

    def load_theme_with_c029_layout(config_root: Path, client: str) -> dict:
        theme = original_load_theme(config_root, client)
        theme.update(
            {
                "font_size_base": 11,
                "title_size": 11,
                "label_size": 10,
                "legend_size": 10,
                "annotation_size": 9.5,
                "figsize_standard": [8.6, 6.8],
                "report_landscape_width": 8.6,
                "report_landscape_height": 6.8,
                "report_portrait_width": 7.4,
                "report_portrait_height": 10.1,
                "dendrogram_tick_size": 9.0,
                "dendrogram_linewidth": 1.25,
                "legend_figure_y": 0.975,
                "tight_layout_top": 0.94,
                "tight_layout_bottom": 0.09,
                "preserve_word_caption_margin": True,
                "savefig_pad_inches": 0.08,
                "dpi": 450,
            }
        )
        return theme

    runner_mod.load_theme = load_theme_with_c029_layout


def _default_output_dir() -> Path:
    itatiaia_root = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia")
    project_dir = next(
        path for path in itatiaia_root.iterdir()
        if "Guanh" in path.name and "Energia" in path.name
    )
    return project_dir / "Resultados e análises" / "29_campanha_Jul_26" / "Herpetofauna"


def main() -> int:
    _install_c029_layout_theme()

    base_out = Path(os.environ.get("HERPETOFAUNA_C029_OUTPUT_DIR", str(_default_output_dir())))
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
            audit_project_slug="ITAGUA001__monitoramento_da_fauna",
            campaigns=[CAMPAIGN],
        )

        result = runner_mod.run(params=params, config_root=ROOT / "configs")
        status = result.get("status", "unknown")
        generated = len(result.get("details", {}).get("generated_files", []))
        print(f"[{status}] {pch_name} -> {out_dir} | arquivos: {generated}")
        if status != "ok":
            print(result.get("error") or result.get("details", {}).get("warning"))
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
