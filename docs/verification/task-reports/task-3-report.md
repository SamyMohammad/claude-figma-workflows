# C3 handoff: safe storage, checkpoints, and budget

## Files changed

- `plugins/figma-core/scripts/figma_core/paths.py` — portable safe bundle paths and case-folded collision checks.
- `plugins/figma-core/scripts/figma_core/storage.py` — SHA-256 hashing and fsynced atomic JSON replacement.
- `plugins/figma-core/scripts/figma_core/checkpoint.py` — verified node completion and conservative cache reuse.
- `plugins/figma-core/scripts/figma_core/budget.py` — SQLite transaction ledger and one-shot dispatch marking.
- `plugins/figma-core/scripts/figma_core/schema.py` — safe paths, recorded hash verification, and complete asset check.
- `tests/scripts/test_storage.py`, `test_checkpoint.py`, `test_budget.py` — path, crash, checkpoint, and concurrent ledger cases.
- `docs/adr/003-cache-and-budget.md` — persistence and budget decisions.

## Verification

- Red phase: `.venv/Scripts/python.exe -m pytest tests/scripts/test_storage.py tests/scripts/test_checkpoint.py tests/scripts/test_budget.py -q --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3` — expected collection failure: `ModuleNotFoundError` for `figma_core.paths`, `figma_core.checkpoint`, and `figma_core.budget`.
- First focused green run, same command — `18 passed in 2.65s`.
- Final C1–C3 run: `.venv/Scripts/python.exe -m pytest tests/scripts -q --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3-final2` — `40 passed, 1 skipped in 10.29s`.
- After a SQLite connection cleanup change: `.venv/Scripts/python.exe -m pytest tests/scripts/test_budget.py -q --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3-budget-final` — `3 passed in 1.03s`.
- Junction detail: `.venv/Scripts/python.exe -m pytest tests/scripts/test_storage.py::test_junction_escape_is_rejected_when_supported -q -rs --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3-junction` — `SKIPPED ... host cannot create junction: Access is denied.` Symlink escape test passed.
- `git diff --check` — no whitespace errors (Git reported only its LF-to-CRLF notice for `schema.py`).

## Review notes

`complete_node` is coordinator-owned. Workers may write only unique staged files. Missing or inconsistent node files keep the manifest partial with a typed error code; a failed manifest replace leaves the previous checkpoint intact. The local path checks do not defend against another process racing filesystem operations. Unknown source revisions never qualify as verified reuse. Budget windows and limits are supplied by the caller; the ledger does not infer account quotas. No commit was made.

## Review round 1 (baseline `9a5bf87`)

Changed `paths.py`, `schema.py`, and `checkpoint.py`, with regressions in `test_storage.py` and `test_checkpoint.py`. Path validation now rejects Windows-invalid component characters and catches case-folded directory aliases and file/directory prefix collisions. Bundle validation checks each available font and asset SHA-256 against its actual file. Checkpoint completion verifies other scoped completed nodes have their required manifest references and files, verifies required bundle files and available assets, and keeps the current node pending if these checks fail.

Red run: `.venv/Scripts/python.exe -m pytest tests/scripts/test_storage.py tests/scripts/test_checkpoint.py -q --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3-review-red` — `10 failed, 18 passed, 1 skipped in 4.07s`; the failures matched the three review findings (five invalid character cases, two folded path collisions, two available entry hash mismatches, and one missing completed-node file reference).

Focused green run: `.venv/Scripts/python.exe -m pytest tests/scripts/test_storage.py tests/scripts/test_checkpoint.py tests/scripts/test_budget.py -q --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3-review-focused` — `31 passed, 1 skipped in 4.39s`.

Full run: `.venv/Scripts/python.exe -m pytest tests/scripts -q --basetemp .superpowers/sdd/2026-10-09-figma-core/tmp-c3-review-full` — `50 passed, 1 skipped in 8.80s`. The one skip remains the Windows junction creation permission denial; symlink coverage passed. `git diff --check` found no whitespace errors, only Git LF-to-CRLF notices. No commit was made.
