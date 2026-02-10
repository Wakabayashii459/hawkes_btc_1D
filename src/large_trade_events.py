import pandas as pd
from pathlib import Path

FILES = [
    Path("data/processed/binance_BTCUSDT_2024-11-05.csv"),
    Path("data/processed/bybit_BTCUSDT_2024-11-05.csv"),
    Path("data/processed/gate_BTCUSDT_2024-11-05.csv"),
]

THRESHOLD = 1.0  # BTC

dfs = []
for f in FILES:
    df = pd.read_csv(f, usecols=["ts_ms","dt_utc","venue","price","qty_base","side"])
    df["qty_base"] = pd.to_numeric(df["qty_base"], errors="coerce")
    dfs.append(df)

tape = pd.concat(dfs, ignore_index=True)
tape = tape.dropna(subset=["ts_ms","qty_base"])

large = tape[tape["qty_base"] >= THRESHOLD].copy()
large = large.sort_values("ts_ms")

# Add second bucket for alignment with premium
large["t_sec"] = (large["ts_ms"] // 1000).astype("int64")

OUT = Path("data/processed/large_trades_BTCUSDT_2024-11-05.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)
large.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("Large trades count:", len(large))
print("\nCounts by venue:")
print(large["venue"].value_counts())
print("\nFirst 5:")
print(large.head(5).to_string(index=False))
print("\nLast 5:")
print(large.tail(5).to_string(index=False))
