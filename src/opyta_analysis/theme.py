from __future__ import annotations

from typing import Dict, List
import colorsys
import matplotlib.pyplot as plt


def _cm_to_inches(cm: float) -> float:
    return float(cm) / 2.54


def get_figsize_by_complexity(theme: Dict, n_categories: int, prefer_landscape: bool = True):
    std = theme.get("figsize_standard")
    if isinstance(std, list) and len(std) == 2:
        return float(std[0]), float(std[1])

    compact_max = int(theme.get("complexity_compact_max", 6))
    inter_max = int(theme.get("complexity_intermediate_max", 12))

    if n_categories <= compact_max:
        cm_w, cm_h = theme.get("size_compact_cm", [10, 15])
    elif n_categories <= inter_max:
        cm_w, cm_h = theme.get("size_intermediate_cm", [12, 18])
    else:
        cm_w, cm_h = theme.get("size_expanded_cm", [35, 15])

    w, h = _cm_to_inches(cm_w), _cm_to_inches(cm_h)

    # For category-heavy bar charts, horizontal reading is usually better.
    if prefer_landscape and h > w:
        w, h = h, w

    return w, h


def apply_rcparams(theme: Dict):
    font_family = str(theme.get("font_family", "Arial"))
    base = int(theme.get("font_size_base", 11))
    title_size = int(theme.get("title_size", base + 5))
    label_size = int(theme.get("label_size", base + 2))
    legend_size = int(theme.get("legend_size", max(base - 1, 8)))

    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.size"] = base
    plt.rcParams["axes.titlesize"] = title_size
    plt.rcParams["axes.labelsize"] = label_size
    plt.rcParams["xtick.labelsize"] = base
    plt.rcParams["ytick.labelsize"] = base
    plt.rcParams["legend.fontsize"] = legend_size


def get_figsize(theme: Dict, variant: str = "default"):
    std = theme.get("figsize_standard")
    if isinstance(std, list) and len(std) == 2:
        return float(std[0]), float(std[1])

    key = "figsize_default" if variant == "default" else "figsize_wide"
    size = theme.get(key)
    if isinstance(size, list) and len(size) == 2:
        return float(size[0]), float(size[1])
    return (14.0, 6.0) if variant == "default" else (18.0, 9.0)


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


def green_palette_from_hex(base_hex: str, n: int) -> List[str]:
    rgb_base = _hex_to_rgb(base_hex)
    h, s, _v = colorsys.rgb_to_hsv(*rgb_base)

    colors = []
    for i in range(max(n, 1)):
        t = i / max(n - 1, 1)
        new_v = 0.5 + 0.5 * t
        new_s = 0.8 + 0.2 * t
        rgb = colorsys.hsv_to_rgb(h, new_s, new_v)
        colors.append(_rgb_to_hex(rgb))
    return colors


def apply_theme(
    ax,
    theme: Dict,
    *,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    x_tick_rotation: float | None = None,
):
    apply_rcparams(theme)

    fig = ax.figure
    bg = str(theme.get("background_color", "white"))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    ax.grid(
        axis="y",
        visible=bool(theme.get("grid_y", True)),
        linestyle=str(theme.get("grid_linestyle", "--")),
        linewidth=float(theme.get("grid_linewidth", 0.7)),
        alpha=float(theme.get("grid_alpha", 0.35)),
        color=str(theme.get("grid_color", "#E0E0E0")),
    )
    ax.grid(axis="x", visible=bool(theme.get("grid_x", False)))
    ax.set_axisbelow(True)

    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color(str(theme.get("spine_color", "#000000")))
        ax.spines[spine].set_linewidth(float(theme.get("spine_linewidth", 1.2)))

    ax.tick_params(
        axis="both",
        labelsize=int(theme.get("font_size_base", 11)),
        direction=str(theme.get("tick_direction", "out")),
    )

    if title is not None:
        ax.set_title(
            title,
            fontweight=str(theme.get("title_weight", "bold")),
            fontsize=int(theme.get("title_size", int(theme.get("font_size_base", 11)) + 5)),
            pad=float(theme.get("title_pad", 12)),
        )
    if xlabel is not None:
        ax.set_xlabel(
            xlabel,
            fontweight=str(theme.get("label_weight", "normal")),
            fontsize=int(theme.get("label_size", int(theme.get("font_size_base", 11)) + 2)),
            labelpad=float(theme.get("xlabel_pad", 10)),
        )
    if ylabel is not None:
        ax.set_ylabel(
            ylabel,
            fontweight=str(theme.get("label_weight", "normal")),
            fontsize=int(theme.get("label_size", int(theme.get("font_size_base", 11)) + 2)),
            labelpad=float(theme.get("ylabel_pad", 8)),
        )
    if x_tick_rotation is not None:
        for label in ax.get_xticklabels():
            label.set_rotation(x_tick_rotation)


def style_legend(legend, theme: Dict):
    if legend is None:
        return
    frame = legend.get_frame()
    frame.set_visible(bool(theme.get("legend_frame", False)))
    for text in legend.get_texts():
        text.set_fontsize(int(theme.get("legend_size", max(int(theme.get("font_size_base", 11)) - 1, 8))))


def place_legend_below_x_axis(fig, ax, theme: Dict, handles=None, labels=None, ncol: int | None = None):
    existing = ax.get_legend()
    if handles is None or labels is None:
        handles, labels = ax.get_legend_handles_labels()

    if not handles:
        return None

    if existing is not None:
        existing.remove()

    if ncol is None:
        ncol = max(1, len(labels))

    legend = fig.legend(
        handles,
        labels,
        loc=str(theme.get("legend_figure_loc", "lower center")),
        bbox_to_anchor=(0.5, float(theme.get("legend_figure_y", 0.02))),
        bbox_transform=fig.transFigure,
        ncol=ncol,
        frameon=bool(theme.get("legend_frame", False)),
    )
    style_legend(legend, theme)
    return legend


def get_tight_layout_rect(theme: Dict, *, has_legend: bool = False, extra_bottom: float = 0.0):
    bottom = float(theme.get("tight_layout_bottom", 0.05))
    top = float(theme.get("tight_layout_top", 0.98))
    if has_legend and bool(theme.get("legend_below_x_axis", True)):
        bottom = max(bottom, float(theme.get("legend_bottom_margin", 0.36)))
    bottom += float(extra_bottom)
    bottom = min(bottom, 0.60)
    return [0, bottom, 1, top]
