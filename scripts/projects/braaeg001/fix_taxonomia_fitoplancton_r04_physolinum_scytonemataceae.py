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
TARGET_NAMES = ["Physolinum sp.", "Scytonemataceae N.I.", "Scytonemataceae"]


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
                   ordem, familia, genero, observacoes
            FROM public.especies
            WHERE nome_cientifico = ANY(:names)
               OR genero = 'Physolinum'
               OR familia = 'Scytonemataceae'
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
                   coalesce(sum(contagem), 0)::numeric AS contagem_total
            FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND id_projeto = :project_id
              AND grupo_biologico = :group
              AND (nome_cientifico = ANY(:names)
                   OR genero = 'Physolinum'
                   OR familia = 'Scytonemataceae')
            GROUP BY nome_cientifico, grupo_biologico, reino, filo, classe,
                     ordem, familia, genero
            ORDER BY nome_cientifico
            """
        ),
        {"code": PROJECT_CODE, "project_id": PROJECT_ID, "group": GROUP, "names": TARGET_NAMES},
    ).mappings()
    return rows_to_df(rows)


def create_backups(conn, stamp: str) -> list[str]:
    backup_species = f"backup_especies_braaeg001_fitoplancton_taxonomia_r04_{stamp}"
    backup_consolidated = f"backup_biota_braaeg001_fitoplancton_taxonomia_r04_{stamp}"
    conn.execute(
        text(f"""
            CREATE TABLE public.{backup_species} AS
            SELECT *
            FROM public.especies
            WHERE nome_cientifico = ANY(:names)
               OR genero = 'Physolinum'
               OR familia = 'Scytonemataceae'
        """),
        {"names": TARGET_NAMES},
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
    return [f"public.{backup_species}", f"public.{backup_consolidated}"]


def apply_updates(conn) -> list[dict[str, Any]]:
    updates = []
    phys = conn.execute(
        text(
            """
            UPDATE public.especies
            SET reino = 'Plantae',
                filo = 'Chlorophyta',
                classe = 'Ulvophyceae',
                ordem = 'Trentepohliales',
                familia = 'Trentepohliaceae',
                genero = 'Physolinum',
                observacoes = concat_ws(
                    ' | ',
                    nullif(observacoes, ''),
                    'R04 BRAAEG001: Physolinum é gênero raro e tratado em AlgaeBase como sinônimo associado a Trentepohlia; nome do laudo preservado como Physolinum sp.'
                )
            WHERE nome_cientifico = 'Physolinum sp.'
            """
        )
    )
    updates.append(
        {
            "taxon": "Physolinum sp.",
            "acao": "classificacao_complementada_nome_preservado",
            "linhas": phys.rowcount or 0,
            "classe": "Ulvophyceae",
            "ordem": "Trentepohliales",
            "familia": "Trentepohliaceae",
            "genero": "Physolinum",
        }
    )

    scyto = conn.execute(
        text(
            """
            UPDATE public.especies
            SET nome_cientifico = 'Scytonemataceae',
                reino = 'Plantae',
                filo = 'Cyanobacteria',
                classe = 'Cyanophyceae',
                ordem = 'Nostocales',
                familia = 'Scytonemataceae',
                genero = NULL,
                observacoes = concat_ws(
                    ' | ',
                    nullif(observacoes, ''),
                    'R04 BRAAEG001: N.I. removido; táxon tratado no nível de família Scytonemataceae, com gênero vazio.'
                )
            WHERE nome_cientifico = 'Scytonemataceae N.I.'
            """
        )
    )
    updates.append(
        {
            "taxon": "Scytonemataceae N.I.",
            "acao": "renomeado_para_familia",
            "novo_nome": "Scytonemataceae",
            "linhas": scyto.rowcount or 0,
            "classe": "Cyanophyceae",
            "ordem": "Nostocales",
            "familia": "Scytonemataceae",
            "genero": "",
        }
    )
    return updates


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
        before_consolidated = fetch_consolidated(conn)
        backups: list[str] = []
        updates: list[dict[str, Any]] = []
        consolidated_rows = 0
        if args.apply:
            backups = create_backups(conn, stamp.lower())
            updates = apply_updates(conn)
            consolidated_rows = rebuild_consolidated(conn)
        after_species = fetch_species(conn)
        after_consolidated = fetch_consolidated(conn)

    summary = pd.DataFrame(
        [
            {"item": "modo", "valor": "apply" if args.apply else "dry_run"},
            {"item": "backups", "valor": "; ".join(backups)},
            {"item": "linhas_consolidadas_recriadas", "valor": consolidated_rows},
            {"item": "decisao_physolinum", "valor": "manter nome Physolinum sp.; completar hierarquia como Trentepohliaceae e registrar atenção taxonômica"},
            {"item": "decisao_scytonemataceae", "valor": "renomear Scytonemataceae N.I. para Scytonemataceae, com gênero vazio"},
        ]
    )
    audit_path = args.output_dir / f"{stamp}_fix_taxonomia_fitoplancton_r04_braaeg001.xlsx"
    write_audit(
        audit_path,
        {
            "resumo": summary,
            "updates": pd.DataFrame(updates),
            "especies_antes": before_species,
            "especies_depois": after_species,
            "consolidado_antes": before_consolidated,
            "consolidado_depois": after_consolidated,
        },
    )
    print({"audit": str(audit_path), "mode": "apply" if args.apply else "dry_run", "consolidated_rows": consolidated_rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
