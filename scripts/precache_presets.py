"""Run every preset headline through the live LLM once (require-llm) so /analyze works offline."""
from src.engine.run import RiskEngine
from src.presets import PRESETS, build_live_item


def main():
    engine = RiskEngine(require_llm=True)
    for p in PRESETS:
        sig = engine.process_items([build_live_item(p["text"], p["source"], p["source_type"])])[0]
        print(f"{p['id']:<16} impact {sig.impact_score:>4.1f} conf {sig.confidence:.2f} themes {sig.themes} "
              f"extractor {sig.model_versions.get('extractor')}")


if __name__ == "__main__":
    main()
