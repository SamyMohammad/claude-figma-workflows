# Final integration fix report

All four Important findings in final-review-report.md addressed. No commits or installation/live operations.

## Changes

- `plugins/figma-core/scripts/figma_core/schema.py`: keyword-only candidate manifest override reuses full bundle validation without publishing the candidate.
- `plugins/figma-core/scripts/figma_core/checkpoint.py`: validate a copied candidate before atomic publication; failure retains partial/pending with typed error.
- `plugins/figma-core/scripts/figma_core/captures.py`: schema/matching checks precede external metadata field access inside report handling; all offline reports explicitly mark freshness unverified; approved tokens content hash enters evidence.
- `plugins/figma-core/scripts/figma_core/reports.py`: fifth required token hash argument; JSON and Markdown freshness disclosure.
- `tests/scripts/test_checkpoint.py`, `tests/scripts/test_captures.py`, `tests/scripts/test_cli.py`, `tests/scripts/test_reports.py`: correctly hashed invalid fonts, malformed metadata blocked report/exit 2, cached verified/unverified offline disclosure, and fresh token approval invalidating both visual/golden approval regressions; existing evidence callers updated.
- `docs/plans/2026-10-09-figma-core.md`: only evidence interface/examples/contract updated; controller status preserved.
- `docs/adr/005-bounded-corrections.md`: metadata/freshness and required token evidence contract; source-reference approval unchanged.
- `docs/verification/core-results.md`: fresh full-suite count.
- `.superpowers/sdd/2026-10-09-figma-core/final-fix-report.md`: this report.

## Verification

Commands run from worktree root:

1. `.venv/Scripts/python.exe -m pytest tests/scripts/test_checkpoint.py tests/scripts/test_captures.py tests/scripts/test_cli.py -q --basetemp .superpowers/sdd/2026-10-09-figma-core/pytest-final-fix-red`
   Exit 1: **5 failed, 36 passed in 24.05s**. Failure excerpts verbatim:
   - `AssertionError: assert 'complete' == 'partial'`
   - `KeyError: 'freshness'` (both cached freshness cases)
   - `AssertionError: assert 'a9036b8e3c79bad9835a20b2c8fe46e4cd7e755fc3a7556054b7494132379b9d' != 'a9036b8e3c79bad9835a20b2c8fe46e4cd7e755fc3a7556054b7494132379b9d'`
   - `KeyError: 'nodeId'`
2. `.venv/Scripts/python.exe -m pytest tests/scripts/test_checkpoint.py tests/scripts/test_captures.py tests/scripts/test_cli.py tests/scripts/test_reports.py -q --basetemp .superpowers/sdd/2026-10-09-figma-core/pytest-final-fix-green`
   Exit 0: **42 passed in 26.10s**.
3. `.venv/Scripts/python.exe -m pytest tests/scripts -q --basetemp .superpowers/sdd/2026-10-09-figma-core/pytest-final-fix-full -rs`
   Exit 0: **148 passed, 1 skipped in 32.44s**. One full suite run after focused green.
   `SKIPPED [1] tests\scripts\test_storage.py:122: host cannot create junction: Access is denied.`
4. `git diff --check`
   Exit 0; no whitespace errors (Git emits LF-to-CRLF working-copy notices).

A documentation edit initially encountered Windows default-codepage `UnicodeDecodeError` before writing; rerun with explicit UTF-8 succeeded. No failed verification remains. Self-review: candidate publication stays atomic; shared checks are reused; upstream metadata validated before reads; no changed PNG/meta/policy hash semantics; source/correction approval rules preserved. No new dependencies or unrelated runtime refactors. Unix/authenticated slash/live Figma/real fonts remain unverified or not run as previously documented.
