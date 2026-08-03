"""Front-matter schema definition for kb-template documents.

Single source of truth for required fields and allowed enum values, per
kb-template/docs/schema.md. Kept as plain data (no parsing logic here) so both
the validator and any future tooling can import just the schema shape.
"""

REQUIRED_FIELDS = (
    "title",
    "type",
    "status",
    "project",
    "authority",
    "created",
    "updated",
    "canonical",
    "related",
)

ALLOWED_TYPE = {"canonical-doc", "agent-adapter", "raw-note", "adr"}
ALLOWED_STATUS = {"draft", "active", "canonical", "deprecated"}
ALLOWED_AUTHORITY = {"invariant", "doctrine", "process", "tool-specific-guidance"}

# status values that make a document canonical, subject to the promotion rule
# (must also physically live outside knowledge/raw/)
CANONICAL_STATUSES = {"canonical", "active"}

RAW_FOLDER_NAME = "raw"
