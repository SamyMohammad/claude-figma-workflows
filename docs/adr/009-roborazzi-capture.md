# ADR-009: Measured native Compose capture evidence

Status: Accepted for the synthetic fixture workflow; actual execution evidence is recorded in the C4 implementation report.

The adapter uses Robolectric API36 native graphics and Roborazzi1.76.0. The screenshot harness records Android configuration, Compose density/fontScale, target bounds, actual PNG dimensions/color space/hash, explicit content font registry, settled clock state and the compiled generated AppThemeIdentity. It captures only a tagged target; window decor is excluded, so crop is target-local and insets are zero. Graphic scenes are static. A frozen clock alone is not sufficient evidence for animated consumer scenes: settle and assert their application state first.

Canonical independent sources are five160x160 no-text Pillow vectors. Home/Button/Card are lightLTR; Review/Badge are darkRTL, locale en-US. Separate synthetic source bundles declare Home240-width and fontScale1.5 variants. Text test variants use bundled Roboto and repeat actual PNG bytes deterministically; they are separate resource/rendering checks, without an independent text reference or liveFigma fidelity assertion. The font registry records the resource explicitly supplied to Text; it does not establish arbitrary fallback glyph provenance.

`prepare_capture(reference_meta, measured, image)` validates the measured receipt schema, image hash/dimensions, target bounds and density; it requires all source-matched facts, including actual content/font registry, crop and textScale, to agree. It emits only the strict core metadata fields. Platform is android and renderer robolectric-native. Adapter-only compiled identity and versions stay in capture-receipt.json.

`prepare-capture` CLI additionally obtains a fresh export through the explicit trusted core command, verifies compiled token/manifest/config identity, regenerates the expected file hashes, checks generator-owned bytes and packaged font resource inputs, and writes actual-meta.json only under app/build/figma-candidates/. Core compare remains the comparison authority; offline freshness is unverified and human visual review is not_run. Synthetic test approvals authorize only declared test sources/policy and never unrelated captures. Every comparison binds the actual PNG hash through the capture receipt and core evidence hash.

Candidate capture command, from the sample project:

```powershell
./gradlew.bat :app:testDebugUnitTest --tests '*FixtureCaptureTest' '-Proborazzi.test.record=true'
```

The project actually exposes recordRoborazziDebug, compareRoborazziDebug, verifyRoborazziDebug and verifyAndRecordRoborazziDebug. Record creates/replaces screenshots; verify checks existing baselines; verifyAndRecord updates while verifying. These tasks are not aliases for core source comparison and must not publish approved source references. C6 owns baseline publication. The explicit property above is for candidate builds only; screenshot tests skip recording when that property is absent. All outputs go under build/figma-candidates, never approved source folders.

The template is the executable synthetic harness with __FIXTURE_PACKAGE__ substituted. Adapt scene/node declarations, static state assertions and the font registry to the consumer's actual content; sourceRevision is fixture metadata and must be bound to the fresh core export. Reference metadata is never copied into the measured receipt. The v2 Compose rule replaces the deprecated factory and retains real idle, displayed-target, size and configuration assertions.

After a failed source comparison, obtain core correction authorization before an approved-target edit, with a hard limit of four. Source PNGs/policy are immutable. Store source, actual, diff, overlay and the exact failure/correction reports. Synthetic approvals used by tests are clearly labelled and live only in separate test bundles. No pass of these graphics establishes text fidelity or owner approval.
