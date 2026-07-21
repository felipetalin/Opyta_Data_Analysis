from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CODE = "BRAANG01"
MATRIX = "Efluente"
PARAM = "Demanda Bioqu\u00edmica de Oxig\u00eanio"
REVISION = "R06_efluente_dbo_pontos_20260710"
DEFAULT_RESULTS_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados"
)
DEFAULT_REV_ROOT = DEFAULT_RESULTS_ROOT / "_revisoes" / REVISION
GROUPS = {
    "MCB907E_MCB907S": ["MCB907E", "MCB907S"],
    "MCB1005": ["MCB1005"],
}

MCB907_SELECTED_CAMPAIGNS = [
    ("jan-2021", "2021-01"),
    ("mar-2021", "2021-03"),
    ("jul-2021", "2021-07"),
    ("set-2021", "2021-09"),
    ("dez-2021", "2021-12"),
    ("mar-2022", "2022-03"),
    ("jun-2022", "2022-06"),
    ("set-2022", "2022-09"),
    ("dez-2022", "2022-12"),
    ("mar-2023", "2023-03"),
    ("jun-2023", "2023-06"),
    ("set-2023", "2023-09"),
    ("nov-2023", "2023-11"),
    ("mar-2024", "2024-03"),
    ("jun-2024", "2024-06"),
    ("set-2024", "2024-09"),
    ("nov-2024", "2024-11"),
    ("mar-2025", "2025-03"),
    ("jun-2025", "2025-06"),
]


def revision_root() -> Path:
    return Path(os.environ.get("BRAANG01_EFLUENTE_DBO_R06_ROOT", str(DEFAULT_REV_ROOT)))


def safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(" ", "_")


def format_limit(value: float) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def first_notna(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    values = df[column].dropna()
    return float(values.iloc[0]) if not values.empty else None


def load_data() -> pd.DataFrame:
    load_dotenv(REPO_ROOT / ".env")
    db_url = os.environ.get("FISICO_DB_URL")
    if not db_url:
        raise RuntimeError("FISICO_DB_URL nao encontrado no .env")
    query = text(
        """
        SELECT *
        FROM public.fisico_analise_consolidada
        WHERE codigo_interno_opyta = :code
          AND matriz = :matrix
          AND nome_ponto = ANY(:points)
          AND nome_parametro = :param
        """
    )
    points = [point for group in GROUPS.values() for point in group]
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '15min'"))
        df = pd.read_sql(
            query,
            conn,
            params={"code": PROJECT_CODE, "matrix": MATRIX, "points": points, "param": PARAM},
        )
    for col in ["valor_medido", "vmp_430_padrao"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["data_hora_coleta"] = pd.to_datetime(df["data_hora_coleta"], errors="coerce")
    df["ano_mes"] = df["data_hora_coleta"].dt.strftime("%Y-%m")
    return df.sort_values(["nome_ponto", "data_hora_coleta"])


def configure_axis(ax, unit: str, point: str, tick_interval: int) -> None:
    ax.set_title(f"Ponto {point}", fontsize=28, fontweight="bold", loc="left", family="Arial", pad=20)
    ax.set_ylabel(unit, fontsize=22, fontweight="bold", family="Arial")
    ax.set_xlabel("Campanhas", fontsize=20, family="Arial")
    ax.yaxis.grid(True, linestyle="-", alpha=0.40, color="#CCCCCC")
    ax.tick_params(axis="y", labelsize=16)
    ax.tick_params(axis="x", rotation=90, labelsize=16)
    formatter = mticker.ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((-3, 4))
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.get_offset_text().set_fontsize(16)
    ax.yaxis.get_offset_text().set_family("Arial")
    if tick_interval > 1:
        ticks = ax.get_xticks()
        labels = [item.get_text() for item in ax.get_xticklabels()]
        keep = set(range(0, len(labels), tick_interval))
        if labels:
            keep.add(len(labels) - 1)
        kept = sorted(keep)
        ax.set_xticks([ticks[i] for i in kept if i < len(ticks)])
        ax.set_xticklabels([labels[i] for i in kept if i < len(labels)])


def plot_group(df: pd.DataFrame, group_name: str, points: list[str], out_dir: Path) -> dict[str, object]:
    d = df[df["nome_ponto"].isin(points)].copy()
    if group_name == "MCB907E_MCB907S":
        selected_months = [month for _label, month in MCB907_SELECTED_CAMPAIGNS]
        d = d[d["ano_mes"].isin(selected_months)].copy()
        x_order = {month: idx for idx, month in enumerate(selected_months)}
        d["_x"] = d["ano_mes"].map(x_order)
        campaigns = [label for label, _month in MCB907_SELECTED_CAMPAIGNS]
        tick_interval = 1
        periodicity = "campanhas_trimestrais_selecionadas"
    else:
        unique = (
            d[["nome_campanha", "data_hora_coleta"]]
            .drop_duplicates()
            .sort_values("data_hora_coleta")
        )
        campaigns = unique["nome_campanha"].tolist()
        x_order = {campaign: idx for idx, campaign in enumerate(campaigns)}
        d["_x"] = d["nome_campanha"].map(x_order)
        tick_interval = 3
        periodicity = "mensal"
    x_ticks = list(range(len(campaigns)))
    unit_values = d["unidade_medida"].dropna()
    unit = str(unit_values.iloc[0]) if not unit_values.empty else "-"

    fig, axes = plt.subplots(len(points), 1, figsize=(19.25, 5.5 * len(points)), squeeze=False)
    axes_flat = [ax for row in axes for ax in row]
    audit = []
    for ax, point in zip(axes_flat, points):
        point_data = d[d["nome_ponto"] == point].copy().sort_values("_x")
        point_data = point_data.dropna(subset=["valor_medido"])
        ax.plot(
            point_data["_x"],
            point_data["valor_medido"],
            marker="o",
            markersize=12,
            color="#2E7D32",
            linewidth=4,
            zorder=4,
        )
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(campaigns)
        configure_axis(ax, unit, point, tick_interval)

        limit = first_notna(point_data, "vmp_430_padrao")
        visible_limits = []
        if limit is not None:
            ax.axhline(
                limit,
                color="red",
                linestyle="--",
                linewidth=3,
                label=f"VMP - m\u00e1ximo: {format_limit(limit)}",
                zorder=2,
            )
            visible_limits.append(limit)
            ax.axhspan(limit, ax.get_ylim()[1] * 20, color="red", alpha=0.07, zorder=0)

        data_max = point_data["valor_medido"].max()
        if pd.isna(data_max):
            data_max = max(visible_limits) if visible_limits else 1.0
        top = max(float(data_max), max(visible_limits) if visible_limits else float(data_max))
        if not math.isfinite(top) or top <= 0:
            top = 1.0
        ax.set_ylim(-0.02 * top * 1.22, top * 1.22)
        if visible_limits:
            legend_loc = "upper left" if group_name == "MCB907E_MCB907S" and point == "MCB907E" else "upper right"
            ax.legend(loc=legend_loc, frameon=True, fontsize=16, facecolor="white", framealpha=1)
        audit.append(
            {
                "point": point,
                "rows": int(len(point_data)),
                "max_value": float(point_data["valor_medido"].max()),
                "vmp_visible": limit,
            }
        )

    fig.subplots_adjust(top=0.80, hspace=0.95)
    title = fill(f"{PARAM} (Efluente)", width=58)
    fig.suptitle(title, fontsize=36, fontweight="bold", family="Arial", y=0.985)
    output = out_dir / f"ST_{safe_filename(PARAM)}_{group_name}.png"
    fig.savefig(output, dpi=600, bbox_inches="tight")
    plt.close(fig)
    return {
        "group": group_name,
        "points": points,
        "file": output.name,
        "periodicity": periodicity,
        "campaign_count": len(campaigns),
        "campaigns": campaigns,
        "audit": audit,
    }


def copy_baseline(rev_root: Path) -> None:
    baseline_dir = rev_root / "linha_base" / "Efluente_DBO"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    sources = [
        DEFAULT_RESULTS_ROOT / "_revisoes" / "R02_efluente_mcb907_periodicidade_20260709" / "revisado" / "Efluente_MCB907" / "ST_Demanda_Bioqu\u00edmica_de_Oxig\u00eanio_MCB907_mensal.png",
        DEFAULT_RESULTS_ROOT / "_revisoes" / "R03_efluente_mcb1005_20260709" / "revisado" / "Efluente_MCB1005" / "ST_Demanda_Bioqu\u00edmica_de_Oxig\u00eanio_MCB1005.png",
    ]
    for source in sources:
        if source.exists():
            shutil.copy2(source, baseline_dir / source.name)


def clear_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for item in path.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json"}:
            item.unlink()


def write_manifest(root: Path, subdir: Path, filename: str) -> None:
    rows = ["sha256,bytes,relative_path"]
    for item in sorted(subdir.iterdir(), key=lambda p: p.name):
        if item.is_file() and item.name != "desktop.ini":
            digest = hashlib.sha256(item.read_bytes()).hexdigest()
            rows.append(f"{digest},{item.stat().st_size},{item.relative_to(root).as_posix()}")
    (root / filename).write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    rev_root = revision_root()
    out_dir = rev_root / "revisado" / "Efluente_DBO"
    scripts_dir = rev_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    copy_baseline(rev_root)
    clear_dir(out_dir)
    shutil.copy2(Path(__file__), scripts_dir / Path(__file__).name)

    df = load_data()
    results = [plot_group(df, group_name, points, out_dir) for group_name, points in GROUPS.items()]
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "revision": REVISION,
        "param": PARAM,
        "groups": GROUPS,
        "mcb907_selected_campaigns": [label for label, _month in MCB907_SELECTED_CAMPAIGNS],
        "vmp_source_column": "vmp_430_padrao",
        "expected_vmp_mg_l": 60.0,
        "output_dir": str(out_dir),
        "png_count": len(list(out_dir.glob("*.png"))),
        "results": results,
    }
    (out_dir / "revision_generation_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_manifest(rev_root, rev_root / "linha_base" / "Efluente_DBO", "manifest_linha_base_sha256.csv")
    write_manifest(rev_root, out_dir, "manifest_revisado_sha256.csv")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()
