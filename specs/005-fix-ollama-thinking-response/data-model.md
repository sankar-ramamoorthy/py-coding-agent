# Phase 1 Data Model: Fix Ollama thinking-model empty response

No data entities. This feature changes request-building and response-handling logic inside
`OllamaProvider.generate()` and adds one new configuration value in `py_mono/config.py` — it
introduces no new persisted state, no new database/file-backed records, and no new domain
entities. See `contracts/ollama-chat-request-contract.md` for the shape of the request/response
this feature touches.
