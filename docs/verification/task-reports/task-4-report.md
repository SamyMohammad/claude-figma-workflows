# Task 4 report — C4 tokens and approvals

Implemented exact token resolution, typed DTCG subset validation, immutable advisory audit, SHA-256 content hashing, and schema/hash/mode-bound approval checks. Source values (including `rem` and decimal precision) are preserved. The code records approval evidence but does not authenticate an owner or create approvals.

## Files changed

- `plugins/figma-core/scripts/figma_core/{tokens.py,token_types.py,approvals.py}`
- `tests/scripts/{test_tokens.py,test_approvals.py}`
- `tests/fixtures/make_core_fixture.py`
- `tests/fixtures/core-v1/{tokens.json,manifest.json}`
- `.superpowers/sdd/2026-10-09-figma-core/task-4-report.md`

The fixture update was authorized by the controller after the C2 fixture's legacy `#336699`, `8px`, `14px`, and `0px` values conflicted with C4's typed DTCG contract. It changes only token value representation and its recorded file hash; the numeric values and node references are unchanged. The [DTCG 2025.10 format](https://www.designtokens.org/tr/2025.10/format/) requires dimension/duration objects and typography `lineHeight` as a number or number-token reference (§8.2, §8.5, §9.8). Dimension line-height aliases and legacy measure strings are rejected.

## Verification

Red regression command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py tests/scripts/test_approvals.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-red
```

Result: exit 1 at collection, before implementation:

```text
E   ModuleNotFoundError: No module named 'figma_core.tokens'
E   ModuleNotFoundError: No module named 'figma_core.approvals'
ERROR tests/scripts/test_tokens.py
ERROR tests/scripts/test_approvals.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.33s
```

Focused green command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py tests/scripts/test_approvals.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-green
```

Result: `11 passed in 0.37s` (before the final additional cases).

Final focused command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py tests/scripts/test_approvals.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-focused-final
```

Result: `25 passed in 0.58s`, exit 0.

Final C1–C4 command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-contract-final
```

Result: `75 passed, 1 skipped in 9.23s`, exit 0. The existing skip was retained.

Checked-in fixture validation:

```text
.venv/Scripts/python.exe -c 'import sys; sys.path.insert(0,"plugins/figma-core/scripts"); from pathlib import Path; from figma_core.schema import validate_bundle; from figma_core.documents import read_json; from figma_core.tokens import audit_tokens; root=Path("tests/fixtures/core-v1"); validate_bundle(root); assert audit_tokens(read_json(root/"tokens.json"))["status"]=="passed"; print("checked-in fixture bundle valid; token audit passed")'
```

Result: `checked-in fixture bundle valid; token audit passed`, exit 0.

`git diff --check` exited 0. Git reported its routine LF-to-CRLF warning for `tests/fixtures/make_core_fixture.py`.

One fixture generation attempt failed before changing files because `fixtures` was not on the standalone Python import path:

```text
ModuleNotFoundError: No module named 'fixtures'
```

The corrected command inserted `tests` on `sys.path` and regenerated only the checked-in token file and manifest.

## Scope and assumptions

- `audit_tokens(document)` treats the present `light` and `dark` groups as selected modes; the separate manifest determines which groups are included in a bundle. `require_approval` checks exact present modes for token documents.
- `base` is shared and audited, but is not an approval mode.
- No skill, CLI, commit, push, or PR was created in this task.

## Review round 1

The reviewer found that `math.isfinite(10**400)` raises `OverflowError`, bypassing typed token errors and crashing audit. The initial repair used a safe-integer cap; review round 2 removed that unrequested cap. The cross-mode mismatch test now uses a valid dimension object and checks the mismatch issue exactly.

Red regression command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-review-red
```

Result: exit 1, `1 failed, 22 passed in 0.58s`:

```text
FAILED tests/scripts/test_tokens.py::test_huge_json_integer_is_typed_error_and_blocks_audit
E       OverflowError: int too large to convert to float
```

Final focused command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py tests/scripts/test_approvals.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-review-green
```

Result: `27 passed in 0.64s`, exit 0.

Final full command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-review-full
```

Result: `77 passed, 1 skipped in 8.95s`, exit 0.

## Review round 2

The safe-integer cap was removed because the DTCG number contract does not impose it. Integer values now remain exact Python integers without a float conversion; finite floats are checked with `math.isfinite`. Audit compares near values through exact rational arithmetic (`Fraction`) so a large subtraction or percentage computation cannot overflow a float. The JSON-parsed `10**400 + 123` regression resolves unchanged, and two huge near values produce a suggestion without mutation or a crash.

Red regression command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-review2-red
```

Result: exit 1, `2 failed, 22 passed in 0.58s`:

```text
FAILED tests/scripts/test_tokens.py::test_huge_json_integer_preserves_precision_and_audits
E           figma_core.errors.CoreError: Invalid number value at light.x
FAILED tests/scripts/test_tokens.py::test_near_value_comparison_handles_large_numbers
E       AssertionError: assert 'blocked' == 'passed'
```

Final focused command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts/test_tokens.py tests/scripts/test_approvals.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-review2-green
```

Result: `27 passed in 0.59s`, exit 0.

Final full command:

```text
.venv/Scripts/python.exe -m pytest tests/scripts -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c4-review2-full
```

Result: `77 passed, 1 skipped in 9.37s`, exit 0.
