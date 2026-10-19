#!/usr/bin/env python3
"""One-time, interactive authorization for read-only Google Calendar access."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from core.google_calendar import CalendarNotConfigured, authorize, client_secret_path, token_path


def main():
    try:
        authorize(interactive=True)
    except CalendarNotConfigured as exc:
        print(f"Calendar setup incomplete: {exc}")
        return 1
    print(f"Google Calendar connected with read-only access. Token saved to {token_path()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
