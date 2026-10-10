"""Central configuration and path management for Signal-to-Shock."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Resolve root repository directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables from .env if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Key directory paths
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
NEWSAPI_RAW_DIR = RAW_DIR / "newsapi"
GDELT_RAW_DIR = RAW_DIR / "gdelt"
SOCIAL_RAW_DIR = RAW_DIR / "social"
CACHE_DIR = DATA_DIR / "cache"
LLM_CACHE_DIR = CACHE_DIR / "llm"
PROCESSED_DIR = DATA_DIR / "processed"
REPLAY_DIR = DATA_DIR / "replay"
EVAL_DIR = DATA_DIR / "eval"

# Key file paths
UNIVERSE_CSV = DATA_DIR / "universe.csv"
PROCESSED_ITEMS_FILE = PROCESSED_DIR / "raw_items.jsonl"
SIGNALS_PROCESSED_FILE = PROCESSED_DIR / "signals.jsonl"
REPLAY_EVENTS_FILE = REPLAY_DIR / "demo_events.jsonl"
SOCIAL_POSTS_FILE = SOCIAL_RAW_DIR / "synthetic_posts.json"
GOLD_EVAL_FILE = EVAL_DIR / "gold.jsonl"

# Engine Parameters & Thresholds
MAX_LLM_CALLS = int(os.getenv("MAX_LLM_CALLS", "150"))
LLM_MAX_RPM = int(os.getenv("LLM_MAX_RPM", "4"))
TRIGGER_IMPACT_THRESHOLD = 7.0
TRIGGER_CONFIDENCE_THRESHOLD = 0.6

# Controlled Risk Themes Vocabulary (Task 1)
CONTROLLED_THEMES = [
    "shipping_disruption",
    "oil_price_up",
    "oil_price_down",
    "credit_downgrade",
    "credit_default",
    "banking_stress",
    "rate_hike",
    "rate_cut",
    "regulatory_action",
    "antitrust",
    "chip_supply_shock",
    "sanctions",
    "demand_shock",
    "merger_activity",
    "none",
]

# Calibration Paths (Tasks 2, 3, 4, 5, 6)
CALIBRATION_DIR = DATA_DIR / "calibration"
CALIBRATION_PRICES_DIR = CALIBRATION_DIR / "prices"
CALIBRATION_EVENTS_FILE = CALIBRATION_DIR / "events.csv"
CALIBRATION_EVENTS_TEXT_FILE = CALIBRATION_DIR / "events_text.jsonl"
CALIBRATION_MODEL_FILE = CALIBRATION_DIR / "calibration_model.json"
SHOCK_SEED_FILE = CALIBRATION_DIR / "shock_seed.csv"

# Source Reliability Priors
SOURCE_RELIABILITY_TABLE = {
    "reuters": 0.85,
    "bloomberg": 0.85,
    "financial times": 0.85,
    "the wall street journal": 0.85,
    "newsapi": 0.80,
    "gdelt": 0.65,
    "social/x": 0.35,
    "default_news": 0.75,
    "default_social": 0.35,
}

# Confidence Component Weights (sum = 1.0)
CONFIDENCE_WEIGHTS = {
    "source_reliability": 0.30,
    "corroboration": 0.25,
    "sentiment_agreement": 0.20,
    "self_consistency": 0.15,
    "claim_certainty": 0.10,
}

# API keys & Providers
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
LLM_API_KEY = (
    os.getenv("LLM_API_KEY", "")
    or GEMINI_API_KEY
    or OPENAI_API_KEY
).strip()

# Offline mode determination
# Default to True when API keys are absent or OFFLINE_MODE is explicitly set
_env_offline = os.getenv("OFFLINE_MODE", "").strip().lower()
if _env_offline in ("true", "1", "yes"):
    OFFLINE_MODE = True
elif _env_offline in ("false", "0", "no"):
    OFFLINE_MODE = False
else:
    # Auto-detect: offline if no news key is provided
    OFFLINE_MODE = not bool(NEWSAPI_KEY)

# Port configurations
API_PORT = int(os.getenv("API_PORT", "8000"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# Logging setup
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
