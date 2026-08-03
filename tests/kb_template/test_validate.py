"""Tests for the kb-template validator (schema, wikilink, and promotion-rule checks)."""

import sys
from pathlib import Path

import pytest

KB_TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "kb-template"
sys.path.insert(0, str(KB_TEMPLATE_ROOT))

from validator.validate import validate_tree  # noqa: E402

VALID_FRONT_MATTER = """---
title: Test Document
type: canonical-doc
status: canonical
project: kb-template
authority: doctrine
created: 2026-08-03
updated: 2026-08-03
canonical: true
related: []
---

# Test Document

Body text with no links.
"""


def write_doc(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_document_passes(tmp_path):
    write_doc(tmp_path / "topics" / "doc.md", VALID_FRONT_MATTER)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is True
    assert results[0].schema_errors == []
    assert results[0].wikilink_errors == []
    assert results[0].promotion_errors == []


def test_missing_required_field_fails(tmp_path):
    content = VALID_FRONT_MATTER.replace("authority: doctrine\n", "")
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is False
    assert any("authority" in e for e in results[0].schema_errors)


def test_invalid_enum_value_fails(tmp_path):
    content = VALID_FRONT_MATTER.replace("status: canonical", "status: published")
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is False
    assert any("status" in e and "published" in e for e in results[0].schema_errors)


def test_non_list_related_field_fails(tmp_path):
    content = VALID_FRONT_MATTER.replace("related: []", "related: not-a-list")
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is False
    assert any("related" in e for e in results[0].schema_errors)


def test_unresolved_wikilink_fails(tmp_path):
    content = VALID_FRONT_MATTER + "\nSee [[nonexistent-target]] for more.\n"
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is False
    assert any("nonexistent-target" in e for e in results[0].wikilink_errors)


def test_resolvable_wikilink_with_alias_and_anchor_passes(tmp_path):
    write_doc(tmp_path / "other.md", VALID_FRONT_MATTER)
    content = VALID_FRONT_MATTER + (
        "\nSee [[other|Other Doc]] and [[other#section]] for more.\n"
    )
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    doc_result = next(r for r in results if r.path.name == "doc.md")
    assert doc_result.wikilink_errors == []


def test_case_insensitive_wikilink_resolves(tmp_path):
    write_doc(tmp_path / "Other-Doc.md", VALID_FRONT_MATTER)
    content = VALID_FRONT_MATTER + "\nSee [[other-doc]] for more.\n"
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    doc_result = next(r for r in results if r.path.name == "doc.md")
    assert doc_result.wikilink_errors == []


def test_malformed_yaml_reports_parse_error_without_crashing(tmp_path):
    content = "---\ntitle: [unclosed\n---\nBody\n"
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is False
    assert results[0].schema_errors


def test_unclosed_front_matter_block_reports_error(tmp_path):
    content = "---\ntitle: Test\nno closing delimiter here\n"
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is False
    assert any("unclosed" in e for e in results[0].schema_errors)


def test_no_front_matter_at_all_is_not_an_error(tmp_path):
    """A plain Markdown file with no '---' block is prose/instructional content,
    not a KB document, and is not schema-checked."""
    write_doc(tmp_path / "doc.md", "# No front matter here\n\nJust prose.\n")
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].valid is True
    assert results[0].schema_errors == []


def test_wikilink_syntax_shown_in_code_span_is_not_flagged(tmp_path):
    """Illustrating wikilink syntax inside backticks (e.g. docs explaining the
    convention) must not be mistaken for a real, unresolved link."""
    content = VALID_FRONT_MATTER + "\nThe syntax looks like `[[example]]` in prose.\n"
    write_doc(tmp_path / "doc.md", content)
    results = validate_tree(tmp_path)
    assert len(results) == 1
    assert results[0].wikilink_errors == []


def test_promotion_violation_in_raw_folder_fails(tmp_path):
    write_doc(tmp_path / "knowledge" / "raw" / "leaked.md", VALID_FRONT_MATTER)
    results = validate_tree(tmp_path)
    result = next(r for r in results if r.path.name == "leaked.md")
    assert result.valid is False
    assert any("raw" in e for e in result.promotion_errors)


def test_promoted_document_in_topics_passes_promotion_check(tmp_path):
    write_doc(tmp_path / "knowledge" / "topics" / "promoted.md", VALID_FRONT_MATTER)
    results = validate_tree(tmp_path)
    result = next(r for r in results if r.path.name == "promoted.md")
    assert result.promotion_errors == []


def test_draft_document_in_raw_folder_is_not_a_promotion_violation(tmp_path):
    content = VALID_FRONT_MATTER.replace("status: canonical", "status: draft")
    write_doc(tmp_path / "knowledge" / "raw" / "note.md", content)
    results = validate_tree(tmp_path)
    result = next(r for r in results if r.path.name == "note.md")
    assert result.promotion_errors == []


def test_shipped_kb_template_scaffold_is_self_consistent():
    results = validate_tree(KB_TEMPLATE_ROOT)
    failures = [r for r in results if not r.valid]
    assert not failures, f"shipped kb-template/ has validation failures: {failures}"
