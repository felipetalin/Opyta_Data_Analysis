"""
Protótipos visuais — Fig. 08 Shannon/Pielou (Porto Estrela)
3 níveis: A (refino científico), B (dashboard editorial), C (web/HTML interativo)
Dados sintéticos plausíveis (não usar para análise real).
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle

OUT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Porto Estrela\Planilha\Resultados\_prototipos_design")
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(7)
anos = np.arange(2005, 2026)
n = len(anos)

# Série sintética: montante mais estável, jusante declina após ~2012
shannon_mont = 2.6 + 0.05 * np.sin(anos/2) + rng.normal(0, 0.08, n)
shannon_jus  = 2.55 + 0.04*np.sin(anos/2) - 0.025*np.clip(anos-2012, 0, None) + rng.normal(0, 0.09, n)
pielou_mont  = 0.82 + 0.02*np.sin(anos/3) + rng.normal(0, 0.015, n)
pielou_jus   = 0.80 + 0.02*np.sin(anos/3) - 0.006*np.clip(anos-2012, 0, None) + rng.normal(0, 0.02, n)

# IC bootstrap-like (apenas para visual)
def banda(y, sd=0.08):
    return y - sd, y + sd

# -------- PALETA --------
C_MONT = "#468FAF"
C_JUS  = "#1E6091"
C_HL   = "#E07A5F"
C_GRID = "#E8ECEF"
C_TXT  = "#2B2D42"
C_TXT2 = "#6C757D"

# =========================================================
# NÍVEL A — Refino científico
# =========================================================
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": C_TXT2,
    "axes.labelcolor": C_TXT,
    "xtick.color": C_TXT2, "ytick.color": C_TXT2,
    "axes.spines.top": False, "axes.spines.right": False,
})

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharex=True)
for ax, (yM, yJ, ylab, ylim) in zip(
    axes,
    [(shannon_mont, shannon_jus, "Shannon (H′)", (2.0, 2.9)),
     (pielou_mont,  pielou_jus,  "Pielou (J′)",  (0.70, 0.92))]
):
    ax.plot(anos, yM, "-o", color=C_MONT, lw=2, ms=4, label="Montante")
    ax.plot(anos, yJ, "-o", color=C_JUS,  lw=2, ms=4, label="Jusante")
    ax.set_ylabel(ylab); ax.set_ylim(ylim)
    ax.grid(axis="y", color=C_GRID, lw=1)
    ax.set_axisbelow(True)
    # rótulo direto no fim da linha
    ax.annotate("Montante", xy=(anos[-1], yM[-1]), xytext=(5,0),
                textcoords="offset points", color=C_MONT, fontsize=9, va="center", weight="bold")
    ax.annotate("Jusante", xy=(anos[-1], yJ[-1]), xytext=(5,0),
                textcoords="offset points", color=C_JUS, fontsize=9, va="center", weight="bold")

fig.suptitle("Jusante perde diversidade após 2012; equitabilidade segue tendência semelhante",
             fontsize=13, weight="bold", color=C_TXT, x=0.07, ha="left", y=0.98)
fig.text(0.07, 0.92, "Índices Shannon (H′) e Pielou (J′) por ano hidrológico — Porto Estrela",
         fontsize=10, color=C_TXT2)
fig.text(0.07, 0.02, "Fonte: monitoramento Bios | n = 21 anos | dados sintéticos para protótipo",
         fontsize=8, color=C_TXT2, style="italic")
plt.tight_layout(rect=[0, 0.04, 1, 0.90])
plt.savefig(OUT/"NIVEL_A_refino_cientifico.png", dpi=170, facecolor="white"); plt.close()

# =========================================================
# NÍVEL B — Dashboard editorial
# =========================================================
fig = plt.figure(figsize=(13, 7.0), facecolor="white")
gs = fig.add_gridspec(3, 6, height_ratios=[0.18, 0.20, 1], hspace=0.35, wspace=0.6)

# Linha 1: título (span 6 cols)
ax_t = fig.add_subplot(gs[0, :]); ax_t.axis("off")
ax_t.text(0.0, 0.55, "Diversidade da ictiofauna — Porto Estrela",
          fontsize=18, weight="bold", color=C_TXT)
ax_t.text(0.0, 0.05, "Jusante mostra declínio sustentado de H′ pós-2012 (−12%); montante estável",
          fontsize=11, color=C_TXT2)

# Linha 2: KPIs em 3 grupos de 2 cols
for k_idx, (lab, val, col) in enumerate(
    [("H′ médio (Mont.)", "2.62", C_MONT),
     ("H′ médio (Jus.)",  "2.31", C_JUS),
     ("Δ H′ pós-2012",    "−0.31", C_HL)]):
    ax_k = fig.add_subplot(gs[1, k_idx*2:(k_idx+1)*2]); ax_k.axis("off")
    ax_k.text(0.0, 0.70, val, fontsize=24, weight="bold", color=col, ha="left")
    ax_k.text(0.0, 0.15, lab, fontsize=9.5, color=C_TXT2, ha="left")

# Painéis (linha 2 do grid B)
for col, (yM, yJ, ylab, ylim) in enumerate([
    (shannon_mont, shannon_jus, "Shannon (H′)", (2.0, 2.9)),
    (pielou_mont,  pielou_jus,  "Pielou (J′)",  (0.70, 0.92))
]):
    ax = fig.add_subplot(gs[2, col*3:(col+1)*3])
    # banda de evento (enchimento UHE hipotético 2010-2012)
    ax.axvspan(2010, 2012, color=C_HL, alpha=0.10, zorder=0)
    ax.text(2011, ylim[1]*0.995, "Enchimento UHE", fontsize=8,
            color=C_HL, ha="center", va="top", style="italic")
    # bandas de incerteza
    lo, hi = banda(yM, 0.08); ax.fill_between(anos, lo, hi, color=C_MONT, alpha=0.15, lw=0)
    lo, hi = banda(yJ, 0.08); ax.fill_between(anos, lo, hi, color=C_JUS,  alpha=0.15, lw=0)
    ax.plot(anos, yM, "-", color=C_MONT, lw=2.2)
    ax.plot(anos, yJ, "-", color=C_JUS,  lw=2.2)
    ax.scatter(anos, yM, color=C_MONT, s=20, zorder=3, edgecolor="white", lw=0.8)
    ax.scatter(anos, yJ, color=C_JUS,  s=20, zorder=3, edgecolor="white", lw=0.8)

    ax.set_ylim(ylim); ax.set_title(ylab, loc="left", fontsize=11, weight="bold", color=C_TXT, pad=8)
    ax.grid(axis="y", color=C_GRID, lw=1); ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors=C_TXT2)

    ax.annotate("Montante", xy=(anos[-1], yM[-1]), xytext=(6,0), textcoords="offset points",
                color=C_MONT, fontsize=9, weight="bold", va="center")
    ax.annotate("Jusante",  xy=(anos[-1], yJ[-1]), xytext=(6,0), textcoords="offset points",
                color=C_JUS,  fontsize=9, weight="bold", va="center")

fig.text(0.01, 0.012, "Bandas = IC95% bootstrap | Faixa salmão = enchimento do reservatório | "
         "Fonte: monitoramento Bios | dados sintéticos para protótipo",
         fontsize=8, color=C_TXT2, style="italic")
plt.savefig(OUT/"NIVEL_B_dashboard_editorial.png", dpi=170,
            bbox_inches="tight", facecolor="white"); plt.close()

# =========================================================
# NÍVEL C — Web-first (mockup estático imitando UI dark/interactive)
# =========================================================
BG = "#0F172A"; CARD = "#1E293B"; TXT_W = "#F8FAFC"; TXT_M = "#94A3B8"
C_MONT2 = "#38BDF8"; C_JUS2 = "#FBBF24"; C_HL2 = "#F87171"

fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
gs = fig.add_gridspec(2, 3, height_ratios=[0.22, 1], hspace=0.20, wspace=0.22)

# header
ax_h = fig.add_subplot(gs[0, :]); ax_h.axis("off"); ax_h.set_facecolor(BG)
ax_h.text(0.005, 0.78, "● OPYTA · Porto Estrela — Diversidade",
          fontsize=14, weight="bold", color=TXT_W)
ax_h.text(0.005, 0.40, "Comparativo temporal H′ / J′  ·  Montante vs Jusante",
          fontsize=10, color=TXT_M)
# pseudo-toggle
for i, (lab, on) in enumerate([("H′", True), ("J′", True), ("CPUEn", False), ("CPUEb", False)]):
    x = 0.55 + i*0.10
    ax_h.add_patch(Rectangle((x, 0.45), 0.08, 0.35,
                             facecolor=C_MONT2 if on else "#334155",
                             edgecolor="none", transform=ax_h.transAxes))
    ax_h.text(x+0.04, 0.62, lab, color=TXT_W if on else TXT_M,
              fontsize=9, ha="center", va="center", weight="bold",
              transform=ax_h.transAxes)

# painéis (card style)
for col, (yM, yJ, ylab, ylim) in enumerate([
    (shannon_mont, shannon_jus, "Shannon (H′)", (2.0, 2.9)),
    (pielou_mont,  pielou_jus,  "Pielou (J′)",  (0.70, 0.92))
]):
    ax = fig.add_subplot(gs[1, col])
    ax.set_facecolor(CARD)
    ax.axvspan(2010, 2012, color=C_HL2, alpha=0.12, zorder=0)
    lo, hi = banda(yM, 0.08); ax.fill_between(anos, lo, hi, color=C_MONT2, alpha=0.18, lw=0)
    lo, hi = banda(yJ, 0.08); ax.fill_between(anos, lo, hi, color=C_JUS2,  alpha=0.18, lw=0)
    ax.plot(anos, yM, "-o", color=C_MONT2, lw=2, ms=4, mec=CARD, mew=0.8)
    ax.plot(anos, yJ, "-o", color=C_JUS2,  lw=2, ms=4, mec=CARD, mew=0.8)
    ax.set_ylim(ylim)
    ax.set_title(ylab, loc="left", fontsize=11, weight="bold", color=TXT_W, pad=8)
    for s in ax.spines.values(): s.set_visible(False)
    ax.grid(axis="y", color="#334155", lw=0.8); ax.set_axisbelow(True)
    ax.tick_params(colors=TXT_M)
    # tooltip mock
    ix = 16  # destaca ano 2021
    ax.scatter([anos[ix]], [yJ[ix]], s=120, color=C_HL2, zorder=5, alpha=0.4)
    ax.scatter([anos[ix]], [yJ[ix]], s=40, color=C_HL2, zorder=6)
    ax.annotate(f"  {anos[ix]}\n  {ylab.split()[0]} = {yJ[ix]:.2f}\n  IC95% ±0.08\n  n=12 amostras",
                xy=(anos[ix], yJ[ix]), xytext=(15, -50),
                textcoords="offset points",
                fontsize=8, color=TXT_W,
                bbox=dict(boxstyle="round,pad=0.5", fc="#0B1220", ec=C_HL2, lw=1),
                arrowprops=dict(arrowstyle="-", color=C_HL2, lw=0.8))

# painel lateral — sparkline + KPIs
ax_s = fig.add_subplot(gs[1, 2]); ax_s.set_facecolor(CARD); ax_s.axis("off")
ax_s.text(0.05, 0.92, "Resumo", fontsize=11, weight="bold", color=TXT_W, transform=ax_s.transAxes)
items = [("H′ Mont.", f"{shannon_mont.mean():.2f}", C_MONT2),
         ("H′ Jus.",  f"{shannon_jus.mean():.2f}",  C_JUS2),
         ("Δ pós-2012", "−0.31", C_HL2),
         ("J′ Mont.", f"{pielou_mont.mean():.2f}", C_MONT2),
         ("J′ Jus.",  f"{pielou_jus.mean():.2f}",  C_JUS2)]
for i, (lab, val, c) in enumerate(items):
    y = 0.78 - i*0.14
    ax_s.text(0.05, y,   lab, fontsize=9, color=TXT_M, transform=ax_s.transAxes)
    ax_s.text(0.05, y-0.05, val, fontsize=16, weight="bold", color=c, transform=ax_s.transAxes)

fig.text(0.01, 0.012, "Protótipo de UI interativa (Plotly/Altair) · Dados sintéticos",
         fontsize=8, color=TXT_M, style="italic")
plt.savefig(OUT/"NIVEL_C_web_first.png", dpi=170, facecolor=BG, bbox_inches="tight"); plt.close()

print("OK")
print(OUT)
