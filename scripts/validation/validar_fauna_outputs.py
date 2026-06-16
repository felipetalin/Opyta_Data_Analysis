#!/usr/bin/env python
"""Post-run audit for fauna pipeline outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from opyta_analysis.fauna.audit import audit_projects  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate fauna output manifests and deliverables.")
    parser.add_argument(
        "--audit-root",
        type=Path,
        default=REPO_ROOT / "outputs" / "_project_scripts",
        help="Root folder containing project audit subfolders.",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Optional project audit folder name, for example FERSAM001__sam_metais_diagnostico.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional manifest path. Defaults to fauna_inventory.json inside the project folder.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return exit code 1 when warnings are present.",
    )
    return parser.parse_args()


def _default_output(audit_root: Path, project: str | None) -> Path:
    if project:
        return audit_root / project / "fauna_inventory.json"
    return audit_root / "fauna_audit_manifest.json"


def main() -> int:
    args = parse_args()
    manifest = audit_projects(args.audit_root, project=args.project, repo_root=REPO_ROOT)
    output = args.output or _default_output(args.audit_root, args.project)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    status = manifest["status"]
    summary = manifest["summary"]
    print(
        "[fauna-audit] "
        f"{status} -> {output} "
        f"(projects={summary['projects_count']}, errors={summary['errors_count']}, warnings={summary['warnings_count']})"
    )

    for error in manifest.get("errors", [])[:20]:
        print(f"  [ERROR] {error}")
    for warning in manifest.get("warnings", [])[:20]:
        print(f"  [WARN] {warning}")

    if status == "ERROR":
        return 1
    if args.strict_warnings and summary["warnings_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
