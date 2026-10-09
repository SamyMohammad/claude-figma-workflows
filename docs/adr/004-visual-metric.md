# ADR 004: Visible pixel comparison

Status: Accepted for the core milestone, 2026-10-09.

## Context

Raw RGBA byte comparison treats hidden RGB under zero alpha as a difference and can miss a small required control when the whole screen is mostly unchanged. Captures can also have incompatible dimensions or color metadata. A pixel ratio alone does not measure layout geometry or replace human review.

## Decision

Load PNG captures as RGBA only when capture metadata declares sRGB and the image is untagged or carries supported sRGB metadata. An embedded ICC profile must match the color-defining header fields and tags of the trusted sRGB profile supplied by Pillow's color management library. Description and copyright tags may differ. Reject additional tags, altered colorants or transfer curves, unsupported color metadata, and non-PNG input. Keep Pillow's decompression safeguards and turn decompression-bomb warnings into errors.

For each pixel, composite both images on black and white backgrounds and use the largest absolute RGB channel difference. A pixel changes only when that value is strictly greater than the policy's required `channelTolerance`. Ignore the union of documented exclusion boxes; all counts and the global ratio use the remaining pixels. Reject an empty eligible area, out-of-bounds boxes, and any ignored box that intersects a critical box. Every critical region has its own ratio and limit. The comparison passes only when the global ratio and every critical ratio meet their limits, including equality at the limit. Never resize inputs. Produce an in-memory red heatmap and an overlay that blends changed pixels with red.

## Alternatives and consequences

Comparing raw RGBA bytes would report invisible differences. Compositing on only one background would miss some alpha changes. A single screen ratio would let a small missing control pass. This metric is deterministic and needs no new dependency, but it does not establish logical-pixel geometry, renderer parity, or human visual acceptance. Those checks remain separate in the capture and reporting workflow.

## Evidence

Literal-pixel tests cover transparent RGB, alpha-only changes, tolerance and ratio boundaries, overlapping masks, an empty eligible area, and individual critical gates. PNG tests cover accepted sRGB, a falsely labeled profile with an altered red colorant, unsupported metadata, wrong formats, and decompression safeguards.
