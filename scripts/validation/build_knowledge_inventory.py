from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class DocItem:
    path: str
    title: str
    area: str


def repo_root_from(start: Path) -> Path:
    for parent in start.resolve().parents:
        if (parent / "src" / "opyta_analysis").exists():
            return parent
    raise RuntimeError("Repository root not found from script path.")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def title_from_markdown(path: Path) -> str:
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("_", " ").title()


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def files(path: Path, suffix: str | None = None) -> list[Path]:
    if not path.exists():
        return []
    found = [item for item in path.rglob("*") if item.is_file()]
    if suffix:
        found = [item for item in found if item.suffix.lower() == suffix.lower()]
    return sorted(found)


def dirs(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([item for item in path.iterdir() if item.is_dir()])


def docs_inventory(root: Path) -> list[DocItem]:
    docs_root = root / "docs"
    items: list[DocItem] = []
    for path in files(docs_root, ".md"):
        relative = rel(path, root)
        parts = path.relative_to(docs_root).parts
        area = parts[0] if len(parts) > 1 else "legacy_root"
        items.append(DocItem(path=relative, title=title_from_markdown(path), area=area))
    return items


def project_output_summary(root: Path) -> list[dict[str, Any]]:
    base = root / "outputs" / "_project_scripts"
    summary = []
    for project_dir in dirs(base):
        group_dirs = dirs(project_dir)
        run_metadata = files(project_dir, ".json")
        reproducers = [path for path in files(project_dir, ".py") if path.name.endswith("_run_this_analysis.py") or path.name == "_run_this_analysis.py"]
        summary.append(
            {
                "slug": project_dir.name,
                "path": rel(project_dir, root),
                "groups": [item.name for item in group_dirs],
                "metadata_json_count": len(run_metadata),
                "reproducer_count": len(reproducers),
            }
        )
    return summary


def collect(root: Path) -> dict[str, Any]:
    registry_dir = root / "docs" / "registry"
    project_registry = load_json(registry_dir / "project_registry.json")
    pattern_registry = load_json(registry_dir / "pattern_registry.json")
    portfolio_registry = load_json(registry_dir / "portfolio_registry.json")
    docs = docs_inventory(root)

    scripts_projects = {
        project_dir.name: len(files(project_dir, ".py"))
        for project_dir in dirs(root / "scripts" / "projects")
    }

    report = {
        "schema_version": "1.0",
        "counts": {
            "docs_total": len(docs),
            "docs_legacy_root": len([item for item in docs if item.area == "legacy_root"]),
            "docs_projects": len([item for item in docs if item.area == "projects"]),
            "docs_patterns": len([item for item in docs if item.area == "patterns"]),
            "docs_control_center": len([item for item in docs if item.area == "control_center"]),
            "registry_projects": len(project_registry.get("projects", [])),
            "registry_patterns": len(pattern_registry.get("patterns", [])),
            "registry_portfolio_cases": len(portfolio_registry.get("cases", [])),
            "project_script_dirs": len(scripts_projects),
            "output_project_dirs": len(project_output_summary(root)),
        },
        "docs": [asdict(item) for item in docs],
        "project_registry": project_registry,
        "pattern_registry": pattern_registry,
        "portfolio_registry": portfolio_registry,
        "scripts_projects": scripts_projects,
        "outputs_project_scripts": project_output_summary(root),
    }
    return report


def print_human(report: dict[str, Any]) -> None:
    print("Opyta knowledge inventory")
    print("")
    print("Counts")
    for key, value in report["counts"].items():
        print(f"- {key}: {value}")

    print("")
    print("Projects")
    for project in report["project_registry"].get("projects", []):
        supabase = project.get("supabase") or {}
        code = supabase.get("codigo_interno_opyta", "UNMAPPED")
        name = supabase.get("nome_projeto", project["canonical_key"])
        print(f"- {project['canonical_key']} | {code} | {project['status']} | {name}")

    print("")
    print("Patterns")
    for pattern in report["pattern_registry"].get("patterns", []):
        print(f"- {pattern['key']} | {pattern['status']} | {pattern['name']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Opyta knowledge inventory.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human summary.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from(Path(__file__))
    report = collect(root)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
