"""Executa Ictiofauna parcial da Campanha 29 (ITAGUA001) por empreendimento.

Le a recipe `configs/projects/itagua001_guanhaes_ictiofauna.json` (campanha,
client proprio do projeto e pasta de saida ja definidos ali) e roda o gerador
`ictio_partial` via `opyta_analysis.runner.run`, exatamente como
`scripts/run/run_project_recipe.py` faria, mas com selecao explicita de
empreendimento(s) por nome (nao por --group, que aqui e sempre "Ictiofauna").

Uso:
    python run_ictio_partial_c029_itagua001.py --pch "Senhora do Porto"
    python run_ictio_partial_c029_itagua001.py --all
    python run_ictio_partial_c029_itagua001.py --pch "Senhora do Porto" --dry-run

Por seguranca (Gate C aprovado apenas para amostra de revisao), o script
exige `--pch <nome>` ou `--all` explicito; nao roda nada por omissao.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import RunParams  # noqa: E402
from opyta_analysis.runner import run  # noqa: E402

RECIPE_PATH = ROOT / "configs" / "projects" / "itagua001_guanhaes_ictiofauna.json"
ENV_FILE = str(ROOT / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pch", action="append", default=None, help="Nome exato do empreendimento (recipe); repetir para varios")
    parser.add_argument("--all", action="store_true", help="Rodar todos os empreendimentos da recipe")
    parser.add_argument("--block", default="all", help="Bloco a executar (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o plano sem executar")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.all and not args.pch:
        print("[ERRO] Informe --pch \"<Empreendimento>\" (pode repetir) ou --all.", file=sys.stderr)
        return 2

    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    if recipe.get("status") != "prototype":
        print(f"[AVISO] recipe status = {recipe.get('status')!r} (esperado 'prototype' ate o Gate R).")

    wanted = None if args.all else set(args.pch)
    output_root = Path(recipe["output_root"])

    planned = []
    for group_cfg in recipe["groups"]:
        pch = group_cfg["pch_target"]
        if wanted is not None and pch not in wanted:
            continue
        planned.append(
            RunParams(
                project_id=int(recipe["project_id"]),
                group=group_cfg["group"],
                pipeline=group_cfg["pipeline"],
                client=recipe["client_config"],
                output_dir=output_root / group_cfg["output_subdir"],
                env_file=ENV_FILE,
                block=args.block,
                audit_project_slug=recipe["audit_project_slug"],
                campaigns=recipe["campaigns"],
                pch_target=pch,
            )
        )

    if not planned:
        print(f"[ERRO] Nenhum empreendimento da recipe corresponde a {args.pch}.", file=sys.stderr)
        return 2

    if args.dry_run:
        for p in planned:
            print(json.dumps({
                "pch_target": p.pch_target,
                "campaigns": p.campaigns,
                "client": p.client,
                "audit_project_slug": p.audit_project_slug,
                "output_dir": str(p.output_dir),
                "block": p.block,
            }, ensure_ascii=False, indent=2))
        return 0

    exit_code = 0
    for params in planned:
        result = run(params=params, config_root=ROOT / "configs")
        details = result.get("details", {})
        status = result.get("status", "unknown")
        generated = len(details.get("generated_files", []))
        warning = details.get("warning")
        extra = f" | {warning}" if warning else ""
        print(f"[{status}] {params.pch_target} -> {params.output_dir} | arquivos: {generated}{extra}")
        if status != "ok":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
