# Core verification results — 2026-10-09

| Check | Status | Evidence |
| --- | --- | --- |
| Packaging TDD | passed | `test_packaging.py` initially failed for missing manifests and plugin lock; after packaging, 3 passed. Initial temp-path setup also failed under sandbox Temp, so final runs use a workspace `--basetemp`. |
| Windows clean lock install | passed | Bundled Python 3.12.14; exact `requirements-core.lock` installed in an isolated venv. First sandbox network attempt failed DNS; escalated install succeeded. |
| Windows Python suite | passed | Final clean venv run after spaced-path test: `python -m pytest tests/scripts -q --basetemp .../pytest-c8-final-spaces -rs` → 143 passed, 1 skipped in 37.62s. The skip is `test_storage.py:122: host cannot create junction: Access is denied.` |
| Dependency consistency | passed | Clean venv: `python -m pip check` → `No broken requirements found.` |
| Claude strict validation | passed | `claude plugin validate plugins/figma-core --strict` and `claude plugin validate . --strict`, both exit 0. Marketplace needed a description for strict validation. |
| Isolated marketplace install | passed | Explicit temporary `CLAUDE_CONFIG_DIR`; marketplace add, project-scope install, and plugin list all exit 0. Repeated with spaces in the config and consumer paths: add/install exit 0. `claude plugin details figma-core@claude-figma-workflows` exits 0 and inventories four skills: `figma-build`, `figma-extract`, `token-audit`, `visual-verify`. Cached plugin contains seven schemas, scripts, lock, and four SKILL.md files. Installed-cache `core.py validate --bundle tests/fixtures/core-v1` from the spaced consumer exits 0 with `status: passed`, `freshness: unverified`. |
| Installed skill invocation | not_run | Component discovery was verified by `claude plugin details`, but no authenticated isolated Claude session invoked a slash skill. The local manifest and inventory establish names, not end-to-end skill behavior. |
| Plugin path with spaces | passed | Packaging subprocess test copies the plugin under `plugin with spaces`, runs its absolute `scripts/core.py` from `consumer directory with spaces`, and checks parsed `status: passed`, `bundleStatus: complete`, `freshness: unverified`. This exercises installed-relative schema resolution. |
| Git whitespace check | passed | `git diff --check` exits 0. |
| Unix suite | blocked | `wsl --list --quiet` shows only `docker-desktop`; no available general Unix distribution. No OS/service installation or remote CI was attempted. The Windows-generated lock includes `colorama`; Unix resolution remains unverified. |
| Real fonts, live Figma, application capture, owner visual review | not_run | No live connection, platform adapters, or real-font pilot in this core milestone. |

The eval case definitions in `tests/evals/core-cases.json` are not execution results. The sparse-context baseline and green traces are independent hypothetical agent simulations, copied under `tests/evals`; they performed no live tools, UI edits, or comparison. See their README for scope.
