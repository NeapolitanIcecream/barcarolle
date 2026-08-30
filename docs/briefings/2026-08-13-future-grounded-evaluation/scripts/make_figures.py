#!/usr/bin/env python3
"""Generate the briefing's observed and explicitly hypothetical figures."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter
import numpy as np


BRIEFING_ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = BRIEFING_ROOT / "figures"
HYPOTHETICAL_CSV = FIGURE_DIR / "data" / "hypothetical-optimization-pressure.csv"


def find_repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        evidence_dir = candidate / "examples" / "modern_agent_panel" / "evidence"
        if evidence_dir.is_dir():
            return candidate
    raise RuntimeError("Could not locate the Barcarolle repository root")


REPOSITORY_ROOT = find_repository_root()
SUMMARY_JSON = (
    REPOSITORY_ROOT
    / "examples"
    / "modern_agent_panel"
    / "evidence"
    / "consensus-rate-summary.json"
)
TRANSFER_JSON = (
    REPOSITORY_ROOT
    / "examples"
    / "modern_agent_panel"
    / "evidence"
    / "consensus-rate-transfer-diagnostic.json"
)

FIGSIZE = (40 / 3, 7.5)
PNG_DPI = 180

# Okabe-Ito-derived, color-vision-deficiency-friendly palette.
BACKGROUND = "#FFFFFF"
TEXT = "#202124"
MUTED = "#5F6368"
GRID = "#DADCE0"
H5_COLOR = "#0072B2"
H10_COLOR = "#E69F00"
BETTER_COLOR = "#0072B2"
WORSE_COLOR = "#D55E00"
ADAPTIVE_COLOR = "#009E73"


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": BACKGROUND,
            "savefig.facecolor": BACKGROUND,
            "axes.facecolor": BACKGROUND,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT,
            "axes.titlecolor": TEXT,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": TEXT,
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "font.weight": 400,
            "axes.titleweight": 400,
            "axes.labelweight": 400,
            "axes.linewidth": 0.8,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.8,
            "legend.frameon": False,
            "svg.fonttype": "none",
        }
    )


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected object at {context}")
    return value


def require_rows(value: Any, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"Expected non-empty row list at {context}")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        rows.append(require_mapping(row, f"{context}[{index}]"))
    return rows


def require_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Expected numeric value at {context}")
    number = float(value)
    if not np.isfinite(number):
        raise ValueError(f"Expected finite numeric value at {context}")
    return number


def horizon_record(summary: dict[str, Any], horizon: str) -> dict[str, Any]:
    horizons = require_mapping(summary.get("horizons"), "summary.horizons")
    return require_mapping(horizons.get(horizon), f"summary.horizons[{horizon!r}]")


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=PNG_DPI)
    fig.savefig(FIGURE_DIR / f"{stem}.svg", format="svg")
    plt.close(fig)


def format_signed(value: float, _position: float | None = None) -> str:
    if abs(value) < 0.0000005:
        return "0"
    return f"{value:+.3f}"


def add_observed_header(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(0.055, 0.94, title, fontsize=23, fontweight=400, ha="left", va="top")
    fig.text(0.055, 0.888, subtitle, fontsize=12.5, color=MUTED, ha="left", va="top")


def make_selector_boundaries(
    summary: dict[str, Any], transfer: dict[str, Any]
) -> None:
    transfer_results = require_mapping(transfer.get("results"), "transfer.results")
    internal_loo = require_mapping(
        transfer_results.get("internal_secondary_loo"),
        "transfer.results.internal_secondary_loo",
    )
    external_targets = require_mapping(
        transfer_results.get("primary_references_external_targets"),
        "transfer.results.primary_references_external_targets",
    )

    labels = [
        "Repository-equal\nprimary development",
        "Origin-weighted\nprimary sensitivity",
        "Modern Full systems\ninternal LOO",
        "13 references →\nexternal targets",
    ]
    values: dict[str, list[float]] = {"5": [], "10": []}
    for horizon in ("5", "10"):
        record = horizon_record(summary, horizon)
        sensitivity = require_mapping(
            record.get("sensitivity"), f"summary.horizons[{horizon}].sensitivity"
        )
        origin_weighted = require_mapping(
            sensitivity.get("origin_weighted"),
            f"summary.horizons[{horizon}].sensitivity.origin_weighted",
        )
        internal_record = require_mapping(
            internal_loo.get(horizon), f"transfer.internal_secondary_loo[{horizon}]"
        )
        external_record = require_mapping(
            external_targets.get(horizon),
            f"transfer.primary_references_external_targets[{horizon}]",
        )
        values[horizon] = [
            require_number(
                record.get("candidate_minus_full"),
                f"summary.horizons[{horizon}].candidate_minus_full",
            ),
            require_number(
                origin_weighted.get("candidate_minus_full"),
                f"summary.horizons[{horizon}].sensitivity.origin_weighted.candidate_minus_full",
            ),
            require_number(
                internal_record.get("candidate_minus_full"),
                f"transfer.internal_secondary_loo[{horizon}].candidate_minus_full",
            ),
            require_number(
                external_record.get("candidate_minus_full"),
                f"transfer.primary_references_external_targets[{horizon}].candidate_minus_full",
            ),
        ]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    add_observed_header(
        fig,
        "Selector evidence changes sign outside the development estimand",
        "Observed Candidate − Full future pass-rate MAE; negative values favor the selector.",
    )
    fig.subplots_adjust(left=0.29, right=0.95, top=0.78, bottom=0.18)

    y_positions = np.arange(len(labels), dtype=float)
    bar_height = 0.28
    offsets = {"5": -0.17, "10": 0.17}
    colors = {"5": H5_COLOR, "10": H10_COLOR}
    names = {"5": "H5", "10": "H10"}

    absolute_max = max(abs(value) for horizon in values.values() for value in horizon)
    limit = max(0.028, absolute_max * 1.28)
    ax.set_xlim(-limit, limit)

    for horizon in ("5", "10"):
        horizon_values = np.asarray(values[horizon], dtype=float)
        bars = ax.barh(
            y_positions + offsets[horizon],
            horizon_values,
            height=bar_height,
            color=colors[horizon],
            label=names[horizon],
            zorder=3,
        )
        for bar, value in zip(bars, horizon_values, strict=True):
            label_offset = limit * 0.018
            ax.text(
                value + (label_offset if value >= 0 else -label_offset),
                bar.get_y() + bar.get_height() / 2,
                f"{value:+.4f}",
                ha="left" if value >= 0 else "right",
                va="center",
                fontsize=10.5,
                fontweight=400,
                color=TEXT,
            )

    ax.axvline(0, color=TEXT, linewidth=1.2, zorder=2)
    ax.set_yticks(y_positions, labels=labels)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(FuncFormatter(format_signed))
    ax.set_xlabel("Candidate − Full MAE")
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    ax.tick_params(axis="y", length=0, pad=10)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(loc="lower right", ncol=2, fontsize=11)
    ax.text(
        0.0,
        1.035,
        "← BETTER",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        color=BETTER_COLOR,
        fontweight=400,
    )
    ax.text(
        1.0,
        1.035,
        "WORSE →",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color=WORSE_COLOR,
        fontweight=400,
    )
    fig.text(
        0.055,
        0.045,
        "OBSERVED • Sources: consensus-rate-summary.json; consensus-rate-transfer-diagnostic.json • Opened transfer diagnostics are not independent confirmation.",
        fontsize=9.5,
        color=MUTED,
        ha="left",
    )
    save_figure(fig, "observed-selector-boundaries")


def repository_matrix(summary: dict[str, Any]) -> tuple[list[str], np.ndarray]:
    by_horizon: dict[str, dict[str, float]] = {}
    order: list[str] = []
    for horizon in ("5", "10"):
        record = horizon_record(summary, horizon)
        rows = require_rows(
            record.get("repository_rows"),
            f"summary.horizons[{horizon}].repository_rows",
        )
        horizon_values: dict[str, float] = {}
        for index, row in enumerate(rows):
            repository_id = row.get("repository_id")
            if not isinstance(repository_id, str) or not repository_id:
                raise ValueError(
                    f"Invalid repository_id at summary.horizons[{horizon}].repository_rows[{index}]"
                )
            if repository_id in horizon_values:
                raise ValueError(f"Duplicate repository row: {repository_id} at H{horizon}")
            deltas = require_mapping(
                row.get("candidate_minus_full"),
                f"summary.horizons[{horizon}].repository_rows[{index}].candidate_minus_full",
            )
            horizon_values[repository_id] = require_number(
                deltas.get("consensus_rate_match"),
                f"summary.horizons[{horizon}].repository_rows[{index}].candidate_minus_full.consensus_rate_match",
            )
            if horizon == "5":
                order.append(repository_id)
        by_horizon[horizon] = horizon_values

    if set(by_horizon["5"]) != set(by_horizon["10"]):
        raise ValueError("H5 and H10 repository sets differ")
    if len(order) != 5:
        raise ValueError(f"Expected five repositories, found {len(order)}")

    matrix = np.asarray(
        [[by_horizon["5"][repository], by_horizon["10"][repository]] for repository in order],
        dtype=float,
    )
    return order, matrix


def make_repository_heterogeneity(summary: dict[str, Any]) -> None:
    repositories, matrix = repository_matrix(summary)
    short_names = {
        "django/django": "Django",
        "matplotlib/matplotlib": "Matplotlib",
        "scikit-learn/scikit-learn": "scikit-learn",
        "sphinx-doc/sphinx": "Sphinx",
        "sympy/sympy": "SymPy",
    }
    labels = [short_names.get(repository, repository) for repository in repositories]

    absolute_max = float(np.max(np.abs(matrix)))
    norm = TwoSlopeNorm(vmin=-absolute_max, vcenter=0.0, vmax=absolute_max)
    cmap = LinearSegmentedColormap.from_list(
        "barcarolle_diverging", [BETTER_COLOR, "#F7F7F7", WORSE_COLOR]
    )

    fig, ax = plt.subplots(figsize=FIGSIZE)
    add_observed_header(
        fig,
        "Repository-level effects are heterogeneous",
        "Observed Candidate − Full future pass-rate MAE; repositories receive equal weight in the primary development estimand.",
    )
    fig.subplots_adjust(left=0.27, right=0.88, top=0.79, bottom=0.28)

    image = ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks([0, 1], labels=["H5", "H10"])
    ax.set_yticks(np.arange(len(labels)), labels=labels)
    ax.tick_params(axis="both", length=0, pad=10)
    ax.set_xlabel("Future horizon")
    ax.set_ylabel("Repository")

    ax.set_xticks(np.arange(-0.5, 2, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color=BACKGROUND, linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            cell_text_color = BACKGROUND if abs(value) > absolute_max * 0.52 else TEXT
            ax.text(
                column_index,
                row_index,
                f"{value:+.4f}",
                ha="center",
                va="center",
                color=cell_text_color,
                fontsize=14,
                fontweight=400,
            )

    colorbar_axis = fig.add_axes([0.27, 0.105, 0.61, 0.026])
    colorbar = fig.colorbar(image, cax=colorbar_axis, orientation="horizontal")
    colorbar.set_label("Candidate − Full MAE   (negative = better)", fontsize=10.5)
    colorbar.ax.xaxis.set_label_position("top")
    colorbar.ax.xaxis.set_major_formatter(FuncFormatter(format_signed))
    colorbar.ax.tick_params(labelsize=9.5)
    colorbar.outline.set_edgecolor(GRID)

    fig.text(
        0.055,
        0.018,
        "OBSERVED • Source: consensus-rate-summary.json / horizons.{5,10}.repository_rows • Cell values are repository-level paired effects.",
        fontsize=9.5,
        color=MUTED,
        ha="left",
    )
    save_figure(fig, "observed-repository-heterogeneity")


def load_hypothetical_layout() -> tuple[list[str], np.ndarray, np.ndarray]:
    with HYPOTHETICAL_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 3:
        raise ValueError("Hypothetical layout CSV must contain at least three stages")

    parsed: list[tuple[int, str, float, float]] = []
    for index, row in enumerate(rows):
        if row.get("status") != "hypothetical":
            raise ValueError(f"CSV row {index + 2} must be explicitly hypothetical")
        try:
            order = int(row["stage_order"])
            fixed = float(row["fixed_benchmark_layout_y"])
            adaptive = float(row["future_grounded_layout_y"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid hypothetical CSV row {index + 2}") from error
        label = row.get("stage_label", "").strip()
        if not label:
            raise ValueError(f"Missing stage_label in hypothetical CSV row {index + 2}")
        if not (0.0 <= fixed <= 1.0 and 0.0 <= adaptive <= 1.0):
            raise ValueError("Hypothetical layout coordinates must be between zero and one")
        parsed.append((order, label, fixed, adaptive))

    parsed.sort(key=lambda row: row[0])
    if [row[0] for row in parsed] != list(range(len(parsed))):
        raise ValueError("Hypothetical stage_order must be contiguous from zero")
    return (
        [row[1] for row in parsed],
        np.asarray([row[2] for row in parsed], dtype=float),
        np.asarray([row[3] for row in parsed], dtype=float),
    )


def make_hypothetical_optimization_pressure() -> None:
    stage_labels, fixed_gap, adaptive_gap = load_hypothetical_layout()
    x_values = np.arange(len(stage_labels), dtype=float)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.text(
        0.055,
        0.94,
        "Conceptual validity gap under repeated benchmark reuse",
        fontsize=23,
        fontweight=400,
        ha="left",
        va="top",
    )
    fig.text(
        0.055,
        0.888,
        "Schematic mechanism: a fixed proxy may decouple, while a future-grounded protocol repeatedly re-anchors and can abstain outside support.",
        fontsize=12.5,
        color=MUTED,
        ha="left",
        va="top",
    )
    fig.subplots_adjust(left=0.13, right=0.82, top=0.78, bottom=0.23)

    ax.plot(
        x_values,
        fixed_gap,
        color=WORSE_COLOR,
        linewidth=3.5,
        marker="o",
        markersize=8,
        label="Fixed benchmark reused",
        zorder=3,
    )
    ax.plot(
        x_values,
        adaptive_gap,
        color=ADAPTIVE_COLOR,
        linewidth=3.5,
        marker="s",
        markersize=8,
        label="Future-grounded adaptive protocol",
        zorder=3,
    )
    ax.fill_between(
        x_values,
        adaptive_gap,
        fixed_gap,
        where=fixed_gap >= adaptive_gap,
        color=WORSE_COLOR,
        alpha=0.08,
        zorder=1,
    )

    wrapped_labels = [label.replace(" ", "\n", 1) for label in stage_labels]
    ax.set_xticks(x_values, labels=wrapped_labels)
    ax.set_yticks([0.15, 0.50, 0.85], labels=["Smaller gap", "", "Larger gap"])
    ax.set_xlabel("Optimization pressure / repeated evaluation reuse (conceptual stages)")
    ax.set_ylabel("Proxy–future validity gap (schematic; no units)")
    ax.set_xlim(-0.15, len(stage_labels) - 0.35)
    ax.set_ylim(0.0, 1.02)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", length=0, pad=10)

    ax.text(
        x_values[-1] + 0.08,
        fixed_gap[-1],
        "Fixed benchmark\nreused",
        color=WORSE_COLOR,
        ha="left",
        va="center",
        fontsize=11,
        fontweight=400,
    )
    ax.text(
        x_values[-1] + 0.08,
        adaptive_gap[-1],
        "Future-grounded\nadaptive protocol",
        color=ADAPTIVE_COLOR,
        ha="left",
        va="center",
        fontsize=11,
        fontweight=400,
    )
    ax.annotate(
        "Later real-work anchor\n+ transfer audit + abstention",
        xy=(x_values[2], adaptive_gap[2]),
        xytext=(x_values[1] + 0.15, 0.43),
        arrowprops={"arrowstyle": "->", "color": MUTED, "linewidth": 1.2},
        color=MUTED,
        fontsize=10.5,
        ha="left",
    )

    fig.text(
        0.50,
        0.49,
        "HYPOTHETICAL — NOT MEASURED",
        fontsize=31,
        fontweight=400,
        color=MUTED,
        alpha=0.16,
        ha="center",
        va="center",
        rotation=17,
    )
    fig.text(
        0.055,
        0.045,
        "HYPOTHETICAL • Layout coordinates only; no effect size, round count, or performance trajectory is claimed • Source: figures/data/hypothetical-optimization-pressure.csv",
        fontsize=9.5,
        color=MUTED,
        ha="left",
    )
    save_figure(fig, "hypothetical-optimization-pressure")


def main() -> None:
    configure_style()
    summary = load_json(SUMMARY_JSON)
    transfer = load_json(TRANSFER_JSON)
    make_selector_boundaries(summary, transfer)
    make_repository_heterogeneity(summary)
    make_hypothetical_optimization_pressure()
    generated = sorted(
        path.name
        for path in FIGURE_DIR.iterdir()
        if path.suffix in {".png", ".svg"}
    )
    print(json.dumps({"status": "pass", "generated": generated}, indent=2))


if __name__ == "__main__":
    main()
