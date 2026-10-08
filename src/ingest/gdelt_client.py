"""GDELT DOC 2.0 API ingestion client with disk caching and offline support."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from src.config import GDELT_RAW_DIR, OFFLINE_MODE, get_logger
from src.schemas import RawItem
from src.ingest.base import BaseIngestClient
from src.ingest.cache import FileCache

logger = get_logger("ingest.gdelt")


class GDELTClient(BaseIngestClient):
    """Client for GDELT DOC 2.0 API with offline resilience."""

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(
        self,
        cache: Optional[FileCache] = None,
        raw_dir: Optional[Path] = None,
        offline_mode: bool = OFFLINE_MODE,
    ):
        super().__init__(name="GDELT", cache=cache, offline_mode=offline_mode)
        self.raw_dir = raw_dir or GDELT_RAW_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_gdelt_timestamp(seendate: Optional[str]) -> str:
        """Parse GDELT timestamp format (e.g. 20261008T163000Z) to ISO 8601."""
        if not seendate:
            return datetime.now(timezone.utc).isoformat()
        try:
            clean = re.sub(r"[^0-9]", "", seendate)
            if len(clean) >= 14:
                dt = datetime.strptime(clean[:14], "%Y%m%d%H%M%S")
                return dt.replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            pass
        return datetime.now(timezone.utc).isoformat()

    def _normalize_article(self, article: Dict[str, Any], query_tag: str) -> Optional[RawItem]:
        """Convert a GDELT article into a validated RawItem."""
        title = (article.get("title") or "").strip()
        url = article.get("url")
        if not title:
            return None

        seendate = article.get("seendate")
        published_at = self._parse_gdelt_timestamp(seendate)
        domain = article.get("domain") or article.get("sourcecountry") or "GDELT"
        item_id = self.generate_item_id("gdelt", title, url)

        return RawItem(
            item_id=item_id,
            source="GDELT",
            source_type="news",
            published_at=published_at,
            title=title,
            text=title,  # GDELT DOC 2.0 provides headlines & snippets
            url=url,
            author=domain,
            engagement={},
            query_tag=query_tag,
            is_synthetic=False,
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
                logger.warning("Error reading local GDELT file %s: %s", json_file, e)
        return articles

    def fetch(
        self,
        query: str = "banking OR economy OR energy OR shipping",
        days: int = 7,
        limit: int = 50,
    ) -> List[RawItem]:
        """Fetch news articles from GDELT DOC 2.0 API or offline storage."""
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": min(limit, 75),
            "timespan": f"{days}d",
        }

        if self.offline_mode:
            logger.info("OFFLINE_MODE enabled. Using cached GDELT articles.")
            cached = self.cache.get("gdelt", params)
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
            try:
                resp = requests.get(self.BASE_URL, params=params, timeout=7.0)
                if resp.status_code == 200:
                    payload = resp.json()
                    # Persist raw snapshot
                    raw_filename = f"gdelt_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
                    with open(self.raw_dir / raw_filename, "w", encoding="utf-8") as rf:
                        json.dump(payload, rf, indent=2)
                    return payload
                logger.warning("GDELT returned HTTP %d", resp.status_code)
                return None
            except Exception as ex:
                logger.warning("GDELT network request failed: %s", ex)
                return None

        result = self.cache.execute_cached("gdelt", params, fetcher)
        raw_articles = (result or {}).get("articles", []) if isinstance(result, dict) else []

        if not raw_articles:
            raw_articles = self._load_local_raw_files()

        items: List[RawItem] = []
        for art in raw_articles:
            item = self._normalize_article(art, query_tag=query)
            if item:
                items.append(item)
        return items
