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


def git_context(repo_root: Path) -> dict[str, object]:
    status_short = run_git(["status", "--short"], repo_root) or ""
    return {
        "branch": run_git(["branch", "--show-current"], repo_root),
        "commit": run_git(["rev-parse", "--short", "HEAD"], repo_root),
        "dirty": bool(status_short),
        "status_short_count": len([line for line in status_short.splitlines() if line.strip()]),
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
