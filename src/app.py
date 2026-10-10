"""`python -m src.app` is an alias for run_demo.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run_demo import main  # noqa: E402

if __name__ == "__main__":
    main()
