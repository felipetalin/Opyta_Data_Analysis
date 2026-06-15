from __future__ import annotations

import runpy
import sys
from pathlib import Path


def run_script(relative_target: str) -> None:
    """Run a moved script while keeping old root-level entrypoints working."""
    scripts_root = Path(__file__).resolve().parent
    target = scripts_root / relative_target
    if not target.exists():
        raise FileNotFoundError(f"Compatibility target not found: {target}")

    repo_root = scripts_root.parent
    for path in [target.parent, scripts_root, repo_root / "src"]:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
