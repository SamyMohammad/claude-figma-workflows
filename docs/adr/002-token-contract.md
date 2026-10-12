# ADR 002: DTCG token subset and modes

Status: Accepted for the core milestone, 2026-10-09.

`tokens.json` uses ordinary DTCG top-level groups `base`, `light`, and `dark`. The manifest selects modes with `tokenModes`. Each selected mode has matching semantic token paths and types. Aliases use full paths, such as `{base.space.small}`; shared spacing belongs in `base` and may be referenced from each mode. No custom mode property is inserted into token values.

The supported subset is color (sRGB), dimension (px/rem), number, fontFamily, fontWeight, duration, cubicBezier, and typography. Source provenance uses `$extensions.org.claude-figma-workflows.source` with `nodeId` and `kind` (`variable`, `style`, or `inferred`). Raw source values and node IDs remain unchanged. Unsupported token types, `$extends`, and `$ref` are rejected by the token audit milestone. This contract does not claim full DTCG coverage.

The synthetic fixture has a shared spacing alias, an sRGB color, and a typography token. Its images contain no text, so empty font manifests and font-hash maps are intentional. Token approval binds to exact content; changes require fresh approval.
