#!/usr/bin/env python3
"""Deadpan Forecasts for Cities That Do Not Exist.

A tiny evening-news studio for a city that does not exist. The
presenter reads one forecast for Zorbania, deadpan, in four beats:
a greeting, the conditions, the odds, and the sun. The studio
assembles the beats, scores the finished line against the contest
rules, and only then puts it on air — that is, writes it to the
entry file and reads it back to prove the broadcast matches the
script.

The forecast itself is fixed. There is no clock, no network and no
randomness here: the same script airs every time, so the entry the
judges read is the entry this program writes.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Contest rules, as numbers the studio enforces rather than remembers.
MAX_CHARS = 160
REQUIRED_ENDING = "."
DEFAULT_ENTRY_PATH = "/output/entry.txt"


class BeatRole(Enum):
    """What one spoken beat of the forecast is doing."""

    GREETING = "greeting"
    CONDITIONS = "conditions"
    ODDS = "odds"
    PUNCHLINE = "punchline"


@dataclass(frozen=True)
class Beat:
    """One beat of the broadcast, with the job it does in the line."""

    role: BeatRole
    text: str

    def __post_init__(self) -> None:
        if not self.text or self.text != self.text.strip():
            raise ValueError(f"beat {self.role.value!r} is empty or padded")
        if "\n" in self.text or "\r" in self.text:
            raise ValueError(f"beat {self.role.value!r} spans more than a line")


@dataclass
class ForecastScript:
    """The whole evening forecast, kept as beats until airtime."""

    city: str = "Zorbania"
    beats: list[Beat] = field(default_factory=list)

    def line(self) -> str:
        """Join the beats into the single entry line."""
        return ", ".join(beat.text for beat in self.beats)

    def fingerprint(self) -> str:
        """A short, stable digest of the line, for the run report."""
        digest = hashlib.sha256(self.line().encode("utf-8")).hexdigest()
        return digest[:12]

    def word_count(self) -> int:
        return len(self.line().split())

    def beat_sheet(self) -> str:
        """One line per beat, for a presenter reading the script aloud."""
        return "\n".join(
            f"{index + 1}. [{beat.role.value}] {beat.text}"
            for index, beat in enumerate(self.beats)
        )


def tonight() -> ForecastScript:
    """Tonight's script: the Zorbania forecast, beat by beat."""
    return ForecastScript(
        beats=[
            Beat(BeatRole.GREETING, "Good evening from Zorbania"),
            Beat(
                BeatRole.CONDITIONS,
                "where tomorrow brings sideways rain at 14 degrees",
            ),
            Beat(
                BeatRole.ODDS,
                "a 90 percent chance of umbrellas surrendering",
            ),
            Beat(BeatRole.PUNCHLINE, "and one very confused sun."),
        ]
    )


@dataclass
class RuleBreak:
    """One contest rule the finished line breaks, in plain words."""

    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.detail}"


def score_line(line: str) -> list[RuleBreak]:
    """Score a finished line against every contest rule at once."""
    breaks: list[RuleBreak] = []
    if not line.strip():
        breaks.append(RuleBreak("empty", "the forecast says nothing"))
    if line != line.strip():
        breaks.append(
            RuleBreak("whitespace", "leading or trailing space around the line")
        )
    if len(line) > MAX_CHARS:
        breaks.append(
            RuleBreak(
                "length",
                f"{len(line)} characters, over the {MAX_CHARS} limit",
            )
        )
    if any(char in line for char in ("\n", "\r")):
        breaks.append(RuleBreak("one line", "the forecast wraps onto more lines"))
    if not line.endswith(REQUIRED_ENDING):
        breaks.append(
            RuleBreak("ending", f"must end with {REQUIRED_ENDING!r}")
        )
    words = line.split()
    if len(words) < 5:
        breaks.append(RuleBreak("too short", "a forecast needs at least five words"))
    return breaks


class Studio:
    """The desk that checks a script and puts it on air."""

    def __init__(self, script: ForecastScript) -> None:
        self.script = script

    def rehearsed_line(self) -> str:
        """Return the line, or raise with every rule it breaks."""
        line = self.script.line()
        breaks = score_line(line)
        if breaks:
            raise ValueError("; ".join(str(b) for b in breaks))
        return line

    def air(self, destination: str) -> Path:
        """Write the checked line and prove the aired copy matches."""
        line = self.rehearsed_line()
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(line, encoding="utf-8")
        aired = target.read_text(encoding="utf-8")
        if aired != line:
            raise ValueError("aired copy differs from the script")
        return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Air tonight's deadpan forecast for Zorbania."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="where to write the entry (default: OUTPUT_PATH or /output/entry.txt)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the forecast and write nothing",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="write the entry without printing it",
    )
    parser.add_argument(
        "--beats",
        action="store_true",
        help="print the beat sheet and write nothing",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="print the character and word counts after airing",
    )
    return parser


def resolve_output(explicit: str | None) -> str:
    if explicit:
        return explicit
    return os.environ.get("OUTPUT_PATH", DEFAULT_ENTRY_PATH)


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    studio = Studio(tonight())
    try:
        line = studio.rehearsed_line()
    except ValueError as problem:
        print(f"forecast fails the rules: {problem}", file=sys.stderr)
        return 1
    if args.check:
        print(
            f"forecast OK: {len(line)} characters, "
            f"{studio.script.word_count()} words, one line"
        )
        return 0
    if args.beats:
        print(studio.script.beat_sheet())
        return 0
    try:
        target = studio.air(resolve_output(args.output))
    except ValueError as problem:
        print(f"broadcast failed: {problem}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(line)
    if args.report:
        print(
            f"aired to {target} "
            f"({len(line)} chars, fingerprint {studio.script.fingerprint()})",
            file=sys.stderr,
        )
    else:
        print(f"broadcast to {target}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
