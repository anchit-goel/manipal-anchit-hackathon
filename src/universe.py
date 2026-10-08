"""Wholesale banking counterparty universe and entity matching."""
import csv
import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from src.config import UNIVERSE_CSV, get_logger

logger = get_logger("universe")


class CompanyExposure(BaseModel):
    """Systemic wholesale banking counterparty exposure record."""
    ticker: str = Field(..., description="Primary equity/bond ticker symbol")
    name: str = Field(..., description="Official entity legal name")
    aliases: List[str] = Field(default_factory=list, description="Common aliases and name variants")
    sector: str = Field(..., description="Industry sector classification")
    country: str = Field(..., description="Country of primary risk exposure")
    sector_etf: str = Field(..., description="Benchmark sector ETF ticker")


# Module-level cache for universe
_UNIVERSE_CACHE: Optional[List[CompanyExposure]] = None


def load_universe(filepath: Optional[Path] = None) -> List[CompanyExposure]:
    """Load the wholesale counterparty universe from CSV with caching."""
    global _UNIVERSE_CACHE
    if _UNIVERSE_CACHE is not None and filepath is None:
        return _UNIVERSE_CACHE

    target_path = filepath or UNIVERSE_CSV
    if not target_path.exists():
        logger.warning("Universe file not found at %s. Returning empty universe.", target_path)
        return []

    universe: List[CompanyExposure] = []
    with open(target_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            alias_list = [a.strip() for a in row.get("aliases", "").split("|") if a.strip()]
            item = CompanyExposure(
                ticker=row["ticker"].strip(),
                name=row["name"].strip(),
                aliases=alias_list,
                sector=row["sector"].strip(),
                country=row["country"].strip(),
                sector_etf=row["sector_etf"].strip(),
            )
            universe.append(item)

    if filepath is None:
        _UNIVERSE_CACHE = universe
    logger.info("Loaded %d companies into risk universe from %s", len(universe), target_path.name)
    return universe


def match_all_companies(text: str, universe: Optional[List[CompanyExposure]] = None) -> List[CompanyExposure]:
    """Find all matching companies in text based on ticker, name, or alias."""
    if not text:
        return []

    if universe is None:
        universe = load_universe()

    matched: List[CompanyExposure] = []
    seen_tickers = set()

    for comp in universe:
        if comp.ticker in seen_tickers:
            continue

        # Candidate tokens to test against text
        # Extract base ticker without exchange suffix (e.g. ICICIBANK.NS -> ICICIBANK)
        base_ticker = comp.ticker.split(".")[0].split("-")[0]
        candidates = {comp.name.lower(), base_ticker.lower()}
        if len(comp.ticker) > 2:
            candidates.add(comp.ticker.lower())
        for alias in comp.aliases:
            candidates.add(alias.lower())

        found = False
        for token in sorted(candidates, key=len, reverse=True):
            if len(token) < 2:
                continue
            # Use regex word boundary
            pattern = r"(?<!\w)" + re.escape(token) + r"(?!\w)"
            if re.search(pattern, text, flags=re.IGNORECASE):
                found = True
                break

        if found:
            matched.append(comp)
            seen_tickers.add(comp.ticker)

    return matched


def match_company(text: str, universe: Optional[List[CompanyExposure]] = None) -> Optional[CompanyExposure]:
    """Find the single most prominent company match in text, or None."""
    matches = match_all_companies(text, universe)
    return matches[0] if matches else None
