"""Social feed loader for synthetic and local social chatter datasets."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import SOCIAL_POSTS_FILE, SOCIAL_RAW_DIR, OFFLINE_MODE, get_logger
from src.schemas import RawItem
from src.ingest.base import BaseIngestClient
from src.ingest.cache import FileCache

logger = get_logger("ingest.social")


class SocialLoader(BaseIngestClient):
    """Loads social feed data (tweets/posts) with schema validation."""

    def __init__(
        self,
        filepath: Optional[Path] = None,
        cache: Optional[FileCache] = None,
        offline_mode: bool = OFFLINE_MODE,
    ):
        super().__init__(name="SocialLoader", cache=cache, offline_mode=offline_mode)
        self.filepath = filepath or SOCIAL_POSTS_FILE
        self.raw_dir = SOCIAL_RAW_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_post(self, post: Dict[str, Any], query_tag: str) -> Optional[RawItem]:
        """Normalize a social media post dictionary into a validated RawItem."""
        text = (post.get("text") or "").strip()
        title = (post.get("title") or text[:80]).strip()
        if not text:
            return None

        published_at = post.get("published_at") or datetime.now(timezone.utc).isoformat()
        author = post.get("author") or "@MarketParticipant"
        url = post.get("url")
        item_id = post.get("post_id") or self.generate_item_id("social", text, url)
        engagement = post.get("engagement") or {}
        is_synthetic = bool(post.get("is_synthetic", True))

        return RawItem(
            item_id=item_id,
            source="Social/X",
            source_type="social",
            published_at=published_at,
            title=title,
            text=text,
            url=url,
            author=author,
            engagement=engagement,
            query_tag=query_tag,
            is_synthetic=is_synthetic,
        )

    def fetch(
        self,
        query: str = "",
        days: int = 7,
        limit: int = 100,
    ) -> List[RawItem]:
        """Load and filter social items from local structured files."""
        if not self.filepath.exists():
            logger.warning("Social posts file not found at %s. Returning empty list.", self.filepath)
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw_posts = json.load(f)
        except Exception as e:
            logger.error("Failed to parse social dataset %s: %s", self.filepath, e)
            return []

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        items: List[RawItem] = []

        query_tokens = [q.lower().strip() for q in query.split() if q.strip()] if query else []

        for p in raw_posts:
            if not isinstance(p, dict):
                continue

            # Query filter if specified
            text = (p.get("text") or "").lower()
            if query_tokens and not any(tok in text for tok in query_tokens):
                continue

            # Lookback filter
            pub_str = p.get("published_at")
            if pub_str:
                try:
                    pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                    if pub_dt < cutoff_date:
                        continue
                except Exception:
                    pass

            item = self._normalize_post(p, query_tag=query)
            if item:
                items.append(item)
                if len(items) >= limit:
                    break

        logger.info("Loaded %d social items from %s", len(items), self.filepath.name)
        return items
