---
name: token-audit
description: Use when inspecting Figma design tokens, their modes, exact source values, or proposed normalization before implementation.
---

# Token audit

With a selected verified venv Python, invoke `${CLAUDE_PLUGIN_ROOT}/scripts/core.py` using discrete quoted arguments: `validate --bundle <path>`, then `audit --bundle <path> --mode light` or `dark` for each manifest mode. The manifest modes must match the actual token groups. Present exact source values separately from alias and near-value proposals. A proposal never mutates a token. Obtain explicit owner approval of the exact content and selected modes before recording a hash-bound token approval; later changes invalidate it. Report offline freshness as unverified. Never use `$ARGUMENTS` in a shell command or read unrelated files.
