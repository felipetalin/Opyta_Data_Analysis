import json
import os
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
FINAL = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados\Zoobentos")
os.environ["WSPKIN001_ZOOBENTOS_OUTPUT"] = str(FINAL)
wrapper = runpy.run_path(str(ROOT / "scripts/projects/wspkin001/generate_wspkin001_zoobentos_full.py"), run_name="wspkin001_bentos_wrapper")
reference = ROOT / "outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos/generate_bentos_results_a4_landscape.py"
namespace = wrapper["adapted_namespace"](reference, minimap=False)
audit = json.loads((ROOT / "outputs/_project_scripts/WSPKIN001__kinross_bandeirinhas/zoobentos/20260909T113338_geracao_resultados_zoobentos_a4_paisagem.json").read_text(encoding="utf-8"))
paths = namespace["build_manifest_and_validation"]([], audit["metrics"], "20260909T113338_REV_R01_FINAL")
print([str(path) for path in paths])
