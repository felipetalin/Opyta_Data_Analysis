from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_CODE = "BIOCOL001"
PROJECT_NAME = "Colider"

BIOS_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios")
ANALYSIS_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data_Analysis")
PROJECT_ROOT = (
    ANALYSIS_ROOT
    / "outputs"
    / "_project_scripts"
    / "BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider"
)
INVENTORY_DIR = PROJECT_ROOT / "inventory"


def _find_one(pattern: str) -> Path:
    matches = list(BIOS_ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    if len(matches) > 1:
        matches = sorted(matches, key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


DATA_WORKBOOK = _find_one(
    "*/Planilha/Migracao/Opyta-Bios-Ictio-2026_MIGRACAO_DE DADOS -version 4.xlsx"
)
SPECIES_WORKBOOK = _find_one(
    "*/Planilha/Migracao/Cadastro_especies_opyta_colider-ictio-2600812.xlsx"
)
CLIENT_OUTPUT_DIR = _find_one("*/Resultados/2026/Junho-2026/Planilha_aprovacao_analises")


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _norm_key(value) -> str:
    return _strip_accents(_norm_text(value)).lower()


def _is_missing_token(value) -> bool:
    key = _norm_key(value).replace(".", "").replace("-", "")
    return key in {"", "na", "nan", "none", "null", "ni", "n/i", "nao informado"}


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False).str.strip(),
        errors="coerce",
    )


def _tipo_base(value) -> str:
    txt = _norm_key(value)
    if "quanti" in txt:
        return "Quantitativa"
    if "quali" in txt:
        return "Qualitativa"
    return _norm_text(value) or "Nao informado"


def _sexo_padronizado(value) -> str:
    if _is_missing_token(value):
        return "Nao informado"
    txt = _norm_key(value)
    if txt in {"f", "femea", "fem", "female"}:
        return "Femea"
    if txt in {"m", "macho", "male"}:
        return "Macho"
    return _norm_text(value)


def _emg_codigo(value, sexo_value=None) -> str:
    if _is_missing_token(value):
        return ""
    txt = _strip_accents(_norm_text(value)).upper().replace(" ", "")
    if not txt:
        return ""
    match = re.search(r"([FM])\s*([1-4])", txt)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    match = re.search(r"(^|[^0-9])([1-4])([^0-9]|$)", txt)
    if match:
        sexo_txt = _sexo_padronizado(sexo_value)
        prefix = "F" if sexo_txt == "Femea" else "M" if sexo_txt == "Macho" else ""
        return f"{prefix}{match.group(2)}" if prefix else match.group(2)
    return txt


def _emg_estadio(code: str) -> str:
    if not code:
        return "Nao informado"
    stage = str(code)[-1]
    return {
        "1": "Repouso",
        "2": "Maturacao inicial",
        "3": "Maturacao avancada/maduro",
        "4": "Desovado/esgotado",
    }.get(stage, "Nao classificado")


def _emg_ordem(code: str) -> float:
    if not code:
        return np.nan
    stage = str(code)[-1]
    return float(stage) if stage in {"1", "2", "3", "4"} else np.nan


def _campanha_operacional(value) -> str:
    match = re.search(r"(C\d{3})", _norm_text(value))
    return match.group(1) if match else ""


def _load_campaign_map() -> pd.DataFrame:
    path = INVENTORY_DIR / "de_para_campanhas_biocol001_regra_aprovada.csv"
    df = pd.read_csv(path)
    return df[["campanha_operacional", "rotulo_canonico"]].drop_duplicates()


def _load_point_layer() -> pd.DataFrame:
    path = INVENTORY_DIR / "camada_operacional_pontos_biocol001.csv"
    return pd.read_csv(path)


def _load_species() -> pd.DataFrame:
    species = pd.read_excel(SPECIES_WORKBOOK, sheet_name="Especies")
    for col in ["Nome_Cientifico", "Origem", "Habito_Alimentar", "Estrategia_Reprodutiva"]:
        if col in species.columns:
            species[col] = species[col].map(_norm_text)
    keep = [
        "Nome_Cientifico",
        "Nome_Popular",
        "Ordem",
        "Familia",
        "Genero",
        "Autor_e_Ano",
        "Status_Ameaca_Estadual",
        "Status_Ameaca_Nacional",
        "Status_Ameaca_Global",
        "Origem",
        "Habito_Alimentar",
        "Estrategia_Reprodutiva",
        "Valor_Economico",
    ]
    keep = [col for col in keep if col in species.columns]
    return species[keep].drop_duplicates("Nome_Cientifico")


def _prepare_base() -> pd.DataFrame:
    resultados = pd.read_excel(DATA_WORKBOOK, sheet_name="Resultados_Ictiofauna")
    campanha_map = _load_campaign_map()
    point_layer = _load_point_layer()
    species = _load_species()

    df = resultados.copy()
    df.insert(0, "Linha_Fonte", np.arange(2, len(df) + 2))
    for col in ["Campanha", "Ponto", "Metodo_de_Captura", "Tipo_de_Amostragem", "Nome_Cientifico"]:
        df[col] = df[col].map(_norm_text)
    df["Linha_Sem_Taxon"] = df["Nome_Cientifico"].eq("")
    df = df[~df["Linha_Sem_Taxon"]].copy()

    df["Campanha_Operacional"] = df["Campanha"].map(_campanha_operacional)
    df = df.merge(campanha_map, left_on="Campanha_Operacional", right_on="campanha_operacional", how="left")
    df["Campanha_Canonica"] = df["rotulo_canonico"].combine_first(df["Campanha"])
    df = df.drop(columns=["campanha_operacional", "rotulo_canonico"])

    df["Tipo_Amostragem_Base"] = df["Tipo_de_Amostragem"].map(_tipo_base)
    df["Numero_de_Individuos_Original"] = _to_number(df["Numero_de_individuos"])
    df["CT_cm_Original"] = _to_number(df["CT_cm"])
    df["CP_cm_Original"] = _to_number(df["CP_cm"])
    df["PC_g_Original"] = _to_number(df["PC_g"])

    df["Numero_de_Individuos"] = df["Numero_de_Individuos_Original"].fillna(0)
    df["CT_cm_num"] = df["CT_cm_Original"]
    df["CP_cm_num"] = df["CP_cm_Original"]
    df["PC_g_individual"] = df["PC_g_Original"]
    df["Regra_Correcao_Biometria"] = ""
    df["Esforco_Linha"] = _to_number(df["Esforço"])
    df["Biomassa_g_linha"] = df["Numero_de_Individuos"] * df["PC_g_individual"]

    quant_mask = df["Tipo_Amostragem_Base"].eq("Quantitativa") & df["Esforco_Linha"].gt(0)
    df["CPUEn_linha"] = np.where(
        quant_mask,
        df["Numero_de_Individuos"] / df["Esforco_Linha"] * 100.0,
        np.nan,
    )
    df["CPUEb_linha"] = np.where(
        quant_mask & df["Biomassa_g_linha"].notna(),
        df["Biomassa_g_linha"] / df["Esforco_Linha"] * 100.0,
        np.nan,
    )

    df["Sexo_Raw"] = df["Sexo"].map(_norm_text)
    df["EMG_Raw"] = df["EMG"].map(_norm_text)
    df["Sexo_Padronizado"] = df["Sexo_Raw"].map(_sexo_padronizado)
    df["EMG_Codigo"] = [
        _emg_codigo(emg, sexo) for emg, sexo in zip(df["EMG_Raw"], df["Sexo_Raw"], strict=False)
    ]
    df["EMG_Estadio"] = df["EMG_Codigo"].map(_emg_estadio)
    df["EMG_Ordem"] = df["EMG_Codigo"].map(_emg_ordem)
    df["Tem_EMG_Informado"] = df["EMG_Codigo"].astype(str).str.len().gt(0)
    df["Evidencia_Reprodutiva_Forte"] = df["EMG_Codigo"].isin({"F3", "M3", "F4", "M4"})

    df = df.merge(point_layer, left_on="Ponto", right_on="ponto", how="left")
    df = df.drop(columns=["ponto"])
    df["Universo_Analise_Geral"] = df["incluir_analises_gerais"].eq("sim")

    df = df.merge(species, on="Nome_Cientifico", how="left")
    df["Codigo_Projeto"] = PROJECT_CODE
    df["Projeto"] = PROJECT_NAME
    return df


def _validations(base: pd.DataFrame) -> pd.DataFrame:
    sexo_informado = base["Sexo_Padronizado"].isin(["Femea", "Macho"])
    emg = base["Tem_EMG_Informado"]
    strong = base["Evidencia_Reprodutiva_Forte"]
    individuos = pd.to_numeric(base["Numero_de_Individuos"], errors="coerce")
    non_integer = individuos.notna() & ~np.isclose(individuos % 1, 0)
    corrected = base["Regra_Correcao_Biometria"].astype(str).str.len().gt(0)
    rows = [
        ("Linhas fonte", len(base), ""),
        ("Individuos fonte", float(base["Numero_de_Individuos"].sum()), ""),
        ("Especies fonte", base["Nome_Cientifico"].nunique(), ""),
        ("Campanhas canonicas", base["Campanha_Canonica"].nunique(), "Esperado: 69"),
        ("Pontos totais", base["Ponto"].nunique(), "Inclui marcacao e STP"),
        ("Pontos universo geral", base.loc[base["Universo_Analise_Geral"], "Ponto"].nunique(), "Esperado: 16"),
        ("Linhas com CP_cm", int(base["CP_cm_num"].notna().sum()), ""),
        ("Linhas com PC_g", int(base["PC_g_individual"].notna().sum()), ""),
        ("Linhas com correcao biometria/N", int(corrected.sum()), "V4 ja contem correcao na fonte"),
        ("Abundancia corrigida nas linhas corrigidas", float(base.loc[corrected, "Numero_de_Individuos"].sum()), ""),
        ("Linhas com Sexo F/M", int(sexo_informado.sum()), ""),
        ("Linhas com EMG informado", int(emg.sum()), ""),
        ("Abundancia com EMG informado", float(base.loc[emg, "Numero_de_Individuos"].sum()), ""),
        ("Linhas evidencia reprodutiva forte", int(strong.sum()), "F3/M3 + F4/M4"),
        ("Abundancia evidencia reprodutiva forte", float(base.loc[strong, "Numero_de_Individuos"].sum()), "F3/M3 + F4/M4"),
        ("Linhas sem camada operacional", int(base["camada_operacional"].isna().sum()), ""),
        ("Especies sem merge cadastro", int(base["Ordem"].isna().sum()), "Contagem de linhas, nao especies"),
        ("Linhas com Numero_de_Individuos decimal", int(non_integer.sum()), "Revisar fonte antes de produtos finais de abundancia"),
    ]
    return pd.DataFrame(rows, columns=["Item", "Valor", "Observacao"])


def _summaries(base: pd.DataFrame) -> dict[str, pd.DataFrame]:
    repro = base[base["Tem_EMG_Informado"]].copy()
    summaries: dict[str, pd.DataFrame] = {}
    summaries["Validacao"] = _validations(base)
    summaries["Repro_EMG_Especie"] = (
        repro.groupby(
            [
                "Nome_Cientifico",
                "Origem",
                "Estrategia_Reprodutiva",
                "Sexo_Padronizado",
                "EMG_Codigo",
                "EMG_Estadio",
                "EMG_Ordem",
            ],
            dropna=False,
        )
        .agg(
            Linhas=("Nome_Cientifico", "size"),
            Abundancia_Total=("Numero_de_Individuos", "sum"),
            Abundancia_Evidencia_Forte=("Evidencia_Reprodutiva_Forte", lambda s: base.loc[s.index, "Numero_de_Individuos"][s].sum()),
            Campanhas=("Campanha_Canonica", "nunique"),
            Pontos=("Ponto", "nunique"),
        )
        .reset_index()
        .sort_values(["Nome_Cientifico", "EMG_Ordem", "Sexo_Padronizado"], na_position="last")
    )
    summaries["Repro_Ponto"] = (
        repro.groupby(["Ponto", "camada_operacional", "incluir_analises_gerais"], dropna=False)
        .agg(
            Linhas_EMG=("Nome_Cientifico", "size"),
            Especies_EMG=("Nome_Cientifico", "nunique"),
            Abundancia_Total_EMG=("Numero_de_Individuos", "sum"),
            Abundancia_Evidencia_Forte=("Evidencia_Reprodutiva_Forte", lambda s: base.loc[s.index, "Numero_de_Individuos"][s].sum()),
        )
        .reset_index()
    )
    summaries["Repro_Campanha"] = (
        repro.groupby(["Campanha_Canonica"], dropna=False)
        .agg(
            Linhas_EMG=("Nome_Cientifico", "size"),
            Especies_EMG=("Nome_Cientifico", "nunique"),
            Abundancia_Total_EMG=("Numero_de_Individuos", "sum"),
            Abundancia_Evidencia_Forte=("Evidencia_Reprodutiva_Forte", lambda s: base.loc[s.index, "Numero_de_Individuos"][s].sum()),
        )
        .reset_index()
        .sort_values("Campanha_Canonica")
    )
    summaries["Sexo_EMG_Distribuicao"] = (
        base.groupby(["Sexo_Padronizado", "EMG_Codigo", "EMG_Estadio"], dropna=False)
        .agg(
            Linhas=("Nome_Cientifico", "size"),
            Abundancia=("Numero_de_Individuos", "sum"),
            Especies=("Nome_Cientifico", "nunique"),
        )
        .reset_index()
        .sort_values(["Sexo_Padronizado", "EMG_Codigo"])
    )
    return summaries


def _save_outputs(base: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> None:
    out_xlsx = CLIENT_OUTPUT_DIR / "base_reproducao_biocol001_estrategia_porto_estrela_R03_v4.xlsx"
    out_csv = INVENTORY_DIR / "base_reproducao_biocol001_estrategia_porto_estrela_R03_v4.csv"
    base.to_csv(out_csv, index=False, encoding="utf-8-sig")

    selected_cols = [
        "Linha_Fonte",
        "Codigo_Projeto",
        "Campanha",
        "Campanha_Canonica",
        "Ponto",
        "camada_operacional",
        "incluir_analises_gerais",
        "Metodo_de_Captura",
        "Tipo_Amostragem_Base",
        "Nome_Cientifico",
        "Numero_de_Individuos",
        "Numero_de_Individuos_Original",
        "CT_cm_num",
        "CT_cm_Original",
        "CP_cm_num",
        "CP_cm_Original",
        "PC_g_individual",
        "PC_g_Original",
        "Biomassa_g_linha",
        "Regra_Correcao_Biometria",
        "Sexo_Raw",
        "Sexo_Padronizado",
        "EMG_Raw",
        "EMG_Codigo",
        "EMG_Estadio",
        "EMG_Ordem",
        "Tem_EMG_Informado",
        "Evidencia_Reprodutiva_Forte",
        "Origem",
        "Habito_Alimentar",
        "Estrategia_Reprodutiva",
    ]
    selected_cols = [col for col in selected_cols if col in base.columns]
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summaries["Validacao"].to_excel(writer, sheet_name="Validacao", index=False)
        base[selected_cols].to_excel(writer, sheet_name="Base_Reproducao", index=False)
        for sheet_name, df in summaries.items():
            if sheet_name == "Validacao":
                continue
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    print(out_xlsx)
    print(out_csv)


def main() -> None:
    base = _prepare_base()
    summaries = _summaries(base)
    _save_outputs(base, summaries)


if __name__ == "__main__":
    main()
