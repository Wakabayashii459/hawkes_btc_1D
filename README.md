# Cross-Venue BTCUSDT Premium by Hawkes 1D

## Project Narrative

In a nutshell, the below question encapsulates the project premise:

**BTCUSDT is trading at premium on Binance relative to other venues. Should I sell Binance and buy elsewhere to capitalize on the premium in a very short time frame?** 

The sub-questions are:

- **Is it a false mean reversion signals?**
- **Is it possible that trader run over during aggressive flow?**
- **Is this a real price dislocation or transient?**
- **Why would the backtested strategy not worked live?**

The core problem is that a premium does not tell you *why* the price moved. To answer, I structured the project around three topics:

- Trade size distributions/behaviour
- Robust premium estimation
- Hawkes-based order-flow regime detection

---

## What I built

#### 1. Same schema trade data

Normalization of BTCUSDT trades from Binance ([Link](https://data.binance.vision/?prefix=data/futures/um/daily/trades/BTCUSDT/)), Bybit  ([Link](https://www.bybit.com/derivatives/en/history-data)), and Gate ([Link](https://www.gate.com/developer/historical_quotes)) (It comes as monthly, extracted the 5th of November 2024) into a unified UTC-aligned schema **(Please don't forget to put the files in data/raw).** 
```
timestamp, venue, price, size, side
```

---

#### 2. Trade size distributions

Observations of examination of trade size distributions per venue and in aggregate.

Summary statistics (BTC size):

- Binance: median 0.007, 99% 0.94, 99.9% 2.95  
- Bybit: median 0.013, 99% 0.96, 99.9% 2.64  
- Gate: median 0.0008, 99% 0.39, 99.9% 1.03  
- Pooled: median 0.008, 99% 0.92, 99.9% 2.84 

Two things stand out immediately:

- Trade sizes exhibit heavy tails across three venue.
- Binance dominates large block trades.

Interpretation:
While most trades are small, frequent large trades dominate short-term price moves.
I therefore treat ≥1 BTC trades as discrete events rather then considering them as a noise.
Intuitively, this overlaps with the idea of rolling averages failing (It is not a Gaussian noise, price dynamic is rather driven by clustered aggressive trades) 


#### 3. Robust cross-venue premium construction (1-second)

**What I want the premium to represent:** relative mispricing that is not coming from one venue that immediately reverts

##### Why 1-second time buckets?

- Intuitively, **1 second is the smallest stable common grid** where I can compare venues consistently. **Sub-seconds may be sparse/multi-second may hide the timing of shocks**. By that, I take the **last trade** per venue as that venue’s “current” price.


##### Why median reference (robust) helps?

Instead of being open contamination during shocks with the naive approaches, I used a robust reference price per second as the **cross-venue median**.
By that, if the one venue spikes (or lag) the refernce is not dragged by it, and refernce remins stable during transient dislocations


### Premium definition (log units)

For each venue `v` and second `t`:

- `P_v(t)` = last traded price on venue `v` during second `t`
- `P_ref(t)` = cross-venue median of `{P_v(t)}`

Premium is defined as:

pi_v(t) = log(P_v(t)) - log(P_ref(t))

Log premium decision is based on its approxiamtion is “bps” for small moves, and symmetric for up/down


##### What I am aiming for rather than the naive approach

- A spike on one venue does not become immediately **`fair price'**
- Observing the **asynchronous trading** in 1-second bucket with venues
- To **contaminate shocks** by median

### 4. Naive rolling estimators comparison

I benchmark the raw 1-second premium against 30s rolling mean and 30s EWMA around **15:30:27 UTC**. The reason behind this is it was one of the highest Hawkes-intensity timestamps of the day. 

![Naive rolling comparison across venues](shock_window.png)

**Figure 1:** Raw 1-second log premium versus rolling mean and EWMA for Binance, Bybit, and Gate during a high-intensity window (±30s around 15:30:27 UTC).

Interpretation:

- As it is observed, naive ones lag and react after the move. Therefore, they understate the short-term deviation.
- This illustrates during aggressive flow they are unreliable, while stressed market is driven by large/discrete order flow shock.

Thus, introducing a flow regime signal such as Hawkes justifiable.


#### 5. Hawkes flow regimes

I used 1D Hawkes with exponential kernel, and the large trades (≥ 1 BTC) are treated as discrete events. By estimating time-varying flow intensity λ(t), I am aiming to capture the periods of clustered aggressive trading versus calm periods. 

Model parameters:

- μ: baseline (exogenous) trade arrival rate  
- α: excitation magnitude  
- β: decay speed of excitation  
- α/β: branching ratio (fraction of activity explained by self-excitation)

The fitted model produces λ(t) at 1-second, and each second is assigned to one of four regimes based on λ-quantiles:

- λ < p50  
- p50 ≤ λ < p90  
- p90 ≤ λ < p99  
- λ ≥ p99  

---

##### Table 1 — Raw 1s premium dispersion by Hawkes regime

| Venue   | Regime            | Std        | Min        | Max        |
|---------|-------------------|------------|------------|------------|
| Binance | λ < p50           | 0.000106   | -0.000539  | 0.000160   |
| Binance | p50 ≤ λ < p90     | 0.000102   | -0.002451  | 0.000194   |
| Binance | p90 ≤ λ < p99     | 0.000104   | -0.000795  | 0.000389   |
| Binance | λ ≥ p99           | 0.000131   | -0.001585  | 0.000102   |
| Bybit   | λ < p50           | 0.000096   | -0.000478  | 0.000371   |
| Bybit   | p50 ≤ λ < p90     | 0.000094   | -0.000366  | 0.000606   |
| Bybit   | p90 ≤ λ < p99     | 0.000086   | -0.000456  | 0.000370   |
| Bybit   | λ ≥ p99           | 0.000078   | -0.000800  | 0.000509   |
| Gate    | λ < p50           | 0.000137   | -0.000139  | 0.000671   |
| Gate    | p50 ≤ λ < p90     | 0.000163   | -0.000657  | 0.000717   |
| Gate    | p90 ≤ λ < p99     | 0.000164   | -0.000192  | 0.001084   |
| Gate    | λ ≥ p99           | 0.000181   | -0.000143  | 0.000778   |

*Table 1: Raw 1-second premium statistics conditioned on Hawkes intensity regimes.*

---


##### Interpretation

During calm regimes (λ < p50), premiums are relatively stable. As intensity rises, extreme deviations grow, particularly in the top 1% regime. 

Considering Figure 1 (rolling comparison) also, 

- Naive rolling hides regime shifts
- Tail risk concentrates in high-λ states
- Mean reversion assumptions break precisely when flow is most aggressive

***Practically, λ(t) provides a real-time market state indicator: when λ is elevated, traders may think about reducing size, or switch to passive execution rather than chasing the observed premium.***

---

##### Optional robustness

I also used a stricter Hawkes and compared in `premium_regime_compare_old_vs_strict.csv`. While parameter magnitudes differ, the qualitative result stays the same: premium tails are regime-dependent.

---

#### 6. Final findings, limitations, and extensions

##### Final findings

- During calm flow (low λ), premiums are relatively stable.
- During clustered aggressive flow (high λ), premium variance and tail risk increase.
- Naive rolling estimators neglects lags, and gives a false sense of reliablity.

**Hawkes intensity provides a practical real-time proxy for market stress and signal reliability.**

***“From a trading perspective, treating Hawkes intensity as a risk toggle would be a valuable tool; trade premiums when λ is low, and when λ spikes, step back — size down, widen entries, or go passive — because regime beats signal.”*** 

---

##### Limitations & Extensions

- Only trade data is used (no order book depth or queue dynamics), 
- Hawkes is fit in 1D on large-trade arrivals rather, for the future, Multivariate Hawkes implementation,
- No transaction costs, latency, or inventory constraints are modeled.


---










## Environment

- WSL2 (Ubuntu)
- Python 3.12  

---


## Reproduce Results (run in order)
### 1. Canonicalize raw trade feeds

```
python src/extract_gate_day.py
python src/normalize_binance_day.py
python src/normalize_bybit_day.py
```

### 2. Trade size distributions
```
python src/size_distributions.py
```

### 3. Cross-venue premium construction
```
python src/build_premium_1s.py
```

### 4. Large-trade conditioning
```
python src/large_trade_events.py
python src/join_large_trades_with_premium.py
```

### 5. Hawkes flow regimes
```
python src/fit_hawkes_1d.py
python src/hawkes_intensity_1s.py
python src/premium_vs_hawkes_regime.py
```

### 6. Optional - Strict Hawkes robustness
```
python src/fit_hawkes_1d_strict.py
python src/hawkes_intensity_1s_strict.py
python src/compare_premium_vs_hawkes.py
```

### 7. Naive rolling comparison
```
python src/naive_rolling_comparison.py
```

## Outputs 
```
data/processed/
```






