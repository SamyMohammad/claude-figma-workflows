# Core Python environment

- Interpreter: `C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` (Python 3.12.14).
- Repository environment: `.venv` (Python 3.12.14), created from that interpreter. The `python` command resolved to a Windows Store alias that could not start.
- Packages installed with `.venv\Scripts\python.exe -m pip install --upgrade Pillow jsonschema pytest`; exact installed versions, including transitive dependencies and pip, are in `requirements-core.lock` from `pip freeze --all`.
- Installation check: `.venv\Scripts\python.exe -m pip check` reported `No broken requirements found.`

The sandbox denied writes to the default Windows Temp path during `ensurepip`. Setting `TEMP` and `TMP` to `.venv/tmp` let the local environment complete. Package installation required network access.
