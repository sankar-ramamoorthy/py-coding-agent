"""Tests for py_mono/skill/prompts.py's SKILL.md prompt template (ISS-011).

build_skill_md_prompt() previously included a literal, unmarked instruction
line ("- List each constraint as a bullet point.") phrased identically to a
real constraint bullet, with nothing distinguishing it as text for the model
to replace rather than content to keep verbatim — confirmed reproduced: a
real generation run echoed it back into the generated SKILL.md unchanged."""

from py_mono.skill.prompts import build_skill_md_prompt


def _build():
    return build_skill_md_prompt(
        skill_name="demo_skill",
        description="a demo skill",
        available_tools={"list_files": "List files"},
    )


def test_old_ambiguous_constraint_line_is_gone():
    prompt = _build()
    assert "- List each constraint as a bullet point." not in prompt


def test_fillable_sections_are_marked_as_instructions():
    prompt = _build()
    # 3 real placeholders (paragraph, expected-output, constraints) plus 2
    # more mentions of the pattern in the closing Rules reminder.
    assert prompt.count("[INSTRUCTION —") == 5


def test_rules_tell_the_model_not_to_copy_instruction_lines():
    prompt = _build()
    assert "never copy an [INSTRUCTION" in prompt
