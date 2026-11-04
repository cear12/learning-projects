"""Create the categorical comparison and cleaned correlation heatmap."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT = Path(__file__).resolve().parent
VARIABLES = ["active", "alco", "cholesterol", "gluc", "overweight", "smoke"]


def prepare_data(frame):
    """Add the BMI flag and normalize cholesterol/glucose without mutating input."""
    prepared = frame.copy()
    bmi = prepared["weight"] / (prepared["height"] / 100) ** 2
    prepared["overweight"] = (bmi > 25).astype(int)
    for column in ("cholesterol", "gluc"):
        prepared[column] = (prepared[column] > 1).astype(int)
    return prepared


df = prepare_data(pd.read_csv(PROJECT / "medical_examination.csv"))


def category_counts(frame):
    """Count both binary values of each plotted variable in each cardio group."""
    melted = frame.melt(id_vars="cardio", value_vars=VARIABLES)
    return melted.groupby(["cardio", "variable", "value"]).size().reset_index(name="total")


def clean_heatmap_data(frame):
    """Apply all blood-pressure and inclusive percentile filters to the same frame."""
    height_bounds = frame["height"].quantile([0.025, 0.975])
    weight_bounds = frame["weight"].quantile([0.025, 0.975])
    valid = (
        frame["ap_lo"].le(frame["ap_hi"])
        & frame["height"].between(height_bounds.loc[0.025], height_bounds.loc[0.975])
        & frame["weight"].between(weight_bounds.loc[0.025], weight_bounds.loc[0.975])
    )
    return frame.loc[valid].copy()


def draw_cat_plot():
    """Return and save the two-panel categorical count comparison."""
    df_cat = category_counts(df)
    palette = {0: "#3274A1", 1: "#E1812C"}
    with sns.axes_style("ticks"):
        grid = sns.catplot(
            data=df_cat, x="variable", y="total", hue="value", col="cardio",
            kind="bar", order=VARIABLES, hue_order=[0, 1], col_order=[0, 1],
            palette=palette, saturation=1, errorbar=None, legend=False,
            height=4.8, aspect=1.15,
        )
        grid.set_axis_labels("variable", "total")
        grid.set_titles("cardio = {col_name}")
        fig = grid.figure
        fig.subplots_adjust(right=0.91, wspace=0.05, bottom=0.14)
        handles = [Patch(facecolor=palette[value], label=str(value)) for value in (0, 1)]
        fig.legend(handles=handles, title="value", loc="center left",
                   bbox_to_anchor=(0.915, 0.5), frameon=False)
    fig.savefig(PROJECT / "catplot.png", dpi=120)
    return fig


def draw_heat_map():
    """Return and save Pearson correlations with the diagonal/upper half masked."""
    df_heat = clean_heatmap_data(df)
    corr = df_heat.corr(method="pearson", numeric_only=True)
    mask = np.triu(np.ones_like(corr, dtype=bool))
    with sns.axes_style("white"):
        fig, ax = plt.subplots(figsize=(11, 9))
        sns.heatmap(
            corr, mask=mask, annot=True, fmt=".1f", cmap="icefire", center=0,
            vmin=-0.1, vmax=0.3, square=True, linewidths=0.5,
            annot_kws={"size": 8}, cbar_kws={"shrink": 0.5}, ax=ax,
        )
        ax.tick_params(axis="x", labelrotation=90)
        ax.tick_params(axis="y", labelrotation=0)
        fig.tight_layout()
    fig.savefig(PROJECT / "heatmap.png", dpi=120)
    return fig
