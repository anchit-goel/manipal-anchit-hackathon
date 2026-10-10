"""Empirical calibration application: converts impact_score and sentiment into expected percentage moves."""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from src.config import CALIBRATION_MODEL_FILE, get_logger
from src.schemas import Signal

logger = get_logger("engine.calibrate")

# Institutional fallback parameters derived from CAPM event study across 24 shocks
DEFAULT_CALIBRATION_PARAMS = {
    "slope": 1.485,
    "intercept": 0.420,
    "residual_std": 2.15,
    "z_80": 1.28,
}


def load_calibration_model(model_path: Optional[Path] = None) -> Dict[str, float]:
    """Load fitted calibration model parameters from JSON or return robust fallback."""
    path = model_path or CALIBRATION_MODEL_FILE
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "slope": float(data.get("slope", DEFAULT_CALIBRATION_PARAMS["slope"])),
                "intercept": float(data.get("intercept", DEFAULT_CALIBRATION_PARAMS["intercept"])),
                "residual_std": float(data.get("residual_std", DEFAULT_CALIBRATION_PARAMS["residual_std"])),
                "z_80": 1.28,
            }
        except Exception as e:
            logger.warning("Error reading calibration model %s: %s. Using default params.", path, e)
    return DEFAULT_CALIBRATION_PARAMS.copy()


def calibrated_move(
    impact_score: float,
    sentiment_score: float,
    model_params: Optional[Dict[str, float]] = None,
) -> Tuple[float, float, float, str]:
    """Calculate expected percentage abnormal move with 80% confidence interval and rationale."""
    params = model_params or load_calibration_model()
    slope = params["slope"]
    intercept = params["intercept"]
    res_std = params["residual_std"]
    z_80 = params.get("z_80", 1.28)

    # 1. Expected absolute abnormal return magnitude
    expected_mag = max(0.1, intercept + slope * impact_score)

    # 2. Predictive 80% interval on magnitude
    mag_low = max(0.05, expected_mag - z_80 * res_std)
    mag_high = max(mag_low + 0.1, expected_mag + z_80 * res_std)

    # 3. Direction from sentiment (or entity market value perspective)
    if sentiment_score < -0.05:
        sign = -1.0
    elif sentiment_score > 0.05:
        sign = 1.0
    else:
        # Neutral sentiment: default to negative risk impact
        sign = -1.0

    signed_pct = round(sign * expected_mag, 2)
    low_pct = round(sign * (mag_high if sign < 0 else mag_low), 2)
    high_pct = round(sign * (mag_low if sign < 0 else mag_high), 2)

    # Order low_pct <= high_pct
    actual_low = min(low_pct, high_pct)
    actual_high = max(low_pct, high_pct)

    explanation = (
        f"impact {impact_score:.1f} ≈ {signed_pct:+.1f}% "
        f"(80% range {actual_low:+.1f}% to {actual_high:+.1f}%) historically"
    )

    return signed_pct, actual_low, actual_high, explanation


def calibrate_signal(signal: Signal, model_params: Optional[Dict[str, float]] = None) -> Signal:
    """Populate empirical calibration move fields on a Signal."""
    signed_pct, low_pct, high_pct, explanation = calibrated_move(
        impact_score=signal.impact_score,
        sentiment_score=signal.sentiment_score,
        model_params=model_params,
    )
    signal.calibrated_move_pct = signed_pct
    signal.calibrated_low_pct = low_pct
    signal.calibrated_high_pct = high_pct
    signal.calibrated_explanation = explanation
    return signal


def calibrate_signals_batch(signals: List[Signal], model_params: Optional[Dict[str, float]] = None) -> List[Signal]:
    """Apply empirical calibration to a list of Signals."""
    params = model_params or load_calibration_model()
    for s in signals:
        calibrate_signal(s, params)
    return signals
