# Install the core plugin

Use Python 3.12 or newer in a dedicated virtual environment. Install the runtime dependencies from `plugins/figma-core/requirements-core.lock` using that environment's Python (`python -m pip install -r <plugin-root>/requirements-core.lock`), then run `python -m pip check`. The plugin does not select or install Python itself. Pass that same Python executable when running `<plugin-root>/scripts/core.py` with discrete quoted arguments. The root lock is an identical source copy for repository development.

After reviewing the local marketplace source, run:

```text
claude plugin marketplace add /absolute/path/to/claude-figma-workflows
claude plugin install figma-core@claude-figma-workflows --scope project
```

The first command registers the marketplace in the selected Claude configuration; project scope controls plugin enablement in the second command. The isolated smoke test used a temporary `CLAUDE_CONFIG_DIR` and a consumer directory containing spaces, without changing the normal user configuration. The installed plugin cache contained all seven schemas, the Python scripts, its lock, and four skills.

`claude plugin details figma-core@claude-figma-workflows` inventories four skills: `figma-extract`, `token-audit`, `visual-verify`, and `figma-build`. Their namespaced IDs are `/figma-core:figma-extract`, `/figma-core:token-audit`, `/figma-core:visual-verify`, and `/figma-core:figma-build`. An authenticated isolated slash-skill invocation has not been run. Core extraction needs the owner's connected Figma server and explicit observed quota. Offline bundle validation reports freshness as unverified. `figma-build` reports a blocked adapter-unavailable result until a separate Flutter or Compose adapter is installed. This milestone does not install an adapter or create an MCP server.
