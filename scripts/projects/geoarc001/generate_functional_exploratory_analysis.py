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
DEFAULT_TRAITS = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\Exploratorio_assembleia_ictiofauna"
    r"\tabela_especie_atributos_funcionais_geoarc001_teste.xlsx"
)
DEFAULT_OUTPUT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\Exploratorio_assembleia_ictiofauna"
)

SEASON_LABELS = {"CH": "Chuvosa", "SC": "Seca", "ND": "N.D."}
ATTRIBUTES = [
    ("Habitat_funcional", "Habitat funcional"),
    ("Preferencia_correnteza", "Preferência por correnteza"),
    ("Guilda_trofica", "Guilda trófica"),
    ("Porte_corporal", "Porte corporal"),
    ("Sensibilidade_funcional", "Sensibilidade ambiental"),
]
COMPOSITION_ATTRIBUTES = [
    "Preferencia_correnteza",
    "Habitat_funcional",
    "Sensibilidade_funcional",
    "Guilda_trofica",
]
CATEGORY_PRIORITY = {
    "Habitat_funcional": ["bentônico", "nectônico", "bentopelágico", "demersal", "sem classificação"],
    "Preferencia_correnteza": ["reofílico", "intermediário", "limnofílico", "generalista", "sem classificação"],
    "Guilda_trofica": [
        "algívoro",
        "detritívoro",
        "herbívoro",
        "insetívoro",
        "invertívoro",
        "onívoro",
        "perifitívoro",
        "piscívoro",
        "planctívoro",
        "sem classificação",
    ],
    "Porte_corporal": ["pequeno", "médio", "grande", "sem classificação"],
    "Sensibilidade_funcional": ["sensível", "intermediária", "tolerante", "sem classificação"],
}
FUNCTIONAL_GROUP_DEFINITIONS = [
    {
        "codigo": "especialistas_loticos_sensiveis",
        "rotulo": "Especialistas lóticos sensíveis",
        "criterio": "Preferência por correnteza = reofílico; sensibilidade = sensível.",
    },
    {
        "codigo": "raspadores_bentonicos_reofilicos",
        "rotulo": "Raspadores/bentônicos reofílicos",
        "criterio": "Guilda trófica = perifitívoro; habitat = bentônico; preferência por correnteza = reofílico.",
    },
    {
        "codigo": "generalistas_tolerantes",
        "rotulo": "Generalistas tolerantes",
        "criterio": "Guilda trófica = onívoro; sensibilidade = tolerante.",
    },
    {
        "codigo": "predadores",
        "rotulo": "Predadores",
        "criterio": "Guilda trófica = piscívoro.",
    },
]


@dataclass(frozen=True)
class SourceTables:
    pontos_campanhas: pd.DataFrame
    esforcos: pd.DataFrame
    resultados: pd.DataFrame
    atributos: pd.DataFrame


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


def _theme_colors(theme: dict) -> tuple[str, str, str]:
    primary = str(theme.get("primary_hex", "#2E6F95"))
    secondary = str(theme.get("secondary_hex", "#E07A5F"))
    highlight = str(theme.get("highlight_hex", "#3D5A80"))
    return primary, secondary, highlight


def _attribute_label(attribute: str) -> str:
    return dict(ATTRIBUTES).get(attribute, attribute)


def _category_sort_key(attribute: str, category: str) -> tuple[int, str]:
    priorities = [_normalize_text(x) for x in CATEGORY_PRIORITY.get(attribute, [])]
    norm = _normalize_text(category)
    try:
        rank = priorities.index(norm)
    except ValueError:
        rank = 1000
    return rank, str(category)


def _ordered_categories(atributos: pd.DataFrame, attribute: str) -> list[str]:
    values = [
        str(x).strip()
        for x in atributos[attribute].dropna().tolist()
        if str(x).strip() and str(x).strip().lower() != "nan"
    ]
    unique = sorted(set(values), key=lambda item: _category_sort_key(attribute, item))
    return unique or ["sem classificação"]


def _percentage(value: float, total: float) -> float:
    return float(value / total * 100.0) if total > 0 else 0.0


def _linear_slope(values: pd.Series) -> float:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    ok = np.isfinite(arr)
    if ok.sum() < 2:
        return float("nan")
    x = np.arange(len(arr), dtype=float)[ok]
    y = arr[ok]
    return float(np.polyfit(x, y, 1)[0])


def read_sources(source: Path, traits: Path) -> SourceTables:
    if not source.exists():
        raise FileNotFoundError(f"Planilha de entrada não encontrada: {source}")
    if not traits.exists():
        raise FileNotFoundError(f"Planilha de atributos funcionais não encontrada: {traits}")
    return SourceTables(
        pontos_campanhas=pd.read_excel(source, sheet_name="Pontos_e_Campanhas"),
        esforcos=pd.read_excel(source, sheet_name="Metadados_Esforco"),
        resultados=pd.read_excel(source, sheet_name="Resultados_Ictiofauna"),
        atributos=pd.read_excel(traits, sheet_name="atributos_funcionais"),
    )


def prepare_traits(atributos: pd.DataFrame) -> pd.DataFrame:
    traits = atributos.copy()
    if "Nome Cientifico" not in traits.columns and "Especie" in traits.columns:
        traits["Nome Cientifico"] = traits["Especie"]
    required = ["Nome Cientifico", *[col for col, _label in ATTRIBUTES]]
    missing = [col for col in required if col not in traits.columns]
    if missing:
        raise ValueError(f"Colunas ausentes na tabela de atributos: {', '.join(missing)}")

    if "Aplicar_no_teste" in traits.columns:
        apply_flag = traits["Aplicar_no_teste"].map(_normalize_text)
        selected = apply_flag.isin(["sim", "s", "yes", "y", "true", "1"])
        if selected.any():
            traits = traits[selected].copy()

    traits["nome_cientifico"] = traits["Nome Cientifico"].astype(str).str.strip()
    traits["species_key"] = traits["nome_cientifico"].map(_normalize_text)
    for col, _label in ATTRIBUTES:
        traits[col] = traits[col].fillna("sem classificação").astype(str).str.strip()
        traits.loc[traits[col].isin(["", "nan", "None"]), col] = "sem classificação"
    return traits.drop_duplicates("species_key").copy()


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
    counts["sample_id"] = counts["nome_campanha"] + " | " + counts["nome_ponto"]
    counts["species_key"] = counts["nome_cientifico"].map(_normalize_text)

    campaigns = sorted(pc["nome_campanha"].dropna().unique().tolist(), key=_campaign_sort_key)
    points = sorted(pc["nome_ponto"].dropna().unique().tolist(), key=_point_sort_key)
    sample_grid = pd.DataFrame(
        [{"nome_campanha": campaign, "nome_ponto": point} for campaign in campaigns for point in points]
    )
    if not campaign_meta.empty:
        sample_grid = sample_grid.merge(campaign_meta, on="nome_campanha", how="left")
    if not point_meta.empty:
        sample_grid = sample_grid.merge(point_meta, on="nome_ponto", how="left")
    sample_grid["sample_id"] = sample_grid["nome_campanha"] + " | " + sample_grid["nome_ponto"]
    sample_grid["campanha_curta"] = sample_grid["nome_campanha"].map(_campaign_short)
    sample_grid["ordem_campanha"] = sample_grid["nome_campanha"].map(_campaign_number)
    sample_grid["ano"] = sample_grid["nome_campanha"].map(_campaign_year)
    sample_grid["estacao"] = sample_grid["nome_campanha"].map(_campaign_season)
    if "Ano_Temporal" in sample_grid.columns:
        sample_grid["ano"] = pd.to_numeric(sample_grid["Ano_Temporal"], errors="coerce").combine_first(
            pd.to_numeric(sample_grid["ano"], errors="coerce")
        )
    if "Periodo_Hidrologico" in sample_grid.columns:
        season_override = sample_grid["Periodo_Hidrologico"].astype(str).str.strip().str.upper()
        sample_grid.loc[season_override.isin(["CH", "SC"]), "estacao"] = season_override[season_override.isin(["CH", "SC"])]
    sample_grid["estacao_rotulo"] = sample_grid["estacao"].map(SEASON_LABELS).fillna("N.D.")
    sample_grid = sample_grid.merge(effort_total, on=["nome_campanha", "nome_ponto"], how="left")

    species = sorted(counts["nome_cientifico"].dropna().unique().tolist(), key=_normalize_text)
    matrix = counts.pivot_table(
        index="sample_id", columns="nome_cientifico", values="CPUEn", aggfunc="sum", fill_value=0
    )
    matrix = matrix.reindex(index=sample_grid["sample_id"].tolist(), columns=species, fill_value=0.0)
    matrix.index.name = "sample_id"

    metadata = sample_grid.copy()
    metadata["CPUEn_total"] = matrix.sum(axis=1).to_numpy(dtype=float)
    metadata["riqueza"] = (matrix.to_numpy(dtype=float) > 0).sum(axis=1).astype(int)
    metadata["captura_quantitativa"] = metadata["CPUEn_total"] > 0
    return matrix, metadata, counts


def build_functional_profiles(
    counts: pd.DataFrame, metadata: pd.DataFrame, traits: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    trait_cols = ["species_key", "nome_cientifico", *[col for col, _label in ATTRIBUTES]]
    records = counts.merge(
        traits[trait_cols],
        on="species_key",
        how="left",
        suffixes=("", "_atributo"),
        validate="m:1",
    )
    records["taxon_sem_atributo"] = records["nome_cientifico_atributo"].isna()
    for col, _label in ATTRIBUTES:
        records[col] = records[col].fillna("sem classificação").astype(str).str.strip()

    functional_rows = []
    for col, label in ATTRIBUTES:
        part = records[
            [
                "sample_id",
                "nome_campanha",
                "nome_ponto",
                "nome_cientifico",
                "species_key",
                "contagem",
                "CPUEn",
                "taxon_sem_atributo",
                col,
            ]
        ].copy()
        part = part.rename(columns={col: "classe_funcional"})
        part["atributo"] = col
        part["atributo_rotulo"] = label
        part["feature"] = part["atributo"] + "::" + part["classe_funcional"]
        functional_rows.append(part)
    functional_records = pd.concat(functional_rows, ignore_index=True)

    categories: dict[str, list[str]] = {}
    for col, _label in ATTRIBUTES:
        cats = _ordered_categories(traits, col)
        if "sem classificação" in functional_records.loc[functional_records["atributo"] == col, "classe_funcional"].unique():
            if "sem classificação" not in cats:
                cats.append("sem classificação")
        categories[col] = cats

    features = [f"{col}::{cat}" for col, _label in ATTRIBUTES for cat in categories[col]]
    functional_matrix = functional_records.pivot_table(
        index="sample_id", columns="feature", values="CPUEn", aggfunc="sum", fill_value=0.0
    )
    functional_matrix = functional_matrix.reindex(index=metadata["sample_id"].tolist(), columns=features, fill_value=0.0)
    functional_matrix.index.name = "sample_id"

    functional_long = (
        functional_records.groupby(
            ["sample_id", "nome_campanha", "nome_ponto", "atributo", "atributo_rotulo", "classe_funcional", "feature"],
            as_index=False,
            dropna=False,
        )
        .agg(
            CPUEn=("CPUEn", "sum"),
            contagem=("contagem", "sum"),
            riqueza_taxa=("species_key", "nunique"),
            taxa_sem_atributo=("taxon_sem_atributo", "sum"),
        )
        .merge(metadata, on=["sample_id", "nome_campanha", "nome_ponto"], how="left")
    )
    return functional_matrix, functional_long, functional_records, records, categories


def temporal_composition(
    functional_long: pd.DataFrame, metadata: pd.DataFrame, categories: dict[str, list[str]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    campaigns = (
        metadata[["nome_campanha", "campanha_curta", "ordem_campanha", "ano", "estacao", "estacao_rotulo"]]
        .drop_duplicates()
        .sort_values("ordem_campanha")
    )
    grouped = (
        functional_long.groupby(["nome_campanha", "atributo", "classe_funcional"], as_index=False)
        .agg(CPUEn=("CPUEn", "sum"), contagem=("contagem", "sum"), riqueza_taxa=("riqueza_taxa", "sum"))
    )
    rows = []
    for _, camp in campaigns.iterrows():
        for attribute, label in ATTRIBUTES:
            total = float(
                grouped.loc[
                    (grouped["nome_campanha"] == camp["nome_campanha"]) & (grouped["atributo"] == attribute),
                    "CPUEn",
                ].sum()
            )
            for category in categories[attribute]:
                value = float(
                    grouped.loc[
                        (grouped["nome_campanha"] == camp["nome_campanha"])
                        & (grouped["atributo"] == attribute)
                        & (grouped["classe_funcional"] == category),
                        "CPUEn",
                    ].sum()
                )
                rows.append(
                    {
                        **camp.to_dict(),
                        "atributo": attribute,
                        "atributo_rotulo": label,
                        "classe_funcional": category,
                        "CPUEn": value,
                        "CPUEn_total_atributo": total,
                        "perc_CPUEn": _percentage(value, total),
                    }
                )
    by_campaign = pd.DataFrame(rows)

    point_grouped = (
        functional_long.groupby(["sample_id", "nome_campanha", "nome_ponto", "atributo", "classe_funcional"], as_index=False)
        .agg(CPUEn=("CPUEn", "sum"), contagem=("contagem", "sum"), riqueza_taxa=("riqueza_taxa", "sum"))
    )
    point_rows = []
    for _, sample in metadata.iterrows():
        for attribute, label in ATTRIBUTES:
            total = float(
                point_grouped.loc[
                    (point_grouped["sample_id"] == sample["sample_id"]) & (point_grouped["atributo"] == attribute),
                    "CPUEn",
                ].sum()
            )
            for category in categories[attribute]:
                value = float(
                    point_grouped.loc[
                        (point_grouped["sample_id"] == sample["sample_id"])
                        & (point_grouped["atributo"] == attribute)
                        & (point_grouped["classe_funcional"] == category),
                        "CPUEn",
                    ].sum()
                )
                point_rows.append(
                    {
                        "sample_id": sample["sample_id"],
                        "nome_campanha": sample["nome_campanha"],
                        "campanha_curta": sample["campanha_curta"],
                        "ano": sample["ano"],
                        "estacao": sample["estacao"],
                        "estacao_rotulo": sample["estacao_rotulo"],
                        "nome_ponto": sample["nome_ponto"],
                        "atributo": attribute,
                        "atributo_rotulo": label,
                        "classe_funcional": category,
                        "CPUEn": value,
                        "CPUEn_total_atributo": total,
                        "perc_CPUEn": _percentage(value, total),
                    }
                )
    return by_campaign, pd.DataFrame(point_rows)


def calculate_lcbd(functional_matrix: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for campaign, group in metadata.groupby("nome_campanha", sort=False):
        sample_ids = group["sample_id"].tolist()
        mat = functional_matrix.loc[sample_ids].to_numpy(dtype=float)
        hel = _hellinger(mat)
        centroid = hel.mean(axis=0)
        ss = ((hel - centroid) ** 2).sum(axis=1)
        ss_total = float(ss.sum())
        lcbd = ss / ss_total if ss_total > 0 else np.zeros_like(ss)
        beta_total = ss_total / max(len(sample_ids) - 1, 1)
        for sample_id, value, ss_value in zip(sample_ids, lcbd, ss, strict=True):
            meta = metadata.loc[metadata["sample_id"] == sample_id].iloc[0]
            profile = functional_matrix.loc[sample_id].to_numpy(dtype=float)
            rows.append(
                {
                    "nome_campanha": campaign,
                    "campanha_curta": meta["campanha_curta"],
                    "ano": meta["ano"],
                    "estacao": meta["estacao"],
                    "estacao_rotulo": meta["estacao_rotulo"],
                    "nome_ponto": meta["nome_ponto"],
                    "sample_id": sample_id,
                    "LCBD_funcional": float(value),
                    "SS_ponto": float(ss_value),
                    "Beta_Total_Hellinger_Campanha": float(beta_total),
                    "CPUEn_total_taxonomico": float(meta["CPUEn_total"]),
                    "n_classes_funcionais": int(np.sum(profile > 0)),
                    "captura_quantitativa": bool(meta["captura_quantitativa"]),
                }
            )
    return pd.DataFrame(rows)


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


def run_nmds_and_tests(
    functional_matrix: pd.DataFrame, metadata: pd.DataFrame, n_perm: int, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    positive = functional_matrix.sum(axis=1).to_numpy(dtype=float) > 0
    ord_matrix = functional_matrix.loc[positive].copy()
    ord_meta = metadata.loc[positive].reset_index(drop=True).copy()
    distance = _bray_curtis_matrix(ord_matrix.to_numpy(dtype=float))

    if len(ord_meta) >= 3:
        kwargs = {
            "n_components": 2,
            "metric": False,
            "dissimilarity": "precomputed",
            "random_state": seed,
            "n_init": 12,
            "max_iter": 3000,
            "eps": 1e-9,
        }
        try:
            nmds = MDS(**kwargs, normalized_stress="auto")
        except TypeError:
            nmds = MDS(**kwargs)
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
        perm.update({"fator": factor, "analise": label, "base": "perfil funcional; amostras com captura quantitativa"})
        permanova_rows.append(perm)
        disp = permdisp(distance, groups, n_perm=n_perm, seed=seed + 17)
        disp.update({"fator": factor, "analise": label, "base": "perfil funcional; amostras com captura quantitativa"})
        permdisp_rows.append(disp)
    return scores, pd.DataFrame(permanova_rows), pd.DataFrame(permdisp_rows)


def functional_indicators(
    by_campaign: pd.DataFrame, metadata: pd.DataFrame, lcbd: pd.DataFrame, records: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    campaigns = (
        metadata[["nome_campanha", "campanha_curta", "ordem_campanha", "ano", "estacao", "estacao_rotulo"]]
        .drop_duplicates()
        .sort_values("ordem_campanha")
        .reset_index(drop=True)
    )

    def value(attribute: str, category: str, campaign: str) -> tuple[float, float]:
        subset = by_campaign[(by_campaign["nome_campanha"] == campaign) & (by_campaign["atributo"] == attribute)]
        cpuen = float(subset.loc[subset["classe_funcional"] == category, "CPUEn"].sum())
        total = float(subset["CPUEn"].sum())
        return cpuen, _percentage(cpuen, total)

    rows = []
    for _, camp in campaigns.iterrows():
        campaign = camp["nome_campanha"]
        cpuen_reofilico, perc_reofilico = value("Preferencia_correnteza", "reofílico", campaign)
        cpuen_bentonico, perc_bentonico = value("Habitat_funcional", "bentônico", campaign)
        cpuen_sensivel, perc_sensivel = value("Sensibilidade_funcional", "sensível", campaign)
        cpuen_tolerante, perc_tolerante = value("Sensibilidade_funcional", "tolerante", campaign)
        campaign_lcbd = lcbd[lcbd["nome_campanha"] == campaign]
        campaign_records = records[records["nome_campanha"] == campaign]
        rows.append(
            {
                **camp.to_dict(),
                "CPUEn_total_taxonomico": float(
                    metadata.loc[metadata["nome_campanha"] == campaign, "CPUEn_total"].sum()
                ),
                "riqueza_taxonomica": int(campaign_records["species_key"].nunique()),
                "CPUEn_reofilico": cpuen_reofilico,
                "perc_CPUEn_reofilico": perc_reofilico,
                "CPUEn_bentonico": cpuen_bentonico,
                "perc_CPUEn_bentonico": perc_bentonico,
                "CPUEn_sensivel": cpuen_sensivel,
                "perc_CPUEn_sensivel": perc_sensivel,
                "CPUEn_tolerante": cpuen_tolerante,
                "perc_CPUEn_tolerante": perc_tolerante,
                "LCBD_funcional_medio": float(campaign_lcbd["LCBD_funcional"].mean()),
                "LCBD_funcional_max": float(campaign_lcbd["LCBD_funcional"].max()),
                "pontos_com_captura": int(
                    metadata.loc[metadata["nome_campanha"] == campaign, "captura_quantitativa"].sum()
                ),
            }
        )
    indicators = pd.DataFrame(rows)

    reading_rows = []
    for col, label in [
        ("perc_CPUEn_reofilico", "Participação de reofílicos (%)"),
        ("perc_CPUEn_bentonico", "Participação de bentônicos (%)"),
        ("perc_CPUEn_sensivel", "Participação de sensíveis (%)"),
        ("perc_CPUEn_tolerante", "Participação de tolerantes (%)"),
        ("LCBD_funcional_max", "LCBD funcional máximo"),
    ]:
        reading_rows.append(
            {
                "Indicador": label,
                "Primeira campanha": float(indicators[col].iloc[0]),
                "Última campanha": float(indicators[col].iloc[-1]),
                "Mínimo": float(indicators[col].min()),
                "Máximo": float(indicators[col].max()),
                "Inclinação linear por campanha": _linear_slope(indicators[col]),
                "Leitura": "Triagem exploratória; interpretar junto com taxonomia, esforço e histórico de campo.",
            }
        )
    return indicators, pd.DataFrame(reading_rows)


def build_functional_group_panel(records: pd.DataFrame, metadata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = records.copy()
    data["habitat_norm"] = data["Habitat_funcional"].map(_normalize_text)
    data["corrente_norm"] = data["Preferencia_correnteza"].map(_normalize_text)
    data["guilda_norm"] = data["Guilda_trofica"].map(_normalize_text)
    data["sensibilidade_norm"] = data["Sensibilidade_funcional"].map(_normalize_text)

    masks = {
        "especialistas_loticos_sensiveis": (data["corrente_norm"] == "reofilico")
        & (data["sensibilidade_norm"] == "sensivel"),
        "raspadores_bentonicos_reofilicos": (data["guilda_norm"] == "perifitivoro")
        & (data["habitat_norm"] == "bentonico")
        & (data["corrente_norm"] == "reofilico"),
        "generalistas_tolerantes": (data["guilda_norm"] == "onivoro")
        & (data["sensibilidade_norm"] == "tolerante"),
        "predadores": data["guilda_norm"] == "piscivoro",
    }

    rows = []
    species_rows = []
    species_columns = [
        "species_key",
        "nome_cientifico",
        "Habitat_funcional",
        "Preferencia_correnteza",
        "Guilda_trofica",
        "Porte_corporal",
        "Sensibilidade_funcional",
        "Confianca_classificacao",
        "Fonte_classificacao",
        "Observacoes_funcionais",
    ]
    species_base = data[[col for col in species_columns if col in data.columns]].drop_duplicates("species_key")
    for order, definition in enumerate(FUNCTIONAL_GROUP_DEFINITIONS, start=1):
        code = definition["codigo"]
        subset = data[masks[code]].copy()
        species_subset = species_base[species_base["species_key"].isin(subset["species_key"].dropna().unique())].copy()
        if not species_subset.empty:
            species_subset.insert(0, "ordem_grupo", order)
            species_subset.insert(1, "grupo_funcional", code)
            species_subset.insert(2, "grupo_rotulo", definition["rotulo"])
            species_subset.insert(3, "criterio", definition["criterio"])
            species_rows.append(species_subset)
        else:
            species_rows.append(
                pd.DataFrame(
                    [
                        {
                            "ordem_grupo": order,
                            "grupo_funcional": code,
                            "grupo_rotulo": definition["rotulo"],
                            "criterio": definition["criterio"],
                            "species_key": "",
                            "nome_cientifico": "Nenhuma espécie enquadrada",
                        }
                    ]
                )
            )
        if subset.empty:
            agg = pd.DataFrame(
                columns=["sample_id", "CPUEn_grupo", "contagem_grupo", "riqueza_taxa_grupo", "especies_grupo"]
            )
        else:
            agg = (
                subset.groupby("sample_id", as_index=False)
                .agg(
                    CPUEn_grupo=("CPUEn", "sum"),
                    contagem_grupo=("contagem", "sum"),
                    riqueza_taxa_grupo=("species_key", "nunique"),
                    especies_grupo=("nome_cientifico", lambda values: "; ".join(sorted(set(map(str, values))))),
                )
            )
        panel = metadata.merge(agg, on="sample_id", how="left")
        panel["CPUEn_grupo"] = pd.to_numeric(panel["CPUEn_grupo"], errors="coerce").fillna(0.0)
        panel["contagem_grupo"] = pd.to_numeric(panel["contagem_grupo"], errors="coerce").fillna(0.0)
        panel["riqueza_taxa_grupo"] = pd.to_numeric(panel["riqueza_taxa_grupo"], errors="coerce").fillna(0).astype(int)
        panel["especies_grupo"] = panel["especies_grupo"].fillna("")
        panel["perc_CPUEn"] = [
            _percentage(value, total)
            for value, total in zip(panel["CPUEn_grupo"], panel["CPUEn_total"], strict=True)
        ]
        panel["grupo_funcional"] = code
        panel["grupo_rotulo"] = definition["rotulo"]
        panel["criterio"] = definition["criterio"]
        panel["ordem_grupo"] = order
        panel["baixa_captura_total"] = (panel["CPUEn_total"] > 0) & (panel["CPUEn_total"] < 1.0)
        rows.append(panel)

    group_panel = pd.concat(rows, ignore_index=True)
    definitions = pd.DataFrame(FUNCTIONAL_GROUP_DEFINITIONS)
    definitions.insert(0, "ordem_grupo", range(1, len(definitions) + 1))
    if species_rows:
        species_groups = pd.concat(species_rows, ignore_index=True)
        grouped_species = set(species_groups["species_key"].dropna())
    else:
        species_groups = pd.DataFrame()
        grouped_species = set()
    ungrouped = species_base[~species_base["species_key"].isin(grouped_species)].copy()
    if not ungrouped.empty:
        ungrouped.insert(0, "ordem_grupo", len(FUNCTIONAL_GROUP_DEFINITIONS) + 1)
        ungrouped.insert(1, "grupo_funcional", "sem_grupo_sentinela")
        ungrouped.insert(2, "grupo_rotulo", "Sem grupo funcional sentinela")
        ungrouped.insert(3, "criterio", "Espécie com atributos funcionais, mas sem enquadramento nos grupos sentinelas definidos.")
        species_groups = pd.concat([species_groups, ungrouped], ignore_index=True)
    species_groups = species_groups.sort_values(["ordem_grupo", "nome_cientifico"]).reset_index(drop=True)
    return group_panel, definitions, species_groups


def _category_palette(categories: list[str], primary: str, secondary: str, highlight: str) -> dict[str, str]:
    base = [primary, secondary, highlight, "#6AA84F", "#A64D79", "#F1C232", "#76A5AF", "#8E7CC3", "#999999"]
    if len(categories) > len(base):
        cmap = plt.cm.get_cmap("tab20", len(categories))
        colors = [mcolors.to_hex(cmap(i)) for i in range(len(categories))]
    else:
        colors = base[: len(categories)]
    return dict(zip(categories, colors, strict=False))


def plot_composition(
    by_campaign: pd.DataFrame, categories: dict[str, list[str]], out_png: Path, theme: dict
) -> None:
    primary, secondary, highlight = _theme_colors(theme)
    attrs = [attr for attr in COMPOSITION_ATTRIBUTES if attr in by_campaign["atributo"].unique()]
    campaigns = (
        by_campaign[["nome_campanha", "campanha_curta", "ordem_campanha", "ano"]]
        .drop_duplicates()
        .sort_values("ordem_campanha")
    )
    x = np.arange(len(campaigns))
    fig, axes = plt.subplots(len(attrs), 1, figsize=(13.2, 10.2), dpi=int(theme.get("dpi", 600)), sharex=True)
    if len(attrs) == 1:
        axes = [axes]
    for idx, (ax, attr) in enumerate(zip(axes, attrs, strict=True), start=1):
        data = (
            by_campaign[by_campaign["atributo"] == attr]
            .pivot_table(index="nome_campanha", columns="classe_funcional", values="perc_CPUEn", aggfunc="sum", fill_value=0)
            .reindex(index=campaigns["nome_campanha"].tolist(), columns=categories[attr], fill_value=0)
        )
        palette = _category_palette(categories[attr], primary, secondary, highlight)
        bottom = np.zeros(len(data), dtype=float)
        for category in categories[attr]:
            values = data[category].to_numpy(dtype=float)
            if not np.any(values > 0):
                continue
            ax.bar(x, values, bottom=bottom, width=0.76, color=palette[category], edgecolor="white", linewidth=0.35, label=category)
            bottom += values
        ax.set_ylim(0, 100)
        ax.set_ylabel("CPUEn (%)", fontsize=10)
        ax.set_title(f"{chr(64 + idx)}) {_attribute_label(attr)}", loc="left", fontsize=12, fontweight="bold")
        ax.grid(True, axis="y", color="#E6E6E6", linewidth=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for i in range(1, len(campaigns)):
            if campaigns["ano"].iloc[i] != campaigns["ano"].iloc[i - 1]:
                ax.axvline(i - 0.5, color="#D0D0D0", linewidth=0.8)
        ax.legend(frameon=False, fontsize=8.5, ncol=min(4, max(1, len(categories[attr]))), loc="upper right")
    fig.suptitle(
        "Composição funcional temporal da ictiofauna",
        x=0.02,
        y=0.995,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(campaigns["campanha_curta"].tolist(), rotation=90, ha="center", fontsize=10)
    axes[-1].set_xlabel("Campanha", fontsize=10)
    fig.text(
        0.02,
        0.012,
        "Percentuais calculados dentro de cada atributo funcional, usando CPUEn agregada por campanha. Produto exploratório.",
        ha="left",
        fontsize=8.8,
        color="#404040",
    )
    fig.tight_layout(rect=[0.01, 0.04, 1, 0.96])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def plot_lcbd_heatmap(lcbd: pd.DataFrame, out_png: Path, theme: dict) -> None:
    primary, secondary, _highlight = _theme_colors(theme)
    campaigns = sorted(lcbd["nome_campanha"].unique().tolist(), key=_campaign_sort_key)
    points = sorted(lcbd["nome_ponto"].unique().tolist(), key=_point_sort_key)
    table = (
        lcbd.pivot_table(index="nome_ponto", columns="nome_campanha", values="LCBD_funcional", aggfunc="mean", fill_value=0)
        .reindex(index=points, columns=campaigns, fill_value=0)
    )
    values = table.to_numpy(dtype=float)
    vmax = max(float(np.nanmax(values)), 0.01)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "geoarc_lcbd_funcional", ["#F7F7F7", "#D9E6F2", secondary, primary]
    )
    fig, ax = plt.subplots(figsize=(12.6, 6.5), dpi=int(theme.get("dpi", 600)))
    im = ax.imshow(values, aspect="auto", cmap=cmap, vmin=0, vmax=vmax)
    ax.set_title("Heatmap LCBD funcional por ponto e campanha", loc="left", fontsize=14, fontweight="bold")
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
    cbar.set_label("LCBD funcional", fontsize=10)
    ax.text(
        0,
        -0.22,
        "Valores destacados correspondem ao quartil superior. Perfil funcional = CPUEn agregada por classes de atributos.",
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
    fig.suptitle("NMDS Bray-Curtis sobre perfil funcional da ictiofauna", x=0.02, ha="left", fontsize=14, fontweight="bold")
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
        ("perc_CPUEn_reofilico", "CPUEn reofílico (%)"),
        ("perc_CPUEn_bentonico", "CPUEn bentônico (%)"),
        ("perc_CPUEn_sensivel", "CPUEn sensível (%)"),
        ("perc_CPUEn_tolerante", "CPUEn tolerante (%)"),
        ("LCBD_funcional_max", "LCBD funcional máximo"),
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
    axes[0].set_title("Painel temporal de indicadores funcionais", loc="left", fontsize=14, fontweight="bold")
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
        "Indicadores exploratórios calculados sobre classes funcionais ponderadas por CPUEn; 2026 possui somente duas campanhas.",
        ha="left",
        fontsize=8.8,
        color="#404040",
    )
    fig.tight_layout(rect=[0.02, 0.05, 1, 0.98])
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def plot_functional_group_heatmaps(group_panel: pd.DataFrame, out_png: Path, theme: dict) -> None:
    primary, _secondary, _highlight = _theme_colors(theme)
    campaigns = sorted(group_panel["nome_campanha"].unique().tolist(), key=_campaign_sort_key)
    points = sorted(group_panel["nome_ponto"].unique().tolist(), key=_point_sort_key)
    groups = sorted(
        group_panel[["grupo_funcional", "grupo_rotulo", "ordem_grupo"]].drop_duplicates().to_dict("records"),
        key=lambda item: item["ordem_grupo"],
    )
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "geoarc_funcoes_sentinela", ["#F7F7F7", "#D9E6F2", "#8DBFD2", primary]
    )
    fig, axes = plt.subplots(
        len(groups),
        1,
        figsize=(13.2, 10.6),
        dpi=int(theme.get("dpi", 600)),
        sharex=True,
        sharey=True,
    )
    if len(groups) == 1:
        axes = [axes]

    im = None
    for idx, (ax, group) in enumerate(zip(axes, groups, strict=True), start=1):
        data = group_panel[group_panel["grupo_funcional"] == group["grupo_funcional"]]
        table = (
            data.pivot_table(index="nome_ponto", columns="nome_campanha", values="perc_CPUEn", aggfunc="mean", fill_value=0)
            .reindex(index=points, columns=campaigns, fill_value=0)
        )
        values = table.to_numpy(dtype=float)
        im = ax.imshow(values, aspect="auto", cmap=cmap, vmin=0, vmax=100)
        ax.set_title(f"{chr(64 + idx)}) {group['grupo_rotulo']}", loc="left", fontsize=12, fontweight="bold")
        ax.set_ylabel("Ponto", fontsize=10)
        ax.set_yticks(np.arange(len(points)))
        ax.set_yticklabels(points, fontsize=9.5)
        ax.set_xticks(np.arange(len(campaigns)))
        ax.set_xticks(np.arange(-0.5, len(campaigns), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(points), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.9)
        ax.tick_params(which="minor", bottom=False, left=False)
        for i in range(1, len(campaigns)):
            if _campaign_year(campaigns[i]) != _campaign_year(campaigns[i - 1]):
                ax.axvline(i - 0.5, color="#606060", linewidth=1.0)

    axes[-1].set_xticklabels([_campaign_short(c) for c in campaigns], rotation=90, ha="center", fontsize=10)
    axes[-1].set_xlabel("Campanha", fontsize=10)
    fig.suptitle(
        "Funções ecológicas sentinelas por ponto e campanha",
        x=0.02,
        y=0.995,
        ha="left",
        fontsize=14,
        fontweight="bold",
    )
    if im is not None:
        cax = fig.add_axes([0.915, 0.18, 0.018, 0.68])
        cbar = fig.colorbar(im, cax=cax, orientation="vertical")
        cbar.set_label("CPUEn do grupo funcional (%)", fontsize=10)
    fig.text(
        0.02,
        0.012,
        "Percentual calculado dentro de cada ponto-campanha. Grupos são sentinelas funcionais independentes e não somam 100%.",
        ha="left",
        fontsize=8.8,
        color="#404040",
    )
    fig.subplots_adjust(left=0.09, right=0.89, top=0.925, bottom=0.105, hspace=0.34)
    fig.savefig(out_png, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)


def write_excel_outputs(
    output_dir: Path,
    functional_matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    traits: pd.DataFrame,
    by_campaign: pd.DataFrame,
    by_point_campaign: pd.DataFrame,
    functional_long: pd.DataFrame,
    functional_records: pd.DataFrame,
    records: pd.DataFrame,
    lcbd: pd.DataFrame,
    scores: pd.DataFrame,
    permanova_df: pd.DataFrame,
    permdisp_df: pd.DataFrame,
    indicators: pd.DataFrame,
    reading: pd.DataFrame,
    group_panel: pd.DataFrame,
    group_definitions: pd.DataFrame,
    species_groups: pd.DataFrame,
) -> dict[str, str]:
    paths = {
        "functional_composition": output_dir / "19_df_composicao_funcional_ictiofauna.xlsx",
        "functional_lcbd": output_dir / "20_df_lcbd_funcional_ponto_campanha_ictiofauna.xlsx",
        "functional_nmds": output_dir / "21_df_nmds_permanova_funcional_ictiofauna.xlsx",
        "functional_panel": output_dir / "22_df_painel_funcional_indicadores_ictiofauna.xlsx",
        "functional_group_heatmaps": output_dir / "23_df_heatmap_funcoes_ecologicas_ictiofauna.xlsx",
    }
    matrix_out = functional_matrix.reset_index()
    matrix_out = matrix_out.merge(metadata, on="sample_id", how="left")
    missing_traits = (
        records.loc[records["taxon_sem_atributo"], ["nome_cientifico", "species_key"]]
        .drop_duplicates()
        .sort_values("nome_cientifico")
    )
    with pd.ExcelWriter(paths["functional_composition"], engine="openpyxl") as writer:
        by_campaign.to_excel(writer, sheet_name="composicao_campanha", index=False)
        by_point_campaign.to_excel(writer, sheet_name="composicao_ponto_campanha", index=False)
        functional_long.to_excel(writer, sheet_name="perfil_funcional_longo", index=False)
        matrix_out.to_excel(writer, sheet_name="matriz_perfil_funcional", index=False)
        traits.to_excel(writer, sheet_name="atributos_usados", index=False)
        missing_traits.to_excel(writer, sheet_name="taxa_sem_atributo", index=False)
    with pd.ExcelWriter(paths["functional_lcbd"], engine="openpyxl") as writer:
        lcbd.to_excel(writer, sheet_name="LCBD_funcional", index=False)
    with pd.ExcelWriter(paths["functional_nmds"], engine="openpyxl") as writer:
        scores.to_excel(writer, sheet_name="NMDS_scores", index=False)
        permanova_df.to_excel(writer, sheet_name="PERMANOVA", index=False)
        permdisp_df.to_excel(writer, sheet_name="PERMDISP", index=False)
    with pd.ExcelWriter(paths["functional_panel"], engine="openpyxl") as writer:
        indicators.to_excel(writer, sheet_name="indicadores_campanha", index=False)
        reading.to_excel(writer, sheet_name="leitura_exploratoria", index=False)
    with pd.ExcelWriter(paths["functional_group_heatmaps"], engine="openpyxl") as writer:
        group_panel.to_excel(writer, sheet_name="heatmap_funcoes", index=False)
        group_definitions.to_excel(writer, sheet_name="definicoes_funcoes", index=False)
        species_groups.to_excel(writer, sheet_name="especies_por_grupo", index=False)
    return {key: str(path) for key, path in paths.items()}


def write_readme(output_dir: Path, summary: dict) -> Path:
    path = output_dir / "README_exploratorio_funcional_geoarc001.md"
    lines = [
        "# GEOARC001 - Exploração de composição funcional da ictiofauna",
        "",
        "Pacote exploratório gerado para testar a integração entre composição taxonômica e composição funcional, sem alteração no banco de dados.",
        "",
        "## Base funcional",
        "",
        "- Tabela de atributos: `tabela_especie_atributos_funcionais_geoarc001_teste.xlsx`.",
        "- Atributos usados: habitat, preferência por correnteza, guilda trófica, porte corporal e sensibilidade ambiental.",
        "- Peso analítico: CPUEn por campanha, ponto e espécie.",
        "- Perfil funcional multivariado: CPUEn agregada por classes de cada atributo, usando a notação `atributo::classe`.",
        "",
        "## Produtos",
        "",
        "- `19_grafico_composicao_funcional_temporal_ictiofauna.png`",
        "- `20_grafico_heatmap_lcbd_funcional_ponto_campanha_ictiofauna.png`",
        "- `21_grafico_nmds_funcional_braycurtis_estacao_ano_ictiofauna.png`",
        "- `22_grafico_painel_funcional_indicadores_ictiofauna.png`",
        "- `23_grafico_heatmap_funcoes_ecologicas_ponto_campanha_ictiofauna.png`",
        "- Planilhas `.xlsx` pareadas com as tabelas de apoio.",
        "",
        "## Notas metodológicas",
        "",
        "- Os percentuais da composição funcional são calculados dentro de cada atributo, não entre atributos diferentes.",
        "- O LCBD funcional usa transformação de Hellinger por campanha e mantém todos os pontos monitorados.",
        "- O NMDS/PERMANOVA usa Bray-Curtis sobre o perfil funcional; amostras sem captura são excluídas da ordenação.",
        "- O painel de funções ecológicas sentinelas usa grupos independentes; portanto os quatro painéis não somam 100%.",
        "- A análise é exploratória e deve ser interpretada junto aos resultados taxonômicos, esforço, sazonalidade e histórico de campo.",
        "- 2026 possui somente duas campanhas no recorte atual.",
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
    parser = argparse.ArgumentParser(description="Gera pacote exploratório funcional da ictiofauna GEOARC001.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Planilha de migração aprovada do GEOARC001.")
    parser.add_argument("--traits", default=str(DEFAULT_TRAITS), help="Planilha espécie x atributos funcionais.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Diretório de saída exploratória.")
    parser.add_argument("--client", default="default", help="Cliente para carregamento de tema visual.")
    parser.add_argument("--n-perm", type=int, default=999, help="Número de permutações para PERMANOVA/PERMDISP.")
    parser.add_argument("--seed", type=int, default=20260625, help="Semente reprodutível.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = load_theme(ROOT / "configs", args.client)

    tables = read_sources(Path(args.source), Path(args.traits))
    traits = prepare_traits(tables.atributos)
    species_matrix, metadata, counts = build_community(tables)
    functional_matrix, functional_long, functional_records, records, categories = build_functional_profiles(
        counts, metadata, traits
    )
    by_campaign, by_point_campaign = temporal_composition(functional_long, metadata, categories)
    lcbd = calculate_lcbd(functional_matrix, metadata)
    scores, permanova_df, permdisp_df = run_nmds_and_tests(
        functional_matrix, metadata, n_perm=args.n_perm, seed=args.seed
    )
    indicators, reading = functional_indicators(by_campaign, metadata, lcbd, records)
    group_panel, group_definitions, species_groups = build_functional_group_panel(records, metadata)

    plot_composition(by_campaign, categories, output_dir / "19_grafico_composicao_funcional_temporal_ictiofauna.png", theme)
    plot_lcbd_heatmap(lcbd, output_dir / "20_grafico_heatmap_lcbd_funcional_ponto_campanha_ictiofauna.png", theme)
    plot_nmds(scores, permanova_df, output_dir / "21_grafico_nmds_funcional_braycurtis_estacao_ano_ictiofauna.png", theme)
    plot_indicator_panel(indicators, output_dir / "22_grafico_painel_funcional_indicadores_ictiofauna.png", theme)
    plot_functional_group_heatmaps(
        group_panel,
        output_dir / "23_grafico_heatmap_funcoes_ecologicas_ponto_campanha_ictiofauna.png",
        theme,
    )

    excel_paths = write_excel_outputs(
        output_dir=output_dir,
        functional_matrix=functional_matrix,
        metadata=metadata,
        traits=traits,
        by_campaign=by_campaign,
        by_point_campaign=by_point_campaign,
        functional_long=functional_long,
        functional_records=functional_records,
        records=records,
        lcbd=lcbd,
        scores=scores,
        permanova_df=permanova_df,
        permdisp_df=permdisp_df,
        indicators=indicators,
        reading=reading,
        group_panel=group_panel,
        group_definitions=group_definitions,
        species_groups=species_groups,
    )

    missing_traits = int(records["taxon_sem_atributo"].sum())
    summary = {
        "source": str(Path(args.source)),
        "traits": str(Path(args.traits)),
        "output_dir": str(output_dir),
        "campaigns": int(metadata["nome_campanha"].nunique()),
        "years": sorted(int(x) for x in metadata["ano"].dropna().unique().tolist()),
        "points": int(metadata["nome_ponto"].nunique()),
        "samples_total": int(len(metadata)),
        "samples_with_capture": int(metadata["captura_quantitativa"].sum()),
        "species_taxonomic_matrix": int(species_matrix.shape[1]),
        "species_with_traits": int(traits["species_key"].nunique()),
        "records_quantitative": int(len(counts)),
        "records_without_traits": missing_traits,
        "functional_features": int(functional_matrix.shape[1]),
        "nmds_samples": int(len(scores)),
        "n_permutations_requested": int(args.n_perm),
        "permanova": permanova_df[["analise", "n", "groups", "F", "R2", "p_perm"]].to_dict("records"),
        "permdisp": permdisp_df[["analise", "n", "groups", "F", "p_perm"]].to_dict("records"),
        "functional_group_definitions": group_definitions.to_dict("records"),
        "excel_outputs": excel_paths,
    }
    (output_dir / "manifesto_exploratorio_funcional_geoarc001.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    readme = write_readme(output_dir, summary)
    summary["readme"] = str(readme)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
