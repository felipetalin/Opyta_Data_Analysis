from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


OUTPUT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Colíder\Resultados"
    r"\2026\Junho-2026\BIOCOL001_RESULTADOS_ICTIOFAUNA_FINAL_R02"
    r"\05_02_5_figura_52_status_identificacao_taxonomica.png"
)

CATEGORIES = [
    ("Identificação definitiva em nível específico", 176, "#2E6EA6"),
    ("Identificação específica duvidosa (cf., aff. ou gr.)", 74, "#D4672A"),
    ("Identificação em nível de gênero ou morfótipo", 71, "#6BA547"),
    ("Potencialmente nova para a ciência", 1, "#7B4EA3"),
]

TOTAL = sum(value for _, value, _ in CATEGORIES)


def percentage(value: int) -> float:
    return 100 * value / TOTAL


def main() -> None:
    assert TOTAL == 322
    assert [round(percentage(value), 1) for _, value, _ in CATEGORIES] == [54.7, 23.0, 22.0, 0.3]

    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 17,
            "legend.fontsize": 20,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(18, 10.2), dpi=300)
    labels = [label for label, _, _ in CATEGORIES]
    values = [value for _, value, _ in CATEGORIES]
    colors = [color for _, _, color in CATEGORIES]

    wedges, _ = ax.pie(
        values,
        startangle=90,
        counterclock=False,
        colors=colors,
        radius=1.0,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.4},
    )

    ax.text(
        0,
        0.07,
        f"{TOTAL}",
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color="#1F1F1F",
    )
    ax.text(
        0,
        -0.12,
        "espécies",
        ha="center",
        va="center",
        fontsize=17,
        color="#595959",
    )

    legend_labels = []
    for label, value, _ in CATEGORIES:
        unit = "espécie" if value == 1 else "espécies"
        legend_labels.append(
            f"{label}\n{value} {unit} ({percentage(value):.1f}%)".replace(".", ",")
        )
    ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(1.00, 0.5),
        frameon=False,
        fontsize=20,
        handlelength=1.65,
        handletextpad=0.7,
        labelspacing=1.15,
    )
    ax.set_aspect("equal")
    ax.set_position([0.045, 0.075, 0.56, 0.85])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=300, facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
