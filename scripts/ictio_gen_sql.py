"""
Gera SQL de migracao de Ictiofauna para Supabase - projeto 165 (ITAGUA001)
Escopo: somente a campanha de Guanhaes (48o Campanha - Seca)
Saida: scripts/ictio_migration.sql
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


XLSX = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Campanhas de campo\28_campanha-Abril_26\Ictiofauna\2. Maio-26\Planilha\projeto_ictio_real-Guanhães.xlsx"
)
OUT_SQL = Path("scripts/ictio_migration.sql")
PROJECT_ID = 165
SOURCE_CAMPAIGN = "48º Campanha (Seca)"
TARGET_CAMPAIGN_SEQ = 28


def _infer_target_campaign(pc_source: pd.DataFrame) -> str:
    """Build normalized campaign name using fauna-aligned sequence and source month/season."""
    sample_date = pd.to_datetime(pc_source["Data"], errors="coerce").dropna().min()
    if pd.isna(sample_date):
        year = 2026
        month = 5
    else:
        year = int(sample_date.year)
        month = int(sample_date.month)
    season_code = "CH" if "Chuva" in SOURCE_CAMPAIGN else "SC"
    return f"C{TARGET_CAMPAIGN_SEQ:03d}-{year:04d}-{month:02d}-{season_code}"


def _norm_str(value: object) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).replace("\xa0", " ").replace("º", "o").strip()
    if text in {"", "nan", "None", "N.A.", "NA", "NaN"}:
        return None
    return text


def _normalize_species_name(value: object) -> str | None:
    text = _norm_str(value)
    if text is None:
        return None
    species_map = {
        "knodus moenkhausii": "Knodus moenkhausii",
        "Hypomasticus copelandii": "Hypomasticus copelandii",
    }
    return species_map.get(text, text)


def _normalize_sample_type(value: object) -> str | None:
    text = _norm_str(value)
    if text is None:
        return None
    if text == "Qualitativo":
        return "Qualitativa"
    return text


def _latlon_to_float(value: object) -> float | None:
    text = _norm_str(value)
    if text is None:
        return None
    text = text.replace("°", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def sq(value: object) -> str:
    text = _norm_str(value)
    if text is None:
        return "NULL"
    return "'" + text.replace("'", "''") + "'"


def nf(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "NULL"
    try:
        return str(float(value))
    except Exception:
        return "NULL"


def ni(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "NULL"
    try:
        return str(int(value))
    except Exception:
        return "NULL"


pc_df = pd.read_excel(XLSX, "Pontos_e_Campanhas")
res_df = pd.read_excel(XLSX, "Resultados_Ictiofauna")
esf_df = pd.read_excel(XLSX, "Metadados_Esforco")

pc_df = pc_df[pc_df["Campanha"].astype(str).eq(SOURCE_CAMPAIGN)].copy()
res_df = res_df[res_df["Campanha"].astype(str).eq(SOURCE_CAMPAIGN)].copy()
esf_df = esf_df[esf_df["Campanha"].astype(str).eq(SOURCE_CAMPAIGN)].copy()

TARGET_CAMPAIGN = _infer_target_campaign(pc_df)

pc_df["Ponto"] = pc_df["Ponto"].map(_norm_str)
pc_df["Latitude"] = pc_df["Latitude"].map(_latlon_to_float)
pc_df["Longitude"] = pc_df["Longitude"].map(_latlon_to_float)
pc_df["Campanha"] = TARGET_CAMPAIGN

res_df["Ponto"] = res_df["Ponto"].map(_norm_str)
res_df["Campanha"] = TARGET_CAMPAIGN
res_df["Metodo_de_Captura"] = res_df["Metodo_de_Captura"].map(_norm_str)
res_df["Tipo_de_Amostragem"] = res_df["Tipo_de_Amostragem"].map(_normalize_sample_type)
res_df["Nome_Cientifico"] = res_df["Nome_Cientifico"].map(_normalize_species_name)

esf_df["Ponto"] = esf_df["Ponto"].map(_norm_str)
esf_df["Campanha"] = TARGET_CAMPAIGN
esf_df["Metodo_de_Captura"] = esf_df["Metodo_de_Captura"].map(_norm_str)
esf_df["Tipo_de_Amostragem"] = esf_df["Tipo_de_Amostragem"].map(_normalize_sample_type)


existing_species = {
    "Astyanax lacustris",
    "Geophagus brasiliensis",
    "Hasemania nana",
    "Hoplias intermedius",
    "Hoplias malabaricus",
    "Knodus moenkhausii",
    "Poecilia reticulata",
    "Rhamdia quelen",
}


point_records: list[dict[str, object]] = []
for _, row in pc_df.sort_values("Ponto").iterrows():
    point_records.append(
        {
            "ponto": row["Ponto"],
            "data": pd.to_datetime(row["Data"]).strftime("%Y-%m-%d") if pd.notna(row["Data"]) else None,
            "latitude": row["Latitude"],
            "longitude": row["Longitude"],
            "curso": _norm_str(row.get("Curso_d_Agua")),
            "bacia": _norm_str(row.get("Bacia_Hidrografica")),
            "municipio": _norm_str(row.get("Municipio")),
            "obs": _norm_str(row.get("Observacoes_Coleta")),
        }
    )


effort_map: dict[tuple[str, str, str], dict[str, object]] = {}
for _, row in esf_df.iterrows():
    key = (row["Ponto"], row["Metodo_de_Captura"], row["Tipo_de_Amostragem"])
    effort_map[key] = {
        "ponto": row["Ponto"],
        "metodo": row["Metodo_de_Captura"],
        "tipo": row["Tipo_de_Amostragem"],
        "esforco": row.get("Esforco"),
        "unidade": _norm_str(row.get("Unidade_Esforco")),
    }

for _, row in res_df.iterrows():
    key = (row["Ponto"], row["Metodo_de_Captura"], row["Tipo_de_Amostragem"])
    if key in effort_map:
        continue
    effort_map[key] = {
        "ponto": row["Ponto"],
        "metodo": row["Metodo_de_Captura"],
        "tipo": row["Tipo_de_Amostragem"],
        "esforco": row.get("Esforco_Amostral"),
        "unidade": _norm_str(row.get("Unidade_Esforco")),
    }

effort_records = [effort_map[key] for key in sorted(effort_map)]


result_records: list[dict[str, object]] = []
for _, row in res_df.iterrows():
    if row["Nome_Cientifico"] is None:
        continue
    result_records.append(
        {
            "ponto": row["Ponto"],
            "metodo": row["Metodo_de_Captura"],
            "tipo": row["Tipo_de_Amostragem"],
            "nome_cientifico": row["Nome_Cientifico"],
            "numero_de_individuos": row.get("Numero_de_Individuos"),
            "ct_cm": row.get("CT_cm"),
            "cp_cm": row.get("CP_cm"),
            "pc_g": row.get("PC_g"),
            "sexo": _norm_str(row.get("Sexo")),
            "emg": _norm_str(row.get("EMG")),
            "observacao": _norm_str(row.get("Observacao_Individuo_Lote")),
        }
    )


new_species = sorted(
    {
        record["nome_cientifico"]
        for record in result_records
        if record["nome_cientifico"] not in existing_species
    }
)

lines: list[str] = []
lines.append("-- ============================================================")
lines.append("-- MIGRACAO ICTIOFAUNA - Projeto 165 (ITAGUA001)")
lines.append(f"-- Campanha: {TARGET_CAMPAIGN}")
lines.append(
    f"-- {len(new_species)} especies novas + {len(point_records)} pontos + {len(effort_records)} esforcos + {len(result_records)} resultados"
)
lines.append("-- ============================================================")
lines.append("")

lines.append("-- PASSO 0: Inserir campanha do monitoramento")
lines.append("INSERT INTO campanhas (nome_campanha)")
lines.append(f"SELECT {sq(TARGET_CAMPAIGN)}")
lines.append(f"WHERE NOT EXISTS (SELECT 1 FROM campanhas WHERE nome_campanha = {sq(TARGET_CAMPAIGN)});")
lines.append("")

lines.append("-- PASSO 1: Inserir especies novas")
lines.append("INSERT INTO especies (nome_cientifico, grupo_biologico)")
if new_species:
    species_rows = [f"  ({sq(name)}, 'Ictiofauna')" for name in new_species]
    lines.append("VALUES")
    lines.append(",\n".join(species_rows))
    lines.append("ON CONFLICT (nome_cientifico) DO NOTHING;")
else:
    lines.append("SELECT NULL, NULL WHERE FALSE;")
lines.append("")

lines.append("-- PASSO 1.5: Limpeza controlada para reexecucao da carga de ictio")
point_name_list = ", ".join(sq(record["ponto"]) for record in point_records)
lines.append("WITH pontos_alvo AS (")
lines.append("  SELECT pc.id_ponto_coleta")
lines.append("  FROM pontos_coleta pc")
lines.append("  JOIN campanhas c ON c.id_campanha = pc.id_campanha")
lines.append(f"  WHERE pc.id_projeto = {PROJECT_ID}")
lines.append(f"    AND c.nome_campanha = {sq(TARGET_CAMPAIGN)}")
lines.append(f"    AND pc.nome_ponto IN ({point_name_list})")
lines.append(")")
lines.append("DELETE FROM resultados_ictiofauna ri")
lines.append("WHERE ri.id_esforco IN (")
lines.append("  SELECT ea.id_esforco")
lines.append("  FROM esforcos_amostragem ea")
lines.append("  WHERE ea.grupo_biologico = 'Ictiofauna'")
lines.append("    AND ea.id_ponto_coleta IN (SELECT id_ponto_coleta FROM pontos_alvo)")
lines.append(");")
lines.append("WITH pontos_alvo AS (")
lines.append("  SELECT pc.id_ponto_coleta")
lines.append("  FROM pontos_coleta pc")
lines.append("  JOIN campanhas c ON c.id_campanha = pc.id_campanha")
lines.append(f"  WHERE pc.id_projeto = {PROJECT_ID}")
lines.append(f"    AND c.nome_campanha = {sq(TARGET_CAMPAIGN)}")
lines.append(f"    AND pc.nome_ponto IN ({point_name_list})")
lines.append(")")
lines.append("DELETE FROM esforcos_amostragem ea")
lines.append("WHERE ea.grupo_biologico = 'Ictiofauna'")
lines.append("  AND ea.id_ponto_coleta IN (SELECT id_ponto_coleta FROM pontos_alvo);")
lines.append("WITH pontos_alvo AS (")
lines.append("  SELECT pc.id_ponto_coleta")
lines.append("  FROM pontos_coleta pc")
lines.append("  JOIN campanhas c ON c.id_campanha = pc.id_campanha")
lines.append(f"  WHERE pc.id_projeto = {PROJECT_ID}")
lines.append(f"    AND c.nome_campanha = {sq(TARGET_CAMPAIGN)}")
lines.append(f"    AND pc.nome_ponto IN ({point_name_list})")
lines.append(")")
lines.append("DELETE FROM pontos_coleta pc")
lines.append("WHERE pc.id_ponto_coleta IN (SELECT id_ponto_coleta FROM pontos_alvo)")
lines.append("  AND NOT EXISTS (")
lines.append("    SELECT 1 FROM esforcos_amostragem ea WHERE ea.id_ponto_coleta = pc.id_ponto_coleta")
lines.append("  );")
lines.append("")

lines.append(f"-- PASSO 2: Inserir pontos da campanha {TARGET_CAMPAIGN}")
lines.append(
    "INSERT INTO pontos_coleta (id_projeto, id_campanha, data_hora_coleta, nome_ponto, latitude, longitude, bacia_hidrografica, observacoes)"
)
lines.append("VALUES")
point_rows = []
for record in point_records:
    obs_parts = [
        f"curso_d_agua={record['curso']}" if record["curso"] else None,
        f"municipio={record['municipio']}" if record["municipio"] else None,
        f"obs_coleta={record['obs']}" if record["obs"] else None,
    ]
    obs_text = " | ".join(part for part in obs_parts if part)
    point_rows.append(
        "  ("
        f"{PROJECT_ID}, "
        f"(SELECT id_campanha FROM campanhas WHERE nome_campanha = {sq(TARGET_CAMPAIGN)} LIMIT 1), "
        f"{sq(record['data'])}, {sq(record['ponto'])}, {nf(record['latitude'])}, {nf(record['longitude'])}, "
        f"{sq(record['bacia'])}, {sq(obs_text)}"
        ")"
    )
lines.append(",\n".join(point_rows))
lines.append(";")
lines.append("")

lines.append("-- PASSO 3: Inserir esforcos de amostragem")
lines.append(
    "INSERT INTO esforcos_amostragem (id_ponto_coleta, grupo_biologico, metodo_de_captura, tipo_de_amostragem, esforco, unidade_esforco)"
)
lines.append("VALUES")
effort_rows = []
for record in effort_records:
    point_subq = (
        f"(SELECT pc.id_ponto_coleta FROM pontos_coleta pc "
        f"JOIN campanhas c ON c.id_campanha = pc.id_campanha "
        f"WHERE pc.id_projeto = {PROJECT_ID} AND c.nome_campanha = {sq(TARGET_CAMPAIGN)} "
        f"AND pc.nome_ponto = {sq(record['ponto'])} LIMIT 1)"
    )
    effort_rows.append(
        "  ("
        f"{point_subq}, 'Ictiofauna', {sq(record['metodo'])}, {sq(record['tipo'])}, "
        f"{nf(record['esforco'])}, {sq(record['unidade'])}"
        ")"
    )
lines.append(",\n".join(effort_rows))
lines.append(";")
lines.append("")

lines.append("-- PASSO 4: Inserir resultados ictiofauna validos (linhas sem especie foram tratadas como ausencia de captura e permanecem apenas no esforco)")
lines.append(
    "INSERT INTO resultados_ictiofauna (id_esforco, id_especie, numero_de_individuos, ct_cm, cp_cm, pc_g, sexo, emg, observacao_individuo_lote, tipo_amostragem)"
)
lines.append("VALUES")
result_rows = []
for record in result_records:
    effort_subq = (
        f"(SELECT ea.id_esforco FROM esforcos_amostragem ea "
        f"JOIN pontos_coleta pc ON pc.id_ponto_coleta = ea.id_ponto_coleta "
        f"JOIN campanhas c ON c.id_campanha = pc.id_campanha "
        f"WHERE pc.id_projeto = {PROJECT_ID} AND c.nome_campanha = {sq(TARGET_CAMPAIGN)} "
        f"AND pc.nome_ponto = {sq(record['ponto'])} "
        f"AND ea.grupo_biologico = 'Ictiofauna' "
        f"AND ea.metodo_de_captura = {sq(record['metodo'])} "
        f"AND ea.tipo_de_amostragem = {sq(record['tipo'])} LIMIT 1)"
    )
    species_subq = f"(SELECT id_especie FROM especies WHERE nome_cientifico = {sq(record['nome_cientifico'])} LIMIT 1)"
    result_rows.append(
        "  ("
        f"{effort_subq}, {species_subq}, {ni(record['numero_de_individuos'])}, {nf(record['ct_cm'])}, {nf(record['cp_cm'])}, {nf(record['pc_g'])}, "
        f"{sq(record['sexo'])}, {sq(record['emg'])}, {sq(record['observacao'])}, {sq(record['tipo'])}"
        ")"
    )
lines.append(",\n".join(result_rows))
lines.append(";")
lines.append("")

lines.append("-- VALIDACAO POS-MIGRACAO")
lines.append(f"SELECT COUNT(*) AS n_pontos FROM pontos_coleta pc JOIN campanhas c ON c.id_campanha = pc.id_campanha WHERE pc.id_projeto = {PROJECT_ID} AND c.nome_campanha = {sq(TARGET_CAMPAIGN)};")
lines.append(f"SELECT COUNT(*) AS n_esforcos FROM esforcos_amostragem ea JOIN pontos_coleta pc ON pc.id_ponto_coleta = ea.id_ponto_coleta JOIN campanhas c ON c.id_campanha = pc.id_campanha WHERE pc.id_projeto = {PROJECT_ID} AND c.nome_campanha = {sq(TARGET_CAMPAIGN)} AND ea.grupo_biologico = 'Ictiofauna';")
lines.append(f"SELECT COUNT(*) AS n_resultados FROM resultados_ictiofauna ri JOIN esforcos_amostragem ea ON ea.id_esforco = ri.id_esforco JOIN pontos_coleta pc ON pc.id_ponto_coleta = ea.id_ponto_coleta JOIN campanhas c ON c.id_campanha = pc.id_campanha WHERE pc.id_projeto = {PROJECT_ID} AND c.nome_campanha = {sq(TARGET_CAMPAIGN)};")
lines.append(f"SELECT COUNT(DISTINCT e.nome_cientifico) AS n_especies FROM resultados_ictiofauna ri JOIN esforcos_amostragem ea ON ea.id_esforco = ri.id_esforco JOIN pontos_coleta pc ON pc.id_ponto_coleta = ea.id_ponto_coleta JOIN campanhas c ON c.id_campanha = pc.id_campanha JOIN especies e ON e.id_especie = ri.id_especie WHERE pc.id_projeto = {PROJECT_ID} AND c.nome_campanha = {sq(TARGET_CAMPAIGN)};")

OUT_SQL.write_text("\n".join(lines), encoding="utf-8")

print(
    f"OK - {len(new_species)} especies novas, {len(point_records)} pontos, "
    f"{len(effort_records)} esforcos, {len(result_records)} resultados"
)
print(f"SQL salvo em {OUT_SQL}")