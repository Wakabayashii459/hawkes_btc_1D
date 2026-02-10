import pandas as pd
import numpy as np
from pathlib import Path

PREM = Path("data/processed/premium_with_hawkes_regime_2024-11-05.csv")
OUT = Path("data/processed/naive_rolling_comparison_stats.csv")

df = pd.read_csv(PREM)
df = df.sort_values("t_sec")

# Work venue-by-venue to avoid mixing liquidity
results = []

for venue, g in df.groupby("venue"):
    g = g.copy()

    # Rolling windows (seconds)
    g["roll_mean_30s"] = g["log_premium"].rolling(30, min_periods=5).mean()
    g["roll_mean_300s"] = g["log_premium"].rolling(300, min_periods=30).mean()

    # EWMA
    g["ewma"] = g["log_premium"].ewm(span=30, adjust=False).mean()

    # Rolling median
    g["roll_median_30s"] = g["log_premium"].rolling(30, min_periods=5).median()

    # VWAP-style rolling premium
    # (volume-weighted premium)
    g["prem_x_vol"] = g["log_premium"] * g["price_venue"]
    g["roll_vwap_30s"] = (
        g["prem_x_vol"].rolling(30, min_periods=5).sum() /
        g["price_venue"].rolling(30, min_periods=5).sum()
    )

    methods = {
        "raw": g["log_premium"],
        "roll_mean_30s": g["roll_mean_30s"],
        "roll_mean_300s": g["roll_mean_300s"],
        "ewma": g["ewma"],
        "roll_median_30s": g["roll_median_30s"],
        "roll_vwap_30s": g["roll_vwap_30s"],
    }

    for name, series in methods.items():
        tmp = g.copy()
        tmp["signal"] = series
        tmp = tmp.dropna(subset=["signal"])

        stats = (
            tmp.groupby("regime")["signal"]
               .agg(["std", "min", "max"])
               .reset_index()
        )
        stats["venue"] = venue
        stats["method"] = name
        results.append(stats)

res = pd.concat(results, ignore_index=True)
res.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("\nSample output:")
print(res.head(12).to_string(index=False))
