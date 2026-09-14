from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "logs" / "revisao_geoambiental_coordenadas"

DUCGEO_REFERENCE = {
    "ICTIO01": (-20.1632590877, -43.4136118424),
    "ICTIO02": (-20.1955096526, -43.4003222630),
    "ICTIO03": (-20.1926698287, -43.3569295261),
    "ICTIO04": (-20.1792346941, -43.3914422400),
    "ICTIO05": (-20.1893337084, -43.3577074087),
}


@dataclass(frozen=True)
class RunOutputs:
    xlsx: Path
    json: Path


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


def normalize_code(value: object) -> str:
    return str(value or "").replace("\xa0", " ").strip()


def normalize_point(value: object) -> str:
    text_value = str(value or "").strip().upper()
    return "".join(ch for ch in text_value if ch.isalnum())


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def max_pairwise_distance(coords: list[tuple[float, float]]) -> float:
    if len(coords) <= 1:
        return 0.0
    max_distance = 0.0
    for i, coord_a in enumerate(coords):
        for coord_b in coords[i + 1 :]:
            max_distance = max(max_distance, haversine_m(*coord_a, *coord_b))
    return max_distance


def fetch_points(conn, code: str) -> pd.DataFrame:
    query = text(
        """
        SELECT
            pc.id_ponto_coleta,
            p.codigo_interno_opyta,
            p.nome_projeto,
            c.nome_campanha,
            pc.nome_ponto,
            pc.latitude::double precision AS latitude,
            pc.longitude::double precision AS longitude
        FROM public.pontos_coleta pc
        JOIN public.projetos p ON p.id_projeto = pc.id_projeto
        LEFT JOIN public.campanhas c ON c.id_campanha = pc.id_campanha
        WHERE btrim(replace(p.codigo_interno_opyta, chr(160), ' ')) = :code
        ORDER BY c.nome_campanha, pc.nome_ponto, pc.id_ponto_coleta
        """
    )
    return pd.read_sql(query, conn, params={"code": code})


def fetch_consolidated(conn, code: str) -> pd.DataFrame:
    query = text(
        """
        SELECT
            id_resultado_pk,
            codigo_interno_opyta,
            nome_empresa,
            nome_projeto,
            nome_campanha,
            nome_ponto,
            grupo_biologico,
            latitude::double precision AS latitude,
            longitude::double precision AS longitude
        FROM public.biota_analise_consolidada
        WHERE btrim(replace(codigo_interno_opyta, chr(160), ' ')) = :code
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY nome_campanha, nome_ponto, grupo_biologico, id_resultado_pk
        """
    )
    return pd.read_sql(query, conn, params={"code": code})


def consolidated_variation(consolidated: pd.DataFrame, threshold_m: float) -> pd.DataFrame:
    if consolidated.empty:
        return pd.DataFrame()

    work = consolidated.copy()
    work["codigo_norm"] = work["codigo_interno_opyta"].map(normalize_code)
    unique_rows = work.drop_duplicates(
        ["codigo_norm", "nome_projeto", "nome_campanha", "nome_ponto", "latitude", "longitude"]
    )
    rows: list[dict[str, object]] = []
    for (code, project, point), group in unique_rows.groupby(
        ["codigo_norm", "nome_projeto", "nome_ponto"], dropna=False
    ):
        coords = list(group[["latitude", "longitude"]].drop_duplicates().itertuples(index=False, name=None))
        max_distance = max_pairwise_distance(coords)
        if max_distance > threshold_m:
            rows.append(
                {
                    "codigo_norm": code,
                    "nome_projeto": project,
                    "nome_ponto": point,
                    "campanhas": int(group["nome_campanha"].nunique()),
                    "pares_coord_distintos": int(len(coords)),
                    "distancia_max_m": float(max_distance),
                    "lat_min": float(group["latitude"].min()),
                    "lat_max": float(group["latitude"].max()),
                    "lon_min": float(group["longitude"].min()),
                    "lon_max": float(group["longitude"].max()),
                }
            )
    return pd.DataFrame(rows).sort_values("distancia_max_m", ascending=False) if rows else pd.DataFrame()


def ducgeo_reference_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ponto_norm": point, "latitude_ref": lat, "longitude_ref": lon}
            for point, (lat, lon) in DUCGEO_REFERENCE.items()
        ]
    )


def plan_ducgeo_points(points: pd.DataFrame, tolerance_m: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in points.iterrows():
        point_norm = normalize_point(row["nome_ponto"])
        ref = DUCGEO_REFERENCE.get(point_norm)
        if not ref:
            rows.append({**row.to_dict(), "status": "ponto_sem_referencia", "distancia_m": None})
            continue
        distance = haversine_m(row["latitude"], row["longitude"], ref[0], ref[1])
        rows.append(
            {
                **row.to_dict(),
                "ponto_norm": point_norm,
                "latitude_ref": ref[0],
                "longitude_ref": ref[1],
                "distancia_m": distance,
                "status": "corrigir" if distance > tolerance_m else "ok",
                "aplicar_update": distance > tolerance_m,
            }
        )
    return pd.DataFrame(rows)


def plan_ducgeo_consolidated(consolidated: pd.DataFrame, tolerance_m: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in consolidated.iterrows():
        point_norm = normalize_point(row["nome_ponto"])
        ref = DUCGEO_REFERENCE.get(point_norm)
        if not ref:
            rows.append({**row.to_dict(), "status": "ponto_sem_referencia", "distancia_m": None})
            continue
        distance = haversine_m(row["latitude"], row["longitude"], ref[0], ref[1])
        rows.append(
            {
                **row.to_dict(),
                "ponto_norm": point_norm,
                "latitude_ref": ref[0],
                "longitude_ref": ref[1],
                "distancia_m": distance,
                "status": "corrigir" if distance > tolerance_m else "ok",
                "aplicar_update": distance > tolerance_m,
            }
        )
    return pd.DataFrame(rows)


def plan_geoarc_consolidated(
    consolidated: pd.DataFrame, points: pd.DataFrame, tolerance_m: float
) -> pd.DataFrame:
    refs = points.copy()
    refs["key"] = refs["nome_campanha"].astype(str) + "|" + refs["nome_ponto"].astype(str)
    ref_map = {
        row["key"]: (float(row["latitude"]), float(row["longitude"]))
        for _, row in refs.dropna(subset=["latitude", "longitude"]).iterrows()
    }
    rows: list[dict[str, object]] = []
    for _, row in consolidated.iterrows():
        key = f"{row['nome_campanha']}|{row['nome_ponto']}"
        ref = ref_map.get(key)
        if not ref:
            rows.append({**row.to_dict(), "status": "sem_ponto_coleta", "distancia_m": None})
            continue
        distance = haversine_m(row["latitude"], row["longitude"], ref[0], ref[1])
        rows.append(
            {
                **row.to_dict(),
                "latitude_ref": ref[0],
                "longitude_ref": ref[1],
                "distancia_m": distance,
                "status": "corrigir" if distance > tolerance_m else "ok",
                "aplicar_update": distance > tolerance_m,
            }
        )
    return pd.DataFrame(rows)


def backup_tables(conn, stamp: str) -> dict[str, str]:
    suffix = stamp.lower().replace("z", "")
    tables = {
        "geoarc_bac": f"backup_bac_geoarc001_coords_{suffix}",
        "ducgeo_pc": f"backup_pc_ducgeo001_coords_{suffix}",
        "ducgeo_bac": f"backup_bac_ducgeo001_coords_{suffix}",
    }
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{tables['geoarc_bac']} AS
            SELECT * FROM public.biota_analise_consolidada
            WHERE btrim(replace(codigo_interno_opyta, chr(160), ' ')) = 'GEOARC001'
            """
        )
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{tables['ducgeo_pc']} AS
            SELECT pc.*
            FROM public.pontos_coleta pc
            JOIN public.projetos p ON p.id_projeto = pc.id_projeto
            WHERE btrim(replace(p.codigo_interno_opyta, chr(160), ' ')) = 'DUCGEO001'
            """
        )
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{tables['ducgeo_bac']} AS
            SELECT * FROM public.biota_analise_consolidada
            WHERE btrim(replace(codigo_interno_opyta, chr(160), ' ')) = 'DUCGEO001'
            """
        )
    )
    return tables


def apply_updates(conn, geoarc_plan: pd.DataFrame, duc_points_plan: pd.DataFrame, duc_bac_plan: pd.DataFrame) -> dict:
    update_bac = text(
        """
        UPDATE public.biota_analise_consolidada
        SET latitude = :latitude_ref,
            longitude = :longitude_ref
        WHERE id_resultado_pk = :id_resultado_pk
        """
    )
    update_pc = text(
        """
        UPDATE public.pontos_coleta
        SET latitude = :latitude_ref,
            longitude = :longitude_ref
        WHERE id_ponto_coleta = :id_ponto_coleta
        """
    )
    counts = {
        "geoarc_consolidated_updated": 0,
        "ducgeo_points_updated": 0,
        "ducgeo_consolidated_updated": 0,
    }
    for _, row in geoarc_plan[geoarc_plan["aplicar_update"] == True].iterrows():  # noqa: E712
        conn.execute(
            update_bac,
            {
                "id_resultado_pk": int(row["id_resultado_pk"]),
                "latitude_ref": float(row["latitude_ref"]),
                "longitude_ref": float(row["longitude_ref"]),
            },
        )
        counts["geoarc_consolidated_updated"] += 1

    for _, row in duc_points_plan[duc_points_plan["aplicar_update"] == True].iterrows():  # noqa: E712
        conn.execute(
            update_pc,
            {
                "id_ponto_coleta": int(row["id_ponto_coleta"]),
                "latitude_ref": float(row["latitude_ref"]),
                "longitude_ref": float(row["longitude_ref"]),
            },
        )
        counts["ducgeo_points_updated"] += 1

    for _, row in duc_bac_plan[duc_bac_plan["aplicar_update"] == True].iterrows():  # noqa: E712
        conn.execute(
            update_bac,
            {
                "id_resultado_pk": int(row["id_resultado_pk"]),
                "latitude_ref": float(row["latitude_ref"]),
                "longitude_ref": float(row["longitude_ref"]),
            },
        )
        counts["ducgeo_consolidated_updated"] += 1
    return counts


def status_counts(frame: pd.DataFrame) -> dict:
    if frame.empty or "status" not in frame.columns:
        return {}
    return {str(k): int(v) for k, v in frame["status"].value_counts(dropna=False).to_dict().items()}


def build_outputs(output_dir: Path, stamp: str, apply: bool) -> RunOutputs:
    mode = "apply" if apply else "dry_run"
    return RunOutputs(
        xlsx=output_dir / f"{stamp}_{mode}_fix_geoambiental_coordinates.xlsx",
        json=output_dir / f"{stamp}_{mode}_fix_geoambiental_coordinates.json",
    )


def write_audit(outputs: RunOutputs, sheets: dict[str, pd.DataFrame], summary: dict) -> None:
    outputs.xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(outputs.xlsx, engine="openpyxl") as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="00_resumo", index=False)
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name[:31], index=False)
    outputs.json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> dict:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    engine = get_engine(args.env_file)
    outputs = build_outputs(args.output_dir, stamp, args.apply)

    with engine.connect() as conn:
        geoarc_points_before = fetch_points(conn, "GEOARC001")
        geoarc_bac_before = fetch_consolidated(conn, "GEOARC001")
        duc_points_before = fetch_points(conn, "DUCGEO001")
        duc_bac_before = fetch_consolidated(conn, "DUCGEO001")

    geoarc_plan = plan_geoarc_consolidated(geoarc_bac_before, geoarc_points_before, args.tolerance_m)
    duc_points_plan = plan_ducgeo_points(duc_points_before, args.tolerance_m)
    duc_bac_plan = plan_ducgeo_consolidated(duc_bac_before, args.tolerance_m)

    backups: dict[str, str] = {}
    update_counts = {
        "geoarc_consolidated_updated": 0,
        "ducgeo_points_updated": 0,
        "ducgeo_consolidated_updated": 0,
    }

    if args.apply:
        with engine.begin() as conn:
            backups = backup_tables(conn, stamp)
            update_counts = apply_updates(conn, geoarc_plan, duc_points_plan, duc_bac_plan)

    with engine.connect() as conn:
        geoarc_points_after = fetch_points(conn, "GEOARC001")
        geoarc_bac_after = fetch_consolidated(conn, "GEOARC001")
        duc_points_after = fetch_points(conn, "DUCGEO001")
        duc_bac_after = fetch_consolidated(conn, "DUCGEO001")

    geoarc_after_plan = plan_geoarc_consolidated(geoarc_bac_after, geoarc_points_after, args.tolerance_m)
    duc_points_after_plan = plan_ducgeo_points(duc_points_after, args.tolerance_m)
    duc_bac_after_plan = plan_ducgeo_consolidated(duc_bac_after, args.tolerance_m)

    geoarc_variation_before = consolidated_variation(geoarc_bac_before, args.tolerance_m)
    geoarc_variation_after = consolidated_variation(geoarc_bac_after, args.tolerance_m)
    duc_variation_before = consolidated_variation(duc_bac_before, args.tolerance_m)
    duc_variation_after = consolidated_variation(duc_bac_after, args.tolerance_m)

    summary = {
        "stamp": stamp,
        "apply": bool(args.apply),
        "tolerance_m": float(args.tolerance_m),
        "geoarc_consolidated_rows": int(len(geoarc_bac_before)),
        "geoarc_consolidated_to_update": int(geoarc_plan.get("aplicar_update", pd.Series(dtype=bool)).fillna(False).sum()),
        "geoarc_status_before": status_counts(geoarc_plan),
        "geoarc_status_after": status_counts(geoarc_after_plan),
        "geoarc_points_with_variation_before": int(len(geoarc_variation_before)),
        "geoarc_points_with_variation_after": int(len(geoarc_variation_after)),
        "ducgeo_points_rows": int(len(duc_points_before)),
        "ducgeo_points_to_update": int(duc_points_plan.get("aplicar_update", pd.Series(dtype=bool)).fillna(False).sum()),
        "ducgeo_points_status_before": status_counts(duc_points_plan),
        "ducgeo_points_status_after": status_counts(duc_points_after_plan),
        "ducgeo_consolidated_rows": int(len(duc_bac_before)),
        "ducgeo_consolidated_to_update": int(duc_bac_plan.get("aplicar_update", pd.Series(dtype=bool)).fillna(False).sum()),
        "ducgeo_consolidated_status_before": status_counts(duc_bac_plan),
        "ducgeo_consolidated_status_after": status_counts(duc_bac_after_plan),
        "ducgeo_points_with_variation_before": int(len(duc_variation_before)),
        "ducgeo_points_with_variation_after": int(len(duc_variation_after)),
        "updates": update_counts,
        "backups": backups,
        "outputs": {"xlsx": str(outputs.xlsx), "json": str(outputs.json)},
    }
    sheets = {
        "01_geoarc_plan": geoarc_plan,
        "02_ducgeo_pontos_plan": duc_points_plan,
        "03_ducgeo_consolidado_plan": duc_bac_plan,
        "04_geoarc_variacao_antes": geoarc_variation_before,
        "05_geoarc_variacao_depois": geoarc_variation_after,
        "06_ducgeo_variacao_antes": duc_variation_before,
        "07_ducgeo_variacao_depois": duc_variation_after,
        "08_geoarc_status_depois": geoarc_after_plan,
        "09_ducgeo_pontos_depois": duc_points_after_plan,
        "10_ducgeo_consol_depois": duc_bac_after_plan,
        "11_referencia_ducgeo": ducgeo_reference_frame(),
    }
    write_audit(outputs, sheets, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Corrige coordenadas usadas pelo Geoambiental para GEOARC001 e DUCGEO001."
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance-m", type=float, default=5.0)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    summary = run(parse_args(argv))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
