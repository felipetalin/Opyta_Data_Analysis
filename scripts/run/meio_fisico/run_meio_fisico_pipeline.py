
import sys
import json
from pathlib import Path
from opyta_analysis.pipelines.diagnostico import run_meio_fisico_pipeline
from opyta_analysis.config import load_theme

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Uso: python scripts/run_meio_fisico_pipeline.py <planilha_path> <codigo_projeto> <nome_projeto> <nome_empresa> <env_file> <output_dir>")
        sys.exit(1)
    # planilha_path = sys.argv[1]  # ignorado, só para compatibilidade
    codigo_projeto = sys.argv[2]
    nome_projeto = sys.argv[3]
    nome_empresa = sys.argv[4]
    env_file = sys.argv[5]
    output_dir = sys.argv[6] if len(sys.argv) > 6 else f"outputs/_project_scripts/{nome_projeto}/meio_fisico"

    config_root = Path("configs")
    theme = load_theme(config_root, codigo_projeto.lower())
    result = run_meio_fisico_pipeline(
        codigo_projeto=codigo_projeto,
        theme=theme,
        output_dir=Path(output_dir),
        env_file=env_file,
        block="all"
    )
    print("[OK] Pipeline concluído.")
    print(json.dumps(result, indent=2, ensure_ascii=False))
