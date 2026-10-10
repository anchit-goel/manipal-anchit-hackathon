"""CLI: python -m src.stress.run --signal sig_replay_008 | --replay"""
import argparse

from src.stress.engine import load_portfolio, run_stress
from src.stress.replay import build_replay, load_signals
from src.stress.shock_table import load_shock_table


def _m(x: float) -> str:
    return f"{x / 1e6:>+9.2f}M"


def print_result(res, signal=None):
    print("=" * 100)
    head = signal.headline[:80] if signal else res.scenario_id
    print(f"{res.scenario_id}  themes={res.themes}  scale={res.severity_scale}  | {head}")
    print(f"  Portfolio before ${res.total_before / 1e6:,.1f}M -> after ${res.total_after / 1e6:,.1f}M")
    print(f"  Exposure-aware: {res.pnl_pct:+.3f}% ({_m(res.pnl_abs)}) | Naive uniform: {res.naive_pnl_pct:+.3f}% ({_m(res.naive_pnl_abs)}) | positions hit: {res.positions_hit}")
    print("  By asset type: " + ", ".join(f"{k} {v / 1e6:+.2f}M" for k, v in res.by_asset_type.items()))
    print("  Top losers:")
    for i in res.top_losers[:5]:
        print(f"    {i.position_id} {i.counterparty:<24} {i.asset_type:<10} {i.pnl / 1e6:+7.2f}M ({i.pnl_pct:+.2f}%) {i.why}")
    if res.top_winners:
        print("  Top winners:")
        for i in res.top_winners[:3]:
            print(f"    {i.position_id} {i.counterparty:<24} {i.asset_type:<10} {i.pnl / 1e6:+7.2f}M ({i.pnl_pct:+.2f}%) {i.why}")


def main():
    ap = argparse.ArgumentParser(description="Signal-to-Shock stress runner")
    ap.add_argument("--signal", type=str)
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()
    pf, tb = load_portfolio(), load_shock_table()
    signals = load_signals()

    if args.signal:
        sig = next((s for s in signals if s.signal_id == args.signal), None)
        if sig is None:
            raise SystemExit(f"signal {args.signal} not found")
        print_result(run_stress(sig, pf, tb), sig)
    elif args.replay:
        for rec in build_replay(signals, pf, tb):
            s, o = rec["signal"], rec["outcome"]
            print(f"\n[{s['signal_id']}] impact {s['impact_score']:.1f} conf {s['confidence']:.2f} themes {s['themes']} :: {s['headline'][:70]}")
            if o["type"] == "stress_result":
                from src.schemas import StressResult
                sig = next(x for x in signals if x.signal_id == s["signal_id"])
                print_result(StressResult(**o["result"]), sig)
            else:
                print(f"  {o['type'].upper()}: {o['reason']}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
