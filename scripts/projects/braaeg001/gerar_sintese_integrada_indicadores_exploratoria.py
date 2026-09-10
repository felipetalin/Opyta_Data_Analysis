from __future__ import annotations

import math
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle


BRANDT_DIR = Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt")
PROJECT_DIR = next(path for path in BRANDT_DIR.iterdir() if path.name.startswith("A&G"))
RESULTS_DIR = PROJECT_DIR / "resultados"
OUT_DIR = RESULTS_DIR / "indicadores_integrados"
HYDROLOGY_KMZ = PROJECT_DIR / "Geo" / "1AEMG002" / "Hidrografia.kmz"

SUPERFICIAL_DIR = RESULTS_DIR / "Meio_fisico" / "resultados" / "superficial"
SEDIMENTOS_DIR = RESULTS_DIR / "Meio_fisico" / "resultados" / "sedimentos"
FITO_DIR = RESULTS_DIR / "migracao_biota" / "fitoplancton"
ZOO_DIR = RESULTS_DIR / "migracao_biota" / "zooplancton"
BENTOS_DIR = RESULTS_DIR / "migracao_biota" / "bentos"
ICTIO_DIR = RESULTS_DIR / "migracao_biota" / "ictiofauna"

CAMPAIGN_ORDER = ["C01-Chuva", "C02-Seca"]
CAMPAIGN_MAP = {
    "Campanha-01-Chuva": "C01-Chuva",
    "Campanha-02-Seca": "C02-Seca",
    "C001-2026-02-CH": "C01-Chuva",
    "C002-2026-06-SC": "C02-Seca",
}
POINT_ORDER = [f"PT_{i:02d}" for i in range(1, 13)]
POINT_LABELS = {point: point.replace("_", "-") for point in POINT_ORDER}

COLORS = {
    "verde": "#178322",
    "verde_claro": "#13f42f",
    "amarelo": "#f2c94c",
    "vermelho": "#ef3b2c",
    "azul": "#2f80ed",
    "cinza": "#d9e2dc",
    "texto": "#17211b",
    "hidro": "#5aa6c8",
}


def load_hydrology_segments(kmz_path: Path) -> list[np.ndarray]:
    if not kmz_path.exists():
        return []
    with zipfile.ZipFile(kmz_path) as archive:
        kml_name = next((name for name in archive.namelist() if name.lower().endswith(".kml")), None)
        if kml_name is None:
            return []
        root = ET.fromstring(archive.read(kml_name))
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    segments: list[np.ndarray] = []
    for coords in root.findall(".//kml:LineString/kml:coordinates", ns):
        text = (coords.text or "").strip()
        pairs = []
        for token in text.split():
            parts = token.split(",")
            if len(parts) >= 2:
                pairs.append((float(parts[0]), float(parts[1])))
        if len(pairs) >= 2:
            segments.append(np.array(pairs))
    return segments


def add_plot_offsets(points: pd.DataFrame) -> pd.DataFrame:
    points = points.copy()
    points["PlotLongitude"] = points["Longitude"]
    points["PlotLatitude"] = points["Latitude"]
    offsets = {
        "PT_08": (-0.00022, 0.00010),
        "PT_11": (0.00022, -0.00010),
        "PT_04": (-0.00014, -0.00010),
        "PT_07": (0.00014, 0.00010),
    }
    for point, (dx, dy) in offsets.items():
        mask = points["Ponto"].eq(point)
        points.loc[mask, "PlotLongitude"] = points.loc[mask, "Longitude"] + dx
        points.loc[mask, "PlotLatitude"] = points.loc[mask, "Latitude"] + dy
    return points


def load_points() -> pd.DataFrame:
    points = pd.read_excel(SUPERFICIAL_DIR / "07_Dados_Minimapas_Agua_Superficial.xlsx", sheet_name="pontos")
    points = points.rename(columns={"Latitude": "Latitude", "Longitude": "Longitude"})
    points = points[points["Ponto"].isin(POINT_ORDER)].copy()
    points["Ponto"] = pd.Categorical(points["Ponto"], POINT_ORDER, ordered=True)
    points = points.sort_values("Ponto").reset_index(drop=True)
    return add_plot_offsets(points)


def iqa_alert(classe: str) -> int:
    classe_norm = str(classe).strip().lower()
    if classe_norm in {"otima", "ótima", "boa"}:
        return 0
    if classe_norm == "regular":
        return 1
    if classe_norm in {"ruim", "pessima", "péssima"}:
        return 2
    return 0


def bmwp_class(value: float) -> str:
    if pd.isna(value):
        return "Sem dado"
    if value >= 86:
        return "Muito boa"
    if value >= 64:
        return "Boa"
    if value >= 37:
        return "Regular"
    if value >= 17:
        return "Ruim"
    return "Péssima"


def bmwp_alert(classe: str) -> int:
    if classe in {"Muito boa", "Boa"}:
        return 0
    if classe == "Regular":
        return 1
    if classe in {"Ruim", "Péssima"}:
        return 2
    return 0


def build_integrated_table() -> pd.DataFrame:
    base = pd.MultiIndex.from_product([CAMPAIGN_ORDER, POINT_ORDER], names=["Campanha", "Ponto"]).to_frame(index=False)

    iqa = pd.read_excel(SUPERFICIAL_DIR / "05_IQA_Tabela.xlsx")
    iqa = iqa.rename(columns={"Classe": "IQA_classe"})
    iqa["Campanha"] = iqa["Campanha"].replace(CAMPAIGN_MAP)
    iqa["Ponto"] = iqa["Ponto"].str.replace("-", "_", regex=False)
    base = base.merge(iqa[["Campanha", "Ponto", "IQA", "IQA_classe"]], on=["Campanha", "Ponto"], how="left")
    base["IQA_alerta"] = base["IQA_classe"].map(iqa_alert).fillna(0).astype(int)

    sed = pd.read_excel(SEDIMENTOS_DIR / "05_Dados_Minimapas_Sedimentos.xlsx", sheet_name="violacoes_por_ponto")
    sed["Campanha"] = sed["Campanha"].replace(CAMPAIGN_MAP)
    sed = sed.rename(
        columns={
            "violacoes": "Sed_violacoes",
            "entre_nivel_1_e_2": "Sed_entre_N1_N2",
            "acima_nivel_2": "Sed_acima_N2",
        }
    )
    base = base.merge(
        sed[["Campanha", "Ponto", "Sed_violacoes", "Sed_entre_N1_N2", "Sed_acima_N2"]],
        on=["Campanha", "Ponto"],
        how="left",
    )
    for col in ["Sed_violacoes", "Sed_entre_N1_N2", "Sed_acima_N2"]:
        base[col] = base[col].fillna(0).astype(int)
    base["Sed_alerta"] = np.select(
        [base["Sed_acima_N2"].gt(0), base["Sed_violacoes"].gt(0)],
        [2, 1],
        default=0,
    )

    fito = pd.read_excel(FITO_DIR / "13_df_mini_mapa_cyanobacteria_fitoplancton.xlsx", sheet_name="cyanobacteria")
    fito = fito.groupby(["campanha_label", "nome_ponto"], as_index=False).agg(
        Ciano_riqueza=("riqueza", "sum"),
        Ciano_taxons=("taxons", lambda s: "; ".join(sorted({str(x) for x in s if pd.notna(x)}))),
    )
    fito = fito.rename(columns={"campanha_label": "Campanha", "nome_ponto": "Ponto"})
    base = base.merge(fito, on=["Campanha", "Ponto"], how="left")
    base["Ciano_riqueza"] = base["Ciano_riqueza"].fillna(0).astype(int)
    base["Ciano_alerta"] = np.select([base["Ciano_riqueza"].ge(2), base["Ciano_riqueza"].eq(1)], [2, 1], default=0)

    zoo = pd.read_excel(ZOO_DIR / "13_df_mini_mapa_taxons_bioindicadores_zooplancton.xlsx", sheet_name="resumo_por_ponto")
    zoo = zoo.groupby(["campanha_label", "nome_ponto"], as_index=False).agg(
        Zoo_grupos=("associacao_ecologica", "nunique"),
        Zoo_riqueza=("riqueza", "sum"),
    )
    zoo = zoo.rename(columns={"campanha_label": "Campanha", "nome_ponto": "Ponto"})
    base = base.merge(zoo, on=["Campanha", "Ponto"], how="left")
    base["Zoo_grupos"] = base["Zoo_grupos"].fillna(0).astype(int)
    base["Zoo_riqueza"] = base["Zoo_riqueza"].fillna(0).astype(int)
    base["Zoo_alerta"] = np.select([base["Zoo_grupos"].ge(3), base["Zoo_grupos"].ge(1)], [2, 1], default=0)

    bentos = pd.read_excel(BENTOS_DIR / "16_df_mini_mapa_bmwp_ept_chol_zoobentos.xlsx", sheet_name="indicadores_por_ponto")
    bentos = bentos.rename(
        columns={
            "campanha_label": "Campanha",
            "nome_ponto": "Ponto",
            "EPT (%)": "EPT_pct",
            "CHOL (%)": "CHOL_pct",
        }
    )
    bentos["BMWP_classe"] = bentos["BMWP"].map(bmwp_class)
    base = base.merge(bentos[["Campanha", "Ponto", "BMWP", "BMWP_classe", "EPT_pct", "CHOL_pct"]], on=["Campanha", "Ponto"], how="left")
    base["BMWP_alerta"] = base["BMWP_classe"].map(bmwp_alert).fillna(0).astype(int)

    ictio = pd.read_excel(ICTIO_DIR / "15_df_mini_mapa_cambevas_cpuen_ictiofauna.xlsx", sheet_name="cpuen_cambevas")
    ictio = ictio.groupby(["campanha_label", "nome_ponto"], as_index=False).agg(
        Cambevas_CPUEn=("CPUEn", "sum"),
        Cambevas_individuos=("individuos", "sum"),
    )
    ictio = ictio.rename(columns={"campanha_label": "Campanha", "nome_ponto": "Ponto"})
    base = base.merge(ictio, on=["Campanha", "Ponto"], how="left")
    base["Cambevas_CPUEn"] = base["Cambevas_CPUEn"].fillna(0)
    base["Cambevas_individuos"] = base["Cambevas_individuos"].fillna(0).astype(int)
    base["Cambevas_presenca"] = base["Cambevas_individuos"].gt(0).astype(int)

    pressure_cols = ["IQA_alerta", "Sed_alerta", "Ciano_alerta", "Zoo_alerta", "BMWP_alerta"]
    base["Pontuacao_atencao_exploratoria"] = base[pressure_cols].sum(axis=1)
    base["Temas_com_atencao"] = base[pressure_cols].gt(0).sum(axis=1)
    base["Indicador_positivo_cambevas"] = base["Cambevas_presenca"]
    base["Ponto_label"] = base["Ponto"].map(POINT_LABELS)
    return base


def cell_color(value: int) -> str:
    return {0: "#dcefd9", 1: "#fff2b2", 2: "#f4b6ae"}.get(int(value), "#f1f1f1")


def plot_matrix(df: pd.DataFrame, out_path: Path) -> None:
    columns = [
        ("IQA", "IQA_alerta", "IQA_classe"),
        ("Sed.", "Sed_alerta", "Sed_violacoes"),
        ("Ciano", "Ciano_alerta", "Ciano_riqueza"),
        ("Zoo", "Zoo_alerta", "Zoo_grupos"),
        ("BMWP", "BMWP_alerta", "BMWP_classe"),
        ("Cambevas", "Cambevas_presenca", "Cambevas_individuos"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(16.54, 8.27), dpi=450, sharey=True)
    for ax, campaign in zip(axes, CAMPAIGN_ORDER):
        sub = df[df["Campanha"].eq(campaign)].set_index("Ponto").reindex(POINT_ORDER).reset_index()
        ax.set_xlim(0, len(columns))
        ax.set_ylim(0, len(POINT_ORDER))
        ax.invert_yaxis()
        ax.set_xticks(np.arange(len(columns)) + 0.5)
        ax.set_xticklabels([col[0] for col in columns], fontsize=8.5, fontweight="bold")
        ax.set_yticks(np.arange(len(POINT_ORDER)) + 0.5)
        ax.set_yticklabels([POINT_LABELS[p] for p in POINT_ORDER], fontsize=8)
        ax.tick_params(length=0)
        ax.set_title(campaign, fontsize=13, fontweight="bold", pad=10)
        for y, row in sub.iterrows():
            for x, (_, score_col, label_col) in enumerate(columns):
                if score_col == "Cambevas_presenca":
                    color = "#cfe1ff" if row[score_col] else "#eeeeee"
                    label = f"{int(row[label_col])} ind." if row[score_col] else "-"
                elif label_col == "Sed_violacoes":
                    color = cell_color(row[score_col])
                    label = f"{int(row[label_col])}"
                elif label_col in {"Ciano_riqueza", "Zoo_grupos"}:
                    color = cell_color(row[score_col])
                    label = f"{int(row[label_col])}"
                elif label_col == "IQA_classe":
                    color = cell_color(row[score_col])
                    label = str(row[label_col]) if pd.notna(row[label_col]) else "-"
                else:
                    color = cell_color(row[score_col])
                    label = str(row[label_col]) if pd.notna(row[label_col]) else "-"
                ax.add_patch(Rectangle((x, y), 1, 1, facecolor=color, edgecolor="white", linewidth=1.2))
                ax.text(x + 0.5, y + 0.5, label, ha="center", va="center", fontsize=7.2, color=COLORS["texto"])
        for spine in ax.spines.values():
            spine.set_visible(False)
    handles = [
        Patch(facecolor="#dcefd9", label="Favorável/sem atenção"),
        Patch(facecolor="#fff2b2", label="Atenção moderada"),
        Patch(facecolor="#f4b6ae", label="Atenção elevada"),
        Patch(facecolor="#cfe1ff", label="Indicador positivo registrado"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, fontsize=9)
    fig.subplots_adjust(top=0.86, bottom=0.08, left=0.07, right=0.98, wspace=0.08)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_integrated_map(df: pd.DataFrame, points: pd.DataFrame, out_path: Path) -> None:
    segments = load_hydrology_segments(HYDROLOGY_KMZ)
    xmin = float(points[["Longitude", "PlotLongitude"]].min().min()) - 0.003
    xmax = float(points[["Longitude", "PlotLongitude"]].max().max()) + 0.003
    ymin = float(points[["Latitude", "PlotLatitude"]].min().min()) - 0.003
    ymax = float(points[["Latitude", "PlotLatitude"]].max().max()) + 0.003
    fig, axes = plt.subplots(1, 2, figsize=(16.54, 8.27), dpi=450, sharex=True, sharey=True)
    norm_max = max(1, int(df["Temas_com_atencao"].max()))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("atencao", ["#dcefd9", "#fff2b2", "#ef3b2c"])
    for ax, campaign in zip(axes, CAMPAIGN_ORDER):
        sub = points.merge(df[df["Campanha"].eq(campaign)], on="Ponto", how="left")
        for seg in segments:
            ax.plot(seg[:, 0], seg[:, 1], color=COLORS["hidro"], lw=0.85, alpha=0.75, zorder=0.8)
        colors = [cmap(v / norm_max) for v in sub["Temas_com_atencao"].fillna(0)]
        sizes = 95 + sub["Temas_com_atencao"].fillna(0) * 55
        ax.scatter(sub["PlotLongitude"], sub["PlotLatitude"], s=sizes, c=colors, edgecolor="#1b2a20", linewidth=0.9, zorder=3)
        cambevas = sub["Cambevas_presenca"].fillna(0).astype(bool)
        ax.scatter(
            sub.loc[cambevas, "PlotLongitude"],
            sub.loc[cambevas, "PlotLatitude"],
            s=sizes[cambevas] + 45,
            facecolor="none",
            edgecolor=COLORS["azul"],
            linewidth=1.5,
            zorder=4,
        )
        for row in sub.itertuples(index=False):
            ax.text(row.PlotLongitude, row.PlotLatitude + 0.00055, row.Ponto_label, ha="center", va="bottom", fontsize=7.5, color=COLORS["texto"], zorder=5)
        ax.set_title(campaign, fontsize=13, fontweight="bold", pad=10)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
            spine.set_color("#6b6b6b")
    handles = [
        Patch(facecolor="#dcefd9", edgecolor="#1b2a20", label="Menor número de temas com atenção"),
        Patch(facecolor="#fff2b2", edgecolor="#1b2a20", label="Atenção intermediária"),
        Patch(facecolor="#ef3b2c", edgecolor="#1b2a20", label="Maior número de temas com atenção"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none", markeredgecolor=COLORS["azul"], markersize=8, label="Cambevas registradas"),
        Line2D([0], [0], color=COLORS["hidro"], lw=1.5, label="Hidrografia"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, fontsize=8.8)
    fig.subplots_adjust(top=0.86, bottom=0.06, left=0.04, right=0.98, wspace=0.05)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    points = load_points()
    df = build_integrated_table()
    xlsx_path = OUT_DIR / "01_sintese_integrada_indicadores_exploratoria.xlsx"
    matrix_path = OUT_DIR / "01_painel_integrado_indicadores_exploratorio.png"
    map_path = OUT_DIR / "02_minimapa_integrado_indicadores_exploratorio.png"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="sintese_por_ponto", index=False)
        df.groupby(["Campanha"], as_index=False).agg(
            media_IQA=("IQA", "mean"),
            pontos_sedimento_com_violacao=("Sed_violacoes", lambda s: int((s > 0).sum())),
            pontos_cianobacteria=("Ciano_riqueza", lambda s: int((s > 0).sum())),
            pontos_zooindicadores=("Zoo_grupos", lambda s: int((s > 0).sum())),
            pontos_bmwp_regular_ou_pior=("BMWP_alerta", lambda s: int((s > 0).sum())),
            pontos_cambevas=("Cambevas_presenca", "sum"),
        ).to_excel(writer, sheet_name="resumo_campanha", index=False)
        pd.DataFrame(
            {
                "Campo": [
                    "IQA_alerta",
                    "Sed_alerta",
                    "Ciano_alerta",
                    "Zoo_alerta",
                    "BMWP_alerta",
                    "Cambevas_presenca",
                    "Pontuacao_atencao_exploratoria",
                ],
                "Critério": [
                    "0 = Ótima/Boa; 1 = Regular; 2 = Ruim/Péssima",
                    "0 = sem violação; 1 = > Nível 1 e <= Nível 2; 2 = > Nível 2",
                    "0 = ausente; 1 = riqueza 1; 2 = riqueza >= 2",
                    "0 = ausente; 1 = 1-2 associações; 2 = >= 3 associações",
                    "0 = BMWP Muito boa/Boa; 1 = Regular; 2 = Ruim/Péssima",
                    "Indicador positivo de integridade; não entra como pressão",
                    "Soma exploratória dos alertas, sem equivalência normativa entre temas",
                ],
            }
        ).to_excel(writer, sheet_name="criterios", index=False)
    plot_matrix(df, matrix_path)
    plot_integrated_map(df, points, map_path)
    print({"xlsx": str(xlsx_path), "painel": str(matrix_path), "mapa": str(map_path)})


if __name__ == "__main__":
    main()
