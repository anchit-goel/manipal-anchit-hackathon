"""End-to-end ingestion pipeline aggregating news and social feeds."""
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.config import (
    OFFLINE_MODE,
    PROCESSED_DIR,
    PROCESSED_ITEMS_FILE,
    get_logger,
)
from src.schemas import RawItem
from src.universe import CompanyExposure, load_universe, match_company
from src.ingest.newsapi_client import NewsAPIClient
from src.ingest.gdelt_client import GDELTClient
from src.ingest.social_loader import SocialLoader

logger = get_logger("ingest.pipeline")


def _simplify_title_key(title: str) -> str:
    """Produce a canonical key for near-duplicate headline detection."""
    clean = re.sub(r"[^a-z0-9\s]", "", title.lower())
    tokens = [t for t in clean.split() if len(t) > 2]
    return " ".join(tokens[:7])


class IngestionPipeline:
    """Coordinates multi-source collection, deduplication, universe filtering, and persistence."""

    def __init__(
        self,
        offline_mode: bool = OFFLINE_MODE,
        output_file: Optional[Path] = None,
    ):
        self.offline_mode = offline_mode
        self.output_file = output_file or PROCESSED_ITEMS_FILE
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.universe: List[CompanyExposure] = load_universe()

        # Initialize clients with offline configuration
        self.newsapi_client = NewsAPIClient(offline_mode=self.offline_mode)
        self.gdelt_client = GDELTClient(offline_mode=self.offline_mode)
        self.social_loader = SocialLoader(offline_mode=self.offline_mode)

    def run(
        self,
        days: int = 7,
        query: str = "banking OR economy OR energy OR shipping",
        limit_per_source: int = 50,
        filter_universe: bool = True,
    ) -> List[RawItem]:
        """Execute ingestion across all channels and persist filtered items."""
        logger.info(
            "Starting ingestion run (offline_mode=%s, days=%d, query='%s')",
            self.offline_mode,
            days,
            query,
        )

        raw_collection: List[RawItem] = []

        # 1. Fetch NewsAPI items
        try:
            news_items = self.newsapi_client.fetch(query=query, days=days, limit=limit_per_source)
            logger.info("NewsAPI returned %d items", len(news_items))
            raw_collection.extend(news_items)
        except Exception as e:
            logger.warning("NewsAPI ingestion encountered non-fatal error: %s", e)

        # 2. Fetch GDELT items
        try:
            gdelt_items = self.gdelt_client.fetch(query=query, days=days, limit=limit_per_source)
            logger.info("GDELT returned %d items", len(gdelt_items))
            raw_collection.extend(gdelt_items)
        except Exception as e:
            logger.warning("GDELT ingestion encountered non-fatal error: %s", e)

        # 3. Fetch Social items
        try:
            social_items = self.social_loader.fetch(query="", days=days, limit=limit_per_source * 2)
            logger.info("Social loader returned %d items", len(social_items))
            raw_collection.extend(social_items)
        except Exception as e:
            logger.warning("Social ingestion encountered non-fatal error: %s", e)

        logger.info("Total raw items collected before dedupe/filter: %d", len(raw_collection))

        # 4. Deduplicate (URL and near-duplicate title)
        deduped: List[RawItem] = []
        seen_urls: Set[str] = set()
        seen_title_keys: Set[str] = set()

        for item in raw_collection:
            if item.url and item.url in seen_urls:
                continue
            title_key = _simplify_title_key(item.title)
            if title_key in seen_title_keys:
                continue

            if item.url:
                seen_urls.add(item.url)
            seen_title_keys.add(title_key)
            deduped.append(item)

        logger.info("Items retained after deduplication: %d", len(deduped))

        # 5. Universe relevance filtering
        filtered: List[RawItem] = []
        for item in deduped:
            content_to_check = f"{item.title} {item.text}"
            matched = match_company(content_to_check, self.universe)
            if filter_universe and not matched:
                continue

            # Tag query with ticker if matched
            if matched and not item.query_tag:
                item.query_tag = matched.ticker

            filtered.append(item)

        logger.info("Items retained after universe filtering: %d", len(filtered))

        # 6. Sort newest first
        filtered.sort(key=lambda x: x.published_at, reverse=True)

        # 7. Write to JSONL
        with open(self.output_file, "w", encoding="utf-8") as f:
            for item in filtered:
                f.write(item.model_dump_json() + "\n")

        logger.info("Persisted %d validated items to %s", len(filtered), self.output_file)
        return filtered

    def get_source_breakdown(self, items: List[RawItem]) -> Dict[str, int]:
        """Compute counts per source_type and provider."""
        counts: Dict[str, int] = {}
        for item in items:
            key = f"source_type:{item.source_type} ({item.source})"
            counts[key] = counts.get(key, 0) + 1
        return counts


def main():
    """CLI entry point for ingestion pipeline."""
    parser = argparse.ArgumentParser(description="Run Signal-to-Shock Data Ingestion Pipeline")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    parser.add_argument("--query", type=str, default="banking OR economy OR energy OR shipping", help="Topic query string")
    parser.add_argument("--offline", action="store_true", default=OFFLINE_MODE, help="Enforce offline cache-only mode")
    parser.add_argument("--no-filter", action="store_true", help="Disable universe filtering")
    parser.add_argument("--limit", type=int, default=50, help="Per-source ingestion limit")

    args = parser.parse_args()

    pipeline = IngestionPipeline(offline_mode=args.offline)
    items = pipeline.run(
        days=args.days,
        query=args.query,
        limit_per_source=args.limit,
        filter_universe=not args.no_filter,
    )

    print("\n" + "=" * 60)
    print("INGESTION PIPELINE RUN SUMMARY")
    print("=" * 60)
    print(f"Total Processed Items: {len(items)}")
    print(f"Persisted File:        {pipeline.output_file}")
    print("\nSource Type Breakdown:")
    breakdown = pipeline.get_source_breakdown(items)
    for src, count in sorted(breakdown.items()):
        print(f"  - {src}: {count}")

    print("\nFirst 5 Processed Items Preview:")
    for i, it in enumerate(items[:5], 1):
        print(f"[{i}] [{it.source_type.upper()}] [{it.source}] ({it.published_at[:10]}) {it.title}")
        print(f"    Target/Tag: {it.query_tag} | URL: {it.url}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
