# Evaluation Benchmark Dataset (`data/eval/gold.jsonl`)

## Overview & Origin
This dataset contains **25 curated benchmark items** constructed from the demonstration replay stream and real GDELT DOC 2.0 articles.

### Labeling Methodology & Author Disclosure
- **Author-Assigned Ground Truth**: All gold standard labels (`gold_class`, `gold_sentiment_sign`, `gold_impact`) were assigned by the candidate following standard quantitative risk assessment guidelines.
- **Categorical Event Classification**: Grounded against the seven canonical case study event classes: `Geopolitical`, `Macroeconomic`, `Credit Event`, `Merger/Acquisition`, `Product Launch`, `Regulatory`, and `Other`.
- **Sentiment Sign**: Directional sign of entity market value impact:
  - `+1`: Value-accretive / credit strengthening (earnings expansion, capital buffer, credit facility)
  - `-1`: Value-dilutive / credit deteriorating (moratorium, antitrust probe, military strike, margin compression)
- **Impact Severity Scale (1.0 - 10.0)**:
  Calibrated against empirical market moves:
  - 1.0 - 3.0: Baseline/Routine (e.g. tablet refresh, standard commercial paper)
  - 4.0 - 5.5: Notable / Moderate (e.g. rumors, capacity utilization, inspection reports)
  - 6.0 - 7.5: High / Sector-moving (e.g. antitrust probe, cross-border M&A veto)
  - 8.0 - 10.0: Systemic / Severe Shock (e.g. Red Sea naval blockade, sovereign debt moratorium, OPEC emergency cut)
