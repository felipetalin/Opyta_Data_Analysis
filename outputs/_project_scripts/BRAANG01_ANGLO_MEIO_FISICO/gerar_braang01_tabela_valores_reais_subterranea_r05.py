from __future__ import annotations

import json
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

PARAMS = [
    "Ars\u00eanio Dissolvido",
    "Ars\u00eanio Total",
    "Cobalto Dissolvido",
    "Cobre Dissolvido",
    "Cromo Dissolvido",
    "S\u00f3lidos Dissolvidos Totais",
    "Sulfato",
    "Zinco Dissolvido",
    "pH",
]

POINTS = ["MCB2001", "MCB2002B", "MCB2003", "MCB2008", "MCB2012"]

# VMP principal para o recorte de dessedentacao; STD fica em consumo humano
# porque nao ha VMP de dessedentacao para esse parametro na CONAMA 396/2008.
VMP_LABELS = {
    "Ars\u00eanio Dissolvido": "0,2",
    "Ars\u00eanio Total": "0,2",
    "Cobalto Dissolvido": "1,0",
    "Cobre Dissolvido": "0,5",
    "Cromo Dissolvido": "1,0",
    "S\u00f3lidos Dissolvidos Totais": "1000*",
    "Sulfato": "1000",
    "Zinco Dissolvido": "24",
    "pH": "-",
}


def fmt(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    value = float(value)
    if abs(value) >= 100:
        return f"{value:g}".replace(".", ",")
    if value >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".").replace(".", ",")
    if value >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{value:.3g}".replace(".", ",")


def build_table() -> pd.DataFrame:
    df = load_data()
    df = df[df["nome_parametro"].isin(PARAMS) & df["nome_ponto"].isin(POINTS)].copy()
    df["valor_medido"] = pd.to_numeric(df["valor_medido"], errors="coerce")

    rows = []
    for param in PARAMS:
        row = {"Par\u00e2metro": param, "VMP": VMP_LABELS[param]}
        subset = df[df["nome_parametro"] == param]
        for point in POINTS:
            max_value = subset.loc[subset["nome_ponto"] == point, "valor_medido"].max()
            row[point] = fmt(max_value)
        rows.append(row)
    return pd.DataFrame(rows)


def draw_table(table_df: pd.DataFrame) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(18, 7.4))
    ax.axis("off")
    col_widths = [0.34, 0.10, 0.112, 0.112, 0.112, 0.112, 0.112]
    table = ax.table(
        cellText=table_df.values.tolist(),
        colLabels=list(table_df.columns),
        bbox=[0.015, 0.14, 0.97, 0.72],
        cellLoc="center",
        colLoc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(15)

    header_color = "#2E7D32"
    band_color = "#F3F7F2"
    edge_color = "#A8B6A3"
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(edge_color)
        cell.set_linewidth(1.0)
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold")
            cell.set_height(cell.get_height() * 1.15)
        else:
            cell.set_facecolor(band_color if row % 2 == 0 else "white")
            if col == 0:
                cell.set_text_props(weight="bold", ha="left")
            if cell.get_text().get_text() == "-":
                cell.set_text_props(color="#777777")

    fig.suptitle(
        "Valores reais por ponto - \u00c1gua Subterr\u00e2nea",
        fontsize=27,
        fontweight="bold",
        y=0.965,
    )
    fig.text(
        0.5,
        0.055,
        "Valores dos pontos representam o maior valor medido na s\u00e9rie. VMP em mg/L, exceto pH; *STD: VMP de consumo humano.",
        ha="center",
        fontsize=12.5,
        color="#333333",
    )
    output = OUT_DIR / "Tabela_Valores_Reais_VMP_Agua_Subterranea_R05.png"
    fig.savefig(output, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def main() -> None:
    table_df = build_table()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "Tabela_Valores_Reais_VMP_Agua_Subterranea_R05.csv"
    table_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    png_path = draw_table(table_df)
    print(json.dumps({"png": str(png_path), "csv": str(csv_path), "rows": len(table_df)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
