# Claude Figma Workflows

Reusable Figma-to-app workflows for Flutter and Android Jetpack Compose.

**Status: design specification approved on 2026-10-09; core implementation plan awaiting review. Plugins are not implemented or installable yet.**

## Agreed direction

- `figma-core`: extract and cache designs, audit tokens, coordinate visual verification.
- `figma-flutter`: build Flutter themes/components/screens and regression tests.
- `figma-compose`: build Compose themes/components/screens and regression tests.

Read the [design specification](docs/specs/2026-10-09-figma-workflows-design.md) for the approved conversational scope, proposed contracts, acceptance criteria, and handoff clarifications.

The [core implementation plan](docs/plans/2026-10-09-figma-core.md) defines eight tested deliverables. Flutter and Compose receive separate plans after the core contract is implemented and verified.

## Progress

- [x] Recover the original conversation and approvals.
- [x] Write the complete design specification and self-review it.
- [x] Owner review of the written specification.
- [x] Write and self-review the core implementation plan.
- [ ] Owner review of the core plan and execution method.
- [ ] Implement and test core, then Flutter, then Compose.
- [ ] Validate plugin installation and run a live Figma pilot.

The original owner approval authorized creation of this separate repository and a documentation commit. This repository does not contain or modify the SAT/EST application. No plugins have been globally enabled and no external repository has been published.
