"""Validate capture provenance before measuring pixels."""

from pathlib import Path

from .approvals import content_hash, require_approval
from .documents import read_json
from .errors import CoreError
from .images import load_png
from .paths import safe_path
from .pixels import measure
from .reports import evidence_payload, write_report
from .schema import validate_bundle, validate_document
from .storage import file_hash


_MATCHED = ("nodeId", "sourceRevision", "logicalSize", "pixelSize", "scale", "locale",
            "direction", "theme", "fontHashes", "containsText", "textScale", "crop", "insets",
            "animation", "colorSpace")


def require_matching_capture(reference_meta: dict, actual_meta: dict) -> None:
    validate_document("meta", reference_meta)
    validate_document("meta", actual_meta)
    for field in _MATCHED:
        if reference_meta[field] != actual_meta[field]:
            raise CoreError("CAPTURE_MISMATCH", f"Capture {field} differs")
    for meta in (reference_meta, actual_meta):
        if any(abs(logical * meta["scale"] - pixel) > 1e-6
               for logical, pixel in zip(meta["logicalSize"], meta["pixelSize"])):
            raise CoreError("CAPTURE_MISMATCH", "Capture size and scale disagree")
        x, y, width, height = meta["crop"]
        if x + width > meta["pixelSize"][0] or y + height > meta["pixelSize"][1]:
            raise CoreError("CAPTURE_MISMATCH", "Capture crop exceeds size")


def _bundle_inputs(bundle: Path, reference: Path, reference_meta: dict, policy: dict,
                   policy_approval: dict) -> str:
    manifest = validate_bundle(bundle)
    if manifest["status"] != "complete":
        raise CoreError("BUNDLE_INCOMPLETE", "Bundle is not complete")
    node = next((item for item in manifest["nodes"]
                 if item["id"] == reference_meta["nodeId"] and item["status"] == "complete"), None)
    if node is None or node["sourceRevision"] != manifest["sourceRevision"]:
        raise CoreError("CAPTURE_MISMATCH", "Reference node or revision is not completed")
    recorded_reference = safe_path(bundle, f'{node["path"]}/reference.png')
    if reference.resolve() != recorded_reference.resolve():
        raise CoreError("REFERENCE_INVALID", "Reference is not the recorded node image")
    recorded_meta = read_json(safe_path(bundle, f'{node["path"]}/meta.json'))
    if reference_meta != recorded_meta:
        raise CoreError("CAPTURE_MISMATCH", "Reference metadata differs from recorded metadata")
    recorded_policy = read_json(safe_path(bundle, "comparison-policy.json"))
    if policy != recorded_policy:
        raise CoreError("POLICY_INVALID", "Policy differs from recorded bundle policy")
    require_approval(policy, policy_approval, "policy")
    tokens = read_json(safe_path(bundle, "tokens.json"))
    modes = {mode for mode in ("light", "dark") if mode in tokens}
    if set(manifest["tokenModes"]) != modes:
        raise CoreError("TOKEN_MODE", "Manifest token modes differ from token groups")
    token_approval_path = safe_path(bundle, "tokens-approval.json")
    if not token_approval_path.is_file() or "tokens-approval.json" not in manifest["files"]:
        raise CoreError("APPROVAL_INVALID", "Token approval is missing")
    token_approval = read_json(token_approval_path)
    require_approval(tokens, token_approval, "tokens")
    if set(token_approval["modes"]) != modes:
        raise CoreError("APPROVAL_INVALID", "Token approval modes differ")
    if reference_meta["theme"] not in set(token_approval["modes"]):
        raise CoreError("APPROVAL_INVALID", "Capture theme is not an approved token mode")
    fonts = read_json(safe_path(bundle, "fonts.json"))["fonts"]
    available = {font["path"]: font for font in fonts
                 if font["status"] == "available" and font["license"] == "approved"}
    if reference_meta["containsText"] and not reference_meta["fontHashes"]:
        raise CoreError("FONT_UNAVAILABLE", "Text capture lacks used-font evidence")
    for path, expected in reference_meta["fontHashes"].items():
        font = available.get(path)
        if font is None or font["sha256"] != expected or file_hash(safe_path(bundle, path)) != expected:
            raise CoreError("FONT_UNAVAILABLE", f"Font unavailable or changed: {path}")
    assets = read_json(safe_path(bundle, "assets/manifest.json"))["assets"]
    if any(asset["status"] != "available" for asset in assets):
        raise CoreError("ASSET_UNAVAILABLE", "Bundle contains unavailable assets")
    return content_hash(tokens)


def compare_capture(bundle: Path, reference: Path, actual: Path, reference_meta: dict,
                    actual_meta: dict, policy: dict, policy_approval: dict, output: Path) -> dict:
    """Return and save a truthful run report; blocked checks have no pixel metric."""
    paths = (bundle.resolve(), reference.resolve(), actual.resolve())
    run = output.resolve()
    if any(run == path or run.is_relative_to(path) or path.is_relative_to(run) for path in paths):
        raise CoreError("REPORT_PATH", "Output overlaps input or bundle")
    report = {"schemaVersion": 1, "status": "blocked", "automatedComparison": "blocked",
              "visualReview": "not_run", "geometry": "not_run", "elapsedCheck": "not_run",
              "freshness": "unverified",
              "freshnessReason": "Offline comparison; source freshness is unverified"}
    images = None
    try:
        require_matching_capture(reference_meta, actual_meta)
        token_hash = _bundle_inputs(bundle, reference, reference_meta, policy, policy_approval)
        images = (load_png(reference, reference_meta["colorSpace"]),
                  load_png(actual, actual_meta["colorSpace"]))
        if images[0].size != tuple(reference_meta["pixelSize"]) or images[1].size != tuple(actual_meta["pixelSize"]):
            raise CoreError("IMAGE_INVALID", "PNG dimensions differ from capture metadata")
        result = measure(*images, policy)
        meta_hash = content_hash({"reference": reference_meta, "actual": actual_meta})
        evidence = evidence_payload(file_hash(reference), file_hash(actual), meta_hash,
                                    content_hash(policy), token_hash)
        report.update({"status": result["status"], "automatedComparison": result["status"],
                       "changedPixels": result["changedPixels"], "eligiblePixels": result["eligiblePixels"],
                       "changedRatio": result["changedRatio"], "criticalResults": result["criticalResults"],
                       "policy": policy, **evidence, "evidenceHash": content_hash(evidence),
                       "referenceRenderer": reference_meta["renderer"], "actualRenderer": actual_meta["renderer"],
                       "referencePlatform": reference_meta["platform"], "actualPlatform": actual_meta["platform"]})
        write_report(output, report, *images, result["diff"], result["overlay"])
    except CoreError as error:
        report.update({"code": error.code, "reason": str(error)})
        write_report(output, report)
    return report
