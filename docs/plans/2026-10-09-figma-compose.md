# Figma Compose Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an installable `figma-compose` plugin that turns approved local Figma bundles into project-native Compose themes and implementation work, captures actual Android UI, delegates visual verification to core, and protects reviewed regression baselines.

**Architecture:** Core remains the authority for bundle validation, token resolution, approvals and comparison. Compose owns Kotlin emission, project adaptation, capture configuration and Kotlin policy checks. An explicit JSON receipt bridges plugins; neither plugin guesses the other's installation directory. Screen implementation is an agent workflow grounded in source context, not an automatic parser of arbitrary natural-language layouts.

**Tech Stack:** Existing Python 3.12 runtime/lock; Kotlin, Compose Material 3, Android Gradle, Robolectric/Roborazzi; Kotlin PSI for code policy; existing Android SDK/emulator for device checks. No REST client or new MCP server. Hilt is the default recommendation for product DI when needed; preserve existing project choices.

**Spec:** `docs/specs/2026-10-09-figma-workflows-design.md`, especially sections 2–5, 7–12. Implemented core contract: `docs/adr/005-bounded-corrections.md` and current core scripts/schemas.

**Status:** Written plan awaiting owner review. Execution method remains subagent-driven, as previously selected. Compose is prioritized before Flutter at the owner's request on 2026-10-09. No Compose runtime implementation has started.

## Global constraints

- “Platform plugins consume local design bundles. They do not independently fetch the same Figma data.”
- “Preserve exact source values and node references.”
- “Any subsequent token change invalidates approval.”
- “Never overwrite hand-written theme or component files without a reviewed change.”
- “Use the common component map by default.”
- “A JVM screenshot is not evidence of device behavior or device performance.”
- “Every check reports passed, failed, blocked, or not run with evidence.”
- Core metadata requires source-backed `containsText`, exact used-font hashes, modes and capture conditions. Visual evidence includes token content hash. At most four corrections per separately owner-approved reference/policy run; no silent reference/tolerance replacement.
- Respect each consumer's existing architecture, Gradle conventions and DI/navigation; no forced upgrades or unrelated refactors.
- No global plugin enablement, upstream cache edits, new remote publication, physical-device setting changes, secrets, or live-Figma success claims in this milestone.

## Review focus

1. A valid core token can exceed Kotlin Float/Int capacity; block that platform conversion instead of truncating or crashing (C2).
2. Two semantic token names can normalize to the same Kotlin name, or contain code-looking text; reject ambiguity/injection (C2).
3. A changed source, role/font mapping or candidate image can invalidate an old golden approval; bind publication to exact candidate content (C4/C6).
4. Android rendering density, font scale and insets can differ from screenshot settings even if image dimensions coincide; verify actual measurements (C4/C7).
5. Comments, strings, import aliases and existing literals can cause false policy results; inspect Kotlin syntax and apply an adoption baseline (C5).

## Planning evidence and toolchain policy

Read-only inspection found Android SDK platforms through API 37, installed API 36 system images, an existing `Pixel_9a` AVD, and Android Studio JBR 21.0.3. The AVD records density 420 and 1080×2424 pixels; it has not been booted or tested for this milestone. No mobile MCP tools are exposed in this session. The available ADB/emulator path is the fallback; lack of mobile-mcp does not prevent JVM tests.

Official metadata checked on 2026-10-09:

| Component | Candidate sample version | Evidence/meaning |
| --- | --- | --- |
| AGP | 9.4.0 | Current stable official release page |
| Gradle wrapper | 9.6.0 | AGP 9.4 minimum/default |
| Kotlin / Compose compiler / PSI | 2.4.21 | Current Kotlin documentation; compiler plugin matches Kotlin |
| Compose BOM | 2026.09.00 | Google Maven metadata and Android setup page |
| Activity Compose | 1.13.0 | Google Maven metadata |
| Lifecycle Compose | 2.11.0 | Google Maven metadata |
| Roborazzi | 1.76.0 | Upstream latest stable release, published 2026-09-29 |
| Robolectric | 4.17 | Maven Central metadata |
| AndroidX test ext JUnit / runner | 1.3.0 / 1.7.0 | Google Maven metadata |
| Macrobenchmark / Baseline Profile plugin | 1.5.0 / 1.5.0 | Google Maven metadata |
| JUnit | 4.13.2 | JUnit 4 used by the Roborazzi Android test contract |

These are candidate integration pins, not a claim that a build passed. Kotlin's published full-support matrix currently ends at AGP 9.3.1 for 2.4.21, while AGP 9.4 is newer. C3 must compile/run the candidate combination before it becomes the supported sample profile. If that fails due to compatibility, record the exact failure and settle a compatible profile before C4; do not label the pair verified or downgrade an existing consumer silently. Existing consumers retain their verified toolchain. The sample uses compile/target SDK 36 (available stable test target), min SDK 26, JDK 21, JVM target 17; no APK publication is planned.

AGP 9 uses built-in Kotlin: do not apply `org.jetbrains.kotlin.android` on top of it. Apply the Compose compiler plugin and verify effective Kotlin/compiler versions in the dependency/build reports. Avoid deprecated `android.kotlinOptions` in new sample files.

ECC cache version 1.10.0 includes four selected skill sources plus `agents/kotlin-reviewer.md` under MIT, copyright 2026 Affaan Mustafa. The source agent uses a Claude-specific model label; preserve attribution but adapt model/tool metadata to the host. No entire ECC plugin activation. Copy only the relevant references with their license and recorded hashes during C8.

## File ownership and dependency order

| Task | Responsibility | Main files | Needs |
| --- | --- | --- | --- |
| C1 | Core export/approval/path bridge and adapter input contract | Core export module/CLI; Compose receipt/config schemas | Existing core |
| C2 | Deterministic Kotlin theme generation and safe publication | Compose generator modules; generator tests | C1 |
| C3 | Runnable sample and exact synthetic source bundle | `samples/compose-fixture/`, Compose fixture builder | C2 |
| C4 | Roborazzi capture adapter and measured metadata | Capture test/template, receipt validation | C3 |
| C5 | Kotlin policy scanner and opt-in hooks | Kotlin PSI tool, Python hook entry, policy tests | C2/C3 |
| C6 | Reviewed golden publication and independent verification | Golden proposal/publish/check tools | C4/C5 |
| C7 | Compose implementation/capture/review skills and device/perf checks | Skills, device test and benchmark templates | C4–C6 |
| C8 | Installation, licensed references and release evidence | Plugin/marketplace, docs/ADRs/evals | C7 |

Repository Python package: `plugins/figma-compose/scripts/compose_adapter/`. Add it to pytest's existing import paths without replacing core paths. Shared authority stays in `plugins/figma-core/scripts/figma_core/`; adapter helpers must not reimplement core token/approval/bundle validation.

## Task 1: C1 — A portable, approved core receipt

**Files:** Create core `adapter_export.py`, `tests/scripts/test_adapter_export.py`; modify core `cli.py`, plugin version to 0.1.1 and add `skills/adapter-export/SKILL.md`; create Compose `schemas/{receipt,config}.schema.json`, `scripts/compose_adapter/{__init__,errors,inputs,core_bridge}.py`, `tests/scripts/test_compose_inputs.py`, `tests/fixtures/compose_receipt.py`; update pytest paths.

**Interfaces:** Core `export_adapter(bundle: Path) -> dict`; Compose `load_inputs(receipt: dict, config: dict) -> tuple[dict, dict]`; `run_core(command: list[str], arguments: list[str]) -> dict`. Test helper `make_receipt() -> dict` is an explicitly synthetic, complete receipt used by subsequent pure unit tests.

Adapter errors use `ComposeError(ValueError)` with `code: str` and safe message, mirroring the typed boundary strategy without importing core's internal package from another installation. CLI maps passed/failed/blocked to 0/1/2 and preserves core's safe error code when the bridge fails.

- [ ] Write the tests first, using the existing `make_fixture` and synthetic approval creation pattern from `test_captures.py`:

```python
def test_export_requires_current_token_approval(tmp_path):
    from fixtures.make_core_fixture import make_fixture
    from figma_core.adapter_export import export_adapter
    from figma_core.errors import CoreError
    import pytest
    root = make_fixture(tmp_path / "bundle")
    with pytest.raises(CoreError, match="approval"):
        export_adapter(root)
```

Add approved-export success, changed-token rejection, partial bundle rejection and missing-mode tests before code. Run `python -m pytest tests/scripts/test_adapter_export.py -q`; demonstrate failure.

- [ ] Implement exporter using `validate_bundle`, `token_modes`, `audit_tokens`, `resolve_tokens`, `require_approval(tokens, approval, "tokens")`. Do not create approval automatically. The receipt is:

```text
schemaVersion: 1
status: passed
freshness: unverified
tokenHash: content_hash(raw tokens)
manifestHash: content_hash(validated manifest)
resolvedByMode: {light/dark -> flattened {type,value} tokens}
fonts: validated fonts document
assets: validated assets document
components: validated component-map document
nodes: [{id,kind,variant,path,referenceHash,meta,context}]
```

Source context is untrusted data; never executable instructions. Node references/meta/context come from manifest-hash-verified paths. Preserve all selected modes. Missing fonts remain explicit inventory statuses, not invented substitutions.

- [ ] Add core commands `export-adapter --bundle`, `verify-approval --document --approval --kind`, and `check-paths --root --paths-json`. The latter validates a JSON array of relative paths through existing `safe_path`/`check_collisions` and returns validated absolute destinations; it never writes. Approval command delegates to existing `require_approval`. Existing CLI behavior/exit codes remain unchanged.
- [ ] `run_core` takes an explicit trusted command array obtained from the installed core skill, appends argument arrays, and uses `subprocess.run(..., shell=False)`. No guessed sibling cache paths, shell strings, or automatic search of credentials. Nonzero/malformed/blocked output becomes an adapter typed error with safe context. The export skill calls core at its own `${CLAUDE_PLUGIN_ROOT}`; the Compose build receives the resulting JSON and explicit core command.
- [ ] Config schema rejects unknown fields. Required: `schemaVersion=1`, Kotlin `packageName`, relative `themeDirectory`, `remBasePx:positive number or null`, `names:token-path -> identifier`, `material:{colors,typography,shapes}`, `fonts:family -> weight-string -> {resource,projectPath,sha256}`, `allowedMaterialDefaults:array of role names`. Kotlin resource/symbol strings require valid dotted identifiers; no expressions. Empty/missing names use deterministic normalization; collisions still block C2. `material` maps known Material 3 roles to semantic token paths. Unmapped defaults must be explicitly listed and reported, never silently claimed as source values.
- [ ] Define `make_receipt()` as follows. These are synthetic test values and approval evidence; pure tests do not claim actual font files exist. This uses the C1 exporter implemented earlier in this task:

```python
def make_receipt():
    from tempfile import TemporaryDirectory
    from pathlib import Path
    from fixtures.make_core_fixture import make_fixture
    from figma_core.documents import read_json
    from figma_core.storage import atomic_json, file_hash
    from figma_core.approvals import content_hash
    from figma_core.adapter_export import export_adapter
    with TemporaryDirectory() as directory:
        root = make_fixture(Path(directory) / "bundle")
        tokens = read_json(root / "tokens.json")
        for mode in ("light", "dark"):
            group = tokens[mode]
            group["type"]["body"]["$value"]["fontFamily"] = "Roboto"
            group["color"]["onPrimary"] = {"$type": "color", "$value": {
                "colorSpace": "srgb", "components": [1, 1, 1], "alpha": 1}}
            group["color"]["background"] = {"$type": "color", "$value": {
                "colorSpace": "srgb", "components": [1, 1, 1] if mode == "light" else [0, 0, 0], "alpha": 1}}
            group["shape"] = {"radius": {"$type": "dimension", "$value": {"value": 16, "unit": "px"}}}
            group["frame"] = {"size": {"$type": "dimension", "$value": {"value": 160, "unit": "px"}}}
            group["motion"] = {
                "duration": {"$type": "duration", "$value": {"value": 200, "unit": "ms"}},
                "easing": {"$type": "cubicBezier", "$value": [0.2, 0, 0, 1]}}
        atomic_json(root, "tokens.json", tokens)
        approval = {"schemaVersion": 1, "kind": "tokens", "contentHash": content_hash(tokens),
                    "owner": "synthetic-test", "evidence": "fixture-only", "approvedAt": "2026-10-09T00:00:00Z",
                    "modes": ["light", "dark"], "deviations": []}
        atomic_json(root, "tokens-approval.json", approval)
        manifest = read_json(root / "manifest.json")
        for path in ("tokens.json", "tokens-approval.json"):
            manifest["files"][path] = file_hash(root / path)
        atomic_json(root, "manifest.json", manifest)
        return export_adapter(root)
```

When the sandbox requires a workspace temp root, configure `TEMP`/`TMP` for tests or make this helper accept a pytest-provided directory. Do not weaken production path checks.
- [ ] Test injected symbols, unknown schema, wrong type/modes, future core receipt version and malformed bridge results; run focused then full suite once; commit `feat(core): export approved adapter inputs`.

## Task 2: C2 — Readable Kotlin theme files without token changes

**Files:** Create Compose `generator.py`, `kotlin_values.py`, `kotlin_theme.py`, `generated_files.py`; `scripts/compose.py`; `tests/scripts/test_compose_generator.py`, `test_compose_writes.py`; `docs/adr/007-compose-token-generation.md`.

**Interfaces:** `render_theme(receipt: dict, config: dict) -> dict[str, str]`; `apply_theme(project: Path, files: dict[str, str], core_command: list[str], source_identity: dict) -> dict`. `render_theme` returns Kotlin filenames; the caller prefixes the validated configured theme directory. Return report includes changed/unchanged files and recorded source/config hashes. CLI: `generate --bundle --receipt --config --project --core-command-json --dry-run`; writing requires omitting `--dry-run` after reviewing the proposed output. Both modes obtain a fresh core export for `--bundle` and compare receipt token/manifest hashes before accepting input; a previously exported receipt is not proof that approval is still current. Test a token/file change between export and generation blocks writing.

- [ ] Before implementation, add focused tests:

```python
def test_fractional_spacing_is_not_rounded():
    from fixtures.compose_receipt import make_receipt
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    receipt["resolvedByMode"]["light"]["space.small"]["value"]["value"] = 13.3
    files = render_theme(receipt, fixture_config())
    assert "13.3.dp" in files["AppTokenValues.kt"]

def test_generated_name_collision_blocks():
    import pytest
    from fixtures.compose_receipt import make_receipt
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    receipt["resolvedByMode"]["light"]["space_small"] = receipt["resolvedByMode"]["light"]["space.small"]
    with pytest.raises(ValueError, match="collision"):
        render_theme(receipt, fixture_config())
```

Define `fixture_config()` in this test module. Group fallback markers below explicitly authorize/report only the *unmapped* Material defaults; they do not turn defaults into source tokens. Extend the C1 config schema to accept these three exact group markers alongside explicit role names, and keep their use visible in the generation report:

```python
def fixture_config():
    return {
        "schemaVersion": 1, "packageName": "dev.figma.fixture.core.theme",
        "themeDirectory": "app/src/main/java/dev/figma/fixture/core/theme",
        "remBasePx": None, "names": {},
        "material": {
            "colors": {"primary": "color.primary", "onPrimary": "color.onPrimary", "background": "color.background"},
            "typography": {"bodyLarge": "type.body"},
            "shapes": {"small": "shape.radius", "medium": "shape.radius", "large": "shape.radius"}},
        "fonts": {"Roboto": {"400": {"resource": "dev.figma.fixture.R.font.roboto_regular",
                                    "projectPath": "app/src/main/res/font/roboto_regular.ttf", "sha256": "a" * 64}}},
        "allowedMaterialDefaults": ["colorScheme:unmapped", "typography:unmapped"],
    }
```

The font hash is synthetic for pure rendering tests; filesystem publication tests use actual fixture-file hashes, and C3 supplies the real downloaded font. No source-fidelity acceptance may use a visible unmapped role without a documented owner-approved deviation. Run the tests and observe RED.

- [ ] Emit `AppTokens.kt`, `AppTokenValues.kt`, `AppTheme.kt`, `AppThemeIdentity.kt`, and optional `AppShapes.kt` only when configured. `AppThemeIdentity` records generated source token and config hashes so the compiled capture harness can report the identity it actually renders. Use immutable value properties, `CompositionLocal`, typed `Color`, `Dp`, `TextStyle`, duration values and `CubicBezierEasing`. Map Material 3 colors/typography/shapes only through explicitly supplied role paths. Report every allowed Material default. Do not overwrite an existing theme or invent missing semantic roles.

```kotlin
val LocalAppTokens = staticCompositionLocalOf<AppTokens> {
    error("AppTheme is required")
}

@Composable
fun AppTheme(dark: Boolean, content: @Composable () -> Unit) {
    val tokens = if (dark) darkTokens else lightTokens
    CompositionLocalProvider(LocalAppTokens provides tokens) {
        MaterialTheme(
            colorScheme = if (dark) darkColors else lightColors,
            typography = appTypography,
            shapes = appShapes,
            content = content,
        )
    }
}
```

Define all emitted identifiers (`AppTokens`, token sets, color sets, typography and shapes) in generated files; validate the output by compiling C3. This code is the intended API, not a literal promise to insert it into every existing project.

- [ ] Logical source px maps to dp for geometry and sp for type at textScale 1. Rem requires explicit `remBasePx`; lineHeight multiplier becomes fontSize × lineHeight in sp. sRGB channels become Compose float channels with alpha. Preserve raw receipt values and report target precision limitations. Reject unrepresentable Float/Int values, negative shape sizes/font sizes and fractional-millisecond durations when an Int millisecond API is required; no clamping, hidden rounding or integer overflow. Allow negative offsets where the actual consuming API supports them. Preserve font weights and verify every configured family/weight resource mapping before publication.
- [ ] Publish only under validated project destinations returned by core `check-paths`. Record `.workflow/compose-theme.json` with source token/manifest/config identities and generated file hashes. A subsequent run may replace only files whose current hash matches this previous generated manifest; hand edits require a reviewed diff. Stage all output first; on replacement failure restore prior files or return explicit partial/error state and block compilation. Never claim atomic multi-file publication solely because individual replacements are atomic.
- [ ] Add idempotence, alias-resolved values, alpha, rem with/without base, typography/lineHeight, UTF-8/injected names, huge numbers, keyword/collision, source config change and hand-edit protection tests. Rerun targeted tests then full Python suite; commit `feat(compose): generate approved Kotlin theme values`.

## Task 3: C3 — A compiled sample grounded in a synthetic source

**Files:** Create `samples/compose-fixture/{settings.gradle.kts,build.gradle.kts,gradle.properties,gradlew,gradlew.bat,gradle/wrapper/gradle-wrapper.jar,gradle/wrapper/gradle-wrapper.properties}`, `gradle/libs.versions.toml`, `app/build.gradle.kts`, Android manifest, `MainActivity.kt`, `presentation/{FixtureRoute,FixtureScreen,FixtureViewModel}.kt`, `core/components/{ActionButton,ContentCard,StatusBadge}.kt`, font/license resources, `tests/fixtures/make_compose_fixture.py`, `tests/fixtures/compose-v1/`, `docs/verification/compose-toolchain.md`.

**Interfaces:** `make_compose_fixture(root: Path, font: Path) -> Path` returns a complete synthetic core-compatible bundle plus an adapter config under `design/figma/compose/config.json`. Components receive typed state and callbacks; `FixtureViewModel` exposes `StateFlow<FixtureUiState>` for local screen selection only. There is no invented backend/business domain in this sample.

- [ ] Add an Android unit/Compose test proving the generated theme and component imports compile, and a UI test that clicking `Continue` selects the review screen. Demonstrate failure before sample implementation. Use JUnit 4 and Compose test APIs; do not add MockK/Kotest just for simple tests.
- [ ] Seed root Gradle plugins with candidate pins and AGP 9 built-in Kotlin. Configure the app explicitly:

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("io.github.takahirom.roborazzi")
}
android {
    namespace = "dev.figma.fixture"
    compileSdk = 36
    defaultConfig {
        applicationId = "dev.figma.fixture"
        minSdk = 26
        targetSdk = 36
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    buildFeatures { compose = true }
    testOptions.unitTests.isIncludeAndroidResources = true
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
kotlin.compilerOptions.jvmTarget.set(JvmTarget.JVM_17)
```

Import `JvmTarget` explicitly. Root plugin versions, repositories `google()/mavenCentral()/gradlePluginPortal()` and version catalog dependency aliases use the planning table; Compose libraries use the BOM, including test configurations. Roborazzi artifacts `roborazzi`, `roborazzi-compose`, and `roborazzi-junit-rule` all use 1.76.0. Native Robolectric uses 4.17. Record resolved effective Kotlin/compiler versions; no incompatible Kotlin Android plugin alongside AGP 9.
- [ ] Obtain the Gradle wrapper from the official 9.6.0 distribution, verify its published checksum, generate/check in wrapper files and pin `distributionSha256Sum`. Use existing JBR for execution, but no absolute machine path in tracked Gradle/local.properties files. Gradle/SDK caches stay local; add appropriate ignores. Run `:app:compileDebugKotlin :app:testDebugUnitTest :app:assembleDebug`; freeze the sample toolchain only after success and record any compatibility ruling.
- [ ] Download Roboto variable font from the Google Fonts `ofl/roboto/Roboto[wdth,wght].ttf` source at a recorded commit, plus its OFL file. Preserve original bytes/license and SHA256. Expose a stable Android resource name. If retrieval/licensing fails, report the font check blocked; do not substitute another font and call the real-font check passed.
- [ ] Build two screen contexts and three component contexts with explicit source geometry, values, variants, interaction expectations and font use. Label every ID/reference as synthetic. Independently draw no-text graphic references from this declared vector fixture using Pillow; never establish a Figma reference from an app screenshot. Separate the no-text pixel test from real-font rendering/golden tests. Use 160 logical-pixel graphic frames and multiples-of-eight geometry, plus light/dark and RTL variants where declared; every reference records actual scale/theme/direction and `containsText`.
- [ ] Implement the declared sample UI using generated tokens and three reusable components. Render only in composables; observe ViewModel state with lifecycle-aware collection. Pass user actions as callbacks, use stable keys where lists exist. Existing-product workflows coordinate business operations through domain use cases; sample screen selection is UI state. Hilt remains the product DI default when injection is needed, rather than a dependency added to a dependency-free preview.
- [ ] Update component-map entries with Compose symbols, project-relative Kotlin paths and source hashes. One coordinator writes the map/manifest hashes using core structural checks; parallel workers never share that writer. Test mismatched variants, missing/stale symbols and project path containment. Record why Component Map is the default and Code Connect is optional in `docs/adr/008-compose-components.md`; commit `feat(compose): add a verified sample and component mapping`.

## Task 4: C4 — Measured Roborazzi capture inputs for core

**Files:** Create Compose `capture_metadata.py`, `templates/ComposeCaptureTest.kt`, `schemas/capture-receipt.schema.json`, sample `app/src/test/java/dev/figma/fixture/FixtureCaptureTest.kt`, `tests/scripts/test_compose_capture.py`, `docs/adr/009-roborazzi-capture.md`.

**Interfaces:** `prepare_capture(reference_meta: dict, measured: dict, image: Path) -> dict` returns actual core metadata only after checking observed image/renderer/font/viewport facts. `capture-receipt.json` includes measured pixel/logical bounds, density, fontScale, configuration locale/direction/theme, crop/insets, used-font hashes, settled animation state, rendered `AppThemeIdentity` hashes and renderer/toolchain versions. It is generated by the test harness, never a copied reference-meta file. Before comparison, verify the rendered identity and generator-owned file hashes against a fresh core export and current config. A stale compiled theme is blocked; adapter-only identity fields remain in the receipt, not inserted into the strict core meta schema.

- [ ] Write Python regressions for wrong observed density, fontScale, font hash, crop and image dimensions; a visually similar PNG must still block when its capture facts differ. Add an Android screenshot test before the template:

```kotlin
@RunWith(AndroidJUnit4::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [36], qualifiers = "w160dp-h160dp-mdpi")
class FixtureCaptureTest {
    @get:Rule val compose = createComposeRule()

    @Test fun graphicCapture() {
        compose.setContent { AppTheme(dark = false) { GraphicFixture() } }
        compose.waitForIdle()
        compose.onNodeWithTag("figma-target")
            .captureRoboImage("build/figma-candidates/graphic.png")
    }
}
```

Import each displayed test/API symbol from the verified library. `GraphicFixture` is the C3 token-sized graphic scene; UI test tags are stable fixture metadata, not business logic. Keep real-font text cases separate.
- [ ] Pin system qualifiers, frame bounds and clock conditions. Observe actual Android display metrics/configuration, Compose target bounds and image dimensions; do not claim `containsText` from screenshot inference. Compare source-backed text/used-font expectations with the test's actual content/font registry. Export measured facts into the receipt; report platform `android`, renderer `robolectric-native`.
- [ ] Write candidate captures under build artifacts, not approved golden/reference folders. Compile and run the manual capture test with `-Proborazzi.test.record=true` only in a clearly designated candidate task/output. Record/verify Gradle task names from actual `:app:tasks --all`; use `recordRoborazziDebug` and `verifyRoborazziDebug` for their documented semantics, not invented aliases. C6 governs publishing approved baselines.
- [ ] Run core comparison on independent no-text source references with matching measured conditions and synthetic test approvals. Test one targeted layout defect to demonstrate a failing gate. For real-font captures, verify rendering/resource hashes and deterministic golden behavior; do not call that a live-Figma fidelity result. Produce light/dark, supported widths and RTL/textScale cases as explicit source/test variants, not mismatched captures against one reference.
- [ ] After a failure, reserve a correction through core before edits. Stop after four approved-target corrections; never alter source/tolerance to reach green. Store source, actual, diff and overlay plus freshness/human-review state. Commit `feat(compose): capture reproducible Android visual evidence`.

## Task 5: C5 — Syntax-aware Kotlin policies and opt-in hooks

**Files:** Create `tools/compose-policy/{settings.gradle.kts,build.gradle.kts,src/main/kotlin/PolicyMain.kt,src/main/kotlin/KotlinPolicy.kt,src/test/kotlin/KotlinPolicyTest.kt}`, Compose `scripts/guard.py`, `hooks/hooks.json`, `schemas/project-policy.schema.json`, `tests/scripts/test_compose_hooks.py`; package the built scanner distribution beneath the Compose plugin in C8.

**Interfaces:** Scanner stdin JSON `{path,content,rules,allowedRanges}` → stdout JSON `{status,findings:[{rule,path,line,message}]}`, exit 0/1/2 for clean/findings/unavailable. Hook reads documented Claude JSON input. Policy activation requires a valid consumer `design/figma/manifest.json` and explicit `design/figma/compose/policy.json`.

- [ ] Write scanner tests first:

```kotlin
@Test fun ignoresStringAndComment() {
    val source = "val label = \"Color(0xff000000) and 16.dp\" // 20.sp"
    assertTrue(scanKotlin(source).isEmpty())
}
@Test fun findsImportedColorAlias() {
    val source = "import androidx.compose.ui.graphics.Color as Paint\nval x = Paint(0xff000000)"
    assertEquals(listOf("literal-color"), scanKotlin(source).map { it.rule })
}
```

`scanKotlin(source: String): List<PolicyFinding>` and `PolicyFinding(rule:String,line:Int,message:String)` are defined in `KotlinPolicy.kt`. Additional tests cover `.dp/.sp` literals and aliases, zero exceptions, constant arithmetic, malformed Kotlin, generated exemptions and source baseline ranges. Run the scanner unit tests RED before implementation.
- [ ] Use Kotlin compiler-embeddable PSI 2.4.21 and parse `KtFile`. Inspect calls/qualified expressions/imports rather than regex-scanning comments or string data. Recognize supported literal design colors, spacing and type sizes in configured presentation roots; report unsupported/dynamic patterns honestly. Do not claim a type-resolved compiler analysis from syntax alone. Allow documented zero/test constants and only hash-current generator-owned files; an arbitrary file header cannot exempt itself.
- [ ] Keep the scanner a standalone Kotlin JVM/application Gradle project with target 17 and JUnit 4.13.2 tests; it does not modify app source. Invoke it through the C3 wrapper using `samples/compose-fixture/gradlew -p tools/compose-policy test installDist` (the `.bat` equivalent on Windows). Build an installable distribution with dependency licenses. Do not add compiler-embeddable to a consumer APK.
- [ ] Hooks gate Write/Edit previews when available and reviewed baseline-update commands; unsupported tool forms must fall back to an independent policy check before approval/commit. For Edit, construct the proposed content only when the supplied old text uniquely matches; ambiguity blocks rather than analyzing the wrong file. Post-write feedback never silently reverts user changes. Validate prospective Kotlin source under project paths only.
- [ ] For projects without valid design manifest/policy, do nothing. For active projects, a missing scanner/Java/configuration yields a clear unavailable/block result, never a false clean gate. Test Windows path quoting, an unrelated project, generated files modified by hand, and existing source baselines. `check-policy --project --policy` uses the same scanner/rules independently of hooks; do not require remote CI to test parity.
- [ ] Commit `feat(compose): enforce opt-in Kotlin design policies`.

## Task 6: C6 — Review candidates before publishing goldens

**Files:** Create Compose `goldens.py`, golden CLI subcommands, `schemas/golden-proposal.schema.json`, `tests/scripts/test_compose_goldens.py`, sample screenshot verification configuration, `docs/adr/010-reviewed-compose-goldens.md`.

**Interfaces:** `golden_proposal(candidate: Path, source_identity: dict, capture_identity: dict) -> dict`; `publish_goldens(project: Path, candidate: Path, baseline: Path, proposal: dict, approval: Path, core_command: list[str]) -> dict`. Proposal binds relative image hashes, current core visual evidence hashes, tokenHash, theme/configHash and capture/toolchain identity. Owner approval uses core `kind=goldens` and the exact proposal hash.

- [ ] Test the critical race before implementation:

```python
def test_candidate_change_invalidates_publication(tmp_path):
    # Helper creates one candidate PNG and a clearly synthetic approval.
    candidate, baseline, proposal, approval = approved_candidate(tmp_path)
    (candidate / "screen.png").write_bytes(b"changed after review")
    with pytest.raises(ValueError, match="hash"):
        publish_goldens(tmp_path, candidate, baseline, proposal, approval, core_command())
    assert not (baseline / "screen.png").exists()
```

Define `approved_candidate` and `core_command` in this test module with the following code. These approvals are synthetic test records, not evidence of user review. No public unattended approval creation command is exposed:

```python
def core_command():
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    return [sys.executable, str(root / "plugins/figma-core/scripts/core.py")]

def approved_candidate(root):
    import json
    from PIL import Image
    from figma_core.approvals import content_hash
    from compose_adapter.goldens import golden_proposal
    candidate = root / "candidates"
    candidate.mkdir()
    Image.new("RGBA", (10, 10), "white").save(candidate / "screen.png")
    proposal = golden_proposal(candidate,
        {"tokenHash": "a" * 64, "themeConfigHash": "b" * 64, "visualEvidenceHashes": ["c" * 64]},
        {"renderer": "robolectric-native", "sdk": 36, "scale": 1, "textScale": 1, "locale": "en", "direction": "ltr"})
    approval = {"schemaVersion": 1, "kind": "goldens", "contentHash": content_hash(proposal),
                "owner": "synthetic-test", "evidence": "fixture-only", "approvedAt": "2026-10-09T00:00:00Z",
                "modes": ["light"], "deviations": []}
    approval_file = root / "approval.json"
    approval_file.write_text(json.dumps(approval), encoding="utf-8")
    return candidate, root / "goldens", proposal, approval_file
```
- [ ] Assemble review artifacts from candidate captures and core reports. A metric pass is insufficient: require owner visual approval before accepting source-fidelity baselines. Include the core evidence payload with its required tokenHash. Config/font/resource changes invalidate the adapter proposal even if its filenames stay fixed.
- [ ] Publish only after core verifies approval and all candidate hashes are rechecked. Validate destination paths with core; do not overwrite hand-written images outside the declared baseline directory. Record the accepted hashes/provenance atomically with the baseline update and expose failures/partial rollback. Enforce that verification mode fails after a deliberate UI change; no auto-record fallback.
- [ ] Guard baseline-mutating Roborazzi task/property forms, including `record`, `verifyAndRecord`, `roborazzi.test.record=true` and baseline clearing. Candidate-only capture is allowed only with a declared safe build output; it may not write approved reference directories. Hooks are assistance, not universal interception; independent `check-goldens` validates baseline/proposal identities and verifies screenshots in normal CI/check runs.
- [ ] Test initial unapproved publication, edited candidate, stale token/config, renamed baseline, missing files, source-reference confusion and a modified screen failing verify. Commit `feat(compose): publish only reviewed screenshot baselines`.

## Task 7: C7 — Build/review skills, device checks and measured performance

**Files:** Create Compose `skills/{build,figma-to-composable,compose-capture,compose-review}/SKILL.md`, focused references, sample `app/src/androidTest/.../FixtureInteractionTest.kt`, device capture helper, `benchmark/` test module with Startup/Scroll/BaselineProfile tests; `tests/evals/compose-cases.json`, `docs/adr/011-compose-runtime-and-di.md`.

**Interfaces:** `figma-compose:build` is the adapter ID already expected by core. It consumes the approved receipt/project/config and routes theme → reusable components → screens → candidate captures → core visual verification → reviewed goldens → policy/code review → per-screen notes. Core remains the single Figma/dispatcher owner.

- [ ] Run an independent baseline pressure scenario before writing skills: sparse context, missing font, stale component mapping, and demand for immediate code. Record actual hypothetical agent choices and missing-tool limits; do not invent failed/green traces. After writing skills rerun with a fresh agent and require missing-data requests/no affected source edits.
- [ ] Descriptions state trigger conditions only. Bodies explicitly inspect repository instructions and existing components/DI/navigation before edits; consume the current core export; reuse mapped components/variants; reject stale maps. UI stays rendering/actions/state observation. Domain/use cases own business operations; ViewModel/StateFlow coordinates them and lifecycle-safe collection renders state. No repositories in composables, invented API results, unnecessary DI migrations or blanket performance annotations.
- [ ] Describe Auto Layout → Row/Column/spaced arrangement, Fill/Hug/constraints → weights/measurement modifiers, overlay → justified Box, and variants → typed parameters. Preserve assets and user interaction. Document material-default decisions and deviations in `docs/design-decisions/<screen>.md`, with why, evidence and unresolved checks. Code Connect is optional; unavailable access must not block the default map.
- [ ] Before corrections call core's approved-target reservation. Obtain source-backed `containsText`, actual used fonts and measured metadata. Never use a source screenshot as an app asset, copy a reference into actual captures, relax tolerances or label unexecuted checks passed.
- [ ] Use the existing AVD only for a local sample smoke test, without changing saved AVD configuration or touching a physical device. Record selected device/SDK/renderer measurements. ADB fallback uses argument arrays and captures binary PNG with `adb exec-out screencap -p`; no text-shell redirection that corrupts bytes. Crop only measured app/node bounds, record insets, and require scale agreement with the source. Do not resize a capture to force matching dimensions. If density differs, obtain an independently rendered matching-scale synthetic/source reference or report the fidelity comparison blocked.
- [ ] Device tests exercise tapping, scrolling, keyboard/focus and lifecycle recreation with English UI and configured RTL/text-scale cases. Run `:app:connectedDebugAndroidTest` only on the selected local emulator; report an unavailable boot/device as blocked without fabricating results or installing new services.
- [ ] Add a benchmark module using verified Macrobenchmark/Baseline Profile plugin 1.5.0 and runner 1.7.0. Measure release/profileable sample startup and scrolling and collect a profile with `BaselineProfileRule`; never benchmark a debug build as production. Templates use the sample application ID, explicit navigation scenario and recorded device/version/build. Use compiler `reportsDestination`/`metricsDestination` to inspect stability and recomposition; do not put broad user types into a stability allowlist to hide problems. An emulator measurement is diagnostic, not a physical-device performance guarantee; no invented timing threshold or fake passing benchmark.
- [ ] Compile benchmark/profile templates and run where the emulator supports them. Record output artifact paths and collected/not_run/blocked distinctions. Commit `feat(compose): orchestrate native implementation and device review`.

## Task 8: C8 — Package the adapter and verify the actual contract

**Files:** Create Compose plugin manifest, runtime lock copy, packaged scanner distribution/notices, selected ECC reference files, `THIRD_PARTY_NOTICES.md`, `docs/installation-compose.md`, `docs/verification/compose-results.md`; update marketplace/README and add `tests/scripts/test_compose_packaging.py`.

- [ ] Write packaging tests before manifest changes: adapter absent from marketplace, missing core dependency, missing scanner/schema/resources and spaces in both installed plugin path/consumer cwd. Check actual parsed results, not only exit 0. Expect RED before packaging.
- [ ] Register core and Compose only; Flutter remains absent until implemented. Declare `dependencies:["figma-core"]` in Compose manifest. Runtime capability/schema checks require the new 0.1.1 export commands; a local marketplace has no tested release-tag version resolution yet, so do not invent constrained dependency behavior. Use name/version/description/author and default skill discovery; no duplicate build dispatcher or new MCP configuration.
- [ ] Copy exactly the four ECC skill references and one reviewer source identified during planning, record file hashes and include MIT notice. Adapt references selectively for the actual project/host; optional testing frameworks from upstream must not become mandatory new app dependencies. Keep upstream caches intact. Preserve notices for bundled compiler/parser dependencies and OFL sample font.
- [ ] Run Python/core regression suite, scanner JVM tests, sample compile/unit/lint/Roborazzi verification, device smoke tests and available diagnostic performance collection. Validate core, Compose and marketplace with `claude plugin validate ... --strict`. Test install in an isolated temporary Claude configuration and paths with spaces; confirm `claude plugin details` discovers `figma-compose:build` and core dispatch resolves it. Actual authenticated skill execution is separately recorded, never inferred from inventory.
- [ ] Reinstall dependencies in a clean environment and use verified wrapper checksums. Record Windows and available Unix results separately. Do not alter global Claude settings or publish remote CI merely to obtain another OS; unavailable execution remains blocked.
- [ ] Final acceptance report lists deterministic Kotlin generation, safe overwrite behavior, actual sample compilation/capture evidence, a deliberate screenshot regression failure, core comparison evidence, golden approval behavior, policy parity, architecture/performance review and licensed installation. A real Figma/production app pilot still needs an actual owner-selected file and live access; the sample cannot establish that claim.
- [ ] Update README to distinguish usable tools/skills from live proof, preserve task/ruling/review records, perform independent whole-branch review and fix material findings. Commit `feat(compose): package verified native design workflow`.

## Coverage and completion limits

Spec section 7 is covered by theme generation (C2), project-native composition/component reuse (C3/C7), Roborazzi (C4/C6), licensed Kotlin guidance (C8), device automation fallback/performance evidence (C7), and optional Code Connect (C7). Shared extraction stays in core; token/approval/source invariants are consumed through C1. Spec sections 8–10 are enforced by C4–C7 and independently verified in C8. Decision docs and installation evidence are C2–C8.

This plan produces the Compose adapter before Flutter, as requested. It does not claim to have built a platform application already. Python/JVM checks, actual Android captures, human visual approval, Unix execution and a live Figma pilot are separate evidence classes. A blocked environmental check must be visible in the final report and cannot be marked completed merely because a template was written.

## Sources consulted for this plan

- [Android AGP 9.4 compatibility](https://developer.android.com/build/releases/agp-9-4-0-release-notes).
- [Kotlin Gradle support matrix](https://kotlinlang.org/docs/gradle-configure-project.html).
- [AGP built-in Kotlin](https://developer.android.com/build/migrate-to-built-in-kotlin).
- [Compose dependencies/compiler](https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler).
- [Roborazzi setup/capture tasks](https://github.com/takahirom/roborazzi), [1.76.0 release](https://github.com/takahirom/roborazzi/releases/tag/1.76.0); API examples also checked through Context7 `/takahirom/roborazzi`.
- [Robolectric getting started](https://robolectric.org/getting-started/).
- [Baseline Profile collection](https://developer.android.com/topic/performance/baselineprofiles/create-baselineprofile).
- [Claude plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies).
- Google Maven/Central `maven-metadata.xml` for the versions listed above, queried directly on 2026-10-09.
- [Roboto OFL](https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/OFL.txt) and the locally inspected ECC 1.10.0 MIT license/source paths.

The owner reviews this written plan before implementation; the previously selected subagent-driven method remains in effect.
