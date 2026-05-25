from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from opyta_analysis.audit_utils import build_file_manifest, discover_deliverables, git_context


RULESET_VERSION = "fauna_audit_v1.0"

FAUNA_PIPELINES = {
    "zoobentos",
    "fitoplancton",
    "zooplancton",
    "ictio",
    "ictio_partial",
    "mastofauna",
    "mastofauna_mon",
    "mastofauna_monitoramento",
    "primatas",
    "herpetofauna",
    "avifauna",
    "macrofitas",
}

FAUNA_GROUP_HINTS = {
    "zoobentos",
    "fitoplancton",
    "zooplancton",
    "ictio",
    "ictiofauna",
    "mastofauna",
    "primatas",
    "herpetofauna",
    "avifauna",
    "macrofitas",
}


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _normalize(value: object) -> str:
    text = "" if value is None else str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _status(errors: list[str], warnings: list[str]) -> str:
    if errors:
        return "ERROR"
    if warnings:
        return "OK_WITH_WARNINGS"
    return "OK"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _coerce_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def is_fauna_metadata(metadata: dict[str, Any]) -> bool:
    pipeline = _normalize(metadata.get("pipeline"))
    group = _normalize(metadata.get("group"))
    return pipeline in FAUNA_PIPELINES or group in FAUNA_GROUP_HINTS


def audit_execution_metadata(metadata_path: Path) -> dict[str, Any]:
    metadata = _load_json(metadata_path)
    errors: list[str] = []
    warnings: list[str] = []

    output_dir_text = str(metadata.get("output_dir") or "")
    output_dir = Path(output_dir_text) if output_dir_text else None
    generated_files = [str(path) for path in _as_list(metadata.get("generated_files"))]
    generated_files_count = _coerce_int(metadata.get("generated_files_count"))
    rows_loaded = _coerce_int(metadata.get("rows_loaded"))
    executed_blocks = _as_list(metadata.get("executed_blocks"))

    if generated_files_count is not None and generated_files_count != len(generated_files):
        errors.append(f"generated_files_count_mismatch={generated_files_count}!={len(generated_files)}")

    if output_dir is None:
        errors.append("missing_output_dir_in_metadata")
        deliverable_inventory: list[dict[str, object]] = []
    elif not output_dir.exists():
        errors.append(f"output_dir_missing={output_dir}")
        deliverable_inventory = []
    else:
        deliverable_inventory = discover_deliverables(output_dir)

    metadata_file_checks = _as_list(metadata.get("generated_file_checks"))
    generated_file_checks = (
        metadata_file_checks
        if metadata_file_checks
        else build_file_manifest(generated_files, base_dir=output_dir if output_dir and output_dir.exists() else None)
    )
    missing_generated = [str(item.get("path")) for item in generated_file_checks if not item.get("exists")]
    if generated_files and missing_generated:
        errors.append(f"missing_generated_files={len(missing_generated)}")

    if rows_loaded is None:
        warnings.append("rows_loaded_missing")
    elif rows_loaded <= 0:
        warnings.append(f"rows_loaded_non_positive={rows_loaded}")

    if not executed_blocks:
        warnings.append("executed_blocks_empty")

    if not generated_files:
        warnings.append("generated_files_empty")
        if deliverable_inventory:
            warnings.append(f"output_dir_has_deliverables_not_linked_in_metadata={len(deliverable_inventory)}")

    if "git" not in metadata:
        warnings.append("metadata_without_git_context")

    if "generated_file_checks" not in metadata:
        warnings.append("metadata_without_generated_file_hashes")

    return {
        "status": _status(errors, warnings),
        "metadata_path": str(metadata_path),
        "audit_dir": str(metadata_path.parent),
        "project_id": metadata.get("project_id"),
        "group": metadata.get("group"),
        "pipeline": metadata.get("pipeline"),
        "client": metadata.get("client"),
        "block": metadata.get("block"),
        "executed_at": metadata.get("executed_at"),
        "runner_version": metadata.get("runner_version"),
        "rows_loaded": rows_loaded,
        "executed_blocks": executed_blocks,
        "output_dir": output_dir_text,
        "output_dir_exists": bool(output_dir and output_dir.exists()),
        "generated_files_count": len(generated_files),
        "generated_files_declared_count": generated_files_count,
        "generated_files_missing_count": len(missing_generated),
        "generated_file_checks": generated_file_checks,
        "deliverable_inventory_count": len(deliverable_inventory),
        "deliverable_inventory": deliverable_inventory,
        "errors": errors,
        "warnings": warnings,
    }


def audit_project(project_dir: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    groups: list[dict[str, Any]] = []
    skipped_metadata: list[str] = []

    if not project_dir.exists():
        errors.append(f"project_audit_dir_missing={project_dir}")
    else:
        for metadata_path in sorted(project_dir.glob("*/execution_metadata.json")):
            try:
                metadata = _load_json(metadata_path)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid_metadata_json={metadata_path}: {exc}")
                continue

            if not is_fauna_metadata(metadata):
                skipped_metadata.append(str(metadata_path))
                continue

            group_audit = audit_execution_metadata(metadata_path)
            groups.append(group_audit)
            errors.extend(f"{group_audit.get('group')}: {err}" for err in group_audit.get("errors", []))
            warnings.extend(f"{group_audit.get('group')}: {warn}" for warn in group_audit.get("warnings", []))

    if not groups and not errors:
        warnings.append("no_fauna_execution_metadata_found")

    project = project_dir.name
    manifest: dict[str, Any] = {
        "generated_at": _utc_timestamp(),
        "status": _status(errors, warnings),
        "ruleset_version": RULESET_VERSION,
        "project": project,
        "project_audit_dir": str(project_dir),
        "git": git_context(repo_root) if repo_root else None,
        "summary": {
            "groups_count": len(groups),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "skipped_metadata_count": len(skipped_metadata),
        },
        "groups": groups,
        "skipped_metadata": skipped_metadata,
        "errors": errors,
        "warnings": warnings,
    }
    return manifest


def audit_projects(audit_root: Path, *, project: str | None = None, repo_root: Path | None = None) -> dict[str, Any]:
    if not audit_root.exists():
        projects: list[dict[str, Any]] = []
        errors = [f"audit_root_missing={audit_root}"]
        warnings: list[str] = []
        return {
            "generated_at": _utc_timestamp(),
            "status": "ERROR",
            "ruleset_version": RULESET_VERSION,
            "audit_root": str(audit_root),
            "git": git_context(repo_root) if repo_root else None,
            "summary": {
                "projects_count": 0,
                "errors_count": len(errors),
                "warnings_count": 0,
            },
            "projects": projects,
            "errors": errors,
            "warnings": warnings,
        }

    project_dirs = [audit_root / project] if project else sorted(path for path in audit_root.iterdir() if path.is_dir())
    projects = [audit_project(project_dir, repo_root=repo_root) for project_dir in project_dirs]
    errors = [err for item in projects for err in item.get("errors", [])]
    warnings = [warn for item in projects for warn in item.get("warnings", [])]
    return {
        "generated_at": _utc_timestamp(),
        "status": _status(errors, warnings),
        "ruleset_version": RULESET_VERSION,
        "audit_root": str(audit_root),
        "git": git_context(repo_root) if repo_root else None,
        "summary": {
            "projects_count": len(projects),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "projects": projects,
        "errors": errors,
        "warnings": warnings,
    }
