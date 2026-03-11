#!/usr/bin/env python3
"""Build static dashboard data for GitHub Pages."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SRC_DIR = REPO_ROOT / "src"


def bootstrap_src_path() -> None:
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


bootstrap_src_path()

from airline_sked.docs_dashboard import ROOT, refresh_dashboard_data


def main() -> None:
    output_file = refresh_dashboard_data()
    print(f"Wrote {output_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
