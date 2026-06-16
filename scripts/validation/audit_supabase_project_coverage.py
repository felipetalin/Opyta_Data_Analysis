from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


def repo_root_from(start: Path) -> Path:
    for parent in start.resolve().parents:
        if (parent / "src" / "opyta_analysis").exists():
            return parent
    raise RuntimeError("Repository root not found from script path.")


ROOT = repo_root_from(Path(__file__))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.supabase_client import get_client, paginate  # noqa: E402


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def normalize_code(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\xa0", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", "", text).upper()


def load_registry(root: Path) -> dict[str, Any]:
    path = root / "docs" / "registry" / "project_registry.json"
    return json.loads(read_text(path))


def registry_codes(registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in registry.get("projects", []):
        supabase = project.get("supabase") or {}
        code = normalize_code(supabase.get("codigo_interno_opyta"))
        if code:
            by_code[code].append(project)
    return dict(by_code)


def excluded_codes(registry: dict[str, Any]) -> set[str]:
    return {
        normalize_code(item.get("codigo_interno_opyta"))
        for item in registry.get("excluded_supabase_codes", [])
        if normalize_code(item.get("codigo_interno_opyta"))
    }


def collect(env_file: str | None) -> dict[str, Any]:
    sb = get_client(env_file)
    rows = paginate(sb, "projetos", select="id_projeto,codigo_interno_opyta,nome_projeto")
    normalized_rows = []
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        item = {
            "id_projeto": row.get("id_projeto"),
            "codigo_interno_opyta_raw": row.get("codigo_interno_opyta"),
            "codigo_interno_opyta_normalized": normalize_code(row.get("codigo_interno_opyta")),
            "nome_projeto": row.get("nome_projeto"),
        }
        normalized_rows.append(item)
        by_code[item["codigo_interno_opyta_normalized"]].append(item)

    registry = load_registry(ROOT)
    registered = registry_codes(registry)
    excluded = excluded_codes(registry)

    supabase_codes = set(by_code) - excluded
    registry_codes_set = set(registered)
    missing_in_registry = sorted(supabase_codes - registry_codes_set)
    missing_in_supabase = sorted(registry_codes_set - supabase_codes)
    duplicate_supabase_codes = {
        code: items for code, items in sorted(by_code.items())
        if code and len(items) > 1
    }
    duplicate_registry_codes = {
        code: items for code, items in sorted(registered.items())
        if code and len(items) > 1
    }

    return {
        "schema_version": "1.0",
        "supabase_rows": len(normalized_rows),
        "supabase_unique_codes": len(supabase_codes),
        "registry_projects_with_supabase_code": sum(len(items) for items in registered.values()),
        "registry_unique_codes": len(registry_codes_set),
        "excluded_supabase_codes": sorted(excluded),
        "missing_in_registry": missing_in_registry,
        "missing_in_supabase": missing_in_supabase,
        "duplicate_supabase_codes": duplicate_supabase_codes,
        "duplicate_registry_codes": duplicate_registry_codes,
        "supabase_projects": sorted(normalized_rows, key=lambda item: (item["codigo_interno_opyta_normalized"], item["id_projeto"] or 0)),
    }


def print_human(report: dict[str, Any]) -> None:
    print("Supabase project coverage")
    print("")
    print(f"- Supabase rows: {report['supabase_rows']}")
    print(f"- Supabase unique normalized codes: {report['supabase_unique_codes']}")
    print(f"- Registry unique Supabase codes: {report['registry_unique_codes']}")
    print(f"- Excluded Supabase codes: {', '.join(report['excluded_supabase_codes']) or 'none'}")

    print("")
    print("Missing in registry")
    if report["missing_in_registry"]:
        for code in report["missing_in_registry"]:
            print(f"- {code}")
    else:
        print("- OK")

    print("")
    print("Registry codes missing in Supabase")
    if report["missing_in_supabase"]:
        for code in report["missing_in_supabase"]:
            print(f"- {code}")
    else:
        print("- OK")

    print("")
    print("Duplicate Supabase codes")
    if report["duplicate_supabase_codes"]:
        for code, items in report["duplicate_supabase_codes"].items():
            ids = ", ".join(str(item["id_projeto"]) for item in items)
            print(f"- {code}: id_projeto={ids}")
    else:
        print("- OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Supabase public.projetos with project_registry.json.")
    parser.add_argument("--env-file", default=str(ROOT / ".env"), help="Path to .env with Supabase credentials.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human summary.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    parser.add_argument("--strict", action="store_true", help="Return exit code 1 when missing or duplicate project codes are found.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = collect(args.env_file)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)

    has_issue = bool(
        report["missing_in_registry"]
        or report["missing_in_supabase"]
        or report["duplicate_supabase_codes"]
        or report["duplicate_registry_codes"]
    )
    return 1 if args.strict and has_issue else 0


if __name__ == "__main__":
    raise SystemExit(main())
