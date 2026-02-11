import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

files = {
    "Binance": "outputs/figures/shock_window_binance_20241105T153027Z.csv",
    "Bybit":   "outputs/figures/shock_window_bybit_20241105T153027Z.csv",
    "Gate":    "outputs/figures/shock_window_gate_20241105T153027Z.csv",
}

fig, axes = plt.subplots(1, 3, figsize=(15,4), sharey=True)

for ax, (name, path) in zip(axes, files.items()):
    df = pd.read_csv(path)
    df["dt_utc"] = pd.to_datetime(df["dt_utc"])

    ax.plot(df["dt_utc"], df["log_premium"], label="raw", lw=1.5)
    ax.plot(df["dt_utc"], df["roll_mean_30s"], label="roll mean 30s", alpha=0.8)
    ax.plot(df["dt_utc"], df["ewma_30s"], label="EWMA 30s", alpha=0.8)

    ax.set_title(name)
    ax.tick_params(axis='x', rotation=45)

axes[0].set_ylabel("log premium")
axes[0].legend()

plt.tight_layout()
Path("outputs/figures").mkdir(exist_ok=True, parents=True)
plt.savefig("outputs/figures/figure1_shock_window.png", dpi=150)
print("Saved outputs/figures/figure1_shock_window.png")
