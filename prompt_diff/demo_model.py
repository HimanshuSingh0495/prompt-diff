"""Bundled fake model for offline demos.

Deterministic and keyword-based: it needs no API keys and makes no network
calls. It is deliberately prompt-sensitive -- directives like "detailed" or
"concrete" in the prompt change how many topic keywords appear in the output
-- so ``prompt-diff demo`` shows a meaningful A/B comparison.

This is a toy for demos and tests, not a real language model.
"""

from __future__ import annotations

#: Topic trigger word -> keywords the fake model "knows" about that topic.
_TOPICS: dict[str, list[str]] = {
    "python": ["python", "dictionary", "key"],
    "database": ["database", "index", "query"],
    "api": ["api", "log", "server"],
}

#: Prompt directives that make the fake model produce a more detailed answer.
_DETAIL_MARKERS = ("detailed", "thorough", "concrete", "technical terms")


def demo_model(prompt: str, case_input: str) -> str:
    """Deterministic fake model: ``(prompt, input) -> output``.

    If the input mentions a known topic, the output names that topic's
    keywords -- all of them when the prompt asks for detail, just the topic
    word otherwise. Inputs about unknown topics get a prompt-independent
    fallback answer, so both prompts tie on those cases.
    """
    lowered_input = case_input.lower()
    topic_words: list[str] | None = None
    for trigger, words in _TOPICS.items():
        if trigger in lowered_input:
            topic_words = words
            break

    if topic_words is None:
        fallback = case_input.split()[:2]
        return "General answer mentioning: " + ", ".join(fallback) + "."

    prompt_lower = prompt.lower()
    detailed = any(marker in prompt_lower for marker in _DETAIL_MARKERS)
    keywords = topic_words if detailed else topic_words[:1]
    topic = topic_words[0]
    if detailed:
        return (
            f"Here is a detailed answer about {topic}. "
            f"Key technical terms: {', '.join(keywords)}. "
            f"One concrete check you can run: verify {keywords[-1]}."
        )
    return f"Brief answer about {topic}: {keywords[0]}."
