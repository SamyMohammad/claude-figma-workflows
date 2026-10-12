# C6 implementation report

## Files

- `plugins/figma-core/scripts/figma_core/captures.py`
- `plugins/figma-core/scripts/figma_core/reports.py`
- `plugins/figma-core/scripts/figma_core/iterations.py`
- `tests/scripts/test_captures.py`
- `tests/scripts/test_reports.py`
- `tests/scripts/test_iterations.py`
- `docs/adr/005-bounded-corrections.md`
- `plugins/figma-core/schemas/meta.schema.json`
- `tests/fixtures/make_core_fixture.py`
- `tests/fixtures/core-v1/manifest.json` and five node `meta.json` files

## Verification

- Red: `.venv/Scripts/python.exe -m pytest tests/scripts/test_captures.py tests/scripts/test_reports.py tests/scripts/test_iterations.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-red` — collection failed for three absent modules, as expected.
- Green: `.venv/Scripts/python.exe -m pytest tests/scripts/test_captures.py tests/scripts/test_reports.py tests/scripts/test_iterations.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-green3` — 16 passed.
- Full: `.venv/Scripts/python.exe -m pytest -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-full-final2` — 115 passed, 1 skipped.
- `git diff --check` — passed.

## Contract notes

Comparison requires an exact recorded reference and metadata, complete verified bundle, matching capture conditions and PNG sizes, available approved-license fonts/assets, matching token modes with bound token approval, and an exact approved policy. Blocked reports have no metric. Automated pass leaves human and geometry review `not_run`. SQLite `BEGIN IMMEDIATE` makes correction count updates transactional across concurrent callers. The caller owns the durable correction ledger and must pass a new approved policy for a changed policy run. Empty fonts are accepted for the synthetic no-text capture fixture.

The C6 API returns a blocked report; the C7 CLI owns mapping that status to exit code 2. There is no separate actual capture metadata file in the bundle: the adapter supplies `actual_meta`, and the evidence hash binds it to the reference metadata.

## Fix round 1

- Red: `.venv/Scripts/python.exe -m pytest tests/scripts/test_captures.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-round1-red` — 2 failed, 16 passed: text capture was blocked only by unknown schema field, and unapproved dark capture incorrectly passed.
- Green: `.venv/Scripts/python.exe -m pytest tests/scripts/test_captures.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-round1-green` — 18 passed.
- Full: `.venv/Scripts/python.exe -m pytest -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-round1-full` — 117 passed, 1 skipped.

`containsText` is now a required source-recorded metadata boolean and a matched capture condition. A text capture requires nonempty used-font hashes; the synthetic no-text fixture records false. The selected theme must belong to the approved token modes. C7 extraction instructions must require source evidence for `containsText`, and platform adapters must pass it with actual capture metadata. The iteration helper accepts source hashes as caller inputs; C7 is responsible for obtaining them from the verified bundle and enforcing approval before a new run.

## Fix round 2

- Red: `.venv/Scripts/python.exe -m pytest tests/scripts/test_captures.py::test_text_capture_uses_subset_of_bundle_fonts -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-round2-red` — 1 failed: a node using font A blocked because unrelated font B was in the bundle.
- Green: `.venv/Scripts/python.exe -m pytest tests/scripts/test_captures.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-round2-green-resume` — 19 passed.
- Full: `.venv/Scripts/python.exe -m pytest -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c6-round2-full` — 118 passed, 1 skipped.

Text captures still require nonempty font evidence, and every referenced font must be available, license approved, and hash verified. Other bundle fonts may exist. The regression covers a two-font bundle where the captured node uses only A, then blocks an unknown used font. The missing/restricted font test now marks that font as used by the node.
