#!/usr/bin/env python
"""
Reproducer script for Ictiofauna analysis - itagua001_guanhaes
Generated: 2026-09-08T19:28:25.313301Z

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
    parser.add_argument("--block", default='all', help="Block to execute (default: all)")
    parser.add_argument("--output-dir", default=r"G:\.shortcut-targets-by-id\1dfa3mDLQkCZuEErnRrnLm1tKG19ZAIjZ\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Resultados e análises\29_campanha_Jul_26\Ictiofauna\Senhora do Porto", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default='C:\\o\\Opyta_Data_Analysis\\.env', help="Optional .env file path")
    parser.add_argument("--campaigns", default=None, help="Override comma-separated campaign filter")
    args = parser.parse_args()
    campaigns = [c.strip() for c in args.campaigns.split(",") if c.strip()] if args.campaigns else ['C029-2026-08-SC']

    params = RunParams(
        project_id=165,
        group='Ictiofauna',
        pipeline='ictio_partial',
        client='itagua001_guanhaes',
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
        audit_project_slug='ITAGUA001__monitoramento_da_fauna',
        campaigns=campaigns,
        pch_target='Senhora do Porto',
        operator=None,
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
