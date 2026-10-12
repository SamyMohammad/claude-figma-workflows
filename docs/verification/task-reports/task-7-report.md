# Task 7 implementation report

## Changed

- Added CLI entry point and modules: `plugins/figma-core/scripts/core.py`, `figma_core/cli.py`, `cli_bundle.py`, `cli_compare.py`, `dispatch.py`.
- Added four core skills and extraction reference under `plugins/figma-core/skills/`.
- Extended reference approval schema and bundle validation in `plugins/figma-core/schemas/approval.schema.json` and `figma_core/schema.py`.
- Added `tests/scripts/test_cli.py` and `test_dispatch.py`.

The correction command derives the reference and metadata hashes from a verified complete bundle, requires recorded and current token, policy, and source-target approval records, and uses the fixed bundle `.workflow/corrections.sqlite3` ledger. It accepts no hash or ledger override. A `reference` approval authorizes the source target for a corrective loop; it is not a final visual approval. Token mode alignment is checked at validation and audit, and already by C6 comparison. Sparse source instructions require detail requests and zero affected app edits.

## Verification

- Red: `.venv\Scripts\python.exe -m pytest tests/scripts/test_cli.py tests/scripts/test_dispatch.py -q` failed collection with `ModuleNotFoundError: No module named 'figma_core.cli'` and `No module named 'figma_core.dispatch'` before implementation.
- Green: `.venv\Scripts\python.exe -m pytest tests/scripts/test_cli.py tests/scripts/test_dispatch.py -q --basetemp .pytest-c7`: **22 passed in 7.79s** after final small URL and SQLite error-handling patch.
- Full suite before that final small patch: `.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-c7-full`: **138 passed, 1 skipped in 24.93s**. No second full suite was run after the isolated patch; its focused tests passed.
- Absolute-path script from `C:\Users\Lenovo\sat-east-platform`: `validate --bundle <fixture>` exited **0**, printed `{"bundleStatus": "complete", "freshness": "unverified", "status": "passed"}`.
- Missing dependencies simulation with Python `-S`: printed `DEPENDENCY_MISSING: Install requirements.lock in the selected Python venv`; the shell tool reported process exit **1** despite the script's explicit `SystemExit(2)`.

CLI tests cover invalid bundles and URLs, unknown commands, complete and partial bundles, mode mismatch, explicit target evidence, missing adapter, blocked and failed comparison exits, human-review `not_run`, correction approval/path gates, and four-correction limit.

## Scope and pending evaluation

The existing `skill-baseline.md` is a hypothetical sparse-context pressure trace, not an independent agent run. The skill text addresses its failure by requiring missing child details before app edits. No post-write behavioral Green evaluation was run; the controller owns that independent scenario. No live Figma access or platform adapter was claimed. No commit or push was made.
