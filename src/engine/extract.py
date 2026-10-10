"""Risk signal extraction prompt and structured LLM pipeline."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from src.schemas import EventClass
from src.universe import CompanyExposure, load_universe
from src.llm.client import LLMClient
from src.config import CONTROLLED_THEMES, get_logger

logger = get_logger("engine.extract")


class ExtractionResult(BaseModel):
    """Schema for LLM structured extraction output."""
    entity: str = Field(..., description="Target company or macroeconomic event name")
    ticker: Optional[str] = Field(None, description="Ticker from allowed universe or null")
    sector: Optional[str] = Field(None, description="Economic sector classification")
    country: Optional[str] = Field(None, description="Country ISO3 or name")
    themes: list[str] = Field(
        default_factory=lambda: ["none"],
        description="Controlled macro and sector risk themes (max 2)"
    )
    event_class: EventClass = Field(..., description="Categorical classification")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment in [-1, 1]")
    impact_score: float = Field(..., ge=1.0, le=10.0, description="Severity in [1, 10]")
    claim_certainty: Literal["confirmed", "reported", "rumor"] = Field(
        ..., description="Verification certainty of the claim"
    )
    rationale: str = Field(..., max_length=500, description="Brief explanation <= 30 words")
    pass2_impact: Optional[float] = Field(None, description="Impact from second consistency pass")
    impact_disagreement: Optional[float] = Field(None, description="Absolute difference between pass 1 and 2")
    model_version: Optional[str] = Field("gemini-3.5-flash", description="Extractor model version")

    @field_validator("rationale", mode="before")
    @classmethod
    def truncate_rationale(cls, v: Any) -> str:
        return str(v)[:300] if v else ""

    @field_validator("event_class", mode="before")
    @classmethod
    def normalize_event_class(cls, v: Any) -> Any:
        if isinstance(v, EventClass):
            return v
        if isinstance(v, str):
            v_clean = v.strip().lower()
            mapping = {
                "geopolitical": EventClass.GEOPOLITICAL,
                "macroeconomic": EventClass.MACROECONOMIC,
                "credit event": EventClass.CREDIT_EVENT,
                "credit": EventClass.CREDIT_EVENT,
                "merger/acquisition": EventClass.MERGER_ACQUISITION,
                "merger": EventClass.MERGER_ACQUISITION,
                "acquisition": EventClass.MERGER_ACQUISITION,
                "product launch": EventClass.PRODUCT_LAUNCH,
                "product": EventClass.PRODUCT_LAUNCH,
                "regulatory": EventClass.REGULATORY,
                "regulation": EventClass.REGULATORY,
                "other": EventClass.OTHER,
            }
            if v_clean in mapping:
                return mapping[v_clean]
            for key, val in mapping.items():
                if key in v_clean:
                    return val
        return EventClass.OTHER

    @field_validator("themes", mode="before")
    @classmethod
    def normalize_themes(cls, v: Any) -> list[str]:
        if not v:
            return ["none"]
        if isinstance(v, str):
            v = [t.strip().lower() for t in v.split(",") if t.strip()]
        valid = [t for t in v if t in CONTROLLED_THEMES]
        return valid[:2] if valid else ["none"]

    @field_validator("sentiment_score")
    @classmethod
    def clamp_sentiment(cls, v: float) -> float:
        return max(-1.0, min(1.0, round(float(v), 2)))

    @field_validator("impact_score")
    @classmethod
    def clamp_impact(cls, v: float) -> float:
        return max(1.0, min(10.0, round(float(v), 1)))


def build_system_prompt(universe: List[CompanyExposure]) -> str:
    """Build grounded system prompt with anchored rubric and few-shot examples."""
    universe_table = "\n".join(
        [f"- Ticker: {c.ticker} | Name: {c.name} | Sector: {c.sector} | Country: {c.country}" for c in universe]
    )

    return f"""You are an elite quantitative credit risk analyst and NLP intelligence engine for a tier-1 wholesale bank.
Your job is to analyze unstructured news headlines and social posts, extract structured risk signals, and predict market impact severity.

### ALLOWED TARGET UNIVERSE:
{universe_table}

GROUNDING RULES:
1. Ground entity/ticker to the ALLOWED UNIVERSE above whenever the text mentions or clearly affects one of these entities.
2. The 'ticker' field MUST be either an exact ticker from the allowed universe above, OR null. Do NOT invent tickers.
3. If an item describes a systemic, geopolitical, or macroeconomic shock without a single specific company (e.g. Red Sea shipping crisis or OPEC oil cut), set 'entity' to the descriptive event name (e.g. 'Red Sea Shipping Disruption' or 'OPEC+ Supply Cut'), set 'ticker' to null, and fill 'sector' and 'country' appropriately.

### CONTROLLED THEMES VOCABULARY (Must select 1-2 themes strictly from this set):
- shipping_disruption (e.g. Red Sea naval missile strikes, Suez transit closure)
- oil_price_up (e.g. OPEC surprise production cut, crude spikes)
- oil_price_down (e.g. crude price tumble, supply glut)
- credit_downgrade (e.g. sovereign/corporate ratings cut, negative credit watch)
- credit_default (e.g. sovereign moratorium, counterparty default, insolvency)
- banking_stress (e.g. bank liquidity crisis, repo facility pressure, bank run)
- rate_hike (e.g. central bank 75bps tightening surprise)
- rate_cut (e.g. emergency policy rate reduction)
- regulatory_action (e.g. FAA grounding order, punitive banking rule)
- antitrust (e.g. FTC/DOJ/EU competition probe, monopoly subpoena)
- chip_supply_shock (e.g. advanced semiconductor export curbs, fab outage)
- sanctions (e.g. OFAC embargo, secondary trade sanctions)
- demand_shock (e.g. pandemic travel restrictions, sharp consumer pullback)
- merger_activity (e.g. hostile mega-buyout, cross-border merger announcement)
- none (e.g. routine operational note, scheduled dividend, seasonal update)

### IMPACT SEVERITY RUBRIC (1.0 - 10.0):
- 1.0 - 2.0: Routine / Baseline news. Minor operational update, scheduled conference, seasonal refresh, standard quarterly dividend. No meaningful market reaction.
- 3.0 - 4.0: Minor company-specific event. Small commercial credit line, routine bond issuance, typical analyst upgrade/downgrade.
- 5.0 - 6.0: Notable sector or operational news. Substantial margin compression warning, localized factory safety review, multi-carrier supply chain delay.
- 7.0 - 8.0: Major risk event with likely multi-percent sector move. Formal antitrust investigation / subpoena, negative credit watch on multi-billion debt, major maritime route diversion, OPEC unexpected output cut.
- 9.0 - 10.0: Systemic crisis or catastrophic credit shock. Active military blockade of major global maritime choke point, sovereign debt moratorium, systemic counterparty default, widespread banking liquidity contagion.

RUMOR RULE:
An unverified rumor or speculation MUST score 2.0 to 3.0 points LOWER in impact_score than the exact same story if confirmed, and MUST have claim_certainty='rumor'.

SENTIMENT RULE:
sentiment_score is in [-1.0, 1.0] evaluated strictly from the perspective of the named entity's equity/credit value.

### FEW-SHOT EXAMPLES:

Example 1 (Routine / Product):
Input: "Apple updates seasonal iPad line and accessory portfolio at annual briefing."
Output:
{{"entity": "Apple Inc.", "ticker": "AAPL", "sector": "Technology", "country": "USA", "themes": ["none"], "event_class": "Product Launch", "sentiment_score": 0.20, "impact_score": 1.5, "claim_certainty": "confirmed", "rationale": "Routine consumer tablet refresh without material price or margin adjustments."}}

Example 2 (Routine / Corporate Debt):
Input: "Chevron concludes $1.5B three-year corporate paper placement at tight spread."
Output:
{{"entity": "Chevron", "ticker": "CVX", "sector": "Energy", "country": "USA", "themes": ["none"], "event_class": "Other", "sentiment_score": 0.35, "impact_score": 2.5, "claim_certainty": "confirmed", "rationale": "Standard corporate debt issuance executed at benchmark-tight spreads reflecting solid balance sheet liquidity."}}

Example 3 (Unverified Rumor - Low Certainty, Low Impact):
Input: "UNCONFIRMED RUMOR: Trader whispers claim Bank of America facing overnight repo liquidity checks on European desks."
Output:
{{"entity": "Bank of America", "ticker": "BAC", "sector": "Banking", "country": "USA", "themes": ["banking_stress"], "event_class": "Credit Event", "sentiment_score": -0.40, "impact_score": 4.5, "claim_certainty": "rumor", "rationale": "Uncorroborated social media rumor alleging liquidity friction; scored down due to lack of verification."}}

Example 4 (Confirmed High-Impact Shock - Geopolitical):
Input: "Missile strike in Bab el-Mandeb: Maersk and ZIM suspend all Red Sea maritime transit indefinitely, adding 14 days around Cape."
Output:
{{"entity": "A.P. Moller - Maersk", "ticker": "MAERSK-B.CO", "sector": "Shipping", "country": "DNK", "themes": ["shipping_disruption"], "event_class": "Geopolitical", "sentiment_score": -0.85, "impact_score": 8.8, "claim_certainty": "confirmed", "rationale": "Severe geopolitical naval threat forcing indefinite fleet diversion around Africa, spiking spot freight rates 45%."}}

Example 5 (Confirmed High-Impact Shock - Credit Event):
Input: "Citigroup placed on negative credit watch over $4.8B distressed sovereign counterparty debt exposure following debt moratorium."
Output:
{{"entity": "Citigroup", "ticker": "C", "sector": "Banking", "country": "USA", "themes": ["credit_downgrade", "credit_default"], "event_class": "Credit Event", "sentiment_score": -0.80, "impact_score": 8.2, "claim_certainty": "confirmed", "rationale": "Sovereign default moratorium jeopardizes major syndicated facilities, creating significant loan loss provisioning risk."}}

Example 6 (Regulatory Shock):
Input: "US FTC and European Commission launch joint antitrust probe into NVIDIA AI server packaging covenants."
Output:
{{"entity": "NVIDIA", "ticker": "NVDA", "sector": "Semiconductors", "country": "USA", "themes": ["antitrust", "regulatory_action"], "event_class": "Regulatory", "sentiment_score": -0.65, "impact_score": 7.5, "claim_certainty": "confirmed", "rationale": "Coordinated international antitrust scrutiny threatening multi-year customer lock-in and high-margin AI bundling covenants."}}

Example 7 (Macroeconomic Shock):
Input: "OPEC+ emergency meeting confirms surprise 1.8M bpd production cut; Brent crude spikes 6.8%."
Output:
{{"entity": "ExxonMobil", "ticker": "XOM", "sector": "Energy", "country": "USA", "themes": ["oil_price_up"], "event_class": "Macroeconomic", "sentiment_score": 0.70, "impact_score": 8.0, "claim_certainty": "confirmed", "rationale": "Unscheduled OPEC quota reduction drives substantial near-term commodity price appreciation and upstream margin expansion."}}

OUTPUT FORMAT:
Output strictly valid JSON with exact keys:
{{"entity": str, "ticker": str|null, "sector": str|null, "country": str|null, "themes": list[str], "event_class": str, "sentiment_score": float, "impact_score": float, "claim_certainty": str, "rationale": str}}
"""


class SignalExtractor:
    """Manages prompt execution, schema parsing, ticker validation, and self-consistency."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.universe: List[CompanyExposure] = load_universe()
        self.valid_tickers = {c.ticker for c in self.universe}
        self.system_prompt = build_system_prompt(self.universe)

    def extract(self, headline: str, body: str = "") -> ExtractionResult:
        """Extract structured signal metrics from text with self-consistency checks."""
        content = f"HEADLINE: {headline}\nTEXT BODY: {body}".strip()

        # Pass 1: Deterministic extraction (temperature 0.0)
        p1_dict = self.llm.complete_json(
            system=self.system_prompt,
            user=content,
            schema=ExtractionResult,
            temperature=0.0,
        )

        # Validate ticker against universe
        raw_ticker = p1_dict.get("ticker")
        if raw_ticker and raw_ticker not in self.valid_tickers:
            logger.info("Ticker '%s' not in universe. Setting to null.", raw_ticker)
            p1_dict["ticker"] = None

        res1 = ExtractionResult.model_validate(p1_dict)

        # Pass 2: Self-consistency check for notable items (impact >= 6.0)
        if res1.impact_score >= 6.0 and not self.llm.offline_mode:
            try:
                p2_dict = self.llm.complete_json(
                    system=self.system_prompt,
                    user=content,
                    schema=ExtractionResult,
                    temperature=0.7,
                )
                pass2_impact = float(p2_dict.get("impact_score", res1.impact_score))
                res1.pass2_impact = pass2_impact
                res1.impact_disagreement = round(abs(res1.impact_score - pass2_impact), 2)
            except Exception as e:
                logger.warning("Pass 2 self-consistency call skipped: %s", e)
                res1.pass2_impact = res1.impact_score
                res1.impact_disagreement = 0.0
        else:
            res1.pass2_impact = res1.impact_score
            res1.impact_disagreement = 0.0

        return res1
