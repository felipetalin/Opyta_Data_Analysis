from __future__ import annotations

import matplotlib.colors as mcolors


def _is_white(color) -> bool:
    r, g, b, _a = mcolors.to_rgba(color)
    return abs(r - 1.0) < 1e-6 and abs(g - 1.0) < 1e-6 and abs(b - 1.0) < 1e-6


def validate_axes_style(ax, expected: dict) -> None:
    errors = []

    if ax.get_axisbelow() is not True:
        errors.append("axisbelow must be True")

    if not _is_white(ax.get_facecolor()):
        errors.append("axes facecolor must be white")
    if not _is_white(ax.figure.get_facecolor()):
        errors.append("figure facecolor must be white")

    for side in ["top", "right", "left", "bottom"]:
        if not ax.spines[side].get_visible():
            errors.append(f"{side} spine must be visible")

    left_w = float(ax.spines["left"].get_linewidth())
    bottom_w = float(ax.spines["bottom"].get_linewidth())
    top_w = float(ax.spines["top"].get_linewidth())
    right_w = float(ax.spines["right"].get_linewidth())
    expected_w = float(expected.get("spine_linewidth", 1.2))
    if any(abs(v - expected_w) > 1e-6 for v in [left_w, bottom_w, top_w, right_w]):
        errors.append("all spine linewidth values must match expected")

    expected_spine = str(expected.get("spine_color", "#000000")).lower()
    for side in ["top", "right", "left", "bottom"]:
        side_color = mcolors.to_hex(ax.spines[side].get_edgecolor()).lower()
        if side_color != expected_spine:
            errors.append(f"{side} spine color mismatch")

    y_grid_visible = any(gl.get_visible() for gl in ax.get_ygridlines())
    x_grid_visible = any(gl.get_visible() for gl in ax.get_xgridlines())
    if y_grid_visible != bool(expected.get("grid_y", True)):
        errors.append("y grid visibility mismatch")
    if x_grid_visible != bool(expected.get("grid_x", False)):
        errors.append("x grid visibility mismatch")

    title = ax.title
    if title.get_text():
        expected_weight = str(expected.get("title_weight", "bold")).lower()
        current_weight = str(title.get_fontweight()).lower()
        if expected_weight not in current_weight:
            errors.append("title fontweight mismatch")

    legend = ax.get_legend()
    using_figure_legend = False
    if legend is None and ax.figure.legends:
        legend = ax.figure.legends[0]
        using_figure_legend = True

    if legend is not None:
        frame_expected = bool(expected.get("legend_frame", False))
        frame_current = legend.get_frame().get_visible()
        if frame_current != frame_expected:
            errors.append("legend frame visibility mismatch")

        expected_loc = str(expected.get("legend_loc", "upper right")).lower()
        loc_map = {
            "best": 0,
            "upper right": 1,
            "upper left": 2,
            "lower left": 3,
            "lower right": 4,
            "right": 5,
            "center left": 6,
            "center right": 7,
            "lower center": 8,
            "upper center": 9,
            "center": 10,
        }
        expected_code = loc_map.get(expected_loc)
        if expected_code is not None:
            current_code = int(getattr(legend, "_loc", -1))
            if current_code != expected_code:
                figure_expected_loc = str(expected.get("legend_figure_loc", expected_loc)).lower()
                figure_expected_code = loc_map.get(figure_expected_loc)
                if not using_figure_legend or figure_expected_code is None or current_code != figure_expected_code:
                    errors.append("legend location mismatch")

        if bool(expected.get("legend_below_x_axis", True)):
            if using_figure_legend:
                legend_bbox = legend.get_bbox_to_anchor().transformed(ax.figure.transFigure.inverted())
                axes_bottom = float(ax.get_position().y0)
                if float(legend_bbox.y1) >= axes_bottom:
                    errors.append("legend must be positioned below x axis")
            else:
                legend_bbox = legend.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
                if float(legend_bbox.y0) >= 0:
                    errors.append("legend must be positioned below x axis")

    expected_dpi = int(expected.get("dpi", 600))
    fig_dpi = int(round(float(ax.figure.dpi)))
    if fig_dpi < expected_dpi:
        errors.append(f"figure dpi below expected minimum ({fig_dpi} < {expected_dpi})")

    if errors:
        raise ValueError("Style validation failed: " + "; ".join(errors))
