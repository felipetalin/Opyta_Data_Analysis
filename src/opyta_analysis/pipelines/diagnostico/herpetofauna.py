from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from opyta_analysis.supabase_client import get_client, paginate
from . import mastofauna as masto


TARGET_PCH_NAME = "Dores de Guanhães"
TARGET_CONTROL_NAME = "Área Controle"


def _infer_empreendimento_from_herpetofauna_point(point_name: object) -> str | None:
    point = masto._norm(point_name).upper()
    point = re.sub(r"[^A-Z0-9]+", "", point)
    if point.startswith(("CO", "CON")):
        return "Area Controle"
    if point.startswith(("DG", "DGN")):
        return "Dores de Guanhaes"
    if point.startswith(("FO", "FOR")):
        return "Fortuna II"
    if point.startswith(("JA", "JAC")):
        return "Jacare"
    if point.startswith(("SP", "SPT")):
        return "Senhora do Porto"
    return None


def _resolve_empreendimento_herpetofauna(point_name: object, id_empreendimento: object, emp_map: dict[object, str]) -> str:
    if id_empreendimento in emp_map:
        return emp_map[id_empreendimento]
    return _infer_empreendimento_from_herpetofauna_point(point_name) or "Sem empreendimento"


def _apply_campaign_filter(df: pd.DataFrame, campaign_filter: Optional[list[str]] = None) -> pd.DataFrame:
    if df.empty or not campaign_filter or "nome_campanha" not in df.columns:
        return df
    allowed = {str(c).strip() for c in campaign_filter if str(c).strip()}
    allowed_norm = {masto._norm(c) for c in allowed}
    campaign_text = df["nome_campanha"].astype(str).str.strip()
    campaign_norm = campaign_text.map(masto._norm)
    mask = campaign_text.isin(allowed) | campaign_norm.isin(allowed_norm)
    for item in allowed_norm:
        if item:
            mask = mask | campaign_norm.str.contains(item, regex=False)
    return df[mask].copy()


def _load_herpetofauna_df(project_id: int, env_file: Optional[str]) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    empreendimentos = paginate(sb, "empreendimentos", filters={"id_projeto": int(project_id)}, select="id_empreendimento,nome")
    emp_map = {e["id_empreendimento"]: e["nome"] for e in empreendimentos}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Herpetofauna"},
        select="id_esforco,id_ponto_coleta,metodo_de_captura,tipo_amostragem,tipo_de_amostragem,esforco,unidade_esforco",
    )
    esforcos = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos:
        return pd.DataFrame()

    esforco_map = {e["id_esforco"]: e for e in esforcos}
    esforco_ids = set(esforco_map.keys())

    resultados = paginate(
        sb,
        "resultados_herpetofauna",
        select="id_esforco,id_especie,numero_de_individuos,tipo_amostragem,observacoes",
    )
    resultados = [r for r in resultados if r.get("id_esforco") in esforco_ids]
    if not resultados:
        return pd.DataFrame()

    especies = paginate(
        sb,
        "especies",
        select="id_especie,nome_cientifico,nome_popular,ordem,familia,status_ameaca_global,status_ameaca_nacional,status_copam,cites,dependencia_florestal,endemismo,habito_alimentar,guilda_alimentar,sensibilidade_ambiental,migratorio,raridade,origem,distribuicao,cinegetica,xerimbabo,observacoes",
    )
    esp_map = {e["id_especie"]: e for e in especies}

    rows: list[dict[str, Any]] = []
    for r in resultados:
        esf = esforco_map.get(r.get("id_esforco"), {})
        ponto = pontos_map.get(esf.get("id_ponto_coleta"), {})
        esp = esp_map.get(r.get("id_especie"), {})
        id_emp = ponto.get("id_empreendimento")
        nome_ponto = ponto.get("nome_ponto")
        rows.append(
            {
                "nome_campanha": camp_map.get(ponto.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": nome_ponto,
                "empreendimento": _resolve_empreendimento_herpetofauna(nome_ponto, id_emp, emp_map),
                "nome_cientifico": esp.get("nome_cientifico"),
                "nome_popular": esp.get("nome_popular"),
                "ordem": esp.get("ordem"),
                "familia": esp.get("familia"),
                "status_ameaca_global": esp.get("status_ameaca_global"),
                "status_ameaca_nacional": esp.get("status_ameaca_nacional"),
                "status_copam": esp.get("status_copam"),
                "cites": esp.get("cites"),
                "dependencia_florestal": esp.get("dependencia_florestal"),
                "endemismo": esp.get("endemismo"),
                "habito_alimentar": esp.get("habito_alimentar"),
                "guilda_alimentar": esp.get("guilda_alimentar"),
                "sensibilidade_ambiental": esp.get("sensibilidade_ambiental"),
                "migratorio": esp.get("migratorio"),
                "raridade": esp.get("raridade"),
                "origem": esp.get("origem"),
                "distribuicao": esp.get("distribuicao"),
                "cinegetica_db": esp.get("cinegetica"),
                "xerimbabo_db": esp.get("xerimbabo"),
                "especie_obs": esp.get("observacoes"),
                "metodo_de_captura": esf.get("metodo_de_captura"),
                "tipo_amostragem": r.get("tipo_amostragem") or esf.get("tipo_amostragem") or esf.get("tipo_de_amostragem"),
                "id_esforco": esf.get("id_esforco"),
                "esforco": esf.get("esforco"),
                "unidade_esforco": esf.get("unidade_esforco"),
                "contagem": r.get("numero_de_individuos"),
                "obs_resultado": r.get("observacoes"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for c in ["nome_campanha", "nome_ponto", "empreendimento", "nome_cientifico", "nome_popular", "ordem", "familia"]:
        df[c] = df[c].astype(str).str.strip()
    df["id_esforco"] = pd.to_numeric(df["id_esforco"], errors="coerce").fillna(-1).astype(int)
    df["contagem"] = pd.to_numeric(df["contagem"], errors="coerce").fillna(0)
    df["esforco"] = pd.to_numeric(df["esforco"], errors="coerce")
    return df


def _load_sampling_units_df(project_id: int, env_file: Optional[str]) -> pd.DataFrame:
    sb = get_client(env_file)

    pontos = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,id_campanha,id_empreendimento",
    )
    if not pontos:
        return pd.DataFrame()

    ponto_ids = {p["id_ponto_coleta"] for p in pontos}
    pontos_map = {p["id_ponto_coleta"]: p for p in pontos}

    campanhas = paginate(sb, "campanhas", select="id_campanha,nome_campanha")
    camp_map = {c["id_campanha"]: c["nome_campanha"] for c in campanhas}

    empreendimentos = paginate(sb, "empreendimentos", filters={"id_projeto": int(project_id)}, select="id_empreendimento,nome")
    emp_map = {e["id_empreendimento"]: e["nome"] for e in empreendimentos}

    esforcos = paginate(
        sb,
        "esforcos_amostragem",
        filters={"grupo_biologico": "Herpetofauna"},
        select="id_esforco,id_ponto_coleta,esforco,unidade_esforco",
    )
    esforcos = [e for e in esforcos if e.get("id_ponto_coleta") in ponto_ids]
    if not esforcos:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for esf in esforcos:
        ponto = pontos_map.get(esf.get("id_ponto_coleta"), {})
        id_emp = ponto.get("id_empreendimento")
        nome_ponto = ponto.get("nome_ponto")
        rows.append(
            {
                "id_esforco": esf.get("id_esforco"),
                "nome_campanha": camp_map.get(ponto.get("id_campanha"), "Campanha desconhecida"),
                "nome_ponto": nome_ponto,
                "empreendimento": _resolve_empreendimento_herpetofauna(nome_ponto, id_emp, emp_map),
                "esforco": esf.get("esforco"),
                "unidade_esforco": esf.get("unidade_esforco"),
            }
        )

    df_units = pd.DataFrame(rows)
    if df_units.empty:
        return df_units

    for c in ["nome_campanha", "nome_ponto", "empreendimento"]:
        df_units[c] = df_units[c].astype(str).str.strip()
    df_units["id_esforco"] = pd.to_numeric(df_units["id_esforco"], errors="coerce").fillna(-1).astype(int)
    df_units["esforco"] = pd.to_numeric(df_units["esforco"], errors="coerce")
    return df_units


def _save_descriptive_report(details: dict[str, Any], output_dir: Path, generated_files: list[str]) -> None:
    text_lines = [
        "Relatorio descritivo - Herpetofauna",
        "",
        f"Area de estudo analisada: {TARGET_PCH_NAME}",
        f"Area Controle analisada: {TARGET_CONTROL_NAME}",
        f"Registros utilizados: {details.get('rows_loaded', 0)}",
        f"Especies totais: {details.get('species_total', 0)}",
        "",
        "6.1 Riqueza, composicao e abundancia:",
        "- Tabelas de especies por area geradas em excel.",
        "- Figuras de abundancia total e relativa geradas para area de estudo e controle.",
        "",
        "6.2 Suficiencia amostral:",
        "- Estimadores (Sobs, Jackknife 1, Bootstrap) calculados para area de estudo e controle.",
        "- Curvas do coletor geradas para as duas areas.",
        "",
        "6.3 Indices de diversidade:",
        "- Shannon, Pielou e Simpson calculados em excel e figura comparativa.",
        "",
        "6.4 Similaridade:",
        "- Indice de Jaccard calculado entre area de estudo e controle.",
        "- Dendrogramas de similaridade gerados.",
        "",
        "6.5 Diagrama de Venn:",
        "- Sobreposicao de especies entre area de estudo e controle gerada.",
        "",
        "6.6-6.8 Tabela geral:",
        "- Consolidacao de ameacadas/endemicas/raras/exoticas/cinegeticas/xerimbabo gerada.",
    ]
    out_txt = output_dir / "6_relatorio_descritivo_herpetofauna.txt"
    out_txt.write_text("\n".join(text_lines), encoding="utf-8")
    generated_files.append(str(out_txt))


def run_herpetofauna_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
    campaign_filter: Optional[list[str]] = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Reaproveita o motor visual da mastofauna com labels de herpetofauna.
    masto.TARGET_PCH_NAME = TARGET_PCH_NAME
    masto.TARGET_CONTROL_NAME = TARGET_CONTROL_NAME

    df = _load_herpetofauna_df(project_id=project_id, env_file=env_file)
    df = _apply_campaign_filter(df, campaign_filter)
    if df.empty:
        return {
            "rows_loaded": 0,
            "executed_blocks": [],
            "generated_files": [],
            "warning": "Sem dados de herpetofauna para o projeto informado.",
        }

    block_sel = str(block).strip().lower()
    generated_files: list[str] = []
    executed_blocks: list[str] = []

    df_pch = masto._subset_by_empreendimento(df, TARGET_PCH_NAME)
    df_control = masto._subset_by_empreendimento(df, TARGET_CONTROL_NAME)
    df_report = pd.concat([df_pch, df_control], ignore_index=True)

    details: dict[str, Any] = {
        "rows_loaded": int(len(df)),
        "species_total": int(df["nome_cientifico"].nunique()),
        "pch_rows": int(len(df_pch)),
        "control_rows": int(len(df_control)),
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()),
    }

    if block_sel in {"6.1", "61", "all"}:
        tab_pch = masto._build_species_list(df_pch)
        tab_ctrl = masto._build_species_list(df_control)
        pch_slug = masto._area_slug(TARGET_PCH_NAME)
        ctrl_slug = masto._area_slug(TARGET_CONTROL_NAME)

        out_pch = output_dir / f"6_1_tabela_especies_{pch_slug}.xlsx"
        out_ctrl = output_dir / f"6_1_tabela_especies_{ctrl_slug}.xlsx"
        tab_pch.to_excel(out_pch, index=False, engine="openpyxl")
        tab_ctrl.to_excel(out_ctrl, index=False, engine="openpyxl")
        generated_files.extend([str(out_pch), str(out_ctrl)])

        out_fig_pch = output_dir / f"6_1_figura_abundancia_total_relativa_herpetofauna_{pch_slug}.png"
        out_fig_ctrl = output_dir / f"6_1_figura_abundancia_herpetofauna_{ctrl_slug}.png"

        metrics_pch = masto._save_abundance_figures(df_area=df_pch, theme=theme, output_png=out_fig_pch)
        masto._save_abundance_figures(df_area=df_control, theme=theme, output_png=out_fig_ctrl)
        generated_files.extend([str(out_fig_pch), str(out_fig_ctrl)])

        details["block_6_1"] = metrics_pch
        executed_blocks.append("6.1")

    if block_sel in {"6.2", "62", "all"}:
        df_units = _load_sampling_units_df(project_id=project_id, env_file=env_file)
        df_units = _apply_campaign_filter(df_units, campaign_filter)
        df_units_pch = masto._subset_by_empreendimento(df_units, TARGET_PCH_NAME) if not df_units.empty else pd.DataFrame()
        df_units_ctrl = masto._subset_by_empreendimento(df_units, TARGET_CONTROL_NAME) if not df_units.empty else pd.DataFrame()

        est_pch = masto._save_estimators_and_curve(
            df_pch,
            masto._area_slug(TARGET_PCH_NAME),
            theme,
            output_dir,
            generated_files,
            sampling_units_df=df_units_pch,
        )
        est_ctrl = masto._save_estimators_and_curve(
            df_control,
            masto._area_slug(TARGET_CONTROL_NAME),
            theme,
            output_dir,
            generated_files,
            sampling_units_df=df_units_ctrl,
        )
        details["block_6_2"] = {"estudo": est_pch, "controle": est_ctrl}
        executed_blocks.append("6.2")

    if block_sel in {"6.3", "63", "all"}:
        masto._save_diversity(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.3")

    if block_sel in {"6.4", "64", "all"}:
        masto._save_similarity_and_venn(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.4")
        if block_sel in {"all"}:
            executed_blocks.append("6.5")

    if block_sel in {"6.5", "65"}:
        masto._save_similarity_and_venn(df_pch, df_control, theme, output_dir, generated_files)
        executed_blocks.append("6.5")

    if block_sel in {"6.6", "66", "6.7", "67", "6.8", "68", "all"}:
        masto._save_general_status_tables(df_report, output_dir, generated_files)
        executed_blocks.extend(["6.6", "6.7", "6.8"])

    if block_sel in {"all"}:
        _save_descriptive_report(details, output_dir, generated_files)

    if not executed_blocks:
        raise ValueError(
            "Unsupported block for herpetofauna pipeline. "
            "Use '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '6.8' or 'all'."
        )

    details["executed_blocks"] = sorted(set(executed_blocks), key=lambda x: float(x))
    details["generated_files"] = generated_files
    return details
