import os
import pandas as pd
from scipy import stats

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def run_validation(scores, prices):
    merged = scores.merge(prices, on="country_iso3", how="inner")
    merged = merged.rename(columns={"pct_price_change": "energy_cpi_change_pct"})
    merged = merged.dropna(subset=["exposure_score", "energy_cpi_change_pct"])
    print(f"Validation sample: {len(merged)} countries")

    x = merged["exposure_score"].values
    y = merged["energy_cpi_change_pct"].values

    # OLS full sample
    slope, intercept, r, p, _ = stats.linregress(x, y)
    print(f"\nOLS full sample (n={len(merged)})")
    print(f"  R² = {r**2:.3f},  p = {p:.3f},  slope = {slope:.2f}")

    # OLS without Korea
    no_kor = merged[merged["country_iso3"] != "KOR"]
    xn = no_kor["exposure_score"].values
    yn = no_kor["energy_cpi_change_pct"].values
    slope_n, intercept_n, r_n, p_n, _ = stats.linregress(xn, yn)
    print(f"\nOLS without KOR (n={len(no_kor)})")
    print(f"  R² = {r_n**2:.3f},  p = {p_n:.3f},  slope = {slope_n:.2f}")

    # Save the merged table
    out = merged[["country_iso3", "volume_loss_pct", "rerouting_cost_pct",
                  "exposure_score", "energy_cpi_change_pct"]]
    out.to_csv(os.path.join(OUTPUT_DIR, "results.csv"), index=False)

    return merged
