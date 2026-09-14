from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from revisar_braang01_agua_subterranea_dessedentacao import load_data


OUT_DIR = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados/_revisoes/"
    "R05_todos_os_vmps_20260710/revisado/\u00c1gua_Subterr\u00e2nea"
)

LIMITS_MG_L = {
    "Ars\u00eanio Dissolvido": {
        "Consumo Humano": 0.01,
        "Dessedenta\u00e7\u00e3o": 0.2,
        "Irriga\u00e7\u00e3o": 0.05,
        "Recrea\u00e7\u00e3o": 0.008,
    },
    "Ars\u00eanio Total": {
        "Consumo Humano": 0.01,
        "Dessedenta\u00e7\u00e3o": 0.2,
        "Irriga\u00e7\u00e3o": 0.05,
        "Recrea\u00e7\u00e3o": 0.008,
    },
    "Cobalto Dissolvido": {
        "Dessedenta\u00e7\u00e3o": 1.0,
        "Irriga\u00e7\u00e3o": 0.05,
        "Recrea\u00e7\u00e3o": 0.01,
    },
    "Cobre Dissolvido": {
        "Consumo Humano": 2.0,
        "Dessedenta\u00e7\u00e3o": 0.5,
        "Irriga\u00e7\u00e3o": 0.2,
        "Recrea\u00e7\u00e3o": 1.0,
    },
    "Cromo Dissolvido": {
        "Consumo Humano": 0.05,
        "Dessedenta\u00e7\u00e3o": 1.0,
        "Irriga\u00e7\u00e3o": 0.1,
        "Recrea\u00e7\u00e3o": 0.05,
    },
    "S\u00f3lidos Dissolvidos Totais": {
        "Consumo Humano": 1000.0,
    },
    "Sulfato": {
        "Consumo Humano": 250.0,
        "Dessedenta\u00e7\u00e3o": 1000.0,
        "Irriga\u00e7\u00e3o": 400.0,
        "Recrea\u00e7\u00e3o": 5.0,
    },
    "Zinco Dissolvido": {
        "Consumo Humano": 5.0,
        "Dessedenta\u00e7\u00e3o": 24.0,
        "Irriga\u00e7\u00e3o": 2.0,
        "Recrea\u00e7\u00e3o": 5.0,
    },
}

USE_LABELS = {
    "Consumo Humano": "Cons. humano",
    "Dessedenta\u00e7\u00e3o": "Dessed.",
    "Irriga\u00e7\u00e3o": "Irrig.",
    "Recrea\u00e7\u00e3o": "Recrea\u00e7\u00e3o",
}


def build_rows() -> list[list[str]]:
    df = load_data()
    df = df[df["nome_parametro"].isin(LIMITS_MG_L)].copy()
    rows: list[list[str]] = []
    for (param, point), group in df.groupby(["nome_parametro", "nome_ponto"], sort=True):
        uses = []
        max_value = pd.to_numeric(group["valor_medido"], errors="coerce").max()
        for use, limit in LIMITS_MG_L[str(param)].items():
            values = pd.to_numeric(group["valor_medido"], errors="coerce")
            if bool((values > limit).any()):
                uses.append(USE_LABELS[use])
        if uses:
            rows.append([str(param), str(point), "; ".join(uses), f"{float(max_value):g}"])
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    rows.sort(key=lambda row: (row[0], row[1]))

    if not rows:
        rows = [["Sem viola\u00e7\u00f5es", "-", "-", "-"]]

    fig_height = max(6.0, 1.0 + 0.42 * len(rows))
    fig, ax = plt.subplots(figsize=(18, fig_height))
    ax.axis("off")

    columns = ["Par\u00e2metro", "Ponto", "Uso(s) violado(s)", "M\u00e1x. medido\n(mg/L)"]
    table = ax.table(
        cellText=rows,
        colLabels=columns,
        bbox=[0.015, 0.10, 0.97, 0.78],
        cellLoc="center",
        colLoc="center",
        colWidths=[0.32, 0.13, 0.43, 0.12],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11.5 if len(rows) > 18 else 13.5)

    header_color = "#8B1E1E"
    band_color = "#F8F1F1"
    edge_color = "#B8A4A4"
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(edge_color)
        cell.set_linewidth(1.0)
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold")
            cell.set_height(cell.get_height() * 1.2)
        else:
            cell.set_facecolor(band_color if row % 2 == 0 else "white")
            if col in {0, 2}:
                cell.set_text_props(ha="left")
            if col == 0:
                cell.set_text_props(weight="bold", ha="left")

    fig.suptitle(
        "Viola\u00e7\u00f5es por par\u00e2metro, ponto e uso - \u00c1gua Subterr\u00e2nea",
        fontsize=24,
        fontweight="bold",
        y=0.965,
    )
    fig.text(
        0.5,
        0.035,
        "Cen\u00e1rio comparativo com VMPs da Resolu\u00e7\u00e3o CONAMA 396/2008; viola\u00e7\u00e3o quando o valor medido excede o limite do uso.",
        ha="center",
        fontsize=12,
        color="#333333",
    )
    fig.text(
        0.5,
        0.012,
        "Abrevia\u00e7\u00f5es: Cons. humano = Consumo Humano; Dessed. = Dessedenta\u00e7\u00e3o; Irrig. = Irriga\u00e7\u00e3o.",
        ha="center",
        fontsize=10.5,
        color="#555555",
    )

    png = OUT_DIR / "Tabela_Violacoes_VMPs_CONAMA396_Agua_Subterranea_R05.png"
    csv = OUT_DIR / "Tabela_Violacoes_VMPs_CONAMA396_Agua_Subterranea_R05.csv"
    fig.savefig(png, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    pd.DataFrame(rows, columns=["Parametro", "Ponto", "Usos_violados", "Max_medido_mg_L"]).to_csv(
        csv,
        index=False,
        encoding="utf-8-sig",
    )
    print(json.dumps({"png": str(png), "csv": str(csv), "rows": len(rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
