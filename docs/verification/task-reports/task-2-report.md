# C2 implementation report

## Files changed

- `pyproject.toml`: adds `tests` to pytest pythonpath for the fixture import.
- `plugins/figma-core/scripts/figma_core/documents.py`: strict JSON reader.
- `plugins/figma-core/scripts/figma_core/schema.py`: document and bundle validation.
- `plugins/figma-core/schemas/{manifest,meta,fonts,component-map,assets,approval,comparison-policy}.schema.json`: seven Draft 2020-12 schemas.
- `tests/fixtures/make_core_fixture.py` and `tests/fixtures/core-v1/`: reproducible synthetic bundle.
- `tests/scripts/test_schema.py`: contract and edge-case tests.
- `docs/adr/001-shared-core.md`, `docs/adr/002-token-contract.md`: bundle and DTCG subset decisions.
- This report.

## RED

Command: `.venv/Scripts/python.exe -m pytest tests/scripts/test_schema.py -q --basetemp=.pytest_tmp_c2`

```text
=================================== ERRORS ====================================
________________ ERROR collecting tests/scripts/test_schema.py ________________
ImportError while importing test module 'C:\Users\Lenovo\.codex\visualizations\2026\10\09\01a12103-6a0c-7682-a0ad-74ed4d1a9312\figma-core-worktree\tests\scripts\test_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\scripts\test_schema.py:6: in <module>
    from figma_core.documents import read_json
E   ModuleNotFoundError: No module named 'figma_core.documents'
=========================== short test summary info ===========================
ERROR tests/scripts/test_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.28s
```

The first implementation run exposed a fixture-builder error (it omitted `assets/manifest.json` because it excluded every file named `manifest.json`). That run reported `2 passed, 1 failed in 1.50s` with the failure:

```text
E               figma_core.errors.CoreError: Missing file reference: assets/manifest.json
```

The fixture builder now excludes only the root manifest.

## GREEN

Focused: `.venv/Scripts/python.exe -m pytest tests/scripts/test_schema.py -q --basetemp=.pytest_tmp_c2`

```text
............                                                             [100%]
12 passed in 2.45s
```

Full C1/C2 suite: `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest_tmp_c2_all`

```text
.............                                                            [100%]
13 passed in 2.64s
```

Static fixture check: `validate_bundle(Path('tests/fixtures/core-v1'))` returned `complete 5` with a manually added package path. Temporary pytest directories were removed after validation.

The first standalone fixture check omitted the package path and failed with:

```text
ModuleNotFoundError: No module named 'figma_core'
```

The corrected standalone check passed. Pytest uses the configured pythonpath.

## Review notes

The bundle validator checks structural references and geometry, while C3 owns file-hash verification and C4 owns detailed DTCG token auditing. A partial manifest remains explicitly `partial`. No live Figma data, approvals, commits, or external writes were created.

## C2 review fix, round 1

Changed `plugins/figma-core/scripts/figma_core/documents.py`, `plugins/figma-core/scripts/figma_core/schema.py`, and `tests/scripts/test_schema.py`. The validator now rejects overlaps between critical and ignored comparison regions; component mappings must point to a component node with its exact variant; available font files require a contained path, SHA-256, and manifest file reference. The strict JSON reader rejects finite-syntax floats that overflow to infinity, including nested values. The existing bundle path resolver also rejects symlink escapes, verified by a regression test. No other task files were changed.

RED: `.venv/Scripts/python.exe -m pytest tests/scripts/test_schema.py -q --basetemp=.pytest_tmp_c2_review`

```text
............FFFF.F                                                       [100%]
================================== FAILURES ===================================
_____________ test_critical_region_cannot_overlap_ignored_region ______________
E       Failed: DID NOT RAISE CoreError
__________ test_component_mapping_must_match_component_node[0-None] ___________
E       Failed: DID NOT RAISE CoreError
__________ test_component_mapping_must_match_component_node[2-other] __________
E       Failed: DID NOT RAISE CoreError
_________________ test_available_font_requires_recorded_file __________________
E       Failed: DID NOT RAISE CoreError
_______________ test_float_overflow_in_nested_meta_is_rejected ________________
E       Failed: DID NOT RAISE CoreError
=========================== short test summary info ===========================
FAILED tests/scripts/test_schema.py::test_critical_region_cannot_overlap_ignored_region
FAILED tests/scripts/test_schema.py::test_component_mapping_must_match_component_node[0-None]
FAILED tests/scripts/test_schema.py::test_component_mapping_must_match_component_node[2-other]
FAILED tests/scripts/test_schema.py::test_available_font_requires_recorded_file
FAILED tests/scripts/test_schema.py::test_float_overflow_in_nested_meta_is_rejected
5 failed, 13 passed in 5.25s
```

GREEN focused: `.venv/Scripts/python.exe -m pytest tests/scripts/test_schema.py -q --basetemp=.pytest_tmp_c2_review`

```text
..................                                                       [100%]
18 passed in 4.06s
```

GREEN full: `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest_tmp_c2_review_all`

```text
...................                                                      [100%]
19 passed in 3.47s
```
