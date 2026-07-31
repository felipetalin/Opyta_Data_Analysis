from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text


PROJECT_ID = 195
PROJECT_CODE = "BRAAEG001"
GROUP = "Fitoplâncton"

TARGET_NAMES = [
    "Encyonema silesiacum",
    "Pinnularia divergens",
    "Eunotia veneris",
    "Gomphonema sp.",
    "Pinnularia boyeriformis",
    "Phormidium tergestinum",
    "Surirella splendida",
    "Iconella splendida",
]

TAXONOMY_FIXES = {
    "Encyonema silesiacum": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Bacillariophyta",
        "classe": "Bacillariophyceae",
        "ordem": "Cymbellales",
        "familia": "Encyonemataceae",
        "genero": "Encyonema",
    },
    "Pinnularia divergens": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Bacillariophyta",
        "classe": "Bacillariophyceae",
        "ordem": "Naviculales",
        "familia": "Pinnulariaceae",
        "genero": "Pinnularia",
    },
    "Eunotia veneris": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Bacillariophyta",
        "classe": "Bacillariophyceae",
        "ordem": "Eunotiales",
        "familia": "Eunotiaceae",
        "genero": "Eunotia",
    },
    "Gomphonema sp.": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Bacillariophyta",
        "classe": "Bacillariophyceae",
        "ordem": "Cymbellales",
        "familia": "Gomphonemataceae",
        "genero": "Gomphonema",
    },
    "Pinnularia boyeriformis": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Bacillariophyta",
        "classe": "Bacillariophyceae",
        "ordem": "Naviculales",
        "familia": "Pinnulariaceae",
        "genero": "Pinnularia",
    },
    "Phormidium tergestinum": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Cyanobacteria",
        "classe": "Cyanophyceae",
        "ordem": "Oscillatoriales",
        "familia": "Oscillatoriaceae",
        "genero": "Phormidium",
    },
    "Iconella splendida": {
        "grupo_biologico": GROUP,
        "reino": "Plantae",
        "filo": "Bacillariophyta",
        "classe": "Bacillariophyceae",
        "ordem": "Surirellales",
        "familia": "Surirellaceae",
        "genero": "Iconella",
    },
}


def connect_engine(opyta_data_root: Path):
    sys.path.insert(0, str(opyta_data_root))
    from core.engine import get_engine  # noqa: PLC0415

    return get_engine()


def rows_to_df(rows) -> pd.DataFrame:
    return pd.DataFrame([dict(row) for row in rows])


def fetch_species(conn) -> pd.DataFrame:
    rows = conn.execute(
        text(
            """
            SELECT id_especie, nome_cientifico, grupo_biologico, reino, filo, classe,
                   ordem, familia, genero
            FROM public.especies
            WHERE nome_cientifico = ANY(:names)
            ORDER BY nome_cientifico
            """
        ),
        {"names": TARGET_NAMES},
    ).mappings()
    return rows_to_df(rows)


def fetch_consolidated(conn) -> pd.DataFrame:
    rows = conn.execute(
        text(
            """
            SELECT nome_cientifico, grupo_biologico, reino, filo, classe, ordem,
                   familia, genero, count(*)::int AS linhas,
                   count(DISTINCT nome_campanha)::int AS campanhas,
                   count(DISTINCT nome_ponto)::int AS pontos,
                   coalesce(sum(contagem), 0)::numeric AS contagem_total
            FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND id_projeto = :project_id
              AND grupo_biologico = :group
              AND nome_cientifico = ANY(:names)
            GROUP BY nome_cientifico, grupo_biologico, reino, filo, classe,
                     ordem, familia, genero
            ORDER BY nome_cientifico
            """
        ),
        {"code": PROJECT_CODE, "project_id": PROJECT_ID, "group": GROUP, "names": TARGET_NAMES},
    ).mappings()
    return rows_to_df(rows)


def fetch_base_results(conn) -> pd.DataFrame:
    rows = conn.execute(
        text(
            """
            SELECT sp.nome_cientifico, rf.id_especie, count(*)::int AS linhas,
                   coalesce(sum(rf.densidade), 0)::numeric AS densidade_total
            FROM public.resultados_fitoplancton rf
            JOIN public.especies sp ON sp.id_especie = rf.id_especie
            JOIN public.esforcos_amostragem e ON e.id_esforco = rf.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :project_id
              AND e.grupo_biologico = :group
              AND sp.nome_cientifico = ANY(:names)
            GROUP BY sp.nome_cientifico, rf.id_especie
            ORDER BY sp.nome_cientifico
            """
        ),
        {"project_id": PROJECT_ID, "group": GROUP, "names": TARGET_NAMES},
    ).mappings()
    return rows_to_df(rows)


def create_backups(conn, stamp: str) -> list[str]:
    backup_species = f"backup_especies_braaeg001_fitoplancton_taxonomia_r03_{stamp}"
    backup_results = f"backup_resultados_fitoplancton_braaeg001_taxonomia_r03_{stamp}"
    backup_consolidated = f"backup_biota_braaeg001_fitoplancton_taxonomia_r03_{stamp}"
    conn.execute(
        text(f"""
            CREATE TABLE public.{backup_species} AS
            SELECT *
            FROM public.especies
            WHERE nome_cientifico = ANY(:names)
        """),
        {"names": TARGET_NAMES},
    )
    conn.execute(
        text(f"""
            CREATE TABLE public.{backup_results} AS
            SELECT rf.*
            FROM public.resultados_fitoplancton rf
            JOIN public.especies sp ON sp.id_especie = rf.id_especie
            JOIN public.esforcos_amostragem e ON e.id_esforco = rf.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :project_id
              AND e.grupo_biologico = :group
              AND sp.nome_cientifico = ANY(:names)
        """),
        {"project_id": PROJECT_ID, "group": GROUP, "names": TARGET_NAMES},
    )
    conn.execute(
        text(f"""
            CREATE TABLE public.{backup_consolidated} AS
            SELECT *
            FROM public.biota_analise_consolidada
            WHERE id_projeto = :project_id
              AND codigo_interno_opyta = :code
              AND grupo_biologico = :group
        """),
        {"project_id": PROJECT_ID, "code": PROJECT_CODE, "group": GROUP},
    )
    return [f"public.{backup_species}", f"public.{backup_results}", f"public.{backup_consolidated}"]


def apply_species_updates(conn) -> list[dict[str, Any]]:
    applied = []
    for name, values in TAXONOMY_FIXES.items():
        result = conn.execute(
            text(
                """
                UPDATE public.especies
                SET grupo_biologico = :grupo_biologico,
                    reino = :reino,
                    filo = :filo,
                    classe = :classe,
                    ordem = :ordem,
                    familia = :familia,
                    genero = :genero
                WHERE nome_cientifico = :nome_cientifico
                """
            ),
            {"nome_cientifico": name, **values},
        )
        applied.append({"nome_cientifico": name, "linhas_atualizadas": result.rowcount or 0, **values})
    return applied


def switch_surirella_to_iconella(conn) -> dict[str, Any]:
    old_id = conn.execute(
        text("SELECT id_especie FROM public.especies WHERE nome_cientifico = 'Surirella splendida'")
    ).scalar_one()
    new_id = conn.execute(
        text("SELECT id_especie FROM public.especies WHERE nome_cientifico = 'Iconella splendida'")
    ).scalar_one()
    result = conn.execute(
        text(
            """
            UPDATE public.resultados_fitoplancton rf
            SET id_especie = :new_id
            FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE rf.id_esforco = e.id_esforco
              AND p.id_projeto = :project_id
              AND e.grupo_biologico = :group
              AND rf.id_especie = :old_id
            """
        ),
        {"new_id": new_id, "old_id": old_id, "project_id": PROJECT_ID, "group": GROUP},
    )
    return {
        "de": "Surirella splendida",
        "para": "Iconella splendida",
        "id_antigo": old_id,
        "id_novo": new_id,
        "linhas_resultados_atualizadas": result.rowcount or 0,
        "justificativa": "AlgaeBase trata Surirella splendida como sinônimo de Iconella splendida; usuário solicitou verificação da sinonímia.",
    }


def rebuild_consolidated(conn) -> int:
    conn.execute(
        text(
            """
            DELETE FROM public.biota_analise_consolidada
            WHERE id_projeto = :project_id
              AND codigo_interno_opyta = :code
              AND grupo_biologico = :group
            """
        ),
        {"project_id": PROJECT_ID, "code": PROJECT_CODE, "group": GROUP},
    )
    result = conn.execute(
        text(
            """
            INSERT INTO public.biota_analise_consolidada (
                nome_empresa, nome_projeto, codigo_opyta, nome_campanha, nome_ponto,
                latitude, longitude, grupo_biologico, nome_cientifico, contagem,
                biomassa, bmwp_score, codigo_interno_opyta, data_hora_coleta,
                bacia_hidrografica, metodo_de_captura, esforco, unidade_esforco,
                nome_popular, reino, filo, classe, ordem, familia, genero, origem,
                medida_1, medida_2, tipo_amostragem, id_empreendimento,
                nome_empreendimento, id_projeto
            )
            SELECT
                cli.nome_empresa, pr.nome_projeto, NULL::text, c.nome_campanha,
                p.nome_ponto, p.latitude, p.longitude, e.grupo_biologico,
                sp.nome_cientifico, rf.densidade::numeric, NULL::numeric,
                sp.bmwp_score, pr.codigo_interno_opyta, p.data_hora_coleta,
                p.bacia_hidrografica, e.metodo_de_captura, e.esforco,
                e.unidade_esforco, sp.nome_popular, sp.reino, sp.filo, sp.classe,
                sp.ordem, sp.familia, sp.genero, sp.origem, NULL::numeric,
                NULL::numeric, COALESCE(rf.tipo_amostragem, e.tipo_amostragem, e.tipo_de_amostragem),
                p.id_empreendimento, emp.nome, pr.id_projeto
            FROM public.resultados_fitoplancton rf
            JOIN public.esforcos_amostragem e ON e.id_esforco = rf.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            JOIN public.campanhas c ON c.id_campanha = p.id_campanha
            JOIN public.projetos pr ON pr.id_projeto = p.id_projeto
            JOIN public.clientes cli ON cli.id_cliente = pr.id_cliente
            JOIN public.especies sp ON sp.id_especie = rf.id_especie
            LEFT JOIN public.empreendimentos emp ON emp.id_empreendimento = p.id_empreendimento
            WHERE p.id_projeto = :project_id
              AND pr.codigo_interno_opyta = :code
              AND e.grupo_biologico = :group
            """
        ),
        {"project_id": PROJECT_ID, "code": PROJECT_CODE, "group": GROUP},
    )
    return result.rowcount or 0


def write_audit(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Fito"))
    parser.add_argument("--opyta-data-root", type=Path, default=Path.cwd().parent / "Opyta_Data")
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    engine = connect_engine(args.opyta_data_root)

    with engine.begin() as conn:
        before_species = fetch_species(conn)
        before_results = fetch_base_results(conn)
        before_consolidated = fetch_consolidated(conn)

        backups: list[str] = []
        applied_updates: list[dict[str, Any]] = []
        switch_result: dict[str, Any] = {}
        consolidated_rows = 0

        if args.apply:
            backups = create_backups(conn, stamp.lower())
            applied_updates = apply_species_updates(conn)
            switch_result = switch_surirella_to_iconella(conn)
            consolidated_rows = rebuild_consolidated(conn)

        after_species = fetch_species(conn)
        after_results = fetch_base_results(conn)
        after_consolidated = fetch_consolidated(conn)

    summary = pd.DataFrame(
        [
            {"item": "modo", "valor": "apply" if args.apply else "dry_run"},
            {"item": "backups", "valor": "; ".join(backups)},
            {"item": "linhas_consolidadas_recriadas", "valor": consolidated_rows},
            {"item": "surirella_para_iconella_linhas", "valor": switch_result.get("linhas_resultados_atualizadas", 0)},
            {"item": "fonte_sinonimia", "valor": "AlgaeBase: Surirella splendida é sinônimo de Iconella splendida"},
        ]
    )
    audit_path = args.output_dir / f"{stamp}_fix_taxonomia_fitoplancton_r03_braaeg001.xlsx"
    write_audit(
        audit_path,
        {
            "resumo": summary,
            "updates_especies": pd.DataFrame(applied_updates),
            "switch_surirella_iconella": pd.DataFrame([switch_result] if switch_result else []),
            "especies_antes": before_species,
            "especies_depois": after_species,
            "resultados_antes": before_results,
            "resultados_depois": after_results,
            "consolidado_antes": before_consolidated,
            "consolidado_depois": after_consolidated,
        },
    )
    print({"audit": str(audit_path), "mode": "apply" if args.apply else "dry_run", "consolidated_rows": consolidated_rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
