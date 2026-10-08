# Demo Replay Dataset (`data/replay/demo_events.jsonl`)

## 1. Purpose & Guarantees
The replay dataset provides a **100% deterministic, offline-capable event timeline** designed for hackathon demonstrations, automated unit testing, and reproducible stress test evaluations.

In accordance with hackathon rules:
- **Zero Confidential / Proprietary Data**: All events and texts are synthetic and original illustrations constructed for this project. No proprietary S&P/CRISIL data or copyright-encumbered news bodies are included.
- **Strict Schema Adherence**: Every row conforms to the Pydantic v2 `RawItem` schema.
- **Offline Self-Containment**: Total dataset size is under 15 KB, requiring no network or external API access.

---

## 2. Chronological Demo Storyline Breakdown

| Item ID | Source Type | Entity / Ticker | Event Narrative & Category | Expected Engine Response |
| :--- | :--- | :--- | :--- | :--- |
| `replay_001` | News | Apple (`AAPL`) | Routine product refresh and seasonal iPad announcement. | **Calm / Low Impact**: Impact ~1-2, Sentiment neutral-positive. No stress test. |
| `replay_002` | News | Microsoft (`MSFT`) | Nordic cloud data center capacity expansion. | **Calm / Low Impact**: Impact ~2, Sentiment positive. No stress test. |
| `replay_003` | Social | Toyota (`TM`) | Resilient hybrid delivery backlogs. | **Calm / Low Impact**: Impact ~2, Sentiment positive. |
| `replay_004` | News | Chevron (`CVX`) | Successful $1.5B 3-year commercial debt issuance. | **Calm / Low Impact**: Impact ~2-3, Credit stable. |
| `replay_005` | Social | Bank of America (`BAC`) | **Unverified Rumor**: Whispers of overnight repo margin collateral squeeze. | **Noise Mitigation**: High severity text but low confidence (<0.35) due to unverified social origin and lack of news corroboration. **Stress test suppressed**. |
| `replay_006` | Social | TSMC (`TSM`) | **Unverified Rumor**: Alleged power glitch at Fab 18. | **Noise Mitigation**: Low confidence. No stress test. |
| `replay_007` | Social | NVIDIA (`NVDA`) | **Speculative Hype**: Exaggerated stock split & call option pump. | **Noise Mitigation**: Filtered out as speculative noise. |
| `replay_008` | News | Maersk (`MAERSK-B.CO`) | **High-Impact Shock (Geopolitical)**: Red Sea missile strike halts Bab el-Mandeb transit; freight rates spike 45%. | **HIGH-IMPACT TRIGGER**: Impact 8.5-9.0, Confidence high (>0.85). Triggers Shipping & Supply Chain stress shocks. |
| `replay_009` | News | ZIM Shipping (`ZIM`) | **Corroborating Event**: Baltic Exchange reports 70% Suez container drop. | **Cross-Source Corroboration**: Bolsters confidence of shipping disruption signal. |
| `replay_010` | News | Citigroup (`C`) | **High-Impact Shock (Credit Event)**: $4.8B sovereign borrower default moratorium puts Citi loans on negative credit watch. | **HIGH-IMPACT TRIGGER**: Impact 8.0, Triggers Wholesale Banking Loan & Counterparty default stress shocks. |
| `replay_011` | News | NVIDIA (`NVDA`) | **High-Impact Shock (Regulatory)**: US FTC & EU launch joint antitrust monopolization probe into AI bundling. | **HIGH-IMPACT TRIGGER**: Impact 7.5, Triggers Semiconductor & Tech Equity shocks. |
| `replay_012` | News | ExxonMobil (`XOM`) | **High-Impact Shock (Macroeconomic)**: OPEC+ surprise 1.8M bpd cut; crude spikes 6.8%. | **HIGH-IMPACT TRIGGER**: Impact 8.0, Shocks Energy Equities (+) and Airline/Transport liabilities (-). |
| `replay_013` | News | Delta Air Lines (`DAL`) | **Second-Order Impact**: Jet fuel margin compression warning following crude surge. | Demonstrates cross-sector shock propagation. |
| `replay_014` | Social | JPMorgan (`JPM`) | Federal Reserve repo liquidity operations confirm normal interbank settlements. | **Resolution & Recovery**: Sentiment stabilization. |
