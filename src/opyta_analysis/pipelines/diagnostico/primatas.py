from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import matplotlib.patches as mpatches
from matplotlib.patches import Circle, FancyBboxPatch
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from opyta_analysis.supabase_client import get_client, paginate
from opyta_analysis.theme import apply_theme, get_figsize_by_complexity, get_tight_layout_rect, place_legend_below_x_axis
from opyta_analysis.validators import validate_axes_style
from . import mastofauna as masto


TARGET_PCH_NAME = "Senhora do Porto"
TARGET_CONTROL_NAME = "Área Controle"

_PCH_NAME_BY_FOLDER_KEY = {
    "dores de guanhaes": "Dores de Guanhães",
    "pch dores de guanhaes": "Dores de Guanhães",
    "fortuna ii": "Fortuna II",
    "pch fortuna ii": "Fortuna II",
    "senhora do porto": "Senhora do Porto",
    "pch senhora do porto": "Senhora do Porto",
    "jacara": "Jacaré",
    "jacare": "Jacaré",
    "pch jacara": "Jacaré",
    "pch jacare": "Jacaré",
}

# Slugs usados no nome do relatório por pasta de empreendimento
_SLUG_MAP = {
    "dores de guanhaes": "DGN",
    "pch dores de guanhaes": "DGN",
    "fortuna ii": "FII",
    "pch fortuna ii": "FII",
    "senhora do porto": "SPT",
    "pch senhora do porto": "SPT",
    "jacara": "JAC",
    "jacare": "JAC",
    "pch jacara": "JAC",
    "pch jacare": "JAC",
    "area controle": "CTRL",
    "controle": "CTRL",
}


def _enterprise_slug_for_dir(output_dir: Path) -> str:
    key = masto._norm(output_dir.name)
    if key in _SLUG_MAP:
        return _SLUG_MAP[key]
    clean = re.sub(r"[^a-zA-Z0-9]", "", output_dir.name)
    return clean[:4].upper() or "PRIM"


def _infer_pch_name_from_output_dir(output_dir: Path) -> Optional[str]:
    key = masto._norm(output_dir.name)
    return _PCH_NAME_BY_FOLDER_KEY.get(key)


MONTH_MAP_PT = {
    "jan": "Janeiro",
    "fev": "Fevereiro",
    "mar": "Março",
    "abr": "Abril",
    "mai": "Maio",
    "jun": "Junho",
    "jul": "Julho",
    "ago": "Agosto",
    "set": "Setembro",
    "out": "Outubro",
    "nov": "Novembro",
    "dez": "Dezembro",
}


def _canonical_campaign_name(value: object) -> str:
    txt = str(value or "").strip()
    # Ex.: 28a-abr-26-SC -> 28ª-abr-26-SC
    return re.sub(r"^(\d+)a-", r"\1ª-", txt, flags=re.IGNORECASE)


def _canonical_method_name(value: object) -> str:
    txt = str(value or "").strip()
    if masto._norm(txt) == "playback e transecto":
        return "Playback e transecto"
    return txt


def _campaign_label_for_title(campaigns: List[str]) -> str:
    if not campaigns:
        return "Campanha"

    base = str(campaigns[0] or "").strip().lower()
    m = re.search(r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[-_ ]?(\d{2,4})", base)
    if not m:
        m = re.search(r"(\d{2,4})[-_ ]?(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)", base)
        if m:
            year_raw, mon_raw = m.group(1), m.group(2)
        else:
            return str(campaigns[0])
    else:
        mon_raw, year_raw = m.group(1), m.group(2)

    mon = MONTH_MAP_PT.get(mon_raw[:3], mon_raw.title())
    year = int(year_raw)
    if year < 100:
        year += 2000
    return f"{mon} {year}"


def _prepare_primatas_df(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    # 1) Preenche empreendimento ausente pela chave de ponto quando houver mapeamento univoco.
    by_point = (
        data.loc[
            data["empreendimento"].notna() & (data["empreendimento"].map(masto._norm) != "sem empreendimento"),
            ["nome_ponto", "empreendimento"],
        ]
        .dropna()
        .drop_duplicates()
    )
    point_to_emp: dict[str, str] = {}
    if not by_point.empty:
        grouped = by_point.groupby(by_point["nome_ponto"].map(masto._norm))["empreendimento"].unique()
        for key, vals in grouped.items():
            values = [str(v) for v in vals if str(v).strip()]
            if len(values) == 1:
                point_to_emp[key] = values[0]

    sem_emp_mask = data["empreendimento"].map(masto._norm) == "sem empreendimento"
    if sem_emp_mask.any():
        inferred = data.loc[sem_emp_mask, "nome_ponto"].map(lambda p: point_to_emp.get(masto._norm(p), ""))
        inferred_mask = inferred.astype(str).str.strip() != ""
        idx = inferred[inferred_mask].index
        data.loc[idx, "empreendimento"] = inferred.loc[idx]

    # 2) Canoniza valores textuais para consolidar duplicidades 28a/28ª e variacao de caixa.
    data["nome_campanha"] = data["nome_campanha"].map(_canonical_campaign_name)
    data["metodo_de_captura"] = data["metodo_de_captura"].map(_canonical_method_name)

    # 3) Remove duplicatas logicas do mesmo evento amostral.
    dedup_key = [
        data["nome_campanha"].map(masto._norm),
        data["nome_ponto"].map(masto._norm),
        data["nome_cientifico"].map(masto._norm),
        data["tipo_amostragem"].map(masto._norm),
        data["contagem"],
    ]
    pref_has_emp = data["empreendimento"].map(masto._norm) != "sem empreendimento"
    pref_campaign_ordinal = data["nome_campanha"].astype(str).str.contains("ª", na=False)

    ranked = data.assign(
        _k0=dedup_key[0],
        _k1=dedup_key[1],
        _k2=dedup_key[2],
        _k3=dedup_key[3],
        _k4=dedup_key[4],
        _pref_emp=pref_has_emp.astype(int),
        _pref_ord=pref_campaign_ordinal.astype(int),
    )
    ranked = ranked.sort_values(["_pref_emp", "_pref_ord"], ascending=[False, False])
    ranked = ranked.drop_duplicates(subset=["_k0", "_k1", "_k2", "_k3", "_k4"], keep="first")
    ranked = ranked.drop(columns=["_k0", "_k1", "_k2", "_k3", "_k4", "_pref_emp", "_pref_ord"])

    return ranked



def _load_project_empreendimentos(project_id: int, env_file: Optional[str]) -> List[str]:
    sb = get_client(env_file)
    empreendimentos = paginate(
        sb,
        "empreendimentos",
        filters={"id_projeto": int(project_id)},
        select="nome",
    )
    normalized_names: Dict[str, str] = {}
    for item in empreendimentos:
        raw_name = str(item.get("nome", "")).strip()
        if not raw_name:
            continue
        key = masto._norm(raw_name)
        if key == masto._norm(TARGET_CONTROL_NAME):
            normalized_names[key] = TARGET_CONTROL_NAME
        elif key == masto._norm(TARGET_PCH_NAME):
            normalized_names[key] = TARGET_PCH_NAME
        elif key not in normalized_names:
            normalized_names[key] = raw_name

    for required in [TARGET_PCH_NAME, TARGET_CONTROL_NAME]:
        normalized_names[masto._norm(required)] = required

    return sorted(normalized_names.values())


# ---------------------------------------------------------------------------
# Block: Figura 17 – Abundância por espécie/área (composição)
# ---------------------------------------------------------------------------

def _save_fig17_abundancia(
    df: pd.DataFrame,
    df_pch: pd.DataFrame,
    df_ctrl: pd.DataFrame,
    theme: Dict[str, Any],
    output_dir: Path,
    generated_files: list[str],
    empreendimentos_all: List[str],
) -> Dict[str, Any]:
    """Figura 17 – Grouped columns by enterprise with one series per species."""

    species_order = sorted(df["nome_cientifico"].dropna().unique())
    areas = []
    for area in [TARGET_PCH_NAME, TARGET_CONTROL_NAME] + list(empreendimentos_all):
        if area not in areas:
            areas.append(area)
    area_dfs = {area: masto._subset_by_empreendimento(df, area) for area in areas}

    # Build species x area abundance matrix
    abund: Dict[str, Dict[str, float]] = {}
    for sp in species_order:
        abund[sp] = {}
        for area, adf in area_dfs.items():
            cnt = adf.loc[adf["nome_cientifico"] == sp, "contagem"]
            abund[sp][area] = float(pd.to_numeric(cnt, errors="coerce").fillna(0).sum())

    # Reordena empreendimentos para leitura do relatório (Fortuna II, SPT, DGN, Jacaré, Controle...)
    display_name_by_key = {
        masto._norm(TARGET_PCH_NAME): "SPT",
        masto._norm(TARGET_CONTROL_NAME): "CONTROLE",
        masto._norm("Área Controle"): "CONTROLE",
        masto._norm("Dores de Guanhães"): "DGN",
    }

    def _display_area(area_name: str) -> str:
        key = masto._norm(area_name)
        if key in display_name_by_key:
            return display_name_by_key[key]
        return str(area_name).upper()

    def _area_rank(area_name: str) -> tuple[int, str]:
        key = masto._norm(area_name)
        if key == masto._norm("Fortuna II"):
            return (0, key)
        if key == masto._norm(TARGET_PCH_NAME):
            return (1, key)
        if key == masto._norm("Dores de Guanhães"):
            return (2, key)
        if key == masto._norm("Jacaré"):
            return (3, key)
        if key in {masto._norm(TARGET_CONTROL_NAME), masto._norm("Área Controle")}:
            return (4, key)
        return (5, key)

    areas = sorted(areas, key=_area_rank)

    n_species = len(species_order)
    n_areas = len(areas)
    x_base = np.arange(n_areas)
    bar_w = min(0.75 / max(n_species, 1), 0.32)
    offsets = [(idx - (n_species - 1) / 2) * bar_w for idx in range(n_species)]

    fig_w = max(11, int(theme.get("fig_width", 12)))
    fig_h = 6.2
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=int(theme.get("dpi", 600)))

    max_val = max((abund[sp][a] for sp in species_order for a in areas), default=1.0)
    if max_val == 0:
        max_val = 1.0

    primary_hex = str(theme.get("primary_hex", "#2E6F95"))
    secondary_hex = str(theme.get("secondary_hex", "#E07A5F"))
    highlight_hex = str(theme.get("highlight_hex", "#3D5A80"))
    species_colors = [primary_hex, secondary_hex, highlight_hex, primary_hex]

    value_color = str(theme.get("spine_color", "#000000"))
    for si, sp in enumerate(species_order):
        vals = [abund[sp][area] for area in areas]
        bars = ax.bar(
            x_base + offsets[si],
            vals,
            width=bar_w,
            color=species_colors[si % len(species_colors)],
            edgecolor=str(theme.get("spine_color", "#000000")),
            linewidth=0.4,
            zorder=2,
            label=f"$\\it{{{sp}}}$" if " " in sp else sp,
        )
        for bar, val in zip(bars, vals):
            label_y = float(bar.get_height()) + (max_val * 0.015 if val > 0 else max_val * 0.02)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                label_y,
                f"{int(val)}",
                va="bottom",
                ha="center",
                fontsize=10,
                color=value_color,
            )

    apply_theme(ax, theme)
    ax.set_xticks(x_base)
    ax.set_xticklabels([_display_area(a) for a in areas], fontsize=10)
    ax.set_ylim(0, max_val + max(1.0, max_val * 0.22))
    ax.tick_params(axis="y", labelsize=10)
    ax.tick_params(axis="x", pad=8)

    ax.set_title("")

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.09),
        ncol=max(1, min(3, n_species)),
        frameon=bool(theme.get("legend_frame", False)),
        fontsize=10,
        handlelength=0.6,
        handletextpad=0.35,
    )

    fig.tight_layout(rect=[0.02, 0.05, 0.98, 0.95])
    out_fig = output_dir / "fig17_abundancia_registros_primatas_campanha.png"
    fig.savefig(out_fig, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_fig))

    # Enterprise x species composition table, including zero-count enterprises
    composition_rows = []
    for area in areas:
        row = {"Empreendimento": _display_area(area)}
        total_area = 0.0
        for sp in species_order:
            value = abund[sp][area]
            row[sp] = int(value)
            total_area += value
        row["Total"] = int(total_area)
        composition_rows.append(row)
    tab_all = pd.DataFrame(composition_rows)
    out_tab = output_dir / "fig17_tabela_composicao_primatas.xlsx"
    tab_all.to_excel(out_tab, index=False, engine="openpyxl")
    generated_files.append(str(out_tab))

    return {
        "riqueza": int(df["nome_cientifico"].nunique()),
        "abundancia_total": int(pd.to_numeric(df["contagem"], errors="coerce").fillna(0).sum()),
        "por_area": {a: int(pd.to_numeric(area_dfs[a]["contagem"], errors="coerce").fillna(0).sum()) for a in areas},
    }


# ---------------------------------------------------------------------------
# Block: 6.2 – Diagrama de Venn (composição por área)
# ---------------------------------------------------------------------------

def _save_venn_primatas(
    df_pch: pd.DataFrame,
    df_ctrl: pd.DataFrame,
    theme: Dict[str, Any],
    output_dir: Path,
    generated_files: list[str],
) -> None:
    """Custom Venn diagram for primatas with dynamic PCH/Control labels."""
    set_pch = set(df_pch["nome_cientifico"].dropna().astype(str).tolist())
    set_ctrl = set(df_ctrl["nome_cientifico"].dropna().astype(str).tolist())
    inter = set_pch & set_ctrl
    union = set_pch | set_ctrl

    only_pch = len(set_pch - set_ctrl)
    only_ctrl = len(set_ctrl - set_pch)
    both = len(inter)

    fig, ax = plt.subplots(figsize=(11, 7.4), dpi=int(theme.get("dpi", 600)))

    # Use TARGET_PCH_NAME and TARGET_CONTROL_NAME dynamically
    pch_label = TARGET_PCH_NAME
    ctrl_label = TARGET_CONTROL_NAME
    pch_color = str(theme.get("primary_hex", "#2E6F95"))
    ctrl_color = str(theme.get("secondary_hex", "#E07A5F"))
    dark_text = "#0D2A1D"

    # Circles with moderate overlap and better visual balance
    c1 = Circle((0.39, 0.67), 0.22, color=pch_color, alpha=0.24, ec="#0E3A22", lw=1.4)
    c2 = Circle((0.61, 0.67), 0.22, color=ctrl_color, alpha=0.22, ec="#4C8642", lw=1.4)
    ax.add_patch(c1)
    ax.add_patch(c2)

    # Valores e descrições internas com alinhamento vertical consistente
    y_num = 0.69
    y_desc = 0.63
    ax.text(0.33, y_num, str(only_pch), ha="center", va="center", fontsize=32, fontweight="bold", color=dark_text)
    ax.text(0.33, y_desc, "Espécies\nexclusivas", ha="center", va="center", fontsize=13.2, color=dark_text)

    ax.text(0.50, y_num, str(both), ha="center", va="center", fontsize=34, fontweight="bold", color=dark_text)
    ax.text(0.50, y_desc, "Espécie\ncompartilhada" if both == 1 else "Espécies\ncompartilhadas", ha="center", va="center", fontsize=13.2, color=dark_text)

    ax.text(0.67, y_num, str(only_ctrl), ha="center", va="center", fontsize=32, fontweight="bold", color="#2F6A34")
    ax.text(0.67, y_desc, "Espécies\nexclusivas", ha="center", va="center", fontsize=13.2, color="#2F6A34")

    # Nomes das áreas com menor peso
    ax.plot([0.27, 0.35], [0.50, 0.50], color="#0E3A22", linewidth=1.8)
    ax.text(0.31, 0.47, pch_label, ha="center", va="center", fontsize=14.2, fontweight="semibold", color="#0E3A22")
    ax.text(0.31, 0.44, f"{len(set_pch)} espécies", ha="center", va="center", fontsize=11.2, color="#1A3D25")

    ax.plot([0.65, 0.73], [0.50, 0.50], color="#4C8642", linewidth=1.8)
    ax.text(0.69, 0.47, ctrl_label, ha="center", va="center", fontsize=14.2, fontweight="semibold", color="#3E7E3A")
    ax.text(0.69, 0.44, f"{len(set_ctrl)} espécies", ha="center", va="center", fontsize=11.2, color="#2C6031")

    # Caixa resumo inferior
    box = FancyBboxPatch(
        (0.18, 0.34),
        0.64,
        0.042,
        boxstyle="round,pad=0.012,rounding_size=0.01",
        linewidth=0.9,
        edgecolor="#1E4D2E",
        facecolor="#F7F7F7",
        alpha=0.90,
    )
    ax.add_patch(box)
    ax.text(0.50, 0.360, f"RIQUEZA TOTAL: {len(union)} ESPÉCIES", ha="center", va="center", fontsize=14.5, fontweight="bold", color=dark_text)
    ax.set_xlim(0.08, 0.92)
    ax.set_ylim(0.32, 0.90)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.set_xticklabels(["", "", ""])
    ax.set_yticklabels(["", "", ""])
    apply_theme(ax, theme, xlabel="", ylabel="")
    validate_axes_style(ax, theme)
    fig.tight_layout()
    out_venn = output_dir / "6_2_prim_diagrama_venn_pch_vs_controle.png"
    fig.savefig(out_venn, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_venn))


# ---------------------------------------------------------------------------
# Block: Mapa – Registros geolocalizados
# ---------------------------------------------------------------------------

def _save_mapa_primatas(
    df: pd.DataFrame,
    project_id: int,
    env_file: Optional[str],
    theme: Dict[str, Any],
    output_dir: Path,
    generated_files: list[str],
) -> Dict[str, Any]:
    """Map of primate occurrence points over satellite imagery using contextily."""
    ponto_ids = set(df["nome_ponto"].dropna().unique())
    # We need actual IDs; reload from mastofauna loader cache
    sb = get_client(env_file)
    pontos_raw = paginate(
        sb,
        "pontos_coleta",
        filters={"id_projeto": int(project_id)},
        select="id_ponto_coleta,nome_ponto,latitude,longitude,id_empreendimento",
    )
    emp_raw = paginate(sb, "empreendimentos", filters={"id_projeto": int(project_id)}, select="id_empreendimento,nome")
    emp_map = {e["id_empreendimento"]: e["nome"] for e in emp_raw}

    coords_rows = []
    for p in pontos_raw:
        if p.get("nome_ponto") not in ponto_ids:
            continue
        lat = p.get("latitude")
        lon = p.get("longitude")
        empreendimento_nome = emp_map.get(p.get("id_empreendimento"), "Sem empreendimento")
        if masto._norm(empreendimento_nome) == "sem empreendimento":
            continue
        if lat is None or lon is None:
            continue
        coords_rows.append({
            "nome_ponto": p["nome_ponto"],
            "lat": float(lat),
            "lon": float(lon),
            "empreendimento": empreendimento_nome,
        })

    if not coords_rows:
        return {"warning": "Sem coordenadas disponíveis para os pontos de primatas."}

    coords_df = pd.DataFrame(coords_rows)

    # Enrich with species info from df
    sp_by_point = df.groupby("nome_ponto")["nome_cientifico"].apply(lambda s: ", ".join(sorted(s.dropna().unique()))).reset_index(name="especies")
    coords_df = coords_df.merge(sp_by_point, on="nome_ponto", how="left")

    # Build map
    primary_hex = str(theme.get("primary_hex", "#11420C"))
    secondary_hex = str(theme.get("secondary_hex", "#5B8E53"))
    area_colors = {
        masto._norm(TARGET_PCH_NAME): primary_hex,
        masto._norm(TARGET_CONTROL_NAME): secondary_hex,
    }

    try:
        import contextily as ctx
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        xs, ys = transformer.transform(coords_df["lon"].values, coords_df["lat"].values)
        coords_df["x"] = xs
        coords_df["y"] = ys
        use_satellite = True
    except Exception:
        use_satellite = False

    fig, ax = plt.subplots(figsize=(12, 10), dpi=int(theme.get("dpi", 600)))

    unique_areas = coords_df["empreendimento"].unique()
    palette = [primary_hex, secondary_hex, "#8B4513", "#DC143C"]
    area_color_map = {a: palette[i % len(palette)] for i, a in enumerate(sorted(unique_areas))}

    species_list = sorted(df["nome_cientifico"].dropna().unique())
    sp_markers = ["o", "s", "^", "D"]
    sp_marker_map = {sp: sp_markers[i % len(sp_markers)] for i, sp in enumerate(species_list)}

    plot_x = "x" if use_satellite else "lon"
    plot_y = "y" if use_satellite else "lat"

    plotted_handles: list = []
    for sp in species_list:
        sp_df = df[df["nome_cientifico"] == sp]
        sp_points = coords_df[coords_df["nome_ponto"].isin(sp_df["nome_ponto"].unique())]
        if sp_points.empty:
            continue
        for area in unique_areas:
            area_sp = sp_points[sp_points["empreendimento"] == area]
            if area_sp.empty:
                continue
            sc = ax.scatter(
                area_sp[plot_x], area_sp[plot_y],
                c=area_color_map[area],
                marker=sp_marker_map[sp],
                s=160, edgecolors="white", linewidths=0.8, zorder=5,
            )
        plotted_handles.append(
            mpatches.Patch(facecolor=sp_marker_map[sp] and "#555555", label=f"$\\it{{{sp}}}$")
        )

    # Point labels
    for _, row in coords_df.iterrows():
        ax.annotate(
            str(row["nome_ponto"]),
            xy=(row[plot_x], row[plot_y]),
            xytext=(6, 6), textcoords="offset points",
            fontsize=7, color="#222222",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="none"),
        )

    if use_satellite:
        try:
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=14, crs="EPSG:3857")
        except Exception:
            try:
                ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=14, crs="EPSG:3857")
            except Exception:
                pass

    # Legend: areas
    area_handles = [mpatches.Patch(facecolor=area_color_map[a], edgecolor="white", linewidth=0.6, label=a) for a in sorted(unique_areas)]
    sp_handles = [mpatches.Patch(
        facecolor="#555555", edgecolor="white", linewidth=0.6,
        label=f"$\\it{{{sp}}}$" if " " in sp else sp,
    ) for sp in species_list]
    ax.legend(handles=area_handles + sp_handles, loc="lower right", fontsize=9, frameon=True, framealpha=0.9)

    ax.set_xlabel("Longitude" if not use_satellite else "")
    ax.set_ylabel("Latitude" if not use_satellite else "")
    ax.set_title("")

    fig.tight_layout()
    out_map = output_dir / "mapa_registros_primatas_georreferenciado.png"
    fig.savefig(out_map, dpi=int(theme.get("dpi", 600)), bbox_inches="tight")
    plt.close(fig)
    generated_files.append(str(out_map))

    # Coordinate table
    coord_table = coords_df[["nome_ponto", "empreendimento", "lat", "lon", "especies"]].copy()
    coord_table.columns = ["Ponto", "Empreendimento", "Latitude (DD)", "Longitude (DD)", "Espécies registradas"]
    out_coords = output_dir / "mapa_tabela_coordenadas_primatas.xlsx"
    coord_table.to_excel(out_coords, index=False, engine="openpyxl")
    generated_files.append(str(out_coords))

    return {"pontos_mapeados": len(coords_df), "satelite": use_satellite}


# ---------------------------------------------------------------------------
# Block: 6.3 – Tabela de espécies: ameaçadas, raras, endêmicas e atributos
# ---------------------------------------------------------------------------

def _save_status_table_primatas(
    df: pd.DataFrame,
    output_dir: Path,
    generated_files: list[str],
) -> None:
    """Full ecological and conservation status table (Item 6.3)."""
    status_cols_src = [
        ("nome_cientifico", "Nome Científico"),
        ("nome_popular", "Nome Popular"),
        ("ordem", "Ordem"),
        ("familia", "Família"),
        ("status_ameaca_global", "Status IUCN (Global)"),
        ("status_ameaca_nacional", "Status MMA (Nacional)"),
        ("status_copam", "Status COPAM (MG)"),
        ("cites", "CITES"),
        ("endemismo", "Endemismo"),
        ("raridade", "Raridade"),
        ("dependencia_florestal", "Dependência Florestal"),
        ("habito_alimentar", "Hábito Alimentar"),
        ("guilda_alimentar", "Guilda Trófica"),
        ("sensibilidade_ambiental", "Sensibilidade Ambiental"),
        ("migratorio", "Migratório"),
        ("origem", "Origem"),
    ]

    available_src = [s for s, _ in status_cols_src if s in df.columns]
    species = (
        df.groupby("nome_cientifico", as_index=False)
          .agg({col: "first" for col in available_src if col != "nome_cientifico"})
    )

    rename_map = {s: label for s, label in status_cols_src if s in species.columns}
    species = species.rename(columns=rename_map)
    display_cols = ["Nome Científico"] + [label for _, label in status_cols_src if label in species.columns and label != "Nome Científico"]
    species = species[display_cols]

    out_status = output_dir / "6_3_tabela_status_ecologico_primatas.xlsx"
    species.to_excel(out_status, index=False, engine="openpyxl")
    generated_files.append(str(out_status))


# ---------------------------------------------------------------------------
# Descriptive report
# ---------------------------------------------------------------------------

def _save_descriptive_report_primatas(
    details: Dict[str, Any],
    output_dir: Path,
    generated_files: list[str],
    slug: str = "PRIM",
) -> None:
    campaigns = "\n".join(f"  - {c}" for c in details.get("campaigns", []))
    points = "\n".join(f"  - {p}" for p in details.get("points", []))
    text_lines = [
        "Relatório descritivo - Primatas",
        "=" * 50,
        "",
        f"Área principal (PCH): {TARGET_PCH_NAME}",
        f"Área Controle: {TARGET_CONTROL_NAME}",
        f"Registros após consolidação: {details.get('rows_loaded', 0)}",
        f"Riqueza total (S): {details.get('species_total_primates', 0)} espécies",
        f"Registros {TARGET_PCH_NAME}: {details.get('pch_rows', 0)}",
        f"Registros {TARGET_CONTROL_NAME}: {details.get('control_rows', 0)}",
        "",
        "Campanhas:",
        campaigns,
        "",
        "Pontos amostrados:",
        points,
        "",
        "Blocos executados:",
        "  fig17  – Figura 17: Abundância por espécie/área",
        "  6.2    – Diagrama de Venn (composição SPT vs Controle)",
        "  6.3    – Tabela de status ecológico e conservação",
    ]
    out_txt = output_dir / f"relatorio_primatas_{slug}.txt"
    out_txt.write_text("\n".join(text_lines), encoding="utf-8")
    generated_files.append(str(out_txt))


# ---------------------------------------------------------------------------
# Main pipeline entry point
# ---------------------------------------------------------------------------

def run_primatas_pipeline(
    project_id: int,
    group: str,
    theme: Dict[str, Any],
    output_dir: Path,
    env_file: Optional[str] = None,
    block: str = "all",
) -> Dict[str, Any]:
    global TARGET_PCH_NAME, TARGET_CONTROL_NAME

    output_dir.mkdir(parents=True, exist_ok=True)

    inferred_pch_name = _infer_pch_name_from_output_dir(output_dir)
    if inferred_pch_name:
        TARGET_PCH_NAME = inferred_pch_name
    TARGET_CONTROL_NAME = "Área Controle"

    df_raw = masto._load_mastofauna_df(project_id=project_id, env_file=env_file)
    if df_raw.empty:
        return {"rows_loaded": 0, "executed_blocks": [], "generated_files": [],
                "warning": "Sem dados de mastofauna/primatas para o projeto."}

    df_prim = df_raw[df_raw.apply(masto._is_primata, axis=1)].copy()
    if df_prim.empty:
        return {"rows_loaded": 0, "executed_blocks": [], "generated_files": [],
                "warning": "Nenhum registro de primatas encontrado para o projeto."}

    df = _prepare_primatas_df(df_prim)
    empreendimentos_all = _load_project_empreendimentos(project_id=project_id, env_file=env_file)

    df_pch = masto._subset_by_empreendimento(df, TARGET_PCH_NAME)
    df_ctrl = masto._subset_by_empreendimento(df, TARGET_CONTROL_NAME)

    block_sel = str(block).strip().lower()
    slug = _enterprise_slug_for_dir(output_dir)
    generated_files: list[str] = []
    executed_blocks: list[str] = []

    details: Dict[str, Any] = {
        "rows_loaded": int(len(df)),
        "species_total_primates": int(df["nome_cientifico"].nunique()),
        "pch_rows": int(len(df_pch)),
        "control_rows": int(len(df_ctrl)),
        "campaigns": sorted(df["nome_campanha"].dropna().astype(str).unique().tolist()),
        "points": sorted(df["nome_ponto"].dropna().astype(str).unique().tolist()),
    }

    # fig17 / abundancia
    if block_sel in {"fig17", "abundancia", "f17", "all"}:
        details["fig17"] = _save_fig17_abundancia(
            df,
            df_pch,
            df_ctrl,
            theme,
            output_dir,
            generated_files,
            empreendimentos_all,
        )
        executed_blocks.append("fig17")

    # 6.2 venn
    if block_sel in {"venn", "6.2", "62", "all"}:
        _save_venn_primatas(df_pch, df_ctrl, theme, output_dir, generated_files)
        executed_blocks.append("6.2")

    # mapa
    # Removido do fluxo padrão do pipeline de primatas.
    if block_sel in {"mapa", "map"}:
        details["mapa"] = _save_mapa_primatas(df, project_id, env_file, theme, output_dir, generated_files)
        executed_blocks.append("mapa")

    # 6.3 status
    if block_sel in {"status", "6.3", "63", "all"}:
        _save_status_table_primatas(df, output_dir, generated_files)
        executed_blocks.append("6.3")

    if block_sel == "all":
        _save_descriptive_report_primatas(details, output_dir, generated_files, slug=slug)

    if not executed_blocks:
        raise ValueError(
            "Block não reconhecido para primatas. Use: fig17, venn/6.2, mapa/map, status/6.3 ou all."
        )

    details["executed_blocks"] = executed_blocks
    details["generated_files"] = generated_files
    return details
