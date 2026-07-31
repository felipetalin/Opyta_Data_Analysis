from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str((Path.cwd().parent / "Opyta_Data").resolve()))
from core.engine import get_engine  # noqa: E402


PROJECT_ID = 195
PROJECT_CODE = "BRAAEG001"
GROUP_LIKE = "Zoopl%"

FIXES = {
    "Ceriodaphinia sp.": {
        "nome_cientifico": "Ceriodaphnia sp.",
        "genero": "Ceriodaphnia",
        "observacao": "R01 BRAAEG001 Zooplâncton: correção ortográfica do gênero Ceriodaphnia.",
    },
    "Cyphoderia ampula": {
        "nome_cientifico": "Cyphoderia ampulla",
        "observacao": "R01 BRAAEG001 Zooplâncton: correção ortográfica do epíteto específico ampulla.",
    },
    "Trichocerca pussila": {
        "nome_cientifico": "Trichocerca pusilla",
        "observacao": "R01 BRAAEG001 Zooplâncton: correção ortográfica do epíteto específico pusilla.",
    },
    "Difflugia lithophila": {
        "nome_cientifico": "Difflugia litophila",
        "observacao": "R01 BRAAEG001 ZooplÃ¢ncton: correÃ§Ã£o ortogrÃ¡fica para Difflugia litophila.",
    },
    "Lecane arculla": {
        "nome_cientifico": "Lecane arcula",
        "observacao": "R01 BRAAEG001 ZooplÃ¢ncton: correÃ§Ã£o ortogrÃ¡fica para Lecane arcula; forma arculla tratada como erro de digitaÃ§Ã£o.",
    },
    "Bosmina freyi": {
        "familia": "Bosminidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família padronizada como Bosminidae.",
    },
    "Alona sp.": {
        "familia": "Chydoridae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família corrigida para Chydoridae.",
    },
    "Diaphanosoma birgei": {
        "familia": "Sididae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família padronizada como Sididae.",
    },
    "Diaphanosoma brevireme": {
        "familia": "Sididae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família padronizada como Sididae.",
    },
    "Thermocyclops minutus": {
        "familia": "Cyclopidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família padronizada como Cyclopidae.",
    },
    "Polyarthra sp.": {
        "familia": "Synchaetidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família corrigida para Synchaetidae.",
    },
    "Synchaeta sp.": {
        "familia": "Synchaetidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família corrigida para Synchaetidae.",
    },
    "Lesquereusia modesta": {
        "familia": "Lesquereusiidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família corrigida para Lesquereusiidae.",
    },
    "Phryganella hemisphaerica": {
        "familia": "Phryganellidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: família corrigida para Phryganellidae.",
    },
    "Conochilus natans": {
        "ordem": "Flosculariida",
        "familia": "Conochilidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: ordem corrigida para Flosculariida; Conochilidae mantida como família.",
    },
    "Conochilus coenobasis": {
        "ordem": "Flosculariida",
        "familia": "Conochilidae",
        "observacao": "R01 BRAAEG001 Zooplâncton: ordem corrigida para Flosculariida; Conochilidae mantida como família.",
    },
    "Bdelloida": {
        "ordem": "Bdelloida",
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: ordem atualizada para Bdelloida; família/gênero não aplicáveis.",
    },
    "CALANOIDA (nauplius)": {
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: estágio larval de Copepoda sem atribuição segura de família/gênero.",
    },
    "CYCLOPOIDA (nauplius)": {
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: estágio larval de Copepoda sem atribuição segura de família/gênero.",
    },
    "CALANOIDA (copepodito)": {
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: copepodito identificado em nível ordinal, sem atribuição segura de família/gênero.",
    },
    "CYCLOPOIDA (copepodito)": {
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: copepodito identificado em nível ordinal, sem atribuição segura de família/gênero.",
    },
    "HARPACTICOIDA (copepodito)": {
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: copepodito identificado em nível ordinal, sem atribuição segura de família/gênero.",
    },
    "Ciliado NI": {
        "nome_cientifico": "Ciliophora",
        "filo": "Ciliophora",
        "classe": "N.A.",
        "ordem": "N.A.",
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: classificação incompatível com Arcella removida; tratado no nível de filo Ciliophora.",
    },
    "Ciliophora NI": {
        "nome_cientifico": "Ciliophora",
        "filo": "Ciliophora",
        "classe": "N.A.",
        "ordem": "N.A.",
        "familia": "N.A.",
        "genero": "N.A.",
        "observacao": "R01 BRAAEG001 Zooplâncton: N.I. removido; táxon tratado no nível de filo Ciliophora.",
    },
}


def output_path(output_dir: Path, stem: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{datetime.now().strftime('%Y%m%dT%H%M%S')}_{stem}.xlsx"


def fetch_species(conn) -> pd.DataFrame:
    names = sorted(set(FIXES) | {fix["nome_cientifico"] for fix in FIXES.values() if "nome_cientifico" in fix})
    return pd.read_sql(
        text(
            """
            select distinct e.id_especie, e.nome_cientifico, e.grupo_biologico, e.reino,
                   e.filo, e.classe, e.ordem, e.familia, e.genero, e.observacoes
            from public.resultados_zooplancton r
            join public.especies e on e.id_especie = r.id_especie
            join public.esforcos_amostragem a on a.id_esforco = r.id_esforco
            join public.pontos_coleta p on p.id_ponto_coleta = a.id_ponto_coleta
            where p.id_projeto = :project_id
              and a.grupo_biologico like :group_like
              and e.nome_cientifico = any(:names)
            order by e.nome_cientifico
            """
        ),
        conn,
        params={"project_id": PROJECT_ID, "group_like": GROUP_LIKE, "names": names},
    )


def fetch_consolidated(conn) -> pd.DataFrame:
    return pd.read_sql(
        text(
            """
            select nome_campanha, nome_ponto, grupo_biologico, nome_cientifico,
                   contagem, filo, classe, ordem, familia, genero, tipo_amostragem
            from public.biota_analise_consolidada
            where id_projeto = :project_id and grupo_biologico like :group_like
            order by nome_campanha, nome_ponto, nome_cientifico
            """
        ),
        conn,
        params={"project_id": PROJECT_ID, "group_like": GROUP_LIKE},
    )


def build_changes(before: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in before.iterrows():
        fix = FIXES.get(row["nome_cientifico"], {})
        after = row.to_dict()
        for col in ["nome_cientifico", "filo", "classe", "ordem", "familia", "genero"]:
            if col in fix:
                after[col] = fix[col]
        obs = str(row.get("observacoes") or "").strip()
        note = fix.get("observacao")
        if note and note not in obs:
            after["observacoes"] = f"{obs} | {note}".strip(" |")
        for col in ["nome_cientifico", "filo", "classe", "ordem", "familia", "genero", "observacoes"]:
            if str(row.get(col)) != str(after.get(col)):
                rows.append(
                    {
                        "id_especie": row["id_especie"],
                        "taxon_original": row["nome_cientifico"],
                        "campo": col,
                        "antes": row.get(col),
                        "depois": after.get(col),
                    }
                )
    return pd.DataFrame(rows)


def backup_tables(conn, stamp: str) -> list[str]:
    backup_species = f"bk_sp_zoo_braaeg001_r01_{stamp}"
    backup_consolidated = f"bk_biota_zoo_braaeg001_r01_{stamp}"
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{backup_species} AS
            SELECT e.*
            FROM public.especies e
            WHERE e.id_especie IN (
                SELECT DISTINCT r.id_especie
                FROM public.resultados_zooplancton r
                JOIN public.esforcos_amostragem a ON a.id_esforco = r.id_esforco
                JOIN public.pontos_coleta p ON p.id_ponto_coleta = a.id_ponto_coleta
                WHERE p.id_projeto = :project_id AND a.grupo_biologico LIKE :group_like
            )
            """
        ),
        {"project_id": PROJECT_ID, "group_like": GROUP_LIKE},
    )
    conn.execute(
        text(
            f"""
            CREATE TABLE public.{backup_consolidated} AS
            SELECT *
            FROM public.biota_analise_consolidada
            WHERE id_projeto = :project_id AND grupo_biologico LIKE :group_like
            """
        ),
        {"project_id": PROJECT_ID, "group_like": GROUP_LIKE},
    )
    return [f"public.{backup_species}", f"public.{backup_consolidated}"]


def apply_species_fixes(conn) -> None:
    for original, fix in FIXES.items():
        target_name = fix.get("nome_cientifico")
        target_id = None
        if target_name:
            target_id = conn.execute(
                text(
                    """
                    SELECT id_especie
                    FROM public.especies
                    WHERE nome_cientifico = :target_name
                      AND nome_cientifico <> :original
                    ORDER BY id_especie
                    LIMIT 1
                    """
                ),
                {"target_name": target_name, "original": original},
            ).scalar()
        if target_id is not None:
            conn.execute(
                text(
                    """
                    UPDATE public.resultados_zooplancton r
                    SET id_especie = :target_id
                    FROM public.especies e, public.esforcos_amostragem a, public.pontos_coleta p
                    WHERE r.id_especie = e.id_especie
                      AND r.id_esforco = a.id_esforco
                      AND a.id_ponto_coleta = p.id_ponto_coleta
                      AND e.nome_cientifico = :original
                      AND p.id_projeto = :project_id
                      AND a.grupo_biologico LIKE :group_like
                    """
                ),
                {
                    "target_id": target_id,
                    "original": original,
                    "project_id": PROJECT_ID,
                    "group_like": GROUP_LIKE,
                },
            )
            if "observacao" in fix:
                conn.execute(
                    text(
                        """
                        UPDATE public.especies
                        SET observacoes = CASE
                            WHEN observacoes IS NULL OR observacoes = '' THEN :observacao
                            WHEN position(:observacao in observacoes) > 0 THEN observacoes
                            ELSE observacoes || ' | ' || :observacao
                        END
                        WHERE id_especie = :target_id
                        """
                    ),
                    {"target_id": target_id, "observacao": fix["observacao"]},
                )
            continue

        sets = []
        params = {"original": original}
        for col in ["nome_cientifico", "filo", "classe", "ordem", "familia", "genero"]:
            if col in fix:
                sets.append(f"{col} = :{col}")
                params[col] = fix[col]
        if "observacao" in fix:
            sets.append(
                "observacoes = CASE WHEN observacoes IS NULL OR observacoes = '' THEN :observacao "
                "WHEN position(:observacao in observacoes) > 0 THEN observacoes "
                "ELSE observacoes || ' | ' || :observacao END"
            )
            params["observacao"] = fix["observacao"]
        if not sets:
            continue
        conn.execute(
            text(
                f"""
                UPDATE public.especies
                SET {", ".join(sets)}
                WHERE nome_cientifico = :original
                  AND id_especie IN (
                    SELECT DISTINCT r.id_especie
                    FROM public.resultados_zooplancton r
                    JOIN public.esforcos_amostragem a ON a.id_esforco = r.id_esforco
                    JOIN public.pontos_coleta p ON p.id_ponto_coleta = a.id_ponto_coleta
                    WHERE p.id_projeto = :project_id AND a.grupo_biologico LIKE :group_like
                  )
                """
            ),
            {**params, "project_id": PROJECT_ID, "group_like": GROUP_LIKE},
        )


def rebuild_consolidated(conn) -> int:
    conn.execute(
        text(
            """
            DELETE FROM public.biota_analise_consolidada
            WHERE id_projeto = :project_id AND grupo_biologico LIKE :group_like
            """
        ),
        {"project_id": PROJECT_ID, "group_like": GROUP_LIKE},
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
                cli.nome_empresa, pr.nome_projeto, NULL::text, c.nome_campanha, p.nome_ponto,
                p.latitude, p.longitude, a.grupo_biologico, sp.nome_cientifico,
                rz.numero_de_individuos::numeric, NULL::numeric, sp.bmwp_score,
                pr.codigo_interno_opyta, p.data_hora_coleta, p.bacia_hidrografica,
                a.metodo_de_captura, a.esforco, a.unidade_esforco,
                sp.nome_popular, sp.reino, sp.filo, sp.classe, sp.ordem, sp.familia,
                sp.genero, sp.origem, NULL::numeric, NULL::numeric,
                COALESCE(rz.tipo_amostragem, a.tipo_amostragem, a.tipo_de_amostragem),
                p.id_empreendimento, emp.nome, pr.id_projeto
            FROM public.resultados_zooplancton rz
            JOIN public.esforcos_amostragem a ON a.id_esforco = rz.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = a.id_ponto_coleta
            JOIN public.campanhas c ON c.id_campanha = p.id_campanha
            JOIN public.projetos pr ON pr.id_projeto = p.id_projeto
            JOIN public.clientes cli ON cli.id_cliente = pr.id_cliente
            JOIN public.especies sp ON sp.id_especie = rz.id_especie
            LEFT JOIN public.empreendimentos emp ON emp.id_empreendimento = p.id_empreendimento
            WHERE p.id_projeto = :project_id
              AND pr.codigo_interno_opyta = :project_code
              AND a.grupo_biologico LIKE :group_like
            """
        ),
        {"project_id": PROJECT_ID, "project_code": PROJECT_CODE, "group_like": GROUP_LIKE},
    )
    return int(result.rowcount or 0)


def write_audit(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/Planilha/Zoo"))
    args = parser.parse_args()

    engine = get_engine()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S").lower()
    audit_path = output_path(args.output_dir, "fix_taxonomia_zooplancton_r01_braaeg001")

    with engine.begin() as conn:
        before_species = fetch_species(conn)
        before_consolidated = fetch_consolidated(conn)
        planned_changes = build_changes(before_species)
        backups = []
        consolidated_rows = 0
        if args.apply:
            backups = backup_tables(conn, stamp)
            apply_species_fixes(conn)
            consolidated_rows = rebuild_consolidated(conn)
        after_species = fetch_species(conn)
        after_consolidated = fetch_consolidated(conn)

    summary = pd.DataFrame(
        [
            {"item": "modo", "valor": "apply" if args.apply else "dry_run"},
            {"item": "taxons_alvo_encontrados", "valor": int(before_species["nome_cientifico"].nunique()) if not before_species.empty else 0},
            {"item": "mudancas_planejadas", "valor": int(len(planned_changes))},
            {"item": "linhas_consolidadas_antes", "valor": int(len(before_consolidated))},
            {"item": "linhas_consolidadas_recriadas", "valor": int(consolidated_rows)},
            {"item": "linhas_consolidadas_depois", "valor": int(len(after_consolidated))},
            {"item": "backups", "valor": "; ".join(backups)},
        ]
    )
    write_audit(
        audit_path,
        {
            "00_resumo": summary,
            "01_mudancas_planejadas": planned_changes,
            "02_especies_antes": before_species,
            "03_especies_depois": after_species,
            "04_consolidado_antes": before_consolidated,
            "05_consolidado_depois": after_consolidated,
        },
    )
    print({"audit": str(audit_path), "mode": "apply" if args.apply else "dry_run", "consolidated_rows": consolidated_rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
