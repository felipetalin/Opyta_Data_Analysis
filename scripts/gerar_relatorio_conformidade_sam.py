#!/usr/bin/env python3
"""
Gerador de Relatório de Conformidade — SAM Metais Meio Físico
Segue padrão visual identificado em exemplos existentes
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import json
from datetime import datetime
import re
import unicodedata
import colorsys

# Config
BASE_DIR = Path(r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos")
INPUT_EXCEL = BASE_DIR / "Migração/Físico/Resultados_Meio_Fisico.xlsx"
VMP_CADASTRO = BASE_DIR / "Migração/Físico/cadastro_parametros_opyta.xlsx"
OUTPUT_BASE = BASE_DIR / "Resultados/Meio_físico"
CONFIG_DIR = Path(r"G:/Meu Drive/Opyta/Opyta_Data_Analysis/configs")
THEME_FILE = CONFIG_DIR / "theme_gold_approved.json"

# Padrão visual
POINT_COLOR = "#1f77b4"  # Azul
VMP_COLOR = "#d62728"     # Vermelho
VIOLATION_COLOR = "#ffcccc"  # Rosa claro
VIOLATION_BAR_COLOR = "#e67e7e"  # Coral

FIGSIZE = (14, 9)
DPI = 600
FAUNA_CAMPAIGN_BASE_HEX = "#11420C"

# Consolidacao oficial solicitada para a tabela de conformidade.
PARAM_CANONICAL_MAP = {
    "pH": "pH In Situ",
}


def _normalize_text(value: str) -> str:
    s = str(value or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _campanha_sort_key(campanha: str):
    s = str(campanha or "")
    m = re.search(r"(\d+)", s)
    if m:
        return (0, int(m.group(1)), s)
    return (1, 9999, s)


def _ponto_sort_key(ponto: str):
    s = str(ponto or "").strip()
    m = re.search(r"(\d+)", s)
    if m:
        return (0, int(m.group(1)), s)
    return (1, 9999, s)


def _hex_to_rgb(hex_color: str):
    h = str(hex_color).lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


def _green_palette_from_hex(base_hex: str, n: int):
    rgb_base = _hex_to_rgb(base_hex)
    h, s, _v = colorsys.rgb_to_hsv(*rgb_base)
    colors = []
    for i in range(max(n, 1)):
        t = i / max(n - 1, 1)
        new_v = 0.5 + 0.5 * t
        new_s = 0.8 + 0.2 * t
        rgb = colorsys.hsv_to_rgb(h, new_s, new_v)
        colors.append(_rgb_to_hex(rgb))
    return colors


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


def _carregar_dados_por_matriz(df_res, matriz_nome):
    """Filtra e prepara dados por matriz (sem mesclar campanhas)."""
    df_sub = df_res[df_res["Matriz"].str.contains(matriz_nome, case=False, na=False)].copy()
    
    if df_sub.empty:
        return None
    
    # Parse valores
    df_sub[["sinal_limite", "valor_medido"]] = df_sub["Resultado"].apply(
        lambda x: pd.Series(_parse_valor(x))
    )

    # Consolidacao de nomenclatura oficial
    df_sub["Parametro"] = df_sub["Parametro"].map(lambda p: PARAM_CANONICAL_MAP.get(str(p), str(p)))
    df_sub["Campanha"] = df_sub["Campanha"].astype(str).str.strip()
    df_sub["Ponto"] = df_sub["Ponto"].astype(str).str.strip()
    df_sub["Matriz"] = df_sub["Matriz"].astype(str).str.strip()

    return df_sub


def _agrupar_para_graficos(df_sub):
    """Estrutura para graficos legados (agregado por ponto)."""
    resultado = {}
    for param in df_sub["Parametro"].unique():
        df_param = df_sub[df_sub["Parametro"] == param].dropna(subset=["valor_medido"])
        if df_param.empty:
            continue

        pontos_valores = {}
        for ponto in df_param["Ponto"].unique():
            vals = df_param[df_param["Ponto"] == ponto]["valor_medido"].astype(float)
            if not vals.empty:
                pontos_valores[ponto] = float(vals.mean())

        if pontos_valores:
            resultado[param] = pontos_valores
    
    return resultado


def _gerar_tabela_conformidade(df_sub, vmp_map, output_dir):
    """Gera 01_Tabela_Conformidade com dados reais separados por campanha e ponto."""
    base = df_sub.dropna(subset=["valor_medido"]).copy()
    if base.empty:
        df_empty = pd.DataFrame(columns=["Parâmetro", "Unidade", "VMP Classe 2", "Conformidade (%)"])
        output_file = output_dir / "01_Tabela_Conformidade.xlsx"
        df_empty.to_excel(output_file, index=False, sheet_name="Conformidade")
        return output_file, df_empty

    params = sorted(base["Parametro"].dropna().unique().tolist())
    campanhas = sorted(base["Campanha"].dropna().unique().tolist(), key=_campanha_sort_key)

    pontos_por_camp = {}
    for camp in campanhas:
        pontos = sorted(base.loc[base["Campanha"] == camp, "Ponto"].dropna().unique().tolist(), key=_ponto_sort_key)
        pontos_por_camp[camp] = pontos

    grouped = (
        base.groupby(["Parametro", "Campanha", "Ponto"], dropna=False)["valor_medido"]
        .mean()
        .reset_index()
    )

    rows = []
    for param in params:
        vmp_info = vmp_map.get(param, {})
        vmp = vmp_info.get("vmp_cl2", vmp_info.get("vmp_cl1", None))
        row = {
            "Parâmetro": param,
            "Unidade": vmp_info.get("unidade", ""),
            "VMP Classe 2": vmp,
        }

        # Conformidade geral e por campanha
        sub_param = grouped[grouped["Parametro"] == param]
        if vmp is not None and not sub_param.empty:
            total = len(sub_param)
            conf = int((sub_param["valor_medido"] <= float(vmp)).sum())
            row["Conformidade (%)"] = round((conf / total) * 100, 2) if total else None
            for camp in campanhas:
                sc = sub_param[sub_param["Campanha"] == camp]
                if sc.empty:
                    row[f"Conformidade {camp} (%)"] = None
                else:
                    c_total = len(sc)
                    c_conf = int((sc["valor_medido"] <= float(vmp)).sum())
                    row[f"Conformidade {camp} (%)"] = round((c_conf / c_total) * 100, 2)
        else:
            row["Conformidade (%)"] = None
            for camp in campanhas:
                row[f"Conformidade {camp} (%)"] = None

        # Colunas na ordem: Campanha seca + pontos; Campanha chuva + pontos
        for camp in campanhas:
            for ponto in pontos_por_camp.get(camp, []):
                key = f"{camp} | {ponto}"
                hit = sub_param[(sub_param["Campanha"] == camp) & (sub_param["Ponto"] == ponto)]
                row[key] = float(hit["valor_medido"].iloc[0]) if not hit.empty else None

        rows.append(row)

    df_conform = pd.DataFrame(rows)

    # Reordena colunas fixas + conformidade por campanha + colunas de dados por campanha/ponto
    ordered_cols = ["Parâmetro", "Unidade", "VMP Classe 2", "Conformidade (%)"]
    ordered_cols.extend([f"Conformidade {c} (%)" for c in campanhas])
    for camp in campanhas:
        ordered_cols.extend([f"{camp} | {p}" for p in pontos_por_camp.get(camp, [])])
    df_conform = df_conform.reindex(columns=ordered_cols)

    output_file = output_dir / "01_Tabela_Conformidade.xlsx"
    try:
        df_conform.to_excel(output_file, index=False, sheet_name="Conformidade")
    except PermissionError:
        alt = output_dir / "01_Tabela_Conformidade_v2.xlsx"
        df_conform.to_excel(alt, index=False, sheet_name="Conformidade")
        output_file = alt

    return output_file, df_conform


def _gerar_grafico_parametro(param, pontos_valores, vmp_value, unidade, matriz_nome, output_dir):
    """Gera gráfico individual de parâmetro (estilo Coliformes)"""
    if not pontos_valores:
        return None
    
    fig, ax = plt.subplots(figsize=FIGSIZE)
    
    # Dados
    pontos = sorted(pontos_valores.keys())
    valores = [pontos_valores[p] for p in pontos]
    
    # Plot
    ax.scatter(range(len(pontos)), valores, s=100, color=POINT_COLOR, zorder=3, label="Amostra")
    
    # Linha VMP
    if vmp_value is not None:
        ax.axhline(y=vmp_value, color=VMP_COLOR, linewidth=2, zorder=2, label=f"VMP Cl2 ({vmp_value:.1f})")
        
        # Sombreamento de violação (acima do VMP)
        y_min = ax.get_ylim()[0]
        y_max = max(max(valores), vmp_value * 1.1) if valores else vmp_value * 1.1
        ax.axhspan(vmp_value, y_max, color=VIOLATION_COLOR, alpha=0.3, zorder=0)
    
    # Formatação
    ax.set_xticks(range(len(pontos)))
    ax.set_xticklabels(pontos, rotation=45, ha="right", fontsize=11)
    ax.set_xlabel("nome_ponto", fontsize=12, fontweight="bold")
    ax.set_ylabel(f"{param} ({unidade})", fontsize=12, fontweight="bold")
    ax.set_title(f"{param} ({matriz_nome})", fontsize=14, fontweight="bold", pad=15)
    
    ax.grid(True, alpha=0.3, zorder=1)
    ax.legend(title="Campanhas e VMPs", loc="upper right", frameon=True, fontsize=11)
    
    plt.tight_layout()
    
    # Salva
    output_file = output_dir / f"{param.replace(' ', '_').replace('/', '_')}.png"
    fig.savefig(output_file, dpi=DPI, bbox_inches="tight")
    plt.close()
    
    return output_file


def _gerar_grafico_violacao(dados_por_param, vmp_map, matriz_nome, output_dir):
    """Gera gráfico de percentual de violação (barras horizontais)"""
    params_list = []
    violacao_pct = []
    
    for param, pontos_valores in sorted(dados_por_param.items()):
        vmp_info = vmp_map.get(param, {})
        vmp = vmp_info.get("vmp_cl2", vmp_info.get("vmp_cl1", None))
        
        if vmp is None or not pontos_valores:
            continue
        
        violados = sum(1 for v in pontos_valores.values() if float(v) > float(vmp))
        total = len(pontos_valores)
        pct = (violados / total * 100) if total > 0 else 0
        
        params_list.append(param)
        violacao_pct.append(pct)
    
    if not params_list:
        return None
    
    fig, ax = plt.subplots(figsize=FIGSIZE)
    
    # Barras horizontais
    y_pos = np.arange(len(params_list))
    ax.barh(y_pos, violacao_pct, color=VIOLATION_BAR_COLOR, height=0.6, zorder=2)
    
    # Formatação
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params_list, fontsize=11)
    ax.set_xlabel("Percentual de Pontos com Violação (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("nome_parametro", fontsize=12, fontweight="bold")
    ax.set_title(f"Distribuição de Violação - {matriz_nome}", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlim(0, 100)
    
    ax.grid(True, axis="x", alpha=0.3, zorder=1)
    ax.legend(["1ª-Campanha-Seca"], loc="upper right", fontsize=11)
    
    plt.tight_layout()
    
    # Salva
    output_file = output_dir / "02_Percentual_Violacao.png"
    fig.savefig(output_file, dpi=DPI, bbox_inches="tight")
    plt.close()
    
    return output_file


def _gerar_piloto_coliformes_gold(df_res, vmp_map, output_dir, theme):
    """Piloto: Coliformes com padrão Gold da fauna (2 campanhas, legenda topo, sem título)."""
    alvo_norm = _normalize_text("Coliformes Termotolerantes por tubos múltiplos - NMP")

    d = df_res.copy()
    d.columns = [str(c).strip() for c in d.columns]
    d = d[d["Matriz"].astype(str).str.strip().str.contains("Água Superficial", case=False, na=False)].copy()
    if d.empty:
        return None

    d["Parametro_norm"] = d["Parametro"].astype(str).map(_normalize_text)
    d = d[d["Parametro_norm"] == alvo_norm].copy()
    if d.empty:
        return None

    d[["sinal_limite", "valor_medido"]] = d["Resultado"].apply(lambda x: pd.Series(_parse_valor(x)))
    d = d.dropna(subset=["valor_medido"]).copy()
    if d.empty:
        return None

    d["nome_campanha"] = d["Campanha"].astype(str).str.strip()
    d["nome_ponto"] = d["Ponto"].astype(str).str.strip()

    campaigns = sorted(d["nome_campanha"].dropna().unique().tolist(), key=_campanha_sort_key)
    points = sorted(d["nome_ponto"].dropna().unique().tolist())
    if not campaigns or not points:
        return None

    pivot = (
        d.groupby(["nome_ponto", "nome_campanha"], dropna=False)["valor_medido"]
        .mean()
        .reset_index()
        .pivot_table(index="nome_ponto", columns="nome_campanha", values="valor_medido", aggfunc="mean")
        .reindex(index=points, columns=campaigns)
    )

    # Padrão fauna (FERSAM001): paleta verde por campanha.
    palette = _green_palette_from_hex(FAUNA_CAMPAIGN_BASE_HEX, len(campaigns))
    color_map = {camp: palette[i] for i, camp in enumerate(campaigns)}

    fig, ax = plt.subplots(figsize=tuple(theme.get("figsize_standard", [15, 10])), dpi=int(theme.get("dpi", DPI)))

    x = np.arange(len(points), dtype=float)
    n_camps = max(len(campaigns), 1)
    offsets = np.linspace(-0.15, 0.15, n_camps) if n_camps > 1 else np.array([0.0])

    for i, camp in enumerate(campaigns):
        vals = pivot[camp].values.astype(float)
        valid = ~np.isnan(vals)
        if not np.any(valid):
            continue
        # Padrão solicitado: pontos por campanha, sem linhas de conexão.
        ax.scatter(
            x[valid] + offsets[i],
            vals[valid],
            s=70,
            marker="o",
            label=camp,
            color=color_map[camp],
            edgecolors="black",
            linewidths=0.4,
            zorder=4,
        )

    vmp = None
    param_cadastro = d["Parametro"].mode().iloc[0]
    if param_cadastro in vmp_map:
        vmp = vmp_map[param_cadastro].get("vmp_cl2") or vmp_map[param_cadastro].get("vmp_cl1")

    if vmp is not None:
        vmp_color = str(theme.get("mf_vmp_n2", VMP_COLOR))
        ax.axhline(float(vmp), color=vmp_color, linewidth=2.0, label=f"VMP Cl2 ({float(vmp):.1f})", zorder=2)
        ax.axhspan(
            float(vmp),
            max(float(np.nanmax(pivot.values)), float(vmp) * 1.10),
            color=str(theme.get("mf_vmp_shade", VIOLATION_COLOR)),
            alpha=float(theme.get("mf_vmp_shade_alpha", 0.10)),
            zorder=1,
        )

    loq_vals = d[d["sinal_limite"] == "<"]["valor_medido"].dropna().astype(float)
    if not loq_vals.empty:
        loq = float(np.nanmax(loq_vals.values))
        ax.axhline(
            loq,
            color=str(theme.get("mf_vmp_n1", "#f39c12")),
            linewidth=1.8,
            linestyle="--",
            label=f"Limite de Quantificacao ({loq:.2f})",
            zorder=2,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(points, rotation=45, ha="right", fontsize=int(theme.get("campaign_label_size", 14)))
    ax.set_xlabel("Ponto", fontsize=int(theme.get("font_size_base", 14)))
    ax.set_ylabel("Coliformes Termotolerantes (NMP/100 mL)", fontsize=int(theme.get("font_size_base", 14)))

    # Padrão Gold fauna: sem título no corpo e legenda no topo.
    ax.set_title("")
    ax.grid(
        axis="y",
        linestyle=str(theme.get("grid_linestyle", "--")),
        linewidth=float(theme.get("grid_linewidth", 0.6)),
        alpha=float(theme.get("grid_alpha", 0.25)),
    )
    ax.grid(
        axis="x",
        linestyle=str(theme.get("grid_linestyle", "--")),
        linewidth=float(theme.get("grid_linewidth", 0.6)),
        alpha=float(theme.get("grid_alpha", 0.25)),
    )

    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(str(theme.get("spine_color", "#000000")))
        ax.spines[side].set_linewidth(float(theme.get("spine_linewidth", 1.2)))

    handles, labels = ax.get_legend_handles_labels()
    legend = fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.99),
        ncol=min(max(2, len(campaigns)), 4),
        frameon=False,
    )
    for t in legend.get_texts():
        t.set_fontsize(int(theme.get("legend_size", 13)))

    fig.tight_layout(rect=[0, 0, 1, 0.90])

    out = output_dir / "PILOTO_Coliformes_Gold_Fauna.png"
    fig.savefig(out, dpi=int(theme.get("dpi", DPI)), bbox_inches="tight")
    plt.close(fig)
    return out


def main():
    print("=" * 70)
    print("  Gerador Relatório Conformidade — SAM Metais Meio Físico")
    print("=" * 70)
    
    # Carrega dados
    print("\n📂  Carregando dados...")
    df_res = pd.read_excel(INPUT_EXCEL, sheet_name="Resultados_Meio_Fisico", dtype=str)
    df_vmp = pd.read_excel(VMP_CADASTRO, dtype=str)
    
    print(f"   ✅ {len(df_res)} resultados")
    print(f"   ✅ {len(df_vmp)} parâmetros VMP")
    
    # Normaliza colunas
    for d in [df_res, df_vmp]:
        d.columns = [str(c).strip() for c in d.columns]
    
    # Monta mapa VMP
    vmp_map = {}
    for _, row in df_vmp.iterrows():
        param = str(row.get("Parametro", "")).strip()
        unidade = str(row.get("Unidade_Medida", "")).strip()
        
        vmp_cl2_max = row.get("VMP_357_Cl2_Max")
        vmp_cl1_max = row.get("VMP_357_Cl1_Max")
        
        # Converte para float, ignorando '-' e NaN
        def to_float(val):
            if pd.isna(val):
                return None
            s = str(val).strip()
            if s in {"-", "nan", "NaN", ""}:
                return None
            try:
                return float(s)
            except:
                return None
        
        vmp_map[param] = {
            "unidade": unidade,
            "vmp_cl1": to_float(vmp_cl1_max),
            "vmp_cl2": to_float(vmp_cl2_max),
        }
    
    theme = _load_theme()

    # Processa matrizes
    matrices = {
        "Água Superficial": "Superficial",
        "Água Subterrânea": "Subterrânea",
        "Sedimento": "Sedimentos",
    }
    
    for matriz_orig, pasta_tema in matrices.items():
        print(f"\n🎨  Processando {pasta_tema}...")
        
        pasta_saida = OUTPUT_BASE / pasta_tema
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        # Carrega dados dessa matriz
        df_matriz = _carregar_dados_por_matriz(df_res, matriz_orig)
        dados = _agrupar_para_graficos(df_matriz) if df_matriz is not None else None
        
        if dados is None:
            print(f"   ⚠️   Sem dados")
            continue
        
        # Tabela de conformidade
        print(f"   📋 Gerando tabela...")
        tab_file, tab_df = _gerar_tabela_conformidade(df_matriz, vmp_map, pasta_saida)
        print(f"       ✅ {tab_file.name}")
        
        # Gráficos por parâmetro
        print(f"   📊 Gerando gráficos por parâmetro...")
        count = 0
        for param in sorted(dados.keys()):
            vmp_info = vmp_map.get(param, {})
            vmp = vmp_info.get("vmp_cl2") or vmp_info.get("vmp_cl1")
            unidade = vmp_info.get("unidade", "")
            
            graph_file = _gerar_grafico_parametro(
                param, dados[param], vmp, unidade, matriz_orig, pasta_saida
            )
            if graph_file:
                count += 1
        print(f"       ✅ {count} gráficos")
        
        # Gráfico de violação
        print(f"   📊 Gerando gráfico de violação...")
        viol_file = _gerar_grafico_violacao(dados, vmp_map, matriz_orig, pasta_saida)
        if viol_file:
            print(f"       ✅ {viol_file.name}")

    # Piloto específico solicitado: Coliformes em Água Superficial no padrão Gold da fauna.
    piloto_dir = OUTPUT_BASE / "Superficial"
    piloto_dir.mkdir(parents=True, exist_ok=True)
    piloto = _gerar_piloto_coliformes_gold(df_res, vmp_map, piloto_dir, theme)
    if piloto:
        print(f"\n🎯  Piloto Gold (Fauna) gerado: {piloto.name}")
    else:
        print("\n⚠️   Piloto Gold (Fauna) não gerado: parâmetro de coliformes não encontrado.")
    
    print("\n" + "=" * 70)
    print("✅  Relatório completo gerado!")
    print("=" * 70)


if __name__ == "__main__":
    main()
