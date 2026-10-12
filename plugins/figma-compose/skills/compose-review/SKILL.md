---
name: compose-review
description: Use when reviewing generated or edited Compose UI code for architecture, performance and policy before reporting a Figma implementation complete.
---

# Compose review checklist

A manual review done by the agent reading the diff. There is no Kotlin policy scanner in this repo; never claim an automated scan ran. Report each item as `ok`, `issue` (with file and line) or `not checked`.

## Architecture
- Composables contain rendering, interaction and state observation only; no repository, data-source or network references; no business rules.
- ViewModel exposes `StateFlow` state; collection is lifecycle-aware; one-off events are modeled deliberately.
- Existing DI, navigation and module boundaries were followed; no unrequested migrations or new libraries.
- Components were reused from the component map; variants are typed parameters.

## Design policy
- Colors, type, shapes and spacing come from generated theme tokens; no stray literals where a token exists.
- Generated theme files are not hand-edited (regenerate instead); fonts come from verified resources.
- No source screenshot used as an asset; no sizing hacks to match captures.
- Mixed-direction/Arabic text and text scaling were considered; non-text controls have content descriptions.

## Performance (by reading, not measured)
- No heavy work in composition (sorting, parsing, large allocations) without a `remember`/derivation reason.
- Lazy lists have stable keys; lambdas passed into hot lists do not capture unstable mutable state needlessly.
- No blanket `@Stable`/`@Immutable` or stability allowlists hiding problems.
- State explicitly that no benchmark or recomposition report was produced unless one actually was.

## Output
List findings, then what was not checked. Do not mark visual review passed; it is `not_run` until the owner reviews. Record unresolved items in `docs/design-decisions/<screen>.md`.
