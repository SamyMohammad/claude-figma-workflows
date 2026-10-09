"""Coordinator-owned extraction checkpoints."""

from pathlib import Path

from .documents import read_json
from .errors import CoreError
from .paths import safe_path
from .schema import _check_meta, validate_document
from .storage import atomic_json, file_hash


_NODE_FILES = ("context.md", "reference.png", "meta.json")


def can_reuse(old: dict, new: dict) -> bool:
    return (old.get("sourceRevision") is not None
            and old.get("sourceRevision") == new.get("sourceRevision")
            and old.get("nodeHash") is not None
            and old.get("nodeHash") == new.get("nodeHash")
            and old.get("captureHash") is not None
            and old.get("captureHash") == new.get("captureHash")
            and old.get("schemaVersion") is not None
            and old.get("schemaVersion") == new.get("schemaVersion")
            and old.get("freshness") == new.get("freshness") == "verified")


def complete_node(root: Path, node_id: str) -> dict:
    """Verify staged node files and publish their hashes in one manifest write."""
    manifest = read_json(safe_path(root, "manifest.json"))
    validate_document("manifest", manifest)
    node = next((item for item in manifest["nodes"] if item["id"] == node_id), None)
    if node is None:
        raise CoreError("NODE_UNKNOWN", f"Unknown node: {node_id}")
    try:
        paths = {suffix: safe_path(root, f'{node["path"]}/{suffix}') for suffix in _NODE_FILES}
        for suffix, path in paths.items():
            if not path.is_file():
                raise CoreError("NODE_INCOMPLETE", f"Missing node file: {suffix}")
        meta = read_json(paths["meta.json"])
        validate_document("meta", meta)
        _check_meta(meta, node)
        if node["sourceRevision"] is None or node["sourceRevision"] != manifest["sourceRevision"]:
            raise CoreError("REVISION_MISMATCH", "Node source revision is unknown or differs")
        hashes = {f'{node["path"]}/{suffix}': file_hash(path) for suffix, path in paths.items()}
        for name, expected in manifest["files"].items():
            if name not in hashes and file_hash(safe_path(root, name)) != expected:
                raise CoreError("HASH_MISMATCH", f"Recorded file hash mismatch: {name}")
    except CoreError as error:
        node["status"] = "pending"
        node["errorCode"] = error.code
        manifest["status"] = "partial"
        atomic_json(root, "manifest.json", manifest)
        return manifest
    manifest["files"].update(hashes)
    node["status"] = "complete"
    node["errorCode"] = None
    asset_doc = read_json(safe_path(root, "assets/manifest.json"))
    validate_document("assets", asset_doc)
    all_assets = all(
        asset["status"] == "available"
        and asset["path"] in manifest["files"]
        and file_hash(safe_path(root, asset["path"])) == asset["sha256"]
        for asset in asset_doc["assets"])
    manifest["status"] = ("complete" if all_assets and all(
        item["status"] == "complete" for item in manifest["nodes"]) else "partial")
    atomic_json(root, "manifest.json", manifest)
    return manifest
