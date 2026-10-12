# SDD ledger — plan: docs/plans/2026-10-09-figma-core.md

Approved 2026-10-09. Base 072c0c4. Branch feat/figma-core; isolated worktree in the current thread's writable visualization directory. Parent repository C:/Users/Lenovo/claude-figma-workflows. No existing runtime/tests at baseline.

## Preflight

| Tasks | Shared contract/file | Finding |
| --- | --- | --- |
| C1/C2/C3/C4/C5/C6/C7 | CoreError(code,message) | Consistent; subcommands map failures centrally |
| C1/C2 | pytest pythonpath | C2 adds tests path; preserve core import path |
| C2/C3 | validate_bundle and manifest | Partial pending nodes allowed; hashes required for complete nodes |
| C2/C4 | DTCG subset and approval schema | Alias/typing semantic validation is C4; schema validation is C2 |
| C2/C5 | comparison-policy schema | C5 uses common validator, bounds checked against image dimensions |
| C2/C6 | meta and bundle schema | Platform/renderer may differ; all rendering conditions otherwise match |
| C3/C6 | safe paths and hashes | Reference must belong to verified bundle; output cannot overwrite input |
| C3/C7 | reservation CLI | Mark-sent is one-shot; ambiguous dispatch consumes budget |
| C4/C6 | content_hash/require_approval | Policy/token approval precedes acceptance; visual approval remains separate |
| C5/C6 | measure results | Pillow diff/overlay objects serialized only in reports module |
| C6/C7 | compare_capture bundle argument | CLI includes --bundle; matches corrected plan |
| C7/C8 | skill IDs / package paths | Core-only marketplace until adapters implemented |
| C1 | Runtime and lock | Steps consistent; actual interpreter must be selected |
| C2 | Schemas and fixture | Consistent; no text fixture has empty font lists, not proof of typography |
| C3 | Atomic persistence and budget | Consistent; coordinator owns manifest writes |
| C4 | Tokens and approval | Consistent; audit never mutates values |
| C5 | Metric and masks | Consistent; no default tolerance, critical regions cannot be masked |
| C6 | Reports and iteration limit | Consistent; persist retries, five total captures maximum |
| C7 | Skills and CLI | Consistent; adapter unavailable is blocked, never synthetic implementation |
| C8 | Packaging and tests | Consistent; actual install isolated, unavailable live/Unix evidence honest |

Ruling: Execute in an isolated worktree via Git fallback — native worktree tools target the SAT/EST checkout rather than this separate repository — cost if wrong: worktree is not attached in the app, but source and Git history remain recoverable.
Ruling: Normalize C1–C8 headings to Task 1–8 — the supplied task-brief script recognizes Task headings only — cost if wrong: documentation-only heading changes.

## Tasks

Task 1: active (base 072c0c4)
Task 1: base updated to cd85896 after documentation-only approval commit.
Task 1: complete (commits cd85896..4e9a65d, review clean). Reviewer audit note resolved by recording controller commit. Task 2: active (base 4e9a65d).
Task 2: fix round 1/5 active after review (critical/ignored overlap, component kind/variant references, font path references, nonfinite JSON overflow). Base 32e8cfd. No parked findings.
Task 2: fix round 1/5 complete (4 findings addressed, 0 open; 32e8cfd..9ce086d). Task 2: complete (4e9a65d..9ce086d, scoped review clean, 19 tests). Task 3: active (base 9ce086d).
Task 3: fix round 1/5 active (portable prefix collisions/characters, entry font/asset hashes, complete checkpoint all-node verification); base9a5bf87.
Task 3: fix round1 complete (3 addressed,0open;9a5bf87..256a657). Task 3: complete (9ce086d..256a657, review clean;50passed1skip junction). Task 4: active (base256a657).
Ruling: C4 owns correcting synthetic fixture hex colors to structured sRGB and regenerating hashes — C2 fixture contradicted approved DTCG subset — cost if wrong: fixture-only data churn and no production impact.
Task 4: fix round1 active: numeric overflow must yield typed error; cross-mode mismatch regression must use valid dimension object. Base cdc4344.
Task 4 cross-task verification: C7 must compare manifest.tokenModes with token document groups/approval modes; C4 require_approval infers present groups. Carry to C7 dispatch.
Task 4: round1 resolves original2 findings but new important safe-int cap restriction. Round2 active: remove arbitrary cap and use overflow-safe audit proposal arithmetic, preserving exact source ints. Baseb479321.
Task4: fix round2 complete (cap addressed,0open;b479321..162791a). Task4: complete (256a657..162791a, reviewed77pass1skip). C7 mode consistency followup remains. Task5: active (base162791a).
Task5: fix round1 active (ICC description spoofing permits non-sRGB characteristics; verify trusted color characteristics). Base8f32807.
Task5: fixround1 complete (ICC addressed,0open;8f32807..ecc3e18). Task5: complete (162791a..ecc3e18,reviewclean96pass1skip). Task6: active (baseecc3e18).
Task6: fixround1active font-free text evidence and theme approval gate. Ruling: add required containsText capture metadata and regenerate no-text fixture — font absence must not silently pass text screens — cost if wrong: schema-v1 consumers must regenerate metadata (only local synthetic fixture exists). C7 carry actual source extraction containsText. C7 must enforce fixed project iteration ledger and approved identity before reserve, otherwise arbitrary hashes reset helper counter.
Task6 round1 original2 fixed, new regression globalfont equality blocks unrelated screen fonts. Round2 active use per-node used-font subset not whole bundle inventory. Base14af10f. C7 retry caller gate remains pending.
Task6: fixround2complete(fontsubset addressed,0open;14af10f..075bdf2). Task6: complete(ecc3e18..075bdf2,reviewclean118pass1skip). Task7: active(base075bdf2). C7 required followups mode alignment, source containsText, approval/fixed ledger correction gate. Baseline pressure trace skill-baseline.md failed sparsecontext noninferential protocol.
Ruling: C7 adds reference-only approval kind/hash (referenceHash+metaHash), needed at correction reservation not initial comparison — changed references cannot reset correction budget without owner evidence — cost if wrong: extra source-target approval before corrective loop; no implication of final visual approval. Publish contract adjustment in C8 docs.
Ruling: four corrections apply per owner-approved reference+policy target, not node lifetime across redesigns — approved C6 plan explicitly allows changed approved identity new run and C7 enforces source approval — cost if wrong: repeated owner approvals can authorize more work, never automatic retries. C8 document exact cap scope. C7 dependency-missing exit2 confirmed focused reviewer subprocess. Independent skill simulation Green trace requests missing details/zero affected edits (baseline premature implementation); no live extraction claimed.
Task7: complete(075bdf2..4fa0fb3,review approved under cap scope clarification,22targeted/full138pass1skip before focused patch). Independent skillsimulation green passed. Task8: active(base4fa0fb3).
Task8 fixround1 active: installed plugin path spaces (not consumer only), slash skill discovery evidence or explicitblocked, skip reason. Base7ed109f. Flutter adapter plan is subsequent milestone; core public contract pending final review.
Task8: fixround1complete(spaces/discovery evidence/skip reason addressed,0open;7ed109f..bc64e53). Task8: complete(4fa0fb3..bc64e53,reviewclean143passed1skipWindowsjunction;Unixblocked/authenticatedslash/liveFigma notrun). Final review pending. All runtime tasks done.
Finalreview bc64e53: 4Important0Critical. One fixwave active shared-document checkpoint validation, malformed capture meta typedblocked, standalone offlinefreshness, token-bound visual evidence. Ruling: add tokenHash to evidence_payload (5input contract) — token approval never substitutes downstream visualapproval — cost if wrong: existing core0.1.0 local evidence regenerated; adapters not yet implemented.
Final fixwave complete(bc64e53..27d150e,all4findings resolved). Final scoped rereview approved core-only;0Critical/Important residual. Windows controller final checks pending.
Controller final:148passed1skipped in38.61s;strictplugin+marketplace validation0,pipcheck0,diffcheck0. Runtime tasks and wholebranch review complete. Integration awaiting owner choice; parentbranch chore/figma-workflow-spec. Permanent reports copied docs/verification. Nextmilestones Flutterplan/Composeplan/livepilot pending.
