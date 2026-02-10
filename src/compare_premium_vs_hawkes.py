import pandas as pd
from pathlib import Path

PREM = Path("data/processed/premium_1s_BTCUSDT_2024-11-05.csv")
LAM_OLD = Path("data/processed/hawkes_lambda_1s_2024-11-05.csv")
LAM_NEW = Path("data/processed/hawkes_lambda_1s_strict_2024-11-05.csv")

prem = pd.read_csv(PREM)
old = pd.read_csv(LAM_OLD)[["t_sec","lambda"]].rename(columns={"lambda":"lambda_old"})
new = pd.read_csv(LAM_NEW)[["t_sec","lambda"]].rename(columns={"lambda":"lambda_strict"})

df = prem.merge(old, on="t_sec", how="left").merge(new, on="t_sec", how="left")
df = df.dropna(subset=["log_premium","lambda_old","lambda_strict"])

def regime_from_lambda(x, p50, p90, p99):
    if x >= p99: return ">=p99"
    if x >= p90: return "p90-p99"
    if x >= p50: return "p50-p90"
    return "<p50"

out_rows = []

for col in ["lambda_old", "lambda_strict"]:
    p50 = df[col].quantile(0.50)
    p90 = df[col].quantile(0.90)
    p99 = df[col].quantile(0.99)
    tmp = df.copy()
    tmp["regime"] = tmp[col].apply(lambda z: regime_from_lambda(z, p50, p90, p99))
    stats = tmp.groupby("regime")["log_premium"].describe()[["count","mean","std","min","max"]]
    stats["model"] = col
    stats["p50"] = p50
    stats["p90"] = p90
    stats["p99"] = p99
    out_rows.append(stats.reset_index())

res = pd.concat(out_rows, ignore_index=True)
OUT = Path("data/processed/premium_regime_compare_old_vs_strict.csv")
res.to_csv(OUT, index=False)

print("Wrote:", OUT)
print(res)
