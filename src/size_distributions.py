import pandas as pd
from pathlib import Path

FILES = [
    Path("data/processed/binance_BTCUSDT_2024-11-05.csv"),
    Path("data/processed/bybit_BTCUSDT_2024-11-05.csv"),
    Path("data/processed/gate_BTCUSDT_2024-11-05.csv"),
]

dfs = []
for f in FILES:
    df = pd.read_csv(f)
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)

# Ensure numeric
data["qty_base"] = pd.to_numeric(data["qty_base"], errors="coerce")

print("\n==============================")
print("ROWS PER VENUE")
print("==============================")
print(data.groupby("venue").size())

# Quantiles to inspect tail behavior
qs = [0.5, 0.9, 0.99, 0.999]

print("\n==============================")
print("SIZE QUANTILES PER VENUE (BTC)")
print("==============================")
for venue, g in data.groupby("venue"):
    print(f"\nVenue: {venue}")
    print(g["qty_base"].quantile(qs))

print("\n==============================")
print("POOLED SIZE QUANTILES (BTC)")
print("==============================")
print(data["qty_base"].quantile(qs))

print("\n==============================")
print("BUY vs SELL MEDIAN SIZE (BTC)")
print("==============================")
print(
    data.groupby(["venue", "side"])["qty_base"]
    .median()
    .unstack()
)

# Top trades snapshot
print("\n==============================")
print("TOP 10 LARGEST TRADES (ALL VENUES)")
print("==============================")
print(
    data.sort_values("qty_base", ascending=False)
        .head(10)[["dt_utc", "venue", "price", "qty_base", "side"]]
)
