# ADR 003: Safe bundle checkpoints and MCP call ledger

Status: Accepted for the core milestone, 2026-10-09.

Bundle paths are POSIX relative paths. The core rejects traversal, absolute or
drive paths, Windows reserved names, ambiguous suffixes, links, junctions, and
case-folded collisions. This prevents accidental and untrusted references from
leaving the bundle. It does not defend against another local process racing
filesystem checks.

Workers write unique staged node files. The coordinator verifies metadata,
revision, required files, and SHA-256 hashes before publishing node completion
and updated hashes through one atomic manifest replacement. A failed write
leaves the previous manifest intact. A bundle is complete only when all scoped
nodes and required assets are complete. Unknown revisions never qualify for
verified cache reuse; offline freshness remains unverified.

The workflow stores call reservations in SQLite. `BEGIN IMMEDIATE` serializes
reservations across processes, and both reserved and sent calls count against
the observed window limit. Repeated reservation of the same pending request is
idempotent. A request can be marked sent exactly once, before MCP dispatch;
ambiguous failures remain spent. Window IDs and limits come from observed account
policy rather than local clock assumptions. This ledger tracks this workflow's
calls only.
