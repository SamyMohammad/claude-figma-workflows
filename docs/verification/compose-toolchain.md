# Compose sample toolchain evidence

The sample pins Gradle9.6.0, AGP9.4.1, Kotlin/Compose compiler2.4.21, Compose BOM2026.09.00, Activity1.13.0, Lifecycle2.11.0, Roborazzi1.76.0 and Robolectric4.17. AGP built-in Kotlin is used, without the Kotlin Android plugin. Effective plugin resolution is recorded in the controller's plugin-build-environment.txt; actual sample build proof is recorded below when complete.

The official Gradle distribution SHA256 is `bbaeb2fef8710818cf0e261201dab964c572f92b942812df0c3620d62a529a01`, pinned in the generated wrapper. Controller independently verified wrapperJAR SHA256 `497c8c2a7e5031f6aa847f88104aa80a93532ec32ee17bdb8d1d2f67a194a9c7` against official published evidence.

Compatibility rulings:

- AGP9.4.1 is the verified stable patch replacing planned9.4.0.
- Actual dependency AAR metadata requires compileSDK37.0 for Compose1.12.1 and Lifecycle2.11.0. The sample uses `compileSdk { version = release(37) { minorApiLevel = 0 } }`; targetSDK36 and minSDK26 retained. No consumer SDK upgrade.
- Host native memory exhaustion at Xmx3g required sample-local512MB heap, one worker and in-process Kotlin. No global memory settings changed.
- JBR21 Robolectric API36 setup failed accessing `jdk.internal.access.SharedSecrets`. Test JVM tasks alone export that package to unnamed modules. This targets the observed IllegalAccessException; see [JetBrains upstream test configuration](https://github.com/JetBrains/compose-multiplatform/blob/master/components/resources/library/build.gradle.kts) for the same Robolectric access requirement. Testworker heap384MB/maxParallelForks1. No application JVM/module changes.

JBR and SDK are selected through execution environment variables. No machine paths are committed to Gradle or local.properties.

Roboto original Google Fonts variable bytes and OFL notice are preserved; source commit, download URLs and SHA256 values are in sample font-provenance.json. Graphic references contain no text; no real-font golden or live Figma fidelity is claimed by C3.

Actual Windows verification (JBR21.0.3): `:app:compileDebugKotlin :app:testDebugUnitTest :app:assembleDebug :app:buildEnvironment` succeeded in 52s; 2 tests, zero failures, including Continue → Review and measured160×160DP graphic frame. Root sample `buildEnvironment` succeeded in 16s and resolved AGP9.4.1, built-in Kotlin Gradle plugin2.2.10 →2.4.21, Compose compiler plugin2.4.21. The first complete compile/test/APK run succeeded in 2m32s. Final generated manifest identity was then regenerated through the production CLI after byte-preservation attributes were added.

Byte integrity: narrow sample/bundle .gitattributes preserve exact source, font, license and manifest bytes across checkout; only wrapper script line endings are selected explicitly. Staged Git blob checks matched all26 bundle manifest file hashes, all4 generated Kotlin hashes and all3 mapped component source hashes. The original OFL includes trailing whitespace; it remains byte-identical rather than being reformatted.

The still-supported JUnit4 `createComposeRule` emits a deprecation warning recommending the v2 package. The current API passed actual tests and is retained for a consistent C4 capture harness; no warning-free claim is made. Device, native golden comparison, Unix and liveFigma checks remain later-task evidence.

Final byte-preservation identity compile/unit/APK build passed in 1m10s (46 tasks); the generated theme identity corresponds to the current bundled manifest.
