from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine  # noqa: E402


PROJECT_ID = 211
PREVIEW_SOURCE = Path("outputs/validacoes/wspkin001_zooplancton_gbif_r03_20260904/preview_gbif_51_taxons.json")
PRESERVE_UNMATCHED = {"Alona sp.", "Ciliado NI", "Polyarthra sp."}
OPERATIONAL_STAGES = {
    "CALANOIDA (copepodito)", "CALANOIDA (nauplius)",
    "CYCLOPOIDA (copepodito)", "CYCLOPOIDA (nauplius)",
    "HARPACTICOIDA (copepodito)",
}


def clean(value):
    return value if value not in (None, "") else None


def build_decisions(rows):
    decisions = []
    for row in rows:
        name = row["nome_cientifico"]
        gbif = row["gbif"]
        new = {k: row.get(k) for k in ["nome_cientifico", "autor_e_ano", "reino", "filo", "classe", "ordem", "familia", "genero"]}
        action = "GBIF"
        if name in PRESERVE_UNMATCHED:
            action = "Preservado: correspondencia GBIF ausente/ambigua"
        elif name == "Bdelloida":
            new.update(nome_cientifico="Bdelloidea", autor_e_ano="N.A.", reino="Animalia", filo="Rotifera", classe="Eurotatoria", ordem="Bdelloidea", familia="N.A.", genero="N.A.")
            action = "GBIF usageKey 1234; nome aceito em nivel de ordem"
        else:
            hierarchy = {"reino": "kingdom", "filo": "phylum", "classe": "class", "ordem": "order", "familia": "family", "genero": "genus"}
            for local, remote in hierarchy.items():
                if clean(gbif.get(remote)) is not None:
                    new[local] = gbif[remote]
            if name == "Difflugia lithophyla":
                new["nome_cientifico"] = "Difflugia litophila"
                new["autor_e_ano"] = gbif["authorship"]
                action = "Fusao no cadastro existente id_especie=114"
            elif gbif.get("matchType") == "EXACT" and name not in OPERATIONAL_STAGES and gbif.get("rank") == "SPECIES":
                new["nome_cientifico"] = gbif.get("canonicalName") or name
                new["autor_e_ano"] = clean(gbif.get("authorship")) or row.get("autor_e_ano") or "N.A."
            elif name in OPERATIONAL_STAGES:
                new["nome_cientifico"] = name
                new["autor_e_ano"] = "N.A."
                new["familia"] = "N.A."
                new["genero"] = "N.A."
                action = "Rotulo operacional preservado; hierarquia GBIF da ordem"
            else:
                action = "Nome operacional preservado; hierarquia do nivel GBIF correspondente"
        before = {k: row.get(k) for k in new}
        decisions.append({
            "id_especie": row["id_especie"], "registros_wsp": row["registros"], "ids_resultados": row["ids_resultados"],
            "gbif_usage_key": gbif.get("usageKey"), "gbif_match_type": gbif.get("matchType"), "gbif_confidence": gbif.get("confidence"),
            "acao": action, "antes": before, "depois": new, "alterado": before != new,
        })
    return decisions


def main():
    rows = json.loads(PREVIEW_SOURCE.read_text(encoding="utf-8"))
    decisions = build_decisions(rows)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    audit_dir = PREVIEW_SOURCE.parent
    proposed_path = audit_dir / f"{stamp}_preview_aplicacao_gbif_zooplancton_r03.json"
    proposed_path.write_text(json.dumps({"status": "PREVIEW", "decisions": decisions}, ensure_ascii=False, indent=2), encoding="utf-8")

    backup_species = f"backup_especies_wspkin001_zoo_gbif_r03_{stamp}"
    backup_results = f"backup_resultados_zoo_wspkin001_gbif_r03_{stamp}"
    backup_consolidated = f"backup_biota_wspkin001_zoo_gbif_r03_{stamp}"
    engine = get_engine()
    with engine.begin() as conn:
        before = conn.execute(text("SELECT count(*) n, coalesce(sum(r.numero_de_individuos),0)::float8 total FROM public.resultados_zooplancton r JOIN public.esforcos_amostragem e USING(id_esforco) JOIN public.pontos_coleta p USING(id_ponto_coleta) WHERE p.id_projeto=:id"), {"id": PROJECT_ID}).mappings().one()
        if before["n"] != 244:
            raise RuntimeError(f"Esperados 244 resultados; encontrados {before['n']}")
        ids = sorted({d["id_especie"] for d in decisions} | {114})
        conn.execute(text(f"CREATE TABLE public.{backup_species} AS SELECT * FROM public.especies WHERE id_especie=ANY(:ids)"), {"ids": ids})
        conn.execute(text(f"CREATE TABLE public.{backup_results} AS SELECT r.* FROM public.resultados_zooplancton r JOIN public.esforcos_amostragem e USING(id_esforco) JOIN public.pontos_coleta p USING(id_ponto_coleta) WHERE p.id_projeto=:id"), {"id": PROJECT_ID})
        conn.execute(text(f"CREATE TABLE public.{backup_consolidated} AS SELECT * FROM public.biota_analise_consolidada WHERE id_projeto=:id AND grupo_biologico ILIKE 'Zoopl%'"), {"id": PROJECT_ID})

        # Merge only WSP links; the source taxon remains available for other projects.
        conn.execute(text("UPDATE public.resultados_zooplancton r SET id_especie=114 FROM public.esforcos_amostragem e JOIN public.pontos_coleta p USING(id_ponto_coleta) WHERE r.id_esforco=e.id_esforco AND p.id_projeto=:id AND r.id_especie=793"), {"id": PROJECT_ID})
        for d in decisions:
            if d["id_especie"] == 793:
                continue
            v = d["depois"]
            conn.execute(text("UPDATE public.especies SET nome_cientifico=:nome,autor_e_ano=:autor,reino=:reino,filo=:filo,classe=:classe,ordem=:ordem,familia=:familia,genero=:genero WHERE id_especie=:id"), {
                "nome": v["nome_cientifico"], "autor": v["autor_e_ano"], "reino": v["reino"], "filo": v["filo"], "classe": v["classe"], "ordem": v["ordem"], "familia": v["familia"], "genero": v["genero"], "id": d["id_especie"],
            })
        # Ensure the existing accepted target is GBIF-compliant.
        target = next(d["depois"] for d in decisions if d["id_especie"] == 793)
        conn.execute(text("UPDATE public.especies SET autor_e_ano=:autor,reino=:reino,filo=:filo,classe=:classe,ordem=:ordem,familia=:familia,genero=:genero WHERE id_especie=114"), {"autor": target["autor_e_ano"], "reino": target["reino"], "filo": target["filo"], "classe": target["classe"], "ordem": target["ordem"], "familia": target["familia"], "genero": target["genero"]})

        # Rebuild only the descriptive taxonomy fields in the WSP analytical slice.
        conn.execute(text("""
            UPDATE public.biota_analise_consolidada b SET
              nome_cientifico = CASE WHEN b.nome_cientifico='Difflugia lithophyla' THEN 'Difflugia litophila' WHEN b.nome_cientifico='Bdelloida' THEN 'Bdelloidea' ELSE s.nome_cientifico END,
              reino=s.reino,filo=s.filo,classe=s.classe,ordem=s.ordem,familia=s.familia,genero=s.genero
            FROM public.especies s
            WHERE b.id_projeto=:id AND b.grupo_biologico ILIKE 'Zoopl%' AND s.id_especie = CASE WHEN b.nome_cientifico='Difflugia lithophyla' THEN 114 ELSE (SELECT sx.id_especie FROM public.especies sx WHERE sx.nome_cientifico=b.nome_cientifico LIMIT 1) END
        """), {"id": PROJECT_ID})
        # Bdelloida was renamed before the name-based join and needs explicit synchronization.
        conn.execute(text("UPDATE public.biota_analise_consolidada SET nome_cientifico='Bdelloidea',reino='Animalia',filo='Rotifera',classe='Eurotatoria',ordem='Bdelloidea',familia='N.A.',genero='N.A.' WHERE id_projeto=:id AND grupo_biologico ILIKE 'Zoopl%' AND nome_cientifico='Bdelloida'"), {"id": PROJECT_ID})
        after = conn.execute(text("SELECT count(*) n,coalesce(sum(r.numero_de_individuos),0)::float8 total,count(DISTINCT r.id_especie) taxa FROM public.resultados_zooplancton r JOIN public.esforcos_amostragem e USING(id_esforco) JOIN public.pontos_coleta p USING(id_ponto_coleta) WHERE p.id_projeto=:id"), {"id": PROJECT_ID}).mappings().one()
        duplicate = conn.execute(text("SELECT count(*) FROM (SELECT r.id_esforco,r.id_especie,count(*) FROM public.resultados_zooplancton r JOIN public.esforcos_amostragem e USING(id_esforco) JOIN public.pontos_coleta p USING(id_ponto_coleta) WHERE p.id_projeto=:id GROUP BY 1,2 HAVING count(*)>1) q"), {"id": PROJECT_ID}).scalar_one()
        if after["n"] != before["n"] or abs(after["total"] - before["total"]) > 1e-12 or duplicate:
            raise RuntimeError(f"Falha de reconciliacao: before={dict(before)}, after={dict(after)}, duplicatas={duplicate}")

    payload = {"status": "OK", "reference": "GBIF Backbone Taxonomy", "preview": str(proposed_path), "backup_species": f"public.{backup_species}", "backup_results": f"public.{backup_results}", "backup_consolidated": f"public.{backup_consolidated}", "before": dict(before), "after": dict(after), "duplicates": duplicate, "taxa_changed": sum(d["alterado"] for d in decisions), "decisions": decisions}
    audit_path = audit_dir / f"{stamp}_aplicacao_gbif_zooplancton_r03.json"
    audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "decisions"} | {"audit_path": str(audit_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
