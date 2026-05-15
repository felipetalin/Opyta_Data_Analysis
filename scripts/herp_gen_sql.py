"""
Gera SQL de migração herpetofauna para Supabase — projeto 165
Saída: scripts/herp_migration.sql
"""
import pandas as pd, math

XLSX = r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Campanhas de campo\28_campanha-Abril_26\Herpetofauna\Planilha\1.ITA-GUA-Dados_brutos-Herpetofauna-Campanha_28_260516_CORRIGIDA_MIGRACAO.xlsx"

spp_df = pd.read_excel(XLSX, 'Cadastro_Especies')
esf_df = pd.read_excel(XLSX, 'Metadados_Esforco')
res_df = pd.read_excel(XLSX, 'Resultados_Herpetofauna')

PONTO_DB = {
    ('Área Controle','CO1'):45722,('Área Controle','CO2'):45723,('Área Controle','CO3'):45724,
    ('Área Controle','CO4'):45725,('Área Controle','CO5'):45726,('Área Controle','CO6'):45727,
    ('Área Controle','CO7'):45728,('Área Controle','CON1'):45712,('Área Controle','CON2'):45713,
    ('Dores de Guanhães','DG1'):45736,('Dores de Guanhães','DG2'):45737,('Dores de Guanhães','DG3'):45738,
    ('Dores de Guanhães','DG4'):45739,('Dores de Guanhães','DG5'):45740,('Dores de Guanhães','DG6'):45741,
    ('Dores de Guanhães','DG7'):45742,('Dores de Guanhães','DGN1'):45716,('Dores de Guanhães','DGN2'):45717,
    ('Fortuna II','FO1'):45729,('Fortuna II','FO2'):45730,('Fortuna II','FO3'):45731,
    ('Fortuna II','FO4'):45732,('Fortuna II','FO5'):45733,('Fortuna II','FO6'):45734,
    ('Fortuna II','FO7'):45735,('Fortuna II','FOR1'):45714,('Fortuna II','FOR2'):45715,
    ('Jacaré','JA1'):45750,('Jacaré','JA2'):45751,('Jacaré','JA3'):45752,
    ('Jacaré','JA4'):45753,('Jacaré','JA5'):45754,('Jacaré','JA6'):45755,
    ('Jacaré','JA7'):45756,('Jacaré','JAC1'):45720,('Jacaré','JAC2'):45721,
    ('Senhora do Porto','SP1'):45743,('Senhora do Porto','SP2'):45744,('Senhora do Porto','SP3'):45745,
    ('Senhora do Porto','SP4'):45746,('Senhora do Porto','SP5'):45747,('Senhora do Porto','SP6'):45748,
    ('Senhora do Porto','SP7'):45749,('Senhora do Porto','SPT1'):45718,('Senhora do Porto','SPT2'):45719,
}

EXISTING_SPP = {'Boana albopunctata': 3763, 'Thoropa miliaris': 3762}


def sq(v):
    """Single-quote escape for SQL string literal."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 'NULL'
    s = str(v).strip()
    if s in ('', 'nan', 'None', 'N.A.', 'NA', 'NaN'):
        return 'NULL'
    return "'" + s.replace("'", "''") + "'"


def ni(v):
    """Numeric integer for SQL."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 'NULL'
    try:
        return str(int(v))
    except Exception:
        return 'NULL'


def nf(v):
    """Numeric float for SQL."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 'NULL'
    try:
        return str(float(v))
    except Exception:
        return 'NULL'


lines = []
lines.append("-- ============================================================")
lines.append("-- MIGRAÇÃO HERPETOFAUNA — Projeto 165 — C028-2026-04-SC")
lines.append("-- 26 novas espécies + 44 esforços + 108 resultados")
lines.append("-- ============================================================")
lines.append("")

# ── PASSO 1: Inserir espécies ─────────────────────────────────────────────────
lines.append("-- ── PASSO 1: Inserir 26 espécies novas ──")
lines.append("INSERT INTO especies (nome_cientifico, nome_popular, grupo_biologico, reino, filo, classe, ordem,")
lines.append("  familia, genero, autor_e_ano, status_ameaca_global, status_ameaca_nacional, status_copam,")
lines.append("  status_estadual, cites, habito_alimentar, guilda_alimentar, dependencia_florestal,")
lines.append("  endemismo, sensibilidade_ambiental, migratorio, raridade)")
lines.append("VALUES")

spp_rows = []
for _, r in spp_df.iterrows():
    nm = str(r['Nome_Cientifico']).strip()
    if nm in EXISTING_SPP:
        continue
    row = (
        f"  ({sq(nm)}, {sq(r.get('Nome_Popular'))}, {sq(r.get('Grupo_Biologico'))}, "
        f"{sq(r.get('Reino'))}, {sq(r.get('Filo'))}, {sq(r.get('Classe'))}, "
        f"{sq(r.get('Ordem'))}, {sq(r.get('Familia'))}, {sq(r.get('Genero'))}, "
        f"{sq(r.get('Autor_e_Ano'))}, "
        f"{sq(r.get('Status_IUCN'))}, {sq(r.get('Status_MMA'))}, "
        f"{sq(r.get('Status_COPAM'))}, {sq(r.get('Status_Estadual'))}, {sq(r.get('CITES'))}, "
        f"{sq(r.get('Habito_Alimentar'))}, {sq(r.get('Guilda_Alimentar'))}, "
        f"{sq(r.get('Dependencia_Florestal'))}, "
        f"{sq(r.get('Endemismo'))}, {sq(r.get('Sensibilidade_Ambiental'))}, "
        f"{sq(r.get('Migratorio'))}, {sq(r.get('Raridade'))})"
    )
    spp_rows.append(row)

lines.append(",\n".join(spp_rows))
lines.append("ON CONFLICT (nome_cientifico) DO NOTHING;")
lines.append("")

# ── PASSO 2: Inserir esforcos ─────────────────────────────────────────────────
lines.append("-- ── PASSO 2: Inserir 44 esforços de amostragem ──")
lines.append("INSERT INTO esforcos_amostragem (id_ponto_coleta, grupo_biologico, metodo_de_captura, tipo_de_amostragem, esforco, unidade_esforco)")
lines.append("VALUES")

esf_rows = []
for _, r in esf_df.iterrows():
    emp = str(r['Empreendimento']).strip()
    pto = str(r['Ponto']).strip()
    pc_id = PONTO_DB[(emp, pto)]
    row = (
        f"  ({pc_id}, {sq(r['Grupo_Biologico'])}, "
        f"{sq(r['Metodo_de_Captura'])}, {sq(r['Tipo_de_Amostragem'])}, "
        f"{nf(r.get('Esforco'))}, {sq(r.get('Unidade_Esforco'))})"
    )
    esf_rows.append(row)

lines.append(",\n".join(esf_rows))
lines.append(";")
lines.append("")

# ── PASSO 3: Inserir resultados via subquery ──────────────────────────────────
lines.append("-- ── PASSO 3: Inserir 108 resultados herpetofauna ──")
lines.append("INSERT INTO resultados_herpetofauna (id_esforco, id_especie, numero_de_individuos, tipo_amostragem, observacoes)")
lines.append("VALUES")

res_rows = []
for _, r in res_df.iterrows():
    emp = str(r['Empreendimento']).strip()
    pto = str(r['Ponto']).strip()
    pc_id = PONTO_DB[(emp, pto)]
    metodo = str(r['Metodo_de_Captura']).strip()
    nm_sp = str(r['Nome_Cientifico']).strip()

    # esforco lookup subquery (by ponto + metodo + grupo)
    esf_subq = (
        f"(SELECT id_esforco FROM esforcos_amostragem "
        f"WHERE id_ponto_coleta={pc_id} AND grupo_biologico='Herpetofauna' "
        f"AND metodo_de_captura={sq(metodo)} LIMIT 1)"
    )
    # especie lookup subquery
    esp_subq = f"(SELECT id_especie FROM especies WHERE nome_cientifico={sq(nm_sp)} LIMIT 1)"

    obs_raw = r.get('Observacoes')
    obs = sq(obs_raw) if (obs_raw is not None and not (isinstance(obs_raw, float) and math.isnan(obs_raw))) else 'NULL'

    row = (
        f"  ({esf_subq}, {esp_subq}, "
        f"{ni(r.get('Numero_de_Individuos'))}, {sq(r.get('Tipo_de_Amostragem'))}, {obs})"
    )
    res_rows.append(row)

lines.append(",\n".join(res_rows))
lines.append(";")
lines.append("")
lines.append("-- ── Validação pós-migração ──")
lines.append("SELECT COUNT(*) AS esforcos FROM esforcos_amostragem ea")
lines.append("  JOIN pontos_coleta pc ON ea.id_ponto_coleta=pc.id_ponto_coleta")
lines.append("  WHERE pc.id_projeto=165 AND ea.grupo_biologico='Herpetofauna';")
lines.append("")
lines.append("SELECT COUNT(*) AS resultados FROM resultados_herpetofauna rh")
lines.append("  JOIN esforcos_amostragem ea ON rh.id_esforco=ea.id_esforco")
lines.append("  JOIN pontos_coleta pc ON ea.id_ponto_coleta=pc.id_ponto_coleta")
lines.append("  WHERE pc.id_projeto=165;")

out = "\n".join(lines)
with open("scripts/herp_migration.sql", "w", encoding="utf-8") as f:
    f.write(out)

print(f"OK — {len(spp_rows)} espécies, {len(esf_rows)} esforços, {len(res_rows)} resultados")
print("SQL salvo em scripts/herp_migration.sql")
