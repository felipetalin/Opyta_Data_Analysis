from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class RunParams:
    project_id: int
    group: str
    pipeline: str
    client: str
    output_dir: Path
    env_file: str | None = None
    block: str = "all"


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_theme(config_root: Path, client: str) -> Dict[str, Any]:
    base = _read_json(config_root / "theme_default.json")
    client_cfg_path = config_root / "clients" / f"{client}.json"
    if not client_cfg_path.exists():
        return base

    client_cfg = _read_json(client_cfg_path)
    theme_override = client_cfg.get("theme_override", {})
    merged = {**base, **theme_override}
    return merged
