"""Tests for py_mono/skill/validator.py's Markdown-fence stripping (ISS-011).

The previous implementation only stripped a leading fence when the whole
output started with one, and only stripped a trailing fence if a leading one
had already been found — so a trailing-only fence, or any preamble text
before the leading fence, was left in place and would fail ast.parse()."""

from py_mono.skill.validator import _strip_markdown_fences


def test_symmetric_fence_is_stripped():
    code = "```python\nx = 1\n```"
    assert _strip_markdown_fences(code) == "x = 1"


def test_symmetric_fence_without_language_tag_is_stripped():
    code = "```\nx = 1\n```"
    assert _strip_markdown_fences(code) == "x = 1"


def test_leading_fence_with_no_trailing_fence_is_stripped():
    code = "```python\nx = 1"
    assert _strip_markdown_fences(code) == "x = 1"


def test_trailing_only_fence_is_stripped():
    """A response with no leading fence but a stray trailing fence — the
    exact shape the previous implementation left unstripped."""
    code = "x = 1\n```"
    assert _strip_markdown_fences(code) == "x = 1"


def test_preamble_before_fence_is_stripped():
    """A response with explanatory text before the fence — previously not
    stripped at all, since the code didn't start with the fence."""
    code = "Here's the code:\n```python\nx = 1\n```"
    assert _strip_markdown_fences(code) == "x = 1"


def test_no_fence_at_all_is_returned_unchanged():
    code = "x = 1"
    assert _strip_markdown_fences(code) == "x = 1"


def test_multiline_fenced_code_preserves_internal_structure():
    code = "```python\ndef f():\n    return 1\n```"
    assert _strip_markdown_fences(code) == "def f():\n    return 1"
