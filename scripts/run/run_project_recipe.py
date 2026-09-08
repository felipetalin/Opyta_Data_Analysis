from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run


def _load_recipe(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Recipe not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an analysis project from configs/projects/*.json")
    parser.add_argument("recipe", help="Recipe path or recipe filename under configs/projects")
    parser.add_argument("--env-file", default=None, help="Optional .env path")
    parser.add_argument("--block", default="all", help="Pipeline block selector")
    parser.add_argument("--group", action="append", default=None, help="Optional group name filter; can be repeated")
    parser.add_argument("--dry-run", action="store_true", help="Print planned runs without executing")
    return parser.parse_args()


def _resolve_recipe(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    candidate = ROOT / "configs" / "projects" / value
    if candidate.exists():
        return candidate
    if not value.endswith(".json"):
        candidate = ROOT / "configs" / "projects" / f"{value}.json"
        if candidate.exists():
            return candidate
    return path


def main() -> int:
    args = parse_args()
    recipe_path = _resolve_recipe(args.recipe)
    recipe = _load_recipe(recipe_path)
    wanted_groups = {group.lower() for group in args.group or []}

    output_root = Path(recipe["output_root"])
    planned = []
    for group_cfg in recipe.get("groups", []):
        group_name = str(group_cfg["group"])
        if wanted_groups and group_name.lower() not in wanted_groups:
            continue
        planned.append(
            {
                "project_id": int(recipe["project_id"]),
                "group": group_name,
                "pipeline": group_cfg["pipeline"],
                "client": recipe["client_config"],
                "output_dir": str(output_root / group_cfg["output_subdir"]),
                "block": args.block,
                "campaigns": group_cfg.get("campaigns", recipe.get("campaigns", [])),
                "pch_target": group_cfg.get("pch_target"),
            }
        )

    if args.dry_run:
        print(json.dumps({"recipe": str(recipe_path), "planned": planned}, ensure_ascii=False, indent=2))
        return 0

    results = []
    for item in planned:
        params = RunParams(
            project_id=item["project_id"],
            group=item["group"],
            pipeline=item["pipeline"],
            client=item["client"],
            output_dir=Path(item["output_dir"]),
            env_file=args.env_file,
            block=item["block"],
            audit_project_slug=recipe.get("audit_project_slug"),
            campaigns=item["campaigns"],
            pch_target=item["pch_target"],
        )
        result = run(params=params, config_root=ROOT / "configs")
        results.append(result)
        if result.get("status") != "ok":
            print(json.dumps({"recipe": str(recipe_path), "results": results}, ensure_ascii=False, indent=2))
            return 1

    print(json.dumps({"recipe": str(recipe_path), "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
