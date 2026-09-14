from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform
from sqlalchemy import create_engine, text


PROJECT_CODE = "BIOCOL001"
ANALYSIS_ROOT = Path(r"G:\Meu Drive\Opyta\Opyta_Data_Analysis")
BIOS_ROOT = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios")
PROJECT_ROOT = (
    ANALYSIS_ROOT
    / "outputs"
    / "_project_scripts"
    / "BIOCOL001__monitoramento_e_resgate_da_ictiofauna_uhe_colider"
)
INVENTORY_DIR = PROJECT_ROOT / "inventory"
OUTPUT_ROOT = Path(
    r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Bios\Colíder\Resultados\2026\Junho-2026"
)
RUN_LABEL = "R02_BIOPOR001_template"
OUT_DIR = OUTPUT_ROOT / "BIOCOL001_ictiofauna_produtos_maduros_R02_BIOPOR001_template"
BASE_DIR = OUT_DIR / "bases_finais"
FIG_DIR = OUT_DIR / "figuras"
OFFICIAL_DIR = OUT_DIR / "produtos_oficiais"

PALETTE = {
    "primary": "#002060",
    "secondary": "#5B9BD5",
    "highlight": "#1F4E79",
    "light": "#DBE5F1",
    "orange": "#D4672A",
    "green": "#6BA547",
    "red": "#B75D69",
    "gray": "#6C757D",
    "grid": "#D9D9D9",
}
ALT_PALETTE = [
    "#2E6EA6",
    "#D4672A",
    "#6BA547",
    "#7B4EA3",
    "#C9A227",
    "#4E9A99",
    "#B75D69",
    "#6C757D",
    "#A6CEE3",
    "#FDBF6F",
]
FIGSIZE_WIDE = (18, 10.2)
FIGSIZE_PANEL = (18, 11.2)
DPI = 300
FAMILY_OVERRIDES_BY_GENUS = {
    "Deuterodon": "Acestrorhamphidae",
    "Astyanax": "Acestrorhamphidae",
    "Brachychalcinus": "Acestrorhamphidae",
    "Hemigrammus": "Acestrorhamphidae",
    "Hyphessobrycon": "Acestrorhamphidae",
    "Jupiaba": "Acestrorhamphidae",
    "Moenkhausia": "Acestrorhamphidae",
    "Thayeria": "Acestrorhamphidae",
    "Holopristis": "Acestrorhamphidae",
    "Megalamphodus": "Acestrorhamphidae",
    "Bario": "Acestrorhamphidae",
    "Bryconamericus": "Stevardiidae",
    "Caiapobrycon": "Stevardiidae",
    "Gymnorhamphichthys": "Rhamphichthyidae",
    "Hypopygus": "Hypopomidae",
    "Pyrrhulina": "Lebiasinidae",
}
SPECIES_NAME_OVERRIDES = {
    "Crenicichla acutirostris": "Lugubria acutirostris",
    "Crenicichla lugubris": "Lugubria lugubris",
    "Crenicichla regani": "Wallaciia regani",
    "Crenicichla strigata": "Lugubria strigata",
    "Hemigrammus ocellifer": "Holopristis ocellifera",
    "Hyphessobrycon bentosi": "Megalamphodus bentosi",
    "Moenkhausia collettii": "Hemigrammus collettii",
    "Moenkhausia oligolepis": "Bario oligolepis",
    "Squaliforma emarginata": "Aphanotorulus emarginatus",
}
STATE_THREAT_STATUS_MT = "Sem lista estadual oficial vigente (MT)"
NATIONAL_NOT_LISTED = "Nao listada"
GLOBAL_NOT_EVALUATED = "NE"
THREATENED_CODES = {"VU", "EN", "CR", "EW", "EX", "RE"}


def _load_env() -> None:
    for env_path in [ANALYSIS_ROOT / ".env", Path(r"G:\Meu Drive\Opyta\Opyta_Data\.env")]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _engine():
    _load_env()
    url = os.environ.get("FISICO_DB_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("FISICO_DB_URL/DATABASE_URL nao encontrado.")
    return create_engine(url, pool_pre_ping=True)


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _norm_key(value) -> str:
    return _strip_accents(_norm_text(value)).lower()


def _infer_genus(scientific_name: object) -> str:
    txt = _norm_text(scientific_name).strip("\"'“”‘’")
    parts = txt.split()
    return parts[0].strip("\"'“”‘’") if parts else ""


def _infer_genus(scientific_name: object) -> str:
    txt = _norm_text(scientific_name).strip("\"'`")
    parts = txt.split()
    genus = parts[0].strip("\"'`") if parts else ""
    return genus[:1].upper() + genus[1:] if genus else ""


def _is_threatened_status(value: object) -> bool:
    raw = _norm_text(value).upper()
    if raw in THREATENED_CODES or raw.startswith("CR("):
        return True
    key = _norm_key(value)
    return bool(re.search(r"\bvulneravel\b|\bem perigo\b|criticamente|ameac", key))


def _load_threat_status_maps() -> tuple[dict[str, str], dict[str, str]]:
    national_path = INVENTORY_DIR / "lista_nacional_ameacadas_mma_1667_2026.csv"
    fishbase_species_path = INVENTORY_DIR / "fishbase_v25_04_species.parquet"
    fishbase_stocks_path = INVENTORY_DIR / "fishbase_v25_04_stocks.parquet"

    national = pd.read_csv(national_path)
    national_map = dict(zip(national["nome_cientifico"], national["categoria_nacional"]))

    fishbase_species = pd.read_parquet(fishbase_species_path, columns=["SpecCode", "Genus", "Species"])
    fishbase_stocks = pd.read_parquet(
        fishbase_stocks_path,
        columns=["SpecCode", "Level", "IUCN_Code", "IUCN_DateAssessed"],
    )
    fishbase_species["nome_cientifico"] = (
        fishbase_species["Genus"].fillna("") + " " + fishbase_species["Species"].fillna("")
    ).str.strip()
    global_rows = fishbase_stocks[fishbase_stocks["Level"].eq("species in general")].copy()
    global_rows = global_rows.sort_values(["SpecCode", "IUCN_DateAssessed"]).drop_duplicates("SpecCode", keep="last")
    global_rows["IUCN_Code"] = global_rows["IUCN_Code"].replace({"N.E.": GLOBAL_NOT_EVALUATED}).fillna(GLOBAL_NOT_EVALUATED)
    global_map = dict(
        fishbase_species[["SpecCode", "nome_cientifico"]]
        .merge(global_rows[["SpecCode", "IUCN_Code"]], on="SpecCode", how="left")
        .drop_duplicates("nome_cientifico")
        .assign(IUCN_Code=lambda frame: frame["IUCN_Code"].fillna(GLOBAL_NOT_EVALUATED))
        .set_index("nome_cientifico")["IUCN_Code"]
    )
    return national_map, global_map


def apply_threat_statuses(base: pd.DataFrame) -> pd.DataFrame:
    national_map, global_map = _load_threat_status_maps()
    base["status_ameaca_estadual"] = STATE_THREAT_STATUS_MT
    base["status_ameaca_nacional"] = base["nome_cientifico"].map(national_map).fillna(NATIONAL_NOT_LISTED)
    base["status_ameaca_global"] = base["nome_cientifico"].map(global_map).fillna(GLOBAL_NOT_EVALUATED)
    return base


def _find_one(pattern: str) -> Path:
    matches = list(BIOS_ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            safe = sheet[:31]
            df.to_excel(writer, sheet_name=safe, index=False)
            ws = writer.book[safe]
            ws.freeze_panes = "A2"
            for col_cells in ws.columns:
                max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col_cells)
                ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 10), 45)


def _fig(path: Path, title: str = "", subtitle: str | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax


def _save_fig(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _style_axes(ax, grid_axis: str = "y") -> None:
    ax.grid(False)
    ax.grid(axis=grid_axis, color=PALETTE["grid"], alpha=0.25, linewidth=1)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.2)
    ax.tick_params(colors="black", labelsize=13)


def shannon(values: pd.Series) -> float:
    arr = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(float)
    arr = arr[arr > 0]
    if arr.sum() <= 0:
        return 0.0
    p = arr / arr.sum()
    return float(-(p * np.log(p)).sum())


def pielou(values: pd.Series) -> float:
    richness = int((pd.to_numeric(values, errors="coerce").fillna(0) > 0).sum())
    return float(shannon(values) / math.log(richness)) if richness > 1 else 0.0


def load_base() -> pd.DataFrame:
    species_workbook = _find_one("*/Planilha/Migracao/Cadastro_especies_opyta_colider-ictio-2600812.xlsx")
    cadastro = pd.read_excel(species_workbook, sheet_name="Especies")
    cadastro["species_key"] = cadastro["Nome_Cientifico"].map(_norm_key)
    cadastro = cadastro.drop_duplicates("species_key")

    point_layer = pd.read_csv(INVENTORY_DIR / "camada_operacional_pontos_biocol001.csv")
    point_layer["ponto_key"] = point_layer["ponto"].map(_norm_key)
    temporal_layer = pd.read_csv(INVENTORY_DIR / "camada_temporal_reservatorio_biocol001.csv")

    query = text(
        """
        SELECT
          d.id_resultado_ictio, d.id_esforco, d.id_especie, d.linha_fonte,
          d.ponto, d.campanha, d.metodo_de_captura, d.tipo_de_amostragem,
          d.malha_ou_anzol, d.numero_de_individuos, d.ct_cm, d.cp_cm, d.pc_g,
          d.sexo_raw, d.sexo_padronizado, d.emg_raw, d.emg_codigo, d.emg_estadio,
          d.emg_ordem, d.evidencia_reprodutiva_forte,
          e.nome_cientifico, e.nome_popular, e.ordem, e.familia, e.genero,
          e.autor_e_ano, e.status_estadual AS status_ameaca_estadual, e.status_ameaca_nacional,
          e.status_ameaca_global, e.origem, e.habito_alimentar,
          e.estrategia_reprodutiva, e.valor_economico
        FROM public.resultados_ictiofauna_detalhe d
        JOIN public.especies e ON e.id_especie = d.id_especie
        WHERE d.codigo_opyta = :code
        """
    )
    with _engine().connect() as conn:
        base = pd.read_sql(query, conn, params={"code": PROJECT_CODE})

    # Complementa atributos com a planilha validada, que e mais completa para estrategia/origem.
    base["species_key"] = base["nome_cientifico"].map(_norm_key)
    comp_cols = [
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
        "species_key",
    ]
    comp_cols = [c for c in comp_cols if c in cadastro.columns]
    base = base.merge(cadastro[comp_cols], on="species_key", how="left", suffixes=("", "_cad"))
    for raw, cad in [
        ("nome_popular", "Nome_Popular"),
        ("ordem", "Ordem"),
        ("familia", "Familia"),
        ("genero", "Genero"),
        ("autor_e_ano", "Autor_e_Ano"),
        ("status_ameaca_estadual", "Status_Ameaca_Estadual"),
        ("status_ameaca_nacional", "Status_Ameaca_Nacional"),
        ("status_ameaca_global", "Status_Ameaca_Global"),
        ("origem", "Origem"),
        ("habito_alimentar", "Habito_Alimentar"),
        ("estrategia_reprodutiva", "Estrategia_Reprodutiva"),
        ("valor_economico", "Valor_Economico"),
    ]:
        if cad in base.columns:
            base[raw] = base[raw].where(base[raw].notna() & (base[raw].astype(str).str.strip() != ""), base[cad])

    base["nome_cientifico_original_pre_fishbase"] = base["nome_cientifico"]
    base["nome_cientifico_limpo"] = base["nome_cientifico"].map(_norm_text).str.strip("\"'â€œâ€â€˜â€™")
    name_override_mask = base["nome_cientifico_limpo"].isin(SPECIES_NAME_OVERRIDES)
    base.loc[name_override_mask, "nome_cientifico"] = base.loc[name_override_mask, "nome_cientifico_limpo"].map(SPECIES_NAME_OVERRIDES)
    base.loc[name_override_mask, "genero"] = base.loc[name_override_mask, "nome_cientifico"].map(_infer_genus)

    base["ponto_key"] = base["ponto"].map(_norm_key)
    base = base.merge(point_layer.drop(columns=["ponto"]), on="ponto_key", how="left")
    base["universo_geral"] = base["incluir_analises_gerais"].eq("sim")
    base["universo_stp"] = base["camada_operacional"].eq("sistema_transposicao_condicional")
    base["universo_marcacao"] = base["camada_operacional"].eq("programacao_marcacao")
    base["biomassa_g_linha"] = pd.to_numeric(base["numero_de_individuos"], errors="coerce").fillna(0) * pd.to_numeric(base["pc_g"], errors="coerce")
    base["ano"] = base["campanha"].astype(str).str.extract(r"-(\d{4})-")[0]
    base["mes"] = base["campanha"].astype(str).str.extract(r"-(\d{4})-(\d{2})")[1]
    base = base.merge(temporal_layer, on="campanha", how="left", suffixes=("", "_temporal"))
    base["estrategia_key"] = base["estrategia_reprodutiva"].map(_norm_key)
    base["genero_inferido"] = base["nome_cientifico"].map(_infer_genus)
    base["familia_original_pre_override"] = base["familia"]
    override_mask = base["genero_inferido"].isin(FAMILY_OVERRIDES_BY_GENUS)
    base.loc[override_mask, "familia"] = base.loc[override_mask, "genero_inferido"].map(FAMILY_OVERRIDES_BY_GENUS)
    base = apply_threat_statuses(base)
    base["classe_migratoria"] = np.select(
        [
            base["estrategia_key"].eq("migradora de curta distancia"),
            base["estrategia_key"].eq("migradora de longa distancia"),
        ],
        ["MCD", "MLD"],
        default="Nao migradora",
    )
    threat_cols = ["status_ameaca_estadual", "status_ameaca_nacional", "status_ameaca_global"]
    base["ameacada"] = False
    for col in threat_cols:
        base["ameacada"] |= base[col].map(_is_threatened_status)
    return base


def build_recruitment(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    migr = base[base["classe_migratoria"].eq("MLD") & base["cp_cm"].notna() & (base["cp_cm"] > 0)].copy()
    rows = []
    tagged = []
    for (species_id, species), g in migr.groupby(["id_especie", "nome_cientifico"], dropna=False):
        ref = g[g["emg_codigo"].isin(["F2", "F3", "F4"])]
        limit = ref["cp_cm"].min() if len(ref) else np.nan
        status = "Sem referencia F2+"
        if pd.notna(limit):
            if len(ref) < 3:
                status = "Aplicavel com cautela: referencia F2+ pequena"
            elif ref["cp_cm"].nunique() < 2:
                status = "Aplicavel com cautela: limite baseado em CP pouco variavel"
            else:
                status = "Aplicavel preliminarmente"
        local = g.copy()
        local["cp_referencia_f2plus_min_cm"] = limit
        local["jovem_preliminar"] = pd.notna(limit) & (local["cp_cm"] < limit)
        local["status_criterio_recrutamento"] = status
        tagged.append(local)
        young = local[local["jovem_preliminar"]]
        rows.append(
            {
                "id_especie": species_id,
                "nome_cientifico": species,
                "classe_recrutamento": g["classe_migratoria"].iloc[0],
                "estrategia_reprodutiva": g["estrategia_reprodutiva"].iloc[0],
                "cp_referencia_f2plus_min_cm": limit,
                "linhas_referencia_f2plus": len(ref),
                "individuos_referencia_f2plus": ref["numero_de_individuos"].sum(),
                "linhas_com_cp_mld": len(g),
                "individuos_com_cp_mld": g["numero_de_individuos"].sum(),
                "linhas_jovens_preliminar": len(young),
                "individuos_jovens_preliminar": young["numero_de_individuos"].sum(),
                "status_criterio_recrutamento": status,
            }
        )
    return pd.DataFrame(rows), pd.concat(tagged, ignore_index=True) if tagged else pd.DataFrame()


def export_bases(base: pd.DataFrame, recruitment_rows: pd.DataFrame) -> list[str]:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    cols = [
        "campanha",
        "ano",
        "ponto",
        "camada_operacional",
        "fase_reservatorio",
        "evento_reservatorio",
        "periodo_rebaixamento_parcial",
        "marco_reenchimento",
        "metodo_de_captura",
        "tipo_de_amostragem",
        "numero_de_individuos",
        "biomassa_g_linha",
        "ct_cm",
        "cp_cm",
        "pc_g",
        "nome_cientifico",
        "nome_popular",
        "ordem",
        "familia",
        "origem",
        "classe_migratoria",
        "estrategia_reprodutiva",
        "status_ameaca_estadual",
        "status_ameaca_nacional",
        "status_ameaca_global",
        "sexo_padronizado",
        "emg_codigo",
        "emg_estadio",
        "evidencia_reprodutiva_forte",
    ]
    cols = [c for c in cols if c in base.columns]
    outputs = []
    datasets = {
        "base_analitica_geral_biocol001.xlsx": base.loc[base["universo_geral"], cols],
        "base_analitica_sem_marcacao_biocol001.xlsx": base.loc[~base["universo_marcacao"], cols],
        "base_analitica_stp_pt13c_pt13d_biocol001.xlsx": base.loc[base["universo_stp"], cols],
        "base_reprodutiva_biometria_biocol001.xlsx": base.loc[base["emg_codigo"].notna() | base["sexo_padronizado"].notna(), cols],
        "base_recrutamento_mld_biocol001.xlsx": recruitment_rows,
    }
    for filename, df in datasets.items():
        path = BASE_DIR / filename
        _write_excel(path, {"base": df})
        outputs.append(str(path))
    return outputs


def export_taxonomic_override_audit(base: pd.DataFrame) -> str:
    family_audit = (
        base.loc[base["genero_inferido"].isin(FAMILY_OVERRIDES_BY_GENUS)]
        .groupby(["genero_inferido", "nome_cientifico", "familia_original_pre_override", "familia"], dropna=False)
        .agg(linhas=("nome_cientifico", "size"), individuos=("numero_de_individuos", "sum"))
        .reset_index()
        .sort_values(["genero_inferido", "nome_cientifico"])
    )
    family_audit = family_audit.rename(
        columns={
            "genero_inferido": "genero",
            "familia_original_pre_override": "familia_original",
            "familia": "familia_corrigida",
        }
    )
    family_audit["tipo_correcao"] = "familia_fishbase_regra_usuario"

    name_audit = (
        base.loc[base["nome_cientifico_original_pre_fishbase"].ne(base["nome_cientifico"])]
        .groupby(["nome_cientifico_original_pre_fishbase", "nome_cientifico", "familia"], dropna=False)
        .agg(linhas=("nome_cientifico", "size"), individuos=("numero_de_individuos", "sum"))
        .reset_index()
        .rename(
            columns={
                "nome_cientifico_original_pre_fishbase": "nome_original",
                "nome_cientifico": "nome_corrigido_fishbase",
                "familia": "familia_corrigida",
            }
        )
        .sort_values(["nome_original", "nome_corrigido_fishbase"])
    )
    name_audit["tipo_correcao"] = "nome_aceito_fishbase"

    inventory_path = INVENTORY_DIR / "auditoria_correcao_taxonomica_fishbase_biocol001.xlsx"
    package_path = OUT_DIR / "auditoria_correcao_taxonomica_fishbase_biocol001.xlsx"
    with pd.ExcelWriter(inventory_path, engine="openpyxl") as writer:
        family_audit.to_excel(writer, sheet_name="Familias", index=False)
        name_audit.to_excel(writer, sheet_name="Nomes", index=False)
    package_path.write_bytes(inventory_path.read_bytes())
    return str(package_path)


def build_tables(base: pd.DataFrame, recruitment_summary: pd.DataFrame) -> dict[str, pd.DataFrame]:
    geral = base[base["universo_geral"]].copy()
    species = (
        geral.groupby("nome_cientifico", dropna=False)
        .agg(
            ordem=("ordem", "first"),
            familia=("familia", "first"),
            genero=("genero", "first"),
            autor_e_ano=("autor_e_ano", "first"),
            nome_popular=("nome_popular", "first"),
            origem=("origem", "first"),
            estrategia_reprodutiva=("estrategia_reprodutiva", "first"),
            classe_migratoria=("classe_migratoria", "first"),
            status_ameaca_estadual=("status_ameaca_estadual", "first"),
            status_ameaca_nacional=("status_ameaca_nacional", "first"),
            status_ameaca_global=("status_ameaca_global", "first"),
            N=("numero_de_individuos", "sum"),
            biomassa_g=("biomassa_g_linha", "sum"),
            pontos_ocorrencia=("ponto", "nunique"),
            campanhas_ocorrencia=("campanha", "nunique"),
        )
        .reset_index()
        .sort_values(["ordem", "familia", "nome_cientifico"])
    )
    biometry = (
        geral.groupby("nome_cientifico", dropna=False)
        .agg(
            N=("numero_de_individuos", "sum"),
            B_g=("biomassa_g_linha", "sum"),
            CT_min_cm=("ct_cm", "min"),
            CT_med_cm=("ct_cm", "mean"),
            CT_max_cm=("ct_cm", "max"),
            CP_min_cm=("cp_cm", "min"),
            CP_med_cm=("cp_cm", "mean"),
            CP_max_cm=("cp_cm", "max"),
            PC_min_g=("pc_g", "min"),
            PC_med_g=("pc_g", "mean"),
            PC_max_g=("pc_g", "max"),
        )
        .reset_index()
        .sort_values("N", ascending=False)
    )
    point = (
        geral.groupby("ponto")
        .agg(riqueza=("nome_cientifico", "nunique"), abundancia=("numero_de_individuos", "sum"), biomassa_g=("biomassa_g_linha", "sum"))
        .reset_index()
        .sort_values("ponto")
    )
    temporal = (
        geral.groupby("campanha")
        .agg(
            riqueza=("nome_cientifico", "nunique"),
            abundancia=("numero_de_individuos", "sum"),
            biomassa_g=("biomassa_g_linha", "sum"),
            fase_reservatorio=("fase_reservatorio", "first"),
            evento_reservatorio=("evento_reservatorio", "first"),
        )
        .reset_index()
        .sort_values("campanha")
    )
    threatened = species[
        species[["status_ameaca_estadual", "status_ameaca_nacional", "status_ameaca_global"]]
        .apply(lambda column: column.map(_is_threatened_status))
        .any(axis=1)
    ].copy()
    return {
        "5_2_composicao_especies": species,
        "5_2_1_classificacao_taxonomica": species[["ordem", "familia", "genero", "nome_cientifico", "autor_e_ano", "nome_popular", "origem", "estrategia_reprodutiva"]],
        "5_3_especies_ameacadas": threatened,
        "5_4_estrutura_populacoes": biometry,
        "5_5_distribuicao_espacial": point,
        "5_6_distribuicao_temporal": temporal,
        "5_15_recrutamento_mld_auditoria": recruitment_summary,
    }


def export_official_tables(tables: dict[str, pd.DataFrame]) -> list[str]:
    outputs: list[str] = []
    mapping = {
        "05_composicao_especies/tabela_05_composicao_especies.xlsx": {"Tabela_05": tables["5_2_composicao_especies"]},
        "06_caracteristicas_biologicas/tabela_06_caracteristicas_biologicas.xlsx": {"Tabela_06": tables["5_2_1_classificacao_taxonomica"]},
        "08_biometria_biomassa/tabela_08_biometria_biomassa.xlsx": {"Tabela_08": tables["5_4_estrutura_populacoes"]},
        "10_curva_coletor/figura_10_curva_coletor_dados.xlsx": {"Curva": tables["5_10_curva_acumulativa"]},
        "11_ordem_familia/figura_11_ordem_familia_dados.xlsx": {
            "Ordem": tables["5_2_composicao_especies"].groupby("ordem", dropna=False)["nome_cientifico"].nunique().reset_index(name="Riqueza"),
            "Familia": tables["5_2_composicao_especies"].groupby("familia", dropna=False)["nome_cientifico"].nunique().reset_index(name="Riqueza"),
        },
        "12_riqueza_temporal/figura_12_riqueza_temporal_dados.xlsx": {"Riqueza": tables["5_6_distribuicao_temporal"]},
        "30_diversidade_equitabilidade/figura_30_diversidade_equitabilidade_dados.xlsx": {"Diversidade": tables["5_8_diversidade_equitabilidade"]},
        "31_similaridade_beta/figura_31_similaridade_bray_curtis_dados.xlsx": {"Similaridade": tables["5_9_similaridade_bray_curtis"]},
        "15_recrutamento_mld/tabela_15_recrutamento_mld_auditoria.xlsx": {"Recrutamento": tables["5_15_recrutamento_mld_auditoria"]},
    }
    threatened = tables["5_3_especies_ameacadas"]
    if not threatened.empty:
        mapping["03_especies_ameacadas/tabela_03_especies_ameacadas.xlsx"] = {"Tabela_03": threatened}
    for rel, sheets in mapping.items():
        path = OFFICIAL_DIR / rel
        _write_excel(path, sheets)
        outputs.append(str(path))
    return outputs


def diversity_table(base: pd.DataFrame) -> pd.DataFrame:
    geral = base[base["universo_geral"]].copy()
    rows = []
    for keys, g in geral.groupby(["campanha", "ponto"], dropna=False):
        vec = g.groupby("nome_cientifico")["numero_de_individuos"].sum()
        rows.append(
            {
                "campanha": keys[0],
                "ponto": keys[1],
                "riqueza": int((vec > 0).sum()),
                "abundancia": float(vec.sum()),
                "Shannon_H": shannon(vec),
                "Pielou_J": pielou(vec),
                "fase_reservatorio": g["fase_reservatorio"].dropna().iloc[0] if g["fase_reservatorio"].notna().any() else "",
                "evento_reservatorio": g["evento_reservatorio"].dropna().iloc[0] if g["evento_reservatorio"].notna().any() else "",
            }
        )
    return pd.DataFrame(rows).sort_values(["campanha", "ponto"])


def similarity_matrix(base: pd.DataFrame, by: str = "campanha") -> pd.DataFrame:
    geral = base[base["universo_geral"]].copy()
    mat = geral.pivot_table(index=by, columns="nome_cientifico", values="numero_de_individuos", aggfunc="sum", fill_value=0)
    if len(mat) < 2:
        return pd.DataFrame()
    dist = squareform(pdist(mat.to_numpy(float), metric="braycurtis"))
    sim = 1 - dist
    return pd.DataFrame(sim, index=mat.index, columns=mat.index).reset_index().rename(columns={by: by})


def accumulation_curve(base: pd.DataFrame, permutations: int = 300, seed: int = 42) -> pd.DataFrame:
    geral = base[base["universo_geral"]].copy()
    pa = (
        geral[["campanha", "ponto", "nome_cientifico"]]
        .drop_duplicates()
        .sort_values(["campanha", "ponto", "nome_cientifico"])
    )
    units_df = pa[["campanha", "ponto"]].drop_duplicates().reset_index(drop=True)
    species = sorted(pa["nome_cientifico"].dropna().astype(str).unique())
    matrix = (
        pa.assign(Presenca=1)
        .pivot_table(index=["campanha", "ponto"], columns="nome_cientifico", values="Presenca", aggfunc="max", fill_value=0)
        .reindex(pd.MultiIndex.from_frame(units_df[["campanha", "ponto"]]), fill_value=0)
        .reindex(columns=species, fill_value=0)
        .to_numpy(dtype=int)
    )
    rng = np.random.default_rng(seed)
    n_units = matrix.shape[0]
    richness = np.zeros((permutations, n_units), dtype=float)
    jackknife = np.zeros((permutations, n_units), dtype=float)
    for perm_idx in range(permutations):
        order = rng.permutation(n_units)
        counts = np.zeros(matrix.shape[1], dtype=int)
        for step, unit_idx in enumerate(order, start=1):
            counts += matrix[unit_idx]
            s_obs = int((counts > 0).sum())
            q1 = int((counts == 1).sum())
            richness[perm_idx, step - 1] = s_obs
            jackknife[perm_idx, step - 1] = s_obs + ((step - 1) / step) * q1
    return pd.DataFrame(
        {
            "Unidade_Amostral": np.arange(1, n_units + 1),
            "Riqueza_Observada_Media": richness.mean(axis=0),
            "Riqueza_Observada_DP": richness.std(axis=0),
            "Jackknife1_Medio": jackknife.mean(axis=0),
            "Jackknife1_DP": jackknife.std(axis=0),
            "Permutacoes": permutations,
            "Unidade": "Campanha x Ponto",
        }
    )


def _plot_donut(df: pd.DataFrame, label_col: str, value_col: str, path: Path, title: str = "") -> str:
    plot_df = df.sort_values(value_col, ascending=False).copy()
    total = int(plot_df[value_col].sum())
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE, dpi=DPI)
    colors = [ALT_PALETTE[i % len(ALT_PALETTE)] for i in range(len(plot_df))]
    wedges, _ = ax.pie(
        plot_df[value_col],
        startangle=90,
        colors=colors,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.2},
    )
    ax.text(0, 0.04, f"{total}", ha="center", va="center", fontsize=27, fontweight="bold", color="#1F1F1F")
    ax.text(0, -0.11, "espécies", ha="center", va="center", fontsize=15, color="#595959")
    labels = [f"{r[label_col]} ({r[value_col]:.0f})" for _, r in plot_df.iterrows()]
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=12)
    ax.set_aspect("equal")
    return str(_save_fig(fig, path))


def _shade_reservoir_events(ax, df: pd.DataFrame, x_col: str = "campanha") -> list:
    handles = []
    if x_col not in df.columns:
        return handles
    local = df[[x_col, "fase_reservatorio", "evento_reservatorio"]].drop_duplicates().reset_index(drop=True)
    local["xpos"] = np.arange(len(local))
    pre = local["fase_reservatorio"].eq("pre_enchimento")
    lowering = local["evento_reservatorio"].eq("rebaixamento_parcial_reservatorio")
    refill = local["evento_reservatorio"].eq("reenchimento_reservatorio")
    if pre.any():
        ax.axvspan(pre[pre].index.min() - 0.5, pre[pre].index.max() + 0.5, color="#F0F0F0", alpha=0.75, linewidth=0, zorder=0)
        handles.append(Patch(facecolor="#F0F0F0", edgecolor="none", alpha=0.75, label="Pré-enchimento"))
    if lowering.any():
        ax.axvspan(lowering[lowering].index.min() - 0.5, lowering[lowering].index.max() + 0.5, color=PALETTE["light"], alpha=0.72, linewidth=0, zorder=0)
        handles.append(Patch(facecolor=PALETTE["light"], edgecolor="none", alpha=0.72, label="Rebaixamento parcial"))
    if refill.any():
        xpos = float(refill[refill].index.min())
        ax.axvline(xpos, color=PALETTE["orange"], linewidth=1.6, linestyle="--", zorder=1)
        handles.append(Line2D([0], [0], color=PALETTE["orange"], linewidth=1.6, linestyle="--", label="Reenchimento"))
    return handles


def make_figures(tables: dict[str, pd.DataFrame], diversity: pd.DataFrame, similarity: pd.DataFrame, accumulation: pd.DataFrame) -> list[str]:
    outputs = []
    composition = tables["5_2_composicao_especies"]
    ordem = composition.groupby("ordem", dropna=False)["nome_cientifico"].nunique().reset_index(name="Riqueza")
    familia = composition.groupby("familia", dropna=False)["nome_cientifico"].nunique().reset_index(name="Riqueza")
    outputs.append(_plot_donut(ordem, "ordem", "Riqueza", OFFICIAL_DIR / "11_ordem_familia" / "figura_11a_percentual_ordem.png", "Figura 11A. Composição por ordem"))
    outputs.append(_plot_donut(familia, "familia", "Riqueza", OFFICIAL_DIR / "11_ordem_familia" / "figura_11b_percentual_familia.png", "Figura 11B. Composição por família"))

    spatial = tables["5_5_distribuicao_espacial"]
    fig, ax = _fig(FIG_DIR / "5_5_distribuicao_espacial_riqueza_abundancia.png", "5.5 Distribuição espacial", "Universo geral: 16 pontos regulares")
    x = np.arange(len(spatial))
    ax.bar(x - 0.2, spatial["riqueza"], width=0.4, color=PALETTE["primary"], label="Riqueza acumulada (nº de espécies)")
    ax2 = ax.twinx()
    ax2.bar(x + 0.2, spatial["abundancia"], width=0.4, color=PALETTE["secondary"], alpha=0.75, label="Abundância acumulada (nº de indivíduos)")
    ax.set_xticks(x)
    ax.set_xticklabels(spatial["ponto"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Riqueza acumulada (nº de espécies)")
    ax2.set_ylabel("Abundância acumulada (nº de indivíduos)")
    fig.legend(
        handles=[
            Patch(facecolor=PALETTE["primary"], edgecolor="none", label="Riqueza acumulada (nº de espécies)"),
            Patch(facecolor=PALETTE["secondary"], edgecolor="none", alpha=0.75, label="Abundância acumulada (nº de indivíduos)"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncol=2,
        frameon=False,
    )
    _style_axes(ax)
    _style_axes(ax2)
    outputs.append(str(_save_fig(fig, FIG_DIR / "5_5_distribuicao_espacial_riqueza_abundancia.png")))

    temporal = tables["5_6_distribuicao_temporal"]
    fig, ax = _fig(OFFICIAL_DIR / "12_riqueza_temporal" / "figura_12_riqueza_temporal_campanha.png", "Figura 12. Riqueza temporal", "Riqueza por campanha canônica")
    event_handles = _shade_reservoir_events(ax, temporal)
    line = ax.plot(np.arange(len(temporal)), temporal["riqueza"], color=PALETTE["primary"], linewidth=2.8, label="Riqueza")[0]
    ax.fill_between(np.arange(len(temporal)), temporal["riqueza"].to_numpy(float), alpha=0.12, color=PALETTE["primary"])
    ax.set_xticks(np.arange(0, len(temporal), max(1, len(temporal) // 12)))
    ax.set_xticklabels(temporal["campanha"].iloc[:: max(1, len(temporal) // 12)], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Riqueza")
    ax.legend(handles=[line, *event_handles], loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=4, frameon=False, fontsize=12)
    _style_axes(ax)
    outputs.append(str(_save_fig(fig, OFFICIAL_DIR / "12_riqueza_temporal" / "figura_12_riqueza_temporal_campanha.png")))

    div_campaign = (
        diversity.groupby("campanha")
        .agg(
            Shannon_H=("Shannon_H", "mean"),
            Pielou_J=("Pielou_J", "mean"),
            fase_reservatorio=("fase_reservatorio", "first"),
            evento_reservatorio=("evento_reservatorio", "first"),
        )
        .reset_index()
    )
    fig, ax = _fig(OFFICIAL_DIR / "30_diversidade_equitabilidade" / "figura_30_diversidade_equitabilidade.png", "Figura 30. Diversidade e equitabilidade", "Médias por campanha e ponto")
    event_handles = _shade_reservoir_events(ax, div_campaign)
    line_h = ax.plot(np.arange(len(div_campaign)), div_campaign["Shannon_H"], color=PALETTE["primary"], linewidth=2.6, label="Shannon H'")[0]
    ax2 = ax.twinx()
    line_j = ax2.plot(np.arange(len(div_campaign)), div_campaign["Pielou_J"], color=PALETTE["secondary"], linewidth=2.6, label="Pielou J'")[0]
    step = max(1, len(div_campaign) // 12)
    ax.set_xticks(np.arange(0, len(div_campaign), step))
    ax.set_xticklabels(div_campaign["campanha"].iloc[::step], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Shannon H'")
    ax2.set_ylabel("Pielou J'")
    ax.legend(handles=[line_h, line_j, *event_handles], loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=5, frameon=False, fontsize=12)
    _style_axes(ax)
    _style_axes(ax2)
    outputs.append(str(_save_fig(fig, OFFICIAL_DIR / "30_diversidade_equitabilidade" / "figura_30_diversidade_equitabilidade.png")))

    if not similarity.empty and len(similarity) > 2:
        mat = similarity.set_index("campanha")
        dist = 1 - mat.to_numpy(float)
        fig, ax = _fig(OFFICIAL_DIR / "31_similaridade_beta" / "figura_31_similaridade_bray_curtis_campanhas.png", "Figura 31. Similaridade", "Dendrograma Bray-Curtis por campanha")
        linkage_matrix = linkage(squareform(dist, checks=False), method="average")
        dendrogram(linkage_matrix, labels=mat.index.tolist(), ax=ax, leaf_rotation=90, leaf_font_size=5, color_threshold=None)
        ax.set_ylabel("Distancia Bray-Curtis")
        _style_axes(ax)
        outputs.append(str(_save_fig(fig, OFFICIAL_DIR / "31_similaridade_beta" / "figura_31_similaridade_bray_curtis_campanhas.png")))

    fig, ax = _fig(OFFICIAL_DIR / "10_curva_coletor" / "figura_10_curva_coletor_observada_jackknife1.png", "Figura 10. Curva do coletor", "Unidade amostral: campanha x ponto; 300 permutações")
    x = accumulation["Unidade_Amostral"].to_numpy()
    y_obs = accumulation["Riqueza_Observada_Media"].to_numpy()
    sd_obs = accumulation["Riqueza_Observada_DP"].to_numpy()
    y_jack = accumulation["Jackknife1_Medio"].to_numpy()
    sd_jack = accumulation["Jackknife1_DP"].to_numpy()
    ax.plot(x, y_obs, color=PALETTE["primary"], linewidth=3.0, label="Riqueza observada (média)")
    ax.fill_between(
        x,
        y_obs - sd_obs,
        y_obs + sd_obs,
        color=PALETTE["primary"],
        alpha=0.12,
        linewidth=0,
        label="±1 DP observado",
    )
    ax.plot(x, y_jack, color=PALETTE["secondary"], linewidth=2.8, linestyle="--", label="Jackknife 1 (média)")
    ax.fill_between(x, y_jack - sd_jack, y_jack + sd_jack, color=PALETTE["secondary"], alpha=0.16, linewidth=0, label="±1 DP Jackknife 1")
    endpoint_specs = [
        (y_obs[-1], PALETTE["primary"], f"Observada: {y_obs[-1]:.0f}"),
        (
            y_jack[-1],
            PALETTE["secondary"],
            f"Estimada (Jackknife 1): {y_jack[-1]:.1f}".replace(".", ","),
        ),
    ]
    for endpoint, color, label in endpoint_specs:
        ax.scatter(x[-1], endpoint, s=52, color=color, edgecolor="white", linewidth=1.2, zorder=5)
        ax.annotate(
            label,
            xy=(x[-1], endpoint),
            xytext=(-12, 13),
            textcoords="offset points",
            ha="right",
            va="bottom",
            color=color,
            fontsize=14,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": color, "alpha": 0.92},
            zorder=6,
        )
    ax.set_xlabel("Unidades amostrais")
    ax.set_ylabel("Riqueza acumulada")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, frameon=False)
    _style_axes(ax)
    outputs.append(str(_save_fig(fig, OFFICIAL_DIR / "10_curva_coletor" / "figura_10_curva_coletor_observada_jackknife1.png")))
    return outputs


def main() -> None:
    started = datetime.now().isoformat(timespec="seconds")
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 17,
            "axes.labelsize": 17,
            "axes.titlesize": 16,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "legend.fontsize": 15,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    for folder in [OUT_DIR, BASE_DIR, FIG_DIR, OFFICIAL_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    base = load_base()
    taxonomic_audit = export_taxonomic_override_audit(base)
    recruitment_summary, recruitment_rows = build_recruitment(base)
    base_outputs = export_bases(base, recruitment_rows)
    tables = build_tables(base, recruitment_summary)
    diversity = diversity_table(base)
    similarity = similarity_matrix(base, by="campanha")
    accumulation = accumulation_curve(base)
    tables["5_8_diversidade_equitabilidade"] = diversity
    tables["5_9_similaridade_bray_curtis"] = similarity
    tables["5_10_curva_acumulativa"] = accumulation
    official_tables = export_official_tables(tables)
    fig_outputs = make_figures(tables, diversity, similarity, accumulation)

    geral = base[base["universo_geral"]]
    manifest = {
        "project": PROJECT_CODE,
        "run_started": started,
        "run_finished": datetime.now().isoformat(timespec="seconds"),
        "run_label": RUN_LABEL,
        "output_dir": str(OUT_DIR),
        "premissas": {
            "template": "BIOPOR001/Porto Estrela: paleta, dimensoes, DPI, nomes oficiais e figuras sem titulo interno.",
            "universo_geral": "16 pontos regulares; exclui ICTIO13A - Marcacao e trata ICTIO13C/D como STP condicional.",
            "stp": "Recorte proprio por ICTIO13C/ICTIO13D, equivalentes aos pontos PT-13C/PT-13D.",
            "recrutamento": "Somente MLD; jovem preliminar = CP_cm menor que menor CP_cm em femeas F2/F3/F4 da especie.",
            "marcos_reservatorio": "Pre-enchimento ate C020; pos-enchimento de C021 em diante; rebaixamento parcial entre 2025-08 e 2026-02; reenchimento em 2026-03.",
            "figuras_temporais": "Riqueza temporal e diversidade/equitabilidade recebem faixas discretas de fase/evento com legenda explicativa; curva do coletor nao recebe faixa temporal porque usa ordem aleatorizada de campanha x ponto.",
            "correcao_taxonomica_fishbase": "Familias e nomes cientificos corrigidos por regras aprovadas BIOCOL001 e auditoria FishBase/rOpenSci v25.04; auditoria exportada no pacote.",
            "aguardar": ["5.1 agua abiotica", "5.14 ovos/larvas/ictioplancton", "5.18 marcacao T-TAG"],
        },
        "totais_base_completa": {
            "linhas": int(len(base)),
            "individuos": float(base["numero_de_individuos"].sum()),
            "especies": int(base["nome_cientifico"].nunique()),
            "campanhas": int(base["campanha"].nunique()),
            "pontos": int(base["ponto"].nunique()),
        },
        "totais_universo_geral": {
            "linhas": int(len(geral)),
            "individuos": float(geral["numero_de_individuos"].sum()),
            "especies": int(geral["nome_cientifico"].nunique()),
            "campanhas": int(geral["campanha"].nunique()),
            "pontos": int(geral["ponto"].nunique()),
        },
        "outputs": {
            "bases": base_outputs,
            "produtos_oficiais_tabelas": official_tables,
            "produtos_oficiais_figuras": fig_outputs,
            "auditoria_taxonomica": [taxonomic_audit],
        },
    }
    manifest_path = OUT_DIR / "manifesto_bateria_produtos_maduros_biocol001_R02_BIOPOR001_template.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest["totais_universo_geral"], ensure_ascii=False, indent=2))
    print(f"out_dir={OUT_DIR}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
