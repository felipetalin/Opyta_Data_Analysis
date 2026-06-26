from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.geo_reference import haversine_km, read_kml_point_coordinates, standardize_point_name


DEFAULT_REFERENCE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Geo\Arcelor_2026.kmz"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "audits" / "geoarc001_coordinates"


def get_engine(env_file: Path):
    load_dotenv(env_file, override=True)
    values = {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
    }
    missing = [key for key, value in values.items() if key != "DB_PORT" and not value]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    url = (
        f"postgresql://{quote_plus(values['DB_USER'])}:{quote_plus(values['DB_PASSWORD'])}"
        f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}?connect_timeout=15"
    )
    return create_engine(url)


def fetch_points(engine, project_id: int) -> pd.DataFrame:
    query = text(
        """
        SELECT
            pc.id_ponto_coleta,
            pc.id_projeto,
            pc.id_campanha,
            c.nome_campanha,
            pc.nome_ponto,
            pc.latitude,
            pc.longitude
        FROM public.pontos_coleta pc
        LEFT JOIN public.campanhas c ON c.id_campanha = pc.id_campanha
        WHERE pc.id_projeto = :project_id
        ORDER BY pc.nome_ponto, c.nome_campanha, pc.id_ponto_coleta
        """
    )
    return pd.read_sql(query, engine, params={"project_id": project_id})


def build_comparison(points: pd.DataFrame, reference: pd.DataFrame, tolerance_m: float) -> pd.DataFrame:
    comp = points.copy()
    comp["Ponto_padrao"] = comp["nome_ponto"].map(standardize_point_name)
    comp["latitude"] = pd.to_numeric(comp["latitude"], errors="coerce")
    comp["longitude"] = pd.to_numeric(comp["longitude"], errors="coerce")
    comp = comp.merge(reference, left_on="Ponto_padrao", right_on="Ponto", how="left")
    distances: list[float | None] = []
    statuses: list[str] = []
    for _, row in comp.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        lat_ref = row.get("Latitude_ref")
        lon_ref = row.get("Longitude_ref")
        if pd.isna(lat_ref) or pd.isna(lon_ref):
            distances.append(None)
            statuses.append("ponto_sem_referencia")
        elif pd.isna(lat) or pd.isna(lon):
            distances.append(None)
            statuses.append("coordenada_banco_ausente")
        else:
            distance_m = haversine_km(float(lat), float(lon), float(lat_ref), float(lon_ref)) * 1000
            distances.append(distance_m)
            statuses.append("ok" if distance_m <= tolerance_m else "corrigir")
    comp["distancia_m"] = distances
    comp["status_correcao"] = statuses
    comp["aplicar_update"] = comp["status_correcao"].isin(["corrigir", "coordenada_banco_ausente"])
    return comp


def apply_updates(engine, updates: pd.DataFrame) -> int:
    query = text(
        """
        UPDATE public.pontos_coleta
        SET latitude = :latitude_ref,
            longitude = :longitude_ref
        WHERE id_ponto_coleta = :id_ponto_coleta
        """
    )
    count = 0
    with engine.begin() as conn:
        for _, row in updates.iterrows():
            conn.execute(
                query,
                {
                    "id_ponto_coleta": int(row["id_ponto_coleta"]),
                    "latitude_ref": float(row["Latitude_ref"]),
                    "longitude_ref": float(row["Longitude_ref"]),
                },
            )
            count += 1
    return count


def write_audit(output_dir: Path, stamp: str, summary: dict, reference: pd.DataFrame, before: pd.DataFrame, comparison: pd.DataFrame, after: pd.DataFrame | None) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx = output_dir / f"geoarc001_coordinate_update_audit_{stamp}.xlsx"
    manifest = output_dir / f"geoarc001_coordinate_update_audit_{stamp}.json"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="00_resumo", index=False)
        reference.to_excel(writer, sheet_name="01_referencia_kmz", index=False)
        before.to_excel(writer, sheet_name="02_supabase_antes", index=False)
        comparison.to_excel(writer, sheet_name="03_comparacao", index=False)
        comparison[comparison["aplicar_update"]].to_excel(writer, sheet_name="04_updates_planejados", index=False)
        if after is not None:
            after.to_excel(writer, sheet_name="05_supabase_depois", index=False)
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"xlsx": str(xlsx), "manifest": str(manifest)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corrige coordenadas do GEOARC001 em pontos_coleta usando KMZ oficial.")
    parser.add_argument("--project-id", type=int, default=190)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance-m", type=float, default=1.0)
    parser.add_argument("--apply", action="store_true", help="Aplica os updates no Supabase. Sem esta flag roda somente auditoria.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    reference = read_kml_point_coordinates(args.reference)
    if reference.empty:
        raise RuntimeError(f"Nenhum ponto lido do KMZ/KML: {args.reference}")

    engine = get_engine(args.env_file)
    before = fetch_points(engine, args.project_id)
    if before.empty:
        raise RuntimeError(f"Nenhum ponto encontrado em pontos_coleta para id_projeto={args.project_id}")

    comparison = build_comparison(before, reference, args.tolerance_m)
    updates = comparison[comparison["aplicar_update"]].copy()
    missing_reference = comparison[comparison["status_correcao"] == "ponto_sem_referencia"].copy()
    updated_rows = apply_updates(engine, updates) if args.apply and not updates.empty else 0
    after = fetch_points(engine, args.project_id) if args.apply else None

    summary = {
        "project_id": int(args.project_id),
        "reference": str(args.reference),
        "env_file": str(args.env_file),
        "apply": bool(args.apply),
        "tolerance_m": float(args.tolerance_m),
        "reference_points": int(reference["Ponto"].nunique()),
        "supabase_rows_before": int(len(before)),
        "supabase_points_before": int(before["nome_ponto"].nunique()),
        "rows_to_update": int(len(updates)),
        "rows_updated": int(updated_rows),
        "rows_without_reference": int(len(missing_reference)),
        "max_distance_before_m": float(pd.to_numeric(comparison["distancia_m"], errors="coerce").max()),
        "status_counts_before": comparison["status_correcao"].value_counts(dropna=False).to_dict(),
    }
    if after is not None:
        after_comparison = build_comparison(after, reference, args.tolerance_m)
        summary["status_counts_after"] = after_comparison["status_correcao"].value_counts(dropna=False).to_dict()
        summary["max_distance_after_m"] = float(pd.to_numeric(after_comparison["distancia_m"], errors="coerce").max())

    outputs = write_audit(args.output_dir, stamp, summary, reference, before, comparison, after)
    summary["outputs"] = outputs
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 2 if not missing_reference.empty else 0


if __name__ == "__main__":
    raise SystemExit(main())
