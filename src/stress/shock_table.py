"""Theme x exposure-tag shock table. Values are at REFERENCE severity (impact 8) and scaled per signal.

Direction comes from the THEME (e.g. oil_price_up helps producers, hurts airlines), never from the
entity's sentiment. Equity values are replaced by measured event-study medians where the calibration
seed has n >= 2 for the matching (theme, sector ETF); everything else is a documented assumption.
"""
from typing import Dict, List, Tuple

import pandas as pd

from src.config import SHOCK_SEED_FILE, SHOCK_TABLE_FILE, get_logger

logger = get_logger("stress.shock_table")

TAG_ETF = {
    "energy_producer": "XLE", "us_banking": "XLF", "eu_banking": "XLF", "semiconductor": "SMH",
    "shipping": "BDRY", "tech": "XLK", "aerospace": "ITA", "airline": "JETS",
}

# (theme, tag, equity_pct, spread_bps, pd_bump_pct, underlying_pct, rationale)
ASSUMED_ROWS: List[Tuple] = [
    ("shipping_disruption", "trade_finance", -4, 60, 3.0, 0, "Rerouted voyages strain trade-finance borrowers"),
    ("shipping_disruption", "shipping", -6, 90, 2.5, 0, "Carrier credit stress; equity side reflects freight-rate windfall when measured"),
    ("shipping_disruption", "asia_trade", -1, 30, 1.0, 0, "Asia-Europe lanes delayed, working capital stress"),
    ("shipping_disruption", "energy_consumer", -1, 10, 0.3, 0, "Higher bunker and logistics costs"),
    ("oil_price_up", "energy_producer", 8, -15, -0.3, 0, "Higher realised crude price lifts margins"),
    ("oil_price_up", "airline", -12, 120, 3.5, 0, "Jet fuel is the largest variable cost"),
    ("oil_price_up", "energy_consumer", -10, 80, 3.0, 0, "Input cost squeeze"),
    ("oil_price_up", "oil", 0, 0, 0.0, 8, "Oil swap underlying moves +8% at reference severity"),
    ("oil_price_down", "energy_producer", -9, 50, 1.5, 0, "Lower realised price compresses margins"),
    ("oil_price_down", "airline", 6, -40, -1.0, 0, "Fuel cost relief"),
    ("oil_price_down", "energy_consumer", 4, -25, -0.5, 0, "Input cost relief"),
    ("oil_price_down", "oil", 0, 0, 0.0, -8, "Oil swap underlying moves -8% at reference severity"),
    ("credit_downgrade", "us_banking", -6, 70, 1.0, 0, "Funding-cost and counterparty-risk repricing"),
    ("credit_downgrade", "eu_banking", -4, 50, 0.7, 0, "Contagion to peers"),
    ("credit_default", "us_banking", -10, 150, 2.0, 0, "Sovereign/counterparty default losses"),
    ("credit_default", "eu_banking", -8, 120, 1.6, 0, "Cross-border contagion"),
    ("credit_default", "india_banking", -5, 80, 1.0, 0, "EM bank spillover"),
    ("credit_default", "trade_finance", -2, 60, 2.0, 0, "Trade credit tightens"),
    ("banking_stress", "us_banking", -12, 120, 1.5, 0, "Liquidity run risk"),
    ("banking_stress", "eu_banking", -10, 100, 1.2, 0, "Liquidity contagion"),
    ("banking_stress", "rate_sensitive", -2, 20, 0.2, 0, "Flight-to-quality spread widening"),
    ("rate_hike", "rate_sensitive", -4, 40, 0.3, 0, "Duration loss on fixed-rate book"),
    ("rate_hike", "tech", -6, 20, 0.2, 0, "Long-duration equity de-rating"),
    ("rate_hike", "rates", 0, 0, 0.0, 0.8, "Pay-fixed swap MTM gain per unit of notional delta"),
    ("rate_cut", "rate_sensitive", 3, -30, -0.2, 0, "Duration gain"),
    ("rate_cut", "tech", 4, -10, -0.1, 0, "Equity re-rating"),
    ("rate_cut", "rates", 0, 0, 0.0, -0.8, "Pay-fixed swap MTM loss"),
    ("regulatory_action", "aerospace", -6, 50, 1.0, 0, "Production and delivery constraints"),
    ("regulatory_action", "tech", -3, 15, 0.2, 0, "Compliance cost"),
    ("antitrust", "tech", -7, 25, 0.3, 0, "Business-model remedies risk"),
    ("antitrust", "semiconductor", -8, 30, 0.4, 0, "Bundling and licensing scrutiny"),
    ("chip_supply_shock", "semiconductor", -10, 60, 1.2, 0, "Packaging/fab capacity shock"),
    ("chip_supply_shock", "chip_dependent", -8, 70, 1.5, 0, "Production line stoppages"),
    ("chip_supply_shock", "tech", -4, 20, 0.3, 0, "Hardware supply constraints"),
    ("sanctions", "energy_producer", -5, 40, 0.8, 0, "Export restrictions and compliance"),
    ("sanctions", "shipping", -4, 50, 1.0, 0, "Trade-lane restrictions"),
    ("sanctions", "asia_trade", -2, 20, 0.5, 0, "Secondary sanction risk"),
    ("demand_shock", "asia_trade", -5, 50, 1.0, 0, "Export volumes fall"),
    ("demand_shock", "shipping", -6, 70, 1.5, 0, "Freight volumes fall"),
    ("demand_shock", "airline", -8, 80, 2.0, 0, "Travel demand falls"),
    ("demand_shock", "tech", -4, 20, 0.3, 0, "Capex cuts"),
]

COLUMNS = ["theme", "tag", "equity_pct", "spread_bps", "pd_bump_pct", "underlying_pct", "source", "rationale"]


def _measured_lookup() -> Dict[Tuple[str, str], float]:
    """(theme, etf) -> measured median abnormal move for cells with n >= 2."""
    if not SHOCK_SEED_FILE.exists():
        return {}
    seed = pd.read_csv(SHOCK_SEED_FILE)
    seed = seed[(seed["n_events"] >= 2) & (seed["data_status"] == "measured")]
    return {(r.theme, r.sector_or_etf): float(r.median_car_pct) for r in seed.itertuples()}


def build_shock_table() -> pd.DataFrame:
    measured = _measured_lookup()
    rows = []
    for theme, tag, eq, spr, pd_bump, und, why in ASSUMED_ROWS:
        source = "assumed"
        etf = TAG_ETF.get(tag)
        if etf and eq != 0 and (theme, etf) in measured:
            eq = measured[(theme, etf)]
            source = "measured"
            why += f" (equity from event study, {etf})"
        rows.append([theme, tag, eq, spr, pd_bump, und, source, why])
    return pd.DataFrame(rows, columns=COLUMNS)


def save_shock_table() -> pd.DataFrame:
    df = build_shock_table()
    SHOCK_TABLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SHOCK_TABLE_FILE, index=False)
    return df


def load_shock_table() -> pd.DataFrame:
    if not SHOCK_TABLE_FILE.exists():
        return save_shock_table()
    return pd.read_csv(SHOCK_TABLE_FILE)


if __name__ == "__main__":
    t = save_shock_table()
    print(t.head(10).to_string(index=False))
    print(t.source.value_counts())
