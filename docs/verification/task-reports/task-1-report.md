# C1 runtime report

## Files changed

- `.gitignore` — ignores coverage and build artifacts in addition to existing environment and cache ignores.
- `pyproject.toml` — minimal pytest import path and test directory configuration.
- `requirements-core.lock` — verbatim bytes from `.venv\Scripts\python.exe -m pip freeze --all` after installation.
- `plugins/figma-core/scripts/figma_core/__init__.py` — package marker.
- `plugins/figma-core/scripts/figma_core/errors.py` — `CoreError` with machine code and safe message.
- `tests/scripts/test_errors.py` — focused `CoreError` test.
- `docs/verification/core-environment.md` — interpreter, installation, and verification record.

## Environment

`python --version` failed because `python.exe` resolved to a Windows Store alias that could not start. The bundled `C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` reported Python 3.12.14. Its first `-m venv .venv` attempt failed while `ensurepip` tried writing under the sandboxed Windows Temp directory. I set `TEMP` and `TMP` to `.venv/tmp` and ran `.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip`, which succeeded. The resulting repository-local environment reports Python 3.12.14.

`.venv\Scripts\python.exe -m pip install --upgrade Pillow jsonschema pytest` initially failed because sandbox DNS access was unavailable. Retrying with elevated network access succeeded. Installed direct versions: Pillow 12.3.0, jsonschema 4.26.0, pytest 9.1.1. The lock contains all installed transitive dependencies and pip 25.0.1.

## RED

Command: `.venv\Scripts\python.exe -m pytest tests/scripts/test_errors.py -q`

Run after writing `pyproject.toml` and `tests/scripts/test_errors.py`, before creating `figma_core`:

```text
E   ModuleNotFoundError: No module named 'figma_core'
=========================== short test summary info ===========================
ERROR tests/scripts/test_errors.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.30s
```

## GREEN and checks

- `.venv\Scripts\python.exe -m pytest tests/scripts/test_errors.py -q` — `1 passed in 0.04s`.
- `.venv\Scripts\python.exe -m pip check` — `No broken requirements found.`
- Byte comparison of `requirements-core.lock` against fresh `.venv\Scripts\python.exe -m pip freeze --all` output — `True`.
- `git diff --check` — exit 0. It emitted only a Windows LF-to-CRLF advisory for `.gitignore`.

No commit was made, per controller instruction. No task files or parent SAT/EST files were edited outside C1 ownership. C8 still needs to reinstall the lock in its clean-environment smoke test.
`nController subsequently committed the reviewed task as 4e9a65d; implementer itself made no commit.
