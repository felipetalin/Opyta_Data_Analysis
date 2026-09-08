"""Preflight de isolamento dos filtros - ITAGUA001 / Ictiofauna / C029.

Somente leitura: carrega dados via `_load_ictio_partial_df` para cada
empreendimento e confirma que:

1. a campanha alvo (C029-2026-08-SC) nao vaza outras campanhas;
2. o filtro de empreendimento nao vaza outros empreendimentos;
3. um rotulo de campanha inexistente (o C029-2026-07-SC citado no briefing,
   que pertence a Avifauna/Mastofauna) retorna vazio para Ictiofauna, em vez
   de cair silenciosamente em outra campanha;
4. os 32 pontos cadastrados aparecem no dataset, incluindo os pontos com
   esforco valido e captura zero (nao apenas os pontos com captura).

Nao gera nenhum produto e nao escreve no Supabase.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "src" / "opyta_analysis").exists()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from opyta_analysis.pipelines.diagnostico.ictio_partial import (  # noqa: E402
    _load_ictio_partial_df,
    _subset_emp,
)

PROJECT_ID = 165
ENV_FILE = str(ROOT / ".env")
CAMPANHA_ALVO = "C029-2026-08-SC"
CAMPANHA_BRIEFING_DIVERGENTE = "C029-2026-07-SC"  # rotulo de Avifauna/Mastofauna, nao de Ictiofauna
EMPREENDIMENTOS = ["Jacaré", "Senhora do Porto", "Dores de Guanhães", "Fortuna II"]

# Pontos cadastrados na campanha por empreendimento (conferido via Supabase, somente leitura)
PONTOS_ESPERADOS = {
    "Jacaré": 9,
    "Senhora do Porto": 8,
    "Dores de Guanhães": 7,
    "Fortuna II": 8,
}


def main() -> int:
    report: dict = {"campanha_alvo": CAMPANHA_ALVO, "checks": []}
    ok = True

    # 0) Controle negativo: rotulo divergente do briefing nao deve retornar dados.
    df_wrong = _load_ictio_partial_df(
        project_id=PROJECT_ID, campanha_alvo=CAMPANHA_BRIEFING_DIVERGENTE, env_file=ENV_FILE
    )
    check0 = {
        "check": "controle_negativo_rotulo_briefing",
        "campanha_testada": CAMPANHA_BRIEFING_DIVERGENTE,
        "linhas": int(len(df_wrong)),
        "esperado": "0 linhas (rotulo pertence a Avifauna/Mastofauna, nao a Ictiofauna)",
        "passou": bool(df_wrong.empty),
    }
    report["checks"].append(check0)
    ok = ok and check0["passou"]

    # 1) Carrega a campanha real uma vez (dataset do projeto inteiro, ainda sem filtrar empreendimento).
    df_full = _load_ictio_partial_df(project_id=PROJECT_ID, campanha_alvo=CAMPANHA_ALVO, env_file=ENV_FILE)
    campanhas_no_df = sorted(df_full["nome_campanha"].dropna().astype(str).unique().tolist()) if not df_full.empty else []
    check1 = {
        "check": "isolamento_campanha",
        "linhas_totais": int(len(df_full)),
        "campanhas_no_dataset": campanhas_no_df,
        "passou": campanhas_no_df in ([], [CAMPANHA_ALVO]),
    }
    report["checks"].append(check1)
    ok = ok and check1["passou"]

    pontos_totais_no_df = sorted(df_full["nome_ponto"].dropna().astype(str).unique().tolist()) if not df_full.empty else []
    check_pontos_totais = {
        "check": "total_pontos_projeto_na_campanha",
        "n_pontos": len(pontos_totais_no_df),
        "esperado": sum(PONTOS_ESPERADOS.values()),
        "passou": len(pontos_totais_no_df) == sum(PONTOS_ESPERADOS.values()),
    }
    report["checks"].append(check_pontos_totais)
    ok = ok and check_pontos_totais["passou"]

    # 2) Por empreendimento: isolamento do filtro + contagem de pontos (com e sem captura).
    por_emp = []
    todos_pontos_por_emp: dict[str, set[str]] = {}
    for pch in EMPREENDIMENTOS:
        df_emp = _subset_emp(df_full, pch)
        emps_no_df = sorted(df_emp["empreendimento"].dropna().astype(str).unique().tolist()) if not df_emp.empty else []
        pontos = sorted(df_emp["nome_ponto"].dropna().astype(str).unique().tolist())
        todos_pontos_por_emp[pch] = set(pontos)
        # Um ponto pode ter mais de um esforco (metodo); so conta como "zero
        # captura" quando NENHUM esforco do ponto teve captura.
        pontos_com_captura = (
            set(df_emp.loc[~df_emp["amostragem_zero_captura"], "nome_ponto"].dropna().astype(str))
            if not df_emp.empty
            else set()
        )
        n_com_captura = len(set(pontos) & pontos_com_captura)
        n_zero = len(pontos) - n_com_captura
        item = {
            "empreendimento": pch,
            "isolamento_ok": emps_no_df in ([], [pch]),
            "empreendimentos_no_subset": emps_no_df,
            "n_pontos": len(pontos),
            "n_pontos_esperado": PONTOS_ESPERADOS[pch],
            "n_pontos_zero_captura": n_zero,
            "n_pontos_com_captura": n_com_captura,
            "n_especies": int(df_emp["nome_cientifico"].nunique()) if not df_emp.empty else 0,
            "passou": emps_no_df in ([], [pch]) and len(pontos) == PONTOS_ESPERADOS[pch],
        }
        por_emp.append(item)
        ok = ok and item["passou"]
    report["por_empreendimento"] = por_emp

    # 3) Isolamento cruzado: nenhum ponto deve aparecer em mais de um empreendimento.
    vistos: dict[str, str] = {}
    colisoes = []
    for pch, pontos in todos_pontos_por_emp.items():
        for p in pontos:
            if p in vistos and vistos[p] != pch:
                colisoes.append({"ponto": p, "empreendimentos": [vistos[p], pch]})
            vistos[p] = pch
    check_colisao = {
        "check": "sem_colisao_de_pontos_entre_empreendimentos",
        "colisoes": colisoes,
        "passou": len(colisoes) == 0,
    }
    report["checks"].append(check_colisao)
    ok = ok and check_colisao["passou"]

    report["preflight_ok"] = ok
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
