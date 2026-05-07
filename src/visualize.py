import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from scipy import stats

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_regression(merged):
    plt.rcParams.update({
        "font.family": "serif", "font.size": 11,
        "axes.linewidth": 0.8, "xtick.direction": "in", "ytick.direction": "in",
    })

    x = merged["exposure_score"].values
    y = merged["energy_cpi_change_pct"].values

    no_kor = merged[merged["country_iso3"] != "KOR"]
    xn = no_kor["exposure_score"].values
    yn = no_kor["energy_cpi_change_pct"].values

    # Full sample OLS
    s1, i1, r1, p1, _ = stats.linregress(x, y)

    # Without Korea OLS + confidence band
    sn, in_, rn, pn, _ = stats.linregress(xn, yn)
    n = len(xn)
    xn_line = np.linspace(xn.min(), xn.max(), 200)
    yn_line = sn * xn_line + in_
    se = np.sqrt(np.sum((yn - (sn*xn + in_))**2) / (n-2) *
                 (1/n + (xn_line - xn.mean())**2 / np.sum((xn - xn.mean())**2)))
    t_crit = stats.t.ppf(0.975, df=n-2)

    fig, ax = plt.subplots(figsize=(7, 5))

    # Plot points — Korea as open square, rest as filled circles
    kor = merged[merged["country_iso3"] == "KOR"]
    rest = merged[merged["country_iso3"] != "KOR"]
    ax.scatter(rest["exposure_score"], rest["energy_cpi_change_pct"],
               s=40, color="black", zorder=3)
    ax.scatter(kor["exposure_score"], kor["energy_cpi_change_pct"],
               s=50, color="black", marker="s", facecolors="none", linewidths=1.2, zorder=3)

    # Regression lines
    ax.plot(xn_line, yn_line, color="black", lw=1.5,
            label=f"OLS excl. KOR:  $R^2$={rn**2:.2f},  $p$={pn:.3f}")
    x_line = np.linspace(x.min(), x.max(), 200)
    ax.plot(x_line, s1*x_line+i1, color="black", lw=1.2, linestyle="--",
            label=f"OLS full sample:  $R^2$={r1**2:.2f},  $p$={p1:.3f}")
    ax.fill_between(xn_line, yn_line - t_crit*se, yn_line + t_crit*se,
                    color="black", alpha=0.08, label="95% CI")

    # Country labels
    offsets = {"KOR": (5, -12), "USA": (5, 4), "DEU": (5, 4),
               "GBR": (5, -12), "ISR": (5, 4), "COL": (5, -12)}
    for _, row in merged.iterrows():
        dx, dy = offsets.get(row["country_iso3"], (5, 4))
        ax.annotate(row["country_iso3"],
                    xy=(row["exposure_score"], row["energy_cpi_change_pct"]),
                    xytext=(dx, dy), textcoords="offset points", fontsize=9)

    ax.set_xlabel("Exposure score")
    ax.set_ylabel("Energy CPI change, Jan–Mar 2026 (%)")
    ax.set_title("Hormuz exposure score vs. observed energy price change", fontsize=11)
    ax.legend(fontsize=8.5, framealpha=1, edgecolor="0.8", loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    plt.tight_layout()

    fig.savefig(os.path.join(OUTPUT_DIR, "regression.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved regression plot to output/regression.png")
