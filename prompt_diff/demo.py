"""Writes the demo prompt versions and eval set used by ``prompt-diff demo``."""

from __future__ import annotations

import json
from pathlib import Path

PROMPT_V1 = "You are a helpful assistant. Answer the user's question briefly."

PROMPT_V2 = (
    "You are a helpful assistant. Give a detailed answer. "
    "Name the key technical terms involved and suggest one concrete check "
    "the user can run."
)

EVAL_CASES = [
    {
        "input": "How do I debug a Python KeyError in my code?",
        "expected_keywords": ["python", "dictionary", "key"],
    },
    {
        "input": "Why is my database query so slow?",
        "expected_keywords": ["database", "index", "query"],
    },
    {
        "input": "My API returns 500 errors under load",
        "expected_keywords": ["api", "log", "server"],
    },
    {
        "input": "Explain recursion to a beginner",
        "expected_keywords": ["explain", "recursion"],
    },
]


def write_demo_files(directory: str | Path) -> dict[str, Path]:
    """Write ``prompt_v1.txt``, ``prompt_v2.txt`` and ``eval.jsonl`` to ``directory``.

    Returns a dict of the written paths (``"v1"``, ``"v2"``, ``"eval"``).
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    v1_path = directory / "prompt_v1.txt"
    v2_path = directory / "prompt_v2.txt"
    eval_path = directory / "eval.jsonl"
    v1_path.write_text(PROMPT_V1 + "\n", encoding="utf-8")
    v2_path.write_text(PROMPT_V2 + "\n", encoding="utf-8")
    eval_path.write_text(
        "\n".join(json.dumps(case) for case in EVAL_CASES) + "\n",
        encoding="utf-8",
    )
    return {"v1": v1_path, "v2": v2_path, "eval": eval_path}
