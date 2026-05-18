#!/usr/bin/env python3
"""
Gerador standalone de Meio Físico — SAM Metais
Lê da Excel, gera gráficos e relatórios sem depender do Supabase
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from datetime import datetime

# Config
BASE_DIR = Path(r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos")
INPUT_EXCEL = BASE_DIR / "Migração/Físico/Resultados_Meio_Fisico.xlsx"
VMP_CADASTRO = BASE_DIR / "Migração/Físico/cadastro_parametros_opyta.xlsx"
OUTPUT_BASE = BASE_DIR / "Resultados/Meio_físico"
CONFIG_DIR = Path(r"G:/Meu Drive/Opyta/Opyta_Data_Analysis/configs")
THEME_FILE = CONFIG_DIR / "theme_gold_approved.json"

# Temas por matriz
MATRICES = {
    "Água Superficial": "Superficial",
    "Água Subterrânea": "Subterrânea",
    "Sedimento": "Sedimentos",
}


def _load_theme():
    """Carrega tema Gold"""
    with open(THEME_FILE) as f:
        return json.load(f)


def _parse_valor(s):
    """Parse valor_medido com símbolo"""
    if pd.isna(s):
        return None, None
    s = str(s).strip()
    if not s or s.upper() in {"NI", "N/I", "ND", "N/D", "NA", "N/A", "-", "--"}:
        return None, None
    
    sinal = None
    if s.startswith("<="):
        sinal = "<="
        s = s[2:].strip()
    elif s.startswith(">="):
        sinal = ">="
        s = s[2:].strip()
    elif s.startswith("<"):
        sinal = "<"
        s = s[1:].strip()
    elif s.startswith(">"):
        sinal = ">"
        s = s[1:].strip()
    
    s = s.replace(".", "").replace(",", ".")
    try:
        val = float(s)
        return sinal, val
    except:
        return None, None


def main():
    print("=" * 70)
    print("  Gerador Meio Físico Standalone — SAM Metais")
    print("=" * 70)
    
    # Carrega dados
    print("\n📂  Carregando dados...")
    df_res = pd.read_excel(INPUT_EXCEL, sheet_name="Resultados_Meio_Fisico", dtype=str)
    df_pts = pd.read_excel(INPUT_EXCEL, sheet_name="Pontos_e_Campanhas", dtype=str)
    df_vmp = pd.read_excel(VMP_CADASTRO, dtype=str)
    
    print(f"   ✅ {len(df_res)} resultados lidos")
    print(f"   ✅ {len(df_pts)} pontos carregados")
    print(f"   ✅ {len(df_vmp)} parâmetros VMP")
    
    # Normaliza colunas
    for d in [df_res, df_pts, df_vmp]:
        d.columns = [str(c).strip() for c in d.columns]
    
    df_res["Matriz"] = df_res["Matriz"].str.strip()
    df_res["Campanha"] = df_res["Campanha"].str.strip()
    df_res["Parametro"] = df_res["Parametro"].str.strip()
    
    # Parse valores
    print("\n📊  Parseando valores...")
    df_res[["sinal_limite", "valor_medido"]] = df_res["Resultado"].apply(
        lambda x: pd.Series(_parse_valor(x))
    )
    
    null_count = df_res["valor_medido"].isna().sum()
    print(f"   ✅ {len(df_res) - null_count} valores parseados ({null_count} nulos)")
    
    # Carrega tema
    theme = _load_theme()
    figsize = (15, 10)
    
    # Cria pastas de saída
    for matriz_nome, pasta_nome in MATRICES.items():
        pasta = OUTPUT_BASE / pasta_nome
        pasta.mkdir(parents=True, exist_ok=True)
    
    # Filtra por matriz
    for matriz_orig, pasta_tema in MATRICES.items():
        print(f"\n🎨  Processando {pasta_tema}...")
        
        # Filtra dados dessa matriz
        df_sub = df_res[df_res["Matriz"].str.contains(matriz_orig, case=False, na=False)].copy()
        
        if df_sub.empty:
            print(f"   ⚠️   Nenhum dado para {matriz_orig}")
            continue
        
        pasta_saida = OUTPUT_BASE / pasta_tema
        
        # Gráfico 1: Distribuição espacial por parâmetro (top 6)
        top_params = df_sub["Parametro"].value_counts().head(6).index
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        axes = axes.flatten()
        
        for idx, param in enumerate(top_params):
            df_param = df_sub[df_sub["Parametro"] == param].dropna(subset=["valor_medido"])
            if df_param.empty:
                axes[idx].text(0.5, 0.5, f"Sem dados: {param}", ha="center")
                axes[idx].set_title(param, fontsize=13, fontweight="bold")
                continue
            
            valores = df_param.groupby("Ponto")["valor_medido"].mean()
            axes[idx].bar(range(len(valores)), valores.values, color="#2980b9")
            axes[idx].set_title(param, fontsize=13, fontweight="bold")
            axes[idx].set_xlabel("Ponto", fontsize=11)
            axes[idx].tick_params(axis="x", rotation=45)
        
        fig.suptitle(f"Distribuição Espacial — {pasta_tema}", fontsize=16, fontweight="bold", y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        output_file = pasta_saida / f"01_Distribuicao_Espacial_{pasta_tema}.png"
        fig.savefig(output_file, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close()
        print(f"   ✅ {output_file.name}")
        
        # Gráfico 2: Série temporal por campanha (top 3 parâmetros)
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        
        for idx, param in enumerate(top_params[:3]):
            df_param = df_sub[df_sub["Parametro"] == param].dropna(subset=["valor_medido"])
            if df_param.empty:
                axes[idx].text(0.5, 0.5, f"Sem dados: {param}", ha="center")
                axes[idx].set_title(param, fontsize=13, fontweight="bold")
                continue
            
            campanhas = sorted(df_param["Campanha"].unique())
            valores_camp = [df_param[df_param["Campanha"] == c]["valor_medido"].mean() for c in campanhas]
            
            axes[idx].plot(campanhas, valores_camp, marker="o", linewidth=2, markersize=8, color="#e74c3c")
            axes[idx].set_title(param, fontsize=13, fontweight="bold")
            axes[idx].set_xlabel("Campanha", fontsize=11)
            axes[idx].tick_params(axis="x", rotation=45)
            axes[idx].grid(True, alpha=0.3)
        
        fig.suptitle(f"Série Temporal — {pasta_tema}", fontsize=16, fontweight="bold", y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        output_file = pasta_saida / f"02_Serie_Temporal_{pasta_tema}.png"
        fig.savefig(output_file, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close()
        print(f"   ✅ {output_file.name}")
        
        # Heatmap: Parâmetros vs Pontos
        fig, ax = plt.subplots(figsize=(14, 8))
        
        pivot_data = df_sub.pivot_table(
            values="valor_medido",
            index="Parametro",
            columns="Ponto",
            aggfunc="mean"
        )
        
        if not pivot_data.empty:
            im = ax.imshow(pivot_data.values, cmap="RdYlGn_r", aspect="auto")
            ax.set_xticks(range(len(pivot_data.columns)))
            ax.set_yticks(range(len(pivot_data.index)))
            ax.set_xticklabels(pivot_data.columns, rotation=45, ha="right", fontsize=10)
            ax.set_yticklabels(pivot_data.index, fontsize=10)
            plt.colorbar(im, ax=ax, label="Valor Medido")
        
        fig.suptitle(f"Heatmap Parâmetros × Pontos — {pasta_tema}", fontsize=16, fontweight="bold", y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        output_file = pasta_saida / f"03_Heatmap_{pasta_tema}.png"
        fig.savefig(output_file, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
        plt.close()
        print(f"   ✅ {output_file.name}")
    
    # Relatório resumido
    print("\n📋  Gerando relatório...")
    
    summary = {
        "data_geracao": datetime.now().isoformat(),
        "projeto": "SAM Metais (FERSAM001)",
        "total_registros": int(len(df_res)),
        "registros_parseados": int(len(df_res) - null_count),
        "matrizes": list(MATRICES.keys()),
        "campanhas": sorted([str(c) for c in df_res["Campanha"].unique().tolist()]),
        "pontos_unicos": int(df_res["Ponto"].nunique()),
        "parametros_unicos": int(df_res["Parametro"].nunique()),
        "output_dir": str(OUTPUT_BASE),
        "figuras_geradas": int(3 * len(MATRICES)),  # 3 gráficos por matriz
    }
    
    report_file = OUTPUT_BASE / "relatorio_sumario.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ {report_file.name}")
    
    print("\n" + "=" * 70)
    print(f"✅  Geração completa! {summary['figuras_geradas']} figuras em:")
    for pasta_nome in MATRICES.values():
        print(f"   - {OUTPUT_BASE / pasta_nome}")
    print("=" * 70)


if __name__ == "__main__":
    main()
