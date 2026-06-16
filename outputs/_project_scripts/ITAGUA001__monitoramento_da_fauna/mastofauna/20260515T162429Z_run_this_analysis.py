#!/usr/bin/env python
"""
Reproducer script for mastofauna analysis - fersam001
Generated: 2026-05-15T16:24:29.828527Z

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
    parser = argparse.ArgumentParser(description="Re-run mastofauna analysis")
    parser.add_argument("--block", default='6.6', help="Block to execute (default: 6.6)")
    parser.add_argument("--output-dir", default=r"G:\Meu Drive\Opyta\Opyta_Data_Analysis\outputs\_gold_validation\mastofauna_165_status_textual", help="Output directory for generated artifacts")
    parser.add_argument("--env-file", default='G:/Meu Drive/Opyta/Opyta_Data/.env', help="Optional .env file path")
    args = parser.parse_args()

    params = RunParams(
        project_id=165,
        group='mastofauna',
        pipeline='mastofauna',
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
