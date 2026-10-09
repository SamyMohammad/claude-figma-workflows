# Claude Figma Workflows

Reusable Figma-to-app workflows for Flutter and Android Jetpack Compose.

**Status: design specification written; awaiting owner review. Plugins are not implemented or installable yet.**

## Agreed direction

- `figma-core`: extract and cache designs, audit tokens, coordinate visual verification.
- `figma-flutter`: build Flutter themes/components/screens and regression tests.
- `figma-compose`: build Compose themes/components/screens and regression tests.

Read the [design specification](docs/specs/2026-10-09-figma-workflows-design.md) for the approved conversational scope, proposed contracts, acceptance criteria, and handoff clarifications.

## Progress

- [x] Recover the original conversation and approvals.
- [x] Write the complete design specification and self-review it.
- [ ] Owner review of the written specification.
- [ ] Write and review the implementation plan.
- [ ] Implement and test core, then Flutter, then Compose.
- [ ] Validate plugin installation and run a live Figma pilot.

The original owner approval authorized creation of this separate repository and a documentation commit. This repository does not contain or modify the SAT/EST application. No plugins have been globally enabled and no external repository has been published.
