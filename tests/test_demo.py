"""Tests for the bundled demo model and demo file writer."""

import json

from prompt_diff.demo import EVAL_CASES, write_demo_files
from prompt_diff.demo_model import demo_model
from prompt_diff.harness import EvalCase, run_ab, summarize


def test_write_demo_files_creates_all_files(tmp_path):
    paths = write_demo_files(tmp_path / "demo")
    assert paths["v1"].is_file()
    assert paths["v2"].is_file()
    assert paths["eval"].is_file()
    assert paths["v1"].read_text(encoding="utf-8").strip()
    assert paths["v2"].read_text(encoding="utf-8").strip()
    assert paths["v1"].read_text() != paths["v2"].read_text()


def test_write_demo_files_eval_is_valid_jsonl(tmp_path):
    paths = write_demo_files(tmp_path)
    lines = paths["eval"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(EVAL_CASES) == 4
    for line in lines:
        obj = json.loads(line)
        assert isinstance(obj["input"], str) and obj["input"]
        assert isinstance(obj["expected_keywords"], list)


def test_demo_model_is_deterministic():
    prompt = "Give a detailed answer with concrete checks."
    case_input = "Why is my database query so slow?"
    assert demo_model(prompt, case_input) == demo_model(prompt, case_input)


def test_demo_model_detail_directive_adds_keywords():
    case_input = "Why is my database query so slow?"
    brief = demo_model("Answer the user's question briefly.", case_input)
    detailed = demo_model(
        "Give a detailed answer. Name the key technical terms.", case_input
    )
    assert "index" in detailed
    assert "index" not in brief
    assert "database" in brief  # brief answers still name the topic


def test_demo_model_unknown_topic_ties_regardless_of_prompt():
    case_input = "Explain recursion to a beginner"
    out_a = demo_model("Answer briefly.", case_input)
    out_b = demo_model("Give a detailed answer with concrete steps.", case_input)
    assert out_a == out_b


def test_demo_ab_end_to_end():
    """The shipped demo prompts + eval set should produce wins and a tie, no losses."""
    cases = [
        EvalCase(c["input"], c["expected_keywords"]) for c in EVAL_CASES
    ]
    from prompt_diff.demo import PROMPT_V1, PROMPT_V2

    totals = summarize(run_ab(PROMPT_V1, PROMPT_V2, cases, demo_model))
    assert totals["total"] == 4
    assert totals["wins"] >= 1
    assert totals["ties"] >= 1
    assert totals["losses"] == 0
