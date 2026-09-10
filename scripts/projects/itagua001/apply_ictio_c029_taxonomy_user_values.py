"""Apply only the ITAGUA001 C029 taxonomic values explicitly supplied by the user."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import bindparam, text

DATA_ROOT = Path("G:/Meu Drive/Opyta/Opyta_Data")
REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(DATA_ROOT / ".env")
sys.path.insert(0, str(DATA_ROOT))
from core.engine import get_engine

THREAT_NA = [
    "Cichla kelberi", "Delturus carinotus", "Deuterodon taeniatus",
    "Hypomasticus copelandii", "Hypostomus affinis", "Oreochromis niloticus",
    "Hoplias malabaricus", "Rhamdia quelen",
]
NOT_ENDEMIC = [
    "Astyanax lacustris", "Geophagus brasiliensis", "Hoplias intermedius",
    "Hypomasticus thayeri", "Knodus moenkhausii", "Phalloceros uai",
    "Cichla kelberi", "Deuterodon taeniatus", "Hypomasticus copelandii",
    "Hypostomus affinis", "Oreochromis niloticus", "Hoplias malabaricus",
    "Rhamdia quelen",
]
ENDEMIC_DOCE = ["Delturus carinotus"]
ALL_NAMES = sorted(set(THREAT_NA + NOT_ENDEMIC + ENDEMIC_DOCE))
OUT = REPO_ROOT / "docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_TAXONOMY_UPDATE.json"

select_sql = text("""
select id_especie,nome_cientifico,status_ameaca_nacional,status_ameaca_global,
       status_estadual,origem,endemismo
from especies where nome_cientifico in :names order by nome_cientifico
""").bindparams(bindparam("names", expanding=True))

engine = get_engine()
with engine.begin() as conn:
    before = [dict(r) for r in conn.execute(select_sql, {"names": ALL_NAMES}).mappings()]
    assert len(before) == len(ALL_NAMES), "Nem todas as especies-alvo foram localizadas de forma exata."
    assert {r["nome_cientifico"] for r in before} == set(ALL_NAMES)
    conn.execute(text("""
        update especies set status_ameaca_nacional='N.A.', status_ameaca_global='N.A.',
                            status_estadual='N.A.'
        where nome_cientifico in :names
    """).bindparams(bindparam("names", expanding=True)), {"names": THREAT_NA})
    conn.execute(text("""
        update especies set endemismo='Não endêmica'
        where nome_cientifico in :names
    """).bindparams(bindparam("names", expanding=True)), {"names": NOT_ENDEMIC})
    conn.execute(text("""
        update especies set endemismo='Endêmica da bacia do rio Doce'
        where nome_cientifico in :names
    """).bindparams(bindparam("names", expanding=True)), {"names": ENDEMIC_DOCE})
    conn.execute(text("""
        update especies
        set origem='Exótica na bacia do rio Doce; nativa da bacia Amazônica'
        where nome_cientifico='Cichla kelberi'
    """))
    after = [dict(r) for r in conn.execute(select_sql, {"names": ALL_NAMES}).mappings()]
    by_name = {r["nome_cientifico"]: r for r in after}
    assert all(by_name[n][f] == "N.A." for n in THREAT_NA
               for f in ("status_ameaca_nacional", "status_ameaca_global", "status_estadual"))
    assert all(by_name[n]["endemismo"] == "Não endêmica" for n in NOT_ENDEMIC)
    assert all(by_name[n]["endemismo"] == "Endêmica da bacia do rio Doce" for n in ENDEMIC_DOCE)
    assert by_name["Cichla kelberi"]["origem"] == "Exótica na bacia do rio Doce; nativa da bacia Amazônica"

audit = {
    "executed_at": datetime.now().astimezone().isoformat(),
    "authorization": "Valores informados diretamente pelo usuario na sessao em 2026-09-08.",
    "scope": "especies usadas na ictiofauna ITAGUA001 C029",
    "before": before,
    "after": after,
    "threat_fields_set_to_na": THREAT_NA,
    "endemism_set_to_not_endemic": NOT_ENDEMIC,
    "endemism_set_to_doce_basin": ENDEMIC_DOCE,
    "cichla_origin": "Exótica na bacia do rio Doce; nativa da bacia Amazônica",
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"updated_species": len(ALL_NAMES), "threat_na": len(THREAT_NA),
                  "not_endemic": len(NOT_ENDEMIC), "endemic_doce": len(ENDEMIC_DOCE),
                  "audit": str(OUT)}, ensure_ascii=False))
