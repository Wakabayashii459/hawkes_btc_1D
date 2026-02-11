import csv
import argparse
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

def parse_dt_utc(s: str) -> datetime:
    s = s.strip().replace(" ", "T")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def mean(dq: deque) -> float:
    return sum(dq) / len(dq) if dq else float("nan")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--venue", required=True, choices=["binance","bybit","gate"])
    ap.add_argument("--center", required=True)  # e.g. 2024-11-05T15:30:27+00:00
    ap.add_argument("--window", type=int, default=30)
    ap.add_argument("--roll30", type=int, default=30)
    ap.add_argument("--roll300", type=int, default=300)
    ap.add_argument("--ewma_span", type=int, default=30)
    args = ap.parse_args()

    infile = Path(args.infile)
    if not infile.exists():
        raise SystemExit(f"Missing infile: {infile}")

    center = parse_dt_utc(args.center)
    start = center.timestamp() - args.window
    end   = center.timestamp() + args.window

    alpha = 2.0 / (args.ewma_span + 1.0)
    ewma = None

    dq30 = deque()
    dq300 = deque()

    out_dir = Path("outputs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"shock_window_{args.venue}_{center.strftime('%Y%m%dT%H%M%SZ')}.csv"

    wrote = 0
    with infile.open("r", newline="") as f, out_path.open("w", newline="") as g:
        reader = csv.DictReader(f)
        need = {"dt_utc","venue","log_premium"}
        missing = need - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing columns in {infile.name}: {sorted(missing)}")

        writer = csv.DictWriter(g, fieldnames=[
            "dt_utc","venue","log_premium","roll_mean_30s","roll_mean_300s","ewma_30s"
        ])
        writer.writeheader()

        for row in reader:
            venue = row["venue"].strip().lower()
            if venue != args.venue:
                continue

            dt = parse_dt_utc(row["dt_utc"])
            t = dt.timestamp()
            prem = float(row["log_premium"])

            dq30.append(prem)
            if len(dq30) > args.roll30:
                dq30.popleft()

            dq300.append(prem)
            if len(dq300) > args.roll300:
                dq300.popleft()

            ewma = prem if ewma is None else (alpha * prem + (1 - alpha) * ewma)

            if start <= t <= end:
                writer.writerow({
                    "dt_utc": dt.isoformat(),
                    "venue": venue,
                    "log_premium": f"{prem:.12g}",
                    "roll_mean_30s": f"{mean(dq30):.12g}",
                    "roll_mean_300s": f"{mean(dq300):.12g}",
                    "ewma_30s": f"{ewma:.12g}",
                })
                wrote += 1

    if wrote == 0:
        raise SystemExit("No rows written. Check venue/center timestamp.")
    print("Wrote:", out_path)
    print("Rows:", wrote)

if __name__ == "__main__":
    main()
