# Padrão Block 6.4: Dendrograma de Similaridade (Mastofauna)

**Aprovado em:** 2026-05-13  
**Versão:** 2.0 (Melhorada com Pontos Amostrais Individuais)  
**Responsável:** Padrão Ouro - Análise Multivariada  
**Status:** ✅ REGISTRADO E OPERACIONAL

---

## 1. Identificação do Bloco

- **Código:** 6.4
- **Título:** Similaridade de Jaccard (Mastofauna)
- **Métrica Principal:** Dendrograma hierárquico baseado em distância de Jaccard
- **Nível de Análise:** **Pontos Amostrais Individuais** (não empreendimentos agregados)
- **Público-alvo:** Comparação estrutural entre todos os pontos de amostragem

---

## 2. Especificação de Figuras

### 2.1 Tipo de Figura
- **Tipo:** Dendrograma hierárquico (hierarchical clustering)
- **Métrica de Distância:** Jaccard (1 - similaridade)
- **Método de Linkage:** Average-linkage (UPGMA)
- **Orientação:** Horizontal (eixo X = similaridade, eixo Y = pontos)
- **Estrutura:** Todos os pontos amostrais como folhas do dendrograma

### 2.2 Dimensões
| Parâmetro | Valor | Notas |
|-----------|-------|-------|
| Resolução (DPI) | 600 | Padrão Ouro |
| Fundo | Branco (#FFFFFF) | Padrão Ouro |
| Altura da figura | Dinâmica (4 + N_pontos × 0.4 pol.) | Mín. 8, máx. 16 pol. |
| Largura da figura | 12 pol. | Fixo para eixo X consistente |
| Formato | PNG | Padrão Ouro |

### 2.3 Eixos

#### Eixo X (Similaridade de Jaccard)
- **Label:** "Similaridade de Jaccard (%)"
- **Intervalo:** 0–100%
- **Direção:** Invertida (100% à esquerda, 0% à direita) para legibilidade
- **Ticks:** A cada 10% (0, 10, 20, ..., 100)
- **Posição:** Topo (xaxis_tick_top)
- **Cor:** Preto, 1.2pt

#### Eixo Y (Pontos Amostrais)
- **Label:** "Pontos Amostrais"
- **Rótulos:** Códigos de ponto + identificação de área (cor)
- **Cor dos rótulos:** 
  - **Azul** (#1F77B4) para PCH Dores de Guanhães
  - **Laranja** (#FF7F0E) para Área Controle
- **Fontweight:** Bold (negrito para leitura fácil)
- **Fontsize:** 10–11pt

---

## 3. Dados e Processamento

### 3.1 Matriz de Presença/Ausência
```python
# Para cada ponto amostral (linha):
# Colunas = todas as espécies (0 ou 1)
# Rows = N pontos amostrais

pa_matrix = np.array([
    [1, 0, 1, 0, ...],  # CO2
    [1, 1, 0, 0, ...],  # CON1
    [0, 1, 1, 1, ...],  # CON2
    # ... (11 pontos no total)
])
```

### 3.2 Cálculo de Distância
- **Métrica:** `pdist(pa_matrix, metric='jaccard')`
- **Resultado:** Vetor de distâncias condenso (55 valores para 11 pontos)
- **Interpretação:** Distância = 1 - Similaridade de Jaccard

### 3.3 Clustering Hierárquico
- **Linkage:** `linkage(dist, method='average')`
- **Saída:** Matriz Z com estrutura de agrupamento
- **Dendrograma:** `dendrogram(Z, orientation='right', labels=pontos_unicos)`

---

## 4. Tipografia e Cores

### 4.1 Rótulos de Pontos
- **Formato:** Código do ponto (ex: "DGN1", "CON2")
- **Cor:**
  - PCH Dores de Guanhães: Azul (#1F77B4), **Bold**
  - Área Controle: Laranja (#FF7F0E), **Bold**
- **Fontsize:** 10pt
- **Exemplo visual no gráfico:**
  ```
  DGN1  ← Azul (PCH)
  CON2  ← Laranja (Controle)
  ```

### 4.2 Legenda de Cores
- **Tipo:** Texto informativo (não ax.legend())
- **Posição:** Canto superior esquerdo (transform=ax.transAxes, x=0.02, y=0.98)
- **Formato:**
  ```
  ■ Dores de Guanhaes  [azul]
  ■ Area Controle      [laranja]
  ```
- **Fundo:** Caixa branca semitransparente (alpha=0.8)
- **Fontsize:** 9pt, negrito

### 4.3 Eixo X (Similaridade)
- **Rótulos:** "0", "10", "20", ..., "100"
- **Fontsize:** 10pt
- **Cor:** Preto

---

## 5. Estrutura de Linhas do Dendrograma

### 5.1 Linhas de Agrupamento
- **Cor:** Padrão (Matplotlib: azul/preto)
- **Largura:** 0.8–1.0pt
- **Estilo:** Sólido

### 5.2 Interpretação de Agrupamentos
- **Pontos próximos horizontalmente**: Comunidades similares (alta similaridade Jaccard)
- **Pontos distantes**: Comunidades divergentes (baixa similaridade)
- **Agrupamentos em nível alto**: Diferença estrutural significativa entre áreas

**Exemplo esperado:**
```
DGN1 (PCH) ─┐
            ├─ ~50% similaridade ─ CON2 (Controle)
CO2, CON1 ──┤                     [1 espécie em comum]
DG7 ────────┤
            └─ Agrupamento Controle (pluriespecífico)
```

---

## 6. Fluxo de Processamento (Implementação)

```python
def _save_similarity_and_venn(df_pch: pd.DataFrame, df_control: pd.DataFrame, 
                              theme: dict, output_dir: Path, generated_files: list[str]) -> None:
    """
    Gera dendrograma com todos os pontos amostrais (Block 6.4 v2.0).
    """
    # 1. Concatenar dados
    df_all = pd.concat([
        df_pch.assign(area=TARGET_PCH_NAME),
        df_control.assign(area=TARGET_CONTROL_NAME)
    ], ignore_index=True)
    
    # 2. Extrair pontos e espécies únicas
    pontos_unicos = sorted(df_all["nome_ponto"].dropna().unique().tolist())
    todas_especies = sorted(union)  # union de PCH e Controle
    
    # 3. Criar matriz PA por ponto
    pa_points = []
    ponto_area_map = {}
    
    for ponto in pontos_unicos:
        df_ponto = df_all[df_all["nome_ponto"] == ponto]
        area = df_ponto["area"].iloc[0]
        ponto_area_map[ponto] = area
        
        presence = [1 if spp in set(df_ponto["nome_cientifico"].dropna().tolist()) 
                    else 0 for spp in todas_especies]
        pa_points.append(presence)
    
    # 4. Calcular distâncias e linkage
    pa_mat = np.array(pa_points, dtype=float)
    dist_points = pdist(pa_mat, metric="jaccard")
    z_points = linkage(dist_points, method="average")
    
    # 5. Criar figura
    n_pts = len(pontos_unicos)
    fig_height = min(max(4 + n_pts * 0.4, 8), 16)
    fig, ax = plt.subplots(figsize=(12, fig_height), dpi=600)
    
    # 6. Dendrograma
    dendro = dendrogram(z_points, labels=pontos_unicos, orientation="right", 
                        ax=ax, color_threshold=None)
    
    # 7. Colorir rótulos
    color_pch = theme.get("primary_hex", "#1f77b4")
    color_ctrl = theme.get("secondary_hex", "#ff7f0e")
    
    for i, label in enumerate(ax.get_yticklabels()):
        ponto_label = label.get_text()
        if ponto_label in ponto_area_map:
            color = color_pch if ponto_area_map[ponto_label] == TARGET_PCH_NAME else color_ctrl
            label.set_color(color)
            label.set_fontweight("bold")
    
    # 8. Configurar eixos
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlim(1.0, 0.0)
    
    ticks_sim = np.arange(0, 101, 10)
    ticks_dist = 1 - (ticks_sim / 100.0)
    ax.set_xticks(ticks_dist)
    ax.set_xticklabels([str(t) for t in ticks_sim], fontsize=10)
    
    # 9. Legenda de cores (caixa de texto)
    ax.text(0.02, 0.98, f"■ {TARGET_PCH_NAME}", 
            transform=ax.transAxes, ha="left", va="top", fontsize=9, 
            color=color_pch, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, 
                     edgecolor="none"))
    ax.text(0.02, 0.91, f"■ {TARGET_CONTROL_NAME}", 
            transform=ax.transAxes, ha="left", va="top", fontsize=9, 
            color=color_ctrl, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, 
                     edgecolor="none"))
    
    # 10. Aplicar tema e validar
    apply_theme(ax, theme, xlabel="Similaridade de Jaccard (%)", 
                ylabel="Pontos Amostrais")
    validate_axes_style(ax, theme)
    
    # 11. Salvar
    fig.tight_layout()
    out_dendro_pts = output_dir / "6_4_dendrograma_jaccard_por_pontos.png"
    fig.savefig(out_dendro_pts, dpi=600, bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_dendro_pts))
```

---

## 7. Exemplos Aprovados

**Arquivo de Referência (Aprovado 2026-05-13 17:48:58Z):**
- Local: `6_4_dendrograma_jaccard_por_pontos.png`
- Pontos inclusos: 11 (CO2, CON1, CON2, DG7, DGN1, FO6, FOR1, JA1, JAC1, SP4, SPT1)
- Agrupamentos visíveis: PCH vs Controle com estrutura ecológica clara

**Metadata de Execução:**
```
outputs\_project_scripts\project_165\mastofauna\
  20260513T174858Z_execution_metadata.json
  20260513T174858Z_run_this_analysis.py (reproducer)
```

---

## 8. Checklist de Validação

Antes de aprovar novo dendrograma Block 6.4, verificar:

- [ ] **Pontos amostrais:** TODOS os N pontos presentes no eixo Y
- [ ] **Identificação individual:** Rótulos legíveis, códigos únicos
- [ ] **Coloração:** Azul (PCH), Laranja (Controle), **bold**
- [ ] **Eixo X:** Similaridade de Jaccard (0–100%), intervalo invertido
- [ ] **Método:** Average-linkage, métrica Jaccard
- [ ] **Legenda:** Caixa de texto com cores (não ax.legend())
- [ ] **Título:** Ausente (enforce_no_chart_title = true)
- [ ] **Validação:** `validate_axes_style(ax, theme)` retorna ✅
- [ ] **Resolução:** DPI = 600
- [ ] **Formato:** PNG, fundo branco
- [ ] **Altura dinâmica:** Escalável com número de pontos
- [ ] **Agrupamentos:** Visualmente interpretáveis (estrutura hierárquica clara)

---

## 9. Comparação: Dendrograma por Pontos vs. por Empreendimento

| Aspecto | Por Pontos (v2.0 — Novo) | Por Empreendimento (v1.0) |
|---------|--------------------------|---------------------------|
| **Folhas do dendrograma** | 11 pontos individuais | 2 empreendimentos |
| **Interpretação espacial** | Detalhada (ponto-a-ponto) | Agregada |
| **Agrupamentos ecológicos** | Visíveis entre pontos | Apenas 1 agrupamento |
| **Robustez multivariada** | Alta (mais observações) | Baixa (n=2) |
| **Arquivo de saída** | `6_4_dendrograma_jaccard_por_pontos.png` | `6_4_dendrograma_jaccard_pch_vs_controle.png` |

**Recomendação:** Usar Block 6.4 v2.0 (pontos) como padrão; manter v1.0 (empreendimentos) como referência auxiliar.

---

## 10. Histórico de Versões

| Versão | Data | Alterações | Status |
|--------|------|-----------|--------|
| 1.0 | 2026-05-13 14:22 | Dendrograma 2 empreendimentos (PCH vs Controle agregados) | ⚠️ Limitado |
| 2.0 | 2026-05-13 17:48 | **Dendrograma com 11 pontos amostrais individuais, coloridos, legendado** | ✅ **APROVADO** |

---

## 11. Notas Futuras

- Aplicar padrão equivalente a outras disciplinas (Ictio, Avifauna, etc.)
- Considerar dendrograma por espécies como análise complementar (6.4b)
- Revisar anualmente ou após atualização de Padrão Ouro
- Documentar desvios justificados em seção "Exceções"
- **Usuário feedback**: "Dendrograma agora contempla todos os pontos, apresentando estrutura clara dos agrupamentos ecológicos" ✅

---

**Assinado Digitalmente:** ✅ Padrão Registrado  
**Data de Registro:** 2026-05-13  
**Próxima Revisão:** 2027-05-13 (anual)

