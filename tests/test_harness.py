"""Tests for prompt_diff.harness: scoring, run_ab, summarize, load_cases."""

import json

import pytest

from prompt_diff.harness import (
    EvalCase,
    keyword_score,
    load_cases,
    run_ab,
    summarize,
)


def _stub_model(prompt: str, case_input: str) -> str:
    """Stub model returning canned outputs keyed by (prompt, input)."""
    table = {
        ("A", "win-case"): "alpha",
        ("B", "win-case"): "alpha beta",
        ("A", "loss-case"): "alpha beta",
        ("B", "loss-case"): "alpha",
        ("A", "tie-case"): "alpha",
        ("B", "tie-case"): "alpha",
    }
    return table[(prompt, case_input)]


def test_keyword_score_counts_case_insensitive_matches():
    assert keyword_score("The INDEX speeds up the query", ["index", "query"]) == 2
    assert keyword_score("nothing relevant", ["index", "query"]) == 0
    assert keyword_score("index index index", ["index"]) == 1  # counted once


def test_keyword_score_ignores_empty_keywords():
    assert keyword_score("some output", ["", "some"]) == 1


def test_run_ab_win_from_b_perspective():
    results = run_ab("A", "B", [EvalCase("win-case", ["alpha", "beta"])], _stub_model)
    result = results[0]
    assert (result.score_a, result.score_b) == (1, 2)
    assert result.verdict == "win"


def test_run_ab_loss_from_b_perspective():
    results = run_ab("A", "B", [EvalCase("loss-case", ["alpha", "beta"])], _stub_model)
    result = results[0]
    assert (result.score_a, result.score_b) == (2, 1)
    assert result.verdict == "loss"


def test_run_ab_tie_on_equal_scores():
    results = run_ab("A", "B", [EvalCase("tie-case", ["alpha"])], _stub_model)
    assert results[0].verdict == "tie"


def test_run_ab_passes_prompt_and_input_to_model():
    seen = []

    def spy(prompt: str, case_input: str) -> str:
        seen.append((prompt, case_input))
        return ""

    run_ab("prompt-a", "prompt-b", [EvalCase("hello", [])], spy)
    assert seen == [("prompt-a", "hello"), ("prompt-b", "hello")]


def test_summarize_totals():
    cases = [
        EvalCase("win-case", ["alpha", "beta"]),
        EvalCase("loss-case", ["alpha", "beta"]),
        EvalCase("tie-case", ["alpha"]),
    ]
    totals = summarize(run_ab("A", "B", cases, _stub_model))
    assert totals == {"wins": 1, "losses": 1, "ties": 1, "total": 3}


def test_summarize_empty_results():
    assert summarize([]) == {"wins": 0, "losses": 0, "ties": 0, "total": 0}


def test_load_cases_reads_jsonl(tmp_path):
    path = tmp_path / "eval.jsonl"
    path.write_text(
        '{"input": "q1", "expected_keywords": ["a", "b"]}\n'
        "\n"  # blank lines are skipped
        '{"input": "q2"}\n',
        encoding="utf-8",
    )
    cases = load_cases(path)
    assert len(cases) == 2
    assert cases[0] == EvalCase(input="q1", expected_keywords=["a", "b"])
    assert cases[1] == EvalCase(input="q2", expected_keywords=[])


def test_load_cases_rejects_invalid_json(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"input": "ok"}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_cases(path)


def test_load_cases_rejects_missing_input_key(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps({"expected_keywords": ["a"]}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'input'"):
        load_cases(path)


def test_load_cases_rejects_non_string_keywords(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps({"input": "q", "expected_keywords": ["a", 42]}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="expected_keywords"):
        load_cases(path)


def test_load_cases_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no eval cases"):
        load_cases(path)
