import os
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_CODE = "GEOHER001"
RESULT_TABLES = [
    {
        "name": "resultados_ictiofauna",
        "pk": "id_resultado_ictio",
        "fields": [
            "numero_de_individuos",
            "ct_cm",
            "cp_cm",
            "pc_g",
            "sexo",
            "emg",
            "observacao_individuo_lote",
            "tipo_amostragem",
        ],
    },
    {
        "name": "resultados_zoobentos",
        "pk": "id_resultado_bento",
        "fields": ["abundancia", "tipo_amostragem"],
    },
]

MONTHS = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}


def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    name = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", "5432")
    missing = [k for k, v in {
        "DB_USER": user,
        "DB_PASSWORD": password,
        "DB_HOST": host,
        "DB_NAME": name,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    url = (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}?connect_timeout=15"
    )
    return create_engine(url)


def normalize_label(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.replace("\u00aa", "a").replace("\u00ba", "o").strip().lower()


def parse_campaign_label(name):
    normalized = normalize_label(name)
    match = re.match(r"^(\d+)a-([a-z]{3})-(\d{2})-(sc|ch)$", normalized)
    if not match:
        return None
    number, month_label, year_short, season = match.groups()
    if month_label not in MONTHS:
        return None
    return {
        "number": int(number),
        "month_from_label": MONTHS[month_label],
        "year_from_label": 2000 + int(year_short),
        "season": season.upper(),
    }


def standard_name(name, data_min=None):
    already_standard = re.match(r"^C\d{2}-\d{2}-\d{4}-(SC|CH)$", str(name).strip())
    if already_standard:
        return str(name).strip()

    parsed = parse_campaign_label(name)
    if not parsed:
        raise ValueError(f"Cannot parse campaign label: {name!r}")

    if data_min is not None and not pd.isna(data_min):
        month = int(data_min.month)
        year = int(data_min.year)
    else:
        month = parsed["month_from_label"]
        year = parsed["year_from_label"]

    return f"C{parsed['number']:02d}-{month:02d}-{year:04d}-{parsed['season']}"


def comparable(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def rows_match(source, target, fields):
    return all(comparable(source.get(field)) == comparable(target.get(field)) for field in fields)


def scalar(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).scalar()


def all_rows(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).mappings().all()


def one_or_none(conn, sql, params=None):
    return conn.execute(text(sql), params or {}).mappings().first()


def collect_campaigns(conn, project_id):
    df = pd.read_sql(
        text(
            """
            SELECT ca.id_campanha, ca.nome_campanha,
                   min(pc.data_hora_coleta) AS data_min,
                   max(pc.data_hora_coleta) AS data_max,
                   count(DISTINCT pc.id_ponto_coleta) AS pontos,
                   count(DISTINCT e.id_esforco) AS esforcos,
                   count(ri.id_resultado_ictio) AS ictio,
                   count(rz.id_resultado_bento) AS bentos,
                   count(DISTINCT e.grupo_biologico) AS grupos
            FROM public.pontos_coleta pc
            JOIN public.campanhas ca ON ca.id_campanha = pc.id_campanha
            LEFT JOIN public.esforcos_amostragem e ON e.id_ponto_coleta = pc.id_ponto_coleta
            LEFT JOIN public.resultados_ictiofauna ri ON ri.id_esforco = e.id_esforco
            LEFT JOIN public.resultados_zoobentos rz ON rz.id_esforco = e.id_esforco
            WHERE pc.id_projeto = :project_id
            GROUP BY ca.id_campanha, ca.nome_campanha
            ORDER BY ca.id_campanha
            """
        ),
        conn,
        params={"project_id": project_id},
    )
    df["standard"] = df.apply(
        lambda row: standard_name(row["nome_campanha"], row["data_min"]),
        axis=1,
    )
    df["result_count"] = df["ictio"] + df["bentos"]
    df["has_ordinal_indicator"] = df["nome_campanha"].astype(str).str.contains("\u00aa", regex=False)
    return df


def choose_keeper(group):
    ranked = group.sort_values(
        by=["result_count", "grupos", "has_ordinal_indicator", "esforcos", "id_campanha"],
        ascending=[False, False, False, False, True],
    )
    return int(ranked.iloc[0]["id_campanha"])


def create_backups(conn, project_id, campaign_ids):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    prefix = f"backup_geoher001_campaign_fix_{stamp}"
    id_list = ", ".join(str(int(value)) for value in sorted(campaign_ids))

    conn.execute(text(f"CREATE TABLE public.{prefix}_campanhas AS SELECT * FROM public.campanhas WHERE id_campanha IN ({id_list})"))
    conn.execute(text(f"CREATE TABLE public.{prefix}_pontos AS SELECT * FROM public.pontos_coleta WHERE id_projeto = :project_id"), {"project_id": project_id})
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_esforcos AS
            SELECT e.*
            FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta pc ON pc.id_ponto_coleta = e.id_ponto_coleta
            WHERE pc.id_projeto = :project_id
            """
        ),
        {"project_id": project_id},
    )
    for table in RESULT_TABLES:
        conn.execute(
            text(
                f"""
                CREATE TABLE public.{prefix}_{table['name']} AS
                SELECT r.*
                FROM public.{table['name']} r
                JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
                JOIN public.pontos_coleta pc ON pc.id_ponto_coleta = e.id_ponto_coleta
                WHERE pc.id_projeto = :project_id
                """
            ),
            {"project_id": project_id},
        )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{prefix}_consolidada AS
            SELECT *
            FROM public.biota_analise_consolidada
            WHERE trim(codigo_interno_opyta) = :project_code
            """
        ),
        {"project_code": PROJECT_CODE},
    )
    return prefix


def ensure_no_external_campaign_usage(conn, project_id, campaign_ids):
    id_list = ", ".join(str(int(value)) for value in sorted(campaign_ids))
    rows = all_rows(
        conn,
        f"""
        SELECT pc.id_campanha, ca.nome_campanha, count(DISTINCT pc.id_projeto) AS projetos
        FROM public.pontos_coleta pc
        JOIN public.campanhas ca ON ca.id_campanha = pc.id_campanha
        WHERE pc.id_campanha IN ({id_list})
        GROUP BY pc.id_campanha, ca.nome_campanha
        HAVING bool_or(pc.id_projeto <> :project_id)
        """,
        {"project_id": project_id},
    )
    if rows:
        raise RuntimeError(f"Campaign IDs used by other projects: {rows}")


def ensure_no_name_conflicts(conn, campaign_ids, standards):
    id_list = ", ".join(str(int(value)) for value in sorted(campaign_ids))
    rows = all_rows(
        conn,
        f"""
        SELECT id_campanha, nome_campanha
        FROM public.campanhas
        WHERE nome_campanha = ANY(:standards)
          AND id_campanha NOT IN ({id_list})
        """,
        {"standards": sorted(standards)},
    )
    if rows:
        raise RuntimeError(f"Standard campaign names already exist outside this fix: {rows}")


def merge_result_table(conn, table, source_effort_id, target_effort_id):
    source_rows = all_rows(
        conn,
        f"SELECT * FROM public.{table['name']} WHERE id_esforco = :source_effort_id ORDER BY {table['pk']}",
        {"source_effort_id": source_effort_id},
    )
    for source in source_rows:
        target = one_or_none(
            conn,
            f"""
            SELECT *
            FROM public.{table['name']}
            WHERE id_esforco = :target_effort_id
              AND id_especie = :id_especie
            """,
            {"target_effort_id": target_effort_id, "id_especie": source["id_especie"]},
        )
        if target is None:
            conn.execute(
                text(
                    f"""
                    UPDATE public.{table['name']}
                    SET id_esforco = :target_effort_id
                    WHERE {table['pk']} = :source_pk
                    """
                ),
                {"target_effort_id": target_effort_id, "source_pk": source[table["pk"]]},
            )
        elif rows_match(source, target, table["fields"]):
            conn.execute(
                text(f"DELETE FROM public.{table['name']} WHERE {table['pk']} = :source_pk"),
                {"source_pk": source[table["pk"]]},
            )
        else:
            raise RuntimeError(
                "Conflicting non-duplicate result: "
                f"{table['name']} source_effort={source_effort_id} "
                f"target_effort={target_effort_id} species={source['id_especie']}"
            )


def merge_effort(conn, source_effort, target_point_id):
    target_effort = one_or_none(
        conn,
        """
        SELECT id_esforco
        FROM public.esforcos_amostragem
        WHERE id_ponto_coleta = :target_point_id
          AND grupo_biologico IS NOT DISTINCT FROM :grupo
          AND metodo_de_captura IS NOT DISTINCT FROM :metodo
        ORDER BY id_esforco
        LIMIT 1
        """,
        {
            "target_point_id": target_point_id,
            "grupo": source_effort["grupo_biologico"],
            "metodo": source_effort["metodo_de_captura"],
        },
    )
    if target_effort is None:
        conn.execute(
            text(
                """
                UPDATE public.esforcos_amostragem
                SET id_ponto_coleta = :target_point_id
                WHERE id_esforco = :source_effort_id
                """
            ),
            {
                "target_point_id": target_point_id,
                "source_effort_id": source_effort["id_esforco"],
            },
        )
        return

    target_effort_id = target_effort["id_esforco"]
    for table in RESULT_TABLES:
        merge_result_table(conn, table, source_effort["id_esforco"], target_effort_id)

    remaining_results = 0
    for table in RESULT_TABLES:
        remaining_results += scalar(
            conn,
            f"SELECT count(*) FROM public.{table['name']} WHERE id_esforco = :source_effort_id",
            {"source_effort_id": source_effort["id_esforco"]},
        )
    if remaining_results:
        raise RuntimeError(f"Source effort still has results: {source_effort['id_esforco']}")

    conn.execute(
        text("DELETE FROM public.esforcos_amostragem WHERE id_esforco = :source_effort_id"),
        {"source_effort_id": source_effort["id_esforco"]},
    )


def merge_campaign(conn, project_id, source_campaign_id, target_campaign_id):
    source_points = all_rows(
        conn,
        """
        SELECT *
        FROM public.pontos_coleta
        WHERE id_projeto = :project_id AND id_campanha = :source_campaign_id
        ORDER BY nome_ponto, id_ponto_coleta
        """,
        {"project_id": project_id, "source_campaign_id": source_campaign_id},
    )

    for point in source_points:
        target_point = one_or_none(
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
                "nome_ponto": point["nome_ponto"],
            },
        )
        if target_point is None:
            conn.execute(
                text(
                    """
                    UPDATE public.pontos_coleta
                    SET id_campanha = :target_campaign_id
                    WHERE id_ponto_coleta = :source_point_id
                    """
                ),
                {
                    "target_campaign_id": target_campaign_id,
                    "source_point_id": point["id_ponto_coleta"],
                },
            )
            continue

        source_efforts = all_rows(
            conn,
            """
            SELECT *
            FROM public.esforcos_amostragem
            WHERE id_ponto_coleta = :source_point_id
            ORDER BY grupo_biologico, metodo_de_captura, id_esforco
            """,
            {"source_point_id": point["id_ponto_coleta"]},
        )
        for effort in source_efforts:
            merge_effort(conn, effort, target_point["id_ponto_coleta"])

        remaining_efforts = scalar(
            conn,
            "SELECT count(*) FROM public.esforcos_amostragem WHERE id_ponto_coleta = :source_point_id",
            {"source_point_id": point["id_ponto_coleta"]},
        )
        if remaining_efforts:
            raise RuntimeError(f"Source point still has efforts: {point['id_ponto_coleta']}")

        conn.execute(
            text("DELETE FROM public.pontos_coleta WHERE id_ponto_coleta = :source_point_id"),
            {"source_point_id": point["id_ponto_coleta"]},
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


def update_consolidated_campaign_names(conn):
    rows = all_rows(
        conn,
        """
        SELECT id_resultado_pk, nome_campanha, data_hora_coleta
        FROM public.biota_analise_consolidada
        WHERE trim(codigo_interno_opyta) = :project_code
        """,
        {"project_code": PROJECT_CODE},
    )
    grouped = {}
    for row in rows:
        grouped[(row["nome_campanha"], row["data_hora_coleta"])] = standard_name(
            row["nome_campanha"],
            row["data_hora_coleta"],
        )

    for (old_name, data_hora), new_name in grouped.items():
        conn.execute(
            text(
                """
                UPDATE public.biota_analise_consolidada
                SET nome_campanha = :new_name
                WHERE trim(codigo_interno_opyta) = :project_code
                  AND nome_campanha = :old_name
                  AND data_hora_coleta IS NOT DISTINCT FROM :data_hora
                """
            ),
            {
                "new_name": new_name,
                "project_code": PROJECT_CODE,
                "old_name": old_name,
                "data_hora": data_hora,
            },
        )

    columns = pd.read_sql(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'biota_analise_consolidada'
            ORDER BY ordinal_position
            """
        ),
        conn,
    )["column_name"].tolist()
    partition_cols = [f'"{col}"' for col in columns if col != "id_resultado_pk"]
    partition_sql = ", ".join(partition_cols)
    deleted = scalar(
        conn,
        f"""
        WITH ranked AS (
            SELECT id_resultado_pk,
                   row_number() OVER (
                       PARTITION BY {partition_sql}
                       ORDER BY id_resultado_pk
                   ) AS rn
            FROM public.biota_analise_consolidada
            WHERE trim(codigo_interno_opyta) = :project_code
        ), deleted AS (
            DELETE FROM public.biota_analise_consolidada b
            USING ranked r
            WHERE b.id_resultado_pk = r.id_resultado_pk
              AND r.rn > 1
            RETURNING b.id_resultado_pk
        )
        SELECT count(*) FROM deleted
        """,
        {"project_code": PROJECT_CODE},
    )
    return int(deleted)


def summarize(conn, project_id):
    summary = pd.read_sql(
        text(
            """
            WITH pontos AS (
                SELECT * FROM public.pontos_coleta WHERE id_projeto = :project_id
            ), esforcos AS (
                SELECT e.*
                FROM public.esforcos_amostragem e
                JOIN pontos p ON p.id_ponto_coleta = e.id_ponto_coleta
            )
            SELECT 'campanhas' AS item, count(DISTINCT id_campanha)::bigint AS total FROM pontos
            UNION ALL SELECT 'pontos', count(*) FROM pontos
            UNION ALL SELECT 'esforcos', count(*) FROM esforcos
            UNION ALL SELECT 'ictio_resultados', count(*)
                FROM public.resultados_ictiofauna r JOIN esforcos e ON e.id_esforco = r.id_esforco
            UNION ALL SELECT 'bentos_resultados', count(*)
                FROM public.resultados_zoobentos r JOIN esforcos e ON e.id_esforco = r.id_esforco
            UNION ALL SELECT 'consolidada', count(*)
                FROM public.biota_analise_consolidada WHERE trim(codigo_interno_opyta) = :project_code
            """
        ),
        conn,
        params={"project_id": project_id, "project_code": PROJECT_CODE},
    )
    return summary


def main():
    engine = get_engine()
    with engine.begin() as conn:
        project_id = scalar(
            conn,
            "SELECT id_projeto FROM public.projetos WHERE trim(codigo_interno_opyta) = :project_code",
            {"project_code": PROJECT_CODE},
        )
        if project_id is None:
            raise RuntimeError(f"Project not found: {PROJECT_CODE}")

        campaigns = collect_campaigns(conn, project_id)
        campaign_ids = set(campaigns["id_campanha"].astype(int))
        standards = set(campaigns["standard"])
        ensure_no_external_campaign_usage(conn, project_id, campaign_ids)
        ensure_no_name_conflicts(conn, campaign_ids, standards)

        before = summarize(conn, project_id)
        backup_prefix = create_backups(conn, project_id, campaign_ids)

        mapping = {}
        for standard, group in campaigns.groupby("standard"):
            keeper = choose_keeper(group)
            mapping[standard] = keeper
            for campaign_id in group["id_campanha"].astype(int):
                if campaign_id != keeper:
                    merge_campaign(conn, project_id, campaign_id, keeper)

        for standard, campaign_id in mapping.items():
            conn.execute(
                text(
                    """
                    UPDATE public.campanhas
                    SET nome_campanha = :standard
                    WHERE id_campanha = :campaign_id
                    """
                ),
                {"standard": standard, "campaign_id": campaign_id},
            )

        deleted_consolidated = update_consolidated_campaign_names(conn)
        after = summarize(conn, project_id)

        print("backup_prefix", backup_prefix)
        print("deleted_consolidated_duplicates", deleted_consolidated)
        print("\nBEFORE")
        print(before.to_string(index=False))
        print("\nAFTER")
        print(after.to_string(index=False))

        campaign_check = pd.read_sql(
            text(
                """
                SELECT ca.id_campanha, ca.nome_campanha,
                       count(DISTINCT pc.id_ponto_coleta) AS pontos,
                       count(DISTINCT e.id_esforco) AS esforcos,
                       string_agg(DISTINCT e.grupo_biologico, ', ' ORDER BY e.grupo_biologico) AS grupos,
                       min(pc.data_hora_coleta) AS data_min,
                       max(pc.data_hora_coleta) AS data_max
                FROM public.pontos_coleta pc
                JOIN public.campanhas ca ON ca.id_campanha = pc.id_campanha
                LEFT JOIN public.esforcos_amostragem e ON e.id_ponto_coleta = pc.id_ponto_coleta
                WHERE pc.id_projeto = :project_id
                GROUP BY ca.id_campanha, ca.nome_campanha
                ORDER BY ca.nome_campanha
                """
            ),
            conn,
            params={"project_id": project_id},
        )
        print("\nCAMPAIGNS_AFTER")
        print(campaign_check.to_string(index=False))


if __name__ == "__main__":
    main()
