from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import warnings
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
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
    {
        "campaign": "45a-Abr-26",
        "folder": "abril-26",
    },
]

AREA_01 = "\u00c1rea de controle 01"
AREA_02 = "\u00c1rea de controle 02"
AC01_POINTS = [
    "PIC-01",
    "PIC-02",
    "PIC-03",
    "PIC-04",
    "PIC-05",
    "PIC-06",
    "PIC-07",
    "PIC-08",
    "PIC-09",
    "PIC-11",
]
AC02_POINTS = ["PIC-10", "PIC-12", "PIC-13"]
POINT_ORDER = AC01_POINTS + AC02_POINTS
AREA_BY_POINT = {p: AREA_01 for p in AC01_POINTS} | {p: AREA_02 for p in AC02_POINTS}
POINT_RANK = {point: idx + 1 for idx, point in enumerate(POINT_ORDER)}

NOT_SAMPLED_CAMPAIGN_RANGES = {
    "PIC-01": [(40, None)],
    "PIC-02": [(40, 42)],
    "PIC-03": [(40, 42), (44, None)],
    "PIC-11": [(40, None)],
}


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


def _campaign_seq(value: object) -> int:
    text = _norm_text(value)
    match = re.search(r"\d+", text)
    if not match:
        raise ValueError(f"Campanha sem sequencia numerica: {value!r}")
    return int(match.group(0))


def _is_not_monitored(point: object, campaign_seq: int) -> bool:
    point_name = "" if point is None else str(point).strip()
    for start, end in NOT_SAMPLED_CAMPAIGN_RANGES.get(point_name, []):
        if campaign_seq >= start and (end is None or campaign_seq <= end):
            return True
    return False


def _monitored_points(campaign_seq: int) -> list[str]:
    return [point for point in POINT_ORDER if not _is_not_monitored(point, campaign_seq)]


def _filter_campaign(df, campaign: str):
    target = _norm_text(campaign)
    mask = df["nome_campanha"].map(_norm_text) == target
    filtered = df.loc[mask].copy()
    if filtered.empty:
        available = sorted(df["nome_campanha"].dropna().astype(str).unique().tolist())
        raise RuntimeError(f"Campanha nao encontrada: {campaign}. Disponiveis: {available}")
    return filtered


def _add_point_area_metadata(df):
    out = df.copy()
    out["nome_ponto"] = out["nome_ponto"].astype(str).str.strip()
    out["area_controle"] = out["nome_ponto"].map(AREA_BY_POINT)
    out["ordem_ponto"] = out["nome_ponto"].map(POINT_RANK)
    out["campanha_seq"] = out["nome_campanha"].map(_campaign_seq)
    out["Status_Monitoramento"] = [
        "Não monitorado" if _is_not_monitored(point, int(seq)) else "Monitorado"
        for point, seq in zip(out["nome_ponto"], out["campanha_seq"])
    ]
    return out


def _pad_zero_points(df_campaign):
    df = _add_point_area_metadata(df_campaign)
    df = df[df["Status_Monitoramento"].eq("Monitorado")].copy()
    campaign_seq = int(df_campaign["nome_campanha"].map(_campaign_seq).iloc[0])
    active_points = _monitored_points(campaign_seq)
    observed_points = set(df["nome_ponto"].dropna().astype(str).str.strip())
    missing_points = [point for point in active_points if point not in observed_points]
    if not missing_points:
        return df

    template = df.iloc[0].to_dict()
    pad_rows = []
    for point in missing_points:
        row = {col: pd.NA for col in df.columns}
        for col in [
            "nome_projeto",
            "nome_campanha",
            "bacia_hidrografica",
            "metodo_de_captura",
            "esforco",
            "unidade_esforco",
            "tipo_amostragem",
        ]:
            if col in row:
                row[col] = template.get(col)
        row["nome_ponto"] = point
        row["area_controle"] = AREA_BY_POINT[point]
        row["ordem_ponto"] = POINT_RANK[point]
        row["campanha_seq"] = campaign_seq
        row["Status_Monitoramento"] = "Monitorado"
        row["contagem"] = 0
        row["bmwp_score"] = 0
        if "taxon_final" in row:
            row["taxon_final"] = pd.NA
        if "nome_cientifico" in row:
            row["nome_cientifico"] = pd.NA
        pad_rows.append(row)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=FutureWarning,
            message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated.*",
        )
        return pd.concat([df, pd.DataFrame(pad_rows, columns=df.columns)], ignore_index=True)


def _run_all_blocks(df_observed, df_point_metrics, theme: dict, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[str] = []
    executed_blocks: list[str] = []

    _run_block_3(df=df_observed, group=GROUP, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("3")

    _run_block_4(
        df=df_observed,
        group=GROUP,
        theme=theme,
        output_dir=output_dir,
        generated_files=generated_files,
    )
    executed_blocks.append("4")

    _run_block_5(df=df_point_metrics, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("5")

    _run_block_6(df=df_point_metrics, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("6")

    _run_block_7(df=df_observed, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("7")

    _run_block_8(df=df_point_metrics, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("8")

    _run_block_9(df=df_observed, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("9")

    _run_block_10(df=df_observed, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("10")

    _run_block_11(df=df_point_metrics, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("11")

    _run_block_12(df=df_point_metrics, group=GROUP, theme=theme, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("12")

    _run_block_13(df=df_observed, group=GROUP, output_dir=output_dir, generated_files=generated_files)
    executed_blocks.append("13")

    return {
        "executed_blocks": executed_blocks,
        "generated_files": generated_files,
    }


def _summarize_df(df, campaign: str) -> dict[str, Any]:
    campaign_seq = _campaign_seq(campaign)
    active_points = _monitored_points(campaign_seq)
    not_monitored_points = [point for point in POINT_ORDER if point not in active_points]
    points_with_result = sorted(df["nome_ponto"].dropna().astype(str).unique().tolist())
    zero_points = [point for point in active_points if point not in set(points_with_result)]
    return {
        "records": int(len(df)),
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": active_points,
        "not_monitored_points": not_monitored_points,
        "points_with_result": points_with_result,
        "zero_points": zero_points,
        "taxa": int(df["taxon_final"].nunique()),
        "abundancia_total": float(df["contagem"].sum()),
    }


def _summary_filename(targets: list[dict[str, str]]) -> str:
    slug = "_".join(
        re.sub(r"[^a-z0-9]+", "_", target["folder"].lower()).strip("_").replace("_26", "")
        for target in targets
    )
    return f"metadata_resultados_zoobentos_{slug}_2026.json"


def run(output_root: Path, env_file: str | None) -> dict[str, Any]:
    theme = load_theme(ROOT / "configs", CLIENT)
    df_all = _load_zoobentos_df(project_id=PROJECT_ID, group=GROUP, env_file=env_file)
    if df_all.empty:
        raise RuntimeError("Nenhum registro de Zoobentos carregado para AVG.")

    results: list[dict[str, Any]] = []
    for target in TARGETS:
        df_campaign_all = _filter_campaign(df_all, target["campaign"])
        df_point_metrics = _pad_zero_points(df_campaign_all)
        df_campaign = _add_point_area_metadata(df_campaign_all)
        df_campaign = df_campaign[df_campaign["Status_Monitoramento"].eq("Monitorado")].copy()
        output_dir = output_root / target["folder"]
        block_result = _run_all_blocks(df_campaign, df_point_metrics, theme, output_dir)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project_id": PROJECT_ID,
            "client": CLIENT,
            "group": GROUP,
            "target_campaign": target["campaign"],
            "output_dir": str(output_dir),
            **_summarize_df(df_campaign, target["campaign"]),
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
    (output_root / _summary_filename(TARGETS)).write_text(
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
