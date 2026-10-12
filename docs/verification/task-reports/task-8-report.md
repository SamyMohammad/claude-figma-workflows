# C8 implementation report

## Changed files

Added `.claude-plugin/marketplace.json`, `plugins/figma-core/.claude-plugin/plugin.json`, `plugins/figma-core/requirements-core.lock`, `tests/scripts/test_packaging.py`, `tests/evals/{core-cases.json,README.md,skill-baseline.md,skill-green.md}`, `docs/verification/core-results.md`, `docs/installation.md`, and `docs/adr/006-upstream-isolation.md`. Updated `README.md` and the dependency guidance in `plugins/figma-core/scripts/{core.py,figma_core/cli.py}`.

## Verification

- TDD red: `.venv/Scripts/python.exe -m pytest tests/scripts/test_packaging.py -q` → 2 failures for missing marketplace manifest and plugin lock; 1 setup error because sandbox Windows Temp was unwritable. Using workspace `--basetemp` resolved the setup issue. Green: 3 passed.
- Clean Python 3.12.14 venv: initial `ensurepip` failed under sandbox Windows Temp; setting `TEMP` and `TMP` to workspace SDD resolved it. Initial `pip install -r requirements-core.lock` failed with DNS/network restriction (`ERROR: Could not find a version that satisfies the requirement attrs==26.1.0 (from versions: none)` and `ERROR: No matching distribution found for attrs==26.1.0`). Escalated installation succeeded with exact locked versions.
- Clean venv `python -m pytest tests/scripts -q --basetemp .superpowers/sdd/2026-10-09-figma-core/pytest-c8-final2` → 143 passed, 1 skipped in 31.63s. Post-test packaging edit: focused packaging test → 3 passed in 1.16s.
- Clean venv `python -m pip check` → `No broken requirements found.` exit 0.
- `claude plugin validate plugins/figma-core --strict` → exit 0. First `claude plugin validate . --strict` failed because marketplace description was absent; added description, reran both strict validations → exit 0.
- Explicit temporary `CLAUDE_CONFIG_DIR`: marketplace add, project install, plugin list → exit 0 each. Installed cache has scripts, seven schemas, lock, and four skills. Installed cache `core.py validate --bundle tests/fixtures/core-v1` → exit 0, `status: passed`, `freshness: unverified`.
- `python -m json.tool tests/evals/core-cases.json` and `git diff --check` → exit 0.
- `wsl --list --quiet` under read-only escalation returned only `docker-desktop`; no general Unix distribution. Unix suite blocked. Real-font and live Figma pilots not run.

No commit, push, remote publication, or normal-user Claude configuration changes were made. No Flutter/Compose adapter was added. The sparse-context eval traces are labeled hypothetical simulations and do not claim live execution.

## Follow-up packaging evidence

- Extended `test_packaging.py` to copy the plugin to `plugin with spaces`, run its absolute `core.py` from `consumer directory with spaces`, and parse the expected `passed` / `complete` / `unverified` JSON. Clean venv focused run → 3 passed in 1.62s. The copied plugin resolves schemas relative to itself.
- Repeated isolated marketplace add and project install with spaces in both `CLAUDE_CONFIG_DIR` and consumer path; both exit 0. `claude plugin details figma-core@claude-figma-workflows` exits 0 and inventories four skills: `figma-build`, `figma-extract`, `token-audit`, `visual-verify`. The cached plugin `core.py validate` from the spaced consumer exits 0 and reports `passed`, `complete`, `unverified`.
- Installed skill discovery is evidenced by component inventory. Authenticated slash-skill invocation was not run in the isolated config; it remains `not_run`, and no credentials were read or copied.
- `python -m pytest tests/scripts/test_storage.py -q -rs --basetemp .../pytest-c8-skip-reason` → 22 passed, 1 skipped. Exact skip: `SKIPPED [1] tests\scripts\test_storage.py:122: host cannot create junction: Access is denied.`
- Final full run after the test change: `python -m pytest tests/scripts -q --basetemp .../pytest-c8-final-spaces -rs` → 143 passed, 1 skipped in 37.62s, exit 0. Same junction skip reason.
