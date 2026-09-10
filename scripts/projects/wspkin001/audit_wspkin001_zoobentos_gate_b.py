from pathlib import Path
import json
import sys

import pandas as pd
from sqlalchemy import bindparam, text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine

SOURCE = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Migração de dados\Resultados_Migração_Zoobentos-WSP.xlsx")
OUT = Path("outputs/validacoes/wspkin001_zoobentos_20260909/auditoria_gate_b.json")
FIELDS = ["reino", "filo", "classe", "ordem", "familia", "genero", "autor_e_ano", "origem", "endemismo", "status_ameaca_nacional", "status_ameaca_global", "bmwp_score"]

names = sorted(pd.read_excel(SOURCE, "Resultados_Zoobentos")["Nome_Cientifico"].dropna().astype(str).str.strip().unique())
engine = get_engine()
with engine.connect() as conn:
    query = text("SELECT * FROM public.especies WHERE nome_cientifico IN :names ORDER BY nome_cientifico").bindparams(bindparam("names", expanding=True))
    rows = [dict(row) for row in conn.execute(query, {"names": names}).mappings()]

found = {row["nome_cientifico"] for row in rows}
incomplete = []
for row in rows:
    missing = [field for field in FIELDS if row.get(field) in (None, "", "N.A.", "N.A")]
    if missing:
        incomplete.append({"nome_cientifico": row["nome_cientifico"], "campos": missing})

payload = {
    "source_taxa": len(names),
    "registered": len(rows),
    "missing_taxa": sorted(set(names) - found),
    "incomplete": incomplete,
    "registered_rows": [{field: row.get(field) for field in ["id_especie", "nome_cientifico", *FIELDS]} for row in rows],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({key: value for key, value in payload.items() if key != "registered_rows"}, ensure_ascii=False, indent=2))
