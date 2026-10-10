"""FastAPI risk signal service exposing REST endpoints for downstream consumption."""
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import (
    API_PORT,
    OFFLINE_MODE,
    SIGNALS_PROCESSED_FILE,
    get_logger,
)
from src.schemas import EventClass, RawItem, Signal
from src.engine.run import RiskEngine

logger = get_logger("api.main")

app = FastAPI(
    title="Signal-to-Shock Risk API",
    description="Institutional AI/NLP Risk Engine delivering structured risk signals and stress test triggers.",
    version="1.0.0",
)

# Enable CORS for Streamlit dashboard and cross-origin clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared RiskEngine instance for /analyze
engine = RiskEngine()


def read_all_signals(filepath: Optional[Path] = None) -> List[Signal]:
    """Read all persisted signals from JSONL file."""
    target_file = filepath or SIGNALS_PROCESSED_FILE
    if not target_file.exists():
        return []

    signals: List[Signal] = []
    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signals.append(Signal.model_validate_json(line))
            except Exception as e:
                logger.warning("Error deserializing signal: %s", e)
    return signals


class AnalyzeRequest(BaseModel):
    """Payload for on-demand text analysis."""
    text: str = Field(..., min_length=5, description="Headline or paragraph to analyze")
    source: Optional[str] = Field("Manual Live Entry", description="Provider label")
    source_type: Optional[str] = Field("news", description="'news' or 'social'")


@app.get("/health")
def health_check():
    """Health check endpoint indicating service status and operation mode."""
    return {
        "status": "ok",
        "service": "Signal-to-Shock Risk Engine",
        "offline_mode": OFFLINE_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/signals", response_model=List[Signal])
def get_signals(
    ticker: Optional[str] = Query(None, description="Filter by company ticker symbol"),
    event_class: Optional[EventClass] = Query(None, description="Filter by EventClass"),
    min_impact: Optional[float] = Query(None, ge=1.0, le=10.0, description="Minimum impact severity"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    since: Optional[str] = Query(None, description="ISO timestamp filter (gte)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum signals returned"),
):
    """Retrieve structured signals with multi-dimensional filtering."""
    signals = read_all_signals()

    filtered = []
    for s in signals:
        if ticker and (not s.ticker or s.ticker.upper() != ticker.upper()):
            continue
        if event_class and s.event_class != event_class:
            continue
        if min_impact is not None and s.impact_score < min_impact:
            continue
        if min_confidence is not None and s.confidence < min_confidence:
            continue
        if since and s.timestamp < since:
            continue
        filtered.append(s)

    return filtered[:limit]


@app.get("/signals/triggers", response_model=List[Signal])
def get_trigger_signals():
    """Retrieve high-severity signals qualified to trigger downstream stress tests."""
    signals = read_all_signals()
    return [s for s in signals if s.trigger_eligible]


@app.get("/signals/{signal_id}", response_model=Signal)
def get_signal_by_id(signal_id: str):
    """Retrieve a single signal by its unique identifier."""
    signals = read_all_signals()
    for s in signals:
        if s.signal_id == signal_id:
            return s
    raise HTTPException(status_code=404, detail=f"Signal with id '{signal_id}' not found")


@app.post("/analyze", response_model=Signal)
def analyze_text(request: AnalyzeRequest):
    """Analyze custom text in real time and return a validated Signal."""
    now_iso = datetime.now(timezone.utc).isoformat()
    raw_item = RawItem(
        item_id=f"live_{int(datetime.now(timezone.utc).timestamp())}",
        source=request.source or "Manual Live Entry",
        source_type="social" if (request.source_type or "").lower() == "social" else "news",
        published_at=now_iso,
        title=request.text[:120],
        text=request.text,
        url=None,
        author="Interactive User",
        engagement={},
        query_tag=None,
        is_synthetic=False,
    )

    signals = engine.process_items([raw_item])
    if not signals:
        raise HTTPException(status_code=500, detail="Failed to process text analysis.")
    return signals[0]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=API_PORT, reload=True)


# ---------------------------------------------------------------------------
# Phase 4: portfolio, shock table, stress testing, replay stream, calibration
# ---------------------------------------------------------------------------
import asyncio  # noqa: E402

from fastapi.responses import StreamingResponse  # noqa: E402

from src.config import CALIBRATION_DIR, CALIBRATION_MODEL_FILE  # noqa: E402
from src.schemas import CustomStressRequest, StressResult  # noqa: E402
from src.stress.engine import load_portfolio, run_custom, run_stress  # noqa: E402
from src.stress.replay import build_replay  # noqa: E402
from src.stress.shock_table import load_shock_table  # noqa: E402
from src.stress.trigger import suppression_reason  # noqa: E402
from src.engine.calibrate import calibrated_move  # noqa: E402
from src.config import CONTROLLED_THEMES  # noqa: E402


@app.get("/portfolio")
def get_portfolio():
    """SYNTHETIC portfolio positions plus aggregate exposures."""
    df = load_portfolio()
    total = float(df["market_value"].sum())
    agg = lambda col: {k: round(float(v), 2) for k, v in df.groupby(col)["market_value"].sum().sort_values(ascending=False).items()}
    tags: dict = {}
    for _, r in df.iterrows():
        for t in r["tag_list"]:
            tags[t] = tags.get(t, 0.0) + float(r["market_value"])
    positions = df.drop(columns=["tag_list"]).fillna("").to_dict(orient="records")
    for p, tl in zip(positions, df["tag_list"]):
        p["tags"] = tl
    return {
        "synthetic": True,
        "total_market_value": round(total, 2),
        "n_positions": len(df),
        "by_asset_type": agg("asset_type"),
        "by_sector": agg("sector"),
        "by_country": agg("country"),
        "by_tag": {k: round(v, 2) for k, v in sorted(tags.items(), key=lambda kv: -kv[1])},
        "positions": positions,
    }


@app.get("/shock-table")
def get_shock_table():
    """Theme x tag shock table with measured/assumed flags."""
    return load_shock_table().to_dict(orient="records")


@app.get("/stress/{signal_id}", response_model=StressResult)
def get_stress(signal_id: str):
    """Stress result for a trigger-eligible signal; 404 with suppression reason otherwise."""
    sig = next((s for s in read_all_signals() if s.signal_id == signal_id), None)
    if sig is None:
        raise HTTPException(status_code=404, detail={"signal_id": signal_id, "reason": "signal not found"})
    reason = suppression_reason(sig)
    if reason:
        raise HTTPException(status_code=404, detail={"signal_id": signal_id, "eligible": False, "reason": reason})
    return run_stress(sig)


@app.post("/stress/custom", response_model=StressResult)
def post_custom_stress(req: CustomStressRequest):
    """What-if: apply a theme at a chosen severity (1-10)."""
    if req.theme not in CONTROLLED_THEMES or req.theme == "none":
        raise HTTPException(status_code=422, detail=f"theme must be one of {CONTROLLED_THEMES}")
    return run_custom(req.theme, req.severity)


@app.get("/replay/stream")
async def replay_stream(speed: float = Query(1.0, gt=0, description="Playback speed multiplier")):
    """Server-Sent Events replay of stored signals with stress outcomes (deterministic, offline-safe)."""
    records = build_replay(read_all_signals())

    async def gen():
        for i, rec in enumerate(records):
            yield f"data: {json.dumps({'type': 'signal', 'index': i, 'signal': rec['signal']})}\n\n"
            await asyncio.sleep(0.5 / speed)
            yield f"data: {json.dumps({**rec['outcome'], 'index': i})}\n\n"
            await asyncio.sleep(1.5 / speed)
        yield f"data: {json.dumps({'type': 'end', 'count': len(records)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/calibration")
def get_calibration():
    """Calibration curve points, bucket table and fit statistics for plotting."""
    if not CALIBRATION_MODEL_FILE.exists():
        raise HTTPException(status_code=404, detail="calibration model not fitted")
    model = json.loads(CALIBRATION_MODEL_FILE.read_text())
    pts_file = CALIBRATION_DIR / "calibration_points.csv"
    points = []
    if pts_file.exists():
        import pandas as pd
        points = pd.read_csv(pts_file).to_dict(orient="records")
    curve = []
    for i in range(10, 101, 5):
        x = i / 10.0
        mid, lo, hi, _ = calibrated_move(x, -1.0)
        curve.append({"impact": x, "move_pct": mid, "low_pct": lo, "high_pct": hi})
    return {"fit": model, "buckets": model.get("buckets", []), "points": points, "curve": curve}
