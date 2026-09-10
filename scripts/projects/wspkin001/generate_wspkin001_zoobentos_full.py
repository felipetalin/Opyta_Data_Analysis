"""Run the approved BRAAEG001 Zoobentos package for WSPKIN001."""

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "outputs/_project_scripts/BRAAEG001__a_g_mineracao_biota_aquatica/bentos"
AUDIT_DIR = ROOT / "outputs/_project_scripts/WSPKIN001__kinross_bandeirinhas/zoobentos"
OUTPUT_DIR = Path(os.environ.get("WSPKIN001_ZOOBENTOS_OUTPUT", str(ROOT / "outputs/validacoes/wspkin001_zoobentos_tipo_amostragem_rev_r01_20260909/pacote_revisado")))
KMZ_PATH = Path(r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\WSP\BAndeirinhas_Kinross\Geo\2026\Projeto_WSPKIN001.kmz")


def adapted_namespace(path: Path, minimap: bool = False) -> dict:
    source = path.read_text(encoding="utf-8-sig")
    source = source.replace('PROJECT_ID = 195', 'PROJECT_ID = 211')
    source = source.replace('BRAAEG001', 'WSPKIN001').replace('braaeg001', 'wspkin001')
    source = source.replace('Barão de Cocais', 'Paracatu')
    source = source.replace(
        'Registros de zoobentos tratados como quantitativos.',
        'Registros qualitativos usados em composição, ocorrência, riqueza e BMWP; registros quantitativos usados nos cálculos de abundância, diversidade, similaridade, EPT e CHOL.',
    )
    if minimap:
        start = source.index('def client_root() -> Path:')
        end = source.index('\n\ndef now_tag()', start)
        replacement = (
            f'CLIENT_ROOT = Path(r"{OUTPUT_DIR.parent}")\n'
            f'OUTPUT_DIR = Path(r"{OUTPUT_DIR}")\n'
            f'AUDIT_DIR = Path(r"{AUDIT_DIR}")\n'
            f'KMZ_PATH = Path(r"{KMZ_PATH}")'
        )
        source = source[:start] + replacement + source[end:]
        source = source.replace(
            'total = float(local["contagem"].sum()) if not local.empty else 0.0\n            positive = local[local["contagem"] > 0].copy()',
            'quantitative = local[local["tipo_amostragem"].astype(str).str.casefold().eq("quantitativa")].copy()\n            total = float(quantitative["contagem"].sum()) if not quantitative.empty else 0.0\n            positive = local[local["contagem"] > 0].copy()\n            quantitative_positive = quantitative[quantitative["contagem"] > 0].copy()',
        )
        source = source.replace(
            'ept = positive[positive.apply(is_ept, axis=1)] if not positive.empty else positive\n            chol = positive[positive.apply(is_chol, axis=1)] if not positive.empty else positive',
            'ept = quantitative_positive[quantitative_positive.apply(is_ept, axis=1)] if not quantitative_positive.empty else quantitative_positive\n            chol = quantitative_positive[quantitative_positive.apply(is_chol, axis=1)] if not quantitative_positive.empty else quantitative_positive',
        )
    else:
        old = '''OUTPUT_DIR = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/"
    "A&G Mineração/resultados/migracao_biota/bentos"
)'''
        source = source.replace(old, f'OUTPUT_DIR = Path(r"{OUTPUT_DIR}")')
        source = source.replace(
            'AUDIT_DIR = ROOT / "outputs" / "_project_scripts" / "WSPKIN001__a_g_mineracao_biota_aquatica" / "bentos"',
            f'AUDIT_DIR = Path(r"{AUDIT_DIR}")',
        )
    namespace = {"__file__": str(path), "__name__": f"adapted_{path.stem}"}
    exec(compile(source, str(path), "exec"), namespace)
    if not minimap:
        def quantitative(df):
            return df[df["tipo_amostragem"].astype(str).str.casefold().eq("quantitativa")].copy()

        for name in ("build_abundance_by_point", "build_abundance_order", "build_abundance_taxon", "plot_taxon_heatmap", "build_diversity", "build_matrix", "build_point_matrix"):
            original = namespace[name]
            namespace[name] = (lambda fn: lambda df, *args, **kwargs: fn(quantitative(df), *args, **kwargs))(original)

        original_composition = namespace["build_composition"]
        def build_composition_mixed(df):
            out = original_composition(df)
            q = quantitative(df).groupby("nome_cientifico")["contagem"].sum()
            qualitative = df[df["tipo_amostragem"].astype(str).str.casefold().eq("qualitativa")].groupby("nome_cientifico").size()
            out["Abundância quantitativa"] = out["Táxon"].map(q).fillna(0)
            out["Registros qualitativos"] = out["Táxon"].map(qualitative).fillna(0).astype(int)
            return out.drop(columns=["Abundância total"])
        namespace["build_composition"] = build_composition_mixed

        original_bio = namespace["build_bioindicators"]
        def build_bio_mixed(df, campaigns, points):
            all_rows = original_bio(df, campaigns, points)
            quant_rows = original_bio(quantitative(df), campaigns, points)
            for col in ("EPT (%)", "CHOL (%)", "abundancia_total", "abundancia_EPT", "abundancia_CHOL"):
                all_rows[col] = quant_rows[col]
            return all_rows
        namespace["build_bioindicators"] = build_bio_mixed

        def build_synthesis_mixed(df, richness_order, abundance_order, bio):
            order_totals = abundance_order.drop(columns=["nome_campanha", "nome_ponto"]).sum().sort_values(ascending=False).reset_index()
            order_totals.columns = ["Ordem", "Abundância quantitativa"]
            summary = df.groupby("nome_campanha").agg(linhas_totais=("nome_cientifico", "size"), pontos=("nome_ponto", "nunique"), táxons_totais=("nome_cientifico", "nunique")).reset_index()
            q_summary = quantitative(df).groupby("nome_campanha").agg(linhas_quantitativas=("nome_cientifico", "size"), abundância_quantitativa=("contagem", "sum")).reset_index()
            return {"riqueza_por_ordem": richness_order, "abundancia_por_ordem": order_totals.rename(columns={"Abundância quantitativa": "Abundância total"}), "bioindicadores_por_ponto": bio, "resumo_por_campanha": summary.merge(q_summary, on="nome_campanha", how="left")}
        namespace["build_synthesis"] = build_synthesis_mixed

        original_metrics = namespace["build_metrics"]
        def build_metrics_mixed(df, *args, **kwargs):
            result = original_metrics(quantitative(df), *args, **kwargs)
            result.update(rows_consolidated=int(len(df)), rows_quantitative=int(len(quantitative(df))), rows_qualitative=int(len(df) - len(quantitative(df))), taxa_total=int(df["nome_cientifico"].nunique()))
            return result
        namespace["build_metrics"] = build_metrics_mixed
    return namespace


def execute_adapted(path: Path, minimap: bool = False) -> int:
    namespace = adapted_namespace(path, minimap=minimap)
    if "main" in namespace:
        return int(namespace["main"]())
    result = namespace["generate"]()
    print({key: result.get(key) for key in ("audit_json", "figures_count", "figures_ok", "files_count", "output_dir")})
    return 0


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if not (OUTPUT_DIR / "16_mini_mapa_bmwp_ept_chol_zoobentos.png").exists():
        execute_adapted(REFERENCE / "generate_minimapa_bmwp_ept_chol_zoobentos.py", minimap=True)
    return execute_adapted(REFERENCE / "generate_bentos_results_a4_landscape.py")


if __name__ == "__main__":
    raise SystemExit(main())
