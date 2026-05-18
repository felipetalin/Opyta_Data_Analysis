"""
Migração Meio Físico via REST — Fiel ao pipeline SQL
====================================================
- Valida todos os parâmetros/matrizes contra o cadastro mestre (parametros_analise)
- Harmoniza e audita os dados conforme staging do script original
- Insere apenas registros válidos, abortando e exibindo erro detalhado se houver inconsistência
- Segue o padrão de staging e distribuição, respeitando as regras do banco
"""
import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Adiciona src ao sys.path para importar opyta_analysis
SRC_PATH = Path(__file__).parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
from opyta_analysis.supabase_client import get_client

# Configurações
PLANILHA_RESULTADOS = r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos/Migração/Físico/Resultados_Meio_Fisico.xlsx"
ABA_RESULTADOS = "Resultados_Meio_Fisico"

# Carregar variáveis de ambiente
load_dotenv()
sb = get_client()

# 1. Carregar cadastro mestre de parâmetros/matrizes
print("🔎 Lendo cadastro mestre de parâmetros...")
parametros = sb.table("parametros_analise").select("nome_parametro,matriz").execute().data
cadastro_keys = set(f"{p['nome_parametro'].strip()}|{p['matriz'].strip()}" for p in parametros)

# 2. Carregar resultados da planilha
print("📥 Lendo Excel de resultados...")
df_res = pd.read_excel(PLANILHA_RESULTADOS, sheet_name=ABA_RESULTADOS).dropna(subset=["Ponto", "Parametro"])

# 3. Validação dos parâmetros/matrizes
planilha_keys = set(df_res["Parametro"].str.strip() + "|" + df_res["Matriz"].str.strip())
erros = planilha_keys - cadastro_keys
if erros:
    print("\n❌ ERRO DE VALIDAÇÃO: Os seguintes parâmetros/matrizes NÃO estão no Cadastro Mestre:")
    for erro in erros:
        p, m = erro.split("|")
        print(f"   - Parâmetro: '{p}' | Matriz: '{m}'")
    print("\n⚠️ A migração foi interrompida. Adicione-os como novos parâmetros ou sinônimos no Cadastro Mestre.")
    sys.exit(1)
print("✅ Todos os parâmetros validados! Iniciando upload...")

# 4. Harmonização e staging
print("🔄 Harmonizando dados para staging...")
df_res_staging = df_res[["Ponto", "Campanha", "Matriz", "Parametro", "Resultado", "Unidade_Medida", "Laboratorio"]].copy()
df_res_staging.columns = ["ponto_nome", "campanha_nome", "matriz_nome", "parametro_nome", "resultado_texto", "unidade", "laboratorio"]
df_res_staging["resultado_texto"] = df_res_staging["resultado_texto"].astype(str).str.replace(",", ".")

# 5. Inserção via REST (em lotes)
print("⬆️ Inserindo dados em lotes de 500...")
registros = df_res_staging.to_dict(orient="records")
BATCH = 500
for i in range(0, len(registros), BATCH):
    batch = registros[i:i+BATCH]
    print(f"Inserindo registros {i+1} a {i+len(batch)}...")
    resp = sb.table("staging_resultados_fisicos").insert(batch).execute()
    if resp.error:
        print(f"Erro ao inserir lote {i//BATCH+1}: {resp.error}")
        sys.exit(1)
    else:
        print(f"Lote {i//BATCH+1} inserido com sucesso.")

print("⚙️ Distribuindo resultados no banco via função SQL (execute manualmente se necessário)...")
print("\nMIGRAÇÃO CONCLUÍDA ATÉ O STAGING. Para finalizar, execute a distribuição SQL conforme o pipeline original.")
