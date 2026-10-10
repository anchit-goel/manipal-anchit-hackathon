"""Empirical event study module: Market-model cumulative abnormal returns (CAR)."""
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

from src.config import (
    CALIBRATION_EVENTS_FILE,
    CALIBRATION_PRICES_DIR,
    get_logger,
)

logger = get_logger("calibration.event_study")


def load_price_series(ticker: str, prices_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load daily adjusted price series from disk cache or yfinance."""
    cache_dir = prices_dir or CALIBRATION_PRICES_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    csv_path = cache_dir / f"{ticker.upper()}.csv"

    if not csv_path.exists():
        logger.info("Fetching online price series for %s...", ticker)
        raw = yf.download(ticker, start="2015-01-01", end="2025-01-01", progress=False)
        if raw.empty:
            raise ValueError(f"No price history retrieved for {ticker}")
        raw.to_csv(csv_path)

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
        if "Price" in first_line:
            df = pd.read_csv(csv_path, header=[0, 1], index_col=0)
            if "Close" in df.columns:
                series = df["Close"].iloc[:, 0]
            else:
                series = df.iloc[:, 0]
        else:
            df = pd.read_csv(csv_path, index_col=0)
            if "Adj Close" in df.columns:
                series = df["Adj Close"]
            elif "Close" in df.columns:
                series = df["Close"]
            else:
                series = df.iloc[:, 0]

        series.index = pd.to_datetime(series.index, errors="coerce", utc=True).tz_localize(None)
        df_out = pd.DataFrame({"adj_close": pd.to_numeric(series, errors="coerce")}).dropna()
        df_out.sort_index(inplace=True)
        return df_out
    except Exception as e:
        logger.warning("Error reading price series %s: %s", csv_path, e)
        raise


def compute_returns(df: pd.DataFrame) -> pd.Series:
    """Compute daily percentage returns from price dataframe."""
    return df["adj_close"].pct_change().dropna()


def estimate_market_model(
    asset_ret: pd.Series,
    bench_ret: pd.Series,
    event_idx: int,
    estimation_days: int = 120,
    gap_days: int = 10,
) -> Tuple[float, float]:
    """Estimate alpha and beta via OLS over estimation window ending gap_days before event."""
    start_idx = max(0, event_idx - estimation_days - gap_days)
    end_idx = max(0, event_idx - gap_days)

    if end_idx - start_idx < 30:
        logger.debug("Too little estimation history (%d days). Using benchmark fallback.", end_idx - start_idx)
        return 0.0, 1.0

    y = asset_ret.iloc[start_idx:end_idx]
    x = bench_ret.iloc[start_idx:end_idx]

    # Align dates
    aligned = pd.concat([y, x], axis=1, join="inner").dropna()
    if len(aligned) < 30:
        return 0.0, 1.0

    r_asset = aligned.iloc[:, 0].values
    r_bench = aligned.iloc[:, 1].values

    var_bench = np.var(r_bench)
    if var_bench < 1e-8:
        return 0.0, 1.0

    cov = np.cov(r_asset, r_bench)[0, 1]
    beta = float(cov / var_bench)
    alpha = float(np.mean(r_asset) - beta * np.mean(r_bench))
    return alpha, beta


def compute_event_car(
    ticker: str,
    benchmark_ticker: str,
    event_date_str: str,
    prices_dir: Optional[Path] = None,
) -> Dict[str, float]:
    """Calculate market model parameters and CAR over [0, +1] and [0, +3] trading days."""
    try:
        asset_df = load_price_series(ticker, prices_dir)
        bench_df = load_price_series(benchmark_ticker, prices_dir)
    except Exception as e:
        logger.warning("Failed loading prices for %s vs %s: %s", ticker, benchmark_ticker, e)
        return {"car_0_1": 0.0, "car_0_3": 0.0, "alpha": 0.0, "beta": 1.0, "verified": 0.0}

    asset_ret = compute_returns(asset_df)
    bench_ret = compute_returns(bench_df)

    # Join returns on common trading days
    combined = pd.concat([asset_ret.rename("asset"), bench_ret.rename("bench")], axis=1, join="inner").dropna()
    combined.sort_index(inplace=True)

    event_dt = pd.to_datetime(event_date_str)

    # Locate nearest trading day on or after event date
    future_dates = combined.index[combined.index >= event_dt]
    if len(future_dates) == 0:
        logger.warning("Event date %s is past price history for %s", event_date_str, ticker)
        return {"car_0_1": 0.0, "car_0_3": 0.0, "alpha": 0.0, "beta": 1.0, "verified": 0.0}

    t0_date = future_dates[0]
    t0_idx = combined.index.get_loc(t0_date)

    # 1. Market model estimation
    alpha, beta = estimate_market_model(combined["asset"], combined["bench"], t0_idx)

    # 2. Abnormal returns
    combined["expected_ret"] = alpha + beta * combined["bench"]
    combined["abnormal_ret"] = combined["asset"] - combined["expected_ret"]

    # 3. CAR windows
    # Window [0, +1] (days t0 and t0+1)
    win_0_1 = combined["abnormal_ret"].iloc[t0_idx : min(len(combined), t0_idx + 2)]
    car_0_1 = float(win_0_1.sum()) * 100.0  # percentage

    # Window [0, +3] (days t0 through t0+3)
    win_0_3 = combined["abnormal_ret"].iloc[t0_idx : min(len(combined), t0_idx + 4)]
    car_0_3 = float(win_0_3.sum()) * 100.0  # percentage

    # 4. Date verification in window [-2, +2]
    verif_start = max(0, t0_idx - 2)
    verif_end = min(len(combined), t0_idx + 3)
    verif_window = combined["abnormal_ret"].iloc[verif_start:verif_end]
    max_abs_day_offset = int(np.argmax(np.abs(verif_window.values)) - (t0_idx - verif_start))
    is_verified = 1.0 if abs(max_abs_day_offset) <= 1 else 0.0

    return {
        "car_0_1": round(car_0_1, 3),
        "car_0_3": round(car_0_3, 3),
        "alpha": round(alpha, 5),
        "beta": round(beta, 3),
        "verified": is_verified,
        "max_shock_offset": max_abs_day_offset,
    }


def run_full_event_study(
    events_csv: Optional[Path] = None,
    prices_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Run event study across all events in events.csv, computing stock and sector CARs."""
    csv_file = events_csv or CALIBRATION_EVENTS_FILE
    if not csv_file.exists():
        raise FileNotFoundError(f"Events CSV not found: {csv_file}")

    events_df = pd.read_csv(csv_file)
    logger.info("Executing empirical event study for %d historical events...", len(events_df))

    results = []
    for _, row in events_df.iterrows():
        eid = str(row["event_id"])
        edate = str(row["event_date"])
        ticker = str(row["affected_ticker"]).strip()
        sector_etf = str(row["sector_etf"]).strip()
        benchmark = str(row["benchmark"]).strip()

        # Compute ticker CAR
        ticker_res = compute_event_car(ticker, benchmark, edate, prices_dir)

        # Compute sector ETF CAR
        sector_res = compute_event_car(sector_etf, benchmark, edate, prices_dir)

        record = {
            "event_id": eid,
            "event_date": edate,
            "region": row["region"],
            "event_class": row["event_class"],
            "themes": row["themes"],
            "description": row["description"],
            "affected_ticker": ticker,
            "sector_etf": sector_etf,
            "benchmark": benchmark,
            "direction_expected": int(row["direction_expected"]),
            "stock_beta": ticker_res["beta"],
            "stock_car_0_1": ticker_res["car_0_1"],
            "stock_car_0_3": ticker_res["car_0_3"],
            "sector_car_0_1": sector_res["car_0_1"],
            "sector_car_0_3": sector_res["car_0_3"],
            "date_verified": bool(ticker_res["verified"] or sector_res["verified"]),
            "notes": row.get("notes", ""),
        }
        results.append(record)

    out_df = pd.DataFrame(results)
    logger.info("Completed event study. Verified %d/%d dates against price shocks.", out_df["date_verified"].sum(), len(out_df))
    return out_df


if __name__ == "__main__":
    df = run_full_event_study()
    print("\n" + "=" * 125)
    print(f"{'ID':<11} | {'DATE':<10} | {'TICKER':<6} | {'SECTOR':<6} | {'STOCK CAR[0,1]':<15} | {'SECT CAR[0,1]':<14} | {'VERIFIED':<8} | {'DESCRIPTION':<35}")
    print("=" * 125)
    for _, r in df.iterrows():
        v_str = "YES" if r["date_verified"] else "CHECK"
        print(f"{r['event_id']:<11} | {r['event_date']:<10} | {r['affected_ticker']:<6} | {r['sector_etf']:<6} | {r['stock_car_0_1']:>+13.2f}% | {r['sector_car_0_1']:>+12.2f}% | {v_str:<8} | {r['description'][:35]}")
    print("=" * 125)
