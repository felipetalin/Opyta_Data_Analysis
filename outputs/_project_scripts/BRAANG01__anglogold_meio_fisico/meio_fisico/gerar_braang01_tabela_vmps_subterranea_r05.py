from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


OUT_DIR = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados/_revisoes/"
    "R05_todos_os_vmps_20260710/revisado/\u00c1gua_Subterr\u00e2nea"
)

ROWS = [
    ("Ars\u00eanio Dissolvido", "0,01", "0,2", "0,05", "0,008"),
    ("Ars\u00eanio Total", "0,01", "0,2", "0,05", "0,008"),
    ("Cobalto Dissolvido", "-", "1,0", "0,05", "0,01"),
    ("Cobre Dissolvido", "2,0", "0,5", "0,2", "1,0"),
    ("Cromo Dissolvido", "0,05", "1,0", "0,1", "0,05"),
    ("S\u00f3lidos Dissolvidos Totais", "1000", "-", "-", "-"),
    ("Sulfato", "250", "1000", "400", "5"),
    ("Zinco Dissolvido", "5", "24", "2", "5"),
    ("pH", "-", "-", "-", "-"),
]

COLUMNS = [
    "Parâmetro",
    "Consumo Humano",
    "Dessedentação",
    "Irrigação",
    "Recreação",
]


def build_table() -> pd.DataFrame:
    return pd.DataFrame([list(row) for row in ROWS], columns=COLUMNS)


def write_editable_outputs(df: pd.DataFrame) -> None:
    csv_path = OUT_DIR / "Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.csv"
    xlsx_path = OUT_DIR / "Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.xlsx"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="VMPs_CONAMA396")
        ws = writer.sheets["VMPs_CONAMA396"]
        widths = {
            "A": 34,
            "B": 18,
            "C": 18,
            "D": 14,
            "E": 14,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_table()
    write_editable_outputs(df)
    columns = [
        "Par\u00e2metro",
        "Consumo\nHumano",
        "Dessedenta\u00e7\u00e3o",
        "Irriga\u00e7\u00e3o",
        "Recrea\u00e7\u00e3o",
    ]

    fig, ax = plt.subplots(figsize=(16, 7.2))
    ax.axis("off")

    table = ax.table(
        cellText=df.to_numpy().tolist(),
        colLabels=columns,
        bbox=[0.015, 0.12, 0.97, 0.74],
        cellLoc="center",
        colLoc="center",
        colWidths=[0.38, 0.15, 0.16, 0.15, 0.15],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(15)

    header_color = "#2E7D32"
    band_color = "#F3F7F2"
    edge_color = "#A8B6A3"
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(edge_color)
        cell.set_linewidth(1.1)
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", weight="bold")
            cell.set_height(cell.get_height() * 1.25)
        else:
            cell.set_facecolor(band_color if row % 2 == 0 else "white")
            if col == 0:
                cell.set_text_props(ha="left", weight="bold")
            if cell.get_text().get_text() == "-":
                cell.set_text_props(color="#777777")

    fig.suptitle(
        "VMPs por uso - \u00c1gua Subterr\u00e2nea",
        fontsize=27,
        fontweight="bold",
        y=0.965,
    )
    fig.text(
        0.5,
        0.045,
        "Limites legais da Resolu\u00e7\u00e3o CONAMA 396/2008. Valores em mg/L; '-' indica limite n\u00e3o aplic\u00e1vel/n\u00e3o definido para o uso.",
        ha="center",
        fontsize=13,
        color="#333333",
    )

    out = OUT_DIR / "Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.png"
    fig.savefig(out, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(out)
    print(OUT_DIR / "Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.xlsx")
    print(OUT_DIR / "Tabela_VMPs_CONAMA396_Agua_Subterranea_R05.csv")


if __name__ == "__main__":
    main()
