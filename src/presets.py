"""Preset headlines for the Analyze tab. Pre-cached through the engine so they work fully offline."""
from datetime import datetime, timezone
from typing import Dict, List

from src.schemas import RawItem

MAX_TEXT_CHARS = 20_000

PRESETS: List[Dict[str, str]] = [
    {"id": "opec_cut", "label": "OPEC surprise cut",
     "text": "OPEC announces surprise 2M bpd crude production cut sending crude oil soaring 8%",
     "source": "Bloomberg", "source_type": "news"},
    {"id": "bank_downgrade", "label": "Bank downgrade",
     "text": "Fitch downgrades Bank of America long-term rating one notch citing deteriorating commercial real estate exposure and rising funding costs",
     "source": "Reuters", "source_type": "news"},
    {"id": "shipping_attack", "label": "Shipping attack",
     "text": "Drone attack hits container vessel in Red Sea as Maersk and ZIM pause Suez Canal transits indefinitely",
     "source": "Reuters", "source_type": "news"},
    {"id": "rumor", "label": "Unverified rumor",
     "text": "UNCONFIRMED: anonymous post claims Citigroup facing emergency liquidity shortfall, no sources cited",
     "source": "Social/X", "source_type": "social"},
    {"id": "product_launch", "label": "Routine product launch",
     "text": "Apple launches new colour options for its iPhone lineup at routine spring product event",
     "source": "Financial Times", "source_type": "news"},
]


def build_live_item(text: str, source: str = "Manual Live Entry", source_type: str = "news") -> RawItem:
    """Build the RawItem used by /analyze (shared with the preset pre-cache script so cache keys match)."""
    text = (text or "")[:MAX_TEXT_CHARS]
    now = datetime.now(timezone.utc)
    return RawItem(
        item_id=f"live_{int(now.timestamp() * 1000)}",
        source=source or "Manual Live Entry",
        source_type="social" if (source_type or "").lower() == "social" else "news",
        published_at=now.isoformat(),
        title=text[:120],
        text=text,
        url=None,
        author="Interactive User",
        engagement={},
        query_tag=None,
        is_synthetic=False,
    )
