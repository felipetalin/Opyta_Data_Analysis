"""
B11 - Sintese executiva (xlsx consolidado por matriz).

Por matriz, gera 1 xlsx com abas:
  - Resumo
  - Pct_Violacao (do B4)
  - Sazonal_MannWhitney (do B9)
  - Indice (IQA/IET para Sup; IQASB parcial para Sub; m-PEL-q para Sed)
  - Pontos_Criticos (top 5 pontos com maior fracao de violacoes)
"""

from __future__ import annotations

import os

import re
from pathlib import Path

import numpy as np
import pandas as pd

CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
SRC = CLIENT_ROOT / "Migração" / "Físico" / "Resultados_Meio_Fisico.xlsx"
CAD = CLIENT_ROOT / "Migração" / "Físico" / "cadastro_parametros_opyta.xlsx"
OUT_ROOT = CLIENT_ROOT / "Resultados" / "Meio_físico"

MATRIZES = {
    "Água Superficial": {"sub": "Superficial", "indice_xlsx": ["05_IQA_Tabela.xlsx", "06_IET_Tabela.xlsx"]},
    "Água Subterrânea": {"sub": "Subterrânea", "indice_xlsx": ["07_IQASB_parcial_Tabela.xlsx"]},
    "Sedimento": {"sub": "Sedimentos", "indice_xlsx": ["08_mPELq_Tabela.xlsx"]},
}


def parse(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return None, ""
    s = str(v).strip()
    sinal = ""
    for sym in ("<=", ">=", "<", ">"):
        if s.startswith(sym):
            sinal = sym
            s = s[len(sym):].strip()
            break
    s = s.replace(",", ".").replace(" ", "")
    try: return float(s), sinal
    except ValueError: return None, sinal


def _num_or_none(v):
    if v is None or pd.isna(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _violou(valor, sinal, limite_min, limite_max):
    if valor is None:
        return False
    if sinal in ("<", "<="):
        return False
    if limite_min is not None and valor < limite_min:
        return True
    if limite_max is not None and valor > limite_max:
        return True
    return False


def _latest_generated(path: Path) -> Path:
    alt = path.with_name(path.stem + "_NEW" + path.suffix)
    existing = [p for p in (path, alt) if p.exists()]
    if not existing:
        return path
    return max(existing, key=lambda p: p.stat().st_mtime)


def main():
    df = pd.read_excel(SRC, sheet_name="Resultados_Meio_Fisico", dtype=str)
    for c in ["Matriz", "Parametro", "Ponto", "Campanha"]:
        df[c] = df[c].astype(str).str.strip()

    for matriz, cfg in MATRIZES.items():
        out_dir = OUT_ROOT / cfg["sub"]
        out_dir.mkdir(parents=True, exist_ok=True)
        d = df[df["Matriz"] == matriz].copy()
        n_amostras = len(d)
        n_pontos = d["Ponto"].nunique()
        n_camp = d["Campanha"].nunique()
        n_params = d["Parametro"].nunique()
        resumo = pd.DataFrame([{
            "Matriz": matriz,
            "N_amostras": n_amostras,
            "N_pontos": n_pontos,
            "N_campanhas": n_camp,
            "N_parametros": n_params,
        }])

        # Pct_Violacao
        pv_path = _latest_generated(out_dir / "04_Pct_Violacao.xlsx")
        df_pv = pd.read_excel(pv_path) if pv_path.exists() else pd.DataFrame()

        # Sazonal
        sz_path = _latest_generated(out_dir / "09_Sazonal_MannWhitney.xlsx")
        df_sz = pd.read_excel(sz_path) if sz_path.exists() else pd.DataFrame()

        # Indice
        indices = []
        for fname in cfg["indice_xlsx"]:
            p = out_dir / fname
            p = _latest_generated(p)
            if p.exists():
                t = pd.read_excel(p)
                t.insert(0, "Origem", fname)
                indices.append(t)
        df_idx = pd.concat(indices, ignore_index=True) if indices else pd.DataFrame()

        # Pontos criticos: ranking por pontos com maior numero de violacoes em B4 desnormalizado.
        pontos_critic = pd.DataFrame()
        if not df_pv.empty:
            limite_map = {}
            for _, row in df_pv.iterrows():
                if "Limite_Min" in df_pv.columns or "Limite_Max" in df_pv.columns:
                    limite_min = _num_or_none(row.get("Limite_Min"))
                    limite_max = _num_or_none(row.get("Limite_Max"))
                else:
                    limite_min = None
                    limite_max = _num_or_none(row.get("VMP_ref"))
                if limite_min is None and limite_max is None:
                    continue
                limite_map[row["Parametro"]] = (limite_min, limite_max)
            rows = []
            parsed = d["Resultado"].map(parse)
            d["_v"] = parsed.map(lambda t: t[0])
            d["_sinal"] = parsed.map(lambda t: t[1])
            for ponto, sub_p in d.groupby("Ponto"):
                nv = 0; nt = 0
                for _, r in sub_p.iterrows():
                    if pd.isna(r["_v"]):
                        continue
                    if r["Parametro"] not in limite_map:
                        continue
                    limite_min, limite_max = limite_map[r["Parametro"]]
                    nt += 1
                    if _violou(float(r["_v"]), r["_sinal"], limite_min, limite_max):
                        nv += 1
                if nt > 0:
                    rows.append({"Ponto": ponto, "N_amostras": nt,
                                 "N_violacoes": nv, "Pct_Violacao": nv/nt*100})
            if rows:
                pontos_critic = pd.DataFrame(rows).sort_values("Pct_Violacao", ascending=False).head(10)

        xlsx_out = out_dir / "11_Sintese_Executiva.xlsx"
        if xlsx_out.exists():
            xlsx_out = xlsx_out.with_name(xlsx_out.stem + "_NEW.xlsx")
        with pd.ExcelWriter(xlsx_out, engine="openpyxl") as w:
            resumo.to_excel(w, sheet_name="Resumo", index=False)
            if not df_pv.empty: df_pv.to_excel(w, sheet_name="Pct_Violacao", index=False)
            if not df_sz.empty: df_sz.to_excel(w, sheet_name="Sazonal_MannWhitney", index=False)
            if not df_idx.empty: df_idx.to_excel(w, sheet_name="Indice", index=False)
            if not pontos_critic.empty: pontos_critic.to_excel(w, sheet_name="Pontos_Criticos", index=False)
        print(f"  [{matriz}] sintese -> {xlsx_out.name}")
    print("[B11] OK")


if __name__ == "__main__":
    main()
