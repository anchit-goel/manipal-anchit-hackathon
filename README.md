# Signal-to-Shock: AI/NLP Risk Engine & Wholesale Portfolio Stress Testing

**S&P Global & CRISIL Campus Hackathon 2026**

---

### Candidate Information
- **Candidate Name**: Anchit Goel
- **College**: Manipal Academy of Higher Education (MAHE)
- **College Email**: anchit.goel@learner.manipal.edu
- **Demo Video Link**: [YouTube / Drive Demo Link (Pending Final Phase Recording)]

---

## 1. Project Overview
**Signal-to-Shock** is an end-to-end institutional-grade AI/NLP risk intelligence platform designed for wholesale banking risk desks. The engine ingests unstructured, multi-modal market narrative streams across financial news and social chatter, extracts structured event signals with validated confidence bounds, and dynamically triggers an exposure-aware stress testing module on a synthetic wholesale-banking balance sheet (loans, bonds, derivatives, equities).

Key technical differentiators include:
1. **Calibrated Impact**: Maps impact scores ($1-10$) to historical abnormal asset moves ($\Delta\%$) using benchmark-adjusted sector returns.
2. **Exposure-Aware Stress Testing**: Granular shock propagation matrix indexed across event classes, asset types, country risks, and sector vectors.
3. **Multi-Factor Confidence**: Incorporates source reliability, cross-source corroboration, and semantic consistency ($[0.0, 1.0]$) to protect risk managers from noisy rumors.
4. **Deterministic Replay & Offline Resilience**: Fully functional without active network access via structured local caches and curated historical replay streams.

---

## 2. Architecture & Tech Stack
```
┌─────────────────────────────────┐
│   Multi-Source Ingestion Feed   │
│  (NewsAPI + GDELT + Social/X)   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│    Offline Cache & Normalizer   │
│   (Pydantic v2 RawItem Models)  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     Entity Matching Universe    │
│  (Counterparties, Banks, Tickers)│
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     AI/NLP Extraction Core      │
│ (FinBERT Sentiment + LLM JSON)  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Calibrated Impact & Confidence │
│   (Empirical Abnormal Returns)  │
└────────────────┬────────────────┘
                 │ High-Impact Filter (Impact > 7)
                 ▼
┌─────────────────────────────────┐
│   Wholesale Portfolio Engine    │
│  (Stress Shocks & PnL Deltas)   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     FastAPI + Streamlit UI      │
│  (Interactive Risk Dashboards)  │
└─────────────────────────────────┘
```

- **Runtime & Language**: Python 3.11+ / macOS arm64 & Linux x86_64 compatible
- **Data Validation & Schemas**: Pydantic v2
- **Backend & APIs**: FastAPI, Uvicorn
- **UI & Visualization**: Streamlit, Plotly
- **Analytics & Data Processing**: pandas, numpy, yfinance
- **Testing**: pytest

---

## 3. Dataset Used
All datasets are stored in `/data`, strictly formatted under lightweight JSON/CSV formats (< 10 MB total) with zero proprietary/confidential data:
1. **Target Universe (`data/universe.csv`)**: 20 major systemic wholesale banking counterparties across Banking, Energy, Tech/Semiconductors, Shipping/Logistics, Aerospace, and Automotive sectors with ticker, aliases, country, and sector ETF mappings.
2. **Curated Historical Replay Dataset (`data/replay/demo_events.jsonl`)**: Curated chronological market event sequence containing baseline market updates, noisy unverified social rumors, and high-severity macro/geopolitical shocks.
3. **Synthetic Social Feed (`data/raw/social/synthetic_posts.json`)**: 100 labeled synthetic market posts simulating institutional and retail sentiment chatter, explicitly tagged with `is_synthetic=True`.
4. **Cached News Feeds (`data/raw/newsapi/`, `data/raw/gdelt/`, `data/cache/`)**: Normalized news snapshots cached for offline execution.

---

## 4. Quickstart & Installation

### System Requirements
- OS: macOS (Apple Silicon / Intel) or Linux (Ubuntu 22.04+)
- Python: 3.11+

### Installation & Execution (Single-Command Run)
```bash
# 1. Clone repository
git clone https://github.com/anchitgoel/manipal-anchit-hackathon.git
cd manipal-anchit-hackathon

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Environment variables (optional - defaults to offline mode if unset)
cp .env.example .env

# 4. Run Phase 1 Ingestion Pipeline
python -m src.ingest.pipeline --offline --days 7

# 5. Run Unit Tests
pytest tests/ -v
```

---

## 5. Key Results & Domain Impact
- **Deterministic Risk Pipeline**: Successfully processes and filters unstructured raw inputs into validated Pydantic schemas within <50ms per item offline.
- **Noise Mitigation**: Low-confidence social rumors are captured but prevented from automatically propagating to stress test triggers.
- **Institutional Wholesale Applicability**: Direct translation of macro and counterparty headlines into calibrated credit and equity portfolio shocks.
