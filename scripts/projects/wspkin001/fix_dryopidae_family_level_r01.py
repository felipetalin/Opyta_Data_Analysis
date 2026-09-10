from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
backup = f"backup_especies_dryopidae_wspkin001_{stamp}"
engine = get_engine()
with engine.begin() as conn:
    conn.execute(text(f"CREATE TABLE public.{backup} AS SELECT * FROM public.especies WHERE nome_cientifico='Dryopidae'"))
    before = dict(conn.execute(text("SELECT id_especie,nome_cientifico,familia,genero,bmwp_score FROM public.especies WHERE nome_cientifico='Dryopidae'")).mappings().one())
    conn.execute(text("UPDATE public.especies SET genero=NULL, observacoes=concat_ws(' ',observacoes,'WSPKIN001 Gate B 2026-09-09: identificacao confirmada somente ate familia.') WHERE nome_cientifico='Dryopidae'"))
    after = dict(conn.execute(text("SELECT id_especie,nome_cientifico,familia,genero,bmwp_score FROM public.especies WHERE nome_cientifico='Dryopidae'")).mappings().one())

payload = {"timestamp": stamp, "backup": f"public.{backup}", "before": before, "after": after}
out = Path("outputs/validacoes/wspkin001_zoobentos_20260909/correcao_dryopidae_r01.json")
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2))
