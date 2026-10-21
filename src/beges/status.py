"""Statut console du pipeline BEGES."""

from __future__ import annotations

import sys

from beges.reporting import build_status_text, load_dashboard_data


def main() -> int:
    try:
        data = load_dashboard_data()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(build_status_text(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
