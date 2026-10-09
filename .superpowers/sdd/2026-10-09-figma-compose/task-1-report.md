# C1 implementation report

Implemented the approved portable core receipt and Compose input boundaries. Complete bundles require explicit current token approval; exporter reuses core bundle/hash, token-mode, audit, resolution and approval APIs. Context/meta/reference hashes come from verified bundle paths and remain untrusted data. Offline freshness is always unverified. No approval is generated in production.

## Files

- `plugins/figma-core/scripts/figma_core/adapter_export.py`
- `plugins/figma-core/scripts/figma_core/cli.py`
- `plugins/figma-core/.claude-plugin/plugin.json` (0.1.1)
- `plugins/figma-core/skills/adapter-export/SKILL.md`
- `plugins/figma-compose/schemas/receipt.schema.json`
- `plugins/figma-compose/schemas/config.schema.json`
- `plugins/figma-compose/scripts/compose_adapter/__init__.py`
- `plugins/figma-compose/scripts/compose_adapter/errors.py`
- `plugins/figma-compose/scripts/compose_adapter/inputs.py`
- `plugins/figma-compose/scripts/compose_adapter/core_bridge.py`
- `tests/scripts/test_adapter_export.py`
- `tests/scripts/test_compose_inputs.py`
- `tests/fixtures/compose_receipt.py`
- `tests/scripts/test_packaging.py` (controller explicitly extended ownership for required version/skill expectations)
- `pyproject.toml`
- This report.

## RED / GREEN evidence

Commands ran from the worktree using its existing installed `.venv/Scripts/python.exe`.

1. `.venv/Scripts/python.exe -m pytest tests/scripts/test_adapter_export.py -q`
   - RED: exit 1, `5 failed in 0.51s`. All five tests failed at import:
     `E ModuleNotFoundError: No module named 'figma_core.adapter_export'`.
   - After exporter implementation, GREEN: exit 0, `5 passed in 1.98s`.
2. `.venv/Scripts/python.exe -m pytest tests/scripts/test_compose_inputs.py -q`
   - RED: exit 1, `21 failed in 0.24s`. All tests failed at import:
     `E ModuleNotFoundError: No module named 'compose_adapter'`.
3. `.venv/Scripts/python.exe -m pytest tests/scripts/test_adapter_export.py tests/scripts/test_compose_inputs.py -q`
   - GREEN: exit 0, `26 passed in 9.69s`.
4. Added CLI path/approval/export, tampered-context, semantic-config and explicit-array cases:
   `.venv/Scripts/python.exe -m pytest tests/scripts/test_adapter_export.py tests/scripts/test_compose_inputs.py tests/scripts/test_cli.py -q`
   - GREEN: exit 0, `56 passed in 14.38s`.
5. Self-review regression:
   `.venv/Scripts/python.exe -m pytest tests/scripts/test_compose_inputs.py -k blocked_json_code -q`
   - RED: exit 1, `1 failed, 31 deselected in 0.14s`:
     ```text
     > assert error.value.code == "APPROVAL_INVALID"
     E AssertionError: assert 'CORE_FAILED' == 'APPROVAL_INVALID'
     E - APPROVAL_INVALID
     E + CORE_FAILED
     ```
   - Fixed bridge to retain safe code from nonzero blocked JSON, in addition to core stderr codes.
   - Focused GREEN (same three files as step 4): exit 0, `57 passed in 15.04s`.
6. Initial full regression: `.venv/Scripts/python.exe -m pytest -q`
   - exit 1, `1 failed, 192 passed in 27.77s`:
     ```text
     > assert manifest["version"] == "0.1.0"
     E AssertionError: assert '0.1.1' == '0.1.0'
     ```
   - Controller authorized updating only packaging version and skill discovery expectations.
7. Final focused validation:
   `.venv/Scripts/python.exe -m pytest tests/scripts/test_adapter_export.py tests/scripts/test_compose_inputs.py tests/scripts/test_packaging.py -q`
   - exit 0, `48 passed in 14.49s`.
8. Final full regression: `.venv/Scripts/python.exe -m pytest -q`
   - exit 0, `194 passed in 32.68s`.
9. `git diff --check` passed with no output.

## Behavior and self-review

Core exposes `export-adapter`, `verify-approval` and read-only `check-paths`, retaining existing 0/1/2 status mappings. Paths use authoritative core safe_path/check_collisions. The installed skill names its own actual `scripts/core.py` entry point. The bridge accepts an explicitly trusted command array and argument array only, runs with `shell=False`, rejects duplicate/non-finite/malformed JSON, retains safe core error codes, and suppresses source-controlled error detail.

Compose schemas reject unknown fields, unsupported versions/modes/types, expressions in symbols, unknown Material roles and invalid font-resource mappings. Receipt token paths/types must match across selected modes. Config applies deterministic missing-name normalization without mutating caller data; collision enforcement is the C2 responsibility. Material mappings must point to tokens of the correct type. Explicit default roles are retained for C2 reporting rather than misrepresented as source values. Fonts keep inventory availability/license evidence; no substitutions or claims of file existence are invented. The synthetic receipt helper uses exactly the task brief's values and synthetic approval evidence.

Root cause is the missing approved portable boundary. Changes are limited to that boundary, CLI surface and its packaging expectations. Existing core tests pass; no SAT app/cache changes, credential discovery or auto-approval. Production Compose inputs do not import another installation's internal core package. C1 includes no Kotlin compilation or font-file verification: those belong to subsequent C2/C3 work. Receipt JSON alone is not proof of current source approval; consumers must freshly export via the explicit trusted core command as the next task requires.

No remaining blocker or architectural decision. No tests skipped. Full regression repeated because the bridge regression and required packaging expectations changed after the initial run.
