"""Validator for kb-template documents.

Checks, for every Markdown file under a scaffold root:
  1. Front-matter schema compliance (required fields, enum values, field types)
  2. Wikilink resolution ([[target]] references resolve to a real file)
  3. The promotion rule (status: canonical/active must not live under knowledge/raw/)

See ../docs/schema.md and ../docs/promotion.md for the rules being enforced, and
../../specs/001-kb-template/contracts/validator-cli.md for the CLI contract.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .schema import (
    ALLOWED_AUTHORITY,
    ALLOWED_STATUS,
    ALLOWED_TYPE,
    CANONICAL_STATUSES,
    RAW_FOLDER_NAME,
    REQUIRED_FIELDS,
)

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")

ENUM_FIELDS = {
    "type": ALLOWED_TYPE,
    "status": ALLOWED_STATUS,
    "authority": ALLOWED_AUTHORITY,
}


@dataclass
class ValidationResult:
    path: Path
    valid: bool
    schema_errors: List[str] = field(default_factory=list)
    wikilink_errors: List[str] = field(default_factory=list)
    promotion_errors: List[str] = field(default_factory=list)


def extract_front_matter(content: str) -> Tuple[Optional[dict], List[str], str, bool]:
    """Split a document into (front_matter_dict_or_None, parse_errors, body, attempted).

    ``attempted`` is False for a plain Markdown file with no opening '---' at all —
    such a file is treated as prose/instructional content, not a KB document, and is
    not schema/promotion-checked (though its wikilinks still are). ``attempted`` is
    True once a file opens a front-matter block, even if that block turns out to be
    malformed — an attempted-but-broken block is a real schema error, not silence.

    body is everything after the closing '---' delimiter (or the whole content
    if front matter is missing/malformed, so wikilinks are still checked).
    """
    if not content.strip().startswith("---"):
        return None, [], content, False

    lines = content.splitlines()
    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return None, ["unclosed front-matter block (no closing '---' delimiter)"], content, True

    yaml_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])

    try:
        meta = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return None, [f"invalid YAML front matter: {e}"], body, True

    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        return None, ["front matter did not parse to a mapping"], body, True

    return meta, [], body, True


def validate_schema(meta: dict) -> List[str]:
    errors: List[str] = []

    for f in REQUIRED_FIELDS:
        if f not in meta:
            errors.append(f"missing required field: {f}")

    for f, allowed in ENUM_FIELDS.items():
        if f in meta and meta[f] not in allowed:
            errors.append(
                f"invalid value for '{f}': {meta[f]!r} (allowed: {sorted(allowed)})"
            )

    if "canonical" in meta and not isinstance(meta["canonical"], bool):
        errors.append(f"'canonical' must be a boolean, got {meta['canonical']!r}")

    if "related" in meta and not isinstance(meta["related"], list):
        errors.append(f"'related' must be a list, got {meta['related']!r}")

    return errors


def check_promotion_rule(meta: Optional[dict], relative_path: Path) -> List[str]:
    if not meta:
        return []
    status = meta.get("status")
    if status not in CANONICAL_STATUSES:
        return []
    if RAW_FOLDER_NAME in relative_path.parts:
        return [
            f"promotion-rule violation: status is '{status}' but file is still under "
            f"'{RAW_FOLDER_NAME}/' ({relative_path})"
        ]
    return []


FENCED_CODE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")


def _strip_code_spans(body: str) -> str:
    """Remove fenced and inline code spans so literal `[[example]]` syntax shown
    for illustration isn't mistaken for a real wikilink (matches how Obsidian
    itself treats bracket syntax inside code)."""
    body = FENCED_CODE_PATTERN.sub("", body)
    body = INLINE_CODE_PATTERN.sub("", body)
    return body


def extract_wikilinks(body: str) -> List[str]:
    body = _strip_code_spans(body)
    return [m.group(1).strip() for m in WIKILINK_PATTERN.finditer(body)]


def build_stem_index(root: Path) -> Dict[str, Path]:
    index: Dict[str, Path] = {}
    for md_file in root.rglob("*.md"):
        index[md_file.stem.lower()] = md_file
    return index


def resolve_wikilinks(targets: List[str], index: Dict[str, Path], source: Path) -> List[str]:
    errors: List[str] = []
    for target in targets:
        stem = Path(target).stem
        match = index.get(stem.lower())
        if match is None:
            errors.append(f"unresolved wikilink '[[{target}]]' in {source}")
    return errors


def validate_file(path: Path, root: Path, index: Dict[str, Path]) -> ValidationResult:
    content = path.read_text(encoding="utf-8")
    meta, parse_errors, body, attempted = extract_front_matter(content)

    schema_errors: List[str] = []
    promotion_errors: List[str] = []
    relative_path = path.relative_to(root)

    if attempted:
        schema_errors.extend(parse_errors)
        if not parse_errors:
            schema_errors.extend(validate_schema(meta))
            promotion_errors.extend(check_promotion_rule(meta, relative_path))

    wikilink_targets = extract_wikilinks(body)
    wikilink_errors = resolve_wikilinks(wikilink_targets, index, relative_path)

    valid = not (schema_errors or wikilink_errors or promotion_errors)
    return ValidationResult(
        path=relative_path,
        valid=valid,
        schema_errors=schema_errors,
        wikilink_errors=wikilink_errors,
        promotion_errors=promotion_errors,
    )


def validate_tree(root: Path) -> List[ValidationResult]:
    root = Path(root).resolve()
    index = build_stem_index(root)
    results = [validate_file(md_file, root, index) for md_file in sorted(root.rglob("*.md"))]
    return results


def _print_report(results: List[ValidationResult]) -> int:
    failed = 0
    for result in results:
        if result.valid:
            print(f"OK {result.path}")
            continue
        failed += 1
        print(f"FAIL {result.path}")
        for e in result.schema_errors:
            print(f"    schema: {e}")
        for e in result.promotion_errors:
            print(f"    promotion: {e}")
        for e in result.wikilink_errors:
            print(f"    wikilink: {e}")

    print(f"{len(results)} files checked, {len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a kb-template knowledge base.")
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Path to the scaffold root to validate (defaults to this script's own parent directory)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    if not root.is_dir():
        print(f"error: root path does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    results = validate_tree(root)
    return _print_report(results)


if __name__ == "__main__":
    sys.exit(main())
