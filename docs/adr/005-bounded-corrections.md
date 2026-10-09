# ADR 005: Bounded visual corrections and evidence

## Decision

A comparison validates the complete recorded bundle, the exact node reference and metadata, capture conditions, available fonts and assets, token approval, and the approved comparison policy before measuring pixels. Recorded metadata explicitly states `containsText`; text captures require nonempty used-font evidence, and each referenced font must be available, licensed, and hash verified. The bundle may contain fonts used by other nodes. Empty font evidence is allowed only for a hash-verified no-text source. The capture theme must be among approved token modes. The run writes a new directory with capture images, diff, overlay, and machine and Markdown reports. A blocked run records its reason without a fabricated metric.

Automated pixel comparison and human visual review remain separate. An automated pass leaves `visualReview` as `not_run`. Geometry is `not_run` until measured bounds are explicitly checked. Platform and renderer labels are recorded, not required to match.

Correction attempts are counted for each node, reference hash, and policy hash. The initial comparison is free; at most four corrections can be recorded. A changed reference or policy has a new identity and requires its own approvals. Persist the correction ledger across resume; do not reset it on a repeat run.

Visual approval binds the reference, actual, both metadata documents, and policy through `content_hash(evidence_payload(...))`. Approval records identify an owner and evidence reference but do not cryptographically prove identity.

## Consequences

Missing dependencies or an altered source block comparison. Pixel results cannot alone establish full visual acceptance. The caller must keep the correction ledger and each run directory as durable evidence.
