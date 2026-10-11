"""FastAPI service: risk signals, portfolio stress testing, replay stream, and the compiled web UI."""
import asyncio
import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import (
    BASE_DIR,
    CALIBRATION_DIR,
    CALIBRATION_MODEL_FILE,
    CONTROLLED_THEMES,
    OFFLINE_MODE,
    PORTFOLIO_FILE,
    SHOCK_TABLE_FILE,
    SIGNALS_PROCESSED_FILE,
    get_logger,
)
from src.engine.calibrate import calibrated_move
from src.engine.run import RiskEngine, normalize_model_label
from src.llm.client import LLMClient
from src.presets import MAX_TEXT_CHARS, PRESETS, build_live_item
from src.schemas import CustomStressRequest, EventClass, Signal, StressResult
from src.stress.engine import load_portfolio, run_custom, run_stress
from src.stress.replay import build_replay
from src.stress.shock_table import load_shock_table
from src.stress.trigger import evaluate_signals, suppression_reason

logger = get_logger("api.main")

UI_DIST = BASE_DIR / "ui" / "dist"
ANALYZE_TIMEOUT_S = 25.0

app = FastAPI(
    title="Signal-to-Shock Risk API",
    description="AI/NLP risk engine: structured signals, calibrated impact and exposure-aware stress tests.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Engines (lazy so importing the app is cheap and never touches the network)
# ---------------------------------------------------------------------------
_engine: Optional[RiskEngine] = None
_fallback_engine: Optional[RiskEngine] = None
_engine_lock = threading.Lock()


def get_engine() -> RiskEngine:
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = RiskEngine()
        return _engine


def get_fallback_engine() -> RiskEngine:
    """Always-offline engine (rules extractor + lexicon sentiment) used when the LLM times out."""
    global _fallback_engine
    with _engine_lock:
        if _fallback_engine is None:
            _fallback_engine = RiskEngine(llm_client=LLMClient(offline_mode=True), force_lexicon_finbert=True)
        return _fallback_engine


def llm_is_live() -> bool:
    llm = get_engine().extractor.llm
    return bool(not llm.offline_mode and llm.api_key)


# ---------------------------------------------------------------------------
# Startup: regenerate cheap deterministic artefacts if missing
# ---------------------------------------------------------------------------
def ensure_artifacts() -> Dict[str, str]:
    status: Dict[str, str] = {}
    try:
        load_portfolio()
        status["portfolio"] = "ok"
    except Exception as e:  # pragma: no cover - defensive
        status["portfolio"] = f"error: {e}"
    try:
        if not SHOCK_TABLE_FILE.exists():
            from src.stress.shock_table import save_shock_table
            save_shock_table()
        status["shock_table"] = "ok"
    except Exception as e:  # pragma: no cover
        status["shock_table"] = f"error: {e}"
    if not CALIBRATION_MODEL_FILE.exists():
        try:
            from src.calibration.fit import run_full_calibration_pipeline
            run_full_calibration_pipeline()
            status["calibration"] = "regenerated"
        except Exception as e:
            logger.warning("Calibration artefacts missing and could not be regenerated: %s", e)
            status["calibration"] = f"unavailable: {e}"
    else:
        status["calibration"] = "ok"
    return status


@app.on_event("startup")
def _startup() -> None:
    logger.info("Artefacts: %s", ensure_artifacts())


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------
def read_all_signals(filepath: Optional[Path] = None) -> List[Signal]:
    """Read persisted signals; missing file -> []; malformed lines skipped; duplicate ids dropped."""
    target_file = filepath or SIGNALS_PROCESSED_FILE
    if not target_file.exists():
        return []
    signals: List[Signal] = []
    seen = set()
    with open(target_file, "r", encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                sig = Signal.model_validate_json(line)
            except Exception as e:
                logger.warning("Skipping malformed signal on line %d: %s", n, str(e)[:120])
                continue
            if sig.signal_id in seen:
                logger.warning("Skipping duplicate signal_id %s on line %d", sig.signal_id, n)
                continue
            seen.add(sig.signal_id)
            signals.append(sig)
    return signals


_replay_cache: Dict[str, Any] = {"key": None, "records": []}


def get_replay_records() -> List[Dict[str, Any]]:
    """Replay outcomes for the stored signals, cached on file mtime so SSE clients share the work."""
    try:
        st = SIGNALS_PROCESSED_FILE.stat()
        key = (st.st_mtime_ns, st.st_size, PORTFOLIO_FILE.exists())
    except FileNotFoundError:
        return []
    if _replay_cache["key"] != key:
        _replay_cache["records"] = build_replay(read_all_signals())
        _replay_cache["key"] = key
    return _replay_cache["records"]


def _extractor_kind(sig: Signal) -> str:
    return "rules-fallback" if "fallback" in (sig.model_versions.get("extractor") or "rules-fallback") else "llm"


def _sha8(path: Path) -> Optional[str]:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:8]
    except Exception:
        return None


class AnalyzeRequest(BaseModel):
    """Payload for on-demand text analysis."""
    text: str = Field(..., min_length=1, description="Headline or paragraph to analyze")
    source: Optional[str] = Field("Manual Live Entry", description="Provider label")
    source_type: Optional[str] = Field("news", description="'news' or 'social'")


@app.get("/health")
def health_check():
    """Service status, operation mode, signal/extractor counts and data versions."""
    signals = read_all_signals()
    kinds = {"llm": 0, "rules-fallback": 0}
    for s in signals:
        kinds[_extractor_kind(s)] += 1
    live = llm_is_live()
    calib_n = None
    if CALIBRATION_MODEL_FILE.exists():
        try:
            calib_n = json.loads(CALIBRATION_MODEL_FILE.read_text()).get("n_events")
        except Exception:
            calib_n = None
    try:
        pf = load_portfolio()
        pf_n = len(pf)
    except Exception:
        pf_n = 0
    return {
        "status": "ok",
        "service": "Signal-to-Shock Risk Engine",
        "mode": "live" if live else "replay-offline",
        "offline_mode": not live,
        "signal_count": len(signals),
        "extractors": kinds,
        "all_fallback": bool(signals) and kinds["llm"] == 0,
        "data_versions": {
            "signals_sha": _sha8(SIGNALS_PROCESSED_FILE),
            "portfolio_positions": pf_n,
            "portfolio_sha": _sha8(PORTFOLIO_FILE),
            "shock_table_rows": int(len(load_shock_table())),
            "calibration_events": calib_n,
        },
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
    filtered = []
    for s in read_all_signals():
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
    """Signals qualified to trigger downstream stress tests."""
    return [s for s in read_all_signals() if s.trigger_eligible]


@app.get("/signals/{signal_id}", response_model=Signal)
def get_signal_by_id(signal_id: str):
    for s in read_all_signals():
        if s.signal_id == signal_id:
            return s
    raise HTTPException(status_code=404, detail=f"Signal with id '{signal_id}' not found")


@app.get("/presets")
def get_presets():
    """Preset headlines (pre-cached through the engine, so they work offline)."""
    return PRESETS


def _analyze_sync(engine: RiskEngine, req: AnalyzeRequest) -> Signal:
    item = build_live_item(req.text, req.source or "Manual Live Entry", req.source_type or "news")
    signals = engine.process_items([item])
    if not signals:
        raise HTTPException(status_code=500, detail="Failed to process text analysis.")
    return signals[0]


@app.post("/analyze", response_model=Signal)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text in real time. Never hangs: an LLM timeout falls back to a labelled rules result."""
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="text must not be blank")
    truncated = len(request.text) > MAX_TEXT_CHARS
    try:
        sig = await asyncio.wait_for(run_in_threadpool(_analyze_sync, get_engine(), request), ANALYZE_TIMEOUT_S)
        fallback_note = None
    except asyncio.TimeoutError:
        logger.warning("/analyze LLM path exceeded %.0fs; returning rules-fallback result", ANALYZE_TIMEOUT_S)
        sig = await run_in_threadpool(_analyze_sync, get_fallback_engine(), request)
        fallback_note = f"LLM did not respond within {ANALYZE_TIMEOUT_S:.0f}s; labelled rules-fallback result"
    sig.model_versions["extractor"] = normalize_model_label(sig.model_versions.get("extractor", "rules-fallback"))
    if truncated:
        sig.model_versions["input_note"] = f"text truncated to {MAX_TEXT_CHARS} characters"
    if fallback_note:
        sig.model_versions["fallback_note"] = fallback_note
    elif "fallback" in sig.model_versions["extractor"]:
        sig.model_versions["fallback_note"] = "No cached or live LLM result available offline; rules-based extraction"
    return sig


# ---------------------------------------------------------------------------
# Portfolio, shock table, stress
# ---------------------------------------------------------------------------
@app.get("/portfolio")
def get_portfolio():
    """SYNTHETIC portfolio positions plus aggregate exposures."""
    df = load_portfolio()
    total = float(df["market_value"].sum())

    def agg(col: str) -> Dict[str, float]:
        return {k: round(float(v), 2) for k, v in df.groupby(col)["market_value"].sum().sort_values(ascending=False).items()}

    tags: Dict[str, float] = {}
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


@app.get("/themes")
def get_themes():
    return [t for t in CONTROLLED_THEMES if t != "none"]


@app.get("/stress/{signal_id}", response_model=StressResult)
def get_stress(signal_id: str):
    """Stress result for a trigger-eligible stored signal; 404 with suppression reason otherwise."""
    sig = next((s for s in read_all_signals() if s.signal_id == signal_id), None)
    if sig is None:
        raise HTTPException(status_code=404, detail={"signal_id": signal_id, "reason": "signal not found"})
    reason = suppression_reason(sig)
    if reason:
        raise HTTPException(status_code=404, detail={"signal_id": signal_id, "eligible": False, "reason": reason})
    return run_stress(sig)


@app.post("/stress/signal", response_model=StressResult)
def post_stress_signal(sig: Signal):
    """Stress an arbitrary (e.g. just-analyzed) signal if it passes the trigger rules."""
    reason = suppression_reason(sig)
    if reason:
        raise HTTPException(status_code=404, detail={"signal_id": sig.signal_id, "eligible": False, "reason": reason})
    return run_stress(sig)


@app.post("/stress/custom", response_model=StressResult)
def post_custom_stress(req: CustomStressRequest):
    """What-if: apply a theme at a chosen severity (1-10)."""
    if req.theme not in CONTROLLED_THEMES or req.theme == "none":
        raise HTTPException(
            status_code=422,
            detail=f"theme '{req.theme}' is not valid; choose one of {[t for t in CONTROLLED_THEMES if t != 'none']}",
        )
    return run_custom(req.theme, req.severity)


@app.get("/scenarios")
def get_scenarios():
    """Debounced scenarios (same theme within 48h merged) produced by the replay, with suppressed signals."""
    signals = read_all_signals()
    scenarios, suppressed = evaluate_signals(signals)
    by_id = {r["signal"]["signal_id"]: r["outcome"] for r in get_replay_records()}
    out = []
    for sc in scenarios:
        res = (by_id.get(sc.lead.signal_id) or {}).get("result") or {}
        out.append({
            "scenario_id": f"scn_{sc.lead.signal_id}",
            "theme": sc.theme,
            "themes": [t for t in sc.lead.themes if t != "none"],
            "lead_signal_id": sc.lead.signal_id,
            "corroborating_signal_ids": sc.corroborating_ids,
            "headline": sc.lead.headline,
            "started_at": sc.start.isoformat(),
            "impact_score": sc.lead.impact_score,
            "calibrated_move_pct": sc.lead.calibrated_move_pct,
            "pnl_abs": res.get("pnl_abs"),
            "pnl_pct": res.get("pnl_pct"),
            "naive_pnl_pct": res.get("naive_pnl_pct"),
        })
    return {"scenarios": out, "suppressed": [{"signal_id": s.signal_id, "reason": s.reason} for s in suppressed]}


# ---------------------------------------------------------------------------
# Replay stream (SSE): restartable, per-connection, safe for concurrent clients
# ---------------------------------------------------------------------------
def _sse(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/replay/stream")
async def replay_stream(
    request: Request,
    speed: float = Query(1.0, gt=0, le=10000, description="Playback speed multiplier"),
    start: int = Query(0, ge=0, description="Resume from this event index"),
):
    """SSE replay of stored signals: signal -> (stress_result | suppressed | merged) ... end."""
    records = get_replay_records()

    async def gen():
        try:
            for i, rec in enumerate(records):
                if i < start:
                    continue
                if await request.is_disconnected():
                    return
                yield _sse({"type": "signal", "index": i, "signal": rec["signal"]})
                await asyncio.sleep(0.6 / speed)
                yield _sse({**rec["outcome"], "index": i})
                await asyncio.sleep(1.6 / speed)
            yield _sse({"type": "end", "count": len(records)})
        except asyncio.CancelledError:  # client went away mid-stream
            return

    return StreamingResponse(
        gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------
@app.get("/calibration")
def get_calibration():
    """Calibration curve points, bucket table and fit statistics for plotting."""
    if not CALIBRATION_MODEL_FILE.exists():
        raise HTTPException(status_code=404, detail="calibration model not fitted")
    model = json.loads(CALIBRATION_MODEL_FILE.read_text())
    pts_file = CALIBRATION_DIR / "calibration_points.csv"
    points: List[Dict[str, Any]] = []
    if pts_file.exists():
        points = pd.read_csv(pts_file).to_dict(orient="records")
    curve = []
    for i in range(10, 101, 5):
        x = i / 10.0
        mid, lo, hi, _ = calibrated_move(x, -1.0)
        curve.append({"impact": x, "move_pct": abs(mid), "low_pct": min(abs(lo), abs(hi)), "high_pct": max(abs(lo), abs(hi))})
    return {"fit": model, "buckets": model.get("buckets", []), "points": points, "curve": curve}


# ---------------------------------------------------------------------------
# Web UI (must be registered last): compiled React app with SPA fallback
# ---------------------------------------------------------------------------
if (UI_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=UI_DIST / "assets"), name="ui-assets")


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    index = UI_DIST / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="UI not built: run `cd ui && npm ci && npm run build`")
    candidate = (UI_DIST / full_path).resolve()
    if full_path and candidate.is_file() and UI_DIST.resolve() in candidate.parents:
        return FileResponse(candidate)
    if "." in full_path.rsplit("/", 1)[-1]:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(index)
