"""Gera Darwin Core IEF de ictiofauna do ITAGUA001 por empreendimento.

Fonte:
    Supabase, view ``biota_analise_consolidada``, filtrada diretamente por
    ``codigo_interno_opyta=ITAGUA001`` e ``grupo_biologico=Ictiofauna``.

Destino:
    <Planilha DarwinCore>/Ictiofauna/<Empreendimento>/

Os arquivos historicos W74.21 existentes na raiz de Ictiofauna nao sao
alterados. A execucao gera tambem um manifesto JSON com contagens, periodo,
campanhas, pontos e SHA-256 dos quatro arquivos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook


ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.pipelines.diagnostico.darwincore_ief import (  # noqa: E402
    ASSOCIATED_OCCURRENCE_COLUMNS,
    FISH_BIOMETRIC_COLUMNS,
    SAMPLING_EVENT_COLUMNS,
    export_darwincore_ief,
)
from opyta_analysis.supabase_client import get_client, paginate  # noqa: E402


PROJECT_CODE = "ITAGUA001"
GROUP = "Ictiofauna"
DEFAULT_CAMPAIGN = "C028-2026-05-SC"
DEFAULT_ENV_FILE = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")
DEFAULT_OUTPUT_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia/"
    "Guanh\u00e3es Energia/Planilha DarwinCore/Ictiofauna"
)

ENTERPRISES = {
    "Dores de Guanh\u00e3es": {
        "code": "DGN",
        "folder": "Dores de Guanh\u00e3es",
        "municipality": "Dores de Guanh\u00e3es",
        "main_water_body": "Guanh\u00e3es",
        "point_tokens": ("DGN",),
    },
    "Fortuna II": {
        "code": "FOR",
        "folder": "Fortuna II",
        "municipality": "Virgin\u00f3polis",
        "main_water_body": "Corrente Grande",
        "point_tokens": ("FOR",),
    },
    "Jacar\u00e9": {
        "code": "JAC",
        "folder": "Jacar\u00e9",
        "municipality": "Dores de Guanh\u00e3es",
        "main_water_body": "Guanh\u00e3es",
        "point_tokens": ("JAC",),
    },
    "Senhora do Porto": {
        "code": "SPT",
        "folder": "Senhora do Porto",
        "municipality": "Dores de Guanh\u00e3es",
        "main_water_body": "Guanh\u00e3es",
        "point_tokens": ("SPT",),
    },
}


def _normalize(value: object) -> str:
    text = str(value or "").strip().lower()
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_project_data(env_file: Path, campaign: str) -> pd.DataFrame:
    sb = get_client(str(env_file))
    rows = paginate(
        sb,
        "biota_analise_consolidada",
        filters={
            "codigo_interno_opyta": PROJECT_CODE,
            "grupo_biologico": GROUP,
            "nome_campanha": campaign,
        },
        select="*",
    )
    if not rows:
        raise RuntimeError(
            f"Nenhum registro encontrado para {PROJECT_CODE}/{GROUP}/{campaign}."
        )

    df = pd.DataFrame(rows)
    required = {
        "codigo_interno_opyta",
        "grupo_biologico",
        "nome_empreendimento",
        "nome_ponto",
        "nome_cientifico",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"Colunas obrigatorias ausentes na view: {missing}")

    project_codes = set(df["codigo_interno_opyta"].dropna().astype(str).str.strip())
    if project_codes != {PROJECT_CODE}:
        raise RuntimeError(f"Escopo de projeto inconsistente: {sorted(project_codes)}")

    groups = {_normalize(value) for value in df["grupo_biologico"].dropna()}
    if groups != {_normalize(GROUP)}:
        raise RuntimeError(f"Escopo de grupo inconsistente: {sorted(groups)}")

    campaigns = set(df["nome_campanha"].dropna().astype(str).str.strip())
    if campaigns != {campaign}:
        raise RuntimeError(f"Escopo de campanha inconsistente: {sorted(campaigns)}")

    df = df[df["nome_cientifico"].notna()].copy()
    df = df[df["nome_cientifico"].astype(str).str.strip().ne("")].copy()
    return df.reset_index(drop=True)


def _prepare_enterprise_data(df: pd.DataFrame, enterprise: str, config: dict) -> pd.DataFrame:
    mask = df["nome_empreendimento"].astype(str).map(_normalize) == _normalize(enterprise)
    subset = df[mask].copy()
    if subset.empty:
        raise RuntimeError(f"Sem dados de ictiofauna para o empreendimento {enterprise}.")

    point_names = subset["nome_ponto"].fillna("").astype(str).str.strip()
    invalid_points = sorted(
        {
            point
            for point in point_names
            if point and not any(token in point.upper() for token in config["point_tokens"])
        }
    )
    if invalid_points:
        raise RuntimeError(
            f"{enterprise}: pontos incompat\u00edveis com o empreendimento: {invalid_points}"
        )

    subset["county"] = config["municipality"]
    subset["municipality"] = config["municipality"]
    subset["waterBody"] = point_names.map(
        lambda point: "Tribut\u00e1rio"
        if point.upper().startswith("TR")
        else config["main_water_body"]
    )
    return subset


def _validate_workbook(path: Path, expected_rows: int, expected_point_tokens: tuple[str, ...]) -> dict:
    wb = load_workbook(path, read_only=True, data_only=True)
    expected_sheets = [
        "Orienta\u00e7\u00f5es",
        "Sampling Events",
        "Associated Occurrences",
        "Fish Biometric data",
    ]
    if wb.sheetnames != expected_sheets:
        raise RuntimeError(f"{path.name}: abas inesperadas: {wb.sheetnames}")

    sheet_specs = {
        "Sampling Events": SAMPLING_EVENT_COLUMNS,
        "Associated Occurrences": ASSOCIATED_OCCURRENCE_COLUMNS,
        "Fish Biometric data": FISH_BIOMETRIC_COLUMNS,
    }
    row_counts = {}
    for sheet_name, expected_columns in sheet_specs.items():
        ws = wb[sheet_name]
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        if headers != expected_columns:
            raise RuntimeError(f"{path.name}/{sheet_name}: cabecalho divergente.")
        row_count = ws.max_row - 1
        if row_count != expected_rows:
            raise RuntimeError(
                f"{path.name}/{sheet_name}: {row_count} linhas; esperado {expected_rows}."
            )
        row_counts[sheet_name] = row_count

    sampling_ws = wb["Sampling Events"]
    locality_index = SAMPLING_EVENT_COLUMNS.index("locality")
    municipalities = set()
    municipality_index = SAMPLING_EVENT_COLUMNS.index("municipality")
    invalid_localities = set()
    for row in sampling_ws.iter_rows(min_row=2, values_only=True):
        locality = str(row[locality_index] or "").strip()
        municipality = str(row[municipality_index] or "").strip()
        if municipality:
            municipalities.add(municipality)
        if locality and not any(token in locality.upper() for token in expected_point_tokens):
            invalid_localities.add(locality)
    if invalid_localities:
        raise RuntimeError(f"{path.name}: localidades misturadas: {sorted(invalid_localities)}")

    validation = {
        "sheets": wb.sheetnames,
        "rows_by_sheet": row_counts,
        "municipalities": sorted(municipalities),
    }
    wb.close()
    return validation


def generate(env_file: Path, output_root: Path, campaign: str) -> dict:
    df = _load_project_data(env_file, campaign)
    observed_enterprises = set(df["nome_empreendimento"].dropna().astype(str).str.strip())
    expected_enterprises = set(ENTERPRISES)
    if observed_enterprises != expected_enterprises:
        raise RuntimeError(
            "Empreendimentos divergentes. "
            f"Esperado={sorted(expected_enterprises)}; observado={sorted(observed_enterprises)}"
        )

    generated_files: list[str] = []
    enterprise_results = []
    for enterprise, config in ENTERPRISES.items():
        subset = _prepare_enterprise_data(df, enterprise, config)
        output_dir = output_root / config["folder"]
        campaign_slug = campaign.split("-", 1)[0]
        output_filename = (
            f"DarwinCore_IEF_Ictiofauna_{PROJECT_CODE}_{campaign_slug}_{config['code']}.xlsx"
        )
        result = export_darwincore_ief(
            df=subset,
            group=GROUP,
            output_dir=output_dir,
            generated_files=generated_files,
            include_fish_biometrics=True,
            output_filename=output_filename,
            county_default=config["municipality"],
            municipality_default=config["municipality"],
        )
        output_path = Path(result["file"])
        validation = _validate_workbook(
            output_path,
            expected_rows=len(subset),
            expected_point_tokens=config["point_tokens"],
        )

        dates = pd.to_datetime(subset.get("data_hora_coleta"), errors="coerce").dropna()
        enterprise_results.append(
            {
                "enterprise": enterprise,
                "code": config["code"],
                "file": str(output_path),
                "sha256": _sha256(output_path),
                "size_bytes": output_path.stat().st_size,
                "rows": int(len(subset)),
                "campaigns": sorted(
                    subset["nome_campanha"].dropna().astype(str).str.strip().unique().tolist()
                ),
                "campaigns_count": int(subset["nome_campanha"].nunique()),
                "points": sorted(
                    subset["nome_ponto"].dropna().astype(str).str.strip().unique().tolist()
                ),
                "points_count": int(subset["nome_ponto"].nunique()),
                "date_min": dates.min().date().isoformat() if not dates.empty else None,
                "date_max": dates.max().date().isoformat() if not dates.empty else None,
                "validation": validation,
            }
        )
        print(
            f"[OK] {enterprise}: {len(subset)} registros, "
            f"{subset['nome_campanha'].nunique()} campanhas -> {output_path}"
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "campaign": campaign,
        "source": "Supabase.biota_analise_consolidada",
        "source_rows": int(len(df)),
        "output_root": str(output_root),
        "historical_root_files_preserved": True,
        "enterprises": enterprise_results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / (
        f"manifest_darwincore_itagua001_{campaign.split('-', 1)[0].lower()}.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] Manifesto: {manifest_path}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera Darwin Core IEF de ictiofauna do ITAGUA001 por empreendimento."
    )
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN)
    args = parser.parse_args()
    generate(args.env_file, args.output_root, args.campaign)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
