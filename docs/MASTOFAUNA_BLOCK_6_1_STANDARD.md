# Padrão Block 6.1: Riqueza, Composição e Abundância (Mastofauna)

**Aprovado em:** 2026-05-13  
**Versão:** 3.0  
**Responsável:** Padrão Ouro - Qualidade Visual  
**Status:** ✅ REGISTRADO E OPERACIONAL

---

## 1. Identificação do Bloco

- **Código:** 6.1
- **Título:** Riqueza, Composição e Abundância (Mastofauna)
- **Métrica Principal:** Abundância por espécie (relativa % e contagem N)
- **Público-alvo:** Duas subpopulações (PCH e Área Controle) comparadas lado-a-lado

---

## 2. Especificação de Figuras

### 2.1 Tipo de Figura
- **Tipo:** Gráfico de barras horizontal (`barh`) com duas séries lado-a-lado
- **Orientação:** Horizontal (eixo X = métricas, eixo Y = espécies)
- **Séries:** Duas barras por espécie (abundância relativa + abundância total)

### 2.2 Dimensões
| Parâmetro | Valor | Notas |
|-----------|-------|-------|
| Resolução (DPI) | 600 | Padrão Ouro |
| Fundo | Branco (#FFFFFF) | Padrão Ouro |
| Altura da figura | Dinâmica (↑ com nº espécies) | Mín. 6 pol., máx. 14 pol. |
| Largura da figura | Dinâmica | Mín. 10 pol., máx. 16 pol. |
| Formato | PNG | Padrão Ouro |

### 2.3 Barras e Espaçamento

#### Barra 1: Abundância Relativa (%)
- **Label:** "Abundância relativa (%)"
- **Largura:** `width = 0.35`
- **Posição Y:** `y_pos - offset_y / 2` (acima da linha central)
- **Cor:** Cor primária do tema (ex: #1f77b4)
- **Borda:** Preta, 0.8pt
- **Ordem de renderização:** Primeira (fundo)

#### Barra 2: Abundância Total (N)
- **Label:** "Abundância total (N)"
- **Largura:** `width = 0.15`
- **Posição Y:** `y_pos + offset_y / 2` (abaixo da linha central)
- **Cor:** Cor secundária do tema (ex: #ff7f0e)
- **Borda:** Preta, 0.8pt
- **Opacidade (alpha):** 0.7
- **Ordem de renderização:** Segunda (frente)

#### Espaçamento Vertical
- **Deslocamento (offset_y):** `0.2` unidades (20% da altura de uma barra)
- **Efeito:** Impede sobreposição visual completa; permite ver ambas as barras claramente

### 2.4 Anotações de Valores

**Abundância Relativa (%):**
- Posição: Extremidade direita da barra
- Formato: `"{:.1f}%"` (1 casa decimal)
- Fonte: Arial 11pt, cor preta

**Abundância Total (N):**
- Posição: Próxima ao final da barra (dentro se houver espaço, fora se barras pequenas)
- Formato: `"{:d}"` (inteiro, sem decimais)
- Fonte: Arial 10pt, cor preta, italizado

---

## 3. Tipografia e Texto

### 3.1 Eixo Y (Nomes de Espécies)
- **Ordem:** Classificação científica (nome científico em itálico + nome popular entre parênteses)
- **Formato:** 
  ```
  Ordem Família Espécie (Nome Comum)
  ```
- **Exemplo:**
  ```
  Didelphimorphia Didelphidae Didelphis aurita (Gambá-de-orelha-branca)
  ```
- **Fonte:** Arial 12pt
- **Nome Científico:** Itálico
- **Nome Popular:** Cursivo normal (não-itálico, entre parênteses)

### 3.2 Legendas e Rótulos
- **Legenda:** Posicionada abaixo do eixo X (usar `place_legend_below_x_axis()`)
- **Altura de legenda:** 2–3 linhas (ajustar spacing se necessário)
- **Fonte legenda:** Arial 11pt
- **Cor texto:** Preto (#000000)

### 3.3 Eixos
- **Eixo X (métricas):** 
  - Intervalo: 0 a Max(abundância relativa %)
  - Rótulo: "Abundância Relativa (%)" / "Abundância Total (N)"
  - Fonte: Arial 11pt
- **Eixo Y (espécies):**
  - Sem rótulo adicional (nomes de espécies são suficientes)
  - Fonte: Arial 12pt

### 3.4 Título
- **Presença:** ❌ PROIBIDO
- **Justificativa:** Padrão Ouro `enforce_no_chart_title = true`
- **Alternativa:** Título figura é fornecido via contexto (título em nível de relatório, não de gráfico)

---

## 4. Cores e Estilos

### 4.1 Cores (Referência Tema Ouro)
- **Espinha/Eixos:** Preto (#000000), 1.2pt
- **Grade (Y):** Cinza claro (#E8E8E8), visível apenas no eixo Y
- **Grade (X):** Desativada (não exibir)
- **Barras Primárias (%):** Azul padrão do tema (#1F77B4)
- **Barras Secundárias (N):** Laranja padrão do tema (#FF7F0E)
- **Fundo:** Branco (#FFFFFF)

### 4.2 Espessuras
- **Borda das barras:** 0.8pt
- **Espinha (eixos):** 1.2pt
- **Grade Y:** 0.5pt (se ativa)

---

## 5. Estrutura de Dados de Entrada

```python
# DataFrame esperado (por área/empreendimento):
# Colunas: ['nome_cientifico', 'nome_popular', 'contagem', 'ordem', 'familia', ...]
# Linhas: Uma por espécie
# Ordem: Decrescente por contagem (espécies mais abundantes em cima)

# Exemplo (PCH Dores de Guanhães):
#                              nome_cientifico               nome_popular  contagem  ordem
# 0  Callicebus personatus personatus  Sauí-de-cara-branca           3     Primates
# 1    Leopardus tigrinus              Gato-do-mato-pequeno           1     Carnivora
```

---

## 6. Fluxo de Processamento (Implementação)

```python
def _save_abundance_figures(df_area: pd.DataFrame, theme: dict, output_png: Path, area_name: str):
    """
    Gera figura de abundância (Block 6.1 Standard).
    
    Args:
        df_area: DataFrame com colunas [nome_cientifico, nome_popular, contagem]
        theme: Dicionário de tema (tema_gold_approved.json)
        output_png: Caminho de saída para PNG
        area_name: Nome da área (ex: "PCH Dores de Guanhães" ou "Área Controle")
    """
    # 1. Agregar e ordenar
    grouped = df_area.groupby("nome_cientifico", as_index=False)["contagem"].sum()
    grouped = grouped.sort_values("contagem", ascending=False).reset_index(drop=True)
    grouped["abund_relativa_pct"] = grouped["contagem"] / grouped["contagem"].sum() * 100
    
    # 2. Preparar figura
    fig, ax = plt.subplots(figsize=(height, width), dpi=600)
    
    y_pos = np.arange(len(grouped))
    width_rel = 0.35
    width_abs = 0.15
    offset_y = 0.2
    
    # 3. Barra relativa (%)
    ax.barh(y_pos - offset_y/2, grouped["abund_relativa_pct"], 
            width=width_rel, label="Abundância relativa (%)", 
            color=theme["primary_color"], edgecolor="black", linewidth=0.8)
    
    # 4. Barra total (N)
    ax.barh(y_pos + offset_y/2, grouped["contagem"], 
            width=width_abs, label="Abundância total (N)", 
            color=theme["secondary_color"], edgecolor="black", linewidth=0.8, alpha=0.7)
    
    # 5. Anotações
    for i, row in grouped.iterrows():
        # Percentual
        ax.text(row["abund_relativa_pct"] + 0.5, i - offset_y/2, 
                f"{row['abund_relativa_pct']:.1f}%", 
                va="center", ha="left", fontsize=11, fontweight="normal")
        # Contagem
        ax.text(row["contagem"] + 0.1, i + offset_y/2, 
                f"{int(row['contagem'])}", 
                va="center", ha="left", fontsize=10, style="italic")
    
    # 6. Eixo Y: Nomes científico + popular
    labels_y = [f"{row['ordem']} {row['familia']} {row['nome_cientifico']} ({row['nome_popular']})" 
                for _, row in grouped.iterrows()]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels_y, fontsize=12)
    # (Aplicar itálico ao nome científico via HTML ou loop post-set)
    
    # 7. Configuração de eixos e estilos
    ax.set_xlabel("Abundância", fontsize=11)
    ax.set_xlim(0, grouped["abund_relativa_pct"].max() * 1.15)
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)
    
    # 8. Legenda (abaixo do eixo X)
    place_legend_below_x_axis(ax, fig)
    
    # 9. Validação
    validate_axes_style(ax, theme)
    
    # 10. Salvar
    plt.tight_layout()
    plt.savefig(output_png, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close()
```

---

## 7. Exemplos Aprovados

**Arquivo de Referência (Aprovado 2026-05-13 17:39:06Z):**
- PCH Dores de Guanhães: `6_1_figura_abundancia_total_relativa_mastofauna_pch_dgn.png`
- Área Controle: `6_1_figura_abundancia_mastofauna_area_controle.png`

**Localização:**
```
G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\
  Resultados e análises\28_campanha-Abril_26\Mastofauna\PCH Dores de Guanhães\
  [Figuras aprovadas]
```

**Metadata de Execução:**
```
outputs\_project_scripts\project_165\mastofauna\
  20260513T173906Z_execution_metadata.json
  20260513T173906Z_run_this_analysis.py (reproducer)
```

---

## 8. Checklist de Validação

Antes de aprovar nova figura Block 6.1, verificar:

- [ ] **Tipo:** Barras horizontais (barh)
- [ ] **Séries:** Exatamente 2 (% + N), lado-a-lado com offset
- [ ] **Espaçamento:** offset_y = 0.2, width_rel = 0.35, width_abs = 0.15
- [ ] **Cores:** Primária e secundária do tema
- [ ] **Título:** Ausente (enforce_no_chart_title = true)
- [ ] **Anotações:** Percentual (1 casa decimal), Contagem (inteiro)
- [ ] **Tipografia:** PT-BR, nomes científicos itálicos, nomes populares em parênteses
- [ ] **Legenda:** Abaixo do eixo X, 2–3 linhas máximo
- [ ] **Validação:** `validate_axes_style(ax, theme)` retorna ✅
- [ ] **Resolução:** DPI = 600
- [ ] **Formato:** PNG, fundo branco

---

## 9. Histórico de Versões

| Versão | Data | Alterações | Status |
|--------|------|-----------|--------|
| 1.0 | 2026-05-13 17:01:43Z | Barras verticais, título, métrica única | ❌ Rejeitado (título + confuso) |
| 2.0 | 2026-05-13 17:30:04Z | Barras horizontais, removido título, métrica dupla | ⚠️ Parcial (barras sobrepostas) |
| 3.0 | 2026-05-13 17:39:06Z | Barras offset, PT-BR, tipografia refinada | ✅ **APROVADO** |

---

## 10. Notas Futuras

- Aplicar padrão equivalente a Blocks 6.2–6.8 conforme iteração qualitativa
- Primatas (subset de mastofauna) seguirá este padrão com filtro `ordem='Primates'`
- Revisar anualmente ou após atualização de Padrão Ouro
- Documentar desvios justificados em seção "Exceções"

---

**Assinado Digitalmente:** ✅ Padrão Registrado  
**Data de Registro:** 2026-05-13  
**Próxima Revisão:** 2027-05-13 (anual)
