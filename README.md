# Cross-Venue BTCUSDT Premium by Hawkes 1D

Repository to reproduce pipeline analyzing BTCUSDT cross-venue premiums by Hawkes model on November 5th 2024 under clustered order flow (Binance, Bybit, and Gate).

The methodology, results, figures, and trading interpretation are provided in the PDF report.

---

## Topics

- Trade size distributions   
- Cross-venue premium estimation  
- Hawkes-based flow regime detection  

---

## Environment

- WSL2 (Ubuntu)
- Python 3.12  

---

## Data

Required raw files, place them into: 
```
data/raw
```

- `BTCUSDT-trades-2024-11-05.zip`   (Binance) [Link](https://data.binance.vision/?prefix=data/futures/um/daily/trades/BTCUSDT/)
- `BTCUSDT2024-11-05.csv.gz`       (Bybit) [Link](https://www.bybit.com/derivatives/en/history-data)
- `BTC_USDT-202411.csv.gz`         (Gate) [Link](https://www.gate.com/developer/historical_quotes)



---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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


