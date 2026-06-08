from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import load_theme  # noqa: E402
from opyta_analysis.pipelines.diagnostico.zoobentos import (  # noqa: E402
    _load_zoobentos_df,
    _run_block_3,
    _run_block_4,
    _run_block_5,
    _run_block_6,
    _run_block_7,
    _run_block_8,
    _run_block_9,
    _run_block_10,
    _run_block_11,
    _run_block_12,
    _run_block_13,
)


PROJECT_ID = 9
GROUP = "Zoobentos"
CLIENT = "braavg002"
DEFAULT_ENV_FILE = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")
DEFAULT_OUTPUT_ROOT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos\Planilha Consolidada\Resultados e planilhas\Resultados bentos\2026"
)

TARGETS = [
    {
        "campaign": "43a-Fev-26",
        "folder": "Fevereir-26",
    },
    {
        "campaign": "44a-Mar-26",
        "folder": "marco-26",
    },
]


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _norm_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = (
        text.replace("\xa0", " ")
        .replace("Âª", "a")
        .replace("ª", "a")
        .replace("Âº", "o")
        .replace("º", "o")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _filter_campaign(df, campaign: str):
    target = _norm_text(campaign)
    mask = df["nome_campanha"].map(_norm_text) == target
    filtered = df.loc[mask].copy()
    if filtered.empty:
        available = sorted(df["nome_campanha"].dropna().astype(str).unique().tolist())
        raise RuntimeError(f"Campanha nao encontrada: {campaign}. Disponiveis: {available}")
    return filtered


def _run_all_blocks(df, theme: dict, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[str] = []
    executed_blocks: list[str] = []

    _run_block_3(df=df, group=GROUP, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("3")

    _run_block_4(df=df, group=GROUP, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("4")

    _run_block_5(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("5")

    _run_block_6(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("6")

    _run_block_7(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("7")

    _run_block_8(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("8")

    _run_block_9(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("9")

    _run_block_10(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("10")

    _run_block_11(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("11")

    _run_block_12(df=df, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("12")

    _run_block_13(df=df, group=GROUP, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("13")

    return {
        "executed_blocks": executed_blocks,
        "generated_files": generated_files,
    }


def _summarize_df(df) -> dict[str, Any]:
    return {
        "records": int(len(df)),
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()),
        "taxa": int(df["taxon_final"].nunique()),
        "abundancia_total": float(df["contagem"].sum()),
    }


def run(output_root: Path, env_file: str | None) -> dict[str, Any]:
    theme = load_theme(ROOT / "configs", CLIENT)
    df_all = _load_zoobentos_df(project_id=PROJECT_ID, group=GROUP, env_file=env_file)
    if df_all.empty:
        raise RuntimeError("Nenhum registro de Zoobentos carregado para AVG.")

    results: list[dict[str, Any]] = []
    for target in TARGETS:
        df_campaign = _filter_campaign(df_all, target["campaign"])
        output_dir = output_root / target["folder"]
        block_result = _run_all_blocks(df_campaign, theme, output_dir)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project_id": PROJECT_ID,
            "client": CLIENT,
            "group": GROUP,
            "target_campaign": target["campaign"],
            "output_dir": str(output_dir),
            **_summarize_df(df_campaign),
            **block_result,
        }
        (output_dir / "metadata_resultados_zoobentos.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
        results.append(payload)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_id": PROJECT_ID,
        "client": CLIENT,
        "group": GROUP,
        "output_root": str(output_root),
        "campaign_results": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "metadata_resultados_zoobentos_fev_mar_2026.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera resultados AVG Bentos por campanha de 2026.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run(output_root=Path(args.output_root), env_file=args.env_file)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
