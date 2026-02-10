import pandas as pd
from pathlib import Path

RAW = Path("data/raw/BTC_USDT-202411.csv.gz")
OUT = Path("data/processed/gate_BTCUSDT_2024-11-05.csv")

# Nov 5, 2024 UTC boundaries in *seconds*
START = 1730764800.0  # 2024-11-05 00:00:00 UTC
END   = 1730851200.0  # 2024-11-06 00:00:00 UTC

cols = ["ts_s", "trade_id", "price", "qty_base", "side_code"]

chunks = []
total = 0
kept = 0

for chunk in pd.read_csv(
    RAW,
    header=None,
    names=cols,
    sep=",",
    chunksize=2_000_000
):
    total += len(chunk)

    # Ensure numeric types
    chunk["ts_s"] = pd.to_numeric(chunk["ts_s"], errors="coerce")
    chunk["price"] = pd.to_numeric(chunk["price"], errors="coerce")
    chunk["qty_base"] = pd.to_numeric(chunk["qty_base"], errors="coerce")
    chunk["side_code"] = pd.to_numeric(chunk["side_code"], errors="coerce")

    sub = chunk[(chunk["ts_s"] >= START) & (chunk["ts_s"] < END)].copy()
    kept += len(sub)
    if len(sub):
        chunks.append(sub)

if not chunks:
    raise SystemExit("No rows matched Nov 5 UTC. Double-check grep for '^17307648'.")

daily = pd.concat(chunks, ignore_index=True)

# Canonical fields (we'll finalize across venues next)
daily["venue"] = "gate"
daily["symbol"] = "BTCUSDT"

# Convert float seconds to integer milliseconds (keep precision)
daily["ts_ms"] = (daily["ts_s"] * 1000.0).round().astype("int64")
daily["dt_utc"] = pd.to_datetime(daily["ts_ms"], unit="ms", utc=True)

# Standardize side
daily["side"] = daily["side_code"].map({1: "Buy", 2: "Sell"}).fillna("Unknown")

# Reorder columns nicely
daily = daily[["ts_ms", "dt_utc", "venue", "symbol", "trade_id", "price", "qty_base", "side"]]

OUT.parent.mkdir(parents=True, exist_ok=True)
daily.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("Rows kept:", kept, "of", total)
print("Min dt:", daily["dt_utc"].min())
print("Max dt:", daily["dt_utc"].max())
print(daily.head(3).to_string(index=False))
