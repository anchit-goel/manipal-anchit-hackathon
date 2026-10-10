"""Trigger logic: eligibility, suppression reasons, and 48h same-theme debounce into scenarios."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from src.config import DEBOUNCE_HOURS, TRIGGER_CONFIDENCE_THRESHOLD, TRIGGER_IMPACT_THRESHOLD
from src.schemas import Signal


@dataclass
class Scenario:
    lead: Signal
    theme: str
    start: datetime
    corroborating_ids: List[str] = field(default_factory=list)


@dataclass
class Suppressed:
    signal_id: str
    reason: str


def _ts(sig: Signal) -> datetime:
    return datetime.fromisoformat(sig.timestamp.replace("Z", "+00:00"))


def suppression_reason(sig: Signal) -> Optional[str]:
    """None if the signal may trigger on its own; otherwise a human-readable reason."""
    reasons = []
    if sig.impact_score <= TRIGGER_IMPACT_THRESHOLD:
        reasons.append(f"impact {sig.impact_score:.1f} <= {TRIGGER_IMPACT_THRESHOLD:g} threshold")
    if sig.confidence < TRIGGER_CONFIDENCE_THRESHOLD:
        reasons.append(f"confidence {sig.confidence:.2f} < {TRIGGER_CONFIDENCE_THRESHOLD:g} threshold (rumor/uncorroborated)")
    if not reasons and not [t for t in sig.themes if t != "none"]:
        reasons.append("no actionable risk theme mapped")
    return "; ".join(reasons) or None


def evaluate_signals(signals: List[Signal]) -> Tuple[List[Scenario], List[Suppressed]]:
    """Split signals into debounced scenarios and suppressed records (chronological)."""
    scenarios: List[Scenario] = []
    suppressed: List[Suppressed] = []
    open_by_theme: Dict[str, Scenario] = {}
    for sig in sorted(signals, key=_ts):
        reason = suppression_reason(sig)
        if reason:
            suppressed.append(Suppressed(sig.signal_id, reason))
            continue
        theme = [t for t in sig.themes if t != "none"][0]
        sc = open_by_theme.get(theme)
        if sc and _ts(sig) - sc.start <= timedelta(hours=DEBOUNCE_HOURS):
            if sig.impact_score > sc.lead.impact_score:
                sc.corroborating_ids.append(sc.lead.signal_id)
                sc.lead = sig
            else:
                sc.corroborating_ids.append(sig.signal_id)
            continue
        sc = Scenario(lead=sig, theme=theme, start=_ts(sig))
        open_by_theme[theme] = sc
        scenarios.append(sc)
    return scenarios, suppressed
