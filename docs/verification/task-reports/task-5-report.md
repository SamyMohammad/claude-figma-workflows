# C5 implementation report

## Files changed

- `plugins/figma-core/scripts/figma_core/images.py` — sRGB PNG loader with format, color metadata, and decompression safeguards.
- `plugins/figma-core/scripts/figma_core/pixels.py` — visible pixel metric, masks, critical gates, diff, and overlay.
- `tests/scripts/test_images.py` — PNG and profile tests.
- `tests/scripts/test_pixels.py` — literal pixel and policy boundary tests.
- `docs/adr/004-visual-metric.md` — metric decision and limits.

## Verification

- Red: `.venv/Scripts/python.exe -m pytest tests/scripts/test_pixels.py tests/scripts/test_images.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c5-red` — exit 1, collection failed because `figma_core.pixels` and `figma_core.images` did not exist.
- First green attempt: targeted tests — 1 failed, 15 passed. The test expected pure red, while the specified overlay blends red with the actual pixel; corrected the assertion to `(127, 0, 0)`.
- `.venv/Scripts/python.exe -m pytest tests/scripts/test_pixels.py tests/scripts/test_images.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c5-green2` — 18 passed in 0.71s.
- `.venv/Scripts/python.exe -m pytest -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c1-c5-final` — 95 passed, 1 skipped in 10.51s.
- `git diff --check` — exit 0, no whitespace errors.

## Scope and concerns

No files outside C5 ownership were changed. No dependencies were added. The metric makes no geometry or human-review claim. No commit was created; the controller handles it.

## Review fix: ICC profile identity

The original check trusted an sRGB profile name and RGB color-space label. A profile with its red colorant zeroed retained that label and was accepted. The loader now compares the color-defining ICC header fields and tag payloads against the trusted sRGB profile from Pillow's color management library. It allows description and copyright text to vary, but rejects changed colorants, transfer curves, or unknown tags. This intentionally rejects other sRGB profile variants until their color characteristics are explicitly reviewed and supported.

- Red: `.venv/Scripts/python.exe -m pytest tests/scripts/test_images.py::test_srgb_named_profile_with_altered_red_colorant_is_rejected -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c5-icc-red` — exit 1, `Failed: DID NOT RAISE CoreError`.
- `.venv/Scripts/python.exe -m pytest tests/scripts/test_images.py tests/scripts/test_pixels.py -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c5-icc-green` — 19 passed in 0.68s.
- `.venv/Scripts/python.exe -m pytest -q --basetemp=.superpowers/sdd/2026-10-09-figma-core/pytest-c1-c5-icc-final` — 96 passed, 1 skipped in 9.17s.
- `git diff --check` — exit 0. Git printed only LF-to-CRLF conversion warnings for the three changed tracked files.
