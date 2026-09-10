"""Merge the misspelling Trichocerca pussilla into Trichocerca pusilla."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text


SOURCE_ID = 100
TARGET_ID = 4046
SOURCE_NAME = "Trichocerca pussilla"
TARGET_NAME = "Trichocerca pusilla"
RESULTS_DIR = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados")
DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")


def engine():
    sys.path.insert(0, str(DATA_ROOT))
    from core.engine import get_engine  # noqa: PLC0415

    return get_engine()


def scalar(conn, sql: str, **params):
    return conn.execute(text(sql), params).scalar()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S").lower()
    db = engine()
    report = {"mode": "apply" if args.apply else "dry_run", "source_id": SOURCE_ID, "target_id": TARGET_ID, "backups": []}
    try:
        with db.begin() as conn:
            source = conn.execute(text("SELECT * FROM public.especies WHERE id_especie=:id AND nome_cientifico=:name"), {"id": SOURCE_ID, "name": SOURCE_NAME}).mappings().one_or_none()
            target = conn.execute(text("SELECT * FROM public.especies WHERE id_especie=:id AND nome_cientifico=:name"), {"id": TARGET_ID, "name": TARGET_NAME}).mappings().one_or_none()
            if source is None or target is None:
                raise RuntimeError("Cadastros fonte/destino não correspondem ao preflight aprovado.")
            source_results = scalar(conn, "SELECT count(*) FROM public.resultados_zooplancton WHERE id_especie=:id", id=SOURCE_ID)
            collisions = scalar(conn, """SELECT count(*) FROM public.resultados_zooplancton a JOIN public.resultados_zooplancton b ON b.id_esforco=a.id_esforco AND b.id_especie=:target WHERE a.id_especie=:source""", source=SOURCE_ID, target=TARGET_ID)
            source_consolidated = scalar(conn, "SELECT count(*) FROM public.biota_analise_consolidada WHERE nome_cientifico=:name", name=SOURCE_NAME)
            report.update({"source_results_before": source_results, "collisions": collisions, "source_consolidated_before": source_consolidated})
            if collisions:
                raise RuntimeError(f"Fusão bloqueada: {collisions} colisões por esforço.")
            if args.apply:
                backup_species = f"backup_especies_trichocerca_r01_{stamp}"
                backup_results = f"backup_resultados_zoo_trichocerca_r01_{stamp}"
                backup_consolidated = f"backup_biota_trichocerca_r01_{stamp}"
                conn.execute(text(f"CREATE TABLE public.{backup_species} AS SELECT * FROM public.especies WHERE id_especie IN (:source,:target)"), {"source": SOURCE_ID, "target": TARGET_ID})
                conn.execute(text(f"CREATE TABLE public.{backup_results} AS SELECT * FROM public.resultados_zooplancton WHERE id_especie IN (:source,:target)"), {"source": SOURCE_ID, "target": TARGET_ID})
                conn.execute(text(f"CREATE TABLE public.{backup_consolidated} AS SELECT * FROM public.biota_analise_consolidada WHERE nome_cientifico IN (:source,:target)"), {"source": SOURCE_NAME, "target": TARGET_NAME})
                report["backups"] = [f"public.{backup_species}", f"public.{backup_results}", f"public.{backup_consolidated}"]

                moved = conn.execute(text("UPDATE public.resultados_zooplancton SET id_especie=:target WHERE id_especie=:source"), {"source": SOURCE_ID, "target": TARGET_ID}).rowcount or 0
                consolidated = conn.execute(
                    text("""UPDATE public.biota_analise_consolidada SET nome_cientifico=:target_name, reino=:reino, filo=:filo, classe=:classe, ordem=:ordem, familia=:familia, genero=:genero WHERE nome_cientifico=:source_name"""),
                    {"source_name": SOURCE_NAME, "target_name": TARGET_NAME, "reino": target["reino"], "filo": target["filo"], "classe": target["classe"], "ordem": target["ordem"], "familia": target["familia"], "genero": target["genero"]},
                ).rowcount or 0
                note = "R01 WSPKIN001: cadastro duplicado Trichocerca pussilla (id 100) fundido em Trichocerca pusilla (id 4046), validado por Catalogue of Life e WoRMS."
                conn.execute(text("""UPDATE public.especies SET observacoes=CASE WHEN observacoes IS NULL OR observacoes='' THEN :note WHEN position(:note in observacoes)>0 THEN observacoes ELSE observacoes || ' | ' || :note END WHERE id_especie=:target"""), {"note": note, "target": TARGET_ID})
                deleted = conn.execute(text("DELETE FROM public.especies WHERE id_especie=:source"), {"source": SOURCE_ID}).rowcount or 0
                report.update({"result_rows_moved": moved, "consolidated_rows_updated": consolidated, "source_species_deleted": deleted})

                remaining_results = scalar(conn, "SELECT count(*) FROM public.resultados_zooplancton WHERE id_especie=:source", source=SOURCE_ID)
                remaining_species = scalar(conn, "SELECT count(*) FROM public.especies WHERE id_especie=:source", source=SOURCE_ID)
                remaining_consolidated = scalar(conn, "SELECT count(*) FROM public.biota_analise_consolidada WHERE nome_cientifico=:source_name", source_name=SOURCE_NAME)
                if any((remaining_results, remaining_species, remaining_consolidated)):
                    raise RuntimeError("Verificação pós-fusão falhou; transação será revertida.")
                report.update({"remaining_source_results": remaining_results, "remaining_source_species": remaining_species, "remaining_source_consolidated": remaining_consolidated})
    finally:
        db.dispose()

    log_dir = RESULTS_DIR / "Controle_Taxonomico_R01" / "Auditoria"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{stamp}_{report['mode']}_merge_trichocerca.json"
    log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
