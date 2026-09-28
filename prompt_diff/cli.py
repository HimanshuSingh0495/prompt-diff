"""Command-line interface for prompt-diff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Sequence

from prompt_diff import __version__
from prompt_diff.demo import write_demo_files
from prompt_diff.demo_model import demo_model
from prompt_diff.diff import format_diff, stat_line
from prompt_diff.harness import CaseResult, load_cases, run_ab, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-diff",
        description=(
            "Word-level diffs for two prompt versions, "
            "plus A/B evals against a labeled eval set."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="PATH",
        help="two prompt files to diff, or 'demo' for a zero-setup demo",
    )
    parser.add_argument(
        "--eval",
        metavar="EVAL.jsonl",
        help="run both prompts through the bundled demo model on this eval set "
        "and report win/tie/loss per case",
    )
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument(
        "--color", action="store_true", help="force ANSI colors even when piped"
    )
    color_group.add_argument(
        "--no-color", action="store_true", help="disable ANSI colors"
    )
    return parser


def _use_color(args: argparse.Namespace) -> bool:
    if args.no_color:
        return False
    if args.color:
        return True
    return sys.stdout.isatty()


def _print_results_table(results: Sequence[CaseResult]) -> None:
    header = ("#", "input", "v1 kw", "v2 kw", "result")
    rows: List[tuple[str, str, str, str, str]] = []
    for i, result in enumerate(results, start=1):
        case_input = result.case.input
        if len(case_input) > 42:
            case_input = case_input[:39] + "..."
        n_keywords = len(result.case.expected_keywords)
        rows.append(
            (
                str(i),
                case_input,
                f"{result.score_a}/{n_keywords}",
                f"{result.score_b}/{n_keywords}",
                result.verdict,
            )
        )
    widths = [
        max([len(header[j])] + [len(row[j]) for row in rows]) for j in range(len(header))
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*header))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))


def _run_eval(prompt_a: str, prompt_b: str, eval_path: str) -> int:
    try:
        cases = load_cases(eval_path)
    except (OSError, ValueError) as exc:
        print(f"prompt-diff: {exc}", file=sys.stderr)
        return 2
    print("--- A/B eval (bundled demo model, fully offline) ---")
    results = run_ab(prompt_a, prompt_b, cases, demo_model)
    _print_results_table(results)
    totals = summarize(results)
    print(
        f"Totals: {totals['wins']} wins, {totals['losses']} losses, "
        f"{totals['ties']} ties (of {totals['total']} cases)"
    )
    print("win/tie/loss are scored from v2's perspective "
          "(win = v2 matched more expected keywords).")
    print("Note: keyword overlap is a rough proxy for prompt quality, "
          "not a quality judgment.")
    return 0


def _cmd_demo(use_color: bool) -> int:
    paths = write_demo_files(Path.cwd())
    print(
        f"Wrote demo files to {Path.cwd()}: "
        "prompt_v1.txt, prompt_v2.txt, eval.jsonl\n"
    )
    prompt_a = paths["v1"].read_text(encoding="utf-8")
    prompt_b = paths["v2"].read_text(encoding="utf-8")
    print("--- word diff: prompt_v1.txt vs prompt_v2.txt ---")
    print(format_diff(prompt_a, prompt_b, use_color=use_color))
    print(stat_line(prompt_a, prompt_b))
    print()
    return _run_eval(prompt_a, prompt_b, str(paths["eval"]))


def _cmd_diff(file_a: str, file_b: str, use_color: bool, eval_path: str | None) -> int:
    try:
        prompt_a = Path(file_a).read_text(encoding="utf-8")
        prompt_b = Path(file_b).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"prompt-diff: cannot read file: {exc}", file=sys.stderr)
        return 2
    print(format_diff(prompt_a, prompt_b, use_color=use_color))
    print(stat_line(prompt_a, prompt_b))
    if eval_path:
        print()
        return _run_eval(prompt_a, prompt_b, eval_path)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``prompt-diff`` console script."""
    parser = build_parser()
    args = parser.parse_args(argv)
    use_color = _use_color(args)

    if args.paths == ["demo"]:
        if args.eval:
            parser.error("--eval cannot be combined with 'demo'")
        return _cmd_demo(use_color)
    if len(args.paths) == 2:
        return _cmd_diff(args.paths[0], args.paths[1], use_color, args.eval)
    parser.print_usage(sys.stderr)
    print(
        "prompt-diff: expected two prompt files, or 'demo'",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
