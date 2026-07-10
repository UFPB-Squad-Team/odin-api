"""Chart generation using matplotlib for embedding in PDF reports.

Generates charts as in-memory PNG bytes using matplotlib with a
consistent ODIN visual identity (colors, fonts, style).
"""

from __future__ import annotations

import io
import logging
from typing import Any

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")  # Non-interactive backend for server-side rendering

logger = logging.getLogger(__name__)

# ODIN color palette — consistent with the project visual identity
ODIN_BLUE = "#1A5276"
ODIN_GREEN = "#27AE60"
ODIN_ORANGE = "#E67E22"
ODIN_RED = "#C0392B"
ODIN_PURPLE = "#8E44AD"
ODIN_TEAL = "#16A085"

COLOR_PALETTE = [
    ODIN_BLUE,
    ODIN_GREEN,
    ODIN_ORANGE,
    ODIN_RED,
    ODIN_PURPLE,
    ODIN_TEAL,
]

# Seaborn-inspired muted colors
MUTED_PALETTE = [
    "#3498DB",
    "#2ECC71",
    "#F39C12",
    "#E74C3C",
    "#9B59B6",
    "#1ABC9C",
    "#34495E",
    "#E67E22",
    "#1A5276",
    "#7FB3D8",
]


def _configure_matplotlib() -> None:
    """Apply ODIN visual identity defaults to matplotlib."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#F8F9FA",
            "axes.edgecolor": "#DEE2E6",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.color": "#ADB5BD",
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 10,
            "figure.dpi": 150,
        }
    )


_configure_matplotlib()


def _get_figure(width: float = 6.5, height: float = 3.5) -> tuple[plt.Figure, plt.Axes]:
    """Create a new figure with ODIN defaults."""
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def _fig_to_bytes(fig: plt.Figure) -> bytes:
    """Render a matplotlib figure to PNG bytes in memory."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_bar_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str | list[str] | None = None,
    width: float = 6.5,
    height: float = 3.5,
) -> bytes:
    """Generate a vertical bar chart and return PNG bytes.

    Args:
        labels: Category labels for the x-axis.
        values: Numeric values for each category.
        title: Chart title text.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        color: Single color or list of colors. Uses palette if None.
        width: Figure width in inches.
        height: Figure height in inches.

    Returns:
        PNG image bytes.
    """
    fig, ax = _get_figure(width, height)

    if color is None:
        color = MUTED_PALETTE[: len(labels)]
    elif isinstance(color, str):
        color = [color] * len(labels)

    bars = ax.bar(labels, values, color=color, edgecolor="white", linewidth=0.5)

    # Add value labels on top of bars
    for bar in bars:
        height_val = bar.get_height()
        if height_val != 0:
            ax.annotate(
                f"{height_val:.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, height_val),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_title(title, fontweight="bold", color=ODIN_BLUE)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    fig.tight_layout()

    return _fig_to_bytes(fig)


def generate_horizontal_bar_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = ODIN_BLUE,
    width: float = 6.5,
    height: float = 3.5,
) -> bytes:
    """Generate a horizontal bar chart and return PNG bytes.

    Useful for ranking visualizations (e.g. top schools by IDEB).
    """
    fig, ax = _get_figure(width, height)

    bars = ax.barh(labels, values, color=color, edgecolor="white", linewidth=0.5)

    # Add value labels after bars
    for bar in bars:
        width_val = bar.get_width()
        if width_val != 0:
            ax.annotate(
                f"{width_val:.2f}",
                xy=(width_val, bar.get_y() + bar.get_height() / 2),
                xytext=(3, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=8,
            )

    ax.set_title(title, fontweight="bold", color=ODIN_BLUE)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.invert_yaxis()  # Highest values at top
    fig.tight_layout()

    return _fig_to_bytes(fig)


def generate_pie_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    colors: list[str] | None = None,
    width: float = 5.0,
    height: float = 4.0,
) -> bytes:
    """Generate a pie/donut chart and return PNG bytes.

    Args:
        labels: Slice labels.
        values: Slice sizes.
        title: Chart title.
        colors: List of colors. Uses palette if None.
        width: Figure width in inches.
        height: Figure height in inches.

    Returns:
        PNG image bytes.
    """
    fig, ax = _get_figure(width, height)

    if colors is None:
        colors = MUTED_PALETTE[: len(labels)]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        textprops={"fontsize": 9},
        pctdistance=0.75,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )

    # Draw center circle for donut effect
    centre_circle = plt.Circle((0, 0), 0.50, fc="white")
    fig.gca().add_artist(centre_circle)

    ax.set_title(title, fontweight="bold", color=ODIN_BLUE, pad=15)
    ax.axis("equal")
    fig.tight_layout()

    return _fig_to_bytes(fig)


def generate_grouped_bar_chart(
    categories: list[str],
    series: dict[str, list[float]],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    width: float = 6.5,
    height: float = 4.0,
) -> bytes:
    """Generate a grouped (clustered) bar chart for comparing multiple series.

    Args:
        categories: X-axis category labels.
        series: Dict mapping series name to list of values (same length as categories).
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        width: Figure width in inches.
        height: Figure height in inches.

    Returns:
        PNG image bytes.
    """
    fig, ax = _get_figure(width, height)

    n_series = len(series)
    n_categories = len(categories)
    bar_width = 0.8 / n_series
    x = range(n_categories)

    colors = MUTED_PALETTE[:n_series]

    for i, (name, values) in enumerate(series.items()):
        offset = (i - n_series / 2) * bar_width + bar_width / 2
        bars = ax.bar(
            [xi + offset for xi in x],
            values,
            bar_width,
            label=name,
            color=colors[i],
            edgecolor="white",
            linewidth=0.5,
        )

    ax.set_title(title, fontweight="bold", color=ODIN_BLUE)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(n_categories))
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.legend(loc="upper right", framealpha=0.9)
    fig.tight_layout()

    return _fig_to_bytes(fig)


__all__ = [
    "generate_bar_chart",
    "generate_horizontal_bar_chart",
    "generate_pie_chart",
    "generate_grouped_bar_chart",
]