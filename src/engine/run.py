"""Engine runner: orchestrates extraction, FinBERT cross-check, confidence scoring, and signal emission."""
import argparse
import json
from pathlib import Path
from typing import List, Optional
import numpy as np

from src.config import (
    PROCESSED_ITEMS_FILE,
    REPLAY_EVENTS_FILE,
    SIGNALS_PROCESSED_FILE,
    get_logger,
)
from src.schemas import RawItem, Signal
from src.llm.client import LLMClient
from src.engine.extract import SignalExtractor, ExtractionResult
from src.engine.finbert import FinBertEngine
from src.engine.confidence import ConfidenceCalculator

logger = get_logger("engine.run")


class RiskEngine:
    """End-to-end Risk Engine turning unstructured RawItems into validated institutional Signals."""

    def __init__(self, llm_client: Optional[LLMClient] = None, force_lexicon_finbert: bool = False):
        self.extractor = SignalExtractor(llm_client=llm_client)
        self.finbert = FinBertEngine(force_lexicon=force_lexicon_finbert)
        self.confidence_calc = ConfidenceCalculator()

    def process_items(self, raw_items: List[RawItem]) -> List[Signal]:
        """Process batch of RawItems through extraction, cross-check, corroboration, and confidence."""
        if not raw_items:
            logger.warning("No raw items provided to RiskEngine.")
            return []

        logger.info("Starting Risk Engine processing on %d raw items...", len(raw_items))

        # 1. First-pass extraction for all items
        extractions: List[ExtractionResult] = []
        for i, item in enumerate(raw_items, 1):
            logger.debug("[%d/%d] Extracting: %s", i, len(raw_items), item.title[:50])
            ext = self.extractor.extract(headline=item.title, body=item.text)
            extractions.append(ext)

        # 2. FinBERT sentiment cross-check
        texts_to_check = [f"{it.title}. {it.text}" for it in raw_items]
        finbert_scores = self.finbert.score_batch(texts_to_check)

        # 3. Batch engagement median (for social hype penalty calculation)
        engagements = [
            (it.engagement or {}).get("likes", 0) + (it.engagement or {}).get("retweets", 0)
            for it in raw_items
            if it.source_type == "social"
        ]
        median_eng = float(np.median(engagements)) if engagements else 50.0

        # 4. Corroboration and multi-factor confidence computation
        signals: List[Signal] = []
        for item, ext, (fb_sent, fb_model) in zip(raw_items, extractions, finbert_scores):
            confidence, parts, trigger_eligible = self.confidence_calc.calculate(
                raw_item=item,
                extraction=ext,
                finbert_sentiment=fb_sent,
                batch_items=raw_items,
                batch_extractions=extractions,
                batch_engagement_median=median_eng,
            )

            signal_id = f"sig_{item.item_id}"
            model_versions = {
                "extractor": ext.model_dump().get("model_version", "gemini-3.8-flash"),
                "finbert": fb_model,
                "confidence_engine": "v1.0",
            }

            sig = Signal(
                signal_id=signal_id,
                timestamp=item.published_at,
                source=item.source,
                source_type=item.source_type,
                headline=item.title,
                entity=ext.entity,
                ticker=ext.ticker,
                sector=ext.sector,
                country=ext.country,
                sentiment_score=ext.sentiment_score,
                event_class=ext.event_class,
                impact_score=ext.impact_score,
                calibrated_move_pct=None,  # Reserved for Phase 3 calibration
                confidence=confidence,
                rationale=ext.rationale,
                trigger_eligible=trigger_eligible,
                finbert_sentiment=fb_sent,
                confidence_parts=parts,
                model_versions=model_versions,
            )
            signals.append(sig)

        logger.info("Successfully generated %d validated signals.", len(signals))
        return signals


def load_raw_items_from_jsonl(filepath: Path, limit: int = 150) -> List[RawItem]:
    """Read RawItems from JSONL file."""
    if not filepath.exists():
        logger.error("Input file not found: %s", filepath)
        return []

    items: List[RawItem] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(RawItem.model_validate_json(line))
                if len(items) >= limit:
                    break
            except Exception as e:
                logger.warning("Skipping malformed raw item line: %s", e)
    return items


def write_signals_to_jsonl(signals: List[Signal], filepath: Path):
    """Persist generated signals to output JSONL file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for s in signals:
            f.write(s.model_dump_json() + "\n")
    logger.info("Wrote %d signals to %s", len(signals), filepath)


def print_summary_table(signals: List[Signal]):
    """Print an executive summary table of signals."""
    print("\n" + "=" * 115)
    print(f"{'ID':<14} | {'ENTITY / TICKER':<24} | {'CLASS':<18} | {'SENT':<6} | {'IMPACT':<6} | {'CONF':<6} | {'TRIGGER':<7} | {'HEADLINE':<25}")
    print("=" * 115)
    for s in signals:
        ent_str = f"{s.entity[:15]} ({s.ticker or '-'})"
        trig_str = "YES" if s.trigger_eligible else "NO"
        print(f"{s.signal_id:<14} | {ent_str:<24} | {s.event_class.value:<18} | {s.sentiment_score:>+5.2f} | {s.impact_score:>5.1f} | {s.confidence:>5.2f} | {trig_str:<7} | {s.headline[:25]}")
    print("=" * 115)

    trigger_count = sum(1 for s in signals if s.trigger_eligible)
    print(f"\nTotal Signals: {len(signals)} | Trigger Eligible: {trigger_count} | Trigger Suppressed: {len(signals) - trigger_count}\n")


def main():
    parser = argparse.ArgumentParser(description="Run Signal-to-Shock Risk Engine")
    parser.add_argument("--input", choices=["processed", "replay"], default="replay", help="Input dataset source")
    parser.add_argument("--limit", type=int, default=150, help="Maximum items to process")
    parser.add_argument("--out", type=str, default=str(SIGNALS_PROCESSED_FILE), help="Output JSONL path")
    parser.add_argument("--offline", action="store_true", help="Force offline rules fallback")

    args = parser.parse_args()

    input_path = REPLAY_EVENTS_FILE if args.input == "replay" else PROCESSED_ITEMS_FILE
    out_path = Path(args.out)

    llm_client = LLMClient(offline_mode=args.offline) if args.offline else None
    engine = RiskEngine(llm_client=llm_client)

    raw_items = load_raw_items_from_jsonl(input_path, limit=args.limit)
    signals = engine.process_items(raw_items)
    write_signals_to_jsonl(signals, out_path)
    print_summary_table(signals)


if __name__ == "__main__":
    main()
