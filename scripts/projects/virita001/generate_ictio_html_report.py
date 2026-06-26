from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.textual.html import render_technical_report
from opyta_analysis.audit_utils import build_file_manifest
from opyta_analysis.textual.models import (
    Evidence,
    FigureReference,
    NarrativeParagraph,
    NarrativeSection,
    TechnicalReport,
)
from opyta_analysis.textual.validation import validate_technical_report


OUTPUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Virtual"
    r"\São Gonçalo\Resultados\Ictiofauna\Campanha_1"
)
POLICY_REFERENCE = "docs/PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md"
POLICY_REVISION = "2026-06-21"


def _read(name: str) -> pd.DataFrame:
    return pd.read_excel(OUTPUT_DIR / name)


def _read_optional(name: str, *, sheet_name: str | int = 0) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_excel(path, sheet_name=sheet_name)


def _fmt(value: float, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _distance_summary(distance: pd.DataFrame) -> dict:
    pairs = []
    if distance.empty or "nome_ponto" not in distance.columns:
        return {
            "max_similarity_pct": 0.0,
            "max_similarity_pair": "sem pares",
            "min_similarity_pct": 0.0,
            "min_similarity_pair": "sem pares",
            "points_compared": 0,
        }

    points = distance["nome_ponto"].astype(str).tolist()
    matrix = distance.set_index("nome_ponto")
    for i, point_a in enumerate(points):
        for point_b in points[i + 1 :]:
            if point_b not in matrix.columns:
                continue
            value = pd.to_numeric(pd.Series([matrix.loc[point_a, point_b]]), errors="coerce").iloc[0]
            if pd.isna(value):
                continue
            similarity = (1.0 - float(value)) * 100.0
            pairs.append((point_a, point_b, similarity))

    if not pairs:
        return {
            "max_similarity_pct": 0.0,
            "max_similarity_pair": "sem pares",
            "min_similarity_pct": 0.0,
            "min_similarity_pair": "sem pares",
            "points_compared": len(points),
        }

    max_pair = max(pairs, key=lambda item: item[2])
    min_pair = min(pairs, key=lambda item: item[2])
    return {
        "max_similarity_pct": max_pair[2],
        "max_similarity_pair": f"{max_pair[0]} e {max_pair[1]}",
        "min_similarity_pct": min_pair[2],
        "min_similarity_pair": f"{min_pair[0]} e {min_pair[1]}",
        "points_compared": len(points),
    }


def _load_metrics() -> dict:
    composition = _read("01_tabela_composicao_ictiofauna.xlsx")
    richness = _read("02_df_riqueza_por_ponto_ictiofauna.xlsx")
    abundance = _read("03_df_abundancia_por_ponto_ictiofauna.xlsx")
    orders = _read("04_df_riqueza_por_ordem_ictiofauna.xlsx")
    families = _read("04_df_riqueza_por_familia_ictiofauna.xlsx")
    cpue = _read("06_df_cpue_por_ponto_ictiofauna.xlsx")
    cpuen_species = _read("08_df_cpuen_por_especie_ictiofauna.xlsx")
    cpueb_species = _read("09_df_cpueb_por_especie_ictiofauna.xlsx")
    diversity = _read("10_df_diversidade_alfa_ictiofauna.xlsx")
    distance = _read("11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx")
    sufficiency = _read("12_df_curva_suficiencia_ictiofauna.xlsx")
    biometry = _read_optional("13_tabela_biometria_biomassa_ictiofauna.xlsx", sheet_name="Dados")

    campaign_col_cpuen = next(column for column in cpuen_species.columns if column != "nome_cientifico")
    campaign_col_cpueb = next(column for column in cpueb_species.columns if column != "nome_cientifico")
    cpuen_top = cpuen_species.sort_values(campaign_col_cpuen, ascending=False).iloc[0]
    cpueb_top = cpueb_species.sort_values(campaign_col_cpueb, ascending=False).iloc[0]
    point_diversity = diversity[~diversity["nome_ponto"].astype(str).str.contains(r"\(Geral\)")].copy()

    non_native = int(
        composition["Origem"].astype(str).str.contains("Não Nativo", case=False, na=False).sum()
    )
    distance_metrics = _distance_summary(distance)
    final_sufficiency = sufficiency.iloc[-1]
    cpue_positive = cpue[pd.to_numeric(cpue["abundancia_total"], errors="coerce").fillna(0) > 0].copy()
    if cpue_positive.empty:
        cpue_positive = cpue.copy()
    if not biometry.empty:
        for column in ["n", "cp_min_cm", "cp_media_cm", "cp_max_cm", "pc_min_g", "pc_max_g", "biomassa_g"]:
            biometry[column] = pd.to_numeric(biometry[column], errors="coerce")
        biometry_top = biometry.sort_values("biomassa_g", ascending=False).iloc[0]
        astyanax = biometry[biometry["especie"].astype(str).str.lower().eq("astyanax lacustris")]
        astyanax_row = astyanax.iloc[0] if not astyanax.empty else None
    else:
        biometry_top = None
        astyanax_row = None

    return {
        "taxa": int(composition["Nome Cientifico"].nunique()),
        "orders": int(len(orders)),
        "families": int(len(families)),
        "native": int(len(composition) - non_native),
        "non_native": non_native,
        "top_order": str(orders.iloc[0]["ordem"]),
        "top_order_n": int(orders.iloc[0]["numero_de_especies"]),
        "top_order_pct": float(orders.iloc[0]["percentual"]),
        "second_order": str(orders.iloc[1]["ordem"]),
        "second_order_n": int(orders.iloc[1]["numero_de_especies"]),
        "second_order_pct": float(orders.iloc[1]["percentual"]),
        "richness": richness,
        "abundance": abundance,
        "cpue": cpue,
        "cpue_positive": cpue_positive,
        "effort_min": float(pd.to_numeric(cpue["esforco_total_ponto"], errors="coerce").min()),
        "effort_max": float(pd.to_numeric(cpue["esforco_total_ponto"], errors="coerce").max()),
        "cpuen_top_species": str(cpuen_top["nome_cientifico"]),
        "cpuen_top": float(cpuen_top[campaign_col_cpuen]),
        "cpueb_top_species": str(cpueb_top["nome_cientifico"]),
        "cpueb_top": float(cpueb_top[campaign_col_cpueb]),
        "biometry": biometry,
        "biometry_species": int(len(biometry)) if not biometry.empty else 0,
        "biometry_total_biomass": float(biometry["biomassa_g"].sum()) if not biometry.empty else 0.0,
        "biometry_top_species": str(biometry_top["especie"]) if biometry_top is not None else "sem dados",
        "biometry_top_biomass": float(biometry_top["biomassa_g"]) if biometry_top is not None else 0.0,
        "astyanax_n": int(astyanax_row["n"]) if astyanax_row is not None else 0,
        "astyanax_cp_mean": float(astyanax_row["cp_media_cm"]) if astyanax_row is not None else 0.0,
        "astyanax_biomass": float(astyanax_row["biomassa_g"]) if astyanax_row is not None else 0.0,
        "diversity": point_diversity,
        **distance_metrics,
        "sobs": float(final_sufficiency["riqueza_obs_media"]),
        "jackknife": float(final_sufficiency["riqueza_est_jackknife1_media"]),
        "samples": int(final_sufficiency["n_amostras"]),
    }


def _build_report(metrics: dict) -> TechnicalReport:
    richness = metrics["richness"].sort_values("riqueza", ascending=False)
    abundance = metrics["abundance"].sort_values("abundancia_total", ascending=False)
    cpue = metrics["cpue"].sort_values("cpuen", ascending=False)
    cpue_positive = metrics["cpue_positive"].sort_values("cpuen", ascending=False)
    diversity = metrics["diversity"].sort_values("Shannon_H", ascending=False)

    evidence = (
        Evidence(
            evidence_id="E01",
            title="Composição taxonômica",
            section="Composição",
            observation=(
                f"Foram registrados {metrics['taxa']} táxons, distribuídos em "
                f"{metrics['orders']} ordens e {metrics['families']} famílias."
            ),
            sources=("01_tabela_composicao_ictiofauna.xlsx",),
            metrics={
                "Táxons": metrics["taxa"],
                "Ordens": metrics["orders"],
                "Famílias": metrics["families"],
                "Nativos": metrics["native"],
                "Não nativos": metrics["non_native"],
            },
            scope="Campanha C001-2026-06-SC, sete pontos amostrais.",
        ),
        Evidence(
            evidence_id="E02",
            title="Estrutura por ordem",
            section="Composição",
            observation=(
                f"{metrics['top_order']} reuniu {metrics['top_order_n']} táxons "
                f"({_fmt(metrics['top_order_pct'], 1)}%), seguida por "
                f"{metrics['second_order']} com {metrics['second_order_n']} "
                f"({_fmt(metrics['second_order_pct'], 1)}%)."
            ),
            sources=("04_df_riqueza_por_ordem_ictiofauna.xlsx",),
            metrics={
                "Ordem principal": metrics["top_order"],
                "Participação principal": f"{_fmt(metrics['top_order_pct'], 1)}%",
                "Segunda ordem": metrics["second_order"],
            },
            scope="Riqueza taxonômica da primeira campanha.",
        ),
        Evidence(
            evidence_id="E03",
            title="Riqueza espacial",
            section="Distribuição espacial",
            observation=(
                f"A riqueza variou de zero a {int(richness.iloc[0]['riqueza'])} táxons por ponto. "
                f"O maior valor ocorreu em {richness.iloc[0]['nome_ponto']}."
            ),
            sources=("02_df_riqueza_por_ponto_ictiofauna.xlsx",),
            metrics={
                "Maior riqueza": f"{richness.iloc[0]['nome_ponto']} ({int(richness.iloc[0]['riqueza'])})",
                "Pontos sem captura": ", ".join(
                    richness.loc[richness["riqueza"] == 0, "nome_ponto"].astype(str).tolist()
                ),
            },
            limitations=(
                "Ausência de captura nesta campanha não equivale a ausência ecológica da ictiofauna.",
            ),
            scope="Todos os métodos e tipos de amostragem.",
        ),
        Evidence(
            evidence_id="E04",
            title="Abundância quantitativa",
            section="Resultados quantitativos",
            observation=(
                f"A amostragem quantitativa registrou {int(abundance['abundancia_total'].sum())} indivíduos. "
                f"{abundance.iloc[0]['nome_ponto']} concentrou {int(abundance.iloc[0]['abundancia_total'])} "
                f"e {abundance.iloc[1]['nome_ponto']} registrou {int(abundance.iloc[1]['abundancia_total'])}."
            ),
            sources=("03_df_abundancia_por_ponto_ictiofauna.xlsx",),
            metrics={
                "Indivíduos quantitativos": int(abundance["abundancia_total"].sum()),
                "Maior abundância": abundance.iloc[0]["nome_ponto"],
            },
            scope="Pontos com esforço quantitativo.",
        ),
        Evidence(
            evidence_id="E05",
            title="CPUEn e CPUEb por ponto",
            section="Resultados quantitativos",
            observation=(
                f"{cpue_positive.iloc[0]['nome_ponto']} apresentou CPUEn de "
                f"{_fmt(cpue_positive.iloc[0]['cpuen'])} ind/100 m² e CPUEb de "
                f"{_fmt(cpue_positive.iloc[0]['cpueb'])} g/100 m². Entre os pontos com captura, "
                f"{cpue_positive.iloc[-1]['nome_ponto']} registrou CPUEn de "
                f"{_fmt(cpue_positive.iloc[-1]['cpuen'])} ind/100 m²."
            ),
            sources=("06_df_cpue_por_ponto_ictiofauna.xlsx",),
            metrics={
                "Maior CPUEn": f"{cpue_positive.iloc[0]['nome_ponto']} ({_fmt(cpue_positive.iloc[0]['cpuen'])})",
                "Maior CPUEb": f"{cpue.sort_values('cpueb', ascending=False).iloc[0]['nome_ponto']} ({_fmt(cpue.sort_values('cpueb', ascending=False).iloc[0]['cpueb'])})",
                "Fórmula de biomassa": "Número de indivíduos × PC_g por linha",
            },
            scope=(
                f"Amostragem quantitativa; esforços por ponto entre "
                f"{_fmt(metrics['effort_min'], 0)} e {_fmt(metrics['effort_max'], 0)} m²/100."
            ),
        ),
        Evidence(
            evidence_id="E06",
            title="Espécies com maior CPUE",
            section="Resultados quantitativos",
            observation=(
                f"{metrics['cpuen_top_species']} apresentou a maior CPUEn "
                f"({_fmt(metrics['cpuen_top'])} ind/100 m²) e a maior CPUEb "
                f"({_fmt(metrics['cpueb_top'])} g/100 m²)."
            ),
            sources=(
                "08_df_cpuen_por_especie_ictiofauna.xlsx",
                "09_df_cpueb_por_especie_ictiofauna.xlsx",
            ),
            metrics={
                "Espécie dominante em CPUEn": metrics["cpuen_top_species"],
                "CPUEn": _fmt(metrics["cpuen_top"]),
                "CPUEb": _fmt(metrics["cpueb_top"]),
            },
            limitations=(
                "A dominância observada está restrita à primeira campanha e aos pontos quantitativos.",
            ),
            scope="CPUEn e CPUEb agregadas por espécie.",
        ),
        Evidence(
            evidence_id="E10",
            title="Biometria e biomassa por espécie",
            section="Resultados quantitativos",
            observation=(
                f"A tabela biométrica consolidou {metrics['biometry_species']} espécies, com biomassa "
                f"total de {_fmt(metrics['biometry_total_biomass'], 1)} g. "
                f"{metrics['biometry_top_species']} apresentou a maior biomassa acumulada "
                f"({_fmt(metrics['biometry_top_biomass'], 1)} g)."
            ),
            sources=("13_tabela_biometria_biomassa_ictiofauna.xlsx",),
            metrics={
                "Espécies na tabela": metrics["biometry_species"],
                "Biomassa total": f"{_fmt(metrics['biometry_total_biomass'], 1)} g",
                "Astyanax lacustris": (
                    f"N={metrics['astyanax_n']}; CP médio={_fmt(metrics['astyanax_cp_mean'])} cm; "
                    f"biomassa={_fmt(metrics['astyanax_biomass'], 1)} g"
                ),
            },
            limitations=(
                "A tabela usa a planilha validada linha a linha como fonte; valores digitados como exemplo "
                "não substituem a fonte oficial sem nova revisão de dados.",
            ),
            scope="Capturas da campanha C001-2026-06-SC com N, CP_cm e PC_g informados.",
        ),
        Evidence(
            evidence_id="E07",
            title="Diversidade e equitabilidade",
            section="Diversidade",
            observation=(
                f"{diversity.iloc[0]['nome_ponto']} apresentou Shannon H' = "
                f"{_fmt(diversity.iloc[0]['Shannon_H'])} e Pielou J' = "
                f"{_fmt(diversity.iloc[0]['Pielou_J'])}; em {diversity.iloc[1]['nome_ponto']}, "
                f"H' = {_fmt(diversity.iloc[1]['Shannon_H'])} e J' = "
                f"{_fmt(diversity.iloc[1]['Pielou_J'])}."
            ),
            sources=("10_df_diversidade_alfa_ictiofauna.xlsx",),
            metrics={
                "Maior Shannon": diversity.iloc[0]["nome_ponto"],
                "Menor equitabilidade": diversity.sort_values("Pielou_J").iloc[0]["nome_ponto"],
            },
            interpretation=(
                "A menor equitabilidade no ponto com maior abundância é compatível com maior concentração "
                "dos indivíduos em poucas espécies."
            ),
            limitations=(
                "Os índices foram calculados para uma única campanha; pontos sem captura têm diversidade nula.",
            ),
            scope="Matriz quantitativa baseada em CPUEn.",
            inference_level="interpretativo",
        ),
        Evidence(
            evidence_id="E08",
            title="Similaridade entre pontos quantitativos",
            section="Diversidade",
            observation=(
                f"A maior similaridade de Bray-Curtis ocorreu entre {metrics['max_similarity_pair']}, "
                f"com {_fmt(metrics['max_similarity_pct'])}%. A menor similaridade foi "
                f"{_fmt(metrics['min_similarity_pct'])}%."
            ),
            sources=("11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx",),
            metrics={
                "Maior similaridade de Bray-Curtis": f"{metrics['max_similarity_pair']} ({_fmt(metrics['max_similarity_pct'])}%)",
                "Menor similaridade de Bray-Curtis": f"{metrics['min_similarity_pair']} ({_fmt(metrics['min_similarity_pct'])}%)",
            },
            interpretation=(
                "Os valores indicam forte diferenciação na estrutura quantitativa observada entre os pontos."
            ),
            limitations=(
                "A comparação é descritiva e não constitui teste de diferença estatística.",
            ),
            scope="Matriz de CPUEn da primeira campanha.",
            inference_level="interpretativo",
        ),
        Evidence(
            evidence_id="E09",
            title="Suficiência amostral",
            section="Suficiência",
            observation=(
                f"Com {metrics['samples']} unidades quantitativas, a riqueza observada média final foi "
                f"{_fmt(metrics['sobs'], 1)} e a estimativa Jackknife 1 foi {_fmt(metrics['jackknife'], 1)}."
            ),
            sources=("12_df_curva_suficiencia_ictiofauna.xlsx",),
            metrics={
                "Unidades quantitativas": metrics["samples"],
                "Riqueza observada": _fmt(metrics["sobs"], 1),
                "Jackknife 1": _fmt(metrics["jackknife"], 1),
            },
            interpretation=(
                "A diferença entre riqueza observada e estimada indica potencial de acréscimo taxonômico "
                "com a continuidade do diagnóstico."
            ),
            limitations=(
                "A curva deve ser atualizada após a segunda campanha para ampliar a base temporal.",
            ),
            scope="Aleatorização dos pontos quantitativos da primeira campanha.",
            inference_level="interpretativo",
        ),
    )

    sections = (
        NarrativeSection(
            section_id="escopo",
            title="Escopo da campanha",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        "A primeira campanha do diagnóstico de ictiofauna foi realizada em 17 e 18 de junho "
                        "de 2026, abrangendo sete pontos amostrais. Os produtos foram estruturados para um "
                        "estudo de duas campanhas, adotando o padrão FERSAM001 para comparações diretas."
                    ),
                    evidence_ids=("E01",),
                    role="contexto",
                ),
            ),
            table_rows=(
                ("Projeto", "VIRITA001 — Diagnóstico da ictiofauna do Projeto Itabrita"),
                ("Campanha", "C001-2026-06-SC — junho de 2026"),
                ("Pontos", "Ictio_01 a Ictio_07"),
                ("Próxima etapa", "Incorporar a segunda campanha ao mesmo conjunto comparativo"),
            ),
        ),
        NarrativeSection(
            section_id="composicao",
            title="Composição taxonômica",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A campanha registrou {metrics['taxa']} táxons, distribuídos em "
                        f"{metrics['orders']} ordens e {metrics['families']} famílias. "
                        f"{metrics['top_order']} e {metrics['second_order']} reuniram, em conjunto, "
                        f"{metrics['top_order_n'] + metrics['second_order_n']} táxons."
                    ),
                    evidence_ids=("E01", "E02"),
                ),
                NarrativeParagraph(
                    text=(
                        f"O cadastro classificou {metrics['native']} táxons como nativos e "
                        f"{metrics['non_native']} como não nativos. A composição deverá ser novamente "
                        "conferida na integração com a segunda campanha."
                    ),
                    evidence_ids=("E01",),
                    role="sintese",
                ),
            ),
            figures=(
                FigureReference(
                    "04_grafico_riqueza_ordem_barras_ictiofauna.png",
                    "Riqueza taxonômica por ordem.",
                    "04_df_riqueza_por_ordem_ictiofauna.xlsx",
                ),
                FigureReference(
                    "04_grafico_riqueza_familia_barras_ictiofauna.png",
                    "Riqueza taxonômica por família.",
                    "04_df_riqueza_por_familia_ictiofauna.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="distribuicao",
            title="Distribuição espacial",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A maior riqueza foi registrada em {richness.iloc[0]['nome_ponto']}, com "
                        f"{int(richness.iloc[0]['riqueza'])} táxons. "
                        f"{richness.iloc[1]['nome_ponto']} apresentou {int(richness.iloc[1]['riqueza'])}, "
                        f"enquanto {richness.iloc[-1]['nome_ponto']} e "
                        f"{richness.iloc[-2]['nome_ponto']} não apresentaram captura."
                    ),
                    evidence_ids=("E03",),
                ),
                NarrativeParagraph(
                    text=(
                        "Os registros sem captura permanecem representados como esforço realizado. "
                        "A confirmação de padrões espaciais depende da repetição amostral prevista na segunda campanha."
                    ),
                    evidence_ids=("E03",),
                    role="limitacao",
                ),
            ),
            figures=(
                FigureReference(
                    "02_grafico_riqueza_por_ponto_ictiofauna.png",
                    "Riqueza por ponto na primeira campanha.",
                    "02_df_riqueza_por_ponto_ictiofauna.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="quantitativos",
            title="Abundância, CPUEn e CPUEb",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A amostragem quantitativa totalizou {int(abundance['abundancia_total'].sum())} "
                        f"indivíduos. {abundance.iloc[0]['nome_ponto']} registrou "
                        f"{int(abundance.iloc[0]['abundancia_total'])} indivíduos, contra "
                        f"{int(abundance.iloc[1]['abundancia_total'])} em "
                        f"{abundance.iloc[1]['nome_ponto']}."
                    ),
                    evidence_ids=("E04",),
                ),
                NarrativeParagraph(
                    text=(
                        f"Entre os pontos com captura, a CPUEn variou de "
                        f"{_fmt(cpue_positive.iloc[-1]['cpuen'])} a "
                        f"{_fmt(cpue_positive.iloc[0]['cpuen'])} ind/100 m², e a CPUEb variou de "
                        f"{_fmt(cpue_positive['cpueb'].min())} a {_fmt(cpue_positive['cpueb'].max())} g/100 m². "
                        f"{metrics['cpuen_top_species']} apresentou os maiores valores por espécie."
                    ),
                    evidence_ids=("E05", "E06"),
                    role="comparacao",
                ),
            ),
            figures=(
                FigureReference(
                    "03_grafico_abundancia_por_ponto_ictiofauna.png",
                    "Abundância quantitativa por ponto.",
                    "03_df_abundancia_por_ponto_ictiofauna.xlsx",
                ),
                FigureReference(
                    "06_grafico_cpuen_por_ponto_ictiofauna.png",
                    "CPUEn por ponto.",
                    "06_df_cpue_por_ponto_ictiofauna.xlsx",
                ),
                FigureReference(
                    "07_grafico_cpueb_por_ponto_ictiofauna.png",
                    "CPUEb por ponto, calculada com biomassa linha a linha.",
                    "06_df_cpue_por_ponto_ictiofauna.xlsx",
                ),
                FigureReference(
                    "08_grafico_cpuen_por_especie_ictiofauna.png",
                    "CPUEn por espécie.",
                    "08_df_cpuen_por_especie_ictiofauna.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="biometria",
            title="Biometria e biomassa",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A Tabela 13 consolida N, comprimento padrão, peso corporal e biomassa por espécie. "
                        f"A biomassa total calculada a partir da planilha linha a linha foi "
                        f"{_fmt(metrics['biometry_total_biomass'], 1)} g, com maior contribuição de "
                        f"{metrics['biometry_top_species']}."
                    ),
                    evidence_ids=("E10",),
                ),
                NarrativeParagraph(
                    text=(
                        f"Para Astyanax lacustris, a fonte validada resultou em N={metrics['astyanax_n']}, "
                        f"CP médio de {_fmt(metrics['astyanax_cp_mean'])} cm e biomassa de "
                        f"{_fmt(metrics['astyanax_biomass'], 1)} g."
                    ),
                    evidence_ids=("E10",),
                    role="comparacao",
                ),
            ),
            table_rows=(
                ("Produto", "13_tabela_biometria_biomassa_ictiofauna.xlsx"),
                ("Espécies consolidadas", str(metrics["biometry_species"])),
                ("Maior biomassa", f"{metrics['biometry_top_species']} ({_fmt(metrics['biometry_top_biomass'], 1)} g)"),
                (
                    "Astyanax lacustris",
                    f"N={metrics['astyanax_n']}; CP médio={_fmt(metrics['astyanax_cp_mean'])} cm; "
                    f"biomassa={_fmt(metrics['astyanax_biomass'], 1)} g",
                ),
            ),
        ),
        NarrativeSection(
            section_id="diversidade",
            title="Diversidade e similaridade",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"{diversity.iloc[0]['nome_ponto']} apresentou maior diversidade e equitabilidade "
                        f"(H' = {_fmt(diversity.iloc[0]['Shannon_H'])}; "
                        f"J' = {_fmt(diversity.iloc[0]['Pielou_J'])}). Em "
                        f"{diversity.iloc[1]['nome_ponto']}, H' foi {_fmt(diversity.iloc[1]['Shannon_H'])} "
                        f"e J' foi {_fmt(diversity.iloc[1]['Pielou_J'])}."
                    ),
                    evidence_ids=("E07",),
                ),
                NarrativeParagraph(
                    text=(
                        f"A maior similaridade de Bray-Curtis foi de "
                        f"{_fmt(metrics['max_similarity_pct'])}% entre {metrics['max_similarity_pair']}; "
                        f"a menor foi {_fmt(metrics['min_similarity_pct'])}%, evidenciando estruturas "
                        "quantitativas distintas na campanha avaliada."
                    ),
                    evidence_ids=("E08",),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "10_grafico_diversidade_alfa_ictiofauna.png",
                    "Diversidade de Shannon e equitabilidade de Pielou.",
                    "10_df_diversidade_alfa_ictiofauna.xlsx",
                ),
                FigureReference(
                    "11_dendrograma_similaridade_ictiofauna_seca_chuva_somadas.png",
                    "Similaridade de Bray-Curtis entre os pontos quantitativos.",
                    "11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="suficiencia",
            title="Suficiência e síntese",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A curva quantitativa terminou com riqueza observada de "
                        f"{_fmt(metrics['sobs'], 1)} e estimativa Jackknife 1 de "
                        f"{_fmt(metrics['jackknife'], 1)} táxons."
                    ),
                    evidence_ids=("E09",),
                ),
                NarrativeParagraph(
                    text=(
                        "A primeira campanha estabelece a linha de base do diagnóstico. A segunda campanha "
                        "deverá ampliar o número de unidades, permitir a comparação direta entre períodos e "
                        "recalibrar composição, CPUE, diversidade, similaridade e suficiência."
                    ),
                    evidence_ids=("E03", "E06", "E09"),
                    role="sintese",
                    inference_level="interpretativo",
                ),
            ),
            figures=(
                FigureReference(
                    "12_curva_suficiencia_amostral_ictiofauna.png",
                    "Curva de suficiência amostral da primeira campanha.",
                    "12_df_curva_suficiencia_ictiofauna.xlsx",
                ),
            ),
        ),
    )

    return TechnicalReport(
        title="Resultados de ictiofauna — Campanha 1",
        subtitle="Diagnóstico da ictiofauna do Projeto Itabrita",
        project_code="VIRITA001",
        group="Ictiofauna",
        period="17 e 18 de junho de 2026",
        metadata={
            "Cliente": "Virtual Ambiental",
            "Município": "São Gonçalo do Pará/MG",
            "Campanha": "C001-2026-06-SC",
            "Padrão analítico": "FERSAM001 — estudos de duas campanhas",
        },
        sections=sections,
        evidence=evidence,
        editorial_profile={
            "policy": POLICY_REFERENCE,
            "policy_revision": POLICY_REVISION,
            "visual_reference": "FERSAM001",
            "inference_limit": "Descritivo e interpretativo, sem atribuição causal",
            "biomass_formula": "Número de indivíduos × PC_g por linha",
        },
        report_status="resultado técnico",
    )


def main() -> None:
    metrics = _load_metrics()
    report = _build_report(metrics)
    issues = validate_technical_report(report, source_dir=OUTPUT_DIR)
    html = render_technical_report(
        report,
        source_dir=OUTPUT_DIR,
        validation_issues=issues,
        embed_assets=True,
    )
    html = html.replace("--blue: #002060;", "--blue: #11420C;")
    html = html.replace("--blue-2: #1f4e79;", "--blue-2: #3F5F3B;")
    html = html.replace("--blue-soft: #eaf1f8;", "--blue-soft: #eef5ec;")

    html_path = OUTPUT_DIR / "relatorio_tecnico_ictiofauna_campanha_1.html"
    evidence_path = OUTPUT_DIR / "evidencias_relatorio_ictiofauna_campanha_1.json"
    validation_path = OUTPUT_DIR / "validacao_textual_ictiofauna_campanha_1.json"
    manifest_path = OUTPUT_DIR / "manifesto_entrega_ictiofauna_campanha_1.json"

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
        "html": str(html_path),
        "policy_reference": POLICY_REFERENCE,
        "policy_revision": POLICY_REVISION,
    }
    validation_path.write_text(
        json.dumps(validation_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    delivery_files = sorted(
        path
        for path in OUTPUT_DIR.iterdir()
        if path.is_file()
        and path.name not in {"desktop.ini", manifest_path.name}
        and not path.name.startswith(".")
        and not path.name.startswith("~$")
    )
    manifest_payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": 189,
        "project_code": "VIRITA001",
        "canonical_key": "VIRITA001__diagnostico_da_ictiofauna_do_projeto_itabrita",
        "campaign": "C001-2026-06-SC",
        "output_dir": str(OUTPUT_DIR),
        "products_count": len(delivery_files),
        "files": build_file_manifest(delivery_files),
        "validation": validation_payload,
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(validation_payload, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
