"""Visualize daily forum traffic, monthly averages, trends and seasonality."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
PROJECT = Path(__file__).resolve().parent
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
MONTH_ABBREVIATIONS = [month[:3] for month in MONTHS]


def clean_data(frame):
    """Keep values within the original inclusive 2.5th–97.5th percentile bounds."""
    lower, upper = frame["value"].quantile([0.025, 0.975])
    return frame.loc[frame["value"].between(lower, upper)].copy()


df = clean_data(pd.read_csv(PROJECT / "fcc-forum-pageviews.csv", parse_dates=["date"], index_col="date"))


def monthly_averages(frame):
    """Return mean daily views for each calendar year/month, preserving missing months."""
    monthly = frame.groupby([frame.index.year, frame.index.month])["value"].mean()
    monthly.index.names = ["year", "month"]
    table = monthly.unstack("month").reindex(columns=range(1, 13)).sort_index()
    table.columns = pd.Index(MONTHS, name="Months")
    return table


def draw_line_plot():
    """Draw all cleaned daily observations and return the saved figure."""
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(df.index, df["value"], color="#e12525", linewidth=1)
    ax.set(title="Daily freeCodeCamp Forum Page Views 5/2016-12/2019",
           xlabel="Date", ylabel="Page Views")
    fig.tight_layout()

    # Save image and return fig (don't change this part)
    fig.savefig('line_plot.png')
    return fig


def draw_bar_plot():
    """Draw average daily page views for each month, grouped by year."""
    df_bar = monthly_averages(df.copy())
    fig, ax = plt.subplots(figsize=(12, 7))
    df_bar.plot(kind="bar", ax=ax, width=0.8, colormap="tab20", rot=0)
    ax.set(xlabel="Years", ylabel="Average Page Views")
    ax.legend(title="Months", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()

    # Save image and return fig (don't change this part)
    fig.savefig('bar_plot.png')
    return fig


def draw_box_plot():
    """Draw yearly trend and calendar-month seasonality on separate axes."""
    df_box = df.copy()
    df_box.reset_index(inplace=True)
    df_box['year'] = [d.year for d in df_box.date]
    df_box['month'] = [d.strftime('%b') for d in df_box.date]

    years = sorted(df_box["year"].unique())
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.boxplot(data=df_box, x="year", y="value", hue="year", order=years,
                hue_order=years, palette="tab10", dodge=False, legend=False,
                linewidth=1, fliersize=2, ax=axes[0])
    sns.boxplot(data=df_box, x="month", y="value", hue="month", order=MONTH_ABBREVIATIONS,
                hue_order=MONTH_ABBREVIATIONS, palette="husl", dodge=False, legend=False,
                linewidth=1, fliersize=2, ax=axes[1])
    axes[0].set(title="Year-wise Box Plot (Trend)", xlabel="Year", ylabel="Page Views")
    axes[1].set(title="Month-wise Box Plot (Seasonality)", xlabel="Month", ylabel="Page Views")
    for ax in axes:
        ax.set_ylim(0, 200000)
        ax.set_yticks(np.arange(0, 200001, 20000))
    fig.tight_layout()

    # Save image and return fig (don't change this part)
    fig.savefig('box_plot.png')
    return fig
