# Research: `generate_skill` output-quality fixes

## Finding 1 — Fence stripping fails on asymmetric/preamble-prefixed output

**Decision**: Replace the leading-fence-only logic with a regex search for a complete fenced
block anywhere in the text (`` ```[lang]\n...``` ``), falling back to stripping a lone
leading/trailing fence line if no complete pair is found.

**Rationale**: The previous implementation (`code.startswith("```")` gate, then strip first and
last line) structurally could not handle a trailing-only fence or preamble text before the
fence, because it never looked for a fence unless the string started with one. Verified via new
tests (`tests/test_skill_validator.py`) covering all four shapes.

**Alternatives considered**: Prompting the model more strictly to never include fences at all
(the prompt already says "Do NOT include markdown code fences"). Rejected as the sole fix —
defense-in-depth against non-compliant model output is the point of `_strip_markdown_fences`
existing at all; a prompt instruction alone doesn't guarantee compliance, which is exactly what
this bug demonstrated.

## Finding 2 — Leaked template placeholder line

**Decision**: Mark every fillable section in `build_skill_md_prompt()`'s template
(`# {skill_name}` paragraph, `## Expected Output`, `## Constraints`) with an explicit
`[INSTRUCTION — ...]` prefix, and add a closing rule telling the model never to copy an
instruction marker into its output.

**Rationale**: `- List each constraint as a bullet point.` was phrased identically to a real
constraint bullet — nothing in its wording distinguished "text describing what to write" from
"text to write." Confirmed reproduced: a real generation run against
`qwen2.5-coder:7b-instruct-q5_K_M` echoed it back verbatim into the generated `SKILL.md`. The
same structural risk existed for two sibling lines in the same template (the one-paragraph
description and the expected-output description) — fixed consistently rather than only the one
line that happened to get caught.

**Alternatives considered**: Removing the instructional prose entirely and leaving blank
sections for the model to fill freeform. Rejected — the existing prose ("one paragraph
explaining...", "brief description of...") gives the model useful guidance on length/tone that a
bare blank section would lose; marking it as an instruction preserves that guidance while making
it unambiguous that the text itself shouldn't be copied.

## Finding 3 — CPU-bound/unoffloaded inference on the remote backend

**Decision**: Query the remote Ollama backend directly (`OLLAMA_REMOTE_URL` from
`.env.example`, `http://100.105.24.12:11434`, reachable from this session) rather than guessing.

**Evidence gathered**:

1. `curl http://100.105.24.12:11434/api/generate` with `qwen2.5-coder:7b-instruct-q5_K_M` (the
   model from the original bug report) and a moderate prompt, followed immediately by
   `curl http://100.105.24.12:11434/api/ps`:
   ```json
   {"name": "qwen2.5-coder:7b-instruct-q5_K_M", "size": 5824325876, "size_vram": 0, ...}
   ```
   `size_vram: 0` against a `size` of ~5.8 GB — **zero bytes of this model are offloaded to
   GPU memory**. It is running entirely on CPU.
2. Repeated with a second, smaller model already present on the same host (`qwen3.5:4b`,
   ~3.2 GB): also `size_vram: 0`. Not model-specific — the host is not GPU-offloading any
   currently-loaded model.

**Conclusion**: This directly explains the originally-reported near-parity between
prompt-processing and generation throughput — both are CPU-bound, so GPU's normal advantage
(much faster parallel prompt processing than sequential generation) isn't present. This is a
genuine finding, not a code bug in this repository: the "remote GPU backend"
(`OLLAMA_REMOTE_URL`, per ADR/ISS-007's dual-backend design) is not currently GPU-accelerating
inference for any model tested.

**Not determined** (would require direct access to that host's own system, not just its Ollama
API port): *why* GPU offload isn't happening — could be no GPU actually present on that host
despite its "remote GPU desktop" designation, a driver/CUDA issue, or Ollama configured with GPU
layers disabled. Flagged as a follow-up for whoever has direct access to that machine.

**Alternatives considered**: Guessing based on the original report's tok/s numbers alone.
Rejected — a repeat of this session's own test produced a different tok/s ratio (364 vs 6.6
tok/s, not the originally reported ~15 vs ~6) for a shorter prompt, showing tok/s ratios alone
are prompt-dependent and not reliable evidence on their own; `size_vram` is a direct,
unambiguous measurement instead of an inference from timing.
