from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Any

from opyta_analysis.config import RunParams, load_theme
from opyta_analysis.pipelines import (
    # Diagnóstico
    run_meio_fisico_pipeline,
    run_meio_fisico_xlsx_pipeline,
    run_fitoplancton_pipeline,
    run_ictio_pipeline,
    run_zoobentos_pipeline,
    run_zooplancton_pipeline,
    run_macrofitas_pipeline,
    run_mastofauna_pipeline,
    run_primatas_pipeline,
    run_herpetofauna_pipeline,
    run_avifauna_pipeline,
    # Monitoramento
    run_mastofauna_monitoring_pipeline,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _slug(value: str) -> str:
    safe = [c.lower() if c.isalnum() else "_" for c in value]
    return "".join(safe).strip("_") or "unknown"


def _get_project_audit_dir(params: RunParams, config_root: Path, details: Dict[str, Any]) -> Path:
    root = config_root.parent
    project_name = details.get("project_name")
    project_folder = _slug(project_name) if project_name else f"project_{params.project_id}"
    group_folder = _slug(params.group)
    audit_dir = root / "outputs" / "_project_scripts" / project_folder / group_folder
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir


def _generate_execution_metadata(
    params: RunParams,
    result: Dict[str, Any],
    config_root: Path,
    audit_dir: Path,
    run_id: str,
) -> str:
    """Generate and save execution metadata JSON for audit trail and reproducibility."""
    details = result.get("details", {})
    campaigns = details.get("campaigns", [])
    points = details.get("points", [])
    generated_files = details.get("generated_files", [])

    metadata = {
        "executed_at": _utc_now().isoformat().replace("+00:00", "Z"),
        "runner_version": "1.1",
        "project_id": params.project_id,
        "group": params.group,
        "pipeline": params.pipeline,
        "client": params.client,
        "block": params.block,
        "rows_loaded": details.get("rows_loaded", 0),
        "executed_blocks": details.get("executed_blocks", []),
        "campaigns": campaigns,
        "campaigns_count": len(campaigns) if isinstance(campaigns, list) else None,
        "points": points,
        "points_count": len(points) if isinstance(points, list) else None,
        "output_dir": str(params.output_dir),
        "generated_files_count": len(generated_files),
        "generated_files": generated_files,
        "config_root": str(config_root),
        "audit_dir": str(audit_dir),
    }

    metadata_file = audit_dir / f"{run_id}_execution_metadata.json"
    latest_metadata_file = audit_dir / "execution_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    with open(latest_metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    return str(metadata_file)


def _generate_reproducer_script(params: RunParams, config_root: Path, audit_dir: Path, run_id: str) -> str:
    """Generate a standalone reproducer script for future re-execution."""
    src_path = (config_root.parent / "src").resolve()
    default_output_dir = params.output_dir.resolve()
    config_root_resolved = config_root.resolve()
    group_literal = repr(params.group)
    pipeline_literal = repr(params.pipeline)
    client_literal = repr(params.client)
    env_file_literal = repr(params.env_file)
    block_literal = repr(params.block)

    script_content = f'''#!/usr/bin/env python
"""
Reproducer script for {params.group} analysis - {params.client}
Generated: {_utc_now().isoformat().replace("+00:00", "Z")}

Usage:
  python _run_this_analysis.py
  python _run_this_analysis.py --block 5  (override block)
"""
import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(r"{src_path}")
sys.path.insert(0, str(src_path))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run

def main():
    parser = argparse.ArgumentParser(description="Re-run {params.group} analysis")
    parser.add_argument("--block", default={block_literal}, help="Block to execute (default: {params.block})")
    parser.add_argument("--output-dir", default=r"{default_output_dir}", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default={env_file_literal}, help="Optional .env file path")
    args = parser.parse_args()

    params = RunParams(
        project_id={params.project_id},
        group={group_literal},
        pipeline={pipeline_literal},
        client={client_literal},
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
    )

    config_root = Path(r"{config_root_resolved}")
    result = run(params, config_root=config_root)

    if result["status"] == "ok":
        print("[OK] Analysis completed successfully")
        print(f"  Generated files: {{result['details'].get('generated_files', [])}}")
        return 0
    else:
        print(f"[ERROR] Analysis failed: {{result.get('error', 'Unknown error')}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    reproducer_file = audit_dir / f"{run_id}_run_this_analysis.py"
    latest_reproducer_file = audit_dir / "_run_this_analysis.py"
    with open(reproducer_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    with open(latest_reproducer_file, "w", encoding="utf-8") as f:
        f.write(script_content)
    reproducer_file.chmod(0o755)  # Make executable on Unix
    latest_reproducer_file.chmod(0o755)  # Make executable on Unix
    return str(reproducer_file)


def run(params: RunParams, config_root: Path) -> Dict[str, Any]:
    theme = load_theme(config_root, params.client)

    if params.pipeline.lower() in {"meio_fisico", "fisico", "meio-fisico", "physicochemical"}:
        details = run_meio_fisico_pipeline(
            codigo_projeto=params.client.upper(),
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
            project_id=params.project_id,
            group=params.group,
        )
    elif params.pipeline.lower() in {"meio_fisico_xlsx", "meio_fisico_gold", "fisico_xlsx", "meio_fisico_v2"}:
        details = run_meio_fisico_xlsx_pipeline(
            client=params.client.upper(),
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
            project_id=params.project_id,
            group=params.group,
            config_root=config_root,
        )
    elif params.pipeline.lower() == "zoobentos":
        details = run_zoobentos_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"fitoplancton", "fito"}:
        details = run_fitoplancton_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"zooplancton", "zoo", "zooplanctonio"}:
        details = run_zooplancton_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"ictio", "ictiofauna", "ichthyo", "ichthyofauna"}:
        details = run_ictio_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    # --- Diagnóstico: stubs ---
    elif params.pipeline.lower() in {"macrofitas", "macrófitas", "macrophytes"}:
        details = run_macrofitas_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"mastofauna", "mastofauna_diag", "mamiferos"}:
        details = run_mastofauna_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"primatas", "primatas_diag", "primates"}:
        details = run_primatas_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"herpetofauna", "herp", "repteis"}:
        details = run_herpetofauna_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    elif params.pipeline.lower() in {"avifauna", "aves", "birds"}:
        details = run_avifauna_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    # --- Monitoramento ---
    elif params.pipeline.lower() in {"mastofauna_mon", "mastofauna_monitoramento", "masto_mon"}:
        details = run_mastofauna_monitoring_pipeline(
            project_id=params.project_id,
            group=params.group,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
        )
    else:
        raise ValueError(f"Unsupported pipeline: {params.pipeline}")

    result = {
        "status": "ok",
        "pipeline": params.pipeline,
        "output": str(params.output_dir),
        "details": details,
        "client": params.client,
    }

    try:
        run_id = _utc_now().strftime("%Y%m%dT%H%M%SZ")
        audit_dir = _get_project_audit_dir(params, config_root, details)
        metadata_path = _generate_execution_metadata(params, result, config_root, audit_dir, run_id)
        reproducer_path = _generate_reproducer_script(params, config_root, audit_dir, run_id)
        result["audit_trail"] = {
            "metadata_file": metadata_path,
            "reproducer_script": reproducer_path,
            "audit_dir": str(audit_dir),
        }
    except Exception as e:
        print(f"[WARNING] Failed to generate audit trail: {e}")

    return result
