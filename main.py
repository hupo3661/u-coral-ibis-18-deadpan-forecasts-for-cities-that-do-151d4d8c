#!/usr/bin/env python3
"""Deadpan Forecasts for Cities That Do Not Exist — one-line entry.

The evening broadcast from Zorbania, a city that does not exist,
delivered deadpan: sideways rain at 14 degrees, a 90 percent chance
of umbrellas surrendering, and one very confused sun. The forecast
is built from its spoken segments, checked against the contest
limit of 160 characters, and broadcast to the entry file.
"""

import os
import sys
from pathlib import Path

CHAR_LIMIT = 160
DEFAULT_OUTPUT = "/output/entry.txt"

# The broadcast, spoken in four beats. Joined with ", " they form the
# entry line exactly — no word added, none removed.
SEGMENTS = (
    "Good evening from Zorbania",
    "where tomorrow brings sideways rain at 14 degrees",
    "a 90 percent chance of umbrellas surrendering",
    "and one very confused sun.",
)

FORECAST = ", ".join(SEGMENTS)


class BroadcastError(Exception):
    """The forecast breaks a contest rule."""


def check_broadcast(line):
    """Raise BroadcastError listing every rule the line breaks."""
    faults = []
    if not line.strip():
        faults.append("forecast is empty")
    if line != line.strip():
        faults.append("forecast has leading or trailing whitespace")
    if len(line) > CHAR_LIMIT:
        faults.append(
            f"forecast is {len(line)} characters, over the "
            f"{CHAR_LIMIT} limit"
        )
    if line.count("\n") or line.count("\r"):
        faults.append("forecast must be one line")
    if not line.endswith("."):
        faults.append("forecast must end with a full stop")
    if faults:
        raise BroadcastError("; ".join(faults))


def pick_output(argv):
    """Destination from --output, else OUTPUT_PATH, else the default."""
    for position, token in enumerate(argv):
        if token == "--output" and position + 1 < len(argv):
            return argv[position + 1]
        if token.startswith("--output="):
            return token.split("=", 1)[1]
    return os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT)


def broadcast(line, destination):
    """Write the forecast and read it back to confirm the broadcast."""
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(line, encoding="utf-8")
    aired = target.read_text(encoding="utf-8")
    if aired != line:
        raise BroadcastError("aired copy differs from the forecast")
    return target


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        check_broadcast(FORECAST)
    except BroadcastError as problem:
        print(f"invalid forecast: {problem}", file=sys.stderr)
        return 1
    if "--check" in argv:
        print(f"forecast OK: {len(FORECAST)} characters, one line")
        return 0
    target = broadcast(FORECAST, pick_output(argv))
    if "--quiet" not in argv:
        print(FORECAST)
        print(f"broadcast to {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
