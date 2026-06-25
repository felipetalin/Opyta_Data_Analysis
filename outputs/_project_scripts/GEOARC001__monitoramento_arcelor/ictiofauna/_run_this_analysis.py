#!/usr/bin/env python
"""
Reproducer script for Ictiofauna analysis - geoarc001_arcelor
Generated: 2026-06-24T19:11:04.282581Z

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
    parser = argparse.ArgumentParser(description="Re-run Ictiofauna analysis")
    parser.add_argument("--block", default='10', help="Block to execute (default: 10)")
    parser.add_argument("--output-dir", default=r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default='.env', help="Optional .env file path")
    parser.add_argument("--campaigns", default=None, help="Override comma-separated campaign filter")
    args = parser.parse_args()
    campaigns = [c.strip() for c in args.campaigns.split(",") if c.strip()] if args.campaigns else ['C001-2022-03-CH', 'C002-2022-07-SC', 'C003-2022-09-SC', 'C004-2022-12-CH', 'C005-2023-03-CH', 'C006-2023-06-SC', 'C007-2023-09-SC', 'C008-2023-12-CH', 'C009-2024-03-CH', 'C010-2024-06-SC', 'C011-2024-09-SC', 'C012-2024-12-CH', 'C013-2025-03-CH', 'C014-2025-06-SC', 'C015-2025-09-SC', 'C016-2025-12-CH', 'C017-2026-03-CH', 'C018-2026-06-SC']

    params = RunParams(
        project_id=190,
        group='Ictiofauna',
        pipeline='ictio',
        client='geoarc001_arcelor',
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
        audit_project_slug='GEOARC001__monitoramento_arcelor',
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
