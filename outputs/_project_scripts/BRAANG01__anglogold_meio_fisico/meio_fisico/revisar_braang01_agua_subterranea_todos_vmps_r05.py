from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from revisar_braang01_agua_subterranea_dessedentacao import (
    MATRIX,
    OUTPUT_SUBDIR,
    PROJECT_CODE,
    REPO_ROOT,
    campaign_key,
    configure_axis,
    format_limit,
    load_data,
    safe_plot_filename,
)


REVISION = "R05_todos_os_vmps_20260710"
BASE_REVISION = "R05_agua_subterranea_vmp_dissolvidos_20260710"
DEFAULT_RESULTS_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados"
)
DEFAULT_REV_ROOT = DEFAULT_RESULTS_ROOT / "_revisoes" / REVISION
BASE_REV_ROOT = DEFAULT_RESULTS_ROOT / "_revisoes" / BASE_REVISION

TARGET_PARAMS = [
    "Ars\u00eanio Dissolvido",
    "Ars\u00eanio Total",
    "Cobalto Dissolvido",
    "Cobre Dissolvido",
    "Cromo Dissolvido",
    "S\u00f3lidos Dissolvidos Totais",
    "Sulfato",
    "Zinco Dissolvido",
    "pH",
]

USE_LIMITS_MG_L = {
    "Ars\u00eanio Dissolvido": {
        "Consumo Humano": 0.01,
        "Dessedenta\u00e7\u00e3o": 0.2,
        "Irriga\u00e7\u00e3o": 0.05,
        "Recrea\u00e7\u00e3o": 0.008,
    },
    "Ars\u00eanio Total": {
        "Consumo Humano": 0.01,
        "Dessedenta\u00e7\u00e3o": 0.2,
        "Irriga\u00e7\u00e3o": 0.05,
        "Recrea\u00e7\u00e3o": 0.008,
    },
    "Cobalto Dissolvido": {
        "Dessedenta\u00e7\u00e3o": 1.0,
        "Irriga\u00e7\u00e3o": 0.05,
        "Recrea\u00e7\u00e3o": 0.01,
    },
    "Cobre Dissolvido": {
        "Consumo Humano": 2.0,
        "Dessedenta\u00e7\u00e3o": 0.5,
        "Irriga\u00e7\u00e3o": 0.2,
        "Recrea\u00e7\u00e3o": 1.0,
    },
    "Cromo Dissolvido": {
        "Consumo Humano": 0.05,
        "Dessedenta\u00e7\u00e3o": 1.0,
        "Irriga\u00e7\u00e3o": 0.1,
        "Recrea\u00e7\u00e3o": 0.05,
    },
    "S\u00f3lidos Dissolvidos Totais": {
        "Consumo Humano": 1000.0,
    },
    "Sulfato": {
        "Consumo Humano": 250.0,
        "Dessedenta\u00e7\u00e3o": 1000.0,
        "Irriga\u00e7\u00e3o": 400.0,
        "Recrea\u00e7\u00e3o": 5.0,
    },
    "Zinco Dissolvido": {
        "Consumo Humano": 5.0,
        "Dessedenta\u00e7\u00e3o": 24.0,
        "Irriga\u00e7\u00e3o": 2.0,
        "Recrea\u00e7\u00e3o": 5.0,
    },
}

USE_COLORS = {
    "Consumo Humano": "#D62728",
    "Dessedenta\u00e7\u00e3o": "#8B4513",
    "Irriga\u00e7\u00e3o": "#006400",
    "Recrea\u00e7\u00e3o": "#1F77B4",
}


def revision_root() -> Path:
    return Path(os.environ.get("BRAANG01_GW_ALL_VMP_R05_ROOT", str(DEFAULT_REV_ROOT)))


def prepare_dirs() -> tuple[Path, Path]:
    rev_root = revision_root()
    baseline_dir = rev_root / "linha_base" / OUTPUT_SUBDIR
    out_dir = rev_root / "revisado" / OUTPUT_SUBDIR
    scripts_dir = rev_root / "scripts"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    base_source = BASE_REV_ROOT / "revisado" / OUTPUT_SUBDIR
    for param in TARGET_PARAMS:
        for page in (1, 2):
            source = base_source / safe_plot_filename(param, page)
            if source.exists():
                shutil.copy2(source, baseline_dir / source.name)
    for item in out_dir.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json"}:
            item.unlink()
    shutil.copy2(Path(__file__), scripts_dir / Path(__file__).name)
    return baseline_dir, out_dir


def add_all_limits(ax, param: str) -> list[dict[str, object]]:
    limits = []
    for use, value in USE_LIMITS_MG_L.get(param, {}).items():
        ax.axhline(
            value,
            color=USE_COLORS[use],
            linestyle="--",
            linewidth=3.2,
            label=f"VMP - {use}: {format_limit(value)}",
            zorder=2,
        )
        limits.append({"uso": use, "valor": value})
    return limits


def plot_param(df_param: pd.DataFrame, param: str, out_dir: Path) -> dict[str, object]:
    points = list(df_param["nome_ponto"].dropna().unique())
    point_groups = [points[i : i + 3] for i in range(0, len(points), 3)]
    unit_values = df_param["unidade_medida"].dropna()
    unit = str(unit_values.iloc[0]) if not unit_values.empty else "-"
    files = []
    audit = []

    for page_index, group in enumerate(point_groups, start=1):
        group_data = df_param[df_param["nome_ponto"].isin(group)].copy()
        campaigns = (
            group_data[["nome_campanha", "ordem_cron"]]
            .drop_duplicates()
            .sort_values("ordem_cron")["nome_campanha"]
            .tolist()
        )
        x_map = {campaign: idx for idx, campaign in enumerate(campaigns)}

        fig, axes = plt.subplots(
            len(group),
            1,
            figsize=(19.25, 5.5 * max(len(group), 1)),
            squeeze=False,
        )
        axes_flat = [ax for row in axes for ax in row]

        for ax, point_label in zip(axes_flat, group):
            point_data = group_data[group_data["nome_ponto"] == point_label].sort_values("ordem_cron")
            point_data = point_data.dropna(subset=["valor_medido"])
            x_values = [x_map[c] for c in point_data["nome_campanha"]]
            ax.plot(
                x_values,
                point_data["valor_medido"],
                marker="o",
                markersize=12,
                color="#2E7D32",
                linewidth=4,
                zorder=4,
            )
            ax.set_xticks(range(len(campaigns)))
            ax.set_xticklabels(campaigns)
            configure_axis(ax, unit, str(point_label))

            limits = add_all_limits(ax, param)
            values = [float(item["valor"]) for item in limits]
            data_max = point_data["valor_medido"].max()
            if pd.isna(data_max):
                data_max = max(values) if values else 1.0
            if values:
                ax.axhspan(min(values), ax.get_ylim()[1] * 20, color="red", alpha=0.05, zorder=0)
            top = max(float(data_max), max(values) if values else float(data_max))
            if not math.isfinite(top) or top <= 0:
                top = 1.0
            ax.set_ylim(-0.02 * top * 1.3, top * 1.3)
            if limits:
                ax.legend(loc="upper right", frameon=True, fontsize=13, facecolor="white", framealpha=1)
            audit.append({"point": str(point_label), "rows": int(len(point_data)), "limits": limits})

        fig.subplots_adjust(top=0.80 if len(group) <= 2 else 0.90, hspace=0.95 if len(group) <= 2 else 0.80)
        fig.suptitle(
            f"{param} ({MATRIX})",
            fontsize=36,
            fontweight="bold",
            family="Arial",
            y=0.985,
        )
        output = out_dir / safe_plot_filename(param, page_index)
        fig.savefig(output, dpi=600, bbox_inches="tight")
        plt.close(fig)
        files.append(output.name)
    return {"param": param, "files": files, "audit": audit}


def write_manifest(root: Path, subdir: Path, filename: str) -> None:
    rows = ["sha256,bytes,relative_path"]
    for item in sorted(subdir.iterdir(), key=lambda p: p.name):
        if item.is_file() and item.name != "desktop.ini":
            rows.append(
                f"{hashlib.sha256(item.read_bytes()).hexdigest()},{item.stat().st_size},{item.relative_to(root).as_posix()}"
            )
    (root / filename).write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    baseline_dir, out_dir = prepare_dirs()
    df = load_data()
    df = df[df["nome_parametro"].isin(TARGET_PARAMS)].copy()
    df["ordem_cron"] = df["nome_campanha"].apply(campaign_key)
    results = []
    for param in TARGET_PARAMS:
        df_param = df[df["nome_parametro"] == param].sort_values("ordem_cron")
        if not df_param.empty:
            results.append(plot_param(df_param, param, out_dir))
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "revision": REVISION,
        "base_revision": BASE_REVISION,
        "scenario": "todos_os_usos_conama_396_2008",
        "legal_limit_source": "Resolucao CONAMA 396/2008, Anexo I.",
        "target_params": TARGET_PARAMS,
        "limits_mg_l": USE_LIMITS_MG_L,
        "output_dir": str(out_dir),
        "png_count": len(list(out_dir.glob("ST_*.png"))),
        "results": results,
    }
    (out_dir / "revision_generation_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    root = revision_root()
    write_manifest(root, baseline_dir, "manifest_linha_base_sha256.csv")
    write_manifest(root, out_dir, "manifest_revisado_sha256.csv")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()
