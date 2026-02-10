import pandas as pd
from pathlib import Path

RAW = Path("data/raw/BTCUSDT2024-11-05.csv.gz")
OUT = Path("data/processed/bybit_BTCUSDT_2024-11-05.csv")

df = pd.read_csv(RAW)

# Expected columns include:
# timestamp (seconds), symbol, side (Buy/Sell), size (base), price, trdMatchID, ...
# Convert to canonical
df["ts_s"] = pd.to_numeric(df["timestamp"], errors="coerce")
df["ts_ms"] = (df["ts_s"] * 1000.0).round().astype("int64")
df["dt_utc"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)

df["venue"] = "bybit"
df["symbol"] = df["symbol"].astype(str)

df["trade_id"] = df["trdMatchID"].astype(str)
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["qty_base"] = pd.to_numeric(df["size"], errors="coerce")
df["side"] = df["side"].astype(str)

out = df[["ts_ms", "dt_utc", "venue", "symbol", "trade_id", "price", "qty_base", "side"]].copy()

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("Rows:", len(out))
print("Min dt:", out["dt_utc"].min())
print("Max dt:", out["dt_utc"].max())
print(out.head(3).to_string(index=False))
