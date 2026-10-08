"""Unit tests for deterministic file cache and offline fallback."""
import tempfile
from pathlib import Path
from src.ingest.cache import FileCache


def test_cache_set_and_get():
    """Verify that items stored in cache are accurately retrieved."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = FileCache(cache_dir=Path(tmp_dir), offline_mode=False)
        params = {"query": "test_bank", "limit": 10}
        payload = {"data": [1, 2, 3]}

        assert cache.get("test_ns", params) is None
        cache.set("test_ns", params, payload)
        retrieved = cache.get("test_ns", params)
        assert retrieved == payload


def test_cache_offline_mode_bypasses_fetcher():
    """Verify that offline mode never invokes the live fetcher on cache miss."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = FileCache(cache_dir=Path(tmp_dir), offline_mode=True)
        params = {"query": "unseen_query"}

        called = False

        def live_fetcher():
            nonlocal called
            called = True
            return {"status": "live"}

        result = cache.execute_cached("offline_ns", params, live_fetcher)
        assert called is False
        assert result is None


def test_cache_online_fetches_and_persists():
    """Verify that online mode calls fetcher and populates cache."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = FileCache(cache_dir=Path(tmp_dir), offline_mode=False)
        params = {"query": "online_query"}

        call_count = 0

        def live_fetcher():
            nonlocal call_count
            call_count += 1
            return {"status": "ok", "items": ["a", "b"]}

        res1 = cache.execute_cached("online_ns", params, live_fetcher)
        assert call_count == 1
        assert res1["status"] == "ok"

        # Second call hits cache, does not call fetcher
        res2 = cache.execute_cached("online_ns", params, live_fetcher)
        assert call_count == 1
        assert res2 == res1


def test_cache_fallback_on_network_error():
    """Verify that on network exception, cached data is gracefully returned."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = FileCache(cache_dir=Path(tmp_dir), offline_mode=False)
        params = {"query": "fail_query"}

        # Pre-seed cache
        cache.set("fail_ns", params, {"stale": "data"})

        def failing_fetcher():
            raise ConnectionError("Simulated network outage")

        res = cache.execute_cached("fail_ns", params, failing_fetcher)
        assert res == {"stale": "data"}
