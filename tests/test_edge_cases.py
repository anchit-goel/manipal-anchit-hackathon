"""Edge-case tests for the Signal-to-Shock risk system.

Covers:
1. /analyze text > 20,000 chars safely truncated.
2. /analyze empty or whitespace text -> 422.
3. /stress/custom invalid theme or 'none' -> 422.
4. /stress/custom out-of-range severity -> 422.
5. Net-positive / multi-position PnL transmission for themes.
6. /stress/signal on an unverified rumor returns 404 with suppression reason.
7. Signals with themes=['none'] or empty themes handled gracefully.
8. Deterministic portfolio regeneration.
9. Empty or missing signals file handled safely.
"""
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from src.api.main import app, read_all_signals
from src.schemas import EventClass, Signal
from src.stress.engine import run_stress, run_custom, load_portfolio
from src.portfolio.build import build_portfolio

client = TestClient(app)


def test_analyze_empty_text_returns_422():
    resp = client.post("/analyze", json={"text": "   "})
    assert resp.status_code == 422
    assert "blank" in resp.json()["detail"]


def test_analyze_text_truncation_over_20k():
    long_text = "OPEC announces supply cuts across Middle East crude facilities. " * 400
    assert len(long_text) > 20_000
    resp = client.post("/analyze", json={"text": long_text})
    assert resp.status_code == 200
    data = resp.json()
    assert "signal_id" in data
    assert data["model_versions"].get("input_note") == "text truncated to 20000 characters"


def test_custom_stress_invalid_theme_returns_422():
    resp = client.post("/stress/custom", json={"theme": "crypto_collapse_nonexistent", "severity": 5.0})
    assert resp.status_code == 422
    assert "not valid" in resp.json()["detail"]


def test_custom_stress_theme_none_returns_422():
    resp = client.post("/stress/custom", json={"theme": "none", "severity": 5.0})
    assert resp.status_code == 422


def test_custom_stress_invalid_severity_returns_422():
    resp = client.post("/stress/custom", json={"theme": "oil_price_up", "severity": 15.0})
    assert resp.status_code == 422
    resp_neg = client.post("/stress/custom", json={"theme": "oil_price_up", "severity": -2.0})
    assert resp_neg.status_code == 422


def test_custom_stress_oil_price_up_runs_successfully():
    result = run_custom("oil_price_up", 7.0)
    assert "oil_price_up" in result.themes
    assert result.severity_scale > 0
    assert result.total_before > 0
    # Energy positions (XOM, CVX) should have positive or zero impact
    xom_impact = next((p for p in result.positions if "XOM" in p.counterparty or p.position_id == "pos_006"), None)
    if xom_impact:
        assert xom_impact.pnl >= 0


def test_stress_signal_suppressed_returns_404():
    unverified_sig = {
        "signal_id": "test_rumor_unverified",
        "timestamp": "2026-10-08T00:00:00Z",
        "source": "Social/X",
        "source_type": "social",
        "headline": "Anonymous post alleges liquidity issue",
        "entity": "Citigroup",
        "ticker": "C",
        "sector": "Banking",
        "country": "USA",
        "sentiment_score": -0.4,
        "event_class": "Credit Event",
        "impact_score": 4.0,
        "confidence": 0.35,  # Below social threshold of 0.70
        "trigger_eligible": False,
        "rationale": "Anonymous social claim without evidence.",
        "themes": ["credit_default"],
    }
    resp = client.post("/stress/signal", json=unverified_sig)
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["eligible"] is False
    assert "confidence" in detail["reason"].lower() or "suppress" in detail["reason"].lower()


def test_stress_signal_with_no_themes_returns_empty_shocks():
    blank_theme_sig = Signal(
        signal_id="test_blank_theme",
        timestamp="2026-10-08T00:00:00Z",
        source="Reuters",
        source_type="news",
        headline="Routine boardroom reshuffle announced",
        entity="Apple",
        ticker="AAPL",
        sector="Technology",
        country="USA",
        sentiment_score=-0.1,
        event_class=EventClass.OTHER,
        impact_score=6.0,
        confidence=0.85,
        trigger_eligible=True,
        rationale="Routine management changes.",
        themes=["none"],
    )
    result = run_stress(blank_theme_sig)
    assert result.pnl_pct == 0.0
    assert result.pnl_abs == 0.0


def test_deterministic_portfolio_generation():
    df1 = build_portfolio()
    df2 = build_portfolio()
    assert len(df1) == 50
    assert len(df2) == 50
    assert float(df1["market_value"].sum()) == pytest.approx(float(df2["market_value"].sum()))
    assert list(df1["ticker"]) == list(df2["ticker"])


def test_empty_signals_file_handled_safely(monkeypatch, tmp_path):
    empty_file = tmp_path / "empty_signals.jsonl"
    empty_file.write_text("")
    monkeypatch.setattr("src.api.main.SIGNALS_PROCESSED_FILE", empty_file)
    signals = read_all_signals()
    assert signals == []
