"""Tests for prompt_diff.cli: diff, eval, and demo commands."""

import sys

import pytest

from prompt_diff.cli import build_parser, main


def _run_cli(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["prompt-diff"] + argv)


def test_cli_diff_two_files(tmp_path, capsys, monkeypatch):
    v1 = tmp_path / "v1.txt"
    v2 = tmp_path / "v2.txt"
    v1.write_text("the quick brown fox", encoding="utf-8")
    v2.write_text("the quick red fox jumps", encoding="utf-8")
    _run_cli(monkeypatch, [str(v1), str(v2), "--no-color"])
    assert main() == 0
    out = capsys.readouterr().out
    assert "- brown" in out
    assert "+ red" in out
    assert "words:" in out and "added" in out


def test_cli_diff_identical_files(tmp_path, capsys, monkeypatch):
    v1 = tmp_path / "v1.txt"
    v2 = tmp_path / "v2.txt"
    v1.write_text("same prompt", encoding="utf-8")
    v2.write_text("same prompt", encoding="utf-8")
    _run_cli(monkeypatch, [str(v1), str(v2), "--no-color"])
    assert main() == 0
    out = capsys.readouterr().out
    assert "0 added, 0 removed, 0 changed" in out


def test_cli_diff_missing_file_returns_error(capsys, monkeypatch):
    _run_cli(monkeypatch, ["nope1.txt", "nope2.txt"])
    assert main() == 2
    assert "cannot read file" in capsys.readouterr().err


def test_cli_diff_with_eval_reports_win_tie_loss(tmp_path, capsys, monkeypatch):
    v1 = tmp_path / "v1.txt"
    v2 = tmp_path / "v2.txt"
    v1.write_text("Answer the user's question briefly.", encoding="utf-8")
    v2.write_text(
        "Give a detailed answer. Name the key technical terms.", encoding="utf-8"
    )
    eval_path = tmp_path / "eval.jsonl"
    eval_path.write_text(
        '{"input": "Why is my database query so slow?", '
        '"expected_keywords": ["database", "index", "query"]}\n',
        encoding="utf-8",
    )
    _run_cli(monkeypatch, [str(v1), str(v2), "--eval", str(eval_path), "--no-color"])
    assert main() == 0
    out = capsys.readouterr().out
    assert "win" in out
    assert "Totals:" in out


def test_cli_demo_writes_files_and_runs_ab(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_cli(monkeypatch, ["demo"])
    assert main() == 0
    out = capsys.readouterr().out
    assert (tmp_path / "prompt_v1.txt").is_file()
    assert (tmp_path / "prompt_v2.txt").is_file()
    assert (tmp_path / "eval.jsonl").is_file()
    assert "win" in out
    assert "tie" in out
    assert "Totals:" in out


def test_cli_no_args_prints_usage_and_errors(capsys, monkeypatch):
    _run_cli(monkeypatch, [])
    assert main() == 2
    assert "expected two prompt files" in capsys.readouterr().err


def test_cli_demo_rejects_eval_flag(monkeypatch):
    _run_cli(monkeypatch, ["demo", "--eval", "x.jsonl"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2


def test_cli_version_flag(capsys, monkeypatch):
    _run_cli(monkeypatch, ["--version"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


def test_parser_has_prompt_diff_prog():
    assert build_parser().prog == "prompt-diff"
