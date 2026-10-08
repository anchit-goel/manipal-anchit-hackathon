"""NewsAPI ingestion client with offline fallback and disk caching."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from src.config import NEWSAPI_KEY, NEWSAPI_RAW_DIR, OFFLINE_MODE, get_logger
from src.schemas import RawItem
from src.ingest.base import BaseIngestClient
from src.ingest.cache import FileCache

logger = get_logger("ingest.newsapi")


class NewsAPIClient(BaseIngestClient):
    """Client for newsapi.org with caching and graceful offline fallback."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[FileCache] = None,
        raw_dir: Optional[Path] = None,
        offline_mode: bool = OFFLINE_MODE,
    ):
        super().__init__(name="NewsAPI", cache=cache, offline_mode=offline_mode)
        self.api_key = api_key or NEWSAPI_KEY
        self.raw_dir = raw_dir or NEWSAPI_RAW_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_article(self, article: Dict[str, Any], query_tag: str) -> Optional[RawItem]:
        """Convert a NewsAPI article JSON dict into a validated RawItem."""
        title = (article.get("title") or "").strip()
        description = (article.get("description") or "").strip()
        content = (article.get("content") or "").strip()
        body = f"{description} {content}".strip() or title
        url = article.get("url")

        if not title or title == "[Removed]":
            return None

        published_at = article.get("publishedAt") or datetime.now(timezone.utc).isoformat()
        author_name = article.get("author") or (article.get("source") or {}).get("name") or "NewsAPI"
        item_id = self.generate_item_id("newsapi", title, url)

        return RawItem(
            item_id=item_id,
            source="NewsAPI",
            source_type="news",
            published_at=published_at,
            title=title,
            text=body,
            url=url,
            author=author_name,
            engagement={},
            query_tag=query_tag,
            is_synthetic=bool(article.get("is_synthetic", False)),
        )

    def _load_local_raw_files(self) -> List[Dict[str, Any]]:
        """Load articles from local JSON files in raw_dir when offline."""
        articles = []
        for json_file in self.raw_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "articles" in data:
                        articles.extend(data["articles"])
                    elif isinstance(data, list):
                        articles.extend(data)
            except Exception as e:
                logger.warning("Error reading local news file %s: %s", json_file, e)
        return articles

    def fetch(
        self,
        query: str = "banking OR economy OR energy OR shipping",
        days: int = 7,
        limit: int = 50,
    ) -> List[RawItem]:
        """Fetch news articles from NewsAPI or offline storage."""
        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
            "language": "en",
        }

        # Offline path or missing API key
        if self.offline_mode or not self.api_key:
            if not self.api_key:
                logger.info("NEWSAPI_KEY is not set. Operating in offline cache mode.")
            else:
                logger.info("OFFLINE_MODE enabled. Using cached NewsAPI articles.")

            # Try cache first, then raw folder
            cached = self.cache.get("newsapi", params)
            if cached and isinstance(cached, dict) and "articles" in cached:
                raw_articles = cached["articles"]
            else:
                raw_articles = self._load_local_raw_files()

            items: List[RawItem] = []
            for art in raw_articles:
                item = self._normalize_article(art, query_tag=query)
                if item:
                    items.append(item)
            return items

        # Online fetch closure
        def fetcher() -> Optional[Dict[str, Any]]:
            headers = {"X-Api-Key": self.api_key}
            try:
                resp = requests.get(self.BASE_URL, params=params, headers=headers, timeout=6.0)
                if resp.status_code == 200:
                    payload = resp.json()
                    # Persist raw snapshot to disk
                    raw_filename = f"news_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
                    with open(self.raw_dir / raw_filename, "w", encoding="utf-8") as rf:
                        json.dump(payload, rf, indent=2)
                    return payload
                logger.warning("NewsAPI returned HTTP %d: %s", resp.status_code, resp.text)
                return None
            except Exception as ex:
                logger.warning("NewsAPI network call failed: %s", ex)
                return None

        result = self.cache.execute_cached("newsapi", params, fetcher)
        raw_articles = (result or {}).get("articles", []) if isinstance(result, dict) else []

        if not raw_articles:
            # Fall back to local raw directory
            raw_articles = self._load_local_raw_files()

        items: List[RawItem] = []
        for art in raw_articles:
            item = self._normalize_article(art, query_tag=query)
            if item:
                items.append(item)
        return items
