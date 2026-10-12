# Install the Compose workflow (user scope, any project)

`figma-compose` is a Claude plugin that depends on `figma-core`. Installing it at user scope makes the workflow available from every project. These commands were run against the real `claude` CLI (2.1.296) in a temporary `CLAUDE_CONFIG_DIR`; see [verification](verification/compose-packaging.md). They have not yet been run against the normal user configuration.

## 1. Register the marketplace and install

```text
claude plugin marketplace add C:/Users/Lenovo/claude-figma-workflows
claude plugin install figma-core@claude-figma-workflows --scope user
claude plugin install figma-compose@claude-figma-workflows --scope user
```

Installing `figma-compose` alone also installs `figma-core` automatically (the manifest declares `"dependencies": ["figma-core"]`), so the second command is optional but harmless. Installed copies live in `<config dir>/plugins/cache/claude-figma-workflows/<plugin>/<version>/`; later source changes need `claude plugin update` (not exercised in verification). Check with:

```text
claude plugin list
claude plugin details figma-compose@claude-figma-workflows
```

`details` should list four skills: `build`, `compose-capture`, `compose-review`, `figma-to-composable` (IDs `figma-compose:build` and so on). Core provides `figma-core:figma-extract`, `token-audit`, `visual-verify`, `figma-build`, `adapter-export`.

## 2. Python environment (once)

Python 3.12 or newer, in a dedicated virtual environment outside your app repositories (or git-ignored). Use the lock shipped in the installed plugin; the compose lock is an identical copy of core's, so one venv serves both:

```text
python -m venv C:/Users/Lenovo/.venvs/figma-workflows
C:/Users/Lenovo/.venvs/figma-workflows/Scripts/python.exe -m pip install -r C:/Users/Lenovo/claude-figma-workflows/plugins/figma-compose/requirements-core.lock
C:/Users/Lenovo/.venvs/figma-workflows/Scripts/python.exe -m pip check
```

The `build` skill repeats these steps and asks where the venv lives if none is found. On macOS/Linux the interpreter is `bin/python`.

## 3. How compose finds core

Claude does not export a dependency's install path. `figma-compose/scripts/locate_core.py` resolves it: first the sibling directory `<cache>/<marketplace>/figma-core/<newest version>`, then `installPath` in `<config dir>/plugins/installed_plugins.json`. It prints the JSON array passed as `--core-command-json`:

```text
<venv python> "${CLAUDE_PLUGIN_ROOT}/scripts/locate_core.py" --python <venv python>
```

The `installed_plugins.json` layout is not a documented stable contract, so the sibling lookup comes first and a test pins both behaviors.

## 4. Use it

From any project containing an Android Compose app, start Claude Code and say:

```text
Use the figma-compose workflow to implement https://www.figma.com/design/<fileKey>/<name>?node-id=<id> in this app.
```

Claude should invoke `figma-core:figma-build`, which dispatches to `figma-compose:build`. Core extraction needs your connected Figma server and an explicit observed quota; token approval is yours to give.

## Not proven or not automated

- An authenticated agent session executing these skills end to end has not been run.
- A live Figma file and a real app have not been used (only the synthetic fixture).
- There is no Kotlin policy scanner, device test runner, benchmark or golden-approval automation; the skills say so and review is manual.
- Core's offline freshness is `unverified`; human visual review is `not_run`.
