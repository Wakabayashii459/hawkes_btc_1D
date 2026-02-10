import pandas as pd
from pathlib import Path

PREM = Path("data/processed/premium_1s_BTCUSDT_2024-11-05.csv")
LAM = Path("data/processed/hawkes_lambda_1s_2024-11-05.csv")

prem = pd.read_csv(PREM)
lam = pd.read_csv(LAM)

# Join on t_sec
prem = prem.merge(lam[["t_sec","lambda"]], on="t_sec", how="left")
prem = prem.dropna(subset=["lambda", "log_premium"])

# Define regimes by lambda quantiles (pooled)
q50 = prem["lambda"].quantile(0.50)
q90 = prem["lambda"].quantile(0.90)
q99 = prem["lambda"].quantile(0.99)

def regime(x):
    if x >= q99: return "lambda>=p99"
    if x >= q90: return "p90<=lambda<p99"
    if x >= q50: return "p50<=lambda<p90"
    return "lambda<p50"

prem["regime"] = prem["lambda"].apply(regime)

OUT = Path("data/processed/premium_with_hawkes_regime_2024-11-05.csv")
prem.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("\nLambda quantiles:", {"p50": q50, "p90": q90, "p99": q99})

print("\nPremium stats by regime (log units):")
print(
    prem.groupby("regime")["log_premium"]
        .describe()[["count","mean","std","min","max"]]
        .sort_index()
)

print("\nPremium tail amplification (|premium| max by regime):")
tmp = prem.copy()
tmp["abs_prem"] = tmp["log_premium"].abs()
print(tmp.groupby("regime")["abs_prem"].max().sort_index())
