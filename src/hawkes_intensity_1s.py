import numpy as np
import pandas as pd
from pathlib import Path

EVENTS_CSV = Path("data/processed/large_trades_BTCUSDT_2024-11-05.csv")
PARAMS_TXT = Path("data/processed/hawkes_fit_params_2024-11-05.txt")
OUT = Path("data/processed/hawkes_lambda_1s_2024-11-05.csv")

# Load fitted params
txt = PARAMS_TXT.read_text().splitlines()
vals = {}
for line in txt:
    if ":" in line:
        k, v = line.split(":", 1)
        vals[k.strip()] = v.strip()

mu = float(vals["mu"])
alpha = float(vals["alpha"])
beta = float(vals["beta"])

# Load events
ev = pd.read_csv(EVENTS_CSV, usecols=["ts_ms"])
t_abs = np.sort(ev["ts_ms"].astype(np.int64).values)  # ms UTC
t0 = t_abs[0]
t_s = (t_abs - t0) / 1000.0  # seconds since start
T = t_s[-1]

# Build 1-second grid over the day coverage
# We'll compute lambda at each integer second boundary
grid = np.arange(0, int(np.floor(T)) + 1, 1, dtype=float)

# Efficiently compute S(t) on grid by iterating over time and consuming events
lam = np.empty_like(grid)
S = 0.0
event_idx = 0
prev_time = 0.0

for i, g in enumerate(grid):
    dt = g - prev_time
    if dt < 0:
        dt = 0.0

    # decay S to current grid time
    S = np.exp(-beta * dt) * S
    prev_time = g

    # add all events that occurred in (prev_grid, g]
    # We treat an event as adding 1.0 to S at its timestamp.
    # Approximation: events within the second are applied at grid boundary (good enough for 1s analysis).
    while event_idx < len(t_s) and t_s[event_idx] <= g:
        # bring S to event time (optional refinement skipped for speed)
        S += 1.0
        event_idx += 1

    lam[i] = mu + alpha * S

out = pd.DataFrame({
    "t_sec": (grid + (t0/1000.0)).astype(np.int64),  # absolute UTC seconds
    "dt_utc": pd.to_datetime((grid * 1000.0 + t0), unit="ms", utc=True),
    "lambda": lam
})

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print("Wrote:", OUT)
print("lambda summary:")
print(out["lambda"].describe()[["min","mean","std","max"]])
print("Top 5 lambda seconds:")
print(out.sort_values("lambda", ascending=False).head(5).to_string(index=False))
