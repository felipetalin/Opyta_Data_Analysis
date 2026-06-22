from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.textual import (  # noqa: E402
    Evidence,
    FigureReference,
    NarrativeParagraph,
    NarrativeSection,
    TechnicalReport,
    render_technical_report,
    validate_technical_report,
)


PROJECT_CODE = "GEOHER001"
GROUP = "Zoobentos"
PERIOD = "C21 a C36 · 2022 a 2025"
POLICY_REFERENCE = "docs/PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md"
POLICY_REVISION = "2026-06-21"


def _default_results_dir() -> Path:
    geomil = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil")
    matches = list(
        geomil.glob(
            "Herculano*Licenciamento Pilhas/Resultados/Bentos"
        )
    )
    if not matches:
        raise FileNotFoundError("Pasta de resultados de Bentos do GEOHER001 não localizada.")
    return matches[0]


def _default_reference_docx() -> Path | None:
    geomil = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil")
    matches = list(
        geomil.glob(
            "Herculano*Licenciamento Pilhas/Diagn*/"
            "OPY-Geomil-Diagn*Bentos*Vers*cliente.docx"
        )
    )
    return matches[0] if matches else None


def _read(results_dir: Path, filename: str, sheet_name: str | int = 0) -> pd.DataFrame:
    path = results_dir / filename
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_excel(path, sheet_name=sheet_name)


def _fmt_int(value: float | int) -> str:
    return f"{int(round(float(value))):,}".replace(",", ".")


def _fmt_num(value: float | int, decimals: int = 1) -> str:
    rendered = f"{float(value):,.{decimals}f}"
    return rendered.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: float | int, decimals: int = 1) -> str:
    return f"{_fmt_num(value, decimals)}%"


def _join_pt(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " e " + values[-1]


def _class_label(value: str) -> str:
    mapping = {
        "Pessima": "Péssima",
        "Ruim": "Ruim",
        "Regular": "Regular",
        "Boa": "Boa",
        "Muito boa": "Muito boa",
    }
    return mapping.get(str(value), str(value))


def _load_metrics(results_dir: Path) -> dict:
    family_col = "Família"
    genus_col = "Gênero"
    taxon_col = "Táxon"
    occurrence_global_col = "% ocorrência global"
    occurrence_units_col = "Ocorrências campanha-ponto"

    composition = _read(results_dir, "01_tabela_composicao_zoobentos.xlsx")
    richness = _read(results_dir, "02_df_riqueza_por_ponto_zoobentos.xlsx")
    abundance = _read(results_dir, "03_df_abundancia_por_ponto_zoobentos.xlsx")
    occurrence = _read(
        results_dir,
        "04A_tabela_sintese_ocorrencia_zoobentos.xlsx",
        "Resumo_Geral",
    )
    order_richness = _read(results_dir, "04_df_riqueza_por_ordem_zoobentos.xlsx")
    point_richness = _read(results_dir, "06A_df_riqueza_total_por_ponto_zoobentos.xlsx")
    diversity = _read(results_dir, "10_df_diversidade_alfa_zoobentos.xlsx")
    bmwp = _read(results_dir, "11_df_bmwp_zoobentos.xlsx")
    bray = _read(results_dir, "11_df_distancias_braycurtis_zoobentos.xlsx")
    sufficiency = _read(results_dir, "12_df_curva_suficiencia_zoobentos.xlsx")
    ept_chol = _read(results_dir, "12_df_ept_chol_zoobentos.xlsx")

    valid_genera = composition[genus_col].replace("-", pd.NA).dropna()
    top_orders = order_richness.head(6).copy()
    top_orders["percent"] = top_orders["numero_de_taxons"] / len(composition) * 100

    campaigns_count = int(richness["nome_campanha"].nunique())
    points_count = int(richness["nome_ponto"].nunique())
    sample_units = campaigns_count * points_count

    occurrence_sorted = occurrence.sort_values(
        occurrence_global_col,
        ascending=False,
    ).reset_index(drop=True)
    top_occurrence = occurrence_sorted.head(5)

    point_sorted = point_richness.sort_values(
        "riqueza_taxons",
        ascending=False,
    ).reset_index(drop=True)
    richness_max = richness.sort_values("riqueza", ascending=False).iloc[0]
    abundance_max = abundance.sort_values("abundancia_total", ascending=False).head(2)

    last_curve = sufficiency.iloc[-1]
    observed_richness = float(last_curve["riqueza_obs_media"])
    estimated_richness = float(last_curve["riqueza_est_jackknife1_media"])
    sampling_coverage = observed_richness / estimated_richness * 100 if estimated_richness else 0

    is_general = diversity["nome_ponto"].astype(str).str.contains(r"\(Geral\)", regex=True)
    diversity_points = diversity.loc[~is_general].copy()
    diversity_general = diversity.loc[is_general].copy()

    bray_matrix = bray.set_index("nome_ponto")
    bray_pairs: list[tuple[str, str, float]] = []
    for row_index, point_a in enumerate(bray_matrix.index):
        for point_b in bray_matrix.columns[row_index + 1 :]:
            bray_pairs.append(
                (str(point_a), str(point_b), float(bray_matrix.loc[point_a, point_b]))
            )
    closest_pair = min(bray_pairs, key=lambda item: item[2])
    farthest_pair = max(bray_pairs, key=lambda item: item[2])
    cluster_labels = fcluster(
        linkage(squareform(bray_matrix.to_numpy(), checks=False), method="average"),
        t=3,
        criterion="maxclust",
    )
    grouped_points: dict[int, list[str]] = {}
    for point, cluster_label in zip(bray_matrix.index, cluster_labels, strict=True):
        grouped_points.setdefault(int(cluster_label), []).append(str(point))
    bray_groups = tuple(grouped_points.values())

    total_organisms = int(ept_chol["total"].sum())
    total_ept = int(ept_chol["ept"].sum())
    total_chol = int(ept_chol["chol"].sum())
    ept_pct = total_ept / total_organisms * 100 if total_organisms else 0
    chol_pct = total_chol / total_organisms * 100 if total_organisms else 0
    robust_indicator_units = ept_chol[ept_chol["total"] >= 10].copy()
    top_ept = robust_indicator_units.sort_values("pct_ept", ascending=False).iloc[0]
    top_chol = robust_indicator_units.sort_values("pct_chol", ascending=False).iloc[0]

    bmwp_counts = bmwp["classificacao"].value_counts()
    bmwp_max = bmwp.sort_values("bmwp_score", ascending=False).iloc[0]

    corbicula = composition[
        composition[taxon_col].astype(str).str.casefold() == "corbicula sp."
    ]
    corbicula_campaigns = (
        str(corbicula.iloc[0]["Ocorrência (Campanhas)"])
        if not corbicula.empty
        else ""
    )

    return {
        "composition": composition,
        "richness": richness,
        "abundance": abundance,
        "occurrence": occurrence,
        "order_richness": order_richness,
        "point_richness": point_richness,
        "diversity": diversity,
        "bmwp": bmwp,
        "sufficiency": sufficiency,
        "ept_chol": ept_chol,
        "taxa": int(len(composition)),
        "phyla": int(composition["Filo"].nunique()),
        "classes": int(composition["Classe"].nunique()),
        "orders": int(composition["Ordem"].nunique()),
        "families": int(composition[family_col].nunique()),
        "genera": int(valid_genera.nunique()),
        "top_orders": top_orders,
        "campaigns": campaigns_count,
        "points": points_count,
        "sample_units": sample_units,
        "total_organisms": total_organisms,
        "top_occurrence": top_occurrence,
        "ubiquitous_campaigns": int(
            (occurrence["Campanhas com ocorrência"] == campaigns_count).sum()
        ),
        "ubiquitous_points": int(
            (occurrence["Pontos com ocorrência"] == points_count).sum()
        ),
        "single_unit_taxa": int((occurrence[occurrence_units_col] == 1).sum()),
        "point_sorted": point_sorted,
        "richness_mean": float(richness["riqueza"].mean()),
        "richness_median": float(richness["riqueza"].median()),
        "richness_max": richness_max,
        "abundance_mean": float(abundance["abundancia_total"].mean()),
        "abundance_median": float(abundance["abundancia_total"].median()),
        "abundance_max": abundance_max,
        "observed_richness": observed_richness,
        "estimated_richness": estimated_richness,
        "sampling_coverage": sampling_coverage,
        "diversity_points": diversity_points,
        "diversity_general": diversity_general,
        "closest_pair": closest_pair,
        "farthest_pair": farthest_pair,
        "bray_groups": bray_groups,
        "total_ept": total_ept,
        "total_chol": total_chol,
        "ept_pct": ept_pct,
        "chol_pct": chol_pct,
        "top_ept": top_ept,
        "top_chol": top_chol,
        "bmwp_counts": bmwp_counts,
        "bmwp_max": bmwp_max,
        "corbicula_campaigns": corbicula_campaigns,
    }


def _build_report(metrics: dict, reference_docx: Path | None) -> TechnicalReport:
    top_orders = metrics["top_orders"]
    order_descriptions = [
        f"{row['ordem']} ({_fmt_int(row['numero_de_taxons'])} táxons; {_fmt_pct(row['percent'])})"
        for _, row in top_orders.head(4).iterrows()
    ]

    top_occurrence = metrics["top_occurrence"]
    occurrence_descriptions = [
        (
            f"<em>{row['Táxon']}</em> "
            f"({_fmt_int(row['Ocorrências campanha-ponto'])} unidades; "
            f"{_fmt_pct(row['% ocorrência global'] * 100)})"
        )
        for _, row in top_occurrence.head(3).iterrows()
    ]

    point_sorted = metrics["point_sorted"]
    richest_points = [
        f"{row['nome_ponto']} ({_fmt_int(row['riqueza_taxons'])} táxons)"
        for _, row in point_sorted.head(3).iterrows()
    ]
    lowest_points = [
        f"{row['nome_ponto']} ({_fmt_int(row['riqueza_taxons'])} táxons)"
        for _, row in point_sorted.tail(2).sort_values("riqueza_taxons").iterrows()
    ]

    diversity_points = metrics["diversity_points"]
    diversity_general = metrics["diversity_general"]
    max_general = diversity_general.sort_values("Shannon_H", ascending=False).iloc[0]
    closest_a, closest_b, closest_distance = metrics["closest_pair"]
    farthest_a, farthest_b, farthest_distance = metrics["farthest_pair"]

    bmwp_counts = metrics["bmwp_counts"]
    bmwp_distribution = {
        _class_label(label): int(count)
        for label, count in bmwp_counts.items()
    }
    lower_classes = bmwp_distribution.get("Péssima", 0) + bmwp_distribution.get("Ruim", 0)
    lower_pct = lower_classes / metrics["sample_units"] * 100

    evidence = (
        Evidence(
            "E01",
            "Escopo analítico consolidado",
            "escopo",
            (
                f"O recorte reúne {metrics['campaigns']} campanhas, {metrics['points']} pontos, "
                f"{metrics['sample_units']} unidades campanha-ponto, {metrics['taxa']} táxons "
                f"e {metrics['total_organisms']} organismos."
            ),
            (
                "01_tabela_composicao_zoobentos.xlsx",
                "02_df_riqueza_por_ponto_zoobentos.xlsx",
                "03_df_abundancia_por_ponto_zoobentos.xlsx",
            ),
            metrics={
                "Campanhas": metrics["campaigns"],
                "Pontos": metrics["points"],
                "Unidades campanha-ponto": metrics["sample_units"],
                "Táxons": metrics["taxa"],
                "Organismos": metrics["total_organisms"],
            },
            scope=PERIOD,
            tags=("escopo", "qa"),
        ),
        Evidence(
            "E02",
            "Composição taxonômica",
            "composicao",
            (
                f"Foram registrados {metrics['taxa']} táxons, distribuídos em "
                f"{metrics['phyla']} filos, {metrics['classes']} classes, "
                f"{metrics['orders']} ordens e {metrics['families']} famílias."
            ),
            (
                "01_tabela_composicao_zoobentos.xlsx",
                "04_df_riqueza_por_ordem_zoobentos.xlsx",
            ),
            inference_level="interpretativo",
            metrics={
                "Filos": metrics["phyla"],
                "Classes": metrics["classes"],
                "Ordens": metrics["orders"],
                "Famílias": metrics["families"],
                "Gêneros preenchidos": metrics["genera"],
            },
            interpretation=(
                "A composição mostra forte participação de insetos aquáticos, mas a riqueza "
                "por ordem não constitui, isoladamente, diagnóstico de qualidade ambiental."
            ),
            limitations=(
                "A identificação ocorreu em diferentes níveis taxonômicos.",
                "Riqueza não informa a abundância relativa nem a condição do habitat.",
            ),
            scope="Conjunto das 16 campanhas",
            tags=("composição", "riqueza"),
        ),
        Evidence(
            "E03",
            "Persistência e distribuição dos táxons",
            "ocorrencia",
            (
                f"Apenas {metrics['ubiquitous_campaigns']} táxon ocorreu em todas as campanhas; "
                f"{metrics['ubiquitous_points']} táxons foram registrados nos oito pontos e "
                f"{metrics['single_unit_taxa']} ocorreram em uma única unidade campanha-ponto."
            ),
            ("04A_tabela_sintese_ocorrencia_zoobentos.xlsx",),
            inference_level="interpretativo",
            metrics={
                "Táxons em todas as campanhas": metrics["ubiquitous_campaigns"],
                "Táxons em todos os pontos": metrics["ubiquitous_points"],
                "Táxons em uma única unidade": metrics["single_unit_taxa"],
            },
            interpretation=(
                "A assembleia combina um núcleo recorrente com uma parcela expressiva de "
                "registros espacial ou temporalmente restritos."
            ),
            limitations=(
                "Frequência de ocorrência não equivale à abundância.",
                "Registros únicos podem representar raridade, detectabilidade ou variação amostral.",
            ),
            scope=f"{metrics['sample_units']} unidades campanha-ponto",
            tags=("ocorrência", "persistência"),
        ),
        Evidence(
            "E04",
            "Riqueza espacial acumulada",
            "riqueza_abundancia",
            (
                f"A riqueza acumulada por ponto variou de "
                f"{int(point_sorted['riqueza_taxons'].min())} a "
                f"{int(point_sorted['riqueza_taxons'].max())} táxons."
            ),
            ("06A_df_riqueza_total_por_ponto_zoobentos.xlsx",),
            inference_level="comparativo",
            metrics={
                row["nome_ponto"]: int(row["riqueza_taxons"])
                for _, row in point_sorted.iterrows()
            },
            limitations=(
                "A riqueza acumulada integra todas as campanhas e não representa uma campanha típica.",
                "Diferenças entre pontos não foram submetidas a teste inferencial neste produto.",
            ),
            scope="Riqueza acumulada de 2022 a 2025",
            tags=("riqueza", "espacial"),
        ),
        Evidence(
            "E05",
            "Variação por unidade amostral",
            "riqueza_abundancia",
            (
                f"A riqueza por unidade apresentou mediana de {_fmt_num(metrics['richness_median'])} "
                f"táxons e máximo de {int(metrics['richness_max']['riqueza'])}; a abundância "
                f"apresentou mediana de {_fmt_num(metrics['abundance_median'], 0)} organismos "
                f"e máximo de {int(metrics['abundance_max'].iloc[0]['abundancia_total'])}."
            ),
            (
                "02_df_riqueza_por_ponto_zoobentos.xlsx",
                "03_df_abundancia_por_ponto_zoobentos.xlsx",
            ),
            inference_level="interpretativo",
            metrics={
                "Riqueza média": _fmt_num(metrics["richness_mean"], 2),
                "Riqueza mediana": _fmt_num(metrics["richness_median"], 1),
                "Riqueza máxima": int(metrics["richness_max"]["riqueza"]),
                "Abundância média": _fmt_num(metrics["abundance_mean"], 2),
                "Abundância mediana": _fmt_num(metrics["abundance_median"], 0),
                "Abundância máxima": int(metrics["abundance_max"].iloc[0]["abundancia_total"]),
            },
            interpretation=(
                "A amplitude entre unidades demonstra heterogeneidade descritiva no conjunto "
                "amostrado e justifica a leitura conjunta das dimensões espacial e temporal."
            ),
            limitations=(
                "Não foi aplicado teste de tendência temporal nesta síntese.",
                "Abundância bruta pode responder ao esforço e à eficiência amostral.",
            ),
            scope=f"{metrics['sample_units']} unidades campanha-ponto",
            tags=("riqueza", "abundância", "temporal"),
        ),
        Evidence(
            "E06",
            "Suficiência amostral",
            "suficiencia",
            (
                f"A riqueza observada final foi de {_fmt_num(metrics['observed_richness'], 0)} "
                f"táxons e o Jackknife 1 estimou {_fmt_num(metrics['estimated_richness'], 1)}, "
                f"resultando em cobertura aproximada de {_fmt_pct(metrics['sampling_coverage'])}."
            ),
            ("12_df_curva_suficiencia_zoobentos.xlsx",),
            inference_level="interpretativo",
            metrics={
                "Riqueza observada": _fmt_num(metrics["observed_richness"], 0),
                "Jackknife 1": _fmt_num(metrics["estimated_richness"], 1),
                "Cobertura aproximada": _fmt_pct(metrics["sampling_coverage"]),
            },
            interpretation=(
                "O esforço acumulado documentou parcela substancial da riqueza estimada, "
                "sem indicar esgotamento completo do conjunto potencial de táxons."
            ),
            limitations=(
                "O estimador depende da frequência de táxons raros e do desenho de permutação.",
                "A cobertura não deve ser apresentada como probabilidade de detectar qualquer táxon futuro.",
            ),
            scope="115 unidades com resultado positivo usadas na curva",
            tags=("suficiência", "jackknife"),
        ),
        Evidence(
            "E07",
            "Diversidade e equitabilidade",
            "diversidade",
            (
                f"Nas unidades por ponto, Shannon apresentou média de "
                f"{_fmt_num(diversity_points['Shannon_H'].mean(), 2)} e amplitude de "
                f"{_fmt_num(diversity_points['Shannon_H'].min(), 2)} a "
                f"{_fmt_num(diversity_points['Shannon_H'].max(), 2)}; Pielou apresentou "
                f"média de {_fmt_num(diversity_points['Pielou_J'].mean(), 2)}."
            ),
            ("10_df_diversidade_alfa_zoobentos.xlsx",),
            inference_level="interpretativo",
            metrics={
                "Shannon médio por ponto-campanha": _fmt_num(
                    diversity_points["Shannon_H"].mean(), 2
                ),
                "Pielou médio por ponto-campanha": _fmt_num(
                    diversity_points["Pielou_J"].mean(), 2
                ),
                "Maior Shannon geral": (
                    f"{max_general['nome_campanha']} · {_fmt_num(max_general['Shannon_H'], 2)}"
                ),
            },
            interpretation=(
                "A variação dos índices é compatível com mudanças na riqueza e na distribuição "
                "relativa das abundâncias entre unidades."
            ),
            limitations=(
                "Valores nulos incluem unidades sem organismos ou com riqueza insuficiente para o índice.",
                "Os índices não identificam quais táxons explicam as diferenças.",
            ),
            scope="128 unidades por ponto e 16 sínteses gerais por campanha",
            tags=("diversidade", "equitabilidade"),
        ),
        Evidence(
            "E08",
            "Dissimilaridade espacial agregada",
            "diversidade",
            (
                f"A menor distância de Bray-Curtis ocorreu entre {closest_a} e {closest_b} "
                f"({_fmt_num(closest_distance, 3)}), enquanto a maior ocorreu entre "
                f"{farthest_a} e {farthest_b} ({_fmt_num(farthest_distance, 3)})."
            ),
            (
                "11_df_distancias_braycurtis_zoobentos.xlsx",
                "11_df_matriz_comunidade_zoobentos.xlsx",
            ),
            inference_level="interpretativo",
            metrics={
                "Par mais próximo": (
                    f"{closest_a}–{closest_b} · similaridade "
                    f"{_fmt_pct((1 - closest_distance) * 100)}"
                ),
                "Par mais distinto": (
                    f"{farthest_a}–{farthest_b} · similaridade "
                    f"{_fmt_pct((1 - farthest_distance) * 100)}"
                ),
            },
            interpretation=(
                "A matriz agregada indica afinidades distintas entre os pontos no conjunto do período."
            ),
            limitations=(
                "A agregação de todas as campanhas oculta mudanças temporais na composição.",
                "A análise é descritiva e não testa associação com variáveis ambientais.",
            ),
            scope="Abundância acumulada por ponto",
            tags=("bray-curtis", "similaridade"),
        ),
        Evidence(
            "E09",
            "EPT e CHOL",
            "indicadores",
            (
                f"EPT reuniu {_fmt_int(metrics['total_ept'])} organismos "
                f"({_fmt_pct(metrics['ept_pct'], 2)}) e CHOL reuniu "
                f"{_fmt_int(metrics['total_chol'])} ({_fmt_pct(metrics['chol_pct'], 2)}) "
                f"da abundância total."
            ),
            ("12_df_ept_chol_zoobentos.xlsx",),
            inference_level="interpretativo",
            metrics={
                "EPT": _fmt_int(metrics["total_ept"]),
                "%EPT global ponderado": _fmt_pct(metrics["ept_pct"], 2),
                "CHOL": _fmt_int(metrics["total_chol"]),
                "%CHOL global ponderado": _fmt_pct(metrics["chol_pct"], 2),
                "Maior %EPT com N ≥ 10": (
                    f"{metrics['top_ept']['nome_campanha']} · "
                    f"{metrics['top_ept']['nome_ponto']} · "
                    f"{_fmt_pct(metrics['top_ept']['pct_ept'])}"
                ),
                "Maior %CHOL com N ≥ 10": (
                    f"{metrics['top_chol']['nome_campanha']} · "
                    f"{metrics['top_chol']['nome_ponto']} · "
                    f"{_fmt_pct(metrics['top_chol']['pct_chol'])}"
                ),
            },
            interpretation=(
                "As métricas mostram alternância na participação relativa de grupos com "
                "diferentes tolerâncias ecológicas entre campanhas e pontos."
            ),
            limitations=(
                "EPT e CHOL não são categorias complementares; outros grupos compõem o total.",
                "Percentuais elevados em amostras com poucos organismos são instáveis.",
                "As métricas não devem ser interpretadas isoladamente como diagnóstico causal.",
            ),
            scope="Abundância total das 128 unidades campanha-ponto",
            tags=("ept", "chol", "bioindicadores"),
        ),
        Evidence(
            "E10",
            "Índice BMWP",
            "indicadores",
            (
                f"As classes Péssima e Ruim somaram {lower_classes} das "
                f"{metrics['sample_units']} unidades ({_fmt_pct(lower_pct)}); o maior escore foi "
                f"{int(metrics['bmwp_max']['bmwp_score'])} em "
                f"{metrics['bmwp_max']['nome_campanha']} · {metrics['bmwp_max']['nome_ponto']}."
            ),
            ("11_df_bmwp_zoobentos.xlsx",),
            inference_level="interpretativo",
            metrics={
                label: count for label, count in bmwp_distribution.items()
            }
            | {
                "Maior escore": (
                    f"{int(metrics['bmwp_max']['bmwp_score'])} · "
                    f"{metrics['bmwp_max']['nome_campanha']} · "
                    f"{metrics['bmwp_max']['nome_ponto']}"
                )
            },
            interpretation=(
                "A distribuição das classes indica predominância de escores inferiores no "
                "conjunto das unidades, com melhora pontual em algumas campanhas e pontos."
            ),
            limitations=(
                "O BMWP depende da identificação em família e dos escores taxonômicos adotados.",
                "Variações de riqueza, esforço, habitat e hidrologia podem influenciar o escore.",
                "A atribuição de causa requer integração com dados físico-químicos e de habitat.",
            ),
            scope="128 unidades campanha-ponto",
            tags=("bmwp", "qualidade ecológica"),
        ),
        Evidence(
            "E11",
            "Registro de Corbicula",
            "taxons_interesse",
            (
                f"<em>Corbicula</em> sp. foi registrada em "
                f"{metrics['corbicula_campaigns'] or 'campanha não determinada'}."
            ),
            ("01_tabela_composicao_zoobentos.xlsx",),
            inference_level="recomendacao",
            metrics={
                "Táxon": "Corbicula sp.",
                "Ocorrência": metrics["corbicula_campaigns"] or "-",
            },
            interpretation=(
                "O registro justifica acompanhamento temporal e, quando possível, refinamento "
                "da identificação taxonômica."
            ),
            limitations=(
                "A identificação no nível de gênero não resolve a espécie.",
                "O registro pontual não permite inferir estabelecimento, expansão ou impacto local.",
            ),
            scope="Composição consolidada",
            tags=("não nativas", "monitoramento"),
        ),
        Evidence(
            "E12",
            "Limites de interpretação integrada",
            "sintese",
            (
                "Os produtos disponíveis descrevem composição, abundância, ocorrência, diversidade "
                "e indicadores biológicos, mas não constituem desenho causal."
            ),
            (
                "10_df_diversidade_alfa_zoobentos.xlsx",
                "11_df_bmwp_zoobentos.xlsx",
                "12_df_ept_chol_zoobentos.xlsx",
            ),
            inference_level="recomendacao",
            metrics={
                "Escala temporal": "16 campanhas",
                "Escala espacial": "8 pontos",
                "Tipo de inferência": "descritiva e comparativa",
            },
            interpretation=(
                "A discussão ambiental deve integrar os indicadores biológicos a dados de habitat, "
                "hidrologia e qualidade da água antes de atribuir mecanismos."
            ),
            limitations=(
                "Não há teste causal ou modelo explicativo ambiental neste conjunto de produtos.",
            ),
            scope="Síntese do diagnóstico",
            tags=("limitações", "integração"),
        ),
    )

    sections = (
        NarrativeSection(
            "escopo",
            "Base analítica e critérios de interpretação",
            (
                NarrativeParagraph(
                    (
                        f"O diagnóstico consolidado compreende {metrics['campaigns']} campanhas "
                        f"realizadas entre 2022 e 2025 em {metrics['points']} pontos amostrais. "
                        f"A base reúne {metrics['sample_units']} combinações campanha-ponto, "
                        f"{metrics['taxa']} táxons e {_fmt_int(metrics['total_organisms'])} organismos."
                    ),
                    ("E01",),
                ),
                NarrativeParagraph(
                    (
                        "A narrativa foi construída a partir das planilhas oficiais atualmente "
                        "validadas. Resultados observados, comparações e interpretações são apresentados "
                        "em camadas distintas, e cada parágrafo mantém vínculo explícito com seus "
                        "arquivos-fonte."
                    ),
                    ("E01", "E12"),
                    role="contexto",
                    inference_level="descritivo",
                ),
                NarrativeParagraph(
                    (
                        "As associações com qualidade ambiental são tratadas como interpretações "
                        "compatíveis com os indicadores utilizados, sem caráter explicativo. "
                        "A atribuição de mecanismos exige integração com informações físico-químicas, "
                        "hidrológicas e de habitat."
                    ),
                    ("E12",),
                    role="limitacao",
                    inference_level="recomendacao",
                ),
            ),
            table_rows=(
                ("Campanhas", str(metrics["campaigns"])),
                ("Pontos", str(metrics["points"])),
                ("Táxons", str(metrics["taxa"])),
                ("Organismos", _fmt_int(metrics["total_organisms"])),
            ),
        ),
        NarrativeSection(
            "composicao",
            "Distribuição, composição e riqueza taxonômica",
            (
                NarrativeParagraph(
                    (
                        f"Foram registrados {metrics['taxa']} táxons, distribuídos em "
                        f"{metrics['orders']} ordens e {metrics['families']} famílias. "
                        f"As ordens com maior riqueza foram {_join_pt(order_descriptions)}."
                    ),
                    ("E02",),
                ),
                NarrativeParagraph(
                    (
                        "A composição foi marcada pela participação expressiva de insetos aquáticos. "
                        "Esse padrão é coerente com assembleias bentônicas de ambientes lóticos, mas "
                        "a representatividade taxonômica, isoladamente, não permite classificar a "
                        "qualidade ambiental dos pontos."
                    ),
                    ("E02",),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "04_grafico_riqueza_ordem_barras_zoobentos.png",
                    "Riqueza taxonômica por ordem no conjunto das 16 campanhas.",
                    "04_df_riqueza_por_ordem_zoobentos.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            "ocorrencia",
            "Persistência temporal e distribuição espacial",
            (
                NarrativeParagraph(
                    (
                        f"Os táxons com maior frequência global foram "
                        f"{_join_pt(occurrence_descriptions)}. "
                        f"Apenas {metrics['ubiquitous_campaigns']} táxon ocorreu nas 16 campanhas, "
                        f"enquanto {metrics['single_unit_taxa']} foram registrados em uma única "
                        f"unidade campanha-ponto."
                    ),
                    ("E03",),
                ),
                NarrativeParagraph(
                    (
                        "O resultado caracteriza uma assembleia formada por um núcleo de táxons "
                        "recorrentes e por numerosos registros restritos. Essa combinação pode estar "
                        "relacionada à heterogeneidade ambiental e à detectabilidade dos organismos, "
                        "mas o quadro de ocorrência não distingue raridade ecológica de variação amostral."
                    ),
                    ("E03",),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "04B_grafico_frequencia_ocorrencia_por_campanha_zoobentos_parte_01.png",
                    "Frequência de ocorrência por campanha — primeira parte.",
                    "04A_tabela_sintese_ocorrencia_zoobentos.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            "riqueza-abundancia",
            "Variação espacial e temporal da riqueza e abundância",
            (
                NarrativeParagraph(
                    (
                        f"A riqueza acumulada foi maior em {_join_pt(richest_points)}. "
                        f"Os menores valores acumulados ocorreram em {_join_pt(lowest_points)}."
                    ),
                    ("E04",),
                    role="comparacao",
                    inference_level="comparativo",
                ),
                NarrativeParagraph(
                    (
                        f"Por unidade campanha-ponto, a riqueza apresentou mediana de "
                        f"{_fmt_num(metrics['richness_median'])} táxons. O maior valor foi "
                        f"{int(metrics['richness_max']['riqueza'])} táxons em "
                        f"{metrics['richness_max']['nome_campanha']} · "
                        f"{metrics['richness_max']['nome_ponto']}. A abundância totalizou "
                        f"{_fmt_int(metrics['total_organisms'])} organismos e alcançou máximo "
                        f"de {int(metrics['abundance_max'].iloc[0]['abundancia_total'])} organismos "
                        f"em uma unidade."
                    ),
                    ("E05",),
                ),
                NarrativeParagraph(
                    (
                        "As amplitudes observadas indicam heterogeneidade entre campanhas e pontos. "
                        "Como esta síntese não aplica testes de tendência ou modelos explicativos, "
                        "as diferenças devem ser tratadas como padrões descritivos do período."
                    ),
                    ("E04", "E05"),
                    role="limitacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "02_grafico_riqueza_por_ponto_zoobentos.png",
                    "Variação da riqueza por ponto ao longo das campanhas.",
                    "02_df_riqueza_por_ponto_zoobentos.xlsx",
                ),
                FigureReference(
                    "03_grafico_abundancia_por_ponto_zoobentos.png",
                    "Variação da abundância por ponto ao longo das campanhas.",
                    "03_df_abundancia_por_ponto_zoobentos.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            "suficiencia",
            "Suficiência amostral",
            (
                NarrativeParagraph(
                    (
                        f"A riqueza observada ao final da curva foi de "
                        f"{_fmt_num(metrics['observed_richness'], 0)} táxons, enquanto o estimador "
                        f"Jackknife 1 indicou {_fmt_num(metrics['estimated_richness'], 1)}. "
                        f"A razão entre riqueza observada e estimada correspondeu a "
                        f"{_fmt_pct(metrics['sampling_coverage'])}."
                    ),
                    ("E06",),
                ),
                NarrativeParagraph(
                    (
                        "O esforço acumulado documentou parcela substancial da riqueza potencial, "
                        "mas a diferença remanescente em relação ao estimador indica possibilidade "
                        "de novos registros com a continuidade das amostragens. Por esse motivo, o "
                        "resultado é apresentado como cobertura aproximada, e não como inventário esgotado."
                    ),
                    ("E06",),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "12_curva_suficiencia_amostral_zoobentos.png",
                    "Riqueza observada e estimada pelo Jackknife 1.",
                    "12_df_curva_suficiencia_zoobentos.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            "diversidade",
            "Diversidade, equitabilidade e similaridade",
            (
                NarrativeParagraph(
                    (
                        f"Nas unidades por ponto, o índice de Shannon apresentou média de "
                        f"{_fmt_num(diversity_points['Shannon_H'].mean(), 2)}, enquanto Pielou "
                        f"apresentou média de {_fmt_num(diversity_points['Pielou_J'].mean(), 2)}. "
                        f"A maior diversidade geral por campanha ocorreu em "
                        f"{max_general['nome_campanha']}, com H′ = "
                        f"{_fmt_num(max_general['Shannon_H'], 2)}."
                    ),
                    ("E07",),
                ),
                NarrativeParagraph(
                    (
                        f"Na matriz agregada de Bray-Curtis, {closest_a} e {closest_b} formaram "
                        f"o par mais próximo, com similaridade equivalente a "
                        f"{_fmt_pct((1 - closest_distance) * 100)}. O maior contraste ocorreu entre "
                        f"{farthest_a} e {farthest_b}, com similaridade de "
                        f"{_fmt_pct((1 - farthest_distance) * 100)}."
                    ),
                    ("E08",),
                    role="comparacao",
                    inference_level="comparativo",
                ),
                NarrativeParagraph(
                    (
                        "Os índices demonstram variação na estrutura da comunidade e diferenças "
                        "agregadas entre pontos. A interpretação ecológica deve considerar que a "
                        "matriz de similaridade combina todo o período e pode ocultar reorganizações "
                        "temporais da assembleia."
                    ),
                    ("E07", "E08"),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "10_grafico_diversidade_alfa_zoobentos.png",
                    "Diversidade de Shannon e equitabilidade de Pielou.",
                    "10_df_diversidade_alfa_zoobentos.xlsx",
                ),
                FigureReference(
                    "11_dendrograma_similaridade_zoobentos.png",
                    "Agrupamento dos pontos com base na distância de Bray-Curtis.",
                    "11_df_distancias_braycurtis_zoobentos.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            "indicadores",
            "Indicadores EPT, CHOL e BMWP",
            (
                NarrativeParagraph(
                    (
                        f"No conjunto das unidades, EPT representou "
                        f"{_fmt_int(metrics['total_ept'])} organismos "
                        f"({_fmt_pct(metrics['ept_pct'], 2)} da abundância), enquanto CHOL "
                        f"representou {_fmt_int(metrics['total_chol'])} "
                        f"({_fmt_pct(metrics['chol_pct'], 2)}). Entre as unidades com pelo menos "
                        f"10 organismos, o maior %EPT ocorreu em "
                        f"{metrics['top_ept']['nome_campanha']} · {metrics['top_ept']['nome_ponto']} "
                        f"({_fmt_pct(metrics['top_ept']['pct_ept'])}) e o maior %CHOL em "
                        f"{metrics['top_chol']['nome_campanha']} · {metrics['top_chol']['nome_ponto']} "
                        f"({_fmt_pct(metrics['top_chol']['pct_chol'])})."
                    ),
                    ("E09",),
                ),
                NarrativeParagraph(
                    (
                        f"No BMWP, as classes Péssima e Ruim reuniram {lower_classes} unidades "
                        f"({_fmt_pct(lower_pct)}). O maior escore foi "
                        f"{int(metrics['bmwp_max']['bmwp_score'])}, registrado em "
                        f"{metrics['bmwp_max']['nome_campanha']} · "
                        f"{metrics['bmwp_max']['nome_ponto']}, classificado como "
                        f"{_class_label(metrics['bmwp_max']['classificacao'])}."
                    ),
                    ("E10",),
                ),
                NarrativeParagraph(
                    (
                        "EPT, CHOL e BMWP apontam variação relevante entre campanhas e pontos, "
                        "mas respondem a dimensões parcialmente diferentes da assembleia. A leitura "
                        "mais robusta é integrada: percentuais devem ser ponderados pelo número de "
                        "organismos, e os escores devem ser avaliados juntamente com riqueza, habitat, "
                        "hidrologia e qualidade físico-química da água."
                    ),
                    ("E09", "E10", "E12"),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "12_grafico_ept_chol_zoobentos.png",
                    "Variação espacial e temporal de %EPT e %CHOL.",
                    "12_df_ept_chol_zoobentos.xlsx",
                ),
                FigureReference(
                    "11_grafico_bmwp_zoobentos.png",
                    "Escores e classes do índice BMWP.",
                    "11_df_bmwp_zoobentos.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            "taxons-interesse",
            "Táxons de interesse para acompanhamento",
            (
                NarrativeParagraph(
                    (
                        f"O molusco <em>Corbicula</em> sp. foi registrado em "
                        f"{metrics['corbicula_campaigns']}. O registro merece acompanhamento, "
                        f"especialmente por incluir um gênero que reúne espécies introduzidas em "
                        f"bacias brasileiras."
                    ),
                    ("E11",),
                    inference_level="recomendacao",
                ),
                NarrativeParagraph(
                    (
                        "Como a identificação permaneceu no nível de gênero e a ocorrência foi "
                        "pontual, os dados disponíveis não permitem afirmar a espécie, o grau de "
                        "estabelecimento ou a existência de efeito local. Recomenda-se manter o "
                        "registro explicitamente qualificado e buscar refinamento taxonômico quando possível."
                    ),
                    ("E11",),
                    role="limitacao",
                    inference_level="recomendacao",
                ),
            ),
        ),
        NarrativeSection(
            "sintese",
            "Síntese técnica",
            (
                NarrativeParagraph(
                    (
                        f"O monitoramento documentou uma assembleia com {metrics['taxa']} táxons, "
                        f"ampla variação entre unidades e diferenças espaciais na riqueza acumulada, "
                        f"na composição e nos indicadores biológicos. A presença simultânea de grupos "
                        f"EPT, táxons recorrentes como <em>Chironomidae</em> e elevada frequência de "
                        f"classes inferiores do BMWP caracteriza um quadro heterogêneo, sem resposta "
                        f"uniforme entre campanhas e pontos."
                    ),
                    ("E02", "E03", "E04", "E09", "E10"),
                    role="sintese",
                    inference_level="interpretativo",
                ),
                NarrativeParagraph(
                    (
                        "A continuidade do monitoramento é tecnicamente pertinente para verificar "
                        "a persistência dos padrões, ampliar a cobertura da riqueza estimada e acompanhar "
                        "táxons de interesse. Para a discussão ambiental final, recomenda-se integrar "
                        "os resultados biológicos às condições de substrato, vazão, qualidade da água "
                        "e alterações locais de habitat."
                    ),
                    ("E06", "E11", "E12"),
                    role="recomendacao",
                    inference_level="recomendacao",
                ),
            ),
        ),
    )

    reference_name = reference_docx.name if reference_docx else "não localizada"
    return TechnicalReport(
        title="Diagnóstico de macroinvertebrados bentônicos",
        subtitle=(
            "Piloto de redação técnica rastreável, calibrado a partir do relatório "
            "consolidado e atualizado com os resultados validados do pipeline."
        ),
        project_code=PROJECT_CODE,
        group=GROUP,
        period=PERIOD,
        metadata={
            "Cliente": "Geomil / Herculano Mineração",
            "Referência editorial": reference_name,
            "Base numérica": "Resultados/Bentos",
            "Status": "Piloto aprovado em revisão técnica em 2026-06-20",
        },
        sections=sections,
        evidence=evidence,
        editorial_profile={
            "Voz": "Impessoal, técnica e predominantemente descritiva.",
            "Estrutura": "Resultado → comparação → interpretação → limitação → implicação.",
            "Calibração": "Mantém o encadeamento do relatório de referência, com números atualizados.",
            "Causalidade": "Vedada sem desenho ou teste causal explícito.",
            "Rastreabilidade": "Cada parágrafo aponta evidências e arquivos-fonte.",
            "Taxonomia": "Táxons em itálico e uso de táxon, família, gênero ou ordem conforme o nível identificado.",
            "Indicadores": "EPT, CHOL e BMWP interpretados de forma integrada e com ressalvas.",
        },
        report_status="aprovado",
    )


def _build_calibrated_report(
    metrics: dict,
    reference_docx: Path | None,
) -> TechnicalReport:
    """Aplica a policy mestre Opyta à base de evidências do piloto."""

    base = _build_report(metrics, reference_docx)
    base_evidence = {item.evidence_id: item for item in base.evidence}

    top_orders = metrics["top_orders"].head(4).copy()
    top_orders["percent"] = top_orders["numero_de_taxons"] / metrics["taxa"] * 100
    top_order_text = [
        f"{row['ordem']} ({_fmt_int(row['numero_de_taxons'])} táxons; {_fmt_pct(row['percent'])})"
        for _, row in top_orders.iterrows()
    ]
    top_order_total = int(top_orders["numero_de_taxons"].sum())
    remaining_orders = metrics["orders"] - len(top_orders)
    remaining_taxa = metrics["taxa"] - top_order_total

    top_occurrence = metrics["top_occurrence"].head(3)
    occurrence_text = [
        (
            f"{row['Táxon']} ({_fmt_int(row['Ocorrências campanha-ponto'])} unidades; "
            f"{_fmt_pct(row['% ocorrência global'] * 100)})"
        )
        for _, row in top_occurrence.iterrows()
    ]

    point_sorted = metrics["point_sorted"]
    richest_points = [
        f"{row['nome_ponto']} ({_fmt_int(row['riqueza_taxons'])} táxons)"
        for _, row in point_sorted.head(3).iterrows()
    ]
    lowest_points = [
        f"{row['nome_ponto']} ({_fmt_int(row['riqueza_taxons'])} táxons)"
        for _, row in point_sorted.sort_values("riqueza_taxons").head(2).iterrows()
    ]

    richness = metrics["richness"]
    abundance = metrics["abundance"]
    richness_top = richness.sort_values(
        ["riqueza", "nome_campanha", "nome_ponto"],
        ascending=[False, True, True],
    ).head(5)
    abundance_top = abundance.sort_values(
        ["abundancia_total", "nome_campanha", "nome_ponto"],
        ascending=[False, True, True],
    ).head(4)
    first_campaign = str(richness.iloc[0]["nome_campanha"])
    initial_zero_points = richness.loc[
        (richness["nome_campanha"] == first_campaign) & (richness["riqueza"] == 0),
        "nome_ponto",
    ].astype(str).tolist()

    richness_top_text = [
        (
            f"{row['nome_campanha']} · {row['nome_ponto']} "
            f"({_fmt_int(row['riqueza'])} táxons)"
        )
        for _, row in richness_top.iterrows()
    ]
    richness_top_locations = [
        f"{row['nome_campanha']} · {row['nome_ponto']}"
        for _, row in richness_top.iterrows()
    ]
    abundance_top_text = [
        (
            f"{row['nome_campanha']} · {row['nome_ponto']} "
            f"({_fmt_int(row['abundancia_total'])} organismos)"
        )
        for _, row in abundance_top.iterrows()
    ]

    diversity_points = metrics["diversity_points"]
    diversity_general = metrics["diversity_general"]
    diversity_top = diversity_points.sort_values(
        ["Shannon_H", "nome_campanha", "nome_ponto"],
        ascending=[False, True, True],
    ).head(3)
    diversity_top_text = [
        (
            f"{row['nome_campanha']} · {row['nome_ponto']} "
            f"({_fmt_num(row['Shannon_H'], 2)})"
        )
        for _, row in diversity_top.iterrows()
    ]
    max_general = diversity_general.sort_values("Shannon_H", ascending=False).iloc[0]
    pielou_max_count = int((diversity_points["Pielou_J"].round(10) == 1).sum())

    closest_a, closest_b, closest_distance = metrics["closest_pair"]
    farthest_a, farthest_b, farthest_distance = metrics["farthest_pair"]
    group_text = [_join_pt(list(group)) for group in metrics["bray_groups"]]

    robust_indicators = metrics["ept_chol"].loc[metrics["ept_chol"]["total"] >= 10]
    top_ept = robust_indicators.sort_values("pct_ept", ascending=False).head(3)
    top_chol = robust_indicators.sort_values("pct_chol", ascending=False).head(3)
    top_ept_text = [
        (
            f"{row['nome_campanha']} · {row['nome_ponto']} "
            f"({_fmt_pct(row['pct_ept'])}; N={_fmt_int(row['total'])})"
        )
        for _, row in top_ept.iterrows()
    ]
    top_chol_text = [
        (
            f"{row['nome_campanha']} · {row['nome_ponto']} "
            f"({_fmt_pct(row['pct_chol'])}; N={_fmt_int(row['total'])})"
        )
        for _, row in top_chol.iterrows()
    ]

    bmwp_counts = {
        _class_label(label): int(count)
        for label, count in metrics["bmwp_counts"].items()
    }
    lower_classes = bmwp_counts.get("Péssima", 0) + bmwp_counts.get("Ruim", 0)
    lower_pct = lower_classes / metrics["sample_units"] * 100

    evidence = (
        replace(
            base_evidence["E01"],
            observation=(
                f"O monitoramento reúne {metrics['campaigns']} campanhas, "
                f"{metrics['points']} pontos, {metrics['taxa']} táxons e "
                f"{_fmt_int(metrics['total_organisms'])} organismos."
            ),
        ),
        replace(
            base_evidence["E02"],
            inference_level="comparativo",
            observation=(
                f"As quatro ordens com maior riqueza reuniram {top_order_total} dos "
                f"{metrics['taxa']} táxons registrados."
            ),
            metrics=base_evidence["E02"].metrics
            | {
                str(row["ordem"]): (
                    f"{_fmt_int(row['numero_de_taxons'])} táxons; "
                    f"{_fmt_pct(row['percent'])}"
                )
                for _, row in top_orders.iterrows()
            }
            | {
                "Demais ordens": f"{remaining_orders} ordens; {remaining_taxa} táxons"
            },
            interpretation=(
                "A riqueza taxonômica apresentou maior participação de Trichoptera, "
                "Diptera, Ephemeroptera e Odonata."
            ),
        ),
        replace(
            base_evidence["E03"],
            inference_level="comparativo",
            observation=(
                f"{metrics['ubiquitous_campaigns']} táxon ocorreu nas 16 campanhas, "
                f"{metrics['ubiquitous_points']} foram registrados nos oito pontos e "
                f"{metrics['single_unit_taxa']} ocorreram em uma única unidade."
            ),
            metrics=base_evidence["E03"].metrics
            | {
                str(row["Táxon"]): (
                    f"{_fmt_int(row['Ocorrências campanha-ponto'])} unidades; "
                    f"{_fmt_pct(row['% ocorrência global'] * 100)}"
                )
                for _, row in top_occurrence.iterrows()
            },
            interpretation=(
                "A distribuição reuniu poucos táxons amplamente recorrentes e maior "
                "número de registros restritos a parte das campanhas ou pontos."
            ),
        ),
        base_evidence["E04"],
        replace(
            base_evidence["E05"],
            inference_level="comparativo",
            observation=(
                "Os máximos e as unidades sem registros de riqueza ou abundância "
                "ocorreram em diferentes campanhas e pontos."
            ),
            metrics=base_evidence["E05"].metrics
            | {
                "Maiores riquezas por unidade": " | ".join(richness_top_text),
                "Maiores abundâncias por unidade": " | ".join(abundance_top_text),
                f"Sem táxons registrados em {first_campaign}": _join_pt(initial_zero_points),
            },
            interpretation=(
                "Os extremos se alternaram entre campanhas e pontos, sem permanência "
                "de um único local entre os maiores valores da série."
            ),
        ),
        replace(
            base_evidence["E06"],
            interpretation=(
                "A diferença entre a riqueza observada e a estimada mantém possibilidade "
                "de acréscimo de táxons com a continuidade do monitoramento."
            ),
        ),
        replace(
            base_evidence["E07"],
            inference_level="comparativo",
            observation=(
                f"Shannon variou de {_fmt_num(diversity_points['Shannon_H'].min(), 2)} "
                f"a {_fmt_num(diversity_points['Shannon_H'].max(), 2)} nas unidades por ponto."
            ),
            metrics=base_evidence["E07"].metrics
            | {
                "Maiores valores de Shannon por unidade": " | ".join(diversity_top_text),
                "Unidades com Pielou igual a 1,00": pielou_max_count,
            },
            interpretation=(
                "Diversidade e equitabilidade oscilaram entre campanhas e pontos, "
                "com máximos distribuídos em diferentes momentos da série."
            ),
        ),
        replace(
            base_evidence["E08"],
            inference_level="comparativo",
            observation=(
                "O agrupamento médio da matriz de Bray-Curtis formou três conjuntos "
                "principais de pontos."
            ),
            metrics=base_evidence["E08"].metrics
            | {
                "Agrupamento 1": ", ".join(metrics["bray_groups"][0]),
                "Agrupamento 2": ", ".join(metrics["bray_groups"][1]),
                "Agrupamento 3": ", ".join(metrics["bray_groups"][2]),
                "Método": "Bray-Curtis; ligação média; corte em 3 grupos",
            },
            interpretation=(
                "Os agrupamentos sintetizam afinidades na composição e abundância "
                "acumuladas entre os pontos."
            ),
        ),
        replace(
            base_evidence["E09"],
            inference_level="comparativo",
            metrics=base_evidence["E09"].metrics
            | {
                "Três maiores %EPT com N ≥ 10": " | ".join(top_ept_text),
                "Três maiores %CHOL com N ≥ 10": " | ".join(top_chol_text),
            },
            interpretation=(
                "Os maiores percentuais de EPT e CHOL ocorreram em campanhas e pontos "
                "distintos."
            ),
        ),
        replace(
            base_evidence["E10"],
            inference_level="comparativo",
            interpretation=(
                "As classes Péssima e Ruim predominaram na série, enquanto classes "
                "superiores ocorreram pontualmente."
            ),
        ),
        replace(
            base_evidence["E11"],
            observation=(
                f"Corbicula sp. foi registrada em "
                f"{metrics['corbicula_campaigns'] or 'campanha não determinada'}."
            ),
            interpretation=(
                "O registro justifica acompanhamento temporal e refinamento da "
                "identificação taxonômica, quando possível."
            ),
        ),
        base_evidence["E12"],
    )

    sections = (
        NarrativeSection(
            "escopo",
            "Caracterização do monitoramento",
            (
                NarrativeParagraph(
                    (
                        f"O monitoramento compreende {metrics['campaigns']} campanhas realizadas "
                        f"entre 2022 e 2025, distribuídas em {metrics['points']} pontos amostrais. "
                        f"Foram registrados {metrics['taxa']} táxons e "
                        f"{_fmt_int(metrics['total_organisms'])} organismos."
                    ),
                    ("E01",),
                ),
            ),
            table_rows=(
                ("Campanhas", str(metrics["campaigns"])),
                ("Pontos", str(metrics["points"])),
                ("Táxons", str(metrics["taxa"])),
                ("Organismos", _fmt_int(metrics["total_organisms"])),
            ),
        ),
        NarrativeSection(
            "composicao",
            "Distribuição, composição e riqueza taxonômica",
            (
                NarrativeParagraph(
                    (
                        f"Foram registrados {metrics['taxa']} táxons, distribuídos em "
                        f"{metrics['orders']} ordens e {metrics['families']} famílias. "
                        f"As maiores riquezas ocorreram em {_join_pt(top_order_text)}."
                    ),
                    ("E02",),
                ),
                NarrativeParagraph(
                    (
                        f"Essas quatro ordens reuniram {top_order_total} táxons "
                        f"({_fmt_pct(top_order_total / metrics['taxa'] * 100)} da riqueza), "
                        f"enquanto as demais {remaining_orders} ordens somaram "
                        f"{remaining_taxa} táxons."
                    ),
                    ("E02",),
                    role="comparacao",
                    inference_level="comparativo",
                ),
            ),
            figures=base.sections[1].figures,
        ),
        NarrativeSection(
            "ocorrencia",
            "Persistência temporal e distribuição espacial",
            (
                NarrativeParagraph(
                    (
                        f"Os táxons com maior frequência foram {_join_pt(occurrence_text)}. "
                        f"No extremo oposto, {metrics['single_unit_taxa']} táxons ocorreram "
                        f"em uma única unidade campanha-ponto."
                    ),
                    ("E03",),
                ),
                NarrativeParagraph(
                    (
                        f"Considerando as {metrics['campaigns']} campanhas, apenas "
                        f"{metrics['ubiquitous_campaigns']} táxon esteve presente em todas elas, "
                        f"e {metrics['ubiquitous_points']} foram registrados nos oito pontos. "
                        "A série combinou poucos táxons amplamente recorrentes com registros "
                        "restritos a parte do recorte temporal ou espacial."
                    ),
                    ("E03",),
                    role="sintese",
                    inference_level="comparativo",
                ),
            ),
            figures=base.sections[2].figures,
        ),
        NarrativeSection(
            "riqueza-abundancia",
            "Variação espacial e temporal da riqueza e abundância",
            (
                NarrativeParagraph(
                    (
                        f"A riqueza acumulada por ponto variou de "
                        f"{_fmt_int(point_sorted['riqueza_taxons'].min())} a "
                        f"{_fmt_int(point_sorted['riqueza_taxons'].max())} táxons. "
                        f"Os maiores valores ocorreram em {_join_pt(richest_points)}, e os "
                        f"menores em {_join_pt(lowest_points)}."
                    ),
                    ("E04",),
                    role="comparacao",
                    inference_level="comparativo",
                ),
                NarrativeParagraph(
                    (
                        f"Na série de riqueza por ponto, os máximos foram registrados em "
                        f"{_join_pt(richness_top_text[:2])}. Valores de 14 táxons ocorreram em "
                        f"{_join_pt(richness_top_locations[2:5])}. Na campanha inicial, não houve "
                        f"registro de táxons em {_join_pt(initial_zero_points)}."
                    ),
                    ("E05",),
                ),
                NarrativeParagraph(
                    (
                        f"Para a abundância, os maiores registros ocorreram em "
                        f"{_join_pt(abundance_top_text)}. Também houve unidades sem organismos "
                        "registrados, principalmente no início da série. Os extremos de "
                        "riqueza e abundância se alternaram entre diferentes pontos e campanhas."
                    ),
                    ("E05",),
                    role="sintese",
                    inference_level="comparativo",
                ),
            ),
            figures=base.sections[3].figures,
        ),
        NarrativeSection(
            "suficiencia",
            "Suficiência amostral",
            (
                NarrativeParagraph(
                    (
                        f"A riqueza observada ao final da curva foi de "
                        f"{_fmt_num(metrics['observed_richness'], 0)} táxons, e o estimador "
                        f"Jackknife 1 indicou {_fmt_num(metrics['estimated_richness'], 1)}. "
                        f"A relação entre os valores correspondeu a "
                        f"{_fmt_pct(metrics['sampling_coverage'])}."
                    ),
                    ("E06",),
                ),
                NarrativeParagraph(
                    (
                        "A diferença remanescente sugere possibilidade de novos registros com a "
                        "continuidade das campanhas, especialmente entre táxons pouco frequentes."
                    ),
                    ("E06",),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=base.sections[4].figures,
        ),
        NarrativeSection(
            "diversidade",
            "Diversidade, equitabilidade e similaridade",
            (
                NarrativeParagraph(
                    (
                        f"Na série por ponto, Shannon variou de "
                        f"{_fmt_num(diversity_points['Shannon_H'].min(), 2)} a "
                        f"{_fmt_num(diversity_points['Shannon_H'].max(), 2)}. Os maiores valores "
                        f"ocorreram em {_join_pt(diversity_top_text)}. Na síntese por campanha, "
                        f"o máximo foi registrado em {max_general['nome_campanha']} "
                        f"(H′ = {_fmt_num(max_general['Shannon_H'], 2)}). Pielou alcançou 1,00 "
                        f"em {pielou_max_count} unidades campanha-ponto."
                    ),
                    ("E07",),
                ),
                NarrativeParagraph(
                    (
                        f"O dendrograma de Bray-Curtis reuniu os pontos em três agrupamentos: "
                        f"um formado por {group_text[0]}, outro por {group_text[1]} e o terceiro "
                        f"por {group_text[2]}. {closest_a} e {closest_b} apresentaram a maior "
                        f"similaridade ({_fmt_pct((1 - closest_distance) * 100)}), enquanto "
                        f"{farthest_a} e {farthest_b} formaram o contraste mais acentuado "
                        f"({_fmt_pct((1 - farthest_distance) * 100)})."
                    ),
                    ("E08",),
                    role="comparacao",
                    inference_level="comparativo",
                ),
                NarrativeParagraph(
                    (
                        "Os máximos de diversidade ocorreram em campanhas e pontos distintos. "
                        "Na avaliação espacial consolidada, Pt10, Pt11, Pt12 e Pt3 apresentaram "
                        "maior afinidade entre si, enquanto Pt7 e Pt8 formaram um grupo separado."
                    ),
                    ("E07", "E08"),
                    role="sintese",
                    inference_level="comparativo",
                ),
            ),
            figures=base.sections[5].figures,
        ),
        NarrativeSection(
            "indicadores",
            "Indicadores EPT, CHOL e BMWP",
            (
                NarrativeParagraph(
                    (
                        f"EPT representou {_fmt_int(metrics['total_ept'])} organismos "
                        f"({_fmt_pct(metrics['ept_pct'], 2)} da abundância total), e CHOL "
                        f"representou {_fmt_int(metrics['total_chol'])} organismos "
                        f"({_fmt_pct(metrics['chol_pct'], 2)}). Entre as unidades com pelo menos "
                        f"10 organismos, os maiores percentuais de EPT ocorreram em "
                        f"{_join_pt(top_ept_text)}. Para CHOL, os maiores valores foram registrados "
                        f"em {_join_pt(top_chol_text)}."
                    ),
                    ("E09",),
                ),
                NarrativeParagraph(
                    (
                        f"No BMWP, as classes Péssima e Ruim reuniram {lower_classes} das "
                        f"{metrics['sample_units']} observações ({_fmt_pct(lower_pct)}). "
                        f"Apenas {bmwp_counts.get('Muito boa', 0)} observação foi classificada "
                        f"como Muito boa, com escore {int(metrics['bmwp_max']['bmwp_score'])} em "
                        f"{metrics['bmwp_max']['nome_campanha']} · "
                        f"{metrics['bmwp_max']['nome_ponto']}."
                    ),
                    ("E10",),
                ),
                NarrativeParagraph(
                    (
                        "Os máximos de EPT e CHOL ocorreram em campanhas e pontos distintos, "
                        "enquanto o BMWP manteve predominância das classes Péssima e Ruim. "
                        "A interpretação ambiental deve considerar conjuntamente composição, "
                        "riqueza, abundância, condições de habitat e os dados de qualidade da "
                        "água disponíveis."
                    ),
                    ("E09", "E10", "E12"),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=base.sections[6].figures,
        ),
        NarrativeSection(
            "taxons-interesse",
            "Táxons de interesse para acompanhamento",
            (
                NarrativeParagraph(
                    (
                        f"O molusco <em>Corbicula</em> sp. foi registrado em "
                        f"{metrics['corbicula_campaigns']}. Recomenda-se acompanhar sua ocorrência "
                        "nas próximas campanhas e buscar refinamento taxonômico, quando possível."
                    ),
                    ("E11",),
                    role="recomendacao",
                    inference_level="recomendacao",
                ),
                NarrativeParagraph(
                    (
                        "A identificação no nível de gênero e o registro pontual não permitem "
                        "definir a espécie ou avaliar seu estabelecimento na área."
                    ),
                    ("E11",),
                    role="limitacao",
                    inference_level="recomendacao",
                ),
            ),
        ),
        NarrativeSection(
            "sintese",
            "Síntese técnica",
            (
                NarrativeParagraph(
                    (
                        "O monitoramento registrou diferenças espaciais na riqueza acumulada e "
                        "oscilações temporais de riqueza, abundância e diversidade. Os pontos com "
                        "maior riqueza acumulada também participaram de parte dos maiores valores "
                        "da série, embora os extremos tenham se alternado entre campanhas. A "
                        "análise de similaridade reuniu os oito pontos em três grupos, e os indicadores "
                        "EPT, CHOL e BMWP apresentaram respostas distintas no período analisado."
                    ),
                    ("E04", "E05", "E07", "E08", "E09", "E10"),
                    role="sintese",
                    inference_level="interpretativo",
                ),
                NarrativeParagraph(
                    (
                        "A continuidade do monitoramento permitirá verificar a permanência desses "
                        "padrões, ampliar a cobertura da riqueza estimada e acompanhar "
                        "<em>Corbicula</em> sp. A avaliação ambiental deve integrar os resultados "
                        "biológicos às condições de substrato, vazão, habitat e qualidade da água."
                    ),
                    ("E06", "E11", "E12"),
                    role="recomendacao",
                    inference_level="recomendacao",
                ),
            ),
        ),
    )

    reference_name = reference_docx.name if reference_docx else "não localizada"
    return TechnicalReport(
        title="Diagnóstico de macroinvertebrados bentônicos",
        subtitle=(
            "Diagnóstico elaborado com base nos resultados validados do monitoramento, "
            "período 2022–2025."
        ),
        project_code=PROJECT_CODE,
        group=GROUP,
        period=PERIOD,
        metadata={
            "Cliente": "Geomil / Herculano Mineração",
            "Base numérica": "Resultados/Bentos",
            "Policy editorial": POLICY_REFERENCE,
            "Revisão da policy": POLICY_REVISION,
            "Referência de calibração": reference_name,
            "Contexto espacial": "Códigos dos pontos; descritores ambientais não disponíveis na base analítica",
        },
        sections=sections,
        evidence=evidence,
        editorial_profile={
            "Voz": "Técnica, direta e compatível com consultoria ambiental.",
            "Narrativa": "Resultados e integração no corpo; rastreabilidade na camada de auditoria.",
            "Séries": "Extremos, campanhas e pontos antes do fechamento geral.",
            "Inferência": "Interpretação proporcional às evidências, sem atribuição causal.",
            "Síntese": "Integra os principais padrões sem repetir integralmente os resultados.",
            "Policy": f"{POLICY_REFERENCE} · revisão {POLICY_REVISION}",
        },
        report_status="calibrado",
    )


def _calibration_markdown(reference_docx: Path | None) -> str:
    reference = str(reference_docx) if reference_docx else "não localizada"
    return f"""# Calibração editorial — GEOHER001/Bentos

## Referência

`{reference}`

## Elementos preservados

- voz impessoal e linguagem técnico-ambiental;
- organização por composição, riqueza, abundância, diversidade e indicadores;
- comparação espacial e temporal;
- transição entre apresentação numérica e síntese interpretativa;
- chamada de figuras e tabelas junto à narrativa.

## Controles adicionados no piloto

- cada parágrafo vinculado a evidências identificadas;
- arquivos-fonte acessíveis no próprio HTML;
- narrativa principal separada do lastro de auditoria;
- distinção entre resultado, comparação, interpretação, limitação e recomendação;
- bloqueio ou alerta para linguagem causal sem desenho apropriado;
- percentuais acompanhados por denominador quando isso altera a interpretação;
- atualização automática dos números a partir das planilhas do pipeline;
- ressalvas para identificação taxonômica incompleta e indicadores não causais.

## Calibração Opyta aplicada em 2026-06-21

- redução de metalinguagem e frases defensivas;
- separação mais estrita entre descrição e interpretação;
- variação de conectivos e estruturas narrativas;
- leitura do contínuo dos dados, com extremos por campanha e ponto;
- descrição dos agrupamentos principais de Bray-Curtis;
- síntese integrada, sem repetição integral dos resultados;
- linguagem de consultoria ambiental;
- contextualização espacial limitada aos códigos dos pontos, pois a base
  analítica não contém descritores ambientais oficiais.

## Pontos do relatório de referência que não devem ser reproduzidos automaticamente

- tabelas taxonômicas anteriores à normalização de classe, ordem e gênero;
- uso intercambiável de “espécie” e “táxon”;
- atribuição direta de padrões à sazonalidade, vazão, substrato ou habitat sem teste;
- classificação de origem biogeográfica quando a identificação não alcança espécie;
- leitura de percentuais extremos sem considerar amostras com poucos organismos;
- sínteses genéricas sem vínculo explícito com planilha, figura ou métrica.

## Fórmula editorial adotada

`resultado observado → comparação → interpretação compatível → limitação → implicação para o monitoramento`
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o piloto de narrativa técnica rastreável para GEOHER001/Bentos."
    )
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "_scratch" / "textual_pilot_geoher001",
    )
    parser.add_argument("--reference-docx", type=Path, default=None)
    parser.add_argument(
        "--no-embed-assets",
        action="store_true",
        help="Mantém links file:// para as imagens em vez de incorporá-las ao HTML.",
    )
    args = parser.parse_args()

    results_dir = (args.results_dir or _default_results_dir()).resolve()
    reference_docx = args.reference_docx or _default_reference_docx()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = _load_metrics(results_dir)
    report = _build_calibrated_report(metrics, reference_docx)
    issues = validate_technical_report(report, source_dir=results_dir)

    html = render_technical_report(
        report,
        source_dir=results_dir,
        validation_issues=issues,
        embed_assets=not args.no_embed_assets,
    )

    html_path = output_dir / "relatorio_piloto_geoher001_bentos.html"
    evidence_path = output_dir / "evidencias_geoher001_bentos.json"
    validation_path = output_dir / "validacao_textual_geoher001_bentos.json"
    calibration_path = output_dir / "calibracao_relatorio_referencia.md"

    html_path.write_text(html, encoding="utf-8")
    evidence_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    errors = [issue for issue in issues if issue.severity == "ERROR"]
    warnings = [issue for issue in issues if issue.severity == "WARNING"]
    validation_payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "ERROR" if errors else ("OK_WITH_WARNINGS" if warnings else "OK"),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "issues": [issue.to_dict() for issue in issues],
        "results_dir": str(results_dir),
        "reference_docx": str(reference_docx) if reference_docx else None,
        "policy_reference": POLICY_REFERENCE,
        "policy_revision": POLICY_REVISION,
        "html": str(html_path),
    }
    validation_path.write_text(
        json.dumps(validation_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    calibration_path.write_text(
        _calibration_markdown(reference_docx),
        encoding="utf-8",
    )

    print(f"status={validation_payload['status']}")
    print(f"errors={len(errors)}")
    print(f"warnings={len(warnings)}")
    print(f"html={html_path}")
    print(f"evidence={evidence_path}")
    print(f"validation={validation_path}")
    print(f"calibration={calibration_path}")

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
