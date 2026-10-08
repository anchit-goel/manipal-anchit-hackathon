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
PROCESSED_DIR = DATA_DIR / "processed"
REPLAY_DIR = DATA_DIR / "replay"

# Key file paths
UNIVERSE_CSV = DATA_DIR / "universe.csv"
PROCESSED_ITEMS_FILE = PROCESSED_DIR / "raw_items.jsonl"
REPLAY_EVENTS_FILE = REPLAY_DIR / "demo_events.jsonl"
SOCIAL_POSTS_FILE = SOCIAL_RAW_DIR / "synthetic_posts.json"

# API keys & Providers
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
LLM_API_KEY = (
    os.getenv("LLM_API_KEY", "")
    or os.getenv("GEMINI_API_KEY", "")
    or os.getenv("OPENAI_API_KEY", "")
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
