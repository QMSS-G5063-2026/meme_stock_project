"""Run the robust Track B and Track C build pipeline."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing import build_google_trends_outputs, build_reddit_outputs, build_static_figures


def main() -> None:
    build_reddit_outputs.main()
    build_google_trends_outputs.main()
    build_static_figures.main()


if __name__ == "__main__":
    main()
