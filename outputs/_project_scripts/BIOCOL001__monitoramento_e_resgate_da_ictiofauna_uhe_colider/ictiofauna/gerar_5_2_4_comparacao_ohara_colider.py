from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


OUTPUT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Colíder\Resultados"
    r"\2026\Junho-2026\BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02"
    r"\05_02_4_figura_51_comparacao_ohara_colider.png"
)

BOOK_TOTAL = 342
BOOK_GENERA = 191
BOOK_FAMILIES = 42
BOOK_ORDERS = 11
COLIDER_TOTAL = 322
COLIDER_ONLY = 90
SHARED = COLIDER_TOTAL - COLIDER_ONLY
BOOK_ONLY = BOOK_TOTAL - SHARED
SHARED_PERCENT_COLIDER = 100 * SHARED / COLIDER_TOTAL

BLUE_BOOK = "#5B9BD5"
BLUE_COLIDER = "#8CC4E8"
BLUE_DARK = "#1F4E79"
TEXT = "#1F1F1F"
GRAY = "#595959"


def add_region_label(
    ax,
    x: float,
    heading: str,
    value: int,
    detail: str | None = None,
) -> None:
    ax.text(
        x,
        5.12,
        heading,
        ha="center",
        va="center",
        fontsize=18,
        color=TEXT,
        linespacing=1.15,
    )
    ax.text(
        x,
        4.08,
        f"{value}",
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )
    if detail:
        ax.text(
            x,
            3.34,
            detail,
            ha="center",
            va="center",
            fontsize=14,
            color=GRAY,
        )


def main() -> None:
    assert SHARED == 232
    assert BOOK_ONLY == 110
    assert COLIDER_ONLY + SHARED == COLIDER_TOTAL
    assert BOOK_ONLY + SHARED == BOOK_TOTAL

    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 17,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(18, 10.2), dpi=300)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10.2)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    left = Ellipse(
        (6.60, 4.75),
        width=8.00,
        height=5.25,
        facecolor=BLUE_BOOK,
        edgecolor=BLUE_DARK,
        linewidth=3.0,
        alpha=0.76,
    )
    right = Ellipse(
        (11.40, 4.75),
        width=8.00,
        height=5.25,
        facecolor=BLUE_COLIDER,
        edgecolor=BLUE_DARK,
        linewidth=3.0,
        alpha=0.76,
    )
    ax.add_patch(left)
    ax.add_patch(right)

    ax.text(
        4.65,
        8.82,
        "Lista regional do rio Teles Pires",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=BLUE_DARK,
    )
    ax.text(
        13.35,
        8.82,
        "Monitoramento da UHE Colíder",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=BLUE_DARK,
    )
    ax.text(
        4.65,
        8.27,
        "Ohara et al. (2017)",
        ha="center",
        va="center",
        fontsize=16,
        color=GRAY,
    )
    ax.text(
        13.35,
        8.27,
        "69 campanhas",
        ha="center",
        va="center",
        fontsize=16,
        color=GRAY,
    )
    ax.text(
        4.65,
        7.74,
        f"{BOOK_TOTAL} espécies | {BOOK_GENERA} gêneros | {BOOK_FAMILIES} famílias | {BOOK_ORDERS} ordens",
        ha="center",
        va="center",
        fontsize=14,
        color=GRAY,
    )
    ax.text(13.35, 7.74, f"{COLIDER_TOTAL} espécies", ha="center", va="center", fontsize=14, color=GRAY)

    add_region_label(ax, 4.45, "Riqueza exclusiva\nda lista regional", BOOK_ONLY)
    add_region_label(
        ax,
        9.00,
        "Riqueza\ncompartilhada",
        SHARED,
        f"{SHARED_PERCENT_COLIDER:.1f}% da riqueza monitorada".replace(".", ","),
    )
    add_region_label(ax, 13.55, "Riqueza exclusiva\ndo monitoramento", COLIDER_ONLY)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(left=0.025, right=0.975, top=0.97, bottom=0.055)
    fig.savefig(OUTPUT, dpi=300, facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
