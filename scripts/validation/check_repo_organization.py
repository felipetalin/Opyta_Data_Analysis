from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SCRIPT_ROOT_ALLOWLIST = {
    "_compat.py",
    "run_pipeline.py",
    "gerar_conformidade_sam_etapa2.py",
    "gerar_b3_grafico_por_parametro.py",
    "gerar_b4_pct_violacao.py",
    "gerar_b5_iqa_cetesb.py",
    "gerar_b6_iet_lamparelli.py",
    "gerar_b7_iqasb_parcial.py",
    "gerar_b8_mpelq.py",
    "gerar_b9_sazonal.py",
    "gerar_b11_sintese.py",
    "gerar_piloto_coliformes_etapa3.py",
    "gerar_resumo_tecnico.py",
}

OPERATION_STATES = {
    "intake",
    "validating",
    "awaiting_data_approval",
    "registering_species",
    "awaiting_species_approval",
    "ready_to_migrate",
    "migrating",
    "consolidating",
    "configuring_analysis",
    "awaiting_analysis_approval",
    "generating_products",
    "reviewing_outputs",
    "reviewing_layout",
    "review_planned",
    "review_scoping",
    "awaiting_review_scope_approval",
    "revising_data",
    "revising_taxonomy",
    "revising_analysis",
    "revising_text",
    "revising_layout",
    "revising_package",
    "validating_revision",
    "awaiting_revision_approval",
    "review_completed",
    "completed",
    "blocked",
}


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str | None = None


def repo_root_from(start: Path) -> Path:
    for parent in start.resolve().parents:
        if (parent / "src" / "opyta_analysis").exists():
            return parent
    raise RuntimeError("Repository root not found from script path.")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def is_wrapper(path: Path) -> bool:
    if path.suffix.lower() != ".py":
        return False
    text = read_text(path)
    return "from _compat import run_script" in text and "run_script(" in text


def files_under(path: Path, suffixes: set[str] | None = None) -> list[Path]:
    if not path.exists():
        return []
    files = [item for item in path.rglob("*") if item.is_file()]
    if suffixes is None:
        return files
    return [item for item in files if item.suffix.lower() in suffixes]


def dirs_under(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [item for item in path.iterdir() if item.is_dir()]


def count_by_parent(files: Iterable[Path], base: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file_path in files:
        try:
            key = file_path.relative_to(base).parts[0]
        except ValueError:
            key = "."
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def normalized_stem(path: Path) -> str:
    return path.stem.lower().replace("-", "_")


def collect_report(root: Path) -> dict[str, object]:
    scripts_dir = root / "scripts"
    configs_projects = root / "configs" / "projects"
    docs_dir = root / "docs"
    control_center_dir = docs_dir / "control_center"
    operations_dir = control_center_dir / "operations"
    reviews_dir = control_center_dir / "reviews"
    registry_dir = docs_dir / "registry"
    docs_projects = root / "docs" / "projects"
    outputs_projects = root / "outputs" / "_project_scripts"
    catalog_path = scripts_dir / "SCRIPT_CATALOG.md"
    required_docs = [
        root / "AGENTS.md",
        docs_dir / "README.md",
        control_center_dir / "README.md",
        control_center_dir / "WORKFLOW.md",
        control_center_dir / "REVIEW_WORKFLOW.md",
        control_center_dir / "ACTIVE_OPERATIONS.md",
        operations_dir / "README.md",
        reviews_dir / "README.md",
        control_center_dir / "PROJECTS.md",
        control_center_dir / "PORTFOLIO.md",
        control_center_dir / "LEARNING_SYSTEM.md",
        control_center_dir / "NAMING_STANDARD.md",
        docs_dir / "templates" / "operation_record_template.md",
        docs_dir / "templates" / "review_record_template.md",
    ]
    registry_files = [
        registry_dir / "project_registry.json",
        registry_dir / "pattern_registry.json",
        registry_dir / "portfolio_registry.json",
    ]

    all_script_files = files_under(scripts_dir, {".py", ".ps1", ".sql"})
    python_files = [path for path in all_script_files if path.suffix.lower() == ".py"]
    root_files = [path for path in scripts_dir.iterdir() if path.is_file()]
    root_python = [path for path in root_files if path.suffix.lower() == ".py"]
    wrappers = [path for path in root_python if is_wrapper(path)]
    root_regular = [
        path for path in root_python
        if not is_wrapper(path) and path.name not in SCRIPT_ROOT_ALLOWLIST
    ]

    project_script_dirs = dirs_under(scripts_dir / "projects")
    migration_dirs = dirs_under(scripts_dir / "migrations")
    maintenance_dirs = dirs_under(scripts_dir / "maintenance")
    prototype_files = files_under(scripts_dir / "prototypes", {".py", ".ps1", ".sql"})
    validation_files = files_under(scripts_dir / "validation", {".py", ".ps1", ".sql"})
    run_files = files_under(scripts_dir / "run", {".py", ".ps1", ".sql"})

    recipes = files_under(configs_projects, {".json"})
    project_docs = files_under(docs_projects, {".md"})
    output_project_dirs = dirs_under(outputs_projects)
    operation_files = [
        path
        for path in files_under(operations_dir, {".md"})
        if path.name.lower() != "readme.md"
    ]
    review_files = [
        path
        for path in files_under(reviews_dir, {".md"})
        if path.name.lower() != "readme.md"
    ]

    catalog_text = read_text(catalog_path).lower() if catalog_path.exists() else ""
    findings: list[Finding] = []

    if not catalog_path.exists():
        findings.append(Finding("error", "missing_catalog", "scripts/SCRIPT_CATALOG.md not found."))

    for path in required_docs:
        if not path.exists():
            findings.append(
                Finding(
                    "warning",
                    "missing_control_center_doc",
                    "Required Knowledge Hub/Control Center document is missing.",
                    rel(path, root),
                )
            )

    loaded_registries: dict[str, dict] = {}
    for path in registry_files:
        if not path.exists():
            findings.append(
                Finding(
                    "warning",
                    "missing_registry",
                    "Required registry JSON is missing.",
                    rel(path, root),
                )
            )
            continue
        try:
            loaded_registries[path.name] = json.loads(read_text(path))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "invalid_registry_json",
                    f"Registry is not valid JSON: {exc}",
                    rel(path, root),
                )
            )

    for path in root_regular:
        findings.append(
            Finding(
                "warning",
                "root_script_without_wrapper",
                "Root script is not a compatibility wrapper and is not in the allowlist.",
                rel(path, root),
            )
        )

    for operation in operation_files:
        text = read_text(operation)
        lower_text = text.lower()
        required_markers = {
            "operation_missing_project": "- projeto:",
            "operation_missing_state": "- estado atual:",
            "operation_missing_next_action": "- proxima acao:",
            "operation_missing_progress": "## progresso",
            "operation_missing_gates": "## gates",
        }
        for code, marker in required_markers.items():
            if marker not in lower_text:
                findings.append(
                    Finding(
                        "warning",
                        code,
                        f"Operation record is missing required marker: {marker}",
                        rel(operation, root),
                    )
                )

        state = None
        for line in text.splitlines():
            if line.strip().lower().startswith("- estado atual:"):
                state = line.split(":", 1)[1].strip().strip("`")
                break
        if state and state not in OPERATION_STATES:
            findings.append(
                Finding(
                    "warning",
                    "invalid_operation_state",
                    f"Operation state is not defined in Control Center workflow: {state}",
                    rel(operation, root),
                )
            )

    for review in review_files:
        text = read_text(review)
        lower_text = text.lower()
        required_markers = {
            "review_missing_project": "- projeto:",
            "review_missing_source_operation": "- operacao de origem:",
            "review_missing_state": "- estado atual:",
            "review_missing_scope": "## escopo",
            "review_missing_baseline": "## linha de base",
            "review_missing_progress": "## progresso",
            "review_missing_gate_r": "## gate r",
        }
        for code, marker in required_markers.items():
            if marker not in lower_text:
                findings.append(
                    Finding(
                        "warning",
                        code,
                        f"Review record is missing required marker: {marker}",
                        rel(review, root),
                    )
                )

        state = None
        for line in text.splitlines():
            if line.strip().lower().startswith("- estado atual:"):
                state = line.split(":", 1)[1].strip().strip("`")
                break
        if state and state not in OPERATION_STATES:
            findings.append(
                Finding(
                    "warning",
                    "invalid_review_state",
                    f"Review state is not defined in Control Center workflow: {state}",
                    rel(review, root),
                )
            )

    for project_dir in project_script_dirs:
        name = project_dir.name.lower()
        if name not in catalog_text:
            findings.append(
                Finding(
                    "warning",
                    "project_dir_not_in_catalog",
                    "Project script folder is not mentioned in SCRIPT_CATALOG.md.",
                    rel(project_dir, root),
                )
            )

    doc_stems = {normalized_stem(path) for path in project_docs}
    recipe_stems = {normalized_stem(path) for path in recipes}
    for recipe in recipes:
        stem = normalized_stem(recipe)
        if stem not in doc_stems:
            findings.append(
                Finding(
                    "warning",
                    "recipe_without_project_doc",
                    "Project recipe has no matching docs/projects note.",
                    rel(recipe, root),
                )
            )

    for doc in project_docs:
        stem = normalized_stem(doc)
        if stem not in recipe_stems:
            findings.append(
                Finding(
                    "info",
                    "project_doc_without_recipe",
                    "Project note has no matching recipe yet.",
                    rel(doc, root),
                )
            )

    for recipe in recipes:
        try:
            recipe_data = json.loads(read_text(recipe))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "invalid_project_recipe_json",
                    f"Project recipe is not valid JSON: {exc}",
                    rel(recipe, root),
                )
            )
            continue
        if not recipe_data.get("canonical_key"):
            findings.append(
                Finding(
                    "warning",
                    "recipe_without_canonical_key",
                    "Project recipe should declare canonical_key based on Supabase code and name.",
                    rel(recipe, root),
                )
            )

    project_registry = loaded_registries.get("project_registry.json", {})
    registered_project_paths = set()
    for item in project_registry.get("projects", []):
        for field in ("recipes", "docs", "scripts", "audit"):
            for value in item.get(field, []) or []:
                registered_project_paths.add(str(value).replace("\\", "/"))
                path = root / value
                if not path.exists():
                    findings.append(
                        Finding(
                            "info",
                            "registered_path_missing",
                            f"Registered {field} path does not exist yet.",
                            str(value),
                        )
                    )

    for recipe in recipes:
        recipe_rel = rel(recipe, root)
        if recipe_rel not in registered_project_paths:
            findings.append(
                Finding(
                    "warning",
                    "recipe_not_in_project_registry",
                    "Project recipe is not listed in project_registry.json.",
                    recipe_rel,
                )
            )

    summary = {
        "projects": {
            "recipes": len(recipes),
            "project_docs": len(project_docs),
            "script_project_dirs": len(project_script_dirs),
            "output_project_dirs": len(output_project_dirs),
            "registry_projects": len(project_registry.get("projects", [])),
        },
        "knowledge_hub": {
            "control_center_docs": len(files_under(control_center_dir, {".md"})),
            "operation_records": len(operation_files),
            "review_records": len(review_files),
            "registry_files": len([path for path in registry_files if path.exists()]),
            "template_files": len(files_under(docs_dir / "templates", {".md"})),
            "pattern_docs": len(files_under(docs_dir / "patterns", {".md"})),
        },
        "scripts": {
            "total_py_ps1_sql": len(all_script_files),
            "python_total": len(python_files),
            "root_python": len(root_python),
            "root_wrappers": len(wrappers),
            "root_regular_not_allowlisted": len(root_regular),
            "projects": len(files_under(scripts_dir / "projects", {".py", ".ps1", ".sql"})),
            "migrations": len(files_under(scripts_dir / "migrations", {".py", ".ps1", ".sql"})),
            "maintenance": len(files_under(scripts_dir / "maintenance", {".py", ".ps1", ".sql"})),
            "prototypes": len(prototype_files),
            "validation": len(validation_files),
            "run": len(run_files),
        },
        "script_project_dirs": {
            path.name: len(files_under(path, {".py", ".ps1", ".sql"}))
            for path in project_script_dirs
        },
        "migration_dirs": {
            path.name: len(files_under(path, {".py", ".ps1", ".sql"}))
            for path in migration_dirs
        },
        "maintenance_dirs": {
            path.name: len(files_under(path, {".py", ".ps1", ".sql"}))
            for path in maintenance_dirs
        },
        "organized_script_counts": count_by_parent(
            files_under(scripts_dir, {".py", ".ps1", ".sql"}),
            scripts_dir,
        ),
        "findings": [asdict(finding) for finding in findings],
    }
    return summary


def print_human(report: dict[str, object]) -> None:
    projects = report["projects"]
    scripts = report["scripts"]
    findings = report["findings"]

    print("Opyta organization check")
    print("")
    print("Projects")
    for key, value in projects.items():
        print(f"- {key}: {value}")

    print("")
    print("Knowledge hub")
    for key, value in report["knowledge_hub"].items():
        print(f"- {key}: {value}")

    print("")
    print("Scripts")
    for key, value in scripts.items():
        print(f"- {key}: {value}")

    print("")
    print("Project script folders")
    for key, value in report["script_project_dirs"].items():
        print(f"- {key}: {value}")

    print("")
    print("Migration folders")
    for key, value in report["migration_dirs"].items():
        print(f"- {key}: {value}")

    print("")
    print("Findings")
    if not findings:
        print("- OK: no organization findings.")
        return
    for item in findings:
        path = f" ({item['path']})" if item.get("path") else ""
        print(f"- {item['level'].upper()} {item['code']}: {item['message']}{path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Opyta repository organization rules.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of the human summary.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the JSON report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 if warnings or errors are found.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root_from(Path(__file__))
    report = collect_report(root)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)

    findings = report["findings"]
    has_strict_findings = any(item["level"] in {"warning", "error"} for item in findings)
    return 1 if args.strict and has_strict_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
