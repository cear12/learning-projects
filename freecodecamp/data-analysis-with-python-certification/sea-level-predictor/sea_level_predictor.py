"""Plot historical sea-level observations and two linear extrapolations."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd
from scipy.stats import linregress

PROJECT = Path(__file__).resolve().parent
SEA_LEVEL = "CSIRO Adjusted Sea Level"


def fit_trends(frame):
    """Fit the full CSIRO series and the observations from 2000 onward."""
    full_fit = linregress(frame["Year"], frame[SEA_LEVEL])
    recent = frame.loc[frame["Year"].ge(2000)]
    recent_fit = linregress(recent["Year"], recent[SEA_LEVEL])
    return full_fit, recent_fit


def draw_plot():
    """Save the required plot and return its Matplotlib Axes."""
    df = pd.read_csv(PROJECT / "epa-sea-level.csv")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["Year"], df[SEA_LEVEL], s=18, color="#2476a8", label="Observed sea level")

    full_fit, recent_fit = fit_trends(df)
    years = np.arange(int(df["Year"].min()), 2051)
    recent_years = np.arange(2000, 2051)
    ax.plot(years, full_fit.intercept + full_fit.slope * years,
            color="#c53b45", label="1880-2013 fit")
    ax.plot(recent_years, recent_fit.intercept + recent_fit.slope * recent_years,
            color="#30864c", label="2000-2013 fit")

    ax.set(title="Rise in Sea Level", xlabel="Year", ylabel="Sea Level (inches)")
    ax.xaxis.set_major_locator(MultipleLocator(25))
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left")
    fig.tight_layout()

    # Save plot and return data for testing (DO NOT MODIFY)
    plt.savefig('sea_level_plot.png')
    return plt.gca()
