# Final scoped rereview — bc64e53..27d150e

## Verdict

**Ready to merge: Yes, for the declared core-only milestone.** All four Important findings from the whole-branch review are addressed. No residual Critical/Important findings or new breakage identified in this fix diff.

## Finding disposition

1. **Checkpoint integrity — resolved.** `checkpoint.py:86–100` builds a deep-copied candidate, updates the staged hashes/status, and passes it through the existing full bundle validator before atomic publication. `schema.py:82` accepts that candidate through a keyword-only override without publishing it first. A typed validation failure preserves pending/partial and an error code. The new regression uses a correctly hashed malformed fonts document and verifies persisted partial state.
2. **Malformed metadata — resolved.** `captures.py:96` invokes schema/matching validation for both external metadata objects inside the CoreError report boundary before `_bundle_inputs` accesses their fields. The CLI regression covers missing fields in either reference or actual metadata, exit 2, blocked JSON/Markdown reports, and absence of a pixel metric.
3. **Offline freshness disclosure — resolved.** `captures.py:90–93` initializes every generated comparison report with unverified freshness and an explicit offline explanation; `reports.py:36–38` includes that statement in Markdown. Tests cover both cached verified and unverified manifests, preventing stale cached verification from becoming a live freshness claim.
4. **Token-bound downstream evidence — resolved, including the plan contract.** `_bundle_inputs` returns the canonical token hash after validating approval. `captures.py:104` passes it as the required fifth argument to `evidence_payload`; the report and evidence hash include `tokenHash`. All runtime/test call sites and the plan/ADR contract use the new signature. The regression changes spacing from 8 to 9, creates a fresh token approval, verifies changed evidence identity, and rejects both old visual and old golden approvals. The separate reference approval and correction-count identity remain unchanged.

## Verification and scope

Reviewed the supplied fix diff and final-fix-report, then inspected the integrated changed functions and all evidence-payload/report/candidate-validator call sites. The supplied verification records 42 focused passes followed by 148 full-suite passes and the already disclosed Windows junction permission skip. These are implementation-run results, not a reviewer rerun. No tests, installs, live calls, implementation edits, or Git mutations were performed during this rereview; this requested report is the only write.

The corrections reuse established boundaries and add focused regressions. The candidate validation does not publish unvalidated state, metadata errors remain typed, offline disclosure is conservative, and visual/golden evidence now binds the already-approved exact token document.

## Declined to judge

- Flutter/Compose adapters, runtime app checks, authenticated slash invocation, live Figma, real fonts, and Unix execution remain outside this fix wave and retain the previously documented incomplete/unavailable statuses.
- A new whole-branch audit or repeated full-suite run was not performed, as requested; this pass covers the four findings and regressions introduced by their fixes.

No residual item requires adjudication.
