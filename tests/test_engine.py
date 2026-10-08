"""Unit tests for Risk Engine components: LLM parsing, ticker grounding, confidence monotonicity, and trigger eligibility."""
import json
import pytest
from unittest.mock import MagicMock

from src.schemas import EventClass, RawItem, Signal
from src.engine.extract import ExtractionResult, SignalExtractor
from src.engine.confidence import ConfidenceCalculator
from src.llm.client import LLMClient


def test_llm_json_repair_and_code_fence_stripping():
    """Verify that LLM client correctly parses raw text wrapped in markdown fences."""
    raw_response = """```json
    {
        "entity": "JPMorgan Chase",
        "ticker": "JPM",
        "sector": "Banking",
        "country": "USA",
        "event_class": "Credit Event",
        "sentiment_score": -0.45,
        "impact_score": 6.5,
        "claim_certainty": "confirmed",
        "rationale": "Credit spread widening across debt facilities."
    }
    ```"""
    cleaned = LLMClient._clean_json_str(raw_response)
    data = json.loads(cleaned)
    assert data["ticker"] == "JPM"
    assert data["impact_score"] == 6.5


def test_ticker_grounding_rejects_unlisted_ticker():
    """Verify that tickers outside the 20 counterparty universe are nullified."""
    mock_llm = MagicMock()
    # Mock LLM returns a hallucinated ticker like 'XYZ_FAKE'
    mock_llm.complete_json.return_value = {
        "entity": "Fictional Firm",
        "ticker": "XYZ_FAKE",
        "sector": "Technology",
        "country": "USA",
        "event_class": "Other",
        "sentiment_score": 0.1,
        "impact_score": 3.0,
        "claim_certainty": "confirmed",
        "rationale": "Non-existent entity.",
    }
    mock_llm.offline_mode = True

    extractor = SignalExtractor(llm_client=mock_llm)
    result = extractor.extract(headline="Fictional firm reports earnings")
    assert result.ticker is None  # Must be nullified because XYZ_FAKE is not in universe


def test_confidence_monotonicity_with_corroboration():
    """Verify that additional cross-source corroborations monotonically increase confidence."""
    calc = ConfidenceCalculator()

    target_item = RawItem(
        item_id="target_01",
        source="Reuters",
        source_type="news",
        published_at="2026-10-07T12:00:00Z",
        title="Maersk halts Red Sea transit",
        text="Maersk container ship avoids Bab el-Mandeb strait.",
    )
    target_ext = ExtractionResult(
        entity="A.P. Moller - Maersk",
        ticker="MAERSK-B.CO",
        sector="Shipping",
        country="DNK",
        event_class=EventClass.GEOPOLITICAL,
        sentiment_score=-0.8,
        impact_score=8.5,
        claim_certainty="confirmed",
        rationale="Severe naval risk.",
    )

    # 0 corroborations
    c_0, _, _ = calc.calculate(
        raw_item=target_item,
        extraction=target_ext,
        finbert_sentiment=-0.75,
        batch_items=[target_item],
        batch_extractions=[target_ext],
    )

    # 1 corroboration from Bloomberg
    corrob_item_1 = RawItem(
        item_id="corrob_01",
        source="Bloomberg",
        source_type="news",
        published_at="2026-10-07T14:00:00Z",
        title="Baltic index confirms Red Sea traffic plunge",
        text="Maersk diversions around Cape confirmed.",
    )
    corrob_ext_1 = ExtractionResult(
        entity="A.P. Moller - Maersk",
        ticker="MAERSK-B.CO",
        sector="Shipping",
        country="DNK",
        event_class=EventClass.GEOPOLITICAL,
        sentiment_score=-0.8,
        impact_score=8.0,
        claim_certainty="confirmed",
        rationale="Corroborating traffic fall.",
    )

    c_1, _, _ = calc.calculate(
        raw_item=target_item,
        extraction=target_ext,
        finbert_sentiment=-0.75,
        batch_items=[target_item, corrob_item_1],
        batch_extractions=[target_ext, corrob_ext_1],
    )

    # 2 corroborations (add Financial Times)
    corrob_item_2 = RawItem(
        item_id="corrob_02",
        source="Financial Times",
        source_type="news",
        published_at="2026-10-07T16:00:00Z",
        title="FT: Maersk freight rerouting confirmed",
        text="Maersk fleet bypasses Suez.",
    )
    corrob_ext_2 = ExtractionResult(
        entity="A.P. Moller - Maersk",
        ticker="MAERSK-B.CO",
        sector="Shipping",
        country="DNK",
        event_class=EventClass.GEOPOLITICAL,
        sentiment_score=-0.8,
        impact_score=8.5,
        claim_certainty="confirmed",
        rationale="Third source confirmation.",
    )

    c_2, _, _ = calc.calculate(
        raw_item=target_item,
        extraction=target_ext,
        finbert_sentiment=-0.75,
        batch_items=[target_item, corrob_item_1, corrob_item_2],
        batch_extractions=[target_ext, corrob_ext_1, corrob_ext_2],
    )

    assert c_0 < c_1 <= c_2


def test_rumor_has_strictly_lower_confidence_than_confirmed():
    """Verify that unverified rumors have strictly lower confidence and are capped."""
    calc = ConfidenceCalculator()

    item = RawItem(
        item_id="post_01",
        source="Social/X",
        source_type="social",
        published_at="2026-10-07T12:00:00Z",
        title="Rumor: Bank of America repo liquidity check",
        text="Wild unconfirmed rumors that BAC desk delayed repo settlement.",
    )

    ext_rumor = ExtractionResult(
        entity="Bank of America",
        ticker="BAC",
        sector="Banking",
        country="USA",
        event_class=EventClass.CREDIT_EVENT,
        sentiment_score=-0.5,
        impact_score=4.0,
        claim_certainty="rumor",
        rationale="Unsubstantiated claim.",
    )

    ext_confirmed = ExtractionResult(
        entity="Bank of America",
        ticker="BAC",
        sector="Banking",
        country="USA",
        event_class=EventClass.CREDIT_EVENT,
        sentiment_score=-0.5,
        impact_score=7.5,
        claim_certainty="confirmed",
        rationale="Official regulatory disclosure.",
    )

    conf_rumor, _, trig_rumor = calc.calculate(item, ext_rumor, -0.5, [item], [ext_rumor])
    conf_confirmed, _, trig_conf = calc.calculate(item, ext_confirmed, -0.5, [item], [ext_confirmed])

    assert conf_rumor < conf_confirmed
    assert conf_rumor <= 0.42
    assert trig_rumor is False


def test_trigger_eligibility_thresholds():
    """Verify trigger_eligible boolean requires both impact > 7.0 AND confidence >= 0.60."""
    calc = ConfidenceCalculator()

    item = RawItem(
        item_id="sig_test",
        source="Reuters",
        source_type="news",
        published_at="2026-10-07T12:00:00Z",
        title="High impact confirmed event",
        text="Major credit default confirmed by international rating agencies.",
    )

    # High impact (8.5), high confidence (confirmed news) -> True
    ext_high = ExtractionResult(
        entity="Citigroup",
        ticker="C",
        sector="Banking",
        country="USA",
        event_class=EventClass.CREDIT_EVENT,
        sentiment_score=-0.8,
        impact_score=8.5,
        claim_certainty="confirmed",
        rationale="Confirmed moratorium.",
    )
    _, _, trig_high = calc.calculate(item, ext_high, -0.8, [item], [ext_high])
    assert trig_high is True

    # High impact (8.5), but low confidence (rumor) -> False
    ext_rumor_high = ExtractionResult(
        entity="Citigroup",
        ticker="C",
        sector="Banking",
        country="USA",
        event_class=EventClass.CREDIT_EVENT,
        sentiment_score=-0.8,
        impact_score=8.5,
        claim_certainty="rumor",
        rationale="Rumored moratorium.",
    )
    _, _, trig_rumor_high = calc.calculate(item, ext_rumor_high, -0.8, [item], [ext_rumor_high])
    assert trig_rumor_high is False

    # Low impact (3.0), high confidence -> False
    ext_low = ExtractionResult(
        entity="Citigroup",
        ticker="C",
        sector="Banking",
        country="USA",
        event_class=EventClass.OTHER,
        sentiment_score=0.2,
        impact_score=3.0,
        claim_certainty="confirmed",
        rationale="Routine note.",
    )
    _, _, trig_low = calc.calculate(item, ext_low, 0.2, [item], [ext_low])
    assert trig_low is False
