"""Plot helpers (matplotlib): one shared style and a colorblind-safe (Okabe-Ito) palette.

Figures are built with the object-oriented API (`matplotlib.figure.Figure`), not pyplot,
so no global figure state leaks between Marimo cells. Return the figure as the last
expression of a cell and Marimo displays it.
"""
from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]


def _new_axes(title: str, xlabel: str, ylabel: str, figsize=(8, 4.2)):
    fig = Figure(figsize=figsize, layout="constrained")
    ax = fig.subplots()
    ax.set_prop_cycle(color=PALETTE)
    ax.set_title(title, fontsize=11, loc="left")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)  # grid behind bars/lines
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return fig, ax


def _mark_vlines(ax, vlines: dict | None, color="grey"):
    for label, xv in (vlines or {}).items():
        ax.axvline(xv, color=color, linestyle="--", linewidth=1)
        ax.annotate(label, xy=(xv, 1.0), xycoords=("data", "axes fraction"),
                    xytext=(3, -3), textcoords="offset points",
                    ha="left", va="top", fontsize=9, color=color)


def line_figure(x, series: dict, title: str, xlabel: str, ylabel: str,
                vlines: dict | None = None) -> Figure:
    """Lines for each named series; `vlines` = {label: x_value} marks key levels."""
    fig, ax = _new_axes(title, xlabel, ylabel)
    for name, y in series.items():
        ax.plot(x, y, label=name, linewidth=1.8)
    _mark_vlines(ax, vlines)
    if len(series) > 1:
        ax.legend(frameon=False)
    return fig


def payoff_figure(spots, payoff, strike=None, title="Payoff at maturity",
                  xlabel="Spot at maturity", ylabel="Payoff") -> Figure:
    return line_figure(spots, {"Payoff": payoff}, title, xlabel, ylabel,
                       {"K": strike} if strike is not None else None)


def distribution_figure(samples, title: str, xlabel: str,
                        marks: dict | None = None, bins: int = 60) -> Figure:
    """Histogram with vertical marks, e.g. {'VaR 99%': -12.3, 'ES 99%': -15.1}."""
    fig, ax = _new_axes(title, xlabel, "Count")
    ax.hist(np.asarray(samples), bins=bins, color=PALETTE[0], alpha=0.8)
    _mark_vlines(ax, marks, color=PALETTE[3])
    return fig


def fan_figure(times, paths, title: str, xlabel="Time (years)", ylabel="Value",
               quantiles=(0.05, 0.5, 0.95)) -> Figure:
    """Quantile fan of simulated paths, shape (n_paths, n_times)."""
    q = np.quantile(paths, quantiles, axis=0)
    fig, ax = _new_axes(title, xlabel, ylabel)
    for qi, row in zip(quantiles, q):
        ax.plot(times, row, label=f"q{int(qi * 100)}", linewidth=1.8)
    if len(quantiles) >= 2:
        ax.fill_between(times, q[0], q[-1], color=PALETTE[0], alpha=0.12)
    ax.legend(frameon=False)
    return fig


def waterfall_figure(labels, values, title="P&L attribution", ylabel="P&L") -> Figure:
    """Waterfall of components plus a total bar."""
    fig, ax = _new_axes(title, "", ylabel)
    values = list(values)
    cum = np.concatenate([[0.0], np.cumsum(values)])
    for i, v in enumerate(values):
        ax.bar(i, v, bottom=cum[i], color=PALETTE[2] if v >= 0 else PALETTE[3])
    ax.bar(len(values), cum[-1], color=PALETTE[0])
    ax.set_xticks(range(len(values) + 1), list(labels) + ["Total"])
    ax.axhline(0, color="black", linewidth=0.8)
    lo, hi = min(0.0, cum.min()), max(0.0, cum.max())
    pad = 0.1 * ((hi - lo) or 1.0)
    ax.set_ylim(lo - (pad if lo < 0 else 0), hi + pad)
    return fig
