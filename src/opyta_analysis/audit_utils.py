from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_DELIVERABLE_PATTERNS = (
    "*.xlsx",
    "*.xlsm",
    "*.csv",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.json",
)

GENERATED_AUDIT_PREFIXES = (
    "outputs/_project_scripts/",
    "outputs\\_project_scripts\\",
)


def run_git(args: Sequence[str], repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _status_path(line: str) -> str:
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip().strip('"')


def _is_generated_audit_path(line: str) -> bool:
    path = _status_path(line)
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix.replace("\\", "/")) for prefix in GENERATED_AUDIT_PREFIXES)


def git_context(repo_root: Path) -> dict[str, object]:
    status_short = run_git(["status", "--short"], repo_root) or ""
    status_lines = [line for line in status_short.splitlines() if line.strip()]
    source_status_lines = [line for line in status_lines if not _is_generated_audit_path(line)]
    return {
        "branch": run_git(["branch", "--show-current"], repo_root),
        "commit": run_git(["rev-parse", "--short", "HEAD"], repo_root),
        "dirty": bool(source_status_lines),
        "status_short_count": len(source_status_lines),
        "full_dirty": bool(status_lines),
        "full_status_short_count": len(status_lines),
        "ignored_generated_audit_count": len(status_lines) - len(source_status_lines),
    }


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: str | Path, base_dir: Path | None = None) -> dict[str, object]:
    raw_path = Path(path)
    resolved_path = raw_path if raw_path.is_absolute() or base_dir is None else base_dir / raw_path
    record: dict[str, object] = {
        "path": str(resolved_path),
        "exists": resolved_path.exists(),
    }
    if not resolved_path.exists():
        return record

    stat = resolved_path.stat()
    record.update(
        {
            "type": "dir" if resolved_path.is_dir() else "file",
            "size_bytes": stat.st_size if resolved_path.is_file() else None,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat().replace("+00:00", "Z"),
        }
    )
    if resolved_path.is_file():
        record["sha256"] = sha256_file(resolved_path)
    return record


def build_file_manifest(paths: Iterable[str | Path], base_dir: Path | None = None) -> list[dict[str, object]]:
    seen: set[str] = set()
    manifest: list[dict[str, object]] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        manifest.append(file_record(path, base_dir=base_dir))
    return manifest


def discover_deliverables(
    root: str | Path,
    patterns: Sequence[str] = DEFAULT_DELIVERABLE_PATTERNS,
    *,
    recursive: bool = True,
    max_files: int | None = 500,
) -> list[dict[str, object]]:
    root_path = Path(root)
    if not root_path.exists() or not root_path.is_dir():
        return []

    files: dict[str, Path] = {}
    for pattern in patterns:
        iterator = root_path.rglob(pattern) if recursive else root_path.glob(pattern)
        for path in iterator:
            if path.is_file():
                files[str(path)] = path

    ordered = sorted(files.values(), key=lambda p: str(p).lower())
    if max_files is not None:
        ordered = ordered[:max_files]
    return build_file_manifest(ordered)
