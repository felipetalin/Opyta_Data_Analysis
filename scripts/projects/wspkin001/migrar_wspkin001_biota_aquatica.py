from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text


PROJECT_CODE = "WSPKIN001"
PROJECT_ID = 211
PROJECT_SLUG = "wspkin001"
OUTPUT_LOG_DIR = Path("outputs/_project_scripts/WSPKIN001__kinross_bandeirinhas/migration_logs")

OFFICIAL_COORDS = {
    "PT_01": (-17.11137946, -46.95024449),
    "PT_02": (-17.14039444, -47.01674724),
    "PT_03": (-17.13333091, -46.94114619),
    "PT_04": (-17.11435337, -46.90079376),
    "PT_05": (-17.10317134, -46.84686704),
    "PT_06": (-17.13558594, -46.91847559),
    "PT_07": (-17.11943072, -46.90675106),
    "PT_08": (-17.12257486, -46.94465538),
    "PT_09": (-17.11897500, -46.82032600),
    "PT_10": (-17.13065849, -46.88515517),
}

ACCEPTED_NAMES = {
    "Stephanocyclus meneghinianus": "Cyclotella meneghiniana",
    "Brachionus patulus": "Platyias patulus",
    "Collurella minima": "Colurella minima",
    "Difflugia kempny": "Difflugia kempnyi",
}


ALL_GROUPS = {
    "Resultados_Fitoplancton": {
        "canonical": "Fitoplâncton",
        "short": "Fitoplancton",
        "table": "resultados_fitoplancton",
    },
    "Resultados_Zooplancton": {
        "canonical": "Zooplâncton",
        "short": "Zooplancton",
        "table": "resultados_zooplancton",
    },
    "Resultados_Zoobentos": {
        "canonical": "Zoobentos",
        "short": "Zoobentos",
        "table": "resultados_zoobentos",
    },
    "Resultados_Ictiofauna": {
        "canonical": "Ictiofauna",
        "short": "Ictiofauna",
        "table": "resultados_ictiofauna",
    },
}

GROUPS = dict(ALL_GROUPS)
RESULT_TABLES = [info["table"] for info in GROUPS.values()]


GROUP_ALIASES = {
    "fitoplancton": "Resultados_Fitoplancton",
    "fito": "Resultados_Fitoplancton",
    "zooplancton": "Resultados_Zooplancton",
    "zoo": "Resultados_Zooplancton",
    "zoobentos": "Resultados_Zoobentos",
    "bentos": "Resultados_Zoobentos",
    "ictiofauna": "Resultados_Ictiofauna",
    "ictio": "Resultados_Ictiofauna",
}


def configure_groups(selected_groups: list[str] | None) -> list[str]:
    global GROUPS, RESULT_TABLES
    if not selected_groups:
        GROUPS = dict(ALL_GROUPS)
        RESULT_TABLES = [info["table"] for info in GROUPS.values()]
        return [info["canonical"] for info in GROUPS.values()]

    selected_sheets: list[str] = []
    for raw_group in selected_groups:
        for part in str(raw_group).split(","):
            key = norm_key(part).replace(" ", "_")
            sheet = GROUP_ALIASES.get(key)
            if sheet is None:
                sheet = next(
                    (
                        candidate
                        for candidate, info in ALL_GROUPS.items()
                        if key
                        in {
                            norm_key(candidate).replace(" ", "_"),
                            norm_key(info["canonical"]).replace(" ", "_"),
                            norm_key(info["short"]).replace(" ", "_"),
                        }
                    ),
                    None,
                )
            if sheet is None:
                valid = sorted(set(GROUP_ALIASES) | set(ALL_GROUPS))
                raise RuntimeError(f"Grupo desconhecido '{part}'. Opcoes validas: {valid}")
            if sheet not in selected_sheets:
                selected_sheets.append(sheet)

    GROUPS = {sheet: ALL_GROUPS[sheet] for sheet in selected_sheets}
    RESULT_TABLES = [info["table"] for info in GROUPS.values()]
    return [info["canonical"] for info in GROUPS.values()]


def active_group_names() -> list[str]:
    return [info["canonical"] for info in GROUPS.values()]


@dataclass
class WorkbookData:
    group: str
    short: str
    path: Path
    result_sheet: str
    capa: pd.DataFrame
    pontos: pd.DataFrame
    esforco: pd.DataFrame
    resultados: pd.DataFrame


def is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text_value = str(value).replace("\xa0", " ").strip()
    return text_value == "" or text_value.lower() in {"nan", "none", "na", "n.a.", "n.a", "n.a"}


def clean_text(value: object) -> str | None:
    if is_blank(value):
        return None
    text_value = str(value).replace("\xa0", " ").strip()
    if text_value in {"N.A.", "NA", "NaN"}:
        return None
    return re.sub(r"\s+", " ", text_value)


def norm_key(value: object) -> str:
    if is_blank(value):
        return ""
    text_value = str(value).replace("\xa0", " ")
    text_value = unicodedata.normalize("NFKD", text_value)
    text_value = "".join(ch for ch in text_value if not unicodedata.combining(ch))
    text_value = text_value.lower()
    return re.sub(r"\s+", " ", text_value).strip()


def to_float(value: object) -> float | None:
    if is_blank(value):
        return None
    text_value = str(value).replace(",", ".").strip()
    if text_value.lower() in {"x", "presente", "sim"}:
        return 1.0
    match = re.search(r"-?\d+(?:\.\d+)?", text_value)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def to_int(value: object) -> int | None:
    numeric = to_float(value)
    if numeric is None:
        return None
    return int(round(numeric))


def numeric_or_zero(value: object) -> float:
    numeric = to_float(value)
    return 0.0 if numeric is None else numeric


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def load_workbooks(input_dir: Path, input_files: list[Path] | None = None) -> list[WorkbookData]:
    workbooks: list[WorkbookData] = []
    paths = input_files if input_files else sorted(input_dir.glob("*.xlsx"))
    for path in paths:
        if path.name.startswith("~$") or path.name.startswith("2026") or "__backup_" in path.name:
            continue
        xls = pd.ExcelFile(path)
        result_sheet = next((sheet for sheet in xls.sheet_names if sheet in GROUPS), None)
        if result_sheet is None:
            continue
        info = GROUPS[result_sheet]
        workbooks.append(
            WorkbookData(
                group=info["canonical"],
                short=info["short"],
                path=path,
                result_sheet=result_sheet,
                capa=pd.read_excel(xls, "Capa_Projeto", dtype=object).dropna(how="all"),
                pontos=pd.read_excel(xls, "Pontos_e_Campanhas", dtype=object).dropna(how="all"),
                esforco=pd.read_excel(xls, "Metadados_Esforco", dtype=object).dropna(how="all"),
                resultados=pd.read_excel(xls, result_sheet, dtype=object).dropna(how="all"),
            )
        )
        results = workbooks[-1].resultados
        explicit_types = results["Tipo_de_Amostragem"].map(clean_text)
        explicit_valid = explicit_types.map(norm_key).isin({"qualitativa", "quantitativa"})
        explicit_counts = explicit_types[explicit_valid].map(lambda value: "Qualitativa" if norm_key(value) == "qualitativa" else "Quantitativa").value_counts().to_dict()
        points = workbooks[-1].pontos
        for point_name, (latitude, longitude) in OFFICIAL_COORDS.items():
            mask = points["Ponto"].astype(str).str.strip().eq(point_name)
            points.loc[mask, "Latitude"] = latitude
            points.loc[mask, "Longitude"] = longitude
        results["Nome_Cientifico"] = results["Nome_Cientifico"].map(lambda value: ACCEPTED_NAMES.get(" ".join(str(value).split()), " ".join(str(value).split())))
        def sampling_type(row: pd.Series) -> str:
            explicit = clean_text(row.get("Tipo_de_Amostragem"))
            if explicit and norm_key(explicit) in {"qualitativa", "quantitativa"}:
                return "Qualitativa" if norm_key(explicit) == "qualitativa" else "Quantitativa"
            return "Qualitativa" if str(row.get("Numero_de_Individuos", "")).strip().upper() == "X" else "Quantitativa"

        results["Tipo_de_Amostragem"] = results.apply(sampling_type, axis=1)
        normalized_counts = results.loc[explicit_valid, "Tipo_de_Amostragem"].value_counts().to_dict()
        if explicit_counts != normalized_counts:
            raise RuntimeError(
                f"{path.name}: tipos de amostragem explícitos foram alterados: fonte={explicit_counts}, normalizado={normalized_counts}"
            )
    found = {wb.group for wb in workbooks}
    missing = {info["canonical"] for info in GROUPS.values()} - found
    if missing:
        raise RuntimeError(f"Planilhas ausentes para grupos: {sorted(missing)}")
    return workbooks


def check_project_codes(workbooks: list[WorkbookData]) -> None:
    for wb in workbooks:
        code = clean_text(wb.capa.iloc[0].get("Codigo_Opyta")) if not wb.capa.empty else None
        if code != PROJECT_CODE:
            raise RuntimeError(f"{wb.path.name}: Codigo_Opyta esperado {PROJECT_CODE}, encontrado {code}")


def connect_engine(opyta_data_root: Path):
    sys.path.insert(0, str(opyta_data_root))
    from core.engine import get_engine  # noqa: PLC0415

    return get_engine()


def ensure_project(conn) -> dict[str, Any]:
    row = conn.execute(
        text(
            """
            SELECT p.id_projeto, p.codigo_interno_opyta, p.nome_projeto, p.id_cliente, c.nome_empresa
            FROM public.projetos p
            JOIN public.clientes c ON c.id_cliente = p.id_cliente
            WHERE p.codigo_interno_opyta = :code
            """
        ),
        {"code": PROJECT_CODE},
    ).mappings().one_or_none()
    if row is None:
        raise RuntimeError(f"Projeto {PROJECT_CODE} nao encontrado.")
    if int(row["id_projeto"]) != PROJECT_ID:
        raise RuntimeError(f"id_projeto esperado {PROJECT_ID}, encontrado {row['id_projeto']}.")
    return dict(row)


def collect_campaigns(workbooks: list[WorkbookData]) -> list[str]:
    campaigns: set[str] = set()
    for wb in workbooks:
        for df in (wb.pontos, wb.esforco, wb.resultados):
            if "Campanha" in df.columns:
                campaigns.update(str(v).strip() for v in df["Campanha"].dropna().tolist() if str(v).strip())
    return sorted(campaigns)


def ensure_campaigns(conn, campaigns: list[str], apply: bool) -> dict[str, int | None]:
    if apply:
        conn.execute(
            text(
                """
                INSERT INTO public.campanhas (nome_campanha)
                VALUES (:nome)
                ON CONFLICT (nome_campanha) DO NOTHING
                """
            ),
            [{"nome": name} for name in campaigns],
        )
    rows = conn.execute(
        text(
            """
            SELECT id_campanha, nome_campanha
            FROM public.campanhas
            WHERE nome_campanha = ANY(:campaigns)
            """
        ),
        {"campaigns": campaigns},
    ).mappings().all()
    mapping = {row["nome_campanha"]: int(row["id_campanha"]) for row in rows}
    if apply:
        missing = sorted(set(campaigns) - set(mapping))
        if missing:
            raise RuntimeError(f"Campanhas nao resolvidas apos insert: {missing}")
    return {name: mapping.get(name) for name in campaigns}


def collect_points(workbooks: list[WorkbookData], campaign_ids: dict[str, int | None]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    for wb in workbooks:
        for idx, row in wb.pontos.iterrows():
            campaign = clean_text(row.get("Campanha"))
            point = clean_text(row.get("Ponto"))
            if not campaign or not point:
                continue
            rec = {
                "id_projeto": PROJECT_ID,
                "id_campanha": campaign_ids.get(campaign),
                "campanha": campaign,
                "nome_ponto": point,
                "data_hora_coleta": pd.to_datetime(row.get("Data"), errors="coerce"),
                "latitude": to_float(row.get("Latitude")),
                "longitude": to_float(row.get("Longitude")),
                "bacia_hidrografica": clean_text(row.get("Bacia_Hidrografica")),
                "curso_d_agua": clean_text(row.get("Curso_d_Agua")),
                "municipio": clean_text(row.get("Municipio")),
                "observacoes": clean_text(row.get("Observacoes_Coleta")),
                "grupo_origem": wb.group,
                "linha_excel": idx + 2,
            }
            if pd.isna(rec["data_hora_coleta"]):
                rec["data_hora_coleta"] = None
            else:
                rec["data_hora_coleta"] = rec["data_hora_coleta"].to_pydatetime()
            key = (campaign, point)
            existing = by_key.get(key)
            if existing is not None:
                compare_cols = ["latitude", "longitude", "bacia_hidrografica", "curso_d_agua", "municipio"]
                changed = [col for col in compare_cols if norm_key(existing.get(col)) != norm_key(rec.get(col))]
                if changed:
                    conflicts.append({"campanha": campaign, "ponto": point, "campos": ", ".join(changed), "grupo": wb.group})
                continue
            by_key[key] = rec
    if conflicts:
        raise RuntimeError(f"Conflitos entre pontos da biota: {conflicts[:10]}")
    return list(by_key.values()), conflicts


def fetch_point_map(conn) -> dict[tuple[int, str], int]:
    rows = conn.execute(
        text(
            """
            SELECT id_ponto_coleta, id_campanha, nome_ponto
            FROM public.pontos_coleta
            WHERE id_projeto = :id_projeto
            """
        ),
        {"id_projeto": PROJECT_ID},
    ).mappings().all()
    return {(int(row["id_campanha"]), str(row["nome_ponto"]).strip()): int(row["id_ponto_coleta"]) for row in rows}


def collect_efforts(
    workbooks: list[WorkbookData],
    campaign_ids: dict[str, int | None],
    point_ids: dict[tuple[int, str], int] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    raw_rows: list[dict[str, Any]] = []
    for wb in workbooks:
        for _, row in wb.esforco.iterrows():
            campaign = clean_text(row.get("Campanha"))
            point = clean_text(row.get("Ponto"))
            method = clean_text(row.get("Metodo_de_Captura"))
            if not campaign or not point or not method:
                continue
            group = wb.group
            key = (campaign, point, group, method)
            rec = grouped.setdefault(
                key,
                {
                    "campanha": campaign,
                    "id_campanha": campaign_ids.get(campaign),
                    "nome_ponto": point,
                    "id_ponto_coleta": None,
                    "grupo_biologico": group,
                    "metodo_de_captura": method,
                    "tipo_values": set(),
                    "esforco_values": [],
                    "unidade_values": [],
                },
            )
            rec["tipo_values"].add(clean_text(row.get("Tipo_de_Amostragem")))
            rec["esforco_values"].append(to_float(row.get("Esforco")))
            rec["unidade_values"].append(clean_text(row.get("Unidade_Esforco")))
            raw_rows.append(
                {
                    "campanha": campaign,
                    "ponto": point,
                    "grupo": group,
                    "metodo": method,
                    "tipo": clean_text(row.get("Tipo_de_Amostragem")),
                    "esforco": row.get("Esforco"),
                    "unidade": clean_text(row.get("Unidade_Esforco")),
                }
            )
    efforts: list[dict[str, Any]] = []
    for rec in grouped.values():
        id_campanha = rec["id_campanha"]
        if point_ids is not None and id_campanha is not None:
            rec["id_ponto_coleta"] = point_ids.get((int(id_campanha), rec["nome_ponto"]))
        tipo_values = sorted(v for v in rec.pop("tipo_values") if v)
        esforco_values = sorted({v for v in rec.pop("esforco_values") if v is not None})
        unidade_values = sorted({v for v in rec.pop("unidade_values") if v})
        rec["tipo_amostragem"] = tipo_values[0] if len(tipo_values) == 1 else "Mista"
        rec["tipo_de_amostragem"] = rec["tipo_amostragem"]
        rec["esforco"] = esforco_values[0] if esforco_values else None
        rec["unidade_esforco"] = unidade_values[0] if unidade_values else None
        rec["tipos_fonte"] = ", ".join(tipo_values)
        rec["unidades_fonte"] = ", ".join(unidade_values)
        efforts.append(rec)
    return efforts, raw_rows


def species_map(conn) -> dict[str, int]:
    rows = conn.execute(text("SELECT id_especie, nome_cientifico FROM public.especies")).mappings().all()
    return {str(row["nome_cientifico"]).strip(): int(row["id_especie"]) for row in rows}


def effort_logical_key(campaign: str, point: str, group: str, method: str) -> tuple[str, str, str, str]:
    return (campaign, point, group, method)


def fetch_effort_map(conn) -> dict[tuple[str, str, str, str], int]:
    rows = conn.execute(
        text(
            """
            SELECT e.id_esforco, c.nome_campanha, p.nome_ponto, e.grupo_biologico, e.metodo_de_captura
            FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            JOIN public.campanhas c ON c.id_campanha = p.id_campanha
            WHERE p.id_projeto = :id_projeto
            """
        ),
        {"id_projeto": PROJECT_ID},
    ).mappings().all()
    return {
        effort_logical_key(
            str(row["nome_campanha"]).strip(),
            str(row["nome_ponto"]).strip(),
            str(row["grupo_biologico"]).strip(),
            str(row["metodo_de_captura"]).strip(),
        ): int(row["id_esforco"])
        for row in rows
    }


def check_result_type_conflicts(workbooks: list[WorkbookData]) -> None:
    conflicts = []
    for wb in workbooks:
        df = wb.resultados.copy()
        for col in ["Ponto", "Campanha", "Metodo_de_Captura", "Nome_Cientifico", "Tipo_de_Amostragem"]:
            df[col] = df[col].map(clean_text)
        type_counts = (
            df.groupby(["Campanha", "Ponto", "Metodo_de_Captura", "Nome_Cientifico"], dropna=False)["Tipo_de_Amostragem"]
            .nunique()
            .reset_index(name="tipos")
        )
        bad = type_counts[type_counts["tipos"] > 1]
        if not bad.empty:
            conflicts.extend({"grupo": wb.group, **row} for row in bad.to_dict(orient="records"))
    if conflicts:
        raise RuntimeError(f"Uma mesma especie aparece em mais de um tipo no mesmo ponto/metodo: {conflicts[:10]}")


def check_sampling_type_integrity(workbooks: list[WorkbookData]) -> None:
    errors = []
    for wb in workbooks:
        effort_types = {}
        for _, row in wb.esforco.iterrows():
            key = (clean_text(row.get("Campanha")), clean_text(row.get("Ponto")), clean_text(row.get("Metodo_de_Captura")))
            effort_types[key] = clean_text(row.get("Tipo_de_Amostragem"))
        for _, row in wb.resultados.iterrows():
            key = (clean_text(row.get("Campanha")), clean_text(row.get("Ponto")), clean_text(row.get("Metodo_de_Captura")))
            result_type = clean_text(row.get("Tipo_de_Amostragem"))
            effort_type = effort_types.get(key)
            if norm_key(result_type) not in {"qualitativa", "quantitativa"}:
                errors.append({"grupo": wb.group, "chave": key, "erro": "tipo_resultado_invalido", "valor": result_type})
            elif effort_type is None:
                errors.append({"grupo": wb.group, "chave": key, "erro": "esforco_ausente"})
            elif norm_key(result_type) != norm_key(effort_type):
                errors.append({"grupo": wb.group, "chave": key, "erro": "resultado_esforco_divergentes", "resultado": result_type, "esforco": effort_type})
    if errors:
        raise RuntimeError(f"Integridade dos tipos de amostragem falhou: {errors[:20]}")


def weighted_mean(values: pd.Series, weights: pd.Series) -> float | None:
    pairs = [(to_float(v), numeric_or_zero(w)) for v, w in zip(values.tolist(), weights.tolist())]
    pairs = [(v, w if w > 0 else 1.0) for v, w in pairs if v is not None]
    if not pairs:
        return None
    denominator = sum(w for _, w in pairs)
    if denominator == 0:
        return sum(v for v, _ in pairs) / len(pairs)
    return sum(v * w for v, w in pairs) / denominator


def prepare_results(
    workbooks: list[WorkbookData],
    effort_ids: dict[tuple[str, str, str, str], int] | None,
    species: dict[str, int],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    check_result_type_conflicts(workbooks)
    check_sampling_type_integrity(workbooks)
    by_table: dict[str, list[dict[str, Any]]] = {table: [] for table in RESULT_TABLES}
    summary_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    for wb in workbooks:
        df = wb.resultados.copy()
        for col in ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico", "Unidade_Esforco"]:
            if col in df.columns:
                df[col] = df[col].map(clean_text)
        df["valor_num"] = df["Numero_de_Individuos"].map(numeric_or_zero)
        missing_species = sorted({name for name in df["Nome_Cientifico"].dropna().unique() if name not in species})
        if missing_species:
            raise RuntimeError(f"{wb.group}: especies ausentes no banco: {missing_species[:20]}")

        grouped_cols = ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]
        if wb.group == "Ictiofauna":
            grouped = []
            for keys, g in df.groupby(grouped_cols, dropna=False):
                campaign, point, method, sample_type, taxon = keys
                n_total = int(round(float(g["valor_num"].sum())))
                grouped.append(
                    {
                        "Campanha": campaign,
                        "Ponto": point,
                        "Metodo_de_Captura": method,
                        "Tipo_de_Amostragem": sample_type,
                        "Nome_Cientifico": taxon,
                        "numero": n_total,
                        "ct_cm": weighted_mean(g.get("CT_cm", pd.Series(dtype=object)), g["valor_num"]),
                        "cp_cm": weighted_mean(g.get("CP_cm", pd.Series(dtype=object)), g["valor_num"]),
                        "pc_g": weighted_mean(g.get("PC_g", pd.Series(dtype=object)), g["valor_num"]),
                        "sexo": "; ".join(sorted({str(v).strip() for v in g.get("Sexo", pd.Series(dtype=object)).dropna() if clean_text(v)})) or None,
                        "emg": "; ".join(sorted({str(v).strip() for v in g.get("EMG", pd.Series(dtype=object)).dropna() if clean_text(v)})) or None,
                        "observacao": "; ".join(sorted({str(v).strip() for v in g.get("Observacao_Individuo_Lote", pd.Series(dtype=object)).dropna() if clean_text(v)})) or None,
                        "linhas_fonte": int(len(g)),
                    }
                )
            aggregate_df = pd.DataFrame(grouped)
        else:
            aggregate_df = (
                df.groupby(grouped_cols, dropna=False)
                .agg(
                    valor=("valor_num", "sum"),
                    unidade=("Unidade_Esforco", lambda values: next((v for v in values if v), None)),
                    observacao=("Observacao_Individuo_Lote", lambda values: "; ".join(sorted({str(v).strip() for v in values.dropna() if clean_text(v)})) or None),
                    linhas_fonte=("valor_num", "size"),
                )
                .reset_index()
            )

        for _, row in aggregate_df.iterrows():
            campaign = row["Campanha"]
            point = row["Ponto"]
            method = row["Metodo_de_Captura"]
            sample_type = row["Tipo_de_Amostragem"]
            taxon = row["Nome_Cientifico"]
            effort_key = effort_logical_key(campaign, point, wb.group, method)
            id_esforco = effort_ids.get(effort_key) if effort_ids is not None else None
            id_especie = species.get(taxon)
            if effort_ids is not None and id_esforco is None:
                raise RuntimeError(f"Esforco nao encontrado para {effort_key}")
            if wb.group == "Fitoplâncton":
                value = float(row["valor"])
                record = {
                    "id_esforco": id_esforco,
                    "id_especie": id_especie,
                    "densidade": value,
                    "unidade_densidade": row.get("unidade"),
                    "biovolume": None,
                    "unidade_biovolume": None,
                    "densidade_cel_ml": None,
                    "biovolume_mm3_l": None,
                    "observacoes": row.get("observacao"),
                    "tipo_amostragem": sample_type,
                }
                by_table["resultados_fitoplancton"].append(record)
                metric_total = value
            elif wb.group == "Zooplâncton":
                value = float(row["valor"])
                record = {
                    "id_esforco": id_esforco,
                    "id_especie": id_especie,
                    "numero_de_individuos": value,
                    "unidade_contagem": row.get("unidade"),
                    "tipo_amostragem": sample_type,
                }
                by_table["resultados_zooplancton"].append(record)
                metric_total = value
            elif wb.group == "Zoobentos":
                value = int(round(float(row["valor"])))
                record = {
                    "id_esforco": id_esforco,
                    "id_especie": id_especie,
                    "abundancia": value,
                    "tipo_amostragem": sample_type,
                }
                by_table["resultados_zoobentos"].append(record)
                metric_total = value
            else:
                value = int(row["numero"])
                record = {
                    "id_esforco": id_esforco,
                    "id_especie": id_especie,
                    "numero_de_individuos": value,
                    "ct_cm": row.get("ct_cm"),
                    "cp_cm": row.get("cp_cm"),
                    "pc_g": row.get("pc_g"),
                    "sexo": row.get("sexo"),
                    "emg": row.get("emg"),
                    "observacao_individuo_lote": row.get("observacao"),
                    "tipo_amostragem": sample_type,
                }
                by_table["resultados_ictiofauna"].append(record)
                metric_total = value
            detail_rows.append(
                {
                    "grupo": wb.group,
                    "campanha": campaign,
                    "ponto": point,
                    "metodo": method,
                    "tipo": sample_type,
                    "taxon": taxon,
                    "linhas_fonte": int(row.get("linhas_fonte", 1)),
                    "valor_migravel": metric_total,
                }
            )
        summary_rows.append(
            {
                "grupo": wb.group,
                "arquivo": str(wb.path),
                "linhas_fonte": int(len(df)),
                "linhas_migraveis": int(len(aggregate_df)),
                "taxons": int(df["Nome_Cientifico"].dropna().nunique()),
                "campanhas": int(df["Campanha"].dropna().nunique()),
                "pontos": int(df["Ponto"].dropna().nunique()),
                "valor_total": float(df["valor_num"].sum()),
            }
        )
    return by_table, summary_rows, detail_rows


def source_summary(points: list[dict[str, Any]], efforts: list[dict[str, Any]], result_summary: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pontos": len(points),
        "campanhas": len({p["campanha"] for p in points}),
        "esforcos": len(efforts),
        "resultados_migraveis": int(sum(row["linhas_migraveis"] for row in result_summary)),
        "linhas_fonte": int(sum(row["linhas_fonte"] for row in result_summary)),
        "taxons_soma_por_grupo": int(sum(row["taxons"] for row in result_summary)),
    }


def sampling_summary(result_detail: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not result_detail:
        return []
    frame = pd.DataFrame(result_detail)
    return (
        frame.groupby(["grupo", "campanha", "tipo"], dropna=False)
        .agg(linhas_fonte=("linhas_fonte", "sum"), registros_migraveis=("taxon", "size"), valor_total=("valor_migravel", "sum"))
        .reset_index()
        .to_dict(orient="records")
    )


def db_counts(conn) -> dict[str, Any]:
    result: dict[str, Any] = {}
    result["pontos"] = conn.execute(
        text("SELECT count(*)::int FROM public.pontos_coleta WHERE id_projeto = :id"),
        {"id": PROJECT_ID},
    ).scalar_one()
    result["esforcos"] = conn.execute(
        text(
            """
            SELECT count(*)::int
            FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id
              AND e.grupo_biologico = ANY(:groups)
            """
        ),
        {"id": PROJECT_ID, "groups": [info["canonical"] for info in GROUPS.values()]},
    ).scalar_one()
    for table in RESULT_TABLES:
        result[table] = conn.execute(
            text(
                f"""
                SELECT count(*)::int
                FROM public.{table} r
                JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
                JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
                WHERE p.id_projeto = :id
                  AND e.grupo_biologico = ANY(:groups)
                """
            ),
            {"id": PROJECT_ID, "groups": [info["canonical"] for info in GROUPS.values()]},
        ).scalar_one()
    result["consolidado"] = conn.execute(
        text(
            """
            SELECT count(*)::int
            FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND grupo_biologico = ANY(:groups)
            """
        ),
        {"code": PROJECT_CODE, "groups": [info["canonical"] for info in GROUPS.values()]},
    ).scalar_one()
    return result


def create_backups(conn, stamp: str) -> dict[str, str]:
    backups: dict[str, str] = {}
    groups = [info["canonical"] for info in GROUPS.values()]
    statements = {
        "pontos": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_pontos AS
            SELECT *
            FROM public.pontos_coleta
            WHERE id_projeto = :id
        """,
        "esforcos": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_esforcos AS
            SELECT e.*
            FROM public.esforcos_amostragem e
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id
              AND e.grupo_biologico = ANY(:groups)
        """,
        "fitoplancton": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_fitoplancton AS
            SELECT r.*
            FROM public.resultados_fitoplancton r
            JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id
        """,
        "zooplancton": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_zooplancton AS
            SELECT r.*
            FROM public.resultados_zooplancton r
            JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id
        """,
        "zoobentos": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_zoobentos AS
            SELECT r.*
            FROM public.resultados_zoobentos r
            JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id
        """,
        "ictiofauna": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_ictiofauna AS
            SELECT r.*
            FROM public.resultados_ictiofauna r
            JOIN public.esforcos_amostragem e ON e.id_esforco = r.id_esforco
            JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
            WHERE p.id_projeto = :id
        """,
        "consolidado": f"""
            CREATE TABLE public.backup_biota_{PROJECT_SLUG}_{stamp}_consolidado AS
            SELECT *
            FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND grupo_biologico = ANY(:groups)
        """,
    }
    for name, sql in statements.items():
        conn.execute(text(sql), {"id": PROJECT_ID, "code": PROJECT_CODE, "groups": groups})
        backups[name] = f"public.backup_biota_{PROJECT_SLUG}_{stamp}_{name}"
    return backups


def delete_existing(conn) -> dict[str, int]:
    groups = [info["canonical"] for info in GROUPS.values()]
    deleted: dict[str, int] = {}
    for table in RESULT_TABLES:
        deleted[table] = conn.execute(
            text(
                f"""
                DELETE FROM public.{table} r
                USING public.esforcos_amostragem e, public.pontos_coleta p
                WHERE r.id_esforco = e.id_esforco
                  AND e.id_ponto_coleta = p.id_ponto_coleta
                  AND p.id_projeto = :id
                  AND e.grupo_biologico = ANY(:groups)
                """
            ),
            {"id": PROJECT_ID, "groups": groups},
        ).rowcount or 0
    deleted["esforcos"] = conn.execute(
        text(
            """
            DELETE FROM public.esforcos_amostragem e
            USING public.pontos_coleta p
            WHERE e.id_ponto_coleta = p.id_ponto_coleta
              AND p.id_projeto = :id
              AND e.grupo_biologico = ANY(:groups)
            """
        ),
        {"id": PROJECT_ID, "groups": groups},
    ).rowcount or 0
    deleted["consolidado"] = conn.execute(
        text(
            """
            DELETE FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND grupo_biologico = ANY(:groups)
            """
        ),
        {"code": PROJECT_CODE, "groups": groups},
    ).rowcount or 0
    return deleted


def insert_points(conn, points: list[dict[str, Any]]) -> None:
    rows = [
        {k: rec.get(k) for k in [
            "id_projeto", "id_campanha", "nome_ponto", "data_hora_coleta", "latitude", "longitude",
            "bacia_hidrografica", "curso_d_agua", "municipio", "observacoes",
        ]}
        for rec in points
    ]
    conn.execute(
        text(
            """
            INSERT INTO public.pontos_coleta (
                id_projeto,
                id_campanha,
                nome_ponto,
                data_hora_coleta,
                latitude,
                longitude,
                bacia_hidrografica,
                curso_d_agua,
                municipio,
                observacoes
            )
            VALUES (
                :id_projeto,
                :id_campanha,
                :nome_ponto,
                :data_hora_coleta,
                :latitude,
                :longitude,
                :bacia_hidrografica,
                :curso_d_agua,
                :municipio,
                :observacoes
            )
            ON CONFLICT (id_projeto, id_campanha, nome_ponto)
                WHERE id_empreendimento IS NULL
            DO UPDATE SET
                data_hora_coleta = EXCLUDED.data_hora_coleta,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                bacia_hidrografica = EXCLUDED.bacia_hidrografica,
                curso_d_agua = EXCLUDED.curso_d_agua,
                municipio = EXCLUDED.municipio,
                observacoes = EXCLUDED.observacoes
            """
        ),
        rows,
    )


def insert_efforts(conn, efforts: list[dict[str, Any]]) -> None:
    rows = [
        {
            "id_ponto_coleta": rec["id_ponto_coleta"],
            "grupo_biologico": rec["grupo_biologico"],
            "metodo_de_captura": rec["metodo_de_captura"],
            "tipo_amostragem": rec["tipo_amostragem"],
            "tipo_de_amostragem": rec["tipo_de_amostragem"],
            "esforco": rec["esforco"],
            "unidade_esforco": rec["unidade_esforco"],
        }
        for rec in efforts
    ]
    conn.execute(
        text(
            """
            INSERT INTO public.esforcos_amostragem (
                id_ponto_coleta,
                grupo_biologico,
                metodo_de_captura,
                tipo_amostragem,
                tipo_de_amostragem,
                esforco,
                unidade_esforco
            )
            VALUES (
                :id_ponto_coleta,
                :grupo_biologico,
                :metodo_de_captura,
                :tipo_amostragem,
                :tipo_de_amostragem,
                :esforco,
                :unidade_esforco
            )
            ON CONFLICT (id_ponto_coleta, grupo_biologico, metodo_de_captura)
            DO UPDATE SET
                tipo_amostragem = EXCLUDED.tipo_amostragem,
                tipo_de_amostragem = EXCLUDED.tipo_de_amostragem,
                esforco = EXCLUDED.esforco,
                unidade_esforco = EXCLUDED.unidade_esforco
            """
        ),
        rows,
    )


def insert_results(conn, results_by_table: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    inserted: dict[str, int] = {}
    specs = {
        "resultados_fitoplancton": (
            ["id_esforco", "id_especie", "densidade", "unidade_densidade", "biovolume", "unidade_biovolume", "densidade_cel_ml", "biovolume_mm3_l", "observacoes", "tipo_amostragem"],
            "uq_resultado_fito_por_esforco_especie",
        ),
        "resultados_zooplancton": (
            ["id_esforco", "id_especie", "numero_de_individuos", "unidade_contagem", "tipo_amostragem"],
            "unq_zoo_resultado",
        ),
        "resultados_zoobentos": (
            ["id_esforco", "id_especie", "abundancia", "tipo_amostragem"],
            "uq_resultado_por_esforco_especie",
        ),
        "resultados_ictiofauna": (
            ["id_esforco", "id_especie", "numero_de_individuos", "ct_cm", "cp_cm", "pc_g", "sexo", "emg", "observacao_individuo_lote", "tipo_amostragem"],
            "uq_resultado_ictio_por_esforco_especie",
        ),
    }
    for table, rows in results_by_table.items():
        if not rows:
            inserted[table] = 0
            continue
        cols, constraint = specs[table]
        col_sql = ", ".join(cols)
        values_sql = ", ".join(f":{col}" for col in cols)
        update_cols = [col for col in cols if col not in {"id_esforco", "id_especie"}]
        update_sql = ", ".join(f"{col}=EXCLUDED.{col}" for col in update_cols)
        prepared = [{col: row.get(col) for col in cols} for row in rows]
        result = conn.execute(
            text(
                f"""
                INSERT INTO public.{table} ({col_sql})
                VALUES ({values_sql})
                ON CONFLICT ON CONSTRAINT {constraint}
                DO UPDATE SET {update_sql}
                """
            ),
            prepared,
        )
        inserted[table] = result.rowcount or len(prepared)
    return inserted


CONSOLIDATE_SQL = text(
    """
    INSERT INTO public.biota_analise_consolidada (
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
        nome_empreendimento,
        id_projeto
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
        rf.densidade::numeric AS contagem,
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
        COALESCE(rf.tipo_amostragem, e.tipo_amostragem, e.tipo_de_amostragem) AS tipo_amostragem,
        p.id_empreendimento,
        emp.nome AS nome_empreendimento,
        pr.id_projeto
    FROM public.resultados_fitoplancton rf
    JOIN public.esforcos_amostragem e ON e.id_esforco = rf.id_esforco
    JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN public.campanhas c ON c.id_campanha = p.id_campanha
    JOIN public.projetos pr ON pr.id_projeto = p.id_projeto
    JOIN public.clientes cli ON cli.id_cliente = pr.id_cliente
    JOIN public.especies sp ON sp.id_especie = rf.id_especie
    LEFT JOIN public.empreendimentos emp ON emp.id_empreendimento = p.id_empreendimento
    WHERE p.id_projeto = :id_projeto
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = 'Fitoplâncton'
      AND e.grupo_biologico = ANY(:groups)
    UNION ALL
    SELECT
        cli.nome_empresa, pr.nome_projeto, NULL::text, c.nome_campanha, p.nome_ponto,
        p.latitude, p.longitude, e.grupo_biologico, sp.nome_cientifico,
        rz.numero_de_individuos::numeric, NULL::numeric, sp.bmwp_score,
        pr.codigo_interno_opyta, p.data_hora_coleta, p.bacia_hidrografica,
        e.metodo_de_captura, e.esforco, e.unidade_esforco,
        sp.nome_popular, sp.reino, sp.filo, sp.classe, sp.ordem, sp.familia,
        sp.genero, sp.origem, NULL::numeric, NULL::numeric,
        COALESCE(rz.tipo_amostragem, e.tipo_amostragem, e.tipo_de_amostragem),
        p.id_empreendimento, emp.nome, pr.id_projeto
    FROM public.resultados_zooplancton rz
    JOIN public.esforcos_amostragem e ON e.id_esforco = rz.id_esforco
    JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN public.campanhas c ON c.id_campanha = p.id_campanha
    JOIN public.projetos pr ON pr.id_projeto = p.id_projeto
    JOIN public.clientes cli ON cli.id_cliente = pr.id_cliente
    JOIN public.especies sp ON sp.id_especie = rz.id_especie
    LEFT JOIN public.empreendimentos emp ON emp.id_empreendimento = p.id_empreendimento
    WHERE p.id_projeto = :id_projeto
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = 'Zooplâncton'
      AND e.grupo_biologico = ANY(:groups)
    UNION ALL
    SELECT
        cli.nome_empresa, pr.nome_projeto, NULL::text, c.nome_campanha, p.nome_ponto,
        p.latitude, p.longitude, e.grupo_biologico, sp.nome_cientifico,
        rb.abundancia::numeric, NULL::numeric, sp.bmwp_score,
        pr.codigo_interno_opyta, p.data_hora_coleta, p.bacia_hidrografica,
        e.metodo_de_captura, e.esforco, e.unidade_esforco,
        sp.nome_popular, sp.reino, sp.filo, sp.classe, sp.ordem, sp.familia,
        sp.genero, sp.origem, NULL::numeric, NULL::numeric,
        COALESCE(rb.tipo_amostragem, e.tipo_amostragem, e.tipo_de_amostragem),
        p.id_empreendimento, emp.nome, pr.id_projeto
    FROM public.resultados_zoobentos rb
    JOIN public.esforcos_amostragem e ON e.id_esforco = rb.id_esforco
    JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN public.campanhas c ON c.id_campanha = p.id_campanha
    JOIN public.projetos pr ON pr.id_projeto = p.id_projeto
    JOIN public.clientes cli ON cli.id_cliente = pr.id_cliente
    JOIN public.especies sp ON sp.id_especie = rb.id_especie
    LEFT JOIN public.empreendimentos emp ON emp.id_empreendimento = p.id_empreendimento
    WHERE p.id_projeto = :id_projeto
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = 'Zoobentos'
      AND e.grupo_biologico = ANY(:groups)
    UNION ALL
    SELECT
        cli.nome_empresa, pr.nome_projeto, NULL::text, c.nome_campanha, p.nome_ponto,
        p.latitude, p.longitude, e.grupo_biologico, sp.nome_cientifico,
        ri.numero_de_individuos::numeric,
        CASE
            WHEN ri.pc_g IS NULL THEN NULL::numeric
            ELSE (ri.pc_g * COALESCE(NULLIF(ri.numero_de_individuos, 0), 1))::numeric
        END AS biomassa,
        sp.bmwp_score,
        pr.codigo_interno_opyta, p.data_hora_coleta, p.bacia_hidrografica,
        e.metodo_de_captura, e.esforco, e.unidade_esforco,
        sp.nome_popular, sp.reino, sp.filo, sp.classe, sp.ordem, sp.familia,
        sp.genero, sp.origem, ri.ct_cm::numeric, ri.cp_cm::numeric,
        COALESCE(ri.tipo_amostragem, e.tipo_amostragem, e.tipo_de_amostragem),
        p.id_empreendimento, emp.nome, pr.id_projeto
    FROM public.resultados_ictiofauna ri
    JOIN public.esforcos_amostragem e ON e.id_esforco = ri.id_esforco
    JOIN public.pontos_coleta p ON p.id_ponto_coleta = e.id_ponto_coleta
    JOIN public.campanhas c ON c.id_campanha = p.id_campanha
    JOIN public.projetos pr ON pr.id_projeto = p.id_projeto
    JOIN public.clientes cli ON cli.id_cliente = pr.id_cliente
    JOIN public.especies sp ON sp.id_especie = ri.id_especie
    LEFT JOIN public.empreendimentos emp ON emp.id_empreendimento = p.id_empreendimento
    WHERE p.id_projeto = :id_projeto
      AND pr.codigo_interno_opyta = :project_code
      AND e.grupo_biologico = 'Ictiofauna'
      AND e.grupo_biologico = ANY(:groups)
    """
)


def consolidate(conn) -> int:
    groups = [info["canonical"] for info in GROUPS.values()]
    conn.execute(
        text(
            """
            DELETE FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND grupo_biologico = ANY(:groups)
            """
        ),
        {"code": PROJECT_CODE, "groups": groups},
    )
    result = conn.execute(CONSOLIDATE_SQL, {"id_projeto": PROJECT_ID, "project_code": PROJECT_CODE, "groups": groups})
    return result.rowcount or 0


def group_campaign_summary(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        text(
            """
            SELECT grupo_biologico, nome_campanha, count(*)::int AS linhas,
                   count(DISTINCT nome_ponto)::int AS pontos,
                   count(DISTINCT nome_cientifico)::int AS taxons,
                   coalesce(sum(contagem), 0)::numeric AS contagem_total,
                   coalesce(sum(biomassa), 0)::numeric AS biomassa_total
            FROM public.biota_analise_consolidada
            WHERE codigo_interno_opyta = :code
              AND grupo_biologico = ANY(:groups)
            GROUP BY grupo_biologico, nome_campanha
            ORDER BY grupo_biologico, nome_campanha
            """
        ),
        {"code": PROJECT_CODE, "groups": [info["canonical"] for info in GROUPS.values()]},
    ).mappings().all()
    return [dict(row) for row in rows]


def build_plan(input_dir: Path, conn, apply: bool, input_files: list[Path] | None = None) -> dict[str, Any]:
    workbooks = load_workbooks(input_dir, input_files)
    check_project_codes(workbooks)
    project = ensure_project(conn)
    campaigns = collect_campaigns(workbooks)
    campaign_ids = ensure_campaigns(conn, campaigns, apply=apply)
    points, point_conflicts = collect_points(workbooks, campaign_ids)
    current_point_ids = fetch_point_map(conn)
    point_ids = current_point_ids if apply else None
    efforts, raw_efforts = collect_efforts(workbooks, campaign_ids, point_ids)
    species = species_map(conn)
    results_by_table, result_summary, result_detail = prepare_results(workbooks, None, species)
    before = db_counts(conn)
    return {
        "active_groups": active_group_names(),
        "project": project,
        "campaigns": [{"nome_campanha": name, "id_campanha": campaign_ids.get(name)} for name in campaigns],
        "points": points,
        "point_conflicts": point_conflicts,
        "efforts": efforts,
        "raw_efforts": raw_efforts,
        "results_by_table": results_by_table,
        "result_summary": result_summary,
        "result_detail": result_detail,
        "sampling_summary": sampling_summary(result_detail),
        "source_summary": source_summary(points, efforts, result_summary),
        "db_before": before,
    }


def apply_migration(input_dir: Path, conn, stamp: str, input_files: list[Path] | None = None) -> dict[str, Any]:
    workbooks = load_workbooks(input_dir, input_files)
    check_project_codes(workbooks)
    project = ensure_project(conn)
    campaigns = collect_campaigns(workbooks)
    before = db_counts(conn)
    backups = create_backups(conn, stamp.lower())
    deleted = delete_existing(conn)
    campaign_ids = ensure_campaigns(conn, campaigns, apply=True)
    points, point_conflicts = collect_points(workbooks, campaign_ids)
    if point_conflicts:
        raise RuntimeError(f"Conflitos de pontos apos apply prep: {point_conflicts[:10]}")
    insert_points(conn, points)
    point_ids = fetch_point_map(conn)
    efforts, raw_efforts = collect_efforts(workbooks, campaign_ids, point_ids)
    missing_point_efforts = [rec for rec in efforts if rec.get("id_ponto_coleta") is None]
    if missing_point_efforts:
        raise RuntimeError(f"Esforcos sem ponto no banco: {missing_point_efforts[:10]}")
    insert_efforts(conn, efforts)
    effort_ids = fetch_effort_map(conn)
    species = species_map(conn)
    results_by_table, result_summary, result_detail = prepare_results(workbooks, effort_ids, species)
    inserted_results = insert_results(conn, results_by_table)
    inserted_consolidated = consolidate(conn)
    after = db_counts(conn)
    by_campaign = group_campaign_summary(conn)
    planned = source_summary(points, efforts, result_summary)
    expected_result_rows = sum(len(rows) for rows in results_by_table.values())
    if after["consolidado"] != expected_result_rows or inserted_consolidated != expected_result_rows:
        raise RuntimeError(
            "Auditoria de consolidacao falhou: "
            f"esperado={expected_result_rows}, consolidado={after['consolidado']}, inserted={inserted_consolidated}"
        )
    return {
        "active_groups": active_group_names(),
        "project": project,
        "campaigns": [{"nome_campanha": name, "id_campanha": campaign_ids.get(name)} for name in campaigns],
        "backups": backups,
        "deleted": deleted,
        "points": points,
        "efforts": efforts,
        "raw_efforts": raw_efforts,
        "result_summary": result_summary,
        "result_detail": result_detail,
        "sampling_summary": sampling_summary(result_detail),
        "result_counts_by_table": {table: len(rows) for table, rows in results_by_table.items()},
        "inserted_results": inserted_results,
        "inserted_consolidated": inserted_consolidated,
        "source_summary": planned,
        "db_before": before,
        "db_after": after,
        "consolidated_by_campaign": by_campaign,
    }


def df_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records) if records else pd.DataFrame()


def serializable_payload(payload: dict[str, Any], applied: bool, stamp: str) -> dict[str, Any]:
    slim = {
        "stamp": stamp,
        "applied": applied,
        "active_groups": payload.get("active_groups") or active_group_names(),
        "project": payload.get("project"),
        "campaigns": payload.get("campaigns"),
        "source_summary": payload.get("source_summary"),
        "db_before": payload.get("db_before"),
        "db_after": payload.get("db_after"),
        "backups": payload.get("backups"),
        "deleted": payload.get("deleted"),
        "result_counts_by_table": payload.get("result_counts_by_table") or {
            table: len(rows) for table, rows in payload.get("results_by_table", {}).items()
        },
        "inserted_results": payload.get("inserted_results"),
        "inserted_consolidated": payload.get("inserted_consolidated"),
        "consolidated_by_campaign": payload.get("consolidated_by_campaign"),
        "sampling_summary": payload.get("sampling_summary"),
    }
    return slim


def write_outputs(payload: dict[str, Any], output_dir: Path, client_output_dir: Path | None, applied: bool, stamp: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if client_output_dir:
        client_output_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"apply_migracao_biota_aquatica_{PROJECT_SLUG}" if applied else f"dry_run_migracao_biota_aquatica_{PROJECT_SLUG}"
    json_path = output_dir / f"{stamp}_{suffix}.json"
    xlsx_path = output_dir / f"{stamp}_{suffix}.xlsx"
    json_payload = serializable_payload(payload, applied=applied, stamp=stamp)
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame([json_payload.get("source_summary", {})]).to_excel(writer, sheet_name="00_source_summary", index=False)
        pd.DataFrame([json_payload.get("db_before", {})]).to_excel(writer, sheet_name="01_db_before", index=False)
        if json_payload.get("db_after"):
            pd.DataFrame([json_payload.get("db_after", {})]).to_excel(writer, sheet_name="02_db_after", index=False)
        df_records(payload.get("campaigns", [])).to_excel(writer, sheet_name="03_campaigns", index=False)
        df_records(payload.get("result_summary", [])).to_excel(writer, sheet_name="04_result_summary", index=False)
        df_records(payload.get("points", [])).to_excel(writer, sheet_name="05_points", index=False)
        df_records(payload.get("efforts", [])).to_excel(writer, sheet_name="06_efforts", index=False)
        df_records(payload.get("result_detail", [])).to_excel(writer, sheet_name="07_result_detail", index=False)
        df_records(payload.get("sampling_summary", [])).to_excel(writer, sheet_name="07B_sampling_summary", index=False)
        if payload.get("consolidated_by_campaign"):
            df_records(payload.get("consolidated_by_campaign", [])).to_excel(writer, sheet_name="08_consolidated_campaign", index=False)
        if payload.get("backups"):
            pd.DataFrame([payload.get("backups", {})]).to_excel(writer, sheet_name="09_backups", index=False)
    if client_output_dir:
        (client_output_dir / json_path.name).write_bytes(json_path.read_bytes())
        (client_output_dir / xlsx_path.name).write_bytes(xlsx_path.read_bytes())
    return json_path, xlsx_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run/apply migration for BRAAEG001 bioaquatic data.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--client-output-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_LOG_DIR)
    parser.add_argument("--opyta-data-root", type=Path, default=Path.cwd().parent / "Opyta_Data")
    parser.add_argument("--input-files", nargs="+", type=Path, help="Exact workbook(s) to read instead of scanning --input-dir.")
    parser.add_argument("--groups", nargs="+", help="Groups to migrate, e.g. Zoobentos or Bentos. Defaults to all groups.")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    configure_groups(args.groups)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    engine = connect_engine(args.opyta_data_root)
    try:
        if args.apply:
            with engine.begin() as conn:
                payload = apply_migration(args.input_dir, conn, stamp, args.input_files)
        else:
            with engine.connect() as conn:
                payload = build_plan(args.input_dir, conn, apply=False, input_files=args.input_files)
        json_path, xlsx_path = write_outputs(payload, args.output_dir, args.client_output_dir, args.apply, stamp)
        result = serializable_payload(payload, applied=args.apply, stamp=stamp)
        result["json"] = str(json_path)
        result["xlsx"] = str(xlsx_path)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=json_default))
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
