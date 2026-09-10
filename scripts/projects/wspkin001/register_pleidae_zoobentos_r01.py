from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine

AUDIT_DIR = Path("outputs/validacoes/wspkin001_zoobentos_20260909")
RECORD = {
    "nome_cientifico": "Pleidae",
    "grupo_biologico": "Zoobentos",
    "reino": "Animalia",
    "filo": "Arthropoda",
    "classe": "Insecta",
    "ordem": "Hemiptera",
    "familia": "Pleidae",
    "genero": None,
    "autor_e_ano": "N.A.",
    "origem": "N.A.",
    "endemismo": "N.A.",
    "status_ameaca_nacional": "N.A.",
    "status_ameaca_global": "N.A.",
    "bmwp_score": 3,
    "observacoes": "Cadastro manual Gate B WSPKIN001; taxonomia e BMWP informados pelo usuario em 2026-09-09. Filo normalizado de Artropoda para Arthropoda conforme padrao do banco.",
}

engine = get_engine()
with engine.begin() as conn:
    existing = conn.execute(text("SELECT * FROM public.especies WHERE nome_cientifico=:name"), {"name": RECORD["nome_cientifico"]}).mappings().one_or_none()
    if existing:
        status = "existing"
        species_id = existing["id_especie"]
    else:
        species_id = conn.execute(text("""
            INSERT INTO public.especies
              (nome_cientifico,grupo_biologico,reino,filo,classe,ordem,familia,genero,
               autor_e_ano,origem,endemismo,status_ameaca_nacional,status_ameaca_global,bmwp_score,observacoes)
            VALUES
              (:nome_cientifico,:grupo_biologico,:reino,:filo,:classe,:ordem,:familia,:genero,
               :autor_e_ano,:origem,:endemismo,:status_ameaca_nacional,:status_ameaca_global,:bmwp_score,:observacoes)
            RETURNING id_especie
        """), RECORD).scalar_one()
        status = "inserted"

payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "id_especie": species_id,
    "record": RECORD,
}
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
audit = AUDIT_DIR / "cadastro_manual_pleidae_r01.json"
audit.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2))
