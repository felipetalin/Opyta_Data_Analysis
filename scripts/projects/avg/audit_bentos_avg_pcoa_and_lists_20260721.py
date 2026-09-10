from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
BASE_DIR = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
ANALYTIC_XLSX = BASE_DIR / "zoobentos_consolidated_analytic_base_20260721" / "base_analitica_consolidada_zoobentos_20260721.xlsx"
SUPPORT_DIR = BASE_DIR / "zoobentos_pcoa_composition_audit_20260721"
FINAL_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Brandt\AVG\Produtos"
    r"\Planilha Consolidada\Resultados e planilhas\Resultados bentos\Consolidado_2026"
)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _bray_curtis(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            denom = matrix[i].sum() + matrix[j].sum()
            value = 0.0 if denom == 0 else np.abs(matrix[i] - matrix[j]).sum() / denom
            dist[i, j] = value
            dist[j, i] = value
    return dist


def _pcoa(distance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = distance.shape[0]
    d2 = distance**2
    h = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * h @ d2 @ h
    eigvals, eigvecs = np.linalg.eigh(b)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    positive = np.maximum(eigvals[:2], 0)
    coords = eigvecs[:, :2] * np.sqrt(positive)
    total = eigvals[eigvals > 0].sum()
    explained = positive / total * 100 if total > 0 else np.zeros(2)
    return coords, explained


def _composition_lists(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    comp = base[["Filo", "Classe", "Ordem", "Familia", "Nome_Cientifico"]].drop_duplicates().copy()
    comp["Ordem_plot"] = comp["Ordem"].fillna("Sem ordem")
    by_order = (
        comp.groupby("Ordem_plot", dropna=False)
        .agg(riqueza_taxonomica=("Nome_Cientifico", "nunique"), familias=("Familia", "nunique"))
        .reset_index()
        .sort_values(["riqueza_taxonomica", "Ordem_plot"], ascending=[False, True])
        .reset_index(drop=True)
    )
    by_order["percentual_riqueza"] = by_order["riqueza_taxonomica"] / by_order["riqueza_taxonomica"].sum() * 100
    by_order.insert(0, "ordem_ranking", np.arange(1, len(by_order) + 1))
    donut = by_order.copy()
    donut["grupo_rosca_sugerido"] = donut["Ordem_plot"]
    if len(donut) > 8:
        donut.loc[donut["ordem_ranking"] > 8, "grupo_rosca_sugerido"] = "Outras ordens"
    donut = (
        donut.groupby("grupo_rosca_sugerido", as_index=False)
        .agg(riqueza_taxonomica=("riqueza_taxonomica", "sum"), percentual_riqueza=("percentual_riqueza", "sum"))
        .sort_values("riqueza_taxonomica", ascending=False)
        .reset_index(drop=True)
    )
    return by_order, donut, comp.sort_values(["Ordem_plot", "Familia", "Nome_Cientifico"])


def _pcoa_lists(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    taxa = sorted(base["Nome_Cientifico"].dropna().unique())
    years = sorted(base["Ano_Temporal"].dropna().unique())
    score_tables = []
    distance_tables = []
    vectors = []
    groups = []
    for year in years:
        sub = base[base["Ano_Temporal"].eq(year)]
        matrix = (
            sub.pivot_table(index="Ponto", columns="Nome_Cientifico", values="Numero_de_Individuos", aggfunc="sum", fill_value=0)
            .reindex(columns=taxa, fill_value=0)
        )
        matrix = matrix.loc[matrix.sum(axis=1) > 0]
        points = matrix.index.tolist()
        dist = _bray_curtis(matrix.to_numpy(dtype=float))
        coords, explained = _pcoa(dist)
        scores = pd.DataFrame(coords, columns=["PCoA1", "PCoA2"])
        scores.insert(0, "Ponto", points)
        scores.insert(0, "Ano_Temporal", year)
        scores["PCoA1_percentual"] = explained[0]
        scores["PCoA2_percentual"] = explained[1]
        score_tables.append(scores)
        distance_tables.append(pd.DataFrame(dist, index=points, columns=points).reset_index(names="Ponto").assign(Ano_Temporal=year))

        if len(points) > 2:
            condensed = squareform(dist, checks=False)
            z = linkage(condensed, method="average")
            labels = fcluster(z, t=0.80, criterion="distance")
        else:
            labels = np.ones(len(points), dtype=int)
        group_df = pd.DataFrame({"Ano_Temporal": year, "Ponto": points, "Grupo_Bray_080": labels})
        groups.append(group_df)

        x = matrix.to_numpy(dtype=float)
        for taxon_idx, taxon in enumerate(matrix.columns):
            values = x[:, taxon_idx]
            if np.count_nonzero(values) < 2 or np.nanstd(values) == 0:
                continue
            corr1 = float(np.corrcoef(values, coords[:, 0])[0, 1]) if np.nanstd(coords[:, 0]) > 0 else 0.0
            corr2 = float(np.corrcoef(values, coords[:, 1])[0, 1]) if np.nanstd(coords[:, 1]) > 0 else 0.0
            strength = float(np.sqrt(corr1**2 + corr2**2))
            vectors.append(
                {
                    "Ano_Temporal": year,
                    "Nome_Cientifico": taxon,
                    "correlacao_PCoA1": corr1,
                    "correlacao_PCoA2": corr2,
                    "forca_associacao": strength,
                    "abundancia_ano": float(values.sum()),
                    "pontos_ocorrencia_ano": int(np.count_nonzero(values)),
                }
            )
    vectors_df = pd.DataFrame(vectors).sort_values(["Ano_Temporal", "forca_associacao"], ascending=[True, False])
    return (
        pd.concat(score_tables, ignore_index=True),
        pd.concat(distance_tables, ignore_index=True),
        pd.concat(groups, ignore_index=True),
        vectors_df,
    )


def main() -> int:
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    base = pd.read_excel(ANALYTIC_XLSX, sheet_name="base_analitica")
    point_campaign = pd.read_excel(ANALYTIC_XLSX, sheet_name="ponto_campanha")
    monitored_base = base[base["Status_Monitoramento"].eq("Monitorado")].copy()
    by_order, donut, taxa_by_order = _composition_lists(monitored_base)
    scores, distances, groups, vectors = _pcoa_lists(monitored_base)
    not_monitored_mask = point_campaign["Status_Monitoramento"].astype(str).str.strip().ne("Monitorado")
    not_monitored = point_campaign.loc[
        not_monitored_mask,
        ["Ponto", "Campanha", "Campanha_Curta", "Ano_Temporal", "Status_Monitoramento"],
    ].sort_values(["Ponto", "Campanha_Curta"])
    out_xlsx = FINAL_DIR / "LISTAS_APROVACAO_composicao_pcoa_amostragem_zoobentos.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        by_order.to_excel(writer, sheet_name="composicao_ordem_completa", index=False)
        donut.to_excel(writer, sheet_name="sugestao_rosca_ordem", index=False)
        taxa_by_order.to_excel(writer, sheet_name="taxons_por_ordem", index=False)
        not_monitored.to_excel(writer, sheet_name="pontos_nao_monitorados", index=False)
        scores.to_excel(writer, sheet_name="pcoa_scores", index=False)
        groups.to_excel(writer, sheet_name="grupos_bray_080", index=False)
        vectors.to_excel(writer, sheet_name="taxons_vetores_pcoa", index=False)
        distances.to_excel(writer, sheet_name="distancias_bray", index=False)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output": out_xlsx,
        "orders": int(len(by_order)),
        "taxa": int(monitored_base["Nome_Cientifico"].nunique()),
        "not_monitored_point_campaigns": int(len(not_monitored)),
        "pcoa_years": sorted(map(int, scores["Ano_Temporal"].unique())),
    }
    manifest = SUPPORT_DIR / "manifesto_listas_aprovacao_composicao_pcoa_amostragem_zoobentos.json"
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
