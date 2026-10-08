"""Abstract base client for ingestion sources."""
import abc
import hashlib
from typing import List, Optional
from src.config import CACHE_DIR, OFFLINE_MODE, get_logger
from src.schemas import RawItem
from src.ingest.cache import FileCache

logger = get_logger("ingest.base")


class BaseIngestClient(abc.ABC):
    """Abstract base class for all news and social ingestion connectors."""

    def __init__(
        self,
        name: str,
        cache: Optional[FileCache] = None,
        offline_mode: bool = OFFLINE_MODE,
    ):
        self.name = name
        self.cache = cache or FileCache(cache_dir=CACHE_DIR, offline_mode=offline_mode)
        self.offline_mode = offline_mode

    @abc.abstractmethod
    def fetch(
        self,
        query: str = "",
        days: int = 7,
        limit: int = 50,
    ) -> List[RawItem]:
        """Fetch items matching query over a lookback window of days."""
        pass

    @staticmethod
    def generate_item_id(prefix: str, text: str, url: Optional[str] = None) -> str:
        """Create a deterministic unique item_id from text and url."""
        seed = f"{prefix}:{url or ''}:{text.strip().lower()}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
        return f"{prefix.lower()}_{digest}"
