"""prompt-diff: word-level diffs for prompt versions, plus A/B evals against labeled cases."""

from prompt_diff.diff import diff_stats, format_diff, word_diff
from prompt_diff.harness import load_cases, run_ab, summarize

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "word_diff",
    "format_diff",
    "diff_stats",
    "run_ab",
    "summarize",
    "load_cases",
]
