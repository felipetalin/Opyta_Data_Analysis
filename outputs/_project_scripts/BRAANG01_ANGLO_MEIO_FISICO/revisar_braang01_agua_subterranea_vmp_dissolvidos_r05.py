from __future__ import annotations

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
    VMP_COLOR,
    VMP_COLUMN,
    VMP_LABEL,
    campaign_key,
    configure_axis,
    format_limit,
    load_data,
    safe_plot_filename,
)


REVISION = "R05_agua_subterranea_vmp_dissolvidos_20260710"
PREVIOUS_REVISION = "R01_agua_subterranea_dessedentacao_20260709"

DEFAULT_RESULTS_ROOT = Path(
    "G:/Meu Drive/Opyta/Clientes/Clientes/Clientes/Brandt/Anglo/dados/"
    "Migra\u00e7\u00e3o e resultados/Resultados"
)
DEFAULT_REV_ROOT = DEFAULT_RESULTS_ROOT / "_revisoes" / REVISION
DEFAULT_BASELINE_ROOT = DEFAULT_RESULTS_ROOT / "_revisoes" / PREVIOUS_REVISION

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

# Valores em mg/L. Limite legal: Resolucao CONAMA 396/2008, Anexo I.
# A legenda visual permanece como VMP - Dessedentacao para preservar o layout.
# Para especies dissolvidas, o limite legal do analito foi aplicado por equivalencia.
VMP_EQUIVALENCE = {
    "Ars\u00eanio Dissolvido": 0.2,
    "Cobalto Dissolvido": 1.0,
    "Cobre Dissolvido": 0.5,
    "Cromo Dissolvido": 1.0,
    "Zinco Dissolvido": 24.0,
}

VMP_NOTES = {
    "Ars\u00eanio Dissolvido": "Limite legal CONAMA 396/2008 aplicado ao parametro dissolvido por equivalencia do analito.",
    "Cobalto Dissolvido": "Limite legal CONAMA 396/2008 aplicado ao parametro dissolvido por equivalencia do analito.",
    "Cobre Dissolvido": "Limite legal CONAMA 396/2008 aplicado ao parametro dissolvido por equivalencia do analito.",
    "Cromo Dissolvido": "Limite legal CONAMA 396/2008 aplicado ao parametro dissolvido por equivalencia do analito.",
    "Zinco Dissolvido": "Limite legal CONAMA 396/2008 aplicado ao parametro dissolvido por equivalencia do analito.",
}


def revision_root() -> Path:
    return Path(os.environ.get("BRAANG01_GW_R05_ROOT", str(DEFAULT_REV_ROOT)))


def baseline_root() -> Path:
    return Path(os.environ.get("BRAANG01_GW_R05_BASELINE", str(DEFAULT_BASELINE_ROOT)))


def target_files() -> list[str]:
    names: list[str] = []
    for param in TARGET_PARAMS:
        for page in (1, 2):
            names.append(safe_plot_filename(param, page))
    return names


def prepare_revision_dirs() -> tuple[Path, Path]:
    rev_root = revision_root()
    baseline_dir = rev_root / "linha_base" / OUTPUT_SUBDIR
    out_dir = rev_root / "revisado" / OUTPUT_SUBDIR
    scripts_dir = rev_root / "scripts"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    source_dir = baseline_root() / "revisado" / OUTPUT_SUBDIR
    for filename in target_files():
        source = source_dir / filename
        if source.exists():
            shutil.copy2(source, baseline_dir / filename)

    for item in out_dir.iterdir():
        if item.is_file() and item.suffix.lower() in {".png", ".json"}:
            item.unlink()

    shutil.copy2(Path(__file__), scripts_dir / Path(__file__).name)
    return baseline_dir, out_dir


def get_limit(point_data: pd.DataFrame, param: str) -> tuple[float | None, str]:
    if param in VMP_EQUIVALENCE:
        return VMP_EQUIVALENCE[param], VMP_NOTES[param]
    values = point_data[VMP_COLUMN].dropna()
    if not values.empty:
        return float(values.iloc[0]), "Limite legal CONAMA 396/2008 preenchido no consolidado."
    return None, "Sem limite legal CONAMA 396/2008 identificado para este parametro."


def plot_param(df_param: pd.DataFrame, param: str, out_dir: Path) -> dict:
    points = list(df_param["nome_ponto"].dropna().unique())
    point_groups = [points[i : i + 3] for i in range(0, len(points), 3)]
    unit_series = df_param["unidade_medida"].dropna()
    unit = str(unit_series.iloc[0]) if not unit_series.empty else "-"
    generated_files: list[str] = []
    point_audit: list[dict[str, object]] = []

    for page_index, group in enumerate(point_groups, start=1):
        group_data = df_param[df_param["nome_ponto"].isin(group)].copy()
        campaigns = (
            group_data[["nome_campanha", "ordem_cron"]]
            .drop_duplicates()
            .sort_values("ordem_cron")["nome_campanha"]
            .tolist()
        )
        x_map = {campaign: idx for idx, campaign in enumerate(campaigns)}

        fig_height = 5.5 * max(len(group), 1)
        fig, axes = plt.subplots(
            len(group),
            1,
            figsize=(5.5 * 3.5, fig_height),
            squeeze=False,
        )
        axes_flat = [ax for row in axes for ax in row]

        for ax, point_label in zip(axes_flat, group):
            point_data = group_data[group_data["nome_ponto"] == point_label].sort_values(
                "ordem_cron"
            )
            point_data = point_data.dropna(subset=["valor_medido"])
            x_values = [x_map[c] for c in point_data["nome_campanha"]]

            ax.plot(
                x_values,
                point_data["valor_medido"],
                marker="o",
                markersize=12,
                color="#2E7D32",
                linewidth=4,
            )
            ax.set_xticks(range(len(campaigns)))
            ax.set_xticklabels(campaigns)
            configure_axis(ax, unit, point_label)

            limit_value, note = get_limit(point_data, param)
            visible_limits: list[float] = []
            if limit_value is not None:
                ax.axhline(
                    limit_value,
                    color=VMP_COLOR,
                    linestyle="--",
                    linewidth=3.5,
                    label=f"{VMP_LABEL}: {format_limit(limit_value)}",
                )
                visible_limits.append(limit_value)
                ax.axhspan(limit_value, ax.get_ylim()[1] * 20, color="red", alpha=0.07, zorder=0)

            data_max = point_data["valor_medido"].max()
            if pd.isna(data_max):
                data_max = 0.0
            limit_max = max(visible_limits) if visible_limits else data_max
            top = max(float(data_max), float(limit_max))
            if not math.isfinite(top) or top <= 0:
                top = 1.0
            top *= 1.3
            ax.set_ylim(-0.02 * top, top)
            if visible_limits:
                ax.legend(
                    loc="upper right",
                    frameon=True,
                    fontsize=16,
                    facecolor="white",
                    framealpha=1,
                )
            point_audit.append(
                {
                    "point": str(point_label),
                    "rows": int(len(point_data)),
                    "vmp_visible": limit_value,
                    "vmp_note": note,
                }
            )

        top_margin = 0.80 if len(group) <= 2 else 0.90
        hspace = 0.95 if len(group) <= 2 else 0.80
        fig.subplots_adjust(top=top_margin, hspace=hspace)
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
        generated_files.append(output.name)

    return {"param": param, "files": generated_files, "points": point_audit}


def write_manifest(root: Path, subdir: Path, name: str) -> None:
    import hashlib

    rows = ["sha256,bytes,relative_path"]
    for item in sorted(subdir.iterdir(), key=lambda p: p.name):
        if not item.is_file() or item.name == "desktop.ini":
            continue
        digest = hashlib.sha256(item.read_bytes()).hexdigest()
        rel = item.relative_to(root).as_posix()
        rows.append(f"{digest},{item.stat().st_size},{rel}")
    (root / name).write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    baseline_dir, out_dir = prepare_revision_dirs()
    df = load_data()
    df = df[df["nome_parametro"].isin(TARGET_PARAMS)].copy()
    df["ordem_cron"] = df["nome_campanha"].apply(campaign_key)

    results = []
    for param in TARGET_PARAMS:
        df_param = df[df["nome_parametro"] == param].sort_values("ordem_cron")
        if df_param.empty:
            results.append({"param": param, "status": "missing"})
            continue
        results.append(plot_param(df_param, param, out_dir))

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_code": PROJECT_CODE,
        "matrix": MATRIX,
        "revision": REVISION,
        "previous_revision": PREVIOUS_REVISION,
        "output_dir": str(out_dir),
        "target_params": TARGET_PARAMS,
        "vmp_column_used": VMP_COLUMN,
        "vmp_equivalence_mg_l": VMP_EQUIVALENCE,
        "legal_limit_source": "Limite legal - Resolucao CONAMA 396/2008, Anexo I.",
        "legend_kept_as": VMP_LABEL,
        "temporal_png_count": len(list(out_dir.glob("ST_*.png"))),
        "results": results,
    }
    with (out_dir / "revision_generation_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    root = revision_root()
    write_manifest(root, baseline_dir, "manifest_linha_base_sha256.csv")
    write_manifest(root, out_dir, "manifest_revisado_sha256.csv")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()
