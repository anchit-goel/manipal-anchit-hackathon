"""Multi-factor confidence scoring engine with corroboration and noise suppression."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from src.config import (
    CONFIDENCE_WEIGHTS,
    SOURCE_RELIABILITY_TABLE,
    TRIGGER_CONFIDENCE_THRESHOLD,
    TRIGGER_IMPACT_THRESHOLD,
    get_logger,
)
from src.schemas import EventClass, RawItem
from src.engine.extract import ExtractionResult

logger = get_logger("engine.confidence")


def parse_iso_dt(ts_str: str) -> Optional[datetime]:
    """Parse ISO8601 string to timezone-naive UTC datetime for arithmetic."""
    try:
        clean = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return dt.replace(tzinfo=None)
    except Exception:
        return None


class ConfidenceCalculator:
    """Calculates granular, explainable confidence scores for extracted risk signals."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or CONFIDENCE_WEIGHTS

    def get_source_reliability(self, source: str, source_type: str) -> float:
        """Lookup source reliability prior from config table."""
        s_lower = source.lower().strip()
        for k, v in SOURCE_RELIABILITY_TABLE.items():
            if k in s_lower:
                return v

        if source_type == "news":
            return SOURCE_RELIABILITY_TABLE.get("default_news", 0.75)
        return SOURCE_RELIABILITY_TABLE.get("default_social", 0.35)

    def calculate_corroboration_score(
        self,
        target_item: RawItem,
        target_extraction: ExtractionResult,
        batch_items: List[RawItem],
        batch_extractions: List[ExtractionResult],
    ) -> float:
        """Score cross-source corroboration within +/- 48h window."""
        t_dt = parse_iso_dt(target_item.published_at)
        target_entity = (target_extraction.entity or "").lower()
        target_ticker = target_extraction.ticker
        target_class = target_extraction.event_class

        distinct_sources = set()
        has_news_corroborator = False

        for other_item, other_ext in zip(batch_items, batch_extractions):
            if other_item.item_id == target_item.item_id:
                continue

            # Check time window (+/- 48 hours)
            o_dt = parse_iso_dt(other_item.published_at)
            if t_dt and o_dt:
                hours_diff = abs((t_dt - o_dt).total_seconds()) / 3600.0
                if hours_diff > 48.0:
                    continue

            # Check entity match (ticker or company name substring)
            o_entity = (other_ext.entity or "").lower()
            entity_match = (
                (target_ticker and other_ext.ticker == target_ticker)
                or (target_entity and target_entity in o_entity)
                or (o_entity and o_entity in target_entity)
            )

            # Check event class alignment
            class_match = (other_ext.event_class == target_class)

            if entity_match and class_match and other_item.source != target_item.source:
                distinct_sources.add(other_item.source)
                if other_item.source_type == "news":
                    has_news_corroborator = True

        corrob_count = len(distinct_sources)

        # Base scoring with diminishing returns
        if corrob_count == 0:
            base_score = 0.25 if target_item.source_type == "news" else 0.10
        elif corrob_count == 1:
            base_score = 0.60
        elif corrob_count == 2:
            base_score = 0.85
        else:
            base_score = 1.00

        # Social items require news corroboration to achieve high confidence
        if target_item.source_type == "social" and not has_news_corroborator:
            base_score = min(base_score, 0.40)

        return round(base_score, 2)

    def calculate(
        self,
        raw_item: RawItem,
        extraction: ExtractionResult,
        finbert_sentiment: float,
        batch_items: List[RawItem],
        batch_extractions: List[ExtractionResult],
        batch_engagement_median: float = 100.0,
    ) -> tuple[float, Dict[str, float], bool]:
        """Compute final confidence in [0, 1], its parts, and trigger eligibility."""
        # 1. Source Reliability Prior
        source_rel = self.get_source_reliability(raw_item.source, raw_item.source_type)

        # 2. Cross-Source Corroboration
        corroboration = self.calculate_corroboration_score(
            raw_item, extraction, batch_items, batch_extractions
        )

        # 3. Sentiment Agreement (LLM vs FinBERT)
        diff_sent = abs(extraction.sentiment_score - finbert_sentiment)
        sentiment_agreement = round(max(0.0, 1.0 - (diff_sent / 2.0)), 2)

        # 4. Self-Consistency (Pass 1 vs Pass 2 impact disagreement)
        disagreement = extraction.impact_disagreement or 0.0
        self_consistency = round(max(0.0, 1.0 - (disagreement / 5.0)), 2)

        # 5. Claim Certainty Modifier
        certainty_map = {"confirmed": 1.0, "reported": 0.80, "rumor": 0.45}
        certainty_mod = certainty_map.get(extraction.claim_certainty, 0.80)

        # Weighted blend
        raw_confidence = (
            self.weights["source_reliability"] * source_rel
            + self.weights["corroboration"] * corroboration
            + self.weights["sentiment_agreement"] * sentiment_agreement
            + self.weights["self_consistency"] * self_consistency
            + self.weights["claim_certainty"] * certainty_mod
        )

        # 6. Social Hype Penalty
        # If social post has extreme engagement without corroboration, down-weight
        engagement = raw_item.engagement or {}
        tot_eng = engagement.get("likes", 0) + engagement.get("retweets", 0)
        is_hyped = (
            raw_item.source_type == "social"
            and tot_eng > (batch_engagement_median * 3.0)
            and corroboration <= 0.40
        )
        if is_hyped:
            raw_confidence = raw_confidence * 0.75

        # If it is explicitly an unverified rumor, enforce an upper bound
        if extraction.claim_certainty == "rumor":
            raw_confidence = min(raw_confidence, 0.42)

        final_confidence = round(float(np.clip(raw_confidence, 0.0, 1.0)), 2)

        parts = {
            "source_reliability": round(source_rel, 2),
            "corroboration": round(corroboration, 2),
            "sentiment_agreement": round(sentiment_agreement, 2),
            "self_consistency": round(self_consistency, 2),
            "claim_certainty": round(certainty_mod, 2),
            "hype_penalty_applied": 1.0 if is_hyped else 0.0,
        }

        # Trigger eligibility check: impact > 7.0 AND confidence >= 0.60
        trigger_eligible = (
            extraction.impact_score > TRIGGER_IMPACT_THRESHOLD
            and final_confidence >= TRIGGER_CONFIDENCE_THRESHOLD
        )

        return final_confidence, parts, trigger_eligible
