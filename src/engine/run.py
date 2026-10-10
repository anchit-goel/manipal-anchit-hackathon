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


from src.engine.calibrate import calibrate_signals_batch


class RiskEngine:
    """End-to-end Risk Engine turning unstructured RawItems into validated institutional Signals."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        force_lexicon_finbert: bool = False,
        require_llm: bool = False,
    ):
        if llm_client is None:
            llm_client = LLMClient(require_llm=require_llm)
        elif require_llm:
            llm_client.require_llm = True

        self.extractor = SignalExtractor(llm_client=llm_client)
        self.finbert = FinBertEngine(force_lexicon=force_lexicon_finbert)
        self.confidence_calc = ConfidenceCalculator()

    def process_items(self, raw_items: List[RawItem]) -> List[Signal]:
        """Process batch of RawItems through extraction, cross-check, corroboration, confidence, and calibration."""
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
            ext_version = ext.model_dump().get("model_version") or getattr(self.extractor.llm, "model_name", "rules-fallback")
            model_versions = {
                "extractor": ext_version,
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
                themes=ext.themes,
                sentiment_score=ext.sentiment_score,
                event_class=ext.event_class,
                impact_score=ext.impact_score,
                calibrated_move_pct=None,
                confidence=confidence,
                rationale=ext.rationale,
                trigger_eligible=trigger_eligible,
                finbert_sentiment=fb_sent,
                confidence_parts=parts,
                model_versions=model_versions,
            )
            signals.append(sig)

        # 5. Apply empirical market calibration
        calibrate_signals_batch(signals)

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
    """Print an executive summary table of signals with calibrated moves."""
    print("\n" + "=" * 145)
    print(f"{'ID':<12} | {'ENTITY / TICKER':<22} | {'CLASS':<14} | {'SENT':<6} | {'IMPACT':<6} | {'CALIB MOVE':<11} | {'CONF':<6} | {'TRIG':<5} | {'EXTRACTOR':<16} | {'HEADLINE':<25}")
    print("=" * 145)
    for s in signals:
        ent_str = f"{s.entity[:13]} ({s.ticker or '-'})"
        trig_str = "YES" if s.trigger_eligible else "NO"
        cal_str = f"{s.calibrated_move_pct:>+6.2f}%" if s.calibrated_move_pct is not None else "  N/A "
        ext_str = s.model_versions.get("extractor", "-")[:16]
        print(f"{s.signal_id:<12} | {ent_str:<22} | {s.event_class.value:<14} | {s.sentiment_score:>+5.2f} | {s.impact_score:>5.1f} | {cal_str:<11} | {s.confidence:>5.2f} | {trig_str:<5} | {ext_str:<16} | {s.headline[:25]}")
    print("=" * 145)

    trigger_count = sum(1 for s in signals if s.trigger_eligible)
    print(f"\nTotal Signals: {len(signals)} | Trigger Eligible: {trigger_count} | Trigger Suppressed: {len(signals) - trigger_count}\n")


def main():
    parser = argparse.ArgumentParser(description="Run Signal-to-Shock Risk Engine")
    parser.add_argument("--input", choices=["processed", "replay"], default="replay", help="Input dataset source")
    parser.add_argument("--limit", type=int, default=150, help="Maximum items to process")
    parser.add_argument("--out", type=str, default=str(SIGNALS_PROCESSED_FILE), help="Output JSONL path")
    parser.add_argument("--offline", action="store_true", help="Force offline rules fallback")
    parser.add_argument("--require-llm", action="store_true", help="Fail loudly if LLM fails instead of falling back")

    args = parser.parse_args()

    input_path = REPLAY_EVENTS_FILE if args.input == "replay" else PROCESSED_ITEMS_FILE
    out_path = Path(args.out)

    llm_client = LLMClient(offline_mode=args.offline, require_llm=args.require_llm) if (args.offline or args.require_llm) else None
    engine = RiskEngine(llm_client=llm_client, require_llm=args.require_llm)

    raw_items = load_raw_items_from_jsonl(input_path, limit=args.limit)
    signals = engine.process_items(raw_items)
    write_signals_to_jsonl(signals, out_path)
    print_summary_table(signals)


if __name__ == "__main__":
    main()
