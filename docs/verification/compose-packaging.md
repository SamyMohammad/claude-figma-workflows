# Compose packaging verification

Date: 2026-10-12. Host: Windows 11, `claude` 2.1.296, Python 3.14 venv built from the plugin lock (`pip check`: no broken requirements). All Claude CLI steps used a temporary `CLAUDE_CONFIG_DIR`; the real user configuration was not touched. The marketplace copy lived in a path with spaces (`...\compose pkg test\market with spaces`) and the working directory was `consumer dir`.

## Executed

| Check | Result |
| --- | --- |
| `claude plugin validate plugins/figma-compose --strict` | passed (the `dependencies` key accepted under strict) |
| `claude plugin validate . --strict` (marketplace) and the same on a copy with spaces | passed |
| `claude plugin marketplace add <path with spaces>` | added `claude-figma-workflows` |
| `claude plugin install figma-compose@claude-figma-workflows --scope user` | installed, `(+ 1 dependency: figma-core)` auto-installed at user scope |
| `claude plugin list` | figma-compose 0.1.0 and figma-core 0.1.1, both user scope, enabled |
| `claude plugin details figma-compose@claude-figma-workflows` | 4 skills: build, compose-capture, compose-review, figma-to-composable; 0 agents/hooks/MCP |
| Installed cache contents | `.claude-plugin`, `requirements-core.lock`, `schemas`, `scripts`, `skills`, `templates` for compose; core likewise |
| `locate_core.py` run from the installed compose cache | printed `[python, <cache>\figma-core\0.1.1\scripts\core.py]` (sibling lookup) |
| Installed core `export-adapter` on `tests/fixtures/compose-v1` | produced a receipt |
| Installed `compose.py generate --dry-run` with that receipt and command, against a copy of `samples/compose-fixture` | exit 0, rendered theme files (dry run, nothing written) |
| `tests/scripts/test_compose_packaging.py` | passes (marketplace, dependency, skill frontmatter, referenced files, lock identity, spaces in paths, core locator) |
| Full `python -m pytest -q` | 301 passed (baseline 291 plus 10 new packaging tests); one existing assertion in `test_packaging.py` was relaxed from an exact marketplace list to core being present |

The dependency key was confirmed in the official plugin docs (`dependencies` array of names or objects) and empirically by the auto-install above. A constrained version range was not used; the local marketplace has no tested tag-based resolution.

## Blocked / not run

- Authenticated skill execution (`/figma-compose:build` in a live session): not run.
- Live Figma extraction and a real app pilot: not run.
- Install into the normal user configuration: not run (isolated config only).
- `claude plugin update` after a source change: not run.
- Gradle build, Roborazzi capture, Android emulator/device tests, benchmarks: not run in this packaging step.
- Kotlin policy scanner, device runner, benchmark and golden approval: do not exist in this repository.
- macOS/Linux: not run.
