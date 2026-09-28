"""A/B testing of two prompts against a labeled eval set.

Scoring is keyword overlap: a prompt scores one point per expected keyword
found (case-insensitively) in its output. This is a rough proxy for prompt
quality, not a quality judgment -- see the README's "How scoring works"
section for the limits.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Sequence

#: A model function takes a prompt and a case input, and returns the model output.
ModelFn = Callable[[str, str], str]


@dataclass
class EvalCase:
    """One labeled eval case: an input plus the keywords a good answer should contain."""

    input: str
    expected_keywords: List[str] = field(default_factory=list)


@dataclass
class CaseResult:
    """The outcome of running both prompts on one case."""

    case: EvalCase
    output_a: str
    output_b: str
    score_a: int
    score_b: int
    #: "win" / "tie" / "loss", always from prompt B's perspective.
    verdict: str


def keyword_score(output: str, expected: Sequence[str]) -> int:
    """Count how many expected keywords appear in the output (case-insensitive)."""
    lowered = output.lower()
    return sum(1 for kw in expected if kw and kw.lower() in lowered)


def run_ab(
    prompt_a: str,
    prompt_b: str,
    cases: Sequence[EvalCase],
    model_fn: ModelFn,
) -> List[CaseResult]:
    """Run both prompts on every case and score the outputs.

    ``verdict`` is ``"win"`` when prompt B's output contains more expected
    keywords than prompt A's, ``"loss"`` when it contains fewer, and
    ``"tie"`` when the counts are equal.
    """
    results: List[CaseResult] = []
    for case in cases:
        output_a = model_fn(prompt_a, case.input)
        output_b = model_fn(prompt_b, case.input)
        score_a = keyword_score(output_a, case.expected_keywords)
        score_b = keyword_score(output_b, case.expected_keywords)
        if score_b > score_a:
            verdict = "win"
        elif score_b < score_a:
            verdict = "loss"
        else:
            verdict = "tie"
        results.append(
            CaseResult(
                case=case,
                output_a=output_a,
                output_b=output_b,
                score_a=score_a,
                score_b=score_b,
                verdict=verdict,
            )
        )
    return results


def summarize(results: Sequence[CaseResult]) -> Dict[str, int]:
    """Total wins/losses/ties across a list of case results (prompt B's perspective)."""
    return {
        "wins": sum(1 for r in results if r.verdict == "win"),
        "losses": sum(1 for r in results if r.verdict == "loss"),
        "ties": sum(1 for r in results if r.verdict == "tie"),
        "total": len(results),
    }


def load_cases(path: str | Path) -> List[EvalCase]:
    """Load eval cases from a JSONL file.

    Each non-blank line must be a JSON object with an ``"input"`` string and
    an optional ``"expected_keywords"`` list of strings.
    """
    path = Path(path)
    cases: List[EvalCase] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON ({exc})") from exc
            if not isinstance(obj, dict) or "input" not in obj:
                raise ValueError(
                    f"{path}:{lineno}: each line must be an object with an 'input' key"
                )
            keywords = obj.get("expected_keywords", [])
            if not isinstance(keywords, list) or not all(
                isinstance(k, str) for k in keywords
            ):
                raise ValueError(
                    f"{path}:{lineno}: 'expected_keywords' must be a list of strings"
                )
            cases.append(
                EvalCase(input=str(obj["input"]), expected_keywords=list(keywords))
            )
    if not cases:
        raise ValueError(f"{path}: no eval cases found")
    return cases
