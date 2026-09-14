from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text


ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
if str(OPYTA_DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(OPYTA_DATA_ROOT))

from core.engine import get_engine  # noqa: E402


PROJECT_CODE = "BRAAVG002"
GROUP = "Ictiofauna"
AUDIT_ROOT = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
DEFAULT_OUTPUT_DIR = AUDIT_ROOT / "species_traits_review_20260713"
GEOARC_TRAITS = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Geomil\Arcellor"
    r"\Arcellor Monitoramento\Produtos\Resultados\Resultados\Ictiofauna"
    r"\Exploratorio_assembleia_ictiofauna\tabela_especie_atributos_funcionais_geoarc001_teste.xlsx"
)

TRAIT_FIELDS = [
    "Habitat_funcional",
    "Preferencia_correnteza",
    "Guilda_trofica",
    "Porte_corporal",
    "Sensibilidade_funcional",
]

TAXON_DISPLAY_OVERRIDES = {
    "Poecilia mexicana": {
        "nome_cientifico_relatorio": "Poecilia cf. mexicana",
        "qualificador_identificacao": "cf.",
        "motivo": "Identificacao mantida com duvida taxonomica indicada pelo usuario em 2026-07-13.",
    }
}

PROPOSED_TRAITS: dict[str, dict[str, Any]] = {
    "Characidium fasciatum": {
        "Habitat_funcional": "bentônico",
        "Preferencia_correnteza": "reofílico",
        "Guilda_trofica": "insetívoro",
        "Porte_corporal": "pequeno",
        "Sensibilidade_funcional": "intermediária",
        "Confianca_classificacao": "media",
        "Fonte_classificacao": "FishBase Characidium fasciatum; Fishipedia Characidium fasciatum; interpretação funcional Opyta por família/gênero",
        "Fonte_urls": "https://www.fishbase.se/summary/Characidium-fasciatum; https://www.fishi-pedia.com/fishes/characidium-fasciatum",
        "Observacoes_funcionais": "FishBase registra espécie benthopelágica e ocorrência no São Francisco; Fishipedia descreve vida próxima ao fundo e dieta carnívora. Classificação como insetívoro/reofílico é preliminar para revisão técnica.",
    },
    "Geophagus brasiliensis": {
        "Habitat_funcional": "bentopelágico",
        "Preferencia_correnteza": "generalista",
        "Guilda_trofica": "onívoro",
        "Porte_corporal": "médio",
        "Sensibilidade_funcional": "tolerante",
        "Confianca_classificacao": "alta",
        "Fonte_classificacao": "FishBase Geophagus brasiliensis; Fishipedia Geophagus brasiliensis",
        "Fonte_urls": "https://www.fishbase.se/summary/Geophagus-brasiliensis.html; https://www.fishi-pedia.com/fishes/geophagus-brasiliensis",
        "Observacoes_funcionais": "FishBase registra habitat benthopelágico e grande amplitude térmica; Fishipedia descreve espécie de fundo e onívora com tendência carnívora. Preferência por correnteza tratada como generalista.",
    },
    "Neoplecostomus franciscoensis": {
        "Habitat_funcional": "bentônico",
        "Preferencia_correnteza": "reofílico",
        "Guilda_trofica": "perifitívoro",
        "Porte_corporal": "médio",
        "Sensibilidade_funcional": "sensível",
        "Confianca_classificacao": "media",
        "Fonte_classificacao": "FishBase Neoplecostomus franciscoensis; literatura/gênero Neoplecostomus; interpretação funcional Opyta por Loricariidae de cabeceira",
        "Fonte_urls": "https://www.fishbase.se/summary/Neoplecostomus-franciscoensis; https://en.wikipedia.org/wiki/Neoplecostomus",
        "Observacoes_funcionais": "FishBase registra espécie demersal de cabeceiras do rio das Velhas/Paraopeba; gênero associado a águas rápidas. Guilda perifitívora por morfoecologia loricariídea, revisar se houver dado de dieta local.",
    },
    "Pareiorhaphis mutuca": {
        "Habitat_funcional": "bentônico",
        "Preferencia_correnteza": "reofílico",
        "Guilda_trofica": "perifitívoro",
        "Porte_corporal": "médio",
        "Sensibilidade_funcional": "sensível",
        "Confianca_classificacao": "alta",
        "Fonte_classificacao": "FishBase Pareiorhaphis mutuca; interpretação funcional Opyta por Loricariidae reofílico",
        "Fonte_urls": "https://www.fishbase.se/summary/Pareiorhaphis-mutuca",
        "Observacoes_funcionais": "FishBase registra espécie demersal, cabeceiras do rio das Velhas, áreas rochosas/pedregosas e status global EN. Classificada como função sensível reofílica.",
    },
    "Parotocinclus robustus": {
        "Habitat_funcional": "bentônico",
        "Preferencia_correnteza": "intermediário",
        "Guilda_trofica": "perifitívoro",
        "Porte_corporal": "pequeno",
        "Sensibilidade_funcional": "intermediária",
        "Confianca_classificacao": "media",
        "Fonte_classificacao": "FishBase Parotocinclus robustus; descrição original Lehmann & Reis 2012 via FishBase; síntese habitat KML/literatura secundária",
        "Fonte_urls": "https://www.fishbase.se/summary/Parotocinclus-robustus; https://en.wikipedia.org/wiki/Parotocinclus_robustus",
        "Observacoes_funcionais": "FishBase registra espécie demersal, 4,2 cm SL e bacia do São Francisco. Habitat descrito como rios rasos de fluxo lento a moderado; por isso preferência intermediária e sensibilidade intermediária.",
    },
    "Poecilia mexicana": {
        "Habitat_funcional": "nectônico",
        "Preferencia_correnteza": "limnofílico",
        "Guilda_trofica": "onívoro",
        "Porte_corporal": "pequeno",
        "Sensibilidade_funcional": "tolerante",
        "Confianca_classificacao": "alta",
        "Fonte_classificacao": "FishBase Poecilia mexicana; padrão funcional GEOARC001 para Poecilia reticulata",
        "Fonte_urls": "https://fishbase.se/summary/SpeciesSummary.php?id=3227",
        "Observacoes_funcionais": "FishBase registra ambientes de canais, valas vegetadas e poças de riachos, alimento principalmente detrito e impacto ecológico em introduções. Mantido como onívoro para compatibilidade com Poecilia reticulata no piloto.",
    },
    "Trichomycterus novalimensis": {
        "Habitat_funcional": "bentônico",
        "Preferencia_correnteza": "reofílico",
        "Guilda_trofica": "insetívoro",
        "Porte_corporal": "pequeno",
        "Sensibilidade_funcional": "sensível",
        "Confianca_classificacao": "media",
        "Fonte_classificacao": "FishBase Trichomycterus novalimensis; Barbosa & Costa 2010; padrão funcional GEOARC001 para Trichomycterus brasiliensis",
        "Fonte_urls": "https://fishbase.se/summary/SpeciesSummary.php?id=65454; https://www.researchgate.net/publication/286883789_Seven_new_species_of_the_catfish_genus_Trichomycterus_Teleostei_Siluriformes_Trichomycteridae_from_Southeastern_Brazil_and_redescription_of_T_brasiliensis",
        "Observacoes_funcionais": "Espécie do complexo T. brasiliensis, associada ao alto rio Mutuca/Nova Lima; classificação segue o padrão aprovado no piloto para T. brasiliensis, com revisão recomendada.",
    },
}


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


def _normalize_text(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_avg_species() -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = get_engine()
    try:
        occurrences = pd.read_sql(
            text(
                """
                SELECT nome_cientifico,
                       COUNT(*) AS registros_consolidados,
                       COUNT(DISTINCT nome_campanha) AS campanhas_com_ocorrencia,
                       COUNT(DISTINCT nome_ponto) AS pontos_com_ocorrencia,
                       SUM(COALESCE(contagem, 0)) AS abundancia_total
                FROM biota_analise_consolidada
                WHERE codigo_interno_opyta = :code
                  AND grupo_biologico ILIKE :group
                  AND nome_cientifico IS NOT NULL
                GROUP BY nome_cientifico
                ORDER BY nome_cientifico
                """
            ),
            engine,
            params={"code": PROJECT_CODE, "group": "%Ictio%"},
        )
        registry = pd.read_sql(
            text(
                """
                SELECT nome_cientifico, nome_popular, ordem, familia, genero, origem,
                       status_ameaca_nacional, status_ameaca_global, status_copam,
                       status_estadual, cites, habito_alimentar, guilda_alimentar,
                       estrategia_reprodutiva, dependencia_florestal, endemismo,
                       sensibilidade_ambiental, migratorio, raridade, distribuicao,
                       valor_economico, observacoes
                FROM especies
                WHERE grupo_biologico ILIKE :group
                """
            ),
            engine,
            params={"group": "%Ictio%"},
        )
    finally:
        engine.dispose()
    return occurrences, registry


def load_geoarc_traits(path: Path) -> pd.DataFrame:
    data = pd.read_excel(path)
    data["species_key"] = data["Nome Cientifico"].map(_normalize_text)
    keep = [
        "Nome Cientifico",
        *TRAIT_FIELDS,
        "Confianca_classificacao",
        "Fonte_classificacao",
        "Observacoes_funcionais",
        "species_key",
    ]
    return data[keep].copy()


def build_review(occurrences: pd.DataFrame, registry: pd.DataFrame, geoarc: pd.DataFrame) -> pd.DataFrame:
    occ = occurrences.copy()
    occ["species_key"] = occ["nome_cientifico"].map(_normalize_text)
    reg = registry.copy()
    reg["species_key"] = reg["nome_cientifico"].map(_normalize_text)
    base = occ.merge(reg, on="species_key", how="left", suffixes=("", "_cadastro"))
    base = base.merge(geoarc, on="species_key", how="left", suffixes=("", "_geoarc"))

    rows = []
    for _, row in base.iterrows():
        name = row["nome_cientifico"]
        proposed = PROPOSED_TRAITS.get(name)
        if proposed is None:
            action = "reaproveitar_geoarc"
            source_kind = "geoarc001"
            traits = {field: row.get(field) for field in TRAIT_FIELDS}
            confidence = row.get("Confianca_classificacao")
            source = row.get("Fonte_classificacao")
            urls = ""
            notes = row.get("Observacoes_funcionais")
        else:
            action = "novo_proposto_revisar"
            source_kind = "bibliografia_preliminar"
            traits = {field: proposed[field] for field in TRAIT_FIELDS}
            confidence = proposed["Confianca_classificacao"]
            source = proposed["Fonte_classificacao"]
            urls = proposed["Fonte_urls"]
            notes = proposed["Observacoes_funcionais"]

        out = {
            "nome_cientifico": name,
            "nome_cientifico_relatorio": TAXON_DISPLAY_OVERRIDES.get(name, {}).get(
                "nome_cientifico_relatorio", name
            ),
            "qualificador_identificacao": TAXON_DISPLAY_OVERRIDES.get(name, {}).get(
                "qualificador_identificacao", ""
            ),
            "observacao_taxonomica": TAXON_DISPLAY_OVERRIDES.get(name, {}).get("motivo", ""),
            "acao": action,
            "origem_trait": source_kind,
            "nome_popular": row.get("nome_popular"),
            "ordem": row.get("ordem"),
            "familia": row.get("familia"),
            "genero": row.get("genero"),
            "origem_banco": row.get("origem"),
            "status_ameaca_global_banco": row.get("status_ameaca_global"),
            "status_estadual_banco": row.get("status_estadual"),
            "registros_consolidados": int(row.get("registros_consolidados", 0)),
            "campanhas_com_ocorrencia": int(row.get("campanhas_com_ocorrencia", 0)),
            "pontos_com_ocorrencia": int(row.get("pontos_com_ocorrencia", 0)),
            "abundancia_total": float(row.get("abundancia_total", 0)),
            **traits,
            "Confianca_classificacao": confidence,
            "Fonte_classificacao": source,
            "Fonte_urls": urls,
            "Observacoes_funcionais": notes,
            "status_revisao": "pendente_aprovacao_usuario",
        }
        rows.append(out)
    return pd.DataFrame(rows)


def build_registry_suggestions(review: pd.DataFrame) -> pd.DataFrame:
    out = review[
        [
            "nome_cientifico",
            "origem_banco",
            "Guilda_trofica",
            "Sensibilidade_funcional",
            "Confianca_classificacao",
            "status_revisao",
        ]
    ].copy()
    out["guilda_alimentar_sugerida"] = out["Guilda_trofica"]
    out["habito_alimentar_sugerido"] = out["Guilda_trofica"]
    out["sensibilidade_ambiental_sugerida"] = out["Sensibilidade_funcional"]
    out["observacao"] = (
        "Sugestao de harmonizacao com a matriz funcional. Nao aplicar no banco antes de Gate B/aprovacao taxonomica."
    )
    return out


def write_outputs(output_dir: Path, review: pd.DataFrame, registry_suggestions: pd.DataFrame) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx = output_dir / "braavg002_ictiofauna_traits_funcionais_revisao.xlsx"
    json_path = output_dir / "braavg002_ictiofauna_traits_funcionais_revisao.json"
    md_path = output_dir / "braavg002_ictiofauna_traits_funcionais_revisao.md"
    sources = (
        review[["nome_cientifico", "Fonte_classificacao", "Fonte_urls", "Confianca_classificacao"]]
        .drop_duplicates()
        .sort_values("nome_cientifico")
    )
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        review.to_excel(writer, sheet_name="traits_funcionais", index=False)
        registry_suggestions.to_excel(writer, sheet_name="sugestoes_cadastro", index=False)
        sources.to_excel(writer, sheet_name="fontes", index=False)
        review[review["acao"] == "novo_proposto_revisar"].to_excel(
            writer, sheet_name="pendentes_aprovacao", index=False
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "species": int(len(review)),
        "reused_geoarc_traits": int((review["acao"] == "reaproveitar_geoarc").sum()),
        "new_proposed_traits": int((review["acao"] == "novo_proposto_revisar").sum()),
        "status": "pending_user_approval",
        "outputs": {"xlsx": str(xlsx), "json": str(json_path), "markdown": str(md_path)},
        "pending_species": review.loc[review["acao"] == "novo_proposto_revisar", "nome_cientifico"].tolist(),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")

    lines = [
        "# BRAAVG002 - Ictiofauna - traits funcionais para revisao",
        "",
        f"- especies avaliadas: {payload['species']}",
        f"- traits reaproveitados do GEOARC001: {payload['reused_geoarc_traits']}",
        f"- traits novos propostos: {payload['new_proposed_traits']}",
        f"- status: `{payload['status']}`",
        "",
        "## Especies Com Traits Novos Propostos",
        "",
    ]
    for _, row in review[review["acao"] == "novo_proposto_revisar"].iterrows():
        lines.append(
            "- {nome}: {habitat}; {correnteza}; {guilda}; {porte}; {sensibilidade} ({confianca})".format(
                nome=row["nome_cientifico"],
                habitat=row["Habitat_funcional"],
                correnteza=row["Preferencia_correnteza"],
                guilda=row["Guilda_trofica"],
                porte=row["Porte_corporal"],
                sensibilidade=row["Sensibilidade_funcional"],
                confianca=row["Confianca_classificacao"],
            )
        )
    lines.extend(
        [
            "",
            "## Arquivos",
            "",
            f"- Excel: `{xlsx}`",
            f"- JSON: `{json_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def run(output_dir: Path, geoarc_traits: Path) -> dict[str, Any]:
    occurrences, registry = load_avg_species()
    geoarc = load_geoarc_traits(geoarc_traits)
    review = build_review(occurrences, registry, geoarc)
    registry_suggestions = build_registry_suggestions(review)
    return write_outputs(output_dir, review, registry_suggestions)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera tabela de revisao de traits funcionais AVG Ictiofauna.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--geoarc-traits", type=Path, default=GEOARC_TRAITS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(args.output_dir, args.geoarc_traits)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
