#!/usr/bin/env python3
"""Build static dashboard data for GitHub Pages."""

from __future__ import annotations

from airline_sked.docs_dashboard import ROOT, refresh_dashboard_data


def main() -> None:
    output_file = refresh_dashboard_data()
    print(f"Wrote {output_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
