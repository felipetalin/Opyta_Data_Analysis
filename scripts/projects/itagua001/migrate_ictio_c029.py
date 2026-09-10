"""Transactional, campaign-scoped migration of ITAGUA001 Ictiofauna C029."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

REPO = Path(__file__).resolve().parents[3]
DATA_ROOT = Path("G:/Meu Drive/Opyta/Opyta_Data")
PREPARED = REPO / "docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_PREPARED.json"
AUDIT = REPO / "docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_MIGRATION.json"
CAMPAIGN = "C029-2026-08-SC"
PROJECT_ID = 165

load_dotenv(DATA_ROOT / ".env")
sys.path.insert(0, str(DATA_ROOT))
sys.path.insert(0, str(DATA_ROOT / "scripts"))
from core.engine import get_engine

spec = importlib.util.spec_from_file_location("generic_ictio_migrator", DATA_ROOT / "scripts/migrar_ictiofauna.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)

payload = json.loads(PREPARED.read_text(encoding="utf-8"))
assert payload["campaign"] == CAMPAIGN and payload["source_preserved"] is True
frames = {name: pd.DataFrame(rows) for name, rows in payload["sheets"].items()}
points = frames["Pontos_e_Campanhas"]
efforts = frames["Metadados_Esforco"]
results = frames["Resultados_Ictiofauna"]
cover = frames["Capa_Projeto"]
points["Data"] = pd.to_datetime(points["Data"], errors="raise").dt.tz_localize(None)
assert set(points.Campanha) == set(efforts.Campanha) == set(results.Campanha) == {CAMPAIGN}
assert cover.iloc[0].Codigo_Opyta == "ITAGUA001"
assert len(points) == 32 and len(efforts) == 49 and len(results) == 99
assert pd.to_numeric(results.Numero_de_Individuos).sum() == 235

engine = get_engine()
with engine.begin() as conn:
    identity = conn.execute(text("select id_projeto from projetos where codigo_interno_opyta='ITAGUA001'")).scalar_one()
    assert identity == PROJECT_ID
    # Campaign-only cleanup for idempotency; history outside C029 is untouched.
    conn.execute(text("""delete from resultados_ictiofauna_detalhe where codigo_opyta='ITAGUA001' and campanha=:c"""), {"c": CAMPAIGN})
    module.limpar_dados_da_campanha(conn, PROJECT_ID, points)
    module.migrar_dados(conn, cover, points, efforts, results)

    species = {r.nome_cientifico: r.id_especie for r in conn.execute(text(
        "select id_especie,nome_cientifico from especies where nome_cientifico=any(:n)"),
        {"n": sorted(results.Nome_Cientifico.unique())})}
    assert len(species) == 14
    effort_map = {(r.nome_ponto, r.metodo_de_captura): r.id_esforco for r in conn.execute(text("""
        select p.nome_ponto,e.metodo_de_captura,e.id_esforco
        from esforcos_amostragem e join pontos_coleta p using(id_ponto_coleta)
        join campanhas c using(id_campanha)
        where p.id_projeto=:p and c.nome_campanha=:c and e.grupo_biologico='Ictiofauna'
    """), {"p": PROJECT_ID, "c": CAMPAIGN})}
    aggregate = {(r.id_esforco, r.id_especie): r.id_resultado_ictio for r in conn.execute(text("""
        select r.id_resultado_ictio,r.id_esforco,r.id_especie
        from resultados_ictiofauna r join esforcos_amostragem e using(id_esforco)
        join pontos_coleta p using(id_ponto_coleta) join campanhas c using(id_campanha)
        where p.id_projeto=:p and c.nome_campanha=:c and e.grupo_biologico='Ictiofauna'
    """), {"p": PROJECT_ID, "c": CAMPAIGN})}
    details = []
    for _, row in results.iterrows():
        effort_id = effort_map[(row.Ponto, row.Metodo_de_Captura)]
        species_id = species[row.Nome_Cientifico]
        details.append({
            "id_resultado_ictio": aggregate[(effort_id, species_id)], "id_esforco": effort_id,
            "id_especie": species_id, "codigo_opyta": "ITAGUA001", "linha_fonte": int(row["_source_excel_row"]) if "_source_excel_row" in row else None,
            "ponto": row.Ponto, "campanha": CAMPAIGN, "metodo_de_captura": row.Metodo_de_Captura,
            "tipo_de_amostragem": row.Tipo_de_Amostragem, "malha_ou_anzol": None if pd.isna(row.Malha_ou_Anzol) else str(row.Malha_ou_Anzol),
            "numero_de_individuos": row.Numero_de_Individuos, "ct_cm": row.CT_cm, "cp_cm": row.CP_cm,
            "pc_g": row.PC_g, "sexo_raw": None if pd.isna(row.Sexo) else str(row.Sexo),
            "emg_raw": None if pd.isna(row.EMG) else str(row.EMG),
            "observacao": None if pd.isna(row.Observacao_Individuo_Lote) else str(row.Observacao_Individuo_Lote),
            "source_workbook": payload["source"],
        })
    conn.execute(text("""
        insert into resultados_ictiofauna_detalhe
        (id_resultado_ictio,id_esforco,id_especie,codigo_opyta,linha_fonte,ponto,campanha,
         metodo_de_captura,tipo_de_amostragem,malha_ou_anzol,numero_de_individuos,ct_cm,cp_cm,
         pc_g,sexo_raw,emg_raw,observacao_individuo_lote,source_workbook,source_sheet)
        values (:id_resultado_ictio,:id_esforco,:id_especie,:codigo_opyta,:linha_fonte,:ponto,:campanha,
         :metodo_de_captura,:tipo_de_amostragem,:malha_ou_anzol,:numero_de_individuos,:ct_cm,:cp_cm,
         :pc_g,:sexo_raw,:emg_raw,:observacao,:source_workbook,'Resultados_Ictiofauna')
    """), details)
    totals = dict(conn.execute(text("""
        select count(distinct p.id_ponto_coleta) points, count(distinct e.id_esforco) efforts,
               count(distinct r.id_resultado_ictio) result_rows,
               coalesce(sum(r.numero_de_individuos),0) individuals,
               count(distinct r.id_especie) species
        from pontos_coleta p join campanhas c using(id_campanha)
        left join esforcos_amostragem e on e.id_ponto_coleta=p.id_ponto_coleta and e.grupo_biologico='Ictiofauna'
        left join resultados_ictiofauna r using(id_esforco)
        where p.id_projeto=:p and c.nome_campanha=:c
    """), {"p": PROJECT_ID, "c": CAMPAIGN}).mappings().one())
    detail_totals = dict(conn.execute(text("""
        select count(*) detail_rows, coalesce(sum(numero_de_individuos),0) detail_individuals
        from resultados_ictiofauna_detalhe where codigo_opyta='ITAGUA001' and campanha=:c
    """), {"c": CAMPAIGN}).mappings().one())
    assert totals == {"points": 32, "efforts": 49, "result_rows": 66, "individuals": 235, "species": 14}
    assert detail_totals == {"detail_rows": 99, "detail_individuals": 235}

record = {"executed_at": datetime.now().astimezone().isoformat(), "project_id": PROJECT_ID,
          "campaign": CAMPAIGN, "source": payload["source"], "source_sha256": payload["sha256"],
          "approved_adjustments": payload["adjustments"], "totals": totals,
          "detail_totals": detail_totals, "history_scope": "only C029 cleaned/written",
          "products_generated": False, "consolidation_executed": False}
AUDIT.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps(record, ensure_ascii=False, default=str))
