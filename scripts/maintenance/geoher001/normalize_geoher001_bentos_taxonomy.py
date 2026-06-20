from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_CODE = "GEOHER001"
GROUP = "Zoobentos"
INSECT_ORDERS = (
    "Coleoptera",
    "Diptera",
    "Ephemeroptera",
    "Hemiptera",
    "Lepidoptera",
    "Megaloptera",
    "Odonata",
    "Plecoptera",
    "Trichoptera",
)


def get_engine(env_file: str) -> object:
    load_dotenv(env_file)
    values = {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    url = (
        f"postgresql://{quote_plus(values['DB_USER'])}:{quote_plus(values['DB_PASSWORD'])}"
        f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}?connect_timeout=15"
    )
    return create_engine(url)


def affected_sql() -> str:
    orders = ", ".join(f"'{value}'" for value in INSECT_ORDERS)
    return f"""
        WITH project_taxa AS (
            SELECT DISTINCT s.id_especie
            FROM public.resultados_zoobentos rz
            JOIN public.esforcos_amostragem e ON e.id_esforco = rz.id_esforco
            JOIN public.pontos_coleta pc ON pc.id_ponto_coleta = e.id_ponto_coleta
            JOIN public.projetos p ON p.id_projeto = pc.id_projeto
            JOIN public.especies s ON s.id_especie = rz.id_especie
            WHERE trim(p.codigo_interno_opyta) = :project_code
              AND e.grupo_biologico = :group_name
        )
        SELECT s.id_especie, s.nome_cientifico, s.filo, s.classe, s.ordem,
               s.familia, s.genero
        FROM public.especies s
        JOIN project_taxa pt ON pt.id_especie = s.id_especie
        WHERE trim(coalesce(s.filo, '')) = 'Artropoda'
           OR (
               trim(coalesce(s.filo, '')) IN ('Artropoda', 'Arthropoda')
               AND trim(coalesce(s.classe, '')) IN ({orders})
               AND trim(coalesce(s.ordem, '')) = 'Insecta'
           )
           OR (
               trim(coalesce(s.filo, '')) = 'Annelida'
               AND trim(coalesce(s.classe, '')) IN ('Rhynchobdellida', 'Tubificida')
               AND trim(coalesce(s.ordem, '')) = 'Clitellata'
           )
           OR (
               trim(coalesce(s.filo, '')) = 'Mollusca'
               AND trim(coalesce(s.classe, '')) = 'Veneroida'
               AND trim(coalesce(s.ordem, '')) = 'Bivalvia'
           )
           OR (
               trim(coalesce(s.familia, '')) <> ''
               AND lower(trim(s.familia)) = lower(trim(coalesce(s.genero, '')))
           )
           OR trim(coalesce(s.genero, '')) ~* '\\s+sp\\.?$'
        ORDER BY s.id_especie
    """


def fetch_affected(conn) -> list[dict]:
    rows = conn.execute(
        text(affected_sql()),
        {
            "project_code": PROJECT_CODE,
            "group_name": GROUP,
        },
    ).mappings()
    return [dict(row) for row in rows]


def fetch_species(conn, ids: list[int]) -> list[dict]:
    if not ids:
        return []
    id_list = ", ".join(str(int(value)) for value in sorted(ids))
    rows = conn.execute(
        text(
            f"""
            SELECT id_especie, nome_cientifico, filo, classe, ordem, familia, genero
            FROM public.especies
            WHERE id_especie IN ({id_list})
            ORDER BY id_especie
            """
        )
    ).mappings()
    return [dict(row) for row in rows]


def apply_updates(conn, ids: list[int], backup_table: str) -> dict[str, int]:
    id_list = ", ".join(str(int(value)) for value in sorted(ids))
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{backup_table} AS
            SELECT *
            FROM public.especies
            WHERE id_especie IN ({id_list})
            """
        )
    )

    results: dict[str, int] = {}
    result = conn.execute(
        text(
            f"""
            UPDATE public.especies
            SET filo = 'Arthropoda'
            WHERE id_especie IN ({id_list})
              AND trim(coalesce(filo, '')) = 'Artropoda'
            """
        )
    )
    results["filo_artropoda_para_arthropoda"] = int(result.rowcount or 0)

    orders = ", ".join(f"'{value}'" for value in INSECT_ORDERS)
    result = conn.execute(
        text(
            f"""
            UPDATE public.especies
            SET ordem = classe,
                classe = 'Insecta'
            WHERE id_especie IN ({id_list})
              AND trim(coalesce(filo, '')) = 'Arthropoda'
              AND trim(coalesce(classe, '')) IN ({orders})
              AND trim(coalesce(ordem, '')) = 'Insecta'
            """
        )
    )
    results["insecta_classe_ordem"] = int(result.rowcount or 0)

    result = conn.execute(
        text(
            f"""
            UPDATE public.especies
            SET ordem = classe,
                classe = 'Clitellata'
            WHERE id_especie IN ({id_list})
              AND trim(coalesce(filo, '')) = 'Annelida'
              AND trim(coalesce(classe, '')) IN ('Rhynchobdellida', 'Tubificida')
              AND trim(coalesce(ordem, '')) = 'Clitellata'
            """
        )
    )
    results["clitellata_classe_ordem"] = int(result.rowcount or 0)

    result = conn.execute(
        text(
            f"""
            UPDATE public.especies
            SET classe = 'Bivalvia',
                ordem = 'Veneroida'
            WHERE id_especie IN ({id_list})
              AND trim(coalesce(filo, '')) = 'Mollusca'
              AND trim(coalesce(classe, '')) = 'Veneroida'
              AND trim(coalesce(ordem, '')) = 'Bivalvia'
            """
        )
    )
    results["bivalvia_classe_ordem"] = int(result.rowcount or 0)

    result = conn.execute(
        text(
            f"""
            UPDATE public.especies
            SET genero = NULL
            WHERE id_especie IN ({id_list})
              AND trim(coalesce(familia, '')) <> ''
              AND lower(trim(familia)) = lower(trim(coalesce(genero, '')))
            """
        )
    )
    results["familia_removida_do_genero"] = int(result.rowcount or 0)

    result = conn.execute(
        text(
            f"""
            UPDATE public.especies
            SET genero = regexp_replace(trim(genero), '\\s+sp\\.?$', '', 'i')
            WHERE id_especie IN ({id_list})
              AND trim(coalesce(genero, '')) ~* '\\s+sp\\.?$'
            """
        )
    )
    results["sp_removido_do_genero"] = int(result.rowcount or 0)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit and normalize GEOHER001 benthos taxonomy across all campaigns."
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--output-dir",
        default="outputs/_migration/geoher001_bentos_taxonomy",
    )
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_table = f"backup_geoher001_bentos_taxonomy_{stamp.lower()}"
    engine = get_engine(args.env_file)

    with engine.connect() as conn:
        before = fetch_affected(conn)

    audit = {
        "timestamp_utc": stamp,
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "period": "all_campaigns",
        "mode": "apply" if args.apply else "dry_run",
        "affected_before": before,
        "affected_count_before": len(before),
        "backup_table": None,
        "updates": {},
        "species_after": [],
        "remaining_affected": [],
    }

    if args.apply and before:
        ids = [int(row["id_especie"]) for row in before]
        with engine.begin() as conn:
            audit["updates"] = apply_updates(conn, ids, backup_table)
            remaining = fetch_affected(conn)
            if remaining:
                raise RuntimeError(
                    f"Taxonomy verification failed; {len(remaining)} target rows remain."
                )
            audit["species_after"] = fetch_species(conn, ids)
            audit["remaining_affected"] = remaining
            audit["backup_table"] = f"public.{backup_table}"

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{stamp}_taxonomy_audit.json"
    output_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"mode={audit['mode']}")
    print(f"affected_before={audit['affected_count_before']}")
    print(f"backup_table={audit['backup_table']}")
    print(f"updates={audit['updates']}")
    print(f"audit={output_path.resolve()}")


if __name__ == "__main__":
    main()
