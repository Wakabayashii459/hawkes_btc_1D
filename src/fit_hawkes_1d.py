import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import minimize

EVENTS_CSV = Path("data/processed/large_trades_BTCUSDT_2024-11-05.csv")
OUT_PARAMS = Path("data/processed/hawkes_fit_params_2024-11-05.txt")

# ---- Load events (pooled across venues) ----
ev = pd.read_csv(EVENTS_CSV, usecols=["ts_ms"])
ev = ev.dropna()
t = ev["ts_ms"].astype(np.int64).values / 1000.0  # seconds
t = np.sort(t)

# Shift to start at 0 for numerical stability
t0 = t[0]
t = t - t0
T = t[-1]

if len(t) < 100:
    raise SystemExit(f"Too few events ({len(t)}). Check threshold or input file.")

# ---- Hawkes exponential kernel MLE ----
# lambda(t) = mu + alpha * sum_{ti < t} exp(-beta (t-ti))
# Stability: branching ratio n = alpha/beta < 1

def neg_loglik(x):
    mu, alpha, beta = x
    if mu <= 0 or alpha <= 0 or beta <= 0:
        return 1e50
    if alpha >= 0.999 * beta:
        return 1e50

    # Recursion for S_i = sum_{j<i} exp(-beta (t_i - t_j))
    S = 0.0
    ll = 0.0
    prev = 0.0

    for i in range(len(t)):
        dt = t[i] - prev
        # update decay
        S = np.exp(-beta * dt) * (S + 1.0 if i > 0 else 0.0)
        lam = mu + alpha * S
        if lam <= 0:
            return 1e50
        ll += np.log(lam)
        prev = t[i]

    # Integral term: ∫0^T λ(u) du = mu*T + (alpha/beta) * sum_{ti<=T} (1 - exp(-beta*(T-ti)))
    integral = mu * T + (alpha / beta) * np.sum(1.0 - np.exp(-beta * (T - t)))
    return -(ll - integral)

# Initial guesses (reasonable)
# mu ~ events per second
mu0 = len(t) / T
alpha0 = 0.5 * mu0
beta0 = 1.0 / 30.0  # 30s decay initial guess

x0 = np.array([max(mu0, 1e-6), max(alpha0, 1e-6), max(beta0, 1e-6)], dtype=float)

bounds = [(1e-9, None), (1e-9, None), (1e-9, None)]

res = minimize(neg_loglik, x0, method="L-BFGS-B", bounds=bounds)

if not res.success:
    raise SystemExit(f"Optimization failed: {res.message}")

mu, alpha, beta = res.x
branch = alpha / beta

OUT_PARAMS.parent.mkdir(parents=True, exist_ok=True)
OUT_PARAMS.write_text(
    f"Events: {len(t)}\n"
    f"T (seconds): {T:.3f}\n"
    f"mu: {mu:.10f}\n"
    f"alpha: {alpha:.10f}\n"
    f"beta: {beta:.10f}\n"
    f"branching_ratio(alpha/beta): {branch:.6f}\n"
    f"half_life_seconds: {np.log(2)/beta:.3f}\n"
)

print("Fitted Hawkes (1D exp kernel)")
print(OUT_PARAMS.read_text())
