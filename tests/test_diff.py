"""Tests for prompt_diff.diff: word-level diffing and stats."""

from prompt_diff.diff import diff_stats, format_diff, stat_line, tokenize, word_diff


def test_tokenize_splits_on_whitespace():
    assert tokenize("hello  world\nnew") == ["hello", "world", "new"]
    assert tokenize("") == []


def test_identical_texts_have_empty_diff():
    text = "You are a helpful assistant. Answer briefly."
    segments = word_diff(text, text)
    assert segments, "expected at least the equal segment"
    assert all(tag == "equal" for tag, _ in segments)
    stats = diff_stats(text, text)
    assert (stats.added, stats.removed, stats.changed) == (0, 0, 0)
    out = format_diff(text, text, use_color=False)
    assert not any(
        line.startswith(("+ ", "- ")) for line in out.splitlines()
    ), "identical texts must produce no +/- lines"


def test_stat_counts_replace_as_changed_plus_surplus():
    # "brown" -> "red" is one changed word; "jumps" is one added word.
    stats = diff_stats("the quick brown fox", "the quick red fox jumps")
    assert stats.changed == 1
    assert stats.added == 1
    assert stats.removed == 0


def test_stat_counts_pure_deletion():
    stats = diff_stats("one two three", "one three")
    assert (stats.added, stats.removed, stats.changed) == (0, 1, 0)


def test_stat_counts_pure_insertion():
    stats = diff_stats("one three", "one two three")
    assert (stats.added, stats.removed, stats.changed) == (1, 0, 0)


def test_stat_counts_replace_with_surplus_on_old_side():
    # "a b c" -> "x": 1 changed, 2 removed.
    stats = diff_stats("a b c", "x")
    assert (stats.added, stats.removed, stats.changed) == (0, 2, 1)


def test_format_uses_plus_minus_prefixes():
    out = format_diff("hello world", "hello there", use_color=False)
    lines = out.splitlines()
    assert any(line.startswith("- ") for line in lines)
    assert any(line.startswith("+ ") for line in lines)
    assert any(line.startswith("  ") for line in lines)  # unchanged context


def test_format_color_codes_only_when_requested():
    colored = format_diff("hello world", "hello there", use_color=True)
    assert "\x1b[" in colored
    plain = format_diff("hello world", "hello there", use_color=False)
    assert "\x1b[" not in plain


def test_stat_line_format():
    line = stat_line("one two three", "one three")
    assert line == "words: 0 added, 1 removed, 0 changed"


def test_diff_against_empty_text():
    stats = diff_stats("", "some words here")
    assert (stats.added, stats.removed, stats.changed) == (3, 0, 0)
    stats = diff_stats("some words here", "")
    assert (stats.added, stats.removed, stats.changed) == (0, 3, 0)
