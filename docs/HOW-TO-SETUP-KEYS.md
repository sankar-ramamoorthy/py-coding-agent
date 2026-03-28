


*** docs\HOW-TO-SETUP-KEYS.md ***

## 1. `docs/HOW-TO-SETUP-KEYS.md` (ready to paste)

```markdown
# HOW‑TO: Set up encrypted API keys (LLM_MASTER_KEY)

This document explains how to set up **encrypted API key management** for `py‑coding‑agent` so your keys are stored securely and never appear in Git or `.env` files.

---

## Overview

- The agent uses `LLM_MASTER_KEY` to encrypt and decrypt API keys stored in `/workspace/.keys.enc`.  
- `LLM_MASTER_KEY` must be set in your **OS environment**, **not** in `.env` or Git.  
- Users can then manage keys at runtime with CLI commands like `/key groq <api_key>`.

---

## Step 1: Install cryptography (if missing)

If you get import errors:

```bash
pip install cryptography
# or
uv sync
```

---

## Step 2: Generate LLM_MASTER_KEY

Run this once anywhere you have Python:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

You’ll see something like:

```text
b'Mra-PTkxvYDqL1C2qZ6uZGkQAvFj-4b1b1eZ6uZGkQAvFj-4b1b='
```

Save that entire string; this is your `LLM_MASTER_KEY`.

---

## Step 3: Set LLM_MASTER_KEY in Windows (PowerShell)

You have two options:

### Option A: Use `setx` (recommended)

```powershell
setx LLM_MASTER_KEY "b'MyActualKeyStringHere'"
```

- No spaces around `=`.  
- Quotes around the key are important.  
- After `setx`, open a **new PowerShell** or Docker shell so the new environment variable is visible.

Verify:

```powershell
$env:LLM_MASTER_KEY
```

### Option B: Use PowerShell‑native environment setting

```powershell
[Environment]::SetEnvironmentVariable(
    "LLM_MASTER_KEY",
    "b'MyActualKeyStringHere'",
    "User"
)
```

- `"User"` sets it per‑user; `"Machine"` sets it system‑wide.  
- Again, open a new shell and verify:

```powershell
$env:LLM_MASTER_KEY
```

---

## Step 4: Do NOT put LLM_MASTER_KEY in Git or .env

Your `.env` file should only contain non‑master‑key items:

```bash
# ✅ Good
#GROQ_API_KEY=sk-...
LITELLM_MODEL=groq/qwen/qwen3-32b
LLM_PROVIDER=litellm
```

Never include:

```bash
# ❌ Never
LLM_MASTER_KEY=b'...'
```

If you ever committed `LLM_MASTER_KEY` to Git, rotate it and clean up the history.

---

## Step 5: Use the CLI key commands

Once the agent is running and `LLM_MASTER_KEY` is set, you can use:

```text
> /key groq sk-abc123
> /key openai sk-xyz456
> /key list
> /key remove groq
```

- Keys are **encrypted** and stored in `/workspace/.keys.enc`.  
- They are **never** printed in logs or stored in plain text.

---

## Tips and pitfalls

- ✅ Only `LLM_MASTER_KEY` in OS env; API keys can be in env or managed via `/key`.  
- ✅ Rotate `LLM_MASTER_KEY` if you think it has leaked (and re‑encrypt keys).  
- ❌ Never print `LLM_MASTER_KEY` in debug logs or configs.  
- ❌ Never commit `.keys.enc` or `LLM_MASTER_KEY` to Git.

Once you complete this setup, your `py‑coding‑agent` will have **fully encrypted runtime key‑management** matching ADR‑006.
```


