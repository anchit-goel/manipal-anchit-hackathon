# Synthetic Social Dataset (`data/raw/social/synthetic_posts.json`)

## Overview & Origin
This dataset contains **100 curated synthetic social media posts** simulating financial micro-blogging feeds (e.g., FinTwit / X). It is purpose-built to test multi-source risk signal ingestion, noise mitigation, and cross-source confidence scoring.

### Dataset Assumptions & Attributes
- **Synthetic Status**: All items are explicitly marked with `"is_synthetic": true`.
- **Target Universe**: Mapped across all 20 wholesale banking counterparties in `data/universe.csv` (JPMorgan, Citigroup, Maersk, TSMC, ExxonMobil, Boeing, etc.).
- **Archetype Breakdown**:
  - **Standard Institutional Updates (40%)**: Balanced brokerage notes, debt issuance reports, and operational summaries.
  - **Unverified Rumors (25%)**: Liquidity concerns, secondary equity offering rumors, unconfirmed regulatory leaks. (Crucial for testing that low-confidence signals do not spuriously trigger portfolio shocks).
  - **Speculative Hype (25%)**: Exaggerated retail bull hype and call option speculation.
  - **High-Impact Market Events (10%)**: Red Sea transit shutdowns, sovereign counterparty default notices, and export sanction developments.
- **Engagement Metrics**: Realistic distributions of likes, retweets, and comment replies to facilitate engagement-weighted confidence modeling in later phases.
