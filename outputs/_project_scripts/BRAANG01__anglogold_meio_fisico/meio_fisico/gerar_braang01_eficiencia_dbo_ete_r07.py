from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CODE = "BRAANG01"
MATRIX = "Efluente"
PARAM = "Demanda Bioqu\u00edmica de Oxig\u00eanio"
REVISION = "R07_eficiencia_dbo_ete_20260713"
DEFAULT_RESULTS_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados"
)
DEFAULT_REV_ROOT = DEFAULT_RESULTS_ROOT / "_revisoes" / REVISION

INPUT_POINT = "MCB907E"
OUTPUT_POINT = "MCB907S"
MIN_EFFICIENCY = 60.0

SELECTED_CAMPAIGNS = [
    ("jan-2021", "2021-01"),
    ("mar-2021", "2021-03"),
    ("jul-2021", "2021-07"),
    ("set-2021", "2021-09"),
    ("dez-2021", "2021-12"),
    ("mar-2022", "2022-03"),
    ("jun-2022", "2022-06"),
    ("set-2022", "2022-09"),
    ("dez-2022", "2022-12"),
    ("mar-2023", "2023-03"),
    ("jun-2023", "2023-06"),
    ("set-2023", "2023-09"),
    ("nov-2023", "2023-11"),
    ("mar-2024", "2024-03"),
    ("jun-2024", "2024-06"),
    ("set-2024", "2024-09"),
    ("nov-2024", "2024-11"),
    ("mar-2025", "2025-03"),
    ("jun-2025", "2025-06"),
]


def revision_root() -> Path:
    return Path(os.environ.get("BRAANG01_DBO_EFF_R07_ROOT", str(DEFAULT_REV_ROOT)))


def load_data() -> pd.DataFrame:
    load_dotenv(REPO_ROOT / ".env")
    db_url = os.environ.get("FISICO_DB_URL")
    if not db_url:
        raise RuntimeError("FISICO_DB_URL nao encontrado no .env")
    query = text(
        """
        SELECT nome_ponto, nome_campanha, data_hora_coleta, valor_medido, unidade_medida
        FROM public.fisico_analise_consolidada
        WHERE codigo_interno_opyta = :code
          AND matriz = :matrix
          AND nome_ponto = ANY(:points)
          AND nome_parametro = :param
        """
    )
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '15min'"))
        df = pd.read_sql(
            query,
            conn,
            params={
                "code": PROJECT_CODE,
                "matrix": MATRIX,
                "points": [INPUT_POINT, OUTPUT_POINT],
                "param": PARAM,
            },
        )
    df["valor_medido"] = pd.to_numeric(df["valor_medido"], errors="coerce")
    df["data_hora_coleta"] = pd.to_datetime(df["data_hora_coleta"], errors="coerce")
    df["ano_mes"] = df["data_hora_coleta"].dt.strftime("%Y-%m")
    return df


def build_efficiency_table(df: pd.DataFrame) -> pd.DataFrame:
    selected_months = [month for _label, month in SELECTED_CAMPAIGNS]
    campaign_labels = {month: label for label, month in SELECTED_CAMPAIGNS}
    order = {month: idx for idx, month in enumerate(selected_months)}

    d = df[df["ano_mes"].isin(selected_months)].copy()
    pivot = (
        d.pivot_table(
            index="ano_mes",
            columns="nome_ponto",
            values="valor_medido",
            aggfunc="first",
        )
        .reset_index()
        .sort_values("ano_mes")
    )
    pivot = pivot[pivot["ano_mes"].isin(selected_months)].copy()
    pivot["ordem"] = pivot["ano_mes"].map(order)
    pivot = pivot.sort_values("ordem")
    pivot["Campanha"] = pivot["ano_mes"].map(campaign_labels)
    pivot["DBO Entrada - MCB907E (mg/L)"] = pivot[INPUT_POINT]
    pivot["DBO Saida - MCB907S (mg/L)"] = pivot[OUTPUT_POINT]
    pivot["Eficiencia de remocao (%)"] = (
        (pivot[INPUT_POINT] - pivot[OUTPUT_POINT]) / pivot[INPUT_POINT] * 100
    )
    pivot["Atende >= 60%"] = pivot["Eficiencia de remocao (%)"] >= MIN_EFFICIENCY
    pivot["Status"] = pivot["Atende >= 60%"].map({True: "Atende", False: "Nao atende"})
    return pivot[
        [
            "Campanha",
            "ano_mes",
            "DBO Entrada - MCB907E (mg/L)",
            "DBO Saida - MCB907S (mg/L)",
            "Eficiencia de remocao (%)",
            "Atende >= 60%",
            "Status",
        ]
    ].reset_index(drop=True)


def summary_table(result: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Campanhas pareadas", len(result)],
            ["Campanhas que atendem", int(result["Atende >= 60%"].sum())],
            ["Campanhas que nao atendem", int((~result["Atende >= 60%"]).sum())],
            ["Eficiencia media simples (%)", round(float(result["Eficiencia de remocao (%)"].mean()), 1)],
            [
                "Eficiencia ponderada (%)",
                round(
                    float(
                        (1 - result["DBO Saida - MCB907S (mg/L)"].sum() / result["DBO Entrada - MCB907E (mg/L)"].sum())
                        * 100
                    ),
                    1,
                ),
            ],
            ["Criterio minimo (%)", MIN_EFFICIENCY],
        ],
        columns=["Indicador", "Valor"],
    )


def write_excel(result: pd.DataFrame, summary: pd.DataFrame, out_dir: Path) -> Path:
    xlsx = out_dir / "Eficiencia_DBO_ETE_MCB907E_MCB907S_R07.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        result.to_excel(writer, sheet_name="eficiencia_por_campanha", index=False)
        result[~result["Atende >= 60%"]].to_excel(writer, sheet_name="nao_atende", index=False)
        summary.to_excel(writer, sheet_name="resumo", index=False)
        wb = writer.book
        for ws in wb.worksheets:
            ws.freeze_panes = "A2"
            for column_cells in ws.columns:
                width = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = min(max(width + 2, 12), 42)
    return xlsx


def plot_efficiency(result: pd.DataFrame, out_dir: Path) -> Path:
    x = range(len(result))
    colors = ["#2E7D32" if ok else "#B22222" for ok in result["Atende >= 60%"]]
    fig, ax = plt.subplots(figsize=(19.25, 7.8))
    ax.plot(x, result["Eficiencia de remocao (%)"], color="#2E7D32", linewidth=3, zorder=2)
    ax.scatter(x, result["Eficiencia de remocao (%)"], s=130, color=colors, zorder=4)
    ax.axhline(
        MIN_EFFICIENCY,
        color="red",
        linestyle="--",
        linewidth=3,
        label="Remo\u00e7\u00e3o m\u00ednima: 60%",
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(result["Campanha"].tolist(), rotation=90, fontsize=14)
    ax.set_ylabel("Efici\u00eancia de remo\u00e7\u00e3o (%)", fontsize=18, fontweight="bold")
    ax.set_xlabel("Campanhas", fontsize=17)
    ax.tick_params(axis="y", labelsize=14)
    ax.yaxis.grid(True, linestyle="-", alpha=0.35, color="#CCCCCC")
    ax.set_ylim(min(-45, float(result["Eficiencia de remocao (%)"].min()) * 1.15), 105)
    ax.legend(loc="lower left", fontsize=14, frameon=True, facecolor="white", framealpha=1)
    fig.suptitle(
        "Efici\u00eancia de remo\u00e7\u00e3o de DBO - ETE MCB907E/S",
        fontsize=28,
        fontweight="bold",
        y=0.97,
    )
    fig.subplots_adjust(bottom=0.25, top=0.86)
    fig.text(
        0.5,
        0.045,
        "Efici\u00eancia = (DBO entrada - DBO sa\u00edda) / DBO entrada x 100. Crit\u00e9rio: remo\u00e7\u00e3o m\u00ednima de 60% de DBO (CONAMA 430/2011, complementar \u00e0 CONAMA 357/2005).",
        ha="center",
        fontsize=11.5,
        color="#333333",
    )
    output = out_dir / "Grafico_Eficiencia_DBO_ETE_MCB907E_MCB907S_R07.png"
    fig.savefig(output, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def write_manifest(root: Path, subdir: Path, filename: str) -> None:
    rows = ["sha256,bytes,relative_path"]
    for item in sorted(subdir.iterdir(), key=lambda p: p.name):
        if item.is_file() and item.name != "desktop.ini":
            rows.append(
                f"{hashlib.sha256(item.read_bytes()).hexdigest()},{item.stat().st_size},{item.relative_to(root).as_posix()}"
            )
    (root / filename).write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    rev_root = revision_root()
    out_dir = rev_root / "revisado" / "Eficiencia_DBO_ETE"
    scripts_dir = rev_root / "scripts"
    baseline_dir = rev_root / "linha_base" / "Eficiencia_DBO_ETE"
    out_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir.mkdir(parents=True, exist_ok=True)
    for item in out_dir.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json", ".csv", ".xlsx"}:
            item.unlink()
    shutil.copy2(Path(__file__), scripts_dir / Path(__file__).name)

    result = build_efficiency_table(load_data())
    summary = summary_table(result)
    csv = out_dir / "Eficiencia_DBO_ETE_MCB907E_MCB907S_R07.csv"
    result.to_csv(csv, index=False, encoding="utf-8-sig")
    xlsx = write_excel(result, summary, out_dir)
    png = plot_efficiency(result, out_dir)
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "revision": REVISION,
        "param": PARAM,
        "input_point": INPUT_POINT,
        "output_point": OUTPUT_POINT,
        "selected_campaign_count": len(result),
        "min_efficiency_percent": MIN_EFFICIENCY,
        "meets_count": int(result["Atende >= 60%"].sum()),
        "fails_count": int((~result["Atende >= 60%"]).sum()),
        "mean_efficiency_percent": round(float(result["Eficiencia de remocao (%)"].mean()), 1),
        "weighted_efficiency_percent": round(
            float(
                (1 - result["DBO Saida - MCB907S (mg/L)"].sum() / result["DBO Entrada - MCB907E (mg/L)"].sum())
                * 100
            ),
            1,
        ),
        "outputs": {
            "csv": str(csv),
            "xlsx": str(xlsx),
            "png": str(png),
        },
        "regulatory_reference": "CONAMA 430/2011, complementar a CONAMA 357/2005; remocao minima de 60% de DBO.",
    }
    (out_dir / "revision_generation_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_manifest(rev_root, out_dir, "manifest_revisado_sha256.csv")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()
