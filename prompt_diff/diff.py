"""Word-level diffing of two prompt texts, built on :mod:`difflib`."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

_WORD_RE = re.compile(r"\S+")

_RED = "\033[31m"
_GREEN = "\033[32m"
_RESET = "\033[0m"


def tokenize(text: str) -> list[str]:
    """Split text into word tokens (whitespace-separated; punctuation stays attached)."""
    return _WORD_RE.findall(text)


def _opcodes(a: str, b: str) -> list[tuple[str, int, int, int, int]]:
    a_tokens = tokenize(a)
    b_tokens = tokenize(b)
    matcher = difflib.SequenceMatcher(a=a_tokens, b=b_tokens, autojunk=False)
    return matcher.get_opcodes()


def word_diff(a: str, b: str) -> list[tuple[str, str]]:
    """Break two texts into word-level diff segments.

    Returns a list of ``(tag, words)`` tuples where ``tag`` is one of
    ``"equal"``, ``"delete"`` or ``"insert"``. A ``replace`` opcode is
    surfaced as a ``"delete"`` segment followed by an ``"insert"`` segment.
    """
    a_tokens = tokenize(a)
    b_tokens = tokenize(b)
    segments: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in _opcodes(a, b):
        if tag == "equal":
            segments.append(("equal", " ".join(a_tokens[i1:i2])))
        elif tag == "delete":
            segments.append(("delete", " ".join(a_tokens[i1:i2])))
        elif tag == "insert":
            segments.append(("insert", " ".join(b_tokens[j1:j2])))
        elif tag == "replace":
            segments.append(("delete", " ".join(a_tokens[i1:i2])))
            segments.append(("insert", " ".join(b_tokens[j1:j2])))
    return segments


@dataclass
class DiffStats:
    """Word counts describing how ``b`` differs from ``a``."""

    added: int = 0
    removed: int = 0
    changed: int = 0

    @property
    def total(self) -> int:
        """Total number of words that differ."""
        return self.added + self.removed + self.changed


def diff_stats(a: str, b: str) -> DiffStats:
    """Count added/removed/changed words between two texts.

    Words paired off inside a replacement count as ``changed``; surplus
    words on either side of a replacement count as ``added``/``removed``.
    """
    stats = DiffStats()
    for tag, i1, i2, j1, j2 in _opcodes(a, b):
        if tag == "delete":
            stats.removed += i2 - i1
        elif tag == "insert":
            stats.added += j2 - j1
        elif tag == "replace":
            n_old, n_new = i2 - i1, j2 - j1
            stats.changed += min(n_old, n_new)
            stats.removed += max(0, n_old - n_new)
            stats.added += max(0, n_new - n_old)
    return stats


def format_diff(a: str, b: str, use_color: bool = False) -> str:
    """Render the word-level diff as lines.

    Removed words are prefixed with ``- `` (red when ``use_color``),
    added words with ``+ `` (green), unchanged words with two spaces.
    Identical texts produce only unchanged lines.
    """

    def paint(text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if use_color else text

    lines: list[str] = []
    for tag, words in word_diff(a, b):
        if tag == "delete":
            lines.append(paint(f"- {words}", _RED))
        elif tag == "insert":
            lines.append(paint(f"+ {words}", _GREEN))
        else:
            lines.append(f"  {words}")
    return "\n".join(lines)


def stat_line(a: str, b: str) -> str:
    """One-line summary like ``"3 added, 2 removed, 1 changed"`` (words)."""
    stats = diff_stats(a, b)
    return (
        f"words: {stats.added} added, "
        f"{stats.removed} removed, "
        f"{stats.changed} changed"
    )
