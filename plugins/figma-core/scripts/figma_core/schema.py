"""Versioned design bundle validation."""

from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .documents import read_json
from .errors import CoreError
from .paths import check_collisions, safe_path
from .storage import file_hash


_SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"
_KINDS = frozenset({"manifest", "meta", "fonts", "component-map", "assets", "approval", "comparison-policy"})
_REQUIRED = ("tokens.json", "fonts.json", "component-map.json", "assets/manifest.json", "comparison-policy.json")


def _inside(root: Path, relative: str) -> Path:
    return safe_path(root, relative)


def _utc(value: str, label: str) -> None:
    if not value.endswith(("Z", "+00:00")):
        raise CoreError("SCHEMA_INVALID", f"Invalid UTC timestamp at {label}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise CoreError("SCHEMA_INVALID", f"Invalid UTC timestamp at {label}") from None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed) or parsed.tzinfo is None:
        raise CoreError("SCHEMA_INVALID", f"Invalid UTC timestamp at {label}")


def validate_document(kind: str, value: dict) -> None:
    if kind not in _KINDS:
        raise CoreError("SCHEMA_UNKNOWN", f"Unknown document kind: {kind}")
    schema = read_json(_SCHEMAS / f"{kind}.schema.json")
    try:
        Draft202012Validator.check_schema(schema)
        problems = sorted(Draft202012Validator(schema).iter_errors(value),
                          key=lambda error: tuple(str(part) for part in error.path))
    except SchemaError:
        raise CoreError("SCHEMA_INVALID", f"Bundled {kind} schema is invalid") from None
    if problems:
        problem = problems[0]
        path = ".".join(str(part) for part in problem.path) or "$"
        if problem.validator == "required":
            missing = set(problem.validator_value) - set(problem.instance)
            path = ".".join(part for part in (path if path != "$" else "", sorted(missing)[0]) if part)
        raise CoreError("SCHEMA_INVALID", f"Invalid value at {path}")
    if kind == "manifest":
        _utc(value["extractedAt"], "extractedAt")
    elif kind == "approval":
        _utc(value["approvedAt"], "approvedAt")


def _check_meta(meta: dict, node: dict) -> None:
    if meta["nodeId"] != node["id"] or meta["sourceRevision"] != node["sourceRevision"]:
        raise CoreError("BUNDLE_INVALID", f"Node metadata mismatch: {node['path']}")
    for logical, pixel in zip(meta["logicalSize"], meta["pixelSize"]):
        if abs(logical * meta["scale"] - pixel) > 1e-6:
            raise CoreError("BUNDLE_INVALID", f"Logical/pixel size mismatch: {node['path']}")
    x, y, width, height = meta["crop"]
    if x + width > meta["pixelSize"][0] or y + height > meta["pixelSize"][1]:
        raise CoreError("BUNDLE_INVALID", f"Crop exceeds pixel size: {node['path']}")


def _boxes_overlap(first: list, second: list) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def _check_comparison_policy(policy: dict) -> None:
    ignored = [region["box"] for region in policy["ignored"]]
    for critical in policy["critical"]:
        if any(_boxes_overlap(critical["box"], box) for box in ignored):
            raise CoreError("BUNDLE_INVALID", "Critical and ignored regions overlap")


def validate_bundle(root: Path, *, manifest_override: dict | None = None) -> dict:
    """Validate bundle structure, references, and recorded file hashes."""
    root = root.resolve()
    manifest = (read_json(_inside(root, "manifest.json"))
                if manifest_override is None else manifest_override)
    validate_document("manifest", manifest)
    files = manifest["files"]
    check_collisions(list(files))
    for name in files:
        if not _inside(root, name).is_file():
            raise CoreError("BUNDLE_INVALID", f"Missing recorded file: {name}")
    for name in _REQUIRED:
        if name not in files:
            raise CoreError("BUNDLE_INVALID", f"Missing file reference: {name}")
    read_json(_inside(root, "tokens.json"))
    documents = {}
    for kind, name in (("fonts", "fonts.json"), ("component-map", "component-map.json"),
                       ("assets", "assets/manifest.json"),
                       ("comparison-policy", "comparison-policy.json")):
        documents[kind] = read_json(_inside(root, name))
        validate_document(kind, documents[kind])
    _check_comparison_policy(documents["comparison-policy"])
    for name in ("tokens-approval.json", "policy-approval.json", "visual-approval.json", "goldens-approval.json"):
        if (root / name).exists():
            validate_document("approval", read_json(_inside(root, name)))
            if name not in files:
                raise CoreError("BUNDLE_INVALID", f"Missing file reference: {name}")
    ids = [node["id"] for node in manifest["nodes"]]
    paths = [node["path"] for node in manifest["nodes"]]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        raise CoreError("BUNDLE_INVALID", "Duplicate node IDs or paths")
    if set(ids) != set(manifest["scope"]) or set(ids) & set(manifest["excludedNodes"]):
        raise CoreError("BUNDLE_INVALID", "Node scope mismatch")
    nodes_by_id = {node["id"]: node for node in manifest["nodes"]}
    mapped = [(entry["nodeId"], entry["variant"], entry["platform"])
              for entry in documents["component-map"]["components"]]
    if len(mapped) != len(set(mapped)) or any(
        node_id not in nodes_by_id
        or nodes_by_id[node_id]["kind"] != "component"
        or nodes_by_id[node_id]["variant"] != variant
        for node_id, variant, _ in mapped
    ):
        raise CoreError("BUNDLE_INVALID", "Invalid component mapping references")
    for font in documents["fonts"]["fonts"]:
        path = font["path"]
        if path is not None:
            _inside(root, path)
        if font["status"] == "available" and (
            path is None or font["sha256"] is None or path not in files
        ):
            raise CoreError("BUNDLE_INVALID", "Available font has no file reference")
        if font["status"] == "available" and file_hash(_inside(root, path)) != font["sha256"]:
            raise CoreError("BUNDLE_INVALID", f"Available font hash mismatch: {path}")
    asset_paths = [entry["path"] for entry in documents["assets"]["assets"]]
    if len(asset_paths) != len(set(asset_paths)):
        raise CoreError("BUNDLE_INVALID", "Duplicate asset paths")
    for asset in documents["assets"]["assets"]:
        _inside(root, asset["path"])
        if asset["nodeId"] not in ids:
            raise CoreError("BUNDLE_INVALID", "Invalid asset node reference")
        if asset["status"] == "available" and asset["path"] not in files:
            raise CoreError("BUNDLE_INVALID", "Available asset has no file reference")
        if (asset["status"] == "available"
                and file_hash(_inside(root, asset["path"])) != asset["sha256"]):
            raise CoreError("BUNDLE_INVALID", f"Available asset hash mismatch: {asset['path']}")
    for node in manifest["nodes"]:
        directory = node["path"]
        _inside(root, directory)
        reference_approval = f"{directory}/reference-approval.json"
        if _inside(root, reference_approval).exists():
            if reference_approval not in files:
                raise CoreError("BUNDLE_INVALID", "Missing source-target approval file reference")
            approval = read_json(_inside(root, reference_approval))
            validate_document("approval", approval)
            if approval["kind"] != "reference":
                raise CoreError("APPROVAL_INVALID", "Source-target approval kind differs")
        if node["status"] != "complete":
            continue
        for suffix in ("context.md", "reference.png", "meta.json"):
            relative = f"{directory}/{suffix}"
            if relative not in files or not _inside(root, relative).is_file():
                raise CoreError("BUNDLE_INVALID", f"Missing completed node file: {relative}")
        meta = read_json(_inside(root, f"{directory}/meta.json"))
        validate_document("meta", meta)
        _check_meta(meta, node)
        for region in (*documents["comparison-policy"]["ignored"],
                       *documents["comparison-policy"]["critical"]):
            x, y, width, height = region["box"]
            if x + width > meta["pixelSize"][0] or y + height > meta["pixelSize"][1]:
                raise CoreError("BUNDLE_INVALID", "Comparison region exceeds pixel size")
    if manifest["status"] == "complete" and any(node["status"] != "complete" for node in manifest["nodes"]):
        raise CoreError("BUNDLE_INVALID", "Complete bundle has incomplete nodes")
    if manifest["status"] == "complete" and any(
        asset["status"] != "available" for asset in documents["assets"]["assets"]
    ):
        raise CoreError("BUNDLE_INVALID", "Complete bundle has missing assets")
    check_collisions(list(files) + paths, set(paths))
    for name, expected in files.items():
        if file_hash(_inside(root, name)) != expected:
            raise CoreError("BUNDLE_INVALID", f"Recorded file hash mismatch: {name}")
    return manifest
