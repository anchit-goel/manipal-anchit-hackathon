"""Pydantic v2 data models and schemas for Signal-to-Shock."""
from enum import Enum
from typing import Literal, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SourceType(str, Enum):
    """Permitted ingestion source types."""
    NEWS = "news"
    SOCIAL = "social"


class EventClass(str, Enum):
    """Categorical classification of market and counterparty events."""
    GEOPOLITICAL = "Geopolitical"
    MACROECONOMIC = "Macroeconomic"
    CREDIT_EVENT = "Credit Event"
    MERGER_ACQUISITION = "Merger/Acquisition"
    PRODUCT_LAUNCH = "Product Launch"
    REGULATORY = "Regulatory"
    OTHER = "Other"


class RawItem(BaseModel):
    """Normalized ingested content item from news or social feeds."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    item_id: str = Field(..., description="Unique deterministic hash or source ID")
    source: str = Field(..., description="Provider name e.g. NewsAPI, GDELT, X/Twitter")
    source_type: Literal["news", "social"] = Field(..., description="Ingested source channel")
    published_at: str = Field(..., description="ISO 8601 published timestamp")
    title: str = Field(..., description="Article title or post summary")
    text: str = Field(..., description="Full text body or snippet")
    url: Optional[str] = Field(None, description="Source URL or canonical link")
    author: Optional[str] = Field(None, description="Author or publisher entity")
    engagement: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Engagement metrics e.g. likes, shares, retweets"
    )
    query_tag: Optional[str] = Field(None, description="Query keyword or ticker searched")
    is_synthetic: bool = Field(False, description="Flag indicating synthetic demonstration data")

    @field_validator("title", "text")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class Signal(BaseModel):
    """Structured risk signal consumed by downstream stress-testing modules."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    signal_id: str = Field(..., description="Unique signal identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp of signal extraction")
    source: str = Field(..., description="Source origin e.g. GDELT, NewsAPI, Social")
    source_type: Literal["news", "social"] = Field(..., description="Channel type")
    headline: str = Field(..., description="Cleaned headline describing the risk event")
    entity: str = Field(..., description="Primary company or institution name")
    ticker: Optional[str] = Field(None, description="Market ticker symbol e.g. JPM, NVDA")
    sector: Optional[str] = Field(None, description="Economic sector classification")
    country: Optional[str] = Field(None, description="Primary geographic domicile")
    sentiment_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment intensity score bounded in [-1.0, 1.0]"
    )
    event_class: EventClass = Field(..., description="Categorical event classification")
    impact_score: float = Field(
        ...,
        ge=1.0,
        le=10.0,
        description="Predicted market impact severity on a scale of 1 to 10"
    )
    calibrated_move_pct: Optional[float] = Field(
        None,
        description="Empirically calibrated expected asset/sector move percentage"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Signal confidence score based on corroboration and model checks"
    )
    rationale: str = Field(..., description="Chain of thought explanation for impact & class")
    model_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Version tags of NLP models and LLM extractors used"
    )
