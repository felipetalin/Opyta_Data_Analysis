from __future__ import annotations

import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "src" / "opyta_analysis").exists())
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.audit_utils import build_file_manifest  # noqa: E402
from opyta_analysis.textual.html import render_technical_report  # noqa: E402
from opyta_analysis.textual.models import (  # noqa: E402
    Evidence,
    FigureReference,
    NarrativeParagraph,
    NarrativeSection,
    TechnicalReport,
)
from opyta_analysis.textual.validation import validate_technical_report  # noqa: E402


OUTPUT_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
)
POLICY_REFERENCE = "docs/PADRAO_MESTRE_REDACAO_TECNICA_OPYTA.md"
PATTERN_REFERENCE = "docs/patterns/linguagem_tecnica_rastreavel.md"
SOURCE_REFERENCE = "docs/projects/GEOARC001_ARCELOR_ICTIOFAUNA.md"


def _read(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_excel(path)


def _fmt(value: float, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_int(value: int | float) -> str:
    return f"{int(round(float(value))):,}".replace(",", ".")


def _norm_text(value: object) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def _top_species_by_total(frame: pd.DataFrame) -> tuple[str, float]:
    value_cols = [column for column in frame.columns if column != "nome_cientifico"]
    totals = frame[value_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    ranked = (
        frame.assign(total=totals)
        .sort_values(["total", "nome_cientifico"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if ranked.empty:
        return "", 0.0
    top = ranked.iloc[0]
    return str(top["nome_cientifico"]), float(top["total"])


def _load_metrics() -> dict:
    composition = _read("01_tabela_composicao_ictiofauna.xlsx")
    richness = _read("02_df_riqueza_por_ponto_ictiofauna.xlsx")
    abundance = _read("03_df_abundancia_por_ponto_ictiofauna.xlsx")
    cpue = _read("06_df_cpue_por_ponto_ictiofauna.xlsx")
    cpuen_species = _read("08_df_cpuen_por_especie_ictiofauna.xlsx")
    cpueb_species = _read("09_df_cpueb_por_especie_ictiofauna.xlsx")
    diversity = _read("10_df_diversidade_alfa_ictiofauna.xlsx")
    bray = _read("11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx")
    sufficiency = _read("12_df_curva_suficiencia_ictiofauna.xlsx")

    cpuen_species_name, cpuen_species_total = _top_species_by_total(cpuen_species)
    cpueb_species_name, cpueb_species_total = _top_species_by_total(cpueb_species)

    diversity_points = diversity[~diversity["nome_ponto"].astype(str).str.contains(r"\(Geral\)")].copy()
    mean_shannon = float(pd.to_numeric(diversity_points["Shannon_H"], errors="coerce").mean())
    mean_pielou = float(pd.to_numeric(diversity_points["Pielou_J"], errors="coerce").mean())
    final_curve = sufficiency.iloc[-1]
    bray_matrix = bray.drop(columns=[bray.columns[0]]).apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if bray_matrix.size:
        pairwise_distances = bray_matrix[np.triu_indices_from(bray_matrix, k=1)]
        bray_similarity_pct = float(np.nanmean(1.0 - pairwise_distances) * 100.0)
    else:
        bray_similarity_pct = 0.0

    rich_sorted = richness.sort_values("riqueza", ascending=False)
    abundance_sorted = abundance.sort_values("abundancia_total", ascending=False)
    cpue_sorted = cpue.sort_values("cpuen", ascending=False)
    origin_norm = composition["Origem"].map(_norm_text)
    order_counts = composition["Ordem"].value_counts()
    family_counts = composition["Familia"].value_counts()
    years = sorted(
        {
            int(year)
            for year in richness["nome_campanha"].astype(str).str.extract(r"(20\d{2}|19\d{2})")[0].dropna()
        }
    )
    abundance_by_point = (
        abundance.assign(abundancia_total=pd.to_numeric(abundance["abundancia_total"], errors="coerce").fillna(0))
        .groupby("nome_ponto", as_index=False)["abundancia_total"]
        .sum()
    )

    return {
        "taxa": int(composition["Nome Cientifico"].nunique()),
        "campaigns": int(richness["nome_campanha"].nunique()),
        "points": int(richness["nome_ponto"].nunique()),
        "points_with_results": int((abundance_by_point["abundancia_total"] > 0).sum()),
        "years": years,
        "total_abundance": int(abundance["abundancia_total"].sum()),
        "native": int((origin_norm == "nativo").sum()),
        "non_native": int(origin_norm.str.contains("nao nativo", na=False).sum()),
        "orders": int(composition["Ordem"].nunique()),
        "families": int(composition["Familia"].nunique()),
        "dominant_order": str(order_counts.index[0]),
        "dominant_order_count": int(order_counts.iloc[0]),
        "dominant_family": str(family_counts.index[0]),
        "dominant_family_count": int(family_counts.iloc[0]),
        "richness_max_point": str(rich_sorted.iloc[0]["nome_ponto"]),
        "richness_max_campaign": str(rich_sorted.iloc[0]["nome_campanha"]),
        "richness_max_value": int(rich_sorted.iloc[0]["riqueza"]),
        "abundance_max_point": str(abundance_sorted.iloc[0]["nome_ponto"]),
        "abundance_max_campaign": str(abundance_sorted.iloc[0]["nome_campanha"]),
        "abundance_max_value": int(abundance_sorted.iloc[0]["abundancia_total"]),
        "cpue_max_point": str(cpue_sorted.iloc[0]["nome_ponto"]),
        "cpue_max_campaign": str(cpue_sorted.iloc[0]["nome_campanha"]),
        "cpue_max_cpuen": float(cpue_sorted.iloc[0]["cpuen"]),
        "cpue_max_cpueb": float(cpue_sorted.iloc[0]["cpueb"]),
        "cpuen_species": cpuen_species_name,
        "cpuen_species_value": cpuen_species_total,
        "cpueb_species": cpueb_species_name,
        "cpueb_species_value": cpueb_species_total,
        "mean_shannon": mean_shannon,
        "mean_pielou": mean_pielou,
        "sobs": float(final_curve["riqueza_obs_media"]),
        "jackknife": float(final_curve["riqueza_est_jackknife1_media"]),
        "samples": int(final_curve["n_amostras"]),
        "bray_similarity_pct": bray_similarity_pct,
    }


def _build_report(metrics: dict) -> TechnicalReport:
    evidence = (
        Evidence(
            evidence_id="E01",
            title="Escopo da série",
            section="Escopo",
            observation=(
                f"A entrega consolida {metrics['campaigns']} campanhas, {metrics['points']} pontos e "
                f"{metrics['taxa']} táxons na série longa de ictiofauna do GEOARC001, com "
                f"{_fmt_int(metrics['total_abundance'])} indivíduos registrados."
            ),
            sources=("01_tabela_composicao_ictiofauna.xlsx",),
            metrics={
                "Campanhas": metrics["campaigns"],
                "Pontos": metrics["points"],
                "Pontos com captura": metrics["points_with_results"],
                "Táxons": metrics["taxa"],
                "Nativos": metrics["native"],
                "Não nativos": metrics["non_native"],
                "Indivíduos": _fmt_int(metrics["total_abundance"]),
            },
            scope="Série longa multicampanha GEOARC001.",
        ),
        Evidence(
            evidence_id="E07",
            title="Composição taxonômica",
            section="Composição",
            observation=(
                f"A composição reúne {metrics['orders']} ordens e {metrics['families']} famílias; "
                f"{metrics['dominant_order']} concentrou {metrics['dominant_order_count']} espécies e "
                f"{metrics['dominant_family']} concentrou {metrics['dominant_family_count']} espécies."
            ),
            sources=(
                "01_tabela_composicao_ictiofauna.xlsx",
                "04_df_riqueza_por_ordem_ictiofauna.xlsx",
                "04_df_riqueza_por_familia_ictiofauna.xlsx",
            ),
            metrics={
                "Ordens": metrics["orders"],
                "Famílias": metrics["families"],
                "Ordem mais rica": f"{metrics['dominant_order']} ({metrics['dominant_order_count']})",
                "Família mais rica": f"{metrics['dominant_family']} ({metrics['dominant_family_count']})",
            },
            scope="Composição taxonômica consolidada para a série GEOARC001.",
        ),
        Evidence(
            evidence_id="E02",
            title="Riqueza e abundância espaciais",
            section="Distribuição espacial",
            observation=(
                f"A maior riqueza ocorreu em {metrics['richness_max_point']} ({metrics['richness_max_value']} táxons; "
                f"{metrics['richness_max_campaign']}) e a maior abundância em {metrics['abundance_max_point']} "
                f"({_fmt_int(metrics['abundance_max_value'])} indivíduos; {metrics['abundance_max_campaign']})."
            ),
            sources=(
                "02_df_riqueza_por_ponto_ictiofauna.xlsx",
                "03_df_abundancia_por_ponto_ictiofauna.xlsx",
            ),
            metrics={
                "Maior riqueza": f"{metrics['richness_max_point']} ({metrics['richness_max_value']}; {metrics['richness_max_campaign']})",
                "Maior abundância": f"{metrics['abundance_max_point']} ({_fmt_int(metrics['abundance_max_value'])}; {metrics['abundance_max_campaign']})",
            },
            scope="Amostragem por ponto ao longo das 18 campanhas.",
        ),
        Evidence(
            evidence_id="E03",
            title="CPUEn e CPUEb por ponto",
            section="Resultados quantitativos",
            observation=(
                f"{metrics['cpue_max_point']} apresentou CPUEn de {_fmt(metrics['cpue_max_cpuen'])} ind/100 m² e "
                f"CPUEb de {_fmt(metrics['cpue_max_cpueb'])} g/100 m² em {metrics['cpue_max_campaign']}."
            ),
            sources=("06_df_cpue_por_ponto_ictiofauna.xlsx",),
            metrics={
                "Ponto líder": metrics["cpue_max_point"],
                "Campanha": metrics["cpue_max_campaign"],
                "CPUEn": _fmt(metrics["cpue_max_cpuen"]),
                "CPUEb": _fmt(metrics["cpue_max_cpueb"]),
            },
            scope="CPUE calculado pela planilha consolidada validada.",
        ),
        Evidence(
            evidence_id="E04",
            title="Espécies dominantes",
            section="Resultados quantitativos",
            observation=(
                f"{metrics['cpuen_species']} liderou o acumulado de CPUEn ({_fmt(metrics['cpuen_species_value'])}) e "
                f"{metrics['cpueb_species']} liderou o acumulado de CPUEb ({_fmt(metrics['cpueb_species_value'])})."
            ),
            sources=(
                "08_df_cpuen_por_especie_ictiofauna.xlsx",
                "08B_df_cpuen_por_especie_ponto_ictiofauna.xlsx",
                "09_df_cpueb_por_especie_ictiofauna.xlsx",
                "09B_df_cpueb_por_especie_ponto_ictiofauna.xlsx",
            ),
            metrics={
                "Espécie líder em CPUEn": metrics["cpuen_species"],
                "CPUEn acumulada": _fmt(metrics["cpuen_species_value"]),
                "Espécie líder em CPUEb": metrics["cpueb_species"],
                "CPUEb acumulada": _fmt(metrics["cpueb_species_value"]),
            },
            scope="Ranking agregado por espécie.",
        ),
        Evidence(
            evidence_id="E05",
            title="Diversidade e suficiência",
            section="Diversidade",
            observation=(
                f"A diversidade média de Shannon e Pielou foi {_fmt(metrics['mean_shannon'])} e {_fmt(metrics['mean_pielou'])}. "
                f"A curva de suficiência fechou com Sobs = {_fmt(metrics['sobs'])}, Jackknife-1 = {_fmt(metrics['jackknife'])} e "
                f"{metrics['samples']} amostras."
            ),
            sources=(
                "10_df_diversidade_alfa_ictiofauna.xlsx",
                "12_df_curva_suficiencia_ictiofauna.xlsx",
            ),
            metrics={
                "Shannon médio": _fmt(metrics["mean_shannon"]),
                "Pielou médio": _fmt(metrics["mean_pielou"]),
                "Sobs final": _fmt(metrics["sobs"]),
                "Jackknife-1": _fmt(metrics["jackknife"]),
            },
            limitations=(
                "Os índices sintetizam a série longa e não equivalem, isoladamente, a inferência causal sobre impacto.",
            ),
            scope="Síntese temporal multicampanha.",
        ),
        Evidence(
            evidence_id="E06",
            title="Similaridade Bray-Curtis",
            section="Estrutura comunitária",
            observation=(
                f"A similaridade média do bloco consolidado foi de {_fmt(metrics['bray_similarity_pct'])}% na matriz Bray-Curtis."
            ),
            sources=("11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx",),
            metrics={
                "Similaridade de referência": _fmt(metrics["bray_similarity_pct"]),
            },
            scope="Matriz Bray-Curtis do consolidado seco-chuva somado.",
        ),
    )

    cpuen_year_figures = tuple(
        FigureReference(
            filename=f"06_grafico_cpuen_por_ano_{year}_ictiofauna.png",
            caption=f"CPUEn por ponto - {year}.",
            source_workbook="06_df_cpue_por_ponto_ictiofauna.xlsx",
        )
        for year in metrics["years"]
    )
    cpueb_year_figures = tuple(
        FigureReference(
            filename=f"07_grafico_cpueb_por_ano_{year}_ictiofauna.png",
            caption=f"CPUEb por ponto - {year}.",
            source_workbook="06_df_cpue_por_ponto_ictiofauna.xlsx",
        )
        for year in metrics["years"]
    )

    sections = (
        NarrativeSection(
            section_id="escopo",
            title="Escopo e identidade",
            table_rows=(
                ("Projeto", "GEOARC001 — Monitoramento Arcelor"),
                ("Grupo", "Ictiofauna"),
                ("Recorte", "18 campanhas de 2022 a 2026"),
                ("Pontos", str(metrics["points"])),
                ("Pontos com captura", str(metrics["points_with_results"])),
                ("Indivíduos", _fmt_int(metrics["total_abundance"])),
            ),
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        "O relatório segue o padrão de linguagem técnica rastreável, com separação explícita entre resultado, "
                        "comparação, interpretação e lastro de auditoria."
                    ),
                    evidence_ids=("E01",),
                    role="contexto",
                    inference_level="descritivo",
                ),
                NarrativeParagraph(
                    text=(
                        f"A base consolidada reúne {metrics['campaigns']} campanhas entre 2022 e 2026, "
                        f"{metrics['points']} pontos amostrais, {metrics['points_with_results']} pontos com captura, "
                        f"{metrics['taxa']} táxons e {_fmt_int(metrics['total_abundance'])} indivíduos."
                    ),
                    evidence_ids=("E01",),
                    role="resultado",
                    inference_level="descritivo",
                ),
            ),
            figures=(
                FigureReference(
                    filename="04A_tabela_sintese_ocorrencia_ictiofauna.xlsx",
                    caption="Tabela síntese de ocorrência multicampanha.",
                ),
            ),
        ),
        NarrativeSection(
            section_id="composicao",
            title="Composição taxonômica",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"Foram registrados {metrics['taxa']} táxons distribuídos em {metrics['orders']} ordens e "
                        f"{metrics['families']} famílias. A origem informada na planilha aponta {metrics['native']} táxons "
                        f"nativos e {metrics['non_native']} não nativos."
                    ),
                    evidence_ids=("E01", "E07"),
                    role="resultado",
                    inference_level="descritivo",
                ),
                NarrativeParagraph(
                    text=(
                        f"A maior contribuição taxonômica ocorreu em {metrics['dominant_order']} "
                        f"({metrics['dominant_order_count']} espécies) e em {metrics['dominant_family']} "
                        f"({metrics['dominant_family_count']} espécies), mantendo o predomínio esperado de pequenos "
                        "Characiformes no conjunto amostrado."
                    ),
                    evidence_ids=("E07",),
                    role="sintese",
                    inference_level="comparativo",
                ),
            ),
            figures=(
                FigureReference(
                    filename="04_grafico_riqueza_ordem_barras_ictiofauna.png",
                    caption="Riqueza por ordem.",
                    source_workbook="04_df_riqueza_por_ordem_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="04_grafico_riqueza_familia_barras_ictiofauna.png",
                    caption="Riqueza por família.",
                    source_workbook="04_df_riqueza_por_familia_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="05_grafico_riqueza_ordem_rosca_ictiofauna.png",
                    caption="Participação relativa das ordens.",
                    source_workbook="04_df_riqueza_por_ordem_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="05_grafico_riqueza_familia_rosca_ictiofauna.png",
                    caption="Participação relativa das famílias.",
                    source_workbook="04_df_riqueza_por_familia_ictiofauna.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="espacial",
            title="Distribuição espacial",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A distribuição espacial concentrou os máximos em {metrics['richness_max_point']} para riqueza "
                        f"({metrics['richness_max_value']} táxons em {metrics['richness_max_campaign']}) e em "
                        f"{metrics['abundance_max_point']} para abundância ({_fmt_int(metrics['abundance_max_value'])} "
                        f"indivíduos em {metrics['abundance_max_campaign']})."
                    ),
                    evidence_ids=("E02", "E03"),
                    role="resultado",
                    inference_level="comparativo",
                ),
                NarrativeParagraph(
                    text=(
                        "Os painéis de ocorrência por campanha e por ponto complementam a leitura espacial ao separar presença "
                        "recorrente, captura pontual e lacunas de registro ao longo da série."
                    ),
                    evidence_ids=("E02", "E07"),
                    role="sintese",
                    inference_level="comparativo",
                ),
            ),
            figures=(
                FigureReference(
                    filename="02_grafico_riqueza_por_ponto_ictiofauna.png",
                    caption="Riqueza por ponto e campanha.",
                    source_workbook="02_df_riqueza_por_ponto_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="03_grafico_abundancia_por_ponto_ictiofauna.png",
                    caption="Abundância total por ponto e campanha.",
                    source_workbook="03_df_abundancia_por_ponto_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="04B_grafico_frequencia_ocorrencia_por_campanha_ictiofauna.png",
                    caption="Frequência de ocorrência por campanha.",
                    source_workbook="04A_tabela_sintese_ocorrencia_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="04C_grafico_frequencia_ocorrencia_por_ponto_ictiofauna.png",
                    caption="Frequência de ocorrência por ponto.",
                    source_workbook="04A_tabela_sintese_ocorrencia_ictiofauna.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="quantitativo",
            title="Resultados quantitativos",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A maior CPUEn por ponto ocorreu em {metrics['cpue_max_point']} "
                        f"({_fmt(metrics['cpue_max_cpuen'])} ind/100 m² em {metrics['cpue_max_campaign']}); no mesmo registro, "
                        f"a CPUEb foi {_fmt(metrics['cpue_max_cpueb'])} g/100 m²."
                    ),
                    evidence_ids=("E03", "E04"),
                    role="sintese",
                    inference_level="comparativo",
                ),
                NarrativeParagraph(
                    text=(
                        f"No ranking acumulado por espécie, {metrics['cpuen_species']} liderou CPUEn "
                        f"({_fmt(metrics['cpuen_species_value'])}) e {metrics['cpueb_species']} liderou CPUEb "
                        f"({_fmt(metrics['cpueb_species_value'])}). Os painéis anuais mantêm a separação por campanha para "
                        "preservar a leitura temporal da série."
                    ),
                    evidence_ids=("E04",),
                    role="resultado",
                    inference_level="comparativo",
                ),
            ),
            figures=(
                *cpuen_year_figures,
                *cpueb_year_figures,
                FigureReference(
                    filename="08_grafico_cpuen_por_especie_ictiofauna.png",
                    caption="CPUEn por espécie.",
                    source_workbook="08_df_cpuen_por_especie_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="08B_grafico_cpuen_por_especie_ponto_ictiofauna.png",
                    caption="CPUEn por espécie e ponto amostral.",
                    source_workbook="08B_df_cpuen_por_especie_ponto_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="09_grafico_cpueb_por_especie_ictiofauna.png",
                    caption="CPUEb por espécie.",
                    source_workbook="09_df_cpueb_por_especie_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="09B_grafico_cpueb_por_especie_ponto_ictiofauna.png",
                    caption="CPUEb por espécie e ponto amostral.",
                    source_workbook="09B_df_cpueb_por_especie_ponto_ictiofauna.xlsx",
                ),
            ),
        ),
        NarrativeSection(
            section_id="diversidade",
            title="Diversidade e estrutura comunitária",
            paragraphs=(
                NarrativeParagraph(
                    text=(
                        f"A diversidade média foi {_fmt(metrics['mean_shannon'])} para Shannon e {_fmt(metrics['mean_pielou'])} "
                        f"para Pielou. A curva de suficiência encerrou com Sobs = {_fmt(metrics['sobs'])} e "
                        f"Jackknife-1 = {_fmt(metrics['jackknife'])} após {metrics['samples']} amostras."
                    ),
                    evidence_ids=("E05", "E06"),
                    role="interpretacao",
                    inference_level="interpretativo",
                ),
                NarrativeParagraph(
                    text=(
                        f"A matriz Bray-Curtis resultou em similaridade de referência de {_fmt(metrics['bray_similarity_pct'])}%. "
                        "A leitura permanece descritiva e proporcional ao desenho amostral, sem atribuição causal."
                    ),
                    evidence_ids=("E06",),
                    role="sintese",
                    inference_level="comparativo",
                ),
            ),
            figures=(
                FigureReference(
                    filename="10_grafico_diversidade_alfa_ictiofauna.png",
                    caption="Shannon e Pielou por ponto e campanha.",
                    source_workbook="10_df_diversidade_alfa_ictiofauna.xlsx",
                ),
                FigureReference(
                    filename="11_dendrograma_similaridade_ictiofauna_seca_chuva_somadas.png",
                    caption="Dendrograma Bray-Curtis do consolidado seco-chuva somado.",
                    source_workbook="11_df_distancias_braycurtis_ictiofauna_seca_chuva_somadas.xlsx",
                ),
                FigureReference(
                    filename="12_curva_suficiencia_amostral_ictiofauna.png",
                    caption="Curva de suficiência amostral.",
                    source_workbook="12_df_curva_suficiencia_ictiofauna.xlsx",
                ),
            ),
        ),
    )

    return TechnicalReport(
        title="Resultados de ictiofauna — GEOARC001",
        subtitle="Monitoramento Arcelor",
        project_code="GEOARC001",
        group="Ictiofauna",
        period="C001 a C018 · 2022 a 2026",
        metadata={
            "Cliente": "Geomil Serviços de Mineração Ltda.",
            "Projeto": "Monitoramento Arcelor",
            "Recorte temporal": "18 campanhas multicampanha",
            "Pasta de saída": str(OUTPUT_DIR),
        },
        sections=sections,
        evidence=evidence,
        editorial_profile={
            "policy": POLICY_REFERENCE,
            "pattern": PATTERN_REFERENCE,
            "reference": SOURCE_REFERENCE,
            "inference_limit": "Descritivo e comparativo, sem atribuição causal.",
            "layout_reference": "GEOARC001 — perfil revisado para série longa e leitura em relatório.",
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

    html_path = OUTPUT_DIR / "relatorio_tecnico_ictiofauna_geoarc001.html"
    evidence_path = OUTPUT_DIR / "evidencias_relatorio_ictiofauna_geoarc001.json"
    validation_path = OUTPUT_DIR / "validacao_textual_ictiofauna_geoarc001.json"
    manifest_path = OUTPUT_DIR / "manifesto_entrega_ictiofauna_geoarc001.json"

    html_path.write_text(html, encoding="utf-8")
    evidence_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")

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
        "pattern_reference": PATTERN_REFERENCE,
        "source_reference": SOURCE_REFERENCE,
    }
    validation_path.write_text(json.dumps(validation_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    delivery_files = sorted(
        path
        for path in OUTPUT_DIR.iterdir()
        if path.is_file() and path.name not in {"desktop.ini", manifest_path.name}
    )
    manifest_payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": 190,
        "project_code": "GEOARC001",
        "canonical_key": "GEOARC001__monitoramento_arcelor",
        "output_dir": str(OUTPUT_DIR),
        "products_count": len(delivery_files),
        "files": build_file_manifest(delivery_files),
        "validation": validation_payload,
    }
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(validation_payload, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
