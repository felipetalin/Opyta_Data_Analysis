"""Back up, repair enterprise/CP fields, and consolidate only ITAGUA001 Ictiofauna C029."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

REPO = Path(__file__).resolve().parents[3]
DATA_ROOT = Path("G:/Meu Drive/Opyta/Opyta_Data")
CAMPAIGN = "C029-2026-08-SC"
PREVIOUS = "C028-2026-05-SC"
PROJECT_ID = 165
CODE = "ITAGUA001"
load_dotenv(DATA_ROOT / ".env")
sys.path.insert(0, str(DATA_ROOT))
from core.engine import get_engine

stamp = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%Sz").lower()
prefix = f"bkp_itagua001_ictio_c029_{stamp}"
backups = {
    "points": f"{prefix}_pontos",
    "results": f"{prefix}_resultados",
    "details": f"{prefix}_detalhes",
    "consolidated": f"{prefix}_consolidado",
}

engine = get_engine()
with engine.begin() as conn:
    identity = conn.execute(text("select id_projeto from projetos where codigo_interno_opyta=:c"), {"c": CODE}).scalar_one()
    assert identity == PROJECT_ID
    mapping = conn.execute(text("""
        select cur.id_ponto_coleta, cur.nome_ponto, prev.id_empreendimento
        from pontos_coleta cur join campanhas cc on cc.id_campanha=cur.id_campanha
        join pontos_coleta prev on prev.id_projeto=cur.id_projeto and prev.nome_ponto=cur.nome_ponto
        join campanhas pc on pc.id_campanha=prev.id_campanha
        where cur.id_projeto=:p and cc.nome_campanha=:cur and pc.nome_campanha=:prev
    """), {"p": PROJECT_ID, "cur": CAMPAIGN, "prev": PREVIOUS}).mappings().all()
    assert len(mapping) == 32 and all(r["id_empreendimento"] is not None for r in mapping)

    conn.execute(text(f"""create table public.{backups['points']} as
        select p.* from pontos_coleta p join campanhas c using(id_campanha)
        where p.id_projeto={PROJECT_ID} and c.nome_campanha='{CAMPAIGN}'"""))
    conn.execute(text(f"""create table public.{backups['results']} as
        select r.* from resultados_ictiofauna r join esforcos_amostragem e using(id_esforco)
        join pontos_coleta p using(id_ponto_coleta) join campanhas c using(id_campanha)
        where p.id_projeto={PROJECT_ID} and c.nome_campanha='{CAMPAIGN}'"""))
    conn.execute(text(f"""create table public.{backups['details']} as
        select * from resultados_ictiofauna_detalhe
        where codigo_opyta='{CODE}' and campanha='{CAMPAIGN}'"""))
    conn.execute(text(f"""create table public.{backups['consolidated']} as
        select * from biota_analise_consolidada
        where id_projeto={PROJECT_ID} and nome_campanha='{CAMPAIGN}' and grupo_biologico='Ictiofauna'"""))

    updated_points = conn.execute(text("""
        update pontos_coleta cur set id_empreendimento=src.id_empreendimento
        from (
          select prev.nome_ponto,prev.id_empreendimento
          from pontos_coleta prev join campanhas pc using(id_campanha)
          where prev.id_projeto=:p and pc.nome_campanha=:prev
        ) src, campanhas cc
        where cur.id_campanha=cc.id_campanha and cur.id_projeto=:p
          and cc.nome_campanha=:cur and cur.nome_ponto=src.nome_ponto
    """), {"p": PROJECT_ID, "prev": PREVIOUS, "cur": CAMPAIGN}).rowcount
    assert updated_points == 32

    updated_cp = conn.execute(text("""
        update resultados_ictiofauna r set cp_cm=src.cp_cm
        from (
          select id_resultado_ictio,
                 sum(cp_cm*numero_de_individuos)/nullif(sum(numero_de_individuos),0) cp_cm
          from resultados_ictiofauna_detalhe
          where codigo_opyta=:code and campanha=:camp and cp_cm is not null
          group by id_resultado_ictio
        ) src where r.id_resultado_ictio=src.id_resultado_ictio
    """), {"code": CODE, "camp": CAMPAIGN}).rowcount

    deleted = conn.execute(text("""
        delete from biota_analise_consolidada
        where id_projeto=:p and nome_campanha=:c and grupo_biologico='Ictiofauna'
    """), {"p": PROJECT_ID, "c": CAMPAIGN}).rowcount
    inserted = conn.execute(text("""
        insert into biota_analise_consolidada (
          nome_empresa,nome_projeto,codigo_opyta,nome_campanha,nome_ponto,latitude,longitude,
          grupo_biologico,nome_cientifico,contagem,biomassa,bmwp_score,codigo_interno_opyta,
          data_hora_coleta,bacia_hidrografica,metodo_de_captura,esforco,unidade_esforco,
          nome_popular,reino,filo,classe,ordem,familia,genero,origem,medida_1,medida_2,
          tipo_amostragem,id_empreendimento,nome_empreendimento,id_projeto)
        select cli.nome_empresa,pr.nome_projeto,null,c.nome_campanha,p.nome_ponto,p.latitude,p.longitude,
          e.grupo_biologico,sp.nome_cientifico,ri.numero_de_individuos,
          case when ri.pc_g is null then null else ri.pc_g*coalesce(nullif(ri.numero_de_individuos,0),1) end,
          sp.bmwp_score,pr.codigo_interno_opyta,p.data_hora_coleta,p.bacia_hidrografica,
          e.metodo_de_captura,e.esforco,e.unidade_esforco,sp.nome_popular,sp.reino,sp.filo,
          sp.classe,sp.ordem,sp.familia,sp.genero,sp.origem,ri.ct_cm,ri.cp_cm,
          coalesce(ri.tipo_amostragem,e.tipo_amostragem,e.tipo_de_amostragem),
          p.id_empreendimento,emp.nome,pr.id_projeto
        from resultados_ictiofauna ri join esforcos_amostragem e using(id_esforco)
        join pontos_coleta p using(id_ponto_coleta) join campanhas c using(id_campanha)
        join projetos pr using(id_projeto) join clientes cli using(id_cliente)
        join especies sp using(id_especie) left join empreendimentos emp using(id_empreendimento)
        where p.id_projeto=:p and c.nome_campanha=:c and e.grupo_biologico='Ictiofauna'
    """), {"p": PROJECT_ID, "c": CAMPAIGN}).rowcount
    audit = dict(conn.execute(text("""
        select count(*) linhas,count(distinct nome_ponto) pontos,count(distinct nome_cientifico) especies,
          sum(contagem) individuos,count(*) filter(where id_empreendimento is null or nome_empreendimento is null) sem_empreendimento,
          count(*) filter(where medida_2 is null) sem_cp
        from biota_analise_consolidada where id_projeto=:p and nome_campanha=:c and grupo_biologico='Ictiofauna'
    """), {"p": PROJECT_ID, "c": CAMPAIGN}).mappings().one())
    by_enterprise = [dict(r) for r in conn.execute(text("""
        select nome_empreendimento,count(*) linhas,count(distinct nome_ponto) pontos,
          count(distinct nome_cientifico) especies,sum(contagem) individuos
        from biota_analise_consolidada where id_projeto=:p and nome_campanha=:c and grupo_biologico='Ictiofauna'
        group by nome_empreendimento order by nome_empreendimento
    """), {"p": PROJECT_ID, "c": CAMPAIGN}).mappings()]
    assert inserted == 66 and audit["linhas"] == 66 and audit["individuos"] == 235
    assert audit["especies"] == 14 and audit["sem_empreendimento"] == 0 and audit["sem_cp"] == 0

record = {"executed_at": datetime.now().astimezone().isoformat(), "project_id": PROJECT_ID,
          "campaign": CAMPAIGN, "backup_tables": backups, "backup_scope": "C029/Ictiofauna",
          "points_mapped_from_c028": updated_points, "aggregate_cp_updated": updated_cp,
          "consolidated_deleted": deleted, "consolidated_inserted": inserted,
          "audit": audit, "by_enterprise": by_enterprise, "products_generated": False}
out = REPO / "docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_CONSOLIDATION.json"
out.write_text(json.dumps(record,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
print(json.dumps(record,ensure_ascii=False,default=str))
