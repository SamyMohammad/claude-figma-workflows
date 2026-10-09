"""Versioned design bundle validation."""

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .documents import read_json
from .errors import CoreError


_SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"
_KINDS = frozenset({"manifest", "meta", "fonts", "component-map", "assets", "approval", "comparison-policy"})
_REQUIRED = ("tokens.json", "fonts.json", "component-map.json", "assets/manifest.json", "comparison-policy.json")


def _relative(value: str) -> Path:
    posix = PurePosixPath(value)
    if (not value or "\\" in value or value.startswith("/") or ":" in value
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise CoreError("PATH_INVALID", "Invalid relative path in bundle")
    return Path(*posix.parts)


def _inside(root: Path, relative: str) -> Path:
    path = root / _relative(relative)
    if not path.resolve().is_relative_to(root.resolve()):
        raise CoreError("PATH_INVALID", "Bundle path leaves its root")
    return path


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


def validate_bundle(root: Path) -> dict:
    """Validate bundle structure and references, without verifying file hashes."""
    root = root.resolve()
    manifest = read_json(root / "manifest.json")
    validate_document("manifest", manifest)
    files = manifest["files"]
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
    mapped = [(entry["nodeId"], entry["variant"], entry["platform"])
              for entry in documents["component-map"]["components"]]
    if len(mapped) != len(set(mapped)) or any(node_id not in ids for node_id, _, _ in mapped):
        raise CoreError("BUNDLE_INVALID", "Invalid component mapping references")
    asset_paths = [entry["path"] for entry in documents["assets"]["assets"]]
    if len(asset_paths) != len(set(asset_paths)):
        raise CoreError("BUNDLE_INVALID", "Duplicate asset paths")
    for asset in documents["assets"]["assets"]:
        _inside(root, asset["path"])
        if asset["nodeId"] not in ids:
            raise CoreError("BUNDLE_INVALID", "Invalid asset node reference")
        if asset["status"] == "available" and asset["path"] not in files:
            raise CoreError("BUNDLE_INVALID", "Available asset has no file reference")
    for node in manifest["nodes"]:
        directory = node["path"]
        _inside(root, directory)
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
    return manifest
