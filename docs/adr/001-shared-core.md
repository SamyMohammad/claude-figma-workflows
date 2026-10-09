# ADR 001: Shared local design bundle

Status: Accepted for the core milestone, 2026-10-09.

Flutter and Compose adapters consume one versioned bundle produced by the core workflow. They do not independently fetch the same Figma source. The manifest records selected node IDs, node status, available source revisions, capture files, SHA-256 references, freshness, and request-budget observations. An offline bundle reports `freshness: unverified`.

Every non-token JSON document carries `schemaVersion: 1` and rejects unknown fields. Bundle validation checks document structure and references; storage and hash verification follow in the storage milestone. A partial bundle may contain pending nodes without capture files. A completed node requires context, reference image, and metadata. Approval records are optional while extracting; the relevant gate requires them before dependent work.

The fixture under `tests/fixtures/core-v1` is generated locally and is not a Figma export. It exercises the shared contract without claiming live source access.
