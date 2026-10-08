"""Unit tests for Pydantic v2 schemas: RawItem, EventClass, and Signal."""
import pytest
from pydantic import ValidationError
from src.schemas import EventClass, RawItem, Signal, SourceType


def test_valid_raw_item():
    """Verify that a compliant raw news/social payload passes validation."""
    item = RawItem(
        item_id="raw_12345",
        source="NewsAPI",
        source_type="news",
        published_at="2026-10-08T12:00:00Z",
        title="JPMorgan announces global infrastructure credit line",
        text="JPMorgan Chase expanded credit financing facilities for wholesale borrowers.",
        url="https://example.com/jpm",
        author="Reuters",
        query_tag="JPM",
        is_synthetic=False,
    )
    assert item.item_id == "raw_12345"
    assert item.source_type == "news"
    assert item.is_synthetic is False


def test_invalid_raw_item_source_type():
    """Verify that an unsupported source type raises ValidationError."""
    with pytest.raises(ValidationError):
        RawItem(
            item_id="raw_invalid",
            source="Unknown",
            source_type="podcast",  # Only 'news' or 'social' allowed
            published_at="2026-10-08T12:00:00Z",
            title="Title",
            text="Text",
        )


def test_valid_signal_model():
    """Verify that a fully-formed Signal instance validates successfully."""
    sig = Signal(
        signal_id="sig_001",
        timestamp="2026-10-08T14:00:00Z",
        source="GDELT",
        source_type="news",
        headline="Red Sea shipping disruption halts container transit",
        entity="A.P. Moller - Maersk",
        ticker="MAERSK-B.CO",
        sector="Shipping",
        country="DNK",
        sentiment_score=-0.85,
        event_class=EventClass.GEOPOLITICAL,
        impact_score=8.7,
        calibrated_move_pct=-6.4,
        confidence=0.92,
        rationale="Severe naval blockade forcing multi-week container voyage rerouting around Africa.",
        model_versions={"nlp": "finbert-v1", "llm": "gemini-1.5"},
    )
    assert sig.sentiment_score == -0.85
    assert sig.impact_score == 8.7
    assert sig.confidence == 0.92
    assert sig.event_class == EventClass.GEOPOLITICAL


@pytest.mark.parametrize(
    "sentiment,impact,confidence,event_class",
    [
        (1.5, 5.0, 0.5, EventClass.MACROECONOMIC),   # sentiment > 1.0
        (-1.5, 5.0, 0.5, EventClass.MACROECONOMIC),  # sentiment < -1.0
        (0.0, 0.5, 0.5, EventClass.MACROECONOMIC),   # impact < 1.0
        (0.0, 10.5, 0.5, EventClass.MACROECONOMIC),  # impact > 10.0
        (0.0, 5.0, -0.1, EventClass.MACROECONOMIC),  # confidence < 0.0
        (0.0, 5.0, 1.2, EventClass.MACROECONOMIC),   # confidence > 1.0
    ],
)
def test_signal_out_of_bounds_raises_error(sentiment, impact, confidence, event_class):
    """Verify that out-of-range numerical metrics trigger validation errors."""
    with pytest.raises(ValidationError):
        Signal(
            signal_id="sig_invalid",
            timestamp="2026-10-08T14:00:00Z",
            source="NewsAPI",
            source_type="news",
            headline="Invalid headline",
            entity="Test Corp",
            sentiment_score=sentiment,
            event_class=event_class,
            impact_score=impact,
            confidence=confidence,
            rationale="Test rationale",
        )


def test_event_class_enumeration():
    """Verify EventClass contains all seven case study event categories."""
    expected = {
        "Geopolitical",
        "Macroeconomic",
        "Credit Event",
        "Merger/Acquisition",
        "Product Launch",
        "Regulatory",
        "Other",
    }
    actual = {e.value for e in EventClass}
    assert expected == actual
