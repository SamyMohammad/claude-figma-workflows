# Claude Figma Workflows

Reusable Figma extraction and visual verification workflows, with planned Flutter and Android Jetpack Compose adapters.

**Status: core plugin 0.1.0 implemented and validated offline on Windows. Flutter and Compose adapters and a live Figma pilot remain pending.**

## Agreed direction

- `figma-core`: extract and cache designs, audit tokens, coordinate visual verification.
- `figma-flutter`: build Flutter themes/components/screens and regression tests.
- `figma-compose`: build Compose themes/components/screens and regression tests.

Read the [design specification](docs/specs/2026-10-09-figma-workflows-design.md) for the approved conversational scope, proposed contracts, acceptance criteria, and handoff clarifications.

The [core implementation plan](docs/plans/2026-10-09-figma-core.md) defines eight tested deliverables. See [installation](docs/installation.md) and [verification results](docs/verification/core-results.md). The core plugin provides four skills: `figma-extract`, `token-audit`, `visual-verify`, and `figma-build`. It validates versioned local bundles, audits a limited DTCG token subset, tracks source call budgets and bounded corrections, and compares approved PNG captures. Offline source freshness is unverified. `figma-build` blocks when a platform adapter is unavailable. No live Figma extraction or full app build is claimed.

## Progress

- [x] Recover the original conversation and approvals.
- [x] Write the complete design specification and self-review it.
- [x] Owner review of the written specification.
- [x] Write and self-review the core implementation plan.
- [x] Owner review of the core plan and execution method.
- [x] Implement and test the core plugin offline on Windows.
- [x] Validate isolated local plugin installation.
- [ ] Plan and implement Flutter and Compose adapters.
- [ ] Run a live Figma and real-font pilot, then owner visual review.

This repository does not contain or modify the SAT/EST application. Installation verification used a temporary Claude configuration; no plugin was enabled in the normal user configuration and no external repository was published.
