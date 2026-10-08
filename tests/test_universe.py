"""Unit tests for wholesale universe loading and entity matching."""
from src.universe import CompanyExposure, load_universe, match_company, match_all_companies


def test_load_universe_contains_expected_count():
    """Verify that universe loads 20 institutions across multiple sectors."""
    universe = load_universe()
    assert len(universe) >= 20
    tickers = {c.ticker for c in universe}
    assert "JPM" in tickers
    assert "NVDA" in tickers
    assert "MAERSK-B.CO" in tickers
    assert "XOM" in tickers


def test_match_company_by_ticker():
    """Verify matching by exact ticker symbol."""
    text = "Breakout earnings report for NVDA as AI accelerator demand surges."
    matched = match_company(text)
    assert matched is not None
    assert matched.ticker == "NVDA"
    assert matched.sector == "Semiconductors"


def test_match_company_by_name():
    """Verify matching by full official company name."""
    text = "Citigroup announces strategic portfolio restructuring across EMEA."
    matched = match_company(text)
    assert matched is not None
    assert matched.ticker == "C"
    assert matched.sector == "Banking"


def test_match_company_by_alias():
    """Verify matching by known colloquial aliases."""
    # Test BofA
    matched = match_company("Trading volume spike noted in BofA equities desk.")
    assert matched is not None
    assert matched.ticker == "BAC"

    # Test Maersk Line
    matched_maersk = match_company("Maersk Line diverts container ships around Cape.")
    assert matched_maersk is not None
    assert matched_maersk.ticker == "MAERSK-B.CO"


def test_match_no_false_positive_on_common_words():
    """Verify that generic words do not spuriously match tickers."""
    text = "A simple meeting about general macroeconomic inflation trends."
    matched = match_company(text)
    assert matched is None


def test_match_all_companies_multiple_entities():
    """Verify that sentences mentioning multiple entities return all of them."""
    text = "ExxonMobil collaborates with Chevron on offshore deepwater gas venture."
    matches = match_all_companies(text)
    matched_tickers = {m.ticker for m in matches}
    assert "XOM" in matched_tickers
    assert "CVX" in matched_tickers
