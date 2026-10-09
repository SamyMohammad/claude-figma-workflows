# ADR-008: Compose component mapping

Status: accepted for the synthetic sample (2026-10-10).

Use the shared core Component Map as the default source-to-Compose contract. Each entry binds the synthetic node ID and variant to a project-relative Kotlin file, a Compose function symbol, and the SHA256 of its source bytes. The fixture coordinator alone writes the map and manifest hashes. Core validates structural schemas and safe paths; the sample fixture checks source presence, symbol presence, variant identity and current hashes.

Code Connect remains optional. It can add live Figma integration when an owner-selected file and suitable access exist, but it is not required to compile, inspect or verify a local approved bundle. This sample establishes only synthetic integration; its IDs, vector references and approval are explicitly synthetic.

Components take typed rendering state and callbacks. FixtureViewModel owns only screen selection; composables render and collect lifecycle-aware state. No backend, business domain or DI container is invented for this preview.
