---
name: compose-capture
description: Use when producing candidate Roborazzi screenshots of generated Compose UI and preparing their metadata for figma-core visual comparison.
---

# Candidate captures

Captures are evidence for core's comparison. They are never approved goldens and never modify the Figma reference.

## Harness

Copy `${CLAUDE_PLUGIN_ROOT}/templates/ComposeCaptureTest.kt` into the app's unit-test source set and replace `__FIXTURE_PACKAGE__` with the app package. Adapt scene/node declarations, state assertions and the font registry to the real content (the template is the synthetic fixture harness; its `sourceRevision` must be bound to the fresh core export). The app needs Roborazzi, Robolectric (native graphics) and Compose UI test dependencies; add them only if absent, following the version catalog, and report each addition. Background: `docs/adr/009-roborazzi-capture.md` in the plugin source repository.

## Run

From the app project, with its own Gradle wrapper (sample command; adapt the filter):

```text
./gradlew.bat :app:testDebugUnitTest --tests '*<YourCaptureTest>' '-Proborazzi.test.record=true'
```

Output goes to `app/build/figma-candidates/<variant>/` only (PNG plus `capture-receipt.json`). Recording is skipped when the property is absent. recordRoborazziDebug and verifyRoborazziDebug are not substitutes for core comparison; never publish into approved source folders.

## Prepare metadata

```text
"<venv python>" "${CLAUDE_PLUGIN_ROOT}/scripts/compose.py" prepare-capture --bundle "<bundle>" --config "<config.json>" --project "<app root>" --core-command-json '<locate_core output>' --reference-meta "<reference meta.json>" --measured "<capture-receipt.json>" --image "<candidate.png>" --output "<app root>/app/build/figma-candidates/<variant>/actual-meta.json"
```

It checks image hash, size, density, crop, fonts and theme identity against the reference facts and the compiled theme, and blocks (exit 2) on any mismatch. Then run `figma-core:visual-verify` with the candidate PNG and `actual-meta.json`.

## Hard rules

- Never copy or link a reference image into the actual capture; never edit reference metadata to match.
- Never relax tolerances or edit the policy to pass; policy changes need fresh owner approval.
- Never resize a capture to force matching dimensions; crop only to measured node bounds. A scale mismatch means obtain a matching-scale reference or report the comparison blocked.
- A synthetic pass says nothing about text fidelity or owner approval. Human visual review remains `not_run`.
- Not automated: device/emulator capture, ADB screencap fallback and golden publication are not provided by this plugin.
