"""Deterministic offline replay of stored signals through trigger logic and the stress engine."""
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config import SIGNALS_PROCESSED_FILE
from src.schemas import Signal
from src.stress.engine import load_portfolio, run_stress
from src.stress.shock_table import load_shock_table
from src.stress.trigger import _ts, evaluate_signals


def load_signals(path=None) -> List[Signal]:
    out: List[Signal] = []
    with open(path or SIGNALS_PROCESSED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(Signal.model_validate_json(line))
    return out


def build_replay(signals: List[Signal], portfolio: Optional[pd.DataFrame] = None,
                 table: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """One record per signal in time order: {signal, outcome:{type: stress_result|suppressed|merged}}."""
    pf = portfolio if portfolio is not None else load_portfolio()
    tb = table if table is not None else load_shock_table()
    scenarios, suppressed = evaluate_signals(signals)
    sup = {s.signal_id: s.reason for s in suppressed}
    lead_of = {sc.lead.signal_id: sc for sc in scenarios}
    merged_into = {cid: sc.lead.signal_id for sc in scenarios for cid in sc.corroborating_ids}

    records = []
    for sig in sorted(signals, key=_ts):
        if sig.signal_id in sup:
            outcome = {"type": "suppressed", "signal_id": sig.signal_id, "reason": sup[sig.signal_id]}
        elif sig.signal_id in lead_of:
            sc = lead_of[sig.signal_id]
            res = run_stress(sig, pf, tb)
            res.corroborating_signal_ids = sc.corroborating_ids
            outcome = {"type": "stress_result", "result": res.model_dump(mode="json")}
        else:
            outcome = {"type": "merged", "signal_id": sig.signal_id, "into": merged_into.get(sig.signal_id),
                       "reason": "same theme within 48h merged into existing scenario"}
        records.append({"signal": sig.model_dump(mode="json"), "outcome": outcome})
    return records
