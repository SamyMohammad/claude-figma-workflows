# Core evaluation cases

`core-cases.json` defines prompts, prerequisites, expected and forbidden actions, and an evidence destination. A case definition is not a passed evaluation. The offline fixture, malformed-bundle, missing-font, approval, and correction behaviors have automated test coverage; see the linked test files and [core results](../../docs/verification/core-results.md). The other cases are `not_run` as live workflows.

The independent sparse-context skill exercise is preserved as [baseline](skill-baseline.md) and [green](skill-green.md). These are hypothetical agent action traces, not live Figma extraction, application edits, or pixel comparisons. Baseline prematurely proposed implementation from missing design facts; green left affected nodes pending and requested source details and approvals. Neither trace proves installed-skill behavior against a connected Figma server.
