"""
Inserção de Meio Físico via Supabase REST (como fauna)
------------------------------------------------------
Este script lê os dados já validados e insere na tabela fisico_analise_consolidada
usando a API REST do Supabase, contornando o bloqueio da porta 5432.

Pré-requisitos:
- Preencher SUPABASE_URL e SUPABASE_ANON_KEY no .env
- Instalar supabase-py: pip install supabase
"""


import os
import sys
from pathlib import Path
SRC_PATH = Path(__file__).parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
import pandas as pd
from dotenv import load_dotenv
from opyta_analysis.supabase_client import get_client

# Caminho dos arquivos de dados (ajuste se necessário)
PLANILHA_RESULTADOS = r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Migração/Físico/Resultados_Meio_Fisico.xlsx"

# Colunas obrigatórias e extras
COLUNAS_OBRIGATORIAS = ["nome_campanha", "nome_ponto", "matriz", "nome_parametro", "valor_medido"]
COLUNAS_EXTRAS = [
    "codigo_interno_opyta", "nome_projeto", "nome_empresa", "data_hora_coleta", "latitude", "longitude", "bacia_hidrografica",
    "sinal_limite", "unidade_medida", "unidade_original_laudo", "laboratorio_responsavel", "observacoes_resultado",
    "vmp_357_cl1_min", "vmp_357_cl1_max", "vmp_357_cl2_min", "vmp_357_cl2_max", "vmp_amonia_dinamico", "vmp_454_n1", "vmp_454_n2",
    "vmp_396_consumo_humano", "vmp_396_dessedentacao_animal", "vmp_396_irrigacao", "vmp_396_recreacao", "vmp_430_padrao"
]

# Mapeamento de colunas (Excel → banco)
COL_MAP = {
    "campanha":          "nome_campanha",
    "nome_campanha":     "nome_campanha",
    "ponto":             "nome_ponto",
    "nome_ponto":        "nome_ponto",
    "matriz":            "matriz",
    "parametro":         "nome_parametro",
    "nome_parametro":    "nome_parametro",
    "sinal":             "sinal_limite",
    "sinal_limite":      "sinal_limite",
    "valor":             "valor_medido",
    "resultado":         "valor_medido",
    "valor_medido":      "valor_medido",
    "unidade":           "unidade_medida",
    "unidade_medida":    "unidade_medida",
    "data":              "data_hora_coleta",
    "data_hora_coleta":  "data_hora_coleta",
    "latitude":          "latitude",
    "longitude":         "longitude",
    "laboratorio":       "laboratorio_responsavel",
    "laboratorio_responsavel": "laboratorio_responsavel",
    "bacia":             "bacia_hidrografica",
    "bacia_hidrografica":"bacia_hidrografica",
    "observacoes":       "observacoes_resultado",
    "observacoes_resultado": "observacoes_resultado",
}

CODIGO_PROJETO = "FERSAM001"
NOME_PROJETO = "Sam Metais Diagnóstico"
NOME_EMPRESA = "Rocha Consultoria e Projetos"

def harmonizar_colunas(df):
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns})
    return df

def _parse_valor_medido(df):
    """Separa '<'/'>' de valor_medido em sinal_limite + número."""
    import re
    def extract(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None, None
        s = str(v).strip()
        m = re.match(r'^([<>]=?)\s*(.+)$', s)
        if m:
            return m.group(1), m.group(2)
        return None, s

    sinais, valores = zip(*df["valor_medido"].apply(extract))
    # Só preencher sinal_limite se ainda não existe ou é vazio
    if "sinal_limite" not in df.columns:
        df["sinal_limite"] = None
    mask = df["sinal_limite"].isna() | (df["sinal_limite"] == "")
    df.loc[mask, "sinal_limite"] = [s for s in sinais]
    df["valor_medido"] = pd.to_numeric(list(valores), errors="coerce")
    return df

def preencher_extras(df):
    df["codigo_interno_opyta"] = CODIGO_PROJETO
    df["nome_projeto"] = NOME_PROJETO
    df["nome_empresa"] = NOME_EMPRESA
    for col in COLUNAS_EXTRAS:
        if col not in df.columns:
            df[col] = None
    df = _parse_valor_medido(df)
    return df

def validar_e_exibir(df, aba):
    nulos = df[COLUNAS_OBRIGATORIAS].isnull().sum()
    print(f"Aba: {aba} | Registros: {len(df)} | Nulos obrigatórios: {dict(nulos[nulos>0])}")

def main():
    load_dotenv()
    print("Lendo apenas a aba 'Resultados_Meio_Fisico'...")
    xls = pd.ExcelFile(PLANILHA_RESULTADOS)
    aba = 'Resultados_Meio_Fisico'
    df = pd.read_excel(xls, sheet_name=aba)
    print(f"Colunas encontradas: {df.columns.tolist()}")
    df = harmonizar_colunas(df)
    print(f"Colunas após harmonização: {df.columns.tolist()}")
    df = preencher_extras(df)
    # Garantir que todas as colunas obrigatórias existem
    faltando = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    if faltando:
        print(f"ERRO: Faltam colunas obrigatórias após harmonização: {faltando}")
        return
    df = df.dropna(subset=COLUNAS_OBRIGATORIAS)
    validar_e_exibir(df, aba)
    print(f"Total de registros a inserir: {len(df)}")

    if len(df) == 0:
        print("Nenhum registro válido para inserir.")
        return

    # --- Validação detalhada da planilha ---
    print("\n[Validação da planilha]")
    problemas = False
    # 1. Colunas obrigatórias
    faltando = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    if faltando:
        print(f"ERRO: Faltam colunas obrigatórias: {faltando}")
        problemas = True
    # 2. Nulos obrigatórios
    nulos = df[COLUNAS_OBRIGATORIAS].isnull().sum()
    if nulos.sum() > 0:
        print(f"ERRO: Existem valores nulos em colunas obrigatórias: {dict(nulos[nulos>0])}")
        problemas = True
    # 3. valor_medido: aceitar '<', '>', números; rejeitar apenas vazio/nulo/ND
    if 'valor_medido' in df.columns:
        def is_valido_valor(val):
            s = str(val).strip().lower()
            if s in ('', 'nan', 'none', 'nd', 'null'):
                return False
            return True

        invalidos = ~df['valor_medido'].apply(is_valido_valor)
        n_invalidos = invalidos.sum()
        if n_invalidos > 0:
            print(f"ERRO: {n_invalidos} valores em 'valor_medido' são vazios, nulos ou 'ND'.")
            linhas_invalidas = df[invalidos].copy()
            print("Exemplo de linhas problemáticas (máx 10):")
            print(linhas_invalidas.head(10)[['nome_ponto','nome_campanha','matriz','nome_parametro','valor_medido']])
            problemas = True
    # 4. NaN, inf, -inf
    import numpy as np
    for col in df.columns:
        if df[col].dtype.kind in 'fc':
            if np.isinf(df[col]).any():
                print(f"ERRO: Coluna '{col}' possui valores infinitos.")
                problemas = True
            if df[col].isnull().any():
                print(f"ERRO: Coluna '{col}' possui valores NaN.")
                problemas = True
    # 5. Duplicados
    dups = df.duplicated(subset=COLUNAS_OBRIGATORIAS, keep=False).sum()
    if dups > 0:
        print(f"AVISO: Existem {dups} linhas duplicadas considerando apenas as colunas obrigatórias.")
    if problemas:
        print("\nCorrija os erros acima antes de tentar inserir no banco.")
        return
    print("Validação OK. Prosseguindo com a inserção...\n")

    # Substituir NaN, np.inf e -np.inf por None para evitar erro de JSON
    df = df.replace([np.nan, np.inf, -np.inf], None)
    registros = df.to_dict(orient="records")
    sb = get_client()
    table = "fisico_analise_consolidada"
    BATCH = 1000
    for i in range(0, len(registros), BATCH):
        batch = registros[i:i+BATCH]
        print(f"Inserindo registros {i+1} a {i+len(batch)}...")
        resp = sb.table(table).insert(batch).execute()
        print(f"Lote {i//BATCH+1} inserido com sucesso ({len(batch)} registros).")
    print("Concluído.")

if __name__ == "__main__":
    main()
