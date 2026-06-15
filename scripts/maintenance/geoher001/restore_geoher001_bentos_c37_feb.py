import os
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_CODE = "GEOHER001"
GROUP = "Zoobentos"
CAMPAIGN_36 = "C36-11-2025-CH"
CAMPAIGN_37 = "C37-02-2026-CH"

SOURCE_BACKUP_PREFIX = "backup_geoher001_bentos_c36_merge_20260615094213"
BACKUP_CAMPAIGNS = f"{SOURCE_BACKUP_PREFIX}_campanhas"
BACKUP_POINTS = f"{SOURCE_BACKUP_PREFIX}_pontos"
BACKUP_EFFORTS = f"{SOURCE_BACKUP_PREFIX}_esforcos"
BACKUP_BENTOS = f"{SOURCE_BACKUP_PREFIX}_resultados_zoobentos"
BACKUP_CONSOLIDATED = f"{SOURCE_BACKUP_PREFIX}_consolidada"


def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    name = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", "5432")
    missing = [key for key, value in {
        "DB_USER": user,
        "DB_PASSWORD": password,
        "DB_HOST": host,
        "DB_NAME": name,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return create_engine(
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}?connect_timeout=15"
    )


def scalar(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).scalar()


def table_columns(conn, table_name):
    return [
        row[0]
        for row in conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        )
    ]


def create_current_backup(conn, project_id, campaign36_id, campaign37_id):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    prefix = f"backup_geoher001_restore_c37_feb_{stamp}"

    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_campanhas AS
            SELECT *
            FROM public.campanhas
            WHERE id_campanha IN (:campaign36_id, :campaign37_id)
            """
        ),
        {"campaign36_id": campaign36_id, "campaign37_id": campaign37_id},
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_pontos AS
            SELECT *
            FROM public.pontos_coleta
            WHERE id_projeto = :project_id
              AND id_campanha IN (:campaign36_id, :campaign37_id)
            """
        ),
        {
            "project_id": project_id,
            "campaign36_id": campaign36_id,
            "campaign37_id": campaign37_id,
        },
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_esforcos AS
            SELECT e.*
            FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta pc ON pc.id_ponto_coleta = e.id_ponto_coleta
            WHERE pc.id_projeto = :project_id
              AND pc.id_campanha IN (:campaign36_id, :campaign37_id)
            """
        ),
        {
            "project_id": project_id,
            "campaign36_id": campaign36_id,
            "campaign37_id": campaign37_id,
        },
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_resultados_zoobentos AS
            SELECT rz.*
            FROM public.resultados_zoobentos rz
            JOIN public.esforcos_amostragem e ON e.id_esforco = rz.id_esforco
            JOIN public.pontos_coleta pc ON pc.id_ponto_coleta = e.id_ponto_coleta
            WHERE pc.id_projeto = :project_id
              AND pc.id_campanha IN (:campaign36_id, :campaign37_id)
              AND e.grupo_biologico = :group_name
            """
        ),
        {
            "project_id": project_id,
            "campaign36_id": campaign36_id,
            "campaign37_id": campaign37_id,
            "group_name": GROUP,
        },
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_consolidada AS
            SELECT *
            FROM public.biota_analise_consolidada
            WHERE trim(codigo_interno_opyta) = :project_code
              AND grupo_biologico = :group_name
              AND nome_campanha IN (:campaign36, :campaign37)
            """
        ),
        {
            "project_code": PROJECT_CODE,
            "group_name": GROUP,
            "campaign36": CAMPAIGN_36,
            "campaign37": CAMPAIGN_37,
        },
    )
    return prefix


def summarize(conn, project_id):
    return pd.read_sql(
        text(
            """
            SELECT ca.nome_campanha, e.grupo_biologico,
                   count(DISTINCT pc.id_ponto_coleta) AS pontos,
                   count(DISTINCT e.id_esforco) AS esforcos,
                   count(ri.id_resultado_ictio) AS ictio_resultados,
                   count(rz.id_resultado_bento) AS bentos_resultados,
                   sum(COALESCE(ri.numero_de_individuos, 0)) AS ictio_abund,
                   sum(COALESCE(rz.abundancia, 0)) AS bentos_abund,
                   min(pc.data_hora_coleta) AS data_min,
                   max(pc.data_hora_coleta) AS data_max
            FROM public.pontos_coleta pc
            JOIN public.campanhas ca ON ca.id_campanha = pc.id_campanha
            LEFT JOIN public.esforcos_amostragem e ON e.id_ponto_coleta = pc.id_ponto_coleta
            LEFT JOIN public.resultados_ictiofauna ri ON ri.id_esforco = e.id_esforco
            LEFT JOIN public.resultados_zoobentos rz ON rz.id_esforco = e.id_esforco
            WHERE pc.id_projeto = :project_id
              AND ca.nome_campanha IN (:campaign36, :campaign37)
            GROUP BY ca.nome_campanha, e.grupo_biologico
            ORDER BY ca.nome_campanha, e.grupo_biologico
            """
        ),
        conn,
        params={
            "project_id": project_id,
            "campaign36": CAMPAIGN_36,
            "campaign37": CAMPAIGN_37,
        },
    )


def delete_current_campaign36_bentos(conn, project_id, campaign36_id):
    conn.execute(
        text(
            """
            DELETE FROM public.resultados_zoobentos rz
            USING public.esforcos_amostragem e, public.pontos_coleta pc
            WHERE rz.id_esforco = e.id_esforco
              AND e.id_ponto_coleta = pc.id_ponto_coleta
              AND pc.id_projeto = :project_id
              AND pc.id_campanha = :campaign36_id
              AND e.grupo_biologico = :group_name
            """
        ),
        {
            "project_id": project_id,
            "campaign36_id": campaign36_id,
            "group_name": GROUP,
        },
    )
    conn.execute(
        text(
            """
            DELETE FROM public.esforcos_amostragem e
            USING public.pontos_coleta pc
            WHERE e.id_ponto_coleta = pc.id_ponto_coleta
              AND pc.id_projeto = :project_id
              AND pc.id_campanha = :campaign36_id
              AND e.grupo_biologico = :group_name
            """
        ),
        {
            "project_id": project_id,
            "campaign36_id": campaign36_id,
            "group_name": GROUP,
        },
    )
    conn.execute(
        text(
            """
            DELETE FROM public.biota_analise_consolidada
            WHERE trim(codigo_interno_opyta) = :project_code
              AND grupo_biologico = :group_name
              AND nome_campanha = :campaign36
            """
        ),
        {
            "project_code": PROJECT_CODE,
            "group_name": GROUP,
            "campaign36": CAMPAIGN_36,
        },
    )


def restore_campaign36_bentos(conn):
    effort_cols = table_columns(conn, "esforcos_amostragem")
    bentos_cols = table_columns(conn, "resultados_zoobentos")
    consolidated_cols = table_columns(conn, "biota_analise_consolidada")

    effort_col_sql = ", ".join(f'"{col}"' for col in effort_cols)
    conn.execute(
        text(
            f"""
            INSERT INTO public.esforcos_amostragem ({effort_col_sql})
            SELECT {', '.join('e.' + col for col in effort_cols)}
            FROM public.{BACKUP_EFFORTS} e
            JOIN public.{BACKUP_POINTS} p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_campanha = 110
              AND e.grupo_biologico = :group_name
            """
        ),
        {"group_name": GROUP},
    )

    bentos_col_sql = ", ".join(f'"{col}"' for col in bentos_cols)
    conn.execute(
        text(
            f"""
            INSERT INTO public.resultados_zoobentos ({bentos_col_sql})
            SELECT {', '.join('r.' + col for col in bentos_cols)}
            FROM public.{BACKUP_BENTOS} r
            JOIN public.{BACKUP_EFFORTS} e ON e.id_esforco = r.id_esforco
            JOIN public.{BACKUP_POINTS} p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_campanha = 110
              AND e.grupo_biologico = :group_name
            """
        ),
        {"group_name": GROUP},
    )

    consolidated_col_sql = ", ".join(f'"{col}"' for col in consolidated_cols)
    conn.execute(
        text(
            f"""
            INSERT INTO public.biota_analise_consolidada ({consolidated_col_sql})
            SELECT {', '.join('c.' + col for col in consolidated_cols)}
            FROM public.{BACKUP_CONSOLIDATED} c
            WHERE c.nome_campanha = :campaign36
              AND c.grupo_biologico = :group_name
            """
        ),
        {"campaign36": CAMPAIGN_36, "group_name": GROUP},
    )


def insert_campaign37_bentos_from_backup(conn, project_id, campaign37_id):
    effort_cols = table_columns(conn, "esforcos_amostragem")
    bentos_cols = table_columns(conn, "resultados_zoobentos")
    consolidated_cols = table_columns(conn, "biota_analise_consolidada")

    effort_exprs = []
    for col in effort_cols:
        if col == "id_ponto_coleta":
            effort_exprs.append("target_pc.id_ponto_coleta")
        else:
            effort_exprs.append(f"e.{col}")

    conn.execute(
        text(
            f"""
            INSERT INTO public.esforcos_amostragem ({', '.join(f'"{col}"' for col in effort_cols)})
            SELECT {', '.join(effort_exprs)}
            FROM public.{BACKUP_EFFORTS} e
            JOIN public.{BACKUP_POINTS} source_pc
              ON source_pc.id_ponto_coleta = e.id_ponto_coleta
            JOIN public.pontos_coleta target_pc
              ON target_pc.id_projeto = :project_id
             AND target_pc.id_campanha = :campaign37_id
             AND target_pc.nome_ponto = source_pc.nome_ponto
            WHERE source_pc.id_campanha = 444
              AND e.grupo_biologico = :group_name
            """
        ),
        {
            "project_id": project_id,
            "campaign37_id": campaign37_id,
            "group_name": GROUP,
        },
    )

    conn.execute(
        text(
            f"""
            INSERT INTO public.resultados_zoobentos ({', '.join(f'"{col}"' for col in bentos_cols)})
            SELECT {', '.join('r.' + col for col in bentos_cols)}
            FROM public.{BACKUP_BENTOS} r
            JOIN public.{BACKUP_EFFORTS} e ON e.id_esforco = r.id_esforco
            JOIN public.{BACKUP_POINTS} source_pc
              ON source_pc.id_ponto_coleta = e.id_ponto_coleta
            WHERE source_pc.id_campanha = 444
              AND e.grupo_biologico = :group_name
            """
        ),
        {"group_name": GROUP},
    )

    consolidated_exprs = []
    for col in consolidated_cols:
        if col == "nome_campanha":
            consolidated_exprs.append(":campaign37")
        elif col == "data_hora_coleta":
            consolidated_exprs.append(
                "(SELECT min(pc.data_hora_coleta) FROM public.pontos_coleta pc "
                "WHERE pc.id_projeto = :project_id AND pc.id_campanha = :campaign37_id)"
            )
        else:
            consolidated_exprs.append(f"c.{col}")

    conn.execute(
        text(
            f"""
            INSERT INTO public.biota_analise_consolidada ({', '.join(f'"{col}"' for col in consolidated_cols)})
            SELECT {', '.join(consolidated_exprs)}
            FROM public.{BACKUP_CONSOLIDATED} c
            WHERE c.nome_campanha = 'C37-11-2025-CH'
              AND c.grupo_biologico = :group_name
            """
        ),
        {
            "project_id": project_id,
            "campaign37_id": campaign37_id,
            "campaign37": CAMPAIGN_37,
            "group_name": GROUP,
        },
    )


def set_sequences(conn):
    sequence_map = {
        "esforcos_amostragem_id_esforco_seq": ("esforcos_amostragem", "id_esforco"),
        "resultados_zoobentos_id_resultado_bento_seq": ("resultados_zoobentos", "id_resultado_bento"),
        "biota_analise_consolidada_id_resultado_pk_seq": ("biota_analise_consolidada", "id_resultado_pk"),
    }
    for sequence, (table, column) in sequence_map.items():
        exists = scalar(conn, "SELECT to_regclass(:sequence_name)", {"sequence_name": f"public.{sequence}"})
        if exists:
            conn.execute(
                text(
                    f"""
                    SELECT setval(
                        'public.{sequence}',
                        COALESCE((SELECT max({column}) FROM public.{table}), 1),
                        true
                    )
                    """
                )
            )


def main():
    engine = get_engine()
    with engine.begin() as conn:
        project_id = scalar(
            conn,
            """
            SELECT id_projeto
            FROM public.projetos
            WHERE trim(codigo_interno_opyta) = :project_code
            """,
            {"project_code": PROJECT_CODE},
        )
        if project_id is None:
            raise RuntimeError(f"Project not found: {PROJECT_CODE}")

        campaign36_id = scalar(
            conn,
            "SELECT id_campanha FROM public.campanhas WHERE nome_campanha = :name",
            {"name": CAMPAIGN_36},
        )
        campaign37_id = scalar(
            conn,
            "SELECT id_campanha FROM public.campanhas WHERE nome_campanha = :name",
            {"name": CAMPAIGN_37},
        )
        if campaign36_id is None or campaign37_id is None:
            raise RuntimeError("Campaign 36 or 37 not found.")

        for table_name in [BACKUP_CAMPAIGNS, BACKUP_POINTS, BACKUP_EFFORTS, BACKUP_BENTOS, BACKUP_CONSOLIDATED]:
            if not scalar(conn, "SELECT to_regclass(:table_name)", {"table_name": f"public.{table_name}"}):
                raise RuntimeError(f"Required backup table not found: {table_name}")

        before = summarize(conn, project_id)
        backup_prefix = create_current_backup(conn, project_id, campaign36_id, campaign37_id)

        delete_current_campaign36_bentos(conn, project_id, campaign36_id)
        restore_campaign36_bentos(conn)
        insert_campaign37_bentos_from_backup(conn, project_id, campaign37_id)
        set_sequences(conn)

        after = summarize(conn, project_id)

        print("current_state_backup_prefix", backup_prefix)
        print("\nBEFORE")
        print(before.to_string(index=False))
        print("\nAFTER")
        print(after.to_string(index=False))


if __name__ == "__main__":
    main()
