import numpy as np
import pandas as pd
from pathlib import Path

EVENTS_CSV = Path("data/processed/large_trades_BTCUSDT_2024-11-05.csv")
PARAMS_TXT = Path("data/processed/hawkes_fit_params_strict_2024-11-05.txt")
OUT = Path("data/processed/hawkes_lambda_1s_strict_2024-11-05.csv")

# Load params
txt = PARAMS_TXT.read_text().splitlines()
vals = {}
for line in txt:
    if ":" in line:
        k, v = line.split(":", 1)
        vals[k.strip()] = v.strip()
mu = float(vals["mu"])
alpha = float(vals["alpha"])
beta = float(vals["beta"])

# Load events (absolute seconds)
ev = pd.read_csv(EVENTS_CSV, usecols=["ts_ms"])
t_abs = np.sort(ev["ts_ms"].astype(np.int64).values) / 1000.0

t0 = t_abs[0]
t = t_abs - t0
T = t[-1]

# 1-second grid in relative seconds
grid = np.arange(0, int(np.floor(T)) + 1, 1, dtype=float)

# Compute R(t) exactly by walking forward in time and consuming events
lam = np.empty_like(grid)
R = 0.0
j = 0
last_time = 0.0

for i, g in enumerate(grid):
    # decay from last_time to g
    R *= np.exp(-beta * (g - last_time))

    # process all events up to time g in chronological order
    while j < len(t) and t[j] <= g:
        # decay from last_time to event time
        R *= np.exp(-beta * (t[j] - last_time))
        # event adds 1 to the kernel sum at its time
        R += 1.0
        last_time = t[j]
        j += 1

    # decay from last_time to grid time g (if last event earlier)
    R *= np.exp(-beta * (g - last_time))
    last_time = g

    lam[i] = mu + alpha * R

out = pd.DataFrame({
    "t_sec": (grid + t0).astype("int64"),
    "dt_utc": pd.to_datetime((grid + t0) * 1000.0, unit="ms", utc=True),
    "lambda": lam
})

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print("Wrote:", OUT)
print(out["lambda"].describe()[["min","mean","std","max"]])
print("Top 5 lambda seconds:")
print(out.sort_values("lambda", ascending=False).head(5).to_string(index=False))
