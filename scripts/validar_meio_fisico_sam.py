#!/usr/bin/env python
"""
Validacao pre-migracao - Meio Fisico (SAM Metais / FERSAM001)

Objetivo:
- Validar integridade dos dados antes de subir para o banco.
- Detectar problemas comuns de migracao (simbolos especiais, parametros, pontos/campanhas).
- Gerar evidencias de validacao (JSON + CSV) para auditoria.

Uso:
  python scripts/validar_meio_fisico_sam.py
  python scripts/validar_meio_fisico_sam.py --base-dir "G:/.../Migracao/Fisico"
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import get_close_matches
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_BASE_DIR = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Ferreira Rocha\SAM Metais\Produtos\Migração\Físico"
)
DEFAULT_RESULTADOS = "Resultados_Meio_Fisico.xlsx"
DEFAULT_CADASTRO = "cadastro_parametros_opyta.xlsx"

OUT_DIR = Path("logs") / "validacao_meio_fisico"

SHEET_RESULTADOS = "Resultados_Meio_Fisico"
SHEET_PONTOS = "Pontos_e_Campanhas"

REQ_COLS_RESULTADOS = [
    "Ponto",
    "Campanha",
    "Matriz",
    "Parametro",
    "Resultado",
    "Unidade_Medida",
    "Laboratorio",
]
REQ_COLS_PONTOS = [
    "Ponto",
    "Campanha",
    "Data",
    "Latitude",
    "Longitude",
]
REQ_COLS_CADASTRO = [
    "Parametro",
    "Unidade_Medida",
]

EXPECTED_MATRIZES = {"Agua Superficial", "Agua Subterranea", "Sedimento"}
EXPECTED_CAMPANHAS = {"Campanha-01-Seca", "Campanha-02-Chuva"}
EXPECTED_FAUNA_POINTS = {f"SAM_{i:02d}" for i in range(1, 27)}
ALLOWED_DRY_POINTS = {"SAM_22"}

# Harmonizacao de nomenclatura de parametros entre laboratorios e cadastro Opyta
PARAM_ALIAS_MAP = {
    "Nitrogenio Nitroso": "Nitrito",
    "Nitrogenio nitrico": "Nitrato",
    "pH": "pH In Situ",
}

# Parametros sem VMP/cadastro formal que podem existir no resultado sem bloquear migracao
ALLOWED_PARAMS_WITHOUT_CADASTRO = {
    "Dureza Total",
    "Materia Organica",
}


@dataclass
class Finding:
    severity: str
    check: str
    details: str


def _ascii_fold(text: Any) -> str:
    s = "" if text is None else str(text).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def _normalize_spaces(text: Any) -> str:
    return re.sub(r"\s+", " ", _ascii_fold(text)).strip()


def _norm_param_strict(text: Any) -> str:
    s = _normalize_spaces(text).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _norm_param_loose(text: Any) -> str:
    s = _norm_param_strict(text)
    # remove qualificadores que costumam variar por laboratorio
    for token in ["cliente", "in situ", "total", "dissolvido", "od"]:
        s = s.replace(token, " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _norm_matriz(text: Any) -> str:
    s = _normalize_spaces(text)
    s = s.replace("Aguas", "Agua")
    return s


def _extract_symbol_and_number(value: Any) -> tuple[str | None, float | None, str | None]:
    """Parse resultado textual e extrai simbolo (<, >, <=, >=) e numero."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None, "empty"

    raw = str(value).strip()
    if not raw:
        return None, None, "empty"

    txt = raw.replace("\u2264", "<=").replace("\u2265", ">=")
    txt = txt.replace("\xa0", " ").strip()

    missing_tokens = {"NI", "N/I", "NA", "N/A", "ND", "N/D", "-", "--"}
    if txt.upper() in missing_tokens:
        return None, None, None

    symbol = None
    for pref in ("<=", ">=", "<", ">"):
        if txt.startswith(pref):
            symbol = pref
            txt = txt[len(pref):].strip()
            break

    # remove textos residuais comuns
    txt = re.sub(r"(?i)\b(nd|n/d|na|n\.a\.|ni|n/i)\b", "", txt).strip()
    txt = txt.replace("%", "")

    # decimal pt-br -> float
    # se tem virgula, assume virgula decimal e ponto de milhar
    if "," in txt:
        txt = txt.replace(".", "")
        txt = txt.replace(",", ".")

    txt = txt.replace(" ", "")

    # apenas numero com sinal e decimal
    if not re.fullmatch(r"[-+]?\d*\.?\d+", txt):
        return symbol, None, f"unparsed:{raw}"

    try:
        return symbol, float(txt), None
    except ValueError:
        return symbol, None, f"float_error:{raw}"


def _check_required_columns(df: pd.DataFrame, required: list[str], label: str, findings: list[Finding]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        findings.append(Finding("ERROR", f"required_columns_{label}", f"missing={missing}"))


def _build_report(
    df_res: pd.DataFrame,
    df_pts: pd.DataFrame,
    df_cad: pd.DataFrame,
    base_dir: Path,
) -> tuple[dict[str, Any], list[Finding], pd.DataFrame]:
    findings: list[Finding] = []

    # colunas obrigatorias
    _check_required_columns(df_res, REQ_COLS_RESULTADOS, "resultados", findings)
    _check_required_columns(df_pts, REQ_COLS_PONTOS, "pontos", findings)
    _check_required_columns(df_cad, REQ_COLS_CADASTRO, "cadastro", findings)

    if any(f.severity == "ERROR" and "required_columns" in f.check for f in findings):
        return {"status": "ERROR", "base_dir": str(base_dir)}, findings, pd.DataFrame()

    # limpeza de texto
    for c in ["Ponto", "Campanha", "Matriz", "Parametro", "Resultado", "Unidade_Medida", "Laboratorio"]:
        df_res[c] = df_res[c].map(_normalize_spaces)
    for c in ["Ponto", "Campanha", "Data", "Latitude", "Longitude"]:
        df_pts[c] = df_pts[c].map(_normalize_spaces)
    for c in ["Parametro", "Unidade_Medida"]:
        df_cad[c] = df_cad[c].map(_normalize_spaces)

    # Aplicar harmonizacao de parametro antes das validacoes de cobertura
    df_res["Parametro_Original"] = df_res["Parametro"]
    df_res["Parametro"] = df_res["Parametro"].map(lambda p: PARAM_ALIAS_MAP.get(p, p))

    # parse de resultado e simbolos
    parsed = df_res["Resultado"].apply(_extract_symbol_and_number)
    df_res["parsed_symbol"] = parsed.map(lambda x: x[0])
    df_res["parsed_value"] = parsed.map(lambda x: x[1])
    df_res["parse_error"] = parsed.map(lambda x: x[2])

    n_parse_err = int(df_res["parse_error"].notna().sum())
    if n_parse_err > 0:
        amostra = df_res.loc[df_res["parse_error"].notna(), ["Resultado"]].head(12)["Resultado"].tolist()
        findings.append(Finding("ERROR", "resultado_parse", f"rows={n_parse_err}, sample={amostra}"))

    sym_counts = {
        "lt": int((df_res["parsed_symbol"] == "<").sum()),
        "gt": int((df_res["parsed_symbol"] == ">").sum()),
        "le": int((df_res["parsed_symbol"] == "<=").sum()),
        "ge": int((df_res["parsed_symbol"] == ">=").sum()),
    }

    # campanhas e matrizes esperadas
    campanhas = set(sorted(df_res["Campanha"].dropna().unique().tolist()))
    matrizes = {_norm_matriz(x) for x in df_res["Matriz"].dropna().unique().tolist()}

    miss_camp = sorted(EXPECTED_CAMPANHAS - campanhas)
    extra_camp = sorted(campanhas - EXPECTED_CAMPANHAS)
    if miss_camp or extra_camp:
        findings.append(Finding("WARN", "campanhas_set", f"missing={miss_camp}, extra={extra_camp}"))

    miss_mat = sorted(EXPECTED_MATRIZES - matrizes)
    extra_mat = sorted(matrizes - EXPECTED_MATRIZES)
    if miss_mat or extra_mat:
        findings.append(Finding("WARN", "matrizes_set", f"missing={miss_mat}, extra={extra_mat}"))

    # consistencia pontos base x resultados
    pts_base = set(df_pts["Ponto"].dropna().unique().tolist())
    pts_res = set(df_res["Ponto"].dropna().unique().tolist())

    miss_in_res = sorted(pts_base - pts_res)
    extra_in_res = sorted(pts_res - pts_base)
    miss_in_res_effective = sorted(set(miss_in_res) - ALLOWED_DRY_POINTS)
    dry_points_ok = sorted(set(miss_in_res) & ALLOWED_DRY_POINTS)
    if miss_in_res_effective:
        findings.append(
            Finding(
                "WARN",
                "points_missing_in_resultados",
                f"count={len(miss_in_res_effective)}, points={miss_in_res_effective}",
            )
        )
    if dry_points_ok:
        findings.append(
            Finding(
                "INFO",
                "points_dry_allowed",
                f"count={len(dry_points_ok)}, points={dry_points_ok}",
            )
        )
    if extra_in_res:
        findings.append(Finding("ERROR", "points_not_in_base", f"count={len(extra_in_res)}, points={extra_in_res}"))

    # ponto+campanha precisa existir na base de pontos
    base_pairs = set(zip(df_pts["Ponto"], df_pts["Campanha"]))
    res_pairs = set(zip(df_res["Ponto"], df_res["Campanha"]))
    invalid_pairs = sorted(res_pairs - base_pairs)
    if invalid_pairs:
        findings.append(
            Finding(
                "ERROR",
                "point_campaign_not_in_base",
                f"count={len(invalid_pairs)}, sample={invalid_pairs[:20]}",
            )
        )

    # regra SAM: fauna 1..26 para superficial/sedimento; subterranea com pocos
    matriz_norm = df_res["Matriz"].map(_norm_matriz)

    for matriz in ["Agua Superficial", "Sedimento"]:
        sub = df_res[matriz_norm == matriz]
        pts = set(sub["Ponto"].unique().tolist())
        miss = sorted((EXPECTED_FAUNA_POINTS - ALLOWED_DRY_POINTS) - pts)
        extra = sorted(pts - EXPECTED_FAUNA_POINTS)
        if miss or extra:
            findings.append(Finding("WARN", f"fauna_points_{matriz}", f"missing={miss}, extra={extra}"))

    sub_agua = df_res[matriz_norm == "Agua Subterranea"]
    sub_points = set(sub_agua["Ponto"].unique().tolist())
    pocos = sorted([p for p in sub_points if "POCO" in _ascii_fold(p).upper() or "POCO_" in _ascii_fold(p).upper()])
    if len(sub_points) > 0 and len(pocos) == 0:
        findings.append(Finding("WARN", "subterranea_points_pattern", "nenhum ponto subterraneo com padrao poco"))

    # parametros: cobertura cadastro e variacao por laboratorio
    cad_raw = set(df_cad["Parametro"].dropna().unique().tolist())
    cad_strict = {_norm_param_strict(x): x for x in cad_raw}
    cad_loose = {_norm_param_loose(x): x for x in cad_raw}

    res_params_df = (
        df_res.groupby(["Laboratorio", "Parametro"], as_index=False)
        .size()
        .rename(columns={"size": "rows"})
    )

    unmatched_rows: list[dict[str, Any]] = []
    for _, row in res_params_df.iterrows():
        lab = row["Laboratorio"]
        prm = row["Parametro"]
        strict = _norm_param_strict(prm)
        loose = _norm_param_loose(prm)

        match_type = None
        mapped = None
        if prm in cad_raw:
            match_type = "exact"
            mapped = prm
        elif strict in cad_strict:
            match_type = "strict"
            mapped = cad_strict[strict]
        elif loose in cad_loose:
            match_type = "loose"
            mapped = cad_loose[loose]

        if match_type is None:
            candidates = get_close_matches(loose, list(cad_loose.keys()), n=3, cutoff=0.5)
            suggestions = [cad_loose[c] for c in candidates]
            unmatched_rows.append(
                {
                    "laboratorio": lab,
                    "parametro_resultado": prm,
                    "rows": int(row["rows"]),
                    "suggestions": " | ".join(suggestions),
                }
            )

    unmatched_df_all = pd.DataFrame(unmatched_rows)
    unmatched_critical = (
        unmatched_df_all[~unmatched_df_all["parametro_resultado"].isin(ALLOWED_PARAMS_WITHOUT_CADASTRO)]
        if not unmatched_df_all.empty
        else unmatched_df_all
    )
    unmatched_allowed = (
        unmatched_df_all[unmatched_df_all["parametro_resultado"].isin(ALLOWED_PARAMS_WITHOUT_CADASTRO)]
        if not unmatched_df_all.empty
        else unmatched_df_all
    )

    if not unmatched_critical.empty:
        by_lab = {}
        for _, r in unmatched_critical.iterrows():
            by_lab[r["laboratorio"]] = by_lab.get(r["laboratorio"], 0) + 1
        findings.append(
            Finding(
                "ERROR",
                "parametros_sem_cadastro",
                f"count={len(unmatched_critical)}, por_laboratorio={by_lab}",
            )
        )
    if not unmatched_allowed.empty:
        findings.append(
            Finding(
                "INFO",
                "parametros_sem_cadastro_permitidos",
                f"count={len(unmatched_allowed)}, params={sorted(unmatched_allowed['parametro_resultado'].unique().tolist())}",
            )
        )

    # parametros cadastrados nao usados
    res_strict = {_norm_param_strict(x) for x in df_res["Parametro"].dropna().unique().tolist()}
    cad_not_used = sorted([x for x in cad_raw if _norm_param_strict(x) not in res_strict])
    if cad_not_used:
        findings.append(
            Finding(
                "INFO",
                "parametros_cadastro_sem_uso",
                f"count={len(cad_not_used)}, sample={cad_not_used[:20]}",
            )
        )

    # duplicidade no grao de migracao
    grain = ["Ponto", "Campanha", "Matriz", "Parametro", "Laboratorio"]
    n_dup = int(df_res.duplicated(subset=grain, keep=False).sum())
    if n_dup > 0:
        findings.append(Finding("WARN", "duplicidade_no_grao", f"rows={n_dup}, grain={grain}"))

    # nulos criticos
    critical = ["Ponto", "Campanha", "Matriz", "Parametro", "Resultado", "Laboratorio"]
    null_counts = {c: int(df_res[c].isna().sum()) for c in critical}
    null_counts = {k: v for k, v in null_counts.items() if v > 0}
    if null_counts:
        findings.append(Finding("ERROR", "nulos_criticos", str(null_counts)))

    # status final
    has_error = any(f.severity == "ERROR" for f in findings)
    status = "FAIL" if has_error else "PASS"

    # dataset de parametros nao mapeados
    unmatched_df = unmatched_df_all

    report = {
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_dir": str(base_dir),
        "files": {
            "resultados": str(base_dir / DEFAULT_RESULTADOS),
            "cadastro": str(base_dir / DEFAULT_CADASTRO),
        },
        "shape": {
            "resultados_rows": int(len(df_res)),
            "pontos_rows": int(len(df_pts)),
            "cadastro_rows": int(len(df_cad)),
        },
        "uniques": {
            "matrizes": sorted(df_res["Matriz"].dropna().unique().tolist()),
            "campanhas": sorted(df_res["Campanha"].dropna().unique().tolist()),
            "laboratorios": sorted(df_res["Laboratorio"].dropna().unique().tolist()),
            "pontos_resultados": int(df_res["Ponto"].nunique()),
            "pontos_base": int(df_pts["Ponto"].nunique()),
            "parametros_resultados": int(df_res["Parametro"].nunique()),
            "parametros_cadastro": int(df_cad["Parametro"].nunique()),
        },
        "resultado_parse": {
            "rows_with_error": n_parse_err,
            "symbols": sym_counts,
        },
        "findings": [f.__dict__ for f in findings],
    }

    return report, findings, unmatched_df


def _load_inputs(base_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    xlsx_resultados = base_dir / DEFAULT_RESULTADOS
    xlsx_cadastro = base_dir / DEFAULT_CADASTRO

    if not xlsx_resultados.exists():
        raise FileNotFoundError(f"arquivo nao encontrado: {xlsx_resultados}")
    if not xlsx_cadastro.exists():
        raise FileNotFoundError(f"arquivo nao encontrado: {xlsx_cadastro}")

    df_res = pd.read_excel(xlsx_resultados, sheet_name=SHEET_RESULTADOS, dtype=str)
    df_pts = pd.read_excel(xlsx_resultados, sheet_name=SHEET_PONTOS, dtype=str)
    df_cad = pd.read_excel(xlsx_cadastro, dtype=str)
    return df_res, df_pts, df_cad


def _save_outputs(report: dict[str, Any], unmatched_df: pd.DataFrame) -> tuple[Path, Path | None]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"{ts}_validacao_meio_fisico_sam.json"
    csv_path = OUT_DIR / f"{ts}_parametros_sem_cadastro.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if not unmatched_df.empty:
        unmatched_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return json_path, csv_path

    return json_path, None


def _print_summary(report: dict[str, Any]) -> None:
    print("=" * 70)
    print("VALIDACAO PRE-MIGRACAO - MEIO FISICO (SAM)")
    print("=" * 70)
    print(f"Status: {report['status']}")
    print(f"Registros resultados: {report['shape']['resultados_rows']}")
    print(f"Matrizes: {report['uniques']['matrizes']}")
    print(f"Campanhas: {report['uniques']['campanhas']}")
    print(f"Laboratorios: {report['uniques']['laboratorios']}")
    print(f"Parse erros: {report['resultado_parse']['rows_with_error']}")
    print(f"Simbolos: {report['resultado_parse']['symbols']}")

    print("\nAchados:")
    if not report["findings"]:
        print("  - nenhum achado")
    else:
        for f in report["findings"]:
            print(f"  - [{f['severity']}] {f['check']}: {f['details']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador pre-migracao para Meio Fisico (SAM)")
    parser.add_argument("--base-dir", type=str, default=str(DEFAULT_BASE_DIR), help="Pasta com planilhas de migracao")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    try:
        df_res, df_pts, df_cad = _load_inputs(base_dir)
    except Exception as exc:
        print(f"ERRO ao carregar entradas: {exc}")
        return 2

    report, findings, unmatched_df = _build_report(df_res, df_pts, df_cad, base_dir)
    _print_summary(report)

    json_path, csv_path = _save_outputs(report, unmatched_df)
    print("\nEvidencias geradas:")
    print(f"  - {json_path}")
    if csv_path:
        print(f"  - {csv_path}")

    return 1 if any(f.severity == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
