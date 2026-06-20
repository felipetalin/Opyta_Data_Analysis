from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from normalize_geoher001_bentos_taxonomy import get_engine


SOURCE_NAME = "Atopsyche"
TARGET_NAME = "Atopsyche sp."
OUTPUT_DIR = Path("outputs/_migration/geoher001_bentos_taxonomy")


def fetch_taxa(conn) -> list[dict]:
    rows = conn.execute(
        text(
            """
            SELECT id_especie, nome_cientifico, filo, classe, ordem, familia, genero
            FROM public.especies
            WHERE nome_cientifico IN (
                'Rhynchobdellida',
                'Tubificida',
                'Ostracoda',
                'Atopsyche',
                'Atopsyche sp.'
            )
            ORDER BY nome_cientifico, id_especie
            """
        )
    ).mappings()
    return [dict(row) for row in rows]


def species_id(rows: list[dict], name: str) -> int:
    matches = [int(row["id_especie"]) for row in rows if row["nome_cientifico"] == name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one species named {name!r}; found {matches}.")
    return matches[0]


def count_references(conn, species_id_value: int) -> dict[str, int]:
    rows = conn.execute(
        text(
            """
            SELECT conrelid::regclass::text AS table_name, a.attname AS column_name
            FROM pg_constraint c
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS ck(attnum, ord) ON true
            JOIN pg_attribute a
              ON a.attrelid = c.conrelid
             AND a.attnum = ck.attnum
            WHERE c.contype = 'f'
              AND c.confrelid = 'public.especies'::regclass
            ORDER BY table_name, column_name
            """
        )
    ).mappings()

    counts: dict[str, int] = {}
    for row in rows:
        table_name = str(row["table_name"])
        column_name = str(row["column_name"])
        count = conn.execute(
            text(
                f'SELECT count(*) FROM {table_name} '
                f'WHERE "{column_name}" = :species_id'
            ),
            {"species_id": species_id_value},
        ).scalar_one()
        if count:
            counts[f"{table_name}.{column_name}"] = int(count)
    return counts


def duplicate_rows(conn, source_id: int, target_id: int) -> list[dict]:
    rows = conn.execute(
        text(
            """
            SELECT source.id_resultado_bento AS source_result_id,
                   target.id_resultado_bento AS target_result_id,
                   source.id_esforco,
                   source.abundancia,
                   source.tipo_amostragem
            FROM public.resultados_zoobentos source
            JOIN public.resultados_zoobentos target
              ON target.id_esforco = source.id_esforco
             AND target.id_especie = :target_id
             AND target.abundancia IS NOT DISTINCT FROM source.abundancia
             AND target.tipo_amostragem IS NOT DISTINCT FROM source.tipo_amostragem
            WHERE source.id_especie = :source_id
            ORDER BY source.id_resultado_bento
            """
        ),
        {"source_id": source_id, "target_id": target_id},
    ).mappings()
    return [dict(row) for row in rows]


def apply_changes(
    conn,
    stamp: str,
    source_id: int,
    target_id: int,
) -> dict:
    species_backup = f"backup_geoher001_bentos_taxa_{stamp}_species"
    results_backup = f"backup_geoher001_bentos_taxa_{stamp}_zoobentos"

    conn.execute(
        text(
            f"""
            CREATE TABLE public.{species_backup} AS
            SELECT *
            FROM public.especies
            WHERE id_especie IN (:source_id, :target_id)
               OR nome_cientifico IN ('Rhynchobdellida', 'Tubificida', 'Ostracoda')
            """
        ),
        {"source_id": source_id, "target_id": target_id},
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{results_backup} AS
            SELECT *
            FROM public.resultados_zoobentos
            WHERE id_especie IN (:source_id, :target_id)
            """
        ),
        {"source_id": source_id, "target_id": target_id},
    )

    taxonomy_update = conn.execute(
        text(
            """
            UPDATE public.especies
            SET familia = CASE
                    WHEN nome_cientifico = 'Tubificida' THEN 'Naididae'
                    WHEN nome_cientifico IN ('Rhynchobdellida', 'Ostracoda') THEN NULL
                    WHEN nome_cientifico = 'Atopsyche sp.' THEN 'Hydrobiosidae'
                    ELSE familia
                END,
                ordem = CASE
                    WHEN nome_cientifico = 'Ostracoda' THEN NULL
                    ELSE ordem
                END,
                genero = CASE
                    WHEN nome_cientifico = 'Atopsyche sp.' THEN 'Atopsyche'
                    ELSE genero
                END
            WHERE nome_cientifico IN (
                'Rhynchobdellida',
                'Tubificida',
                'Ostracoda',
                'Atopsyche sp.'
            )
            """
        )
    )

    duplicate_delete = conn.execute(
        text(
            """
            DELETE FROM public.resultados_zoobentos source
            WHERE source.id_especie = :source_id
              AND EXISTS (
                  SELECT 1
                  FROM public.resultados_zoobentos target
                  WHERE target.id_esforco = source.id_esforco
                    AND target.id_especie = :target_id
                    AND target.abundancia IS NOT DISTINCT FROM source.abundancia
                    AND target.tipo_amostragem IS NOT DISTINCT FROM source.tipo_amostragem
              )
            """
        ),
        {"source_id": source_id, "target_id": target_id},
    )

    result_transfer = conn.execute(
        text(
            """
            UPDATE public.resultados_zoobentos
            SET id_especie = :target_id
            WHERE id_especie = :source_id
            """
        ),
        {"source_id": source_id, "target_id": target_id},
    )

    remaining_references = count_references(conn, source_id)
    if remaining_references:
        raise RuntimeError(
            f"Source taxon still has references after merge: {remaining_references}"
        )

    species_delete = conn.execute(
        text("DELETE FROM public.especies WHERE id_especie = :source_id"),
        {"source_id": source_id},
    )

    return {
        "backup_tables": [
            f"public.{species_backup}",
            f"public.{results_backup}",
        ],
        "taxonomy_rows_updated": int(taxonomy_update.rowcount or 0),
        "duplicate_results_deleted": int(duplicate_delete.rowcount or 0),
        "exclusive_results_transferred": int(result_transfer.rowcount or 0),
        "source_species_deleted": int(species_delete.rowcount or 0),
    }


def verify(conn, source_id: int, target_id: int) -> dict:
    source_exists = conn.execute(
        text("SELECT count(*) FROM public.especies WHERE id_especie = :source_id"),
        {"source_id": source_id},
    ).scalar_one()
    target = conn.execute(
        text(
            """
            SELECT id_especie, nome_cientifico, filo, classe, ordem, familia, genero
            FROM public.especies
            WHERE id_especie = :target_id
            """
        ),
        {"target_id": target_id},
    ).mappings().one()
    pending = conn.execute(
        text(
            """
            SELECT nome_cientifico, familia
            FROM public.especies
            WHERE nome_cientifico IN ('Rhynchobdellida', 'Tubificida', 'Ostracoda')
            ORDER BY nome_cientifico
            """
        )
    ).mappings()
    target_results = conn.execute(
        text(
            """
            SELECT count(*) AS records, sum(coalesce(abundancia, 0)) AS abundance
            FROM public.resultados_zoobentos
            WHERE id_especie = :target_id
            """
        ),
        {"target_id": target_id},
    ).mappings().one()

    verification = {
        "source_exists": int(source_exists),
        "source_references": count_references(conn, source_id),
        "target": dict(target),
        "pending_taxa": [dict(row) for row in pending],
        "target_results": dict(target_results),
    }
    if verification["source_exists"] or verification["source_references"]:
        raise RuntimeError(f"Atopsyche merge verification failed: {verification}")
    if target["nome_cientifico"] != TARGET_NAME or target["familia"] != "Hydrobiosidae":
        raise RuntimeError(f"Canonical target verification failed: {dict(target)}")
    return verification


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve pending GEOHER001 benthos taxonomy and merge Atopsyche."
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    stamp_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    table_stamp = stamp_utc.lower().replace("t", "_").replace("z", "")
    engine = get_engine(args.env_file)

    with engine.connect() as conn:
        before = fetch_taxa(conn)
        source_id = species_id(before, SOURCE_NAME)
        target_id = species_id(before, TARGET_NAME)
        source_references = count_references(conn, source_id)
        duplicates = duplicate_rows(conn, source_id, target_id)

    audit = {
        "timestamp_utc": stamp_utc,
        "mode": "apply" if args.apply else "dry_run",
        "source_taxon": SOURCE_NAME,
        "target_taxon": TARGET_NAME,
        "source_id": source_id,
        "target_id": target_id,
        "taxa_before": before,
        "source_references_before": source_references,
        "exact_duplicate_results_before": duplicates,
        "changes": {},
        "verification": {},
    }

    if args.apply:
        with engine.begin() as conn:
            audit["changes"] = apply_changes(
                conn,
                table_stamp,
                source_id,
                target_id,
            )
            audit["verification"] = verify(conn, source_id, target_id)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"{stamp_utc}_pending_taxa_audit.json"
    output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"mode={audit['mode']}")
    print(f"source_id={source_id}")
    print(f"target_id={target_id}")
    print(f"source_references_before={source_references}")
    print(f"exact_duplicate_results_before={len(duplicates)}")
    print(f"changes={audit['changes']}")
    print(f"audit={output.resolve()}")


if __name__ == "__main__":
    main()
