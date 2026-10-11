"""Unit and API tests for portfolio stress testing (Phase 4)."""
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.schemas import Signal
from src.stress.engine import _core, position_shock, run_custom, severity_scale
from src.stress.trigger import evaluate_signals, suppression_reason

TABLE = pd.DataFrame(
    [
        ["shipping_disruption", "shipping", -6, 60, 3.0, 0, "assumed", ""],
        ["oil_price_up", "energy_producer", 8, -15, -0.3, 0, "assumed", ""],
        ["oil_price_up", "airline", -12, 120, 3.5, 0, "assumed", ""],
        ["oil_price_up", "oil", 0, 0, 0.0, 8, "assumed", ""],
        ["credit_downgrade", "us_banking", -6, 70, 1.0, 0, "measured", ""],
    ],
    columns=["theme", "tag", "equity_pct", "spread_bps", "pd_bump_pct", "underlying_pct", "source", "rationale"],
)


def pos(asset_type, tags, mv=10e6, notional=10e6, duration=0.0, delta=0.0, coll=0.0, ticker="X"):
    return pd.Series({
        "position_id": "p1", "asset_type": asset_type, "counterparty": "Acme", "ticker": ticker,
        "sector": "S", "country": "USA", "market_value": mv, "notional": notional,
        "duration": duration, "delta": delta, "collateral_pct": coll, "tag_list": tags,
    })


def sig(sid, ts, theme="shipping_disruption", impact=8.5, conf=0.8, move=-3.0):
    return Signal(signal_id=sid, timestamp=ts, source="Reuters", source_type="news", headline="h", entity="e",
                  themes=[theme], sentiment_score=-0.5, event_class="Geopolitical", impact_score=impact,
                  confidence=conf, rationale="r", calibrated_move_pct=move)


# ---- shock maths (hand-checked) ----
def test_bond_spread_times_duration():
    # -(60bp) * duration 5 * 10M = -300,000
    p, tag, src = position_shock(pos("bond", ["shipping"], duration=5.0), "shipping_disruption", 1.0, TABLE)
    assert p == pytest.approx(-300_000.0)
    assert tag == "shipping" and src == "assumed"


def test_loan_expected_loss_with_collateral():
    # -(3.0% PD bump * 0.45 LGD * 10M * (1 - 0.2)) = -108,000
    p, _, _ = position_shock(pos("loan", ["shipping"], coll=0.2), "shipping_disruption", 1.0, TABLE)
    assert p == pytest.approx(-108_000.0)


def test_derivative_mtm_delta_notional():
    # delta -0.6 * 100M * 8% = -4.8M (bank short oil)
    p, _, _ = position_shock(pos("derivative", ["oil"], mv=2e6, notional=100e6, delta=-0.6), "oil_price_up", 1.0, TABLE)
    assert p == pytest.approx(-4_800_000.0)


def test_unmatched_tags_zero_change():
    p, tag, src = position_shock(pos("equity", ["semiconductor"]), "oil_price_up", 1.0, TABLE)
    assert (p, tag, src) == (0.0, None, None)


def test_theme_direction_oil():
    prod, _, _ = position_shock(pos("equity", ["energy_producer"]), "oil_price_up", 1.0, TABLE)
    air, _, _ = position_shock(pos("equity", ["airline"]), "oil_price_up", 1.0, TABLE)
    assert prod > 0 > air


def test_floor_no_loss_beyond_exposure():
    pf = pd.DataFrame([pos("derivative", ["oil"], mv=2e6, notional=100e6, delta=-1.0)])
    res = _core([("oil_price_up", 2.0)], -5.0, pf, TABLE, "t")
    # raw MTM -16M, capped at max(mv, 10% notional) = 10M
    assert res.pnl_abs == pytest.approx(-10_000_000.0)


def test_combined_distinct_themes_sum():
    pf = pd.DataFrame([pos("bond", ["shipping", "airline"], duration=5.0)])
    one = _core([("shipping_disruption", 1.0)], -3, pf, TABLE, "a").pnl_abs
    two = _core([("oil_price_up", 1.0)], -3, pf, TABLE, "b").pnl_abs
    both = _core([("shipping_disruption", 1.0), ("oil_price_up", 1.0)], -3, pf, TABLE, "c").pnl_abs
    assert both == pytest.approx(one + two)


def test_severity_scaling_monotone():
    lo, hi = run_custom("oil_price_up", 3.0), run_custom("oil_price_up", 9.0)
    assert severity_scale(9.0, -5.0) >= severity_scale(3.0, -2.0)
    assert abs(hi.pnl_abs) >= abs(lo.pnl_abs)


def test_naive_differs_from_exposure_aware():
    res = run_custom("oil_price_up", 8.0)
    assert res.naive_pnl_pct < 0
    assert res.pnl_pct != pytest.approx(res.naive_pnl_pct)
    assert 0 < res.positions_hit < len(res.positions)


def test_unmapped_theme_leaves_book_unchanged():
    res = run_custom("merger_activity", 8.0)
    assert res.pnl_abs == 0 and res.positions_hit == 0


# ---- trigger logic ----
def test_low_confidence_never_triggers():
    s = sig("rumor", "2026-10-05T00:00:00Z", impact=9.5, conf=0.3)
    assert "confidence" in suppression_reason(s)
    scenarios, suppressed = evaluate_signals([s])
    assert scenarios == [] and suppressed[0].signal_id == "rumor"


def test_debounce_merges_same_theme_within_48h():
    a = sig("a", "2026-10-06T10:00:00Z", impact=8.0)
    b = sig("b", "2026-10-06T12:00:00Z", impact=9.0)
    c = sig("c", "2026-10-10T12:00:00Z", impact=8.0)  # > 48h later -> new scenario
    scenarios, _ = evaluate_signals([a, b, c])
    assert len(scenarios) == 2
    assert scenarios[0].lead.signal_id == "b" and scenarios[0].corroborating_ids == ["a"]


# ---- API ----
client = TestClient(app)


def test_api_portfolio_and_shock_table():
    r = client.get("/portfolio").json()
    assert r["synthetic"] is True and r["n_positions"] >= 45
    assert 0.8e9 < r["total_market_value"] < 2.5e9
    t = client.get("/shock-table").json()
    assert {row["source"] for row in t} <= {"measured", "assumed"}


def test_api_custom_stress_and_calibration():
    r = client.post("/stress/custom", json={"theme": "oil_price_up", "severity": 8})
    assert r.status_code == 200 and r.json()["pnl_pct"] != 0
    assert client.post("/stress/custom", json={"theme": "bogus", "severity": 8}).status_code == 422
    c = client.get("/calibration")
    assert c.status_code == 200 and "buckets" in c.json() and c.json()["curve"]


def test_api_stress_by_signal_and_404_reason():
    sigs = [json.loads(l) for l in open("data/processed/signals.jsonl")]
    eligible = next(s for s in sigs if s["impact_score"] > 7 and s["confidence"] >= 0.6 and s["themes"])
    assert client.get(f"/stress/{eligible['signal_id']}").status_code == 200
    calm = min(sigs, key=lambda s: s["impact_score"])
    r = client.get(f"/stress/{calm['signal_id']}")
    assert r.status_code == 404 and "reason" in r.json()["detail"]


def test_api_replay_stream_emits_all_events_in_order():
    with client.stream("GET", "/replay/stream?speed=1000") as resp:
        lines = [l for l in resp.iter_lines() if l.startswith("data:")]
    events = [json.loads(l[5:]) for l in lines]
    signal_events = [e for e in events if e["type"] == "signal"]
    assert len(signal_events) == 14
    stamps = [e["signal"]["timestamp"] for e in signal_events]
    assert stamps == sorted(stamps)
    kinds = {e["type"] for e in events}
    assert {"stress_result", "suppressed"} <= kinds and events[-1]["type"] == "end"
