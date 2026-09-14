from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
from sklearn.manifold import MDS


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.config import load_theme


DEFAULT_SOURCE = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Planilhas de migracao"
    r"\Projeto_GEOARC001_ictio_260326xlsx_TAXONOMIA_GATE_B_R02.xlsx"
)
DEFAULT_COMPOSITION = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\01_tabela_composicao_ictiofauna.xlsx"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "_scratch" / "geoarc001_ictiofauna_exploratorio_assembleia"
SEASON_LABELS = {"CH": "Chuvosa", "SC": "Seca", "ND": "N.D."}


@dataclass(frozen=True)
class SourceTables:
    pontos_campanhas: pd.DataFrame
    esforcos: pd.DataFrame
    resultados: pd.DataFrame
    composicao: pd.DataFrame


def _normalize_text(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _campaign_number(campaign: str) -> int:
    match = re.search(r"^C0*(\d+)", str(campaign), flags=re.IGNORECASE)
    return int(match.group(1)) if match else 999999


def _campaign_sort_key(campaign: str) -> tuple[int, str]:
    return (_campaign_number(campaign), str(campaign))


def _campaign_short(campaign: str) -> str:
    number = _campaign_number(campaign)
    return f"C{number:02d}" if number < 999999 else str(campaign)


def _campaign_year(campaign: str) -> int | None:
    match = re.search(r"(20\d{2}|19\d{2})", str(campaign))
    return int(match.group(1)) if match else None


def _campaign_month(campaign: str) -> int | None:
    match = re.search(r"20\d{2}[-_](\d{2})", str(campaign))
    return int(match.group(1)) if match else None


def _campaign_season(campaign: str) -> str:
    text = str(campaign).upper()
    if re.search(r"(^|[-_\s])CH($|[-_\s])", text):
        return "CH"
    if re.search(r"(^|[-_\s])SC($|[-_\s])", text):
        return "SC"
    return "ND"


def _point_number(point: str) -> int:
    match = re.search(r"(\d+)", str(point))
    return int(match.group(1)) if match else 999999


def _point_sort_key(point: str) -> tuple[int, str]:
    return (_point_number(point), str(point))


def _is_quantitative(value: object) -> bool:
    return "quantit" in _normalize_text(value)


def _shannon(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[arr > 0]
    if arr.size == 0:
        return 0.0
    p = arr / arr.sum()
    return float(-np.sum(p * np.log(p)))


def _pielou(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[arr > 0]
    if arr.size <= 1:
        return 0.0
    return float(_shannon(arr) / np.log(arr.size))


def _hellinger(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=float)
    row_sums = arr.sum(axis=1, keepdims=True)
    out = np.zeros_like(arr, dtype=float)
    np.divide(arr, row_sums, out=out, where=row_sums > 0)
    return np.sqrt(out)


def _bray_curtis_matrix(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=float)
    numerator = np.abs(arr[:, None, :] - arr[None, :, :]).sum(axis=2)
    denominator = (arr[:, None, :] + arr[None, :, :]).sum(axis=2)
    dist = np.zeros_like(numerator, dtype=float)
    np.divide(numerator, denominator, out=dist, where=denominator > 0)
    np.fill_diagonal(dist, 0.0)
    return dist


def _pcoa_coordinates(distance: np.ndarray) -> np.ndarray:
    d = np.asarray(distance, dtype=float)
    n = d.shape[0]
    if n == 0:
        return np.empty((0, 0))
    j = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * j @ (d**2) @ j
    eigvals, eigvecs = np.linalg.eigh(b)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    positive = eigvals > 1e-12
    if not positive.any():
        return np.zeros((n, 1))
    return eigvecs[:, positive] * np.sqrt(eigvals[positive])


def read_sources(source: Path, composition: Path) -> SourceTables:
    if not source.exists():
        raise FileNotFoundError(f"Planilha de entrada não encontrada: {source}")
    if not composition.exists():
        raise FileNotFoundError(f"Tabela de composição não encontrada: {composition}")
    return SourceTables(
        pontos_campanhas=pd.read_excel(source, sheet_name="Pontos_e_Campanhas"),
        esforcos=pd.read_excel(source, sheet_name="Metadados_Esforco"),
        resultados=pd.read_excel(source, sheet_name="Resultados_Ictiofauna"),
        composicao=pd.read_excel(composition),
    )


def build_species_origin(composicao: pd.DataFrame) -> pd.DataFrame:
    comp = composicao.copy()
    comp = comp.rename(columns={"Nome Cientifico": "nome_cientifico", "Origem": "origem"})
    comp = comp[comp["nome_cientifico"].notna()].copy()
    if "ID Especie" in comp.columns:
        preferred = comp[comp["ID Especie"].notna()].copy()
        if not preferred.empty:
            comp = preferred
    comp["species_key"] = comp["nome_cientifico"].map(_normalize_text)
    comp["origem_norm"] = comp.get("origem", "").map(_normalize_text)
    comp = comp.drop_duplicates("species_key")
    comp["nao_nativa"] = comp["origem_norm"].str.contains("nao nativo|nao nativa|exot|aloc|introdu", regex=True)
    return comp[["species_key", "nome_cientifico", "origem", "nao_nativa"]].copy()


def build_community(tables: SourceTables) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pc = tables.pontos_campanhas.rename(
        columns={"Campanha": "nome_campanha", "Ponto": "nome_ponto", "Data": "data"}
    ).copy()
    effort = tables.esforcos.rename(
        columns={
            "Campanha": "nome_campanha",
            "Ponto": "nome_ponto",
            "Metodo_de_Captura": "metodo_de_captura",
            "Unidade_Esforco": "unidade_esforco",
            "Tipo_de_Amostragem": "tipo_amostragem",
            "Esforco": "esforco",
        }
    ).copy()
    results = tables.resultados.rename(
        columns={
            "Campanha": "nome_campanha",
            "Ponto": "nome_ponto",
            "Metodo_de_Captura": "metodo_de_captura",
            "Tipo_de_Amostragem": "tipo_amostragem",
            "Unidade_Esforco": "unidade_esforco",
            "Nome_Cientifico": "nome_cientifico",
            "Numero_de_Individuos": "contagem",
        }
    ).copy()

    for frame in [pc, effort, results]:
        for col in ["nome_campanha", "nome_ponto"]:
            frame[col] = frame[col].astype(str).str.strip()
    campaign_meta_cols = [
        col
        for col in [
            "Ano_Temporal",
            "Ano_Calendario",
            "Mes",
            "Periodo_Hidrologico",
            "Ciclo_Temporal",
            "Rotulo_Relatorio",
        ]
        if col in pc.columns
    ]
    campaign_meta = (
        pc[["nome_campanha", *campaign_meta_cols]]
        .drop_duplicates("nome_campanha")
        .copy()
        if campaign_meta_cols
        else pd.DataFrame(columns=["nome_campanha"])
    )
    point_meta_cols = [col for col in ["Area_Controle"] if col in pc.columns]
    point_meta = (
        pc[["nome_ponto", *point_meta_cols]].drop_duplicates("nome_ponto").copy()
        if point_meta_cols
        else pd.DataFrame(columns=["nome_ponto"])
    )
    results["nome_cientifico"] = results["nome_cientifico"].astype(str).str.strip()
    results.loc[results["nome_cientifico"].str.lower().isin(["nan", "none", ""]), "nome_cientifico"] = np.nan
    results["contagem"] = pd.to_numeric(results["contagem"], errors="coerce").fillna(0)

    effort = effort[effort["tipo_amostragem"].map(_is_quantitative)].copy()
    effort["esforco"] = pd.to_numeric(effort["esforco"], errors="coerce")
    effort = effort[effort["esforco"].notna() & (effort["esforco"] > 0)].copy()
    effort_cols = ["nome_campanha", "nome_ponto", "metodo_de_captura", "unidade_esforco", "esforco"]
    effort_total = (
        effort[effort_cols]
        .drop_duplicates()
        .groupby(["nome_campanha", "nome_ponto"], as_index=False, dropna=False)
        .agg(esforco_total=("esforco", "sum"))
    )

    results_q = results[results["tipo_amostragem"].map(_is_quantitative)].copy()
    results_q = results_q[results_q["nome_cientifico"].notna()].copy()
    counts = (
        results_q.groupby(["nome_campanha", "nome_ponto", "nome_cientifico"], as_index=False, dropna=False)
        .agg(contagem=("contagem", "sum"))
        .merge(effort_total, on=["nome_campanha", "nome_ponto"], how="left")
    )
    counts = counts[counts["esforco_total"].notna() & (counts["esforco_total"] > 0)].copy()
    counts["CPUEn"] = counts["contagem"] / counts["esforco_total"] * 100.0

    campaigns = sorted(pc["nome_campanha"].dropna().unique().tolist(), key=_campaign_sort_key)
    points = sorted(pc["nome_ponto"].dropna().unique().tolist(), key=_point_sort_key)
    sample_grid = (
        pc[["nome_campanha", "nome_ponto", "data"]]
        .drop_duplicates(["nome_campanha", "nome_ponto"])
        .merge(effort_total, on=["nome_campanha", "nome_ponto"], how="left")
    )
    if not campaign_meta.empty:
        sample_grid = sample_grid.merge(campaign_meta, on="nome_campanha", how="left")
    if not point_meta.empty:
        sample_grid = sample_grid.merge(point_meta, on="nome_ponto", how="left")
    sample_grid["nome_campanha"] = pd.Categorical(sample_grid["nome_campanha"], categories=campaigns, ordered=True)
    sample_grid["nome_ponto"] = pd.Categorical(sample_grid["nome_ponto"], categories=points, ordered=True)
    sample_grid = sample_grid.sort_values(["nome_campanha", "nome_ponto"]).reset_index(drop=True)
    sample_grid["nome_campanha"] = sample_grid["nome_campanha"].astype(str)
    sample_grid["nome_ponto"] = sample_grid["nome_ponto"].astype(str)
    sample_grid["sample_id"] = sample_grid["nome_campanha"] + " | " + sample_grid["nome_ponto"]
    sample_grid["ano"] = sample_grid["nome_campanha"].map(_campaign_year)
    sample_grid["mes"] = sample_grid["nome_campanha"].map(_campaign_month)
    sample_grid["estacao"] = sample_grid["nome_campanha"].map(_campaign_season)
    if "Ano_Temporal" in sample_grid.columns:
        sample_grid["ano"] = pd.to_numeric(sample_grid["Ano_Temporal"], errors="coerce").combine_first(
            pd.to_numeric(sample_grid["ano"], errors="coerce")
        )
    if "Mes" in sample_grid.columns:
        sample_grid["mes"] = pd.to_numeric(sample_grid["Mes"], errors="coerce").combine_first(
            pd.to_numeric(sample_grid["mes"], errors="coerce")
        )
    if "Periodo_Hidrologico" in sample_grid.columns:
        season_override = sample_grid["Periodo_Hidrologico"].astype(str).str.strip().str.upper()
        sample_grid.loc[season_override.isin(["CH", "SC"]), "estacao"] = season_override[season_override.isin(["CH", "SC"])]
    sample_grid["estacao_rotulo"] = sample_grid["estacao"].map(SEASON_LABELS)
    sample_grid["campanha_curta"] = sample_grid["nome_campanha"].map(_campaign_short)
    sample_grid["ordem_campanha"] = sample_grid["nome_campanha"].map(_campaign_number)

    species = sorted(counts["nome_cientifico"].dropna().unique().tolist(), key=lambda s: _normalize_text(s))
    table = counts.pivot_table(
        index=["nome_campanha", "nome_ponto"],
        columns="nome_cientifico",
        values="CPUEn",
        aggfunc="sum",
        fill_value=0.0,
        observed=False,
    )
    table.index = [f"{camp} | {point}" for camp, point in table.index]
    matrix = table.reindex(index=sample_grid["sample_id"].tolist(), columns=species, fill_value=0.0).astype(float)
    sample_grid["CPUEn_total"] = matrix.sum(axis=1).to_numpy()
    sample_grid["riqueza"] = (matrix > 0).sum(axis=1).to_numpy(dtype=int)
    sample_grid["captura_quantitativa"] = sample_grid["CPUEn_total"] > 0
    return matrix, sample_grid, counts


def calculate_lcbd(matrix: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for campaign, group in metadata.groupby("nome_campanha", sort=False):
        sample_ids = group["sample_id"].tolist()
        mat = matrix.loc[sample_ids].to_numpy(dtype=float)
        hel = _hellinger(mat)
        centroid = hel.mean(axis=0)
        ss = ((hel - centroid) ** 2).sum(axis=1)
        ss_total = float(ss.sum())
        lcbd = ss / ss_total if ss_total > 0 else np.zeros_like(ss)
        beta_total = ss_total / max(len(sample_ids) - 1, 1)
        for sample_id, value, ss_value in zip(sample_ids, lcbd, ss, strict=True):
            meta = metadata.loc[metadata["sample_id"] == sample_id].iloc[0]
            rows.append(
                {
                    "nome_campanha": campaign,
                    "campanha_curta": meta["campanha_curta"],
                    "ano": meta["ano"],
                    "estacao": meta["estacao"],
                    "estacao_rotulo": meta["estacao_rotulo"],
                    "nome_ponto": meta["nome_ponto"],
                    "sample_id": sample_id,
                    "LCBD": float(value),
                    "SS_ponto": float(ss_value),
                    "Beta_Total_Hellinger_Campanha": float(beta_total),
                    "CPUEn_total": float(meta["CPUEn_total"]),
                    "riqueza": int(meta["riqueza"]),
                }
            )
    return pd.DataFrame(rows)


def beta_partition(a_vec: np.ndarray, b_vec: np.ndarray) -> dict[str, float]:
    x = np.asarray(a_vec, dtype=float) > 0
    y = np.asarray(b_vec, dtype=float) > 0
    shared = int(np.logical_and(x, y).sum())
    only_x = int(np.logical_and(x, ~y).sum())
    only_y = int(np.logical_and(~x, y).sum())
    denom_sor = 2 * shared + only_x + only_y
    beta_sor = (only_x + only_y) / denom_sor if denom_sor > 0 else 0.0
    denom_sim = shared + min(only_x, only_y)
    beta_sim = min(only_x, only_y) / denom_sim if denom_sim > 0 else 0.0
    beta_nes = max(0.0, beta_sor - beta_sim)
    return {
        "shared_species": shared,
        "exclusive_a": only_x,
        "exclusive_b": only_y,
        "richness_a": int(x.sum()),
        "richness_b": int(y.sum()),
        "beta_sorensen": float(beta_sor),
        "turnover_beta_sim": float(beta_sim),
        "nestedness_beta_nes": float(beta_nes),
    }


def calculate_beta_tables(matrix: pd.DataFrame, metadata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    seasonal_rows = []
    for year, year_meta in metadata.groupby("ano", sort=True):
        if pd.isna(year):
            continue
        vectors = {}
        for season in ["CH", "SC"]:
            sample_ids = year_meta.loc[year_meta["estacao"] == season, "sample_id"].tolist()
            if sample_ids:
                vectors[season] = matrix.loc[sample_ids].sum(axis=0).to_numpy(dtype=float)
        if {"CH", "SC"}.issubset(vectors):
            out = beta_partition(vectors["CH"], vectors["SC"])
            out.update({"ano": int(year), "comparacao": "Chuvosa x Seca", "unidade_a": "Chuvosa", "unidade_b": "Seca"})
            seasonal_rows.append(out)

    consecutive_rows = []
    years = sorted(int(y) for y in metadata["ano"].dropna().unique().tolist())
    for y0, y1 in zip(years[:-1], years[1:], strict=False):
        ids0 = metadata.loc[metadata["ano"] == y0, "sample_id"].tolist()
        ids1 = metadata.loc[metadata["ano"] == y1, "sample_id"].tolist()
        if not ids0 or not ids1:
            continue
        out = beta_partition(
            matrix.loc[ids0].sum(axis=0).to_numpy(dtype=float),
            matrix.loc[ids1].sum(axis=0).to_numpy(dtype=float),
        )
        out.update({"par_anos": f"{y0}-{y1}", "ano_a": y0, "ano_b": y1, "comparacao": "Anos consecutivos"})
        consecutive_rows.append(out)

    return pd.DataFrame(seasonal_rows), pd.DataFrame(consecutive_rows)


def permanova(distance: np.ndarray, groups: pd.Series, n_perm: int = 999, seed: int = 20260625) -> dict:
    d = np.asarray(distance, dtype=float)
    labels = pd.Series(groups).astype(str).reset_index(drop=True)
    valid_groups = labels.value_counts()
    keep_labels = valid_groups[valid_groups >= 2].index
    keep = labels.isin(keep_labels).to_numpy()
    d = d[np.ix_(keep, keep)]
    labels = labels[keep].reset_index(drop=True)
    n = len(labels)
    unique = labels.unique().tolist()
    g = len(unique)
    if n < 3 or g < 2 or n <= g:
        return {"n": n, "groups": g, "F": np.nan, "R2": np.nan, "p_perm": np.nan, "permutations": 0}

    def pseudo_f(current: pd.Series) -> tuple[float, float]:
        total_ss = float((d**2).sum() / (2 * n))
        within_ss = 0.0
        for label in current.unique():
            idx = np.where(current.to_numpy() == label)[0]
            if len(idx) <= 1:
                continue
            sub = d[np.ix_(idx, idx)]
            within_ss += float((sub**2).sum() / (2 * len(idx)))
        among_ss = max(0.0, total_ss - within_ss)
        df_among = g - 1
        df_within = n - g
        f_value = (among_ss / df_among) / (within_ss / df_within) if within_ss > 0 and df_within > 0 else np.nan
        r2 = among_ss / total_ss if total_ss > 0 else np.nan
        return float(f_value), float(r2)

    observed_f, observed_r2 = pseudo_f(labels)
    rng = np.random.default_rng(seed)
    count = 0
    perms = 0
    labels_arr = labels.to_numpy()
    for _ in range(n_perm):
        permuted = pd.Series(rng.permutation(labels_arr))
        f_perm, _r2_perm = pseudo_f(permuted)
        if np.isfinite(f_perm):
            perms += 1
            if f_perm >= observed_f:
                count += 1
    p_value = (count + 1) / (perms + 1) if perms else np.nan
    return {
        "n": int(n),
        "groups": int(g),
        "F": observed_f,
        "R2": observed_r2,
        "p_perm": float(p_value),
        "permutations": int(perms),
        "group_sizes": labels.value_counts().sort_index().to_dict(),
    }


def permdisp(distance: np.ndarray, groups: pd.Series, n_perm: int = 999, seed: int = 20260625) -> dict:
    d = np.asarray(distance, dtype=float)
    labels = pd.Series(groups).astype(str).reset_index(drop=True)
    valid_groups = labels.value_counts()
    keep_labels = valid_groups[valid_groups >= 2].index
    keep = labels.isin(keep_labels).to_numpy()
    d = d[np.ix_(keep, keep)]
    labels = labels[keep].reset_index(drop=True)
    coords = _pcoa_coordinates(d)
    n = len(labels)
    unique = labels.unique().tolist()
    g = len(unique)
    if n < 3 or g < 2 or n <= g:
        return {"n": n, "groups": g, "F": np.nan, "p_perm": np.nan, "permutations": 0}

    def distances_to_centroid(current: pd.Series) -> np.ndarray:
        values = np.zeros(n, dtype=float)
        arr = current.to_numpy()
        for label in current.unique():
            idx = np.where(arr == label)[0]
            centroid = coords[idx].mean(axis=0)
            values[idx] = np.sqrt(((coords[idx] - centroid) ** 2).sum(axis=1))
        return values

    def anova_f(current: pd.Series) -> float:
        values = distances_to_centroid(current)
        grand = float(values.mean())
        ss_between = 0.0
        ss_within = 0.0
        for label in current.unique():
            group_values = values[current.to_numpy() == label]
            mean_group = float(group_values.mean())
            ss_between += len(group_values) * (mean_group - grand) ** 2
            ss_within += float(((group_values - mean_group) ** 2).sum())
        return (ss_between / (g - 1)) / (ss_within / (n - g)) if ss_within > 0 and n > g else np.nan

    observed_f = float(anova_f(labels))
    rng = np.random.default_rng(seed)
    count = 0
    perms = 0
    labels_arr = labels.to_numpy()
    for _ in range(n_perm):
        permuted = pd.Series(rng.permutation(labels_arr))
        f_perm = anova_f(permuted)
        if np.isfinite(f_perm):
            perms += 1
            if f_perm >= observed_f:
                count += 1
    p_value = (count + 1) / (perms + 1) if perms else np.nan
    return {
        "n": int(n),
        "groups": int(g),
        "F": observed_f,
        "p_perm": float(p_value),
        "permutations": int(perms),
        "group_sizes": labels.value_counts().sort_index().to_dict(),
    }


def run_nmds_and_tests(matrix: pd.DataFrame, metadata: pd.DataFrame, n_perm: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    positive = metadata["captura_quantitativa"].to_numpy(dtype=bool)
    ord_matrix = matrix.loc[positive].copy()
    ord_meta = metadata.loc[positive].reset_index(drop=True).copy()
    distance = _bray_curtis_matrix(ord_matrix.to_numpy(dtype=float))

    if len(ord_meta) >= 3:
        nmds = MDS(
            n_components=2,
            metric=False,
            dissimilarity="precomputed",
            random_state=seed,
            n_init=12,
            max_iter=3000,
            eps=1e-9,
            normalized_stress="auto",
        )
        coords = nmds.fit_transform(distance)
        stress = float(getattr(nmds, "stress_", np.nan))
    else:
        coords = np.zeros((len(ord_meta), 2))
        stress = np.nan

    scores = ord_meta.copy()
    scores["NMDS1"] = coords[:, 0] if len(coords) else []
    scores["NMDS2"] = coords[:, 1] if len(coords) else []
    scores["stress"] = stress

    permanova_rows = []
    permdisp_rows = []
    for factor, label in [("estacao_rotulo", "Estação seca x chuvosa"), ("ano", "Ano")]:
        groups = ord_meta[factor].astype(str)
        perm = permanova(distance, groups, n_perm=n_perm, seed=seed)
        perm.update({"fator": factor, "analise": label, "base": "amostras com captura quantitativa"})
        permanova_rows.append(perm)
        disp = permdisp(distance, groups, n_perm=n_perm, seed=seed + 17)
        disp.update({"fator": factor, "analise": label, "base": "amostras com captura quantitativa"})
        permdisp_rows.append(disp)

    return scores, pd.DataFrame(permanova_rows), pd.DataFrame(permdisp_rows)


def campaign_indicators(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    lcbd: pd.DataFrame,
    species_origin: pd.DataFrame,
) -> pd.DataFrame:
    non_native_keys = set(species_origin.loc[species_origin["nao_nativa"], "species_key"].tolist())
    non_native_species = [col for col in matrix.columns if _normalize_text(col) in non_native_keys]
    rows = []
    for campaign, meta in metadata.groupby("nome_campanha", sort=False):
        ids = meta["sample_id"].tolist()
        mat = matrix.loc[ids]
        vec = mat.sum(axis=0).to_numpy(dtype=float)
        cpuen_total = float(vec.sum())
        exotic_cpuen = float(mat[non_native_species].sum().sum()) if non_native_species else 0.0
        lcbd_campaign = lcbd[lcbd["nome_campanha"] == campaign]
        rows.append(
            {
                "nome_campanha": campaign,
                "campanha_curta": _campaign_short(campaign),
                "ano": int(meta["ano"].dropna().iloc[0]) if meta["ano"].notna().any() else np.nan,
                "estacao": str(meta["estacao"].iloc[0]),
                "estacao_rotulo": str(meta["estacao_rotulo"].iloc[0]),
                "ordem_campanha": int(meta["ordem_campanha"].iloc[0]),
                "riqueza_total": int((vec > 0).sum()),
                "CPUEn_total": cpuen_total,
                "Shannon_H": _shannon(vec),
                "Pielou_J": _pielou(vec),
                "CPUEn_nao_nativa": exotic_cpuen,
                "perc_CPUEn_nao_nativa": (exotic_cpuen / cpuen_total * 100.0) if cpuen_total > 0 else 0.0,
                "LCBD_medio": float(lcbd_campaign["LCBD"].mean()) if not lcbd_campaign.empty else np.nan,
                "LCBD_max": float(lcbd_campaign["LCBD"].max()) if not lcbd_campaign.empty else np.nan,
                "pontos_com_captura": int(meta["captura_quantitativa"].sum()),
                "pontos_monitorados": int(len(meta)),
            }
        )
    return pd.DataFrame(rows)


def _linear_slope(values: pd.Series) -> float:
    y = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    valid = np.isfinite(y)
    if valid.sum() < 2:
        return 0.0
    return float(np.polyfit(x[valid], y[valid], 1)[0])


def build_alert_matrix(indicators: pd.DataFrame, permanova_df: pd.DataFrame, lcbd: pd.DataFrame) -> pd.DataFrame:
    recent = indicators.tail(4)
    prev = indicators.iloc[:-4] if len(indicators) > 4 else indicators
    lcbd_positive = lcbd["LCBD"][lcbd["LCBD"] > 0]
    lcbd_p90 = float(lcbd_positive.quantile(0.90)) if not lcbd_positive.empty else np.nan
    lcbd_peaks = lcbd[lcbd["LCBD"] >= lcbd_p90].copy() if np.isfinite(lcbd_p90) else pd.DataFrame()
    recurrent_lcbd_points = (
        lcbd_peaks.groupby("nome_ponto")["nome_campanha"].nunique().loc[lambda s: s >= 3].index.tolist()
        if not lcbd_peaks.empty
        else []
    )

    richness_slope = _linear_slope(indicators["riqueza_total"])
    cpuen_slope = _linear_slope(indicators["CPUEn_total"])
    shannon_slope = _linear_slope(indicators["Shannon_H"])
    exotic_slope = _linear_slope(indicators["perc_CPUEn_nao_nativa"])

    def _class_richness() -> str:
        if (
            richness_slope < 0
            and cpuen_slope < 0
            and recent["riqueza_total"].mean() < prev["riqueza_total"].quantile(0.25)
        ):
            return "Perturbação provável"
        if recent["riqueza_total"].min() < indicators["riqueza_total"].quantile(0.25) or cpuen_slope < 0:
            return "Atenção"
        return "Baixo risco"

    def _class_diversity() -> str:
        if shannon_slope < 0 and recent["Shannon_H"].mean() < prev["Shannon_H"].quantile(0.25):
            return "Perturbação provável"
        if recent["Shannon_H"].min() < indicators["Shannon_H"].quantile(0.25):
            return "Atenção"
        return "Baixo risco"

    def _class_permanova() -> str:
        p_values = pd.to_numeric(permanova_df.get("p_perm"), errors="coerce")
        if (p_values <= 0.05).any():
            return "Perturbação provável"
        if (p_values <= 0.10).any():
            return "Atenção"
        return "Baixo risco"

    def _class_lcbd() -> str:
        if recurrent_lcbd_points:
            return "Perturbação provável"
        if not lcbd_peaks.empty:
            return "Atenção"
        return "Baixo risco"

    def _class_exotics() -> str:
        recent_share = float(recent["perc_CPUEn_nao_nativa"].mean())
        prev_share = float(prev["perc_CPUEn_nao_nativa"].median())
        if exotic_slope > 0 and recent_share > max(10.0, prev_share * 1.5):
            return "Perturbação provável"
        if indicators["perc_CPUEn_nao_nativa"].max() > 0:
            return "Atenção"
        return "Baixo risco"

    rows = [
        {
            "Evidencia": "Riqueza/CPUEn",
            "Baixo risco": "estável",
            "Atenção": "oscilação pontual",
            "Perturbação provável": "queda persistente",
            "Classe preliminar": _class_richness(),
            "Leitura exploratória": (
                f"slope riqueza={richness_slope:.3f}; slope CPUEn={cpuen_slope:.3f}; "
                f"média recente riqueza={recent['riqueza_total'].mean():.2f}"
            ),
        },
        {
            "Evidencia": "Shannon/Pielou",
            "Baixo risco": "estável",
            "Atenção": "dominância pontual",
            "Perturbação provável": "dominância recorrente",
            "Classe preliminar": _class_diversity(),
            "Leitura exploratória": (
                f"slope Shannon={shannon_slope:.3f}; menor Shannon={max(0.0, indicators['Shannon_H'].min()):.3f}"
            ),
        },
        {
            "Evidencia": "NMDS/PERMANOVA",
            "Baixo risco": "sem separação",
            "Atenção": "separação fraca",
            "Perturbação provável": "separação clara",
            "Classe preliminar": _class_permanova(),
            "Leitura exploratória": "; ".join(
                f"{row['analise']}: p={row['p_perm']:.3f}, R2={row['R2']:.3f}"
                for _, row in permanova_df.iterrows()
                if pd.notna(row.get("p_perm"))
            ),
        },
        {
            "Evidencia": "LCBD",
            "Baixo risco": "baixo",
            "Atenção": "pico isolado",
            "Perturbação provável": "picos recorrentes",
            "Classe preliminar": _class_lcbd(),
            "Leitura exploratória": (
                f"p90 LCBD={lcbd_p90:.3f}; pontos recorrentes={', '.join(recurrent_lcbd_points) or 'nenhum'}"
            ),
        },
        {
            "Evidencia": "Exóticas",
            "Baixo risco": "raras",
            "Atenção": "aumento pontual",
            "Perturbação provável": "aumento persistente",
            "Classe preliminar": _class_exotics(),
            "Leitura exploratória": (
                f"max %CPUEn não nativa={indicators['perc_CPUEn_nao_nativa'].max():.1f}; "
                f"slope={exotic_slope:.3f}"
            ),
        },
    ]
    out = pd.DataFrame(rows)
    out["Nota"] = "Triagem exploratória; não representa índice novo nem conclusão causal."
    return out


def _theme_colors(theme: dict) -> tuple[str, str, str]:
    primary = str(theme.get("primary_hex", "#002060"))
    secondary = str(theme.get("secondary_hex", "#5B9BD5"))
    highlight = str(theme.get("highlight_hex", "#1F4E79"))
    return primary, secondary, highlight


def plot_lcbd_heatmap(lcbd: pd.DataFrame, out_png: Path, theme: dict) -> None:
    primary, secondary, _highlight = _theme_colors(theme)
    campaigns = sorted(lcbd["nome_campanha"].unique().tolist(), key=_campaign_sort_key)
    points = sorted(lcbd["nome_ponto"].unique().tolist(), key=_point_sort_key)
    table = (
        lcbd.pivot_table(index="nome_ponto", columns="nome_campanha", values="LCBD", aggfunc="mean", fill_value=0)
        .reindex(index=points, columns=campaigns, fill_value=0)
    )
    values = table.to_numpy(dtype=float)
    vmax = max(float(np.nanmax(values)), 0.01)
    cmap = mcolors.LinearSegmentedColormap.from_list("geoarc_lcbd", ["#F7F7F7", "#D9E6F2", secondary, primary])
    fig, ax = plt.subplots(figsize=(12.6, 6.5), dpi=int(theme.get("dpi", 600)))
    im = ax.imshow(values, aspect="auto", cmap=cmap, vmin=0, vmax=vmax)
    ax.set_title("Heatmap LCBD por ponto e campanha", loc="left", fontsize=14, fontweight="bold")
    ax.set_ylabel("Ponto amostral", fontsize=11)
    ax.set_xlabel("Campanha", fontsize=11)
    ax.set_yticks(np.arange(len(points)))
    ax.set_yticklabels(points, fontsize=10)
    ax.set_xticks(np.arange(len(campaigns)))
    ax.set_xticklabels([_campaign_short(c) for c in campaigns], rotation=90, ha="center", fontsize=10)
    ax.set_xticks(np.arange(-0.5, len(campaigns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(points), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(1, len(campaigns)):
        if _campaign_year(campaigns[i]) != _campaign_year(campaigns[i - 1]):
            ax.axvline(i - 0.5, color="#606060", linewidth=1.0)

    threshold = np.nanquantile(values[values > 0], 0.75) if np.any(values > 0) else math.inf
    for row_idx, point in enumerate(points):
        for col_idx, campaign in enumerate(campaigns):
            value = float(table.loc[point, campaign])
            if value >= threshold:
                color = "white" if value > vmax * 0.55 else "black"
                ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", fontsize=7.5, color=color)

    cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.025, pad=0.018)
    cbar.set_label("LCBD", fontsize=10)
    ax.text(
        0,
        -0.22,
        "Valores destacados correspondem ao quartil superior de LCBD. Pontos sem captura foram mantidos como zeros na matriz.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#404040",
    )
    fig.tight_layout(rect=[0.02, 0.08, 1, 1])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def _add_ellipse(ax, x: np.ndarray, y: np.ndarray, color: str) -> None:
    if len(x) < 3:
        return
    cov = np.cov(x, y)
    if not np.isfinite(cov).all():
        return
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    if np.any(vals <= 0):
        return
    angle = math.degrees(math.atan2(vecs[1, 0], vecs[0, 0]))
    width, height = 2 * np.sqrt(vals)
    ellipse = Ellipse(
        (float(np.mean(x)), float(np.mean(y))),
        width=width,
        height=height,
        angle=angle,
        facecolor=color,
        edgecolor=color,
        alpha=0.12,
        linewidth=1.2,
    )
    ax.add_patch(ellipse)


def plot_nmds(scores: pd.DataFrame, permanova_df: pd.DataFrame, out_png: Path, theme: dict) -> None:
    primary, secondary, highlight = _theme_colors(theme)
    season_colors = {"Chuvosa": primary, "Seca": secondary, "N.D.": "#808080"}
    years = sorted(scores["ano"].dropna().astype(int).unique().tolist())
    year_colors = dict(zip(years, plt.cm.viridis(np.linspace(0.1, 0.9, max(len(years), 1))), strict=False))
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.8), dpi=int(theme.get("dpi", 600)), sharex=True, sharey=True)

    ax = axes[0]
    for season, group in scores.groupby("estacao_rotulo", sort=False):
        color = season_colors.get(str(season), highlight)
        ax.scatter(group["NMDS1"], group["NMDS2"], s=34, color=color, edgecolor="white", linewidth=0.4, alpha=0.88, label=season)
        _add_ellipse(ax, group["NMDS1"].to_numpy(), group["NMDS2"].to_numpy(), color)
    ax.set_title("A) Estação", loc="left", fontsize=12, fontweight="bold")
    ax.legend(frameon=False, fontsize=9)

    ax = axes[1]
    for year, group in scores.groupby("ano", sort=True):
        year_int = int(year)
        color = year_colors.get(year_int, (0.2, 0.2, 0.2, 1.0))
        label = f"{year_int}" + (" (2 campanhas)" if year_int == 2026 else "")
        ax.scatter(group["NMDS1"], group["NMDS2"], s=34, color=color, edgecolor="white", linewidth=0.4, alpha=0.88, label=label)
        _add_ellipse(ax, group["NMDS1"].to_numpy(), group["NMDS2"].to_numpy(), color)
    ax.set_title("B) Ano", loc="left", fontsize=12, fontweight="bold")
    ax.legend(frameon=False, fontsize=8, ncol=1)

    for ax in axes:
        ax.axhline(0, color="#D0D0D0", linewidth=0.8)
        ax.axvline(0, color="#D0D0D0", linewidth=0.8)
        ax.set_xlabel("NMDS1", fontsize=10)
        ax.set_ylabel("NMDS2", fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, color="#E6E6E6", linewidth=0.7)

    stress = scores["stress"].dropna().iloc[0] if scores["stress"].notna().any() else np.nan
    perm_txt = []
    for _, row in permanova_df.iterrows():
        perm_txt.append(f"{row['analise']}: PERMANOVA p={row['p_perm']:.3f}, R2={row['R2']:.3f}")
    fig.suptitle("NMDS Bray-Curtis sobre CPUEn por campanha-ponto", x=0.02, ha="left", fontsize=14, fontweight="bold")
    fig.text(
        0.02,
        0.02,
        f"Amostras sem captura excluídas da ordenação. Stress={stress:.3f}. " + " | ".join(perm_txt),
        ha="left",
        va="bottom",
        fontsize=8.8,
        color="#404040",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.94])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def plot_indicator_panel(indicators: pd.DataFrame, out_png: Path, theme: dict) -> None:
    primary, secondary, highlight = _theme_colors(theme)
    season_colors = {"CH": primary, "SC": secondary, "ND": highlight}
    metrics = [
        ("riqueza_total", "Riqueza total"),
        ("CPUEn_total", "CPUEn total"),
        ("Shannon_H", "Shannon (H')"),
        ("perc_CPUEn_nao_nativa", "CPUEn não nativa (%)"),
        ("LCBD_max", "LCBD máximo"),
    ]
    campaigns = indicators["nome_campanha"].tolist()
    x = np.arange(len(campaigns))
    fig, axes = plt.subplots(len(metrics), 1, figsize=(12.5, 9.6), dpi=int(theme.get("dpi", 600)), sharex=True)
    for ax, (col, ylabel) in zip(axes, metrics, strict=True):
        y = pd.to_numeric(indicators[col], errors="coerce").to_numpy(dtype=float)
        ax.plot(x, y, color="#606060", linewidth=1.0, zorder=1)
        for season, group in indicators.groupby("estacao", sort=False):
            idx = group.index.to_numpy()
            ax.scatter(idx, group[col], s=42, color=season_colors.get(season, highlight), edgecolor="white", linewidth=0.5, zorder=2)
        mean = np.nanmean(y)
        ax.axhline(mean, color="#A0A0A0", linestyle="--", linewidth=0.8)
        for i in range(1, len(campaigns)):
            if indicators.loc[i, "ano"] != indicators.loc[i - 1, "ano"]:
                ax.axvline(i - 0.5, color="#D0D0D0", linewidth=0.8)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(True, axis="y", color="#E6E6E6", linewidth=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_title("Painel temporal de indicadores da assembleia", loc="left", fontsize=14, fontweight="bold")
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(indicators["campanha_curta"].tolist(), rotation=90, fontsize=10)
    axes[-1].set_xlabel("Campanha", fontsize=10)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=season_colors["CH"], markeredgecolor="white", label="Chuvosa"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=season_colors["SC"], markeredgecolor="white", label="Seca"),
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.98, 0.985), frameon=False, ncol=2, fontsize=9)
    fig.text(
        0.02,
        0.015,
        "2026 possui somente duas campanhas no recorte atual. Linhas tracejadas indicam média da série por indicador. LCBD médio consta na tabela; o painel usa LCBD máximo por ser informativo.",
        ha="left",
        fontsize=8.8,
        color="#404040",
    )
    fig.tight_layout(rect=[0.02, 0.05, 1, 0.98])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def plot_beta_partition(seasonal: pd.DataFrame, consecutive: pd.DataFrame, out_png: Path, theme: dict) -> None:
    primary, secondary, _highlight = _theme_colors(theme)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9), dpi=int(theme.get("dpi", 600)), sharey=True)
    specs = [
        (axes[0], seasonal, "ano", "A) Chuvosa x seca por ano"),
        (axes[1], consecutive, "par_anos", "B) Anos consecutivos"),
    ]
    for ax, df, label_col, title in specs:
        if df.empty:
            ax.set_axis_off()
            ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
            ax.text(0.5, 0.5, "Sem comparacoes calculaveis", ha="center", va="center")
            continue
        x = np.arange(len(df))
        turnover = pd.to_numeric(df["turnover_beta_sim"], errors="coerce").fillna(0).to_numpy()
        nestedness = pd.to_numeric(df["nestedness_beta_nes"], errors="coerce").fillna(0).to_numpy()
        ax.bar(x, turnover, color=primary, label="Turnover")
        ax.bar(x, nestedness, bottom=turnover, color=secondary, label="Nestedness")
        ax.set_xticks(x)
        ax.set_xticklabels(df[label_col].astype(str).tolist(), rotation=45, ha="right", fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
        ax.grid(True, axis="y", color="#E6E6E6", linewidth=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("Beta-Sorensen particionada", fontsize=10)
    axes[1].legend(frameon=False, loc="upper right", fontsize=9)
    fig.suptitle("Beta diversidade particionada por presença-ausência", x=0.02, ha="left", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def write_excel_outputs(
    output_dir: Path,
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    lcbd: pd.DataFrame,
    scores: pd.DataFrame,
    permanova_df: pd.DataFrame,
    permdisp_df: pd.DataFrame,
    indicators: pd.DataFrame,
    alert: pd.DataFrame,
    beta_seasonal: pd.DataFrame,
    beta_consecutive: pd.DataFrame,
) -> dict[str, str]:
    paths = {
        "community_matrix": output_dir / "15_matriz_comunidade_cpuen_ponto_campanha_especie.xlsx",
        "lcbd": output_dir / "15_df_lcbd_ponto_campanha_ictiofauna.xlsx",
        "nmds": output_dir / "16_df_nmds_permanova_ictiofauna.xlsx",
        "panel": output_dir / "17_df_painel_indicadores_assembleia_ictiofauna.xlsx",
        "beta": output_dir / "18_df_beta_particionada_ictiofauna.xlsx",
    }
    matrix_out = matrix.copy()
    matrix_out.insert(0, "sample_id", matrix.index)
    matrix_out = matrix_out.merge(metadata, on="sample_id", how="left")
    with pd.ExcelWriter(paths["community_matrix"], engine="openpyxl") as writer:
        matrix_out.to_excel(writer, sheet_name="matriz_cpuen", index=False)
        metadata.to_excel(writer, sheet_name="metadados_amostras", index=False)
    with pd.ExcelWriter(paths["lcbd"], engine="openpyxl") as writer:
        lcbd.to_excel(writer, sheet_name="LCBD_ponto_campanha", index=False)
    with pd.ExcelWriter(paths["nmds"], engine="openpyxl") as writer:
        scores.to_excel(writer, sheet_name="NMDS_scores", index=False)
        permanova_df.to_excel(writer, sheet_name="PERMANOVA", index=False)
        permdisp_df.to_excel(writer, sheet_name="PERMDISP", index=False)
    with pd.ExcelWriter(paths["panel"], engine="openpyxl") as writer:
        indicators.to_excel(writer, sheet_name="indicadores_campanha", index=False)
        alert.to_excel(writer, sheet_name="matriz_alerta", index=False)
    with pd.ExcelWriter(paths["beta"], engine="openpyxl") as writer:
        beta_seasonal.to_excel(writer, sheet_name="seca_chuvosa_por_ano", index=False)
        beta_consecutive.to_excel(writer, sheet_name="anos_consecutivos", index=False)
    return {key: str(path) for key, path in paths.items()}


def write_readme(output_dir: Path, summary: dict) -> Path:
    path = output_dir / "README_exploratorio_geoarc001_assembleia.md"
    lines = [
        "# GEOARC001 - Avaliação integrada exploratória da assembleia",
        "",
        "Pacote exploratório gerado para revisão técnica conjunta. Estes produtos não substituem os produtos oficiais do relatório e não representam conclusão causal.",
        "",
        "## Escopo aprovado",
        "",
        "- Estação: seca x chuvosa, usando `SC` e `CH` no código da campanha.",
        "- Ano: 2022 a 2026; 2026 possui somente duas campanhas no recorte atual.",
        "- Área de influência: não aplicada, pois não há de-para legal validado para ADA/AID/controle.",
        "- LCBD e painel temporal: aprovados como exploratórios.",
        "",
        "## Produtos",
        "",
        "- `15_grafico_heatmap_lcbd_ponto_campanha_ictiofauna.png`",
        "- `16_grafico_nmds_braycurtis_estacao_ano_ictiofauna.png`",
        "- `17_grafico_painel_temporal_indicadores_assembleia_ictiofauna.png`",
        "- `18_grafico_beta_particionada_ictiofauna.png`",
        "- Planilhas `.xlsx` pareadas com as tabelas de apoio.",
        "",
        "## Notas metodológicas",
        "",
        "- Base quantitativa: CPUEn por campanha, ponto e especie.",
        "- NMDS/PERMANOVA: Bray-Curtis sobre CPUEn; amostras sem captura foram excluídas da ordenação para evitar compartilhamento de ausências.",
        "- LCBD: calculado por campanha com transformação de Hellinger, mantendo todos os pontos monitorados.",
        "- Beta particionada: presença-ausência com beta-Sorensen, turnover e nestedness.",
        "- Matriz de alerta: triagem interpretativa, sem criar índice novo.",
        "",
        "## Resumo automático",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera pacote exploratorio de estabilidade da assembleia GEOARC001.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Planilha de migracao aprovada do GEOARC001.")
    parser.add_argument("--composition", default=str(DEFAULT_COMPOSITION), help="Tabela de composicao com atributos ecologicos.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Diretório de saída exploratória.")
    parser.add_argument("--client", default="geoarc001_arcelor")
    parser.add_argument("--n-perm", type=int, default=999)
    parser.add_argument("--seed", type=int, default=20260625)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", args.client)

    tables = read_sources(Path(args.source), Path(args.composition))
    species_origin = build_species_origin(tables.composicao)
    matrix, metadata, counts = build_community(tables)
    lcbd = calculate_lcbd(matrix, metadata)
    scores, permanova_df, permdisp_df = run_nmds_and_tests(matrix, metadata, n_perm=args.n_perm, seed=args.seed)
    beta_seasonal, beta_consecutive = calculate_beta_tables(matrix, metadata)
    indicators = campaign_indicators(matrix, metadata, lcbd, species_origin)
    alert = build_alert_matrix(indicators, permanova_df, lcbd)

    plot_lcbd_heatmap(lcbd, output_dir / "15_grafico_heatmap_lcbd_ponto_campanha_ictiofauna.png", theme)
    plot_nmds(scores, permanova_df, output_dir / "16_grafico_nmds_braycurtis_estacao_ano_ictiofauna.png", theme)
    plot_indicator_panel(indicators, output_dir / "17_grafico_painel_temporal_indicadores_assembleia_ictiofauna.png", theme)
    plot_beta_partition(beta_seasonal, beta_consecutive, output_dir / "18_grafico_beta_particionada_ictiofauna.png", theme)
    excel_paths = write_excel_outputs(
        output_dir=output_dir,
        matrix=matrix,
        metadata=metadata,
        lcbd=lcbd,
        scores=scores,
        permanova_df=permanova_df,
        permdisp_df=permdisp_df,
        indicators=indicators,
        alert=alert,
        beta_seasonal=beta_seasonal,
        beta_consecutive=beta_consecutive,
    )

    summary = {
        "source": str(Path(args.source)),
        "composition": str(Path(args.composition)),
        "output_dir": str(output_dir),
        "campaigns": int(metadata["nome_campanha"].nunique()),
        "years": sorted(int(x) for x in metadata["ano"].dropna().unique().tolist()),
        "points": int(metadata["nome_ponto"].nunique()),
        "samples_total": int(len(metadata)),
        "samples_with_capture": int(metadata["captura_quantitativa"].sum()),
        "species": int(matrix.shape[1]),
        "records_quantitative": int(len(counts)),
        "nmds_samples": int(len(scores)),
        "n_permutations_requested": int(args.n_perm),
        "permanova": permanova_df[["analise", "n", "groups", "F", "R2", "p_perm"]].to_dict("records"),
        "alert_matrix": alert[["Evidencia", "Classe preliminar"]].to_dict("records"),
        "excel_outputs": excel_paths,
    }
    (output_dir / "manifesto_exploratorio_geoarc001_assembleia.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    readme = write_readme(output_dir, summary)
    summary["readme"] = str(readme)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
