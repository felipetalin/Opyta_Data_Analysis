from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import RunParams
from opyta_analysis.runner import run


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Opyta analysis pipeline from central core")
    p.add_argument("--project-id", type=int, required=True)
    p.add_argument("--group", type=str, required=True)
    p.add_argument("--pipeline", type=str, required=True, help="ex: zoobentos")
    p.add_argument("--client", type=str, required=True, help="config file name in configs/clients")
    p.add_argument("--output-dir", type=str, required=True)
    p.add_argument("--env-file", type=str, default=None, help="Optional path to .env with Supabase credentials")
    p.add_argument("--block", type=str, default="all", help="Pipeline block selector, ex: 6")
    p.add_argument("--audit-project-slug", type=str, default=None, help="Optional outputs/_project_scripts project folder override")
    p.add_argument(
        "--campaigns",
        type=str,
        default=None,
        help="Optional comma-separated campaign filter, ex: C21-03-2022-CH,C22-05-2022-SC",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    campaigns = [c.strip() for c in str(args.campaigns).split(",") if c.strip()] if args.campaigns else None

    params = RunParams(
        project_id=args.project_id,
        group=args.group,
        pipeline=args.pipeline,
        client=args.client,
        output_dir=Path(args.output_dir),
        env_file=args.env_file,
        block=args.block,
        audit_project_slug=args.audit_project_slug,
        campaigns=campaigns,
    )

    result = run(params=params, config_root=ROOT / "configs")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
