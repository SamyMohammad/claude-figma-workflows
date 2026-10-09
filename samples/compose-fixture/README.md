# Synthetic Compose fixture

This dependency-free Android sample consumes generated AppTheme and LocalAppTokens from a local core-approved synthetic bundle. The fixture source is `tests/fixtures/make_compose_fixture.py`; bundle `tests/fixtures/compose-v1` contains independently drawn Pillow graphics. No live Figma fidelity claim is made.

Run from this directory with JDK 21 and an installed Android SDK selected through local environment variables:

```
./gradlew :app:compileDebugKotlin :app:testDebugUnitTest :app:assembleDebug
```

The pinned compile SDK is 37.0; target SDK 36 and minimum SDK 26. The serial 512 MB Gradle heap and in-process Kotlin compiler keep this small sample usable on the measured memory-constrained host.

Roboto is the original Google Fonts variable font at the commit in `font-provenance.json`, distributed under the bundled OFL notice. Graphic-only references contain no text; they cannot establish a real-font golden comparison. The test renders actual Roboto text and exercises Continue → Review, while device checks and reviewed text goldens are later milestone evidence.
