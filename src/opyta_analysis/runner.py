from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Any

from opyta_analysis.audit_utils import build_file_manifest, git_context
from opyta_analysis.config import RunParams, load_theme
from opyta_analysis.pipelines import (
    # Diagnóstico
    run_meio_fisico_pipeline,
    run_meio_fisico_xlsx_pipeline,
    run_fitoplancton_pipeline,
    run_ictio_pipeline,
    run_ictio_partial_pipeline,
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
    safe = [c if c.isalnum() else "_" for c in value]
    return "".join(safe).strip("_") or "unknown"


def _client_audit_project_slug(params: RunParams, config_root: Path) -> str | None:
    cfg_path = config_root / "clients" / f"{params.client}.json"
    if not cfg_path.exists():
        return None
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    value = cfg.get("audit_project_slug") or cfg.get("project_slug")
    return str(value).strip() if value else None


def _get_project_group_dir(params: RunParams, config_root: Path, details: Dict[str, Any]) -> Path:
    """Diretorio estavel por (projeto, grupo). Mantido no MESMO caminho de
    sempre porque `opyta_analysis.fauna.audit.audit_project()` descobre
    metadados com `project_dir.glob("*/execution_metadata.json")` — um unico
    nivel de subdiretorio a partir do projeto. Mudar esse caminho quebraria
    silenciosamente o audit manifest de todos os projetos."""
    root = config_root.parent
    project_name = params.audit_project_slug or details.get("project_name") or _client_audit_project_slug(params, config_root)
    project_folder = _slug(project_name) if project_name else f"project_{params.project_id}"
    group_folder = _slug(params.group).lower()
    group_dir = root / "outputs" / "_project_scripts" / project_folder / group_folder
    group_dir.mkdir(parents=True, exist_ok=True)
    return group_dir


def _campaign_identity_slug(params: RunParams, details: Dict[str, Any]) -> str:
    campaigns = params.campaigns or details.get("campaigns") or []
    campaigns = [str(c) for c in campaigns if c]
    if not campaigns:
        return "sem_campanha_definida"
    if len(campaigns) == 1:
        return _slug(campaigns[0])
    ordered = sorted(campaigns)
    return f"{len(ordered)}campanhas_{_slug(ordered[0])}_a_{_slug(ordered[-1])}"


def _pch_identity_slug(params: RunParams) -> str:
    return _slug(params.pch_target) if params.pch_target else "sem_pch_alvo"


def _get_execution_run_dir(group_dir: Path, params: RunParams, details: Dict[str, Any], run_id: str) -> Path:
    """Diretorio IMUTAVEL por execucao: projeto+grupo (via `group_dir`) mais
    campanha, empreendimento e `run_id`. Nunca reutilizado nem podado por
    outra execucao — cada chamada cria um diretorio novo e este runner nunca
    apaga arquivos dentro de `runs/`."""
    identity = f"{_campaign_identity_slug(params, details)}__{_pch_identity_slug(params)}"
    run_dir = group_dir / "runs" / identity / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _generate_execution_metadata(
    params: RunParams,
    result: Dict[str, Any],
    config_root: Path,
    group_dir: Path,
    run_dir: Path,
    run_id: str,
) -> str:
    """Generate and save execution metadata JSON for audit trail and reproducibility.

    Written to two places:
    - `run_dir` (immutable, unique per execution: projeto+grupo+campanha+
      empreendimento+run_id) — never overwritten or pruned by another run.
    - `group_dir` (stable "latest" pointer, same path used since before this
      fix) — overwritten every run, kept ONLY for
      `opyta_analysis.fauna.audit.audit_project()`, which discovers metadata
      with a fixed-depth glob (`<project>/*/execution_metadata.json`).
    """
    details = result.get("details", {})
    campaigns = details.get("campaigns", [])
    points = details.get("points", [])
    generated_files = details.get("generated_files", [])
    generated_file_checks = build_file_manifest(generated_files)
    missing_generated_files = [item["path"] for item in generated_file_checks if not item.get("exists")]
    warnings = list(details.get("warnings", [])) if isinstance(details.get("warnings", []), list) else []
    if missing_generated_files:
        warnings.append(f"missing_generated_files={len(missing_generated_files)}")

    metadata = {
        "executed_at": _utc_now().isoformat().replace("+00:00", "Z"),
        "runner_version": "1.2",
        "project_id": params.project_id,
        "group": params.group,
        "pipeline": params.pipeline,
        "client": params.client,
        "block": params.block,
        "campaign_filter": params.campaigns,
        "git": git_context(config_root.parent),
        "rows_loaded": details.get("rows_loaded", 0),
        "executed_blocks": details.get("executed_blocks", []),
        "campaigns": campaigns,
        "campaigns_count": len(campaigns) if isinstance(campaigns, list) else None,
        "points": points,
        "points_count": len(points) if isinstance(points, list) else None,
        "output_dir": str(params.output_dir),
        "generated_files_count": len(generated_files),
        "generated_files": generated_files,
        "generated_file_checks": generated_file_checks,
        "generated_files_missing_count": len(missing_generated_files),
        "config_root": str(config_root),
        "audit_dir": str(run_dir),
        "run_id": run_id,
        "warnings": warnings,
    }

    run_metadata_file = run_dir / "execution_metadata.json"
    latest_metadata_file = group_dir / "execution_metadata.json"
    for target in (run_metadata_file, latest_metadata_file):
        with open(target, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    return str(run_metadata_file)


def _generate_reproducer_script(params: RunParams, config_root: Path, group_dir: Path, run_dir: Path, run_id: str) -> str:
    """Generate a standalone reproducer script for future re-execution."""
    src_path = (config_root.parent / "src").resolve()
    default_output_dir = params.output_dir.resolve()
    config_root_resolved = config_root.resolve()
    group_literal = repr(params.group)
    pipeline_literal = repr(params.pipeline)
    client_literal = repr(params.client)
    env_file_literal = repr(params.env_file)
    block_literal = repr(params.block)
    audit_project_slug_literal = repr(params.audit_project_slug)
    campaigns_literal = repr(params.campaigns)
    pch_target_literal = repr(params.pch_target)

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
    parser.add_argument("--campaigns", default=None, help="Override comma-separated campaign filter")
    args = parser.parse_args()
    campaigns = [c.strip() for c in args.campaigns.split(",") if c.strip()] if args.campaigns else {campaigns_literal}

    params = RunParams(
        project_id={params.project_id},
        group={group_literal},
        pipeline={pipeline_literal},
        client={client_literal},
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
        audit_project_slug={audit_project_slug_literal},
        campaigns=campaigns,
        pch_target={pch_target_literal},
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

    reproducer_file = run_dir / "_run_this_analysis.py"
    latest_reproducer_file = group_dir / "_run_this_analysis.py"
    for target in (reproducer_file, latest_reproducer_file):
        with open(target, "w", encoding="utf-8") as f:
            f.write(script_content)
        target.chmod(0o755)  # Make executable on Unix
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
            campaign_filter=params.campaigns,
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
            campaign_filter=params.campaigns,
        )
    elif params.pipeline.lower() in {"ictio_partial", "ictiofauna_parcial", "ictio_parcial"}:
        if not params.campaigns or len(params.campaigns) != 1:
            raise ValueError(
                "pipeline 'ictio_partial' requer RunParams.campaigns com exatamente "
                "uma campanha (a campanha unica do relatorio parcial por empreendimento)."
            )
        if not params.pch_target:
            raise ValueError(
                "pipeline 'ictio_partial' requer RunParams.pch_target (nome do "
                "empreendimento/PCH a filtrar)."
            )
        details = run_ictio_partial_pipeline(
            project_id=params.project_id,
            theme=theme,
            output_dir=params.output_dir,
            env_file=params.env_file,
            block=params.block,
            campanha_alvo=params.campaigns[0],
            pch_alvo=params.pch_target,
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
        group_dir = _get_project_group_dir(params, config_root, details)
        run_dir = _get_execution_run_dir(group_dir, params, details, run_id)
        metadata_path = _generate_execution_metadata(params, result, config_root, group_dir, run_dir, run_id)
        reproducer_path = _generate_reproducer_script(params, config_root, group_dir, run_dir, run_id)
        result["audit_trail"] = {
            "metadata_file": metadata_path,
            "reproducer_script": reproducer_path,
            "audit_dir": str(run_dir),
            "run_id": run_id,
        }
    except Exception as e:
        print(f"[WARNING] Failed to generate audit trail: {e}")

    return result
