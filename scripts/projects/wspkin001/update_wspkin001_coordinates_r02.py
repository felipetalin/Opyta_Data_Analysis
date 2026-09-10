from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine  # noqa: E402


PROJECT_ID = 211
COORDINATES = {
    "PT_01": (-17.11137946, -46.95024449),
    "PT_02": (-17.14039444, -47.01674724),
    "PT_03": (-17.13333091, -46.94114619),
    "PT_04": (-17.11435337, -46.90079376),
    "PT_05": (-17.10317134, -46.84686704),
    "PT_06": (-17.13558594, -46.91847559),
    "PT_07": (-17.11943072, -46.90675106),
    "PT_08": (-17.12257486, -46.94465538),
    "PT_09": (-17.11897500, -46.82032600),
    "PT_10": (-17.13065849, -46.88515517),
}


def scalar(conn, sql: str, **params):
    return conn.execute(text(sql), params).scalar_one()


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    backup_points = f"backup_pontos_wspkin001_coordenadas_r02_{stamp}"
    backup_consolidated = f"backup_biota_wspkin001_coordenadas_r02_{stamp}"
    values_sql = ",\n".join(
        f"('{point}', {lat:.8f}, {lon:.8f})"
        for point, (lat, lon) in COORDINATES.items()
    )
    engine = get_engine()
    with engine.begin() as conn:
        before = conn.execute(
            text(
                """
                SELECT c.nome_campanha, p.nome_ponto,
                       p.latitude::float8 AS latitude,
                       p.longitude::float8 AS longitude
                FROM public.pontos_coleta p
                JOIN public.campanhas c USING (id_campanha)
                WHERE p.id_projeto = :project_id
                ORDER BY c.nome_campanha, p.nome_ponto
                """
            ),
            {"project_id": PROJECT_ID},
        ).mappings().all()
        if len(before) != 20:
            raise RuntimeError(f"Esperadas 20 linhas ponto-campanha; encontradas {len(before)}.")
        found_points = {row["nome_ponto"] for row in before}
        if found_points != set(COORDINATES):
            raise RuntimeError(f"Pontos divergentes: banco={sorted(found_points)}")

        consolidated_before = scalar(
            conn,
            "SELECT count(*) FROM public.biota_analise_consolidada WHERE id_projeto=:project_id",
            project_id=PROJECT_ID,
        )
        if consolidated_before != 368:
            raise RuntimeError(
                f"Esperadas 368 linhas consolidadas; encontradas {consolidated_before}."
            )

        conn.execute(
            text(
                f"CREATE TABLE public.{backup_points} AS "
                "SELECT * FROM public.pontos_coleta WHERE id_projeto=:project_id"
            ),
            {"project_id": PROJECT_ID},
        )
        conn.execute(
            text(
                f"CREATE TABLE public.{backup_consolidated} AS "
                "SELECT * FROM public.biota_analise_consolidada WHERE id_projeto=:project_id"
            ),
            {"project_id": PROJECT_ID},
        )

        conn.execute(
            text(
                f"""
                WITH coord(nome_ponto, latitude, longitude) AS (
                    VALUES {values_sql}
                )
                UPDATE public.pontos_coleta p
                SET latitude=coord.latitude, longitude=coord.longitude
                FROM coord
                WHERE p.id_projeto=:project_id AND p.nome_ponto=coord.nome_ponto
                """
            ),
            {"project_id": PROJECT_ID},
        )
        conn.execute(
            text(
                """
                UPDATE public.biota_analise_consolidada b
                SET latitude=p.latitude, longitude=p.longitude
                FROM public.pontos_coleta p
                JOIN public.campanhas c ON c.id_campanha=p.id_campanha
                WHERE b.id_projeto=:project_id
                  AND p.id_projeto=b.id_projeto
                  AND p.nome_ponto=b.nome_ponto
                  AND c.nome_campanha=b.nome_campanha
                """
            ),
            {"project_id": PROJECT_ID},
        )

        after = conn.execute(
            text(
                """
                SELECT c.nome_campanha, p.nome_ponto,
                       p.latitude::float8 AS latitude,
                       p.longitude::float8 AS longitude
                FROM public.pontos_coleta p
                JOIN public.campanhas c USING (id_campanha)
                WHERE p.id_projeto=:project_id
                ORDER BY c.nome_campanha, p.nome_ponto
                """
            ),
            {"project_id": PROJECT_ID},
        ).mappings().all()
        mismatches = []
        for row in after:
            expected = COORDINATES[row["nome_ponto"]]
            if abs(row["latitude"] - expected[0]) > 1e-10 or abs(row["longitude"] - expected[1]) > 1e-10:
                mismatches.append(dict(row))
        consolidated_mismatch = scalar(
            conn,
            """
            SELECT count(*)
            FROM public.biota_analise_consolidada b
            JOIN public.pontos_coleta p ON p.id_projeto=b.id_projeto AND p.nome_ponto=b.nome_ponto
            JOIN public.campanhas c ON c.id_campanha=p.id_campanha AND c.nome_campanha=b.nome_campanha
            WHERE b.id_projeto=:project_id
              AND (b.latitude IS DISTINCT FROM p.latitude OR b.longitude IS DISTINCT FROM p.longitude)
            """,
            project_id=PROJECT_ID,
        )
        if mismatches or consolidated_mismatch:
            raise RuntimeError(
                f"Falha de validacao: pontos={len(mismatches)}, consolidado={consolidated_mismatch}."
            )

    before_by_key = {(r["nome_campanha"], r["nome_ponto"]): r for r in before}
    changes = []
    for row in after:
        old = before_by_key[(row["nome_campanha"], row["nome_ponto"])]
        changes.append(
            {
                "campanha": row["nome_campanha"],
                "ponto": row["nome_ponto"],
                "latitude_antes": old["latitude"],
                "longitude_antes": old["longitude"],
                "latitude_depois": row["latitude"],
                "longitude_depois": row["longitude"],
                "alterado": old["latitude"] != row["latitude"] or old["longitude"] != row["longitude"],
            }
        )
    audit_dir = Path("outputs/validacoes/wspkin001_coordenadas_r02_20260904")
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / f"{stamp}_auditoria_coordenadas_wspkin001_r02.json"
    payload = {
        "status": "OK",
        "project_id": PROJECT_ID,
        "applied_at_utc": stamp,
        "backup_points": f"public.{backup_points}",
        "backup_consolidated": f"public.{backup_consolidated}",
        "point_campaign_rows": len(after),
        "consolidated_rows": consolidated_before,
        "consolidated_coordinate_mismatches": consolidated_mismatch,
        "changes": changes,
    }
    audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**payload, "audit_path": str(audit_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
