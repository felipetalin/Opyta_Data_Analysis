import os
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_CODE = "GEOHER001"
SOURCE_CAMPAIGN = "C37-11-2025-CH"
TARGET_CAMPAIGN = "C36-11-2025-CH"
GROUP = "Zoobentos"


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

    url = (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}?connect_timeout=15"
    )
    return create_engine(url)


def scalar(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).scalar()


def mappings(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).mappings().all()


def mapping_one(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).mappings().first()


def create_backup(conn, project_id, source_campaign_id, target_campaign_id):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    prefix = f"backup_geoher001_bentos_c36_merge_{stamp}"
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_campanhas AS
            SELECT *
            FROM public.campanhas
            WHERE id_campanha IN (:source_campaign_id, :target_campaign_id)
            """
        ),
        {
            "source_campaign_id": source_campaign_id,
            "target_campaign_id": target_campaign_id,
        },
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_pontos AS
            SELECT *
            FROM public.pontos_coleta
            WHERE id_projeto = :project_id
              AND id_campanha IN (:source_campaign_id, :target_campaign_id)
            """
        ),
        {
            "project_id": project_id,
            "source_campaign_id": source_campaign_id,
            "target_campaign_id": target_campaign_id,
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
              AND pc.id_campanha IN (:source_campaign_id, :target_campaign_id)
            """
        ),
        {
            "project_id": project_id,
            "source_campaign_id": source_campaign_id,
            "target_campaign_id": target_campaign_id,
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
              AND pc.id_campanha IN (:source_campaign_id, :target_campaign_id)
              AND e.grupo_biologico = :group_name
            """
        ),
        {
            "project_id": project_id,
            "source_campaign_id": source_campaign_id,
            "target_campaign_id": target_campaign_id,
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
              AND nome_campanha IN (:source_campaign, :target_campaign)
            """
        ),
        {
            "project_code": PROJECT_CODE,
            "group_name": GROUP,
            "source_campaign": SOURCE_CAMPAIGN,
            "target_campaign": TARGET_CAMPAIGN,
        },
    )
    return prefix


def merge_relational(conn, project_id, source_campaign_id, target_campaign_id):
    source_points = mappings(
        conn,
        """
        SELECT *
        FROM public.pontos_coleta
        WHERE id_projeto = :project_id
          AND id_campanha = :source_campaign_id
        ORDER BY nome_ponto
        """,
        {"project_id": project_id, "source_campaign_id": source_campaign_id},
    )

    merged_results = 0
    moved_results = 0

    for source_point in source_points:
        target_point = mapping_one(
            conn,
            """
            SELECT *
            FROM public.pontos_coleta
            WHERE id_projeto = :project_id
              AND id_campanha = :target_campaign_id
              AND nome_ponto = :nome_ponto
            ORDER BY id_ponto_coleta
            LIMIT 1
            """,
            {
                "project_id": project_id,
                "target_campaign_id": target_campaign_id,
                "nome_ponto": source_point["nome_ponto"],
            },
        )
        if not target_point:
            raise RuntimeError(f"Target point not found for {source_point['nome_ponto']}")

        source_effort = mapping_one(
            conn,
            """
            SELECT *
            FROM public.esforcos_amostragem
            WHERE id_ponto_coleta = :source_point_id
              AND grupo_biologico = :group_name
            ORDER BY id_esforco
            LIMIT 1
            """,
            {
                "source_point_id": source_point["id_ponto_coleta"],
                "group_name": GROUP,
            },
        )
        if not source_effort:
            continue

        target_effort = mapping_one(
            conn,
            """
            SELECT *
            FROM public.esforcos_amostragem
            WHERE id_ponto_coleta = :target_point_id
              AND grupo_biologico = :group_name
              AND metodo_de_captura IS NOT DISTINCT FROM :metodo
            ORDER BY id_esforco
            LIMIT 1
            """,
            {
                "target_point_id": target_point["id_ponto_coleta"],
                "group_name": GROUP,
                "metodo": source_effort["metodo_de_captura"],
            },
        )
        if not target_effort:
            raise RuntimeError(f"Target effort not found for {source_point['nome_ponto']}")

        source_results = mappings(
            conn,
            """
            SELECT *
            FROM public.resultados_zoobentos
            WHERE id_esforco = :source_effort_id
            ORDER BY id_resultado_bento
            """,
            {"source_effort_id": source_effort["id_esforco"]},
        )
        for source_result in source_results:
            target_result = mapping_one(
                conn,
                """
                SELECT *
                FROM public.resultados_zoobentos
                WHERE id_esforco = :target_effort_id
                  AND id_especie = :id_especie
                """,
                {
                    "target_effort_id": target_effort["id_esforco"],
                    "id_especie": source_result["id_especie"],
                },
            )
            if target_result:
                conn.execute(
                    text(
                        """
                        UPDATE public.resultados_zoobentos
                        SET abundancia = COALESCE(abundancia, 0) + COALESCE(:source_abundancia, 0),
                            tipo_amostragem = COALESCE(tipo_amostragem, :source_tipo)
                        WHERE id_resultado_bento = :target_result_id
                        """
                    ),
                    {
                        "source_abundancia": source_result["abundancia"],
                        "source_tipo": source_result["tipo_amostragem"],
                        "target_result_id": target_result["id_resultado_bento"],
                    },
                )
                conn.execute(
                    text(
                        """
                        DELETE FROM public.resultados_zoobentos
                        WHERE id_resultado_bento = :source_result_id
                        """
                    ),
                    {"source_result_id": source_result["id_resultado_bento"]},
                )
                merged_results += 1
            else:
                conn.execute(
                    text(
                        """
                        UPDATE public.resultados_zoobentos
                        SET id_esforco = :target_effort_id
                        WHERE id_resultado_bento = :source_result_id
                        """
                    ),
                    {
                        "target_effort_id": target_effort["id_esforco"],
                        "source_result_id": source_result["id_resultado_bento"],
                    },
                )
                moved_results += 1

        remaining = scalar(
            conn,
            """
            SELECT count(*)
            FROM public.resultados_zoobentos
            WHERE id_esforco = :source_effort_id
            """,
            {"source_effort_id": source_effort["id_esforco"]},
        )
        if remaining:
            raise RuntimeError(f"Source effort still has bentos results: {source_effort['id_esforco']}")

        conn.execute(
            text("DELETE FROM public.esforcos_amostragem WHERE id_esforco = :source_effort_id"),
            {"source_effort_id": source_effort["id_esforco"]},
        )

        remaining_efforts = scalar(
            conn,
            """
            SELECT count(*)
            FROM public.esforcos_amostragem
            WHERE id_ponto_coleta = :source_point_id
            """,
            {"source_point_id": source_point["id_ponto_coleta"]},
        )
        if remaining_efforts:
            raise RuntimeError(f"Source point still has efforts: {source_point['id_ponto_coleta']}")

        conn.execute(
            text("DELETE FROM public.pontos_coleta WHERE id_ponto_coleta = :source_point_id"),
            {"source_point_id": source_point["id_ponto_coleta"]},
        )

    remaining_points = scalar(
        conn,
        """
        SELECT count(*)
        FROM public.pontos_coleta
        WHERE id_campanha = :source_campaign_id
        """,
        {"source_campaign_id": source_campaign_id},
    )
    if remaining_points:
        raise RuntimeError(f"Source campaign still has points: {source_campaign_id}")

    conn.execute(
        text("DELETE FROM public.campanhas WHERE id_campanha = :source_campaign_id"),
        {"source_campaign_id": source_campaign_id},
    )
    return moved_results, merged_results


def merge_consolidated(conn):
    source_rows = mappings(
        conn,
        """
        SELECT *
        FROM public.biota_analise_consolidada
        WHERE trim(codigo_interno_opyta) = :project_code
          AND grupo_biologico = :group_name
          AND nome_campanha = :source_campaign
        ORDER BY id_resultado_pk
        """,
        {
            "project_code": PROJECT_CODE,
            "group_name": GROUP,
            "source_campaign": SOURCE_CAMPAIGN,
        },
    )
    moved_rows = 0
    merged_rows = 0

    for row in source_rows:
        target = mapping_one(
            conn,
            """
            SELECT id_resultado_pk, contagem
            FROM public.biota_analise_consolidada
            WHERE trim(codigo_interno_opyta) = :project_code
              AND grupo_biologico = :group_name
              AND nome_campanha = :target_campaign
              AND nome_ponto = :nome_ponto
              AND metodo_de_captura IS NOT DISTINCT FROM :metodo
              AND nome_cientifico = :nome_cientifico
              AND tipo_amostragem IS NOT DISTINCT FROM :tipo_amostragem
            ORDER BY id_resultado_pk
            LIMIT 1
            """,
            {
                "project_code": PROJECT_CODE,
                "group_name": GROUP,
                "target_campaign": TARGET_CAMPAIGN,
                "nome_ponto": row["nome_ponto"],
                "metodo": row["metodo_de_captura"],
                "nome_cientifico": row["nome_cientifico"],
                "tipo_amostragem": row["tipo_amostragem"],
            },
        )
        if target:
            conn.execute(
                text(
                    """
                    UPDATE public.biota_analise_consolidada
                    SET contagem = COALESCE(contagem, 0) + COALESCE(:source_contagem, 0)
                    WHERE id_resultado_pk = :target_id
                    """
                ),
                {
                    "source_contagem": row["contagem"],
                    "target_id": target["id_resultado_pk"],
                },
            )
            conn.execute(
                text(
                    """
                    DELETE FROM public.biota_analise_consolidada
                    WHERE id_resultado_pk = :source_id
                    """
                ),
                {"source_id": row["id_resultado_pk"]},
            )
            merged_rows += 1
        else:
            conn.execute(
                text(
                    """
                    UPDATE public.biota_analise_consolidada
                    SET nome_campanha = :target_campaign
                    WHERE id_resultado_pk = :source_id
                    """
                ),
                {
                    "target_campaign": TARGET_CAMPAIGN,
                    "source_id": row["id_resultado_pk"],
                },
            )
            moved_rows += 1

    return moved_rows, merged_rows


def summarize(conn, project_id):
    return pd.read_sql(
        text(
            """
            SELECT ca.nome_campanha,
                   count(rz.id_resultado_bento) AS registros_bentos,
                   count(DISTINCT rz.id_especie) AS taxa_bentos,
                   count(DISTINCT pc.nome_ponto) AS pontos,
                   sum(COALESCE(rz.abundancia, 0)) AS abundancia_bentos
            FROM public.pontos_coleta pc
            JOIN public.campanhas ca ON ca.id_campanha = pc.id_campanha
            LEFT JOIN public.esforcos_amostragem e
              ON e.id_ponto_coleta = pc.id_ponto_coleta
             AND e.grupo_biologico = :group_name
            LEFT JOIN public.resultados_zoobentos rz ON rz.id_esforco = e.id_esforco
            WHERE pc.id_projeto = :project_id
              AND ca.nome_campanha IN (:source_campaign, :target_campaign)
            GROUP BY ca.nome_campanha
            ORDER BY ca.nome_campanha
            """
        ),
        conn,
        params={
            "project_id": project_id,
            "group_name": GROUP,
            "source_campaign": SOURCE_CAMPAIGN,
            "target_campaign": TARGET_CAMPAIGN,
        },
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

        source_campaign_id = scalar(
            conn,
            "SELECT id_campanha FROM public.campanhas WHERE nome_campanha = :name",
            {"name": SOURCE_CAMPAIGN},
        )
        target_campaign_id = scalar(
            conn,
            "SELECT id_campanha FROM public.campanhas WHERE nome_campanha = :name",
            {"name": TARGET_CAMPAIGN},
        )
        if source_campaign_id is None or target_campaign_id is None:
            raise RuntimeError("Source or target campaign not found.")

        external = mappings(
            conn,
            """
            SELECT pc.id_campanha, count(DISTINCT pc.id_projeto) AS project_count
            FROM public.pontos_coleta pc
            WHERE pc.id_campanha IN (:source_campaign_id, :target_campaign_id)
            GROUP BY pc.id_campanha
            HAVING bool_or(pc.id_projeto <> :project_id)
            """,
            {
                "source_campaign_id": source_campaign_id,
                "target_campaign_id": target_campaign_id,
                "project_id": project_id,
            },
        )
        if external:
            raise RuntimeError(f"Campaign used by another project: {external}")

        before = summarize(conn, project_id)
        backup_prefix = create_backup(conn, project_id, source_campaign_id, target_campaign_id)
        moved_results, merged_results = merge_relational(
            conn,
            project_id,
            source_campaign_id,
            target_campaign_id,
        )
        moved_rows, merged_rows = merge_consolidated(conn)
        after = summarize(conn, project_id)

        print("backup_prefix", backup_prefix)
        print("relational_moved_results", moved_results)
        print("relational_merged_results", merged_results)
        print("consolidated_moved_rows", moved_rows)
        print("consolidated_merged_rows", merged_rows)
        print("\nBEFORE")
        print(before.to_string(index=False))
        print("\nAFTER")
        print(after.to_string(index=False))


if __name__ == "__main__":
    main()
