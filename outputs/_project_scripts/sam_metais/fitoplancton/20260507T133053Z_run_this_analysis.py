#!/usr/bin/env python
"""
Reproducer script for Fitoplancton analysis - fersam001
Generated: 2026-05-07T13:30:54.066511Z

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
    parser = argparse.ArgumentParser(description="Re-run Fitoplancton analysis")
    parser.add_argument("--block", default='all', help="Block to execute (default: all)")
    parser.add_argument("--output-dir", default=r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Ferreira Rocha\SAM Metais\Produtos\Resultados\Fitoplancton", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default=None, help="Optional .env file path")
    args = parser.parse_args()

    params = RunParams(
        project_id=62,
        group='Fitoplancton',
        pipeline='fitoplancton',
        client='fersam001',
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
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
