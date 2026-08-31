from __future__ import annotations

import hashlib
import html
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
PROJECT_CODE = os.getenv("OPYTA_DELIVERY_PROJECT_CODE", "BRAAEG001")
PROJECT_ID = int(os.getenv("OPYTA_DELIVERY_PROJECT_ID", "195"))
PACKAGE_SLUG = os.getenv("OPYTA_DELIVERY_PACKAGE_SLUG", "braaeg001")
REPORT_TITLE = os.getenv("OPYTA_DELIVERY_REPORT_TITLE", f"{PROJECT_CODE} - Diagnóstico da ictiofauna")
AUDIT_DIR = Path(
    os.getenv(
        "OPYTA_DELIVERY_AUDIT_DIR",
        str(ROOT / "outputs" / "_project_scripts" / "BRAAEG001__a_g_mineracao_biota_aquatica" / "ictiofauna"),
    )
)
OUTPUT_DIR = Path(
    os.getenv(
        "OPYTA_DELIVERY_OUTPUT_DIR",
        "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/A&G Mineração/resultados/migracao_biota/ictiofauna",
    )
)

PACKAGE_NAMES = {
    "14_tabela_sintese_ecologica_ictiofauna.xlsx",
    "14_grafico_sintese_ecologica_ictiofauna.png",
    f"relatorio_tecnico_ictiofauna_{PACKAGE_SLUG}.html",
    f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.json",
    f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.xlsx",
    f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.md",
    f"validacao_entrega_ictiofauna_{PACKAGE_SLUG}.json",
}

COLUMN_LABELS = {
    "nome_campanha": "Campanha",
    "nome_ponto": "Ponto",
    "individuos": "Indivíduos",
    "biomassa_g": "Biomassa (g)",
    "cpuen_total": "CPUEn total",
    "cpueb_total": "CPUEb total",
    "Shannon_H": "Shannon H'",
    "Pielou_J": "Pielou J'",
}

BAD_VISIBLE_REPORT_TERMS = [
    "Pacote diagn" + "ostico",
    "indiv" + "iduos",
    "fam" + "ilias",
    "S" + "intese por campanha",
    "Destaques diagn" + "osticos",
    "Maior abund" + "ancia",
    "curva de sufici" + "encia",
    "Os ind" + "ices",
    "apoio diagn" + "ostico",
    "Abund" + "ancia por ponto",
    "S" + "intese ecol" + "ogica",
    "Sufici" + "encia amostral",
    "ind/100m2",
    "g/100m2",
]


def validate_report_ptbr(html_text: str) -> None:
    found = [term for term in BAD_VISIBLE_REPORT_TERMS if term in html_text]
    if found:
        joined = ", ".join(found)
        raise ValueError(f"Texto visível sem acentuação pt-BR no relatório HTML: {joined}")


def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_xlsx(name: str) -> pd.DataFrame:
    return pd.read_excel(OUTPUT_DIR / name)


def clean_category(value: object) -> str:
    text = str(value).strip() if value is not None else ""
    if not text or text.lower() in {"nan", "none"}:
        return "N.A."
    return text


def ecological_summaries(comp: pd.DataFrame) -> dict[str, pd.DataFrame]:
    keep_cols = [
        "Nome Cientifico",
        "Ordem",
        "Familia",
        "Origem",
        "Status Amea\u00e7a Estadual",
        "Status Amea\u00e7a Nacional",
        "Status Amea\u00e7a Global",
        "Endemismo",
        "Habito Alimentar",
        "Guilda Alimentar",
        "Migratorio",
        "Raridade",
        "Sensibilidade Ambiental",
        "Abundancia Total",
    ]
    attrs = comp[[col for col in keep_cols if col in comp.columns]].copy()
    if "Abundancia Total" in attrs.columns:
        attrs["Abundancia Total"] = pd.to_numeric(attrs["Abundancia Total"], errors="coerce").fillna(0)
    else:
        attrs["Abundancia Total"] = 0

    for col in attrs.columns:
        if col != "Abundancia Total":
            attrs[col] = attrs[col].map(clean_category)

    sheets: dict[str, pd.DataFrame] = {"atributos_por_especie": attrs}
    summary_specs = [
        ("Origem", "sintese_origem"),
        ("Migratorio", "sintese_migratorio"),
        ("Status Amea\u00e7a Estadual", "sintese_ameaca_estadual"),
        ("Status Amea\u00e7a Nacional", "sintese_ameaca_nacional"),
        ("Status Amea\u00e7a Global", "sintese_ameaca_global"),
        ("Endemismo", "sintese_endemismo"),
        ("Habito Alimentar", "sintese_habito_alimentar"),
        ("Guilda Alimentar", "sintese_guilda_alimentar"),
        ("Raridade", "sintese_raridade"),
        ("Sensibilidade Ambiental", "sintese_sensibilidade"),
    ]

    total_taxa = max(len(attrs), 1)
    total_abundance = float(attrs["Abundancia Total"].sum()) or 1.0
    for col, sheet in summary_specs:
        if col not in attrs.columns:
            continue
        grouped = (
            attrs.groupby(col, dropna=False)
            .agg(
                especies=("Nome Cientifico", "nunique"),
                abundancia_total=("Abundancia Total", "sum"),
            )
            .reset_index()
            .rename(columns={col: "categoria"})
        )
        grouped["especies_pct"] = grouped["especies"] / total_taxa * 100
        grouped["abundancia_pct"] = grouped["abundancia_total"] / total_abundance * 100
        sheets[sheet] = grouped.sort_values(["abundancia_total", "especies"], ascending=False)

    coverage_rows = []
    for col in [c for c, _ in summary_specs if c in attrs.columns]:
        na_species = int((attrs[col] == "N.A.").sum())
        coverage_rows.append(
            {
                "atributo": col,
                "especies_com_informacao": int(len(attrs) - na_species),
                "especies_sem_informacao": na_species,
                "cobertura_pct": ((len(attrs) - na_species) / total_taxa) * 100,
            }
        )
    sheets["cobertura_atributos"] = pd.DataFrame(coverage_rows)
    return sheets


def write_ecological_outputs(comp: pd.DataFrame) -> list[Path]:
    sheets = ecological_summaries(comp)
    out_xlsx = OUTPUT_DIR / "14_tabela_sintese_ecologica_ictiofauna.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)

    fig_path = OUTPUT_DIR / "14_grafico_sintese_ecologica_ictiofauna.png"
    plot_data = []
    for sheet, title in [
        ("sintese_origem", "Origem"),
        ("sintese_migratorio", "Comportamento migratório"),
    ]:
        df = sheets.get(sheet, pd.DataFrame())
        if not df.empty:
            local = df[["categoria", "abundancia_total"]].copy()
            local["painel"] = title
            plot_data.append(local)

    if plot_data:
        data = pd.concat(plot_data, ignore_index=True)
        panels = data["painel"].drop_duplicates().tolist()
        fig, axes = plt.subplots(1, len(panels), figsize=(15, 10), dpi=600)
        if len(panels) == 1:
            axes = [axes]
        for ax, panel in zip(axes, panels):
            sub = data[data["painel"] == panel].sort_values("abundancia_total", ascending=True)
            ax.barh(sub["categoria"], sub["abundancia_total"], color="#11420C")
            ax.set_title(panel, fontweight="bold", fontsize=17, pad=12)
            ax.set_xlabel("Abundância total", fontsize=12, labelpad=10)
            ax.tick_params(axis="both", labelsize=12)
            ax.grid(axis="x", alpha=0.2, linestyle="--")
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
        fig.suptitle(f"Síntese ecológica da ictiofauna - {PROJECT_CODE}", fontweight="bold", fontsize=17)
        fig.tight_layout(rect=[0, 0.02, 1, 0.95])
        fig.savefig(fig_path, dpi=600, bbox_inches="tight")
        plt.close(fig)
    return [out_xlsx, fig_path]


def compute_metrics() -> dict:
    comp = read_xlsx("01_tabela_composicao_ictiofauna.xlsx")
    richness = read_xlsx("02_df_riqueza_por_ponto_ictiofauna.xlsx")
    abundance = read_xlsx("03_df_abundancia_por_ponto_ictiofauna.xlsx")
    cpue = read_xlsx("06_df_cpue_por_ponto_ictiofauna.xlsx")
    diversity = read_xlsx("10_df_diversidade_alfa_ictiofauna.xlsx")
    suff = read_xlsx("12_df_curva_suficiencia_ictiofauna.xlsx")
    biometry = read_xlsx("13_tabela_biometria_biomassa_ictiofauna.xlsx")

    for col in ["riqueza"]:
        richness[col] = pd.to_numeric(richness[col], errors="coerce").fillna(0)
    for col in ["abundancia_total"]:
        abundance[col] = pd.to_numeric(abundance[col], errors="coerce").fillna(0)
    for col in ["abundancia_total", "biomassa_total", "cpuen", "cpueb"]:
        cpue[col] = pd.to_numeric(cpue[col], errors="coerce").fillna(0)

    max_rich = richness.sort_values("riqueza", ascending=False).head(1).to_dict("records")[0]
    max_abund = abundance.sort_values("abundancia_total", ascending=False).head(1).to_dict("records")[0]
    max_cpuen = cpue.sort_values("cpuen", ascending=False).head(1).to_dict("records")[0]
    max_cpueb = cpue.sort_values("cpueb", ascending=False).head(1).to_dict("records")[0]
    suff_last = suff.tail(1).to_dict("records")[0]

    geral = diversity[diversity["nome_ponto"].astype(str).str.contains("Geral", case=False, na=False)].copy()
    if geral.empty:
        geral = diversity.copy()

    bio_rows = biometry[biometry["ESP\u00c9CIE"].notna()].copy()
    bio_rows = bio_rows[bio_rows["ESP\u00c9CIE"].astype(str).str.strip().str.lower() != "nan"]
    biomass_col = "Unnamed: 7" if "Unnamed: 7" in bio_rows.columns else bio_rows.columns[-1]
    bio_rows[biomass_col] = pd.to_numeric(bio_rows[biomass_col], errors="coerce").fillna(0)

    by_campaign = cpue.groupby("nome_campanha").agg(
        individuos=("abundancia_total", "sum"),
        biomassa_g=("biomassa_total", "sum"),
        cpuen_total=("cpuen", "sum"),
        cpueb_total=("cpueb", "sum"),
    ).reset_index()

    metrics = {
        "taxa_total": int(len(comp)),
        "ordens": int(comp["Ordem"].nunique()) if "Ordem" in comp.columns else None,
        "familias": int(comp["Familia"].nunique()) if "Familia" in comp.columns else None,
        "individuos_total": int(abundance["abundancia_total"].sum()),
        "biomassa_total_g": float(bio_rows[biomass_col].sum()),
        "campanhas": sorted(richness["nome_campanha"].dropna().astype(str).unique().tolist()),
        "pontos": sorted(richness["nome_ponto"].dropna().astype(str).unique().tolist()),
        "max_riqueza": max_rich,
        "max_abundancia": max_abund,
        "max_cpuen": max_cpuen,
        "max_cpueb": max_cpueb,
        "diversidade_geral": geral.to_dict("records"),
        "suficiencia_final": suff_last,
        "por_campanha": by_campaign.to_dict("records"),
    }
    return metrics


def table_html(rows: list[dict], columns: list[str]) -> str:
    head = "".join(f"<th>{html.escape(COLUMN_LABELS.get(col, col))}</th>" for col in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(format_value(row.get(col)))}</td>" for col in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def write_report(metrics: dict) -> Path:
    out_html = OUTPUT_DIR / f"relatorio_tecnico_ictiofauna_{PACKAGE_SLUG}.html"
    figures = [
        ("02_grafico_riqueza_por_ponto_ictiofauna.png", "Riqueza por ponto"),
        ("03_grafico_abundancia_por_ponto_ictiofauna.png", "Abundância por ponto"),
        ("06_grafico_cpuen_por_ponto_ictiofauna.png", "CPUEn por ponto"),
        ("07_grafico_cpueb_por_ponto_ictiofauna.png", "CPUEb por ponto"),
        ("14_grafico_sintese_ecologica_ictiofauna.png", "Síntese ecológica"),
        ("10_grafico_diversidade_alfa_ictiofauna.png", "Diversidade alfa"),
        ("11_dendrograma_similaridade_ictiofauna_seca_chuva_somadas.png", "Similaridade"),
        ("12_curva_suficiencia_amostral_ictiofauna.png", "Suficiência amostral"),
    ]
    figure_blocks = []
    for name, caption in figures:
        if (OUTPUT_DIR / name).exists():
            figure_blocks.append(
                f'<figure><img src="{html.escape(name)}" alt="{html.escape(caption)}">'
                f"<figcaption>{html.escape(caption)}</figcaption></figure>"
            )

    richness = metrics["max_riqueza"]
    abundance = metrics["max_abundancia"]
    cpuen = metrics["max_cpuen"]
    cpueb = metrics["max_cpueb"]
    suff = metrics["suficiencia_final"]

    body = f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>{html.escape(REPORT_TITLE)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ color: #11420C; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #d6d6d6; border-radius: 6px; padding: 12px; }}
    .value {{ font-size: 24px; font-weight: 700; color: #11420C; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d6d6d6; padding: 7px 9px; text-align: left; }}
    th {{ background: #eef4ec; }}
    figure {{ margin: 24px 0; page-break-inside: avoid; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #e5e7eb; }}
    figcaption {{ font-size: 13px; color: #4b5563; margin-top: 6px; }}
    .note {{ background: #f7faf5; border-left: 4px solid #11420C; padding: 10px 12px; }}
  </style>
</head>
<body>
  <h1>{html.escape(REPORT_TITLE)}</h1>
  <p>Pacote diagnóstico gerado para as campanhas {html.escape(', '.join(metrics['campanhas']))}, com {len(metrics['pontos'])} pontos amostrais.</p>
  <div class="cards">
    <div class="card"><div class="value">{metrics['taxa_total']}</div><div>táxons</div></div>
    <div class="card"><div class="value">{metrics['individuos_total']}</div><div>indivíduos</div></div>
    <div class="card"><div class="value">{metrics['biomassa_total_g']:.1f} g</div><div>biomassa</div></div>
    <div class="card"><div class="value">{metrics['ordens']}</div><div>ordens</div></div>
    <div class="card"><div class="value">{metrics['familias']}</div><div>famílias</div></div>
  </div>

  <h2>Síntese por campanha</h2>
  {table_html(metrics['por_campanha'], ['nome_campanha', 'individuos', 'biomassa_g', 'cpuen_total', 'cpueb_total'])}

  <h2>Destaques diagnósticos</h2>
  <ul>
    <li>Maior riqueza: {html.escape(str(richness['nome_ponto']))} em {html.escape(str(richness['nome_campanha']))}, com {format_value(richness['riqueza'])} táxons.</li>
    <li>Maior abundância: {html.escape(str(abundance['nome_ponto']))} em {html.escape(str(abundance['nome_campanha']))}, com {format_value(abundance['abundancia_total'])} indivíduos.</li>
    <li>Maior CPUEn: {html.escape(str(cpuen['nome_ponto']))} em {html.escape(str(cpuen['nome_campanha']))}, com {format_value(cpuen['cpuen'])} ind/100 m².</li>
    <li>Maior CPUEb: {html.escape(str(cpueb['nome_ponto']))} em {html.escape(str(cpueb['nome_campanha']))}, com {format_value(cpueb['cpueb'])} g/100 m².</li>
    <li>Riqueza observada final na curva de suficiência: {format_value(suff['riqueza_obs_media'])}; Jackknife 1: {format_value(suff['riqueza_est_jackknife1_media'])}.</li>
  </ul>

  <h2>Diversidade alfa</h2>
  {table_html(metrics['diversidade_geral'], ['nome_campanha', 'nome_ponto', 'Shannon_H', 'Pielou_J'])}
  <p class="note">Os índices de diversidade e a curva de suficiência devem ser interpretados como apoio diagnóstico, pois o conjunto atual tem baixa riqueza total e apenas duas campanhas.</p>

  <h2>Figuras principais</h2>
  {''.join(figure_blocks)}

  <h2>Rastreabilidade</h2>
  <p>Manifesto: <code>manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.json</code> e <code>manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.xlsx</code>.</p>
</body>
</html>
"""
    validate_report_ptbr(body)
    out_html.write_text(body, encoding="utf-8")
    return out_html


def build_manifest(extra_files: list[Path], metrics: dict) -> tuple[Path, Path, Path]:
    files = []
    for path in sorted(OUTPUT_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.name == "desktop.ini" or path.name.startswith("~$"):
            continue
        if path.name.startswith(f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}"):
            continue
        files.append(path)

    rows = []
    for path in files:
        rows.append(
            {
                "arquivo": path.name,
                "extensao": path.suffix.lower().lstrip("."),
                "tamanho_bytes": path.stat().st_size,
                "modificado_em": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z"),
                "sha256": sha256(path),
            }
        )

    manifest = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "project_code": PROJECT_CODE,
        "project_id": PROJECT_ID,
        "group": "Ictiofauna",
        "campaigns": metrics["campanhas"],
        "output_dir": str(OUTPUT_DIR),
        "summary": {
            "taxa_total": metrics["taxa_total"],
            "individuos_total": metrics["individuos_total"],
            "biomassa_total_g": metrics["biomassa_total_g"],
            "ordens": metrics["ordens"],
            "familias": metrics["familias"],
        },
        "files_count": len(rows),
        "files": rows,
    }

    out_json = OUTPUT_DIR / f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.json"
    out_xlsx = OUTPUT_DIR / f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.xlsx"
    out_md = OUTPUT_DIR / f"manifesto_entrega_ictiofauna_{PACKAGE_SLUG}.md"

    out_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(rows).to_excel(out_xlsx, index=False, engine="openpyxl")

    lines = [
        f"# {PROJECT_CODE} - Manifesto de entrega - Ictiofauna",
        "",
        f"- gerado em: `{manifest['generated_at']}`",
        f"- arquivos listados: `{len(rows)}`",
        f"- taxons: `{metrics['taxa_total']}`",
        f"- indivíduos: `{metrics['individuos_total']}`",
        f"- biomassa total: `{metrics['biomassa_total_g']:.1f} g`",
        "",
        "## Arquivos",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['arquivo']}` ({row['extensao']}, {row['tamanho_bytes']} bytes)")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_json, out_xlsx, out_md


def write_validation(manifest_json: Path) -> Path:
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    files = manifest.get("files", [])
    missing = [row["arquivo"] for row in files if not (OUTPUT_DIR / row["arquivo"]).exists()]
    zero_size = [row["arquivo"] for row in files if (OUTPUT_DIR / row["arquivo"]).exists() and (OUTPUT_DIR / row["arquivo"]).stat().st_size <= 0]
    validation = {
        "validated_at": now_iso(),
        "status": "OK" if not missing and not zero_size else "ERROR",
        "files_checked": len(files),
        "missing_files": missing,
        "zero_size_files": zero_size,
        "errors_count": len(missing) + len(zero_size),
        "warnings": [
            "Diversidade, similaridade e suficiência são apoio diagnóstico para base curta."
        ],
    }
    out = OUTPUT_DIR / f"validacao_entrega_ictiofauna_{PACKAGE_SLUG}.json"
    out.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    comp = read_xlsx("01_tabela_composicao_ictiofauna.xlsx")
    ecological_files = write_ecological_outputs(comp)
    metrics = compute_metrics()
    report = write_report(metrics)
    manifest_json, manifest_xlsx, manifest_md = build_manifest(ecological_files + [report], metrics)
    validation = write_validation(manifest_json)

    print("Generated delivery package:")
    for path in ecological_files + [report, manifest_json, manifest_xlsx, manifest_md, validation]:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
