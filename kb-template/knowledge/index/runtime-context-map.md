# Runtime Context Map

Routes a task category to the documents relevant to it, so an agent or contributor loads
only what a given task needs instead of the entire knowledge base.

This is a template — when you adopt `kb-template/` in a project, replace the example rows
below with your own task categories and the canonical topics that answer them.

| Task category | Load these documents |
|---------------|------------------------|
| Understanding this scaffold itself | `[[../../docs/schema]]`, `[[../../docs/promotion]]`, `[[../../docs/authoring-rules]]` |
| Authoring a new canonical document | `[[../../docs/authoring-rules]]`, `[[../../examples/example-canonical-doc]]` |
| Authoring a new raw note | `[[../../docs/authoring-rules]]`, `[[../../examples/example-raw-note]]` |
| Briefing an agent on a topic | `[[../../examples/example-agent-adapter]]` |
| Validating the knowledge base | `[[../../validator/README]]` |

As your knowledge base grows, add one row per recurring task category, pointing at the
`topics/` documents that actually answer it — not at `raw/` or `processed/` material.
