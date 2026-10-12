---
name: visual-verify
description: Use when comparing a rendered Flutter or Compose capture with an approved Figma reference or tracking corrective visual iterations.
---

# Visual verification

Use the selected verified venv Python to run `${CLAUDE_PLUGIN_ROOT}/scripts/core.py compare` with discrete quoted `--bundle`, `--reference`, `--actual`, `--reference-meta`, `--actual-meta`, `--policy`, `--policy-approval`, and `--output` arguments. `passed`, `failed`, and `blocked` use exit codes 0, 1, and 2. Present the generated report and image artifacts. Human visual review remains `not_run` until the owner performs it; an automated pass cannot claim that approval. Do not alter the reference or tolerance to force a pass.

Before each corrective edit, ensure exact owner approval of the source target hash and meta hash is recorded in the bundle, plus current token and policy approvals. Run `correction --bundle ... --node-id ... --policy ... --policy-approval ...` to reserve one of at most four corrections in the fixed bundle ledger. A changed reference or policy needs fresh owner approval. Do not invoke the low-level iteration helper or substitute a new ledger. If any gate blocks, report the reason and stop that correction. Never shell-interpolate `$ARGUMENTS` or use the skill as permission to read unrelated files.
