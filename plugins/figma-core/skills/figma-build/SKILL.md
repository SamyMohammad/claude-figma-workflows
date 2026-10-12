---
name: figma-build
description: Use when a user requests implementation of a Figma design in a Flutter or Jetpack Compose application.
---

# Build from a verified bundle

Use `figma-core:figma-extract` to prepare or refresh the requested bundle, then `figma-core:token-audit`. A sparse screenshot or context leaves affected nodes pending; request missing child data and make zero code edits for those nodes. Offline bundle freshness is unverified and must be surfaced.

Inspect the selected application root and explicit project evidence. Flutter requires a Flutter dependency in its `pubspec.yaml`. Compose requires Compose plugin/dependency evidence in the selected Android project. A Flutter-generated Android host is not Compose. If multiple app roots or both targets are possible, ask for the target/root. Dispatch only to an installed `figma-flutter:build` or `figma-compose:build` skill ID. If the adapter is unavailable, report blocked; do not synthesize a replacement UI.

Invoke local checks with the selected verified venv Python and `${CLAUDE_PLUGIN_ROOT}/scripts/core.py`, passing discrete quoted arguments. Do not use `$ARGUMENTS` as shell text. Access only files relevant to the requested project and bundle.
