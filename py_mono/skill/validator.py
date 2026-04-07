# py_mono/skill/validator.py
"""
Validation layer for LLM-generated skill files.

Validates both SKILL.md and skill.py before saving to disk.

Validation results:
    SkillMdValidationResult  — result of SKILL.md validation
    SkillPyValidationResult  — result of skill.py validation

See ADR-011 and ADR-013 for design details.
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Forbidden patterns for skill.py
# ---------------------------------------------------------------------------
TOOL_USAGE_HINT = "Retrieve tools via context.agent_tools.get(...) and execute using tool.run(...)"

FORBIDDEN_PATTERNS = [
    (r"\bos\.system\s*\(", "os.system() is forbidden — use shell tool  — {TOOL_USAGE_HINT}"),
    (r"\bsubprocess\b", "subprocess is forbidden — use shell tool  — {TOOL_USAGE_HINT}"),
    (r"\bexec\s*\(", "exec() is forbidden"),
    (r"\beval\s*\(", "eval() is forbidden"),
    (r"\b__import__\s*\(", "__import__() is forbidden"),
    (r"\bopen\s*\(\s*['\"]\/", "open() with absolute path is forbidden — use context.workspace_root"),
    (r"\brequests\b", "requests is forbidden — use MCP tools for network calls"),
    (r"\bhttpx\b", "httpx is forbidden — use MCP tools for network calls"),
    (r"\burllib\b", "urllib is forbidden — use MCP tools for network calls"),
    (r"\bsocket\b", "socket is forbidden"),
    (r"\.func\s*\(", "Direct tool.func() usage is forbidden — use tool.run({...})"),
]

# Allowed top-level imports in skill.py
ALLOWED_IMPORT_MODULES = {
    "py_mono",
    "pathlib",
    "typing",
    "json",
    "re",
    "csv",
    "os",       # os.path only — forbidden patterns catch os.system etc.
    "datetime",
    "collections",
    "itertools",
    "functools",
    "math",
    "string",
    "textwrap",
    "dataclasses",
    "enum",
    "abc",
}


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SkillMdValidationResult:
    valid: bool
    warnings: List[str] = field(default_factory=list)
    fixed_content: Optional[str] = None   # content after auto-fixes applied

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


@dataclass
class SkillPyValidationResult:
    valid: bool
    forbidden_patterns: List[str] = field(default_factory=list)
    syntax_errors: List[str] = field(default_factory=list)
    structure_errors: List[str] = field(default_factory=list)

    def has_forbidden(self) -> bool:
        return len(self.forbidden_patterns) > 0

    def has_syntax_errors(self) -> bool:
        return len(self.syntax_errors) > 0

    def failure_reason(self) -> str:
        """Return a human-readable summary of all failures."""
        lines = []
        if self.forbidden_patterns:
            lines.append("Forbidden patterns found:")
            for p in self.forbidden_patterns:
                lines.append(f"  - {p}")
        if self.syntax_errors:
            lines.append("Syntax errors:")
            for e in self.syntax_errors:
                lines.append(f"  - {e}")
        if self.structure_errors:
            lines.append("Structure errors:")
            for e in self.structure_errors:
                lines.append(f"  - {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# SKILL.md validator
# ---------------------------------------------------------------------------

def validate_skill_md(
    content: str,
    skill_name: str,
    known_tools: Optional[List[str]] = None,
) -> SkillMdValidationResult:
    """
    Validate and auto-fix SKILL.md content.

    Checks:
    - Valid YAML front-matter
    - Required fields present (name, description, status)
    - status is "proposed" (force if not)
    - allowed_tools only reference known tools (warn if not)

    Args:
        content      : raw SKILL.md string from LLM
        skill_name   : expected skill name
        known_tools  : list of known tool names (optional)

    Returns:
        SkillMdValidationResult
    """
    warnings = []
    fixed_content = content

    # Check for front-matter
    if not content.strip().startswith("---"):
        warnings.append("Missing YAML front-matter — SKILL.md may be incomplete")
        return SkillMdValidationResult(valid=True, warnings=warnings, fixed_content=content)

    # Extract front-matter
    lines = content.splitlines()
    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        warnings.append("Unclosed YAML front-matter block")
        return SkillMdValidationResult(valid=True, warnings=warnings, fixed_content=content)

    yaml_text = "\n".join(lines[1:end])

    try:
        meta = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as e:
        warnings.append(f"Invalid YAML front-matter: {e}")
        return SkillMdValidationResult(valid=True, warnings=warnings, fixed_content=content)

    # Check name
    if "name" not in meta:
        warnings.append("Missing 'name' field in front-matter")
    elif meta["name"] != skill_name:
        warnings.append(
            f"name field '{meta['name']}' does not match expected '{skill_name}' — auto-correcting"
        )
        fixed_content = fixed_content.replace(
            f"name: {meta['name']}", f"name: {skill_name}", 1
        )

    # Check description
    if "description" not in meta:
        warnings.append("Missing 'description' field in front-matter")

    # Force status to proposed
    status = meta.get("status", "proposed")
    if status != "proposed":
        warnings.append(
            f"status was '{status}' — forced to 'proposed' for safety"
        )
        fixed_content = re.sub(
            r"status:\s*\S+",
            "status: proposed",
            fixed_content,
            count=1
        )

    # Check allowed_tools against known tools
    if known_tools and "allowed_tools" in meta:
        raw_tools = meta["allowed_tools"]
        if isinstance(raw_tools, str):
            skill_tools = [t.strip() for t in raw_tools.split(",")]
        elif isinstance(raw_tools, list):
            skill_tools = raw_tools
        else:
            skill_tools = []

        unknown = [t for t in skill_tools if t and t not in known_tools]
        if unknown:
            warnings.append(
                f"allowed_tools references unknown tools: {unknown} — these will be ignored"
            )

    return SkillMdValidationResult(
        valid=True,
        warnings=warnings,
        fixed_content=fixed_content,
    )


# ---------------------------------------------------------------------------
# skill.py validator
# ---------------------------------------------------------------------------

def validate_skill_py(
    code: str,
    skill_name: str,
) -> SkillPyValidationResult:
    """
    Validate LLM-generated skill.py code.

    Checks:
    1. No forbidden patterns (hard fail triggers)
    2. Valid Python syntax
    3. Contains a Skill subclass
    4. Subclass implements name(), description(), run()
    5. name() returns correct skill_name

    Args:
        code        : raw Python code string from LLM
        skill_name  : expected skill name

    Returns:
        SkillPyValidationResult
    """
    forbidden = []
    syntax_errors = []
    structure_errors = []

    # Strip markdown fences if LLM included them despite instructions
    code = _strip_markdown_fences(code)

    # 1. Check forbidden patterns
    for pattern, message in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            forbidden.append(message)

    # 2. Check syntax
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        syntax_errors.append(f"SyntaxError at line {e.lineno}: {e.msg}")
        return SkillPyValidationResult(
            valid=False,
            forbidden_patterns=forbidden,
            syntax_errors=syntax_errors,
            structure_errors=structure_errors,
        )

    # 3. Find Skill subclass
    skill_classes = _find_skill_subclasses(tree)
    if not skill_classes:
        structure_errors.append(
            "No Skill subclass found — class must extend Skill from py_mono.skill.base"
        )
    sig_error = _check_run_signature(tree)
    if sig_error:
        structure_errors.append(sig_error)

    # 4. Check required methods
    for cls_node in skill_classes:
        methods = {n.name for n in ast.walk(cls_node) if isinstance(n, ast.FunctionDef)}
        for required in ("name", "description", "run"):
            if required not in methods:
                structure_errors.append(
                    f"Skill subclass '{cls_node.name}' is missing required method: {required}()"
                )

    import_error = _check_required_imports(code)
    if import_error:
        structure_errors.append(import_error)
        
    # 5. Check name() returns correct skill_name
    if skill_classes:
        name_check = _check_name_return(tree, skill_name)
        if name_check:
            structure_errors.append(name_check)

    valid = (
        len(forbidden) == 0
        and len(syntax_errors) == 0
        and len(structure_errors) == 0
    )

    return SkillPyValidationResult(
        valid=valid,
        forbidden_patterns=forbidden,
        syntax_errors=syntax_errors,
        structure_errors=structure_errors,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_markdown_fences(code: str) -> str:
    """Remove ```python ... ``` or ``` ... ``` fences if present."""
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        # Remove first line (```python or ```)
        lines = lines[1:]
        # Remove last ``` if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    return code


def _find_skill_subclasses(tree: ast.Module) -> List[ast.ClassDef]:
    """Find all class definitions that appear to subclass Skill."""
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = ""
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name == "Skill":
                    result.append(node)
    return result

def _check_run_signature(tree: ast.Module) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            args = [arg.arg for arg in node.args.args]
            if args != ["self", "request", "context"]:
                return "run() must have signature: (self, request, context)"
    return None

def _check_name_return(tree: ast.Module, expected_name: str) -> Optional[str]:
    """
    Check if any name() method returns the expected skill_name string.
    Returns an error message if not, or None if OK.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "name":
            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    if isinstance(child.value, ast.Constant):
                        if child.value.value == expected_name:
                            return None  # found correct return
                        else:
                            return (
                                f"name() returns '{child.value.value}' "
                                f"but expected '{expected_name}'"
                            )
    return f"Could not verify name() returns '{expected_name}'"

def _check_required_imports(code: str) -> Optional[str]:
    if "from py_mono.skill.base import Skill, SkillContext" not in code:
        return "Missing required import: Skill, SkillContext from py_mono.skill.base"
    return None

