# Data Directory Documentation

This directory contains all data assets utilized by the Signal-to-Shock risk platform. All files are strictly non-confidential, lightweight (<10 MB total), and self-contained for offline replication.

## 1. Directory Structure

- `data/universe.csv`:
  The 20 systemic wholesale banking counterparties mapped across sectors (Banking, Energy, Shipping, Tech/Semiconductors, Autos, Aerospace, Airlines), countries, and benchmark ETFs.
- `data/raw/gdelt/`:
  - `gdelt_real_pull.json`: 50 **real articles** fetched via live GDELT DOC 2.0 API queries covering market themes (banking, Red Sea, shipping, energy, credit downgrades, mergers). Contains real public titles, URLs, and source domains from the past 7 days.
  - `sample_gdelt_illustrative.json`: Hand-curated illustrative templates explicitly marked with `is_synthetic: true`.
- `data/raw/newsapi/`:
  - `sample_news_illustrative.json`: Hand-curated illustrative templates explicitly marked with `is_synthetic: true` used for offline demonstration when a live NewsAPI subscription key is unavailable.
- `data/raw/social/`:
  - `synthetic_posts.json`: 100 synthetic market posts covering the universe tickers with realistic distributions of institutional notes, unverified rumors, and retail hype. Explicitly marked `is_synthetic: true`.
  - `README.md`: Specific schema and category breakdown for social chatter.
- `data/replay/`:
  - `demo_events.jsonl`: 14 hand-curated chronological scenario events spanning baseline low-impact news, uncorroborated social rumors, and 4 high-impact market shocks. Formatted as `RawItem` lines, explicitly marked `is_synthetic: true`.
  - `README.md`: Detailed scenario storyline and event metadata.
- `data/processed/`:
  - `raw_items.jsonl`: Output of the ingestion pipeline after deduplication and universe filtering.
  - `signals.jsonl`: Output of the Phase 2 risk engine containing fully extracted and validated risk signals.
- `data/eval/`:
  - `gold.jsonl`: ~25 author-labeled evaluation items used for benchmarking engine extraction accuracy, sentiment correlation, and impact MAE.
  - `README.md`: Annotation guidelines and dataset origin.
- `data/cache/`:
  Deterministic hash-keyed disk cache for offline reproducibility.
