from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
OPYTA_DATA_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data")
for path in (ROOT / "src", OPYTA_DATA_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.engine import get_engine  # noqa: E402


PROJECT_ID = 9
PROJECT_CODE = "BRAAVG002"
GROUP = "Zoobentos"
TARGET_TABLE = "biota_analise_consolidada"
AUDIT_DIR = ROOT / "outputs" / "_migration" / "avg_bentos_2026"


SOURCE_SUMMARY_SQL = text(
    """
    SELECT
        COUNT(*)::int AS linhas,
        COUNT(DISTINCT rz.id_esforco)::int AS esforcos_com_resultado,
        COUNT(DISTINCT rz.id_especie)::int AS taxa,
        COALESCE(SUM(rz.abundancia), 0)::numeric AS contagem_total,
        COUNT(DISTINCT p.id_campanha)::int AS campanhas,
        COUNT(DISTINCT p.nome_ponto)::int AS pontos,
        MIN(p.data_hora_coleta) AS primeira_data,
        MAX(p.data_hora_coleta) AS ultima_data
    FROM resultados_zoobentos rz
    JOIN esforcos_amostragem e
        ON e.id_esforco = rz.id_esforco
    JOIN pontos_coleta p
        ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN projetos pr
        ON pr.id_projeto = p.id_projeto
    WHERE p.id_projeto = :project_id
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = :group
    """
)


TARGET_SUMMARY_SQL = text(
    """
    SELECT
        COUNT(*)::int AS linhas,
        COUNT(DISTINCT nome_campanha)::int AS campanhas,
        COUNT(DISTINCT nome_ponto)::int AS pontos,
        COUNT(DISTINCT nome_cientifico)::int AS taxa,
        COALESCE(SUM(contagem), 0)::numeric AS contagem_total,
        MIN(data_hora_coleta) AS primeira_data,
        MAX(data_hora_coleta) AS ultima_data
    FROM biota_analise_consolidada
    WHERE codigo_interno_opyta = :project_code
      AND grupo_biologico = :group
    """
)


SOURCE_CAMPAIGNS_SQL = text(
    """
    SELECT
        c.id_campanha::int AS id_campanha,
        c.nome_campanha,
        COUNT(*)::int AS linhas,
        COUNT(DISTINCT p.nome_ponto)::int AS pontos,
        COUNT(DISTINCT rz.id_especie)::int AS taxa,
        COALESCE(SUM(rz.abundancia), 0)::numeric AS contagem_total
    FROM resultados_zoobentos rz
    JOIN esforcos_amostragem e
        ON e.id_esforco = rz.id_esforco
    JOIN pontos_coleta p
        ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN campanhas c
        ON c.id_campanha = p.id_campanha
    JOIN projetos pr
        ON pr.id_projeto = p.id_projeto
    WHERE p.id_projeto = :project_id
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = :group
    GROUP BY c.id_campanha, c.nome_campanha
    ORDER BY c.id_campanha
    """
)


TARGET_CAMPAIGNS_SQL = text(
    """
    SELECT
        nome_campanha,
        COUNT(*)::int AS linhas,
        COUNT(DISTINCT nome_ponto)::int AS pontos,
        COUNT(DISTINCT nome_cientifico)::int AS taxa,
        COALESCE(SUM(contagem), 0)::numeric AS contagem_total
    FROM biota_analise_consolidada
    WHERE codigo_interno_opyta = :project_code
      AND grupo_biologico = :group
    GROUP BY nome_campanha
    ORDER BY MIN(data_hora_coleta), nome_campanha
    """
)


INSERT_SQL = text(
    """
    INSERT INTO biota_analise_consolidada (
        nome_empresa,
        nome_projeto,
        codigo_opyta,
        nome_campanha,
        nome_ponto,
        latitude,
        longitude,
        grupo_biologico,
        nome_cientifico,
        contagem,
        biomassa,
        bmwp_score,
        codigo_interno_opyta,
        data_hora_coleta,
        bacia_hidrografica,
        metodo_de_captura,
        esforco,
        unidade_esforco,
        nome_popular,
        reino,
        filo,
        classe,
        ordem,
        familia,
        genero,
        origem,
        medida_1,
        medida_2,
        tipo_amostragem,
        id_empreendimento,
        nome_empreendimento
    )
    SELECT
        cli.nome_empresa,
        pr.nome_projeto,
        NULL::text AS codigo_opyta,
        c.nome_campanha,
        p.nome_ponto,
        p.latitude,
        p.longitude,
        e.grupo_biologico,
        sp.nome_cientifico,
        rz.abundancia::numeric AS contagem,
        NULL::numeric AS biomassa,
        sp.bmwp_score,
        pr.codigo_interno_opyta,
        p.data_hora_coleta,
        p.bacia_hidrografica,
        e.metodo_de_captura,
        e.esforco,
        e.unidade_esforco,
        sp.nome_popular,
        sp.reino,
        sp.filo,
        sp.classe,
        sp.ordem,
        sp.familia,
        sp.genero,
        sp.origem,
        NULL::numeric AS medida_1,
        NULL::numeric AS medida_2,
        COALESCE(rz.tipo_amostragem, e.tipo_amostragem, e.tipo_de_amostragem) AS tipo_amostragem,
        p.id_empreendimento,
        emp.nome AS nome_empreendimento
    FROM resultados_zoobentos rz
    JOIN esforcos_amostragem e
        ON e.id_esforco = rz.id_esforco
    JOIN pontos_coleta p
        ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN campanhas c
        ON c.id_campanha = p.id_campanha
    JOIN projetos pr
        ON pr.id_projeto = p.id_projeto
    JOIN clientes cli
        ON cli.id_cliente = pr.id_cliente
    JOIN especies sp
        ON sp.id_especie = rz.id_especie
    LEFT JOIN empreendimentos emp
        ON emp.id_empreendimento = p.id_empreendimento
    WHERE p.id_projeto = :project_id
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = :group
    ORDER BY p.data_hora_coleta, c.id_campanha, p.nome_ponto, sp.nome_cientifico, rz.id_resultado_bento
    """
)


DELETE_SQL = text(
    """
    DELETE FROM biota_analise_consolidada
    WHERE codigo_interno_opyta = :project_code
      AND grupo_biologico = :group
    """
)


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _params() -> dict[str, Any]:
    return {
        "project_id": PROJECT_ID,
        "project_code": PROJECT_CODE,
        "group": GROUP,
    }


def _one_mapping(conn, stmt) -> dict[str, Any]:
    return dict(conn.execute(stmt, _params()).mappings().one())


def _all_mappings(conn, stmt) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(stmt, _params()).mappings().all()]


def _write_audit(name: str, payload: dict[str, Any]) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / name
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return out


def preflight(engine) -> dict[str, Any]:
    with engine.begin() as conn:
        source_summary = _one_mapping(conn, SOURCE_SUMMARY_SQL)
        target_before = _one_mapping(conn, TARGET_SUMMARY_SQL)
        source_campaigns = _all_mappings(conn, SOURCE_CAMPAIGNS_SQL)
        target_campaigns = _all_mappings(conn, TARGET_CAMPAIGNS_SQL)
    return {
        "applied": False,
        "project_id": PROJECT_ID,
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "source_summary": source_summary,
        "target_before": target_before,
        "source_campaigns": source_campaigns,
        "target_campaigns_before": target_campaigns,
    }


def apply_consolidation(engine) -> dict[str, Any]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_table = f"bkp_biota_avg_zoobentos_{stamp}"
    params = _params()
    with engine.begin() as conn:
        source_summary = _one_mapping(conn, SOURCE_SUMMARY_SQL)
        target_before = _one_mapping(conn, TARGET_SUMMARY_SQL)
        source_campaigns = _all_mappings(conn, SOURCE_CAMPAIGNS_SQL)

        conn.execute(
            text(
                f"""
                CREATE TABLE {backup_table} AS
                SELECT *
                FROM biota_analise_consolidada
                WHERE codigo_interno_opyta = :project_code
                  AND grupo_biologico = :group
                """
            ),
            params,
        )
        backed_up = conn.execute(text(f"SELECT COUNT(*)::int FROM {backup_table}")).scalar_one()
        deleted = conn.execute(DELETE_SQL, params).rowcount
        inserted = conn.execute(INSERT_SQL, params).rowcount

        target_after = _one_mapping(conn, TARGET_SUMMARY_SQL)
        target_campaigns_after = _all_mappings(conn, TARGET_CAMPAIGNS_SQL)

    expected_rows = int(source_summary["linhas"])
    after_rows = int(target_after["linhas"])
    if after_rows != expected_rows or inserted != expected_rows:
        raise RuntimeError(
            "Consolidacao aplicada, mas a conferencia de linhas falhou: "
            f"source={expected_rows}, inserted={inserted}, target_after={after_rows}"
        )

    return {
        "applied": True,
        "project_id": PROJECT_ID,
        "project_code": PROJECT_CODE,
        "group": GROUP,
        "backup_table": backup_table,
        "source_summary": source_summary,
        "target_before": target_before,
        "backed_up_rows": backed_up,
        "deleted_rows": deleted,
        "inserted_rows": inserted,
        "target_after": target_after,
        "source_campaigns": source_campaigns,
        "target_campaigns_after": target_campaigns_after,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolida AVG Zoobentos na tabela analitica.")
    parser.add_argument("--apply", action="store_true", help="Executa backup, delete e insert da fatia AVG/Zoobentos.")
    args = parser.parse_args()

    engine = get_engine()
    try:
        if args.apply:
            payload = apply_consolidation(engine)
            out = _write_audit("consolidation_applied.json", payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
            print(f"\nAudit: {out}")
        else:
            payload = preflight(engine)
            out = _write_audit("consolidation_preflight.json", payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
            print(f"\nAudit: {out}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
