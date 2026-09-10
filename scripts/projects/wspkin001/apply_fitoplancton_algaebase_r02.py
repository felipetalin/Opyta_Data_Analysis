from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine  # noqa: E402


PROJECT_ID = 211
ALLOWED_PHYLA = {
    "Bacillariophyta",
    "Charophyta",
    "Cyanobacteria",
    "Euglenozoa",
    "Chlorophyta",
    "Ochrophyta",
    "Rhodophyta",
    "Cryptophyta",
}


def expected(reino: str, filo: str, classe: str, genero: str) -> tuple[str, str]:
    if classe in {"Bacillariophyceae", "Mediophyceae"}:
        return "Chromista", "Bacillariophyta"
    if classe == "Cyanophyceae":
        return "Bacteria", "Cyanobacteria"
    if classe == "Euglenophyceae":
        return "Protozoa", "Euglenozoa"
    if classe == "Chlorophyceae":
        return "Plantae", "Chlorophyta"
    if classe == "Zygnematophyceae":
        return "Plantae", "Charophyta"
    if classe == "Florideophyceae":
        return "Plantae", "Rhodophyta"
    if genero == "Cryptomonas" or filo.lower() == "cryptophyta":
        return "Chromista", "Cryptophyta"
    if genero in {"Dinobryon", "Synura"} or classe == "Chrysophyceae":
        return "Chromista", "Ochrophyta"
    raise RuntimeError(f"Sem regra AlgaeBase: reino={reino}, filo={filo}, classe={classe}, genero={genero}")


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    backup_species = f"backup_especies_wspkin001_fito_algaebase_r02_{stamp}"
    backup_consolidated = f"backup_biota_wspkin001_fito_algaebase_r02_{stamp}"
    engine = get_engine()
    with engine.begin() as conn:
        taxa = conn.execute(
            text(
                """
                SELECT DISTINCT s.id_especie, s.nome_cientifico, s.reino, s.filo,
                       s.classe, s.genero
                FROM public.especies s
                JOIN public.resultados_fitoplancton r USING (id_especie)
                JOIN public.esforcos_amostragem e USING (id_esforco)
                JOIN public.pontos_coleta p USING (id_ponto_coleta)
                WHERE p.id_projeto=:project_id
                ORDER BY s.id_especie
                """
            ),
            {"project_id": PROJECT_ID},
        ).mappings().all()
        if len(taxa) != 77:
            raise RuntimeError(f"Esperados 77 taxons; encontrados {len(taxa)}")
        decisions = []
        for row in taxa:
            new_reino, new_filo = expected(row["reino"], row["filo"], row["classe"], row["genero"])
            decisions.append(
                {
                    "id_especie": row["id_especie"],
                    "nome_cientifico": row["nome_cientifico"],
                    "reino_anterior": row["reino"],
                    "filo_anterior": row["filo"],
                    "reino_algaebase": new_reino,
                    "filo_algaebase": new_filo,
                    "alterado": row["reino"] != new_reino or row["filo"] != new_filo,
                }
            )

        conn.execute(text(f"CREATE TABLE public.{backup_species} AS SELECT s.* FROM public.especies s WHERE s.id_especie=ANY(:ids)"), {"ids": [d["id_especie"] for d in decisions]})
        conn.execute(text(f"CREATE TABLE public.{backup_consolidated} AS SELECT * FROM public.biota_analise_consolidada WHERE id_projeto=:project_id AND grupo_biologico ILIKE 'Fito%'"), {"project_id": PROJECT_ID})
        for d in decisions:
            conn.execute(
                text("UPDATE public.especies SET reino=:reino, filo=:filo WHERE id_especie=:id"),
                {"reino": d["reino_algaebase"], "filo": d["filo_algaebase"], "id": d["id_especie"]},
            )
        conn.execute(
            text(
                """
                UPDATE public.biota_analise_consolidada b
                SET reino=s.reino, filo=s.filo
                FROM public.especies s
                WHERE b.id_projeto=:project_id AND b.grupo_biologico ILIKE 'Fito%'
                  AND b.nome_cientifico=s.nome_cientifico
                """
            ),
            {"project_id": PROJECT_ID},
        )
        summary = conn.execute(
            text("SELECT reino,filo,count(DISTINCT nome_cientifico) taxa,count(*) registros FROM public.biota_analise_consolidada WHERE id_projeto=:project_id AND grupo_biologico ILIKE 'Fito%' GROUP BY 1,2 ORDER BY 2"),
            {"project_id": PROJECT_ID},
        ).mappings().all()
        found = {r["filo"] for r in summary}
        if found != ALLOWED_PHYLA:
            raise RuntimeError(f"Filos finais divergentes: {sorted(found)}")
        invalid = conn.execute(
            text("SELECT count(*) FROM public.biota_analise_consolidada WHERE id_projeto=:project_id AND grupo_biologico ILIKE 'Fito%' AND ((filo='Cyanobacteria' AND reino<>'Bacteria') OR (filo='Euglenozoa' AND reino<>'Protozoa') OR (filo IN ('Bacillariophyta','Ochrophyta','Cryptophyta') AND reino<>'Chromista') OR (filo IN ('Charophyta','Chlorophyta','Rhodophyta') AND reino<>'Plantae'))"),
            {"project_id": PROJECT_ID},
        ).scalar_one()
        if invalid:
            raise RuntimeError(f"Hierarquias finais invalidas: {invalid}")

    audit_dir = Path("outputs/validacoes/wspkin001_fitoplancton_algaebase_r02_20260904")
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_dir / f"{stamp}_auditoria_fitoplancton_algaebase_r02.json"
    payload = {
        "status": "OK",
        "project_id": PROJECT_ID,
        "reference": "AlgaeBase",
        "backup_species": f"public.{backup_species}",
        "backup_consolidated": f"public.{backup_consolidated}",
        "taxa_checked": len(decisions),
        "taxa_changed": sum(d["alterado"] for d in decisions),
        "consolidated_rows": sum(r["registros"] for r in summary),
        "allowed_phyla": sorted(ALLOWED_PHYLA),
        "summary": [dict(r) for r in summary],
        "decisions": decisions,
    }
    audit.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**payload, "audit_path": str(audit)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
