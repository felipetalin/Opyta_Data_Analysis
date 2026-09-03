#!/usr/bin/env python
"""
Reproducer script for Ictiofauna analysis - bracar001
Generated: 2026-09-03T12:49:47.553000Z

Usage:
  python _run_this_analysis.py
  python _run_this_analysis.py --block 5  (override block)
"""
import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(r"C:\o\Opyta_Data_Analysis\src")
sys.path.insert(0, str(src_path))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run

def main():
    parser = argparse.ArgumentParser(description="Re-run Ictiofauna analysis")
    parser.add_argument("--block", default='5', help="Block to execute (default: 5)")
    parser.add_argument("--output-dir", default=r"G:\.shortcut-targets-by-id\1dfa3mDLQkCZuEErnRrnLm1tKG19ZAIjZ\Opyta\Clientes\Clientes\Clientes\Brasil PCH\Projeto Carangola\Resultados\Consolidado_2026", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default='.env', help="Optional .env file path")
    parser.add_argument("--campaigns", default=None, help="Override comma-separated campaign filter")
    args = parser.parse_args()
    campaigns = [c.strip() for c in args.campaigns.split(",") if c.strip()] if args.campaigns else None

    params = RunParams(
        project_id=208,
        group='Ictiofauna',
        pipeline='ictio',
        client='bracar001',
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
        audit_project_slug=None,
        campaigns=campaigns,
    )

    config_root = Path(r"C:\o\Opyta_Data_Analysis\configs")
    result = run(params, config_root=config_root)

    if result["status"] == "ok":
        print("[OK] Analysis completed successfully")
        print(f"  Generated files: {result['details'].get('generated_files', [])}")
        return 0
    else:
        print(f"[ERROR] Analysis failed: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
