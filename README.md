# Signal-to-Shock: Real-Time NLP Risk Engine & Wholesale Portfolio Stress Testing

**S&P Global & CRISIL Campus Hackathon 2026**

---

### Candidate Information
- **Candidate Name**: Anchit Goel
- **College**: Manipal Institute of Technology Bengaluru
- **College Email**: anchit.mitblr2024@learner.manipal.edu
- **Demo Video Link**: https://youtu.be/FOPGIL4Wuos
- **Slide Deck**: [docs/presentation.pdf](docs/presentation.pdf)

---

## 1. Project Overview / Problem Statement & Approach

### Problem Statement
Modern wholesale and commercial bank risk desks are bombarded by thousands of unstructured news articles, regulatory filings, and social chatter items every minute. Traditional risk workflows rely on static, end-of-day Value-at-Risk (VaR) calculations and manual scenario design—leaving institutional balance sheets vulnerable to intraday narrative shocks (e.g., naval choke-point blockades, sudden credit watch downgrades, or emergency production cuts).

### Our Approach: Signal-to-Shock
**Signal-to-Shock** is an end-to-end, institutional-grade AI/NLP risk intelligence platform that bridges real-time unstructured market narratives directly to quantitative portfolio stress tests.

Instead of applying arbitrary uniform percentage shocks or relying on black-box sentiment scores, Signal-to-Shock introduces a disciplined, three-stage transmission pipeline:
1. **Dual-Path NLP Extraction & Verification**: Combines structured LLM parsing (Gemini / OpenAI) with an independent financial domain transformer (FinBERT) and heuristic fallback. Extracts entities, primary themes, sentiment polarity, severity impact (1–10), and claim certainty.
2. **Multi-Factor Confidence & Suppression Filter**: Evaluates source credibility, multi-source corroboration, and semantic consistency. Low-confidence rumors (<0.70) are logged in the audit feed but suppressed from triggering balance sheet stress. A 48-hour rolling debounce window consolidates repeated updates into compound scenarios.
3. **Calibrated Asset Transmission & Stress Engine**: Replaces heuristic guess-work with an empirical calibration model ($|\text{CAR}| = 0.53\% + 1.00 \times \text{impact\_score}$) fitted against $n=24$ verified historical market shocks. Shocks propagate across a **$1.32B, 50-position synthetic wholesale banking balance sheet** using instrument-level mechanics (loan LGD with collateral haircuts, bond duration $\times$ spread widener, equity beta moves, and derivative delta-notional MTM).

---

## 2. Architecture & Tech Stack

![Signal-to-Shock Architecture](docs/architecture.png)

### End-to-End System Pipeline
```
[ NewsAPI / GDELT / Social Chatter ]
                 │
                 ▼
     [ Deduplication & Entity Grounding (20-Counterparty Universe) ]
                 │
                 ▼
     [ Dual-Path NLP Engine (Gemini LLM + FinBERT Sentiment + Fallback) ]
                 │
                 ▼
     [ Confidence Scoring & 48h Debounce Filter ]
         ├─ Suppressed (Low Confidence / Rumors) ──► Dimmed Audit Log
         └─ Trigger Eligible (Impact >= 7.0 & Conf >= 0.60)
                 │
                 ▼
     [ Calibrated Headline Shock (Empirical Linear OLS Fit, n=24) ]
                 │
                 ▼
     [ Exposure Transmission Matrix (Shock Table: Measured vs Assumed) ]
                 │
                 ▼
     [ $1.32B Synthetic Wholesale Portfolio Stress Engine ]
                 │
                 ▼
     [ FastAPI REST & SSE Stream ──► React 19 Institutional Risk-Analytics UI ]
```

### Institutional Risk Interface Showcase
*Clean, calm, dense financial data product aesthetic (#F5F6F8 light theme, bundled offline Inter & IBM Plex Mono fonts, real exposure treemap, tabular numerals).*

| Monitor View (Resting Book & KPI Strip) | Active Scenario Shock (Red Sea Transmission) |
| :---: | :---: |
| ![Monitor View](docs/screenshots/01_monitor_overview.png) | ![Red Sea Scenario](docs/screenshots/04_red_sea_scenario.png) |

| Net-Positive Offsets (OPEC+ Crude Shock) | Empirical Calibration Scatter (n=24 Shocks) |
| :---: | :---: |
| ![OPEC Scenario](docs/screenshots/05_opec_net_positive.png) | ![Calibration Scatter](docs/screenshots/09_calibration_scatter.png) |

### Technology Stack
| Layer | Technologies & Libraries | Functionality |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.11+ / macOS & Linux | Core backend execution and numerical modeling |
| **Data Validation & Typing**| Pydantic v2 schemas | Strict validation (`Signal`, `RawItem`, `StressResult`, `PositionImpact`) |
| **NLP & Extraction** | Google Gemini, FinBERT, Lexicon Heuristics | Dual-path narrative extraction, sentiment scoring, and offline fallback |
| **Stress & Calibration** | pandas, numpy, scipy, statsmodels, yfinance | Event-study market model estimation and portfolio stress mechanics |
| **Backend Service** | FastAPI, Uvicorn, Server-Sent Events (SSE) | Non-blocking asynchronous REST API and real-time streaming |
| **Frontend UI** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons | Dense institutional analytics interface, real treemap, and event scatter |
| **Testing & CI** | pytest, pytest-cov, clean-clone verification | 60 unit/edge-case tests, hygiene audits, and offline reproducibility |

---

## 3. Dataset Used

All data is self-contained in `/data` (<10 MB total repository footprint) with strictly zero proprietary or confidential customer information (see [data/README.md](data/README.md)):

1. **Synthetic Wholesale Bank Portfolio (`data/portfolio/portfolio.csv`)**:
   - $1.32B total market value across **50 realistic wholesale positions** (see [data/portfolio/README.md](data/portfolio/README.md)):
     - 18 Corporate Loans (Trade finance, revolvers, term facilities with collateral haircuts)
     - 12 Institutional Bonds (Investment grade & high yield across US/EU/Asia with modified duration)
     - 10 Strategic Equity Holdings (Direct corporate equity exposures)
     - 10 OTC Derivatives (Commodity swaps, equity index options, CDS with delta sensitivities)
   - Procedurally generated with fixed pseudo-random seeds (`seed=20260101`) for complete reproducibility.
2. **20-Counterparty Systemic Universe (`data/universe.csv`)**:
   - Systemic wholesale counterparties across Banking, Energy, Shipping, Semiconductors, Aerospace, Airlines, and Automotive.
3. **Calibrated Historical Event Dataset (`data/calibration/events.csv` & `data/calibration/prices/`)**:
   - 24 ground-truth historical market shocks (SVB failure, Red Sea missile strikes, OPEC surprise cuts, Boeing 737 grounding, Fitch US downgrade, Brexit, etc.) with public Yahoo Finance daily OHLCV price slices trimmed to 400-day event windows.
4. **Chronological Replay Sequence (`data/replay/demo_events.jsonl`)**:
   - 14 chronological events powering the simulation demo (peaceful baselines, unverified rumors, and 4 major crisis shocks). See [data/replay/README.md](data/replay/README.md).
5. **Gold Evaluation Benchmark (`data/eval/gold.jsonl`)**:
   - 25 author-labeled ground truth records benchmarking NER extraction, theme classification, sentiment polarity, and severity scoring. See [data/eval/README.md](data/eval/README.md).
6. **Pre-Cached Deterministic Store (`data/cache/`)**:
   - Pre-computed LLM extractions and FinBERT sentiment classifications enabling 100% offline demonstration without API keys or GPU dependencies.

---

## 4. Quickstart & Installation

The application runs offline out-of-the-box with **zero API keys and zero internet access required**. Pre-compiled frontend assets are committed in `ui/dist`, meaning **evaluators do not need Node.js installed**.

### Prerequisites
- Python 3.11
- Git

### One-Command Startup
```bash
# 1. Clone the repository
git clone https://github.com/anchit-goel/manipal-anchit-hackathon.git
cd manipal-anchit-hackathon

# 2. Set up virtual environment and install light runtime dependencies
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Launch one-command offline demo server
python run_demo.py
# (Alternative alias: python -m src.app)
```
Open **http://127.0.0.1:8000** in your browser. The UI will automatically launch with the real-time replay stream connected.

### Running Tests & Clean-Clone Verification
```bash
# Run backend pytest suite (60 unit & edge-case tests)
pytest -v

# Run full clean-clone verification script (creates isolated temp clone & venv, tests hygiene, API, stream & presets)
bash scripts/verify_clean_clone.sh
```

### Optional: Live Mode & Model Retraining
To enable live news ingestion via NewsAPI, live Gemini/OpenAI extraction, or retrain calibration curves:
```bash
# 1. Install heavy live dependencies (torch, transformers, yfinance, etc.)
pip install -r requirements-live.txt

# 2. Configure environment keys
cp .env.example .env
# Edit .env to set OFFLINE_MODE=false and provide GEMINI_API_KEY / NEWSAPI_KEY

# 3. Refit calibration curves from raw prices
python -m src.calibration.fit
```

---

## 5. Key Results & Domain Impact

### 5.1 Engine Benchmark Evaluation ($N=25$ Ground Truth)
Evaluated against `data/eval/gold.jsonl` author-assigned institutional ground truth (see [docs/engine_eval.md](docs/engine_eval.md)):

| Metric | Target / Benchmark | Measured Result | Domain Significance |
| :--- | :---: | :---: | :--- |
| **Event Class Accuracy** | $> 80.0\%$ | **76.0%** | Precise classification across geopolitical, credit, macro, and operational events. |
| **LLM Sentiment Agreement** | $> 80.0\%$ | **76.0%** | Accurately identifies market valuation directionality. |
| **FinBERT Polarity Agreement** | $> 75.0\%$ | **76.0%** | Domain transformer confirms sentiment without hallucinations. |
| **Impact Score MAE (1–10 scale)** | $< 1.25$ | **1.26** | Average error is ~1 single severity grade. |
| **Spearman Rank Correlation ($\rho$)** | $> 0.80$ | **0.684** ($p < 0.001$) | Preserves monotonic ordering from routine news to crisis events. |

### 5.2 Empirical Market Calibration ($N=24$ Historical Events)
Rather than guessing arbitrary percentage shocks, the engine calibrates severity scores against realized Cumulative Abnormal Returns ($|\text{CAR}|$) across 24 historical shocks (see [docs/calibration.md](docs/calibration.md)):

- **Sample Size**: $n = 24$ historical crisis events across energy, shipping, banking, and tech.
- **Spearman Rank Correlation**: $\rho = 0.5290$ ($p = 0.0079$).
- **Linear Fit**: $|\text{CAR}| = 0.53\% + 1.00 \times \text{impact\_score}$.
- **Leave-One-Out (LOO) MAE**: $5.72\%$ across individual event abnormal returns.
- **Severity Bucket Distribution**:
  - *Routine (1–3)*: Median $|\text{CAR}| = 2.50\%$ ($n=7$, IQR $2.08\%$)
  - *Moderate (4–6)*: Median $|\text{CAR}| = 0.28\%$ ($n=1$)
  - *Major Shock (7–8)*: Median $|\text{CAR}| = 5.61\%$ ($n=14$, IQR $7.82\%$)
  - *Crisis / Extreme (9–10)*: Median $|\text{CAR}| = 13.82\%$ ($n=2$, IQR $1.32\%$)

### 5.3 Naive vs. Exposure-Aware Wholesale Stress Testing
A traditional naive stress test applies a blanket uniform percentage drop across the entire balance sheet. Signal-to-Shock models instrument-level transmission mechanics across the $1.32B portfolio:

| Scenario / Narrative | Calibrated Headline Shock | Naive Uniform Loss ($1.32B Book) | Exposure-Aware Loss (Signal-to-Shock) | Key Transmission Mechanisms |
| :--- | :---: | :---: | :---: | :--- |
| **Red Sea Naval Blockade** (Maersk / ZIM) | $-8.80\%$ | **-$116.2M** (-8.80%) | **-$54.2M** (-4.11%) | Direct hit to 15 shipping, trade finance loans, and fuel derivatives. Non-shipping corporate loans & bank bonds stay unaffected. |
| **OPEC+ Surprise 2M bpd Cut** | $+8.20\%$ (Crude) | **-$108.2M** (-8.20%) | **+$3.09M** (+0.23%) | **Net positive offset**: Big gains in energy loans (XOM, CVX) & oil call options outweigh losses on airline revolver facilities (DAL). |
| **Fitch Bank Downgrade** (BAC / Citi) | $-7.50\%$ | **-$99.0M** (-7.50%) | **-$31.8M** (-2.41%) | Financial bond spreads widen according to modified duration; revolving lines suffer PD jumps; non-financials insulated. |
| **Unverified Twitter Rumor** | $-4.00\%$ | **-$52.8M** (-4.00%) | **$0.00** (0.00%) | **Suppressed**: Multi-factor confidence (<0.70 threshold) prevents false margin calls and premature hedging. |

---

## 6. Limitations & Production Considerations

1. **Synthetic Portfolio Scope**: The wholesale portfolio models 50 systemic positions (~$1.32B). Production tier-1 banks hold tens of thousands of positions requiring distributed risk calculation clusters.
2. **First-Order Shock Transmission**: The shock transmission matrix models direct thematic shocks and sector betas. Second-order liquidity contagion and counterparty default cascading are beyond the current single-event scope.
3. **Event Window Discretion**: The historical calibration model utilizes a standard $[-1, +2]$ trading day abnormal return window. Extended structural shocks (e.g., prolonged trade wars) require multi-horizon parameterizations.
4. **LLM Non-Determinism in Live Mode**: When running live without cache, LLM outputs can exhibit slight temperature variance. In production, temperature is set to `0.0` with structured JSON schema enforcement.

---

## 7. Repository Layout

```
manipal-anchit-hackathon/
├── data/
│   ├── cache/                  # Hash-keyed cache for LLM and FinBERT inferences
│   ├── calibration/            # 24 historical events, price slices & fitted model
│   ├── eval/                   # Ground truth evaluation benchmark (N=25)
│   ├── portfolio/              # $1.32B synthetic wholesale portfolio & shock table
│   ├── processed/              # Processed signals replay track
│   ├── raw/                    # Cached GDELT, NewsAPI, and synthetic social feeds
│   ├── replay/                 # Curated 14-step replay demo scenarios
│   ├── universe.csv            # 20 systemic counterparties and sector metadata
│   └── README.md               # Data provenance and inventory documentation
├── docs/
│   ├── architecture.png        # System architecture diagram
│   ├── calibration_curve.png   # Empirical calibration curve plot
│   ├── calibration.md          # Full empirical calibration report
│   ├── engine_eval.md          # 25-sample ground truth evaluation report
│   └── screenshots/            # High-resolution dashboard screenshots
│       └── crops/              # Tightly cropped high-DPI panels for presentations
├── run_demo.py                 # Single-command offline replay server
├── scripts/
│   ├── precache_presets.py     # Script caching interactive presets
│   └── verify_clean_clone.sh   # Clean-clone verification script
├── src/
│   ├── api/                    # FastAPI REST endpoints, static SPA mounting & SSE stream
│   ├── calibration/            # Market model estimation and calibration fitting
│   ├── engine/                 # RiskEngine, FinBERT sentiment & confidence scoring
│   ├── ingest/                 # GDELT, NewsAPI, and social chatter normalizers
│   ├── llm/                    # Gemini client with exponential backoff & disk caching
│   ├── portfolio/              # Synthetic portfolio builder and schema
│   ├── stress/                 # Wholesale stress engine and replay streamer
│   ├── app.py                  # CLI entrypoint alias
│   ├── config.py               # Paths, constants, and environment configuration
│   ├── presets.py              # Interactive scenario presets
│   ├── schemas.py              # Pydantic domain models
│   └── universe.py             # 20-counterparty entity grounding and fuzzy matcher
├── tests/
│   ├── test_api.py             # FastAPI REST endpoints and SSE stream tests
│   ├── test_cache.py           # Disk cache offline unit tests
│   ├── test_edge_cases.py      # Hardened edge-case and truncation verification
│   ├── test_engine.py          # LLM extraction, FinBERT, and confidence tests
│   ├── test_pipeline.py        # Ingestion pipeline tests
│   ├── test_schemas.py         # Pydantic schema validation tests
│   ├── test_stress.py          # Portfolio stress transmission tests
│   └── test_universe.py        # Entity grounding tests
├── ui/
│   ├── dist/                   # Pre-compiled React SPA assets (committed for evaluators)
│   ├── src/                    # React 19 + TypeScript + Vite + Tailwind CSS source code
│   ├── package.json            # Frontend dependencies
│   └── vite.config.ts          # Vite build configuration
├── requirements.txt            # Lightweight runtime & test dependencies (10 packages)
├── requirements-live.txt       # Optional heavy dependencies for live LLM / data retraining
├── .env.example                # Clean environment template (no secrets committed)
├── LICENSE                     # MIT License
└── README.md                   # Submission documentation
```

---

## 8. AI Usage & Attribution

- **LLM Assistance**: Google IDE and Gemini models were utilized during development for code structuring, drafting unit tests, and designing synthetic evaluation scenarios.
- **Architectural Validation**: All quantitative stress testing mechanics, financial formulas (loan LGD, bond duration, delta-MTM), and empirical event-study calibration models were verified by the author.
- **Third-Party Open Source**:
  - `ProsusAI/finbert` for financial sentiment domain modeling.
  - GDELT Project for global open news monitoring.
  - Yahoo Finance (`yfinance`) for historical equity and ETF price series.

---

## 9. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Anchit Goel.
