"""
Resumo Tecnico Analitico (TXT por matriz + consolidado).

Le todos os xlsx gerados em B4-B11 e escreve 4 arquivos:
  Resultados/Meio_físico/RESUMO_Aguas_Superficiais.txt
  Resultados/Meio_físico/RESUMO_Aguas_Subterraneas.txt
  Resultados/Meio_físico/RESUMO_Sedimentos.txt
  Resultados/Meio_físico/RESUMO_CONSOLIDADO.txt

Linguagem tecnica ambiental, paragrafos fluidos, sem causalidade absoluta.
"""

from __future__ import annotations

import os

from pathlib import Path

import numpy as np
import pandas as pd

CLIENT_ROOT = Path(os.environ.get("OPYTA_MF_CLIENT_ROOT", r"G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Ferreira Rocha/SAM Metais/Produtos"))
OUT_ROOT = CLIENT_ROOT / "Resultados" / "Meio_físico"


def fmt_pct(p): return f"{p:.1f}%".replace(".", ",")
def fmt(v, n=2): return f"{v:.{n}f}".replace(".", ",")


def ler(path):
    return pd.read_excel(path) if path.exists() else pd.DataFrame()


def secao_contextualizacao(matriz, sub):
    pv = ler(OUT_ROOT / sub / "11_Sintese_Executiva.xlsx")
    res = ler(OUT_ROOT / sub / "11_Sintese_Executiva.xlsx") if False else None
    # ler resumo da aba "Resumo"
    p = OUT_ROOT / sub / "11_Sintese_Executiva.xlsx"
    if not p.exists():
        # tentar _NEW
        p = OUT_ROOT / sub / "11_Sintese_Executiva_NEW.xlsx"
    try:
        df = pd.read_excel(p, sheet_name="Resumo")
        r = df.iloc[0]
        n_amostras, n_pontos, n_camp, n_params = r["N_amostras"], r["N_pontos"], r["N_campanhas"], r["N_parametros"]
    except Exception:
        n_amostras = n_pontos = n_camp = n_params = "—"
    txt = (
        f"1. CONTEXTUALIZACAO\n\n"
        f"A presente analise refere-se ao monitoramento de qualidade de {matriz.lower()} no contexto do "
        f"empreendimento SAM Metais, sob responsabilidade da Ferreira Rocha. O conjunto amostral consolidou "
        f"{n_amostras} resultados analiticos distribuidos em {n_pontos} pontos de coleta e {n_camp} campanhas "
        f"de monitoramento, contemplando {n_params} parametros entre fisico-quimicos, microbiologicos e metais. "
        f"As campanhas abrangem os periodos hidrologicos de seca e chuva, permitindo avaliacao integrada do "
        f"comportamento sazonal e espacial dos parametros monitorados. A avaliacao de conformidade utilizou os "
        f"valores maximos permitidos (VMP) das resolucoes CONAMA aplicaveis ao tipo de matriz, conforme "
        f"protocolo metodologico do diagnostico ambiental."
    )
    return txt


def secao_conformidade(matriz, sub):
    p = OUT_ROOT / sub / "04_Pct_Violacao.xlsx"
    df = ler(p)
    if df.empty:
        return "2. CONFORMIDADE\n\nNao foram identificados parametros com VMP de referencia para avaliacao de conformidade."
    df = df.sort_values("Pct_Violacao", ascending=False)
    n_sem_viol = (df["Pct_Violacao"] == 0).sum()
    n_baixo = ((df["Pct_Violacao"] > 0) & (df["Pct_Violacao"] <= 25)).sum()
    n_med = ((df["Pct_Violacao"] > 25) & (df["Pct_Violacao"] <= 50)).sum()
    n_alto = (df["Pct_Violacao"] > 50).sum()
    top = df.head(5)
    top_txt = "; ".join(f"{r['Parametro']} ({fmt_pct(r['Pct_Violacao'])})" for _, r in top.iterrows())
    txt = (
        "2. CONFORMIDADE (DESEMPENHO PERANTE OS PADROES LEGAIS)\n\n"
        f"A analise de conformidade contemplou {len(df)} parametros com VMP regulatorio aplicavel. "
        f"Identificaram-se {int(n_sem_viol)} parametros em plena conformidade ao longo de todo o periodo monitorado, "
        f"{int(n_baixo)} com taxa de violacao baixa (ate 25%), {int(n_med)} com taxa moderada (25-50%) e "
        f"{int(n_alto)} com taxa elevada (acima de 50%). Os parametros com maiores frequencias relativas de "
        f"violacao foram, em ordem decrescente: {top_txt}. O padrao observado sugere a presenca de pressoes "
        f"ambientais especificas que merecem atencao redobrada, sem prejuizo da avaliacao integrada com os "
        f"demais indicadores."
    )
    return txt


def secao_sazonal(matriz, sub):
    p = OUT_ROOT / sub / "09_Sazonal_MannWhitney.xlsx"
    df = ler(p)
    if df.empty:
        return "3. COMPORTAMENTO SAZONAL\n\nNao foi possivel avaliar comportamento sazonal."
    sig = df[df["p_valor"] < 0.05]
    n_sig = len(sig); n_tot = len(df)
    if n_sig == 0:
        body = (
            f"Nao foram observadas diferencas estatisticamente significativas (p < 0,05) entre os periodos de "
            f"seca e chuva para nenhum dos {n_tot} parametros testados pelo teste de Mann-Whitney."
        )
    else:
        top = sig.head(5)
        det = []
        for _, r in top.iterrows():
            sentido = "elevou-se" if r["Delta_pct"] > 0 else "reduziu-se"
            det.append(f"{r['Parametro']} (mediana {sentido} em {fmt_pct(abs(r['Delta_pct']))} entre seca e chuva, p={fmt(r['p_valor'], 3)})")
        body = (
            f"O teste nao-parametrico de Mann-Whitney revelou diferencas estatisticamente significativas "
            f"(p < 0,05) entre seca e chuva em {n_sig} de {n_tot} parametros analisados ({fmt_pct(n_sig/n_tot*100)}). "
            f"Entre as variacoes mais expressivas destacam-se: " + "; ".join(det) + ". "
            f"Tais variacoes refletem influencias hidrologicas e processos de diluicao, lixiviacao e remobilizacao "
            f"caracteristicos do regime pluviometrico regional."
        )
    return "3. COMPORTAMENTO SAZONAL (SECA x CHUVA)\n\n" + body


def secao_espacial(matriz, sub):
    p = OUT_ROOT / sub / "11_Sintese_Executiva.xlsx"
    if not p.exists():
        p = OUT_ROOT / sub / "11_Sintese_Executiva_NEW.xlsx"
    try:
        df = pd.read_excel(p, sheet_name="Pontos_Criticos")
    except Exception:
        df = pd.DataFrame()
    if df.empty:
        return "4. DISTRIBUICAO ESPACIAL\n\nNao ha dados consolidados de distribuicao espacial."
    top = df.head(5)
    det = "; ".join(f"{r['Ponto']} ({fmt_pct(r['Pct_Violacao'])} de violacoes em {int(r['N_amostras'])} analises)"
                    for _, r in top.iterrows())
    txt = (
        "4. DISTRIBUICAO ESPACIAL\n\n"
        f"A ordenacao dos pontos amostrais segundo a frequencia relativa de inconformidades indica que os pontos "
        f"com maior concentracao de desvios foram: {det}. Esse comportamento sugere influencia diferenciada de "
        f"fontes potenciais de pressao ambiental sobre setores especificos da area monitorada e justifica a "
        f"manutencao desses pontos no escopo de monitoramento continuado, com eventual densificacao espacial em "
        f"futuras campanhas."
    )
    return txt


def secao_indices(matriz, sub):
    if matriz == "Água Superficial":
        df_iqa = ler(OUT_ROOT / sub / "05_IQA_Tabela.xlsx")
        df_iet = ler(OUT_ROOT / sub / "06_IET_Tabela.xlsx")
        partes = []
        if not df_iqa.empty:
            med = df_iqa["IQA"].mean(); mn = df_iqa["IQA"].min(); mx = df_iqa["IQA"].max()
            classes = df_iqa["Classe"].value_counts().to_dict()
            partes.append(
                f"O Indice de Qualidade da Agua (IQA-CETESB) apresentou valor medio de {fmt(med, 1)} "
                f"(amplitude {fmt(mn, 1)}-{fmt(mx, 1)}), com distribuicao das amostras nas seguintes classes: "
                + ", ".join(f"{c} ({n})" for c, n in classes.items()) + "."
            )
        if not df_iet.empty:
            df_iet_v = df_iet.dropna(subset=["IET"])
            if not df_iet_v.empty:
                med = df_iet_v["IET"].mean()
                classes = df_iet_v["Classe"].value_counts().to_dict()
                partes.append(
                    f"O Indice de Estado Trofico (IET-Lamparelli) registrou valor medio de {fmt(med, 1)}, "
                    f"com classificacao predominante em " + ", ".join(f"{c} ({n})" for c, n in classes.items()) + "."
                )
        body = " ".join(partes) if partes else "Indices nao calculados."
    elif matriz == "Água Subterrânea":
        df = ler(OUT_ROOT / sub / "07_IQASB_parcial_Tabela.xlsx")
        if df.empty:
            body = "Indice IQASB nao calculado."
        else:
            med = df["IQASB_parcial"].mean()
            classes = df["Classe"].value_counts().to_dict()
            body = (
                f"O IQASB foi calculado em sua versao PARCIAL, utilizando 4 dos 5 parametros classicos do indice "
                f"(pH, OD, condutividade eletrica e nitrato), com pesos renormalizados em razao da ausencia do "
                f"sulfato no escopo analitico. O valor medio resultante foi de {fmt(med, 1)}, com distribuicao "
                f"das amostras nas classes: " + ", ".join(f"{c} ({n})" for c, n in classes.items()) + ". "
                f"Os resultados devem ser interpretados como aproximacao da qualidade integrada das aguas subterraneas, "
                f"sem prejuizo da analise parametro a parametro perante os VMP da Resolucao CONAMA 396/2008."
            )
    else:  # Sedimento
        df = ler(OUT_ROOT / sub / "08_mPELq_Tabela.xlsx")
        if df.empty:
            body = "Indice m-PEL-q nao calculado."
        else:
            med = df["m_PEL_q"].mean()
            classes = df["Classe"].value_counts().to_dict()
            body = (
                f"O indice m-PEL-q (media das razoes concentracao/Nivel 2 da Resolucao CONAMA 454/2012), "
                f"calculado a partir dos oito metais regulamentados (As, Cd, Cr, Cu, Pb, Hg, Ni e Zn), apresentou "
                f"valor medio de {fmt(med, 3)}, com distribuicao das amostras nas classes: "
                + ", ".join(f"{c} ({n})" for c, n in classes.items()) + ". "
                f"Esse indice constitui medida sintetica do potencial de toxicidade integrada dos sedimentos avaliados."
            )
    return "5. INDICES INTEGRADOS DE QUALIDADE\n\n" + body


def secao_integrada(matriz, sub):
    txt = (
        "6. AVALIACAO INTEGRADA\n\n"
        "A interpretacao integrada dos resultados deve considerar de forma conjunta os tres eixos analiticos: "
        "(i) o cumprimento dos padroes legais aplicaveis (conformidade), (ii) o comportamento sazonal e espacial "
        "dos parametros e (iii) os indices sinteticos de qualidade ambiental. A convergencia entre indicadores "
        "fortalece a robustez do diagnostico, enquanto eventuais divergencias entre eles - como, por exemplo, "
        "violacoes pontuais de VMP em parametros isolados acompanhadas de indices integrados favoraveis - "
        "devem ser examinadas a luz de fatores naturais, hidrologicos e operacionais ja documentados no "
        "diagnostico ambiental da area de influencia."
    )
    return txt


def secao_conclusao(matriz, sub):
    txt = (
        "7. CONCLUSAO\n\n"
        f"Os resultados do monitoramento da matriz {matriz.lower()} indicam um quadro geral compativel com o "
        f"esperado para a area de influencia do empreendimento, com a maior parcela dos parametros e pontos "
        f"em conformidade aos respectivos padroes legais. As inconformidades pontuais, quando presentes, "
        f"apresentam padrao concentrado em parametros e/ou setores especificos que ja se encontram identificados "
        f"no escopo desta avaliacao. Recomenda-se a manutencao do plano de monitoramento, com atencao especial "
        f"aos parametros e pontos destacados nas secoes anteriores, alem da avaliacao de medidas adicionais "
        f"de gestao ambiental caso o padrao observado se mantenha em futuras campanhas."
    )
    return txt


def secao_diretrizes():
    return (
        "8. DIRETRIZES PARA REDACAO DE RELATORIO\n\n"
        "- Manter linguagem tecnica neutra, evitando afirmacoes de causalidade absoluta sem comprovacao analitica.\n"
        "- Sempre referenciar a base legal aplicada (CONAMA 357/2005, 396/2008 ou 454/2012, conforme matriz).\n"
        "- Reportar os indices integrados (IQA, IET, IQASB, m-PEL-q) com a respectiva classificacao e advertencias "
        "metodologicas (e.g., IQASB parcial pela ausencia de sulfato).\n"
        "- Distinguir conformidade parametro-a-parametro (binaria, perante VMP) da avaliacao integrada por indices.\n"
        "- Evitar inferir tendencias temporais com base em apenas duas campanhas; tratar diferencas seca/chuva "
        "como indicacoes preliminares sujeitas a confirmacao em campanhas subsequentes.\n"
        "- Considerar limites de quantificacao (LQ) no julgamento de nao-detecoes, preservando rastreabilidade analitica."
    )


def secao_saida(matriz, sub, txt_path):
    return (
        "9. SAIDA E REPRODUTIBILIDADE\n\n"
        f"Pasta de outputs: Resultados/Meio_físico/{sub}/\n"
        f"Tabelas-fonte: 02_Conformidade.xlsx, 04_Pct_Violacao.xlsx, "
        f"09_Sazonal_MannWhitney.xlsx, indices (05/06/07/08 conforme matriz) e 11_Sintese_Executiva.xlsx.\n"
        f"Graficos: 03_*.png (por parametro), 04_Pct_Violacao.png, indices e 09_Sazonal_Boxplots_top12.png.\n"
        f"Arquivo deste resumo: {txt_path.name}"
    )


def gerar_resumo(matriz, sub):
    out_path = OUT_ROOT / f"RESUMO_{sub.replace('Subterrânea','Subterraneas').replace('Superficial','Superficiais').replace('Sedimentos','Sedimentos')}.txt"
    # nomes mais corretos
    nome_map = {
        "Superficial": "Aguas_Superficiais",
        "Subterrânea": "Aguas_Subterraneas",
        "Sedimentos": "Sedimentos",
    }
    out_path = OUT_ROOT / f"RESUMO_{nome_map[sub]}.txt"
    blocos = [
        f"RESUMO TECNICO ANALITICO - {matriz.upper()}",
        "Diagnostico SAM Metais | Ferreira Rocha | Opyta\n",
        secao_contextualizacao(matriz, sub),
        secao_conformidade(matriz, sub),
        secao_sazonal(matriz, sub),
        secao_espacial(matriz, sub),
        secao_indices(matriz, sub),
        secao_integrada(matriz, sub),
        secao_conclusao(matriz, sub),
        secao_diretrizes(),
        secao_saida(matriz, sub, out_path),
    ]
    out_path.write_text("\n\n".join(blocos) + "\n", encoding="utf-8")
    return out_path


def main():
    paths = []
    for matriz, sub in [("Água Superficial", "Superficial"),
                        ("Água Subterrânea", "Subterrânea"),
                        ("Sedimento", "Sedimentos")]:
        p = gerar_resumo(matriz, sub)
        paths.append(p)
        print(f"  [OK] {p.name}")

    # Consolidado
    consolidado = OUT_ROOT / "RESUMO_CONSOLIDADO.txt"
    header = ("RESUMO TECNICO ANALITICO CONSOLIDADO\nDiagnostico Meio Fisico SAM Metais | Ferreira Rocha | Opyta\n"
              "Inclui Aguas Superficiais, Aguas Subterraneas e Sedimentos.\n")
    partes = [header]
    for p in paths:
        partes.append("=" * 80)
        partes.append(p.read_text(encoding="utf-8"))
    consolidado.write_text("\n".join(partes) + "\n", encoding="utf-8")
    print(f"  [OK] {consolidado.name}")


if __name__ == "__main__":
    main()
