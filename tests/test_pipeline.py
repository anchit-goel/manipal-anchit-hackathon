"""Unit and integration tests for the multi-source ingestion pipeline."""
import json
import tempfile
from pathlib import Path

from src.ingest.pipeline import IngestionPipeline, _simplify_title_key
from src.schemas import RawItem


def test_simplify_title_key_deduplication():
    """Verify that near-identical headlines map to the same deduplication key."""
    t1 = "Maersk Reroutes Container Ships Around Red Sea!"
    t2 = "Maersk reroutes container ships around Red Sea"
    t3 = "Maersk reroutes container vessels via Cape of Good Hope"
    assert _simplify_title_key(t1) == _simplify_title_key(t2)
    assert _simplify_title_key(t1) != _simplify_title_key(t3)


def test_pipeline_offline_execution_end_to_end():
    """Verify end-to-end pipeline execution in offline mode with file persistence."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "test_raw_items.jsonl"
        pipeline = IngestionPipeline(offline_mode=True, output_file=output_file)

        items = pipeline.run(days=14, limit_per_source=20, filter_universe=True)

        assert len(items) > 0
        assert output_file.exists()

        # Check source types present
        source_types = {it.source_type for it in items}
        assert "news" in source_types
        assert "social" in source_types

        # Verify line-by-line schema compliance in saved JSONL
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == len(items)
            for line in lines:
                raw_dict = json.loads(line)
                validated = RawItem.model_validate(raw_dict)
                assert validated.item_id is not None
                assert validated.source_type in ("news", "social")


def test_pipeline_never_crashes_with_empty_or_bad_sources():
    """Verify resilience when source clients return empty collections."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "empty_output.jsonl"
        pipeline = IngestionPipeline(offline_mode=True, output_file=output_file)

        # Mock clients to simulate empty or missing files
        pipeline.newsapi_client.raw_dir = Path(tmp_dir) / "nonexistent_news"
        pipeline.gdelt_client.raw_dir = Path(tmp_dir) / "nonexistent_gdelt"
        pipeline.social_loader.filepath = Path(tmp_dir) / "nonexistent_social.json"

        # Should execute cleanly without raising exceptions
        items = pipeline.run(days=1, limit_per_source=5)
        assert items == []
        assert output_file.exists()
