"""Unit tests for FastAPI REST endpoints using TestClient."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.api.main import app
from src.schemas import EventClass, Signal

client = TestClient(app)

MOCK_SIGNALS = [
    Signal(
        signal_id="sig_test_01",
        timestamp="2026-10-07T12:00:00Z",
        source="Reuters",
        source_type="news",
        headline="Maersk diverts fleet from Red Sea",
        entity="A.P. Moller - Maersk",
        ticker="MAERSK-B.CO",
        sector="Shipping",
        country="DNK",
        sentiment_score=-0.85,
        event_class=EventClass.GEOPOLITICAL,
        impact_score=8.8,
        confidence=0.88,
        trigger_eligible=True,
        rationale="Severe naval blockade.",
    ),
    Signal(
        signal_id="sig_test_02",
        timestamp="2026-10-07T14:00:00Z",
        source="Social/X",
        source_type="social",
        headline="Rumor about Bank of America repo",
        entity="Bank of America",
        ticker="BAC",
        sector="Banking",
        country="USA",
        sentiment_score=-0.40,
        event_class=EventClass.CREDIT_EVENT,
        impact_score=4.0,
        confidence=0.32,
        trigger_eligible=False,
        rationale="Unverified rumor.",
    ),
    Signal(
        signal_id="sig_test_03",
        timestamp="2026-10-07T16:00:00Z",
        source="Bloomberg",
        source_type="news",
        headline="Citigroup sovereign debt moratorium negative credit watch",
        entity="Citigroup",
        ticker="C",
        sector="Banking",
        country="USA",
        sentiment_score=-0.80,
        event_class=EventClass.CREDIT_EVENT,
        impact_score=8.2,
        confidence=0.85,
        trigger_eligible=True,
        rationale="Distressed sovereign debt.",
    ),
]


def test_api_health_endpoint():
    """Verify /health returns 200 with service status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


@patch("src.api.main.read_all_signals", return_value=MOCK_SIGNALS)
def test_api_get_signals_all(mock_read):
    """Verify /signals returns all items when unfiltered."""
    response = client.get("/signals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@patch("src.api.main.read_all_signals", return_value=MOCK_SIGNALS)
def test_api_get_signals_filters(mock_read):
    """Verify filtering by ticker, event_class, min_impact, and min_confidence."""
    # Filter by ticker
    res_ticker = client.get("/signals?ticker=BAC")
    assert res_ticker.status_code == 200
    data_ticker = res_ticker.json()
    assert len(data_ticker) == 1
    assert data_ticker[0]["ticker"] == "BAC"

    # Filter by event_class
    res_class = client.get("/signals?event_class=Geopolitical")
    assert res_class.status_code == 200
    data_class = res_class.json()
    assert len(data_class) == 1
    assert data_class[0]["event_class"] == "Geopolitical"

    # Filter by min_impact
    res_impact = client.get("/signals?min_impact=8.0")
    assert res_impact.status_code == 200
    assert len(res_impact.json()) == 2

    # Filter by min_confidence
    res_conf = client.get("/signals?min_confidence=0.80")
    assert res_conf.status_code == 200
    assert len(res_conf.json()) == 2


@patch("src.api.main.read_all_signals", return_value=MOCK_SIGNALS)
def test_api_get_signal_by_id(mock_read):
    """Verify /signals/{id} returns single signal or 404."""
    res_found = client.get("/signals/sig_test_01")
    assert res_found.status_code == 200
    assert res_found.json()["signal_id"] == "sig_test_01"

    res_missing = client.get("/signals/sig_nonexistent")
    assert res_missing.status_code == 404


@patch("src.api.main.read_all_signals", return_value=MOCK_SIGNALS)
def test_api_get_triggers(mock_read):
    """Verify /signals/triggers returns only trigger_eligible signals."""
    response = client.get("/signals/triggers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for s in data:
        assert s["trigger_eligible"] is True


def test_api_post_analyze():
    """Verify POST /analyze produces a valid structured Signal for arbitrary input."""
    with patch("src.api.main.get_engine") as mock_get_engine:
        mock_get_engine.return_value.process_items.return_value = [MOCK_SIGNALS[0].model_copy(deep=True)]
        payload = {
            "text": "Missile attack in Red Sea damages commercial freighter; Maersk reroutes shipping fleets.",
            "source": "Interactive Test",
            "source_type": "news",
        }
        response = client.post("/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "signal_id" in data
        assert data["event_class"] == "Geopolitical"
        assert data["impact_score"] >= 7.0
        assert data["sentiment_score"] < 0.0
