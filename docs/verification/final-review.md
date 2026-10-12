# Whole-branch final review — Figma core 0.1.0

Reviewed baseline `072c0c4` through `bc64e53`, the approved specification, core plan/constraints, rulings ledger, runtime integration, skill entry points, schemas, and permanent verification evidence. No implementation, index, HEAD, or branch changes; no suite rerun. Focused reproductions used copied fixtures outside the checkout. This report is the only checkout write.

## Strengths

- Source and policy approvals are checked against exact content; correction entry points use the fixed bundle ledger and require separately recorded reference/meta approval. The four-correction scope matches the explicit owner-approved-reference/policy ruling.
- Portable bundle paths reject traversal, links and case-folded collisions. Hash verification connects assets/fonts and completed source nodes to the manifest.
- Comparison handles alpha on black and white, refuses unsupported color characteristics, rejects empty eligible masks and masked critical regions, and leaves human/geometry review explicitly not run.
- Release evidence is candid: Windows installation and paths with spaces were exercised; Unix, authenticated slash invocation, live Figma, real fonts, and platform adapters are not presented as completed.

## Issues

### Critical

None found.

### Important

1. **Completion publishes a complete manifest without validating the shared bundle documents.**
   - Location: `plugins/figma-core/scripts/figma_core/checkpoint.py:95` (checks immediately before publication at lines 75–85).
   - `complete_node` validates the manifest, node metadata, and asset manifest, but only checks existence/hash for fonts, component map, tokens and comparison policy. A staged shared document with its correctly updated hash can therefore be invalid while this operation returns/persists `complete`; the CLI reports success. This is observable state corruption at the checkpoint boundary, not a malicious-hash scenario: extraction writes both shared documents and their hashes normally.
   - Reproduction: copied the synthetic fixture, marked one node pending, replaced `fonts.json` with `{}`, updated its manifest hash, and completed the node. Result: `checkpoint published: complete`; immediately calling `validate_bundle` produced `SCHEMA_INVALID Invalid value at fonts`.
   - Fix: validate the candidate completed state with the same shared structural/reference checks before atomically publishing it, preserving pending/partial with an error when those checks fail. Keep the validator reusable without requiring a temporarily published complete manifest. Add a regression for a correctly hashed but invalid shared document.

2. **Malformed reference metadata bypasses typed failure/report handling.**
   - Location: `plugins/figma-core/scripts/figma_core/captures.py:42`, ordering at `captures.py:94`.
   - `_bundle_inputs` indexes `reference_meta['nodeId']` before `require_matching_capture` validates either supplied metadata document. A valid JSON object missing that field is a normal external-input failure, but raises `KeyError`; neither the comparison handler nor CLI handles it. No blocked report is written, and a CLI invocation terminates with an uncaught exception instead of the documented exit 2.
   - Reproduction against the unchanged complete fixture: `compare_capture(..., reference_meta={}, ...)` raised `KeyError 'nodeId'`; the output directory did not exist.
   - Fix: schema-validate both metadata inputs inside the comparison error-handling boundary before any field access, then perform bundle/provenance checks. Regression should assert blocked report, safe reason/code and exit 2.

3. **The standalone visual report loses offline freshness evidence.**
   - Location: `plugins/figma-core/scripts/figma_core/captures.py:94` and `captures.py:103`.
   - `_bundle_inputs` returns the manifest but its return value is discarded. Neither report format nor comparison output includes freshness. The public visual-verify skill presents these artifacts directly and does not require a separate freshness-bearing validation output. Thus a successful offline comparison can be shared without the required statement that its source freshness is unverified. This is not a request to fail offline comparisons; their limitation must accompany their result.
   - Reproduction: a token-approved copy of the shipped `freshness: unverified` fixture produced a `passed` comparison; `freshness in report: False`. The Markdown report only contains status and changed ratio.
   - Fix: propagate source freshness to machine and human-facing reports, including an explicit unverified statement; avoid asserting live verification merely because a cached manifest once claimed verified. Test the supported offline path.

4. **Visual/golden approval identity survives token changes once the new tokens are approved. [Plan-contract issue]**
   - Location: `plugins/figma-core/scripts/figma_core/reports.py:11`, invocation at `captures.py:102`; C6 evidence interface and ADR 005 prescribe this omission.
   - Token approval correctly blocks an unapproved token edit. However, after a new token proposal is approved, the visual/golden evidence hash still only covers images, capture metadata and policy. It cannot distinguish the old token set from the new one. An existing visual approval for the old evidence remains valid for a new report generated with changed tokens, without a new human visual review. Token proposal approval does not authorize visual/golden acceptance. This conflicts with the integration review requirement that token changes invalidate downstream evidence.
   - Reproduction: compared identical fixture captures, changed the actual shared spacing token from 8 to 9, updated its recorded hash and supplied a fresh synthetic token approval, then compared again with unchanged images/meta/policy. Both comparisons passed and the visual evidence hashes were identical. An approval checked against that evidence payload consequently cannot distinguish them.
   - Fix: include the approved token content identity in the visual/golden evidence payload and update the documented contract/tests. This requires correcting the plan's four-input evidence interface, rather than claiming the implementer departed from it. A test must show a fresh token approval cannot preserve the prior visual/golden evidence hash.

### Minor

None raised.

## Trust boundaries and verification

- Local manifest and approval writers are trusted coordinators. Approval owner/evidence records are auditable statements, not authenticated signatures. No finding assumes a hostile user can be prevented from deleting the correction ledger, forging approvals, or editing all local hashes.
- Captures and source metadata remain caller-provided evidence; real renderer/font/source truth cannot be proven by this offline fixture suite. `containsText` follows the settled source-metadata ruling.
- No global install, Figma writes, network invocation, suite rerun, or platform application work was performed by this review.
- Focused probe artifacts are in sibling directories `final-review-s5nqwx56` (checkpoint and malformed-meta) and `final-review-evidence-ct9vo_t7` (freshness and token evidence) under the task visualization root. The latter includes original and changed-token report artifacts.

## Declined to judge

- Flutter/Compose generation, runtime app behavior, platform hooks/goldens/performance: explicitly deferred adapter milestones.
- Unix execution and authenticated slash/live-Figma behavior: unavailable/not run, explicitly disclosed; no portability or live-success claim judged as established.
- Whether identical source pixels justify a new human approval after a token-only change: the contract explicitly requires downstream invalidation; finding 4 reports the contract mismatch instead of silently setting it aside.
- Malicious concurrent filesystem replacement between path checks and writes, manual ledger deletion or forged human approvals: outside the documented trusted local coordinator model.

## Recommendations and assessment

Address the four integration findings in one focused fix wave with regressions for each boundary. Preserve the explicit core-only release limitations and settled correction/reference rulings.

**Ready to merge? With fixes.** No critical vulnerability was found, but checkpoint integrity, malformed-input handling, freshness disclosure, and downstream approval identity need correction before the core contract is frozen for adapters.
