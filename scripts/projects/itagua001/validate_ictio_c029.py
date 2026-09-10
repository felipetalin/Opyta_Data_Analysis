"""Read-only source/database preflight for ITAGUA001 C029; never migrates."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[3]
SOURCE = next(Path('G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Itatiaia').glob(
    'Guanh*/Campanhas de campo/29_campanha-Julho_26/Ictiofauna/3.Agosto-26/Planilha/projeto_ictio_real*260817.xlsx'))
CAMPAIGN = 'C029-2026-08-SC'
frames = pd.read_excel(SOURCE, sheet_name=None)
data = {k: v.loc[v.Campanha.eq(CAMPAIGN)].copy() for k, v in frames.items() if 'Campanha' in v}
p, e, r = (data[k] for k in ('Pontos_e_Campanhas', 'Metadados_Esforco', 'Resultados_Ictiofauna'))
adjustments = []
if '--approved-adjustments' in sys.argv:
    mask = r.Ponto.eq('TRDGN2') & r.Metodo_de_Captura.eq('Rede de emalhar')
    assert r.loc[mask, 'Tipo_de_Amostragem'].eq('Qualitativa').all()
    assert set(r.loc[mask, 'Nome_Cientifico']) <= {'Phalloceros uai'}
    assert len(r.loc[mask]) <= 1
    adjustments = [{'source_excel_row': int(i)+2, 'field': 'Metodo_de_Captura',
                    'before': 'Rede de emalhar', 'after': 'Peneira e arrasto',
                    'authorization': 'Usuario confirmou explicitamente na sessao em 2026-09-08'}
                   for i in r.index[mask]]
    r.loc[mask, 'Metodo_de_Captura'] = 'Peneira e arrasto'
def keys(df, cols):
    return set(df[cols].itertuples(index=False, name=None))
pk = ['Campanha', 'Ponto']
ek = pk + ['Metodo_de_Captura']
rk = ek + ['Nome_Cientifico', 'Tipo_de_Amostragem']
report = {
    'source': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'campaign': CAMPAIGN, 'project': frames['Capa_Projeto'].iloc[0]['Codigo_Opyta'],
    'approved_in_memory_adjustments': adjustments,
    'counts': {k: len(v) for k, v in data.items()},
    'individuals': pd.to_numeric(r.Numero_de_Individuos, errors='coerce').sum(),
    'species': sorted(r.Nome_Cientifico.dropna().unique()),
    'aggregated_rows': len(r.groupby(rk)),
    'missing_result_effort_keys': sorted(keys(r, ek) - keys(e, ek)),
    'missing_effort_point_keys': sorted(keys(e, pk) - keys(p, pk)),
    'duplicate_points': int(p.duplicated(pk).sum()),
    'duplicate_efforts': int(e.duplicated(ek).sum()),
    'missing_result_group_keys': int(r[rk].isna().any(axis=1).sum()),
    'dates': sorted(p.Data.astype(str).unique()),
    'methods': e.groupby(['Metodo_de_Captura','Tipo_de_Amostragem'], dropna=False).size().to_string(),
    'numeric_issues': {}, 'coordinates': {},
}
for df, cols in ((r, ['Numero_de_Individuos','CT_cm','PC_g']), (e,['Esforco'])):
    for col in cols:
        n = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce')
        report['numeric_issues'][col] = {'missing_or_invalid':int(n.isna().sum()),'negative':int(n.lt(0).sum()),'zero':int(n.eq(0).sum())}
for col, bound in [('Latitude',90),('Longitude',180)]:
    n=pd.to_numeric(p[col], errors='coerce')
    report['coordinates'][col]={'missing':int(n.isna().sum()),'invalid':int(n.abs().gt(bound).sum()),'min':n.min(),'max':n.max()}
hist=frames['Pontos_e_Campanhas']
hist=hist.loc[hist.Campanha.eq('C028-2026-05-SC')]
comparison=p.merge(hist,on='Ponto',suffixes=('_29','_28'))
report['coordinates']['previous_campaign_compared']=len(comparison)
report['coordinates']['previous_campaign_changed_points'] = comparison.loc[
    (pd.to_numeric(comparison.Latitude_29)-pd.to_numeric(comparison.Latitude_28)).abs().gt(1e-6) |
    (pd.to_numeric(comparison.Longitude_29)-pd.to_numeric(comparison.Longitude_28)).abs().gt(1e-6), 'Ponto'].tolist()
try:
    sys.path.insert(0, 'G:/Meu Drive/Opyta/Opyta_Data')
    from dotenv import load_dotenv
    load_dotenv('G:/Meu Drive/Opyta/Opyta_Data/.env')
    from core.engine import get_engine
    engine=get_engine()
    with engine.connect() as c:
        c.execute(text('SET TRANSACTION READ ONLY'))
        c.execute(text("SET LOCAL statement_timeout = '20s'"))
        report['database_identity']=[dict(x) for x in c.execute(text('SELECT id_projeto, codigo_interno_opyta, nome_projeto FROM projetos WHERE codigo_interno_opyta=:code'),{'code':'ITAGUA001'}).mappings()]
        report['database_c029']= [dict(x) for x in c.execute(text('''SELECT ca.nome_campanha, count(*) AS rows, sum(r.numero_de_individuos) AS individuals
          FROM resultados_ictiofauna r JOIN esforcos_amostragem e USING(id_esforco)
          JOIN pontos_coleta p USING(id_ponto_coleta) JOIN campanhas ca USING(id_campanha)
          WHERE p.id_projeto=165 AND ca.nome_campanha LIKE 'C029%' GROUP BY ca.nome_campanha''')).mappings()]
        taxa = [dict(x) for x in c.execute(text('SELECT * FROM especies WHERE nome_cientifico = ANY(:names)'),
                                          {'names': report['species']}).mappings()]
        fields = ['status_ameaca_nacional', 'status_ameaca_global', 'origem', 'endemismo']
        report['taxonomy'] = {
            'matched': len(taxa),
            'missing_species': sorted(set(report['species']) - {x['nome_cientifico'] for x in taxa}),
            'missing_attribute_counts': {f: sum(x[f] is None or str(x[f]).strip() == '' for x in taxa) for f in fields},
            'missing_attributes_by_species': {x['nome_cientifico']: [f for f in fields if x[f] is None or str(x[f]).strip() == ''] for x in taxa},
            'state_context_review': {x['nome_cientifico']: x['status_estadual'] for x in taxa if '(MT)' in str(x['status_estadual'])},
        }
        (ROOT/'docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_TAXONOMY.json').write_text(
            json.dumps(taxa,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
except Exception as ex:
    report['database_error_type']=type(ex).__name__
out=ROOT/'docs/control_center/operations/ITAGUA001_ICTIOFAUNA_C029_VALIDATION.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
if '--approved-adjustments' in sys.argv:
    prepared = {'source': str(SOURCE), 'sha256': report['sha256'], 'campaign': CAMPAIGN,
                'adjustments': adjustments, 'source_preserved': True,
                'sheets': {'Capa_Projeto': json.loads(frames['Capa_Projeto'].to_json(orient='records',date_format='iso'))}}
    prepared['sheets'].update({k: json.loads(v.assign(_source_excel_row=v.index+2).to_json(orient='records',date_format='iso')) for k,v in data.items()})
    (out.parent/'ITAGUA001_ICTIOFAUNA_C029_PREPARED.json').write_text(
        json.dumps(prepared,ensure_ascii=False,indent=2),encoding='utf-8')
print(out.read_text(encoding='utf-8'))
