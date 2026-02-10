import pandas as pd
import numpy as np
from pathlib import Path

IN_FILES = [
    Path("data/processed/binance_BTCUSDT_2024-11-05.csv"),
    Path("data/processed/bybit_BTCUSDT_2024-11-05.csv"),
    Path("data/processed/gate_BTCUSDT_2024-11-05.csv"),
]

OUT = Path("data/processed/premium_1s_BTCUSDT_2024-11-05.csv")

dfs = []
for f in IN_FILES:
    df = pd.read_csv(f, usecols=["ts_ms","venue","symbol","price","qty_base","side"])
    df["ts_ms"] = pd.to_numeric(df["ts_ms"], errors="coerce").astype("int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["qty_base"] = pd.to_numeric(df["qty_base"], errors="coerce")
    dfs.append(df)

tape = pd.concat(dfs, ignore_index=True)
tape = tape.dropna(subset=["ts_ms","price"])
tape = tape.sort_values(["ts_ms"])

# Bucket to 1-second bins in UTC (ms)
tape["t_sec"] = (tape["ts_ms"] // 1000).astype("int64")

# Per venue, per second: last trade price in that second
px = (
    tape.groupby(["t_sec","venue"], as_index=False)
        .agg(price_last=("price","last"))
)

# Pivot to wide (one column per venue)
wide = px.pivot(index="t_sec", columns="venue", values="price_last").sort_index()

# Reference price = median across venues available in that second
ref = wide.median(axis=1, skipna=True)

# Build long premium table
rows = []
for venue in wide.columns:
    p = wide[venue]
    prem = np.log(p) - np.log(ref)
    rows.append(pd.DataFrame({
        "t_sec": wide.index.values,
        "dt_utc": pd.to_datetime(wide.index.values, unit="s", utc=True),
        "venue": venue,
        "symbol": "BTCUSDT",
        "price_venue": p.values,
        "price_ref": ref.values,
        "log_premium": prem.values
    }))

prem_df = pd.concat(rows, ignore_index=True)

# Drop rows where venue price missing (can't compute premium)
prem_df = prem_df.dropna(subset=["price_venue","price_ref","log_premium"])

OUT.parent.mkdir(parents=True, exist_ok=True)
prem_df.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("Rows:", len(prem_df))
print("\nCoverage (seconds with venue price):")
print(prem_df.groupby("venue")["t_sec"].nunique())

print("\nPremium summary (log units):")
print(prem_df.groupby("venue")["log_premium"].describe()[["mean","std","min","max"]])
