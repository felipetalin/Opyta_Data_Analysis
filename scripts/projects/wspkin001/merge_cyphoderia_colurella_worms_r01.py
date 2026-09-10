"""Apply approved Cyphoderia and Colurella canonical merges for R01."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text


DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
RESULTS_DIR = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Resultados")
MERGES = [
    {
        "label": "cyphoderia",
        "source_id": 4010,
        "source_name": "Cyphoderia ampula",
        "target_id": 82,
        "target_name": "Cyphoderia ampulla",
        "taxonomy": {
            "reino": "Chromista",
            "filo": "Cercozoa",
            "classe": "Imbricatea",
            "ordem": "Euglyphida",
            "familia": "Cyphoderiidae",
            "genero": "Cyphoderia",
            "autor_e_ano": "(Ehrenberg, 1840) Leidy, 1878",
        },
        "note": "R01 WSPKIN001: fusão Cyphoderia ampula em Cyphoderia ampulla; classificação WoRMS AphiaID 136874, decisão do usuário em 2026-09-04.",
    },
    {
        "label": "colurella",
        "source_id": 90,
        "source_name": "Colurella miníma",
        "target_id": 131,
        "target_name": "Colurella minima",
        "taxonomy": {
            "reino": "Animalia",
            "filo": "Rotifera",
            "classe": "Eurotatoria",
            "ordem": "Ploima",
            "familia": "Lepadellidae",
            "genero": "Colurella",
            "autor_e_ano": "N.A.",
        },
        "note": "R01 WSPKIN001: fusão da grafia Colurella miníma em Colurella minima, sem acento, com gênero Colurella; decisão do usuário em 2026-09-04.",
    },
]


def get_engine():
    sys.path.insert(0, str(DATA_ROOT))
    from core.engine import get_engine as factory  # noqa: PLC0415

    return factory()


def scalar(conn, sql: str, **params):
    return conn.execute(text(sql), params).scalar()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S").lower()
    report = {"mode": "apply" if args.apply else "dry_run", "merges": [], "backups": []}
    engine = get_engine()
    try:
        with engine.begin() as conn:
            for merge in MERGES:
                source = conn.execute(text("SELECT * FROM public.especies WHERE id_especie=:id AND nome_cientifico=:name"), {"id": merge["source_id"], "name": merge["source_name"]}).mappings().one_or_none()
                target = conn.execute(text("SELECT * FROM public.especies WHERE id_especie=:id AND nome_cientifico=:name"), {"id": merge["target_id"], "name": merge["target_name"]}).mappings().one_or_none()
                if source is None or target is None:
                    raise RuntimeError(f"Preflight falhou para {merge['label']}: cadastro fonte/destino divergente.")
                collisions = scalar(conn, """SELECT count(*) FROM public.resultados_zooplancton a JOIN public.resultados_zooplancton b ON b.id_esforco=a.id_esforco AND b.id_especie=:target WHERE a.id_especie=:source""", source=merge["source_id"], target=merge["target_id"])
                source_results = scalar(conn, "SELECT count(*) FROM public.resultados_zooplancton WHERE id_especie=:source", source=merge["source_id"])
                if collisions:
                    raise RuntimeError(f"Fusão {merge['label']} bloqueada por {collisions} colisões de esforço.")
                report["merges"].append({"label": merge["label"], "source_results": source_results, "collisions": collisions})

            if args.apply:
                ids = [item[key] for item in MERGES for key in ("source_id", "target_id")]
                names = [item[key] for item in MERGES for key in ("source_name", "target_name")]
                backup_species = f"backup_especies_wspkin001_worms_r01_{stamp}"
                backup_results = f"backup_resultados_zoo_wspkin001_worms_r01_{stamp}"
                backup_consolidated = f"backup_biota_wspkin001_worms_r01_{stamp}"
                conn.execute(text(f"CREATE TABLE public.{backup_species} AS SELECT * FROM public.especies WHERE id_especie=ANY(:ids)"), {"ids": ids})
                conn.execute(text(f"CREATE TABLE public.{backup_results} AS SELECT * FROM public.resultados_zooplancton WHERE id_especie=ANY(:ids)"), {"ids": ids})
                conn.execute(text(f"CREATE TABLE public.{backup_consolidated} AS SELECT * FROM public.biota_analise_consolidada WHERE nome_cientifico=ANY(:names)"), {"names": names})
                report["backups"] = [f"public.{backup_species}", f"public.{backup_results}", f"public.{backup_consolidated}"]

                for merge, merge_report in zip(MERGES, report["merges"]):
                    taxonomy = merge["taxonomy"]
                    conn.execute(
                        text("""UPDATE public.especies SET reino=:reino,filo=:filo,classe=:classe,ordem=:ordem,familia=:familia,genero=:genero,autor_e_ano=:autor_e_ano,observacoes=CASE WHEN observacoes IS NULL OR observacoes='' THEN :note WHEN position(:note in observacoes)>0 THEN observacoes ELSE observacoes || ' | ' || :note END WHERE id_especie=:target"""),
                        {**taxonomy, "note": merge["note"], "target": merge["target_id"]},
                    )
                    moved = conn.execute(text("UPDATE public.resultados_zooplancton SET id_especie=:target WHERE id_especie=:source"), {"source": merge["source_id"], "target": merge["target_id"]}).rowcount or 0
                    consolidated = conn.execute(
                        text("""UPDATE public.biota_analise_consolidada SET nome_cientifico=:target_name,reino=:reino,filo=:filo,classe=:classe,ordem=:ordem,familia=:familia,genero=:genero WHERE nome_cientifico IN (:source_name,:target_name)"""),
                        {**{k: taxonomy[k] for k in ("reino", "filo", "classe", "ordem", "familia", "genero")}, "source_name": merge["source_name"], "target_name": merge["target_name"]},
                    ).rowcount or 0
                    deleted = conn.execute(text("DELETE FROM public.especies WHERE id_especie=:source"), {"source": merge["source_id"]}).rowcount or 0
                    remaining = {
                        "source_species": scalar(conn, "SELECT count(*) FROM public.especies WHERE id_especie=:source", source=merge["source_id"]),
                        "source_results": scalar(conn, "SELECT count(*) FROM public.resultados_zooplancton WHERE id_especie=:source", source=merge["source_id"]),
                        "source_consolidated": scalar(conn, "SELECT count(*) FROM public.biota_analise_consolidada WHERE nome_cientifico=:source_name", source_name=merge["source_name"]),
                    }
                    if any(remaining.values()):
                        raise RuntimeError(f"Validação pós-fusão falhou para {merge['label']}: {remaining}")
                    merge_report.update({"result_rows_moved": moved, "consolidated_rows_updated": consolidated, "source_species_deleted": deleted, "remaining": remaining})
    finally:
        engine.dispose()

    log_dir = RESULTS_DIR / "Controle_Taxonomico_R01" / "Auditoria"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{stamp}_{report['mode']}_merge_cyphoderia_colurella.json"
    log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
