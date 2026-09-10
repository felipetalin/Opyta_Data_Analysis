from pathlib import Path
import json
import sys

from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine

OFFICIAL = {
    "PT_01": (-17.11137946, -46.95024449), "PT_02": (-17.14039444, -47.01674724),
    "PT_03": (-17.13333091, -46.94114619), "PT_04": (-17.11435337, -46.90079376),
    "PT_05": (-17.10317134, -46.84686704), "PT_06": (-17.13558594, -46.91847559),
    "PT_07": (-17.11943072, -46.90675106), "PT_08": (-17.12257486, -46.94465538),
    "PT_09": (-17.11897500, -46.82032600), "PT_10": (-17.13065849, -46.88515517),
}

engine = get_engine()
with engine.connect() as conn:
    groups = [dict(x) for x in conn.execute(text("SELECT grupo_biologico,count(*) linhas,count(DISTINCT nome_cientifico) taxa,coalesce(sum(contagem),0)::float8 total FROM public.biota_analise_consolidada WHERE id_projeto=211 GROUP BY grupo_biologico ORDER BY 1")).mappings()]
    coords = [dict(x) for x in conn.execute(text("SELECT nome_ponto,latitude::float8 latitude,longitude::float8 longitude,count(*) linhas FROM public.biota_analise_consolidada WHERE id_projeto=211 AND grupo_biologico='Zoobentos' GROUP BY 1,2,3 ORDER BY 1")).mappings()]
    taxa = [dict(x) for x in conn.execute(text("SELECT nome_cientifico,reino,filo,classe,ordem,familia,genero,bmwp_score,count(*) linhas FROM public.biota_analise_consolidada WHERE id_projeto=211 AND grupo_biologico='Zoobentos' AND nome_cientifico IN ('Pleidae','Dryopidae','Melanoides sp.','Planorbidae','Sphaerium sp.') GROUP BY 1,2,3,4,5,6,7,8 ORDER BY 1")).mappings()]
    campaigns = [dict(x) for x in conn.execute(text("SELECT nome_campanha,count(*) linhas,count(DISTINCT nome_ponto) pontos,count(DISTINCT nome_cientifico) taxa,sum(contagem)::float8 total FROM public.biota_analise_consolidada WHERE id_projeto=211 AND grupo_biologico='Zoobentos' GROUP BY 1 ORDER BY 1")).mappings()]
    sampling = [dict(x) for x in conn.execute(text("SELECT nome_campanha,tipo_amostragem,count(*) linhas,count(DISTINCT nome_cientifico) taxa,sum(contagem)::float8 total FROM public.biota_analise_consolidada WHERE id_projeto=211 AND grupo_biologico='Zoobentos' GROUP BY 1,2 ORDER BY 1,2")).mappings()]

coord_errors = []
for row in coords:
    expected = OFFICIAL[row["nome_ponto"]]
    if abs(row["latitude"] - expected[0]) > 1e-8 or abs(row["longitude"] - expected[1]) > 1e-8:
        coord_errors.append(row)
expected_sampling = {("C001-2026-03-CH", "Qualitativa"): (35, 35.0), ("C001-2026-03-CH", "Quantitativa"): (25, 52.0), ("C002-2026-07-SC", "Qualitativa"): (28, 28.0), ("C002-2026-07-SC", "Quantitativa"): (64, 234.0)}
sampling_errors = [row for row in sampling if expected_sampling.get((row["nome_campanha"], row["tipo_amostragem"])) != (row["linhas"], row["total"])]
payload = {"status": "OK" if not coord_errors and not sampling_errors else "ERROR", "groups": groups, "campaigns": campaigns, "sampling": sampling, "sampling_errors": sampling_errors, "coordinate_errors": coord_errors, "selected_taxa": taxa}
out = Path("outputs/validacoes/wspkin001_zoobentos_20260909/auditoria_pos_migracao.json")
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2))
