from __future__ import annotations

import json
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
import opyta_analysis.pipelines.diagnostico.avifauna as avi_mod


CAMPAIGN = "C029-2026-07-SC"


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
                "avifauna_landscape_width": 8.6,
                "avifauna_landscape_height": 6.8,
                "avifauna_species_label_size": 9.8,
                "avifauna_bar_annotation_size": 9.2,
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


def main() -> int:
    _install_c029_layout_theme()

    base_out = Path(
        os.environ.get(
            "AVIFAUNA_C029_OUTPUT_DIR",
            "G:\\Meu Drive\\Opyta\\Clientes\\Clientes\\Clientes\\Itatiaia\\"
            "Guanhães Energia\\Resultados e análises\\29_campanha_Jul_26\\Avifauna",
        )
    )
    base_out.mkdir(parents=True, exist_ok=True)

    targets = [
        ("Dores de Guanhães", "Dores de Guanhães"),
        ("Fortuna II", "Fortuna II"),
        ("Jacaré", "Jacaré"),
        ("Senhora do Porto", "Senhora do Porto"),
    ]

    premises = {
        "grupo": "Avifauna",
        "campanha": CAMPAIGN,
        "controle": "Área Controle",
        "regra_empreendimento": {
            "CO": "Área Controle",
            "DG/RNDG": "Dores de Guanhães",
            "FO/RNFO": "Fortuna II",
            "JC/RNJC": "Jacaré",
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
        avi_mod.TARGET_CONTROL_NAME = "Área Controle"

        params = RunParams(
            project_id=165,
            group="Avifauna",
            pipeline="avifauna",
            client="fersam001",
            output_dir=out_dir,
            env_file="G:\\Meu Drive\\Opyta\\Opyta_Data\\.env",
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
