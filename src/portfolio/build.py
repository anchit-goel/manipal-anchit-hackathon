"""Build the SYNTHETIC wholesale-bank portfolio (seeded, reproducible, no real client data)."""
import numpy as np
import pandas as pd

from src.config import PORTFOLIO_FILE, get_logger
from src.universe import load_universe

logger = get_logger("portfolio.build")

SEED = 20260101

# (asset_type, subtype, ticker, extra_tags, rating, size_mn_lo, size_mn_hi, maturity_years)
# Ticker keys into data/universe.csv. Tags drive exposure-aware stress transmission.
SPEC = [
    # --- Corporate loans: shipping / trade finance concentration ---
    ("loan", "trade_finance", "ZIM", "shipping|trade_finance|asia_trade", "BB", 35, 55, 1.0),
    ("loan", "trade_finance", "MAERSK-B.CO", "shipping|trade_finance|asia_trade", "BBB", 40, 60, 1.0),
    ("loan", "trade_finance", "TM", "trade_finance|asia_trade|automotive", "A", 25, 40, 1.0),
    ("loan", "trade_finance", "HDB", "trade_finance|asia_trade|india_banking", "BBB", 25, 40, 1.0),
    ("loan", "revolver", "ZIM", "shipping|asia_trade", "BB", 30, 45, 3.0),
    ("loan", "term_loan", "MAERSK-B.CO", "shipping|asia_trade", "BBB", 45, 65, 5.0),
    # --- Corporate loans: energy producers vs consumers ---
    ("loan", "revolver", "XOM", "energy_producer", "AA", 40, 60, 3.0),
    ("loan", "term_loan", "CVX", "energy_producer", "AA", 35, 55, 5.0),
    ("loan", "revolver", "SHEL", "energy_producer", "A", 30, 50, 3.0),
    ("loan", "term_loan", "BP", "energy_producer", "A", 30, 45, 5.0),
    ("loan", "revolver", "DAL", "airline|energy_consumer", "BB", 40, 60, 3.0),
    ("loan", "term_loan", "DAL", "airline|energy_consumer", "BB", 30, 45, 6.0),
    # --- Corporate loans: others ---
    ("loan", "term_loan", "BA", "aerospace|airline_supplier", "BBB", 35, 55, 5.0),
    ("loan", "revolver", "TSLA", "automotive|chip_dependent", "BB", 25, 40, 3.0),
    ("loan", "revolver", "NVDA", "semiconductor|tech", "A", 30, 45, 3.0),
    ("loan", "term_loan", "TSM", "semiconductor|asia_trade", "AA", 35, 50, 5.0),
    ("loan", "term_loan", "ICICIBANK.NS", "india_banking|asia_trade", "BBB", 20, 35, 4.0),
    ("loan", "revolver", "MSFT", "tech", "AAA", 25, 40, 3.0),
    # --- Bonds: banks (US/EU) ---
    ("bond", "ig_bond", "JPM", "us_banking|rate_sensitive", "A", 25, 45, 6.0),
    ("bond", "ig_bond", "BAC", "us_banking|rate_sensitive", "A", 25, 45, 7.0),
    ("bond", "ig_bond", "C", "us_banking|rate_sensitive", "BBB", 30, 50, 7.0),
    ("bond", "ig_bond", "HSBA.L", "eu_banking|rate_sensitive", "A", 25, 40, 6.0),
    # --- Bonds: corporates ---
    ("bond", "ig_bond", "XOM", "energy_producer|rate_sensitive", "AA", 20, 35, 8.0),
    ("bond", "ig_bond", "SHEL", "energy_producer|rate_sensitive", "A", 20, 35, 7.0),
    ("bond", "ig_bond", "AAPL", "tech|rate_sensitive", "AA", 20, 35, 9.0),
    ("bond", "ig_bond", "MAERSK-B.CO", "shipping|asia_trade", "BBB", 15, 30, 5.0),
    ("bond", "hy_bond", "DAL", "airline|energy_consumer", "BB", 15, 30, 5.0),
    ("bond", "hy_bond", "ZIM", "shipping|asia_trade", "BB", 10, 25, 4.0),
    ("bond", "hy_bond", "TSLA", "automotive|chip_dependent", "BB", 10, 25, 5.0),
    ("bond", "hy_bond", "BA", "aerospace|airline_supplier", "BB", 15, 30, 6.0),
    # --- Derivatives (bank view): notional and delta, MTM exposure ~2% of notional ---
    ("derivative", "irs", "JPM", "us_banking|rate_sensitive|rates", "A", 200, 350, 7.0),
    ("derivative", "irs", "C", "us_banking|rate_sensitive|rates", "BBB", 150, 300, 5.0),
    ("derivative", "irs", "HSBA.L", "eu_banking|rate_sensitive|rates", "A", 150, 300, 5.0),
    ("derivative", "irs", "BAC", "us_banking|rate_sensitive|rates", "A", 150, 250, 5.0),
    ("derivative", "fx_forward", "MAERSK-B.CO", "shipping|asia_trade|fx", "BBB", 80, 140, 1.0),
    ("derivative", "fx_forward", "TM", "automotive|asia_trade|fx", "A", 60, 120, 1.0),
    ("derivative", "commodity_swap", "DAL", "airline|energy_consumer|oil", "BB", 120, 200, 2.0),
    ("derivative", "commodity_swap", "CVX", "energy_producer|oil", "AA", 120, 200, 2.0),
    ("derivative", "commodity_swap", "XOM", "energy_producer|oil", "AA", 100, 180, 2.0),
    ("derivative", "commodity_swap", "SHEL", "energy_producer|oil", "A", 80, 150, 2.0),
    # --- Equities: strategic holdings ---
    ("equity", "strategic", "JPM", "us_banking", "", 15, 30, 0.0),
    ("equity", "strategic", "C", "us_banking", "", 15, 30, 0.0),
    ("equity", "strategic", "HSBA.L", "eu_banking", "", 12, 25, 0.0),
    ("equity", "strategic", "NVDA", "semiconductor|tech", "", 20, 35, 0.0),
    ("equity", "strategic", "TSM", "semiconductor|asia_trade", "", 20, 35, 0.0),
    ("equity", "strategic", "XOM", "energy_producer", "", 15, 30, 0.0),
    ("equity", "strategic", "DAL", "airline|energy_consumer", "", 10, 20, 0.0),
    ("equity", "strategic", "MAERSK-B.CO", "shipping|asia_trade", "", 10, 20, 0.0),
    ("equity", "strategic", "MSFT", "tech", "", 15, 30, 0.0),
    ("equity", "strategic", "BA", "aerospace|airline_supplier", "", 10, 20, 0.0),
]

REGION = {"USA": "North America", "GBR": "Europe", "DNK": "Europe", "ISR": "Middle East",
          "IND": "Asia", "TWN": "Asia", "JPN": "Asia"}

# Bank delta on commodity swaps: bank is short oil vs airlines hedging, long vs producers.
COMMODITY_DELTA = {"DAL": -0.6, "CVX": 0.5, "XOM": 0.5, "SHEL": 0.4}


def build_portfolio(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    uni = {c.ticker: c for c in load_universe()}
    rows = []
    for i, (atype, sub, tkr, tags, rating, lo, hi, mat) in enumerate(SPEC, start=1):
        c = uni[tkr]
        size = round(float(rng.uniform(lo, hi)) * 1e6, -4)
        if atype == "derivative":
            notional = size
            mv = round(notional * 0.02, -3)
            if sub == "irs":
                delta = round(float(rng.uniform(0.35, 0.6)), 2)
            elif sub == "commodity_swap":
                delta = COMMODITY_DELTA[tkr]
            else:
                delta = round(float(rng.uniform(0.2, 0.5)), 2)
            duration = 0.0
            collateral = round(float(rng.choice([0.5, 0.7, 0.9])), 2)
        else:
            notional = size
            mv = size
            delta = 0.0
            duration = round(min(mat * 0.85, 9.0), 1) if atype == "bond" else 0.0
            collateral = round(float(rng.choice([0.0, 0.2, 0.4])), 2) if atype == "loan" else 0.0
            if atype == "loan" and sub == "trade_finance":
                collateral = round(float(rng.choice([0.1, 0.25])), 2)
        rows.append({
            "position_id": f"pos_{i:03d}",
            "asset_type": atype,
            "subtype": sub,
            "counterparty": c.name,
            "ticker": tkr,
            "sector": c.sector,
            "country": c.country,
            "region": REGION.get(c.country, "Other"),
            "rating": rating,
            "market_value": mv,
            "notional": notional,
            "duration": duration,
            "maturity_years": mat,
            "delta": delta,
            "collateral_pct": collateral,
            "tags": tags,
        })
    df = pd.DataFrame(rows)
    df["synthetic"] = True
    return df


def main():
    df = build_portfolio()
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PORTFOLIO_FILE, index=False)
    print(f"Wrote {len(df)} SYNTHETIC positions to {PORTFOLIO_FILE}; total MV = ${df.market_value.sum() / 1e9:.2f}B")
    print(df.groupby("asset_type").market_value.agg(["count", "sum"]))


if __name__ == "__main__":
    main()
