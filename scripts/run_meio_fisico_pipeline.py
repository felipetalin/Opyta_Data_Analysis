import sys
from opyta_analysis.pipelines.diagnostico import run_meio_fisico_pipeline

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Uso: python scripts/run_meio_fisico_pipeline.py <planilha_path> <codigo_projeto> <nome_projeto> <nome_empresa> [env_file]")
        sys.exit(1)
    planilha_path = sys.argv[1]
    codigo_projeto = sys.argv[2]
    nome_projeto = sys.argv[3]
    nome_empresa = sys.argv[4]
    env_file = sys.argv[5] if len(sys.argv) > 5 else None
    run_meio_fisico_pipeline(planilha_path, codigo_projeto, nome_projeto, nome_empresa, env_file)
