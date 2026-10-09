# ADR 006: Isolated core plugin packaging

## Decision

Ship the original core implementation through a local Claude marketplace with one `figma-core` plugin. The plugin carries its own copy of the exact core lock, schemas, Python scripts, and four default-discovered skills. It uses the owner's connected Figma tools; it adds no MCP server, REST client, or global hook. No upstream plugin code is redistributed and no public license is declared without an owner decision. The reviewed `compare.py` informed behavior but was not copied.

Run installation verification with an explicit temporary `CLAUDE_CONFIG_DIR` and separate consumer directory. Local marketplace registration writes to the selected Claude configuration even when plugin enablement is project scoped. Normal installation therefore remains an explicit user action.

## Consequences

The local cache is self-contained for deterministic Python validation once its locked dependencies are installed. Flutter and Compose adapters remain separate future milestones. A reference correction requires owner approval of `referenceHash` and `metaHash` with approval kind `reference`, as well as current token and policy approvals. The initial capture is free and at most four corrections apply to one node and owner-approved reference plus policy identity. A changed approved target starts a new run after fresh approval, rather than resetting a lifetime node cap. This permits deliberate redesign at the cost of a new approval and evidence chain.

This packaging proves only offline core behavior. Live Figma use, licensed font rendering, adapter generation, and full application visual acceptance require later pilots. The Windows lock includes `colorama`; a Unix installation must be checked independently before a portability claim.
