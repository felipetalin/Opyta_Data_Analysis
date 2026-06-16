#!/usr/bin/env python
"""
Reproducer script for Zoobentos analysis - geoher001
Generated: 2026-06-15T18:23:17.726899Z

Usage:
  python _run_this_analysis.py
  python _run_this_analysis.py --block 5  (override block)
"""
import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(r"G:\Meu Drive\Opyta\Opyta_Data_Analysis\src")
sys.path.insert(0, str(src_path))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run

def main():
    parser = argparse.ArgumentParser(description="Re-run Zoobentos analysis")
    parser.add_argument("--block", default='all', help="Block to execute (default: all)")
    parser.add_argument("--output-dir", default=r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Herculano - Informações Complementares Licenciamento Pilhas\Resultados\Bentos", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default='.env', help="Optional .env file path")
    parser.add_argument("--campaigns", default=None, help="Override comma-separated campaign filter")
    args = parser.parse_args()
    campaigns = [c.strip() for c in args.campaigns.split(",") if c.strip()] if args.campaigns else ['C21-03-2022-CH', 'C22-05-2022-SC', 'C23-08-2022-SC', 'C24-11-2022-CH', 'C25-02-2023-CH', 'C26-05-2023-SC', 'C27-08-2023-SC', 'C28-11-2023-CH', 'C29-02-2024-CH', 'C30-05-2024-SC', 'C31-08-2024-SC', 'C32-11-2024-CH', 'C33-02-2025-CH', 'C34-05-2025-SC', 'C35-08-2025-SC', 'C36-11-2025-CH']

    params = RunParams(
        project_id=30,
        group='Zoobentos',
        pipeline='zoobentos',
        client='geoher001',
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
        audit_project_slug='geoher001_recorte_2022_2025',
        campaigns=campaigns,
    )

    config_root = Path(r"G:\Meu Drive\Opyta\Opyta_Data_Analysis\configs")
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
