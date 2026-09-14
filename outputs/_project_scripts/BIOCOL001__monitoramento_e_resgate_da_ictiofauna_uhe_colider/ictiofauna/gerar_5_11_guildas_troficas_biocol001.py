from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


OUTPUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Colíder\Resultados\2026\Junho-2026\BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02"
)
OUTPUT_PATH = OUTPUT_DIR / "05_11_figura_guildas_troficas.png"

CATEGORIES = (
    "Piscívoro",
    "Onívoro",
    "Detritívoro",
    "Herbívoro",
    "Insetívoro",
    "Não determinada",
    "Bentívoro*",
)
VALUES = (27, 26, 17, 16, 10, 2, 1)
COLORS = (
    "#2E6EA6",
    "#D4672A",
    "#6BA547",
    "#7B4EA3",
    "#C9A227",
    "#6C757D",
    "#4E9A99",
)


def main() -> None:
    total = sum(VALUES)
    if total != 99:
        raise RuntimeError(f"Total trofico inesperado: {total}; esperado: 99.")
    labels = [
        f"{category} — {value} ({value / total:.1%})".replace(".", ",")
        for category, value in zip(CATEGORIES, VALUES)
    ]

    plt.rcParams.update({"font.family": "Arial", "font.size": 15})
    fig, ax = plt.subplots(figsize=(18, 10.2), dpi=300, facecolor="white")
    wedges, _ = ax.pie(
        VALUES,
        startangle=90,
        colors=COLORS,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.4},
    )
    ax.text(
        0,
        0.04,
        f"{total}",
        ha="center",
        va="center",
        fontsize=27,
        fontweight="bold",
        color="#1F1F1F",
    )
    ax.text(
        0,
        -0.11,
        "espécies",
        ha="center",
        va="center",
        fontsize=15,
        color="#595959",
    )
    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=15,
        labelspacing=1.25,
    )
    ax.set_aspect("equal")
    fig.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"total={total}")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
