import pandas as pd
from pathlib import Path
import zipfile

ZIP_PATH = Path("data/raw/BTCUSDT-trades-2024-11-05.zip")
OUT = Path("data/processed/binance_BTCUSDT_2024-11-05.csv")

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    # pick the first csv in the archive
    csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if not csv_names:
        raise SystemExit("No CSV found in the Binance zip.")
    csv_name = csv_names[0]

    with z.open(csv_name) as f:
        df = pd.read_csv(f)

# Expected columns: id, price, qty, quote_qty, time, is_buyer_maker
# time is milliseconds since epoch (UTC)
df["ts_ms"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
df["dt_utc"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)

df["venue"] = "binance"
df["symbol"] = "BTCUSDT"

# trade_id
df["trade_id"] = df["id"]

# qty_base
df["qty_base"] = pd.to_numeric(df["qty"], errors="coerce")

# side: is_buyer_maker=False means buyer aggressive -> Buy
# is_buyer_maker=True  means buyer maker -> Sell aggressive -> Sell
df["side"] = df["is_buyer_maker"].map({False: "Buy", True: "Sell"})

df["price"] = pd.to_numeric(df["price"], errors="coerce")

out = df[["ts_ms", "dt_utc", "venue", "symbol", "trade_id", "price", "qty_base", "side"]].copy()

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("Rows:", len(out))
print("Min dt:", out["dt_utc"].min())
print("Max dt:", out["dt_utc"].max())
print(out.head(3).to_string(index=False))
