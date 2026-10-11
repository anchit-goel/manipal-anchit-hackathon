# Data Directory Documentation & Provenance

This directory contains all data assets utilized by the **Signal-to-Shock** real-time risk platform. Every asset is strictly non-confidential, public or synthetic, and lightweight (<10 MB total tracked footprint), engineered for 100% deterministic offline replication.

---

## 1. Safety, Privacy & Synthetic Data Declaration

- **No Proprietary Data**: No confidential, proprietary, or client-identifying institutional banking data is included.
- **Synthetic Portfolios**: The wholesale credit, bond, and derivative portfolio (`data/portfolio/portfolio.csv`) is entirely synthetic, procedurally generated with fixed pseudo-random seeds (`seed=20260101`). Counterparty names reference public entities strictly for realism and demonstration purposes.
- **Public & Open Sources**: Market prices and event study benchmarks are sourced from public financial records via Yahoo Finance. News samples are sourced from the public GDELT DOC 2.0 API or author-curated illustrative templates.
- **Offline Cache**: Deterministic pre-computed cache files enable complete system execution, calibration inspection, and SSE event streaming without external network calls or paid API keys.

---

## 2. Directory Structure & Inventory

### `data/universe.csv`
- **Description**: The 20 systemic wholesale banking counterparties mapped across 7 core sectors (Banking, Energy, Shipping, Tech/Semiconductors, Autos, Aerospace, Airlines), headquarters countries, and benchmark ETFs (e.g., XLF, XLE, XTN, SMH).

### `data/portfolio/`
- `portfolio.csv`: Synthetic 50-position wholesale credit and derivatives portfolio (~$1.3B total market value). Spans 18 commercial loans (with trade finance collateral), 12 corporate bonds (with durations up to 9 years), 10 OTC derivatives (MTM exposure proxy and delta sensitivities to oil/rates), and 10 strategic equity holdings. Generated via `python -m src.portfolio.build`.
- `shock_table.csv`: Quantitative transmission matrix mapping event themes (e.g., `oil_price_up`, `shipping_disruption`, `bank_credit_negative`, `cyber_tech_outage`) to asset-class-specific valuation shocks across sectors, tags, and ratings.
- `README.md`: Formal portfolio modeling assumptions, delta definitions, and shock calibration methodology.

### `data/calibration/`
- `events.csv`: 24 real historical financial shocks spanning 2020–2025 across Macroeconomic, Credit, Operational, Supply Chain, and Geopolitical event classes. Includes event date, primary ticker, benchmark index, and description.
- `events_text.jsonl`: Curated headline and summary text associated with each historical calibration event.
- `prices/`: Trimmed daily OHLCV CSV slices for relevant tickers and benchmark ETFs (e.g., `BA.csv`, `BAC.csv`, `CS.csv`, `NVDA.csv`, `SPY.csv`, `XLF.csv`) spanning the 400-day estimation window `[-300, +30]` required for event-study market models. Sourced from Yahoo Finance.
- `calibration_points.csv`: Empirical Cumulative Abnormal Returns (CAR[-1, +2]) fitted against engine impact scores.
- `shock_seed.csv`: Statistically measured equity price drawdowns from historical events used to seed the shock transmission matrix.
- `calibration_model.json`: Fitted OLS linear model parameters (`|CAR| = 0.53% + 1.00 * impact_score`) with empirical uncertainty standard errors and quantile thresholds.

### `data/raw/`
- `gdelt/gdelt_real_pull.json`: 50 real articles fetched via live GDELT DOC 2.0 API queries covering systemic market themes (Red Sea shipping attacks, bank downgrades, tech sanctions, energy supply). Contains real public titles, URLs, and source domains.
- `gdelt/sample_gdelt_illustrative.json`: Author-curated illustrative templates explicitly marked with `is_synthetic: true` for offline testing.
- `newsapi/sample_news_illustrative.json`: Author-curated illustrative templates explicitly marked with `is_synthetic: true` used for offline demonstration when an active NewsAPI key is absent.
- `social/synthetic_posts.json`: 100 synthetic market posts covering universe tickers with realistic distributions of institutional notes, unverified rumors, and retail hype. Explicitly marked `is_synthetic: true`.
- `social/README.md`: Schema definition, engagement metrics, and classification distribution for synthetic social posts.

### `data/replay/`
- `demo_events.jsonl`: 14 hand-curated chronological scenario events powering the live simulation demo. Spans baseline news, uncorroborated rumors, and 4 major market shocks (Red Sea shipping crisis, Fitch bank downgrade, CrowdStrike IT outage, OPEC production cut). Formatted as `RawItem` records with `is_synthetic: true`.
- `README.md`: Chronological storyline, scenario narrative, and event metadata.

### `data/eval/`
- `gold.jsonl`: 25 human-annotated ground truth evaluation records for benchmarking NER entity resolution, theme classification, sentiment polarity, and impact scoring.
- `README.md`: Evaluation annotation guidelines, inter-annotator notes, and performance metric definitions.

### `data/processed/`
- `raw_items.jsonl`: Ingestion pipeline output after deduplication, content truncation, and universe entity filtering.
- `signals.jsonl`: Output of the Phase 2 risk engine containing fully structured, enriched, and validated risk signals.

### `data/cache/`
- `llm/`: Deterministic hash-keyed JSON cache files for Gemini / OpenAI extractions across the 14 replay demo events, 5 preset headlines, and 24 calibration events.
- `finbert/`: Pre-computed sentiment classifications and scores for headline phrases, enabling instant offline operation without HuggingFace model weight downloads.

---

## 3. Data Provenance & Sources

| Dataset Component | Source / Provider | Type / License | Notes |
|---|---|---|---|
| Historical Equities & ETFs | Yahoo Finance (`yfinance`) | Public Market Data | Trimmed to 400-day estimation windows around event dates |
| Macro & Financial News | GDELT DOC 2.0 API | Public News Index | Public domain / Fair use research index |
| Bank Wholesale Portfolio | Internal Synthetic Generator | Synthetic Procedural | Generated via `src.portfolio.build` (seed `20260101`) |
| Historical Calibration Shocks | Public Market History (2020–2025) | Public Financial Record | Documented in `data/calibration/events.csv` |
| Evaluation Benchmark | Human Annotation | Author-labeled Ground Truth | 25 gold-standard records in `data/eval/gold.jsonl` |
| Replay Narrative | Scenario Authoring | Synthetic Simulation | 14 chronological events in `data/replay/demo_events.jsonl` |
