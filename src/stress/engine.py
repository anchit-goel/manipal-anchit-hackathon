"""Exposure-aware stress engine: theme shocks transmitted by asset type, plus a naive uniform benchmark."""
from typing import Dict, List, Optional, Tuple
import uuid

import pandas as pd

from src.config import LOAN_LGD, PORTFOLIO_FILE, get_logger
from src.engine.calibrate import calibrated_move
from src.schemas import PositionImpact, Signal, StressResult
from src.stress.shock_table import load_shock_table

logger = get_logger("stress.engine")

ENTITY_BOOST = 1.25         # extra downside scale on the named entity's own positions
SCALE_MIN, SCALE_MAX = 0.25, 2.0
DERIV_EXPOSURE_FLOOR_PCT = 0.10  # max derivative loss as share of notional
DERIV_CVA_EAD_PCT = 0.05         # potential future exposure proxy for CVA


REQUIRED_PORTFOLIO_COLS = {
    "position_id", "asset_type", "counterparty", "ticker", "sector", "country", "market_value",
    "notional", "duration", "delta", "collateral_pct", "tags",
}


def load_portfolio(path=None) -> pd.DataFrame:
    """Load the synthetic book; a missing/malformed default file is regenerated deterministically."""
    target = path or PORTFOLIO_FILE
    df = None
    try:
        df = pd.read_csv(target)
        if not REQUIRED_PORTFOLIO_COLS <= set(df.columns) or df.empty:
            df = None
    except Exception as e:
        logger.warning("Portfolio file unreadable (%s)", e)
    if df is None:
        if path is not None:
            raise ValueError(f"malformed portfolio file: {path}")
        from src.portfolio.build import build_portfolio
        logger.warning("Regenerating synthetic portfolio at %s", target)
        df = build_portfolio()
        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=False)
    for col in ("market_value", "notional", "duration", "delta", "collateral_pct"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["tag_list"] = df["tags"].fillna("").apply(lambda s: [t for t in s.split("|") if t])
    return df


def severity_scale(impact: float, calibrated_move_pct: Optional[float] = None) -> float:
    """Scale relative to reference severity (impact 8). Uses calibrated move; falls back to impact/8."""
    if calibrated_move_pct is None:
        s = impact / 8.0
    else:
        ref = abs(calibrated_move(8.0, -1.0)[0])
        s = abs(calibrated_move_pct) / ref if ref > 0 else impact / 8.0
    return float(min(SCALE_MAX, max(SCALE_MIN, s)))


def _pick(rows: pd.DataFrame, col: str) -> Optional[pd.Series]:
    rows = rows[rows[col] != 0]
    if rows.empty:
        return None
    return rows.loc[rows[col].abs().idxmax()]


def _exposure_cap(pos) -> float:
    if pos["asset_type"] == "derivative":
        return max(pos["market_value"], DERIV_EXPOSURE_FLOOR_PCT * pos["notional"])
    return pos["market_value"]


def position_shock(pos, theme: str, scale: float, table: pd.DataFrame) -> Tuple[float, Optional[str], Optional[str]]:
    """Return (pnl, matched_tag, rule_source) for one position under one theme."""
    rows = table[(table["theme"] == theme) & (table["tag"].isin(pos["tag_list"]))]
    if rows.empty:
        return 0.0, None, None
    at, mv = pos["asset_type"], pos["market_value"]
    pnl, used = 0.0, []

    if at == "equity":
        r = _pick(rows, "equity_pct")
        if r is not None:
            pnl, used = mv * r.equity_pct / 100.0 * scale, [r]
    elif at == "bond":
        r = _pick(rows, "spread_bps")
        if r is not None:
            pnl, used = -(r.spread_bps / 1e4) * pos["duration"] * mv * scale, [r]
    elif at == "loan":
        r = _pick(rows, "pd_bump_pct")
        if r is not None:
            pnl = -(r.pd_bump_pct / 100.0) * scale * LOAN_LGD * mv * (1 - pos["collateral_pct"])
            used = [r]
    elif at == "derivative":
        m = _pick(rows, "underlying_pct")
        if m is not None:
            pnl += pos["delta"] * pos["notional"] * m.underlying_pct / 100.0 * scale
            used.append(m)
        c = _pick(rows, "pd_bump_pct")
        if c is not None:
            ead = max(mv, DERIV_CVA_EAD_PCT * pos["notional"])
            pnl += -(c.pd_bump_pct / 100.0) * scale * LOAN_LGD * ead * (1 - pos["collateral_pct"])
            used.append(c)
    if not used:
        return 0.0, None, None
    lead = used[0]
    sources = {u.source for u in used}
    return float(pnl), lead.tag, "measured" if sources == {"measured"} else "assumed"


def _core(
    components: List[Tuple[str, float]],
    headline_move_pct: float,
    portfolio: pd.DataFrame,
    table: pd.DataFrame,
    scenario_id: str,
    lead_signal_id: Optional[str] = None,
    corroborating: Optional[List[str]] = None,
    boost_ticker: Optional[str] = None,
) -> StressResult:
    # components: (theme, scale) or (theme, scale, group). Themes from one signal share a group
    # (correlated, so the worst applies); distinct groups (different signals/themes) sum.
    components = [c if len(c) == 3 else (c[0], c[1], c[0]) for c in components]
    impacts: List[PositionImpact] = []
    by_type: Dict[str, float] = {}
    by_sector: Dict[str, float] = {}
    by_country: Dict[str, float] = {}
    total_before = float(portfolio["market_value"].sum())

    for _, pos in portfolio.iterrows():
        tags, srcs, whys, theme_lead = [], [], [], None
        group_best: Dict[str, float] = {}
        for theme, scale, group in components:
            p, tag, src = position_shock(pos, theme, scale, table)
            if tag is None:
                continue
            if boost_ticker and pos["ticker"] == boost_ticker and p < 0:
                p *= ENTITY_BOOST
            if abs(p) >= abs(group_best.get(group, 0.0)):
                group_best[group] = p
            tags.append(tag)
            srcs.append(src)
            whys.append(f"{theme} x {tag} ({src})")
            theme_lead = theme_lead or theme
        pnl = sum(group_best.values())
        pnl = max(pnl, -_exposure_cap(pos))  # no position loses more than its exposure
        mv = float(pos["market_value"])
        impacts.append(PositionImpact(
            position_id=pos["position_id"], counterparty=pos["counterparty"], asset_type=pos["asset_type"],
            sector=pos["sector"], country=pos["country"], market_value=mv, pnl=round(pnl, 2),
            pnl_pct=round(pnl / _exposure_cap(pos) * 100.0, 3) if mv else 0.0,
            theme=theme_lead, tag=tags[0] if tags else None,
            rule_source="measured" if srcs and set(srcs) == {"measured"} else ("assumed" if srcs else None),
            why="; ".join(whys) if whys else "no matching exposure tag - unaffected",
        ))
        by_type[pos["asset_type"]] = by_type.get(pos["asset_type"], 0.0) + pnl
        by_sector[pos["sector"]] = by_sector.get(pos["sector"], 0.0) + pnl
        by_country[pos["country"]] = by_country.get(pos["country"], 0.0) + pnl

    pnl_abs = float(sum(i.pnl for i in impacts))
    naive_abs = total_before * headline_move_pct / 100.0
    losers = sorted([i for i in impacts if i.pnl < 0], key=lambda i: i.pnl)
    winners = sorted([i for i in impacts if i.pnl > 0], key=lambda i: -i.pnl)
    top10 = losers[:10]
    other = sum(i.pnl for i in losers[10:])
    waterfall = [{"label": i.counterparty, "position_id": i.position_id, "pnl": i.pnl} for i in top10]
    if other:
        waterfall.append({"label": "Other losses", "position_id": None, "pnl": round(other, 2)})
    waterfall.append({"label": "Gains", "position_id": None, "pnl": round(sum(i.pnl for i in winners), 2)})
    waterfall.append({"label": "Total", "position_id": None, "pnl": round(pnl_abs, 2)})

    rnd = lambda d: {k: round(v, 2) for k, v in sorted(d.items(), key=lambda kv: kv[1])}
    return StressResult(
        scenario_id=scenario_id, lead_signal_id=lead_signal_id, corroborating_signal_ids=corroborating or [],
        themes=[c[0] for c in components], severity_scale=round(max([c[1] for c in components] or [0]), 3),
        headline_move_pct=round(headline_move_pct, 3), total_before=round(total_before, 2),
        total_after=round(total_before + pnl_abs, 2), pnl_abs=round(pnl_abs, 2),
        pnl_pct=round(pnl_abs / total_before * 100.0, 4), naive_pnl_abs=round(naive_abs, 2),
        naive_pnl_pct=round(headline_move_pct, 4), positions_hit=sum(1 for i in impacts if i.pnl != 0),
        by_asset_type=rnd(by_type), by_sector=rnd(by_sector), by_country=rnd(by_country),
        top_losers=top10, top_winners=winners[:10], waterfall=waterfall, positions=impacts,
    )


def _themes(sig_themes: List[str]) -> List[str]:
    return [t for t in sig_themes if t and t != "none"]


def run_stress(signal: Signal, portfolio: Optional[pd.DataFrame] = None,
               table: Optional[pd.DataFrame] = None) -> StressResult:
    """Stress the book with one signal. Naive benchmark applies -|calibrated move| to every position."""
    pf = portfolio if portfolio is not None else load_portfolio()
    tb = table if table is not None else load_shock_table()
    scale = severity_scale(signal.impact_score, signal.calibrated_move_pct)
    headline = -abs(signal.calibrated_move_pct if signal.calibrated_move_pct is not None
                    else calibrated_move(signal.impact_score, -1.0)[0])
    return _core([(t, scale, signal.signal_id) for t in _themes(signal.themes)], headline, pf, tb,
                 scenario_id=f"scn_{signal.signal_id}", lead_signal_id=signal.signal_id,
                 boost_ticker=signal.ticker)


def run_custom(theme: str, severity: float, portfolio: Optional[pd.DataFrame] = None,
               table: Optional[pd.DataFrame] = None) -> StressResult:
    """What-if: apply a theme at a given 1-10 severity."""
    pf = portfolio if portfolio is not None else load_portfolio()
    tb = table if table is not None else load_shock_table()
    move = calibrated_move(severity, -1.0)[0]
    scale = severity_scale(severity, move)
    return _core([(theme, scale)], -abs(move), pf, tb, scenario_id=f"custom_{theme}_{severity:g}")


def run_combined(scenarios, portfolio: Optional[pd.DataFrame] = None,
                 table: Optional[pd.DataFrame] = None) -> StressResult:
    """Combine concurrent scenarios: distinct themes sum per position, floor keeps losses <= exposure."""
    pf = portfolio if portfolio is not None else load_portfolio()
    tb = table if table is not None else load_shock_table()
    comp: Dict[str, Tuple[float, str]] = {}
    headline = 0.0
    for sc in scenarios:
        lead = sc.lead
        scale = severity_scale(lead.impact_score, lead.calibrated_move_pct)
        for t in _themes(lead.themes):
            if t not in comp or scale > comp[t][0]:
                comp[t] = (scale, lead.signal_id)  # same theme across scenarios counted once
        headline += -abs(lead.calibrated_move_pct or 0.0)
    return _core([(t, v[0], v[1]) for t, v in comp.items()], max(headline, -50.0), pf, tb,
                 scenario_id="scn_combined_" + uuid.uuid4().hex[:6],
                 lead_signal_id=scenarios[0].lead.signal_id if scenarios else None,
                 corroborating=[s.lead.signal_id for s in scenarios[1:]])
