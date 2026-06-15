#!/usr/bin/env python
"""
Migração SAM Metais — Meio Físico
===================================
Lê as planilhas de migração do projeto FERSAM001 e insere os registros
na tabela `fisico_analise_consolidada` do Supabase.

Arquivos esperados
------------------
  PLANILHA_RESULTADOS : Excel com abas por campanha/matriz ou formato flat
  PLANILHA_PARAMETROS : Excel com mapeamento parâmetro → VMPs

Pré-requisitos
--------------
  1. Preencher os caminhos nas constantes abaixo.
  2. Ter FISICO_DB_URL no arquivo .env (mesma variável usada pelo pipeline).
  3. pip install pandas openpyxl sqlalchemy python-dotenv psycopg2-binary

Execução
--------
  python scripts/migrar_meio_fisico_sam.py
  python scripts/migrar_meio_fisico_sam.py --dry-run   (só exibe, não insere)
  python scripts/migrar_meio_fisico_sam.py --truncate  (limpa dados FERSAM001 antes)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — AJUSTE AQUI
# ---------------------------------------------------------------------------

CODIGO_PROJETO  = "FERSAM001"
NOME_PROJETO    = "Sam Metais Diagnóstico"
NOME_EMPRESA    = "Rocha Consultoria e Projetos"

# Pasta com os arquivos de migração
PASTA_MIGRACAO  = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Ferreira Rocha"
    r"\SAM Metais\Produtos\Migração\Físico"
)

PLANILHA_RESULTADOS = PASTA_MIGRACAO / "Resultados_Meio_Fisico.xlsx"
PLANILHA_PARAMETROS = PASTA_MIGRACAO / "cadastro_parametros_opyta.xlsx"

ENV_FILE = Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")

# ---------------------------------------------------------------------------
# Colunas esperadas em PLANILHA_RESULTADOS
# ---------------------------------------------------------------------------
# A planilha pode ter os seguintes nomes de colunas (case-insensitive):
#   nome_campanha | nome_ponto | matriz | nome_parametro
#   sinal_limite  | valor_medido | unidade_medida
#   data_hora_coleta | latitude | longitude | laboratorio_responsavel
#   bacia_hidrografica | observacoes_resultado
#
# Colunas opcionais — preenchidas com NULL se ausentes.

COL_MAP = {
    # Excel → banco
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

COLUNAS_OBRIGATORIAS = ["nome_campanha", "nome_ponto", "matriz",
                        "nome_parametro", "valor_medido"]

# ---------------------------------------------------------------------------
# Colunas de VMP em PLANILHA_PARAMETROS
# ---------------------------------------------------------------------------
# A planilha deve conter: nome_parametro + colunas vmp_*
VMP_COLUNAS = [
    "vmp_357_cl1_min", "vmp_357_cl1_max",
    "vmp_357_cl2_min", "vmp_357_cl2_max",
    "vmp_amonia_dinamico",
    "vmp_454_n1", "vmp_454_n2",
    "vmp_396_consumo_humano", "vmp_396_dessedentacao_animal",
    "vmp_396_irrigacao", "vmp_396_recreacao",
    "vmp_430_padrao",
]

# Harmonizacao de nomenclatura de parametro entre resultado e cadastro
PARAM_ALIAS_MAP = {
    "Nitrogenio Nitroso": "Nitrito",
    "Nitrogenio nitrico": "Nitrato",
    "pH": "pH In Situ",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_engine():
    from sqlalchemy import create_engine

    load_dotenv(ENV_FILE, override=True)
    db_url = os.getenv("FISICO_DB_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit(
            "❌  FISICO_DB_URL não encontrado em .env.\n"
            f"   Arquivo .env esperado: {ENV_FILE}"
        )
    return create_engine(db_url)


def _normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas usando COL_MAP (case-insensitive, sem acentos)."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns})
    return df


def _carregar_resultados() -> pd.DataFrame:
    print(f"📂  Lendo resultados: {PLANILHA_RESULTADOS.name}")
    xf = pd.ExcelFile(str(PLANILHA_RESULTADOS))

    frames = []
    # Preferir aba operacional de resultados; evita ingestao de capa/metadados.
    abas = ["Resultados_Meio_Fisico"] if "Resultados_Meio_Fisico" in xf.sheet_names else xf.sheet_names
    for aba in abas:
        df = pd.read_excel(xf, sheet_name=aba, dtype=str)
        df = _normalizar_colunas(df)
        # Se a aba indica a matriz, preenchemos automaticamente
        if "matriz" not in df.columns:
            df["matriz"] = aba
        frames.append(df)

    df_total = pd.concat(frames, ignore_index=True)

    # Verificar colunas obrigatórias
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df_total.columns]
    if faltando:
        sys.exit(
            f"❌  Colunas obrigatórias ausentes em {PLANILHA_RESULTADOS.name}:\n"
            f"   {faltando}\n"
            f"   Colunas encontradas: {list(df_total.columns)}"
        )

    # Separar sinal de limite (< ou >)
    if "sinal_limite" not in df_total.columns:
        df_total["sinal_limite"] = None

    # Converter valor_medido: extrair sinal se necessário
    def _parse_valor(v):
        s = str(v).strip() if pd.notna(v) else ""
        if not s:
            return None, None

        s = s.replace("≤", "<=").replace("≥", ">=")
        token = s.upper().replace(" ", "")
        if token in {"NI", "N/I", "ND", "N/D", "NA", "N/A", "-", "--"}:
            return None, None

        sinal = None
        for pref in ("<=", ">=", "<", ">"):
            if s.startswith(pref):
                sinal = pref
                s = s[len(pref):].strip()
                break

        s = s.replace("%", "").replace(".", "") if "," in s else s
        s = s.replace(",", ".").strip()
        return sinal, s

    sinais, valores = zip(*df_total["valor_medido"].apply(_parse_valor))
    df_total["sinal_limite"] = [
        s if pd.isna(orig) or orig == "" else orig
        for s, orig in zip(sinais, df_total.get("sinal_limite", [None] * len(df_total)))
    ]
    df_total["valor_medido"] = pd.to_numeric(valores, errors="coerce")

    # Harmonizar nomes de parametro para casar com cadastro de VMP
    if "nome_parametro" in df_total.columns:
        df_total["nome_parametro_original"] = df_total["nome_parametro"]
        df_total["nome_parametro"] = df_total["nome_parametro"].map(
            lambda p: PARAM_ALIAS_MAP.get(p, p)
        )

    print(f"   ✅ {len(df_total)} registros lidos.")
    return df_total


def _carregar_vmps() -> pd.DataFrame:
    print(f"📂  Lendo VMPs: {PLANILHA_PARAMETROS.name}")
    df = pd.read_excel(str(PLANILHA_PARAMETROS))
    df = _normalizar_colunas(df)
    if "nome_parametro" not in df.columns:
        sys.exit(
            f"❌  Coluna 'nome_parametro' não encontrada em {PLANILHA_PARAMETROS.name}.\n"
            f"   Colunas encontradas: {list(df.columns)}"
        )
    for c in VMP_COLUNAS:
        if c not in df.columns:
            df[c] = None
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    print(f"   ✅ {len(df)} parâmetros mapeados.")
    return df


def _montar_df_final(df_res: pd.DataFrame, df_vmp: pd.DataFrame) -> pd.DataFrame:
    """Une resultados com VMPs e adiciona metadados do projeto."""
    df = df_res.merge(df_vmp[["nome_parametro"] + VMP_COLUNAS],
                      on="nome_parametro", how="left")
    df["codigo_interno_opyta"] = CODIGO_PROJETO
    df["nome_projeto"]         = NOME_PROJETO
    df["nome_empresa"]         = NOME_EMPRESA

    # Garantir colunas opcionais
    for col in ["data_hora_coleta", "latitude", "longitude",
                "laboratorio_responsavel", "bacia_hidrografica",
                "observacoes_resultado", "unidade_medida"]:
        if col not in df.columns:
            df[col] = None

    return df


def _validar(df: pd.DataFrame):
    nulos_criticos = df[COLUNAS_OBRIGATORIAS].isnull().sum()
    matrizes = sorted(df["matriz"].dropna().astype(str).unique().tolist()) if "matriz" in df.columns else []
    campanhas = sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()) if "nome_campanha" in df.columns else []
    pontos = sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()) if "nome_ponto" in df.columns else []
    print("\n📊  Validação:")
    print(f"   Total de registros : {len(df)}")
    print(f"   Matrizes           : {matrizes}")
    print(f"   Campanhas          : {campanhas}")
    print(f"   Pontos             : {pontos}")
    print(f"   Parâmetros         : {df['nome_parametro'].nunique()}")
    print(f"   Nulos críticos     :\n{nulos_criticos[nulos_criticos > 0]}")
    if nulos_criticos.sum() > 0:
        print("   ⚠️   Há nulos em colunas obrigatórias — revise antes de inserir.")


# ---------------------------------------------------------------------------
# Migração
# ---------------------------------------------------------------------------

COLS_INSERT = [
    "codigo_interno_opyta", "nome_projeto", "nome_empresa",
    "nome_campanha", "nome_ponto", "data_hora_coleta",
    "latitude", "longitude", "bacia_hidrografica",
    "matriz", "nome_parametro", "sinal_limite",
    "valor_medido", "unidade_medida", "unidade_original_laudo",
    "laboratorio_responsavel", "observacoes_resultado",
] + VMP_COLUNAS


def _inserir(df: pd.DataFrame, engine, truncate: bool):
    from sqlalchemy import text

    with engine.begin() as conn:
        if truncate:
            print(f"\n🗑️   Removendo registros existentes de {CODIGO_PROJETO}...")
            conn.execute(
                text("DELETE FROM fisico_analise_consolidada "
                     "WHERE codigo_interno_opyta = :cod"),
                {"cod": CODIGO_PROJETO},
            )
            print("   ✅ Registros removidos.")

        # Manter apenas colunas que existem no DataFrame
        cols = [c for c in COLS_INSERT if c in df.columns]
        df_ins = df[cols].where(pd.notna(df[cols]), other=None)

        records = df_ins.to_dict(orient="records")
        chunk_size = 500

        print(f"\n⬆️   Inserindo {len(records)} registros em lotes de {chunk_size}...")
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            cols_str = ", ".join(cols)
            placeholders = ", ".join([f":{c}" for c in cols])
            sql = text(
                f"INSERT INTO fisico_analise_consolidada ({cols_str}) "
                f"VALUES ({placeholders})"
            )
            conn.execute(sql, chunk)
            print(f"   Lote {i // chunk_size + 1}: {len(chunk)} registros.")

    print(f"\n✅  Migração concluída: {len(records)} registros inseridos.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Migração SAM Metais — Meio Físico")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Apenas valida e exibe — não insere no banco.")
    parser.add_argument("--truncate", action="store_true",
                        help="Apaga registros de FERSAM001 antes de inserir.")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Pula a validacao pre-migracao (nao recomendado).")
    parser.add_argument("--allow-validation-errors", action="store_true",
                        help="Permite seguir mesmo com erro na validacao (uso excepcional).")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  Migração Meio Físico — {CODIGO_PROJETO}")
    print("=" * 60)

    # Verificar arquivos
    for p in (PLANILHA_RESULTADOS, PLANILHA_PARAMETROS):
        if not p.exists():
            sys.exit(f"❌  Arquivo não encontrado: {p}")

    if not args.skip_validation:
        validator_script = Path(__file__).with_name("validar_meio_fisico_sam.py")
        if not validator_script.exists():
            sys.exit(f"❌  Validador não encontrado: {validator_script}")

        print("\n🔎  Executando validação pre-migração...")
        cmd = [
            sys.executable,
            str(validator_script),
            "--base-dir",
            str(PASTA_MIGRACAO),
        ]
        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0 and not args.allow_validation_errors:
            sys.exit(
                "❌  Validação retornou erro. Corrija os achados antes da migração.\n"
                "   Para forçar (não recomendado), use --allow-validation-errors."
            )

    df_res = _carregar_resultados()
    df_vmp = _carregar_vmps()
    df_final = _montar_df_final(df_res, df_vmp)
    _validar(df_final)

    if args.dry_run:
        print("\n🔍  DRY-RUN — nenhum dado foi inserido no banco.")
        print("   Execute sem --dry-run para inserir.")
        return

    engine = _get_engine()
    _inserir(df_final, engine, truncate=args.truncate)


if __name__ == "__main__":
    main()
