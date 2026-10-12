# Claude Figma Workflows

Reusable Figma extraction and visual verification workflows, with planned Flutter and Android Jetpack Compose adapters.

**Status: `figma-core` and `figma-compose` install as Claude plugins and are validated offline on Windows. Flutter adapter, live Figma pilot and authenticated skill runs remain pending.**

## Agreed direction

- `figma-core`: extract and cache designs, audit tokens, coordinate visual verification.
- `figma-flutter`: build Flutter themes/components/screens and regression tests.
- `figma-compose`: build Compose themes/components/screens and regression tests.

Read the [design specification](docs/specs/2026-10-09-figma-workflows-design.md) for the approved conversational scope, proposed contracts, acceptance criteria, and handoff clarifications.

The [core implementation plan](docs/plans/2026-10-09-figma-core.md) defines eight tested deliverables. See [installation](docs/installation.md) and [verification results](docs/verification/core-results.md). The core plugin provides four skills: `figma-extract`, `token-audit`, `visual-verify`, and `figma-build`. It validates versioned local bundles, audits a limited DTCG token subset, tracks source call budgets and bounded corrections, and compares approved PNG captures. Offline source freshness is unverified. `figma-build` blocks when a platform adapter is unavailable. No live Figma extraction or full app build is claimed.

## Usable now vs unproven

Usable and verified offline (see [Compose install](docs/installation-compose.md) and [packaging verification](docs/verification/compose-packaging.md)):
- Both plugins validate with `claude plugin validate --strict`, install at user scope from the local marketplace (compose auto-installs core), and list their skills.
- Core CLI: bundle validation, token audit, PNG comparison, correction ledger, adapter export.
- Compose CLI: deterministic Kotlin theme generation (`generate`), capture metadata checks (`prepare-capture`), core locator; exercised against the synthetic fixture only.
- Compose skills: `build`, `figma-to-composable`, `compose-capture`, `compose-review` (instructions, not yet executed by an authenticated agent).

Not proven or not built: live Figma extraction, a real app pilot, authenticated skill execution, the Flutter adapter, a Kotlin policy scanner, device/benchmark automation, golden approval. Offline freshness is `unverified`; human visual review is `not_run`.

## Progress

- [x] Recover the original conversation and approvals.
- [x] Write the complete design specification and self-review it.
- [x] Owner review of the written specification.
- [x] Write and self-review the core implementation plan.
- [x] Owner review of the core plan and execution method.
- [x] Implement and test the core plugin offline on Windows.
- [x] Validate isolated local plugin installation.
- [x] Compose adapter scripts, skills and plugin packaging (offline).
- [ ] Flutter adapter.
- [ ] Compose device checks, policy scanner and benchmarks.
- [ ] Run a live Figma and real-font pilot, then owner visual review.

This repository does not contain or modify the SAT/EST application. Installation verification used a temporary Claude configuration; no plugin was enabled in the normal user configuration and no external repository was published.
