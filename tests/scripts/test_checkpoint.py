import json

import pytest

from figma_core.checkpoint import can_reuse, complete_node
from figma_core.documents import read_json
from figma_core.errors import CoreError
from fixtures.make_core_fixture import make_fixture


def test_unknown_revision_never_claims_freshness():
    entry = {"sourceRevision": None, "nodeHash": "a", "captureHash": "b", "schemaVersion": 1, "freshness": "verified"}
    assert can_reuse(entry, entry) is False


def test_changed_revision_never_reuses():
    entry = {"sourceRevision": "old", "nodeHash": "a", "captureHash": "b", "schemaVersion": 1, "freshness": "verified"}
    assert not can_reuse(entry, {**entry, "sourceRevision": "new"})
    assert can_reuse(entry, dict(entry))


def test_missing_reference_keeps_node_pending(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    node = manifest["nodes"][0]
    node["status"] = "pending"
    manifest["status"] = "partial"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (root / node["path"] / "reference.png").unlink()
    result = complete_node(root, node["id"])
    assert result["nodes"][0]["status"] == "pending"
    assert result["nodes"][0]["errorCode"] is not None
    assert read_json(manifest_path)["status"] == "partial"


def test_complete_node_updates_staged_hashes(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    node = manifest["nodes"][0]
    node["status"] = "pending"
    manifest["status"] = "partial"
    for suffix in ("context.md", "reference.png", "meta.json"):
        manifest["files"].pop(f'{node["path"]}/{suffix}')
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = complete_node(root, node["id"])
    assert result["status"] == "complete"
    assert result["nodes"][0]["status"] == "complete"
    assert len(result["files"][f'{node["path"]}/reference.png']) == 64


def test_crashed_manifest_replace_keeps_previous_checkpoint(tmp_path, monkeypatch):
    root = make_fixture(tmp_path / "bundle")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    node = manifest["nodes"][0]
    node["status"] = "pending"
    manifest["status"] = "partial"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr("figma_core.storage.os.replace", fail)
    with pytest.raises(CoreError, match="replace failed"):
        complete_node(root, node["id"])
    assert read_json(manifest_path)["nodes"][0]["status"] == "pending"


def test_other_complete_node_missing_file_ref_blocks_final_completion(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    pending = manifest["nodes"][0]
    other = manifest["nodes"][1]
    pending["status"] = "pending"
    manifest["status"] = "partial"
    manifest["files"].pop(f'{other["path"]}/reference.png')
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = complete_node(root, pending["id"])
    assert result["status"] == "partial"
    assert result["nodes"][0]["status"] == "pending"
    assert result["nodes"][0]["errorCode"] is not None
