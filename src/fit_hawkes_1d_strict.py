import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import minimize

EVENTS_CSV = Path("data/processed/large_trades_BTCUSDT_2024-11-05.csv")
OUT_PARAMS = Path("data/processed/hawkes_fit_params_strict_2024-11-05.txt")

# Load pooled events (seconds, sorted)
ev = pd.read_csv(EVENTS_CSV, usecols=["ts_ms"])
t_abs = np.sort(ev["ts_ms"].astype(np.int64).values) / 1000.0  # seconds UTC

t0 = t_abs[0]
t = t_abs - t0
T = t[-1]
n = len(t)

if n < 200:
    raise SystemExit(f"Too few events ({n}).")

# Exponential Hawkes:
# lambda(t) = mu + alpha * sum_{ti<t} exp(-beta (t-ti))
# with stability alpha/beta < 1

def neg_loglik(x):
    mu, alpha, beta = x
    if mu <= 0 or alpha <= 0 or beta <= 0:
        return 1e50

    # strict stability margin
    if alpha >= 0.95 * beta:
        return 1e50

    # Recursion:
    # R_i = sum_{j<i} exp(-beta (t_i - t_j))
    # R_1 = 0
    # R_i = exp(-beta * (t_i - t_{i-1})) * (1 + R_{i-1})
    R = 0.0
    ll = 0.0
    for i in range(n):
        if i == 0:
            R = 0.0
        else:
            dt = t[i] - t[i-1]
            R = np.exp(-beta * dt) * (1.0 + R)
        lam = mu + alpha * R
        if lam <= 0:
            return 1e50
        ll += np.log(lam)

    # Integral term:
    # ∫0^T λ(u)du = mu*T + (alpha/beta) * sum_{i=1}^n (1 - exp(-beta*(T - t_i)))
    integral = mu * T + (alpha / beta) * np.sum(1.0 - np.exp(-beta * (T - t)))
    return -(ll - integral)

# Initial guesses
mu0 = n / T                    # events per second
beta0 = 1.0 / 30.0             # 30s half-ish
alpha0 = 0.5 * beta0           # make branching ratio ~0.5 initially

x0 = np.array([max(mu0, 1e-6), max(alpha0, 1e-6), max(beta0, 1e-6)], dtype=float)
bounds = [(1e-9, None), (1e-9, None), (1e-9, None)]

res = minimize(neg_loglik, x0, method="L-BFGS-B", bounds=bounds)

if not res.success:
    raise SystemExit(f"Optimization failed: {res.message}")

mu, alpha, beta = res.x
branch = alpha / beta
half_life = np.log(2) / beta

OUT_PARAMS.parent.mkdir(parents=True, exist_ok=True)
OUT_PARAMS.write_text(
    f"Events: {n}\n"
    f"T (seconds): {T:.3f}\n"
    f"mu: {mu:.10f}\n"
    f"alpha: {alpha:.10f}\n"
    f"beta: {beta:.10f}\n"
    f"branching_ratio(alpha/beta): {branch:.6f}\n"
    f"half_life_seconds: {half_life:.3f}\n"
)

print("STRICT Hawkes (1D exp kernel) fitted")
print(OUT_PARAMS.read_text())
