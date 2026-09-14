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


PROJECT_ID = 9
PROJECT_CODE = "BRAAVG002"
AUDIT_ROOT = ROOT / "outputs" / "_project_scripts" / "BRAAVG002__monitoramento_de_ictio_e_bentos_brumado_avg"
DEFAULT_OUTPUT_DIR = AUDIT_ROOT / "campaign_crosswalk_20260713"
MONTHS = {
    "jan": (1, "Jan"),
    "janeiro": (1, "Jan"),
    "fev": (2, "Fev"),
    "fevereiro": (2, "Fev"),
    "mar": (3, "Mar"),
    "marco": (3, "Mar"),
    "março": (3, "Mar"),
    "abr": (4, "Abr"),
    "abri": (4, "Abr"),
    "abril": (4, "Abr"),
    "mai": (5, "Mai"),
    "maio": (5, "Mai"),
    "jun": (6, "Jun"),
    "junho": (6, "Jun"),
    "jul": (7, "Jul"),
    "julho": (7, "Jul"),
    "ago": (8, "Ago"),
    "agosto": (8, "Ago"),
    "set": (9, "Set"),
    "setembro": (9, "Set"),
    "out": (10, "Out"),
    "outubro": (10, "Out"),
    "nov": (11, "Nov"),
    "novembro": (11, "Nov"),
    "dez": (12, "Dez"),
    "dezembro": (12, "Dez"),
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


def campaign_parts(value: object) -> tuple[int, int, str, int]:
    raw = str(value or "")
    normalized = _normalize_text(raw)
    match = re.match(r"^\s*(\d+)", normalized)
    if not match:
        raise ValueError(f"Campanha sem numero ordinal: {raw}")
    seq = int(match.group(1))
    month_num = None
    month_label = None
    year = None
    for token in normalized.split():
        if token in MONTHS:
            month_num, month_label = MONTHS[token]
        elif re.fullmatch(r"\d{2,4}", token):
            raw_year = int(token)
            year = 2000 + raw_year if raw_year < 100 else raw_year
    if month_num is None or year is None:
        raise ValueError(f"Campanha sem mes/ano reconhecidos: {raw}")
    return seq, month_num, month_label, year


def season_from_month(month: int) -> str:
    return "CH" if month in {10, 11, 12, 1, 2, 3} else "SC"


def temporal_cycle_from_year_month(year: int, month: int) -> tuple[int, int, str]:
    start_year = year if month >= 8 else year - 1
    end_year = start_year + 1
    return start_year, end_year, f"{start_year}/{end_year}"


def load_campaign_usage() -> pd.DataFrame:
    engine = get_engine()
    try:
        campaigns = pd.read_sql(
            text(
                """
                SELECT c.id_campanha, c.nome_campanha,
                       COUNT(DISTINCT p.id_ponto_coleta) AS pontos_projeto
                FROM campanhas c
                JOIN pontos_coleta p ON p.id_campanha = c.id_campanha
                WHERE p.id_projeto = :pid
                GROUP BY c.id_campanha, c.nome_campanha
                """
            ),
            engine,
            params={"pid": PROJECT_ID},
        )
        biota_usage = pd.read_sql(
            text(
                """
                SELECT nome_campanha, grupo_biologico, COUNT(*) AS linhas
                FROM biota_analise_consolidada
                WHERE id_projeto = :pid OR codigo_interno_opyta = :code
                GROUP BY nome_campanha, grupo_biologico
                """
            ),
            engine,
            params={"pid": PROJECT_ID, "code": PROJECT_CODE},
        )
        fisico_usage = pd.read_sql(
            text(
                """
                SELECT nome_campanha, COUNT(*) AS linhas
                FROM fisico_analise_consolidada
                WHERE codigo_interno_opyta = :code
                GROUP BY nome_campanha
                """
            ),
            engine,
            params={"code": PROJECT_CODE},
        )
    finally:
        engine.dispose()
    return campaigns, biota_usage, fisico_usage


def build_crosswalk(campaigns: pd.DataFrame, biota_usage: pd.DataFrame, fisico_usage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in campaigns.iterrows():
        seq, month_num, month_label, year = campaign_parts(row["nome_campanha"])
        season = season_from_month(month_num)
        temporal_start, temporal_end, temporal_cycle = temporal_cycle_from_year_month(year, month_num)
        canonical = f"C{seq:03d}-{year}-{month_num:02d}-{season}"
        rows.append(
            {
                "id_campanha": int(row["id_campanha"]),
                "nome_campanha_atual": row["nome_campanha"],
                "campanha_ordem": seq,
                "ano": year,
                "mes": month_num,
                "mes_rotulo": month_label,
                "periodo_hidrologico": season,
                "ano_temporal_inicio": temporal_start,
                "ano_temporal_fim": temporal_end,
                "ciclo_temporal": temporal_cycle,
                "nome_campanha_padrao": canonical,
                "rotulo_curto": f"C{seq:03d}",
                "rotulo_relatorio": f"{month_label}/{str(year)[-2:]}",
                "pontos_projeto": int(row["pontos_projeto"]),
            }
        )
    crosswalk = pd.DataFrame(rows).sort_values("campanha_ordem").reset_index(drop=True)

    usage_pivot = (
        biota_usage.pivot_table(index="nome_campanha", columns="grupo_biologico", values="linhas", aggfunc="sum", fill_value=0)
        .reset_index()
        .rename_axis(None, axis=1)
    )
    usage_pivot = usage_pivot.rename(
        columns={
            "Ictiofauna": "linhas_biota_ictiofauna",
            "Zoobentos": "linhas_biota_zoobentos",
            "Fitoplancton": "linhas_biota_fitoplancton",
            "Zooplancton": "linhas_biota_zooplancton",
        }
    )
    fisico_usage = fisico_usage.rename(columns={"linhas": "linhas_fisico"})
    crosswalk = crosswalk.merge(usage_pivot, left_on="nome_campanha_atual", right_on="nome_campanha", how="left")
    crosswalk = crosswalk.drop(columns=["nome_campanha"], errors="ignore")
    crosswalk = crosswalk.merge(fisico_usage, left_on="nome_campanha_atual", right_on="nome_campanha", how="left")
    crosswalk = crosswalk.drop(columns=["nome_campanha"], errors="ignore")
    for col in [
        "linhas_biota_ictiofauna",
        "linhas_biota_zoobentos",
        "linhas_biota_fitoplancton",
        "linhas_biota_zooplancton",
        "linhas_fisico",
    ]:
        if col not in crosswalk.columns:
            crosswalk[col] = 0
        crosswalk[col] = pd.to_numeric(crosswalk[col], errors="coerce").fillna(0).astype(int)
    crosswalk["aplicar_no_banco"] = False
    crosswalk["observacao"] = "Aprovado inicialmente como camada analitica; apply no banco exige Gate A/B conforme impacto."
    return crosswalk


def sql_literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def build_dry_run_sql(crosswalk: pd.DataFrame) -> str:
    values = ",\n".join(
        f"    ({int(row.id_campanha)}, {sql_literal(row.nome_campanha_atual)}, {sql_literal(row.nome_campanha_padrao)})"
        for row in crosswalk.itertuples(index=False)
    )
    return f"""-- BRAAVG002 campaign rename dry-run / template.
-- NAO EXECUTAR sem Gate A/B explicito e backup aprovado.
WITH mapa(id_campanha, nome_atual, nome_padrao) AS (
  VALUES
{values}
)
SELECT
  'campanhas' AS tabela,
  COUNT(*) AS linhas_afetadas
FROM public.campanhas c
JOIN mapa m ON m.id_campanha = c.id_campanha
WHERE c.nome_campanha = m.nome_atual
UNION ALL
SELECT
  'biota_analise_consolidada' AS tabela,
  COUNT(*) AS linhas_afetadas
FROM public.biota_analise_consolidada b
JOIN mapa m ON m.nome_atual = b.nome_campanha
WHERE b.codigo_interno_opyta = 'BRAAVG002' OR b.id_projeto = 9
UNION ALL
SELECT
  'fisico_analise_consolidada' AS tabela,
  COUNT(*) AS linhas_afetadas
FROM public.fisico_analise_consolidada f
JOIN mapa m ON m.nome_atual = f.nome_campanha
WHERE f.codigo_interno_opyta = 'BRAAVG002';

-- Aplicacao, se aprovada:
-- 1) criar backups de public.campanhas, public.biota_analise_consolidada para BRAAVG002
--    e public.fisico_analise_consolidada para BRAAVG002 quando houver linhas;
-- 2) atualizar campanhas por id_campanha;
-- 3) atualizar campos denormalizados nome_campanha nas tabelas consolidadas;
-- 4) reexecutar auditoria de totais e produtos dependentes.
"""


def write_outputs(output_dir: Path, crosswalk: pd.DataFrame, sql: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx = output_dir / "braavg002_campaign_crosswalk.xlsx"
    json_path = output_dir / "braavg002_campaign_crosswalk.json"
    md_path = output_dir / "braavg002_campaign_crosswalk.md"
    sql_path = output_dir / "braavg002_campaign_rename_dry_run.sql"
    cycle_summary = (
        crosswalk.groupby("ciclo_temporal", as_index=False)
        .agg(
            campanhas=("nome_campanha_atual", "nunique"),
            primeira=("nome_campanha_atual", "first"),
            ultima=("nome_campanha_atual", "last"),
            campanhas_padrao=("nome_campanha_padrao", lambda values: "; ".join(values)),
        )
        .sort_values("ciclo_temporal")
    )
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        crosswalk.to_excel(writer, sheet_name="crosswalk", index=False)
        cycle_summary.to_excel(writer, sheet_name="ciclos_temporais", index=False)
    sql_path.write_text(sql, encoding="utf-8")
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "campaigns": int(len(crosswalk)),
        "first_campaign": str(crosswalk.iloc[0]["nome_campanha_atual"]),
        "last_campaign": str(crosswalk.iloc[-1]["nome_campanha_atual"]),
        "season_rule": "CH = outubro a marco; SC = abril a setembro",
        "temporal_year_rule": "ano temporal = agosto a julho; meses ago-dez pertencem ao ano de inicio, jan-jul ao ano anterior",
        "temporal_cycles": cycle_summary.to_dict("records"),
        "recommended_strategy": "crosswalk_analitico_primeiro",
        "apply_to_database": "not_approved",
        "impact": {
            "campanhas_rows": int(len(crosswalk)),
            "biota_ictiofauna_rows": int(crosswalk["linhas_biota_ictiofauna"].sum()),
            "biota_zoobentos_rows": int(crosswalk["linhas_biota_zoobentos"].sum()),
            "fisico_rows": int(crosswalk["linhas_fisico"].sum()),
        },
        "outputs": {"xlsx": str(xlsx), "json": str(json_path), "markdown": str(md_path), "sql": str(sql_path)},
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    lines = [
        "# BRAAVG002 - Crosswalk de campanhas",
        "",
        f"- campanhas: {payload['campaigns']}",
        f"- regra sazonal: {payload['season_rule']}",
        f"- ano temporal: {payload['temporal_year_rule']}",
        f"- estrategia recomendada: `{payload['recommended_strategy']}`",
        f"- apply no banco: `{payload['apply_to_database']}`",
        "",
        "## Impacto Estimado Se Renomear No Banco",
        "",
        f"- `public.campanhas`: {payload['impact']['campanhas_rows']} linhas globais por `id_campanha`",
        f"- `public.biota_analise_consolidada` Ictiofauna: {payload['impact']['biota_ictiofauna_rows']} linhas",
        f"- `public.biota_analise_consolidada` Zoobentos: {payload['impact']['biota_zoobentos_rows']} linhas",
        f"- `public.fisico_analise_consolidada`: {payload['impact']['fisico_rows']} linhas",
        "",
        "## Primeiros Exemplos",
        "",
    ]
    for _, row in crosswalk.head(8).iterrows():
        lines.append(f"- `{row['nome_campanha_atual']}` -> `{row['nome_campanha_padrao']}`")
    lines.extend(["", "## Arquivos", "", f"- Excel: `{xlsx}`", f"- SQL dry-run: `{sql_path}`"])
    lines.extend(["", "## Ciclos Temporais", ""])
    for _, row in cycle_summary.iterrows():
        lines.append(f"- `{row['ciclo_temporal']}`: {int(row['campanhas'])} campanhas ({row['primeira']} a {row['ultima']})")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def run(output_dir: Path) -> dict[str, Any]:
    campaigns, biota_usage, fisico_usage = load_campaign_usage()
    crosswalk = build_crosswalk(campaigns, biota_usage, fisico_usage)
    sql = build_dry_run_sql(crosswalk)
    return write_outputs(output_dir, crosswalk, sql)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera crosswalk de campanhas AVG.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(args.output_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
