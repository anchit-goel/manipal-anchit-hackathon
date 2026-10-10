"""One-command demo: python run_demo.py  (offline replay mode, no API key or network needed)."""
import argparse
import os
import threading
import time
import urllib.request
import webbrowser


def main() -> None:
    ap = argparse.ArgumentParser(description="Signal-to-Shock demo server")
    ap.add_argument("--port", type=int, default=int(os.getenv("API_PORT", "8000")))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--live", action="store_true", help="use .env keys for live LLM/news instead of offline replay")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    if not args.live:  # must be set before src.config is imported
        os.environ["OFFLINE_MODE"] = "true"
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        for key in ("LLM_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"):
            os.environ[key] = ""

    import uvicorn

    url = f"http://{args.host}:{args.port}"

    def open_when_ready() -> None:
        for _ in range(120):
            try:
                urllib.request.urlopen(f"{url}/health", timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        print(f"\n  Signal-to-Shock is running ({'LIVE' if args.live else 'REPLAY - OFFLINE'}): {url}\n")
        if not args.no_browser:
            webbrowser.open(url)

    threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run("src.api.main:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
