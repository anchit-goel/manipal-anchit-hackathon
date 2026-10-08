"""FinBERT sentiment cross-check engine with lazy loading, batching, caching, and lexicon fallback."""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional
from src.config import CACHE_DIR, get_logger

logger = get_logger("engine.finbert")

FINBERT_CACHE_DIR = CACHE_DIR / "finbert"


class FinanceLexiconScorer:
    """Fallback sentiment scorer when transformer models or torch are unavailable."""

    POSITIVE_WORDS = {
        "surge", "rally", "gain", "profit", "beat", "record", "expand", "growth",
        "strong", "resilient", "secure", "outperform", "dividend", "upgraded",
        "recovery", "rebound", "boost", "liquidity", "bullish", "acquisition"
    }
    NEGATIVE_WORDS = {
        "plunge", "fall", "drop", "loss", "risk", "default", "alert", "cancel",
        "probe", "penalty", "suspend", "halt", "moratorium", "downgrade", "pressure",
        "cut", "glitch", "delay", "warning", "distressed", "disruption", "bearish"
    }

    def score(self, text: str) -> float:
        """Compute normalized sentiment score in [-1.0, 1.0]."""
        words = text.lower().split()
        if not words:
            return 0.0

        pos = sum(1 for w in words if w.strip(".,!?:;\"'()[]") in self.POSITIVE_WORDS)
        neg = sum(1 for w in words if w.strip(".,!?:;\"'()[]") in self.NEGATIVE_WORDS)

        total = pos + neg
        if total == 0:
            return 0.0
        diff = (pos - neg) / total
        return round(max(-1.0, min(1.0, diff)), 2)


class FinBertEngine:
    """Lazy-loaded ProsusAI/finbert cross-check engine with disk caching."""

    def __init__(self, cache_dir: Optional[Path] = None, force_lexicon: bool = False):
        self.cache_dir = cache_dir or FINBERT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.force_lexicon = force_lexicon
        self.lexicon_scorer = FinanceLexiconScorer()

        self._tokenizer = None
        self._model = None
        self._torch = None
        self._is_loaded = False
        self._load_failed = False

    def _ensure_loaded(self):
        """Lazy load Hugging Face transformers pipeline."""
        if self._is_loaded or self._load_failed or self.force_lexicon:
            return

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            logger.info("Loading ProsusAI/finbert model onto CPU...")
            self._torch = torch
            self._tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self._model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self._model.eval()
            self._is_loaded = True
            logger.info("FinBERT successfully loaded.")
        except Exception as e:
            logger.warning("Could not load ProsusAI/finbert (%s). Falling back to lexicon scorer.", e)
            self._load_failed = True

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _get_cached(self, text_hash: str) -> Optional[float]:
        cache_path = self.cache_dir / f"{text_hash}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("score")
            except Exception:
                pass
        return None

    def _set_cached(self, text_hash: str, score: float, model_tag: str):
        cache_path = self.cache_dir / f"{text_hash}.json"
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"score": score, "model": model_tag}, f)
        except Exception:
            pass

    def score_single(self, text: str) -> tuple[float, str]:
        """Compute FinBERT sentiment: P(positive) - P(negative) in [-1.0, 1.0]."""
        clean_text = text[:400].strip()
        text_hash = self._hash_text(clean_text)

        # Cache check
        cached_val = self._get_cached(text_hash)
        if cached_val is not None:
            return cached_val, "ProsusAI/finbert"

        self._ensure_loaded()

        # If live transformer model is available
        if self._is_loaded and self._model is not None and self._tokenizer is not None:
            try:
                inputs = self._tokenizer(
                    clean_text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=128,
                    padding=True,
                )
                with self._torch.no_grad():
                    logits = self._model(**inputs).logits
                    probs = self._torch.nn.functional.softmax(logits, dim=-1)[0]
                    # ProsusAI/finbert classes: [positive (0), negative (1), neutral (2)]
                    p_pos = float(probs[0])
                    p_neg = float(probs[1])
                    sentiment = round(p_pos - p_neg, 2)
                    self._set_cached(text_hash, sentiment, "ProsusAI/finbert")
                    return sentiment, "ProsusAI/finbert"
            except Exception as e:
                logger.warning("FinBERT inference failed (%s). Using lexicon fallback.", e)

        # Lexicon fallback
        sentiment = self.lexicon_scorer.score(clean_text)
        self._set_cached(text_hash, sentiment, "lexicon-fallback")
        return sentiment, "lexicon-fallback"

    def score_batch(self, texts: List[str]) -> List[tuple[float, str]]:
        """Batch score a collection of text strings."""
        return [self.score_single(t) for t in texts]
