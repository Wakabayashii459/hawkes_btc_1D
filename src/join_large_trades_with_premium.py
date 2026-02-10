import pandas as pd
from pathlib import Path

PREM = Path("data/processed/premium_1s_BTCUSDT_2024-11-05.csv")
LARGE = Path("data/processed/large_trades_BTCUSDT_2024-11-05.csv")
OUT = Path("data/processed/premium_with_large_trades_2024-11-05.csv")

prem = pd.read_csv(PREM)
large = pd.read_csv(LARGE, usecols=["t_sec","venue","qty_base","side"])

# Flag seconds with at least one large trade (pooled)
large_flag = (
    large.groupby("t_sec")
         .size()
         .rename("large_trade_count")
         .reset_index()
)

prem = prem.merge(large_flag, on="t_sec", how="left")
prem["large_trade_count"] = prem["large_trade_count"].fillna(0).astype(int)
prem["has_large_trade"] = prem["large_trade_count"] > 0

prem.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("\nSeconds with ≥1 large trade:", prem["has_large_trade"].sum())
print("\nPremium stats when NO large trade:")
print(prem.loc[~prem["has_large_trade"], "log_premium"].describe()[["mean","std","min","max"]])
print("\nPremium stats when LARGE trade present:")
print(prem.loc[prem["has_large_trade"], "log_premium"].describe()[["mean","std","min","max"]])
