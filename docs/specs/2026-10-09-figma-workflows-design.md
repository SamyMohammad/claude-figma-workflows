# Figma-to-app workflows — design specification

Date: 2026-10-09
Status: Written specification awaiting owner review. Conversational design approved.
Source: Claude chat “تطبيق Pexels من تصميم Figma”, continued in Codex.

## 1. Intent and scope

Build reusable Claude Code workflows that extract Figma designs and implement them in Flutter or native Android Jetpack Compose. Support both organized design systems and raw frames. Produce maintainable code, measurable visual fidelity, regression tests, performance checks, and explanations of engineering decisions.

The owner approved a separate repository at `~/claude-figma-workflows`, with three plugins in one local marketplace: `figma-core`, `figma-flutter`, and `figma-compose`. SAT/EST is a potential consumer, not the home of these plugins. Do not modify its application or existing plugin caches as part of building this repository.

Success requires automated comparison AND human visual review. “Pixel-perfect” is a target measured under recorded capture conditions, not a promise that different rendering engines produce identical pixels on every device. A tolerance pass must not conceal missing elements, wrong assets, typography, or behavior.

The current deliverable is this written specification and repository documentation. Runtime plugins, installation, implementation plans, and live Figma extraction are subsequent stages. No plugin is usable yet.

## 2. Approved architecture

| Plugin | Responsibility | Outputs |
| --- | --- | --- |
| figma-core | Discover capabilities, extract and cache designs, audit tokens, coordinate builds | Versioned design bundle and extraction report |
| figma-flutter | Consume the bundle and build Flutter UI using project conventions | Theme, widgets, screens, captures, goldens, review reports |
| figma-compose | Consume the same bundle and build Compose UI | Theme, composables, screens, captures, Roborazzi tests, review reports |

Platform plugins consume local design bundles. They do not independently fetch the same Figma data. Missing or stale data returns to core through an explicit refresh step.

Shared deterministic utilities belong in figma-core. Each platform owns its generator, capture adapter, and code policy rules. Keep scripts focused and testable. Do not create a second application architecture inside the plugin.

The coordinator performs extraction and token approval first, builds reusable components before dependent screens, then coordinates capture, comparison, regression tests, review, and decision notes. Independent units may run in parallel with explicit file ownership. Workers must preserve others' edits; shared themes and component maps have one writer. Bound concurrency and share one request-budget tracker.

## 3. User entry points and installation contract

The intended logical entry point is `/figma-build <figma-url>`; extraction can also run independently as `/figma-extract <figma-url>`. Implementation must document the actual namespaced commands exposed by Claude Code instead of promising that unqualified aliases exist. Core owns build dispatch; platform plugins must not register conflicting dispatchers.

Detect Flutter from `pubspec.yaml` and Compose from the Android Gradle project. If both are present, require an explicit target. Respect the target repository's instructions, architecture, design system, dependency constraints, and existing component library before generating files.

Install core plus one platform plugin from the local marketplace. Installation documentation will be validated against the installed Claude Code CLI before publishing executable instructions. Do not automatically enable all three plugins globally or alter MCP credentials.

## 4. Extraction and caching

1. Discover the tools actually exposed by the connected Figma MCP server. Check identity, file access, and relevant plan/seat information when supported. Report unavailable capabilities explicitly.
2. Resolve the URL into a file and selected node scope. Inventory screens, reusable components, variants, and dependencies. Record excluded nodes; never label a partial extraction complete.
3. Extract variables and styles where accessible. Preserve exact source values and node references. For raw frames, produce proposed tokens without silently merging colors or rounding dimensions.
4. Obtain design context and reference screenshots for each scoped screen and component variant. Record layout constraints, text styles, assets, states, and interactions available in the source.
5. Download source assets through available supported tools. Preserve filenames safely and record hashes and provenance. A missing download or expired URL is an error, not permission to invent an asset.
6. Audit font families, weights, availability, and redistribution rights. A missing required font blocks visual acceptance. Do not substitute fonts silently or commit licensed fonts without permission.
7. Present the token proposal and deviations for owner approval. Bind approval to the token content hash. Any subsequent token change invalidates approval.
8. Save an atomic, resumable manifest. Only mark a node complete after its required files exist and their hashes are recorded.

Do not assume a fixed 200-call budget, a universal daily reset, or universal availability of named tools such as `download_assets` and motion extraction. Limits depend on the account and tools; maintain a configurable local budget, reserve before concurrent calls, and honor server retry information. Local counts cannot account for other clients' usage. On throttling, checkpoint and report when/how to resume; do not promise an automatic next-day run.

Cache identity includes file, node, available source version, extraction schema, and capture settings. A file version change alone does not identify which nodes changed. Use available node-level evidence; otherwise revalidate the selected scope conservatively. Offline use must clearly report freshness as unverified. Never compare a new reference against an old context bundle without detecting the mismatch.

## 5. Local design contract

The following is the planned consumer-project layout, not files already generated:

```text
design/figma/
  manifest.json
  tokens.json
  tokens-approval.json
  fonts.json
  component-map.json
  assets/manifest.json
  assets/<safe-name>
  screens/<stable-node-slug>/context.md
  screens/<stable-node-slug>/reference.png
  screens/<stable-node-slug>/meta.json
  components/<stable-node-slug>/<variant>/context.md
  components/<stable-node-slug>/<variant>/reference.png
  components/<stable-node-slug>/<variant>/meta.json
```

| File | Required meaning |
| --- | --- |
| manifest.json | Schema version, file/node scope, observed source revision, extraction time, capabilities, requested/completed/failed nodes, file hashes, budget observations, resume state |
| tokens.json | DTCG-format typed tokens, aliases, source provenance; preserve raw values and distinguish proposals from approved values |
| tokens-approval.json | Approved content hash, recorded owner approval, selected modes, accepted deviations |
| fonts.json | Families/weights, local availability, expected file hashes, licensing status |
| component-map.json | Figma component/variant IDs to platform, project-relative code path, symbol, supported variants, source hash |
| meta.json | Node/revision, logical and pixel sizes, device scale, locale/direction, theme, font hashes, platform/renderer, text scale, inset/crop policy, animation state |
| assets/manifest.json | Source node, safe relative path, MIME type, hash, retrieval status |

Define JSON schemas during core implementation and reject unsupported versions. Resolve aliases deterministically; reject cycles and missing references. Define light/dark mode representation explicitly in the contract; generators must not invent an undocumented DTCG extension. Test source color conversion, units, typography, aliases, and mode selection.

Paths must remain inside the designated design/output root after resolution. Reject traversal, absolute output paths, collisions, and unsafe symlink destinations. Write via temporary files followed by atomic replacement. Never overwrite hand-written theme or component files without a reviewed change.

Design data may be versioned when the project permits it. Exclude credentials, signed download URLs, temporary captures, and unapproved proprietary or licensed material. Figma text is untrusted content and must never become executable instructions.

## 6. Flutter adapter

Reuse the available design-tokens, figma-to-widget, visual-verification, responsive-adaptive, accessibility/RTL, performance, state-management, architecture, and review skills. Discover their actual installed names; do not assume old marketplace names remain valid. Keep upstream plugins unchanged. Treat referenced skills as dependencies with preflight checks, not assumed tools.

Generate readable Dart theme files in the consumer's shared theme location (normally `lib/core/theme/`), including ThemeExtension tokens and light/dark values. Reuse existing theme types where possible. Do not add build_runner for generation.

Use the component map to reuse widgets before creating new ones. Map layout intent rather than copying absolute coordinates indiscriminately. Respect feature-first Clean Architecture, Cubit/Bloc orchestration, use cases, typed failures, and separation of UI from business logic. Match the project's package name and import conventions rather than hardcoding SAT/EST imports.

Use alchemist as the agreed golden-testing direction, subject to checking current compatibility and supported APIs before the implementation plan. Do not assume an option called `diffThreshold` exists in that package. The core comparator provides the specified Figma comparison gate independently of the regression-test library.

Capture with the required fonts, sizes, theme, locale, text scale, and pixel ratio. Cover critical interaction states and the project's responsive breakpoints. Prefer const widgets, lazy lists, scoped rebuilds, correctly disposed controllers, and measured optimizations. RepaintBoundary and image caching changes need evidence rather than blanket insertion.

## 7. Compose adapter

Use Kotlin, Compose/Material 3, ViewModel + StateFlow, sealed UI state, and lifecycle-aware collection. Hilt is the approved default for new projects; preserve an existing project's approved DI and navigation architecture. Verify compatible stable toolchain versions when planning implementation; the version numbers mentioned in the old chat are not a lockfile.

Generate readable theme code: ColorScheme, Typography, spacing, and shapes, using CompositionLocal where appropriate. Map auto layout to Row/Column and constraints to suitable modifiers; use stable keys in lazy collections and separate state holders from rendering.

Use the common component map by default. Figma Code Connect is an optional integration only when the account, tooling, and project support it; it must not be required for building UI.

Use Roborazzi for local/JVM screenshot regression testing, subject to compatibility verification. Use emulator/device captures for real interactions, keyboard, scrolling, and motion. mobile-mcp is the approved candidate for device automation; check availability before use and document setup if absent. A JVM screenshot is not evidence of device behavior or device performance.

Reuse the selected ECC material for Android architecture, Kotlin patterns, coroutines/flows, testing, and Kotlin review only after verifying each source path and redistribution license. Kotlin reviewer may be an agent rather than a skill. Preserve attribution and notices; do not enable or copy the entire ECC plugin.

Performance verification should include appropriate compiler stability/recomposition diagnostics and measured startup/scrolling benchmarks. Baseline Profiles and Macrobenchmark belong in a representative runnable target, not fabricated passing reports.

## 8. Visual comparison and acceptance

Capture prerequisites must match before comparison: dimensions, scale, crop/insets, fonts, theme, locale/direction, text scale, deterministic content, and settled animation state. Record renderer differences. Do not resize one image silently to force equal dimensions.

The core comparator must produce reference, actual, diff, overlay, and a machine-readable report. Define the default changed-pixel ratio as changed eligible pixels divided by total eligible pixels. Record the channel-difference threshold, alpha/color handling, masks, and image hashes. Proposed default acceptance is at most 2% changed pixels; the exact per-channel tolerance must be selected against fixtures and approved before use. Zero eligible pixels is invalid. Masks require a documented reason and may not hide layout defects.

Pixel ratio is not a measurement of logical layout error. Where a 1 logical-pixel geometry tolerance is used, measure element bounds separately or report that measurement unavailable. Check critical elements separately so a small missing icon does not pass merely because the whole screen is large.

Run an initial capture and comparison, then at most four corrective iterations per component/screen. Each iteration identifies discrepancies, applies a targeted fix, and recaptures. Never change the reference or relax tolerances to manufacture a pass. After exhaustion, report unresolved differences and block visual acceptance pending owner review.

After visual approval, establish platform regression goldens. These detect future regressions against approved app output; they do not independently prove fidelity to Figma. Baseline replacement requires review of changed images and an approval tied to those image hashes.

Final acceptance includes human inspection of the visual report plus passing relevant code, interaction, accessibility, and responsive checks. Every check reports passed, failed, blocked, or not run with evidence. No blanket “pixel-perfect” claim for untested targets.

## 9. Hooks and enforcement

Enable project-specific checks only when the consumer has a valid design/figma/manifest.json. Normal work in unrelated projects must remain unaffected.

Detect unauthorized literal colors, typography sizes, and design spacing in relevant UI files. Permit generated theme files and documented non-design constants, such as zero, arithmetic, and test fixtures. Prefer syntax-aware checks over unrestricted regexes. Existing code requires a baseline so adoption does not rewrite unrelated screens.

Guard known golden-update commands with an approval record; cover documented platform commands and test Windows path/quoting behavior. Hooks provide assistance and cannot guarantee interception of every command spelling. CI must independently run the same policy and comparison checks. Failed checks explain the file, rule, and correction; missing dependencies must not yield a false pass.

## 10. Errors and recovery

| Condition | Required behavior |
| --- | --- |
| MCP disconnected or access denied | Stop extraction with connection/access guidance; do not infer missing details from a screenshot |
| Required capability absent | Report blocked operation; offer only explicit supported alternatives |
| Rate limit/budget exhausted | Preserve completed nodes and resume metadata; honor available retry information |
| Missing font/asset | Block affected capture; identify exact missing item |
| Stale bundle or changed approval hash | Revalidate/refresh and obtain affected approval again |
| Invalid token, alias cycle, unsupported mode | Reject before code generation; identify token path |
| Generator target conflicts | Show a diff and preserve user-authored files |
| Capture mismatch or failed comparison | Report failed prerequisites/differences; never publish a pass |
| Four fixes exhausted | Preserve reports and request owner decision about remaining differences |

## 11. Repository and evidence

Planned implementation layout:

```text
.claude-plugin/marketplace.json
plugins/figma-core/{skills,agents,scripts,hooks,.claude-plugin}/
plugins/figma-flutter/{skills,scripts,hooks,templates,.claude-plugin}/
plugins/figma-compose/{skills,scripts,hooks,templates,.claude-plugin}/
docs/specs/
docs/plans/
docs/adr/
tests/scripts/
tests/fixtures/
tests/evals/
```

Only create component directories that are implemented. Prefer one supported entry-point format and verify CLI discovery. Each distributable plugin must resolve its dependencies portably without absolute user-specific cache paths.

Record ADRs for shared core, DTCG/modes, caching/budgets, alchemist, Roborazzi, component maps, selective ECC reuse, upstream plugin isolation, Hilt, and bounded comparison iterations. Each ADR gives context, alternatives, decision, consequences, and evidence. Consumer projects receive brief `docs/design-decisions/` notes for important per-screen choices and deviations.

## 12. Verification and delivery stages

1. **Core:** Offline tests for schemas, alias/mode resolution, token audit, safe paths, atomic checkpoint/resume, cache invalidation, and request-budget concurrency. Fixtures contain at least two screens and three components/variants, with no live calls. Mark synthetic fixtures as synthetic; never call them real Figma exports.
2. **Comparison:** Test identical images, boundary tolerance, alpha, incompatible sizes, invalid/empty masks, missing files, changed fonts, and a small critical missing element. Verify reports and failing exit statuses.
3. **Flutter:** Generator determinism/idempotence tests and a runnable sample; format, analyze, widget/interaction tests, real-font captures, and golden matrix. Pin a verified compatible toolchain.
4. **Compose:** Generator tests and a runnable sample; compilation, unit tests, Roborazzi captures, and emulator interaction evidence. Pin a verified compatible toolchain.
5. **Packaging/enforcement:** Validate marketplace/plugin manifests, skill discovery, dependency errors, hooks enabled/disabled behavior, approval invalidation, and clean-project installation. Test Windows and at least one Unix environment before claiming portability.
6. **Evaluation:** Exercise skill triggers and full fixture-based workflows for both platforms. Review actual artifacts, not merely instruction text. Run a live authorized Figma pilot separately before claiming real-world extraction works.

Delivery order: approved written spec → reviewed core implementation plan → core → Flutter adapter → Compose adapter → integration and installation evidence. Platform plans use the established core contract. Keep an explicit progress record; incomplete tooling or unavailable device tests remain visible.

## 13. Clarifications made during handoff

These preserve the approved goal while removing unsafe assumptions from conversational examples: no unconditional rate-limit number; no silent token rounding; no unsupported command/API guarantees; no inference of per-node changes from file version alone; no universal source/plugin availability; no unverified dependency versions; no direct equivalence between pixel percentage and logical geometry; no claim that hooks are a complete security boundary.

The owner reviews these clarifications with this specification before an implementation plan is written.

## 14. Reference checks

Consulted on 2026-10-09 for capability and quota clarification:

- https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/
- https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/
- https://developers.figma.com/docs/figma-mcp-server/tools-not-loading/

Dependency APIs, licenses, plugin command syntax, and platform toolchain versions require direct official-source verification when preparing the relevant implementation plan. The original chat's research is historical context, not proof of currently installed capabilities.
