"""Deterministic disk caching layer for resilient offline-first API operations."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from src.config import CACHE_DIR, OFFLINE_MODE, get_logger

logger = get_logger("cache")


class FileCache:
    """Hash-keyed JSON file cache supporting strict offline fallback."""

    def __init__(self, cache_dir: Optional[Path] = None, offline_mode: bool = OFFLINE_MODE):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode

    def _hash_key(self, namespace: str, params: Dict[str, Any]) -> str:
        """Generate a deterministic hex digest from namespace and parameters."""
        serialized = json.dumps(params, sort_keys=True, default=str)
        raw_key = f"{namespace}:{serialized}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get_cache_path(self, namespace: str, params: Dict[str, Any]) -> Path:
        """Return the absolute path for a cached request file."""
        key_hash = self._hash_key(namespace, params)
        sub_dir = self.cache_dir / namespace
        sub_dir.mkdir(parents=True, exist_ok=True)
        return sub_dir / f"{key_hash}.json"

    def get(self, namespace: str, params: Dict[str, Any]) -> Optional[Any]:
        """Retrieve cached payload if present."""
        path = self.get_cache_path(namespace, params)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("payload")
        except Exception as e:
            logger.warning("Failed to read cache file %s: %s", path, e)
            return None

    def set(self, namespace: str, params: Dict[str, Any], payload: Any) -> None:
        """Persist payload to disk with metadata."""
        path = self.get_cache_path(namespace, params)
        cache_entry = {
            "namespace": namespace,
            "params": params,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2)
        except Exception as e:
            logger.warning("Failed to write cache file %s: %s", path, e)

    def execute_cached(
        self,
        namespace: str,
        params: Dict[str, Any],
        fetcher: Callable[[], Any],
    ) -> Optional[Any]:
        """Execute a network fetcher with cache-first and offline-fallback semantics."""
        cached_data = self.get(namespace, params)

        # In offline mode, strictly return cached content without making external calls
        if self.offline_mode:
            if cached_data is not None:
                logger.debug("Cache HIT in offline mode for %s", namespace)
                return cached_data
            logger.info("Cache MISS in offline mode for %s. Bypassing network call.", namespace)
            return None

        # When online, check cache first
        if cached_data is not None:
            return cached_data

        # Online fetch with graceful fallback
        try:
            logger.debug("Executing live fetch for %s", namespace)
            result = fetcher()
            if result is not None:
                self.set(namespace, params, result)
            return result
        except Exception as e:
            logger.warning(
                "Network request failed for %s (%s). Attempting stale cache fallback.",
                namespace,
                e,
            )
            # Re-check cache in case of any concurrent write
            return cached_data
